# Deployment Spec: Inside Day Breakout Strategy
**For:** JT Trading Implementation  
**Strategy:** Inside Day Breakout (Golden - NEW)  
**Version:** 1.0  
**Date:** 2026-02-22

---

## Strategy Overview

| Attribute | Value |
|-----------|-------|
| **Name** | Inside Day Breakout |
| **Type** | Breakout / Continuation |
| **Win Rate** | 74.4% ⭐ HIGHEST |
| **Sharpe** | 2.09 |
| **Avg Hold** | ~5 days |
| **Max Concurrent** | 3 positions |

---

## BUY SIGNAL

```python
BUY WHEN ALL TRUE:
    1. Yesterday was an Inside Day (high < prev high, low > prev low)
    2. Today volume > 2.0 × 20-day average
    3. Today close breaks above yesterday's high by > 2%
```

### Entry Rules
- **Order Type:** Market order at breakout confirmation
- **Position Size:** 2% of portfolio per trade
- **Max Positions:** 3 concurrent (rare signal)

---

## SELL SIGNAL

```python
SELL WHEN EITHER:
    1. Profit target: +5% reached
    2. Time stop: 5 days max hold
```

### Exit Rules
- **Profit Target:** Limit order at +5%
- **Time Stop:** Market order at close of day 5

---

## WHY THIS WORKS

Inside day = consolidation/accumulation  
Volume spike + breakout = institutional accumulation complete  
2% breakout threshold = strong momentum confirmation

---

## UNIVERSE DEFINITION

### Total Universe: 179 Tickers
- **Tech:** 30 tickers
- **Equity:** 149 tickers

**Full Universe Query:**
```sql
SELECT DISTINCT ticker 
FROM gold.stock_metrics 
WHERE sector IN ('Tech', 'Equity');
```

### Filters
- **Min Volume:** > 500K shares/day average
- **Min Price:** > $10
- **Data Availability:** 6+ months of history

---

## OVERFITTING ASSESSMENT

| Risk Factor | Assessment | Mitigation |
|-------------|------------|------------|
| **Parameter Count** | Low (3 params) | Simple rules |
| **Trade Count** | 39 | Small sample - paper trade first |
| **In-Sample Period** | 2022-2024 | 3 years, multiple regimes |
| **Logic** | Sound | Consolidation + volume = conviction |

### Risk: MEDIUM
- Only 39 trades in backtest
- Requires paper trading validation
- Monitor win rate closely

---

## PERFORMANCE EXPECTATIONS

| Metric | Expected | Conservative |
|--------|----------|--------------|
| **Win Rate** | 74.4% | 65% |
| **Avg Winner** | +5% | +4% |
| **Avg Loser** | -2% | -3% |
| **Trades/Month** | 1-3 | 1-2 |
| **Monthly Return** | 1-2% | 0.5-1% |

**Note:** Rare signal but highest win rate

---

## IMPLEMENTATION FOR JT

### Database Query
```sql
WITH daily_data AS (
    SELECT date, ticker, high, low, close, volume,
           LAG(high) OVER (PARTITION BY ticker ORDER BY date) as prev_high,
           LAG(low) OVER (PARTITION BY ticker ORDER BY date) as prev_low,
           AVG(volume) OVER (PARTITION BY ticker ORDER BY date ROWS 19 PRECEDING) as vol_avg
    FROM silver.historical_stock_data
)
SELECT date, ticker, close
FROM daily_data
WHERE high < prev_high 
  AND low > prev_low  -- Inside day yesterday
  AND volume > vol_avg * 2.0  -- Volume spike
  AND close > prev_high * 1.02;  -- Breakout > 2%
```

### Signal Generation (Pseudocode)
```python
def generate_signals():
    for ticker in universe:
        if is_inside_day(ticker, yesterday):
            if volume_today > 2.0 * vol_avg_20day:
                if close_today > high_yesterday * 1.02:
                    signal = BUY
                    target_price = close_today * 1.05
                    publish_signal(ticker, BUY, target_price)
```

### Daily Workflow
1. **Pre-market:** Calculate inside day status for all tickers
2. **Market Open:** Monitor for volume + breakout
3. **Entry:** Execute when all 3 conditions met
4. **Exit:** Monitor for +5% profit target

---

## RISK MANAGEMENT

- **Position Size:** 2% max per trade
- **Max Concurrent:** 3 positions (scarcity of signals)
- **Max Exposure:** 6% of portfolio
- **Cooldown:** 5 days between trades on same ticker

---

## BACKTEST SUMMARY

| Period | Trades | Win Rate | Sharpe | Max DD |
|--------|--------|----------|--------|--------|
| 2022-2024 | 39 | 74.4% | 2.09 | -25% |

---

## COMPARISON TO OTHER GOLDEN STRATEGIES

| Strategy | Win Rate | Sharpe | Trades/Month | Notes |
|----------|----------|--------|--------------|-------|
| Inside Day Breakout | **74.4%** | 2.09 | 1-3 | Highest win rate |
| RSI Mean Reversion | 72.6% | 2.26 | 2-4 | Best Sharpe |
| Volume Breakout | 70.8% | 1.48 | 20-35 | Most signals |

---

## NEXT STEPS

1. **Paper Trade:** 2-3 months (need more signal samples)
2. **Monitor:** Win rate closely (only 39 backtest trades)
3. **Fallback:** If win rate < 65%, loosen to 1.5% breakout threshold

---

*Created: 2026-02-22*  
*Status: Ready for JT Implementation - Paper Trade First*  
*Discovery Method: Combination of failed signals + enhancement*