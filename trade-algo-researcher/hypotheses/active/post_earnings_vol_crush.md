# Hypothesis: Post-Earnings Volatility Crush

**Status:** idea  
**Created:** 2026-02-19  
**Asset Class:** Options (Equities)  
**Direction:** Short volatility  
**Horizon:** 1-3 days  
**Target Win Rate:** 60-70%

---

## Core Idea

Options implied volatility expands before earnings (uncertainty), then collapses after earnings announcement (certainty). Short straddles/strangles post-earnings capture vol crush.

**The Edge:**
- IV typically 2-3x normal before earnings
- IV crush = 30-50% drop in implied vol post-announcement
- Stock often moves less than implied (straddle overpriced)
- Systematic overpricing of earnings risk

---

## Signal Construction

**Entry (After Earnings Announcement):**
```python
IF earnings_just_announced (after hours or pre-market):
    AND stock_move < implied_move (straddle breakeven):
    AND IV_still_elevated > 50th percentile:
    
    Short straddle (ATM call + ATM put)
    OR short iron butterfly (defined risk)
    
    Hold 1-3 days for vol crush
```

**Stock Move vs Implied:**
```python
straddle_price = call_ATM + put_ATM
implied_move = straddle_price / stock_price
actual_move = abs(after_earnings_price - before_earnings_price) / before_earnings_price

IF actual_move < implied_move * 0.8:
    # Stock moved less than expected = vol crush candidate
    Enter short vol position
```

**Universe:**
- High options volume: AAPL, TSLA, AMZN, NVDA, META, NFLX
- Predictable earnings: Stable businesses, not biotech
- Avoid: Binary outcome stocks (FDA decisions, major product launches)

---

## Expected Performance

| Metric | Target |
|--------|--------|
| Win Rate | 60-70% |
| Avg Return | 15-25% per trade (on margin) |
| Sharpe | 1.2-1.6 |
| Losses | Large when stock gaps > implied move |

---

## Data Requirements

- **Earnings calendar:** Exact announcement dates/times
- **Options prices:** Pre and post earnings
- **Implied vol:** By strike and expiration
- **Historical earnings moves:** For expected move calculation

---

## Implementation

**Timing:**
- Enter: After earnings announcement (after hours)
- Use next-day opening if announced pre-market
- Exit: 1-3 days after (vol crush complete)

**Risk Management:**
- Position size small (1-2% max loss per trade)
- Use iron butterfly (defined risk) not naked straddle
- Hard stop if stock continues moving against position

---

## Academic Support

- Patatoukas et al. (2018): Post-earnings announcement drift
- Barth et al. (2017): Options trading volume and stock price jumps
- Diz & Finucane (1993): Rationality of options price expectations

---

*Sell the uncertainty, buy the certainty.*
