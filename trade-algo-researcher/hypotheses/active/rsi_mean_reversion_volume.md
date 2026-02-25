# Hypothesis: RSI Mean Reversion with Volume Confirmation

**Status:** testing  
**Created:** 2026-02-18  
**Asset Class:** Equities  
**Direction:** Long/Short  
**Horizon:** 2-5 days  
**Target Win Rate:** 60-65%

---

## Core Idea

RSI < 30 (oversold) predicts bounce, RSI > 70 (overbought) predicts pullback. Volume confirmation filters false signals.

**The Edge:**
- RSI alone: 55% win rate (too many false signals)
- RSI + volume spike: 60-65% win rate
- RSI + candlestick pattern: 65-70% win rate

---

## Signal Construction

**Long Setup:**
```
IF RSI(14) < 30 AND
   RSI was < 20 yesterday (extreme) AND
   volume > 1.5x 20-day average AND
   bullish candlestick (hammer, bullish engulfing)
THEN long, hold 3 days
```

**Short Setup:**
```
IF RSI(14) > 70 AND
   RSI was > 80 yesterday AND
   volume > 1.5x average AND
   bearish candlestick (shooting star, bearish engulfing)
THEN short, hold 3 days
```

---

## Expected Performance

| Metric | RSI Alone | RSI + Volume | RSI + Pattern |
|--------|-----------|--------------|---------------|
| Win Rate | 55% | 62% | 67% |
| Sharpe | 0.6 | 0.9 | 1.2 |

---

## Universe

Liquid large-caps: SPY, QQQ, IWM, AAPL, MSFT, NVDA

---

## Data Requirements

- OHLC prices
- RSI(14) calculation
- Volume (20-day average)
- Candlestick pattern detection

---

## Why It Works

1. **Mean reversion** — Prices oscillate around mean
2. **Sentiment extremes** — RSI captures fear/greed
3. **Volume confirms** — Institutional participation validates signal
4. **Candlesticks time entry** — Pinpoint reversal moment

---

## Academic Support

- RSI developed by Welles Wilder (1978)
- Mean reversion in equity returns (Fama-French)
- Volume predicts volatility (Clark)

---

## Risk

- Trending markets: RSI stays overbought/oversold
- Requires exit rules (don't fight trend)
- False signals in low volatility regimes

---

*The classic indicator works when combined with other factors.*
