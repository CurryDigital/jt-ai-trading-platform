# Hong Kong IPO Post-Listing Momentum Strategy

**Hypothesis ID:** HK_IPO_POST_LISTING_001  
**Date:** 2026-02-20  
**Region:** Hong Kong (HK)  
**Asset Class:** Equities  
**Expected Sharpe:** 0.9-1.3  
**Expected Win Rate:** 55-62%  
**Time Horizon:** Short-term (5-20 days)

---

## Core Thesis

**Hong Kong IPOs exhibit predictable post-listing price patterns driven by institutional allocation dynamics, retail oversubscription effects, and greenshoe option exercises.**

### Market Mechanics
1. **High Retail Oversubscription:** HK IPOs often 100x-1000x oversubscribed (financing culture)
2. **Cornerstone Investors:** 30-60% allocated to long-only institutional holders (lock-up)
3. **Greenshoe Over-Allotment:** Stabilization manager supports price in first 30 days
4. **Sector Concentration:** Heavy bias toward China tech, biotech, property
5. **Index Inclusion:** Large IPOs (>$5B) often fast-tracked into Hang Seng indexes

### Key Insight
Post-listing behavior follows predictable phases:
- **Day 1-2:** Retail flipping (high volume, volatile)
- **Day 3-10:** Stabilization period (greenshoe support)
- **Day 11-20:** True price discovery (removal of stabilizer)
- **Day 30+:** Lock-up expiry risk (cornerstone shares)

The strategy captures the **stabilization phase** (Day 3-10) where greenshoe support creates asymmetric upside.

---

## Universe

### Primary Universe: Recent HK IPOs

| Ticker | Name | Sector | IPO Date | Market Cap |
|--------|------|--------|----------|------------|
| Varies | New listings | Tech/Biotech/Property | <30 days | >HK$5B |

### Selection Criteria
- **Minimum Size:** HK$5B market cap at IPO (liquidity)
- **Maximum Size:** HK$50B (too large for retail effects)
- **Retail Oversubscription:** >50x (indicates retail enthusiasm)
- **Cornerstone Allocation:** 30-60% (stability)
- **Sector:** Tech, Biotech, Consumer (avoid property due to cyclicality)
- **Sponsor Quality:** Top-tier sponsors (Goldman, Morgan Stanley, CICC)

### Exclusion Criteria
- **Property Developers:** Too cyclical; policy-sensitive
- **Small Caps (<HK$2B):** Liquidity risk
- **Low Oversubscription (<10x):** Lack of retail interest
- **Broken IPOs:** Already trading <-20% from IPO price

---

## Signal Logic

### Primary Signal: Greenshoe Stabilization Play

```python
# Phase 1: IPO Day Analysis (No Entry)
IF IPO_first_day_return > -5% AND IPO_first_day_return < +30%:
    IF retail_oversubscription > 50x:
        IF greenshoe_exercised = True:  # Stabilization active
            SIGNAL = WATCHLIST

# Phase 2: Stabilization Entry (Day 3-5)
IF days_since_IPO >= 3 AND days_since_IPO <= 5:
    IF price_vs_IPO > -5%:  # Holding above IPO price
        IF volume_3d_avg < volume_IPO_day * 0.5:  # Selling pressure easing
            IF price_vs_first_day_close > -3%:  # Not breaking down
                SIGNAL = LONG
                position_size = base * (oversubscription / 100x)

# Phase 3: Momentum Hold (Day 6-15)
IF days_since_IPO > 5 AND days_since_IPO <= 15:
    IF price_vs_entry > +5%:  # Profitable
        IF momentum_5d > 0:  # Still trending
            HOLD
        ELSE:
            TAKE_PROFIT  # Momentum fading
    ELIF price_vs_entry < -5%:
        STOP_LOSS

# Phase 4: Pre-Lockup Exit (Day 16-25)
IF days_since_IPO > 15:
    IF days_to_lockup_expiry < 10:
        EXIT = LOCKUP_RISK  # Cornerstone shares coming
    ELIF momentum_5d < 0:
        EXIT = MOMENTUM_FADE
```

### Secondary Signal: Index Inclusion Play

```python
# Large IPOs get fast-tracked into Hang Seng indexes
IF expected_index_inclusion = True:  # >HK$20B market cap
    IF days_to_inclusion_announcement < 30:
        SIGNAL = INDEX_INCLUSION_BETA
        # Passive flows drive price up
```

---

## Entry/Exit Rules

