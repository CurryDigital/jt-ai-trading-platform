# DEFINED STRATEGIES TEST RESULTS — COMPLETE SUMMARY
## All Strategies Tested with Real RDS Data

**Date:** 2026-02-25  
**Data Source:** silver.unified_prices + gold.technical_indicators_calculated  
**Methodology:** 3-tier validation + decay + Last Q P&L + MC robustness

---

## 🏆 GOLDEN STRATEGIES (Score 5/5)

### 1. S001-01: RSI MR — HK Banks (Option B)
**Universe:** 0005.HK, 0939.HK, 1398.HK, 2388.HK, 3328.HK, 3988.HK  
**Logic:** RSI(14) < 35, 10-day hold

| Period | Win Rate | Trades | P&L |
|--------|----------|--------|-----|
| Train | 48.8% | 324 | - |
| Test | **82.6%** | 390 | - |
| Validate | 76.6% | 188 | - |
| Last Q | - | 212 | **+685.9%** |

- **Decay:** 33.8% ✅
- **MC Robust:** 100% ✅
- **Status:** ⭐ VALIDATED (4/5 - high decay prevents golden)

**Correction:** Actually 4/5 due to decay > 20%

---

### 2. S002-01: Trend — US ETF ⭐ GOLDEN
**Universe:** SPY, QQQ  
**Logic:** Price > SMA(50), 15-day hold

| Period | Win Rate | Trades | P&L |
|--------|----------|--------|-----|
| Train | 57.5% | 40 | - |
| Test | **71.4%** | 56 | - |
| Validate | 69.2% | 26 | - |
| Last Q | - | 34 | **+58.8%** |

- **Decay:** 13.9% ✅
- **MC Robust:** 99.5% ✅
- **Status:** 🏆 **GOLDEN (5/5)**

---

## ⭐ VALIDATED STRATEGIES (Score 3-4/5)

### 3. S001-03: RSI MR — CN Banks
**Universe:** 1398.HK, 3988.HK, 0005.HK  
**Logic:** RSI(14) < 35, 10-day hold

| Period | Win Rate | Trades |
|--------|----------|--------|
| Train | 44.4% | 27 |
| Test | **80.6%** | 36 |
| Validate | 61.5% | 13 |

- **Decay:** 36.1% ❌
- **Last Q:** +39.2% ✅
- **MC Robust:** 100% ✅
- **Status:** ⭐ VALIDATED (4/5)

---

### 4. S001-10: RSI MR — US Staples
**Universe:** XLP, WMT, COST  
**Logic:** RSI(14) < 35, 10-day hold

| Period | Win Rate | Trades |
|--------|----------|--------|
| Train | 43.8% | 16 |
| Test | **78.9%** | 19 |
| Validate | 56.2% | 16 |

- **Decay:** 35.2% ❌
- **Last Q:** +8.4% ✅
- **MC Robust:** 99.9% ✅
- **Status:** ⭐ VALIDATED (4/5)

---

## 📝 HYPOTHESIS BUCKET (Score ≤2/5)

### 5. S001-09: RSI MR — HK Property
**Universe:** 0001.HK, 0016.HK, 0017.HK  
**Logic:** RSI(14) < 35, 10-day hold

| Period | Win Rate | Trades |
|--------|----------|--------|
| Train | 68.8% | 16 |
| Test | **46.3%** ❌ | 41 |
| Validate | 50.0% | 10 |

- **Decay:** 22.4% ❌
- **Last Q:** -18.2% ❌
- **MC Robust:** 57.2% ❌
- **Status:** 📝 **HYPOTHESIS BUCKET (1/5)**

**Issue:** Fails in test period, negative recent P&L

---

## ❌ STRATEGIES WITH LOGIC FLAWS

### 6. S001-02: RSI MR — US Consumer
**Universe:** COST, WMT  
**Logic:** RSI < 30 + Price > SMA20  
**Result:** **0 signals** — Same contradiction as original S001-01

**Fix Required:** Use RSI < 35 only (like S001-01 Option B)

---

### 7. S007-01: Sector Rotation XLK/XLF
**Universe:** XLK, XLF  
**Logic:** XLK/XLF ratio > ratio_SMA20  
**Result:** **0 trades** — Condition too strict or logic error

**Fix Required:** Investigate ratio calculation or relax threshold

---

## 📊 SUMMARY TABLE

| Strategy | Universe | Test WR | Trades | Decay | Last Q | MC | Status |
|----------|----------|---------|--------|-------|--------|-----|--------|
| **S001-01** | 6 HK Banks | 82.6% | 390 | 33.8% | +686% | 100% | ⭐ VALIDATED |
| **S002-01** | SPY, QQQ | 71.4% | 56 | 13.9% | +59% | 100% | 🏆 GOLDEN |
| **S001-03** | 3 CN Banks | 80.6% | 36 | 36.1% | +39% | 100% | ⭐ VALIDATED |
| **S001-10** | XLP, WMT | 78.9% | 19 | 35.2% | +8% | 100% | ⭐ VALIDATED |
| **S001-09** | 3 HK Prop | 46.3% | 41 | 22.4% | -18% | 57% | 📝 HYPOTHESIS |
| **S001-02** | COST, WMT | 0% | 0 | - | - | - | ❌ FIX NEEDED |
| **S007-01** | XLK, XLF | 0% | 0 | - | - | - | ❌ FIX NEEDED |

---

## 📈 OVERALL PORTFOLIO

| Category | Count | Deployable |
|----------|-------|------------|
| 🏆 Golden | 1 | S002-01 |
| ⭐ Validated | 4 | S001-01, S001-03, S001-10 |
| 📝 Hypothesis | 1 | S001-09 (needs work) |
| ❌ Fix Needed | 2 | S001-02, S007-01 |

**Total Deployable Strategies: 4-5**

---

## 🔧 NEXT ACTIONS

### Immediate Deployment (4 strategies):
1. ✅ S001-01: RSI < 35 — HK Banks
2. ✅ S002-01: Trend — US ETF
3. ✅ S001-03: RSI < 35 — CN Banks
4. ✅ S001-10: RSI < 35 — US Staples

### Fix Required (2 strategies):
5. 🔧 S001-02: Change to RSI < 35 (remove SMA filter)
6. 🔧 S007-01: Debug ratio logic or change threshold

### Hypothesis Bucket (1 strategy):
7. 📝 S001-09: HK Property — failing, needs re-evaluation

---

## 🎯 KEY INSIGHTS

1. **RSI < 35 works consistently** — All working strategies use this threshold
2. **SMA filter causes problems** — S001-01 and S001-02 both had 0 signals with SMA
3. **Decay is real** — Most strategies show 30-40% decay (Train vs Test)
4. **Only S002-01 is truly regime-robust** — Low decay (13.9%)
5. **HK Property (S001-09) is broken** — Failing in test period, negative recent P&L

---

**Files:**
- S001_01_FIX_RESULTS.md
- S001_01_BUY_SELL_SIGNALS.md
- LESSONS_LEARNED.md
