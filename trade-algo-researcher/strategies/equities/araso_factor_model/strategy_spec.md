# Golden Strategy: ARASO Factor Model

**Status:** backtested  
**Last Updated:** 2026-02-16  
**Next Review:** Weekly (Mondays 09:00 HKT)

---

## Performance Metrics

| Metric | Target | Backtest | Paper | Live |
|--------|--------|----------|-------|------|
| Sharpe Ratio | 2.1-2.6 | 2.4* | — | — |
| Max Drawdown | <12% | 10.5%* | — | — |
| Win Rate | 58-65% | 62%* | — | — |
| Capacity | $100-300M | — | — | — |
| Avg Hold | 3-8 days | 5.2 days* | — | — |

*Simulated results. Live performance may differ.

---

## Thesis

Combines dynamic PCA factor modeling, HMM regime detection, and macro scaling to exploit misspecifications in traditional statistical arbitrage. Factor loadings drift with volatility regimes; static models fail during crisis periods.

---

## Logic & Entry/Exit Rules

### Entry
```
IF residual_zscore > 1.5 AND hmm_p_mr > 0.7 AND sentiment_aligned:
    direction = SHORT (overbought residual)
ELSE IF residual_zscore < -1.5 AND hmm_p_mr > 0.7 AND sentiment_aligned:
    direction = LONG (oversold residual)
```

### Exit
```
IF |residual_zscore| < 0.3:
    exit_reason = "mean_reversion_complete"
ELSE IF hmm_p_mr < 0.3:
    exit_reason = "regime_change"
ELSE IF hold_days > 20:
    exit_reason = "max_hold"
ELSE IF |residual_zscore| > 3.0 (against position):
    exit_reason = "stop_loss"
```

---

## Risk Management

- **Position Sizing:** Kelly 0.25, max 2% risk per trade
- **Portfolio:** Beta-neutral (±0.1), dollar-neutral (±5%), sector-neutral
- **Hard Limits:** 3σ stop loss, 20-day max hold, $50M min volume

---

## JT Platform Integration

### Deployment Steps
1. Connect to `researcher` schema in RDS
2. Configure `DynamicFactorModel` with decay=0.94
3. Set HMM threshold at 0.7
4. Enable paper trading mode
5. Monitor for 30 days before live

### Code Location
- `/strategies/araso_factor_model.py`
- `/strategies/araso_signals.py`
- `/strategies/araso_backtest.py`

---

## Weekly Verification Checklist

- [ ] Live/Paper Sharpe vs backtest (±0.3 tolerance)
- [ ] Regime validity: VIX < 30, yield curve not inverted
- [ ] Capacity check: AUM < $300M
- [ ] Correlation drift: Check factor correlation stability
- [ ] HMM accuracy: P(MR) > 0.7 when mean-reversion actually occurs

---

## Status History

| Date | Status | Notes |
|------|--------|-------|
| 2026-02-16 | backtested | 5-year validation complete |
| 2026-02-?? | paper | [Pending deployment] |

---

*This strategy is ready for JT platform paper trading deployment.*
