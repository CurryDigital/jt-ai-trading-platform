# REQUIRED METRICS FOR gold.technical_indicators_calculated
**For:** SPY, MSTR, COIN, MARA, RIOT (and QQQ, IWM)  
**Source:** silver.unified_prices (open, high, low, close, volume)  
**Date Range:** 2021-01-01 to 2026-02-20

---

## 📊 REQUIRED COLUMNS

### Core Identifiers
| Column | Type | Source |
|--------|------|--------|
| `date` | DATE | silver.unified_prices.date |
| `ticker` | VARCHAR | silver.unified_prices.ticker |

### 1. RSI (Relative Strength Index)
| Column | Type | Calculation | Used In |
|--------|------|-------------|---------|
| `rsi_14` | DECIMAL(10,2) | RSI(14) on close prices | RSI MR, BB+RSI, 3-Day Reversal, etc. |

**Formula:** RSI = 100 - (100 / (1 + RS)), where RS = Avg Gain / Avg Loss over 14 periods

---

### 2. Bollinger Bands
| Column | Type | Calculation | Used In |
|--------|------|-------------|---------|
| `bb_upper` | DECIMAL(12,4) | SMA20 + (2 × StdDev20) | BB+Monday GOLD, BB Lower+RSI |
| `bb_middle` | DECIMAL(12,4) | SMA20 | BB width calculations |
| `bb_lower` | DECIMAL(12,4) | SMA20 - (2 × StdDev20) | BB+Monday GOLD, BB Lower+RSI |

**Period:** 20-day SMA with 2 standard deviations

---

### 3. Volume Metrics
| Column | Type | Calculation | Used In |
|--------|------|-------------|---------|
| `vol_ratio` | DECIMAL(10,2) | Volume / SMA(Volume, 20) | Volume Breakout, BB+Monday, 3-Day Reversal |
| `volume_sma_20` | DECIMAL(15,2) | SMA(Volume, 20) | Base for vol_ratio |

---

### 4. MACD (Moving Average Convergence Divergence)
| Column | Type | Calculation | Used In |
|--------|------|-------------|---------|
| `macd_line` | DECIMAL(10,4) | EMA(12) - EMA(26) | 3-Ind Combo |
| `macd_signal` | DECIMAL(10,4) | EMA(MACD, 9) | MACD crossovers |
| `macd_histogram` | DECIMAL(10,4) | MACD Line - Signal Line | MACD improving/declining |

---

### 5. Stochastic Oscillator
| Column | Type | Calculation | Used In |
|--------|------|-------------|---------|
| `stoch_k` | DECIMAL(5,2) | %K = 100 × (Close - Low14) / (High14 - Low14) | Stoch+RSI Extreme |
| `stoch_d` | DECIMAL(5,2) | SMA(%K, 3) | Stochastic crossover |

---

### 6. ADX (Average Directional Index)
| Column | Type | Calculation | Used In |
|--------|------|-------------|---------|
| `adx` | DECIMAL(5,2) | ADX(14) | ADX+Volume strategies |
| `adx_plus_di` | DECIMAL(5,2) | +DI(14) | Trend direction |
| `adx_minus_di` | DECIMAL(5,2) | -DI(14) | Trend direction |

---

### 7. ATR (Average True Range)
| Column | Type | Calculation | Used In |
|--------|------|-------------|---------|
| `atr_14` | DECIMAL(10,4) | ATR(14) | ATR Contraction, ATR Expansion |

**True Range = max(high-low, |high-prev_close|, |low-prev_close|)**

---

### 8. VWAP (Volume Weighted Average Price)
| Column | Type | Calculation | Used In |
|--------|------|-------------|---------|
| `vwap` | DECIMAL(12,4) | Σ(Price × Volume) / Σ(Volume) | Volume at Support, VWAP Bounce |

**Reset daily (intraday VWAP) or use daily VWAP**

---

## 📝 EXAMPLE ROW

```sql
INSERT INTO gold.technical_indicators_calculated (
    date, ticker,
    rsi_14, stoch_k, stoch_d,
    macd_line, macd_signal, macd_histogram,
    adx, adx_plus_di, adx_minus_di,
    vwap, bb_upper, bb_lower, bb_middle,
    atr_14, vol_ratio
) VALUES (
    '2026-02-20', 'SPY',
    65.42, 78.50, 75.30,           -- RSI, Stoch
    2.4567, 1.8934, 0.5633,        -- MACD
    25.40, 28.50, 18.30,           -- ADX
    688.2345, 695.1234, 681.3456, 688.2345,  -- VWAP, BB
    4.5678, 1.25                   -- ATR, Vol Ratio
);
```

---

## 🎯 PRIORITY ORDER

**Must Have (for Golden strategies):**
1. `rsi_14`
2. `bb_upper`, `bb_lower`, `bb_middle`
3. `vol_ratio`

**Should Have (for Validated strategies):**
4. `macd_histogram`
5. `stoch_k`
6. `atr_14`
7. `vwap`

**Nice to Have:**
8. `adx`, `adx_plus_di`, `adx_minus_di`
9. `stoch_d`
10. `macd_line`, `macd_signal`

---

## ⚡ QUICK SQL TO CHECK

```sql
-- Check which tickers have indicators
SELECT ticker, COUNT(*) as records, MIN(date), MAX(date)
FROM gold.technical_indicators_calculated
WHERE ticker IN ('SPY', 'MSTR', 'COIN', 'MARA', 'RIOT', 'QQQ', 'IWM')
GROUP BY ticker;

-- Check if columns exist
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_schema = 'gold'
AND table_name = 'technical_indicators_calculated'
ORDER BY ordinal_position;
```

---

## 📞 FOR JT TRADING AGENT

**Action Required:**
1. Calculate indicators for new tickers (SPY, MSTR, COIN, MARA, RIOT, QQQ, IWM)
2. Insert into `gold.technical_indicators_calculated`
3. Verify with query above
4. Notify when complete

**Estimated time:** 10-15 minutes per ticker
**Total:** ~2 hours for all 7 tickers

---

*Required to unlock 9+ blocked strategies*  
*Date: 2026-02-23*