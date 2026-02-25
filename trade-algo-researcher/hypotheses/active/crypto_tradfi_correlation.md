# Hypothesis: Crypto-TradFi Correlation Breakdown

**Status:** testing  
**Created:** 2026-02-18  
**Asset Class:** Cross-Asset (Crypto + Equities)  
**Direction:** Pairs trade during correlation regime shifts  
**Horizon:** 1-4 weeks  
**Target Win Rate:** 60-65%

---

## Core Idea

BTC and NASDAQ correlate (~0.6) during risk-on/risk-off. But correlation breaks during:
- Crypto-specific events (halving, ETF approval)
- TradFi crises (BTC as hedge)
- Regulatory news

**The Edge:**
- Detect correlation regime shifts
- Trade the mean reversion when correlation normalizes
- Exploit relative value dislocations

---

## Regime Detection

**High Correlation Regime:**
- BTC-NQ correlation >0.5
- Macro drives both
- Risk-on/risk-off

**Low Correlation Regime:**
- BTC-NQ correlation <0.2
- Crypto idiosyncratic
- Trade crypto-specific premium/discount

---

## Signal Construction

**From High → Low Correlation:**
```
IF rolling_30d_correlation drops below 0.2 AND
   was above 0.5 AND
   BTC_up_NQ_down OR BTC_down_NQ_up
THEN trade convergence:
   - If BTC lagging: Long BTC, Short NQ
   - If NQ lagging: Long NQ, Short BTC
```

**Reversion Window:**
- Regime shifts last 1-4 weeks
- Correlation mean reverts to 0.4-0.6
- Close when correlation >0.4

---

## Expected Performance

| Metric | Target |
|--------|--------|
| Win Rate | 60-65% |
| Avg Return | 8-15% per trade |
| Sharpe | 1.2-1.8 |

---

## Data Requirements

- BTC prices
- NQ (Nasdaq futures) prices
- Rolling 30-day correlation
- Regime detection (HMM or thresholds)

---

## Why It Works

1. **Two fundamentally different assets** — Temporary correlation breakdown
2. **Different investor bases** — Crypto natives vs TradFi
3. **Reversion to mean correlation** — ~0.5 long-term
4. **Market inefficiency** — Two markets with different information

---

## Risk

- Correlation can stay broken (regime change)
- Requires both crypto and equity accounts
- Basis risk during convergence

---

*Trade the gap between digital gold and tech stocks.*
