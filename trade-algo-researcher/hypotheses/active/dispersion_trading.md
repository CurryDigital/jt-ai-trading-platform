# Hypothesis: Dispersion Trading (Index vs Components)

**Status:** testing  
**Created:** 2026-02-18  
**Asset Class:** Options  
**Direction:** Neutral  
**Horizon:** 1-4 weeks  
**Target Win Rate:** 65-70%

---

## Core Idea

Sell index options (SPY), buy single-stock options (components). Captures implied correlation premium — index IV trades rich to realized correlation.

**Academic Research:**
- "Dispersion Trading" — Quantpedia
- Index IV consistently overprices realized correlation
- 65-70% win rate with proper hedging

---

## Signal

**Entry:**
- Sell SPY straddle (30 DTE)
- Buy component straddles (same expiration)
- Weighted by index weights
- When implied correlation >60%

**Exit:**
- 7 days to expiration
- Or correlation reverts to <40%

---

## Universe

SPY vs top 50 components

---

## Expected Performance

| Metric | Target |
|--------|--------|
| Win Rate | 65-70% |
| Avg Return | 2-4% per month |
| Sharpe | 1.0-1.5 |

---

## Data

- Options chain data (delta, gamma, IV)
- Component weights
- Correlation matrix

---

## Risk

- Correlation spike (market crash)
- Single-stock blowups
- Execution complexity

---

*Next: Collect options data, backtest dispersion trades.*
