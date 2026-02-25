# Hypothesis: Carry + Momentum + Value (CMV) Multi-Factor

**Status:** idea  
**Created:** 2026-02-19  
**Academic Basis:** Asness (2013), Koijen et al. (2018), Moskowitz et al. (2012)  
**Asset Class:** Multi-asset (FX, Bonds, Commodities, Equities)  
**Direction:** Long/Short  
**Horizon:** 1-12 months  
**Target Win Rate:** 60-65%

---

## Core Idea

Combine three robust factors across asset classes:
1. **Carry** - High yield / low yield (Brunnermeier et al. 2008)
2. **Momentum** - Past winners (Jegadeesh & Titman 1993)
3. **Value** - Cheap vs expensive (Fama-French 1993)

These factors are **negatively correlated** (-0.3 to -0.5), providing diversification. Combined portfolio has higher Sharpe than individual factors.

**Academic Support:**
- **Asness (2013):** "Value and Momentum Everywhere" - Both factors work across asset classes
- **Koijen et al. (2018):** "Carry" - Carry factor is distinct and additive
- **Moskowitz et al. (2012):** Time-series momentum complements cross-sectional

---

## Factor Definitions by Asset Class

### FX (Currency)
```python
fx_signals = {
    "carry": interest_rate_diff,  # Long high rate, short low rate
    "momentum": return_12m,        # Long appreciating, short depreciating
    "value": ppp_deviation         # Long undervalued (Big Mac index), short overvalued
}

# Example: Long AUD/JPY (carry), Long USD/CHF (momentum), Short EUR/USD (value)
```

### Bonds
```python
bond_signals = {
    "carry": yield_curve_slope,    # Long steep (higher carry), short flat
    "momentum": return_12m,        # Long outperforming bonds
    "value": real_yield_diff       # Long high real yield, short low
}

# Example: Long 10Y US (carry + value), Long 30Y JGB (momentum), Short 10Y EU (low carry)
```

### Commodities
```python
commodity_signals = {
    "carry": roll_yield,           # Long backwardation, short contango
    "momentum": return_12m,        # Long trending up
    "value": deviation_from_5y_avg # Long below average, short above
}

# Example: Long crude (backwardation + momentum), Short gold (contango)
```

### Equities (Enhancement to RSI Strategy)
```python
equity_signals = {
    "carry": dividend_yield + buyback_yield,
    "momentum": return_12m_excl_last_month,
    "value": composite_value_score(pe, pb, ps)
}

# Filter RSI signals through CMV lens
IF RSI < 30:  # Oversold
    IF carry_score > 0 AND momentum_score > 0 AND value_score > 0:
        # Triple confirmation - maximum conviction
        position_size = base_size * 1.5
    ELIF sum([carry, momentum, value]) > 1:  # At least 2 positive
        position_size = base_size
    ELSE:
        position_size = base_size * 0.5  # Weak fundamental support
```

---

## Portfolio Construction

### Equal Risk Contribution
```python
# Target 10% annualized volatility per factor
factor_vol = {
    "carry": 0.10,
    "momentum": 0.10,
    "value": 0.10
}

# Position sizes inversely proportional to realized volatility
carry_size = target_vol / realized_vol_carry
momentum_size = target_vol / realized_vol_momentum
value_size = target_vol / realized_vol_value

# Equal risk contribution (not equal dollar)
allocation = {
    "carry": 0.33,
    "momentum": 0.33,
    "value": 0.33
}
```

### Cross-Asset Diversification
```python
# Correlation between factors is low (0.0 to 0.3)
# Build multi-asset portfolio

assets = {
    "FX": 0.25,        # 8 major pairs
    "Bonds": 0.25,     # 10Y US, EU, JP, UK, AU
    "Commodities": 0.25,  # Oil, gold, copper, wheat
    "Equities": 0.25   # US, EU, JP, EM
}

# Within each asset class, apply CMV signal
```

---

## Enhancement to Existing Strategies

### RSI Mean Reversion + CMV Filter
```python
# Original: RSI < 30 → Long
# Enhanced: RSI < 30 + CMV confirmation → Long

IF RSI < 30:
    # Score the stock on CMV
    carry_score = percentile(dividend_yield, 90)  # High yield
    momentum_score = return_12m  # Positive trend
    value_score = -P/E  # Low PE
    
    cmv_score = (carry_score + momentum_score + value_score) / 3
    
    IF cmv_score > 0.6:  # Strong CMV characteristics
        position_size = base_size * 1.3
        hold_period = 7_days  # Longer hold
    ELIF cmv_score > 0.4:
        position_size = base_size
        hold_period = 5_days
    ELSE:
        SKIP  # Skip weak fundamentals
```

### AH Premium + Carry Enhancement
```python
# H-shares offer implicit carry: higher dividend yield than A-shares

ah_carry = dividend_yield_H - dividend_yield_A

IF premium > 30%:  # Entry signal
    IF ah_carry > 1%:  # H-shares yield 1%+ more
        # Double benefit: premium convergence + carry
        position_size = base_size * 1.4
        expected_return += ah_carry  # Add carry to expected return
```

---

## Expected Performance

| Factor | Standalone Sharpe | Correlation to Others |
|--------|-------------------|----------------------|
| Carry | 0.6-0.8 | -0.4 to momentum |
| Momentum | 0.8-1.0 | -0.3 to value |
| Value | 0.5-0.7 | -0.2 to carry |
| **Combined CMV** | **1.2-1.5** | Diversified |

### Historical Performance (Asness 2013)
- **Value + Momentum:** Sharpe 1.1 (vs 0.8 momentum, 0.6 value alone)
- **Adding Carry:** Sharpe 1.3-1.5

---

## Data Requirements

- **FX:** Interest rates (central bank), spot prices
- **Bonds:** Yield curves, sovereign yields
- **Commodities:** Futures curves (backwardation/contango), spot prices
- **Equities:** Dividends, buybacks, multiples, prices

---

## Academic Citations

```bibtex
@article{asness2013value,
  title={The value and momentum everywhere},
  author={Asness, Cliff and others},
  journal={Journal of Finance},
  year={2013}
}

@article{brunnermeier2008carry,
  title={Carry trades and currency crashes},
  author={Brunnermeier, Markus K and others},
  journal={NBER Macroeconomics Annual},
  year={2008}
}

@article{koijen2018carry,
  title={Carry},
  author={Koijen, Ralph SJ and others},
  journal={Journal of Financial Economics},
  year={2018}
}

@article{moskowitz2012time,
  title={Time series momentum},
  author={Moskowitz, Tobias J and Ooi, Yao Hua and Pedersen, Lasse Heje},
  journal={Journal of Financial Economics},
  year={2012}
}
```

---

*Three factors, one portfolio, superior risk-adjusted returns.*
