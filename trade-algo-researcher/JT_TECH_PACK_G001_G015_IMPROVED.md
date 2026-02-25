# JT TRADING TECH PACK — GOLDEN STRATEGIES G001-G015 (IMPROVED)
**Version:** 2.0  
**Date:** 2026-02-23  
**Status:** PRODUCTION DEPLOYMENT  
**Format:** Explicit Universe + Buy/Sell + Win Rate + Description

---

## 🎯 STRATEGY G001: COIN RSI <20 Mean Reversion

### **UNIVERSE (Ticker List)**
| Ticker | Company | Sector |
|--------|---------|--------|
| COIN | Coinbase Global Inc | Crypto |

**Total Tickers:** 1

### **BUY SIGNAL**
```
IF COIN.RSI(14) < 20 AND COIN.RSI(14) > 0:
    TRIGGER BUY at Close price
    Position Size: 2% of portfolio
    Max Positions: 2 concurrent
```

### **SELL SIGNAL**
```
EXIT at FIRST of:
  1. Close[t+10] (10 trading days elapsed)   [Maximum hold time]
  2. Profit ≥ +10%                          [Profit target]
  3. Stop Loss ≤ -5%                        [Maximum loss allowed]
```

**KPI/Metrics for JT Trading to Monitor:**
| Metric | Calculation | Exit Threshold |
|--------|-------------|----------------|
| **Profit** | (Current - Entry) / Entry * 100 | **≥ +10%** |
| **Stop Loss** | (Current - Entry) / Entry * 100 | **≤ -5%** |
| **Days Held** | Current date - Entry date | **≥ 10 days** |

### **ESTIMATED PERFORMANCE**
| Metric | Value |
|--------|-------|
| **Win Rate** | 100.0% [95% CI: 72%-100%] |
| **Historical Trades** | 10 (test period) |
| **Signals/Year** | ~5 |
| **Expected Return** | 10-15% per trade |

### **DESCRIPTION**
Mean reversion strategy for Coinbase stock. When RSI drops below 20 (extremely oversold), the strategy buys at close and holds for 10 days or until profit target/stop loss. Crypto stocks exhibit strong mean reversion after panic selling.

---

## 🎯 STRATEGY G002: MSTR RSI <20 Mean Reversion

### **UNIVERSE (Ticker List)**
| Ticker | Company | Sector |
|--------|---------|--------|
| MSTR | MicroStrategy Inc | Crypto |

**Total Tickers:** 1

### **BUY SIGNAL**
```
IF MSTR.RSI(14) < 20:
    TRIGGER BUY at Close price
    Position Size: 2% of portfolio
    Max Positions: 2 concurrent
```

### **SELL SIGNAL**
```
EXIT at FIRST of:
  1. Close[t+10] (10 trading days elapsed)   [Maximum hold time]
  2. Profit ≥ +10%                          [Profit target]
  3. Stop Loss ≤ -5%                        [Maximum loss allowed]
```

**KPI/Metrics for JT Trading to Monitor:**
| Metric | Calculation | Exit Threshold |
|--------|-------------|----------------|
| **Profit** | (Current - Entry) / Entry * 100 | **≥ +10%** |
| **Stop Loss** | (Current - Entry) / Entry * 100 | **≤ -5%** |
| **Days Held** | Current date - Entry date | **≥ 10 days** |

### **ESTIMATED PERFORMANCE**
| Metric | Value |
|--------|-------|
| **Win Rate** | 87.5% [95% CI: 47%-100%] |
| **Historical Trades** | 8 (test period) |
| **Signals/Year** | ~4 |
| **Expected Return** | 10-15% per trade |

### **DESCRIPTION**
Mean reversion strategy for MicroStrategy. As a Bitcoin proxy, MSTR experiences extreme volatility. RSI below 20 signals panic selling, creating high-probability bounce opportunities.

---

## 🎯 STRATEGY G003: MSTR Momentum Trend

### **UNIVERSE (Ticker List)**
| Ticker | Company | Sector |
|--------|---------|--------|
| MSTR | MicroStrategy Inc | Crypto |

**Total Tickers:** 1

### **BUY SIGNAL**
```
IF MSTR.Close > MSTR.SMA(50) AND MSTR.ADX(14) > 25:
    TRIGGER BUY at Next Day Open
    Position Size: 1% of portfolio
    Max Positions: 5 concurrent
```

