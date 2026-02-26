# MEMORY.md - Trade Algo QA Knowledge Base

**Last Updated:** 2026-02-26  
**Session:** Trade Count Standards Updated

---

## Repository Configuration

| Setting | Value |
|---------|-------|
| **Repository URL** | `https://github.com/jacky-gt/algorithmic-trading-strategies.git` |
| **Access Token** | `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` |
| **Branch** | `main` (stable), `research/*` (submissions) |

## Database Access (QA Verification)

| Setting | Value |
|---------|-------|
| **Host** | `openclaw.cjs04usueagu.ap-southeast-1.rds.amazonaws.com` |
| **Port** | `5432` |
| **Database** | `aitrading` |
| **User** | `openclaw_user` |
| **Auth** | IAM RDS Auth Token |
| **Schemas** | `silver` (raw data), `gold` (indicators), `openclaw_researcher` (backtests) |

### Key Tables for Verification
- `silver.unified_prices` — Price data (OHLCV)
- `gold.technical_indicators_calculated` — RSI, MACD, BB, etc.
- `openclaw_researcher.backtest_results` — Researcher backtest claims
- `openclaw_researcher.hypothesis_registry` — Strategy registry
- `gold.strategy_performance` — Deployed strategy metrics

### Data Coverage (as of 2026-02-26)
- **Tickers**: 204 (US: 118, HK: 50, others)
- **Date Range**: 2021-01-01 to 2026-02-25
- **Indicators**: 208 tickers with RSI, MACD, BB, Stoch, ADX

---

## QA Tools (Trade Algo QA Skill)

Custom skill for automated strategy verification.

**Location:** `/home/ubuntu/.openclaw/workspace/trade-algo-qa/skills/trade-algo-qa/`

### Quick Verification Command
```bash
cd /home/ubuntu/.openclaw/workspace/trade-algo-qa/skills/trade-algo-qa
python3 taq-verify.py \
  --strategy S001 \
  --trades 994 \
  --wr 52.3 \
  --script /path/to/backtest.py
```

### What It Checks
| Check | Description |
|-------|-------------|
| Data Availability | 204 tickers? Date range covered? |
| Database Verification | Claims match `backtest_results`? |
| Lookahead Detection | `.shift(1)` used? No same-day entry? |
| Statistical Quality | ≥100 trades? Significant win rate? |
| Market Breakdown | US/HK/CN/Crypto distribution |

### Installation
```bash
# Publish to ClawHub
clawhub publish ./trade-algo-qa --slug trade-algo-qa --version 1.0.0

# Or use locally
chmod +x taq-verify.py
./taq-verify.py --strategy S001 --trades 994 --wr 52.3
```

---

## Verification Standards

### Minimum Standards for Strategy Approval

| Metric | Threshold | Notes |
|--------|-----------|-------|
| **Expectancy** | > $0 per trade | (Win% × Avg Win) - (Loss% × Avg Loss) |
| **Profit Factor** | ≥ 1.3 | Gross Profit / Gross Loss |
| **Sharpe Ratio** | ≥ 1.0 | Risk-adjusted return (1.5+ preferred) |
| **Win Rate** | 35-70% | Outside range = overfit warning |
| **Max Drawdown** | ≤ 20% | Worst peak-to-trough decline |
| **Total Trades** | ≥ 50 | Statistical significance |
| **R-Multiple** | > 1.0 | Avg Win / Avg Loss ratio |
| **Out-of-Sample** | Required | Must test on unseen period |

### Why Expectancy > Win Rate

**Win rate alone is meaningless.** A 40% win rate strategy can be highly profitable if winners are 3x larger than losers.

**Example - Strategy A (Good):**
- Win Rate: 42%
- Avg Win: $300 | Avg Loss: $100
- Expectancy: (0.42 × $300) - (0.58 × $100) = **$68/trade** ✅

**Example - Strategy B (Bad despite 72% win rate):**
- Win Rate: 72%
- Avg Win: $50 | Avg Loss: $120
- Expectancy: (0.72 × $50) - (0.28 × $120) = **-$3.60/trade** ❌

### Evidence Requirements (Must Be in PR + RDS)

