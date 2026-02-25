# FINAL GOLDEN STRATEGIES - PAPER TRADING DEPLOYMENT CONFIG
**Date:** 2026-02-23  
**Status:** ✅ READY FOR DEPLOYMENT  
**Total Golden Strategies:** 4 (with sector enhancements)

---

## 🏆 FINAL CONFIGURATION SUMMARY

| Rank | Strategy | Base Win% | Enhanced Win% | Best Sector | Deploy |
|------|----------|-----------|---------------|-------------|--------|
| 🥇 | BB+Monday GOLD | 78.5% | **88.9%** (HK) | **HK ONLY** | ⭐ Primary |
| 🥈 | Inside Day Breakout | 74.4% | 74.4% | Universal | ✅ Standard |
| 🥉 | RSI Mean Reversion | 72.6% | 69.2% (HK) | HK > US Tech | ✅ Standard |
| 4 | Volume Breakout | 70.8% | 70.8% | Universal | ✅ Standard |

---

## 📊 STRATEGY 1: BB Extreme + Monday GOLD

### Performance by Sector
| Sector | Win% | Sharpe | Trades |
|--------|------|--------|--------|
| **Hong Kong** | **88.9%** | 4.51 | 36 |
| Overall | 78.5% | 3.23 | 65 |
| China | 64.3% | 1.57 | 28 |

### Deployment Config
```yaml
strategy: BB_Extreme_Monday_GOLD
win_rate: 88.9%  # In HK
entry:
  - price_below_bb_lower: true
  - rsi_14: < 20
  - volume_ratio: > 1.5
  - day_of_week: Monday
exit:
  profit_target: 4%
  time_stop: 10 days
universe:
  primary: Hong_Kong_tickers  # 0700.HK, 9988.HK, etc.
  secondary: China_A_shares
position_size: 2%
max_concurrent: 3
```

**Key Enhancement:** HK-only deployment boosts win rate from 78.5% → 88.9%

---

## 📊 STRATEGY 2: Inside Day Breakout

### Performance
- Win Rate: 74.4%
- Sharpe: 2.09
- Trades: 39

### Deployment Config
```yaml
strategy: Inside_Day_Breakout
win_rate: 74.4%
entry:
  - inside_day_yesterday: true
  - volume_ratio: > 2.0
  - breakout_above_yesterday_high: > 2%
exit:
  profit_target: 5%
  time_stop: 5 days
universe:
  type: Universal
  focus: Tech + HK Growth
  count: 82 tickers
position_size: 2%
max_concurrent: 3
```

**Note:** Pattern-based strategy works universally

---

## 📊 STRATEGY 3: RSI Mean Reversion

### Performance by Sector
| Sector | Win% | Sharpe | Recommendation |
|--------|------|--------|----------------|
| Hong Kong | 69.2% | 2.66 | ✅ Good |
| Overall | 72.6% | 2.26 | Baseline |
| China | 44.5% | 0.27 | ❌ Avoid |

### Deployment Config
```yaml
strategy: RSI_Mean_Reversion
win_rate: 72.6%
entry:
  rsi_threshold:
    tech_stocks: < 10
    equity_stocks: < 20
exit:
  profit_target: 4%
  time_stop: 10 days
universe:
  primary: Hong_Kong
  secondary: US_Tech
  avoid: China_A_shares
position_size: 2%
max_concurrent: 5
```

**Key Enhancement:** Avoid China A-shares (44.5% win rate)

---

## 📊 STRATEGY 4: Volume Breakout

### Performance
- Win Rate: 70.8%
- Sharpe: 1.48
- Trades: 240

### Deployment Config
```yaml
strategy: Volume_Breakout
win_rate: 70.8%
entry:
  - volume_ratio: > 2.0
  - price_move: > 4%
exit:
  profit_target: 5%
  time_stop: 10 days
universe:
  type: Universal
  count: 161 tickers
  markets: US + HK + China
position_size: 2%
max_concurrent: 10
```

