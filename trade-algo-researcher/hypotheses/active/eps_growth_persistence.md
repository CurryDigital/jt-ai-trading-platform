# Hypothesis: Multi-Year EPS Growth Persistence

**Status:** testing  
**Created:** 2026-02-18  
**Asset Class:** Equities  
**Direction:** Long  
**Horizon:** 2-5 years  
**Target Win Rate:** 70-80% (positive returns)

---

## Core Idea

Companies with 5+ consecutive years of EPS growth exhibit momentum that persists. High-quality earnings growth compounds and is underappreciated by short-term focused market.

**The Edge:**
- Earnings persistence = quality (not accounting tricks)
- Compound growth undervalued by DCF models
- Institutional accumulation over quarters
- "Boring" consistency beats volatile winners

---

## Signal Construction

**Growth Quality Criteria:**
```python
# Consecutive growth
eps_growth_streak = 5+ years of yoy EPS growth
revenue_growth_streak = 5+ years of yoy revenue growth  # Confirm not just buybacks

# Growth magnitude
eps_cagr_5y = >= 10% annually
revenue_cagr_5y = >= 8% annually

# Quality checks
margin_expansion = gross_margin trend positive or stable
fcf_conversion = fcf / net_income > 0.8  # Real cash earnings
low_accruals = accrual_ratio < 0.1  # Not accounting manipulation
```

**Scoring:**
```python
persistence_score = (
    eps_growth_streak * 0.25 +
    eps_cagr_5y * 0.2 +
    revenue_growth_streak * 0.2 +
    margin_stability * 0.15 +
    fcf_conversion * 0.1 +
    (1 - accruals) * 0.1
)

# Top 25 by persistence_score
# Hold 2-5 years
# Rebalance annually
```

---

## Expected Performance

| Metric | Growth Persistence | SPY | Outperformance |
|--------|-------------------|-----|----------------|
| 1-year return | 18% | 10% | +8% |
| 3-year CAGR | 16% | 10% | +6% |
| 5-year CAGR | 15% | 10% | +5% |
| Win rate (3yr+) | 75% | 65% | +10pp |
| Max DD | 25% | 35% | Lower risk |

**Key finding:** Persistence beats magnitude. 10% growth for 10 years > 30% growth for 2 years.

---

## Universe

**Characteristics:**
- Mid-to-large cap ($5B+)
- Non-cyclical sectors (tech, healthcare, consumer staples)
- Sustainable competitive advantages (moats)

**Examples:**
- **Tech:** V, MA, MSFT, ADBE (subscription models)
- **Healthcare:** UNH, LLY, JNJ (demographics)
- **Industrials:** ROP, TDG (niche dominance)
- **Consumer:** EL, LULU, DPZ (brand loyalty)

---

## Academic Support

- Lakonishok et al. (1994): Contrarian investment, extrapolation, and risk
- Chan et al. (1996): Momentum strategies
- Piotroski (2000): Value investing and fundamental analysis
- Novy-Marx (2015): Fundamentally, momentum is fundamental momentum
- Asness et al. (2019): Quality minus junk

---

## Data Requirements

- **Earnings history:** 7-10 years EPS (Compustat)
- **Revenue reconciliation:** Confirm growth not just buybacks
- **Cash flow:** FCF conversion quality
- **Real-time:** Prices for rebalancing
- **Sources:** Compustat, Bloomberg, FactSet

---

## Risk Factors

1. **Growth stall** - Law of large numbers, saturation
2. **Multiple compression** - High P/E implies perfection
3. **Disruption** - Tech change kills moat (e.g., retail vs AMZN)
4. **Mean reversion** - Eventually growth normalizes

---

## Implementation

**Screening:** Annually (after fiscal year-end)
**Position sizing:** 3-4% per name (high conviction)
**Hold:** 2-5 years minimum
**Trim rules:**
- EPS growth breaks (2 quarters)
- Valuation > 40x P/E (take profits)
- Thesis broken (disruption, regulation)

**Tax efficiency:**
- Qualified dividends
- Long-term cap gains
- Ideal for taxable accounts

---

*Buy compounders, let them work.*