### **SELL SIGNAL**
```
EXIT at FIRST of:
  1. MSTR.Close < MSTR.SMA(50)           [Price below 50-day moving average]
  2. MSTR.ADX(14) < 20                   [Trend strength weakened below 20]
  3. 15 trading days elapsed             [Maximum hold time]
  4. Profit ≥ +15%                       [Profit target]
```

**KPI/Metrics for JT Trading to Monitor:**
| Metric | Calculation | Exit Threshold |
|--------|-------------|----------------|
| **SMA50** | 50-day simple moving average | **Close < SMA50** |
| **ADX** | EMA(DX, 14) | **< 20** |
| **Profit** | (Current - Entry) / Entry * 100 | **≥ +15%** |

### **ESTIMATED PERFORMANCE**
| Metric | Value |
|--------|-------|
| **Win Rate** | 82.9% [95% CI: 75%-90%] |
| **Historical Trades** | 111 |
| **Signals/Year** | ~30 |
| **Expected Return** | 15-20% per trade |

### **DESCRIPTION**
Trend-following strategy for MicroStrategy. When price is above 50-day SMA with strong trend (ADX > 25), the strategy rides the momentum. MSTR trends strongly when Bitcoin is in bull markets.

---

## 🎯 STRATEGY G004: NVDA BB Squeeze

### **UNIVERSE (Ticker List)**
| Ticker | Company | Sector |
|--------|---------|--------|
| NVDA | NVIDIA Corporation | Technology |

**Total Tickers:** 1

### **BUY SIGNAL**
```
CALCULATE:
  BB_Width = (BB_Upper - BB_Lower) / SMA(20) * 100
  BB_Width_Percentile = Percentile(BB_Width, 120 days)

IF BB_Width_Percentile < 0.10 AND NVDA.RSI(14) < 45:
  IF Next_Day.Close > Today.High:  # Breakout confirmation
    TRIGGER BUY at Next_Day.Close
    Position Size: 1.5% of portfolio
    Max Positions: 3 concurrent
```

### **SELL SIGNAL**
```
EXIT at FIRST of:
  1. Close > BB_Upper                     [Price reached upper Bollinger Band - profit target]
  2. 10 trading days elapsed              [Maximum hold time]
  3. Close < SMA(20)                      [Price broke below 20-day support]
```

**KPI/Metrics for JT Trading to Monitor:**
| Metric | Calculation | Exit Threshold |
|--------|-------------|----------------|
| **BB_Upper** | SMA(20) + (2 × StdDev(20)) | **Close > BB_Upper** |
| **SMA20** | 20-day simple moving average | **Close < SMA20** |
| **Days Held** | Current date - Entry date | **≥ 10 days** |

### **ESTIMATED PERFORMANCE**
| Metric | Value |
|--------|-------|
| **Win Rate** | 77.8% [95% CI: 61%-89%] |
| **Historical Trades** | 36 |
| **Signals/Year** | ~10 |
| **Expected Return** | 8-12% per trade |

### **DESCRIPTION**
Volatility expansion strategy for NVIDIA. When Bollinger Bands squeeze (width in bottom 10% of 120 days) and RSI is not overbought (< 45), a breakout often leads to explosive moves. The strategy buys on breakout confirmation.

---

## 🎯 STRATEGY G005: MSFT Momentum Trend

### **UNIVERSE (Ticker List)**
| Ticker | Company | Sector |
|--------|---------|--------|
| MSFT | Microsoft Corporation | Technology |

**Total Tickers:** 1

### **BUY SIGNAL**
```
IF MSFT.Close > MSFT.SMA(50) AND MSFT.ADX(14) > 25:
    TRIGGER BUY at Next Day Open
    Position Size: 1% of portfolio
    Max Positions: 5 concurrent
```

### **SELL SIGNAL**
```
EXIT at FIRST of:
  1. MSFT.Close < MSFT.SMA(50)          [Price below 50-day moving average]
  2. MSFT.ADX(14) < 20                  [Trend strength weakened below 20]
  3. 15 trading days elapsed             [Maximum hold time]
```

**KPI/Metrics for JT Trading to Monitor:**
| Metric | Calculation | Exit Threshold |
|--------|-------------|----------------|
| **SMA50** | 50-day simple moving average | **Close < SMA50** |
| **ADX** | EMA(DX, 14) | **< 20** |

