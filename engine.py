"""
Deterministic trading engine — Python port of src/trader/engine/*.

Runs natively in the claude.ai cloud Python env (Neeraj's setup) so the scheduled
tasks call it for reproducible, backtestable confluence / stance / price / signal
decisions instead of LLM guesswork. Dependency-light (stdlib math only); it takes
pre-computed TA values as input, so TA (RSI/MACD/BB/MA/ATR) can come from
pandas-ta in the cloud env or any source.

Kept 1:1 with the TypeScript engine (engine-1.3.0) — see test_engine.py for parity.
"""
from __future__ import annotations
import math
from dataclasses import dataclass
from typing import Optional

ENGINE_CONFIG_VERSION = "engine-1.3.0"

# ── Conservative (decision-of-record) ───────────────────────────────────────
ENGINE_CONFIG = {
    "confluence": {
        "structure": {"ma200_ratio": 0.97},
        "momentum": {"rsi_min": 40, "rsi_max": 65, "min_volume_ratio": 1.0},
        "setup": {"bb_middle_mult": 1.03},
        "catalyst": {"news_score_min": 5, "rel_strength_5d_min": 2.0},
    },
    "tier": {"regime_cap": {"BULLISH": 1, "NEUTRAL": 2, "DEFENSIVE": 2, "RISK_OFF": 3}},
    "buy_rule": {"min_confluence_for_buy": 3, "max_tier_for_alert": 2, "risk_off_requires_four": True},
    "prices": {"atr_fallback_pct": 0.025, "stop_atr_mult": 2, "stop_floor_pct": 0.9,
               "trim1_atr_mult": 3, "trim2_atr_mult": 5, "target_atr_mult": 7},
    "targets": {"week_days": 5, "month_days": 21},
}

# ── Aggressive profile (separate; looser) ───────────────────────────────────
AGGRESSIVE_CONFIG_VERSION = "aggressive-0.1.0"
AGGRESSIVE_CONFIG = {
    **ENGINE_CONFIG,
    "confluence": {
        "structure": {"ma200_ratio": 0.93},
        "momentum": {"rsi_min": 30, "rsi_max": 78, "min_volume_ratio": 0.7},
        "setup": {"bb_middle_mult": 1.12},
        "catalyst": {"news_score_min": 3, "rel_strength_5d_min": 0.5},
    },
    "tier": {"regime_cap": {"BULLISH": 1, "NEUTRAL": 1, "DEFENSIVE": 2, "RISK_OFF": 2}},
    # max_tier_for_alert = 3 so a 2/4 setup (which computes to tier 3) can actually
    # fire — otherwise min_confluence_for_buy=2 and the tier gate contradict.
    "buy_rule": {"min_confluence_for_buy": 2, "max_tier_for_alert": 3, "risk_off_requires_four": False},
}


@dataclass
class Decision:
    layers: dict
    confluence_count: int
    tier: int
    prices: dict
    signal: str          # "BUY" | "NO_TRADE"
    reason: str
    stance: str          # "STRONG BUY" | "BUY" | "WATCH" | "AVOID"


def _g(d: Optional[dict], *path, default=None):
    cur = d
    for p in path:
        if cur is None:
            return default
        cur = cur.get(p) if isinstance(cur, dict) else None
    return default if cur is None else cur


def compute_confluence_layers(ta: dict, news: Optional[dict], peers: Optional[dict], config=ENGINE_CONFIG) -> dict:
    c = config["confluence"]
    price, ma50, ma200 = ta.get("price"), ta.get("ma50"), ta.get("ma200")
    rsi = ta.get("rsi14")
    macd_h = _g(ta, "macd", "histogram", default=-1)
    vol = ta.get("volume_ratio", 0) or 0
    bb_lower = _g(ta, "bollinger", "lower")
    bb_mid = _g(ta, "bollinger", "middle")

    structure = (ma50 is not None and ma200 is not None
                 and price > ma50 and ma50 > ma200 * c["structure"]["ma200_ratio"])
    momentum = (rsi is not None
                and c["momentum"]["rsi_min"] <= rsi <= c["momentum"]["rsi_max"]
                and macd_h > 0 and vol >= c["momentum"]["min_volume_ratio"])
    setup = (bb_lower is not None and bb_mid is not None
             and price >= bb_lower and price <= bb_mid * c["setup"]["bb_middle_mult"])
    catalyst = ((_g(news, "score", default=0) >= c["catalyst"]["news_score_min"])
                or (_g(peers, "rel_strength_5d", default=0) > c["catalyst"]["rel_strength_5d_min"]))
    return {"structure": bool(structure), "momentum": bool(momentum),
            "setup": bool(setup), "catalyst": bool(catalyst)}


