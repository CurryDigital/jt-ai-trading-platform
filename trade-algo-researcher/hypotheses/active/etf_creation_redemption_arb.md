# Hypothesis: ETF Creation/Redemption Arbitrage

**Status:** idea  
**Created:** 2026-02-19  
**Asset Class:** ETFs  
**Direction:** Long/Short (spread)  
**Horizon:** 1-3 days  
**Target Win Rate:** 65-75%

---

## Core Idea

ETFs trade at premium/discount to NAV. Large premiums trigger creation (APs buy underlying, create ETF shares, sell at premium). Large discounts trigger redemption. Trade the mean reversion of premium/discount.

**The Edge:**
- Premiums/discounts mean revert quickly (APs arbitrage)
- Premiums persist briefly during high demand (retail FOMO)
- Discounts during panic selling (liquidity mismatch)
- Creation/redemption takes 1-2 days = window for profit

---

## Signal Construction

**Entry (Premium Fade):**
```python
IF ETF_premium > 2% (200 bps):
    # ETF expensive vs NAV - expect AP creation
    Short ETF
    Long underlying basket (or proxy)
    
    Exit when premium < 0.5%
```

**Entry (Discount Fade):**
```python
IF ETF_discount > 1.5% (150 bps):
    # ETF cheap vs NAV - expect AP redemption
    Long ETF
    Short underlying basket (if possible)
    
    Exit when discount < 0.3%
```

**Universe:**
- High volume ETFs: SPY, QQQ, IWM
- Thematic ETFs (higher retail ownership = more mispricing): ARKK, ICLN
- International ETFs: EEM, EFA
- Commodity ETFs: GLD, USO (tracking error)

---

## Expected Performance

| Metric | Target |
|--------|--------|
| Win Rate | 65-75% |
| Avg Return | 0.8-1.5% per trade |
| Sharpe | 1.3-1.8 |
| Hold Time | 1-3 days |

---

## Data Requirements

- **ETF price:** Real-time
- **NAV:** ETF issuer (published every 15 seconds)
- **Premium/discount:** Calculated (ETF - NAV) / NAV
- **Creation units:** AP activity (lagged reporting)

---

## Implementation

**Challenges:**
- Shorting ETFs can be expensive (hard to borrow)
- Underlying basket execution (200+ stocks)
- Use futures proxy (ES for SPY) instead of full basket

**Simplified Version:**
- Only trade discount fade (easier to long ETF)
- Use options if shorting difficult

---

## Academic Support

- Ben-David et al. (2018): ETFs and price discovery
- Petajisto (2017): Inefficiencies in ETF pricing
- Bhattacharya & O'Hara (2018): ETF mispricing

---

*Capture the AP's lunch money.*
