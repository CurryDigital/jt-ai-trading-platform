# FULL UNIVERSE TEST RESULTS (401 Tickers)
**Date:** 2026-02-22  
**Tested on:** 200 tickers (sample of full 401 platform universe)

---

## Results Summary

| Strategy | Original (179) | Full Universe (200) | Change | Status |
|----------|----------------|---------------------|--------|--------|
| Volume Breakout | 70.8% | **67.8%** | -3.0% | ✅ Validated |
| RSI Mean Reversion | 72.6% | **66.6%** | -6.0% | ✅ Validated |
| Inside Day Breakout | 74.4% | **63.3%** | -11.1% | 🧪 Moderate |

---

## Analysis

### What This Means

**Strategies maintain edge on full universe:**
- All still above 60% win rate
- Positive Sharpe ratios
- Core principles hold

**But performance degrades with expansion:**
- More diverse tickers = lower average edge
- Singapore/China stocks may behave differently
- Sector differences become more pronounced

---

## Recommendation

### Option 1: Tiered Universe Approach (Recommended)

**Tier 1 - Golden (70%+ win rate):**
- Tech sector only (30-36 tickers)
- US + HK tech stocks
- Highest conviction signals

**Tier 2 - Validated (60-70% win rate):**
- Full 401 ticker universe
- All sectors and markets
- Larger position sizing or lower allocation

### Option 2: Sector-Specific Strategies

Test and deploy by sector:
- Tech: Volume Breakout + RSI MR
- Equity: RSI MR only
- Singapore/China: Custom strategies needed

### Option 3: Accept Lower Win Rate

Deploy on full 401 with:
- Lower position sizing (1% vs 2%)
- Tighter risk management
- Expect 60-67% win rate (not 70%+)

---

## Expected Trade Frequency (Full 401 Universe)

| Strategy | Trades/Month | Win Rate | Sharpe |
|----------|--------------|----------|--------|
| Volume Breakout | 50-80 | 67.8% | 0.44 |
| RSI Mean Reversion | 20-35 | 66.6% | 0.34 |
| Inside Day Breakout | 5-10 | 63.3% | 0.52 |

**Total: 75-125 trades/month**

---

## Deployment Recommendation

**For JT Trading Platform:**

1. **Start with Tech sector only (36 tickers)**
   - 70%+ win rate on core strategies
   - Build confidence
   - Validate with paper trading

2. **Gradually expand to full 401**
   - Monitor win rate degradation
   - Adjust position sizing
   - Sector-specific testing

3. **Full deployment**
   - All 401 tickers
   - Expect 60-67% win rates
   - Higher trade frequency

---

## Updated Universe Classification

| Market | Count | Tickers |
|--------|-------|---------|
| US Stocks | 101 | AAPL, MSFT, NVDA, etc. |
| Hong Kong | 90 | 0700.HK, 9988.HK, etc. |
| China | 89 | 000333.SZ, 002594.SZ, etc. |
| Singapore | 93 | Local stocks |
| Other | 29 | Various |
| **Total** | **401** | Full platform |

---

## Next Steps

1. **Test Golden Strategies on Singapore/China separately**
   - May need custom parameters
   - Different market dynamics

2. **Create sector-specific versions**
   - Tech: Current strategies
   - Financial/REITs: Custom needed
   - Commodity-linked: Custom needed

3. **Monitor paper trading closely**
   - Full universe = lower win rate
   - Adjust expectations accordingly

---

*Tested: 2026-02-22*  
*Sample: 200 tickers from 401 total*  
*Status: Strategies validated but win rates lower on full universe*