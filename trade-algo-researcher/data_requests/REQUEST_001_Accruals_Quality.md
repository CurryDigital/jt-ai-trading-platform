## DATA REQUEST - Accruals Quality (Sloan 1996)

**From:** Trade Algo Researcher  
**To:** JT Trading Agent (via Jacky)  
**Date:** 2026-02-20  
**Priority:** HIGH

---

### Data Required

**Table/Schema:** `gold.stock_metrics` OR new table `gold.fundamental_metrics`  
**Columns:** 
- `accruals_ratio` (or components: `net_income`, `operating_cash_flow`, `total_assets`)
- `ticker`
- `date`

**Time Period:** 2020-01-01 to 2024-12-31  
**Frequency:** Quarterly (aligned with earnings)  
**Universe:** S&P 500, Russell 1000 constituents

---

### Purpose

Testing **Accruals Quality hypothesis** based on Sloan (1996):
- High accrual firms have lower future returns
- Combining with RSI mean reversion improves signal quality
- Need 5 years of historical accruals data for robust backtest

Current gold schema only has Feb 2026 data (3,578 rows, recent only).

---

### Blocking Status

☑️ **BLOCKING** - Cannot proceed without this data

The hypothesis requires historical accruals to calculate:
```python
accruals_ratio = (net_income - operating_cash_flow) / total_assets
```

Without 2020-2024 data, cannot validate the enhancement to RSI strategy.

---

### Suggested Source

**Option 1 (Preferred):** Calculate from existing data
- Source: Compustat via Bloomberg/FactSet
- Method: (NI - OCF) / Assets quarterly
- Backfill to gold.fundamental_metrics

**Option 2:** External provider
- Source: S&P Global Compustat
- API: FactSet or Bloomberg API
- Cost: ~$500-2000/month

**Option 3:** Free alternative
- Source: Financial Modeling Prep (FMP)
- Endpoint: /cash-flow-statement and /income-statement
- Limitation: Rate limits, coverage gaps

---

### Acceptance Criteria

- [ ] Data completeness > 95% for S&P 500
- [ ] Quarterly frequency (4+ years = 16+ quarters)
- [ ] No look-ahead bias (accruals from t, returns from t+1)
- [ ] Aligns with price data dates in silver schema
- [ ] Documentation on calculation methodology

---

### Current Status

**Backtest Attempted:** 2026-02-20  
**Result:** BLOCKED - insufficient historical data  
**Impact:** 1 of 13 Tier 1 hypotheses cannot proceed

---

### Next Steps

1. JT Trading Agent to confirm data source
2. Backfill to openclaw_researcher or gold schema
3. Notify Trade Algo Researcher when complete
4. Resume backtest

---

**Do not proceed with Accruals Quality backtest until this request is fulfilled.**

Estimated time to validate hypothesis once data available: **2 hours**  
Current delay: **Until data backfilled**
