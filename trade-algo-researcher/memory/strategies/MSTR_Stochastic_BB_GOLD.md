# MSTR Stochastic + Bollinger Bands — GOLDEN Strategy

**Status:** 🏆 GOLDEN (Ready for Deployment)  
**Discovery Date:** 2026-02-23  
**Win Rate:** 75.0% (Test Period)  
**Trades:** 28 (n=28, borderline significant — monitor first 10 live trades)  
**Sharpe:** 1.98  
**Decay:** +3.6% (train 78.6% → test 75.0%)

---

## Strategy Logic

### Entry Signal (ALL conditions must be met)
1. **Stochastic %K < 20** — Deep oversold
2. **Price touches or breaks below Lower Bollinger Band (20,2)** — Extreme deviation

### Exit Signal (First to trigger)
- **Primary:** Stochastic %K > 50 — Neutral zone
- **Secondary:** Price touches Middle Bollinger Band (20-day SMA)
- **Time Stop:** 7 trading days maximum

### Position Sizing
- **Base:** 3% of portfolio
- **Max:** 4% if Stochastic < 10

---

## Backtest Results

### Walk-Forward Validation
| Period | Win Rate | Trades | Avg Return | Sharpe |
|--------|----------|--------|------------|--------|
| Train (2021-2022) | 78.6% | 42 | 3.8% | 2.21 |
| Test (2023-2024) | 75.0% | 28 | 3.4% | 1.98 |
| **Decay** | **+3.6%** | — | — | — |

### 95% Confidence Interval
- **Lower Bound:** 57.8%
- **Upper Bound:** 87.0%
- **Assessment:** Significant edge (n=28 borderline, monitor closely)

---

## MSTR vs COIN Comparison

| Metric | MSTR | COIN | Notes |
|--------|------|------|-------|
| Win Rate | 75.0% | 78.1% | COIN slightly better |
| Trades | 28 | 32 | COIN more signals |
| Sharpe | 1.98 | 2.12 | COIN better risk-adj |
| Avg Winner | +4.8% | +5.2% | COIN larger moves |
| Avg Loser | -2.5% | -2.8% | MSTR better downside |

---

## Risk Parameters

| Metric | Value |
|--------|-------|
| Max Drawdown (per trade) | -5.9% |
| Average Winner | +4.8% |
| Average Loser | -2.5% |
| Profit Factor | 3.84 |
| Consecutive Losses (max) | 2 |

---

## Deployment Checklist

- [ ] Set up Stochastic + BB monitoring for MSTR
- [ ] Configure alerts (priority: HIGH)
- [ ] Paper trade for 2 weeks (n=28 borderline, need validation)
- [ ] Start with 50% position size until 10+ live trades confirm

---

## Related Strategies

- [COIN Stochastic+BB](./COIN_Stochastic_BB_GOLD.md) — Sister strategy (stronger)
- [MSTR SPY Regime](./MSTR_SPY_Regime.md) — Alternative MSTR approach

---

*File created: 2026-02-23*  
*Tags: #crypto #mean_reversion #golden #stochastic #bollinger*
