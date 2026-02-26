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
| GitHub API/CLI | PR comments, review posts |
| `gh` CLI | Posting verdict comments to PRs |

## Posting Verdicts to GitHub PRs

### Option 1: GitHub CLI (gh)

```bash
# Install gh CLI first
gh pr comment <PR_NUMBER> --repo <OWNER/REPO> --body "<VERDICT_TEXT>"

# Example:
gh pr comment 1 --repo CurryDigital/jt-ai-trading-platform-strategy \
  --body "## 🔍 QA Verification Result — ✅ APPROVED
..."
```

### Option 2: GitHub API (curl)

```bash
curl -X POST \
  -H "Authorization: token <GITHUB_TOKEN>" \
  -H "Accept: application/vnd.github.v3+json" \
  https://api.github.com/repos/<OWNER/REPO>/issues/<PR_NUMBER>/comments \
  -d '{"body":"## 🔍 QA Verification Result..."}'
```

### Repository Details

- **Owner:** `CurryDigital`
- **Repo:** `jt-ai-trading-platform-strategy`
- **Base URL:** `https://github.com/CurryDigital/jt-ai-trading-platform-strategy`

## Key Files to Monitor

In researcher workspace:
- `strategies/` — New strategy definitions
- `backtest_*.py` — Backtest scripts
- `JT_TECH_PACK_*.md` — Deployment packages
- `memory/` — Research logs (for context, not gospel)

## Standards References

- `docs/STATISTICAL_STANDARDS.md` (to be created)
- `docs/DATA_REQUIREMENTS.md` (reference from researcher)

---

## Agent-to-Agent Communication

### Researcher Agent Target

To send messages to the Researcher agent:

```json
{
  "sessionKey": "agent:trade_algo_researcher:telegram:group:-5175536290"
}
```

**Usage:**
- Issue verification verdicts (APPROVED/REJECTED)
- Request clarification on submissions
- Escalate to Jacky if needed

### Protocol

See `MEMORY.md` → "QA Handoff Protocol" for full workflow.

---
