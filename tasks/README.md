# Scheduled tasks (claude.ai Project)

These are the prompts for the claude.ai scheduled tasks. They keep Neeraj's shell
(Notion system-of-record, cloud Python env, Telegram, working rules) and add our
**deterministic engine** as the brain: each task runs `run.py`, which is
the decision-of-record, then the task's LLM layer adds a *labeled* forward-looking
read on top. **The LLM never changes the engine's numbers or stances.**

## Shared conventions (copy into project memory)
- **The engine decides; you advise.** `run.py` output (stance, entry/stop/trims/
  target, confluence) is authoritative and reproducible. Your job is the read, the
  narration, and writing it down — not overriding the math.
- **Advisory only.** We never place trades. Every message ends "informational only
  — you decide & execute." Orders are the owner's, by hand.
- **Where things are.** Engine + cycle: `engine-py/` in the cloud env. System of
  record: Notion (Holdings, Ideas, Agenda, Journal + Portfolio Brief, Manual).
  Messages: **claude.ai push notifications** (the task's end-of-run message —
  turn the toggle on per task). Times: America/Toronto.
- **How to run the engine.** Start a data session (`python3 -c 'import yfinance'`);
  if it imports, the cloud env is live. Then `python3 run.py <mode>` —
  it prints the formatted message and a `<<<JSON>>>` block with the full rows to
  write into Notion.
- **How to report.** Short, mobile-first. Verdict first line, numbers kept, names
  explained on first mention, honest uncertainty allowed, false confidence not.
- **Gotchas.** If yfinance throttles even in the cloud, swap `data.fetch_bars` to a
  keyed API (the only change). One bad ticker never stops a cycle (handled).

## The tasks (each pushes its own end-of-run notification)
| Task | When (Toronto) | Runs | Pushes |
|---|---|---|---|
| Market check | 9:35 weekdays | `run.py digest` | watchlist table + read |
| Opportunity scan | 9:40 + 15:55 weekdays | `run.py scan` | new ideas (WATCH+) |
| Aggressive scan | 9:45 + 16:00 weekdays | `run.py aggressive` | aggressive, forward-looking |
| Weekly review | Sun 18:00 | engine + Notion history | perf, regime, proposals |
