# Hypothesis: Cross-Sectional Momentum (Industry Neutral)

**Status:** testing  
**Created:** 2026-02-18  
**Asset Class:** Equities  
**Direction:** Long/Short  
**Horizon:** 1 month  
**Target Win Rate:** 60-65%

---

## Core Idea

Long top 10% momentum stocks, short bottom 10%, within each industry. Neutralizes sector risk, captures stock-specific momentum.

**Academic Research:**
- "Mo' Momentum, Mo' Problems?" (Man Group)
- Moskowitz & Grinblatt (1999): Industry momentum
- Carhart (1997): Momentum factor

---

## Signal

**Monthly rebalance:**
- Calculate 12-month momentum for each stock
- Rank within industry (GICS)
- Long top decile, short bottom decile
- Equal weight within legs

---

## Universe

S&P 500 + mid-cap (liquid only)

---

## Expected Performance

| Metric | Target |
|--------|--------|
| Win Rate | 60-65% (monthly) |
| Annual Return | 6-10% |
| Sharpe | 0.8-1.2 |
| Beta | ~0 (market neutral)

---

## Data

- Stock prices
- GICS industry classifications
- Monthly rebalance dates

---

## Risk

- Momentum crashes (2009, 2021)
- Requires shorting
- Transaction costs

---

*Next: Get S&P 500 + GICS data, backtest industry-neutral momentum.*
