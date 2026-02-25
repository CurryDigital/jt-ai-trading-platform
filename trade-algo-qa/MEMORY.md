# MEMORY.md - Trade Algo QA Knowledge Base

**Last Updated:** 2026-02-25  
**Session:** Workspace Initialization

---

## Repository Configuration

| Setting | Value |
|---------|-------|
| **Repository URL** | `https://github.com/jacky-gt/algorithmic-trading-strategies.git` |
| **Access Token** | `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` |
| **Branch** | `main` (stable), `research/*` (submissions) |

---

## Verification Standards

### Minimum Standards for Strategy Approval

| Metric | Threshold | Notes |
|--------|-----------|-------|
| Sharpe Ratio | ≥ 1.0 | Risk-adjusted return (1.5+ preferred) |
| Max Drawdown | ≤ 20% | Worst peak-to-trough decline |
| Total Trades | ≥ 50 | Statistical significance |
| Win Rate | 35-65% | Outside this range = overfit warning |
| Profit Factor | ≥ 1.3 | Gross profit / gross loss |
| Out-of-Sample | Required | Must test on unseen period |

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

## Common Researcher Shortcuts (Watch List)

### High-Frequency Offenses
1. **In-sample optimization** — Tuning on test data
2. **Lookahead bias** — Using future information
3. **Ignoring transaction costs** — Makes everything look profitable
4. **Cherry-picked timeframes** — Only showing bull markets

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
