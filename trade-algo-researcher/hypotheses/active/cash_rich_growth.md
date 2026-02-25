# Hypothesis: Cash-Rich Growth (Savings → Capex Alpha)

**Status:** testing  
**Created:** 2026-02-18  
**Asset Class:** Equities  
**Direction:** Long  
**Horizon:** 1-2 years  
**Target Win Rate:** 60-65%

---

## Core Idea

Companies with high cash reserves ("savings") relative to market cap invest in growth (Capex, R&D, M&A) over 1-2 years, leading to outperformance. Cash is optionality that converts to growth.

**The Edge:**
- Cash-rich companies can acquire distressed competitors
- R&D spending leads to product cycles
- Buybacks at low multiples = value creation
- Market underprices optionality of cash

---

## Signal Construction

**Cash Position Score:**
```python
# Cash metrics
cash_to_market_cap = cash_and_investments / market_cap
cash_to_annual_expenses = cash / (opex + capex)
net_cash = cash - total_debt  # Enterprise value adjustment

# Growth catalyst score
recent_acquisitions = last_12m > 0
rd_intensity = rd_spend / revenue > industry_avg
capex_growth = yoy_capex_change > 10%

# Quality filter
fcf_positive = free_cash_flow > 0
profitability = operating_margin > 10%
```

**Composite Score:**
```python
cash_score = (
    cash_to_market_cap * 0.3 +
    cash_to_expenses * 0.2 +
    (1 if recent_acquisitions else 0) * 0.15 +
    rd_intensity * 0.15 +
    capex_growth * 0.1 +
    fcf_positive * 0.1
)

# Top 20 by cash_score
# Hold 12-24 months
```

---

## Expected Performance

| Metric | Cash-Rich | Cash-Poor | Difference |
|--------|-----------|-----------|------------|
| 1-year return | 15% | 8% | +7% |
| 2-year return | 28% | 15% | +13% |
| Volatility | 18% | 22% | Lower risk |
| Sharpe | 0.8 | 0.4 | 2x better |

**Academic finding:** Cash-rich companies outperform by 5-8% annually (Harford 1999, Dittmar & Mahrt-Smith 2007).

---

## Universe

**Sectors with cash hoarders:**
- **Tech:** AAPL, MSFT, GOOGL, META (legacy cash)
- **Semis:** NVDA, AMD, AVGO (R&D conversion)
- **Biotech:** Cash for clinical trials → FDA approvals
- **Japanese companies:** Historically cash-rich (activist targets)

**Screen:**
- Cash/Market Cap > 15%
- Profitable (positive FCF)
- Market cap > $5B (no micro-cap)

---

## Academic Support

- Jensen (1986): Free cash flow problem (but can be opportunity)
- Harford (1999): Cash-rich companies make better acquisitions
- Dittmar & Mahrt-Smith (2007): Corporate governance and cash
- Fresard (2010): Cash holdings and product market performance
- Chen & Zhang (2020): Cash-rich firms and innovation

---

## Data Requirements

- **Balance sheet:** Cash, investments, debt (quarterly)
- **Cash flow:** Capex, R&D, M&A (quarterly)
- **Real-time:** Market cap for ratios
- **Sources:** Compustat, Bloomberg, SEC filings (10-Q)

---

## Risk Factors

1. **Empire building** - CEO squanders cash on bad acquisitions
2. **Activist pressure** - Carl Icahn forces buyback instead of growth
3. **Opportunity cost** - Cash sits idle too long
4. **Sector rotation** - Growth to value hurts cash-rich tech

---

## Implementation

**Screening:** Quarterly (after earnings)
**Entry:** 2-4% positions in top 15 cash-rich growers
**Hold:** 18-24 months (time for cash deployment)
**Rebalance:** Annually unless thesis broken

**Catalyst watch:**
- M&A announcements
- New product launches
- Capex guidance increases
- Buyback authorization (with growth)

---

*Cash is optionality. Watch them exercise it.*
