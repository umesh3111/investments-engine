"""
AI capex-cycle overlay — Stage 1 (informational only; never changes a stance).

Tracks the hyperscalers' combined capital expenditure from quarterly cash-flow
statements and classifies where the AI buildout cycle is:

    ACCELERATING  sequential capex growth >= last quarter's sequential growth
    DECELERATING  still growing, but sequential growth is slowing
    CONTRACTING   year-over-year capex is down, or two straight sequential declines
    + STRETCHED   flag when capex > operating cash flow (buildout now balance-sheet/debt funded)

Suppliers tend to peak when the *growth rate* of capex peaks, not when spending
does — hence the acceleration measure. yfinance only returns ~5 quarters, so
acceleration is sequential (QoQ vs prior QoQ) and YoY is latest vs 4 quarters back.
Quarters are aligned by date (fiscal years differ, Yahoo has gaps), and each
comparison uses only the spenders that have both quarters (like-for-like).

classify_capex() is pure (testable); current_capex() fetches in the cloud env and
returns None on any failure so the cycle never breaks.
"""
from __future__ import annotations
from datetime import date, timedelta
from typing import Dict, List, Optional, Tuple

SPENDERS = ["MSFT", "GOOGL", "AMZN", "META", "ORCL"]

# How each name is exposed to the AI capex cycle. Untagged = not directly exposed.
EXPOSURE = {
    **{t: "SPENDER" for t in ["MSFT", "GOOG", "GOOGL", "AMZN", "META", "ORCL"]},
    **{t: "SUPPLIER" for t in ["NVDA", "AVGO", "AMD", "TSM", "ASML", "AMAT", "LRCX", "KLAC",
                               "ARM", "MRVL", "ANET", "CSCO", "DELL", "INTC", "ADI", "SMCI"]},
    **{t: "MEMORY" for t in ["MU", "SNDK", "SKHY"]},
    **{t: "NEOCLOUD" for t in ["CRWV", "NBIS"]},
    **{t: "POWER" for t in ["VRT", "ETN", "GEV", "CEG"]},
}
TAG_SHORT = {"SPENDER": "SPND", "SUPPLIER": "SUPP", "MEMORY": "MEM", "NEOCLOUD": "NEO", "POWER": "PWR"}

STRETCHED_INTENSITY = 1.0   # capex / operating cash flow
ALIGN_TOLERANCE_DAYS = 25   # how far a quarter-end may drift from the expected date

# A quarter = (period_end, capex_usd_positive, operating_cash_flow_usd)
Quarter = Tuple[date, float, Optional[float]]


def exposure(ticker: str) -> Optional[str]:
    return EXPOSURE.get(ticker.upper())


def _at(quarters: List[Quarter], anchor: date, days_back: int) -> Optional[Quarter]:
    """The quarter ending ~days_back before anchor (within tolerance), else None."""
    target = anchor - timedelta(days=days_back)
    best = min(quarters, key=lambda q: abs((q[0] - target).days), default=None)
    if best is None or abs((best[0] - target).days) > ALIGN_TOLERANCE_DAYS:
        return None
    return best


def _ratio(series: Dict[str, List[Quarter]], back_a: int, back_b: int) -> Tuple[Optional[float], int]:
    """sum(capex at back_a) / sum(capex at back_b) - 1, like-for-like; returns (growth, n_spenders)."""
    num = den = 0.0
    n = 0
    for qs in series.values():
        if not qs:
            continue
        anchor = max(q[0] for q in qs)
        a, b = _at(qs, anchor, back_a), _at(qs, anchor, back_b)
        if a and b and b[1] > 0:
            num, den, n = num + a[1], den + b[1], n + 1
    return (num / den - 1 if den > 0 else None), n


