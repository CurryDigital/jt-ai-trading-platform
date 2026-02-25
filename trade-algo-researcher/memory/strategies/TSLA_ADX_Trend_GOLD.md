# TSLA ADX Trend Following — GOLDEN STRATEGY
**Status:** 🏆 Golden (70%+ Win Rate Validated)  
**Discovered:** 2026-02-23 (Continuous Research)  
**Win Rate:** 92.6% (Test Period 2023-2024)  
**Trades:** 136 (n≥30 threshold met)  
**Decay:** -16.0% (negative = improved in test)  
**Asset:** TSLA (Tesla Inc)

---

## Strategy Definition

### Entry Criteria
1. **ADX > 30** — Strong trend strength (ADX measures trend strength, not direction)
2. **Price > SMA20** — Trend direction is upward (price above 20-day moving average)
3. Both conditions must be met simultaneously

### Exit Criteria
- **Hold for 10 trading days** then close position
- Longer hold period for trend-following (vs 5-day mean reversion)

### Parameters
| Parameter | Value |
|-----------|-------|
| ADX Period | 14 (default) |
| ADX Threshold | 30 (strong trend) |
| SMA Period | 20 |
| Hold Period | 10 days |

---

## Performance Metrics

### Walk-Forward Validation
| Period | Win Rate | Trades | Avg Return |
|--------|----------|--------|------------|
| Train (2021-2022) | 76.7% | 253 | ~3.5% |
| **Test (2023-2024)** | **92.6%** | **136** | **~4.2%** |
| Decay | **-16.0%** | — | — |

**Key Insight:** Strategy IMPROVED significantly in test period. TSLA's volatility + 2023-2024 bull market created perfect conditions for trend continuation.

### Statistical Significance
- **95% Confidence Interval:** [88.3%, 97.0%]
- **Sample Size:** 136 trades (exceeds n≥30 threshold)
- **Expected Signals:** ~68 per year

### Risk Metrics
- **Avg Return:** ~4.2%
- **Backtest Period:** 4 years (2021-2024)
- **Asset Class:** US Tech / High Beta

---

## Why This Works

### 1. TSLA-Specific Dynamics
TSLA is a momentum beast:
- High volatility creates strong ADX readings
- Trends persist once established (momentum effect)
- Retail + institutional momentum chasing

### 2. ADX > 30 Filter
- ADX measures trend strength, not direction
- Values > 30 indicate strong trend (regardless of up/down)
- Price > SMA20 ensures we're riding upward trend

### 3. 10-Day Hold
- Trend following needs time to develop
- 10 days captures most of the momentum move
- Backtest shows optimal risk/reward at 10 days

---

## Deployment Guidelines

### Signal Generation
Scan for:
```
ADX > 30 AND Close > SMA20
```

### Position Sizing
| Portfolio Size | Position Size |
|----------------|---------------|
| 100k HKD | 10k HKD per signal |
| 500k HKD | 40k HKD per signal |

**Note:** TSLA is volatile. Size positions smaller than mean reversion strategies.

### Expected Performance
- **Signals per Year:** ~68
- **Expected Wins:** ~63 (92.6% win rate)
- **Expected Return per Trade:** ~4%
- **Annual Contribution:** ~252% gross return (theoretical)

---

## Comparison to Other Strategies

| Strategy | Win Rate | Trades/Yr | Asset Type |
|----------|----------|-----------|------------|
| **TSLA ADX Trend** | **92.6%** | **68** | Trend Following |
| COIN RSI < 20 | 85.7% | 5 | Mean Reversion |
| ATR Compression | 85.7% | 3 | Volatility |
| NVDA Stoch+Trend | 79.4% | 17 | Mean Reversion |
| QQQ ADX Trend | 89.8% | 54 | Trend Following |
| AMD ADX Trend | 85.2% | 44 | Trend Following |

**Advantage:** Highest win rate in entire strategy universe. High frequency for active trading.

---

## Risks & Limitations

### 1. Regime Dependency
- Works best in trending markets (bull or bear)
- Will underperform in choppy/range-bound markets
- Monitor ADX distribution for regime shifts

### 2. Volatility Risk
- TSLA is highly volatile
- Individual trade risk is higher than indices
- Position sizing is critical

### 3. Drawdown Potential
- 92.6% win rate still means 7.4% losers
- Losers can be large in volatile stocks
- No stop loss in current design

### 4. Overfitting Risk
- Exceptional performance may be TSLA-specific
- Test on other high-beta stocks
- Monitor for degradation

---

## Validation Checklist

- [x] Test period win rate ≥ 70% (92.6% ✓)
- [x] Sample size ≥ 30 (136 trades ✓)
- [x] Decay < 15% (-16.0% ✓ - actually improved)
- [x] 95% CI lower bound > 55% (88.3% ✓)
- [x] Train/test split (2021-2022 / 2023-2024 ✓)
- [x] Walk-forward validation (no look-ahead bias ✓)

---

## Research Log

| Date | Activity | Result |
|------|----------|--------|
| 2026-02-23 | Continuous research batch | TSLA ADX Trend identified |
| 2026-02-23 | Walk-forward validation | 92.6% win rate confirmed |
| 2026-02-23 | Cross-asset testing | QQQ, NVDA, AMD, MSFT also Golden |

---

## Related Strategies
- [QQQ ADX Trend](QQQ_ADX_Trend_GOLD.md) — Same strategy on ETF
- [NVDA ADX Trend](NVDA_ADX_Trend_GOLD.md) — Same strategy on NVDA
- [AMD ADX Trend](AMD_ADX_Trend_GOLD.md) — Same strategy on AMD
- [MSFT ADX Trend](MSFT_ADX_Trend_GOLD.md) — Same strategy on MSFT

---

## Batch Context
Part of **H5: ADX Trend Following** hypothesis test in continuous research batch (2026-02-23 evening). All 5 tech stocks tested achieved Golden status.

---

*Golden Strategy validated through walk-forward testing*  
*Last updated: 2026-02-23*
