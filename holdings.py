"""
Holdings view — the engine applied to positions you actually own (IBKR, read-only).

For each US stock position: live price + TA, the engine's stance on the ticker,
and deterministic position rules ported from the TS position-manager:

    hard stop  max(cost - 2·ATR, cost · 0.90)
    ratchet    peak P&L since entry ≥8% → breakeven, ≥12% → +4%, ≥18% → +8%, ≥25% → +15%
    trims      trim1 = cost + 3·ATR, trim2 = cost + 5·ATR, target = cost + 7·ATR
    pyramid    engine BUY/STRONG BUY, no adds yet, P&L +3..+8% → ADD window
    thesis     engine AVOID → WATCH (review); AVOID and P&L ≤ -6% → flagged as thesis check
    earnings   report within 5 days → flag

The ratchet is stateless: it uses the highest close since the entry date (from the
IBKR trade history), which is equivalent to "only ever raises". ATR is today's ATR
(entry-day ATR isn't stored), so levels drift slightly with volatility.

View (Holdings "Stance"): SELL | TRIM | ADD | HOLD | WATCH — the engine's rule
output, advisory only. The owner decides and executes.
"""
from __future__ import annotations
from datetime import date, timedelta
from typing import Callable, Dict, List, Optional

from engine import evaluate, ENGINE_CONFIG
from ta import compute_ta
from capex import exposure, TAG_SHORT

RULES = {
    "stop_atr_mult": 2, "stop_floor_pct": 0.90,
    "trim1_atr_mult": 3, "trim2_atr_mult": 5, "target_atr_mult": 7,
    "ratchet": [(25, 1.15), (18, 1.08), (12, 1.04), (8, 1.00)],  # (peak pnl % ≥, stop = cost ×)
    "pyramid_pnl": (3, 8),
    "thesis_pnl": -6,
    "earnings_days": 5,
}
VIEW_ORDER = {"SELL": 0, "TRIM": 1, "ADD": 2, "WATCH": 3, "HOLD": 4}


def position_history(trades: List[dict], shares: float) -> dict:
    """Walk this ticker's trades backwards from the current share count to find the
    entry (the BUY that took it from flat) and count adds/trims since then."""
    cum = shares
    entry_idx = None
    for i in range(len(trades) - 1, -1, -1):
        t = trades[i]
        cum = cum - t["qty"] if t["side"] == "BUY" else cum + t["qty"]
        if t["side"] == "BUY" and cum <= 1e-6:
            entry_idx = i
            break
    since = trades[entry_idx + 1:] if entry_idx is not None else trades
    return {
        "entry_date": trades[entry_idx]["date"] if entry_idx is not None else None,
        "adds": sum(1 for t in since if t["side"] == "BUY"),
        "trims": sum(1 for t in since if t["side"] == "SELL"),
    }


