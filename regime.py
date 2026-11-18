"""
Market regime (port of market-regime.service) — BULLISH/NEUTRAL/DEFENSIVE/RISK_OFF
from ^GSPC/^IXIC 50-DMA position + ^VIX level/trend. The classify() rule is pure
(testable); current_regime() fetches the indices in the cloud env.
"""
from __future__ import annotations
from typing import Optional
from ta import sma

# VIX trend = VIX's own 5-day % change. VIX routinely moves 5%+ in a week, so ±10%
# separates a real move from noise. (The TS port proxied this with the Nasdaq's
# 5-day change, which is inverted — a selloff read as "FALLING" and RISK_OFF
# could never fire in one.)
VIX = {"risk_off": 28, "defensive": 22, "bullish": 18, "rising_pct": 10, "falling_pct": -10}


def classify(spy_above_50: bool, qqq_above_50: bool, vix: float, vix_trend: str) -> str:
    if vix > VIX["risk_off"] and vix_trend == "RISING":
        return "RISK_OFF"
    if vix > VIX["defensive"] or (not spy_above_50 and not qqq_above_50):
        return "DEFENSIVE"
    if spy_above_50 and qqq_above_50 and vix < VIX["bullish"]:
        return "BULLISH"
    return "NEUTRAL"


def vix_trend(vix_closes: list) -> str:
    """RISING / FALLING / FLAT from VIX's own 5-day % change."""
    if len(vix_closes) < 6 or not vix_closes[-6]:
        return "FLAT"
    chg = (vix_closes[-1] - vix_closes[-6]) / vix_closes[-6] * 100
    return "RISING" if chg > VIX["rising_pct"] else "FALLING" if chg < VIX["falling_pct"] else "FLAT"


def current_regime(fetch_closes=None, fetch_vix=None) -> dict:
    """fetch_closes(ticker)->[closes], fetch_vix()->[VIX closes] (a bare float = no trend). Injectable."""
    if fetch_closes is None or fetch_vix is None:
        import yfinance as yf
        from data import with_retry

        def fetch_closes(t):  # noqa: F811
            df = with_retry(lambda: yf.Ticker(t).history(period="90d", interval="1d"))
            return [float(c) for c in df["Close"].tolist()]

        def fetch_vix():  # noqa: F811
            df = with_retry(lambda: yf.Ticker("^VIX").history(period="15d", interval="1d"))
            return [float(c) for c in df["Close"].tolist()]

    spy = fetch_closes("^GSPC")
    qqq = fetch_closes("^IXIC")
    vix_raw = fetch_vix()
    vix_closes = [float(v) for v in vix_raw] if isinstance(vix_raw, (list, tuple)) else [float(vix_raw)]
    vix = vix_closes[-1]
    spy_above = len(spy) >= 50 and spy[-1] > (sma(spy, 50) or 0)
    qqq_above = len(qqq) >= 50 and qqq[-1] > (sma(qqq, 50) or 0)
    trend = vix_trend(vix_closes)
    regime = classify(spy_above, qqq_above, vix, trend)
    return {"regime": regime, "vix": vix, "spy_above_50": spy_above, "qqq_above_50": qqq_above, "vix_trend": trend}
