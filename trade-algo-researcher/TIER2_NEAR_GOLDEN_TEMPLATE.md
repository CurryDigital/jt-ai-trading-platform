# Tier 2: Near-Golden Strategy Template

Use this template when promoting a Validated Hypothesis to Near-Golden.

## File Structure

```
/strategies/near_golden/{strategy_name}/
├── strategy.yaml              # REQUIRED: Full machine-readable spec
├── strategy_spec.md           # REQUIRED: Human-readable thesis + rules
├── backtest_report.json       # REQUIRED: Detailed metrics
├── equity_curve.png           # REQUIRED: Visual proof
├── stress_test_results.md     # REQUIRED: Crisis performance
└── enhancement_roadmap.md     # REQUIRED: Path to Golden
```

---

## strategy.yaml

```yaml
name: "Enhanced 3-Day RSI Mean Reversion"
version: "2.0"
tier: "near_golden"
status: "near_golden"          # validated_hypothesis → near_golden

promotion_history:
  - date: "2026-02-20"
    from: "idea"
    to: "validated_hypothesis"
    evidence: "Win rate 55%, Sharpe 0.95 on full universe"
  - date: "2026-02-26"
    from: "validated_hypothesis"
    to: "near_golden"
    evidence: "Enhanced to 64% win rate, Sharpe 1.35, DD 14%"

# --- PERFORMANCE EVIDENCE ---
# Near-Golden Thresholds: Win ≥60%, Sharpe ≥1.2, DD <20%, Decay <20%
target_win_rate: 0.65
actual_win_rate: 0.64

sharpe_ratio: 1.35
max_drawdown: 0.14
profit_factor: 1.72

avg_hold_days: 4.2
total_trades: 423

# 3-Tier Validation (REQUIRED)
backtest_period: "2019-01-01 to 2024-12-31"
oos_period: "2023-01-01 to 2024-12-31"      # ≥ 20% of data

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
  decay_vs_train: 0.0986                    # < 20%

oos_metrics:
  period: "2024"
  trades: 80
  win_rate: 0.62
  sharpe: 1.31
  max_dd: 0.14
  decay_vs_test: 0.0234                     # < 20%

# Universe Coverage (REQUIRED)
universe:
  asset_class: "equities"
  total_tested: 412
  valid_signals: 156
  coverage_pct: 37.9
  
  # Near-Golden: Document per-asset performance
  by_ticker:
    top_performers:
      - ticker: "AAPL"
        signals: 12
        win_rate: 0.75
      - ticker: "MSFT"
        signals: 10
        win_rate: 0.70
    
    bottom_performers:
      - ticker: "TSLA"
        signals: 8
        win_rate: 0.38        # Document failures too
        reason: "High volatility breaks mean-reversion assumption"

# --- STRATEGY LOGIC ---
asset_class: "equities"
direction: "long"
horizon: "short_term"

signals:
  frequency: "daily"
  rebalance: "daily"
  
  # Entry Logic (Explicit, falsifiable)
  entry_conditions:
    - condition: "consecutive_down_days >= 3"
      weight: 1.0
    - condition: "rsi_14 < 15"                # Tightened from 20
      weight: 1.0
    - condition: "volume > 2.5 * sma_volume_20"  # Tightened from 2x
      weight: 1.0
    - condition: "atr_14 < 0.05"              # NEW: Volatility filter
      weight: 0.5
  
  entry_logic: "ALL required: 3 down days + RSI<15 + Volume>2.5x + ATR<5%"
  
  # Exit Logic
  exit_conditions:
    - condition: "rsi_14 > 50"
      type: "target"
    - condition: "hold_days >= 7"              # Extended from 5
      type: "time_stop"
    - condition: "entry_price * 0.95"          # NEW: Stop loss
      type: "stop_loss"

# --- RISK MANAGEMENT (REQUIRED for Near-Golden) ---
risk:
  stop_loss_type: "fixed_percent"
  stop_loss_pct: 0.05                         # 5% hard stop
  
  position_sizing_method: "fixed_risk"
  max_position_pct: 0.04                      # 4% per position
  
  max_sector_pct: 0.15
  max_correlated_positions: 3                 # Don't pile into similar setups
  
  portfolio_heat: 0.20                        # Max 20% at risk

# --- EXECUTION ---
execution:
  venue: "IBKR"
  order_type: "market"
  slippage: 0.001                             # 10 bps
  transaction_costs: 0.0005                   # 5 bps per side

# --- ENHANCEMENT HISTORY ---
enhancements_applied:
  - date: "2026-02-22"
    change: "Tightened RSI threshold 20→15"
    impact: "+3% win rate, -12% trade frequency"
    
  - date: "2026-02-23"
    change: "Added ATR volatility filter"
    impact: "+4% win rate, filters high-vol false signals"
    
  - date: "2026-02-24"
    change: "Added 5% stop loss"
    impact: "-2% max DD, minimal win rate impact"
    
  - date: "2026-02-25"
    change: "Extended hold period 5→7 days"
    impact: "+2% avg winner, better capture of mean reversion"

# --- PATH TO GOLDEN ---
golden_gap_analysis:
  current_win_rate: 0.64
  target_win_rate: 0.70
  gap: 0.06
  
  current_sharpe: 1.35
  target_sharpe: 1.5
  gap: 0.15
  
  current_max_dd: 0.14
  target_max_dd: 0.15                        # Already better than target
  
  primary_blockers:
    - "Win rate 64% < 70% - need +6%"
    - "Sharpe 1.35 < 1.5 - need +0.15"

planned_enhancements:
  - priority: 1
    idea: "Sector-specific RSI thresholds"
    expected_impact: "+2-3% win rate"
    test_plan: "Run optimization per sector, avoid overfit"
    
  - priority: 2
    idea: "Add momentum filter (require price > 50d MA for tech)"
    expected_impact: "+1-2% win rate, filters falling knives"
    test_plan: "Test on tech-heavy periods"
    
  - priority: 3
    idea: "Profit target vs trailing stop comparison"
    expected_impact: "Improve risk-adjusted returns"
    test_plan: "A/B test on OOS period"

estimated_promotion_date: "2026-03-15"

# Metadata
author: "Trade Algo Researcher"
created: "2026-02-20"
promoted_near_golden: "2026-02-26"
qa_verified: false
```

