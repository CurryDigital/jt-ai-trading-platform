# Data Request to JT Trading
**Date:** 2026-02-22  
**From:** Trade Algo Researcher  
**To:** JT Trading Team  
**Priority:** Medium

---

## Purpose
Request additional technical indicator data to test 5 hypotheses that were skipped due to missing data.

---

## Data Requirements

### 1. ADX (Average Directional Index)
**For Hypothesis:** ADX Trend Strength Strategy

**Required Fields:**
- Ticker
- Date
- ADX(14) value
- +DI(14) value
- -DI(14) value

**Calculation:**
```python
# Standard ADX calculation
TR = max(high - low, abs(high - prev_close), abs(low - prev_close))
+DM = high - prev_high if (high - prev_high) > (prev_low - low) else 0
-DM = prev_low - low if (prev_low - low) > (high - prev_high) else 0

+DI = 100 * SMA(+DM, 14) / SMA(TR, 14)
-DI = 100 * SMA(-M, 14) / SMA(TR, 14)
DX = 100 * abs(+DI - -DI) / (+DI + -DI)
ADX = SMA(DX, 14)
```

**Universe:** All 401 tickers  
**History:** 2020-01-01 to present

---

### 2. Stochastic Oscillator
**For Hypothesis:** Stochastic Oversold Strategy

**Required Fields:**
- Ticker
- Date
- %K (fast, period 14)
- %D (slow, period 3)

**Calculation:**
```python
Lowest_Low = min(low, 14)
Highest_High = max(high, 14)

%K = 100 * (close - Lowest_Low) / (Highest_High - Lowest_Low)
%D = SMA(%K, 3)
```

**Universe:** All 401 tickers  
**History:** 2020-01-01 to present

---

### 3. MACD Histogram
**For Hypothesis:** MACD Histogram Divergence Strategy

**Required Fields:**
- Ticker
- Date
- MACD Line (12, 26)
- Signal Line (9)
- Histogram (MACD - Signal)

**Calculation:**
```python
EMA12 = EMA(close, 12)
EMA26 = EMA(close, 26)
MACD_Line = EMA12 - EMA26
Signal_Line = EMA(MACD_Line, 9)
Histogram = MACD_Line - Signal_Line
```

**Universe:** All 401 tickers  
**History:** 2020-01-01 to present

---

### 4. Parabolic SAR
**For Hypothesis:** Parabolic SAR Flip Strategy

**Required Fields:**
- Ticker
- Date
- PSAR value
- PSAR direction (bull/bear)

**Calculation:**
```python
# Standard Parabolic SAR
AF = 0.02 (acceleration factor)
Max AF = 0.20

If bullish:
    PSAR = Prior PSAR + AF * (Prior EP - Prior PSAR)
If bearish:
    PSAR = Prior PSAR - AF * (Prior EP - Prior PSAR)
```

**Universe:** All 401 tickers  
**History:** 2020-01-01 to present

---

### 5. Volume Profile / Point of Control (POC)
**For Hypothesis:** Volume Profile POC Strategy

**Required Fields:**
- Ticker
- Date
- POC price (price with highest volume)
- Value Area High (70% of volume)
- Value Area Low (70% of volume)
- Volume at each price level (histogram)

**Note:** Requires intraday data (hourly or daily OHLCV with volume by price)

**Calculation:**
```python
# Aggregate volume by price level
VolumeProfile = defaultdict(float)
for each bar in lookback_period:
    VolumeProfile[price] += volume

POC = price with max(VolumeProfile)
TotalVolume = sum(VolumeProfile.values())

# Find Value Area (70% of total volume)
sorted_prices = sort(VolumeProfile by volume descending)
cumulative = 0
ValueArea = []
for price in sorted_prices:
    cumulative += VolumeProfile[price]
    ValueArea.append(price)
    if cumulative >= TotalVolume * 0.7:
        break

ValueAreaHigh = max(ValueArea)
ValueAreaLow = min(ValueArea)
```

