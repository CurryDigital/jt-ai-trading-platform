# MASTER DEPLOYMENT PACKAGE

**Date:** 2026-02-19  
**Status:** READY FOR IMMEDIATE DEPLOYMENT  
**Strategies:** 3 (AH Premium, SG REIT, RSI Mean Reversion)

---

## Executive Summary

| Strategy | Market | Win Rate | Sharpe | Allocation | Status |
|----------|--------|----------|--------|------------|--------|
| **AH Premium Arbitrage** | HK/CN | 72% | 2.33 | 10-15% | ✅ Deploy |
| **SG REIT Dividend** | SG | 73% | 0.73 | 5-10% | ✅ Deploy |
| **RSI Mean Reversion** | Universal | 60-63% | 1.2 | 20-40% | ✅ Deploy |

**Total Recommended Allocation:** 35-65% of portfolio

---

## Quick Deploy Commands

### 1. AH Premium Arbitrage
```python
# Deploy top 5 pairs
pairs = ['1398.HK', '0939.HK', '3988.HK', '1288.HK', '0998.HK']
sizing = 2.5% each
entry = premium > 30% AND premium > 1.2x historical avg
exit = 20 days OR premium < 25%
```

### 2. SG REIT Dividend
```python
# Deploy quarterly (simplified: EWS only)
ticker = 'EWS'
sizing = 5-10%
schedule = ['Jan 1-14', 'Apr 1-14', 'Jul 1-14', 'Oct 1-14']
exit = 21 days after month start
```

### 3. RSI Mean Reversion
```python
# Deploy across 4 markets
top_tickers = {
    'US': ['NVDA', 'GOOGL', 'AAPL'],
    'HK': ['0700.HK', '1299.HK'],
    'CN': ['PDD', 'JD'],
    'SG': ['Z74.SI', 'D05.SI']
}
sizing = 2% per ticker
entry = RSI(14) < 30 AND volume > 1.3x avg
exit = RSI > 50 OR 5 days
```

---

## Risk Summary

| Strategy | Max Drawdown | Correlation to SPY | Best Environment |
|----------|--------------|-------------------|------------------|
| AH Premium | -15% | 0.4 | China stability, rate cuts |
| SG REIT | -10% | 0.6 | Low rates, stable SGD |
| RSI Mean Reversion | -12% | 0.8 | Range-bound markets |

**Combined Portfolio:**
- Expected Sharpe: 1.0-1.3
- Max DD: -15-20%
- Annual Return: 15-25%

---

## Implementation Checklist

### Prerequisites
- [ ] IBKR account with US/HK/SG exchange access
- [ ] A-share price feed for AH premium calc
- [ ] Real-time RSI calculation capability
- [ ] Dividend calendar for S-REITs

### Deployment Steps
1. **Week 1:** Deploy RSI Mean Reversion (most liquid, easiest)
2. **Week 2:** Add AH Premium Arbitrage (need FX rates)
3. **Week 3:** Add SG REIT (wait for next quarter entry)

### Monitoring
- Daily: RSI signals, AH premium levels
- Weekly: Position review
- Quarterly: REIT dividend entries

---

## Files Included

1. `deployment/ah_premium_deployment.md` - Full AH premium specs
2. `deployment/sg_reit_deployment.md` - Full S-REIT specs
3. `deployment/rsi_mean_reversion_deployment.md` - Full RSI specs
4. `results/ah_premium_backtest.csv` - Backtest data
5. `results/sg_reit_dividend_backtest.csv` - Backtest data
6. `results/strategy_region_definitions.json` - All 17 combos

---

**Ready for JT Platform Integration**
**Contact:** Trade Algo Researcher
**Date:** 2026-02-19
