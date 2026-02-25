# S001-01 FIX RESULTS: Option A vs B
## Strategy: RSI Mean Reversion — HK Banks

**Date:** 2026-02-25  
**Original Issue:** RSI < 30 + Price > SMA20 produced ZERO signals  
**Fix Applied:** Removed SMA filter, tested RSI < 30 (A) and RSI < 35 (B)

---

## RESULTS SUMMARY

| Option | Logic | Test WR | Trades | Decay | MC | Status |
|--------|-------|---------|--------|-------|-----|--------|
| **A** | RSI < 30 | **90.2%** | 224 | 36.2% | 100% | ⭐ VALIDATED |
| **B** | RSI < 35 | **82.6%** | 390 | 33.8% | 100% | ⭐ VALIDATED |

---

## DETAILED BREAKDOWN

### Option A: RSI < 30 (Tighter Filter)

| Ticker | Test WR | Trades | Decay | Status |
|--------|---------|--------|-------|--------|
| 0005.HK | 67.9% | 28 | 12.3% | 🏆 GOLDEN |
| 0939.HK | 86.5% | 37 | 42.4% | ⭐ VALIDATED |
| 1398.HK | 96.0% | 50 | 60.0% | ⭐ VALIDATED |
| 2388.HK | 89.1% | 46 | 13.1% | 🏆 GOLDEN |
| 3328.HK | 97.2% | 36 | 43.2% | ⭐ VALIDATED |
| 3988.HK | 100.0% | 27 | 36.8% | ⭐ VALIDATED |

**Aggregate:**
- Train: 54.0% (176 trades)
- Test: 90.2% (224 trades)
- Validate: 84.9% (106 trades)
- Last Q P&L: +471.3%
- MC Robust: 100%

**Signal Frequency:** ~15 signals/ticker/year

---

### Option B: RSI < 35 (Relaxed Filter)

| Ticker | Test WR | Trades | Decay | Status |
|--------|---------|--------|-------|--------|
| 0005.HK | 72.7% | 44 | 18.3% | 🏆 GOLDEN |
| 0939.HK | 82.9% | 70 | 45.9% | ⭐ VALIDATED |
| 1398.HK | 87.2% | 78 | 42.4% | ⭐ VALIDATED |
| 2388.HK | 71.4% | 84 | 11.9% | 🏆 GOLDEN |
| 3328.HK | 89.8% | 59 | 41.5% | ⭐ VALIDATED |
| 3988.HK | 92.7% | 55 | 38.7% | ⭐ VALIDATED |

**Aggregate:**
- Train: 48.8% (324 trades)
- Test: 82.6% (390 trades)
- Validate: 76.6% (188 trades)
- Last Q P&L: +685.9%
- MC Robust: 100%

**Signal Frequency:** ~25 signals/ticker/year

---

## COMPARISON

| Metric | Option A | Option B | Winner |
|--------|----------|----------|--------|
| Test Win Rate | 90.2% | 82.6% | **A** |
| Total Trades | 224 | 390 | **B** |
| Decay | 36.2% | 33.8% | **B** |
| Last Q P&L | +471% | +686% | **B** |
| Signals/Year | 15/ticker | 25/ticker | **B** |
| MC Robust | 100% | 100% | Tie |

---

## RECOMMENDATION

### For Higher Win Rate: **Option A (RSI < 30)**
- 90.2% win rate
- More selective (15 signals/ticker/year)
- Better for concentrated positions

### For More Signals: **Option B (RSI < 35)**
- 82.6% win rate (still excellent)
- More opportunities (25 signals/ticker/year)
- Better for diversification

### Both are VALIDATED — Choose Based on Preference:
- **Conservative:** Option A (90% WR)
- **Active:** Option B (83% WR, more signals)

---

## UPDATED TECH PACK

**Strategy ID:** S001-01 (Revised)  
**Entry:** RSI(14) < 30 (or < 35)  
**Exit:** 10-day hold  
**Universe:** 6 HK Bank tickers  
**Status:** ⭐ VALIDATED (both options)  
**Expected Signals:** 90-150 per year (depending on option)

---

**Neither option needs to move to hypothesis bucket — both pass validation criteria.**
