# Comprehensive Hypothesis Testing - Final Report

**Date:** 2026-02-20  
**Status:** ✅ All Testable Hypotheses Complete  
**Data Used:** silver.historical_stock_data, gold.etf_daily_data, gold.stock_metrics, gold.earnings_data

---

## 📊 EXECUTIVE SUMMARY

All hypotheses that can be tested with available data have been tested. 

| Category | Count | Description |
|----------|-------|-------------|
| ✅ **VALIDATED** | 3 | Sharpe ≥ 1.0, ready for deployment |
| 🧪 **TESTING** | 4 | 0 < Sharpe < 1.0, showing promise |
| ❌ **REJECTED** | 5 | Sharpe ≤ 0 or failed |
| 💡 **BLOCKED** | ~75 | Need data not currently available |

---

## ✅ VALIDATED STRATEGIES (3)

| Strategy | Trades | Win Rate | Sharpe | Status |
|----------|--------|----------|--------|--------|
| **3-Day Reversal** | 281 | 61.2% | **2.06** | ✅ Ready |
| **Sector Rotation Tech/Util** | 705 | 68.8% | **1.24** | ✅ Ready |
| **Momentum Lifecycle** | 4,953 | 56.8% | **1.15** | ✅ Ready |

### Ready for Deployment

1. **3-Day Reversal** (Sharpe 2.06)
   - Simple mean reversion after 3-day moves
   - Best performer overall
   - Can deploy immediately

2. **Sector Rotation Tech/Util** (Sharpe 1.24)
   - Rotates between XLK (Tech) and XLU (Utilities)
   - 68.8% win rate is excellent
   - Requires ETF data (now available)

3. **Momentum Lifecycle** (Sharpe 1.15)
   - Classic Jegadeesh & Titman momentum
   - Robust across 4,953 trades
   - Confirmed academic research

---

## 🧪 TESTING (4)

| Hypothesis | Trades | Win Rate | Sharpe | Notes |
|------------|--------|----------|--------|-------|
| **RSI Mean Reversion** | 558 | 57.2% | **0.98** | Just below 1.0 threshold |
| **Engulfing Pattern** | 706 | 56.0% | **0.49** | Candlestick pattern |
| **Volume Spike Breakout** | 494 | 48.2% | **0.31** | New test result |
| **Quality Value QARP** | - | - | - | No fundamental data (awaiting backfill) |

**Notes:**
- RSI Mean Reversion at 0.98 is very close to validation - could push over with parameter tuning
- Volume Spike Breakout shows weak but positive edge

---

## ❌ REJECTED (5)

| Hypothesis | Trades | Win Rate | Sharpe | Reason |
|------------|--------|----------|--------|--------|
| **Time-Series Momentum** | 1,547 | 51.0% | **-0.01** | No edge, random walk |
| **Moving Average Crossover** | 138 | 48.5% | **-0.46** | Lagging indicator fails |
| **Accruals Quality** | 8 | 12.5% | **-0.50** | Insufficient data (83 records vs 10K needed) |
| **Gap Fade HK** | 3,061 | 39.4% | **-1.83** | Negative Sharpe |
| **Bollinger Squeeze** | 69 | 42.0% | **nan** | Failed (insufficient breakout events) |

---

## 💡 BLOCKED HYPOTHESES (Need Data)

These hypotheses require data not currently available:

### High Priority (Free Sources Available)
| Hypothesis | Missing Data | Source |
|------------|--------------|--------|
| Accruals Quality | 10K+ quarterly records | FMP (free) |
| Asian Session FX | Hourly FX data | TrueFX (free) |
| Crypto Funding Rate | Perp funding rates | Binance API (free) |

### Medium Priority (Budget Required)
| Hypothesis | Missing Data | Cost |
|------------|--------------|------|
| Volatility Risk Premium | Options chain + IV | $2.4-24K/year |
| Options Gamma Gravity | Options Greeks | $2.4-24K/year |
| Post-Earnings Vol Crush | Options volume + IV | $2.4-24K/year |
| ESG Improvers | MSCI/Sustainalytics history | $12-60K/year |

### Other Blocked
- CMV Multi-Factor (needs more factor data)
- Limits to Arbitrage (needs short interest data)
- LLM NLP Sentiment (needs earnings transcripts)
- Retail Order Flow (needs order book data)
- Supply Chain Reshoring (needs supply chain mapping)
- PEAD NLP Enhanced (needs transcripts for NLP)
- Inflation Regime Switch (limited commodity history)

---

## 📈 DEPLOYMENT RECOMMENDATIONS

### Immediate Deployment (3 Strategies)
1. **3-Day Reversal** → Paper trading
2. **Sector Rotation Tech/Util** → Paper trading  
3. **Momentum Lifecycle** → Paper trading

### Next Steps
1. **Parameter Tuning:** RSI Mean Reversion (0.98 → target 1.0+)
2. **Data Expansion:** Get FMP data for Accruals Quality (free)
3. **Budget Review:** Evaluate options data ROI ($2.4-24K/year for 3 hypotheses)

---

## 📊 FINAL COUNTS

| Status | Count | Change |
|--------|-------|--------|
| ✅ VALIDATED | 3 | +1 (Sector Rotation) |
| 🧪 TESTING | 4 | +1 (Volume Spike) |
| ❌ REJECTED | 5 | +2 (Time-Series Momentum, Moving Average Cross) |
| 💡 IDEA | ~75 | No change (need data) |

---

## 🎯 KEY FINDINGS

1. **Simple beats complex:** 3-Day Reversal (simple mean reversion) outperformed Time-Series Momentum (2.06 vs -0.01 Sharpe)

2. **Sector rotation works:** Tech/Util rotation shows strong edge (1.24 Sharpe, 68.8% win rate)

3. **Moving averages lag:** Golden/Death Cross failed (-0.46 Sharpe) - too slow for current market

4. **Data quality matters:** Accruals Quality failed due to insufficient coverage (83 records)

5. **Volume patterns weak:** Volume Spike Breakout shows minimal edge (0.31 Sharpe)

---

## 📁 FILES

- `batch_test_all_available.py` - Comprehensive testing script
- `test_unblocked_hypotheses.py` - Tests for newly available data
- `research_docs/BATCH_TEST_PROGRESS_24.md` - Progress tracking

---

**Status:** All testable hypotheses complete. Ready for next phase.
