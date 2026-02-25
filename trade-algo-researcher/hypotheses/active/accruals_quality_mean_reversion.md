# Hypothesis: Accruals Quality + Mean Reversion

**Status:** idea  
**Created:** 2026-02-19  
**Academic Basis:** Sloan (1996), Richardson et al. (2005)  
**Asset Class:** Equities  
**Direction:** Long/Short  
**Horizon:** 6-12 months  
**Target Win Rate:** 60-65%

---

## Core Idea

Combine Sloan's (1996) accruals anomaly with RSI mean reversion. High accrual firms (low earnings quality) that are also technically oversold (RSI < 30) have a "double edge":
1. **Fundamental edge:** Accruals mean-revert (Sloan)
2. **Technical edge:** RSI oversold bounce

**Academic Support:**
- **Sloan (1996):** "Do Stock Prices Fully Reflect Information in Accruals and Cash Flows About Future Earnings?" - High accrual firms have lower future returns
- **Richardson et al. (2005):** Decomposition of accruals into reliable/unreliable components
- **Shleifer & Vishny (1997):** Limits to arbitrage prevent full correction

---

## The Accruals Anomaly

**Sloan's Finding:**
- Earnings = Cash Flow + Accruals
- Accruals are less persistent than cash flows
- Investors overestimate persistence of accruals
- High accrual firms → lower future returns (mean reversion)
- Low accrual firms → higher future returns

**Calculation:**
```python
accruals = (ΔCurrentAssets - ΔCash) 
         - (ΔCurrentLiabilities - ΔDebt) 
         - Depreciation

accrual_ratio = accruals / average_total_assets
```

---

## Signal Construction

### Entry: High Accrual + RSI Oversold (Contrarian Long)
```python
# Step 1: Identify high accrual firms
accrual_percentile = percentile(accrual_ratio, 90)  # Top 10% = highest accruals

# Step 2: Check for technical oversold
IF accrual_ratio > accrual_percentile:  # High accruals (Sloan short signal)
    AND RSI(14) < 30:  # BUT technically oversold
    AND price < 50_day_MA:  # In downtrend
    
    # Paradox: High accruals predict lower returns, BUT extreme oversold may bounce
    # This captures "oversold high-accrual" mean reversion
    
    LONG position (contrarian)
    Hold 3-6 months
    Size: 2-3%
```

### Entry: Low Accrual + Momentum (Trend Following Long)
```python
# Step 1: Identify low accrual firms
IF accrual_ratio < percentile(accrual_ratio, 20):  # Bottom 20% = lowest accruals
    AND return_12m > percentile(return_12m, 80):  # Price momentum
    AND earnings_surprise > 0:  # Fundamental momentum
    
    # High quality (low accruals) + momentum = best of both worlds
    LONG position
    Hold 6-12 months
    Size: 3-4%
```

---

## Enhanced RSI Strategy Integration

This **enhances** the existing RSI Mean Reversion deployment:

**Original:** RSI < 30 → Long  
**Enhanced:** RSI < 30 + Accrual Quality Filter → Long

```python
# ENHANCED RSI ENTRY
IF RSI < 30:
    IF accrual_ratio < median:  # Low accruals = high quality
        position_size = base_size * 1.5  # Increase size
        confidence = "high"
    ELIF accrual_ratio > 80th_percentile:  # High accruals = risky
        position_size = base_size * 0.5  # Reduce size
        confidence = "low"
    ELSE:
        position_size = base_size  # Normal size
        confidence = "medium"
```

---

## Expected Performance

| Component | Win Rate | Sharpe | Annual Return |
|-----------|----------|--------|---------------|
| RSI alone (baseline) | 60-63% | 1.2 | 15-20% |
| RSI + Accruals filter | 62-66% | 1.4 | 18-24% |
| Improvement | +2-3% | +0.2 | +20% |

---

## Data Requirements

- **Financial statements:** Balance sheet, income statement (quarterly)
- **Calculation:** Accruals from cash flow statement
- **Sources:** Compustat, Bloomberg, or free alternative (calculated from yfinance)

**Free Alternative:**
```python
# Approximation using yfinance data
accruals_approx = (net_income - operating_cash_flow) / total_assets
```

---

## Why It Works (Academic Rationale)

1. **Sloan (1996):** Accruals predict earnings persistence
2. **Shleifer & Vishny (1997):** Limits to arbitrage prevent immediate correction
3. **Richardson et al. (2005):** Not all accruals equal - working capital vs. long-term
4. **Hong & Stein (1999):** Gradual information diffusion causes drift

---

## Academic Citations

```bibtex
@article{sloan1996stock,
  title={Do stock prices fully reflect information in accruals and cash flows about future earnings?},
  author={Sloan, Richard G},
  journal={Accounting Review},
  year={1996}
}

@article{shleifer1997limits,
  title={The limits of arbitrage},
  author={Shleifer, Andrei and Vishny, Robert W},
  journal={Journal of Finance},
  year={1997}
}

@article{richardson2005accrual,
  title={Accrual reliability, earnings persistence and stock prices},
  author={Richardson, Scott A and others},
  journal={Journal of Accounting and Economics},
  year={2005}
}
```

---

*Fundamental quality meets technical timing.*
