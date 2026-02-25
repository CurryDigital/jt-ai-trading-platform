# BB Squeeze Breakout — AMD 🏆 GOLDEN STRATEGY
**Ticker:** AMD (Advanced Micro Devices)  
**Strategy Type:** Volatility Expansion / Breakout  
**Win Rate:** 79.2%  
**Sample Size:** 24 trades  
**Avg Return:** 0.39% per trade  
**Status:** 🟡 Near-Golden (n<30 but >20)  
**File Created:** 2026-02-23

---

## Strategy Logic

### Entry Criteria
1. **BB Squeeze:** Bollinger Band width < 80% of 20-day average width
2. **Breakout:** Close > Previous day's BB upper band

### Exit Criteria
- **Time-based:** Exit after 5 trading days

---

## Performance Metrics

### Walk-Forward Results (Test: 2023-2024)
| Metric | Value |
|--------|-------|
| Win Rate | 79.2% |
| Number of Trades | 24 |
| Average Return | 0.39% |
| 95% CI (Win Rate) | [58.4%, 91.0%] |

**Note:** n=24 is slightly below Golden threshold of 30, but above minimum of 20. Monitor for additional signals.

---

## Why It Works

**AMD-Specific Edge**
- High-beta semiconductor play
- Volatility compression precedes product cycles
- Strong institutional accumulation on breakouts

---

## Risk Considerations

### Strengths
- ✅ Highest avg return of BB Squeeze family (0.39%)
- ✅ Good win rate (79.2%)

### Weaknesses
- ⚠️ n=24 is below ideal 30 threshold
- ⚠️ Wide confidence interval due to smaller sample
- ⚠️ More volatile than MSFT/NVDA

---

## Validation History

| Date | Action | Result |
|------|--------|--------|
| 2026-02-23 | Discovered | 79.2% win rate |
| 2026-02-23 | Documented | Near-Golden status (n<30) |

---

## Related Strategies

- [MSFT_BB_Squeeze_GOLD](MSFT_BB_Squeeze_GOLD.md) — 91.7% win
- [NVDA_BB_Squeeze_GOLD](NVDA_BB_Squeeze_GOLD.md) — 88.4% win
- [AMD_ADX_Pullback](AMD_ADX_Pullback.md) — Trend strategy

---

*Near-Golden: Win rate ≥70% but n=20-30. Monitor for more signals.*  
*Last updated: 2026-02-23*
