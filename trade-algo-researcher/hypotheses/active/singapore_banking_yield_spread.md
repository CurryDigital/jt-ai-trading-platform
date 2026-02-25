# Singapore Banking Yield Spread Strategy

**Hypothesis ID:** SG_BANKING_YIELD_SPREAD_001  
**Date:** 2026-02-20  
**Region:** Singapore (SG)  
**Asset Class:** Equities  
**Expected Sharpe:** 1.1-1.5  
**Expected Win Rate:** 62-68%  
**Time Horizon:** Medium-term (1-3 months)

---

## Core Thesis

**Singapore banks (DBS, OCBC, UOB) benefit from rising interest rates through net interest margin (NIM) expansion, creating a cyclical alpha opportunity around rate regime changes.**

### Macro Drivers
1. **Fed Policy Transmission:** Singapore rates track US closely (SGD managed float vs USD)
2. **NIM Expansion:** Higher rates → wider lending-deposit spreads
3. **Wealth Management:** Safe haven flows benefit Singapore private banking
4. **Dividend Yield:** 5-6% yields attract income investors in volatile markets
5. **ASEAN Exposure:** Loan growth from regional economic expansion

### Key Insight
Singapore banks trade on:
- **Rate expectations** (forward guidance)
- **NIM realization** (quarterly earnings)
- **Credit quality** (NPL ratios)
- **Dividend sustainability** (payout ratios)

The strategy captures the **NIM expansion phase** of rate cycles and exits before credit quality concerns emerge.

---

## Universe

### The "Big Three" Singapore Banks

| Ticker | Name | Market Cap | Yield | NIM | Key Driver |
|--------|------|------------|-------|-----|------------|
| D05.SI | DBS Group | ~S$80B | 5.2% | 2.15% | Largest; wealth mgmt focus |
| O39.SI | OCBC | ~S$60B | 5.5% | 2.20% | ASEAN exposure; insurance |
| U11.SI | UOB | ~S$50B | 5.4% | 2.08% | Regional commercial focus |

### Selection Criteria
- **Primary:** Big 3 only (liquidity, coverage, index weight)
- **Min Volume:** S$50M daily
- **Dividend:** Consistent payout history (5+ years)
- **Credit Quality:** NPL < 1.5%

---

## Signal Logic

### Primary Signal: Rate Cycle NIM Play

```python
# Phase 1: Rate Hike Entry
IF Fed_dot_plot_shift = "hawkish" OR MAS_policy_statement = "tightening":
    IF 10Y_US_Treasury_yield_slope > 0:  # Positive yield curve (no recession fear)
        IF SG_banks_index_underperformance > 5%:  # Lagging vs STI
            SIGNAL = WATCHLIST

# Phase 2: Earnings Confirmation
IF quarterly_NIM QoQ > +5bps:  # NIM expanding
    IF net_interest_income YoY > +10%:
        IF credit_costs_stable:  # NPL not spiking
            SIGNAL = LONG
            position_size = base * (NIM_expansion / 10bps)

# Phase 3: Dividend Capture Enhancement
IF days_to_ex_dividend < 14:
    IF dividend_yield > 5%:
        IF price_vs_52w_high < 0.90:  # Not extended
            SIGNAL = ADD / SIZE_UP

# Phase 4: Exit Conditions
IF Fed_dot_plot_shift = "dovish" OR yield_curve_inverts:  # Rate cuts coming
    EXIT = CYCLE_END
    
IF quarterly_NIM QoQ < 0:  # NIM contraction
    EXIT = FUNDAMENTAL_CHANGE
    
IF NPL_ratio > 2.0%:  # Credit deterioration
    EXIT = CREDIT_RISK
    
IF holding_days > 90 AND momentum_20d < 0:
    EXIT = TIME_STOP
```

### Secondary Signal: Relative Value

```python
# Among Big 3, pick best risk/reward
FOR bank IN [DBS, OCBC, UOB]:
    score = (
        bank.NIM_expansion * 0.3 +
        bank.dividend_yield * 0.25 +
        bank.price_vs_52w_low * 0.25 +
        bank.credit_quality_score * 0.2
    )

# Long top scorer; avoid bottom
LONG = max(score)
AVOID = min(score)  # Or short if hedging
```

---