def evaluate_position(pos: dict, bars: List[dict], regime: str, history: dict,
                      earnings_in_days: Optional[int] = None, config=ENGINE_CONFIG) -> dict:
    """Pure: one position + its bars -> view, levels and flags."""
    ta = compute_ta(bars)
    price = ta["price"]
    cost = pos["avg_cost"] or pos["mark_price"] or price
    atr = ta.get("atr14") or price * config["prices"]["atr_fallback_pct"]
    pnl = (price / cost - 1) * 100

    entry = history.get("entry_date")
    closes_since = [b["close"] for b in bars if entry and b.get("date") and b["date"] >= entry]
    peak = max(closes_since + [price]) if closes_since else price
    peak_pnl = (peak / cost - 1) * 100

    hard = max(cost - RULES["stop_atr_mult"] * atr, cost * RULES["stop_floor_pct"])
    ratchet = next((cost * m for lvl, m in RULES["ratchet"] if peak_pnl >= lvl), None)
    stop = max(hard, ratchet) if ratchet else hard
    trim1 = cost + RULES["trim1_atr_mult"] * atr
    trim2 = cost + RULES["trim2_atr_mult"] * atr
    target = cost + RULES["target_atr_mult"] * atr

    d = evaluate({"priceTA": ta, "news": None, "peers": None}, regime, config)
    flags = []
    lo, hi = RULES["pyramid_pnl"]
    if price <= stop:
        view, line = "SELL", f"Stop hit: ${price:.2f} ≤ stop ${stop:.2f}"
    elif price >= target:
        view, line = "TRIM", f"Target reached (${target:.0f}) — take profit / tighten"
    elif price >= trim2 and history["trims"] < 2:
        view, line = "TRIM", f"Trim-2 zone (≥ ${trim2:.0f})"
    elif price >= trim1 and history["trims"] < 1:
        view, line = "TRIM", f"Trim-1 zone (≥ ${trim1:.0f})"
    elif d.stance in ("STRONG BUY", "BUY") and history["adds"] == 0 and lo <= pnl <= hi:
        view, line = "ADD", f"Pyramid window: engine {d.stance}, up {pnl:.1f}%, no adds yet"
    elif d.stance == "AVOID" and pnl <= RULES["thesis_pnl"]:
        view, line = "WATCH", f"Thesis check: engine AVOID and down {abs(pnl):.1f}%"
    elif d.stance == "AVOID":
        view, line = "WATCH", "Engine AVOID on the ticker — review the thesis"
    else:
        view, line = "HOLD", f"Engine {d.stance}; stop ${stop:.2f}"
    if ratchet and stop > hard:
        flags.append(f"stop ratcheted to ${stop:.2f} (peak +{peak_pnl:.0f}%)")
    if earnings_in_days is not None and 0 <= earnings_in_days <= RULES["earnings_days"]:
        flags.append(f"earnings in {earnings_in_days}d")

    r2 = lambda v: round(v, 2)
    return {
        "ticker": pos["ticker"], "ok": True, "view": view, "line": line, "flags": flags,
        "engine_stance": d.stance, "cc": d.confluence_count,
        "shares": pos["shares"], "avg_cost": r2(cost), "price": r2(price), "pnl_pct": round(pnl, 1),
        "value": r2(price * pos["shares"]), "pct_of_nav": pos.get("pct_of_nav"),
        "stop": r2(stop), "trim1": r2(trim1), "trim2": r2(trim2), "target": r2(target),
        "entry_date": entry, "adds": history["adds"], "trims": history["trims"],
        "exposure": exposure(pos["ticker"]),
    }


def _earnings_days(ticker: str) -> Optional[int]:
    import yfinance as yf
    from data import with_retry
    cal = with_retry(lambda: yf.Ticker(ticker).calendar) or {}
    dates = cal.get("Earnings Date") if isinstance(cal, dict) else None
    if not dates:
        return None
    nxt = min(d for d in dates if d >= date.today()) if any(d >= date.today() for d in dates) else None
    return (nxt - date.today()).days if nxt else None