**GitHub PR Comment Must Include:**
```markdown
| Metric | Value | Threshold | Status |
|--------|-------|-----------|--------|
| Expectancy | $X.XX | > $0 | ✅/❌ |
| Profit Factor | X.XX | ≥ 1.3 | ✅/❌ |
| Sharpe Ratio | X.XX | ≥ 1.0 | ✅/❌ |
| Win Rate | XX% | 35-70% | ✅/❌ |
| Max DD | XX% | ≤ 20% | ✅/❌ |
| Trades | XXX | ≥ 50 | ✅/❌ |
| R-Multiple | X.XX | > 1.0 | ✅/❌ |

**Trade Distribution:**
- Avg Win: $XXX | Avg Loss: $XXX
| Max Win | $XXX | Max Loss | $XXX |
| Median Win | $XXX | Median Loss | $XXX |
```

**RDS Table Requirements:**
- All metrics stored in `backtest_results` table
- Trade-level data in `trade_history` table
- Out-of-sample results clearly flagged
- Decay analysis across Train/Test/Validate

### Statistical Significance Standards (Updated 2026-02-26)

**Minimum Trades by Strategy Type:**

| Strategy Type | Minimum/Year | Target/Year | Multi-Year Alternative |
|---------------|--------------|-------------|------------------------|
| **Sector-Specific** | 30 | 50 | 60 total over 2+ years |
| **Market-Level** | 50 | 100 | N/A — should generate signals |
| **Multi-Asset** | 75 | 150 | N/A — diversified universe |

**Confidence Interval Guidelines:**
| CI Width | Verdict | Action |
|----------|---------|--------|
| < 20% | ✅ Robust | Approve for deployment |
| 20-28% | 🟡 Acceptable | Deploy with caution |
| 28-35% | ⚠️ Marginal | Require longer track record |
| > 35% | ❌ Insufficient | Reject — results could be luck |

**Example:** 20 trades/year at 55% WR → CI: 33%-77% (44% width) = **REJECTED**
**Example:** 50 trades/year at 55% WR → CI: 41%-69% (28% width) = **ACCEPTABLE**

### Transaction Cost Assumptions (Minimum)

| Asset Class | Slippage + Fees |
|-------------|-----------------|
| US Equities (Large Cap) | 0.05% per side |
| US Equities (Small Cap) | 0.10% per side |
| Crypto (Liquid) | 0.10% per side |
| Crypto (Illiquid) | 0.25% per side |
| FX (Major Pairs) | 0.03% per side |
| FX (Exotic) | 0.15% per side |

### Data Quality Checks

- **No future data** in signals
- **No interpolated prices** during market halts
- **Survivorship bias addressed** (delisted tickers included)
- **Corporate actions adjusted** (splits, dividends)
- **Timezone consistency** (all timestamps in UTC or market local)

---

## 🔄 QA HANDOFF PROTOCOL

### Researcher → QA (Submission)

When Researcher submits a strategy:

1. **Receive notification via sessions_send**
   ```
   Source: agent:trade_algo_researcher:telegram:group:-5175536290
   
   Expect:
   - PR link
   - Strategy name/ID
   - Claimed metrics (Sharpe, CAGR, Max DD, Win Rate, N Trades)
   - Data range tested
   ```

2. **Pull and verify independently**
   - Clone/checkout the PR branch
   - Reproduce backtest with fresh data
   - Do NOT trust researcher's numbers

3. **Run full verification checklist**
   - See "Verification Procedures" section below
   - Document all findings

### QA → Researcher (Verdict) — HYBRID WORKFLOW

**Step 1: Post to GitHub PR as comment (Source of Truth)**

Use the GitHub API to post a detailed comment on the PR:

```bash
# Example using gh CLI or API
gh pr comment <PR_NUMBER> --body "<VERDICT_TEXT>"
```

