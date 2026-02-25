# COIN_Strong_Uptrend_GOLD — Strategy Memory
**Asset:** COIN (Coinbase) — BTC Proxy  
**Status:** Near-Golden (93.3% win rate)  
**Discovery Date:** 2026-02-23  
**Discovery Method:** Market Regime Exploration

---

## 🎯 Breakthrough Discovery

**93.3% Win Rate with Market Regime Filter!**

Created by combining:
1. COIN RSI mean reversion (RSI < 25)
2. SPY Strong Uptrend regime filter

**Improvement over baseline:** +7.6% win rate (85.7% → 93.3%)

---

## 📊 Performance Metrics

| Metric | Value |
|--------|-------|
| **Win Rate** | **93.3%** |
| Trades | 15 |
| Avg Return | 9.12% |
| Expected Signals/Year | 7-8 |
| Hold Period | 10 days |

---

## 🔍 Strategy Logic

### Entry Conditions:
1. COIN RSI(14) < 25 (extreme oversold)
2. SPY in **Strong Uptrend** regime:
   - Price > 200-day SMA
   - ADX > 25 (strong trend)

### Exit:
- Time stop: 10 days
- Optional: +4% profit target

---

## 💡 Why It Works

**Strong Uptrend + Extreme Oversold = High Probability Snapback**

- Strong trend = institutional buying support
- Extreme RSI = temporary dislocation
- Combined = rapid mean reversion as buyers step in

**Avoid Weak Uptrends:**
- Low ADX = weak trend conviction
- Mean reversion less reliable
- Win rate drops to 66.7%

---

## 📈 Comparison to Baseline

| Strategy | Win% | Trades | Quality |
|----------|------|--------|---------|
| COIN RSI<25 (baseline) | 85.7% | 28 | ✅ Validated |
| **+ Strong Uptrend** | **93.3%** | 15 | ⭐ **Near-Golden** |
| + Weak Uptrend | 66.7% | 6 | ❌ Poor |

---

## 🎯 Deployment Recommendation

**Immediate Deployment:**
- Position size: 2-3% (high conviction)
- Signals: 7-8/year (selective but powerful)
- Expected annual return: ~60-70% (7 trades × 9% avg)

**Risk Management:**
- Time stop only (no hard stop loss)
- Max 1 position at a time (rare signals)
- Skip if SPY regime changes mid-trade

---

## ⚠️ PLATFORM VARIATION — UNDER TEST

### JT Trading Agent Implementation
JT uses **Golden Cross filter** (50d SMA > 200d SMA) instead of ADX > 25.

| Filter | Implementation | Status |
|--------|---------------|--------|
| Original (ADX > 25) | Researcher spec | 93.3% win (backtest) |
| Platform (Golden Cross) | JT implementation | 🔄 **Live testing** |

### Difference Explained
- **ADX > 25:** Measures trend **strength** (institutional momentum)
- **Golden Cross:** Measures trend **direction** (lagging indicator)

### Expected Impact
- More signals (10-15/year vs 7-8/year)
- Slightly lower win rate (80-85% vs 93.3%)
- Trade-off: Frequency vs Quality

### Test Status
**Hypothesis H#004:** Golden Cross performs acceptably (>=80% win rate)
- **Tracking:** [H004_platform_variation_test.md](../../hypotheses/H004_platform_variation_test.md)
- **Target:** 30 trades for statistical significance
- **Decision:** Accept if >=80%, request ADX if <80%

### Recommendation
Use JT's Golden Cross version but **monitor closely**. If live win rate drops below 80% after 20 trades, request ADX filter implementation.

---

## 🔬 Methodology

**Market Regime Calculation:**
```python
# From SPY data
vix_proxy = parkinson_volatility(20d) * sqrt(252) * 100
adx = trend_strength(14d)

if price > 200d_sma and adx > 25:
    regime = 'Strong Uptrend'
elif price > 200d_sma and adx <= 25:
    regime = 'Weak Uptrend'
elif price < 200d_sma and adx > 25:
    regime = 'Strong Downtrend'
else:
    regime = 'Weak Downtrend'
```

---

## 📁 Files

- Discovery script: `exploration_market_regimes.py`
- Test results: `results/COIN_STRONG_UPTREND_GOLD.json`
- Market regime data: Calculated from `silver.unified_prices` (SPY)

---

## 🔗 Related Strategies

- `COIN_SPY_Regime` — Baseline RSI + SPY filter
- `MSTR_SPY_Regime` — Similar setup for MSTR
- `Crypto_SPY_Regime` — Master comparison file

---

## 🎯 Next Steps

1. **Test on MSTR** — Does Strong Uptrend filter help MSTR too?
2. **Test on RIOT** — Expand to other crypto proxies
3. **Deploy to paper trading** — 7-8 signals/year is actionable
4. **Monitor regime transitions** — Exit if SPY drops from Strong Uptrend

---

## 📝 Research Note

**Discovery Context:**
- Original goal: Test market sentiment (failed — data too new)
- Pivot: Create market regimes from SPY price data
- Result: Discovered +7.6% improvement with Strong Uptrend filter

**Lesson:** When primary data fails, pivot to derived indicators

---

*New Golden-tier strategy discovered through exploration*  
*Date: 2026-02-23*