"""
Market regime (port of market-regime.service) — BULLISH/NEUTRAL/DEFENSIVE/RISK_OFF
from ^GSPC/^IXIC 50-DMA position + ^VIX level/trend. The classify() rule is pure
(testable); current_regime() fetches the indices in the cloud env.
"""
from __future__ import annotations
from typing import Optional
from ta import sma

VIX = {"risk_off": 28, "defensive": 22, "bullish": 18, "rising_pct": 2, "falling_pct": -2}


def classify(spy_above_50: bool, qqq_above_50: bool, vix: float, vix_trend: str) -> str:
    if vix > VIX["risk_off"] and vix_trend == "RISING":
        return "RISK_OFF"
    if vix > VIX["defensive"] or (not spy_above_50 and not qqq_above_50):
        return "DEFENSIVE"
    if spy_above_50 and qqq_above_50 and vix < VIX["bullish"]:
        return "BULLISH"
    return "NEUTRAL"


def current_regime(fetch_closes=None, fetch_vix=None) -> dict:
    """fetch_closes(ticker)->[closes], fetch_vix()->float. Injectable for tests."""
    if fetch_closes is None or fetch_vix is None:
        import yfinance as yf

        def fetch_closes(t):  # noqa: F811
            df = yf.Ticker(t).history(period="90d", interval="1d")
            return [float(c) for c in df["Close"].tolist()]

        def fetch_vix():  # noqa: F811
            df = yf.Ticker("^VIX").history(period="10d", interval="1d")
            return float(df["Close"].iloc[-1])

    spy = fetch_closes("^GSPC")
    qqq = fetch_closes("^IXIC")
    vix = fetch_vix()
    spy_above = len(spy) >= 50 and spy[-1] > (sma(spy, 50) or 0)
    qqq_above = len(qqq) >= 50 and qqq[-1] > (sma(qqq, 50) or 0)
    # VIX trend from the Nasdaq 5-day change (proxy, matching the TS service)
    trend = "FLAT"
    if len(qqq) >= 6:
        chg = (qqq[-1] - qqq[-6]) / qqq[-6] * 100
        trend = "RISING" if chg > VIX["rising_pct"] else "FALLING" if chg < VIX["falling_pct"] else "FLAT"
    regime = classify(spy_above, qqq_above, vix, trend)
    return {"regime": regime, "vix": vix, "spy_above_50": spy_above, "qqq_above_50": qqq_above, "vix_trend": trend}
