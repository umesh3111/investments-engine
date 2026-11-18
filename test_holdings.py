"""IBKR Flex parsing/fetch + holdings position rules (mock data, no network)."""
import math
from datetime import date, timedelta
import ibkr
from ibkr import parse_statement, fetch_statement, FlexError
from holdings import position_history, evaluate_position, run_holdings, format_holdings

FLEX = """<FlexQueryResponse queryName="book" type="AF">
 <FlexStatements count="1">
  <FlexStatement accountId="U1234567" fromDate="20251118" toDate="20261117">
   <AccountInformation accountId="U1234567" currency="CAD"/>
   <EquitySummaryInBase>
    <EquitySummaryByReportDateInBase reportDate="20261116" cash="10000" total="100000"/>
    <EquitySummaryByReportDateInBase reportDate="20261117" cash="12000" total="101000"/>
   </EquitySummaryInBase>
   <CashReport><CashReportCurrency currency="BASE_SUMMARY" endingCash="12000"/></CashReport>
   <OpenPositions>
    <OpenPosition levelOfDetail="SUMMARY" symbol="NVDA" assetCategory="STK" currency="USD" position="100"
      markPrice="180" costBasisPrice="150" costBasisMoney="15000" positionValue="18000"
      fifoPnlUnrealized="3000" percentOfNAV="24.5" fxRateToBase="1.38"/>
    <OpenPosition levelOfDetail="LOT" symbol="NVDA" assetCategory="STK" currency="USD" position="60"/>
    <OpenPosition levelOfDetail="SUMMARY" symbol="BRK B" assetCategory="STK" currency="USD" position="10"
      markPrice="580" costBasisPrice="500" percentOfNAV="7.9"/>
    <OpenPosition levelOfDetail="SUMMARY" symbol="RY" assetCategory="STK" currency="CAD" position="50"
      markPrice="200" costBasisPrice="180" percentOfNAV="9.9"/>
   </OpenPositions>
   <Trades>
    <Trade levelOfDetail="EXECUTION" tradeID="9001" symbol="NVDA" assetCategory="STK" currency="USD"
      tradeDate="20260601" buySell="BUY" quantity="60" tradePrice="140"/>
    <Trade levelOfDetail="EXECUTION" tradeID="9002" symbol="NVDA" assetCategory="STK" currency="USD"
      tradeDate="20260801" buySell="BUY" quantity="60" tradePrice="160"/>
    <Trade levelOfDetail="EXECUTION" tradeID="9003" symbol="NVDA" assetCategory="STK" currency="USD"
      tradeDate="20261113" buySell="SELL" quantity="-20" tradePrice="185" fifoPnlRealized="700"/>
    <Trade levelOfDetail="ORDER" tradeID="9003" symbol="NVDA" assetCategory="STK" buySell="SELL" quantity="-20"/>
   </Trades>
  </FlexStatement>
 </FlexStatements>
</FlexQueryResponse>"""


def bars(path, start=date(2026, 1, 1)):
    """path: list of closes -> dated bars."""
    return [{"date": (start + timedelta(days=i)).isoformat(), "high": c * 1.01, "low": c * 0.99,
             "close": c, "volume": 1_000_000} for i, c in enumerate(path)]


def trend(n, a, b, wiggle=0.0):
    return [a + (b - a) * i / (n - 1) + wiggle * math.sin(i / 3) for i in range(n)]


