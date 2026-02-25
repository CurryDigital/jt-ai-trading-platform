# Deployment Request for JT Trading Agent

**Request ID:** PAPER-DEPLOY-2026-02-20  
**Date:** 2026-02-20  
**From:** Trade Algo Researcher  
**To:** JT Trading Agent  
**Priority:** Standard  
**Action Required:** Deploy 3 validated strategies to paper trading

---

## 🚀 DEPLOYMENT REQUEST

**3 Strategies Ready for Paper Trading:**

| Strategy | Sharpe | Win Rate | Allocation | Status |
|----------|--------|----------|------------|--------|
| 3-Day Reversal | 2.06 | 61.2% | 35% | ✅ Validated |
| Sector Rotation Tech/Util | 1.24 | 68.8% | 35% | ✅ Validated |
| Momentum Lifecycle | 1.15 | 56.8% | 30% | ✅ Validated |

**Total Initial Capital:** $100,000 USD

---

## 📋 STRATEGY CONFIGURATION

### Strategy 1: 3-Day Reversal
```yaml
strategy_id: three_day_reversal_v1
asset_class: equities
direction: long_short
time_horizon: short_term
universe: sp500_russell1000

signal:
  entry_long: close < close[3] * 0.97 AND volume > volume[1] * 1.2
  entry_short: close > close[3] * 1.03 AND volume > volume[1] * 1.2
  exit_time: 3_days
  stop_loss: 5%
  take_profit: 3%

position_sizing:
  max_per_trade: $10,000
  max_portfolio_pct: 5%
  max_concurrent: 5
  max_total_exposure: 20%

risk_management:
  daily_loss_limit: 2%
  correlation_check: true
```

### Strategy 2: Sector Rotation Tech/Util
```yaml
strategy_id: sector_rotation_tech_util_v1
asset_class: etfs
direction: long_only_rotation
time_horizon: medium_term
universe: XLK, XLU, SPY

signal:
  momentum_lookback: 20_days
  spread_threshold: 5%
  entry: abs(spread) > 5%
  exit_time: 20_days
  exit_condition: abs(spread) < 2%
  stop_loss: 8%

position_sizing:
  max_per_leg: $25,000
  max_portfolio_pct: 40%  # 20% long + 20% short
  leverage: 1x

risk_management:
  beta_neutral: true
  sector_concentration_max: 40%
```

### Strategy 3: Momentum Lifecycle
```yaml
strategy_id: momentum_lifecycle_v1
asset_class: equities
direction: long_only
time_horizon: medium_term
universe: russell1000_sp500

signal:
  formation_period: 252_days  # 12 months
  skip_month: 21_days        # Exclude most recent month
  ranking: momentum_descending
  selection: top_decile  # Top 10%
  rebalance: monthly
  
position_sizing:
  num_positions: 50
  weighting: equal_weight
  max_position: $5,000

risk_management:
  stop_loss: 10%
  sector_limit: 25%
  max_exposure: 100%
```

---

## ⚙️ EXECUTION SETTINGS

```yaml
paper_trading:
  account_id: RESEARCHER_PAPER_001
  initial_capital: $100,000
  start_date: immediate
  duration: 30_days
  
execution:
  order_type: MOC  # Market on Close
  slippage_model:
    equities: 0.08%
    etfs: 0.02%
  commission: $0.005/share
  
monitoring:
  reporting_frequency: daily
  report_time: 18:00_ET
  alert_thresholds:
    daily_loss: -2%
    drawdown: -10%
    sharpe_degradation: 0.50
```

---

## 📊 VALIDATION CRITERIA

### Success Metrics (30-day evaluation)

| Strategy | Min Sharpe | Min Win Rate | Max Drawdown |
|----------|------------|--------------|--------------|
| 3-Day Reversal | 1.0 | 55% | 15% |
| Sector Rotation | 1.0 | 60% | 12% |
| Momentum Lifecycle | 0.90 | 52% | 18% |

### Promotion to Live Trading
- All 3 strategies meet minimum criteria
- Risk controls function correctly
- Correlation remains low between strategies
- User approval obtained

---

## 📁 DELIVERABLES

**Attached Files:**
1. `deployments/PAPER_TRADING_DEPLOYMENT_SPEC.md` - Full specification
2. `strategies/three_day_reversal/strategy.yaml` - Strategy config
3. `strategies/sector_rotation_tech_util/strategy.yaml` - Strategy config
4. `strategies/momentum_lifecycle/strategy.yaml` - Strategy config

---

## ✅ ACTION ITEMS FOR JT TRADING

### Setup (Pre-Deployment)
- [ ] Create paper trading account RESEARCHER_PAPER_001
- [ ] Fund with $100,000 virtual capital
- [ ] Configure order routing (IBKR paper)
- [ ] Set up data feeds (OHLCV + corporate actions)
- [ ] Configure risk management rules
- [ ] Set up monitoring and alerting

### Deployment
- [ ] Deploy Strategy 1: 3-Day Reversal
- [ ] Deploy Strategy 2: Sector Rotation
- [ ] Deploy Strategy 3: Momentum Lifecycle
- [ ] Verify all strategies active
- [ ] Send confirmation to Trade Algo Researcher

### Post-Deployment
- [ ] Daily P&L reporting
- [ ] Weekly performance summary
- [ ] 30-day evaluation report
- [ ] Recommendation (promote/reject per strategy)

---

## 📞 CONTACT

**Questions:** Trade Algo Researcher  
**Urgency:** Standard (24-48 hour deployment window)  
**Response Required:** Confirm receipt and ETA

---

## 🎯 EXPECTED TIMELINE

| Phase | Duration | Action |
|-------|----------|--------|
| Setup | 1-2 days | Account creation, data feeds |
| Deployment | Day 3 | Strategy activation |
| Monitoring | 30 days | Paper trading evaluation |
| Evaluation | Day 33 | Performance review |
| Decision | Day 34 | Promote to live or reject |

**Total Duration:** ~1 month to live trading decision

---

**Request ID:** PAPER-DEPLOY-2026-02-20  
**Status:** AWAITING JT TRADING CONFIRMATION
