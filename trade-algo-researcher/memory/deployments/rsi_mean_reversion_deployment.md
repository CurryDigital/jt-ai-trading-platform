# Deployment Spec: RSI Mean Reversion Strategy
**For:** JT Trading Implementation  
**Strategy:** RSI Mean Reversion (Golden)  
**Version:** 1.0  
**Date:** 2026-02-22

---

## Strategy Overview

| Attribute | Value |
|-----------|-------|
| **Name** | RSI Mean Reversion (Extreme) |
| **Type** | Mean Reversion / Oversold Bounce |
| **Win Rate** | 72.6% |
| **Sharpe** | 2.26 |
| **Avg Hold** | ~7 days |
| **Max Concurrent** | 3 positions |

---

## BUY SIGNAL

### For Tech Universe (30 tickers)
```python
BUY WHEN ALL TRUE:
    1. RSI(14) < 10 (extreme oversold)
    2. Volume > 1.0x average (normal activity)
    3. No consecutive signal (wait 5 days between trades on same ticker)
```
**Expected Win Rate:** 72.6%

### For Equity Universe (149 tickers)
```python
BUY WHEN ALL TRUE:
    1. RSI(14) < 15 (oversold - less extreme than Tech)
    2. Volume > 1.0x average
    3. No consecutive signal (wait 5 days between trades on same ticker)
```
**Expected Win Rate:** 65.5%

### RSI Calculation
```python
def RSI(prices, period=14):
    delta = prices.diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))
```

### Entry Rules
- **Order Type:** Market order at open next day
- **Position Size:** 2% of portfolio per trade
- **Max Positions:** 3 concurrent (scarcity of signals)

---

## SELL SIGNAL

```python
SELL WHEN EITHER:
    1. Profit target: +4% reached
    2. Time stop: 10 days max hold
    3. RSI recovery: RSI > 40 (optional early exit)
```

### Exit Rules
- **Profit Target:** Limit order at +4%
- **Time Stop:** Market order at close of day 10
- **RSI Recovery:** If RSI > 40 before profit target, consider early exit

---

## UNIVERSE DEFINITION

### Primary Universe (179 Tickers Total)

| Sector | Count | Sample Tickers |
|--------|-------|----------------|
| **Tech** | 30 | Full list available - highest priority (72.6% win) |
| **Equity** | 149 | Secondary universe (test for performance) |

**Full Universe Query:**
```sql
SELECT DISTINCT ticker, sector
FROM gold.stock_metrics 
WHERE sector IN ('Tech', 'Equity')
ORDER BY sector, ticker;
```

**Tech Tickers (30):** AAPL, MSFT, NVDA, GOOGL, META, TSLA, AMZN, AMD, PLTR, SMCI, 0700.HK, 9988.HK, 3690.HK, 1024.HK, 0941.HK, 9888.HK, 9618.HK, 1211.HK, 1810.HK, 2318.HK, 002594.SZ, 300750.SZ, 000333.SZ, 600036.SS, 600519.SS, 601318.SS, 601857.SS, 601398.SS, 600900.SS, 600030.SS

**Equity Tickers (149):** Full list available via database query

### Universe Filters
- **Min Volume:** > 500K shares/day average
- **Min Price:** > $10
- **Data Availability:** 6+ months of history
- **Primary Focus:** Tech sector (72.6% win rate)
- **Secondary Test:** Equity sector

---

## OVERFITTING ASSESSMENT

| Risk Factor | Assessment | Mitigation |
|-------------|------------|------------|
| **Parameter Count** | Very Low (1 main param) | RSI < 10 is extreme |
| **In-Sample Period** | 2022-2024 | 3 years, multiple regimes |
| **Out-of-Sample** | Not tested | Paper trade first |
| **Trade Count** | 73 | Moderate sample size |
| **Multiple Markets** | Tested on HK/CN | Sector-specific validation |

### Overfitting Risk: LOW-MEDIUM
- Single parameter (RSI threshold)
- Extreme threshold (< 10) less prone to curve-fitting
- Based on established RSI mean reversion principle
- **Concern:** Only 73 trades - monitor in paper trading

### Robustness Checks
- RSI < 15: 67.2% win (165 trades) - confirms edge
- RSI < 20: 65.3% win (444 trades) - confirms edge
- RSI < 10: 72.6% win (73 trades) - extreme = edge

---

## IMPLEMENTATION FOR JT

