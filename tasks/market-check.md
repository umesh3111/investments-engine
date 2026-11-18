# Task: Market check (morning digest) — 9:35 Toronto, weekdays

**Goal.** Give the owner one glanceable morning read of the watchlist, backed by
the deterministic engine, and log it.

**Steps.**
1. Confirm the cloud env: `python3 -c 'import yfinance'`. If it fails, note it and
   use the connectors; don't hand-type numbers.
2. Run the engine: `python3 run.py digest`. It computes the regime,
   grades every watchlist ticker (stance + ±ATR·√t weekly/monthly ranges), and
   prints the table plus a `<<<JSON>>>` block.
3. **Do not change any number or stance the engine produced.** Add, below the
   table, a 2–3 sentence *labeled* read: what the regime + the actionable names
   mean today, and the single thing worth watching. Mark it "🤖 Read:".
4. Write one **Journal** row in Notion via the Notion connector. The Journal
   data source is `collection://95d70264-3bbc-4af6-8254-9dadff206aca` (its
   database id is `7d2fac9a31754b43b596849bf7b41e66`) — create a page with
   `parent` = that `data_source_id`. Properties: Name = "Market check <date>",
   Kind = "Market check", Date = today, Regime = the engine's regime, and
   Portfolio value / Change % if available. Put the table + your read in the page
   body, ending with a `## Log` heading. Then update the **Portfolio Brief**
   "Today" line. (All IDs are also in SYSTEM.md.)
5. Your **end-of-run message is the push notification** — the table + your read.
   Keep it phone-sized.

**Report.** First line = regime + count actionable. Then the table, then "🤖 Read:".
Keep it mobile-first. Advisory only — end with "informational only — you decide &
execute."

**Gotchas.** Everything after `<<<JSON>>>` is for you to parse into Notion, not for
Telegram. The engine is the decision-of-record; your read is opinion layered on top.
