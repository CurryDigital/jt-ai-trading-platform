# Batch Testing Results - 24 Hypotheses Progress

**Date:** 2026-02-20  
**Session:** Testing with Available Data Only  
**Status:** 7 of 24 Tested (29%)

---

## ✅ VALIDATED (2)

| Hypothesis | Trades | Win Rate | Sharpe | Status |
|------------|--------|----------|--------|--------|
| **3-Day Reversal** | 281 | 61.2% | **2.06** | ✅ VALIDATED |
| **Momentum Lifecycle** | 4,953 | 56.8% | **1.15** | ✅ VALIDATED |

**Total Validated Today:** 2

---

## 🧪 TESTING (2)

| Hypothesis | Trades | Win Rate | Sharpe | Status |
|------------|--------|----------|--------|--------|
| RSI Mean Reversion | 558 | 57.2% | 0.98 | TESTING |
| Engulfing Pattern | 706 | 56.0% | 0.49 | TESTING |

**Notes:** Below 1.0 threshold but showing edge

---

## ❌ LIKELY REJECT (3)

| Hypothesis | Trades | Win Rate | Sharpe | Reason |
|------------|--------|----------|--------|--------|
| Gap Fade HK | 3,061 | 39.4% | **-1.83** | Negative Sharpe |
| Bollinger Squeeze | 69 | 42.0% | N/A | Low win rate, insufficient trades |
| Accruals Quality | 0 | N/A | N/A | No data (awaiting backfill) |

**Total Likely Reject:** 3

---

## ⏸️ BLOCKED - CANNOT TEST WITH AVAILABLE DATA (17)

### Missing ETF Data
| Hypothesis | Required Data | Issue |
|------------|---------------|-------|
| Sector Rotation Tech/Util | XLK, XLU, SPY ETFs | ETFs not in silver schema |
| Sector Momentum | Sector ETFs | No sector classification in DB |

### Missing Fundamental Data
| Hypothesis | Required Data | Issue |
|------------|---------------|-------|
| Quality Value QARP | ROE, profit margins, P/E | gold.stock_metrics lacks fundamentals |
| ESG Improvers | MSCI/Sustainalytics ratings | Not in DB - REQUEST FILED |
| Accruals Quality | Accruals ratio calculation | Historical data needed - REQUEST FILED |

### Missing Intraday/Alt Data
| Hypothesis | Required Data | Issue |
|------------|---------------|-------|
| Asian Session FX | Hourly FX data | Daily only in DB - REQUEST FILED |
| Crypto Funding Rate | Perp funding rates | Not in DB - REQUEST FILED |
| VRP / Gamma / Vol Crush | Options chain + Greeks | Not in DB - REQUEST FILED |
| LLM NLP Sentiment | Earnings transcripts | Not in DB |

### Missing Specific Universes
| Hypothesis | Required Data | Issue |
|------------|---------------|-------|
| AH Premium Arbitrage | Dual-listed HK/CN pairs | Limited A-share data |
| SG REIT Dividend | Singapore REITs | Limited SG tickers in DB |
| HK Property NAV | HK property developers | Specific universe needed |

### Others (Can Test When Data Available)
- Time-Series Momentum Overlay
- Inflation Regime Switch
- PEAD NLP Enhanced
- CMV Multi-Factor
- Limits to Arbitrage
- Supply Chain Reshoring
- Retail Order Flow

---

## 📊 SUMMARY

### Tested Today
| Category | Count |
|----------|-------|
| ✅ Validated | 2 |
| 🧪 Testing | 2 |
| ❌ Likely Reject | 3 |
| **Total Tested** | **7** |

### Remaining
| Category | Count |
|----------|-------|
| ⏸️ Blocked (need data) | 17 |
| **Can Test with Current Data** | **~5-8** |

### Success Rate
- **Validation Rate:** 29% (2/7)
- **Rejection Rate:** 43% (3/7)
- **Testing Rate:** 29% (2/7)

---

## 🎯 WHAT CAN BE TESTED NOW

With available silver/gold data:

1. **Simple Technical Patterns**
   - ✅ RSI Mean Reversion (done)
   - ✅ 3-Day Reversal (done)
   - ✅ Engulfing Pattern (done)
   - ✅ Bollinger Squeeze (done)
   - 🔄 Support/Resistance breaks
   - 🔄 Volume spike patterns

2. **Momentum Strategies**
   - ✅ Time-series momentum (partial)
   - 🔄 Cross-sectional momentum (need more tickers)
   - 🔄 Sector momentum (need sector data)

3. **Mean Reversion**
   - ✅ RSI (done)
   - ✅ 3-Day Reversal (done)
   - 🔄 Pairs trading (need cointegrated pairs)

---

## 📋 DATA REQUESTS NEEDED

To test remaining 17 hypotheses:

| Priority | Request | Cost | Blocks |
|----------|---------|------|--------|
| HIGH | Accruals data | FREE | 1 hypothesis |
| MEDIUM | ETF data (XLK, XLU) | FREE | 2 hypotheses |
| MEDIUM | Hourly FX | FREE | 1 hypothesis |
| MEDIUM | Crypto funding | FREE | 1 hypothesis |
| LOW | ESG ratings | $$$ | 1 hypothesis |
| LOW | Options data | $$$ | 3 hypotheses |

---

## 🚀 NEXT ACTIONS

### Option A: Continue with Available Data (Recommended)
Test remaining 5-8 hypotheses that work with OHLCV only:
- Support/Resistance breaks
- Volume patterns
- Moving average crossovers
- Pairs trading (find cointegrated pairs in DB)

### Option B: Wait for Data Backfill
Pause until JT Trading Agent provides:
- ETF historical data
- Accruals calculation
- Hourly FX

### Option C: Hybrid Approach
Test what we can with available data, queue blocked hypotheses for when data arrives.

---

**Recommendation:** Continue with Option A - test 5-8 more technical patterns using existing OHLCV data while waiting for data requests to be fulfilled.

---

**Files:**
- batch_test_24_hypotheses.py
- research_docs/BACKTEST_AVAILABLE_DATA_2026-02-20.md