def main():
    # ── parse ──
    st = parse_statement(FLEX)
    tick = [p["ticker"] for p in st["positions"]]
    assert tick == ["NVDA", "BRK-B"], tick                    # LOT row dropped, "BRK B" -> BRK-B, CAD excluded
    assert [p["ticker"] for p in st["other_positions"]] == ["RY"]
    assert len(st["trades"]) == 3 and st["trades"][-1]["side"] == "SELL" and st["trades"][-1]["qty"] == 20
    assert st["trades"][0]["date"] == "2026-06-01"
    assert st["nav"] == 101000 and st["nav_change_pct"] == 1.0 and st["cash"] == 12000
    assert st["base_currency"] == "CAD" and st["as_of"] == "2026-11-17"

    # ── trade history walk: entry 06-01, one add, one trim ──
    h = position_history(st["trades"], 100)
    assert h == {"entry_date": "2026-06-01", "adds": 1, "trims": 1}, h
    assert position_history([], 10) == {"entry_date": None, "adds": 0, "trims": 0}

    pos = st["positions"][0]  # NVDA, cost 150
    # SELL: price collapses below the hard stop (cost·0.90 = 135 floor or cost-2ATR)
    sell = evaluate_position(pos, bars(trend(260, 170, 120)), "NEUTRAL", h)
    assert sell["view"] == "SELL" and "Stop hit" in sell["line"], sell

    # Ratchet: peaked +30% since entry, now +10% -> stop raised to cost·1.15 = 172.5 -> SELL (gave back gains)
    path = trend(150, 140, 195) + trend(110, 195, 165)
    rat = evaluate_position(pos, bars(path), "NEUTRAL", h)
    assert rat["stop"] == 172.5 and rat["view"] == "SELL", rat

    # TRIM: steady climb far above cost, no trims yet
    h0 = {"entry_date": "2026-01-01", "adds": 0, "trims": 0}
    up = evaluate_position({**pos, "avg_cost": 100}, bars(trend(260, 100, 160, 0.5)), "BULLISH", h0)
    assert up["view"] == "TRIM", up

    # WATCH: engine AVOID and down 7%, still above the stop (wide daily ranges -> ATR ~7 -> stop at the 10% floor)
    wide = [{**x, "high": x["close"] * 1.04, "low": x["close"] * 0.96} for x in bars(trend(260, 110, 93))]
    dn = evaluate_position({**pos, "avg_cost": 100}, wide, "DEFENSIVE",
                           {"entry_date": None, "adds": 0, "trims": 0})
    assert dn["view"] == "WATCH" and "Thesis check" in dn["line"] and dn["stop"] == 90.0, dn

    # Earnings flag
    e = evaluate_position(pos, bars(trend(260, 140, 160, 1)), "NEUTRAL", h, earnings_in_days=3)
    assert "earnings in 3d" in e["flags"], e

    # ── run_holdings end-to-end with injected fetchers ──
    def fb(t):
        return bars(trend(260, 120, 181, 1)) if t == "NVDA" else []
    res = run_holdings(st, "NEUTRAL", bars_fetcher=fb, earnings_fetcher=lambda t: None, today=date(2026, 11, 18))
    assert [r["ok"] for r in res["rows"]].count(True) == 1 and res["rows"][-1]["ticker"] == "BRK-B"
    assert res["ai_exposure_pct"] == {"SUPPLIER": 24.5}, res["ai_exposure_pct"]
    assert [t["trade_id"] for t in res["recent_trades"]] == ["9003"]
    msg = format_holdings(res, {"phase": "DECELERATING", "stretched": True}, "2026-11-18")
    print(msg)
    assert "NAV CAD 101,000 (+1.0% d)" in msg and "AI-capex exposed: 24% of NAV" in msg
    assert "Non-US (not graded): RY" in msg and "No price data: BRK-B" in msg and "SELL 20 NVDA" in msg

    # ── fetch: SendRequest -> in-progress -> statement; token never leaks into errors ──
    calls = []
    def http(url):
        calls.append(url)
        if "SendRequest" in url:
            return "<FlexStatementResponse><Status>Success</Status><ReferenceCode>42</ReferenceCode>" \
                   "<Url>https://x/GetStatement</Url></FlexStatementResponse>"
        if len(calls) == 2:
            return "<FlexStatementResponse><Status>Warn</Status><ErrorCode>1019</ErrorCode>" \
                   "<ErrorMessage>Statement generation in progress</ErrorMessage></FlexStatementResponse>"
        return FLEX
    out = fetch_statement("SECRET", "123", http_get=http, sleep=lambda s: None)
    assert out == FLEX and len(calls) == 3 and "q=42" in calls[-1]

    def bad(url):
        return "<FlexStatementResponse><Status>Fail</Status><ErrorCode>1012</ErrorCode>" \
               "<ErrorMessage>Token has expired.</ErrorMessage></FlexStatementResponse>"
    try:
        fetch_statement("SECRET", "123", http_get=bad, sleep=lambda s: None)
        raise AssertionError("expected FlexError")
    except FlexError as err:
        assert "1012" in str(err) and "SECRET" not in str(err)

    import os
    os.environ.pop("IBKR_FLEX_TOKEN", None)
    assert not ibkr.configured()
    print("holdings + IBKR flex ok")


if __name__ == "__main__":
    main()