**APPROVED Template:**
```markdown
## 🔍 QA Verification Result — ✅ APPROVED

### Core Metrics Verification

| Metric | Claimed | Verified | Threshold | Status |
|--------|---------|----------|-----------|--------|
| **Expectancy** | $X.XX | $X.XX | > $0 | ✅ |
| **Profit Factor** | X.XX | X.XX | ≥ 1.3 | ✅ |
| **Sharpe Ratio** | X.XX | X.XX | ≥ 1.0 | ✅ |
| **Win Rate** | XX% | XX% | 35-70% | ✅ |
| **R-Multiple** | X.XX | X.XX | > 1.0 | ✅ |
| **Max Drawdown** | XX% | X.X% | ≤ 20% | ✅ |
| **Total Trades** | XXX | XXX | ≥ 50 | ✅ |

### Trade Distribution (Verified)

| Statistic | Value |
|-----------|-------|
| Avg Win | $XXX |
| Avg Loss | $XXX |
| Expectancy | $X.XX |

**Expectancy Check:** (XX% × $XXX) - (XX% × $XXX) = **$X.XX** ✅

### Validation Evidence (3-Tier)

| Period | Sharpe | Profit Factor | Expectancy |
|--------|--------|---------------|------------|
| Train (2021-22) | X.XX | X.XX | $X.XX |
| Test (2023-24) | X.XX | X.XX | $X.XX |
| Validate (2025+) | X.XX | X.XX | $X.XX |
| **Decay** | X.X% | X.X% | X.X% |

**Decay Threshold:** <20% ✅

### RDS Verification

✅ `backtest_results.strategy_id = [ID]` — **VERIFIED**  
✅ `trade_history.strategy_id = [ID]` — **VERIFIED**

### Summary

**Data Range:** YYYY-MM to YYYY-MM  
**Issues Found:** None / Minor (see below)  
**Recommendation:** ✅ **APPROVED for paper trading**

---
*Verified by: Trade Algo QA Agent 🔍*  
*Timestamp: YYYY-MM-DD HH:MM UTC*
```

**REJECTED Template:**
```markdown
## 🔍 QA Verification Result — ❌ REJECTED

### Core Metrics Verification

| Metric | Claimed | Verified | Threshold | Status |
|--------|---------|----------|-----------|--------|
| **Expectancy** | $X.XX | $X.XX | > $0 | ❌ |
| **Profit Factor** | X.XX | X.XX | ≥ 1.3 | ❌ |
| **Sharpe Ratio** | X.XX | X.XX | ≥ 1.0 | ❌ |
| **Win Rate** | XX% | XX% | 35-70% | ❌ |
| **R-Multiple** | X.XX | X.XX | > 1.0 | ❌ |
| **Max Drawdown** | XX% | X.X% | ≤ 20% | ❌ |
| **Total Trades** | XXX | XXX | ≥ 50 | ❌ |

### Critical Issues

1. **Expectancy ≤ $0** — Strategy loses money per trade despite XX% win rate
   - Calculation: (XX% × $XXX) - (XX% × $XXX) = **-$X.XX/trade**
   - Issue: Avg loss ($XXX) too large relative to avg win ($XXX)
   - Fix required: Redesign risk/reward ratio

2. **[Other issues as needed]**

### Required Actions
- [ ] Fix expectancy calculation (must be > $0)
- [ ] Re-run backtest on full universe
- [ ] Re-submit with updated metrics

---
*Verified by: Trade Algo QA Agent 🔍*  
*Timestamp: YYYY-MM-DD HH:MM UTC*
```

**Step 2: Notify Researcher via Chat (sessions_send)**

Send a brief notification to the Researcher Telegram group:

**APPROVED Notification:**
```
✅ PR #X VERIFIED — Strategy: [Name]

GitHub Comment: [link to PR comment]
Status: APPROVED for paper trading
Next: You can proceed to deploy
```

**REJECTED Notification:**
```
❌ PR #X REJECTED — Strategy: [Name]

GitHub Comment: [link to PR comment]
Critical Issues: [number]
Required: Fixes before re-submission

Reply here if you need clarification on any issue.
```

**Step 3: Quick Clarifications (Chat Only)**

For back-and-forth discussion:
- Use **chat** for quick questions ("Can you explain line 45?")
- Do NOT post every clarification to GitHub
- Update GitHub PR comment only if conclusion changes verdict

### Communication Channel Guide

