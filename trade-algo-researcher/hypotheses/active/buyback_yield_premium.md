# Hypothesis: Share Buyback Yield Premium

**Status:** testing  
**Created:** 2026-02-18  
**Asset Class:** Equities  
**Direction:** Long  
**Horizon:** 1-3 years  
**Target Win Rate:** 60-70%

---

## Core Idea

Companies with high shareholder yield (dividends + buybacks) outperform. Buybacks are tax-efficient return of capital and signal management confidence. Best when at discount to intrinsic value.

**The Edge:**
- Buybacks reduce share count = EPS growth
- Tax-efficient vs dividends (deferred until sale)
- Signal: Management thinks stock undervalued
- Compound effect over years

---

## Signal Construction

**Shareholder Yield Calculation:**
```python
buyback_yield = (shares_repurchased * avg_price) / market_cap
dividend_yield = annual_dividend / price
shareholder_yield = buyback_yield + dividend_yield

# Quality filters
buyback_from_fcf = buybacks < free_cash_flow  # Sustainable
shares_outstanding_change = < -2% annually  # Real reduction
price_to_fair_value = price / dcf_value < 1.0  # Undervalued buyback

# Avoid
buyback_with_debt = net_debt_increasing  # Financial engineering
dilution_from_sbc = sbc > buybacks  # Fake buybacks (tech trap)
```

**Scoring:**
```python
yield_score = (
    shareholder_yield * 0.35 +
    fcf_sustainability * 0.25 +
    shares_reduction_rate * 0.2 +
    valuation_discount * 0.15 +
    (1 if not_sbc_funded else 0) * 0.05
)

# Top 20 by yield_score
# Rebalance semi-annually
```

---

## Expected Performance

| Metric | High Buyback | No Buyback | Difference |
|--------|--------------|------------|------------|
| Annual return | 12-14% | 8% | +4-6% |
| EPS growth | 8% | 4% | +4% |
| Sharpe | 0.8 | 0.5 | Better |
| Yield | 5-8% | 1.5% | +4-6% |

**Academic evidence:** Buyback yield adds 3-5% annual alpha (Boudoukh et al. 2007).

---

## Universe

**Sectors with strong buybacks:**
- **Tech:** AAPL, MSFT, META, AVGO (huge buybacks)
- **Financials:** GS, MS, JPM (capital return)
- **Industrials:** LMT, RTX, HON (mature cash cows)
- **Energy:** XOM, CVX (disciplined return)

**Screen:**
- Shareholder yield > 4%
- Buybacks < FCF (sustainable)
- Market cap > $10B

---

## Academic Support

- Ikenberry et al. (1995): Market underreaction to open market share repurchases
- Boudoukh et al. (2007): Shareholder yield and expected returns
- Grullon & Michaely (2004): Information content of share repurchases
- Manconi et al. (2019): Buybacks and acquisition returns

---

## Data Requirements

- **Buyback data:** 10-K, quarterly reports (cash flow statement)
- **Shares outstanding:** Quarterly change tracking
- **SBC data:** Distinguish real vs fake buybacks
- **FCF:** Sustainability check
- **Sources:** Compustat, Bloomberg, company filings

---

## Risk Factors

1. **Overpayment** - Buybacks at market peaks destroy value
2. **Neglect of investment** - Starve R&D for buybacks
3. **SBC funding** - Tech companies issue stock to employees, buy back less
4. **Debt-funded** - Borrowing to buy back = unsustainable

---

## Implementation

**Screening:** Semi-annually (post-earnings)
**Entry:** 2-3% positions in top 15 buyback stories
**Hold:** 18-36 months
**Rebalance:** Trim when yield drops < 3%, add new qualifiers

**Quality checks:**
- FCF covers buyback + dividend
- Shares actually declining (not just authorized)
- Buyback at < 20x P/E (reasonable)

---

*Tax-efficient compounding via share count reduction.*
