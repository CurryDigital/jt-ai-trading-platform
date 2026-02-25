

---

## EXIT STRATEGY FRAMEWORK - OFFICIAL (2026-02-23)

### Key Finding: Exit Method Depends on Strategy Tier

| Tier | Win% Range | Exit Method | Reason |
|------|------------|-------------|--------|
| Golden | 70%+ | Time exits | Preserve Sharpe, already successful |
| Near-Golden | 60-70% | +3% Profit Target | Push to 70% Golden status |
| Validated | 55-60% | Time or +4% PT | Already at threshold |

### Universal Rules Discovered

**DO:**
- Use profit targets (+3%) to boost win rate by ~10%
- Keep time exits for Golden strategies (preserve Sharpe)
- Apply sector-specific optimization (HK for BB+Monday = 88.9%)

**DON'T:**
- Use trailing stops (destroy win rate by -11.2%)
- Add tight stop losses (exit on noise)
- Change exits on already-successful strategies

### Profit Target Impact (RSI Mean Reversion Test)

| Exit | Win% | Sharpe | Change |
|------|------|--------|--------|
| +3% PT | 65.2% | -0.08 | +9.9% win rate |
| +5% PT | 59.6% | 0.30 | +4.3% win rate |
| Time 10d | 55.3% | 0.92 | Baseline |
| Trailing -3% | 44.1% | 0.73 | -11.2% FAIL |

### Documentation

Full exit strategy guide: EXIT_STRATEGY_RECOMMENDATIONS.md
Updated deployment index: JT_DEPLOYMENT_INDEX_ALL_20.md

---

*Exit strategy optimization complete*
*Date: 2026-02-23*