**Universe:** All 401 tickers  
**History:** 2020-01-01 to present  
**Data Type:** Daily or intraday volume profile

---

## Schema Suggestion

### Option 1: New Table per Indicator
```sql
-- gold.adx_data
CREATE TABLE gold.adx_data (
    ticker VARCHAR(20),
    date DATE,
    adx_14 DECIMAL(10,4),
    plus_di_14 DECIMAL(10,4),
    minus_di_14 DECIMAL(10,4),
    PRIMARY KEY (ticker, date)
);

-- gold.stochastic_data
CREATE TABLE gold.stochastic_data (
    ticker VARCHAR(20),
    date DATE,
    k_fast DECIMAL(10,4),
    d_slow DECIMAL(10,4),
    PRIMARY KEY (ticker, date)
);

-- gold.macd_data
CREATE TABLE gold.macd_data (
    ticker VARCHAR(20),
    date DATE,
    macd_line DECIMAL(10,4),
    signal_line DECIMAL(10,4),
    histogram DECIMAL(10,4),
    PRIMARY KEY (ticker, date)
);

-- gold.psar_data
CREATE TABLE gold.psar_data (
    ticker VARCHAR(20),
    date DATE,
    psar_value DECIMAL(10,4),
    direction VARCHAR(10), -- 'bull' or 'bear'
    PRIMARY KEY (ticker, date)
);

-- gold.volume_profile
CREATE TABLE gold.volume_profile (
    ticker VARCHAR(20),
    date DATE,
    poc_price DECIMAL(10,4),
    value_area_high DECIMAL(10,4),
    value_area_low DECIMAL(10,4),
    PRIMARY KEY (ticker, date)
);
```

### Option 2: Extend Existing stock_metrics Table
```sql
ALTER TABLE gold.stock_metrics ADD COLUMN adx_14 DECIMAL(10,4);
ALTER TABLE gold.stock_metrics ADD COLUMN stochastic_k DECIMAL(10,4);
ALTER TABLE gold.stock_metrics ADD COLUMN macd_histogram DECIMAL(10,4);
ALTER TABLE gold.stock_metrics ADD COLUMN psar_value DECIMAL(10,4);
```

---

## Priority Order

1. **MACD** (Highest priority - commonly used)
2. **Stochastic** (High priority - mean reversion)
3. **ADX** (Medium priority - trend strength)
4. **PSAR** (Medium priority - trailing stops)
5. **Volume Profile** (Lower priority - requires more complex data)

---

## Hypotheses to Test Once Data Available

| # | Hypothesis | Indicator Needed | Expected Impact |
|---|------------|------------------|-----------------|
| 30 | ADX Trend Strength | ADX | Trend following |
| 31 | Stochastic Oversold | Stoch | Mean reversion |
| 32 | MACD Histogram Div | MACD | Momentum |
| 33 | Parabolic SAR Flip | PSAR | Trend following |
| 37 | Volume Profile POC | Volume Profile | Support/Resistance |

---

## Alternative: Calculate from Existing Price Data

If external data import is difficult, these can be calculated from existing `silver.historical_stock_data`:

```sql
-- Example: Calculate MACD from existing prices
WITH ema_calc AS (
    SELECT 
        ticker,
        date,
        close,
        -- EMA12 and EMA26 would need recursive/window function
    FROM silver.historical_stock_data
)
SELECT * FROM ema_calc;
```

**Recommendation:** Pre-calculate and store in gold schema for query performance.

---

## Timeline Request

| Priority | Indicator | Requested By |
|----------|-----------|--------------|
| P1 | MACD | 1 week |
| P1 | Stochastic | 1 week |
| P2 | ADX | 2 weeks |
| P2 | PSAR | 2 weeks |
| P3 | Volume Profile | 1 month |

---

## Contact

Questions? Contact Trade Algo Researcher.

---

*Requested: 2026-02-22*  
*Status: Pending JT Trading Team*  
*Blocking: 5 hypothesis tests*