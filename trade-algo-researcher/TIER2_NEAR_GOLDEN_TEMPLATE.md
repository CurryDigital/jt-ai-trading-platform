# Tier 2: Near-Golden Strategy Template

**Promotion Criteria:** Win ≥ 55%, PF ≥ 1.5, Sharpe ≥ 1.2, DD < 20%, N ≥ 300

## File Structure

```
/strategies/near_golden/{name}/
├── strategy.yaml           # Full spec
├── strategy_spec.md        # Thesis + rules
├── backtest_report.json    # Detailed metrics
├── equity_curve.png        # Visual proof
├── stress_test_results.md  # Crisis performance
└── enhancement_roadmap.md  # Path to Golden
```

---

## strategy.yaml

```yaml
name: "Enhanced RSI Mean Reversion"
version: "2.0"
tier: "near_golden"
status: "near_golden"

promotion_history:
  - date: "2026-02-10"
    from: "idea"
    to: "validated_hypothesis"
  - date: "2026-02-26"
    from: "validated_hypothesis"
    to: "near_golden"

# Performance
win_rate: 0.64
profit_factor: 1.72
sharpe_ratio: 1.35
max_drawdown: 0.14
total_trades: 423
avg_hold_days: 4.2

# 3-Tier Validation
backtest_period: "2019-01-01 to 2024-12-31"
oos_period: "2023-01-01 to 2024-12-31"

train_metrics:
  period: "2019-2021"
  trades: 198
  win_rate: 0.66
  sharpe: 1.42
  max_dd: 0.12

test_metrics:
  period: "2022-2023"
  trades: 145
  win_rate: 0.63
  sharpe: 1.28
  max_dd: 0.15
  decay_vs_train: 0.0986

oos_metrics:
  period: "2024"
  trades: 80
  win_rate: 0.62
  sharpe: 1.31
  max_dd: 0.14
  decay_vs_test: 0.0234

# Universe
universe:
  asset_class: "equities"
  total_tested: 412
  valid_signals: 156
  coverage_pct: 37.9

# Logic
signals:
  frequency: "daily"
  entry_logic: "3 down days + RSI<15 + Volume>2.5x + ATR<5%"
  exit_logic: "RSI>50 OR hold_days>=7 OR stop_loss_5%"

# Risk
risk:
  stop_loss_pct: 0.05
  position_sizing: "fixed_risk"
  max_position_pct: 0.04
  max_sector_pct: 0.15

# Execution
execution:
  venue: "IBKR"
  slippage: 0.001
  transaction_costs: 0.0005

# Path to Golden
golden_gap_analysis:
  current_win_rate: 0.64
  target_win_rate: 0.70  # Path A
  gap: 0.06
  
  current_profit_factor: 1.72
  target_profit_factor: 1.8  # Path B
  gap: 0.08

planned_enhancements:
  - priority: 1
    idea: "Sector-specific RSI thresholds"
    expected_impact: "+2-3% win rate"
    
  - priority: 2
    idea: "Momentum filter for tech"
    expected_impact: "+1-2% win rate"

estimated_promotion_date: "2026-03-15"

author: "Trade Algo Researcher"
created: "2026-02-20"
```

---

## strategy_spec.md

```markdown
# Near-Golden Strategy: [Name]

## Status
**Tier:** Near-Golden  
**Target:** Golden (Path A: 70%+ win rate OR Path B: 1.8+ PF)

## Performance

| Metric | Target | Current | Gap |
|--------|--------|---------|-----|
| Win Rate | 70% | 64% | -6% |
| Profit Factor | 1.8 | 1.72 | -0.08 |
| Sharpe | 1.5 | 1.35 | -0.15 |
| Max DD | <15% | 14% | ✅ |

## 3-Tier Validation

| Period | Trades | Win Rate | Sharpe | Decay |
|--------|--------|----------|--------|-------|
| Train | 198 | 66% | 1.42 | — |
| Test | 145 | 63% | 1.28 | 9.9% |
| OOS | 80 | 62% | 1.31 | 2.3% |

## Thesis
[Clear explanation of why this edge exists]

## Entry/Exit Rules

### Entry
- 3+ consecutive down days
- RSI(14) < 15
- Volume > 2.5x 20-day average
- ATR(14) < 5% of price

### Exit
- RSI > 50 (target)
- Hold days >= 7 (time stop)
- Price < entry * 0.95 (stop loss)

## Risk Management
- Max position: 4%
- Stop loss: 5%
- Max sector: 15%

## Path to Golden

### Blockers
1. Win rate 64% < 70% (Path A)
2. Profit factor 1.72 < 1.8 (Path B)

### Planned Enhancements
1. **Sector-specific thresholds** → +2-3% win rate
2. **Momentum filter** → +1-2% win rate
3. **Profit target optimization** → +0.15 Sharpe

**Timeline:** Target Golden by 2026-03-15
```

---

## enhancement_roadmap.md

```markdown
# Enhancement Roadmap: [Strategy Name]

## Current Status
- Win Rate: 64% (Target: 70% for Path A)
- Profit Factor: 1.72 (Target: 1.8 for Path B)
- Sharpe: 1.35 (Target: 1.5)
- Trades: 423 (Target: 500)

## Goal
Reach Golden tier via Path A (high win rate) OR Path B (high PF)

## Phase 1: Sector Optimization
**Expected:** +2-3% win rate

| Sector | Current RSI | Proposed |
|--------|-------------|----------|
| Technology | < 15 | < 12 |
| Healthcare | < 15 | < 18 |
| Financials | < 15 | < 16 |

**Success Criteria:** Win rate ≥ 66%

## Phase 2: Momentum Filter
**Expected:** +1-2% win rate

Require price > 50d MA for tech stocks to avoid falling knives.

**Success Criteria:** Win rate ≥ 68%

## Phase 3: Profit Target Testing
**Expected:** +0.15 Sharpe

Test fixed profit target vs trailing stop vs current RSI exit.

## Exit Criteria (Golden)

Meet ANY path:
- [ ] Path A: Win ≥ 70%, PF ≥ 1.5, Sharpe ≥ 1.5, DD < 15%
- [ ] Path B: Win ≥ 40%, PF ≥ 1.8, Sharpe ≥ 1.5, DD < 15%
- [ ] Path C: Win ≥ 35%, PF ≥ 1.5, Sharpe ≥ 2.0, DD < 12%
- [ ] Path D: Win ≥ 50%, PF ≥ 1.6, Sharpe ≥ 1.5, DD < 10%

All paths require:
- [ ] Trades ≥ 500
- [ ] Decay < 20%
- [ ] Stress tests pass
```

---

*Template Version: 2026-02-26*
