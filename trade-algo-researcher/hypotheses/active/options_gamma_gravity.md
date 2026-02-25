# Hypothesis: Options Gamma Gravity (Pin Risk)

**Status:** idea  
**Created:** 2026-02-19  
**Asset Class:** Equities  
**Direction:** Mean reversion  
**Horizon:** 1-3 days (monthly expiration)  
**Target Win Rate:** 60-70%

---

## Core Idea

Stocks with heavy options open interest tend to "pin" to max pain strikes at monthly expiration. Dealer gamma hedging creates magnetic effect around high-OI strikes.

**The Edge:**
- Dealers hedge delta by buying/selling stock
- Long gamma = buy dips, sell rallies (mean reversion)
- Short gamma = buy rallies, sell dips (trend following)
- High gamma concentration creates "gravity"

---

## Signal Construction

**Max Pain Calculation:**
```python
# Strike where options holders lose max money
# = Strike with minimum total dollar value of ITM options

max_pain_strike = min(
    sum(call_OI * abs(strike - spot) for all calls) +
    sum(put_OI * abs(strike - spot) for all puts)
    for strike in all_strikes
)
```

**Entry (3-5 days before expiration):**
```python
IF stock_price > max_pain_strike + 2%:
    # Above gravity well - expect pull down
    Short stock
    Target: max_pain_strike
    
IF stock_price < max_pain_strike - 2%:
    # Below gravity well - expect pull up
    Long stock
    Target: max_pain_strike
```

**Universe:**
- High options OI stocks: AAPL, TSLA, AMZN, NVDA, META
- Monthly expiration only (3rd Friday)

---

## Expected Performance

| Metric | Target |
|--------|--------|
| Win Rate | 60-70% |
| Avg Return | 1-2% per trade |
| Sharpe | 1.2-1.6 |
| Best Window | 3-5 days before expiration |

**Risks:**
- Strong trend overrides gamma (breakout)
- Earnings/announcements
- Low liquidity in deep OTM options

---

## Data Requirements

- **Options chain:** OI by strike, expiration
- **Max pain calculation:** Real-time
- **Gamma exposure:** By strike and aggregate
- **Sources:** CBOE, Unusual Whales, IBKR

---

## Implementation

**Timing:**
- Enter: Monday-Wednesday of expiration week
- Exit: Thursday or Friday before close
- Avoid: Earnings weeks, Fed weeks

**Position Sizing:**
- 1-2% per trade
- Diversify across 5-10 names

---

## Academic Support

- Ni et al. (2008): Stock price clustering on option expiration dates
- Krishnan & Nelken (2001): The effect of options on stock prices
- Billingsley & Chance (1985): Options market structure

---

*Trade the pin, but don't get pinned.*