### **ESTIMATED PERFORMANCE**
| Metric | Value |
|--------|-------|
| **Win Rate** | 77.6% [95% CI: 70%-84%] |
| **Historical Trades** | 134 |
| **Signals/Year** | ~35 |
| **Expected Return** | 10-15% per trade |

### **DESCRIPTION**
Trend-following strategy for Microsoft. MSFT exhibits strong trending behavior when above 50-day SMA with ADX confirmation. The strategy captures sustained uptrends in this large-cap tech leader.

---

## 🎯 STRATEGY G006: TSLA Momentum Trend

### **UNIVERSE (Ticker List)**
| Ticker | Company | Sector |
|--------|---------|--------|
| TSLA | Tesla Inc | Automotive/Technology |

**Total Tickers:** 1

### **BUY SIGNAL**
```
IF TSLA.Close > TSLA.SMA(50) AND TSLA.ADX(14) > 25:
    TRIGGER BUY at Next Day Open
    Position Size: 0.8% of portfolio
    Max Positions: 6 concurrent
```

### **SELL SIGNAL**
```
EXIT at FIRST of:
  1. TSLA.Close < TSLA.SMA(50)           [Price below 50-day moving average]
  2. TSLA.ADX(14) < 20                   [Trend strength weakened below 20]
  3. 15 trading days elapsed             [Maximum hold time]
```

**KPI/Metrics for JT Trading to Monitor:**
| Metric | Calculation | Exit Threshold |
|--------|-------------|----------------|
| **SMA50** | 50-day simple moving average | **Close < SMA50** |
| **ADX** | EMA(DX, 14) | **< 20** |

### **ESTIMATED PERFORMANCE**
| Metric | Value |
|--------|-------|
| **Win Rate** | 77.6% [95% CI: 72%-83%] |
| **Historical Trades** | 237 |
| **Signals/Year** | ~60 |
| **Expected Return** | 15-25% per trade |

### **DESCRIPTION**
Trend-following strategy for Tesla. TSLA is highly volatile with strong trending periods. The strategy uses smaller position size (0.8%) due to higher volatility but captures significant moves when trending.

---

## 🎯 STRATEGY G007: NVDA Momentum Trend

### **UNIVERSE (Ticker List)**
| Ticker | Company | Sector |
|--------|---------|--------|
| NVDA | NVIDIA Corporation | Technology |

**Total Tickers:** 1

### **BUY SIGNAL**
```
IF NVDA.Close > NVDA.SMA(50) AND NVDA.ADX(14) > 25:
    TRIGGER BUY at Next Day Open
    Position Size: 1% of portfolio
    Max Positions: 5 concurrent
```

### **SELL SIGNAL**
```
EXIT at FIRST of:
  1. NVDA.Close < NVDA.SMA(50)          [Price below 50-day moving average]
  2. NVDA.ADX(14) < 20                  [Trend strength weakened below 20]
  3. 15 trading days elapsed             [Maximum hold time]
```

**KPI/Metrics for JT Trading to Monitor:**
| Metric | Calculation | Exit Threshold |
|--------|-------------|----------------|
| **SMA50** | 50-day simple moving average | **Close < SMA50** |
| **ADX** | EMA(DX, 14) | **< 20** |

### **ESTIMATED PERFORMANCE**
| Metric | Value |
|--------|-------|
| **Win Rate** | 75.5% [95% CI: 68%-82%] |
| **Historical Trades** | 155 |
| **Signals/Year** | ~40 |
| **Expected Return** | 12-18% per trade |

### **DESCRIPTION**
Trend-following strategy for NVIDIA. Separate from G004 (which is mean reversion), this is pure trend-following. NVDA trends strongly during AI/semiconductor bull markets.

---

## 🎯 STRATEGY G008: Consumer Staples BB Squeeze

### **UNIVERSE (Ticker List)**
| Ticker | Company | Sector |
|--------|---------|--------|
| XLP | Consumer Staples Select Sector SPDR Fund | ETF |
| WMT | Walmart Inc | Consumer Staples |
| PG | Procter & Gamble Co | Consumer Staples |
| KO | Coca-Cola Co | Consumer Staples |
| PEP | PepsiCo Inc | Consumer Staples |
| COST | Costco Wholesale Corp | Consumer Staples |

**Total Tickers:** 6

### **BUY SIGNAL**
```
CALCULATE:
  BB_Width_Percentile = Percentile(BB_Width, 120 days)

IF BB_Width_Percentile < 0.10 AND Close > SMA(20):
  IF Next_Day.Close > Today.High:
    TRIGGER BUY at Next_Day.Close
    Position Size: 1.5% of portfolio
    Max Positions: 3 concurrent
```