## Entry/Exit Rules

### Entry Conditions
1. **Rate Regime:** Fed/MAS hawkish guidance; 10Y yield stable/rising
2. **Valuation:** Price < 52W high by >5% (not chasing)
3. **NIM Trend:** Last quarter NIM expansion OR guidance for expansion
4. **Credit Quality:** NPL stable or improving
5. **Yield:** Dividend yield > 5%

### Exit Conditions
1. **Cycle End:** Dovish pivot signals; yield curve inversion
2. **NIM Peak:** Quarter-over-quarter NIM contraction
3. **Credit Risk:** NPL > 2%; credit costs rising
4. **Time Stop:** 90 days without NIM improvement
5. **Profit Taking:** +20% gain (cyclical peak often +15-25%)

---

## Position Sizing

```python
max_theme_exposure = 0.15  # 15% of portfolio
max_single_bank = 0.10  # 10% single name

# Diversify across 2-3 banks
IF only_1_bank_passes_filters:
    position_size = 0.10
ELIF 2_banks_pass:
    position_size_each = 0.075
ELIF all_3_pass:
    position_size_each = 0.05
```

---

## Risk Management

### Specific Risks
| Risk | Mitigation |
|------|------------|
| **Rate Cut Cycle** | Monitor Fed dot plot; exit on dovish pivot |
| **Credit Cycle** | Watch NPL ratios quarterly; exit if >2% |
| **Property Exposure** | Track Singapore/HK property prices; banks have exposure |
| **Currency Risk** | SGD stable vs USD; minimal FX risk for SGD-based investors |
| **Concentration** | Max 15% theme exposure; banks are correlated |

### Correlation Check
- High correlation among Big 3 (0.8-0.9)
- Also correlated with HK banks (HSBC, HKEX)
- Avoid if portfolio already has Asian financials exposure

---

## Expected Performance

### Historical Context (Proxy: 2022-2023 rate cycle)
- **DBS:** +40% from Oct 2022 to Jul 2023 (rate hike cycle)
- **OCBC:** +35% over same period
- **UOB:** +32% over same period

### Backtest Assumptions
- **Win Rate:** 62-68% (rate cycles are somewhat predictable)
- **Avg Winner:** +15%
- **Avg Loser:** -7%
- **Profit Factor:** 2.2-2.8
- **Sharpe:** 1.1-1.5
- **Max Drawdown:** -12% (banks are less volatile than tech)

### Scenario Analysis
| Scenario | Probability | Return Impact |
|----------|-------------|---------------|
| Extended rate cycle | 35% | +20-30% |
| Soft landing | 40% | +10-15% |
| Recession/cuts | 20% | -5-10% |
| Credit crisis | 5% | -20%+ |

---

## Data Requirements

### Essential (Free)
- [ ] OHLCV for D05.SI, O39.SI, U11.SI (yfinance)
- [ ] Quarterly earnings (SGX announcements)
- [ ] Fed dot plot releases (Fed website)
- [ ] MAS policy statements
- [ ] US Treasury yield curve (FRED)

### Optional ($)
- [ ] Bank earnings consensus (Bloomberg/Reuters)
- [ ] Credit quality data (Moody's, bank reports)

---

## Academic Support

- **Interest Rate Sensitivity:** Banking sector beta to rates is 0.8-1.2
- **Dividend Capture:** Ex-date effects in high-yield stocks (Loncarski et al., 2008)
- **Cycle Timing:** Rate regime changes predict sector rotation (Stangl et al., 2021)

---

## Related Strategies

- **HK Property NAV Discount:** Property developers also rate-sensitive
- **FX Carry SGD/USD:** Can hedge/enhance SGD exposure
- **SG REIT Dividend Capture:** Alternative Singapore income play

---

## Testing Plan

1. **Phase 1:** Validate signal using 2022-2023 rate cycle (recent data)
2. **Phase 2:** Backtest 2015-2019 cycle (previous rate regime)
3. **Phase 3:** Paper trade with live earnings tracking
4. **Phase 4:** Full deployment

---

**Status:** IDEA → Pending Data Collection  
**Priority:** MEDIUM (requires rate cycle timing)  
**Effort:** Low (only 3 tickers, free data)  
**Expected Validation:** 1-2 weeks
