# Hypothesis: MACD Histogram Divergence

**Status:** testing  
**Created:** 2026-02-18  
**Asset Class:** Equities / Crypto  
**Direction:** Long/Short  
**Horizon:** 3-10 days  
**Target Win Rate:** 58-62%

---

## Core Idea

MACD histogram divergence predicts trend exhaustion. Price makes new high, MACD histogram makes lower high = bearish divergence. Price makes new low, histogram makes higher low = bullish divergence.

**The Edge:**
- MACD crossover: 52% win rate (too slow)
- MACD divergence: 58-62% win rate
- Divergence + trendline break: 65% win rate

---

## Signal Construction

**Bearish Divergence (Short):**
```
Price: High[0] > High[-5] > High[-10] (higher highs)
MACD Hist: Hist[0] < Hist[-5] < Hist[-10] (lower highs)
Volume: Declining on second high
THEN short, stop above recent high
```

**Bullish Divergence (Long):**
```
Price: Low[0] < Low[-5] < Low[-10] (lower lows)
MACD Hist: Hist[0] > Hist[-5] > Hist[-10] (higher lows)
Volume: Declining on second low
THEN long, stop below recent low
```

**Parameters:**
- MACD: 12, 26, 9 (standard)
- Lookback: 5-15 bars for divergence formation

---

## Expected Performance

| Metric | Target |
|--------|--------|
| Win Rate | 58-62% |
| Avg Return | 3-5% per trade |
| Sharpe | 1.0-1.3 |
| Best Timeframe | 4H, Daily |

---

## Universe

Trending stocks: Tech, crypto, commodities

---

## Data Requirements

- OHLC prices
- MACD calculation (EMA12 - EMA26)
- Histogram (MACD - Signal)
- Peak/trough detection

---

## Why It Works

1. **Momentum divergence** — Price trend continues, momentum fades
2. **Trend exhaustion** — Buyers/sellers exhausted
3. **Early warning** — Divergence precedes price reversal
4. **Works in all markets** — Stocks, FX, crypto

---

## Best Markets

- **Crypto:** High volatility, clear trends, strong divergences
- **Commodities:** Trending markets (gold, oil)
- **Tech stocks:** Strong momentum, clear reversals

---

## Risk

- Multiple divergences (can extend)
- Requires trend (not range-bound)
- False signals in choppy markets

---

*Divergence = disagreement between price and momentum = opportunity.*
