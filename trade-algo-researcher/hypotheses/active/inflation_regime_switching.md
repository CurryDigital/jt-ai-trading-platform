# Hypothesis: Inflation Regime Switching

**Status:** idea  
**Created:** 2026-02-19  
**Source:** Post-2021 inflation research (transitory vs persistent debate)  
**Asset Class:** Multi-asset (Stocks, Bonds, Commodities)  
**Direction:** Regime-dependent  
**Horizon:** 3-6 months  
**Target Win Rate:** 60-70%

---

## Core Idea

Markets exhibit distinct regimes: inflationary (commodities win, bonds lose) vs disinflationary (tech wins, commodities lose). Machine learning classifiers predict regime switches using:
- CPI/PCE trends
- Wage growth
- Supply chain pressure index
- Inflation expectations (breakevens)

**Academic Support:**
- Reis (2022): "Losing the Inflation Anchor"
- Blanchard (2023): "Why I was wrong about inflation"
- Cieslak (2023): "Inflation and Asset Returns"

---

## Signal Construction

**Regime Detection:**
```python
IF CPI_3m_change > 0.5% AND wage_growth > 4%:
    regime = "inflationary"
    Long: Commodities (GLD, USO), Short: Long-duration bonds
    
ELIF CPI_3m_change < 0.2% AND wage_growth < 3%:
    regime = "disinflationary"
    Long: Tech (QQQ), Long-duration bonds
    
ELSE:
    regime = "neutral"
    Balanced portfolio
```

**Rotation Timing:**
- Enter when 3-month CPI trend changes direction
- Hold until regime flips

---

## Expected Performance

| Regime | Winners | Losers |
|--------|---------|--------|
| Inflation | Commodities, REITs, Value | Bonds, Tech, Growth |
| Disinflation | Tech, Bonds, Growth | Commodities, REITs |

| Metric | Target |
|--------|--------|
| Regime Prediction Accuracy | 70-75% |
| Sharpe | 1.0-1.3 |
| Max DD | -12% |

---

## Data Requirements

- **CPI/PCE:** Monthly (BLS)
- **Wage data:** Atlanta Fed Wage Tracker
- **Supply chain:** NY Fed Global Supply Chain Pressure Index
- **Inflation expectations:** 5Y5Y breakevens

---

*Ride the inflation waves.*
