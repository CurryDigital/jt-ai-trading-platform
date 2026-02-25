# Honest Assessment: Backtesting Status

**Date:** 2026-02-21  
**Purpose:** Clarify what was actually backtested vs pre-populated

---

## ⚠️ CRITICAL DISCLOSURE

You asked a great question. Let me be completely transparent:

### What I Actually Backtested Myself

| Strategy | Trades | Sharpe | Status | Notes |
|----------|--------|--------|--------|-------|
| **3-Day Reversal** | 281 | 2.06 | ✅ VALIDATED | Proper test |
| **Sector Rotation Tech/Util** | 705 | 1.24 | ✅ VALIDATED | Proper test |
| **Momentum Lifecycle** | 4,953 | 1.15 | ✅ VALIDATED | Proper test |
| **RSI Mean Reversion** | 558 | 0.98 | 🧪 TESTING | Close but below 1.0 |
| **Engulfing Pattern** | 706 | 0.49 | ❌ FAILED | Below threshold |
| **Gap Fade HK** | 3,061 | -1.83 | ❌ FAILED | Negative Sharpe |
| **Volume Spike** | 494 | 0.31 | ❌ FAILED | Below threshold |
| **Time-Series Momentum** | 1,547 | -0.01 | ❌ FAILED | No edge |
| **Moving Average Cross** | 138 | -0.46 | ❌ FAILED | Negative |
| **Accruals Quality** | 8 | -0.50 | ❌ FAILED | Insufficient data |
| **China AI Chip** | 12 | 0.78 | 🧪 TESTING | Proxy data (HK tickers) |
| **Singapore Banking** | 2 | 0.55 | 🧪 TESTING | Proxy data (HSBC/AIA) |

**Total I Backtested: 12 strategies  
Actually Validated: 3 strategies**

---

### The Problem: Pre-Populated Data

**The other 20+ strategies** in your deployed list (like Gap Fade HK, AH Premium, etc.) came from:

```sql
SELECT * FROM gold.strategy_definitions
```

These were **already in the database** when I started. I did NOT backtest these myself.

### Strategies I Did NOT Backtest (Pre-Populated)

| Strategy | Listed Sharpe | Source | My Verification |
|----------|---------------|--------|-----------------|
| Gap Fade (HK) | 3.45 | Pre-populated | ❌ NOT VERIFIED BY ME |
| AH Premium Arbitrage | 2.33 | Pre-populated | ❌ NOT VERIFIED BY ME |
| SG REIT Dividend | 0.73 | Pre-populated | ❌ NOT VERIFIED BY ME |
| Crypto Funding | 2.50 | Pre-populated | ❌ NOT VERIFIED BY ME |
| ARASO Factor | 2.40 | Pre-populated | ❌ NOT VERIFIED BY ME |
| Info Arbitrage | 1.80 | Pre-populated | ❌ NOT VERIFIED BY ME |
| FX Carry | 1.20 | Pre-populated | ❌ NOT VERIFIED BY ME |
| Gold/Silver | 1.11 | Pre-populated | ❌ NOT VERIFIED BY ME |
| ALL RSI variants | 1.10-1.35 | Pre-populated | ❌ NOT VERIFIED BY ME |

---

### The Risk Parameter Research

My risk parameter recommendations were based on:

1. **Academic research** (Jegadeesh & Titman for momentum, etc.)
2. **Volatility analysis** of the 12 strategies I did test
3. **Asset class characteristics** (FX vs equities vs crypto)
4. **Time horizon** (intraday vs monthly)

**BUT:** I did NOT backtest every strategy with the new parameters.

---

## What This Means

### For the 3 Validated Strategies (My Backtests)
- 3-Day Reversal: Properly tested, 2.06 Sharpe ✅
- Sector Rotation: Properly tested, 1.24 Sharpe ✅
- Momentum Lifecycle: Properly tested, 1.15 Sharpe ✅

### For the Pre-Populated Strategies
- Sharpe ratios came from someone else's backtests
- I don't know their methodology
- Risk parameters may be wrong
- **These need independent verification**

### For the Risk Parameters
- General guidance based on asset class and horizon
- Not backtested for each specific strategy
- May need tuning

---

## Recommended Actions

1. **Audit the pre-populated strategies:**
   - Re-backtest Gap Fade HK (failed in my test)
   - Verify AH Premium with actual dual-listed data
   - Test SG REIT with dividend calendar

2. **Validate risk parameters:**
   - Run fresh backtests with new targets/stops
   - Compare win rates vs old parameters
   - Start with 3 validated strategies

3. **Be cautious with deployment:**
   - Many strategies deployed without my verification
   - Gap Fade HK shows -1.83 Sharpe but is deployed!

---

## Bottom Line

**I backtested 12 strategies, only 3 passed.**  
**The other 20+ in your deployed list came pre-populated and need verification.**

My risk parameter research is theoretical/academic guidance, not proven for each strategy.

---

*Full transparency. Let me know how you'd like to proceed.*
