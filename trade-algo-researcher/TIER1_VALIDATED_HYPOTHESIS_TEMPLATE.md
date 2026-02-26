# Tier 1: Validated Hypothesis Template

Use this template when promoting an idea to a Validated Hypothesis.

## File Structure

```
/hypotheses/validated/H{XXX}_{hypothesis_name}/
├── hypothesis.yaml          # REQUIRED: Machine-readable spec
├── test_results.json        # REQUIRED: Full backtest metrics
├── backtest_summary.md      # REQUIRED: Human-readable summary
└── README.md                # REQUIRED: Thesis + logic
```

---

## hypothesis.yaml

```yaml
name: "Descriptive Hypothesis Name"
version: "1.0"
tier: "validated_hypothesis"
hypothesis_id: "H001"           # Auto-assigned

# --- PROMOTION CRITERIA ---
# ALL of these must be met to qualify as Validated Hypothesis
status: "validated_hypothesis"  # idea → testing → validated_hypothesis
validated_date: "2026-02-26"

# Performance Metrics (REQUIRED)
win_rate: 0.55                  # ≥ 50%
sharpe_ratio: 0.95              # ≥ 0.8
total_trades: 156               # ≥ 100
max_drawdown: 0.18              # Documented, no hard limit but be honest

# 2-Tier Validation (REQUIRED)
train_period: "2021-01-01 to 2022-12-31"
test_period: "2023-01-01 to 2024-12-31"
train_metrics:
  win_rate: 0.57
  sharpe: 1.02
  trades: 89
test_metrics:
  win_rate: 0.52
  sharpe: 0.88
  trades: 67
  decay_vs_train: 0.14          # < 30%

# Universe Coverage (REQUIRED)
universe:
  total_tested: 412             # Full universe count
  valid_signals: 89             # Tickers with sufficient signals
  coverage_pct: 21.6            # valid_signals / total_tested

# --- HYPOTHESIS LOGIC ---
asset_class: "equities"         # equities | fx | crypto | commodities
direction: "long"               # long | short | neutral
horizon: "short_term"           # intraday | short_term | medium_term

# Signal Definition (REQUIRED)
signal:
  setup: "3 consecutive down days"           # What setup are you looking for?
  confirmation: "RSI < 20"                   # What confirms the setup?
  entry_trigger: "Volume > 2x average"       # What triggers entry?
  exit_logic: "RSI > 50 OR 5 days elapsed"   # When do you exit?

# Economic Rationale (REQUIRED - Why does this work?)
thesis: |
  Mean reversion after overextension. When a stock drops 3+ days 
  consecutively with RSI hitting extreme oversold (<20), short-term 
  selling exhaustion creates a bounce opportunity. Volume confirmation 
  (>2x) indicates capitulation/panic selling, which typically marks 
  local bottoms.

edge_persistence: |
  Behavioral bias: Retail panic selling creates dislocations. 
  Institutional rebalancing provides mean-reverting pressure. 
  Edge persists because human fear/greed cycles are stable.

# --- TESTING NOTES ---
test_parameters:
  entry_threshold: 20           # RSI threshold
  volume_multiplier: 2.0        # Volume confirmation level
  max_hold_days: 5              # Time stop
  profit_target_pct: null       # Null = none, or specify
  stop_loss_pct: null           # Null = none, or specify

transaction_costs: 0.0005       # 0.05% per side (REQUIRED)

# --- LIMITATIONS ---
limitations:
  - "Does not work in bear markets (2022 test period lower performance)"
  - "Requires high volume confirmation - misses some valid setups"
  - "Holding period may be too short for full mean reversion"

# --- NEXT STEPS ---
promotion_path: "near_golden"   # Target next tier
enhancement_ideas:
  - "Add volatility filter (ATR-based)"
  - "Test sector-specific thresholds"
  - "Try profit target vs time stop comparison"
  - "Combine with volume profile analysis"

# Metadata
author: "Trade Algo Researcher"
created: "2026-02-20"
validated: "2026-02-26"
qa_verified: false              # Set true after QA approval
```

---

## test_results.json

