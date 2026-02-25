# Hypothesis: Time-Series Momentum (Trend Following) Overlay

**Status:** idea  
**Created:** 2026-02-19  
**Academic Basis:** Hurst, Ooi, & Pedersen (2017), Moskowitz, Ooi, & Pedersen (2012)  
**Asset Class:** Multi-asset (Equities, Bonds, Commodities, FX)  
**Direction:** Long/Short  
**Horizon:** 1-12 months  
**Target Win Rate:** 55-60%

---

## Core Idea

Add a **time-series momentum overlay** to existing strategies. Unlike cross-sectional momentum (buy winners vs losers), time-series momentum bets on assets' own past returns (buy if positive trend, short if negative trend). Works across all asset classes and provides crisis alpha.

**Academic Support:**
- **Moskowitz, Ooi, & Pedersen (2012):** "Time Series Momentum" - Trend following works in every asset class
- **Hurst, Ooi, & Pedersen (2017):** "A Century of Evidence on Trend-Following Investing" - 100+ years of positive returns
- **Asness (2013):** "Value and Momentum Everywhere" - Momentum is universal

---

## The Time-Series Momentum Signal

```python
# Hurst et al. (2017) approach
def time_series_momentum_signal(returns, lookback_months=12):
    """
    Returns excess return over risk-free rate for past 12 months
    Positive = Long, Negative = Short
    """
    excess_return = mean(returns[-lookback_months:]) - risk_free_rate
    
    # Exponentially weighted (recent months matter more)
    weights = exponential_weights(lookback_months, half_life=6)
    weighted_return = sum(returns[-lookback_months:] * weights) - risk_free_rate
    
    return weighted_return

# Position sizing based on volatility (risk parity)
position_size = target_volatility / realized_volatility(returns, 63_days)
```

---

## Signal Construction

### 1. Trend Strength Scoring
```python
# Multiple timeframes (1m, 3m, 6m, 12m)
trend_score = (
    0.4 * sign(return_12m) +
    0.3 * sign(return_6m) +
    0.2 * sign(return_3m) +
    0.1 * sign(return_1m)
)

# -1.0 = strong downtrend across all timeframes
# +1.0 = strong uptrend across all timeframes
```

### 2. Volatility-Adjusted Position Sizing
```python
# Target 10% annualized volatility per position
realized_vol = std(returns, 63) * sqrt(252)  # Annualized
target_vol = 0.10

# Position inversely proportional to volatility
position_size = target_vol / realized_vol

# Example: If stock has 20% vol, position = 0.10/0.20 = 50% of base size
# Example: If stock has 5% vol, position = 0.10/0.05 = 200% of base size
```

### 3. Risk-Off Filter (Crisis Alpha)
```python
# During high correlation periods (crisis), trend following works best
correlation_spike = correlation_stocks > 0.8
volatility_spike = VIX > 30

IF correlation_spike OR volatility_spike:
    # Increase trend following allocation
    trend_weight = 0.60  # Up from 0.40
ELSE:
    trend_weight = 0.40
```

---

## Enhancement to RSI Mean Reversion Strategy

**Problem:** RSI mean reversion fails in strong trends (catches falling knives).

**Solution:** Add trend filter - only take RSI signals in direction of trend.

```python
# ENHANCED RSI with Trend Overlay
IF RSI < 30:  # Oversold signal
    
    IF time_series_momentum > 0:  # BUT in uptrend
        # Bull market pullback - safe to buy
        position_size = base_size * 1.2
        confidence = "high"
        
    ELIF time_series_momentum < -0.5:  # In strong downtrend
        # Bear market - skip or short
        position_size = 0  # Skip
        OR short_stock  # Alternative: trend following
        
    ELSE:  # Neutral trend
        position_size = base_size * 0.8
        confidence = "medium"
```

---

## Enhancement to AH Premium Arbitrage

**Trend Overlay for Currency Hedging:**

```python
# When trading AH premium, hedge HKD/CNY exposure with trend signal
IF HKD_CNY_trend > 0:  # HKD strengthening vs CNY
    # Favors H-shares (denominated in HKD)
    increase_H_share_allocation()
    
ELIF HKD_CNY_trend < 0:  # HKD weakening
    # Reduce exposure or hedge
    decrease_H_share_allocation()
```

---

## Expected Performance

| Component | CAGR | Sharpe | Max DD | Crisis Alpha |
|-----------|------|--------|--------|--------------|
| Time-Series Momentum (standalone) | 10-15% | 1.0 | -15% | Yes |
| RSI Mean Reversion (standalone) | 15-20% | 1.2 | -12% | No |
| **Combined (RSI + Trend Filter)** | **18-25%** | **1.4** | **-10%** | **Partial** |

---

## Implementation

### Asset Allocation Overlay
```python
# Apply trend following as portfolio overlay
base_allocation = {
    "RSI_MeanReversion": 0.40,
    "AH_Premium": 0.20,
    "SG_REIT": 0.15,
    "ARASO": 0.25
}

# Adjust based on equity trend
equity_trend = time_series_momentum(SPY, 12_months)

IF equity_trend < -0.2:  # Strong downtrend
    # Reduce equity exposure
    allocation["RSI_MeanReversion"] *= 0.5
    allocation["AH_Premium"] *= 0.5
    
    # Increase trend following (short equity)
    allocation["Trend_Following_Short"] = 0.30
```

---

## Data Requirements

- Price data: 12+ months for all assets
- Volatility: 3-month realized vol
- Risk-free rate: T-bill yields
- VIX: For risk-off detection

---

## Academic Citations

```bibtex
@article{moskowitz2012time,
  title={Time series momentum},
  author={Moskowitz, Tobias J and Ooi, Yao Hua and Pedersen, Lasse Heje},
  journal={Journal of Financial Economics},
  year={2012}
}

@article{hurst2017century,
  title={A century of evidence on trend-following investing},
  author={Hurst, Brian and Ooi, Yao Hua and Pedersen, Lasse Heje},
  journal={Journal of Portfolio Management},
  year={2017}
}

@article{asness2013value,
  title={The value and momentum everywhere},
  author={Asness, Cliff and others},
  journal={Journal of Finance},
  year={2013}
}
```

---

*Ride the trends, avoid the crashes.*