### Entry Conditions
1. **Timing:** Day 3-5 after IPO (stabilization window)
2. **Price:** Within -5% to +20% of IPO price (not broken, not parabolic)
3. **Volume:** Declining volume from Day 1 (flipping completed)
4. **Oversubscription:** Retail >50x (retail enthusiasm indicator)
5. **Sector:** Tech/Biotech/Consumer (avoid property)

### Exit Conditions
1. **Profit Target:** +15-20% from entry (typical stabilization gain)
2. **Time Stop:** Day 20 (lock-up expiry risk)
3. **Stop Loss:** -7% from entry
4. **Lockup Warning:** 10 days before lockup expiry
5. **Momentum Fade:** 5-day momentum turns negative

---

## Position Sizing

```python
max_theme_exposure = 0.10  # 10% of portfolio (high risk theme)
max_single_IPO = 0.03  # 3% single name (binary event risk)
max_concurrent_positions = 3  # Diversify across IPOs

# Adjust by conviction
position_size = base * min(oversubscription / 100x, 2.0)  # Cap at 2x
```

---

## Risk Management

### Specific Risks
| Risk | Mitigation |
|------|------------|
| **Broken IPO** | Stop loss at -7%; avoid if Day 1 <-10% |
| **Lockup Crash** | Mandatory exit 10 days before lockup |
| **Market Crash** | Global risk off affects all IPOs; reduce size |
| **Liquidity** | Minimum HK$5B market cap; avoid low volume |
| **Sector Rotation** | Avoid property; monitor China policy |

### Correlation Check
- IPOs are correlated with each other (market sentiment)
- Also correlated with Hang Seng Tech Index
- Reduce size if portfolio already has HK exposure

---

## Expected Performance

### Historical Context (Proxy: 2020-2021 HK IPO boom)
- **Successful IPOs:** +10-30% in first 30 days (post-stabilization)
- **Broken IPOs:** -20-40% (avoided by entry filters)
- **Greenshoe Support:** Visible in Day 3-15 price floors

### Backtest Assumptions
- **Win Rate:** 55-62% (IPO outcomes are binary)
- **Avg Winner:** +18%
- **Avg Loser:** -8%
- **Profit Factor:** 1.8-2.3
- **Sharpe:** 0.9-1.3 (higher volatility)
- **Max Drawdown:** -15% (concentration risk)

### Scenario Analysis
| Scenario | Probability | Return Impact |
|----------|-------------|---------------|
| Strong stabilization | 40% | +15-25% |
| Weak/moderate | 30% | +5-10% |
| Broken IPO | 25% | -5-10% |
| Disaster IPO | 5% | -20%+ |

---

## Data Requirements

### Essential (Free)
- [ ] HKEX IPO calendar (HKEX website)
- [ ] IPO prospectuses (oversubscription data)
- [ ] OHLCV for recent listings (yfinance)
- [ ] Greenshoe exercise announcements
- [ ] Lock-up expiry dates (prospectus)

### Optional ($)
- [ ] Real-time IPO grey market prices
- [ ] Cornerstone investor tracking
- [ ] Stabilization manager reports

---

## Academic Support

- **IPO Underpricing:** Ritter (1991), Loughran & Ritter (1995) - global IPO patterns
- **Stabilization Effects:** Ellis et al. (2000) - greenshoe impact on post-IPO prices
- **Retail Trading:** Barber et al. (2009) - retail investor behavior in new listings

---

## Related Strategies

- **China Policy Drift:** IPOs often China tech; same policy sensitivity
- **AH Premium Arbitrage:** Some IPOs dual-list
- **RSI Mean Reversion HK:** Entry timing for oversold IPOs

---

## Testing Plan

1. **Phase 1:** Backtest 2020-2024 HK IPO cohorts (4 years of data)
2. **Phase 2:** Validate greenshoe signal accuracy
3. **Phase 3:** Paper trade live IPOs (need ongoing IPO flow)
4. **Phase 4:** Full deployment with position limits

---

## Important Note on Data

HK IPO data requires:
- Manual tracking of IPO calendar
- Prospectus reading for oversubscription/lockup data
- Real-time monitoring of new listings

This is **higher maintenance** than systematic strategies but offers **less competition** (retail-dominated inefficiency).

---

**Status:** IDEA → Pending IPO Calendar Data  
**Priority:** MEDIUM (requires active monitoring)  
**Effort:** Medium (data collection intensive)  
**Expected Validation:** 2-3 weeks (need recent IPO cohort)
