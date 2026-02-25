# Hypothesis: Commodity Term Structure (Contango/Backwardation)

**Status:** testing  
**Created:** 2026-02-18  
**Asset Class:** Commodities  
**Direction:** Long/Short based on term structure  
**Horizon:** 1-3 months  
**Target Win Rate:** 60-65%

---

## Core Idea

Commodities in backwardation (spot > futures) generate positive roll yield. Long backwardation, short contango.

**Academic Research:**
- "Term Structure of Commodity Returns"
- Roll yield is significant component of returns
- Backwardation predicts positive returns

---

## Signal

**Backwardation:**
- Spot > 3M futures
- Long commodity (positive roll yield)

**Contango:**
- Spot < 3M futures
- Avoid or short (negative roll yield)

---

## Universe

Crude oil, natural gas, gold, corn, wheat futures

---

## Expected Performance

| Metric | Target |
|--------|--------|
| Win Rate | 60-65% |
| Annual Return | 5-10% |
| Sharpe | 0.6-0.9 |

---

## Data

- Futures curves
- Spot vs futures prices
- Roll yields by commodity

---

## Risk

- Commodity volatility
- Storage cost changes
- Requires futures account

---

*Next: Get futures curve data, calculate term structure, backtest.*
