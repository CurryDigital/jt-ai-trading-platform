# Continuous Strategy Research — 2026-02-24 12:00 UTC
**Mission:** Research, test, and improve trading strategies
**Researcher:** Trade Algo Researcher
**Status:** 🔄 IN PROGRESS

---

## Today's Hypotheses (3 New)

### H1: Bearish Trend Continuation (Short Strategy)
**Concept:** Short strong downtrends — test if trend following works on short side

**Entry Criteria:**
- ADX > 25 (strong trend)
- Price < 50-day SMA (downtrend)
- RSI between 50-70 (not oversold, room to fall)
- Volume > average (confirms participation)

**Exit:** 5-day hold (cover)

**Rationale:** If trend following works long, it should work short. Tests bearish capability.

**Tickers to Test:** SPY, QQQ, TSLA, NVDA, META, AMD, AAPL, MSFT, COIN, MSTR

---

### H2: Multi-Timeframe Momentum (Weekly + Daily)
**Concept:** Weekly trend + Daily pullback = high-probability continuation

**Entry Criteria:**
- Weekly close > Weekly SMA20 (bullish weekly trend)
- Daily RSI < 40 (oversold daily pullback)
- Daily ADX > 20 (trending on daily)
- Price > 200-day SMA (long-term uptrend)

**Exit:** 5-day hold

**Rationale:** Strong weekly trends with healthy daily pullbacks should continue.

**Tickers to Test:** SPY, QQQ, NVDA, MSFT, AAPL, META, AMD

---

### H3: Volume-Confirmed Breakout
**Concept:** Breakouts with volume confirmation have higher follow-through

**Entry Criteria:**
- Price breaks above 20-day high
- Volume > 1.5x 20-day average
- ATR < 5% of price (not too volatile)
- RSI < 70 (not overbought)

**Exit:** 3-day hold (momentum burst capture)

**Rationale:** Volume confirms institutional participation in breakout.

**Tickers to Test:** SPY, QQQ, TSLA, NVDA, META, AMD, COIN, MSTR

---

## Validation Protocol

For each hypothesis:
1. **Walk-forward testing:** Train 2021-2022, Test 2023-2024
2. **Minimum n=30** for statistical significance
3. **Calculate 95% confidence intervals**
4. **Report decay** (train vs test)
5. **Promote to Golden if:** Test ≥70%, n≥30, Decay <15%

---

## Expected Outcomes

| Hypothesis | Expected Win% | Expected Signals/Yr | Confidence |
|------------|---------------|---------------------|------------|
| H1 Bearish Trend | 55-65% | 20-40 | Medium (untested) |
| H2 Multi-TF | 65-75% | 10-20 | High (logic sound) |
| H3 Vol Breakout | 60-70% | 30-50 | Medium (volume edge) |

---

## Research Notes

**Market Context:**
- 2023-2024 was strong bull market → may bias against bearish strategies
- Most existing strategies are long-only
- Need bearish strategies for market downturns

**Key Questions:**
1. Does trend following work short? (H1)
2. Does weekly context improve daily signals? (H2)
3. Does volume confirmation add edge? (H3)

---

*Research started: 2026-02-24 12:00 UTC*
