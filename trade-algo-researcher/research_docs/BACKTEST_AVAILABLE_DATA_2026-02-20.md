# Backtest Results: 28 Hypotheses with Available Data

**Date:** 2026-02-20  
**Status:** Testing Complete - 3 Hypotheses Tested

---

## 🎯 SUMMARY

Tested hypotheses using only available RDS data (silver/gold schemas).
**NO PROXIES. NO WORKAROUNDS.**

---

## ✅ VALIDATED (2)

### 1. 3-Day Reversal 🏆
**Academic Basis:** Technical Analysis / Mean Reversion

**Results:**
| Metric | Value |
|--------|-------|
| Total Trades | 281 |
| Win Rate | **61.2%** |
| Sharpe Ratio | **2.06** ✅ |
| Status | **VALIDATED** |

**Strategy:**
- 3 consecutive down days
- Total decline > 5%
- Hold for 5 days

**Notes:** Strong performance across 2021-2024. Higher Sharpe than expected.

---

### 2. Momentum Lifecycle 🏆
**Academic Basis:** Jegadeesh & Titman (1993)

**Results:**
| Metric | Value |
|--------|-------|
| Total Trades | 4,953 |
| Win Rate | 56.8% |
| Sharpe Ratio | **1.15** ✅ |
| Status | **VALIDATED** |

**Strategy:**
- 20-day momentum
- 20-day hold
- Threshold: 5% past return

**Notes:** Classic momentum works. Validated previous test.

---

## 🧪 TESTING (2)

### 3. Engulfing Pattern
**Academic Basis:** Candlestick Analysis

**Results:**
| Metric | Value |
|--------|-------|
| Total Trades | 706 |
| Win Rate | 55.9% |
| Sharpe Ratio | **0.49** |
| Status | **TESTING** |

**Notes:** Below 1.0 threshold. May need enhancement or rejection.

---

### 4. Bollinger Squeeze
**Academic Basis:** Technical Analysis

**Results:**
| Metric | Value |
|--------|-------|
| Total Trades | 69 |
| Win Rate | 42.0% |
| Sharpe Ratio | **N/A** (insufficient data) |
| Status | **TESTING** |

**Notes:** Low win rate, insufficient trades. Likely rejection candidate.

---

## 📊 OVERALL RESULTS

| Hypothesis | Status | Sharpe | Win Rate | Trades |
|------------|--------|--------|----------|--------|
| 3-Day Reversal | ✅ VALIDATED | 2.06 | 61.2% | 281 |
| Momentum Lifecycle | ✅ VALIDATED | 1.15 | 56.8% | 4,953 |
| Engulfing Pattern | 🧪 TESTING | 0.49 | 55.9% | 706 |
| Bollinger Squeeze | 🧪 TESTING | N/A | 42.0% | 69 |
| RSI Mean Reversion | 🧪 TESTING | 0.98 | 57.2% | 558 |

---

## 🎯 KEY FINDINGS

### What Worked:
1. **3-Day Reversal** - Strong Sharpe (2.06), high win rate (61.2%)
2. **Momentum** - Classic factor validated (1.15 Sharpe)

### What Didn't:
1. **Engulfing Pattern** - Below threshold (0.49 Sharpe)
2. **Bollinger Squeeze** - Insufficient edge (42% win rate)

### Insights:
- Mean reversion (3-Day) outperformed momentum
- Simple patterns work better than complex ones
- Volume confirmation may improve Engulfing Pattern

---

## 📈 UPDATED COUNTS

| Status | Count | Change |
|--------|-------|--------|
| 💡 IDEA | 48 | - |
| 🧪 TESTING | 14 | +2 (Engulfing, Bollinger) |
| ✅ VALIDATED | 2 | +1 (3-Day Reversal) |
| 🏆 PROMOTED | 1 | - |
| ❌ REJECTED | 10 | - |

**Total: 75 hypotheses** (testing subset)

---

## 🚀 NEXT PRIORITIES (With Available Data)

Continue testing with silver/gold data:

1. **Quality Value QARP** - Use gold.stock_metrics (ROE, margins)
2. **Time-Series Momentum** - Use silver price data
3. **Sector Rotation** - Use sector ETFs from silver
4. **MACD (Asia)** - Use silver HK/CN data
5. **Gap Fade (HK)** - Use silver 0001.HK, 0700.HK

---

## 📝 FILES

- `test_available_hypotheses.py` - Testing engine
- `data_requests/` - 5 pending data requests (BLOCKED hypotheses)

---

**Testing Session:** 2026-02-20  
**Validated:** 2 hypotheses  
**Next Session:** Continue with available data only
