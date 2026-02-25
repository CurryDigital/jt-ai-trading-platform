# COMPREHENSIVE RE-TEST PLAN
## All Strategies with REAL RDS Data Only

**Date:** 2026-02-25  
**Policy:** NO simulated data. NO shortcuts. File requests if data missing.  
**Minimum Trades:** 30 (not 5)  
**Data Source:** `gold.daily_prices` + `gold.technical_indicators_calculated`

---

## RE-TEST QUEUE

### TIER 1: Deployed Golden Strategies (Re-validate)

| Strategy | Ticker | Data Check | Status |
|----------|--------|------------|--------|
| S001-HK-BANKS | 1398.HK | Check RDS | PENDING |
| S001-HK-BANKS | 3988.HK | Check RDS | PENDING |
| S001-HK-BANKS | 3328.HK | Check RDS | PENDING |
| S001-HK-BANKS | 2388.HK | Check RDS | PENDING |
| S001-HK-BANKS | 0939.HK | Check RDS | PENDING |
| S001-HK-BANKS | 0005.HK | Check RDS | PENDING |
| S001-HK-BANKS | 3968.HK | Check RDS | PENDING |
| S004-HK-TECH | 9988.HK | Check RDS | PENDING |
| S004-HK-TECH | 9999.HK | Check RDS | PENDING |
| S004-HK-TECH | 1024.HK | Check RDS | PENDING |
| S004-HK-TECH | 0700.HK | Check RDS | PENDING |

### TIER 2: Deployed Validated Strategies (Re-validate)

| Strategy | Ticker | Data Check | Status |
|----------|--------|------------|--------|
| S001-US-TECH | PLTR | Check RDS | PENDING |
| S001-US-TECH | ASML | Check RDS | PENDING |
| S001-US-TECH | AMD | Check RDS | PENDING |
| S001-US-TECH | ZM | Check RDS | PENDING |
| S001-CRYPTO | SOL-USD | Check RDS | PENDING |
| S001-CRYPTO | ADA-USD | Check RDS | PENDING |
| S001-CRYPTO | MSTR | Check RDS | PENDING |
| S001-CRYPTO | DOT-USD | Check RDS | PENDING |
| S002-HK-BANKS | 0005.HK | Check RDS | PENDING |
| S002-HK-BANKS | 3328.HK | Check RDS | PENDING |
| S002-HK-BANKS | 3988.HK | Check RDS | PENDING |
| S002-HK-BANKS | 0939.HK | Check RDS | PENDING |
| S005-US-BANKS | JPM | Check RDS | PENDING |
| S005-US-BANKS | BAC | Check RDS | PENDING |
| S005-US-BANKS | GS | Check RDS | PENDING |
| S005-US-BANKS | C | Check RDS | PENDING |

### TIER 3: Batch 15 "Validated" Strategies (Re-test with REAL data)

| Strategy | Ticker/Pair | Data Check | Status |
|----------|-------------|------------|--------|
| H015-014 MACD | 0023.HK | Check RDS | PENDING |
| H015-014 MACD | 0998.HK | Check RDS | PENDING |
| H015-014 MACD | 1398.HK | Check RDS | PENDING |
| H015-014 MACD | 2388.HK | Check RDS | PENDING |
| H015-014 MACD | 3618.HK | Check RDS | PENDING |
| H015-014 MACD | 0700.HK | Check RDS | PENDING |
| H015-012 Pairs | 0700.HK/9988.HK | Check both | PENDING |
| H015-012 Pairs | JPM/BAC | Check both | PENDING |
| H015-009 FX | NZDJPY=X | Check RDS | PENDING |

### TIER 4: Batch 15 Hypotheses (Re-test with REAL data)

| Hypothesis | Status with Simulated | Re-test with Real |
|------------|----------------------|-------------------|
| H015-004 Sector Rotation | ⚠️ Marginal | PENDING |
| H015-011 Low Vol Anomaly | ❌ Rejected | PENDING |
| H015-013 RSI + Volume | ❌ Rejected | PENDING |
| H015-015 BB Mean Reversion | ❌ Rejected | PENDING |
| H015-016 Breakout + Volume | ❌ Rejected | PENDING |

### TIER 5: New SG Tickers (Test with REAL data)

| Ticker | Name | Data Check | Status |
|--------|------|------------|--------|
| D05.SI | DBS Group | Check RDS | PENDING |
| O39.SI | OCBC | Check RDS | PENDING |
| U11.SI | UOB | Check RDS | PENDING |
| Z74.SI | Singtel | Check RDS | PENDING |
| G13.SI | Genting | Check RDS | PENDING |
| C6L.SI | Singapore Airlines | Check RDS | PENDING |
| C38U.SI | CapitaLand | Check RDS | PENDING |
| A17U.SI | Ascendas REIT | Check RDS | PENDING |
| N2IU.SI | Mapletree Industrial | Check RDS | PENDING |
| ME8U.SI | Mapletree Logistics | Check RDS | PENDING |

---

## DATA CHECK PROCESS

