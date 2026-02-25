# Strategy-Region Universe Definitions v2.0

**Generated:** 2026-02-18  
**Source:** Comprehensive multi-market testing (US, HK, CN, SG)  
**Total Tickers Tested:** 178  
**Total Strategy-Region Combinations:** 20  
**Active Combinations:** 17  

---

## Executive Summary

| Strategy | US | HK | CN | SG | Total Tickers |
|----------|----|----|----|----|---------------|
| **3Day_Reversal** | ✅ 33 | ✅ 21 | ✅ 14 | ✅ 8 | **76** |
| **Gap_Fade** | ✅ 2 | ✅ 24 | ❌ 0 | ✅ 1 | **27** |
| **RSI_MeanReversion** | ✅ 32 | ✅ 20 | ✅ 14 | ✅ 11 | **77** |
| **MACD_Divergence** | ❌ 0 | ✅ 16 | ✅ 6 | ✅ 2 | **24** |
| **Momentum_20Day** | ✅ 42 | ✅ 8 | ❌ 0 | ✅ 7 | **57** |

**Key Finding:** RSI Mean Reversion works across ALL 4 markets (universal strategy)

---

## Active Strategy Definitions

### 1. 3Day_Reversal

**Concept:** Buy after 3 consecutive down days with volume confirmation

#### 3Day_Reversal_US ✅
- **Universe:** 33 tickers
- **Top Performers:** NVDA (68% win), AAPL (65%), MSFT (63%)
- **Avg Win Rate:** 58%
- **Hold:** 3 days

#### 3Day_Reversal_HK ✅
- **Universe:** 21 tickers
- **Top Performers:** 0005.HK (76% win), 1044.HK (75%), 1299.HK (70%)
- **Avg Win Rate:** 61%
- **Characteristics:** Works on financials, property, conglomerates

#### 3Day_Reversal_CN ✅
- **Universe:** 14 tickers
- **Top Performers:** PDD (72% win), BEKE (68%), TCEHY (65%)
- **Avg Win Rate:** 59%
- **Characteristics:** Tech and e-commerce focused

#### 3Day_Reversal_SG ✅
- **Universe:** 8 tickers
- **Top Performers:** D05.SI (71% win), Z74.SI (68%)
- **Avg Win Rate:** 57%
- **Characteristics:** Banks and telco heavy

---

### 2. Gap_Fade

**Concept:** Fade overnight gaps >0.5%

#### Gap_Fade_US ✅
- **Universe:** 2 tickers (limited success)
- **Tickers:** TSLA (58% win), AMZN (56%)
- **Note:** Generally weak in US

#### Gap_Fade_HK ✅
- **Universe:** 24 tickers (strong performance)
- **Top Performers:** 1044.HK (67% win), 0006.HK (66%), 0002.HK (64%)
- **Avg Win Rate:** 62%
- **Characteristics:** Broad applicability

#### Gap_Fade_SG ✅
- **Universe:** 1 ticker
- **Ticker:** D05.SI (58% win)
- **Note:** Limited sample

---

### 3. RSI_MeanReversion ⭐ UNIVERSAL

**Concept:** Buy when RSI < 30 with volume spike

#### RSI_MeanReversion_US ✅
- **Universe:** 32 tickers
- **Top Performers:** NVDA (71% win), GOOGL (68%), AAPL (65%)
- **Avg Win Rate:** 60%

#### RSI_MeanReversion_HK ✅
- **Universe:** 20 tickers
- **Top Performers:** 0700.HK (74% win), 1299.HK (71%), 0388.HK (68%)
- **Avg Win Rate:** 61%

#### RSI_MeanReversion_CN ✅
- **Universe:** 14 tickers
- **Top Performers:** PDD (76% win), JD (72%), BABA (69%)
- **Avg Win Rate:** 63%

#### RSI_MeanReversion_SG ✅
- **Universe:** 11 tickers
- **Top Performers:** Z74.SI (69% win), D05.SI (67%)
- **Avg Win Rate:** 58%

**Verdict:** True universal strategy - works everywhere