---

## strategy_spec.md

```markdown
# Near-Golden Strategy: Enhanced 3-Day RSI Mean Reversion

## Status
**Tier:** Near-Golden  
**Target:** Golden (70%+ win rate, 1.5+ Sharpe)  
**Gap:** +6% win rate, +0.15 Sharpe  

---

## Performance Metrics

| Metric | Target | Current | Gap |
|--------|--------|---------|-----|
| Win Rate | 70% | 64% | -6% 🎯 |
| Sharpe Ratio | 1.5 | 1.35 | -0.15 🎯 |
| Max Drawdown | <15% | 14% | ✅ |
| Profit Factor | 1.5 | 1.72 | ✅ |
| Sample Size | 500 | 423 | ⚠️ |

## 3-Tier Validation

| Period | Trades | Win Rate | Sharpe | Decay | Status |
|--------|--------|----------|--------|-------|--------|
| Train (2019-21) | 198 | 66% | 1.42 | — | ✅ |
| Test (2022-23) | 145 | 63% | 1.28 | 9.9% | ✅ |
| OOS (2024) | 80 | 62% | 1.31 | 2.3% | ✅ |

All decay metrics < 20% threshold.

---

## Thesis

### Core Logic
Mean reversion after extreme oversold conditions with enhanced 
filtering to avoid high-volatility false signals.

### Why It Works
1. **Panic Selling Exhaustion:** 3+ down days + RSI < 15 indicates capitulation
2. **Volume Confirmation:** >2.5x volume validates institutional interest
3. **Volatility Filter:** ATR < 5% avoids earnings/momentum-driven moves

### Edge Persistence
Behavioral bias (panic selling) is stable. Volatility filter adapts 
to regime changes.

---

## Entry/Exit Rules

### Entry (ALL conditions required)
```
1. Consecutive down days ≥ 3
2. RSI(14) < 15
3. Volume > 2.5 × 20-day average
4. ATR(14) < 5% of price (volatility filter)
```

### Exit (ANY condition triggers)
```
1. RSI(14) > 50 (mean reversion target)
2. Hold days ≥ 7 (time stop)
3. Price < entry × 0.95 (5% stop loss)
```

---

## Risk Management

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| Max Position | 4% | Diversification across setups |
| Stop Loss | 5% hard | Limit single trade risk |
| Max Sector | 15% | Avoid concentration |
| Portfolio Heat | 20% | Max simultaneous risk |

---

## Enhancement History

| Date | Enhancement | Impact |
|------|-------------|--------|
| 2026-02-22 | Tightened RSI 20→15 | +3% win rate |
| 2026-02-23 | Added ATR filter | +4% win rate |
| 2026-02-24 | Added 5% stop loss | -2% max DD |
| 2026-02-25 | Extended hold 5→7 days | +2% avg winner |

**Cumulative:** 55% → 64% win rate

---

## Path to Golden

### Blockers
1. Win rate 64% < 70% target
2. Sharpe 1.35 < 1.5 target
3. Sample size 423 < 500 target

### Planned Enhancements

**Priority 1: Sector-Specific Thresholds**
- Tech: RSI < 12 (more extreme)
- Healthcare: RSI < 18 (less extreme)
- Expected: +2-3% win rate

**Priority 2: Momentum Filter for Tech**
- Require price > 50d MA for tech stocks
- Filters falling knives
- Expected: +1-2% win rate

**Priority 3: Profit Target Optimization**
- Test fixed profit target vs trailing stop
- Expected: +0.1-0.2 Sharpe

**Timeline:** Target Golden by 2026-03-15

---

## Known Limitations

1. **Low-frequency:** 156 signals/year on 412 tickers
2. **Tech underperformance:** TSLA 38% win rate (documented)
3. **Bear market decay:** 2022 showed 12% win rate drop
4. **Sample size:** Need 6+ more months to reach 500 trades

---

*Near-Golden Status: 2026-02-26 | Next Review: 2026-03-01*
```

