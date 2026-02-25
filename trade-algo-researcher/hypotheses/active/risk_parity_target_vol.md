# Hypothesis: Risk Parity with Target Volatility

**Status:** testing  
**Created:** 2026-02-18  
**Asset Class:** Cross-Asset  
**Direction:** Long  
**Horizon:** Long-term (monthly rebalance)  
**Target Win Rate:** 60% (positive years)

---

## Core Idea

Equal risk contribution from stocks, bonds, commodities. Scale exposure to target 10% volatility. Improves Sharpe vs traditional 60/40.

**Academic Research:**
- Bridgewater All Weather Fund
- "Volatility Targeting Improves Risk-Adjusted Returns" (Alpha Architect)
- Dalio: Risk parity outperforms in all environments

---

## Signal

**Allocation (equal risk):**
- 25% Equities (SPY)
- 25% Long Bonds (TLT)
- 25% Gold (GLD)
- 25% Commodities (DBC)

**Volatility Scaling:**
- Target 10% annual volatility
- Scale positions inversely to recent vol (30-day)
- Reduce size when VIX >30

---

## Universe

SPY, TLT, GLD, DBC

---

## Expected Performance

| Metric | Target |
|--------|--------|
| Annual Return | 8-10% |
| Volatility | 10% (target) |
| Sharpe | 0.8-1.0 |
| Max DD | <15% |

---

## Data

- Daily prices
- 30-day rolling volatility
- VIX for regime filter

---

## Risk

- Rising rate environment hurts bonds
- Correlation breakdown in crisis
- Leverage required for bonds

---

*Next: Backtest risk parity with vol targeting 2010-2024.*
