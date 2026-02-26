# Tier 3: Golden Strategy Template

**Promotion Criteria:** Meet ANY of 4 paths + stress tests + 35 QA checks

## File Structure

```
/strategies/golden/{name}/
├── strategy.yaml              # Machine-readable spec
├── strategy_spec.md           # Human-readable thesis
├── backtest_report.json       # Full metrics
├── equity_curve.png           # Visual proof
├── stress_test_results.md     # Crisis performance
├── oos_validation.json        # OOS results
├── academic_refs.md           # Research basis
└── .github/workflows/
    └── validate.yml           # CI enforcement
```

---

## strategy.yaml

```yaml
name: "ARASO Factor Model Enhanced"
version: "2.0"
tier: "golden"
status: "backtested"

# Golden Path (must meet ONE)
golden_path: "C"  # A, B, C, or D

# Path A: High Win Rate
# win_rate: 0.72, profit_factor: 1.85, sharpe: 1.8, max_dd: 0.12

# Path B: High Profit Factor
# win_rate: 0.45, profit_factor: 2.1, sharpe: 1.7, max_dd: 0.14

# Path C: Exceptional Sharpe (selected)
win_rate: 0.67
profit_factor: 2.1
sharpe_ratio: 2.4
max_drawdown: 0.095

# Path D: Low Risk
# win_rate: 0.58, profit_factor: 1.7, sharpe: 1.6, max_dd: 0.08

# Promotion History
tier_promotion_history:
  - date: "2026-02-10"
    from: "idea"
    to: "validated_hypothesis"
  - date: "2026-02-18"
    from: "validated_hypothesis"
    to: "near_golden"
  - date: "2026-02-26"
    from: "near_golden"
    to: "golden"
    qa_approved: true

# Statistical Significance
total_trades_backtest: 647
backtest_period: "2019-01-01 to 2024-12-31"
oos_period: "2023-01-01 to 2024-12-31"
oos_pct_of_total: 0.33

# 3-Tier Validation
train_metrics:
  period: "2019-2021"
  trades: 289
  win_rate: 0.69
  sharpe: 2.6
  max_dd: 0.08
  profit_factor: 1.95

test_metrics:
  period: "2022-2023"
  trades: 198
  win_rate: 0.65
  sharpe: 2.3
  max_dd: 0.11
  profit_factor: 1.82
  decay_vs_train: 0.1154

oos_metrics:
  period: "2024"
  trades: 160
  win_rate: 0.67
  sharpe: 2.4
  max_dd: 0.09
  profit_factor: 1.91
  decay_vs_test: 0.0435

# Stress Tests
stress_tests:
  covid_crash_2020:
    period: "2020-02-19 to 2020-03-23"
    sp500_return: -0.34
    strategy_return: 0.08
    max_dd: 0.06
    trades: 12
    win_rate: 0.75
    survived: true
    
  rate_hikes_2022:
    period: "2022-01-01 to 2022-10-12"
    sp500_return: -0.25
    strategy_return: -0.03
    max_dd: 0.09
    trades: 67
    win_rate: 0.61
    survived: true

stress_test_summary:
  total_crises: 2
  survived: 2
  avg_max_dd_during_crises: 0.075

# Strategy Logic
asset_class: "equities"
direction: "neutral"
horizon: "short_term"

universe:
  total_assets: 450
  selection_criteria: "Top 450 US equities by market cap"
  liquidity_threshold: "Avg daily volume > $5M"

signals:
  frequency: "daily"
  rebalance: "weekly"
  entry_logic: "|residual_zscore| > 1.5 AND hmm_p_mr > 0.7 AND ml_confidence > 0.6"
  exit_logic: "|residual_zscore| < 0.3 OR regime_change OR hold_days > 20"

# Risk Management
risk:
  position_sizing: "uncertainty_weighted"
  max_position_pct: 0.05
  max_sector_pct: 0.15
  beta_neutral: true
  beta_tolerance: 0.1
  stop_loss_sigma: 3.0
  max_hold_days: 20

# Execution
execution:
  venue: "IBKR"
  slippage: 0.001
  transaction_costs: 0.0005

# Implementation
capacity_millions: 100

# Academic Basis
jt_ready: true
golden_reasoning: |
  Meets Path C (Exceptional Sharpe): 2.4 Sharpe > 2.0 threshold.
  PCA residual capture + HMM regime detection + ML uncertainty weighting.
  Survived all stress tests with <10% DD.

academic_references:
  - "Uncertainty of ML Predictions in Asset Pricing (2025)"
  - "Kaufman Adaptive Moving Average Strategy (2025)"
  - "Interacting Anomalies (2024)"

# Deployment
deployment:
  mode: "paper"
  jt_integration: true
  paper_start_date: null
  live_start_date: null

# QA Verification
qa_verification:
  verified: true
  verified_date: "2026-02-26"
  verifier: "trade-algo-qa"
  sections_passed:
    performance_thresholds: true
    three_tier_validation: true
    stress_tests: true
    risk_management: true
    implementation: true
    documentation: true
    statistical_rigor: true
  total_checks: 35
  checks_passed: 35

author: "Trade Algo Researcher"
created: "2019-01-01"
golden_date: "2026-02-26"
```