def assign_tier(count: int, regime: str, config=ENGINE_CONFIG) -> int:
    tier = 1 if count == 4 else 2 if count == 3 else 3
    return max(tier, config["tier"]["regime_cap"][regime])


def compute_engine_signal(count: int, tier: int, regime: str, config=ENGINE_CONFIG):
    r = config["buy_rule"]
    if regime == "RISK_OFF" and r["risk_off_requires_four"] and count < 4:
        return "NO_TRADE", f"RISK_OFF requires 4/4 confluence (have {count}/4)"
    if count < r["min_confluence_for_buy"]:
        return "NO_TRADE", f"confluence {count}/4 below {r['min_confluence_for_buy']}"
    if tier > r["max_tier_for_alert"]:
        return "NO_TRADE", f"tier {tier} below alert threshold {r['max_tier_for_alert']}"
    return "BUY", f"{count}/4 confluence, tier {tier}, {regime}"


def compute_trade_prices(price: float, atr14: Optional[float], config=ENGINE_CONFIG) -> dict:
    p = config["prices"]
    atr = atr14 if atr14 is not None else price * p["atr_fallback_pct"]
    hard_stop = max(price - p["stop_atr_mult"] * atr, price * p["stop_floor_pct"])
    rnd = lambda v: round(v, 4)
    return {"entry": rnd(price), "hard_stop": rnd(hard_stop),
            "trim1": rnd(price + p["trim1_atr_mult"] * atr),
            "trim2": rnd(price + p["trim2_atr_mult"] * atr),
            "target": rnd(price + p["target_atr_mult"] * atr)}


def project_targets(price: float, atr14: Optional[float], config=ENGINE_CONFIG) -> dict:
    t = config["targets"]
    atr = atr14 if atr14 is not None else price * config["prices"]["atr_fallback_pct"]
    wk, mo = atr * math.sqrt(t["week_days"]), atr * math.sqrt(t["month_days"])
    rnd = lambda v: round(v, 2)
    return {"week_low": rnd(price - wk), "week_high": rnd(price + wk),
            "month_low": rnd(price - mo), "month_high": rnd(price + mo)}


def compute_stance(count: int, regime: str, signal: str, aggressive: bool = False) -> str:
    if aggressive:
        stance = "STRONG BUY" if count >= 3 else "BUY" if count == 2 else "WATCH" if count == 1 else "AVOID"
    else:
        stance = "STRONG BUY" if count >= 4 else "BUY" if count == 3 else "WATCH" if count == 2 else "AVOID"
    if regime == "RISK_OFF" and stance in ("STRONG BUY", "BUY"):
        stance = "WATCH"
    if signal == "NO_TRADE" and stance == "STRONG BUY":
        stance = "BUY"
    return stance


def evaluate(results: dict, regime: str, config=ENGINE_CONFIG, aggressive: bool = False) -> Decision:
    ta = results["priceTA"]
    layers = compute_confluence_layers(ta, results.get("news"), results.get("peers"), config)
    count = sum(1 for v in layers.values() if v)
    tier = assign_tier(count, regime, config)
    prices = compute_trade_prices(ta["price"], ta.get("atr14"), config)
    signal, reason = compute_engine_signal(count, tier, regime, config)
    stance = compute_stance(count, regime, signal, aggressive)
    return Decision(layers, count, tier, prices, signal, reason, stance)
