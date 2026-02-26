# Three-Tier Strategy Classification System

## Quick Reference

| Tier | Status | Location | Win Rate | Sharpe | Max DD | Trades | Key Purpose |
|------|--------|----------|----------|--------|--------|--------|-------------|
| **Tier 1** | Validated Hypothesis | `/hypotheses/validated/` | ≥ 50% | ≥ 0.8 | Documented | ≥ 100 | Prove concept |
| **Tier 2** | Near-Golden | `/strategies/near_golden/` | ≥ 60% | ≥ 1.2 | < 20% | ≥ 300 | Enhance to Golden |
| **Tier 3** | Golden | `/strategies/golden/` | ≥ 70% | ≥ 1.5 | < 15% | ≥ 500 | Production ready |

---

## Detailed Criteria by Tier

### Tier 1: Validated Hypothesis

**Promotion Criteria (from "Idea"):**
- Win rate ≥ 50%
- Sharpe ratio ≥ 0.8
- Sample size ≥ 100 trades
- Decay (Train→Test) < 30%
- Full universe tested (400+ tickers)
- Economic rationale documented

**Required Artifacts:**
- `hypothesis.yaml` — Machine-readable spec
- `test_results.json` — Full metrics
- `backtest_summary.md` — Human-readable
- `README.md` — Thesis + logic

**QA Verification:** 4-hour target response

**Next Steps:** 
- Continue testing combinations
- Enhance toward Tier 2 (60%+ win rate)
- Archive if decay > 50%

---

### Tier 2: Near-Golden

**Promotion Criteria (from Tier 1):**
- Win rate ≥ 60%
- Sharpe ratio ≥ 1.2
- Max drawdown < 20%
- Sample size ≥ 300 trades
- 3-tier validation complete (Train/Test/OOS)
- OOS period ≥ 20% of data
- Decay (Test→OOS) < 20%
- Stop loss defined
- Position sizing documented

**Required Artifacts:**
- `strategy.yaml` — Full spec
- `strategy_spec.md` — Thesis + rules
- `backtest_report.json` — Detailed metrics
- `equity_curve.png` — Visual proof
- `stress_test_results.md` — Crisis performance
- `enhancement_roadmap.md` — Path to Golden

**QA Verification:** 24-hour target response

**Next Steps:**
- Focus on ENHANCEMENT to reach Tier 3
- Target: 60-70% → 70%+ win rate
- Add risk management refinements
- Document path to Golden

---

### Tier 3: Golden

**Promotion Criteria (from Tier 2):**
- Win rate ≥ 70%
- Sharpe ratio ≥ 1.5
- Max drawdown < 15%
- Profit factor ≥ 1.5
- Sample size ≥ 500 trades
- OOS period ≥ 20% of data
- Decay < 20% across all periods

**Stress Tests (REQUIRED):**
- COVID Crash 2020 — Must survive with < 15% DD
- Rate Hikes 2022 — Must survive with < 15% DD
- Bear Market 2022 — Must survive with < 15% DD

**Risk Management (REQUIRED):**
- Stop loss defined per trade or portfolio
- Position sizing methodology (Kelly/risk-parity/vol-adjusted)
- Max single position ≤ 5% of capital
- Max sector exposure ≤ 15% of capital
- Beta neutral documented (if claimed)

**Implementation (REQUIRED):**
- Transaction costs ≥ 0.05% per side
- Slippage assumption documented
- Liquidity verified (avg daily volume > $1M)
- Capacity documented ($100M+ preferred)
- Execution venue specified (IBKR-compatible)

**Required Artifacts:**
- `strategy.yaml` — Full machine-readable spec
- `strategy_spec.md` — Human-readable thesis
- `backtest_report.json` — Full metrics (generated)
- `equity_curve.png` — Visual proof
- `stress_test_results.md` — Crisis performance
- `oos_validation.json` — Out-of-sample results
- `academic_refs.md` — Research basis
- `.github/workflows/validate.yml` — CI enforcement

