"""
Cycle runner — the deterministic brain a scheduled task calls. For each ticker:
fetch -> TA -> engine.evaluate -> stance + trade plan + horizon targets. Produces
the morning-digest table and the opportunity list (WATCH-or-better), ready for the
task's LLM layer to add its forward-looking read and send to Telegram/Notion.

Usage in the cloud env:
    from cycle import run_cycle, format_digest, format_opportunities
    rows = run_cycle(WATCHLIST, regime="BULLISH")
    print(format_digest(rows, "BULLISH", "2026-11-05"))
"""
from __future__ import annotations
from typing import List, Optional
from engine import evaluate, project_targets, ENGINE_CONFIG, AGGRESSIVE_CONFIG, ENGINE_CONFIG_VERSION
from capex import exposure, format_capex_line, TAG_SHORT

STANCE_ORDER = {"STRONG BUY": 0, "BUY": 1, "WATCH": 2, "AVOID": 3}
STANCE_LABEL = {"STRONG BUY": "STRONG", "BUY": "BUY", "WATCH": "WATCH", "AVOID": "AVOID"}


def run_cycle(tickers: List[str], regime: str = "NEUTRAL",
              news_by_ticker: Optional[dict] = None, aggressive: bool = False,
              ta_fetcher=None) -> List[dict]:
    """ta_fetcher(ticker)->priceTA dict is injectable (defaults to data.fetch_ta) for testing."""
    if ta_fetcher is None:
        from data import fetch_ta as ta_fetcher  # lazy: keeps engine/ta importable without yfinance
    config = AGGRESSIVE_CONFIG if aggressive else ENGINE_CONFIG
    rows: List[dict] = []
    for t in tickers:
        try:
            ta = ta_fetcher(t)
        except Exception as e:  # noqa: BLE001 — one bad ticker never stops the cycle
            rows.append({"ticker": t, "ok": False, "error": str(e)})
            continue
        if not ta:
            rows.append({"ticker": t, "ok": False, "error": "no data"})
            continue
        news = (news_by_ticker or {}).get(t)
        d = evaluate({"priceTA": ta, "news": news, "peers": None}, regime, config, aggressive)
        tg = project_targets(ta["price"], ta.get("atr14"), config)
        rows.append({"ticker": t, "ok": True, "stance": d.stance, "signal": d.signal,
                     "cc": d.confluence_count, "tier": d.tier, "price": ta["price"],
                     "prices": d.prices, "targets": tg, "exposure": exposure(t)})
    return rows


def _rng(lo: float, hi: float) -> str:
    return f"{round(lo)}-{round(hi)}"


def format_digest(rows: List[dict], regime: str, date_label: str, capex: Optional[dict] = None) -> str:
    good = [r for r in rows if r.get("ok")]
    good.sort(key=lambda r: (STANCE_ORDER[r["stance"]], r["ticker"]))
    skipped = [r["ticker"] for r in rows if not r.get("ok")]
    actionable = sum(1 for r in good if r["stance"] in ("STRONG BUY", "BUY"))
    # AVOIDs collapse to one line so a large watchlist stays phone-sized.
    shown = [r for r in good if r["stance"] != "AVOID"]
    avoid = [r["ticker"] for r in good if r["stance"] == "AVOID"]

    head = f"{'Ticker':<8}{'Signal':<7}{'AI':<5}{'Price':>6}  {'1wk':<13}1mo"
    lines = [f"📋 Morning Signals — {date_label}",
             f"Regime {regime} · {len(good)} analyzed · {actionable} actionable",
             format_capex_line(capex, [r["ticker"] for r in rows]), "", "```", head]
    for r in shown:
        t = r["targets"]
        lines.append(f"{r['ticker']:<8}{STANCE_LABEL[r['stance']]:<7}"
                     f"{TAG_SHORT.get(r.get('exposure'), '-'):<5}"
                     f"${round(r['price']):>5}  {_rng(t['week_low'], t['week_high']):<13}"
                     f"{_rng(t['month_low'], t['month_high'])}")
    lines.append("```")
    if avoid:
        lines.append(f"AVOID ({len(avoid)}): {', '.join(avoid)}")
    if skipped:
        lines.append(f"Skipped (no data): {', '.join(skipped)}")
    lines.append(f"📊 engine {ENGINE_CONFIG_VERSION} · ±ATR·√t projections · AI = capex exposure "
                 f"(SPND/SUPP/MEM/NEO/PWR) · informational only")
    return "\n".join(lines)


def format_opportunities(rows: List[dict], regime: str, date_label: str, title: str = "Opportunity Scan",
                         capex: Optional[dict] = None) -> Optional[str]:
    opps = [r for r in rows if r.get("ok") and r["stance"] != "AVOID"]
    if not opps:
        return None
    opps.sort(key=lambda r: (STANCE_ORDER[r["stance"]], r["ticker"]))
    pct = lambda v, e: f"{'+' if v >= e else '-'}{round(abs(v - e) / e * 100)}%"
    head = f"{'Ticker':<7}{'Signal':<7}{'Entry':<7}{'Stop':<6}{'Tgt':<6}"
    lines = [f"🔭 {title} — {date_label}", f"Regime {regime} · {len(opps)} found",
             format_capex_line(capex, [r["ticker"] for r in opps]), "", "```", head]
    for r in opps:
        p = r["prices"]
        lines.append(f"{r['ticker']:<7}{STANCE_LABEL[r['stance']]:<7}"
                     f"${round(p['entry']):<6}{pct(p['hard_stop'], p['entry']):<6}{pct(p['target'], p['entry']):<6}")
    lines.append("```")
    lines.append(f"📊 engine {ENGINE_CONFIG_VERSION} · informational only — you decide & execute")
    return "\n".join(lines)
