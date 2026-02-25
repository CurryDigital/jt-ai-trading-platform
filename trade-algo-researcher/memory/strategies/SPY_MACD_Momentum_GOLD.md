# SPY MACD Momentum Strategy — GOLDEN
**Classification:** 🏆 Golden (Test ≥70%, n≥30, Decay <15%)
**Asset:** SPY (S&P 500 ETF)
**Strategy Type:** Momentum / Trend Following
**Last Updated:** 2026-02-24

---

## Performance Metrics

| Metric | Value | 95% CI |
|--------|-------|--------|
| **Test Win Rate** | **78.4%** | [64.5%, 88.2%] |
| Sample Size | 51 trades | — |
| Wins/Losses | 40W / 11L | — |
| Avg Return | +0.23% | — |
| Test Period | 2023-2024 | — |

---

## Entry Criteria

**H2: MACD Momentum Continuation**

1. **MACD > 0** (bullish momentum)
   - MACD line above zero = bullish trend

2. **MACD Histogram > 0** (accelerating)
   - Histogram positive = momentum increasing
   - MACD line above signal line

3. **Price > SMA20** (short-term uptrend)
   - Confirms price alignment with momentum

4. **RSI < 65** (not overbought)
   - Avoid extreme overbought conditions
   - Room for further upside

---

## Exit Criteria

**Hold Period:** 5 trading days

**Logic:** Capture momentum continuation over 1-week period

---

## Signal Frequency

| Period | Signals | Signals/Year |
|--------|---------|--------------|
| 2023-2024 | 51 | ~25 |

---

## Why It Works

1. **Momentum Persistence:** MACD > 0 + Histogram > 0 = strong bullish momentum
2. **Trend Alignment:** Price > SMA20 confirms short-term trend
3. **Not Overbought:** RSI < 65 provides safety buffer
4. **Large Cap ETF:** SPY's liquidity and trend persistence

---

## Comparison to Other SPY Strategies

| Strategy | Win Rate | n | Type |
|----------|----------|---|------|
| SPY MACD Momentum | **78.4%** | 51 | Momentum |
| SPY Pullback | 74.5% | 51 | Pullback |
| SPY BB Walk | 78.9% | 57 | Trend |
| SPY ADX Trend | 79.6% | 191 | Trend |

---

## Deployment Status

🟡 **Ready for Paper Trading**

**Recommended Sizing:** 5-10% of portfolio per signal

---

*Discovered: 2026-02-24 Continuous Research Batch*
