# Task: Aggressive scan (forward-looking) — 9:45 and 16:00 Toronto, weekdays

**Goal.** Be the aggressive money-maker read — more setups, forward-looking — while
staying honest and advisory. This is the one task where your judgment carries
weight *on top of* the engine.

**Steps.**
1. `python3 -c 'import yfinance'` to confirm the cloud env.
2. **Infer today's forward paradigm** yourself from recent news, macro and sector
   rotation (rate path, which sectors lead, current themes) and the engine's `AI capex:`
   line (ACCELERATING/DECELERATING/CONTRACTING, STRETCHED = capex > op. cash). From that paradigm,
   **propose ~30–50 fresh, aggressive US candidates** — higher-beta names, recent
   movers, theme leaders — that you'd want a louder lens on. US only, liquid.
   (Avoid names already in the Notion Ideas data source from the last few days:
   `collection://4be9ec83-893c-4522-998f-1acd909e59ad`, and names already held —
   Active rows in Holdings `collection://9c854975-fe10-4f78-81c4-bbec3715e721`.
   Weigh fit against the book: if it's already heavy in AI-capex names, say so.)
3. **Let the engine grade them with the aggressive profile:**
   `python3 run.py aggressive TICK1,TICK2,...` (comma-separated, no spaces). The
   aggressive profile fires on 2/4 with wider bands, so expect more names. It prints
   the table + `<<<JSON>>>`. **The engine sets the entries, stops and targets —
   keep them.** Then rank/annotate the candidates that cleared by how well they fit
   your paradigm, and flag any you'd pass on despite the engine, with why.
4. Label everything "⚡ Aggressive read" and keep it clearly separate from the
   deterministic table. Honest uncertainty allowed; no false confidence.
5. Your **end-of-run message is the push notification** — the aggressive table +
   your ranked read. End with "informational only — you decide & execute." You
   never place trades.

**Report.** `⚡ Aggressive` table (engine) + your ranked forward read beneath it,
2–5 names max, each with a one-line thesis and the one risk.

**Gotchas.** Aggressive = more marginal setups and a lower expected hit-rate — say
so when the tape is thin. The aggressive profile is still being backtest-tuned;
treat it as a louder lens, not a promise.
