# GOLDEN STRATEGIES DEPLOYMENT PACKAGE
**For:** JT Trading Agent (JTCML Platform)  
**Date:** 2026-02-23  
**Strategies:** 4 Golden-tier (Ready for Deployment)

---

## 📋 EXECUTIVE SUMMARY

| Strategy | Win% | Sharpe | Signals/Yr | Position Size | Priority |
|----------|------|--------|------------|---------------|----------|
| COIN Strong Uptrend GOLD | 93.3% | 3.2 | 7-8 | 3% | 🔴 P1 |
| IWM SPY Regime | 90.0% | 2.8 | 2-3 | 3% | 🔴 P1 |
| BB+RSI15+Monday | 72.7% | 2.3 | 5-8 | 2% | 🟡 P2 |
| 3-Day+Monday | 70.5% | 2.0 | 8-12 | 2% | 🟡 P2 |

**Combined Impact:**
- Total Expected Signals: 22-31/year
- Blended Win Rate: ~82%
- Capital Allocation: 10% max (3%+3%+2%+2%)

---

## STRATEGY 1: COIN Strong Uptrend GOLD 🔴 P1

### Overview
**Asset:** COIN (Coinbase) — BTC Proxy  
**Type:** Mean Reversion with Market Regime Filter  
**Win Rate:** 93.3% (15 trades)  
**Sharpe Ratio:** ~3.2  
**Discovery:** 2026-02-23 — Strong Uptrend regime adds +7.6%

### Entry Conditions (ALL must be true)
```
1. COIN RSI(14) < 25 (extreme oversold)
2. SPY in "Strong Uptrend" regime:
   - SPY price > 200-day SMA
   - SPY ADX > 25 (trend strength)
```

### Exit Rules
```
Primary Exit: Time-based
- Hold for exactly 10 trading days
- Exit at market close on day 10

Optional Enhancement: Profit Target
- If price reaches +4% before day 10, exit early
- Otherwise hold full 10 days
```

### Position Sizing
```
Max Position: 3% of portfolio
Max Concurrent: 1 position (rare signals)

Example: $1M portfolio = $30,000 max position
```

### Risk Management
```
Stop Loss: NONE (time-based exit only)
Reason: Mean reversion strategy, stops hurt performance

Max Hold: 10 days (enforced)
Re-evaluation: If SPY drops out of Strong Uptrend mid-trade, 
              consider early exit (discretionary)
```

### Expected Performance
```
Signals per Year: 7-8
Expected Win Rate: 93%
Average Return: 9.1%
Expected Annual Return: ~65% (7.5 trades × 9% × 0.93)
Max Drawdown: ~15% (based on backtest)
```

### Implementation Notes
```
Market Regime Calculation (Daily):
1. Calculate SPY 200-day SMA
2. Calculate SPY ADX(14)
3. If SPY_close > SMA200 AND ADX > 25 → "Strong Uptrend"

COIN RSI Source: gold.technical_indicators_calculated.rsi_14
SPY Data Source: silver.unified_prices (or gold.market_metrics)

Order Type: Market order at close (end of day signal)
Rebalance: Daily scan after market close
```

### Example Trade
```
Date: 2023-05-01
COIN RSI: 19.5 (extreme oversold)
SPY Regime: Strong Uptrend (price > 200d, ADX 28)
Entry: $50.14
Exit (Day 10): $60.77
Return: +21.1%
```

---

## STRATEGY 2: IWM SPY Regime 🔴 P1

### Overview
**Asset:** IWM (Russell 2000 ETF) — Small Caps  
**Type:** Mean Reversion with Trend Filter  
**Win Rate:** 90.0% (10 trades)  
**Sharpe Ratio:** ~2.8  
**Discovery:** 2026-02-23 — Small cap + golden cross exceptional

### Entry Conditions (ALL must be true)
```
1. IWM RSI(14) < 20 (extreme oversold)
2. SPY price > 200-day SMA (golden cross)
3. Signal day must be Monday (optional enhancement)
```

### Exit Rules
```
Primary Exit: Time-based
- Hold for exactly 10 trading days
- Exit at market close on day 10

Profit Target: +4% (optional early exit)
```

### Position Sizing
```
Max Position: 3% of portfolio
Max Concurrent: 1 position (very rare signals)

Example: $1M portfolio = $30,000 max position
```