```json
{
  "hypothesis_id": "H001",
  "name": "3-Day Down + RSI Extreme Mean Reversion",
  "validation_date": "2026-02-26",
  "tier": "validated_hypothesis",
  
  "overall_metrics": {
    "total_trades": 156,
    "winning_trades": 86,
    "losing_trades": 70,
    "win_rate": 0.5513,
    "avg_winner_pct": 0.042,
    "avg_loser_pct": -0.031,
    "profit_factor": 1.38,
    "sharpe_ratio": 0.95,
    "max_drawdown": 0.18,
    "max_drawdown_pct": 18.0,
    "total_return_pct": 12.4
  },
  
  "train_period": {
    "start": "2021-01-01",
    "end": "2022-12-31",
    "trades": 89,
    "win_rate": 0.5730,
    "sharpe": 1.02,
    "max_dd": 0.15
  },
  
  "test_period": {
    "start": "2023-01-01",
    "end": "2024-12-31",
    "trades": 67,
    "win_rate": 0.5224,
    "sharpe": 0.88,
    "max_dd": 0.18,
    "decay_vs_train": 0.1373
  },
  
  "universe_coverage": {
    "total_tested": 412,
    "valid_signals": 89,
    "coverage_pct": 21.6,
    "by_sector": {
      "technology": {"signals": 23, "win_rate": 0.52},
      "healthcare": {"signals": 15, "win_rate": 0.60},
      "financials": {"signals": 18, "win_rate": 0.56}
    }
  },
  
  "monthly_returns": [
    {"month": "2021-01", "return_pct": 1.2, "trades": 4},
    {"month": "2021-02", "return_pct": -0.8, "trades": 3}
  ],
  
  "parameters": {
    "entry_threshold": 20,
    "volume_multiplier": 2.0,
    "max_hold_days": 5,
    "transaction_costs": 0.0005
  }
}
```

---

## backtest_summary.md

```markdown
# Backtest Summary: 3-Day Down + RSI Extreme Mean Reversion

## Hypothesis
Mean reversion after 3+ consecutive down days with RSI < 20 and 
volume confirmation > 2x average.

## Test Periods
- **Train:** 2021-01-01 to 2022-12-31 (Bear/Bull transition)
- **Test:** 2023-01-01 to 2024-12-31 (Bull market)

## Key Results

| Metric | Train | Test | Overall |
|--------|-------|------|---------|
| Win Rate | 57.3% | 52.2% | 55.1% |
| Sharpe | 1.02 | 0.88 | 0.95 |
| Max DD | 15% | 18% | 18% |
| Trades | 89 | 67 | 156 |

## Decay Analysis
- Train → Test decay: 13.7% (ACCEPTABLE, <30%)
- Performance held up in different market regimes

## Universe Coverage
- Tested on: 412 tickers
- Valid signals: 89 tickers (21.6% coverage)
- Best performing sector: Healthcare (60% win rate)

## Limitations
1. Lower performance in sustained bear markets
2. Requires high volume - misses some valid setups
3. Time stop may exit before full mean reversion

## Conclusion
✅ **VALIDATED HYPOTHESIS** - Meets Tier 1 criteria.
Win rate 55.1% (≥50%), Sharpe 0.95 (≥0.8), decay 13.7% (<30%).

## Next Steps
Enhance to reach Near-Golden tier (60%+ win rate, 1.2+ Sharpe):
- Add ATR volatility filter
- Test profit targets vs time stops
- Sector-specific parameter tuning
```

---

## README.md

```markdown
# H001: 3-Day Down + RSI Extreme Mean Reversion

## Thesis
When stocks experience 3+ consecutive down days with RSI hitting 
extreme oversold levels (<20) on volume spikes (>2x), it signals 
capitulation selling. This creates a mean-reversion opportunity as 
short-term selling exhausts itself.

## Why This Edge Exists
1. **Behavioral Bias:** Retail investors panic sell at extremes
2. **Institutional Rebalancing:** Creates natural buying pressure
3. **Short Covering:** Oversold conditions trigger short covering

## Signal Logic

### Entry
```
IF consecutive_down_days >= 3 
   AND RSI(14) < 20 
   AND Volume > 2 * Avg_Volume(20):
    ENTER LONG
```

### Exit
```
IF RSI(14) > 50 
   OR hold_days >= 5:
    EXIT
```

## Performance
- Win Rate: 55.1%
- Sharpe Ratio: 0.95
- Max Drawdown: 18%
- Total Trades: 156

## Validation
- ✅ Tested on 412 tickers (full universe)
- ✅ Train/Test split with time-ordering
- ✅ Transaction costs included (0.05% per side)
- ✅ Decay 13.7% (<30% threshold)

## Risks & Limitations
- Underperforms in sustained bear markets
- Requires high volume confirmation
- May exit before full mean reversion

## Researcher Notes
Initial test on tech stocks only showed 48% win rate. Expanding 
to full universe improved to 55% due to healthcare/financials 
performance. Consider sector-specific thresholds for enhancement.

---
*Validated: 2026-02-26 | Researcher: Trade Algo Researcher*
```

---

## QA Verification Checklist

Before submitting for QA verification, ensure:

- [ ] hypothesis.yaml is valid YAML
- [ ] All REQUIRED fields are populated
- [ ] test_results.json matches hypothesis.yaml metrics
- [ ] Train/Test periods don't overlap
- [ ] Decay calculation is correct
- [ ] Universe coverage >= 400 tickers tested
- [ ] Transaction costs included in backtest
- [ ] README.md explains the thesis clearly
- [ ] Limitations are honestly documented
- [ ] Enhancement ideas are listed

---

*Template Version: 2026-02-26*
