# Hypothesis: Bond Futures Calendar Spread (Steepener/Flattener)

**Status:** testing  
**Created:** 2026-02-18  
**Asset Class:** Rates  
**Direction:** Long/Short spread  
**Horizon:** 1-3 months  
**Target Win Rate:** 65-70%

---

## Core Idea

Trade yield curve shape (2s10s, 5s30s). When curve steepens, long short-duration bonds, long long-duration. When flattens, reverse.

**Academic Research:**
- Yield curve as recession predictor
- Curve steepening post-Fed pause
- 65-70% win rate on curve trades

---

## Signal

**Entry:**
- 2s10s spread >200bps → Expect flattening (short 10Y, long 2Y)
- 2s10s spread <50bps → Expect steepening (long 10Y, short 2Y)

**Futures:**
- TU (2Y), FV (5Y), TY (10Y), US (30Y)

---

## Universe

Treasury futures: /ZT, /ZF, /ZN, /ZB

---

## Expected Performance

| Metric | Target |
|--------|--------|
| Win Rate | 65-70% |
| Avg Return | 2-4% per trade |
| Sharpe | 0.9-1.3 |

---

## Data

- Treasury yield data
- Fed policy expectations
- Futures prices

---

## Risk

- Fed surprise moves
- Flight to quality flattens curve
- Requires futures account

---

*Next: Get yield curve data, backtest curve trades 2015-2024.*
