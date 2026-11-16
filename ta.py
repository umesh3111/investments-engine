"""
Pure-Python technical analysis (stdlib only) — RSI/MACD/Bollinger/SMA/ATR.

Kept dependency-light on purpose so the engine + TA run anywhere (the cloud env,
or locally for tests) without pandas-ta. Standard formulas: Wilder RSI/ATR,
EMA-based MACD(12/26/9), Bollinger(20, 2σ population).
"""
from __future__ import annotations
import statistics
from typing import List, Optional


def sma(values: List[float], period: int) -> Optional[float]:
    if len(values) < period:
        return None
    return sum(values[-period:]) / period


def _ema_series(values: List[float], period: int) -> List[float]:
    if len(values) < period:
        return []
    k = 2 / (period + 1)
    ema = [sum(values[:period]) / period]  # seed with SMA
    for v in values[period:]:
        ema.append(v * k + ema[-1] * (1 - k))
    return ema


def rsi(values: List[float], period: int = 14) -> Optional[float]:
    if len(values) <= period:
        return None
    gains, losses = [], []
    for i in range(1, len(values)):
        ch = values[i] - values[i - 1]
        gains.append(max(ch, 0.0))
        losses.append(max(-ch, 0.0))
    avg_g = sum(gains[:period]) / period
    avg_l = sum(losses[:period]) / period
    for i in range(period, len(gains)):
        avg_g = (avg_g * (period - 1) + gains[i]) / period
        avg_l = (avg_l * (period - 1) + losses[i]) / period
    if avg_l == 0:
        return 100.0
    rs = avg_g / avg_l
    return 100 - 100 / (1 + rs)


def macd_histogram(values: List[float], fast: int = 12, slow: int = 26, signal: int = 9) -> Optional[float]:
    ef = _ema_series(values, fast)
    es = _ema_series(values, slow)
    if not ef or not es:
        return None
    n = len(es)  # es is the shorter series; align ef's tail to it
    macd_line = [ef[-n + i] - es[i] for i in range(n)]
    sig = _ema_series(macd_line, signal)
    if not sig:
        return None
    return macd_line[-1] - sig[-1]


def bollinger(values: List[float], period: int = 20, stddev: float = 2.0) -> Optional[dict]:
    if len(values) < period:
        return None
    window = values[-period:]
    mid = sum(window) / period
    sd = statistics.pstdev(window)  # population σ (matches technicalindicators)
    return {"lower": mid - stddev * sd, "middle": mid, "upper": mid + stddev * sd}


def atr(highs: List[float], lows: List[float], closes: List[float], period: int = 14) -> Optional[float]:
    if len(closes) <= period:
        return None
    trs = []
    for i in range(1, len(closes)):
        trs.append(max(highs[i] - lows[i], abs(highs[i] - closes[i - 1]), abs(lows[i] - closes[i - 1])))
    atr_val = sum(trs[:period]) / period
    for i in range(period, len(trs)):
        atr_val = (atr_val * (period - 1) + trs[i]) / period
    return atr_val


def compute_ta(bars: List[dict]) -> dict:
    """bars: list of {high,low,close,volume} oldest->newest. Returns the priceTA dict the engine expects."""
    closes = [b["close"] for b in bars]
    highs = [b["high"] for b in bars]
    lows = [b["low"] for b in bars]
    vols = [b.get("volume", 0) for b in bars]
    vol_avg = sum(vols[-20:]) / 20 if len(vols) >= 20 else 0
    return {
        "price": closes[-1],
        "ma50": sma(closes, 50),
        "ma200": sma(closes, 200),
        "rsi14": rsi(closes, 14),
        "macd": {"histogram": macd_histogram(closes)},
        "volume_ratio": (vols[-1] / vol_avg) if vol_avg > 0 else 0,
        "bollinger": bollinger(closes, 20, 2),
        "atr14": atr(highs, lows, closes, 14),
    }
