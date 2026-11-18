# System map — Notion IDs (claude.ai-native setup)

Workspace: **Umesh Sharma's Notion** (umesh.sh31@gmail.com). Created private (draft)
— move into a teamspace from the hub page when ready.

## Hub
- **Investments** (hub page): `41633724-e57f-81f5-b332-e6fa2cbf28f3`
  https://app.notion.com/p/41633724e57f81f5b332e6fa2cbf28f3

## Databases (use the collection:// data_source_id in the tasks)
| DB | database id | collection:// (data_source_id) |
|---|---|---|
| Holdings | `977ce6a2af6b42579519902defcf17d3` | `9c854975-fe10-4f78-81c4-bbec3715e721` |
| Ideas | `a3eee54278d64370aa972ad8fdaa0ad6` | `4be9ec83-893c-4522-998f-1acd909e59ad` |
| Agenda | `63d97428d4c24c4faec22bc5166815b1` | `4b29ef79-7097-4267-869f-a173eb063494` |
| Journal | `7d2fac9a31754b43b596849bf7b41e66` | `95d70264-3bbc-4af6-8254-9dadff206aca` |

## Pages (under the hub)
| Page | id |
|---|---|
| Manual | `41633724-e57f-8113-9211-d341d9a45dd2` |
| Portfolio Brief | `41633724-e57f-81c7-95a4-c76eaa90ab1e` |
| Working Notes | `41633724-e57f-81a3-baca-ea6b935e8085` |

## Schemas (US-only, engine-adapted)
- **Holdings** (synced from IBKR by Market check): Name, Ticker, Status(Active/Exited),
  Shares, Avg Price, Invested, Value, P&L %, % of NAV, **Stance(ADD/HOLD/TRIM/SELL/WATCH)**
  (= engine position-rule view), Stance line, Engine stance, Entry, Entry date, Stop,
  Trim 1, Trim 2, Target, AI exposure, Conviction, Last synced. Row "Cash (IBKR)" = cash.
- **Ideas**: Name, Ticker, Sector, Stage(Scanned/Researching/Buy/Wait/Drop),
  **Stance(STRONG BUY/BUY/WATCH/AVOID)**, Conviction, Status line, Price, Entry,
  Stop, Target, Last checked, Next check.
- **Agenda**: Name, Kind(Do/Read/Decide/Event), Owner(Umesh/Claude/Market), Date,
  Done, Priority.
- **Journal**: Name, Kind(Market check/Scan/Aggressive/Weekly/Trade/Research), Date,
  Regime, Portfolio value, Change %, Action, Ticker, Qty, Price, Go No-Go,
  Executed, Review due, **Trade ID** (IBKR dedupe key), Realized P&L, Engine view.

## Paste-in kit (repo)
- `engine-py/setup.sh` → cloud-env setup script
- `engine-py/project-instructions.md` → Project instructions field
- `engine-py/tasks/*.md` → the scheduled-task prompts

## Optional later
- Two-way relations (Holdings↔Ideas, Agenda→Holdings/Ideas/Journal) via
  update_data_source.
- Google Calendar (Agenda rows → events).

## IBKR (read-only Flex)
Cloud env vars: `IBKR_FLEX_TOKEN`, `IBKR_FLEX_QUERY_ID`. Activity Flex Query (XML,
Last 365 Calendar Days): Open Positions, Trades (Execution), Cash Report, NAV in Base,
Change in NAV. `python3 run.py holdings`. The token reads statements only — no orders.
