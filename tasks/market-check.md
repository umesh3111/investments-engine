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
4. Write one **Journal** row in Notion (Kind = "Market check", Date = today,
   Portfolio value / Change % if available) with the table + your read in the body,
   ending `## Log`. Update the **Portfolio Brief** "Today" line.
5. Your **end-of-run message is the push notification** — the table + your read.
   Keep it phone-sized.

**Report.** First line = regime + count actionable. Then the table, then "🤖 Read:".
Keep it mobile-first. Advisory only — end with "informational only — you decide &
execute."

**Gotchas.** Everything after `<<<JSON>>>` is for you to parse into Notion, not for
Telegram. The engine is the decision-of-record; your read is opinion layered on top.
