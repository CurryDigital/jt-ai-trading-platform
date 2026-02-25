# Hypothesis: Quality Factor + Value Filter

**Status:** idea  
**Created:** 2026-02-19  
**Academic Basis:** Asness (2018), Fama-French (2015), Novy-Marx (2013)  
**Asset Class:** Equities  
**Direction:** Long  
**Horizon:** 6-18 months  
**Target Win Rate:** 60-65%

---

## Core Idea

Combine Quality (profitability, stability) with Value (cheap multiples) for "Quality at a Reasonable Price" (QARP). High-quality firms trade at premium, but when they become cheap (value + quality), they offer asymmetric upside.

**Academic Support:**
- **Asness et al. (2018):** "Quality Minus Junk" - Quality factor exists and is distinct from value
- **Novy-Marx (2013):** "The Other Side of Value" - Profitability (quality) predicts returns as well as value
- **Fama-French (2015):** Five-factor model adds profitability and investment (quality proxies)

---

## Quality Metrics (Asness 2018)

### 1. Profitability
```python
profitability = {
    "gross_profit_margin": gross_profit / revenue,
    "return_on_equity": net_income / equity,
    "return_on_assets": net_income / assets
}
```

### 2. Stability
```python
stability = {
    "earnings_volatility": std(earnings_growth, 5_years),
    "asset_growth_stability": std(asset_growth, 5_years)
}
```

### 3. Payout
```python
payout = {
    "dividend_yield": dividend / price,
    "buyback_yield": buybacks / market_cap,
    "total_payout": dividend_yield + buyback_yield
}
```

---

## Signal Construction

### Quality Score Calculation
```python
def quality_score(stock):
    """Asness (2018) quality components"""
    
    profitability_z = z_score(
        gross_profit_margin + ROE + ROA
    )
    
    stability_z = z_score(
        -earnings_volatility - asset_growth_volatility
    )
    
    payout_z = z_score(
        total_payout_yield
    )
    
    quality = (profitability_z + stability_z + payout_z) / 3
    return quality
```

### Value Score Calculation
```python
def value_score(stock):
    """Traditional value metrics"""
    
    pe_z = z_score(-P/E)
    pb_z = z_score(-P/B)
    ps_z = z_score(-P/S)
    
    value = (pe_z + pb_z + ps_z) / 3
    return value
```

### Combined QARP Signal
```python
# Quality at Reasonable Price
qarp_score = quality_score + value_score

# Entry: High quality + cheap valuation
IF qarp_score > 80th_percentile:
    AND quality_score > 60th_percentile:  # Must be decent quality
    AND value_score > 60th_percentile:    # Must be reasonably cheap
    
    LONG stock
    Hold 9-18 months
    Size: 3-4%
```

---

## Enhancement to AH Premium Arbitrage

**Apply Quality Filter to H-Share Selection:**

```python
# When selecting among AH pairs, prefer high-quality Chinese banks

quality_factors = {
    "NPL_ratio": non_performing_loans / total_loans,  # Lower = better
    "ROE": net_income / equity,
    "Tier1_capital_ratio": tier1_capital / risk_weighted_assets
}

# Rank AH pairs by quality
IF premium > 30%:  # Entry signal
    IF quality_score > median:  # High quality
        position_size = base_size * 1.3  # Larger position
    ELIF quality_score < 30th_percentile:  # Low quality
        position_size = base_size * 0.5  # Smaller position
```

---

## Enhancement to SG REIT Strategy

**Quality Filter for REIT Selection:**

```python
# REIT quality metrics
reit_quality = {
    "occupancy_rate": occupied_sqft / total_sqft,
    "debt_to_assets": total_debt / total_assets,
    "interest_coverage": EBIT / interest_expense,
    "dividend_coverage": FFO / dividends
}

# Only buy REITs passing quality threshold
IF quality_score > median:
    AND dividend_yield > 5%:  # Entry condition
    
    LONG REIT
```

---

## Expected Performance

| Component | Win Rate | Sharpe | Annual Return |
|-----------|----------|--------|---------------|
| Quality only (Asness 2018) | 55-58% | 0.9 | 8-12% |
| Value only (Fama-French) | 52-55% | 0.7 | 6-10% |
| **Quality + Value (QARP)** | **60-65%** | **1.1** | **12-18%** |

---

## Data Requirements

- **Financial statements:** Income statement, balance sheet (quarterly)
- **Calculation:** Profitability, stability, payout ratios
- **Sources:** Compustat, Bloomberg, or free (yfinance for US)

---

## Academic Citations

```bibtex
@article{asness2018quality,
  title={Quality minus junk},
  author={Asness, Cliff and others},
  journal={Review of Accounting Studies},
  year={2018}
}

@article{novymarx2013other,
  title={The other side of value: The gross profitability premium},
  author={Novy-Marx, Robert},
  journal={Journal of Financial Economics},
  year={2013}
}

@article{famafrench2015five,
  title={A five-factor asset pricing model},
  author={Fama, Eugene F and French, Kenneth R},
  journal={Journal of Financial Economics},
  year={2015}
}
```

---

*Quality companies at bargain prices.*