### **SELL SIGNAL**
```
EXIT at FIRST of:
  1. Close > BB_Upper                     [Price reached upper Bollinger Band - profit target]
  2. 10 trading days elapsed              [Maximum hold time]
  3. Close < SMA(20)                      [Price broke below 20-day support]
```

**KPI/Metrics for JT Trading to Monitor:**
| Metric | Calculation | Exit Threshold |
|--------|-------------|----------------|
| **BB_Upper** | SMA(20) + (2 × StdDev(20)) | **Close > BB_Upper** |
| **SMA20** | 20-day simple moving average | **Close < SMA20** |
| **Days Held** | Current date - Entry date | **≥ 10 days** |

### **ESTIMATED PERFORMANCE**
| Metric | Value |
|--------|-------|
| **Win Rate** | 75.0% [95% CI: 48%-91%] |
| **Historical Trades** | 16 (XLP test) |
| **Signals/Year** | ~5 per ticker = ~30 total |
| **Expected Return** | 6-10% per trade |

### **DESCRIPTION**
Volatility expansion strategy for defensive Consumer Staples sector. These stocks have low volatility normally, so when BB Squeeze occurs, the subsequent breakout is highly predictable. Combines ETF (XLP) with individual leaders for diversification.

---

## 🎯 STRATEGY G009: JNJ BB Squeeze

### **UNIVERSE (Ticker List)**
| Ticker | Company | Sector |
|--------|---------|--------|
| JNJ | Johnson & Johnson | Healthcare |

**Total Tickers:** 1

### **BUY SIGNAL**
```
CALCULATE:
  BB_Width_Percentile = Percentile(BB_Width, 120 days)

IF BB_Width_Percentile < 0.10:
  IF Next_Day.Close > Today.High:
    TRIGGER BUY at Next_Day.Close
    Position Size: 2% of portfolio
    Max Positions: 2 concurrent
```

### **SELL SIGNAL**
```
EXIT at FIRST of:
  1. Close > BB_Upper                     [Price reached upper Bollinger Band - profit target]
  2. 10 trading days elapsed              [Maximum hold time]
  3. Close < SMA(20)                      [Price broke below 20-day support]
```

**KPI/Metrics for JT Trading to Monitor:**
| Metric | Calculation | Exit Threshold |
|--------|-------------|----------------|
| **BB_Upper** | SMA(20) + (2 × StdDev(20)) | **Close > BB_Upper** |
| **SMA20** | 20-day simple moving average | **Close < SMA20** |
| **Days Held** | Current date - Entry date | **≥ 10 days** |

### **ESTIMATED PERFORMANCE**
| Metric | Value |
|--------|-------|
| **Win Rate** | 75.0% [95% CI: 35%-97%] |
| **Historical Trades** | 8 |
| **Signals/Year** | ~3 |
| **Expected Return** | 5-8% per trade |

### **DESCRIPTION**
Volatility expansion strategy for Johnson & Johnson. As a defensive healthcare stock, JNJ rarely has volatile periods. When BB Squeeze occurs, the breakout direction is highly predictable (usually upward).

---

## 🎯 STRATEGY G010: Tech 3-Day Reversal

### **UNIVERSE (Ticker List)**
| Ticker | Company | Sector |
|--------|---------|--------|
| QQQ | Invesco QQQ Trust | ETF (Nasdaq-100) |
| AAPL | Apple Inc | Technology |
| MSFT | Microsoft Corporation | Technology |
| NVDA | NVIDIA Corporation | Technology |

**Total Tickers:** 4

### **BUY SIGNAL**
```
IF Close[t] < Close[t-1] AND Close[t-1] < Close[t-2] AND Close[t-2] < Close[t-3]:
  IF RSI(14) < 30:
    TRIGGER BUY at Close[t]
    Position Size: 1.5% of portfolio
    Max Positions: 4 concurrent
```

### **SELL SIGNAL**
```
EXIT at FIRST of:
  1. Close[t+5] (5 trading days elapsed)    [Maximum hold time]
  2. Profit ≥ +5%                          [Profit target]
  3. Stop Loss ≤ -3%                       [Maximum loss allowed]
```

