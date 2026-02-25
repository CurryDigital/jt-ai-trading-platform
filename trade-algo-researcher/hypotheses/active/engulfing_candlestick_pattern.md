# Hypothesis: Engulfing Candlestick Pattern

**Status:** testing  
**Created:** 2026-02-18  
**Asset Class:** Equities  
**Direction:** Long/Short  
**Horizon:** 2-5 days  
**Target Win Rate:** 55-60%

---

## Core Idea

Bullish engulfing (green candle completely covers previous red) predicts bounce. Bearish engulfing (red covers green) predicts pullback. Works best at support/resistance with volume.

**The Pattern:**

**Bullish Engulfing:**
- Day 1: Red candle (close < open)
- Day 2: Green candle (close > open)
- Day 2 body completely engulfs Day 1 body
- Day 2 low < Day 1 low (stops shaken out)
- Day 2 close > Day 1 open

**Bearish Engulfing:**
- Day 1: Green candle
- Day 2: Red candle
- Day 2 body completely engulfs Day 1 body
- Day 2 high > Day 1 high (traps longs)
- Day 2 close < Day 1 open

---

## Signal Construction

**Long Setup:**
```
IF bullish_engulfing AND
   price near support (20-day low) AND
   volume on Day 2 > 1.3x Day 1 AND
   RSI < 40 (not overbought)
THEN long, stop below Day 2 low
```

**Short Setup:**
```
IF bearish_engulfing AND
   price near resistance (20-day high) AND
   volume on Day 2 > 1.3x Day 1 AND
   RSI > 60 (not oversold)
THEN short, stop above Day 2 high
```

---

## Expected Performance

| Metric | Candlestick Alone | + Volume | + RSI Filter |
|--------|-------------------|----------|--------------|
| Win Rate | 52% | 56% | 60% |
| Sharpe | 0.5 | 0.7 | 0.9 |

---

## Universe

Liquid large-caps with clear S/R: SPY, QQQ, AAPL, MSFT

---

## Data Requirements

- Daily OHLC
- Volume
- RSI (optional filter)
- Support/resistance levels

---

## Why It Works

1. **Sentiment reversal** — Bears exhausted on Day 1, bulls take over Day 2
2. **Stop hunting** — Day 2 low/high shakes out weak hands
3. **Confirmation** — Body engulfing shows conviction
4. **Visual pattern** — Recognized by many traders (self-fulfilling)

---

## Best Conditions

- At support/resistance
- After trend (not in middle)
- With volume confirmation
- In direction of higher timeframe trend

---

## Risk

- Works 55-60% (not 80%)
- Requires strict stops
- False signals in choppy markets

---

*The most reliable candlestick pattern — when confirmed.*
