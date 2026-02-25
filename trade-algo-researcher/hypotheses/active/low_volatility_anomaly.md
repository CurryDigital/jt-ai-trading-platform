# Hypothesis: Low Volatility Anomaly (Betting Against Beta)

**Status:** testing  
**Created:** 2026-02-18  
**Asset Class:** Equities  
**Direction:** Long low vol, short high vol  
**Horizon:** 1 month  
**Target Win Rate:** 58-62%

---

## Core Idea

Low volatility stocks outperform high volatility on risk-adjusted basis. Betting against beta generates alpha.

**Academic Research:**
- Frazzini & Pedersen (2014): Betting Against Beta
- Low volatility anomaly
- USMV outperforms SPY with lower risk

---

## Signal

**Monthly rebalance:**
- Calculate 1-year volatility for S&P 500
- Long lowest decile (USMV)
- Short highest decile (SPHB)

---

## Universe

S&P 500 constituents

---

## Expected Performance

| Metric | Target |
|--------|--------|
| Win Rate | 58-62% |
| Annual Return | 4-8% |
| Sharpe | 0.8-1.2 |
| Beta | 0.5 |

---

## Data

- Stock prices
- 252-day volatility
- Decile rankings

---

## Risk

- Underperforms in strong bull markets
- Requires shorting
- Crowding in low vol factor

---

*Next: Backtest BAB factor 2000-2024.*