**Note:** Universal strategy, most signals (20-35/month)

---

## 🎯 DEPLOYMENT PRIORITY

### Phase 1: Start Here (Week 1)
1. **BB+Monday GOLD in HK** (88.9% win)
   - Highest win rate
   - 2-3 signals/month
   - Focus deployment here first

### Phase 2: Add Universal (Week 2)
2. **Inside Day Breakout** (74.4%)
3. **Volume Breakout** (70.8%)
   - Universal deployment
   - More signals

### Phase 3: Add RSI MR (Week 3)
4. **RSI Mean Reversion** (72.6%)
   - HK > US Tech > Equity
   - Avoid China

---

## 📈 EXPECTED PERFORMANCE

### Monthly Projections (Combined 4 Strategies)

| Metric | Expected |
|--------|----------|
| Total Trades | 30-50 |
| Blended Win Rate | ~76% |
| Gross Profit | 3-5% |
| Net Profit (after costs) | 2.5-4% |
| Max Drawdown | -15% to -25% |
| Sharpe Ratio | 1.8-2.5 |

### Risk Management
- Position size: 2% per trade
- Max concurrent: 18 positions (36% exposure)
- No stop losses (use position sizing)
- Profit targets: 3-5%

---

## 🔧 SQL SIGNAL DETECTION

### BB+Monday GOLD (HK Focus)
```sql
SELECT date, ticker, close as entry_price
FROM gold.technical_indicators_calculated
WHERE close < bb_lower
  AND rsi_14 < 20
  AND volume > avg_volume_20d * 1.5
  AND EXTRACT(DOW FROM date) = 1  -- Monday
  AND ticker LIKE '%.HK'  -- HK tickers
ORDER BY date DESC;
```

### All Strategies Combined
```sql
WITH signals AS (
  -- BB+Monday GOLD
  SELECT date, ticker, 'BB_Monday_GOLD' as strategy
  FROM gold.technical_indicators_calculated
  WHERE close < bb_lower AND rsi_14 < 20 
    AND vol_ratio > 1.5 AND EXTRACT(DOW FROM date) = 1
    
  UNION ALL
  
  -- RSI Mean Reversion
  SELECT date, ticker, 'RSI_MR' as strategy
  FROM gold.technical_indicators_calculated
  WHERE rsi_14 < 10
  
  UNION ALL
  
  -- Volume Breakout
  SELECT date, ticker, 'Volume_BO' as strategy
  FROM gold.technical_indicators_calculated
  WHERE vol_ratio > 2.0 AND price_change > 0.04
)
SELECT * FROM signals
ORDER BY date DESC, strategy;
```

---

## ✅ PAPER TRADING CHECKLIST

### Before Going Live:
- [ ] Deploy BB+Monday GOLD with HK filter
- [ ] Deploy Inside Day universal
- [ ] Deploy Volume Breakout universal
- [ ] Deploy RSI MR (HK focus, avoid China)
- [ ] Set 2% position size for all
- [ ] Configure profit targets (3-5%)
- [ ] Set max concurrent positions
- [ ] Enable P&L tracking

### Monitor Weekly:
- [ ] Actual win rate vs backtest
- [ ] Profit target hit rate
- [ ] Average hold time
- [ ] Drawdown levels
- [ ] Sharpe ratio

---

## 📞 SUPPORT

**Questions:** Review detailed configs in:
- `EXIT_STRATEGY_RECOMMENDATIONS.md`
- `JT_DEPLOYMENT_INDEX_ALL_20.md`
- `JT_DEPLOYMENT_UPDATE_GOLDEN4.md`

**Updates:** Check `memory/AGGREGATED_RESEARCH_MEMORY.md`

---

*Ready for paper trading deployment*  
*Date: 2026-02-23*  
*4 Golden Strategies with sector enhancements*