"""
IBKR portfolio feed — READ-ONLY, via the Flex Web Service.

Why Flex: it's a token + query-id HTTPS pull that works from the cloud env with no
gateway, no daily login and no 2FA. The token can only read statements — it cannot
place, modify or cancel orders, which matches the system's rule: we never trade.

Data freshness: an Activity Flex statement covers through the last business day's
close (today's fills show up on the next run). Live prices for the holdings view
come from yfinance, so P&L and rules use current prices.

Setup (owner, once, in IBKR Client Portal):
  Performance & Reports > Flex Queries > Activity Flex Query > Create
    Sections: Open Positions (Summary), Trades (Execution), Cash Report,
              Net Asset Value (NAV) in Base, Change in NAV
    Format XML · Period "Last 365 Calendar Days" · date format yyyyMMdd
  Flex Web Service Configuration > enable > generate token
Cloud env variables: IBKR_FLEX_TOKEN, IBKR_FLEX_QUERY_ID. Never print the token.

fetch_statement() does the two-step request; parse_statement() is pure (tested).
"""
from __future__ import annotations
import os
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import date, datetime
from typing import Callable, Dict, List, Optional

FLEX_BASE = "https://ndcdyn.interactivebrokers.com/AccountManagement/FlexWebService"
IN_PROGRESS_CODES = {"1001", "1004", "1005", "1006", "1007", "1008", "1009", "1018", "1019", "1021"}


class FlexError(RuntimeError):
    pass


def configured() -> bool:
    return bool(os.environ.get("IBKR_FLEX_TOKEN") and os.environ.get("IBKR_FLEX_QUERY_ID"))


