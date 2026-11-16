"""
CLI the scheduled tasks call. Computes regime, runs the deterministic engine over
a ticker set, prints the formatted message AND a JSON block the task's agent can
parse to write Notion rows.

    python3 run.py digest       # watchlist morning table
    python3 run.py scan         # universe opportunity scan (new ideas)
    python3 run.py aggressive   # universe, aggressive profile

The agent then adds its forward-looking read and sends to Telegram / Notion.
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
    "AAPL", "MSFT", "NVDA", "GOOGL", "META", "AMZN", "AVGO", "TSLA", "AMD", "NFLX",
    "PLTR", "UBER", "COIN", "MU", "INTC", "IBKR", "LLY", "PANW", "CRCL", "MSTR",
    "APP", "NBIS", "SNDK", "WLDN",
]
# Universe "new ideas" beyond the watchlist.
UNIVERSE = [
    "QCOM", "ARM", "MRVL", "AMAT", "LRCX", "KLAC", "TSM", "ASML", "ORCL", "CRM",
    "ADBE", "NOW", "CRWD", "SPOT", "JPM", "V", "MA", "UNH", "XOM", "CVX",
    "COST", "HD", "ISRG", "VRTX", "CDNS", "SNPS", "BKNG", "ADI", "TXN", "GE",
]


def toronto_date() -> str:
    return datetime.now(ZoneInfo("America/Toronto")).strftime("%Y-%m-%d")


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "digest"
    reg = current_regime()
    regime, date = reg["regime"], toronto_date()
    aggressive = mode == "aggressive"
    tickers = WATCHLIST if mode == "digest" else UNIVERSE

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
