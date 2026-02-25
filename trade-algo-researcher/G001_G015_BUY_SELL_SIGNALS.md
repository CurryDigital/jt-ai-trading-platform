# GOLDEN STRATEGIES G001-G015 — BUY & SELL SIGNALS
**Complete Entry/Exit Specifications**

---

## G001: COIN RSI <20 Mean Reversion

**BUY SIGNAL:**
```
IF COIN.RSI(14) < 20 AND COIN.RSI(14) > 0:
    TRIGGER BUY at Close price
    Position Size: 2% of portfolio
```

**SELL SIGNAL:**
```
EXIT at FIRST of:
  1. Close[t+10] (10 trading days elapsed)
  2. Profit ≥ +10%
  3. Stop Loss ≤ -5%
```

---

## G002: MSTR RSI <20 Mean Reversion

**BUY SIGNAL:**
```
IF MSTR.RSI(14) < 20:
    TRIGGER BUY at Close price
    Position Size: 2% of portfolio
```

**SELL SIGNAL:**
```
EXIT at FIRST of:
  1. Close[t+10] (10 trading days elapsed)
  2. Profit ≥ +10%
  3. Stop Loss ≤ -5%
```

---

## G003: MSTR Momentum Trend

**BUY SIGNAL:**
```
IF MSTR.Close > MSTR.SMA(50) AND MSTR.ADX(14) > 25:
    TRIGGER BUY at Next Day Open
    Position Size: 1% of portfolio
```

**SELL SIGNAL:**
```
EXIT at FIRST of:
  1. MSTR.Close < MSTR.SMA(50)
  2. MSTR.ADX(14) < 20
  3. 15 trading days elapsed
  4. Profit ≥ +15%
```

---

## G004: NVDA BB Squeeze

**BUY SIGNAL:**
```
CALCULATE:
  BB_Width = (BB_Upper - BB_Lower) / SMA(20) * 100
  BB_Width_Pctile = Percentile(BB_Width, 120 days)

IF BB_Width_Pctile < 0.10 AND NVDA.RSI(14) < 45:
  IF Next_Day.Close > Today.High:  # Breakout confirmation
    TRIGGER BUY at Next_Day.Close
    Position Size: 1.5% of portfolio
```

**SELL SIGNAL:**
```
EXIT at FIRST of:
  1. Close > BB_Upper (profit target)
  2. 10 trading days elapsed
  3. Close < SMA(20)
```

---

## G005: MSFT Momentum Trend

**BUY SIGNAL:**
```
IF MSFT.Close > MSFT.SMA(50) AND MSFT.ADX(14) > 25:
    TRIGGER BUY at Next Day Open
    Position Size: 1% of portfolio
```

**SELL SIGNAL:**
```
EXIT at FIRST of:
  1. MSFT.Close < MSFT.SMA(50)
  2. MSFT.ADX(14) < 20
  3. 15 trading days elapsed
```

---

## G006: TSLA Momentum Trend

**BUY SIGNAL:**
```
IF TSLA.Close > TSLA.SMA(50) AND TSLA.ADX(14) > 25:
    TRIGGER BUY at Next Day Open
    Position Size: 0.8% of portfolio
```

**SELL SIGNAL:**
```
EXIT at FIRST of:
  1. TSLA.Close < TSLA.SMA(50)
  2. TSLA.ADX(14) < 20
  3. 15 trading days elapsed
```

---

## G007: NVDA Momentum Trend

**BUY SIGNAL:**
```
IF NVDA.Close > NVDA.SMA(50) AND NVDA.ADX(14) > 25:
    TRIGGER BUY at Next Day Open
    Position Size: 1% of portfolio
```

**SELL SIGNAL:**
```
EXIT at FIRST of:
  1. NVDA.Close < NVDA.SMA(50)
  2. NVDA.ADX(14) < 20
  3. 15 trading days elapsed
```

---

## G008: XLP BB Squeeze

**BUY SIGNAL:**
```
CALCULATE:
  BB_Width_Pctile = Percentile(BB_Width, 120 days)

IF BB_Width_Pctile < 0.10 AND Close > SMA(20):
  IF Next_Day.Close > Today.High:
    TRIGGER BUY at Next_Day.Close
    Position Size: 1.5% of portfolio
```

**SELL SIGNAL:**
```
EXIT at FIRST of:
  1. Close > BB_Upper
  2. 10 trading days elapsed
  3. Close < SMA(20)
```

---

## G009: JNJ BB Squeeze

