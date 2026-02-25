# Creative Hypothesis Test Results

**Date:** 2026-02-18  
**Tests Run:** 4 creative strategies

---

## ✅ WORKED

### 1. Gold/Silver Ratio (Already Validated)
- **Sharpe:** 1.11
- **Win Rate:** 65.2%
- **Status:** ✅ PROMOTED to Golden Strategy

---

## ⚠️ MIXED RESULTS

### 2. Supply Chain Information Diffusion
**Test:** NVDA → AMD, MSFT → NVDA, AMZN → UPS

| Pair | Lag | Correlation | Status |
|------|-----|-------------|--------|
| NVDA → AMD | 0d | 0.727 | ❌ No lag |
| MSFT → NVDA | 0d | 0.671 | ❌ No lag |
| AMZN → UPS | 0d | 0.360 | ❌ Weak |

**Finding:** High correlation but ZERO time lag. Market too efficient.

**Verdict:** Needs alternative data (earnings transcripts vs price), not just price.

---

### 3. Put-Write Strategy (Proxy)
**Test:** Simulated SPY put-write 2019-2024

| Metric | Result |
|--------|--------|
| Months tested | 71 |
| Months positive | 47 |
| Proxy win rate | 66% |

**Note:** Real put-write would have different payoff (limited upside, large downside).

**Verdict:** Needs real options data for accurate backtest.

---

## ❌ NEEDS FIXING

### 4. 3-Day Reversal
**Issue:** Pandas indexing errors in script
**Data available:** 128 instances of 3 down days in SPY
**Potential:** Needs intraday data for accurate gap fill detection

### 5. Gap Fade
**Issue:** Pandas indexing errors in script  
**Data available:** 431 gaps >1% in SPY
**Potential:** Intraday data needed for accurate fill detection

---

## SUMMARY

| Strategy | Data | Win Rate | Status |
|----------|------|----------|--------|
| Gold/Silver | yfinance | 65% | ✅ Validated |
| Supply Chain | yfinance | N/A | ❌ No lag found |
| Put-Write | Proxy | 66% | ⚠️ Needs options data |
| 3-Day Reversal | yfinance | TBD | ⚠️ Script errors |
| Gap Fade | yfinance | TBD | ⚠️ Script errors |

---

## KEY INSIGHT

**Price-based supply chain doesn't work** — market prices simultaneously.

**Need alternative data for supply chain:**
- Earnings call transcripts (customer mentions supplier)
- Guidance changes
- Segment reporting
- Not just price

---

## NEXT STEPS

1. **Fix scripts** — Resolve pandas indexing issues
2. **Get options data** — For put-write, gamma gravity
3. **Get earnings transcripts** — For supply chain NLP
4. **Test remaining creative hypotheses:**
   - Retail flow reversal (need social/options data)
   - Gamma gravity (need options chain)
   - Index rebalancing (need announcement dates)
   - Merger arb (need deal database)

---

**Bottom line:** Creative hypotheses require creative data. Price alone isn't enough.
