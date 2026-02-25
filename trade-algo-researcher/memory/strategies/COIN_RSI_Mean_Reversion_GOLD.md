# RSI Mean Reversion Strategy — COIN GOLD

**Classification:** 🏆 Golden Strategy (Walk-Forward Validated)

## Performance Summary

| Metric | Value |
|--------|-------|
| **Test Win Rate** | **70.3%** |
| **Train Win Rate** | ~60% |
| **Sample Size (Test)** | 37 trades |
| **Decay** | ~-10% (improved in test) |
| **95% CI** | [54.2%, 82.5%] |
| **Signal Frequency** | ~19 signals/year |

## Strategy Logic

**Entry Signal:**
1. RSI(14) < 30 (oversold condition)
2. 5-day hold period

**Parameters:**
- RSI Period: 14 days
- Threshold: RSI < 30
- Hold Period: 5 days

## Edge Explanation

COIN (Coinbase) exhibits strong mean reversion characteristics when oversold. As a crypto proxy with high volatility, extreme RSI readings often represent emotional selling that reverses within days.

## Validation

- **Train Period:** 2021-2022
- **Test Period:** 2023-2024
- **Method:** Walk-forward analysis
- **Status:** ✅ Validated — Meets all Golden criteria

## Trade Statistics

| Period | Win Rate | Trades |
|--------|----------|--------|
| Train | ~60% | ~45 |
| Test | **70.3%** | **37** |

## Risk Notes

- Crypto assets have high volatility — position size accordingly
- Works best in bull markets for crypto
- Consider adding SPY uptrend filter for enhanced safety

## Deployment Status

🟡 **Ready for Paper Trading**

---
*Generated: 2026-02-23*  
*Research ID: CONTINUOUS-2026-02-23-COIN-RSI-MR*
