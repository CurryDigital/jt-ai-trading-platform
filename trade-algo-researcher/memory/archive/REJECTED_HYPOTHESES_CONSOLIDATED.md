# Rejected Hypotheses

**Last Updated:** 2026-02-21  
**Purpose:** Document failed hypotheses with reasons to avoid retesting

---

## Why Track Rejected Hypotheses?

1. **Avoid wasted effort** - Don't retest the same failed ideas
2. **Learn from failures** - Understand why strategies don't work
3. **Build knowledge base** - Know what doesn't work in markets
4. **Save time** - Focus on promising hypotheses only

---

## REJECTED HYPOTHESES

### 1. Gap Fade Strategy
**Date Tested:** 2026-02-21

**Hypothesis:** Fade overnight gaps > 2% (buy gap down, sell gap up)

**Results:**
- Tech: Sharpe -0.07, Win 50.5%
- Equity: Sharpe 0.13, Win 51.7%

**Why Rejected:**
- Win rate ~50% (coin flip, no edge)
- Gaps tend to CONTINUE in direction, not mean revert
- Average gap 3.5% suggests news-driven moves
- Fading = betting against information (losing proposition)

**Alternative to Try:**
- Gap FOLLOW strategy (go WITH the gap, not against)
- Test inversing the logic

**File:** `memory/strategies/gap_fade.md`

---

### 2. Moving Average Crossover (As Tested)
**Date Tested:** 2026-02-21

**Hypothesis:** Golden cross (20/50 MA) trend following

**Results:**
- Tech: Sharpe 0.46, Win 49.1%
- Equity: Sharpe 0.31, Win 48.7%

**Why Rejected (in current form):**
- Lagging indicator - too slow for modern markets
- Win rate below 50% (worse than random)
- Max drawdown -80%+ catastrophic
- Better alternatives exist (momentum, volume)

**Potential Enhancements (before rejecting fully):**
- Faster MAs (10/30 instead of 20/50)
- Add volume confirmation
- Only trade in strong trends

**File:** `memory/strategies/ma_crossover.md`

---

### 3. Momentum Strategy (Basic)
**Date Tested:** 2026-02-21

**Hypothesis:** Buy stocks with 20-day momentum > 5%

**Results:**
- Tech: Sharpe 0.56, Win 51.3%
- Equity: Sharpe -0.01, Win 47.0%

**Why Rejected:**
- Entry too late (16% avg momentum = chasing)
- No edge in basic form
- Win rate barely above 50%
- Better with enhancements (filters, earlier entry)

**Note:** NOT fully rejected - may work with:
- Earlier entry (3% instead of 5%)
- Trend filters
- Sector rotation

---

## LESSONS FROM FAILURES

### Pattern 1: Mean Reversion is Hard
- Gap fade failed (markets trend)
- Basic RSI worked but needed enhancement (tighter threshold)
- Lesson: Mean reversion needs EXTREME conditions

### Pattern 2: Lagging Indicators Fail
- MA crossover too slow
- By the time signal triggers, move is over
- Lesson: Need leading or coincident indicators

### Pattern 3: Simple Momentum Doesn't Work
- Buying what's already up = chasing
- Need entry timing or filters
- Lesson: Momentum needs refinement

### Pattern 4: News-Driven Moves Trend
- Gaps continue, don't fade
- Volume + price = information
- Lesson: Don't fight news/earnings

### 4. Higher Lows Trend Strategy
**Date Tested:** 2026-02-21

**Hypothesis:** Buy when price makes 3 consecutive higher lows (uptrend confirmation)

**Results:**
- Tech: Sharpe -0.11, Win 37.7%
- Equity: Sharpe 0.20, Win 39.8%

**Why Rejected:**
- Win rate below 40% (worse than random)
- Entry too late in trend (chasing)
- Simple price patterns not sufficient alone
- No volume or momentum confirmation
- Max drawdown -90%+ catastrophic

**Lessons:**
- Pure price patterns without confirmation fail
- Need volume/momentum filters
- Entry timing critical - higher lows = late signal

### 7. Gap Follow Strategy
**Date Tested:** 2026-02-22

**Hypothesis:** Buy gap up > 2% (follow momentum)

**Results:**
- Tech: Sharpe 0.37, Win 47.6%
- Equity: Sharpe -0.13, Win 46.4%

**Why Rejected:**
- Gap following worse than gap fading
- Gaps are noise, not signal
- Neither fading nor following works consistently
- Win rate below 50% in both directions

**Key Insight:**
- Gaps represent information (earnings, news)
- Can't predict direction from gap alone
- Need additional context (volume, sector, earnings)

**Comparison:**
| Strategy | Win Rate | Sharpe |
|----------|----------|--------|
| Gap Fade | 50.5% | -0.07 |
| Gap Follow | 47.6% | 0.37 |

Both fail. Gaps are not tradable signals alone.

---

