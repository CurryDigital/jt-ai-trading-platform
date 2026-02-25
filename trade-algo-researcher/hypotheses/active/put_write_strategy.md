# Hypothesis: Put-Write Strategy (Covered Put)

**Status:** testing  
**Created:** 2026-02-18  
**Asset Class:** Options  
**Direction:** Short volatility  
**Horizon:** 1 month  
**Target Win Rate:** 75-80%

---

## Core Idea

Sell cash-secured puts on SPY. Collect premium. 75-80% expire worthless. Covered call equivalent.

**Academic Research:**
- PutWrite index (CBOE PUT)
- Outperforms SPY with lower volatility
- 75-80% of puts expire worthless

---

## Signal

**Monthly:**
- Sell 30 DTE SPY put
- Strike at -5% OTM
- Collect ~1% premium

**Exit:**
- Expiration
- Or roll if ITM

---

## Universe

SPY (liquid options)

---

## Expected Performance

| Metric | Target |
|--------|--------|
| Win Rate | 75-80% |
| Annual Return | 8-12% |
| Sharpe | 0.8-1.2 |
| Max DD | 20-25% |

---

## Data

- Options chain
- SPY prices
- Implied volatility

---

## Risk

- Severe drawdowns in crashes
- Assignment in bear markets
- Tail risk

---

*Next: Get options data, backtest put-write 2005-2024.*
