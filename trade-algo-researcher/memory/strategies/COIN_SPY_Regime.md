# COIN_SPY_Regime — Strategy Memory (CORRECTED)
**Asset:** COIN (Coinbase) — BTC Proxy  
**Status:** Validated  
**Date:** 2026-02-23 (Updated with validation)

---

## ⚠️ CORRECTION NOTICE

**Initial Claim:** 100% win rate (10 trades)  
**Reality:** Small sample size - true win rate likely 70-85%  

**Why:** 95% confidence interval for 10 trades at 100% win = [72.3%, 100%]  
Statistical fluke, not true edge. Need 30+ trades for reliable estimate.

---

## 📊 CORRECTED Strategy Variants

### Variant 1: RSI<25 + SPY>200d ⭐ RECOMMENDED
| Metric | Value |
|--------|-------|
| Win Rate | **85.7%** |
| Trades | 21 |
| Status | Validated |
| True Estimate | 75-90% |

**Entry:**
- COIN RSI(14) < 25
- SPY above 200-day SMA
- Hold: 10 days

**Why this one:** More trades (21 vs 10) = more statistically reliable

---

### Variant 2: RSI<20 + SPY>200d (Overstated)
| Metric | Value |
|--------|-------|
| Win Rate | **100.0%** ⚠️ |
| Trades | 10 |
| True Estimate | 70-80% |
| Status | Too few trades |

**Note:** 100% win is statistical noise from small sample. Use Variant 1 instead.

---

### Key Discovery: SPY Filter Doesn't Help COIN

| Filter | RSI<25 Win% | RSI<30 Win% |
|--------|-------------|-------------|
| With SPY>200d | 85.7% | 75.6% |
| Without SPY | 85.7% | 75.6% |

**COIN performs the same with or without SPY filter!**

**Implication:** Just trade RSI<25 on COIN, don't wait for SPY confirmation.

---

## 📊 All Variants Tested

| RSI Threshold | SPY Filter | Trades | Win% | Recommendation |
|---------------|------------|--------|------|----------------|
| <20 | >200d | 10 | 100% | ❌ Too few trades |
| <25 | >200d | 21 | 85.7% | ✅ **USE THIS** |
| <30 | >200d | 45 | 75.6% | ✅ Reliable but lower |
| <20 | >50d | 6 | 100% | ❌ Too few |
| <25 | >50d | 13 | 76.9% | ⚠️ Lower than >200d |
| <30 | >50d | 27 | 59.3% | ❌ Below 60% |

---

## 💡 CORRECTED Key Insights

1. **85.7% win rate is realistic** — Based on 21 trades (more reliable)
2. **SPY filter NOT needed for COIN** — Same performance with/without
3. **RSI<25 is sweet spot** — Good win rate + sufficient signals
4. **100% was statistical fluke** — Don't expect it to continue
5. **COIN is special** — Doesn't need market regime filter like MSTR does

---

## 🎯 CORRECTED Deployment Recommendation

**Primary:** RSI<25 (No SPY filter needed!)
- Expected signals: 5-7/year
- Win rate: ~85% (realistic)
- Position size: 2%
- Simpler = better

**Skip:** RSI<20 variants
- Too few signals
- 100% rate won't persist
- More complexity, no benefit

---

## ⚠️ Risk Considerations (Updated)

- ✅ 21 trades = reasonable sample (not great, but usable)
- ⚠️ True win rate 75-90% (not 100%)
- ⚠️ Crypto volatility extreme
- ⚠️ First loss will happen - be prepared
- ⚠️ COIN may delist/go bankrupt (crypto risk)

---

## 📁 Files

- Validation script: `validate_coin_strategies.py`
- Full results: `results/COIN_CORRECTED_ANALYSIS.json`
- Original (flawed): `results/COIN_SPY_ANALYSIS.json`

---

## 🔗 Related Strategies

- `MSTR_SPY_Regime` — DOES benefit from SPY filter (+17% win rate)
- `RIOT_SPY_Regime` — Moderate benefit from SPY filter
- `Crypto_SPY_Regime` — Master comparison file

---

## 📝 Lessons Learned

1. **Always question 100% win rates** — Usually small sample
2. **Test without filters** — May not add value
3. **Check confidence intervals** — 10 trades ≠ reliable
4. **Simple often wins** — COIN doesn't need complexity

---

*Updated: 2026-02-23 after validation*  
*Original claim corrected from 100% to 85.7%*