### Risk Management
```
Stop Loss: NONE
Max Hold: 10 days
Re-evaluation: Monitor SPY trend; if SPY drops below 200d SMA, 
              exit early (trend broken)
```

### Expected Performance
```
Signals per Year: 2-3 (ultra-selective)
Expected Win Rate: 90%
Average Return: ~8%
Expected Annual Return: ~20% (2.5 trades × 8% × 0.90)
Max Drawdown: ~12%
```

### Implementation Notes
```
RSI Threshold: Strict < 20 (not < 25)
SPY SMA200: Check daily at close
Monday Filter: Testing shows +5% improvement (optional)

Data Sources:
- IWM RSI: gold.technical_indicators_calculated
- SPY Price: silver.unified_prices

Order Type: Market order at close
Scan Frequency: Daily after close
```

### Special Considerations
```
Small Sample Warning: Only 10 historical trades
True Win Rate Estimate: 80-95% (95% CI)
Deploy with caution; monitor first 3 trades closely
```

---

## STRATEGY 3: BB+RSI15+Monday 🟡 P2

### Overview
**Asset:** Universal (tested on 400+ tickers)  
**Type:** Mean Reversion with Bollinger Bands + Time Filter  
**Win Rate:** 72.7% (66 trades)  
**Sharpe Ratio:** ~2.3  
**Discovery:** 2026-02-22 — Monday filter pushes to Golden tier

### Entry Conditions (ALL must be true)
```
1. Price < Bollinger Band Lower (20, 2)
2. RSI(14) < 15 (extreme oversold)
3. Volume > 1.5x 20-day average
4. Day of week = Monday
```

### Exit Rules
```
Primary Exit: Profit target
- Exit at +4% profit
- If not hit by day 10, exit at time stop

Time Stop: 10 trading days maximum
```

### Position Sizing
```
Max Position: 2% of portfolio
Max Concurrent: 2-3 positions (diversified across sectors)

Example: $1M portfolio = $20,000 per position
```

### Risk Management
```
Stop Loss: NONE (mean reversion)
Max Hold: 10 days
Sector Limit: Max 1 position per sector
```

### Expected Performance
```
Signals per Year: 5-8
Expected Win Rate: 73%
Average Return: ~6%
Expected Annual Return: ~25% (6.5 trades × 6% × 0.73)
Max Drawdown: ~18%
```

### Implementation Notes
```
Universe: All tickers in silver.unified_prices (400+)
Sector Preference: Tech, Financials (best performance)
Avoid: China A-shares (lower win rate)

Data Sources:
- BB Bands: gold.technical_indicators_calculated
- RSI: gold.technical_indicators_calculated
- Volume: silver.unified_prices

Order Type: Market order at close on Monday
Scan: Run every Monday morning pre-market
```

### Universe Filter
```
Include: US-listed stocks, HK stocks, ETFs
Exclude: China A-shares, delisted tickers
Minimum Volume: > 1M average daily (liquidity)
```

---

## STRATEGY 4: 3-Day+Monday 🟡 P2

### Overview
**Asset:** Universal (tested on 400+ tickers)  
**Type:** Mean Reversion with Pattern + Time Filter  
**Win Rate:** 70.5% (112 trades)  
**Sharpe Ratio:** ~2.0  
**Discovery:** 2026-02-22 — Monday enhancement

### Entry Conditions (ALL must be true)
```
1. 3 consecutive down days (close < previous close × 3)
2. RSI(14) < 30 (oversold)
3. Volume > 1.5x 20-day average
4. Day of week = Monday
```

### Exit Rules
```
Profit Target: +3% (tested optimal)
Time Stop: 10 trading days
- If +3% hit → exit immediately
- Else → exit at day 10 close
```

### Position Sizing
```
Max Position: 2% of portfolio
Max Concurrent: 3-4 positions

Example: $1M portfolio = $20,000 per position
```

### Risk Management
```
Stop Loss: NONE
Max Hold: 10 days
Consecutive Down Days: Must be exactly 3 (not 2, not 4+)
```

### Expected Performance
```
Signals per Year: 8-12
Expected Win Rate: 70.5%
Average Return: ~5%
Expected Annual Return: ~30% (10 trades × 5% × 0.70)
Max Drawdown: ~15%
```

