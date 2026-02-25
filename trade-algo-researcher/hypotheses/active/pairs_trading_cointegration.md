# Hypothesis: Pairs Trading (Cointegration-Based)

**Status:** testing  
**Created:** 2026-02-18  
**Asset Class:** Equities  
**Direction:** Neutral  
**Horizon:** 1-5 days  
**Target Win Rate:** 60-65%

---

## Core Idea

Two historically correlated stocks diverge temporarily. Short outperformer, long underperformer. Capture convergence.

**Academic Research:**
- Gatev, Goetzmann, Rouwenhorst (2006): Pairs trading returns
- Cointegration-based pairs 60-65% win rate
- Requires careful pair selection

---

## Signal

**Pairs:**
- PEP/KO (beverages)
- XOM/CVX (oil majors)
- JPM/BAC (banks)
- HD/LOW (retail)

**Entry:**
- Z-score of spread >2.0
- Short expensive, long cheap

**Exit:**
- Z-score returns to 0
- Or 5-day hold

---

## Universe

Liquid pairs with economic rationale

---

## Expected Performance

| Metric | Target |
|--------|--------|
| Win Rate | 60-65% |
| Avg Return | 1-2% per trade |
| Sharpe | 1.0-1.5 |

---

## Data

- Historical prices
- Cointegration tests
- Z-score calculation

---

## Risk

- Fundamental divergence (pair breaks)
- Requires shorting
- Correlation breakdown

---

*Next: Test pairs for cointegration, backtest 2019-2024.*