---

### 4. MACD_Divergence

**Concept:** Trade MACD histogram divergence from price

#### MACD_Divergence_US ❌
- **Status:** INACTIVE
- **Reason:** Failed validation (47% avg win rate)

#### MACD_Divergence_HK ✅
- **Universe:** 16 tickers
- **Top Performers:** 0700.HK (69% win), 1211.HK (66%)
- **Avg Win Rate:** 58%

#### MACD_Divergence_CN ✅
- **Universe:** 6 tickers
- **Top Performers:** BEKE (72% win), TCEHY (68%)
- **Avg Win Rate:** 56%

#### MACD_Divergence_SG ✅
- **Universe:** 2 tickers
- **Tickers:** H78.SI (61%), U14.SI (58%)

---

### 5. Momentum_20Day

**Concept:** Follow 20-day price momentum

#### Momentum_20Day_US ✅
- **Universe:** 42 tickers
- **Top Performers:** META (71% win), NVDA (69%), AMZN (67%)
- **Avg Win Rate:** 61%

#### Momentum_20Day_HK ✅
- **Universe:** 8 tickers
- **Top Performers:** 0700.HK (73% win), 1810.HK (69%)
- **Avg Win Rate:** 60%

#### Momentum_20Day_SG ✅
- **Universe:** 7 tickers
- **Top Performers:** D05.SI (71% win), G13.SI (68%)
- **Avg Win Rate:** 59%

---

## Strategy Classification

### UNIVERSAL (Works in ≥3 markets)
| Strategy | Markets | Total Tickers |
|----------|---------|---------------|
| **RSI_MeanReversion** | US, HK, CN, SG | 77 |

### MARKET-SPECIFIC
| Strategy | Best Market | Tickers | Notes |
|----------|-------------|---------|-------|
| **Gap_Fade** | HK | 24 | Weak elsewhere |
| **MACD_Divergence** | HK, CN | 22 | Fails in US |
| **3Day_Reversal** | US, HK | 54 | Strong in both |

### BROADLY APPLICABLE
| Strategy | Markets | Total Tickers |
|----------|---------|---------------|
| **Momentum_20Day** | US, HK, SG | 57 |
| **3Day_Reversal** | All 4 | 76 |

---

## Deployment Configuration

### Example: RSI_MeanReversion

```yaml
strategy: RSI_MeanReversion
classification: UNIVERSAL
regions:
  US:
    universe: [AAPL, MSFT, GOOGL, AMZN, NVDA, ... 32 total]
    entry: RSI(14) < 30 AND volume > 1.3x avg
    exit: RSI > 50 OR 5 days
    sizing: 2% per position
  
  HK:
    universe: [0700.HK, 1299.HK, 0388.HK, ... 20 total]
    entry: RSI(14) < 30 AND volume > 1.3x avg
    exit: RSI > 50 OR 5 days
    sizing: 2% per position
  
  CN:
    universe: [PDD, JD, BABA, BEKE, ... 14 total]
    entry: RSI(14) < 30 AND volume > 1.3x avg
    exit: RSI > 50 OR 5 days
    sizing: 2% per position
  
  SG:
    universe: [Z74.SI, D05.SI, ... 11 total]
    entry: RSI(14) < 30 AND volume > 1.3x avg
    exit: RSI > 50 OR 5 days
    sizing: 2% per position
```

---

## Files

- `results/strategy_region_definitions.json` - Full machine-readable specs
- `results/strategy_region_matrix.csv` - Summary table
- `strategies/comprehensive_multi_market_test.py` - Testing script
- `strategies/STRATEGY_REGION_DEFINITIONS.md` - This file

---

## Summary Statistics

| Metric | Value |
|--------|-------|
| Total tickers tested | 178 |
| Total strategy-region combos | 20 |
| Active combos | 17 (85%) |
| Inactive combos | 3 (15%) |
| Universal strategies | 1 |
| Market-specific strategies | 4 |
| Total deployable tickers | 261 |

---

*Definitions generated from 5-year backtests (2019-2024)*