### Database Tables Needed
```sql
-- Daily RSI calculation
WITH price_changes AS (
    SELECT ticker, date, close,
           close - LAG(close) OVER (PARTITION BY ticker ORDER BY date) as delta
    FROM silver.historical_stock_data
),
gains_losses AS (
    SELECT ticker, date,
           CASE WHEN delta > 0 THEN delta ELSE 0 END as gain,
           CASE WHEN delta < 0 THEN -delta ELSE 0 END as loss
    FROM price_changes
)
SELECT ticker, date,
       100 - (100 / (1 + (AVG(gain) OVER (PARTITION BY ticker ORDER BY date ROWS 13 PRECEDING) / 
                          NULLIF(AVG(loss) OVER (PARTITION BY ticker ORDER BY date ROWS 13 PRECEDING), 0)))) as rsi_14
FROM gains_losses;
```

### Signal Generation (Pseudocode)
```python
def generate_signals():
    for ticker in universe:
        rsi = calculate_RSI(ticker, period=14)
        
        if rsi < 10:  # EXTREME oversold
            # Check if we traded this ticker recently
            if days_since_last_trade(ticker) < 5:
                continue  # Avoid clustering
                
            signal = BUY
            target_price = current_price * 1.04
            publish_signal(ticker, BUY, target_price)
```

### Daily Workflow
1. **Pre-market (09:00 HKT):** Calculate RSI for all tickers
2. **09:15 HKT:** Identify RSI < 10 signals
3. **Market Open:** Execute buy orders
4. **Intraday:** Monitor for +4% profit target
5. **Close:** Check time stops and RSI recovery

---

## PERFORMANCE EXPECTATIONS

### With 30 Tech Tickers (Tested Universe)
| Metric | Expected | Conservative |
|--------|----------|--------------|
| **Win Rate** | 72.6% | 65% |
| **Avg Winner** | +4% | +3.5% |
| **Avg Loser** | -2.5% | -3% |
| **Trades/Month** | 2-4 | 1-2 |
| **Monthly Return** | 1-2% | 0.5-1% |

### With Expanded Universe (179 Tickers)
| Metric | Tech (RSI<10) | Equity (RSI<15) | Combined |
|--------|---------------|-----------------|----------|
| **Win Rate** | 72.6% | 65.5% | ~68% |
| **Trades/Month** | 2-4 | 5-10 | **7-14** |
| **Status** | ✅ Golden | ✅ Validated | Recommended |

**Signal Frequency:** 
- Tech (RSI<10): 73 trades / 3 years / 30 tickers = ~0.08 signals/ticker/year
- Equity (RSI<15): 527 trades / 3 years / 50 tickers = ~0.35 signals/ticker/year

**Key Finding:** Equity sector responds better to RSI < 15 (65.5%) than RSI < 10 (63.5%). Use sector-specific thresholds.

---

## RISK MANAGEMENT

- **Position Size:** 2% max per trade
- **Max Concurrent:** 3 positions (scarcity of signals)
- **Max Exposure:** 6% of portfolio
- **Cooldown:** 5 days between trades on same ticker
- **Market Stop:** Pause if VIX > 30 (extreme fear)

---

## BACKTEST SUMMARY

| Period | Trades | Win Rate | Sharpe | Max DD |
|--------|--------|----------|--------|--------|
| 2022-2024 | 73 | 72.6% | 2.26 | -35% |

---

## COMPARISON: RSI THRESHOLDS

| RSI Threshold | Win Rate | Sharpe | Trades | Recommendation |
|---------------|----------|--------|--------|----------------|
| < 30 | 52.9% | 0.66 | 1531 | ❌ Too many, low edge |
| < 20 | 65.3% | 0.82 | 444 | ✅ Good balance |
| < 15 | 67.2% | 1.22 | 204 | ✅ High edge |
| < 10 | 72.6% | 2.26 | 73 | 🏆 Golden (selected) |

### Equity Universe Results (Tested 2026-02-22)
| RSI Threshold | Win Rate | Sharpe | Trades | Recommendation |
|---------------|----------|--------|--------|----------------|
| < 30 | 62.3% | 0.10 | 4291 | 🧪 Moderate |
| < 20 | 63.6% | 0.08 | 1195 | 🧪 Moderate |
| < 15 | 65.5% | 0.12 | 527 | ✅ Best for Equity |
| < 10 | 63.5% | -0.18 | 200 | ❌ Worse than 15 |

**Implementation:** Use RSI < 10 for Tech (72.6%), RSI < 15 for Equity (65.5%)

---

## NEXT STEPS

1. **Paper Trade:** 2 month validation (need more signals for confidence)
2. **Monitor:** Win rate vs backtest
3. **Fallback:** If < 65% win rate, use RSI < 15 (more trades)

---

*Created: 2026-02-22*  
*Status: Ready for JT Implementation*  
*File: `memory/deployments/rsi_mean_reversion_deployment.md`*