"""Verify the AI capex-cycle classifier with synthetic quarters (no yfinance)."""
from datetime import date
from capex import classify_capex, current_capex, format_capex_line, exposure

Q = [date(2025, 9, 30), date(2025, 12, 31), date(2026, 3, 31), date(2026, 6, 30), date(2026, 9, 30)]


def series(capex, ocf=None, dates=Q):
    """capex/ocf oldest -> newest, in $B."""
    ocf = ocf or [c * 1.5 for c in capex]
    return [(d, c * 1e9, o * 1e9) for d, c, o in zip(dates, capex, ocf)]


def main():
    # Accelerating: sequential growth 10% then 20%
    acc = classify_capex({"A": series([100, 105, 110, 121, 145.2])})
    assert acc["phase"] == "ACCELERATING" and not acc["stretched"], acc
    assert acc["yoy_pct"] == 45.2 and acc["qoq_pct"] == 20.0 and acc["prev_qoq_pct"] == 10.0, acc

    # Decelerating + stretched: growth 20% then 10%, capex above op. cash flow
    dec = classify_capex({"A": series([100, 110, 120, 144, 158.4], ocf=[90] * 5)})
    assert dec["phase"] == "DECELERATING" and dec["stretched"] and dec["intensity_pct"] == 176, dec

    # Contracting: YoY down
    con = classify_capex({"A": series([100, 95, 90, 85, 80])})
    assert con["phase"] == "CONTRACTING", con

    # Like-for-like: a spender missing the prior quarter is excluded from QoQ, not zeroed
    gap = [d for i, d in enumerate(series([100, 105, 110, 121, 145.2])) if i != 3]
    mixed = classify_capex({"A": series([100, 105, 110, 121, 145.2]), "B": gap})
    assert mixed["coverage"]["qoq"] == 1 and mixed["coverage"]["yoy"] == 2, mixed
    assert mixed["qoq_pct"] == 20.0, mixed

    # Different fiscal quarter-ends still align (ORCL-style Aug year)
    orcl_dates = [date(2025, 8, 31), date(2025, 11, 30), date(2026, 2, 28), date(2026, 5, 31), date(2026, 8, 31)]
    orcl = classify_capex({"O": series([100, 105, 110, 121, 145.2], dates=orcl_dates)})
    assert orcl["phase"] == "ACCELERATING" and orcl["yoy_pct"] == 45.2, orcl

    # Empty / failure paths never raise
    assert classify_capex({}) is None
    assert classify_capex({"A": []}) is None
    boom = lambda t: (_ for _ in ()).throw(RuntimeError("yahoo down"))
    assert current_capex(fetch_quarters=boom, fetch_smh=lambda: None) is None
    assert format_capex_line(None) == "AI capex: n/a"

    # Header line + exposure tags
    line = format_capex_line(dec | {"smh_above_50": False}, ["NVDA", "MU", "AAPL", "CRWV"])
    assert "DECELERATING · STRETCHED" in line and "SMH < 50d" in line and "3/4 exposed" in line, line
    assert exposure("nvda") == "SUPPLIER" and exposure("GOOG") == "SPENDER" and exposure("AAPL") is None

    print(line)
    print("capex classifier ok")


if __name__ == "__main__":
    main()