---

## .github/workflows/validate.yml

```yaml
name: Validate Golden Strategy

on:
  push:
    paths:
      - 'strategies/golden/**/strategy.yaml'
  pull_request:
    paths:
      - 'strategies/golden/**'

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      
      - name: Install dependencies
        run: pip install pyyaml jsonschema
      
      - name: Check Golden Path
        run: |
          python scripts/validate_golden_path.py \
            --path-a "win>=0.70,pf>=1.5,sharpe>=1.5,dd<=0.15" \
            --path-b "win>=0.40,pf>=1.8,sharpe>=1.5,dd<=0.15" \
            --path-c "win>=0.35,pf>=1.5,sharpe>=2.0,dd<=0.12" \
            --path-d "win>=0.50,pf>=1.6,sharpe>=1.5,dd<=0.10" \
            --min-trades 500 \
            --max-decay 0.20
      
      - name: Verify Stress Tests
        run: |
          python scripts/validate_stress_tests.py \
            --required covid_2020 \
            --required rate_hikes_2022
      
      - name: Generate Report
        run: python scripts/generate_validation_report.py
```

---

## QA Verification Checklist (35 Checks)

### Section A: Performance (Meet ONE path + Common)
- [ ] Meets Path A, B, C, OR D
- [ ] Sample size ≥ 500
- [ ] OOS period ≥ 20%

### Section B: 3-Tier Validation
- [ ] Train period documented
- [ ] Test period documented
- [ ] OOS period documented
- [ ] Decay Train→Test < 20%
- [ ] Decay Test→OOS < 20%

### Section C: Stress Tests
- [ ] COVID 2020 survived (DD < 15%)
- [ ] Rate Hikes 2022 survived (DD < 15%)
- [ ] Trades during each crisis ≥ 20

### Section D: Risk Management
- [ ] Stop loss defined
- [ ] Position sizing documented
- [ ] Max position ≤ 5%
- [ ] Max sector ≤ 15%
- [ ] Beta neutral (if claimed)

### Section E: Implementation
- [ ] Transaction costs ≥ 0.05%
- [ ] Slippage documented
- [ ] Liquidity > $1M ADV
- [ ] Capacity documented
- [ ] Venue specified

### Section F: Documentation
- [ ] strategy.yaml
- [ ] strategy_spec.md
- [ ] backtest_report.json
- [ ] equity_curve.png
- [ ] stress_test_results.md
- [ ] oos_validation.json
- [ ] academic_refs.md
- [ ] CI workflow

### Section G: Statistical Rigor
- [ ] No lookahead bias
- [ ] No data leakage
- [ ] No survivorship bias
- [ ] Reproducible
- [ ] 95% CI provided

**Total: 35 checks. ALL must pass.**

---

*Template Version: 2026-02-26*
