# Task: Opportunity scan — 9:40 and 15:55 Toronto, weekdays

**Goal.** Surface genuinely new ideas beyond the watchlist — US names the engine
rates WATCH-or-better — and send them with their verdict.

**Steps.**
1. `python3 -c 'import yfinance'` to confirm the cloud env.
2. Run `python3 run.py scan`. It grades the universe (names not in the
   watchlist) and prints the opportunity table (stance + entry / stop% / target%)
   plus a `<<<JSON>>>` block. Silent-worthy if nothing clears.
3. For each opportunity, add one short labeled line of context ("🤖 why it's here")
   — the setup in plain words. **Never change the engine's stance or prices.**
4. Append any new names to the Notion **Ideas** database (Stage = "Scanned",
   Conviction from the engine, Status line = one sentence), so nothing is surfaced
   twice without reason.
5. Your **end-of-run message is the push notification** — the opportunity table.
   If zero found, say "no new setups above WATCH today" in one line (or skip).

**Report.** `🔭 Opportunity Scan` table, then your one-liners. Advisory only.

**Gotchas.** Open and close are different data — re-run each time (no same-day
reuse here). One bad ticker never stops the scan.
