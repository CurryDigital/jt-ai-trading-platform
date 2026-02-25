# TOOLS.md - QA Agent Environment Notes

## Primary Data Sources

### GitHub Repository
- **URL:** _(to be configured)_
- **Access:** Read-only for audit trails
- **Branch:** `main` (stable), `research/*` (submissions)

### Database Access (Read-Only)
- **Purpose:** Verify researcher's data claims
- **Tables:**
  - `gold_indicators` — validated indicator data
  - `signals` — generated signals for verification
  - `backtest_results` — to cross-check claims

### Backtesting Engine
- **Path:** `/app/services/backtest_engine.py` (reference)
- **Your role:** Audit, not execute

## Verification Stack

| Tool | Purpose |
|------|---------|
| `pandas` | Data validation, calculations |
| `numpy` | Statistical checks |
| `pytest` | Test case validation |
| `git` | Code review, diff analysis |
| GitHub API | PR review, comment threads |

## Key Files to Monitor

In researcher workspace:
- `strategies/` — New strategy definitions
- `backtest_*.py` — Backtest scripts
- `JT_TECH_PACK_*.md` — Deployment packages
- `memory/` — Research logs (for context, not gospel)

## Standards References

- `docs/STATISTICAL_STANDARDS.md` (to be created)
- `docs/DATA_REQUIREMENTS.md` (reference from researcher)