**QA Verification:** 48-hour deep audit

**Next Steps:**
- Deploy to paper trading
- 30-day paper validation
- Promote to live trading
- Weekly monitoring per checklist

---

## Promotion Flow

```
┌─────────────┐    Win ≥50%    ┌─────────────────────┐    Win ≥60%    ┌──────────────────┐
│             │ ──────────────→│                     │ ──────────────→│                  │
│    Idea     │   Sharpe ≥0.8  │  Validated Hypothesis│   Sharpe ≥1.2  │   Near-Golden    │
│             │   N ≥100       │    (Tier 1)          │   DD <20%     │    (Tier 2)      │
└─────────────┘                │                     │   Decay <20%   │                  │
     ↓ Reject                  └─────────────────────┘                └──────────────────┘
┌─────────────┐                        ↓ Reject                              ↓ Reject
│  Archive    │                                               ┌──────────────────────┐
└─────────────┘                                               │                      │
                                                              │      Archive         │
                                                              │                      │
                                                              └──────────────────────┘
                                                                       ↑
                                                                       │ Win ≥70%
                                                                       │ Sharpe ≥1.5
                                                                       │ DD <15%
                                                                       │ Stress tests pass
                                                              ┌──────────────────────┐
                                                              │                      │
                                                              │       Golden         │
                                                              │      (Tier 3)        │
                                                              │                      │
                                                              └──────────────────────┘
                                                                       ↓
                                                              ┌──────────────────────┐
                                                              │                      │
                                                              │    Paper Trading     │
                                                              │      30 days         │
                                                              │                      │
                                                              └──────────────────────┘
                                                                       ↓
                                                              ┌──────────────────────┐
                                                              │                      │
                                                              │    Live Trading      │
                                                              │      90 days         │
                                                              │                      │
                                                              └──────────────────────┘
```

---

## QA Verification by Tier

### Tier 1 QA Checklist
- [ ] Data integrity (no NaNs, gaps < 5%)
- [ ] Temporal validity (time-ordered split)
- [ ] Sample size ≥ 100
- [ ] Win rate ≥ 50%
- [ ] Sharpe ≥ 0.8
- [ ] Decay < 30%
- [ ] Full universe tested (400+)
- [ ] Economic rationale documented

**Output:** ✅ VALIDATED / ❌ REJECTED

### Tier 2 QA Checklist
- All Tier 1 checks PLUS:
- [ ] Win rate ≥ 60%
- [ ] Sharpe ≥ 1.2
- [ ] Max DD < 20%
- [ ] Sample size ≥ 300
- [ ] 3-tier validation complete
- [ ] OOS ≥ 20% of data
- [ ] Decay (Test→OOS) < 20%
- [ ] Stop loss defined
- [ ] Position sizing documented
- [ ] Transaction costs ≥ 0.05%

**Output:** ✅ NEAR-GOLDEN / ❌ REJECTED

### Tier 3 QA Checklist (35 checks total)

**Section A: Performance (6)**
- [ ] Win rate ≥ 70%
- [ ] Sharpe ≥ 1.5
- [ ] Max DD < 15%
- [ ] Profit factor ≥ 1.5
- [ ] Sample size ≥ 500
- [ ] OOS ≥ 20%

**Section B: 3-Tier Validation (3)**
- [ ] Train period passes thresholds
- [ ] Test period passes thresholds
- [ ] OOS period passes thresholds
- [ ] Decay < 20%

**Section C: Stress Tests (3+)**
- [ ] COVID 2020 survived
- [ ] Rate hikes 2022 survived
- [ ] Bear market survived
- [ ] All crisis DD < 15%

**Section D: Risk Management (5)**
- [ ] Stop loss defined
- [ ] Position sizing method documented
- [ ] Max position ≤ 5%
- [ ] Max sector ≤ 15%
- [ ] Beta neutral (if claimed)

