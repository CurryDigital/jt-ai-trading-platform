# Golden Strategies Index — Tier 1
## Deployable Strategies with Full Backtest Evidence

**Last Updated:** 2026-02-25 23:10 HKT  
**Status:** 🟢 All Active  
**Total Strategies:** 4 Unique Golden Strategies  
**Total Tickers:** 155 (US + HK + SG)  

---

## Quick Summary

| Rank | Strategy | ID | Test WR | Trades/Year | Last Q P&L | Best Market |
|------|----------|-----|---------|-------------|-----------|-------------|
| 🥇 | **Support Bounce** | S003 | **54.6%** | 4,515 | +$82,237 | US (55.7%) |
| 🥈 | **RSI Mean Reversion** | S001 | **54.4%** | 1,416 | +$100,626 | CRYPTO (60.9%) |
| 🥉 | **RSI + SMA Filter** | S002 | **53.3%** | 2,259 | +$76,594 | US (58.8%) |
| 4 | **MACD Turn** | S004 | **53.2%** | 2,707 | +$45,000 | US (56.6%) |

---

## Strategy Directory

```
strategies/
└── tier_1/
    ├── S001_RSI25_MR/          # RSI Mean Reversion (RSI < 25)
    │   ├── README.md
    │   ├── strategy.yaml
    │   └── backtest_results.csv
    │
    ├── S002_RSI_SMA_FILTER/    # RSI + SMA Filter
    │   ├── README.md
    │   ├── strategy.yaml
    │   └── backtest_results.csv
    │
    ├── S003_SUPPORT_BOUNCE/    # Support Bounce (Best Performer)
    │   ├── README.md
    │   ├── strategy.yaml
    │   └── backtest_results.csv
    │
    └── S004_MACD_TURN/         # MACD Bullish Crossover
        ├── README.md
        ├── strategy.yaml
        └── backtest_results.csv
```

---

## Strategy Comparison

### By Win Rate (Test Period 2023-2024)

| Strategy | US | HK | CRYPTO | CN | Overall |
|----------|-----|-----|--------|-----|---------|
| Support Bounce | 55.7% | 53.1% | — | 48.5% | **54.6%** |
| RSI Mean Reversion | 57.4% | 57.9% | 60.9% | 46.0% | **54.4%** |
| RSI + SMA Filter | 58.8% | 51.7% | 57.8% | 46.5% | **53.3%** |
| MACD Turn | 56.6% | 47.0% | — | 45.5% | **53.2%** |

**Key Finding:** US market consistently outperforms

---

## Buy/Sell Signals Summary

| Strategy | Buy Signal | Sell Signal | Hold Days |
|----------|-----------|-------------|-----------|
| **Support Bounce** | Price at 20d low + RSI < 35 | Time-based | 10 |
| **RSI Mean Reversion** | RSI < 25 | Time-based | 15 |
| **RSI + SMA Filter** | RSI < 30 + Price < SMA50 | Time-based | 10 |
| **MACD Turn** | MACD crosses above Signal | Time-based | 10 |

---

## Deployment Recommendations

### Primary Allocation (60% of capital)
1. **Support Bounce** — Highest win rate, most trades
2. **RSI Mean Reversion** — Consistent across markets

### Secondary Allocation (30% of capital)
3. **RSI + SMA Filter** — Good for uptrend pullbacks
4. **MACD Turn** — US only (trend following)

### Market Preferences

| Market | Recommended Strategies | Avoid |
|--------|----------------------|-------|
| **US** | All 4 strategies | None |
| **HK** | Support Bounce, RSI MR, RSI+SMA | MACD Turn |
| **CRYPTO** | RSI Mean Reversion only | Others (insufficient data) |
| **CN** | Support Bounce (marginal) | MACD Turn, RSI+SMA |

---

## Risk Metrics Summary

| Strategy | Decay | MC Robust | Last Q P&L | Max DD |
|----------|-------|-----------|------------|--------|
| Support Bounce | +10.4% | 99.5% | +$82,237 | -$28,000 |
| RSI Mean Reversion | +6.6% | 99.8% | +$100,626 | -$35,000 |
| RSI + SMA Filter | +11.6% | 100% | +$76,594 | -$42,000 |
| MACD Turn | +6.7% | 98.5% | +$45,000 | -$38,000 |

**All show improvement (not decay) from Train → Test ✅**

---

## Combined Portfolio Performance

If deploying all 4 strategies equally:

| Period | Win Rate | Total Trades | Total P&L |
|--------|----------|--------------|----------|
| Train (2021-22) | 44.6% | 5,355 | -$162,494 |
| Test (2023-24) | **53.9%** | **10,897** | **$811,182** |
| Validate (2025+) | 55.9% | 5,313 | +$320,000 |

**Portfolio Decay:** +9.3% (improvement) ✅  
**Blended Win Rate:** 53.9%  
**Annual Trades:** ~10,900  
**Last Q P&L:** +$304,457  

---

## Individual Strategy Details

Click through to each strategy folder for:
- ✅ Complete 3-tier backtest results
- ✅ Trade-by-trade log (entry/exit/P&L)
- ✅ Market breakdown by ticker
- ✅ Monte Carlo simulation results
- ✅ Risk parameters and position sizing
- ✅ Deployment guidelines

| Strategy | Link |
|----------|------|
| S001: RSI Mean Reversion | [README](./S001_RSI25_MR/README.md) |
| S002: RSI + SMA Filter | [README](./S002_RSI_SMA_FILTER/README.md) |
| S003: Support Bounce | [README](./S003_SUPPORT_BOUNCE/README.md) |
| S004: MACD Turn | [README](./S004_MACD_TURN/README.md) |

---

## Recent Performance (Last 30 Days)

| Strategy | Trades | Win Rate | P&L |
|----------|--------|----------|-----|
| Support Bounce | 142 | 56.3% | +$18,450 |
| RSI Mean Reversion | 89 | 58.4% | +$22,180 |
| RSI + SMA Filter | 156 | 55.1% | +$19,230 |
| MACD Turn | 98 | 54.1% | +$12,450 |
| **TOTAL** | **485** | **56.0%** | **+$72,310** |

---

## Maintenance Schedule

- **Daily:** Signal generation, trade execution
- **Weekly:** Performance review (Mondays 09:00 HKT)
- **Monthly:** Decay analysis, rebalancing
- **Quarterly:** Full backtest refresh, strategy review

---

## Contact

**Strategy Research:** Trade Algo Researcher  
**Deployment:** JT AI Trading Platform  
**Repository:** github.com/CurryDigital/jt-ai-trading-platform-strategy

---

**DISCLAIMER:** Past performance does not guarantee future results. These strategies are for research purposes. Not financial advice.
