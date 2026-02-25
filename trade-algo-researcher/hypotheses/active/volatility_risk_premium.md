# Hypothesis: Volatility Risk Premium Harvesting

**Status:** idea  
**Created:** 2026-02-19  
**Academic Basis:** Coval & Shumway (2001), AQR VRP Research, Carr & Wu (2009)  
**Asset Class:** Options / Equities (via proxy)  
**Direction:** Short volatility (via proxy)  
**Horizon:** 1-3 months  
**Target Win Rate:** 65-75%

---

## Core Idea

Sell volatility (via proxy strategies) to capture the volatility risk premium - the excess return earned by selling options/insurance against market declines. Implied volatility consistently overestimates realized volatility by 2-4% annually.

**Academic Support:**
- **Coval & Shumway (2001):** "Expected Option Returns" - Zero-beta straddles earn negative returns (selling volatility wins)
- **Carr & Wu (2009):** "Variance Risk Premiums" - Variance swaps embed risk premium
- **AQR (2018):** "Understanding the Volatility Risk Premium" - Systematic excess returns from selling volatility

**Volatility Risk Premium Formula:**
```
VRP = Implied Volatility - Expected Realized Volatility > 0 (on average)
```

---

## The Problem (For Our Setup)

We don't have options data for direct VRP harvesting. **Solution:** Create proxy strategies using equities.

---

## Proxy Strategy 1: Short Volatility via Low-Vol Equities

```python
# Low volatility stocks embed short volatility exposure
# These stocks are "selling insurance" via their stable business models

universe = large_cap_stocks  # S&P 500 constituents

# Calculate realized volatility
realized_vol_1m = std(returns, 21_days)

# ENTRY: Lowest volatility decile
IF realized_vol_1m < percentile(realized_vol_1m, 10):
    AND RSI > 40:  # Not oversold (avoid value trap)
    AND earnings_surprise > -0.05:  # No major negative surprise
    
    LONG stock
    # These are the "sellers" of volatility
    Hold 1-3 months
```

**Rationale:** Low vol stocks attract capital from volatility-selling strategies, creating persistent premium.

---

## Proxy Strategy 2: VIX Contango Roll Yield

```python
# When VIX futures are in contango (front < back month)
# Short VIX ETFs earn roll yield

IF VIX_term_structure > 0:  # Contango
    AND VIX > 20:  # Elevated vol = higher premium
    
    SHORT VIXY (long VIX ETF)  # OR
    LONG SVXY (inverse VIX ETF)
    
    # Capture daily roll yield as futures converge to spot
    Hold until VIX drops below 15 OR term structure flips
```

**Note:** VXX delisted in 2024 - need SVXY or VIX futures directly.

---

## Proxy Strategy 3: Earnings Volatility Collapse

```python
# After earnings, implied volatility collapses (vol crush)
# Sell pre-earnings, buy back post-earnings (proxy via equities)

# Pre-earnings (1 week before)
IF days_to_earnings <= 7:
    AND implied_vol_spike > 30%:  # IV elevated
    AND historical_earnings_move < 5%:  # Usually quiet
    
    # Proxy: Buy the stock (selling put-like exposure)
    LONG stock
    
# Post-earnings (day after)
IF earnings_just_announced:
    IF return > 0:  # Positive surprise
        HOLD  # Let post-earnings drift work
    ELSE:
        SELL  # Cut loss
```

---

## Enhancement to RSI Mean Reversion

**Volatility-Adjusted RSI Thresholds:**

```python
# Standard RSI uses fixed thresholds (30/70)
# Enhanced: Dynamic thresholds based on volatility regime

IF VIX < 15:  # Low vol regime
    rsi_oversold = 25  # Harder to trigger
    rsi_overbought = 75
    
ELIF VIX > 30:  # High vol regime  
    rsi_oversold = 35  # Easier to trigger
    rsi_overbought = 65
    
ELSE:  # Normal
    rsi_oversold = 30
    rsi_overbought = 70

# Reason: In high vol, oversold is more common but less meaningful
```

---

## Expected Performance

| Strategy | Win Rate | Annual Return | Sharpe | Notes |
|----------|----------|---------------|--------|-------|
| Low-vol equity proxy | 60-65% | 8-12% | 1.0 | Defensive |
| VIX contango | 55-60% | 15-25% | 0.9 | Crash risk |
| Earnings vol crush | 60-70% | 10-18% | 1.2 | Event-driven |
| **Combined overlay** | **60-65%** | **12-18%** | **1.1** | Diversified |

---

## Risk Management

**Volatility selling is "picking up pennies in front of a steamroller":**

```python
# Position sizing based on volatility regime
IF VIX > 40:  # Extreme fear
    # Reduce vol selling exposure
    vrp_allocation = base_allocation * 0.3
    
ELIF VIX > 30:  # Elevated
    vrp_allocation = base_allocation * 0.6
    
ELSE:  # Normal
    vrp_allocation = base_allocation

# Hard stop: If VIX spikes 50% in 1 week, exit all VRP positions
```

---

## Data Requirements

- **VIX spot and futures:** Free from CBOE (delayed)
- **Options implied vol:** Need options chain data ($$$)
- **Alternative:** Use earnings calendar + historical vol

---

## Academic Citations

```bibtex
@article{coval2001expected,
  title={Expected option returns},
  author={Coval, Joshua D and Shumway, Tyler},
  journal={Journal of Finance},
  year={2001}
}

@article{carr2009variance,
  title={Variance risk premiums},
  author={Carr, Peter and Wu, Liuren},
  journal={Review of Financial Studies},
  year={2009}
}

@techreport{aqr2018vrp,
  title={Understanding the Volatility Risk Premium},
  institution={AQR Capital Management},
  year={2018}
}
```

---

*Sell insurance, manage the tail risk.*
