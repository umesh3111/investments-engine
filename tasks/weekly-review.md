# Task: Weekly review — Sunday 18:00 Toronto

**Goal.** The one run that steps back: how did last week's calls do, is the regime
shifting, and should any rule change — proposed, never auto-applied.

**Steps.**
1. Read the week's **Journal** rows in Notion (Market checks, scans, any trades)
   and the open **Holdings**.
2. For resolved ideas/trades, score the outcome deterministically: forward return
   vs the S&P 500 over the same window (alpha), and whether the engine's stance
   was right. Record outcome + one-line lesson on each.
3. Recompute the regime (`python3 run.py digest` prints it) and note any
   shift vs last week — including the `AI capex:` phase. In earnings season, read
   the hyperscalers' (MSFT, GOOGL, AMZN, META, ORCL) capex guidance and log a
   labeled "🤖 Capex read" in Working Notes; the engine uses reported numbers only.
4. **Propose** (do not apply) at most 3 bounded tweaks to the engine config
   (thresholds in `engine.py` / `AGGRESSIVE_CONFIG`) with the evidence for each —
   these go in **Working Notes** under "Proposed changes", awaiting the owner's go.
   Config only changes in code + git, never silently.
5. Rewrite the **Portfolio Brief** "book in ten lines".
6. Your **end-of-run message is the push notification** — a short summary:
   performance vs benchmark, regime, notable wins/misses, and any proposals
   awaiting a decision.

**Report.** Numbers first (return, alpha, win-rate), then regime, then proposals.
Judge the **process** (was the rule followed, was the reasoning sound), only then
the outcome — ~40–50% of good decisions still lose.

**Gotchas.** The aggressive profile's tuning lives here: as outcomes accumulate,
this is where we check whether its looser thresholds actually earn their keep
(expectancy, not just more signals).
