# BB Squeeze Breakout Strategy — SPY GOLD

**Classification:** 🏆 Golden Strategy (Walk-Forward Validated)

## Performance Summary

| Metric | Value |
|--------|-------|
| **Test Win Rate** | **82.6%** |
| **Train Win Rate** | 61.0% |
| **Sample Size (Test)** | 23 trades |
| **Decay** | -21.6% (improved in test) |
| **95% CI** | [62.9%, 93.0%] |
| **Signal Frequency** | ~12 signals/year |

## Strategy Logic

**Entry Signal:**
1. BB Width in bottom 10% of 120-day range (squeeze condition)
2. Next day: Close > Previous day's high (breakout)
3. 5-day hold period

**Parameters:**
- BB Period: 20 days
- Squeeze Threshold: 10th percentile of 120-day BB width
- Hold Period: 5 days

## Edge Explanation

Market-wide volatility compression (measured via SPY BB width) precedes directional moves. The breakout filter ensures we capture the direction of the expansion, not just random noise.

## Validation

- **Train Period:** 2021-2022
- **Test Period:** 2023-2024
- **Method:** Walk-forward analysis
- **Status:** ✅ Validated — Strong out-of-sample performance

## Use Case

This strategy can serve as a **market regime filter**. When SPY BB Squeeze triggers:
- Consider increasing position sizes across other strategies
- Reduce hedges
- Expect higher volatility ahead

## Deployment Status

🟡 **Ready for Paper Trading**

---
*Generated: 2026-02-23*  
*Research ID: CONTINUOUS-2026-02-23-SPY-BB-SQUEEZE*
