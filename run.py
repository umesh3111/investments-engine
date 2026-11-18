"""
CLI the scheduled tasks call. Computes regime, runs the deterministic engine over
a ticker set, prints the formatted message AND a JSON block the task's agent can
parse to write Notion rows.

    python3 run.py digest                 # watchlist morning table
    python3 run.py scan                   # opportunity scan over the fallback UNIVERSE
    python3 run.py scan NVDA,AVGO,VRT,...  # grade an LLM-proposed candidate list (rotating lens)
    python3 run.py aggressive NVDA,AMD,... # same, aggressive profile

Rotating-lens discovery (Neeraj's way): the scheduled task's LLM picks a lens and
proposes the candidate tickers, then passes them here as a comma-separated 3rd arg.
The engine still grades every candidate deterministically — the LLM only widens the
funnel, it never decides. With no list passed, scan/aggressive fall back to UNIVERSE.
"""
from __future__ import annotations
import sys
import os
import json
from datetime import datetime
from zoneinfo import ZoneInfo

# Resolve sibling modules regardless of the caller's working directory.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from regime import current_regime
from cycle import run_cycle, format_digest, format_opportunities

WATCHLIST = [
    "AAPL", "MSFT", "NVDA", "GOOG", "GOOGL", "META", "AMZN", "AVGO", "TSLA", "AMD",
    "NFLX", "PLTR", "UBER", "COIN", "MU", "INTC", "IBKR", "LLY", "PANW", "CRCL",
    "MSTR", "APP", "NBIS", "SNDK", "WLDN", "ADI", "CRWV", "SPCX", "SKHY",
]
# Universe "new ideas" beyond the watchlist.
UNIVERSE = [
    "QCOM", "ARM", "MRVL", "AMAT", "LRCX", "KLAC", "TSM", "ASML", "ORCL", "CRM",
    "ADBE", "NOW", "CRWD", "SPOT", "JPM", "V", "MA", "UNH", "XOM", "CVX",
    "COST", "HD", "ISRG", "VRTX", "CDNS", "SNPS", "BKNG", "ADI", "TXN", "GE",
]


def toronto_date() -> str:
    return datetime.now(ZoneInfo("America/Toronto")).strftime("%Y-%m-%d")


def parse_tickers(arg: str) -> list:
    """Split, upper-case, de-dupe (preserve order) an LLM-proposed candidate list."""
    seen, out = set(), []
    for t in arg.replace(" ", ",").split(","):
        t = t.strip().upper()
        if t and t not in seen:
            seen.add(t)
            out.append(t)
    return out


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "digest"
    reg = current_regime()
    regime, date = reg["regime"], toronto_date()
    aggressive = mode == "aggressive"

    if mode == "digest":
        tickers = WATCHLIST
    elif len(sys.argv) > 2 and sys.argv[2].strip():
        tickers = parse_tickers(sys.argv[2])  # LLM-proposed rotating-lens candidates
    else:
        tickers = UNIVERSE  # fallback when no candidate list is passed

    rows = run_cycle(tickers, regime=regime, aggressive=aggressive)

    if mode == "digest":
        msg = format_digest(rows, regime, date)
    else:
        title = "Aggressive Scan" if aggressive else "Opportunity Scan"
        msg = format_opportunities(rows, regime, date, title) or f"🔭 {title} — {date}\nNo setups above WATCH today."
    print(msg)
    print("\n<<<JSON>>>")
    print(json.dumps({"mode": mode, "regime": reg, "date": date, "rows": rows}, default=str))


if __name__ == "__main__":
    main()