**BUY SIGNAL:**
```
CALCULATE:
  BB_Width_Pctile = Percentile(BB_Width, 120 days)

IF BB_Width_Pctile < 0.10:
  IF Next_Day.Close > Today.High:
    TRIGGER BUY at Next_Day.Close
    Position Size: 2% of portfolio
```

**SELL SIGNAL:**
```
EXIT at FIRST of:
  1. Close > BB_Upper
  2. 10 trading days elapsed
  3. Close < SMA(20)
```

---

## G010: Tech 3-Day Reversal

**BUY SIGNAL:**
```
IF Close[t] < Close[t-1] AND Close[t-1] < Close[t-2] AND Close[t-2] < Close[t-3]:
  IF RSI(14) < 30:
    TRIGGER BUY at Close[t]
    Position Size: 1.5% of portfolio
```

**SELL SIGNAL:**
```
EXIT at FIRST of:
  1. Close[t+5] (5 trading days elapsed)
  2. Profit ≥ +5%
  3. Stop Loss ≤ -3%
```

---

## G011: CVX BB Squeeze

**BUY SIGNAL:**
```
CALCULATE:
  BB_Width_Pctile = Percentile(BB_Width, 120 days)

IF BB_Width_Pctile < 0.10:
  IF Next_Day.Close > Today.High:
    TRIGGER BUY at Next_Day.Close
    Position Size: 2% of portfolio
```

**SELL SIGNAL:**
```
EXIT at FIRST of:
  1. Close > BB_Upper
  2. 10 trading days elapsed
  3. Close < SMA(20)
```

---

## G012: BB Squeeze Breakout (Universal)

**BUY SIGNAL:**
```
CALCULATE:
  BB_Width_Pctile = Percentile(BB_Width, 120 days)

IF BB_Width_Pctile < 0.10:
  IF Next_Day.Close > Today.High:
    TRIGGER BUY at Next_Day.Close
    Position Size: 0.5% of portfolio
```

**SELL SIGNAL:**
```
EXIT at FIRST of:
  1. Close > BB_Upper
  2. 10 trading days elapsed
  3. Close < SMA(20)
```

---

## G013: Hammer Pattern (Universal)

**BUY SIGNAL:**
```
CALCULATE:
  Body = abs(Close - Open)
  Lower_Shadow = min(Open, Close) - Low
  Upper_Shadow = High - max(Open, Close)

IF Lower_Shadow > Body * 2 AND Upper_Shadow < Body * 0.5 AND Body > 0:
  TRIGGER BUY at Close
  Position Size: 1.5% of portfolio
```

**SELL SIGNAL:**
```
EXIT at FIRST of:
  1. Close[t+5] (5 trading days elapsed)
  2. Profit ≥ +5%
  3. Close < Hammer.Low (pattern invalidated)
```

---

## G014: Bullish Engulfing

**BUY SIGNAL:**
```
CALCULATE:
  Body[t] = abs(Close[t] - Open[t])
  Body[t-1] = abs(Close[t-1] - Open[t-1])

IF Open[t] < Close[t-1] AND Close[t] > Open[t-1] AND Body[t] > Body[t-1] * 1.2:
  IF Volume[t] > Volume[t-1]:
    TRIGGER BUY at Close[t]
    Position Size: 1% of portfolio
```

**SELL SIGNAL:**
```
EXIT at FIRST of:
  1. Profit ≥ +3%
  2. 5 trading days elapsed
  3. Close < Open (pattern invalidated)
```

---

## G015: ADX >25 Trend (Universal)

**BUY SIGNAL:**
```
CALCULATE:
  +DI = 100 * EMA(+DM, 14) / ATR(14)
  -DI = 100 * EMA(-DM, 14) / ATR(14)
  DX = 100 * abs(+DI - -DI) / (+DI + -DI)
  ADX = EMA(DX, 14)

IF ADX > 25 AND +DI > -DI AND Close > SMA(50):
  TRIGGER BUY at Next Day Open
  Position Size: 0.3% of portfolio
```

**SELL SIGNAL:**
```
EXIT at FIRST of:
  1. ADX < 20
  2. -DI > +DI
  3. Close < SMA(50)
  4. 15 trading days elapsed
```

---

## SUMMARY: EXIT RULES BY TYPE

| Exit Type | Strategies |
|-----------|------------|
| **Time-based (5 days)** | G010, G013, G014 |
| **Time-based (10 days)** | G001, G002, G004, G008, G009, G011, G012 |
| **Time-based (15 days)** | G003, G005, G006, G007, G015 |
| **Profit target** | All strategies (3-15%) |
| **Stop loss** | G001, G002, G010 |
| **Technical breakdown** | G003-G015 |
