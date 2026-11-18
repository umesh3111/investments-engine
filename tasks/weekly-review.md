# Task: Weekly review — Sunday 18:00 Toronto

**Goal.** The one run that steps back: how did last week's calls **and your actual
trades** do, is the regime shifting, what should change in the book, and should any
rule change. Like Neeraj's Weekly review, it is **the only run that proposes adding,
trimming, selling or rebalancing** — as Journal Trade rows for the owner's go/no-go.
Proposals are never executed by us.

**Steps.**
1. Run `python3 run.py holdings` for the fresh book (IBKR, read-only) and read the
   week's **Journal** rows (Market checks, scans, Trade rows) and **Holdings**.
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
5. **Book proposals (the core of this run).** From the holdings JSON, propose at
   most 3 trades, each grounded in an engine output — a SELL/TRIM/ADD `view`, a
   ratcheted stop, an earnings flag, or concentration (e.g. AI-capex exposure % of
   NAV while the `AI capex:` phase is DECELERATING/STRETCHED, or one name > 20% of
   NAV). For each, create a Journal **Trade** row: Action, Ticker, Qty, Price
   (current), Go No-Go = **Pending**, Executed = unchecked, Engine view, Review due =
   +21 days. Body (Neeraj's format): the case in three reasons, the main risk, what
   happens on a no, then `## Log`. The Market check marks it Executed when the fill
   shows up in IBKR. No proposal is a fine outcome — say why.
6. **Trade reviews:** for Trade rows past Review due without an outcome, write
   `## Outcome` (return since the trade vs S&P 500 over the same window) and
   `## Lesson`. Note whether the trade followed the Engine view at the time.
7. Rewrite the **Portfolio Brief** "book in ten lines" — NAV, cash %, top weights,
   AI-capex exposure, open SELL/TRIM views, pending proposals.
8. Your **end-of-run message is the push notification** — a short summary:
   performance vs benchmark, regime, notable wins/misses, and the trade proposals
   awaiting your go/no-go (reply in Notion: set Go No-Go). Informational only — you
   decide & execute.

**Report.** Numbers first (return, alpha, win-rate), then regime, then proposals.
Judge the **process** (was the rule followed, was the reasoning sound), only then
the outcome — ~40–50% of good decisions still lose.

**Gotchas.** The aggressive profile's tuning lives here: as outcomes accumulate,
this is where we check whether its looser thresholds actually earn their keep
(expectancy, not just more signals).
