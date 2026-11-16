"""Regime classification rules (pure, no fetch)."""
from regime import classify, current_regime


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
    print("Regime rules OK:", reg["regime"])


if __name__ == "__main__":
    main()
