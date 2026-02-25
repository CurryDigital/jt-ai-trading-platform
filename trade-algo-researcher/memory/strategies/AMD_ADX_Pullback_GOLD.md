# AMD ADX Trend Pullback — GOLD Strategy
**Classification:** Golden (70%+ Win Rate, n≥30)  
**Discovery Date:** 2026-02-23  
**Win Rate:** 80.4% | **Trades:** 56 | **Sharpe:** 0.76

---

## Strategy Overview

**Asset:** AMD (Advanced Micro Devices)  
**Type:** Trend-Following + Mean Reversion Hybrid  
**Timeframe:** Daily  
**Hold Period:** 5 days

### Philosophy
Buy pullbacks within established uptrends. AMD as a high-beta semiconductor stock exhibits strong trending behavior with predictable pullbacks to the 20-day SMA during trending periods.

---

## Entry Rules

1. **Trend Confirmation:** ADX > 25 (established trend)
2. **Pullback Condition:** Close price < 20-day SMA
3. **Hold Period:** Exit after 5 trading days

### Signal Logic
```
ENTRY when:
  ADX > 25 AND
  close < sma_20

EXIT after 5 days (time-based)
```

---

## Performance Metrics

### Walk-Forward Validation (Test: 2023-2024)

| Metric | Value |
|--------|-------|
| **Win Rate** | **80.4%** |
| **Sample Size** | 56 trades |
| **Average Return** | +0.45% |
| **Median Return** | +0.29% |
| **Maximum Gain** | +1.93% |
| **Maximum Loss** | -0.52% |
| **Sharpe Ratio** | 0.76 |
| **Total Return** | +25.40% |
| **95% CI** | [70.0%, 90.8%] |

### Train vs Test (Decay Analysis)
| Period | Win Rate | Sample |
|--------|----------|--------|
| Train (2021-2022) | 81.0% | - |
| Test (2023-2024) | 80.4% | 56 |
| **Decay** | **+0.7%** | ✅ Stable |

### Golden Criteria Check
- ✅ Test ≥ 70% (80.4%)
- ✅ n ≥ 30 (56 trades)
- ✅ Decay < 15% (+0.7% - excellent stability)
- ✅ 95% CI lower bound > 60% (70.0%)

---

## Why This Works

1. **AMD Characteristics:** High-beta semiconductor with strong momentum cycles
2. **Trend Persistence:** ADX > 25 confirms directional movement, not chop
3. **Pullback Logic:** 20-day SMA acts as dynamic support in trending markets
4. **Short Hold:** 5-day exit captures mean reversion before trend resumes

---

## Risk Considerations

### Strengths
- Large sample size (56 trades) for statistical significance
- Near-zero decay (strategy stable across regimes)
- Tight max loss (-0.52%) limits downside

### Weaknesses
- Requires trending market (ADX > 25 filter)
- Limited signals (~28/year)
- Single-asset concentration risk

### When to Avoid
- When ADX drops below 25 (choppy markets)
- During earnings week (increased volatility)
- Broader semiconductor sector weakness

---

## Implementation Notes

### Signal Frequency
- ~2.3 signals per month
- ~28 signals per year

### Position Sizing
- Suggest 5-10% allocation per signal
- Can run alongside other uncorrelated strategies

### Correlation
- Highly correlated with NVDA (semiconductor sector)
- Moderate correlation with QQQ (tech beta)
- Diversify with non-tech strategies

---

## Research Log

| Date | Action | Result |
|------|--------|--------|
| 2026-02-23 | Initial test | Validated at 80.4% |
| 2026-02-23 | Golden promotion | ✅ Deployable |

---

## Files
- Stats: `results/AMD_ADX_Pullback_GOLD_stats.json`
- Research: `results/continuous_research_2026-02-23_batch2.json`

---

*Validated with walk-forward analysis (Train 2021-2022 / Test 2023-2024)*  
*Not financial advice. For research purposes only.*