def run_holdings(statement: dict, regime: str, bars_fetcher: Optional[Callable] = None,
                 earnings_fetcher: Optional[Callable] = None, today: Optional[date] = None) -> dict:
    if bars_fetcher is None:
        from data import fetch_bars as bars_fetcher
    earnings_fetcher = earnings_fetcher or _earnings_days
    from ibkr import trades_by_ticker
    by_t = trades_by_ticker(statement["trades"])

    rows: List[dict] = []
    for pos in statement["positions"]:
        t = pos["ticker"]
        try:
            bars = bars_fetcher(t)
            if len(bars) < 50:
                raise ValueError("no data")
            try:
                ed = earnings_fetcher(t)
            except Exception:  # noqa: BLE001
                ed = None
            rows.append(evaluate_position(pos, bars, regime, position_history(by_t.get(t, []), pos["shares"]), ed))
        except Exception as e:  # noqa: BLE001 — one bad position never stops the run
            rows.append({"ticker": t, "ok": False, "error": str(e), "shares": pos["shares"],
                         "avg_cost": pos.get("avg_cost"), "pct_of_nav": pos.get("pct_of_nav")})
    rows.sort(key=lambda r: (VIEW_ORDER.get(r.get("view"), 9), -(r.get("pct_of_nav") or 0)))

    # Concentration: % of NAV in AI-capex-exposed names (ties the book to the capex overlay).
    exposed: Dict[str, float] = {}
    for r in rows:
        tag = exposure(r["ticker"])
        if tag and r.get("pct_of_nav") is not None:
            exposed[tag] = exposed.get(tag, 0.0) + r["pct_of_nav"]

    today = today or date.today()
    recent_cut = (today - timedelta(days=7)).isoformat()
    return {
        "account_as_of": statement["as_of"],
        "nav": statement["nav"], "nav_change_pct": statement["nav_change_pct"],
        "cash": statement["cash"], "base_currency": statement.get("base_currency"),
        "rows": rows,
        "other_positions": [p["ticker"] for p in statement["other_positions"]],
        "ai_exposure_pct": {k: round(v, 1) for k, v in exposed.items()},
        "recent_trades": [t for t in statement["trades"] if (t["date"] or "") >= recent_cut],
        "trades": statement["trades"],
    }


def format_holdings(res: dict, capex: Optional[dict], date_label: str) -> str:
    cur = res.get("base_currency") or ""
    nav = res.get("nav")
    head = f"💼 Book — {date_label}"
    if nav is not None:
        chg = res.get("nav_change_pct")
        head += f" · NAV {cur} {nav:,.0f}" + (f" ({chg:+.1f}% d)" if chg is not None else "")
    if res.get("cash") is not None and nav:
        head += f" · cash {res['cash'] / nav * 100:.0f}%"
    lines = [head]

    exp = res.get("ai_exposure_pct") or {}
    if exp:
        total = sum(exp.values())
        parts = ", ".join(f"{TAG_SHORT[k]} {v:.0f}%" for k, v in sorted(exp.items(), key=lambda x: -x[1]))
        cyc = f" · cycle {capex['phase']}{'·STRETCHED' if capex['stretched'] else ''}" if capex else ""
        lines.append(f"AI-capex exposed: {total:.0f}% of NAV ({parts}){cyc}")

    ok = [r for r in res["rows"] if r.get("ok")]
    if ok:
        lines += ["", "```", f"{'Ticker':<7}{'View':<6}{'P&L':>6}  {'Price':>6}  {'Stop':>6}"]
        for r in ok:
            lines.append(f"{r['ticker']:<7}{r['view']:<6}{r['pnl_pct']:>+5.0f}%  "
                         f"${r['price']:>5.0f}  ${r['stop']:>5.0f}")
        lines.append("```")
    act = [r for r in ok if r["view"] in ("SELL", "TRIM", "ADD") or r["flags"]]
    for r in act:
        extra = f" · {'; '.join(r['flags'])}" if r["flags"] else ""
        lines.append(f"• {r['ticker']} {r['view']}: {r['line']}{extra}")
    bad = [r["ticker"] for r in res["rows"] if not r.get("ok")]
    if bad:
        lines.append(f"No price data: {', '.join(bad)}")
    if res.get("other_positions"):
        lines.append(f"Non-US (not graded): {', '.join(res['other_positions'])}")
    if res.get("recent_trades"):
        tr = "; ".join(f"{t['side']} {t['qty']:g} {t['ticker']} @ ${t['price']:.2f} ({t['date'][5:]})"
                       for t in res["recent_trades"][-5:])
        lines.append(f"Recent fills: {tr}")
    lines.append(f"📊 IBKR as of {res['account_as_of']} · live prices · rules = stop/ratchet/trims/pyramid "
                 f"· informational only — you decide & execute")
    return "\n".join(lines)
