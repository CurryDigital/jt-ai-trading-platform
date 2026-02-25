# Hypothesis: VIX Term Structure Contango Roll

**Status:** idea  
**Created:** 2026-02-19  
**Asset Class:** Volatility (VIX futures)  
**Direction:** Short  
**Horizon:** 1 month (roll cycle)  
**Target Win Rate:** 65-75%

---

## Core Idea

VIX futures typically trade in contango (front month cheaper than back month). Shorting front-month VIX futures and rolling monthly captures the roll yield as contango decays toward spot.

**The Edge:**
- VIX futures in contango 70-80% of the time
- Roll yield = ~5-10% annualized from term structure decay
- Short VIX = short volatility risk premium (investors overpay for protection)

---

## Signal Construction

**Entry:**
```python
IF VIX_term_structure_slope > 0 (contango):
    AND VIX_index < 25 (not crisis):
    AND Front_month_premium > 5%:
    
    Short front-month VIX futures
    Hold until 7 days before expiration
    Roll to next month
```

**Enhanced Filter:**
```python
# Higher conviction when:
- VIX < 20 (low vol environment)
- Term structure steep (M2/M1 > 1.10)
- No Fed meeting in next 2 weeks
- SPY above 50-day MA (bullish backdrop)
```

**Exit:**
- 7 days before expiration (avoid settlement risk)
- Or VIX > 30 (risk-off, cover shorts)

---

## Expected Performance

| Metric | Target |
|--------|--------|
| Annual Return | 8-12% |
| Sharpe | 0.8-1.2 |
| Max DD | -25% (VIX spike risk) |
| Win Rate | 65-75% monthly |

**Risks:**
- VIX spike (short vol = crash risk)
- Backwardation during crisis (negative roll yield)
- Term structure inversion

**Mitigation:**
- Position size small (2-3% max)
- Hard stop if VIX > 30
- Avoid Fed weeks, earnings seasons

---

## Data Requirements

- **VIX futures prices:** CBOE, IBKR
- **Term structure:** M1, M2, M3, M4 prices
- **VIX index:** Real-time
- **Contango calculation:** (M2-M1)/M1

---

## Implementation

**Instruments:**
- Short VIX futures (direct)
- Long SVXY (ETP, has volatility drag)
- Short VXX (has borrow costs)

**Best:** Short VIX futures directly via IBKR

---

## Academic Support

- Whaley (1993): Derivatives on market volatility
- Simon (2003): The VIX futures basis
- Eraker & Wu (2014): Exploiting the volatility term structure

---

*Collect the volatility risk premium.*
