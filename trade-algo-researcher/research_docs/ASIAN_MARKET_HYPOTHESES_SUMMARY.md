# Asian Market Hypotheses - Complete Set

**Date:** 2026-02-18  
**Markets Covered:** Hong Kong (HK), China (CN), Singapore (SG)  
**Total Hypotheses:** 12 (5 original + 5 new + 2 from prior)

---

## Validated & Deployable

### 1. RSI_MeanReversion_HK ⭐ UNIVERSAL
- **Status:** ACTIVE (20 tickers)
- **Win Rate:** 61%
- **Universe:** 0700.HK, 1299.HK, 0388.HK, 0005.HK, etc.
- **Entry:** RSI < 30 + volume spike
- **Hold:** 5 days

### 2. 3Day_Reversal_HK
- **Status:** ACTIVE (21 tickers)
- **Win Rate:** 61%
- **Universe:** 0005.HK, 1044.HK, 1299.HK, etc.
- **Entry:** 3 down days + >5% decline + volume
- **Hold:** 3 days

### 3. Gap_Fade_HK
- **Status:** ACTIVE (24 tickers)
- **Win Rate:** 62%
- **Universe:** 1044.HK, 0006.HK, 0002.HK, etc.
- **Entry:** Gap >0.5%
- **Hold:** 1 day

### 4. MACD_Divergence_HK
- **Status:** ACTIVE (16 tickers)
- **Win Rate:** 58%
- **Universe:** 0700.HK, 1211.HK, 1810.HK, etc.
- **Entry:** MACD histogram divergence
- **Hold:** 5 days

### 5. Momentum_20Day_HK
- **Status:** ACTIVE (8 tickers)
- **Win Rate:** 60%
- **Universe:** 0700.HK, 1810.HK, 1211.HK, etc.
- **Entry:** 20-day momentum >5%
- **Hold:** 20 days

---

## New Hypotheses (Pending Testing)

### 6. AH Premium Arbitrage (HK + CN)
**Concept:** Trade dual-listed China A-share/H-share premium

**Signal:** Long H-shares when AH premium > 30%
**Universe:** 2318.HK/601318.SH, 1398.HK/601398.SH, 0939.HK/601939.SH
**Target:** 60-70% win, 1.0-1.5 Sharpe
**Horizon:** 1-4 weeks
**Data:** Dual-listed prices, HKD/CNY rates

**Key Insight:** A-shares trade at 20-40% premium; mean reverts at extremes

---

### 7. Singapore REIT Dividend Capture (SG)
**Concept:** Buy S-REITs before ex-date, capture dividend + recovery

**Signal:** Enter 7-14 days before ex-date
**Universe:** A17U.SI, C38U.SI, M44U.SI, N2IU.SI, ME8U.SI
**Target:** 65-75% win, 1.2-1.6 Sharpe
**Horizon:** 1-2 months (quarterly)
**Data:** Dividend calendars, REIT fundamentals

**Key Insight:** S-REITs yield 5-7%; price recovers post ex-date within 2-4 weeks

---

### 8. China Policy Announcement Drift (CN + HK)
**Concept:** Trade regulatory/policy announcement drifts

**Signal:** Short bearish policies, long bullish policies within 24-48h
**Universe:** BABA, JD, PDD, NIO, 0700.HK, 9988.HK
**Target:** 60-70% win, 1.2-1.8 Sharpe
**Horizon:** 1-5 days
**Data:** News feeds (Xinhua, SCMP, Caixin), NLP

**Key Insight:** China policy creates 24-48h drift window; underreaction then absorption

---

### 9. HK Property NAV Discount (HK)
**Concept:** Buy developers at discount to NAV, hold for recovery

**Signal:** Price/NAV < 0.60 (40% discount)
**Universe:** 0001.HK, 0016.HK, 0017.HK, 1113.HK
**Target:** 60-65% win, 12-18% annual return
**Horizon:** 3-6 months
**Data:** NAV estimates, HIBOR rates, land sales

**Key Insight:** HK developers trade at 0.4-0.7x NAV; mean reverts with rate cycles

---

### 10. Northbound Stock Connect Flow (HK + CN)
**Concept:** Follow Mainland China money via Stock Connect

**Signal:** Northbound net buy > 50% of ADV, top 10 list
**Universe:** 0700.HK, 3690.HK, 9988.HK, 2318.HK, 1299.HK
**Target:** 58-62% win, 0.9-1.2 Sharpe
**Horizon:** 1-2 weeks
**Data:** HKEX Stock Connect daily flows

**Key Insight:** Northbound flows persist 1-2 weeks; momentum from China retail/institutional

---

## China-Specific (Prior)

### 11. RSI_MeanReversion_CN ⭐ UNIVERSAL
- **Status:** ACTIVE (14 tickers)
- **Win Rate:** 63%
- **Universe:** PDD, JD, BABA, BEKE, TCEHY, etc.

### 12. 3Day_Reversal_CN
- **Status:** ACTIVE (14 tickers)
- **Win Rate:** 59%
- **Universe:** PDD, BEKE, TCEHY, BABA, JD, etc.

---

## Summary by Market

| Market | Active Strategies | Pending Tests | Key Themes |
|--------|-------------------|---------------|------------|
| **Hong Kong** | 5 | 3 (AH, Property, Northbound) | Property, China exposure, Stock Connect |
| **China** | 2 | 2 (AH, Policy) | ADRs, Policy-sensitive, Retail-driven |
| **Singapore** | 0 | 1 (REITs) | REITs, Dividend capture |

---

## Data Requirements Summary

| Hypothesis | Primary Data | Source | Cost |
|------------|--------------|--------|------|
| AH Premium | Dual-listed prices, FX | Bloomberg/yfinance | Free-$ |
| SG REIT | Dividend calendars | SGX, REITsFacts | Free |
| China Policy | News feeds | Xinhua, SCMP, Caixin | Free-$ |
| HK Property | NAV estimates | Annual reports, Bloomberg | $ |
| Northbound | Stock Connect flows | HKEX website | Free |

---

## Testing Priority

**High Priority (Free Data):**
1. Northbound Stock Connect (HKEX free data)
2. SG REIT Dividend (SGX free data)
3. AH Premium (yfinance free)

**Medium Priority (News Data):**
4. China Policy (needs news API)

**Lower Priority (Fundamental Data):**
5. HK Property NAV (needs broker reports)

---

## Files

- `ah_premium_arbitrage.md`
- `singapore_reit_dividend_capture.md`
- `china_policy_announcement_drift.md`
- `hk_property_nav_discount.md`
- `northbound_stock_connect_flow.md`

---

*12 Asian market hypotheses: 7 deployable, 5 pending validation*
