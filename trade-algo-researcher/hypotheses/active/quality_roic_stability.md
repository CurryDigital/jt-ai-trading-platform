# Hypothesis: Quality Factor (ROIC Stability)

**Status:** testing  
**Created:** 2026-02-18  
**Asset Class:** Equities  
**Direction:** Long  
**Horizon:** 3-5 years  
**Target Win Rate:** 70-80%

---

## Core Idea

High-quality companies (stable ROIC, low leverage, consistent margins) outperform junk over long periods. Quality provides downside protection and compound growth. "Quality minus Junk" factor generates 3-5% annual alpha.

**The Edge:**
- ROIC stability = durable competitive advantage
- Low leverage = survival in recessions
- Consistent margins = pricing power
- Market underprays quality during bubbles

---

## Signal Construction

**Quality Metrics:**
```python
# Profitability
roic = nopat / invested_capital  # Return on invested capital
roe = net_income / equity
roa = net_income / assets

# Stability
gross_margin_std = std_dev(gross_margin, 5y)  # Lower = better
roic_stability = std_dev(roic, 5y)  # Lower = better
earnings_consistency = years_of_positive_eps / total_years

# Balance sheet strength
leverage = total_debt / ebitda  # < 3x preferred
current_ratio = current_assets / current_liabilities  # > 1.5
interest_coverage = ebitda / interest_expense  # > 5x

# Cash flow
fcf_conversion = fcf / net_income  # > 0.8 = quality earnings
```

**Composite Quality Score (Asness et al.):**
```python
quality_score = (
    profitability_percentile * 0.3 +
    stability_percentile * 0.25 +
    growth_percentile * 0.15 +
    safety_percentile * 0.15 +
    payout_percentile * 0.15
)

# Top 30 by quality_score
# Hold 3-5 years
# Rebalance annually
```

---

## Expected Performance

| Metric | Quality | Junk | Difference |
|--------|---------|------|------------|
| Annual return | 12% | 6% | +6% |
| Volatility | 14% | 25% | -11pp |
| Sharpe | 0.85 | 0.25 | +0.6 |
| Max DD | 20% | 50% | Much safer |
| Down capture | 70% | 120% | Protects in crashes |

**Academic finding:** Quality factor generates 3-5% annual alpha (Asness et al. 2019).

---

## Universe

**Quality company characteristics:**
- Market cap > $5B
- 10+ years of positive earnings
- ROIC > 12% consistently
- Debt/EBITDA < 2.5x

**Examples:**
- **Consumer staples:** PG, KO, PEP (pricing power)
- **Industrials:** UNP, UPS, CNI (network effects)
- **Tech:** MSFT, V, MA (platform moats)
- **Healthcare:** JNJ, ABT, SYK (defensive)

---

## Academic Support

- Piotroski (2000): F-Score (fundamental health)
- Novy-Marx (2013): Other people's money (gross profitability)
- Asness et al. (2019): Quality minus junk
- Fama-French (2015): Profitability factor
- Kozak et al. (2018): Interpreting factor models

---

## Data Requirements

- **Financial history:** 10+ years (Compustat)
- **Quality metrics:** ROIC, ROE, margin stability
- **Balance sheet:** Debt, cash, working capital
- **Real-time:** Prices for factor construction
- **Sources:** Compustat, Bloomberg, MSCI Quality indices

---

## Risk Factors

1. **Value trap** - Quality at any price = overvaluation
2. **Growth vs value cycles** - Quality underperforms in bubble frenzies
3. **Disruption** - Quality incumbents killed by innovation
4. **Mean reversion** - ROIC tends toward cost of capital over time

---

## Implementation

**Screening:** Annually (full year results)
**Entry:** 2-4% positions in top 25 quality names
**Hold:** 3-5 years (minimum)
**Rebalance:** Annually unless quality deteriorates

**Quality deterioration signals:**
- ROIC drops below 10% for 2 quarters
- Leverage increases > 4x Debt/EBITDA
- Margin compression trend

**Advanced:**
- Combine quality + value (Piotroski F-Score)
- Quality + momentum (quality at reasonable price)
- Quality + low vol (defensive compounders)

---

*Quality is the ultimate long-term edge.*