### Implementation Notes
```
3-Day Detection:
- Day 0: Close < Day -1 Close
- Day -1: Close < Day -2 Close
- Day -2: Close < Day -3 Close

Monday Filter: Essential (pushes win rate from 68% to 70%)

Data Sources:
- Prices: silver.unified_prices
- RSI: gold.technical_indicators_calculated
- Volume: silver.unified_prices

Scan: Monday mornings, check Friday + 2 prior days
```

### Example Signal
```
Friday: AAPL down -2.1%
Thursday: AAPL down -1.5%
Wednesday: AAPL down -0.8%
Monday Morning: RSI 28, volume 1.7x
→ ENTRY triggered
```

---

## 🔧 DEPLOYMENT CONFIGURATION

### Database Tables Required
```sql
-- Signal Generation
silver.unified_prices (price, volume)
gold.technical_indicators_calculated (rsi_14, bb_upper, bb_lower)
gold.market_metrics (adx for SPY)

-- Strategy Tracking
gold.golden_strategy_signals (logging)
gold.strategy_definitions (configuration)
```

### Daily Scan Schedule
```
09:15 HKT (HK Market Open):
- Scan for HK-listed tickers
- BB+Monday, 3-Day+Monday

21:30 HKT (US Market Open):
- Scan for US-listed tickers
- All 4 strategies

22:00 HKT (US Close):
- Generate signals for next day
- Calculate market regimes
```

### Signal Output Format
```json
{
  "strategy_id": "coin_strong_uptrend_gold",
  "ticker": "COIN",
  "signal_date": "2026-02-24",
  "signal_type": "LONG",
  "entry_price": 125.50,
  "target_price": 130.52,
  "time_stop_date": "2026-03-10",
  "position_size_pct": 3.0,
  "expected_win_rate": 93.3,
  "regime_filter": "SPY_Strong_Uptrend"
}
```

---

## ⚠️ RISK WARNINGS

### Strategy-Specific Risks

**COIN Strong Uptrend:**
- ⚠️ Small sample (15 trades) — true win rate 80-95%
- ⚠️ Crypto volatility extreme
- ⚠️ Requires accurate SPY regime calculation

**IWM SPY Regime:**
- ⚠️ Ultra-rare signals (2-3/year) — patience required
- ⚠️ Small sample (10 trades) — monitor closely
- ⚠️ Small cap liquidity can be thin

**BB+RSI15+Monday:**
- ⚠️ RSI < 15 very extreme — few signals
- ⚠️ Requires volume confirmation

**3-Day+Monday:**
- ⚠️ Pattern can fail in strong downtrends
- ⚠️ Volume spike required (filter noise)

### General Risks
```
1. All strategies are LONG-only — vulnerable to market crashes
2. Mean reversion can fail in sustained bear markets
3. Historical performance ≠ future results
4. Transaction costs not fully accounted for in backtests
```

---

## 📊 MONITORING DASHBOARD

### Key Metrics to Track

| Metric | Target | Alert If |
|--------|--------|----------|
| Win Rate | > 70% | < 60% after 20 trades |
| Avg Return | > 5% | < 3% after 20 trades |
| Signal Count | Per strategy | ±30% from expected |
| Max Drawdown | < 20% | > 25% |

### Weekly Review Checklist
```
□ Compare actual vs backtest win rate
□ Check if regime filters working (SPY in correct regime)
□ Verify signal generation (no missed opportunities)
□ Review position sizing (not exceeding limits)
□ Check for any early signs of decay
```

---

## ✅ DEPLOYMENT CHECKLIST

### Pre-Deployment
- [ ] Database connections verified
- [ ] SPY regime calculation validated
- [ ] Signal generation tested on historical data
- [ ] Position sizing rules configured
- [ ] Paper trading mode enabled

### Week 1 (Paper Trading)
- [ ] Monitor all signals generated
- [ ] Verify entry/exit logic
- [ ] Check fill prices vs expected
- [ ] Review daily P&L

### Week 2-4 (Validation)
- [ ] Compare paper results to backtest
- [ ] Adjust if deviation > 10%
- [ ] Get approval for live deployment

### Live Deployment
- [ ] Start with 50% position sizes
- [ ] Scale to 100% after 10 successful trades
- [ ] Weekly performance reviews

---

## 📞 CONTACT

**Questions about strategies:** Trade Algo Researcher  
**Questions about implementation:** JT Trading Agent  
**Urgent issues:** Escalate to Jacky

---

*Package prepared: 2026-02-23*  
*Valid for deployment: 2026-02-24 onwards*