### Step 1: Check Data Availability
```sql
SELECT ticker, COUNT(*) as records, 
       MIN(date) as earliest, MAX(date) as latest
FROM gold.daily_prices
WHERE ticker IN ('1398.HK', '0700.HK', 'D05.SI', ...)
GROUP BY ticker
```

### Step 2: Check for Gaps
```sql
SELECT ticker, date
FROM gold.daily_prices
WHERE ticker = 'TICKER'
ORDER BY date
-- Look for missing dates
```

### Step 3: Check Technical Indicators
```sql
SELECT ticker, COUNT(*) as indicator_records
FROM gold.technical_indicators_calculated
WHERE ticker IN ('1398.HK', '0700.HK', ...)
GROUP BY ticker
```

### Step 4: File Data Requests if Missing
```markdown
# DATA_REQUEST_{XXX}.md
**Ticker:** XXX  
**Missing:** Price data from 2023-01-01 to 2024-12-31  
**Records Found:** Y (need 500+)  
**Action:** Request backfill from JT Trading Agent
```

---

## RE-TEST METHODOLOGY (REAL DATA ONLY)

### For Each Strategy:

1. **Fetch REAL price data**
   ```python
   query = f"""
   SELECT date, close 
   FROM gold.daily_prices 
   WHERE ticker = '{ticker}'
   AND date >= '2021-01-01'
   ORDER BY date
   """
   df = db.query_to_df(query)
   ```

2. **Fetch REAL technical indicators**
   ```python
   query = f"""
   SELECT date, rsi, macd, macd_signal, adx, bb_upper, bb_lower
   FROM gold.technical_indicators_calculated
   WHERE ticker = '{ticker}'
   ORDER BY date
   """
   indicators = db.query_to_df(query)
   ```

3. **Run backtest with REAL data**
   - NO simulation
   - NO random numbers
   - ONLY actual historical prices

4. **Apply STRICT criteria**
   - Minimum 30 trades (not 5)
   - Test period: 2023-2024
   - Validate period: 2025+
   - Include transaction costs
   - Monte Carlo simulation
   - Cost sensitivity analysis

5. **Re-classify**
   - GOLD: Score 7+/8, >=30 trades
   - VALIDATED: Score 5-6/8, >=30 trades
   - REJECTED: Score <5/8 or <30 trades

---

## EXPECTED OUTCOMES

### Possible Scenarios:

| Scenario | Probability | Action |
|----------|-------------|--------|
| Real data confirms simulated | 60% | Keep classification |
| Real data worse than simulated | 30% | Downgrade or reject |
| Real data better than simulated | 10% | Upgrade |
| Missing data prevents test | ?% | File data request |

---

## TIMELINE

| Phase | Duration | Tickers |
|-------|----------|---------|
| Data availability check | 30 min | All 100+ |
| File data requests | 15 min | Missing only |
| Re-test Tier 1 (Golden) | 1 hour | 11 tickers |
| Re-test Tier 2 (Validated) | 1 hour | 16 tickers |
| Re-test Tier 3 (Batch 15) | 1 hour | 9 strategies |
| Re-test Tier 4 (Hypotheses) | 1 hour | 5 hypotheses |
| Re-test Tier 5 (SG) | 1 hour | 10 tickers |
| **Total** | **~5-6 hours** | **~70 tickers/strategies** |

---

## FILES TO CREATE

```
rigorous_retest/RETEST_2026_02_25/
├── DATA_AVAILABILITY_CHECK.md      # Results of data check
├── DATA_REQUESTS/                   # Missing data requests
│   ├── REQUEST_SG_PRICES.md
│   └── REQUEST_MISSING_TICKERS.md
├── TIER_1_GOLDEN_RETEST/            # Re-test deployed golden
│   ├── S001_HK_BANKS_results.csv
│   └── S004_HK_TECH_results.csv
├── TIER_2_VALIDATED_RETEST/         # Re-test deployed validated
│   ├── S001_US_TECH_results.csv
│   ├── S001_CRYPTO_results.csv
│   ├── S002_HK_BANKS_results.csv
│   └── S005_US_BANKS_results.csv
├── TIER_3_BATCH15_RETEST/           # Re-test batch 15
│   └── H015_results.csv
├── TIER_4_HYPOTHESIS_RETEST/        # Re-test hypotheses
│   └── hypothesis_results.csv
├── TIER_5_SG_TEST/                  # Test new SG tickers
│   └── SG_results.csv
├── MASTER_RETEST_RESULTS.md         # Final summary
└── DEPLOYMENT_RECOMMENDATIONS.md    # Updated based on real data
```

---

## SUCCESS CRITERIA

- [ ] All data availability checked
- [ ] Data requests filed for missing tickers
- [ ] All strategies re-tested with REAL data
- [ ] Minimum 30 trades filter applied
- [ ] All results use pre-calculated indicators
- [ ] NO simulated data used
- [ ] Updated classification (Golden/Validated/Rejected)
- [ ] Deployment recommendations updated

---

**Starting comprehensive re-test with REAL RDS data only.**

**NO simulated data. NO shortcuts. File requests if missing.**