def classify_capex(series: Dict[str, List[Quarter]], smh_above_50: Optional[bool] = None) -> Optional[dict]:
    """series: ticker -> quarters (any order). Pure; returns None if there's nothing to measure."""
    latest = []
    for qs in series.values():
        if qs:
            latest.append(max(qs, key=lambda q: q[0]))
    if not latest:
        return None
    capex_latest = sum(q[1] for q in latest)
    ocf_latest = sum(q[2] for q in latest if q[2] is not None)
    with_ocf = [q for q in latest if q[2] is not None]
    intensity = (sum(q[1] for q in with_ocf) / ocf_latest) if ocf_latest > 0 else None

    yoy, n_yoy = _ratio(series, 0, 365)
    qoq, n_qoq = _ratio(series, 0, 91)
    prev_qoq, n_prev = _ratio(series, 91, 182)

    if (yoy is not None and yoy < 0) or (qoq is not None and prev_qoq is not None and qoq < 0 and prev_qoq < 0):
        phase = "CONTRACTING"
    elif qoq is not None and prev_qoq is not None:
        phase = "ACCELERATING" if qoq >= prev_qoq else "DECELERATING"
    else:
        phase = "UNKNOWN"

    return {
        "phase": phase,
        "stretched": intensity is not None and intensity > STRETCHED_INTENSITY,
        "capex_latest_bn": round(capex_latest / 1e9, 1),
        "yoy_pct": None if yoy is None else round(yoy * 100, 1),
        "qoq_pct": None if qoq is None else round(qoq * 100, 1),
        "prev_qoq_pct": None if prev_qoq is None else round(prev_qoq * 100, 1),
        "intensity_pct": None if intensity is None else round(intensity * 100),
        "smh_above_50": smh_above_50,
        "coverage": {"spenders": len(latest), "yoy": n_yoy, "qoq": n_qoq, "prev_qoq": n_prev},
        "as_of": max(q[0] for q in latest).isoformat(),
    }


def format_capex_line(capex: Optional[dict], tickers: Optional[List[str]] = None) -> str:
    """One header line for the digest/scan, e.g.
    'AI capex: ACCELERATING · STRETCHED 116% of op. cash · $230B/q +118% YoY · SMH > 50d · 22/73 exposed'"""
    parts = []
    if not capex:
        parts.append("AI capex: n/a")
    else:
        parts.append(f"AI capex: {capex['phase']}" + (" · STRETCHED" if capex["stretched"] else ""))
        if capex["intensity_pct"] is not None:
            parts.append(f"{capex['intensity_pct']}% of op. cash")
        growth = f" {capex['yoy_pct']:+.0f}% YoY" if capex["yoy_pct"] is not None else ""
        parts.append(f"${round(capex['capex_latest_bn'])}B/q{growth}")
        if capex["smh_above_50"] is not None:
            parts.append("SMH > 50d" if capex["smh_above_50"] else "SMH < 50d")
    if tickers:
        exposed = sum(1 for t in tickers if exposure(t))
        parts.append(f"{exposed}/{len(tickers)} exposed")
    return " · ".join(parts)


def _fetch_quarters(ticker: str) -> List[Quarter]:
    import yfinance as yf
    cf = yf.Ticker(ticker).quarterly_cashflow
    cap = cf.loc["Capital Expenditure"].dropna()
    ocf = cf.loc["Operating Cash Flow"] if "Operating Cash Flow" in cf.index else None
    out: List[Quarter] = []
    for d, v in cap.items():
        o = None
        if ocf is not None and d in ocf.index and ocf[d] == ocf[d]:  # not NaN
            o = float(ocf[d])
        out.append((d.date(), abs(float(v)), o))
    return out


def _smh_above_50() -> Optional[bool]:
    import yfinance as yf
    from ta import sma
    closes = [float(c) for c in yf.Ticker("SMH").history(period="90d", interval="1d")["Close"].tolist()]
    return closes[-1] > sma(closes, 50) if len(closes) >= 50 else None


def current_capex(fetch_quarters=None, fetch_smh=None) -> Optional[dict]:
    """Fetch + classify. Injectable for tests. Never raises — returns None on failure."""
    fetch_quarters = fetch_quarters or _fetch_quarters
    fetch_smh = fetch_smh or _smh_above_50
    series: Dict[str, List[Quarter]] = {}
    for t in SPENDERS:
        try:
            series[t] = fetch_quarters(t)
        except Exception:  # noqa: BLE001 — one spender missing just lowers coverage
            series[t] = []
    try:
        smh = fetch_smh()
    except Exception:  # noqa: BLE001
        smh = None
    try:
        return classify_capex(series, smh)
    except Exception:  # noqa: BLE001
        return None