### 6. Bullish Engulfing Pattern
**Date Tested:** 2026-02-22

**Hypothesis:** Small red candle followed by larger green engulfing candle = reversal signal

**Results:**
- Tech: Sharpe 0.00, Win 49.3%
- Equity: Sharpe -0.50, Win 44.7%

**Why Rejected:**
- Win rate ~50% (coin flip, no edge)
- Classic candlestick pattern not predictive in modern markets
- May work with volume confirmation but standalone fails
- Max drawdown catastrophic (-90%+)

**Lessons:**
- Candlestick patterns alone not sufficient
- Need volume or momentum confirmation
- Price-only patterns dominated by noise

---

### 5. Sector Rotation Momentum
**Date Tested:** 2026-02-21

**Hypothesis:** Buy strongest sector ETF, sell weakest (pairs trade)

**Results:**
- Sharpe: -0.43, Win 48.8%

**Why Rejected:**
- Win rate below 50%
- Negative Sharpe (losing strategy)
- Sector momentum not persistent enough
- 20-day lookback too slow for sector rotation

**Lessons:**
- Sector rotation faster than individual stocks
- Need shorter lookback (5-10 days)
- May work better with timing (economic cycle)

---

### 6. Higher Lows Trend Strategy

A hypothesis is REJECTED when:
- Win rate < 50% (worse than coin flip)
- Sharpe < 0 (losing money)
- Max drawdown > 90% (catastrophic)
- No improvement after 3+ enhancement attempts

---

## BEFORE REJECTING, TRY:

1. **Parameter tuning** - Different thresholds, periods
2. **Add filters** - Volume, trend, sector
3. **Different exit** - Profit targets, trailing stops
4. **Sector-specific** - May work in one industry only
5. **Inverse the logic** - Short instead of long, fade instead of follow

---

## REVISITING REJECTED HYPOTHESES

Can retry rejected hypotheses when:
- New data becomes available (longer history)
- Market regime changes (bull/bear)
- New filters/techniques discovered
- Different asset class available (crypto, FX)

**Current Rejected Count:** 25
**Last Updated:** 2026-02-22

---

## BATCH 3: 10 Additional Hypotheses (All Failed)
**Date Tested:** 2026-02-22

| # | Hypothesis | Win Rate | Sharpe | Trades |
|---|------------|----------|--------|--------|
| 18 | Doji Star Reversal | 49.1% | -0.11 | 470 |
| 19 | Hammer Pattern | 47.7% | -0.50 | 564 |
| 20 | Volume Climax Fade | 51.0% | -0.09 | 149 |
| 21 | 3-Day Down + Volume | 51.8% | 0.61 | 465 |
| 22 | Inside Day Breakout | 48.5% | -0.19 | 1016 |
| 23 | BB Squeeze Breakout | 47.5% | 0.27 | 528 |
| 24 | Range Expansion | 47.7% | 0.57 | 1194 |
| 25 | RSI Divergence | 49.7% | 0.10 | 1333 |
| 26 | VWAP Deviation | 51.0% | 0.34 | 6910 |
| 27 | Prev High Breakout | 47.4% | 0.01 | 3388 |

### Common Failure Patterns
1. **Candlestick patterns alone** - All failed (Doji, Hammer)
2. **Breakout strategies** - Failed (Inside Day, Prev High, BB Squeeze)
3. **Mean reversion variants** - Failed (VWAP, Volume Climax)
4. **Divergence signals** - Failed (RSI Divergence)

### Key Insight
After testing 27 hypotheses total, only **2 strategies** achieved 70%+ win rate:
- Volume Breakout (70.8%)
- RSI Mean Reversion (72.6%)

Most technical analysis patterns (candlesticks, breakouts, divergences) do NOT provide edge.

---

*This file prevents retesting failed ideas*
*Failures are learning opportunities*
*Document why to build institutional knowledge*

---

## BATCH 4: 10 Additional Hypotheses (6 Failed, 5 Pending Data)
**Date Tested:** 2026-02-22

### Tested and Failed

| # | Hypothesis | Win Rate | Sharpe | Trades |
|---|------------|----------|--------|--------|
| 28 | Shooting Star | 46.1% | -0.50 | 895 |
| 29 | Morning Star | 48.6% | 0.18 | 775 |
| 34 | 52-Week High Breakout | 52.2% | 0.34 | 276 |
| 35 | MA20 Bounce | 48.6% | 0.01 | 2,656 |
| 36 | Resist Break | 47.4% | 0.63 | 409 |
| 38 | Fib 61.8% | 48.7% | 0.05 | 6,218 |

### Pending Data (Not Tested Yet)

| # | Hypothesis | Data Required | Requested From |
|---|------------|---------------|----------------|
| 30 | ADX Trend Strength | ADX indicator | JT Trading |
| 31 | Stochastic Oversold | Stochastic | JT Trading |
| 32 | MACD Histogram Div | MACD | JT Trading |
| 33 | PSAR Flip | Parabolic SAR | JT Trading |
| 37 | Volume Profile POC | Volume Profile | JT Trading |

