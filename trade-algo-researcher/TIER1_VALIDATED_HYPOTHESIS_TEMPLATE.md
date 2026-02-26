# Tier 1: Validated Hypothesis Template

**Promotion Criteria:** Win ≥ 50%, PF ≥ 1.3, Sharpe ≥ 0.8, DD < 25%, N ≥ 100

## File Structure

```
/hypotheses/validated/H{XXX}_{name}/
├── hypothesis.yaml       # Core spec
├── test_results.json     # Metrics
├── backtest_summary.md   # Human-readable
└── README.md             # Thesis
```

---

## hypothesis.yaml

```yaml
name: "Descriptive Hypothesis Name"
hypothesis_id: "H001"
tier: "validated_hypothesis"
status: "validated_hypothesis"
validated_date: "2026-02-26"

# Performance Metrics
win_rate: 0.55
profit_factor: 1.38
sharpe_ratio: 0.95
max_drawdown: 0.18
total_trades: 156

# 2-Tier Validation
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
  decay_vs_train: 0.14

# Universe
universe:
  total_tested: 412
  valid_signals: 89
  coverage_pct: 21.6

# Logic
asset_class: "equities"
direction: "long"
horizon: "short_term"

signal:
  setup: "3 consecutive down days"
  confirmation: "RSI < 20"
  entry_trigger: "Volume > 2x average"
  exit_logic: "RSI > 50 OR 5 days elapsed"

thesis: |
  Mean reversion after overextension. When a stock drops 3+ days 
  consecutively with RSI hitting extreme oversold (<20), short-term 
  selling exhaustion creates a bounce opportunity.

# Testing Notes
transaction_costs: 0.0005

limitations:
  - "Does not work in bear markets"
  - "Requires high volume confirmation"

# Next Steps
promotion_path: "near_golden"
enhancement_ideas:
  - "Add volatility filter (ATR-based)"
  - "Test sector-specific thresholds"

author: "Trade Algo Researcher"
created: "2026-02-20"
validated: "2026-02-26"
qa_verified: false
```

---

## test_results.json

```json
{
  "hypothesis_id": "H001",
  "tier": "validated_hypothesis",
  "overall_metrics": {
    "total_trades": 156,
    "win_rate": 0.5513,
    "profit_factor": 1.38,
    "sharpe_ratio": 0.95,
    "max_drawdown": 0.18
  },
  "train_metrics": {
    "trades": 89,
    "win_rate": 0.5730,
    "sharpe": 1.02
  },
  "test_metrics": {
    "trades": 67,
    "win_rate": 0.5224,
    "sharpe": 0.88,
    "decay_vs_train": 0.1373
  },
  "universe_coverage": {
    "total_tested": 412,
    "valid_signals": 89
  }
}
```

---

## backtest_summary.md

```markdown
# Backtest Summary: [Name]

## Hypothesis
[1-2 sentence description of the edge]

## Test Periods
- Train: 2021-01-01 to 2022-12-31
- Test: 2023-01-01 to 2024-12-31

## Results

| Metric | Train | Test | Overall |
|--------|-------|------|---------|
| Win Rate | 57.3% | 52.2% | 55.1% |
| Profit Factor | 1.45 | 1.28 | 1.38 |
| Sharpe | 1.02 | 0.88 | 0.95 |
| Max DD | 15% | 18% | 18% |
| Trades | 89 | 67 | 156 |

## Decay Analysis
- Train → Test decay: 13.7% (ACCEPTABLE)

## Universe Coverage
- Tested: 412 tickers
- Valid signals: 89 (21.6%)

## Conclusion
✅ VALIDATED HYPOTHESIS — Meets Tier 1 criteria.

## Next Steps
Enhance to reach Near-Golden tier:
- Add ATR volatility filter
- Test profit targets vs time stops
```

---

## README.md

```markdown
# H001: [Hypothesis Name]

## Thesis
[Why does this edge exist? Why will it persist?]

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
IF RSI(14) > 50 OR hold_days >= 5:
    EXIT
```

## Performance
- Win Rate: 55.1%
- Profit Factor: 1.38
- Sharpe Ratio: 0.95
- Max Drawdown: 18%

## Validation
- ✅ Tested on 412 tickers
- ✅ Time-ordered split
- ✅ Transaction costs included
- ✅ Decay 13.7% (< 30%)

## Limitations
- Underperforms in sustained bear markets
- Requires high volume confirmation

---
*Validated: 2026-02-26*
```

---

*Template Version: 2026-02-26*
