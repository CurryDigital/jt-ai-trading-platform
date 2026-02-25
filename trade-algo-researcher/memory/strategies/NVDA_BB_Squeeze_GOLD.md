# NVDA BB Squeeze + RSI Strategy

## Status: 🏆 GOLDEN
**Discovered:** February 23, 2026 - Evening Batch  
**Win Rate:** 77.8% (Test Period 2023-2024)  
**Sample Size:** 36 trades  
**Decay:** 10.3% (train vs test)  
**95% CI:** [61.4%, 88.3%]

---

## Entry Criteria
1. **BB Width < 5%** (Bollinger Band squeeze - volatility compression)
2. **RSI < 45** (oversold but not extreme)
3. **2 consecutive days** of BB squeeze confirmation

## Exit Criteria
- **Hold for 5 trading days**
- Fixed exit - no trailing stop

## Performance Metrics

| Metric | Value |
|--------|-------|
| Test Win Rate | 77.8% |
| Train Win Rate | 67.5% |
| Decay | +10.3% (improved in test) |
| Trades (Test) | 36 |
| Trades (Train) | 43 |
| Signals/Year | ~18 |

## Validation
- ✅ Test ≥ 70% (77.8%)
- ✅ n ≥ 30 (36 trades)
- ✅ Decay < 15% (10.3%)
- ✅ 95% CI lower bound > 60% (61.4%)

## Rationale
Bollinger Band squeezes represent volatility compression that typically precedes expansion. By combining with RSI < 45, we filter for oversold conditions where mean reversion has higher probability. The 5-day hold captures the typical mean reversion cycle without overstay.

## Walk-Forward Results

| Period | Win Rate | Trades |
|--------|----------|--------|
| Train (2021-2022) | 67.5% | 43 |
| Test (2023-2024) | 77.8% | 36 |

## Risk Considerations
- Strategy performs mean reversion - avoid during strong trending periods
- Best suited for volatile tech stocks
- Fixed 5-day hold may not optimize individual trades

## Deployment Notes
- Position size: Standard mean reversion allocation
- Stop loss: Not implemented (hold fixed 5 days)
- Market regime: Works in both bull and bear markets
- Correlation: Check against existing NVDA strategies for overlap

---

**File Created:** 2026-02-23  
**Next Review:** Weekly verification (Monday 09:00 HKT)
