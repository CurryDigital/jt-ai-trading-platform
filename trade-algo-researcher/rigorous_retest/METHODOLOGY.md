# RIGOROUS STRATEGY RETEST — FROM SCRATCH

## Methodology (Non-Negotiable)

### 1. Strategy Logic Must Be Simple and Testable
- Entry conditions: MAX 2-3 simple rules
- No compound conditions that rarely trigger together
- Each condition must produce signals independently

### 2. Backtest Code Must Be Verified
- Test logic on single ticker first
- Verify signal count > 0
- Print sample signals for manual verification
- Only then run full universe

### 3. Full Universe Testing
- Test on ALL available tickers
- Report: PASS, FAIL, INSUFFICIENT for every ticker
- No cherry-picking
- Show full distribution of results

### 4. Statistical Significance
- Minimum 30 trades for consideration
- Report confidence intervals
- Show win rate distribution
- Report failure rate honestly

### 5. Validation Requirements
- Train: 2021-2022 (bear market)
- Test: 2023-2024 (bull market)
- Validate: 2025+ (out-of-sample)
- ALL THREE must show promise (not just one period)

### 6. No Deployment Until
- Logic verified by manual inspection
- At least 3 independent tickers show consistent results
- Decay analysis complete
- Written confirmation that methodology is sound

---

## Current Status: STARTING FROM ZERO

Previous strategies: ARCHIVED (not trusted)
Current valid strategies: ZERO
Deployment status: HALTED

---

## Candidate Strategies to Test (Simple Logic Only)

### S001-Candidate: RSI Extreme Mean Reversion
- **Logic:** RSI(14) < 25 (extreme oversold), Hold 10 days
- **Why simple:** Single condition, clear signal
- **Expected signals:** More frequent than RSI<30 + Price>SMA20

### S002-Candidate: 3-Day Panic Reversal
- **Logic:** 3 consecutive down days, Buy on Day 3 close, Hold 5 days
- **Why simple:** No indicators, pure price action

### S003-Candidate: Gap Down Recovery
- **Logic:** Open >5% below previous close, Buy at open, Hold 3 days
- **Why simple:** Single gap condition

### S004-Candidate: Volume Spike Breakout
- **Logic:** Volume >2x 20-day average, Hold 5 days
- **Why simple:** Volume confirmation only

---

## Verification Checklist Before Declaring "Valid"

- [ ] Code reviewed line-by-line
- [ ] Sample signals printed and verified manually
- [ ] At least 20 signals in test period
- [ ] Test WR >= 55%
- [ ] Validate WR >= 50% (or no significant decay)
- [ ] At least 3 tickers show consistent pattern
- [ ] Full results table provided (pass AND fail)

---

*Started: 2026-02-25*
*Status: Building from zero with rigorous standards*
