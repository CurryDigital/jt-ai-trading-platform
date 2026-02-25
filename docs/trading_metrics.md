# Popular Trading Strategy Metrics & Indicators

*Quick reference for technical analysis and quantitative trading*

---

## 1. Momentum Indicators

| Indicator | Description | Typical Usage |
|-----------|-------------|---------------|
| **RSI** (Relative Strength Index) | Measures speed/magnitude of price movements on a 0-100 scale | Overbought (>70), Oversold (<30), Divergences |
| **Stochastic Oscillator** | Compares closing price to price range over period (%K and %D lines) | Overbought (>80), Oversold (<20), Crossovers |
| **CCI** (Commodity Channel Index) | Measures deviation from average price | Overbought (>100), Oversold (<-100) |
| **Williams %R** | Inverse of Stochastic; measures momentum (-100 to 0) | Overbought (>-20), Oversold (<-80) |
| **MFI** (Money Flow Index) | RSI with volume weighting | Confirms RSI signals with volume |
| **ROC** (Rate of Change) | Percentage change in price over N periods | Trend strength, momentum shifts |

---

## 2. Trend Indicators

| Indicator | Description | Typical Usage |
|-----------|-------------|---------------|
| **MACD** (Moving Average Convergence Divergence) | Difference between 12 EMA and 26 EMA, with signal line (9 EMA) | Crossovers, histogram momentum, divergences |
| **SMA** (Simple Moving Average) | Arithmetic mean of prices over N periods | Trend direction, support/resistance |
| **EMA** (Exponential Moving Average) | Weighted average favoring recent prices | Faster reaction to price changes |
| **ADX** (Average Directional Index) | Measures trend strength (0-100), derived from +DI and -DI | Trend strength >25 = strong, <20 = weak |
| **Parabolic SAR** | Trailing stop-and-reverse dots above/below price | Entry/exit signals, stop placement |
| **Ichimoku Cloud** | Complex system: Tenkan-sen, Kijun-sen, Senkou Span A/B, Chikou Span | Trend, support/resistance, momentum |

---

## 3. Volume Indicators

| Indicator | Description | Typical Usage |
|-----------|-------------|---------------|
| **Volume** | Raw number of shares/contracts traded | Confirm trends, spot breakouts |
| **VWAP** (Volume-Weighted Average Price) | Average price weighted by volume | Institutional benchmark, intraday support/resistance |
| **OBV** (On-Balance Volume) | Cumulative volume: +vol on up days, -vol on down days | Volume trend, divergences with price |
| **Chaikin Money Flow (CMF)** | Money flow volume over N periods | Buying/selling pressure |
| **Accumulation/Distribution (A/D Line)** | Money flow multiplier × volume | Trend confirmation, divergences |
| **Volume Profile** | Volume traded at specific price levels | Support/resistance zones, point of control |

---

## 4. Volatility Indicators

| Indicator | Description | Typical Usage |
|-----------|-------------|---------------|
| **Bollinger Bands** | SMA ± 2 standard deviations | Squeeze = low vol (breakout coming), expansion = high vol |
| **ATR** (Average True Range) | Average of true range (high-low or gaps) | Stop loss placement, position sizing |
| **Keltner Channels** | EMA ± ATR multiplier | Trend following, breakout signals |
| **Donchian Channels** | Highest high and lowest low over N periods | Breakout trading, trend identification |

---

## 5. K-Line / Candlestick Patterns

### Single Candle Patterns
| Pattern | Description | Signal |
|---------|-------------|--------|
| **Doji** | Open ≈ Close, small body | Indecision, potential reversal |
| **Hammer** | Small body at top, long lower wick | Bullish reversal (at bottom) |
| **Hanging Man** | Small body at top, long lower wick | Bearish reversal (at top) |
| **Shooting Star** | Small body at bottom, long upper wick | Bearish rejection |
| **Marubozu** | No wicks, full body | Strong momentum |

### Multi-Candle Patterns
| Pattern | Description | Signal |
|---------|-------------|--------|
| **Engulfing** | Second candle fully engulfs first | Bullish/Bearish reversal |
| **Morning Star** | Bearish → Small indecision → Bullish | Bullish reversal |
| **Evening Star** | Bullish → Small indecision → Bearish | Bearish reversal |
| **Harami** | Small candle inside previous large candle | Potential reversal |
| **Three White Soldiers** | Three consecutive bullish candles | Strong bullish continuation |
| **Three Black Crows** | Three consecutive bearish candles | Strong bearish continuation |

---

## 6. Market Breadth & Sentiment

| Metric | Description | Usage |
|--------|-------------|-------|
| **VIX** (Volatility Index) | Expected 30-day volatility from SPX options | Fear gauge, contrarian indicator |
| **Put/Call Ratio** | Total puts traded / total calls traded | Extreme readings = sentiment extremes |
| **Advance-Decline Line** | Net advancing stocks - declining stocks | Market breadth, divergences with index |
| **Fear & Greed Index** | Composite of 7 sentiment indicators | 0 (Extreme Fear) to 100 (Extreme Greed) |

---

## 7. Risk & Performance Metrics

| Metric | Formula | Interpretation |
|--------|---------|----------------|
| **Sharpe Ratio** | (Return - Risk-Free Rate) / StdDev | Risk-adjusted return (>1 good, >2 great) |
| **Sortino Ratio** | (Return - Risk-Free Rate) / Downside StdDev | Sharpe focusing only on downside risk |
| **Max Drawdown** | (Peak - Trough) / Peak | Worst peak-to-trough decline |
| **Win Rate** | Winning Trades / Total Trades | % of profitable trades |
| **Profit Factor** | Gross Profit / Gross Loss | >1.5 = good, >2 = excellent |
| **Expectancy** | (Win% × Avg Win) - (Loss% × Avg Loss) | Expected value per trade |
| **Calmar Ratio** | CAGR / Max Drawdown | Return relative to worst drawdown |

---

## 8. Quantitative Strategy Metrics

| Metric | Description |
|--------|-------------|
| **Beta (β)** | Correlation to market (β=1 moves with market) |
| **Alpha (α)** | Excess return vs. benchmark |
| **Information Ratio** | Active Return / Tracking Error |
| **R-squared** | % of movement explained by benchmark |
| **Skewness** | Asymmetry of return distribution |
| **Kurtosis** | Tail risk (fat tails = higher kurtosis) |

---

## Quick Reference: Common Timeframes

| Indicator | Short-Term | Medium-Term | Long-Term |
|-----------|------------|-------------|-----------|
| RSI | 7-9 periods | 14 periods | 21 periods |
| MACD | (6,13,4) | (12,26,9) | (24,52,18) |
| SMA/EMA | 10, 20 | 50 | 200 |
| Bollinger Bands | 10 periods | 20 periods | 50 periods |
| ATR | 10 periods | 14 periods | 20 periods |
| Stochastic | (5,3,3) | (14,3,3) | (21,5,5) |

---

*Document version: 2026-02-25*
*Source: JTCML Trading Knowledge Base*