### Pattern Confirmed

**Classic TA continues to fail:**
- Candlestick patterns: ~48% win rate
- Support/Resistance: ~48% win rate
- Breakouts: ~50% win rate
- Fibonacci: ~49% win rate

**Running Total:** 29 rejected, 5 pending data

---

## DATA REQUEST SENT TO JT TRADING

**File:** `DATA_REQUEST_JT_TRADING.md`

**Requested:**
1. MACD (Priority 1)
2. Stochastic (Priority 1)
3. ADX (Priority 2)
4. Parabolic SAR (Priority 2)
5. Volume Profile (Priority 3)

**Timeline:** 1-4 weeks depending on complexity


---

## BATCH 5: 5 Technical Indicator Hypotheses (All Failed)
**Date Tested:** 2026-02-22
**Method:** Calculated indicators from price data (2022-2024)

| # | Hypothesis | Win Rate | Sharpe | Trades | Result |
|---|------------|----------|--------|--------|--------|
| 30 | ADX Trend Strength (>25, +DI>-DI) | 49.4% | 0.59 | 4,655 | ❌ |
| 31 | Stochastic Oversold (K<20) | 51.5% | 0.02 | 2,692 | ❌ |
| 32 | MACD Histogram Divergence | 48.8% | -0.07 | 566 | ❌ |
| 33 | MACD Crossover | 50.5% | 0.73 | 491 | ❌ |
| 37 | VWAP Mean Reversion | 50.5% | 0.34 | 8,648 | ❌ |

### Key Finding

**Classic Technical Indicators DON'T WORK:**
- All ~50% win rates (coin flip)
- No statistical edge
- Confirmed across 5 different indicators
- ADX, MACD, Stochastic, VWAP all failed

### Final Lesson Learned

After testing 38 hypotheses:
- **34 rejected** (~90%)
- **3 Golden** (7.9%) - Volume BO, RSI MR, Inside Day
- **2 Validated** (5.3%) - 3-Day combo, Range combo

**Only strategies with real edge:**
1. Volume + Price confirmation (70.8%)
2. Extreme RSI mean reversion (72.6%)
3. Combination: Setup + Volume + Breakout (74.4%)

**Everything else = random noise**

---

*Updated: 2026-02-22*
*Total: 34 rejected, 3 Golden, 2 Validated*

---

## BATCH 6: 10 Hypotheses with Calculated Indicators (2 Validated)
**Date Tested:** 2026-02-22
**Data Source:** gold.technical_indicators_calculated

### ✅ VALIDATED (2)

| # | Hypothesis | Win Rate | Sharpe | Trades | Status |
|---|------------|----------|--------|--------|--------|
| **42** | **Stochastic + RSI Extreme** | **56.3%** | 0.94 | 829 | ✅ Validated |
| **46** | **3-Indicator Combo** | **62.9%** | 1.32 | 35 | ✅ Validated |

#### H42: Stochastic + RSI Extreme
**Entry:** Stoch K < 10 AND RSI < 15 (double extreme oversold)
**Results:** 56.3% win, 0.94 Sharpe, 829 trades
**Note:** Good sample size, moderate edge

#### H46: 3-Indicator Combo
**Entry:** RSI < 25 + MACD histogram improving + Volume > 2x
**Results:** 62.9% win, 1.32 Sharpe, 35 trades
**Note:** Small sample, needs more testing but promising

### ❌ FAILED (6)

| # | Hypothesis | Win Rate | Sharpe | Trades | Result |
|---|------------|----------|--------|--------|--------|
| 39 | BB Squeeze + Breakout | 43.5% | 0.44 | 480 | ❌ |
| 40 | RSI + MACD Combo | 48.2% | 0.38 | 114 | ❌ |
| 43 | BB Mean Reversion | 50.9% | 0.30 | 1,130 | ❌ |
| 44 | ADX + Volume Combo | 45.0% | 0.47 | 647 | ❌ |
| 45 | VWAP + Volume Break | 42.1% | 0.09 | 240 | ❌ |

### Insufficient Data (2)

| # | Hypothesis | Trades | Issue |
|---|------------|--------|-------|
| 41 | ATR Expansion | 22 | Too rare |
| 47 | Extreme BB MeanRev | 10 | Too rare |
| 48 | Trend + Volume | 11 | Too rare |

### Key Finding

**Combinations work better than single indicators:**
- Single indicator strategies: ~48% win rate
- Two indicators (Stoch+RSI): 56.3% win rate ✅
- Three indicators (RSI+MACD+Vol): 62.9% win rate ✅

**Pattern:** More confirmation filters = fewer but higher quality trades

---

*Updated: 2026-02-22*
*Total: 42 rejected, 3 Golden, 4 Validated*