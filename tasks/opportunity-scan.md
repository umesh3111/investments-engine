# Task: Opportunity scan (rotating lens) — 9:40 and 15:55 Toronto, weekdays

**Goal.** Surface genuinely NEW ideas from across the whole US market — not a fixed
list. You (the LLM) are the wide funnel: pick a lens, propose candidates. The
deterministic engine is the judge: it grades them. You never decide the trade, only
what to look at.

**Steps.**
1. Confirm the cloud env: `python3 -c 'import yfinance'`.
2. **Pick today's lens.** Choose ONE angle that fits the current tape (rotate it —
   don't repeat the last run's). Examples: a sector in a pullback (semis, software,
   health, energy, financials, industrials), new 52-week highs, post-earnings
   gap-ups, oversold quality, a current theme (AI infra, power/grid, GLP-1,
   cybersecurity, defense). Note the lens in one phrase.
3. **Avoid re-screening.** Read the Notion **Ideas** data source
   `collection://4be9ec83-893c-4522-998f-1acd909e59ad` for names scanned in the last
   ~5 trading days; don't propose those again. This gives the rotation — "nothing
   screened twice."
4. **Propose ~30–50 fresh US tickers** that fit the lens (large/mid-cap, liquid,
   real companies — your own knowledge; read a little news if helpful). US only, no
   funds / leveraged ETFs.
5. **Let the engine grade them:**
   `python3 run.py scan TICK1,TICK2,TICK3,...` (comma-separated, no spaces). It
   prints the opportunity table (WATCH-or-better) + a `<<<JSON>>>` block. **Do not
   change any stance or price it produces.**
6. For each name that cleared WATCH+, add one short labeled line of context
   ("🤖 why it's here"). Append the new names to the Notion **Ideas** data source
   (`collection://4be9ec83-893c-4522-998f-1acd909e59ad`): Name, Ticker, Sector,
   Stage = "Scanned", Stance + Conviction from the engine, Status line = one
   sentence, Last checked = today. Briefly note the rejects too so step 3 can skip
   them next time.
7. Your **end-of-run message is the push notification** — lead with the lens, then
   the engine's opportunity table, then your one-liners. If nothing cleared WATCH,
   say "lens <X>: no setups above WATCH today" in one line.

**Report.** `🔭 Opportunity Scan — lens: <phrase>` + the table. Advisory only.

**Gotchas.** You widen the funnel (candidates); the engine decides (grades). Open
and close are different tape — use a different lens and re-run, don't reuse the
morning's names. One bad ticker never stops the scan. Keep the candidate list to
~50 so the run stays under time limits.
