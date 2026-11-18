"""Regime classification rules (pure, no fetch)."""
from regime import classify, current_regime, vix_trend
from data import with_retry


def main():
    assert classify(True, True, 15.0, "FALLING") == "BULLISH"
    assert classify(True, True, 20.0, "FLAT") == "NEUTRAL"          # vix>18 so not bullish
    assert classify(False, False, 15.0, "FLAT") == "DEFENSIVE"       # both below 50dma
    assert classify(True, True, 25.0, "FLAT") == "DEFENSIVE"         # vix>22
    assert classify(True, True, 30.0, "RISING") == "RISK_OFF"        # vix>28 & rising
    assert classify(True, True, 30.0, "FLAT") == "DEFENSIVE"         # high vix but not rising
    # injectable fetchers -> no yfinance
    reg = current_regime(fetch_closes=lambda t: [100 + i for i in range(60)], fetch_vix=lambda: 14.0)
    assert reg["regime"] == "BULLISH" and reg["spy_above_50"] and reg["qqq_above_50"], reg
    assert reg["vix_trend"] == "FLAT"  # bare float -> no trend

    # VIX trend comes from VIX itself, not the Nasdaq
    assert vix_trend([20, 21, 22, 24, 26, 29]) == "RISING"     # +45%
    assert vix_trend([30, 29, 28, 27, 26, 25.6]) == "FALLING"  # -15%
    assert vix_trend([25, 26, 25, 24, 25, 25.6]) == "FLAT"     # +2.4%
    # Selloff: Nasdaq falling, VIX spiking above 28 -> RISK_OFF (the old proxy said FALLING here)
    sell = current_regime(fetch_closes=lambda t: [200 - i for i in range(60)],
                          fetch_vix=lambda: [20, 22, 24, 26, 28, 31])
    assert sell["vix_trend"] == "RISING" and sell["regime"] == "RISK_OFF", sell

    # Retry: recovers from a 429, retries empty results, gives up cleanly
    calls = {"n": 0}
    def flaky():
        calls["n"] += 1
        if calls["n"] < 3:
            raise RuntimeError("429 Too Many Requests")
        return [1, 2, 3]
    assert with_retry(flaky, sleep=lambda s: None) == [1, 2, 3] and calls["n"] == 3
    class Empty:
        empty = True
    assert with_retry(lambda: Empty(), sleep=lambda s: None).empty   # bad ticker -> stays empty
    try:
        with_retry(lambda: 1 / 0, sleep=lambda s: None)
        raise AssertionError("should re-raise after the last attempt")
    except ZeroDivisionError:
        pass
    print("Regime rules OK:", reg["regime"])


if __name__ == "__main__":
    main()
