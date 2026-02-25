# Hypothesis: Hong Kong Property NAV Discount Rotation

**Status:** idea  
**Created:** 2026-02-18  
**Market:** Hong Kong (HK)  
**Direction:** Long  
**Horizon:** 3-6 months  
**Target Win Rate:** 60-65%

---

## Core Idea

Hong Kong property developers trade at persistent discounts to NAV (Net Asset Value). Discounts widen during rate hikes/construction slowdowns, narrow during recovery. Mean reversion trade.

**The Edge:**
- HK property developers trade at 0.4-0.7x NAV historically
- Discounts widest during pessimism (rate hikes, China slowdown)
- Discounts narrow during: rate cuts, sales launches, policy support
- High dividend yields (4-6%) cushion holding period

**Key Players:**
- 0001.HK (CK Hutchison) - Conglomerate with property
- 0016.HK (Sun Hung Kai Properties)
- 0017.HK (New World Development)
- 01113.HK (CK Property)
- 01972.HK (Swire Properties)

---

## Signal Construction

**NAV Calculation:**
```python
# Simplified (need actual developer financials)
NAV_per_share = (Investment_properties_market_value + 
                 Development_properties_value + 
                 Cash - Debt) / Shares_outstanding

Price_to_NAV = Stock_price / NAV_per_share
Discount = 1 - Price_to_NAV  # e.g., 0.40 = 40% discount
```

**Entry (Deep Discount):**
```python
IF Price_to_NAV < 0.60 (40% discount):
    AND Discount > 1.5x historical average:
    AND Dividend_yield > 5%:
    AND Interest_rate_cycle peaking (HIBOR/SOR stable or falling):
    
    Long developer
    Hold 3-6 months
```

**Exit (Narrow Discount):**
```python
IF Price_to_NAV > 0.75 (25% discount):
    OR Discount normalized to historical average:
    
    Exit position
```

**Macro Triggers:**
- Fed pause/cut (HK rates follow US via currency peg)
- China reopening/stimulus
- New property sales launch
- Govt land sales (signal of policy support)

---

## Expected Performance

| Metric | Target |
|--------|--------|
| Annual Return | 12-18% |
| Dividend Yield | 4-6% (annual) |
| Price Appreciation | 8-12% (discount narrowing) |
| Win Rate | 60-65% |
| Sharpe | 0.8-1.0 |

**Cycle Timing:**
- Best entry: Late rate hike cycle (HIBOR peaks)
- Best exit: Early recovery, NAV discount narrows

---

## Data Requirements

- **NAV estimates:** Broker reports, company filings
- **Property prices:** Centaline, Midland Realty indices
- **Interest rates:** HIBOR, US Fed funds
- **Land sales data:** HK Government land auction results
- **Transaction volumes:** HK property market data

**Sources:**
- Company annual reports (NAV disclosures)
- Bloomberg/Refinitiv (consensus NAV estimates)
- HK Government Land Registry

---

## Risk Factors

1. **Interest rate risk:** HK rates rise with US (peg), hurts property
2. **China slowdown:** HK property demand tied to China buyers
3. **Oversupply:** New construction glut
4. **Currency peg:** HKD follows USD (can't ease independently)

**Mitigation:**
- Diversify across 3-4 developers
- Monitor HIBOR (HK interbank rates) - leading indicator
- Cut loss if NAV discount widens beyond 50%

---

## Academic Support

- Tse & Webb (2020): NAV discounts in HK property
- Hui et al. (2021): Interest rate sensitivity of HK REITs and developers
- HKU Real Estate Research reports

---

## Current Opportunity (Feb 2024)

**Context:**
- Fed rates high (5.25-5.5%)
- HIBOR elevated
- China property crisis spillover
- HK property prices down 20% from peak

**Result:**
- Developers trading at 0.5-0.6x NAV
- Dividend yields 5-6%
- Potential mean reversion when Fed cuts

**Play:**
- Entry: When Fed signals pause/cuts
- Developers: 0016.HK, 0017.HK, 1113.HK
- Hold: 6-12 months into recovery

---

*Buy HK property at 40-50 cents on the dollar.*
