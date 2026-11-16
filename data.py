"""
Thin market-data fetch for the cloud env (yfinance — Neeraj's stack). Returns the
priceTA dict the engine expects. Runs in the claude.ai cloud env where yfinance is
installed; the heavy TA + engine logic lives in ta.py/engine.py (stdlib, tested).

Swap point: if yfinance ever throttles in the cloud too, replace fetch_bars with a
keyed API (Alpaca/Polygon) — the rest is unchanged.
"""
from __future__ import annotations
from typing import List, Optional
from ta import compute_ta


def fetch_bars(ticker: str, days: int = 400) -> List[dict]:
    """~400 calendar days (~275 trading bars) — enough for a real MA200."""
    import yfinance as yf  # imported lazily so ta/engine stay import-clean locally
    df = yf.Ticker(ticker).history(period=f"{days}d", interval="1d", auto_adjust=False)
    bars: List[dict] = []
    for row in df.itertuples():
        try:
            bars.append({
                "high": float(row.High), "low": float(row.Low),
                "close": float(row.Close), "volume": int(row.Volume or 0),
            })
        except (ValueError, TypeError):
            continue
    return bars


def fetch_ta(ticker: str, days: int = 400) -> Optional[dict]:
    bars = fetch_bars(ticker, days)
    if len(bars) < 50:  # not enough for MA50
        return None
    return compute_ta(bars)
