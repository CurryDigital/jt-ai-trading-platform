# Deployment Index
**For:** JT Trading Implementation  
**Date:** 2026-02-22  
**Status:** Ready for Implementation (Full 401 Ticker Universe)

---

## 🎯 TIERED DEPLOYMENT STRATEGY

### Tier 1: Golden (Tech Only - 36 Tickers) 🏆
Highest conviction, 70%+ win rates

| # | Strategy | Win Rate | Sharpe | Trades/Mo | File |
|---|----------|----------|--------|-----------|------|
| 1 | **Inside Day Breakout** | **74.4%** | 2.09 | 1-2 | `inside_day_breakout_deployment.md` |
| 2 | **RSI Mean Reversion** | **72.6%** | 2.26 | 2-4 | `rsi_mean_reversion_deployment.md` |
| 3 | **Volume Breakout** | **70.8%** | 1.48 | 8-15 | `volume_breakout_deployment.md` |

**Total: 11-21 trades/month, 70%+ win rate**

---

### Tier 2: Validated (Full Universe - 401 Tickers) ✅
Good edge, 60-70% win rates

| Strategy | Win Rate | Trades/Mo | Expected |
|----------|----------|-----------|----------|
| Volume Breakout | 67.8% | 50-80 | Validated |
| RSI Mean Reversion | 66.6% | 20-35 | Validated |
| Inside Day Breakout | 63.3% | 5-10 | Moderate |

**Total: 75-125 trades/month, 60-67% win rate**

---

## Full Platform Universe (401 Tickers)

| Market | Count | Sample Tickers |
|--------|-------|----------------|
| **US Stocks** | 101 | AAPL, MSFT, NVDA, GOOGL, META, TSLA, AMZN, AMD, AVGO, NFLX, etc. |
| **Hong Kong** | 90 | 0700.HK, 9988.HK, 3690.HK, 1024.HK, 0941.HK, etc. |
| **China A-Shares** | 89 | 000333.SZ, 002594.SZ, 300750.SZ, 600036.SS, etc. |
| **Singapore** | 93 | Local Singapore stocks |
| **Other** | 29 | Various international |
| **TOTAL** | **401** | Full JT Trading Platform |

---

## Quick Reference: Buy/Sell Signals

### 1. Inside Day Breakout (Best Strategy)
```
BUY:  Inside day yesterday AND Volume > 2x AND Breakout > 2%
SELL: +5% profit target OR 5 days max
```
- **Tech Only:** 74.4% win rate
- **Full Universe:** 63.3% win rate

### 2. RSI Mean Reversion
```
BUY:  RSI(14) < 10 (Tech) or < 15 (Equity)
SELL: +4% profit target OR 10 days max
```
- **Tech Only:** 72.6% win rate
- **Full Universe:** 66.6% win rate

### 3. Volume Breakout
```
BUY:  Volume > 2.0x avg AND Price up > 4%
SELL: +5% profit target OR 10 days max
```
- **Tech Only:** 70.8% win rate
- **Full Universe:** 67.8% win rate

---

## Deployment Recommendation

### Phase 1: Tech Only (Start Here) 🚀
- **Universe:** 36 Tech tickers (US + HK)
- **Strategies:** All 3 Golden strategies
- **Expected:** 11-21 trades/month, 70%+ win rate
- **Position Size:** 2% per trade
- **Risk:** Low - proven edge

### Phase 2: Gradual Expansion
- Add Equity sector (Financial, Industrial, etc.)
- Monitor win rate degradation
- Adjust position sizing

### Phase 3: Full Universe
- All 401 tickers
- 75-125 trades/month
- Expect 60-67% win rates
- Higher trade frequency

---

## Risk Parameters

| Parameter | Tier 1 (Tech) | Tier 2 (Full) |
|-----------|---------------|---------------|
| Position Size | 2% | 1-2% |
| Max Concurrent | 5-8 | 10-15 |
| Max Exposure | 10-16% | 15-30% |
| Profit Target | +4-5% | +4-5% |

---

## Performance Expectations

### Tier 1 - Tech Only (36 Tickers)
| Metric | Expected |
|--------|----------|
| Win Rate | 70-74% |
| Trades/Month | 11-21 |
| Monthly Return | 2-4% |
| Confidence | HIGH |

### Tier 2 - Full Universe (401 Tickers)
| Metric | Expected |
|--------|----------|
| Win Rate | 60-68% |
| Trades/Month | 75-125 |
| Monthly Return | 3-6% |
| Confidence | MEDIUM |

---

## Implementation Checklist for JT

### Immediate (Week 1)
- [ ] Classify 14 new US stocks (Tech/Financial/Auto)
- [ ] Deploy on Tech-only universe (36 tickers)
- [ ] Start paper trading

### Short-term (Month 1)
- [ ] Monitor win rates on Tech universe
- [ ] Gradually add Equity tickers
- [ ] Test sector-specific performance

### Long-term (Month 2-3)
- [ ] Expand to full 401 tickers
- [ ] Implement tiered position sizing
- [ ] Build sector-specific strategies

---

## Files for JT

1. `inside_day_breakout_deployment.md` - Full spec (74.4% win on Tech)
2. `volume_breakout_deployment.md` - Full spec (70.8% win on Tech)
3. `rsi_mean_reversion_deployment.md` - Full spec (72.6% win on Tech)
4. `INDEX.md` - This file

---

## Key Documents

- `UNIVERSE_EXPANSION_PROPOSAL.md` - Expansion plan
- `FULL_UNIVERSE_TEST_RESULTS.md` - 401 ticker test results
- `DATA_VERIFICATION_REPORT.md` - Data availability confirmed

---

*Updated: 2026-02-22*  
*Platform: 401 Active Tickers*  
*Golden Strategies: 3*  
*Status: Ready for Tiered Deployment*