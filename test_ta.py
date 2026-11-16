"""Verify pure-Python TA computes sane values and feeds the engine end-to-end."""
import math
from ta import compute_ta
from engine import evaluate


def synth_bars(n=260):
    """Uptrend with a mild recent pullback — oldest->newest."""
    bars = []
    for i in range(n):
        trend = 100 + i * 0.35
        wobble = 3 * math.sin(i / 7.0)
        pullback = -6 if i > n - 8 else 0  # last ~week dips
        c = trend + wobble + pullback
        bars.append({"high": c + 1.2, "low": c - 1.2, "close": c, "volume": 1_000_000 + (i % 5) * 50_000})
    return bars


def main():
    ta = compute_ta(synth_bars())
    # sanity
    assert ta["ma50"] is not None and ta["ma200"] is not None, "MAs should compute with 260 bars"
    assert 0 <= ta["rsi14"] <= 100, ta["rsi14"]
    assert ta["atr14"] and ta["atr14"] > 0, ta["atr14"]
    assert ta["bollinger"]["lower"] < ta["bollinger"]["middle"] < ta["bollinger"]["upper"]
    assert ta["ma50"] > ta["ma200"], "uptrend: MA50 should exceed MA200"
    print(f"TA ok: price={ta['price']:.2f} ma50={ta['ma50']:.2f} ma200={ta['ma200']:.2f} "
          f"rsi={ta['rsi14']:.1f} macd_h={ta['macd']['histogram']:.3f} atr={ta['atr14']:.2f} "
          f"bb=[{ta['bollinger']['lower']:.1f},{ta['bollinger']['upper']:.1f}]")

    d = evaluate({"priceTA": ta, "news": {"score": 6}, "peers": {"rel_strength_5d": 1.5}}, "NEUTRAL")
    print(f"Engine: {d.signal} tier{d.tier} {d.confluence_count}/4 stance={d.stance} layers={d.layers}")
    assert d.signal in ("BUY", "NO_TRADE") and d.stance in ("STRONG BUY", "BUY", "WATCH", "AVOID")
    print("\nTA -> engine pipeline works end-to-end (no yfinance).")


if __name__ == "__main__":
    main()
