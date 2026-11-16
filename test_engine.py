"""Parity check: Python engine vs the known TypeScript engine outputs."""
from engine import evaluate, ENGINE_CONFIG, AGGRESSIVE_CONFIG

def approx(a, b, tol=0.01):
    return abs(a - b) <= tol

def case_nvda():
    # From the engine trace (NEUTRAL): 4/4, Tier 2, BUY, stop 170.90 / trim1 199.90 / trim2 211.50 / target 223.10
    results = {"priceTA": {"price": 182.50, "ma50": 175.0, "ma200": 140.0, "rsi14": 58.0,
                           "macd": {"histogram": 0.45}, "volume_ratio": 1.25,
                           "bollinger": {"lower": 168.0, "middle": 180.0, "upper": 192.0}, "atr14": 5.80},
               "news": {"score": 6}, "peers": {"rel_strength_5d": 1.4}}
    d = evaluate(results, "NEUTRAL")
    assert d.confluence_count == 4, d.layers
    assert d.tier == 2, d.tier
    assert d.signal == "BUY", d.reason
    assert d.stance == "STRONG BUY", d.stance
    assert approx(d.prices["hard_stop"], 170.90), d.prices
    assert approx(d.prices["trim1"], 199.90), d.prices
    assert approx(d.prices["trim2"], 211.50), d.prices
    assert approx(d.prices["target"], 223.10), d.prices
    print("NVDA  conservative: 4/4 T2 BUY STRONG BUY  stop/trim/target OK  ✓")

def case_aapl():
    # 3/4 (structure false: no ma200), Tier 2, BUY, stance BUY
    results = {"priceTA": {"price": 342.96, "ma50": 324.46, "ma200": None, "rsi14": 62.0,
                           "macd": {"histogram": 0.14}, "volume_ratio": 1.31,
                           "bollinger": {"lower": 320.0, "middle": 336.8, "upper": 352.0}, "atr14": 6.68},
               "news": {"score": 7}, "peers": {"rel_strength_5d": 1.0}}
    d = evaluate(results, "NEUTRAL")
    assert d.confluence_count == 3, d.layers
    assert d.layers["structure"] is False, d.layers
    assert d.tier == 2 and d.signal == "BUY" and d.stance == "BUY", (d.tier, d.signal, d.stance)
    print("AAPL  conservative: 3/4 T2 BUY  (structure false, no MA200)  ✓")

def case_aggressive():
    # A 2/4 name: conservative NO_TRADE/WATCH; aggressive fires BUY.
    results = {"priceTA": {"price": 100.0, "ma50": 98.0, "ma200": 110.0, "rsi14": 70.0,
                           "macd": {"histogram": -0.1}, "volume_ratio": 0.8,
                           "bollinger": {"lower": 95.0, "middle": 99.0, "upper": 105.0}, "atr14": 2.0},
               "news": {"score": 4}, "peers": {"rel_strength_5d": 0.6}}
    cons = evaluate(results, "NEUTRAL", ENGINE_CONFIG)
    aggr = evaluate(results, "NEUTRAL", AGGRESSIVE_CONFIG, aggressive=True)
    assert cons.signal == "NO_TRADE", cons.reason
    assert aggr.confluence_count >= 2 and aggr.signal == "BUY", (aggr.confluence_count, aggr.reason)
    print(f"Aggr  conservative NO_TRADE ({cons.confluence_count}/4) vs aggressive BUY ({aggr.confluence_count}/4)  ✓")

if __name__ == "__main__":
    case_nvda(); case_aapl(); case_aggressive()
    print("\nAll parity checks passed — Python engine matches the TS engine.")