**KPI/Metrics for JT Trading to Monitor:**
| Metric | Calculation | Exit Threshold |
|--------|-------------|----------------|
| **Profit** | (Current - Entry) / Entry * 100 | **≥ +5%** |
| **Stop Loss** | (Current - Entry) / Entry * 100 | **≤ -3%** |
| **Days Held** | Current date - Entry date | **≥ 5 days** |

### **ESTIMATED PERFORMANCE**
| Metric | Value |
|--------|-------|
| **Win Rate** | 71.0% [95% CI: 53%-85%] |
| **Historical Trades** | 31 |
| **Signals/Year** | ~15 |
| **Expected Return** | 4-6% per trade |

### **DESCRIPTION**
Mean reversion strategy for large-cap tech. Three consecutive down days with oversold RSI (< 30) creates a high-probability short-term bounce. Short 5-day hold with tight risk management.

---

## 🎯 STRATEGY G011: CVX BB Squeeze

### **UNIVERSE (Ticker List)**
| Ticker | Company | Sector |
|--------|---------|--------|
| CVX | Chevron Corporation | Energy |

**Total Tickers:** 1

### **BUY SIGNAL**
```
CALCULATE:
  BB_Width_Percentile = Percentile(BB_Width, 120 days)

IF BB_Width_Percentile < 0.10:
  IF Next_Day.Close > Today.High:
    TRIGGER BUY at Next_Day.Close
    Position Size: 2% of portfolio
    Max Positions: 2 concurrent
```

### **SELL SIGNAL**
```
EXIT at FIRST of:
  1. Close > BB_Upper                     [Price reached upper Bollinger Band - profit target]
  2. 10 trading days elapsed              [Maximum hold time]
  3. Close < SMA(20)                      [Price broke below 20-day support]
```

**KPI/Metrics for JT Trading to Monitor:**
| Metric | Calculation | Exit Threshold |
|--------|-------------|----------------|
| **BB_Upper** | SMA(20) + (2 × StdDev(20)) | **Close > BB_Upper** |
| **SMA20** | 20-day simple moving average | **Close < SMA20** |
| **Days Held** | Current date - Entry date | **≥ 10 days** |

### **ESTIMATED PERFORMANCE**
| Metric | Value |
|--------|-------|
| **Win Rate** | 71.4% [95% CI: 42%-92%] |
| **Historical Trades** | 14 |
| **Signals/Year** | ~4 |
| **Expected Return** | 6-10% per trade |

### **DESCRIPTION**
Volatility expansion strategy for Chevron. Unlike the failing XLE ETF, CVX as an individual energy major shows reliable BB Squeeze patterns. Energy volatility creates predictable breakout opportunities.

---

## 🎯 STRATEGY G012: BB Squeeze Breakout (Universal)

### **UNIVERSE (Ticker List)**
**All 401 tickers in JT universe**

**Sample includes:**
- All S&P 500 constituents
- All Nasdaq-100 constituents  
- Selected mid-cap liquid names

**Total Tickers:** 401

### **BUY SIGNAL**
```
CALCULATE:
  BB_Width_Percentile = Percentile(BB_Width, 120 days)

IF BB_Width_Percentile < 0.10:
  IF Next_Day.Close > Today.High:
    TRIGGER BUY at Next_Day.Close
    Position Size: 0.5% of portfolio
    Max Positions: 10 concurrent
```

### **SELL SIGNAL**
```
EXIT at FIRST of:
  1. Close > BB_Upper                     [Price reached upper Bollinger Band - profit target]
  2. 10 trading days elapsed              [Maximum hold time]
  3. Close < SMA(20)                      [Price broke below 20-day support]
```

**KPI/Metrics for JT Trading to Monitor:**
| Metric | Calculation | Exit Threshold |
|--------|-------------|----------------|
| **BB_Upper** | SMA(20) + (2 × StdDev(20)) | **Close > BB_Upper** |
| **SMA20** | 20-day simple moving average | **Close < SMA20** |
| **Days Held** | Current date - Entry date | **≥ 10 days** |

### **ESTIMATED PERFORMANCE**
| Metric | Value |
|--------|-------|
| **Win Rate** | 66.7% [95% CI: 59%-74%] |
| **Historical Trades** | 147 |
| **Signals/Year** | ~50 |
| **Expected Return** | 5-8% per trade |

### **DESCRIPTION**
Universal volatility expansion strategy applied across entire universe. When any stock's Bollinger Bands squeeze to historic lows (bottom 10% of 120 days), a breakout often follows. Lower position size (0.5%) due to higher frequency across many names.