def _http_get(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "investments-engine/1.0"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read().decode("utf-8", errors="replace")


def fetch_statement(token: Optional[str] = None, query_id: Optional[str] = None,
                    http_get: Callable[[str], str] = _http_get, sleep=time.sleep,
                    attempts: int = 12, wait: float = 5) -> str:
    """SendRequest -> reference code -> poll GetStatement until the XML is ready."""
    token = token or os.environ.get("IBKR_FLEX_TOKEN")
    query_id = query_id or os.environ.get("IBKR_FLEX_QUERY_ID")
    if not token or not query_id:
        raise FlexError("IBKR not configured (set IBKR_FLEX_TOKEN and IBKR_FLEX_QUERY_ID)")

    q = urllib.parse.urlencode({"t": token, "q": query_id, "v": "3"})
    resp = ET.fromstring(http_get(f"{FLEX_BASE}/SendRequest?{q}"))
    if (resp.findtext("Status") or "").strip() != "Success":
        # Message only — the URL (which carries the token) is never surfaced.
        raise FlexError(f"Flex SendRequest failed: {resp.findtext('ErrorCode')} {resp.findtext('ErrorMessage')}")
    ref = (resp.findtext("ReferenceCode") or "").strip()
    url = (resp.findtext("Url") or f"{FLEX_BASE}/GetStatement").strip()

    for _ in range(attempts):
        body = http_get(f"{url}?{urllib.parse.urlencode({'t': token, 'q': ref, 'v': '3'})}")
        root = ET.fromstring(body)
        if root.tag == "FlexQueryResponse":
            return body
        code = (root.findtext("ErrorCode") or "").strip()
        if code not in IN_PROGRESS_CODES:
            raise FlexError(f"Flex GetStatement failed: {code} {root.findtext('ErrorMessage')}")
        sleep(wait)
    raise FlexError("Flex statement still generating after retries")


def _f(v, default=None) -> Optional[float]:
    try:
        return float(v) if v not in (None, "") else default
    except ValueError:
        return default


def _d(v: Optional[str]) -> Optional[str]:
    """IBKR dates come as yyyyMMdd, yyyy-MM-dd or 'yyyyMMdd;HHmmss' -> ISO date."""
    if not v:
        return None
    v = v.split(";")[0].split(" ")[0].strip()
    for fmt in ("%Y%m%d", "%Y-%m-%d", "%m/%d/%Y"):
        try:
            return datetime.strptime(v, fmt).date().isoformat()
        except ValueError:
            continue
    return None


def _keep(el, wanted: str) -> bool:
    lvl = el.get("levelOfDetail")
    return lvl is None or lvl.upper() == wanted


def parse_statement(xml: str) -> dict:
    """Flex XML -> {account, as_of, base_currency, positions, other_positions, trades, cash, nav, nav_change_pct}.
    positions = US-listed stocks (USD, STK); everything else lands in other_positions."""
    root = ET.fromstring(xml)
    st = root.find(".//FlexStatement")
    if st is None:
        raise FlexError("No FlexStatement in response")

    positions, other = [], []
    for p in st.iter("OpenPosition"):
        if not _keep(p, "SUMMARY"):
            continue
        row = {
            "ticker": (p.get("symbol") or "").strip().replace(" ", "-"),  # BRK B -> BRK-B
            "description": p.get("description"),
            "asset": p.get("assetCategory"),
            "currency": p.get("currency"),
            "shares": _f(p.get("position"), 0.0),
            "mark_price": _f(p.get("markPrice")),
            "avg_cost": _f(p.get("costBasisPrice")),
            "cost_basis": _f(p.get("costBasisMoney")),
            "value": _f(p.get("positionValue")),
            "unrealized_pnl": _f(p.get("fifoPnlUnrealized")),
            "pct_of_nav": _f(p.get("percentOfNAV")),
            "fx_to_base": _f(p.get("fxRateToBase"), 1.0),
        }
        if not row["shares"]:
            continue
        (positions if row["asset"] == "STK" and row["currency"] == "USD" else other).append(row)

    trades = []
    for t in st.iter("Trade"):
        if not _keep(t, "EXECUTION") or t.get("assetCategory") != "STK":
            continue
        qty = _f(t.get("quantity"), 0.0)
        trades.append({
            "trade_id": t.get("tradeID") or t.get("transactionID"),
            "ticker": (t.get("symbol") or "").strip().replace(" ", "-"),
            "date": _d(t.get("tradeDate") or t.get("dateTime")),
            "side": (t.get("buySell") or ("BUY" if qty > 0 else "SELL")).upper().replace("(CA.)", ""),
            "qty": abs(qty),
            "price": _f(t.get("tradePrice")),
            "commission": _f(t.get("ibCommission")),
            "realized_pnl": _f(t.get("fifoPnlRealized")),
            "open_close": t.get("openCloseIndicator"),
            "currency": t.get("currency"),
        })
    trades.sort(key=lambda r: (r["date"] or "", r["trade_id"] or ""))

    cash = None
    for c in st.iter("CashReportCurrency"):
        if c.get("currency") == "BASE_SUMMARY":
            cash = _f(c.get("endingCash"))

    nav = nav_prev = None
    eq = [e for e in st.iter("EquitySummaryByReportDateInBase") if e.get("total")]
    eq.sort(key=lambda e: _d(e.get("reportDate")) or "")
    if eq:
        nav = _f(eq[-1].get("total"))
        if cash is None:
            cash = _f(eq[-1].get("cash"))
        if len(eq) >= 2:
            nav_prev = _f(eq[-2].get("total"))
    chg = st.find(".//ChangeInNAV")
    if nav is None and chg is not None:
        nav = _f(chg.get("endingValue"))

    return {
        "account": st.get("accountId"),
        "as_of": _d(st.get("toDate")) or date.today().isoformat(),
        "base_currency": (root.find(".//AccountInformation").get("currency")
                          if root.find(".//AccountInformation") is not None else None),
        "positions": positions,
        "other_positions": other,
        "trades": trades,
        "cash": cash,
        "nav": nav,
        "nav_change_pct": round((nav / nav_prev - 1) * 100, 2) if nav and nav_prev else None,
    }


def trades_by_ticker(trades: List[dict]) -> Dict[str, List[dict]]:
    out: Dict[str, List[dict]] = {}
    for t in trades:
        out.setdefault(t["ticker"], []).append(t)
    return out
