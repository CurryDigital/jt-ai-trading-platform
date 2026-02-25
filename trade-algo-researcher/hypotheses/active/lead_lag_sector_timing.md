# Hypothesis: Lead-Lag Sector Timing Adds 0.3-0.5 Sharpe

**Status:** testing  
**Created:** 2026-02-16  
**Last Updated:** 2026-02-16

---

## Core Idea

Information diffuses from sector ETFs to individual constituents with 1-3 day lag. By identifying when a sector ETF has significant residual movement, we can predict delayed reaction in correlated stocks.

---

## Evidence So Far

- **Literature:** Lo & MacKinlay (1990) documented lead-lag effects
- **Theory:** Large-cap/ETF lead, small-cap lags due to information processing speed
- **Hypothesis:** τ_sector_to_stock = 1-3 days

---

## Testing Plan

1. **Backtest Analysis (Weeks 1-2)**
   - Calculate rolling correlations between sector ETFs and constituents
   - Measure optimal lag for each sector
   - Identify lead-lag pairs

2. **Signal Generation (Weeks 3-4)**
   - Build lead-lag overlay for ARASO
   - Test if sector signal improves entry timing
   - Measure Sharpe improvement

3. **Validation (Weeks 5-8)**
   - Out-of-sample testing
   - Walk-forward analysis
   - Statistical significance test

---

## Validation Criteria

**Validated if:**
- Lead-lag overlay adds >0.3 Sharpe to ARASO
- τ measurement consistent (1-3 days)
- Correlation >0.6 between sector lead and stock lag

**Rejected if:**
- No significant Sharpe improvement
- τ varies unpredictably
- Correlation <0.4

---

## Next Actions

- [ ] Run correlation analysis on 5-year data
- [ ] Identify optimal lag per sector
- [ ] Integrate with ARASO backtest

---

## Confidence

**Current weight:** 0.60  
**Trend:** Theoretically sound, needs empirical validation  
**Target for promotion:** 0.80

---

*This hypothesis has strong theoretical backing but needs backtest validation.*
