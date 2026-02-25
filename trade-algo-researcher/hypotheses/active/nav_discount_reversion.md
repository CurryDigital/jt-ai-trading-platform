# Hypothesis: NAV Discount/Premium Reversion (Closed-End Funds)

**Status:** testing  
**Created:** 2026-02-18  
**Asset Class:** Closed-End Funds (CEFs), REITs  
**Direction:** Long  
**Horizon:** 6-18 months  
**Target Win Rate:** 60-70%

---

## Core Idea

Closed-end funds (CEFs) and REITs often trade at persistent discounts or premiums to Net Asset Value (NAV). Mean reversion occurs as:
1. Discounts > 10% attract activist investors
2. Premiums collapse when enthusiasm fades
3. Distribution coverage drives convergence

**The Edge:**
- Retail investors create pricing inefficiencies
- NAV is knowable (published daily for CEFs)
- Discount + yield = double compounding

---

## Signal Construction

**Discount Calculation:**
```python
nav_discount = (NAV - market_price) / NAV
# Positive = trading at discount
# Negative = trading at premium
```

**Entry Criteria (Long Discount):**
```python
nav_discount > 10%  # Deep discount
historical_discount_avg = 5%  # Compare to 3-year average
z_score = (current_discount - avg) / std_dev > 1.5  # Extreme

# Quality filters
distribution_coverage = NII / distribution > 0.9  # Sustainable payout
expense_ratio = < 1.5%  # Not too expensive
leverage = < 40%  # Manageable risk
avg_daily_volume = > $500K  # Liquid enough
```

**Exit Criteria:**
```python
nav_discount < 5%  # Converged to normal
OR distribution_cut announced
OR premium develops (sell)
```

---

## Expected Performance

| Metric | Target |
|--------|--------|
| Annual Return | 8-12% |
| Yield component | 6-8% |
| Capital appreciation | 2-4% (discount narrowing) |
| Win Rate (convergence) | 60-70% |
| Avg Hold | 9-12 months |

**Discount Capture Example:**
- Buy at 15% discount
- NAV grows 5%
- Discount narrows to 5%
- Total return: 5% NAV + 10% discount = 15%

---

## Universe

**CEF Categories:**
- **Municipal bonds:** NIO, NUW (tax-free yield)
- **Corporate bonds:** JPS, JQC
- **REITs:** BXMT, WPC, O (real estate exposure)
- **Utilities:** DPG, UTG
- **Multi-asset:** EOI, ETJ (option income)

**REITs:** Focus on NAV discount/premium vs property values

---

## Academic Support

- Thompson (1978): CEF discount puzzle
- Pontiff (1996): Costly arbitrage and price deviation
- Gemmill & Thomas (2002): CEF discounts and noise trader risk
- Chernenko & Sunderam (2016): Frictions in CEF pricing

---

## Data Requirements

- **NAV data:** CEFConnect, Morningstar (daily NAV)
- **Market prices:** Bloomberg, Yahoo Finance
- **Distribution data:** Coverage ratios, sustainability
- **REIT NAV:** Property appraisals, funds from operations (FFO)

---

## Risk Factors

1. **Distribution cuts** - Most common reason for persistent discount
2. **Leverage squeeze** - Rising rates hurt leveraged CEFs
3. **Manager quality** - Underperforming NAV vs benchmark
4. **Liquidity risk** - Wide spreads, low volume in small CEFs

---

## Implementation

**Screening:** Weekly scan for discounts > 10%
**Diversification:** 10-15 CEFs across sectors
**Sizing:** 2-3% per position (CEF-specific risk)
**Rebalance:** Quarterly (trim converged, add new discounts)

**Advanced:**
- Pair trade: Long discounted CEF / Short ETF with same holdings
- Activist tracking: Follow Bulldog, Saba campaigns

---

*Buy $1.00 for $0.85, collect yield while waiting.*