---

## enhancement_roadmap.md

```markdown
# Enhancement Roadmap: Enhanced 3-Day RSI Mean Reversion

## Current Status
- **Tier:** Near-Golden
- **Win Rate:** 64% (target: 70%)
- **Sharpe:** 1.35 (target: 1.5)
- **Trades:** 423 (target: 500)

## Goal
Reach Golden tier by 2026-03-15

---

## Enhancement Queue

### Phase 1: Sector Optimization (Week 1)
**Objective:** +2-3% win rate through sector-specific thresholds

| Sector | Current RSI | Proposed | Rationale |
|--------|-------------|----------|-----------|
| Technology | < 15 | < 12 | Higher volatility needs more extreme |
| Healthcare | < 15 | < 18 | Lower volatility, faster mean reversion |
| Financials | < 15 | < 16 | Moderate adjustment |
| Energy | < 15 | < 14 | Commodity sensitivity |

**Success Criteria:**
- Win rate improvement ≥ 2%
- No sector sees win rate drop > 5%
- Decay remains < 20%

**Test Plan:**
1. Run 3-tier validation per sector
2. Combine optimized sectors
3. Verify full-period metrics

---

### Phase 2: Momentum Filter (Week 2)
**Objective:** +1-2% win rate by filtering falling knives

**Filter Logic:**
```
IF sector == "Technology" AND price < SMA(50):
    REQUIRE additional confirmation (RSI < 10)
```

**Rationale:** Tech stocks below 50d MA in down trends often 
continue falling (momentum). Require more extreme RSI to 
compensate.

**Success Criteria:**
- Win rate improvement ≥ 1%
- Max DD improvement ≥ 1%
- Trade frequency reduction < 20%

---

### Phase 3: Profit Target Optimization (Week 2-3)
**Objective:** +0.1-0.2 Sharpe improvement

**Test Variants:**
| Variant | Exit Logic | Expected Impact |
|---------|------------|-----------------|
| A (Current) | RSI > 50 | Baseline |
| B | Fixed 4% profit target | Faster exits, lower variance |
| C | Trailing stop 3% | Let winners run |
| D | RSI > 55 | More patience |

**Success Criteria:**
- Sharpe improvement ≥ 0.1
- Win rate maintained ≥ 63%
- Max DD unchanged or better

---

### Phase 4: Sample Size Accumulation (Ongoing)
**Objective:** Reach 500+ trades

**Current:** 423 trades (2019-2024)  
**Need:** 77 more trades  
**At current frequency:** ~6 months

**Acceleration Options:**
- Expand universe to 500+ tickers
- Relax ATR filter slightly (4% → 5%)
- Add international markets

**Risk:** Any expansion must not degrade metrics

---

## Exit Criteria (Golden Promotion)

All must be met:
- [ ] Win rate ≥ 70% (verified on 3-tier)
- [ ] Sharpe ≥ 1.5 (verified on 3-tier)
- [ ] Max DD < 15% (stress tested)
- [ ] Trades ≥ 500 (statistical power)
- [ ] Decay < 20% (stability)
- [ ] All artifacts complete
- [ ] QA verification passed

---

## Rollback Criteria

If any enhancement causes:
- Win rate drop > 3%
- Sharpe drop > 0.2
- Max DD increase > 3%

→ **ROLLBACK** and try next enhancement

---

*Roadmap Created: 2026-02-26 | Target Completion: 2026-03-15*
```

---

## QA Verification Checklist (Tier 2)

Before submitting for QA verification, ensure:

### Performance Thresholds
- [ ] Win rate ≥ 60%
- [ ] Sharpe ≥ 1.2
- [ ] Max DD < 20%
- [ ] Profit factor ≥ 1.3
- [ ] Sample size ≥ 300 trades

### 3-Tier Validation
- [ ] Train period documented
- [ ] Test period documented (no overlap with train)
- [ ] OOS period ≥ 20% of data
- [ ] Decay (Test→Train) < 20%
- [ ] Decay (OOS→Test) < 20%

### Risk Management
- [ ] Stop loss defined
- [ ] Position sizing documented
- [ ] Max position % specified
- [ ] Max sector % specified

### Implementation
- [ ] Transaction costs ≥ 0.05% per side
- [ ] Slippage assumption documented
- [ ] Execution venue specified

### Documentation
- [ ] strategy.yaml complete
- [ ] strategy_spec.md with thesis
- [ ] enhancement_roadmap.md with plan to Golden
- [ ] stress_test_results.md (at least COVID 2020)

### Code Quality
- [ ] No lookahead bias
- [ ] No data leakage
- [ ] Fixed random seeds
- [ ] Reproducible results

---

*Template Version: 2026-02-26*