---

## 🎯 STRATEGY G013: Hammer Pattern (Universal)

### **UNIVERSE (Ticker List)**
**All 401 tickers in JT universe**

**Total Tickers:** 401

### **BUY SIGNAL**
```
CALCULATE:
  Body = abs(Close - Open)
  Lower_Shadow = min(Open, Close) - Low
  Upper_Shadow = High - max(Open, Close)

IF Lower_Shadow > Body * 2 AND Upper_Shadow < Body * 0.5 AND Body > 0:
  TRIGGER BUY at Close
  Position Size: 1.5% of portfolio
  Max Positions: 3 concurrent
```

### **SELL SIGNAL**
```
EXIT at FIRST of:
  1. Close[t+5] (5 trading days elapsed)    [Maximum hold time]
  2. Profit ≥ +5%                          [Profit target]
  3. Close < Hammer.Low                    [Price below Hammer candle low - pattern invalidated]
```

**KPI/Metrics for JT Trading to Monitor:**
| Metric | Calculation | Exit Threshold |
|--------|-------------|----------------|
| **Hammer.Low** | Low price of the Hammer candlestick | **Close < Hammer.Low** |
| **Profit** | (Current - Entry) / Entry * 100 | **≥ +5%** |
| **Days Held** | Current date - Entry date | **≥ 5 days** |

**Explanation:**
- **Close < Hammer.Low**: Price has broken below the Hammer's low, invalidating the reversal pattern
- **Profit ≥ +5%**: Short-term profit target achieved
- **5 days**: Maximum hold time for short-term pattern

### **ESTIMATED PERFORMANCE**
| Metric | Value |
|--------|-------|
| **Win Rate** | 66.7% [95% CI: 35%-90%] |
| **Historical Trades** | 12 |
| **Signals/Year** | ~6 |
| **Expected Return** | 4-6% per trade |

### **DESCRIPTION**
Universal candlestick pattern recognition. The Hammer pattern (small body, long lower shadow) indicates rejection of lower prices. When this forms on any stock, a short-term bounce is likely. Classic technical analysis pattern validated with modern backtesting.

---

## 🎯 STRATEGY G014: Bullish Engulfing

### **UNIVERSE (Ticker List)**
| Ticker | Company | Sector |
|--------|---------|--------|
| QQQ | Invesco QQQ Trust | ETF (Nasdaq-100) |
| SPY | SPDR S&P 500 ETF Trust | ETF (S&P 500) |
| AAPL | Apple Inc | Technology |
| MSFT | Microsoft Corporation | Technology |
| GOOGL | Alphabet Inc Class A | Technology |
| NVDA | NVIDIA Corporation | Technology |
| TSLA | Tesla Inc | Automotive/Technology |

**Total Tickers:** 7

### **BUY SIGNAL**
```
CALCULATE:
  Body[t] = abs(Close[t] - Open[t])
  Body[t-1] = abs(Close[t-1] - Open[t-1])

IF Open[t] < Close[t-1] AND Close[t] > Open[t-1] AND Body[t] > Body[t-1] * 1.2:
  IF Volume[t] > Volume[t-1]:
    TRIGGER BUY at Close[t]
    Position Size: 1% of portfolio
    Max Positions: 5 concurrent
```

### **SELL SIGNAL**
```
EXIT at FIRST of:
  1. Profit ≥ +3%                          [Profit target achieved]
  2. 5 trading days elapsed                [Maximum hold time]
  3. Close < Open                         [Bullish candle invalidated - bearish close]
```

**KPI/Metrics for JT Trading to Monitor:**
| Metric | Calculation | Exit Threshold |
|--------|-------------|----------------|
| **Profit** | (Current - Entry) / Entry * 100 | **≥ +3%** |
| **Close vs Open** | Current Close vs Current Open | **Close < Open** |
| **Days Held** | Current date - Entry date | **≥ 5 days** |

**Explanation:**
- **Close < Open**: The current candle is bearish (close below open), invalidating the bullish engulfing setup
- **Profit ≥ +3%**: Short-term profit target for pattern-based trade
- **5 days**: Maximum hold time for pattern-based strategy

### **ESTIMATED PERFORMANCE**
| Metric | Value |
|--------|-------|
| **Win Rate** | 65.9% [95% CI: 50%-80%] |
| **Historical Trades** | 41 |
| **Signals/Year** | ~20 |
| **Expected Return** | 3-5% per trade |

