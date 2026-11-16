# investments-engine

US-only advisory investing engine for **Claude Code scheduled tasks**. A deterministic
Python engine (confluence → stance → prices → signal) is the decision-of-record; the
scheduled task's LLM adds a labeled, advisory-only read. **Never places trades.**

## Run
```
python3 run.py digest        # watchlist morning table
python3 run.py scan          # universe opportunity scan
python3 run.py aggressive    # universe, aggressive profile
```
Prints the push-notification message + a `<<<JSON>>>` block for Notion.

## Files
- `engine.py` `ta.py` `regime.py` `cycle.py` `data.py` `run.py` — the engine (stdlib + yfinance)
- `tasks/` — the scheduled-task prompts (market-check, opportunity-scan, aggressive-scan, weekly-review)
- `setup.sh` — cloud-env setup (installs yfinance); `project-instructions.md` — Project persona/rules
- `SYSTEM.md` — Notion database IDs
- `test_*.py` — parity/pipeline tests (`python3 test_engine.py` etc.)
