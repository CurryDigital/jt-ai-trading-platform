# Hypothesis: Dividend Aristocrat Momentum

**Status:** testing  
**Created:** 2026-02-18  
**Asset Class:** Equities  
**Direction:** Long  
**Horizon:** 1-3 years  
**Target Win Rate:** 65-75% (annual outperformance)

---

## Core Idea

Companies with 10+ consecutive years of dividend growth (Dividend Aristocrats) exhibit long-term outperformance due to:
1. Quality earnings (sustainable cash flows)
2. Management discipline (capital allocation)
3. Shareholder alignment
4. Flight to safety during volatility

**The Edge:**
- Dividend growth predicts future earnings growth
- Reinvestment at compound rates beats market timing
- Lower volatility than broad market
- Inflation hedge (dividend growth > inflation)

---

## Signal Construction

**Entry Criteria:**
```python
# Dividend Aristocrat criteria
consecutive_dividend_growth = >= 10 years
dividend_yield = 2-4% (sweet spot)
dividend_growth_rate = >= 5% annually
payout_ratio = < 60% (sustainable)
free_cash_flow_yield = > dividend_yield (covered)

# Quality filters
ROE = > 12%
debt_to_equity = < 0.5
earnings_stability = < 20% std dev over 5 years
```

**Scoring:**
```python
score = (
    dividend_growth_years * 0.3 +
    dividend_cagr_5y * 0.25 +
    (1 / payout_ratio) * 0.2 +
    roe * 0.15 +
    fcf_coverage * 0.1
)

# Select top 20 by score
# Rebalance quarterly
# Hold 1-3 years
```

---

## Expected Performance

| Metric | Target | Benchmark (SPY) |
|--------|--------|-----------------|
| Annual Return | 10-12% | 10% |
| Volatility | 12-14% | 16% |
| Sharpe | 0.8-0.9 | 0.6 |
| Max DD | 20-25% | 35% |
| Yield | 2.5-3.5% | 1.5% |

**Rolling 3-year win rate vs SPY:** 65-75%

---

## Universe

S&P 500 Dividend Aristocrats (60+ stocks), filtered to:
- Market cap > $10B
- Dividend yield 2-5% (not yield traps)
- Payout ratio < 70%

**Examples:**
- Consumer staples: KO, PEP, PG, WMT
- Industrials: MMM, CAT, ITW
- Healthcare: JNJ, ABT, MDT
- Financials: CVX, XOM (energy but dividend focus)

---

## Academic Support

- Fama-French (1988): Dividend yields predict returns
- Naranjo et al. (1998): Dividend yield and returns
- Harris & Marston (1994): Dividend growth and stock returns
- Fuller & Goldstein (2011): Dividend Aristocrats study (outperformance)

---

## Data Requirements

- **Dividend history:** 10+ years (Compustat, Bloomberg)
- **Financials:** FCF, earnings, debt (quarterly updates)
- **Real-time:** Prices for rebalancing
- **Sources:** S&P Dow Jones (official list), Quandl, Yahoo Finance

---

## Risk Factors

1. **Rising rates** - Dividend stocks compete with bonds
2. **Dividend cuts** - Aristocrat status lost (e.g., T, VFC)
3. **Value trap** - High yield = distressed, not quality
4. **Sector concentration** - Heavy staples/utilities weight

---

## Implementation

**Entry:** Quarterly rebalancing
**Sizing:** Equal weight or dividend yield weight
**Rebalance:** Quarterly (remove cutters, add new qualifiers)
**Hold:** 1-3 years minimum (tax efficiency)

**Tax Considerations:**
- Qualified dividends: 15-20% tax rate
- Hold >1 year for long-term cap gains
- Ideal for tax-advantaged accounts

---

*Compound the queens, not just the kings.*
