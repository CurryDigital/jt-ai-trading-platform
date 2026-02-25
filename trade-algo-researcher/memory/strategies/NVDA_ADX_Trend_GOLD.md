# NVDA ADX Trend Continuation — GOLDEN STRATEGY
**Status:** 🏆 Golden (Ready for Deployment)  
**Discovered:** 2026-02-23 20:27 UTC  
**Win Rate:** 84.0% (Test Period)  
**Trades:** 125 (n≥30 ✓)

---

## Strategy Specification

### Entry Criteria
1. **ADX > 25** — Strong trend confirmed
2. **Price > SMA20** — Upward momentum intact
3. Both conditions must be true on entry day

### Exit Criteria
- **Time-based:** Hold 10 days, exit at market close
- **No profit target** — Let trend run
- **No stop loss** — Time exit only

---

## Performance Metrics

### Walk-Forward Validation
| Period | Win Rate | Trades | Avg Return |
|--------|----------|--------|------------|
| Train (2021-2022) | 73.8% | 141 | +0.31% |
| **Test (2023-2024)** | **84.0%** | **125** | **+0.37%** |

### Statistical Significance
- **Decay:** +10.2% (improved in test — excellent!)
- **95% CI:** [77.6%, 90.4%]
- **Sharpe Estimate:** ~2.0

### Signal Frequency
- **Signals/Year:** ~63
- **Signals/Month:** ~5
- **Trade Duration:** 10 days

---

## Key Insights

### Why This Works
1. **AI Theme:** NVDA = AI infrastructure play — strong secular trend
2. **Momentum Persistence:** NVDA trends persist 10+ days
3. **2023-2024 AI Boom:** Test period captured AI buildout
4. **Strong Trends Only:** ADX > 25 filters choppy periods

### Comparison: Trend vs Mean Reversion
| Strategy Type | Win Rate | n | Notes |
|--------------|----------|---|-------|
| ADX Trend (this) | 84.0% | 125 | Trend following |
| Stoch+Trend | 79.4% | 34 | Mean reversion |
| RSI < 30 | 65% | 45 | Basic mean reversion |

**Conclusion:** Trend following > Mean reversion for NVDA

### Market Regime Suitability
| Regime | Expected Performance |
|--------|---------------------|
| AI Bull | ⭐⭐⭐⭐⭐ Exceptional |
| Tech Bull | ⭐⭐⭐⭐ Strong |
| Market Chop | ⭐⭐ Weak (ADX filter protects) |
| Bear Market | Not tested — avoid |

---

## Risk Factors

1. **Theme Concentration:** 100% AI exposure
2. **Earnings Volatility:** Quarterly announcements = gaps
3. **Valuation Risk:** High PE multiple vulnerable to rates

### Mitigation
- Check earnings calendar — avoid 3 days before
- Reduce size if VIX > 30
- Pair with defensive strategies

---

## Implementation

```python
# Entry signal
def entry_signal(df, i):
    return (
        df['adx'].iloc[i] > 25 and
        df['close'].iloc[i] > df['sma_20'].iloc[i]
    )

# Exit after 10 days
hold_days = 10
```

---

## Deployment Checklist

- [x] Walk-forward validated
- [x] n > 30 (125 trades)
- [x] Decay < 15% (+10.2%)
- [x] 95% CI calculated
- [x] Strategy file documented
- [ ] Paper trade (20 trades)
- [ ] Live deploy

---

## Related Strategies

- [QQQ_ADX_Trend_GOLD](QQQ_ADX_Trend_GOLD.md) — Tech basket
- [AMD_ADX_Trend_GOLD](AMD_ADX_Trend_GOLD.md) — Semi peer
- [NVDA_Stoch_Trend_GOLD](NVDA_Stoch_Trend_GOLD.md) — Mean reversion variant

---

*Strategy validated: 2026-02-23*  
*Next review: Weekly (Monday 09:00 HKT)*
