# Task: Market check (book + morning digest) — 9:35 Toronto, weekdays

**Goal.** One glanceable morning read: **your book first** (IBKR positions graded by
the engine's position rules), then the watchlist — backed by the deterministic
engine, and logged. Mirrors Neeraj's Market check: refresh every holding and cash
row, check exit rules, log trades, one Journal row, refresh the Brief.

## Where things are
- Engine: this cloned repo — `python3 run.py holdings` and `python3 run.py digest`.
- IBKR: read-only Flex feed (cloud env vars `IBKR_FLEX_TOKEN`, `IBKR_FLEX_QUERY_ID`).
  It reflects through the **last business day's close**; prices/P&L use live quotes.
- Notion (IDs in SYSTEM.md): **Holdings** `collection://9c854975-fe10-4f78-81c4-bbec3715e721`,
  **Journal** `collection://95d70264-3bbc-4af6-8254-9dadff206aca`, Portfolio Brief page.
- Times: America/Toronto. **We never place trades** — the owner executes by hand.

## Steps
1. Confirm the cloud env: `python3 -c 'import yfinance'`. If it fails, note it and
   use the connectors; don't hand-type numbers.
2. **Book:** `python3 run.py holdings`. It prints the book block + `<<<JSON>>>`.
   If it says "not configured" or "fetch failed", say so in one line and continue —
   never ask the owner to log in mid-run.
3. **Sync Holdings** from the JSON (`rows`), one row per US position, matched on Ticker:
   Shares, Avg Price, Value, Invested (= shares × avg_cost), P&L % (`pnl_pct`),
   % of NAV, Stance (= `view`), Stance line (= `line` + flags), Engine stance,
   Stop, Trim 1, Trim 2, Target, Entry date, AI exposure, Status = Active,
   Last synced = today. Create rows for new tickers. Any Active row whose ticker
   is no longer held → Status = Exited (never delete). One Holdings row named
   "Cash (IBKR)" holds the cash value.
4. **Log fills** (`trades`) as Journal **Trade** rows, deduped on **Trade ID** (skip
   any ID already in Journal). Action: Buy (first entry) / Add / Trim (still held) /
   Sell (position closed). Ticker, Qty, Price, Realized P&L, Date = trade date,
   Executed = ✓, Engine view = that ticker's current `view` (or engine stance if no
   longer held), Review due = trade date + 21 days. If a **Pending/Go** Trade row
   already exists for the same ticker + action from the last ~10 days, update that
   row instead (Executed ✓, Go No-Go = Go, Trade ID) — it's the owner acting on a
   proposal. On the first sync (empty Journal), log only the last 30 days of fills.
5. **Watchlist:** `python3 run.py digest` — regime, capex line, the graded table.
6. **Do not change any number, stance or view the engine produced.** Add a 2–3
   sentence labeled read: "🤖 Read:" — what the book's views + regime mean today,
   any exit-rule hit (SELL/TRIM) first, and the single thing worth watching. The
   `AI capex:` line and the book's "AI-capex exposed % of NAV" are engine data —
   connect them when the book is concentrated in a decelerating cycle.
7. Write one Journal row: Name = "Market check <date>", Kind = "Market check",
   Date, Regime, Portfolio value = NAV, Change % = `nav_change_pct` / 100 (the
   property is percent-formatted). Body: book block + watchlist table + your read,
   ending with `## Log`. Update the **Portfolio Brief** "Today" line.

## How to report (the push notification)
Line 1: verdict — regime, NAV and day change, any SELL/TRIM in the book.
Then the 💼 book table and its action bullets, then the watchlist table, then
"🤖 Read:". Phone-sized; name every ticker plainly. End "informational only — you
decide & execute."

## Gotchas
- Everything after `<<<JSON>>>` is for Notion, not the notification.
- The views (SELL/TRIM/ADD/HOLD/WATCH) are rules, not orders: a stop hit means the
  pre-agreed exit rule fired. Say it plainly; the owner decides.
- Non-US positions are listed but not graded (US-only system).
- Today's fills appear on the next run (Flex covers through yesterday's close).
- Notion: create rows with their body in the same call, ≤10 per batch.
