# Hypothesis: Singapore REIT Dividend Capture

**Status:** idea  
**Created:** 2026-02-18  
**Market:** Singapore (SG)  
**Direction:** Long  
**Horizon:** 1-2 months (quarterly cycle)  
**Target Win Rate:** 65-75%

---

## Core Idea

Singapore REITs (S-REITs) exhibit predictable price patterns around dividend ex-dates. Buy before ex-date, capture dividend + potential price recovery.

**The Edge:**
- S-REITs required to distribute 90% of income (high yields 5-7%)
- Price typically drops by dividend amount on ex-date
- Often recovers within 2-4 weeks post-ex-date
- Retail investors chase yield, creating pre-ex-date run-up

---

## Signal Construction

**Universe:** S-REITs (Singapore REITs)
- A17U.SI (Ascendas REIT)
- C38U.SI (CapitaLand Integrated Commercial Trust)
- M44U.SI (Mapletree Logistics Trust)
- N2IU.SI (Mapletree Commercial Trust)
- ME8U.SI (Mapletree Industrial Trust)
- BUOU.SI (Frasers Logistics & Commercial Trust)
- RW0U.SI (Keppel DC REIT)
- AJBU.SI (Keppel Infrastructure Trust)

**Dividend Calendar:**
- Most S-REITs pay quarterly
- Ex-dates clustered in Jan/Feb, Apr/May, Jul/Aug, Oct/Nov

**Entry (1-2 weeks before ex-date):**
```python
IF days_to_ex_date <= 14 AND days_to_ex_date >= 3:
    # Avoid last 3 days (too late, price already ran up)
    Buy REIT
    Hold through ex-date
    Exit 2-4 weeks after ex-date (recovery)
```

**Enhanced Filter:**
```python
# Higher conviction if:
- Dividend yield > 5%
- Price momentum positive (20-day MA sloping up)
- No rights issue announced
- Occupancy rate > 90% (check quarterly reports)
```

---

## Expected Performance

| Component | Return |
|-----------|--------|
| Dividend capture | 1.5-2.5% quarterly (6-10% annualized)
| Price recovery | 0.5-1.5% (post ex-date drift)
| **Total** | **8-12% annualized** |
| Win Rate | 65-75% |
| Sharpe | 1.2-1.6 |

**Risks:**
- Price doesn't recover (market downturn)
- Rights issue announced (dilution)
- Interest rate rise hurts REITs

---

## Data Requirements

- **Dividend calendar:** Ex-dates, payment dates
- **Historical prices:** 5 years for pattern analysis
- **REIT fundamentals:** NAV, occupancy, gearing ratio
- **Interest rates:** SOR, Fed funds rate (REIT sensitivity)

**Sources:**
- SGX website (dividend announcements)
- REITsFacts (S-REIT data aggregator)
- Individual REIT investor relations

---

## Academic Support

- Ong et al. (2020): S-REIT dividend persistence
- Sing et al. (2021): Interest rate sensitivity of S-REITs
- REIT Association of Singapore annual reports

---

## Best Candidates

| REIT | Ticker | Yield | Sector | Quality |
|------|--------|-------|--------|---------|
| Ascendas | A17U.SI | 5.5% | Industrial/Logistics | High |
| CapitaLand ICT | C38U.SI | 4.8% | Retail/Office | High |
| Mapletree Log | M44U.SI | 5.2% | Logistics | High |
| Keppel DC | RW0U.SI | 4.2% | Data Centers | High (growth) |

**Avoid:**
- Hospitality REITs (too cyclical)
- High gearing (>40%)
- Declining occupancy trends

---

## Implementation

**Quarterly Routine:**
1. Check upcoming ex-dates (2 weeks ahead)
2. Screen for yield > 5%, positive momentum
3. Enter 7-14 days before ex-date
4. Hold through ex-date
5. Exit 2-4 weeks after (or when price recovers)

**Risk Management:**
- Max 10% portfolio in REITs
- Diversify across sectors (industrial, retail, data center)
- Cut loss if -5% from entry

---

*Quarterly yield capture from Singapore REITs.*