**Section E: Implementation (5)**
- [ ] Transaction costs ≥ 0.05%
- [ ] Slippage model documented
- [ ] Liquidity > $1M ADV
- [ ] Capacity documented
- [ ] Execution venue specified

**Section F: Documentation (7)**
- [ ] strategy.yaml present
- [ ] strategy_spec.md present
- [ ] backtest_report.json present
- [ ] equity_curve.png present
- [ ] stress_test_results.md present
- [ ] oos_validation.json present
- [ ] academic_refs.md present
- [ ] CI workflow present

**Section G: Statistical Rigor (5)**
- [ ] No lookahead bias
- [ ] No data leakage
- [ ] No survivorship bias
- [ ] Reproducible (fixed seeds)
- [ ] 95% confidence intervals

**Output:** ✅ GOLDEN / ⏸️ CONDITIONAL / ❌ REJECTED

---

## Artifact Templates

| Tier | Template File |
|------|---------------|
| Tier 1 | `TIER1_VALIDATED_HYPOTHESIS_TEMPLATE.md` |
| Tier 2 | `TIER2_NEAR_GOLDEN_TEMPLATE.md` |
| Tier 3 | `TIER3_GOLDEN_TEMPLATE.md` |

---

## Quick Decision Matrix

| Win Rate | Sharpe | Decay | Classification | Action |
|----------|--------|-------|----------------|--------|
| < 50% | Any | Any | ❌ REJECT | Archive |
| 50-60% | ≥ 0.8 | < 30% | Tier 1 | Document, enhance |
| 60-70% | ≥ 1.2 | < 20% | Tier 2 🎯 | PR + enhancement focus |
| ≥ 70% | ≥ 1.5 | < 20% | Tier 3 🏆 | Full deployment |

---

## Researcher Responsibilities by Tier

### Tier 1 (Validated Hypothesis)
- Test on full universe (400+ tickers)
- Document economic rationale
- Be honest about limitations
- Plan enhancements to reach Tier 2

### Tier 2 (Near-Golden)
- Complete 3-tier validation
- Add comprehensive risk management
- Document stress tests
- Create detailed enhancement roadmap
- **Focus:** Push 60-70% → 70%+

### Tier 3 (Golden)
- Pass ALL 35 QA checks
- Survive stress tests
- Complete all artifacts
- Set up CI/CD pipeline
- Weekly verification checklist

---

## QA Responsibilities by Tier

### Tier 1
- Quick sanity check (4 hours)
- Verify metrics match claims
- Check for cherry-picking
- Approve/reject

### Tier 2
- Full verification (24 hours)
- Reproduce backtest
- Verify 3-tier validation
- Check risk management
- Approve/reject

### Tier 3
- Deep audit (48 hours)
- Reproduce ALL metrics
- Verify stress tests
- Check implementation feasibility
- **HOLD FIRM** on all 35 checks
- **DO NOT** rubber-stamp
- Approve/reject/conditional

---

## Escalation Rules

Escalate to Jacky when:
1. Researcher disputes rejection
2. Intentional gaming detected
3. Low-confidence concerns despite passing checks
4. Deadlock on interpretation
5. Pressure to approve sub-standard strategy
6. **Tier misclassification detected** (claiming Golden when Near-Golden)

---

## Memory Files

### Researcher
- `memory/strategies/{name}.md` — Strategy memory
- `memory/enhancements/{name}.md` — Enhancement attempts
- `memory/hypotheses/H{XXX}.md` — Hypothesis notes

### QA
- `memory/audit_log_YYYY-MM-DD.md` — Daily verifications
- `memory/standards.md` — Evolving standards
- `memory/researcher_patterns.md` — Recurring issues
- `memory/tier_promotions.md` — Promotion log
- `audit_trail/PR{N}_audit_YYYY-MM-DD.md` — PR-specific audits

---

*System Version: 2026-02-26*
*Applies to: Trade Algo Researcher, Trade Algo QA*
