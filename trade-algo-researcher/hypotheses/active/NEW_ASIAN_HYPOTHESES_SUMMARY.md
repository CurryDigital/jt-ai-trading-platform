# New Asian Market Hypotheses - Research Summary

**Date:** 2026-02-20  
**Research Focus:** China AI/Infra, Singapore Banking, Hong Kong IPOs  
**New Hypotheses:** 3  
**Status:** IDEA → Pending Data

---

## Summary of New Hypotheses

| # | Hypothesis | Region | Asset | Expected Sharpe | Status |
|---|------------|--------|-------|-----------------|--------|
| 1 | **China AI Chip & Infrastructure** | CN/HK | Equities | 1.3-1.8 | IDEA |
| 2 | **Singapore Banking Yield Spread** | SG | Equities | 1.1-1.5 | IDEA |
| 3 | **HK IPO Post-Listing Momentum** | HK | Equities | 0.9-1.3 | IDEA |

---

## Hypothesis 1: China AI Chip & Infrastructure

### Thesis
China's forced domestic AI chip development due to US export bans creates a multi-year investment cycle. State-backed "Big Fund" ($50B+) + SMIC 7nm breakthrough + local cloud demand (Baidu, Alibaba, Tencent) = thematic alpha.

### Key Tickers
**Tier 1 (Chips):** 688981.SS (SMIC), 688012.SS (NAURA), 688256.SS (Hua Hong)  
**Tier 2 (Infra):** 000938.SZ (Inspur), 603019.SS (Sugon)  
**Tier 3 (HK):** 9988.HK (Alibaba), 0700.HK (Tencent), 9866.HK (NIO)

### Signal
Policy announcement → Capex confirmation → Earnings validation → Exit on execution risk

### Data Needs
- Xinhua/State Council policy announcements (NLP)
- Quarterly capex data
- Earnings surprises

### Edge
Policy-driven investment cycles have 18-month predictability; less analyst coverage = alpha

---

## Hypothesis 2: Singapore Banking Yield Spread

### Thesis
Singapore banks (DBS, OCBC, UOB) benefit from Fed rate hikes through NIM expansion. Cyclical play on rate regime with 5-6% dividend yield as downside protection.

### Key Tickers
D05.SI (DBS), O39.SI (OCBC), U11.SI (UOB)

### Signal
Fed/MAS hawkish + NIM expansion + credit quality stable → Long Big 3  
Exit on dovish pivot OR NIM contraction

### Data Needs
- Fed dot plot releases
- MAS policy statements
- Quarterly NIM data
- NPL ratios

### Edge
Rate cycle predictability + high dividend yield + liquid large caps

---

## Hypothesis 3: HK IPO Post-Listing Momentum

### Thesis
HK IPOs exhibit predictable Day 3-15 stabilization patterns due to:
- Retail oversubscription (100x-1000x)
- Greenshoe support
- Cornerstone lockups

### Key Universe
Recent HK IPOs (>HK$5B, <30 days, tech/biotech/consumer)

### Signal
Day 3-5 entry after IPO if:
- Price holding above IPO
- Volume declining (flipping done)
- Retail oversubscription >50x
- Greenshoe active

Exit before Day 20 (lockup risk)

### Data Needs
- HKEX IPO calendar
- Prospectus data (oversubscription, lockup dates)
- Greenshoe exercise announcements

### Edge
Retail-dominated inefficiency + stabilization support = asymmetric upside

---

## Regional Coverage Update

| Region | Before | After | Change |
|--------|--------|-------|--------|
| **China (CN)** | 4 | 5 | +1 (AI Chip) |
| **Hong Kong (HK)** | 5 | 6 | +1 (IPO) |
| **Singapore (SG)** | 1 | 2 | +1 (Banking) |
| **Total Asia** | 12 | 15 | +3 |

---

## Data Requirements Summary

| Hypothesis | Primary Data | Source | Cost | Priority |
|------------|--------------|--------|------|----------|
| CN AI Chip | Policy news, earnings | Xinhua, Tushare | Free | HIGH |
| SG Banking | Earnings, Fed dot plot | SGX, Fed | Free | HIGH |
| HK IPO | IPO calendar, prospectuses | HKEX | Free | MEDIUM |

**All 3 hypotheses can be tested with FREE data sources.**

---

## Testing Priority

1. **SG Banking** (Easiest - only 3 tickers, clear signal, free data)
2. **CN AI Chip** (High impact - thematic macro, more complexity)
3. **HK IPO** (Maintenance - requires ongoing IPO monitoring)

---

## Files Created

| File | Purpose |
|------|---------|
| `china_ai_chip_infrastructure.md` | Full strategy spec |
| `singapore_banking_yield_spread.md` | Full strategy spec |
| `hk_ipo_post_listing_momentum.md` | Full strategy spec |
| `NEW_ASIAN_HYPOTHESES_SUMMARY.md` | This summary |

---

## Next Steps

1. **Register hypotheses** in `hypothesis_registry` table
2. **Collect data** for SG Banking (start here - easiest)
3. **Backtest** SG Banking using 2022-2023 rate cycle
4. **Build CN policy scraper** for AI chip announcements
5. **Monitor** HK IPO calendar for upcoming listings

---

*Research continues. Question everything. Let the data speak.*
