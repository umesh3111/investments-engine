"""
Thin market-data fetch for the cloud env (yfinance — Neeraj's stack). Returns the
priceTA dict the engine expects. Runs in the claude.ai cloud env where yfinance is
installed; the heavy TA + engine logic lives in ta.py/engine.py (stdlib, tested).

Swap point: if yfinance ever throttles in the cloud too, replace fetch_bars with a
keyed API (Alpaca/Polygon) — the rest is unchanged.
"""
from __future__ import annotations
import time
from typing import List, Optional
from ta import compute_ta

RETRY_DELAYS = (2, 5, 10)  # seconds between attempts — rides out Yahoo 429 throttling


def _empty(result) -> bool:
    return result is None or getattr(result, "empty", False)


def with_retry(fn, delays=RETRY_DELAYS, sleep=time.sleep):
    """Call fn(); on an exception (e.g. 429) or an empty frame, back off and retry.
    Returns the last result (possibly empty) — a genuinely bad ticker still ends as
    'no data' after the retries; only the final exception is re-raised."""
    for i in range(len(delays) + 1):
        try:
            result = fn()
            if not _empty(result) or i == len(delays):
                return result
        except Exception:  # noqa: BLE001
            if i == len(delays):
                raise
        sleep(delays[i])


def fetch_bars(ticker: str, days: int = 400) -> List[dict]:
    """~400 calendar days (~275 trading bars) — enough for a real MA200."""
    import yfinance as yf  # imported lazily so ta/engine stay import-clean locally
    df = with_retry(lambda: yf.Ticker(ticker).history(period=f"{days}d", interval="1d", auto_adjust=False))
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