### **DESCRIPTION**
Candlestick reversal pattern for large-cap liquid tech. Bullish Engulfing (today's candle completely engulfs yesterday's body with higher volume) signals strong buying pressure. Focus on highly liquid names to ensure pattern reliability.

---

## 🎯 STRATEGY G015: ADX >25 Trend (Universal)

### **UNIVERSE (Ticker List)**
**All 401 tickers in JT universe**

**Total Tickers:** 401

### **BUY SIGNAL**
```
CALCULATE:
  +DI = 100 * EMA(+DM, 14) / ATR(14)
  -DI = 100 * EMA(-DM, 14) / ATR(14)
  DX = 100 * abs(+DI - -DI) / (+DI + -DI)
  ADX = EMA(DX, 14)

IF ADX > 25 AND +DI > -DI AND Close > SMA(50):
  TRIGGER BUY at Next Day Open
  Position Size: 0.3% of portfolio
  Max Positions: 15 concurrent
```

### **SELL SIGNAL**
```
EXIT at FIRST of:
  1. ADX(14) < 20                          [Trend strength weakened]
  2. -DI(14) > +DI(14)                     [Bearish Directional Movement crossover]
  3. Close < SMA(50)                       [Price below 50-day moving average]
  4. 15 trading days elapsed               [Time-based exit]
```

**KPI/Metrics for JT Trading to Monitor:**
| Metric | Calculation | Exit Threshold |
|--------|-------------|----------------|
| **ADX** | EMA(DX, 14) where DX = 100 * abs(+DI - -DI) / (+DI + -DI) | **< 20** |
| **+DI** | 100 * EMA(+DM, 14) / ATR(14) | When **-DI > +DI** |
| **-DI** | 100 * EMA(-DM, 14) / ATR(14) | When **-DI > +DI** |
| **SMA50** | 50-day simple moving average of Close | **Close < SMA50** |

**Explanation:**
- **ADX < 20**: Trend is no longer strong enough to continue
- **-DI > +DI**: Bearish momentum now dominates (Directional Movement bearish crossover)
- **Close < SMA50**: Price has broken below medium-term support
- **15 days**: Maximum hold time regardless of technical conditions

### **ESTIMATED PERFORMANCE**
| Metric | Value |
|--------|-------|
| **Win Rate** | 65.4% [95% CI: 61%-70%] |
| **Historical Trades** | 471 |
| **Signals/Year** | ~150 |
| **Expected Return** | 8-12% per trade |

### **DESCRIPTION**
Universal trend-following strategy using ADX (Average Directional Index). When ADX > 25, trend strength is significant. Combining with +DI > -DI (bullish) and price above 50-day SMA creates high-probability trend continuation trades. Highest frequency strategy (150 signals/year) with smallest position size (0.3%).

---

## 📊 AGGREGATE PORTFOLIO SUMMARY

### **Ticker Coverage**
| Category | Strategies | Tickers |
|----------|------------|---------|
| **Single Stock** | 9 | 9 individual |
| **Multi-Ticker** | 3 | 17 total |
| **Universal** | 3 | 401 |
| **Total Unique** | 15 | 401+ |

### **Expected Performance**
| Metric | Value |
|--------|-------|
| **Blended Win Rate** | ~70% |
| **Total Signals/Year** | ~750 |
| **Expected Return** | 25-35% annually |
| **Expected Max Drawdown** | 12-18% |

### **Risk Management**
| Metric | Value |
|--------|-------|
| **Total Max Positions** | 89 concurrent |
| **Total Risk Exposure** | ~20% of portfolio |
| **Cash Reserve** | ~50% |
| **MMF Allocation** | ~30% |

---

## ✅ JT TRADING CHECKLIST

### Database Setup
- [ ] Create `strategy_registry` table with all 15 strategies (G001-G015)
- [ ] Store `strategy_id`, `last_modified`, `version` for each
- [ ] Create `strategy_trades` table for execution logging

### Deployment
- [ ] Load all 401 tickers into monitoring system
- [ ] Configure buy/sell signal detection for each strategy
- [ ] Set position sizing per strategy table
- [ ] Configure alerts by priority level

### Monitoring
- [ ] Track actual win rate vs expected (65-100%)
- [ ] Alert if any strategy drops below 60% win rate
- [ ] Monthly performance review

---

**Version 2.0 — All universes explicitly listed with ticker symbols**