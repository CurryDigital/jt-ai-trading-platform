# Hypothesis: Intraday First Hour Momentum

**Status:** testing  
**Created:** 2026-02-18  
**Asset Class:** Equities  
**Direction:** Momentum  
**Horizon:** Intraday (2-4 hours)  
**Target Win Rate:** 60-65%

---

## Core Idea

First 30-minute move (09:30-10:00) predicts intraday direction. Strong opening momentum continues through midday.

**Academic Research:**
- "Intraday Trading Edge: First Hour vs Rest of Day"
- Opening range breakout strategies
- 60-65% win rate with proper filters

---

## Signal

**Entry (10:00):**
- If 09:30-10:00 up >0.5% → Long
- If 09:30-10:00 down >0.5% → Short

**Exit (12:00 or 15:30):**
- 2-hour hold or
- Before close to avoid overnight

**Filters:**
- VIX <25 (avoid choppy)
- Above VWAP for longs

---

## Universe

SPY, QQQ, IWM (liquid ETFs)

---

## Expected Performance

| Metric | Target |
|--------|--------|
| Win Rate | 60-65% |
| Avg Win | 0.6% |
| Avg Loss | 0.4% |
| Expectancy | +0.22% per trade |
| Sharpe | 1.5-2.0 |

---

## Data

- Intraday 1-min or 5-min bars
- Real-time VWAP

---

## Risk

- Whipsaws in choppy market
- Requires active monitoring
- Execution speed matters

---

*Next: Get intraday data, backtest first hour momentum.*
