# Hypothesis: Volatility Skew Trading (Put/Call Imbalance)

**Status:** testing  
**Created:** 2026-02-18  
**Asset Class:** Options  
**Direction:** Long/Short volatility  
**Horizon:** 2-4 weeks  
**Target Win Rate:** 60-65%

---

## Core Idea

When put skew is extreme (puts expensive vs calls), sell puts, buy calls (bullish skew). Mean reversion in skew.

**Academic Research:**
- Options skew mean reverts
- Extreme fear (high put skew) predicts bounce
- 60-65% win rate on skew trades

---

## Signal

**Entry:**
- Put IV > Call IV by >15% (25 delta)
- VIX >25 (fear)
- Sell puts, buy calls (risk reversal)

**Exit:**
- Skew normalizes
- Or 30 DTE

---

## Universe

SPY, QQQ, IWM (liquid options)

---

## Expected Performance

| Metric | Target |
|--------|--------|
| Win Rate | 60-65% |
| Avg Return | 10-15% per trade |
| Sharpe | 1.0-1.4 |

---

## Data

- Options chain (IV by strike)
- VIX level
- Delta, skew calculations

---

## Risk

- Market continues falling (skew extends)
- Assignment on puts
- Requires options approval

---

*Next: Get options chain data, calculate skew, backtest.*