| Situation | Channel |
|-----------|---------|
| Verdict post (APPROVED/REJECTED) | **Both** — GitHub PR + Chat |
| Line-specific code issues | GitHub PR comment |
| Quick clarification questions | Chat (Telegram) |
| "Fix this and resubmit" | GitHub PR comment |
| Urgent/blocking issues | Chat (immediate notification) |
| Final approval after fixes | GitHub PR comment + Chat |

### Escalation to Jacky

Escalate if:
- Researcher disputes rejection without fixing issues
- Evidence of intentional gaming/faking
- Borderline case you're uncertain about
- Process deadlock

Use: Direct message to Jacky

---

## Common Researcher Shortcuts (Watch List)

### High-Frequency Offenses
1. **In-sample optimization** — Tuning on test data
2. **Lookahead bias** — Using future information
3. **Ignoring transaction costs** — Makes everything look profitable
4. **Cherry-picked timeframes** — Only showing bull markets
5. **Unverified backtest claims** — Claiming results not in database

### Verification Red Flags
- Claims metrics but no database records
- Win rates > 60% without market regime breakdown
- Sharpe ratios > 2.0 on < 100 trades
- No out-of-sample period
- Missing backtest scripts

### Database Verification Protocol
1. Check `openclaw_researcher.backtest_results` for claimed strategy
2. Verify `total_trades`, `win_rate_pct`, `sharpe_ratio` match claims
3. Cross-reference dates with `silver.unified_prices` availability
4. Reproduce 10-20 sample trades to verify logic

### Medium-Frequency Offenses
5. **Insufficient sample size** — 10 trades = not a strategy
6. **No out-of-sample test** — Overfit to noise
7. **Missing edge cases** — Gaps, halts, circuit breakers
8. **Unrealistic fills** — Assuming VWAP execution

### Low-Frequency but Critical
9. **Data snooping** — Testing 100 variants, reporting best
10. **Regime change blindness** — Strategy works 2010-2021, dies 2022+

---

## Verification Procedures

### Step 1: Code Review
- [ ] Logic matches stated hypothesis
- [ ] No hardcoded magic numbers
- [ ] Proper error handling
- [ ] Clear comments and documentation

### Step 2: Data Audit
- [ ] Date range matches claims
- [ ] No missing data in critical periods
- [ ] Adjusted prices (splits/dividends)
- [ ] Correct ticker universe

### Step 3: Backtest Reproduction
- [ ] Reproduce claimed results independently
- [ ] Verify all trades are executable
- [ ] Check signal timing (no lookahead)
- [ ] Validate position sizing logic

### Step 4: Robustness Tests
- [ ] Parameter sensitivity analysis
- [ ] Walk-forward validation
- [ ] Monte Carlo simulation (if applicable)
- [ ] Different market regimes

---

## Audit Trail Template

```markdown
## Audit: [Strategy ID] - [Date]

### Submitted By
Algo Research Agent

### Claims
- Sharpe: X.XX
- CAGR: XX%
- Max DD: XX%
- N Trades: XXX

### Verification Results
| Metric | Claimed | Verified | Status |
|--------|---------|----------|--------|
| Sharpe | X.XX | X.XX | ✅/❌ |
| CAGR | XX% | XX% | ✅/❌ |
| Max DD | XX% | XX% | ✅/❌ |

### Issues Found
1. [Description + severity + fix required]

### Recommendation
APPROVED / REJECTED / NEEDS_REVISION

### Next Steps
[Actions required]
```

---

## Researcher Pattern Tracking

**Started:** 2026-02-25  
**Purpose:** Identify systematic issues for process improvement

| Pattern | Frequency | Last Seen | Action |
|---------|-----------|-----------|--------|
| (To be populated) | | | |

---

## Escalation Log

| Date | Issue | Resolution |
|------|-------|------------|
| (To be populated) | | |

---

## Open Questions

1. What is the minimum acceptable out-of-sample period? (Suggest: 1 year)
2. How to handle strategies with high Sharpe but low trade frequency?
3. Should we require walk-forward validation for all strategies?

---

*This document evolves. Update it as standards tighten and new shortcuts are discovered.*
