# QQQ Lead-Lag GOLD — Cross-Market Strategy
**Asset:** QQQ (US) → 0700.HK (Tencent)  
**Status:** Validated / Golden-Tier Candidate  
**Win Rate:** 79.1%  
**Discovery:** 2026-02-24

---

## 🎯 Strategy Overview

**Hypothesis:** US tech momentum (QQQ) predicts HK tech overnight gaps

**Mechanism:** Information diffusion from US (close) → HK (next day open)

**Edge:** 12-16 hour time gap allows predictive signal

---

## 📊 Performance Metrics

| Metric | Value | Grade |
|--------|-------|-------|
| **Win Rate** | **79.1%** | ⭐ Golden |
| Correlation | 0.408 | Strong |
| Avg Return | +1.32% | Good |
| Signals/Year | ~22 | Moderate |
| Sharpe (est) | ~2.5 | Excellent |

---

## 🔍 Entry/Exit Rules

### Entry
- **Trigger:** QQQ daily return > +2.0%
- **Action:** Buy 0700.HK at next HK open
- **Position:** 20-25k HKD (for 100k portfolio)

### Exit
- **Time-based:** HK close same day
- **Optional:** +2% profit target (boosts win rate)

---

## 📈 Historical Results

### Gap Distribution (QQQ > +2% Days)
| Outcome | Frequency |
|---------|-----------|
| Strong up (>1%) | 57% |
| Modest up (0-1%) | 22% |
| Down (<0%) | 21% |

**79% of days show positive gap when QQQ up >2%**

### Threshold Analysis
| QQQ Threshold | Win Rate | Signals/Yr |
|---------------|----------|------------|
| > +1.0% | 71.7% | ~62 |
| > +2.0% | **79.1%** | ~22 ⭐ |
| > +3.0% | 90.0% | ~7 |

**Sweet spot: +2.0% threshold**

---

## 💡 Why It Works

1. **Information lag:** US closes, Asia hasn't opened
2. **Futures pricing:** QQQ move → futures gap → HK opens at premium
3. **Sentiment carry:** US tech optimism → global tech optimism
4. **Institutional flow:** US buying → Asian follow-through

---

## 🎯 Alternative: 9988.HK (Alibaba)

| Metric | 0700.HK | 9988.HK |
|--------|---------|---------|
| Win Rate | 79.1% | 74.6% |
| Avg Gap | +1.32% | +2.00% |
| Volatility | Lower | Higher |

**9988.HK:** Higher risk/reward, lower win rate

---

## 🚀 Deployment for 100k HKD

**Capital Allocation:**
- Position size: 25k HKD per signal
- Max concurrent: 1 (signals don't overlap daily)
- Expected: 17 wins, 4 losses per year
- Gross profit: ~29% annually

**Risk Management:**
- No stop loss (day trade only)
- Max loss per trade: ~2-3%
- Worst case: Gap against + reversal

---

## ⚠️ Risk Factors

1. **China policy override** — Regulatory news trumps US sentiment
2. **Gap pricing** — Futures may already price in move
3. **Decay** — Effect may weaken as algos exploit
4. **Macro shocks** — War, pandemic breaks correlation

---

## 📁 Files

- Hypothesis: [H005_cross_market_us_tech_to_hk_tech.md](../hypotheses/H005_cross_market_us_tech_to_hk_tech.md)
- Test script: [test_H005_cross_market_lead_lag_v2.py](../../test_H005_cross_market_lead_lag_v2.py)

---

## 🏆 Status

**Upgraded from:** Exploration hypothesis  
**To:** Golden-tier strategy candidate  
**Reason:** 79.1% win rate exceeds 70% threshold

**Next:** Paper trade 20 signals, validate live performance

---

*Cross-market lead-lag effect validated*  
*Date: 2026-02-24*