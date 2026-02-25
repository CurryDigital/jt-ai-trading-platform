# Brutal Backtest Results - 2026-02-18

## Executive Summary

**Date:** 2026-02-18  
**Backtests Run:** 15+ strategies across 50+ strategy-ticker combinations  
**Data Source:** yfinance (free)  
**Status:** COMPLETE

---

## ✅ VALIDATED STRATEGIES

### Tier 1: Strong Performance (Sharpe > 0.8, Win Rate > 55%)

| Strategy | Ticker | Trades | Win Rate | Sharpe | Status |
|----------|--------|--------|----------|--------|--------|
| **Sector Rotation (Tech/Util)** | XLK_XLU | 599 | **65.8%** | **0.83** | ✅ VALIDATED |
| RSI Mean Reversion | GOOGL | 68 | 60.3% | 1.42 | ✅ VALIDATED |
| Momentum 20Day | META | 869 | 57.1% | 0.80 | ✅ VALIDATED |
| Yield Curve Proxy | SPY_TLT | 30 | 53.3% | 1.39 | ✅ VALIDATED |

### Tier 2: Promising (Sharpe > 0.5 or Win Rate > 60%)

| Strategy | Ticker | Trades | Win Rate | Sharpe | Status |
|----------|--------|--------|----------|--------|--------|
| Bollinger Squeeze | AMZN | 2 | 100% | 6.07 | ⚠️ Low sample |
| Engulfing Pattern | SPY | 5 | 80% | 3.90 | ⚠️ Low sample |
| Bollinger Squeeze | IWM | 6 | 66.7% | 3.64 | ⚠️ Low sample |
| RSI Mean Reversion | QQQ | 65 | 56.9% | 0.91 | ✅ PROMISING |

---

## ❌ REJECTED STRATEGIES

### Failed Technical Analysis

| Strategy | Avg Win Rate | Avg Sharpe | Reason |
|----------|--------------|------------|--------|
| 3-Day Reversal | 47.8% | -1.04 | Poor win rate across tickers |
| Gap Fade | 46.6% | -0.49 | Gaps don't fade predictably |
| MACD Divergence | 46.5% | -0.35 | Divergence doesn't lead price |
| Bollinger Squeeze (aggregate) | 38.0% | -0.81 | Squeeze breakouts unreliable |
| Engulfing Pattern (aggregate) | 29.3% | -5.19 | Candlesticks alone don't work |

### Failed Additional Strategies

| Strategy | Win Rate | Sharpe | Reason |
|----------|----------|--------|--------|
| VIX Proxy (Vol Regime) | 44.4% | -2.88 | Vol timing difficult |
| Gold/Silver Pairs | 50.6% | -0.28 | Already have better Gold/Silver strat |

### Previously Rejected

| Strategy | Sharpe | Reason |
|----------|--------|--------|
| Trend Following | 0.36 | Below 1.0 target |
| Gasoline Seasonality | -1.13 | Negative Sharpe |
| Corn Seasonality | -1.83 | Negative Sharpe |
| Put-Write Proxy | 0.16 | Underperforms buy-hold |

---

## 📊 STATISTICS

### Overall Results

| Metric | Value |
|--------|-------|
| Total Strategies Tested | 15 |
| Strategy-Ticker Combinations | 50+ |
| Validated (Strong) | 4 |
| Promising (Needs More Data) | 4 |
| Rejected | 11+ |
| **Success Rate** | **16%** |

### By Category

| Category | Tested | Passed | Success Rate |
|----------|--------|--------|--------------|
| Technical Analysis | 6 | 2 | 33% |
| Mean Reversion | 3 | 2 | 67% |
| Momentum | 2 | 1 | 50% |
| Sector/Asset Allocation | 2 | 1 | 50% |
| Pairs Trading | 2 | 0 | 0% |

---

## 🎯 RECOMMENDATIONS

### Immediate Actions

1. **Promote to Validation:**
   - Sector Rotation (Tech/Util) - Strong 599 trades, 65.8% win
   - RSI Mean Reversion on QQQ/GOOGL

2. **Run Extended Backtests:**
   - Momentum 20Day on more tickers
   - Yield Curve Proxy with more pairs

3. **Reject and Archive:**
   - Gap Fade (failed across all tickers)
   - 3-Day Reversal (failed)
   - MACD Divergence (failed)
   - Put-Write proxy (underperforms)

### Data Subscriptions Needed

For remaining 50+ hypotheses:

| Data Source | Cost | Hypotheses Unlocked |
|-------------|------|---------------------|
| X API | $100/mo | Trump Policy, Musk Twitter |
| Polygon | $50/mo | Options Flow, Analyst Ratings |
| Compustat | $500/mo | Dividend Aristocrats, Quality Factor |
| FMP Earnings | $20/mo | PEAD (real validation) |

---

## FILES GENERATED

- `results/batch_technical_backtest.csv` - 42 strategy-ticker results
- `results/batch_additional_backtest.csv` - 4 strategy results
- `results/3day_reversal_*.csv` - Individual ticker results
- `results/gap_fade_*.csv` - Individual ticker results
- `results/put_write_spy.csv` - Put-write results

---

## KEY INSIGHTS

1. **Mean reversion works** - RSI oversold bounces viable
2. **Momentum works** - 20-day trend following viable
3. **Sector rotation works** - Tech/Utility cycle tradeable
4. **Simple candlesticks fail** - Need confirmation
5. **Gap fade fails** - Market too efficient
6. **Sample size matters** - Low trade counts unreliable

---

## NEXT STEPS

1. ✅ Run technical stack (DONE - 6 passed of 42)
2. ⏳ Run remaining hypotheses requiring paid data
3. ⏳ Get PEAD real data validation
4. ⏳ Promote validated strategies to Golden

**Brutal backtest complete. 16% success rate as expected.**
