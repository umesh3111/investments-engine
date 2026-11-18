# Task: Opportunity scan (rotating lens) — mirrors Neeraj's scan

**Goal.** Surface **two to five genuinely new ideas** from across the whole US
market through a rotating lens, and record what you rejected so nothing is screened
twice. You (the LLM) are the wide funnel: pick a lens, propose candidates. The
deterministic engine is the judge: it grades them. You never decide the trade.

## Inputs (set these to your book)
- **Portfolio context:** _one sentence about the book — size, tilt, what it already
  holds, so new ideas complement rather than duplicate._
- **Risk profile:** _your risk appetite — e.g. "swing trades, 2–3 week holds, max
  one new idea per scan, avoid pre-earnings."_

## Where things are
- Engine + cycle: this cloned repo. Run with `python3 run.py ...`.
- System of record: Notion. **Ideas** data source
  `collection://4be9ec83-893c-4522-998f-1acd909e59ad` (new ideas land here).
- Times: America/Toronto. We never place trades.

## Steps
1. Confirm the cloud env: `python3 -c 'import yfinance'`.
2. **Pick today's lens.** ONE angle that fits the tape and that you did NOT use last
   run (rotate it): a sector in a pullback (semis, software, health, energy,
   financials, industrials), AI capex beneficiaries beyond chips (power, grid,
   cooling, networking — check the `AI capex:` phase first), new 52-week highs, post-earnings gap-ups, oversold
   quality, or a current theme (AI infra, power/grid, GLP-1, cybersecurity, defense).
3. **Don't re-screen.** Read the **Ideas** data source for names scanned in the last
   ~5 trading days and don't propose those again — that's the rotation.
4. **Propose ~30–50 fresh US tickers** fitting the lens (liquid large/mid-cap, real
   companies; US only, no funds / leveraged ETFs) that also fit the risk profile.
5. **Let the engine grade them:** `python3 run.py scan TICK1,TICK2,...`
   (comma-separated, no spaces). It prints the WATCH-or-better table + a `<<<JSON>>>`
   block. **Never change a stance or price it produces.**
6. From what cleared, present the **best 2–5 ideas** (not everything) — the ones that
   best fit the lens and the book. Append them to **Ideas**: Name, Ticker, Sector,
   Stage = "Scanned", Stance + Conviction from the engine, Status line = one
   sentence, Last checked = today. Briefly log the rejects so step 3 skips them.

## How to report
Your end-of-run message is the push notification. Lead: `🔭 Opportunity Scan —
lens: <phrase>`. Then the engine's table for the 2–5 ideas, each with one labeled
line ("🤖 why it's here"). Mobile-first; every ticker named plainly. If nothing
cleared: "lens <X>: no setups above WATCH today." End "informational only — you
decide & execute."

## Gotchas
- You widen the funnel (candidates); the engine decides (grades). Keep the candidate
  list ≤ ~50 so the run stays under time limits.
- One bad/thinly-traded ticker never stops the scan — it just gets skipped.
- Runs weekly (Sunday), but can be run on demand anytime. On a manual re-run, pick a
  different lens from the last one and skip recently-scanned names (step 3) so it
  keeps rotating instead of repeating.
