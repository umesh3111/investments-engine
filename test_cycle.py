"""Verify run_cycle + digest/opportunity formatting end-to-end with mock data (no yfinance)."""
import math
from ta import compute_ta
from cycle import run_cycle, format_digest, format_opportunities


def bars(seed: float, pullback: bool):
    out = []
    for i in range(260):
        c = 100 + i * 0.35 * seed + 3 * math.sin(i / 7.0) + (-6 if pullback and i > 252 else 0)
        out.append({"high": c + 1.2, "low": c - 1.2, "close": c, "volume": 1_000_000 + (i % 5) * 50_000})
    return out


# Different shapes -> different stances
PROFILES = {
    "AAA": bars(1.0, True),    # uptrend + pullback
    "BBB": bars(1.0, False),   # steady uptrend
    "CCC": bars(0.2, True),    # flattish
    "DDD": bars(-0.3, False),  # downtrend
}
NEWS = {"AAA": {"score": 6}, "BBB": {"score": 7}, "CCC": {"score": 2}, "DDD": {"score": 1}}


def mock_fetch(ticker):
    if ticker == "ZZZ":  # simulate a no-data ticker
        return None
    return compute_ta(PROFILES[ticker])


def main():
    tickers = ["AAA", "BBB", "CCC", "DDD", "ZZZ"]
    rows = run_cycle(tickers, regime="BULLISH", news_by_ticker=NEWS, ta_fetcher=mock_fetch)
    ok = [r for r in rows if r.get("ok")]
    assert len(ok) == 4 and any(not r.get("ok") for r in rows), rows

    digest = format_digest(rows, "BULLISH", "2026-11-05")
    print(digest)
    assert "Morning Signals" in digest and "Skipped (no data): ZZZ" in digest

    print("\n" + "-" * 40 + "\n")
    opps = format_opportunities(rows, "BULLISH", "2026-11-05", "S&P Test Scan")
    print(opps if opps else "(no opportunities)")

    print("\nCycle + formatting works end-to-end (mock data, no yfinance).")


if __name__ == "__main__":
    main()
