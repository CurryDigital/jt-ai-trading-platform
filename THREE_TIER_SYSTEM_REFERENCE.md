# Three-Tier Strategy Classification System

## Quick Reference

| Tier | Win Rate | Profit Factor | Sharpe | Max DD | Trades | Location |
|------|----------|---------------|--------|--------|--------|----------|
| **Validated Hypothesis** | ≥ 50% | ≥ 1.3 | ≥ 0.8 | < 25% | ≥ 100 | `/hypotheses/validated/` |
| **Near-Golden** | ≥ 55% | ≥ 1.5 | ≥ 1.2 | < 20% | ≥ 300 | `/strategies/near_golden/` |
| **Golden** | See 4 paths below | | | | ≥ 500 | `/strategies/golden/` |

---

## Golden Tier — Four Paths

A strategy qualifies as Golden via **ANY** of these paths:

| Path | Win Rate | Profit Factor | Sharpe | Max DD | Best For |
|------|----------|---------------|--------|--------|----------|
| **A: High Win Rate** | ≥ 70% | ≥ 1.5 | ≥ 1.5 | < 15% | Mean reversion |
| **B: High Profit Factor** | ≥ 40% | ≥ 1.8 | ≥ 1.5 | < 15% | Trend following |
| **C: Exceptional Sharpe** | ≥ 35% | ≥ 1.5 | ≥ 2.0 | < 12% | Multi-factor |
| **D: Low Risk** | ≥ 50% | ≥ 1.6 | ≥ 1.5 | < 10% | Arbitrage |

**Common requirements (all paths):**
- Sample size ≥ 500 trades
- OOS period ≥ 20% of data  
- Decay < 20% across periods
- Stress tests passed (COVID 2020, Rate Hikes 2022)
- Stop loss defined
- Position sizing documented
- Max position ≤ 5%, max sector ≤ 15%

---

## Classification Matrix

| Win% | PF | Sharpe | Classification |
|------|-------|--------|----------------|
| < 50% | < 1.3 | < 0.8 | ❌ REJECT |
| 50-55% | 1.3-1.5 | 0.8-1.2 | Tier 1: Validated Hypothesis |
| 55-70% | 1.5-1.8 | 1.2-1.5 | Tier 2: Near-Golden |
| ≥ 70% | ≥ 1.5 | ≥ 1.5 | Tier 3A: Golden |
| ≥ 40% | ≥ 1.8 | ≥ 1.5 | Tier 3B: Golden |
| ≥ 35% | ≥ 1.5 | ≥ 2.0 | Tier 3C: Golden |
| ≥ 50% | ≥ 1.6 | ≥ 1.5 | Tier 3D: Golden |

---

## Promotion Flow

```
Idea → Validated Hypothesis → Near-Golden → Golden → Paper → Live
        (≥50%, PF≥1.3)    (≥55%, PF≥1.5)   (4 paths)
```

---

## QA Verification by Tier

### Tier 1 (4 hours)
- 8 checks: Win ≥50%, PF ≥1.3, Sharpe ≥0.8, DD <25%, N≥100, Decay <30%, Full universe, No lookahead

### Tier 2 (24 hours)
- 14 checks: Win ≥55%, PF ≥1.5, Sharpe ≥1.2, DD <20%, N≥300, 3-tier validation, OOS≥20%, Decay <20%, Stop loss, Position sizing, Costs

### Tier 3 (48 hours)
- 35 checks: Performance (4 paths), 3-tier validation (5), Stress tests (3), Risk mgmt (5), Implementation (5), Documentation (8), Statistical rigor (5)

---

## Examples

| Strategy | Win% | PF | Sharpe | DD | Path | Golden? |
|----------|------|-------|--------|-----|------|---------|
| RSI Mean Rev | 72% | 1.85 | 1.8 | 12% | A | ✅ |
| Breakout Trend | 42% | 1.9 | 1.6 | 14% | B | ✅ |
| Factor Residual | 67% | 2.1 | 2.4 | 9.5% | C | ✅ |
| Pairs Arb | 78% | 1.4 | 1.3 | 6% | None | ❌ (PF < 1.5) |
| 3-Day Reversal | 64% | 1.72 | 1.35 | 14% | None | → Tier 2 |

---

## Artifact Templates

| Tier | Template |
|------|----------|
| Tier 1 | `TIER1_VALIDATED_HYPOTHESIS_TEMPLATE.md` |
| Tier 2 | `TIER2_NEAR_GOLDEN_TEMPLATE.md` |
| Tier 3 | `TIER3_GOLDEN_TEMPLATE.md` |

---

*System Version: 2026-02-26*
