# H#004: Platform Variation Test — Golden Cross vs ADX Filter
**Strategy:** COIN Strong Uptrend GOLD  
**Hypothesis:** Golden Cross filter performs similarly to ADX > 25 filter  
**Status:** 🔄 Testing (Live)  
**Start Date:** 2026-02-23

---

## 🎯 Test Objective

Compare JT Trading Agent's implementation (Golden Cross) vs Researcher's specification (ADX > 25) to determine if the platform variation is acceptable.

---

## 🔬 Filter Definitions

| Filter | Formula | Logic |
|--------|---------|-------|
| **Original (ADX)** | SPY Price > 200d AND ADX(14) > 25 | Measures trend **strength** |
| **Platform (Golden Cross)** | SPY 50d SMA > 200d SMA | Measures trend **direction** |

**Key Difference:**
- ADX > 25 filters for **strong** uptrends (institutional momentum)
- Golden Cross signals any uptrend, including weak ones

---

## 📊 Historical Backtest Comparison

### Original Specification (ADX > 25)
| Metric | Value |
|--------|-------|
| Win Rate | **93.3%** |
| Trades | 15 |
| Avg Return | 9.1% |
| Sharpe | ~3.2 |
| Signals/Year | 7-8 |

### Platform Implementation (Golden Cross) - Estimated
| Metric | Estimate | Range |
|--------|----------|-------|
| Win Rate | **85%** | 80-90% |
| Trades | ~20 | (to be confirmed) |
| Avg Return | ~7% | 6-8% |
| Sharpe | ~2.5 | 2.0-3.0 |
| Signals/Year | 10-15 | Higher frequency |

**Trade-off:** More signals (frequency) at slightly lower win rate (quality)

---

## 📈 Live Test Tracking

### Test Parameters
- **Sample Size Target:** 30 trades (for statistical significance)
- **Minimum Viable:** 15 trades (initial assessment)
- **Test Duration:** ~3-6 months (depends on signal frequency)

### Results Table (Update After Each Trade)

| # | Date | Entry | Exit | Return | Win? | Filter Used | Notes |
|---|------|-------|------|--------|------|-------------|-------|
| 1 | - | - | - | - | - | Golden Cross | Awaiting first signal |
| 2 | - | - | - | - | - | - | - |
| 3 | - | - | - | - | - | - | - |
| ... | ... | ... | ... | ... | ... | ... | ... |
| 30 | - | - | - | - | - | - | Final assessment |

### Running Statistics (Update Weekly)

| Metric | Current | After 10 | After 20 | After 30 |
|--------|---------|----------|----------|----------|
| Trades | 0 | - | - | - |
| Win Rate | N/A | - | - | - |
| Avg Return | N/A | - | - | - |
| Max DD | N/A | - | - | - |

---

## ✅ Decision Criteria

### After 15 Trades (Checkpoint 1)
| Win Rate | Decision |
|----------|----------|
| >= 85% | ✅ **Accept variation** — Performance acceptable |
| 80-85% | 🟡 **Continue testing** — Need larger sample |
| < 80% | ❌ **Request ADX filter** — Below threshold |

### After 30 Trades (Final Decision)
| Win Rate | Decision |
|----------|----------|
| >= 85% | ✅ **Accept as permanent** — Update spec to Golden Cross |
| 80-85% | ⚠️ **Marginal** — Continue monitoring or request ADX |
| < 80% | ❌ **Reject** — Request JT implement ADX > 25 filter |

**Confidence Interval:** With 30 trades, 95% CI for win rate is ±18 percentage points

---

## 🎓 Expected Outcomes

### Scenario A: Golden Cross ≈ ADX (Win Rate 85-90%)
**Implication:** Platform variation is acceptable
**Action:** Update strategy specification to match JT implementation
**Benefit:** More signals (10-15 vs 7-8/year), still high win rate

### Scenario B: Golden Cross < ADX (Win Rate 70-80%)
**Implication:** Filter difference matters significantly
**Action:** Request JT implement ADX > 25 filter
**Risk:** Lower win rate could impact overall portfolio performance

### Scenario C: Golden Cross > ADX (Win Rate 90-95%)
**Implication:** JT's filter actually better (unexpected)
**Action:** Learn from result, update research methodology
**Benefit:** Discover that Golden Cross > ADX for crypto

---

## 📝 Research Notes

### Why This Matters
1. **Implementation fidelity:** Ensures live performance matches backtest
2. **Platform differences:** JT may have constraints affecting filter choice
3. **Robustness test:** If both filters work, strategy is more robust

### What We're Learning
- Does trend direction (Golden Cross) matter more than trend strength (ADX) for crypto mean reversion?
- Is selectivity (ADX) or frequency (Golden Cross) more important?
- Can we generalize this to other strategies?

---

## 🔗 Related Files

- Strategy: [COIN_Strong_Uptrend_GOLD.md](../strategies/COIN_Strong_Uptrend_GOLD.md)
- Research Log: [RESEARCH_LOG_OPTIMIZED.md](../RESEARCH_LOG_OPTIMIZED.md) — H#004 entry
- Test Script: [test_H004_golden_cross_vs_adx.py](../../test_H004_golden_cross_vs_adx.py)

---

## ⏱️ Timeline

| Milestone | Target Date | Status |
|-----------|-------------|--------|
| Test Start | 2026-02-23 | ✅ Started |
| First Trade | TBD | ⏳ Waiting for signal |
| Checkpoint 1 (15 trades) | ~2026-04-01 | ⏳ Pending |
| Checkpoint 2 (30 trades) | ~2026-06-01 | ⏳ Pending |
| Final Decision | ~2026-06-15 | ⏳ Pending |

---

*Hypothesis created: 2026-02-23*  
*Testing method: Live performance tracking*  
*Success criteria: Win rate >= 80% with 30 trades*