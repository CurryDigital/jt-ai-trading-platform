# Hypothesis: Cross-Sectional Momentum + Reversal Combo

**Status:** idea  
**Created:** 2026-02-19  
**Academic Basis:** Jegadeesh & Titman (1993, 2001), Hong & Stein (1999), Asness (2013)  
**Asset Class:** Equities  
**Direction:** Long/Short  
**Horizon:** 1-12 months (staged)  
**Target Win Rate:** 65-70%

---

## Core Idea

Combine SHORT-TERM reversal (1 month) with MEDIUM-TERM momentum (3-12 months) and LONG-TERM reversal (3-5 years) - the "momentum lifecycle" documented by Jegadeesh & Titman and Asness.

**Academic Support:**
- **Jegadeesh & Titman (1993):** "Returns to Buying Winners and Selling Losers" - 12-month momentum works
- **Jegadeesh & Titman (2001):** Momentum profits persist beyond 1990s sample
- **Hong & Stein (1999):** "A Unified Theory of Underreaction" - gradual information diffusion explains momentum
- **Asness (2013):** "Value and Momentum Everywhere" - combination of value + momentum optimal

---

## The Momentum Lifecycle

```
Month 0:     Earnings surprise / news
Months 1-3:  Short-term reversal (overreaction correction)
Months 3-12: Medium-term momentum (gradual information diffusion)
Years 1-3:   Continuation
Years 3-5:   Long-term reversal (mean reversion)
```

---

## Signal Construction

### Stage 1: Short-Term Reversal (1-3 months)
```python
# Recent losers bounce back
IF return_1m < -10%:  # Extreme short-term loser
    AND volume > 1.5x_average:  # Capitulation volume
    AND short_interest_high:  # Short squeeze potential
    
    LONG position (1-3 month hold)
    Size: 2% per stock
```

### Stage 2: Medium-Term Momentum (3-12 months) 
```python
# Past 12-month winners continue (excluding last month)
past_12m_return = return_12m - return_1m  # Skip most recent month

IF past_12m_return > 80th_percentile:
    AND return_1m > -5%:  # Not in short-term freefall
    AND earnings_surprise > 0:  # Fundamental support
    
    LONG position (3-6 month hold)
    Size: 2% per stock
```

### Stage 3: Long-Term Reversal (3-5 years)
```python
# 5-year losers become value plays
IF return_5y < 20th_percentile:  # Long-term loser
    AND P/E < industry_median:  # Value characteristic
    AND earnings_trend_improving:  # Turnaround signal
    
    LONG position (12-24 month hold)
    Size: 1-2% per stock
```

---

## Integrated Portfolio Construction

```python
# Allocate across momentum lifecycle stages
portfolio = {
    "short_term_reversal": 30%,  # 1-3 month holds
    "medium_term_momentum": 50%,  # 3-12 month holds  
    "long_term_reversal": 20%,    # 12-24 month holds
}

# Rebalance monthly
# Each stage has independent exit rules
```

---

## Expected Performance

| Component | Win Rate | Avg Return | Sharpe |
|-----------|----------|------------|--------|
| Short-term reversal | 58-62% | 3-5% | 1.2 |
| Medium-term momentum | 60-65% | 8-15% | 1.0 |
| Long-term reversal | 55-60% | 15-25% | 0.8 |
| **Combined** | **60-65%** | **10-18%** | **1.1** |

---

## Enhancement to RSI Mean Reversion Strategy

This hypothesis **enhances** the existing RSI Mean Reversion deployment by:
1. Adding **time dimension** (not just entry signal, but lifecycle stage)
2. Combining with **momentum** (not just mean reversion)
3. Using **earnings surprise** as confirmation (Ball & Brown PEAD)

---

## Data Requirements

- Price data: 5 years history
- Earnings surprise data (IBES/Bloomberg)
- Short interest data
- Volume data

---

## Academic Citations

```bibtex
@article{jegadeesh1993returns,
  title={Returns to buying winners and selling losers: Implications for stock market efficiency},
  author={Jegadeesh, Narasimhan and Titman, Sheridan},
  journal={Journal of Finance},
  year={1993}
}

@article{hong1999unified,
  title={A unified theory of underreaction, momentum trading, and overreaction in asset markets},
  author={Hong, Harrison and Stein, Jeremy C},
  journal={Journal of Finance},
  year={1999}
}

@article{asness2013value,
  title={The value and momentum everywhere},
  author={Asness, Cliff and others},
  journal={Journal of Finance},
  year={2013}
}
```

---

*Ride the full momentum lifecycle.*
