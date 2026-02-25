# Hypothesis: China AH Share Premium Arbitrage

**Status:** testing  
**Created:** 2026-02-18  
**Asset Class:** Equities (Dual-Listed China)  
**Direction:** Neutral  
**Horizon:** Intraday to 1 day  
**Target Sharpe:** 1.5-2.0

---

## Core Idea

Chinese companies listed in both Shanghai (A-shares, local investors) and Hong Kong (H-shares, foreign investors) often trade at different prices. The AH premium/discount fluctuates and mean-reverts.

**Academic Research:**
- "The AH premium: A tale of 'siamese twin' stocks" (ScienceDirect)
- "Information in the A-H Premium" (NYU Stern)
- Premium typically 10-30% (A-shares more expensive)

**Why it exists:**
- Different investor bases (retail vs institutional)
- Capital controls prevent arbitrage
- Information flows asymmetrically

---

## Universe

| A-Share (Shanghai) | H-Share (Hong Kong) | Sector |
|-------------------|---------------------|--------|
| 600519.SS (Kweichow Moutai) | 2916.HK | Alcohol |
| 601888.SS (CTG Duty Free) | 1880.HK | Retail |
| 600036.SS (China Merchants Bank) | 3968.HK | Banking |
| 000001.SZ (Ping An Bank) | Not dual-listed | Banking |
| 002594.SZ (BYD) | 1211.HK | Auto |

---
## Signal

**Deviation:** (A-Share Price - H-Share Price) / H-Share Price

**Historical Range:** 10-30% premium for A-shares

**Trade:**
- When premium >30% → Short A, Long H
- When premium <10% → Long A, Short H

**Hold:** Until premium reverts to 20% mean

---

## Data Requirements

| Data | Source | Notes |
|------|--------|-------|
| A-share prices | yfinance (suffix .SS, .SZ) | Shanghai/Shenzhen |
| H-share prices | yfinance (suffix .HK) | Hong Kong |
| FX rate | yfinance (CNYHKD=X) | Critical for fair comparison |
| Trading hours | Manual | A-shares 09:30-15:00 CST, H-shares 09:30-16:00 HKT |

---

## Risk Factors

1. **Capital controls** — Cannot freely arbitrage between markets
2. **Different settlement** — T+1 A-shares, T+2 H-shares
3. **Currency risk** — CNY vs HKD fluctuation
4. **Liquidity** — Some H-shares are illiquid
5. **Market hours** — Only 2 hours overlap (09:30-11:30 HKT)

---

## Implementation Notes

**For international investors:**
- Cannot directly trade A-shares (need QFII or Stock Connect)
- Can trade H-shares via HKEX

**Alternative approach:**
- Trade A-share ETFs (ASHR, KWEB) vs H-share ETFs (2801.HK)

---

## Academic Basis

- Arquette et al. (2008): "The AH Premium: A Tale of Siamese Twin Stocks"
- Chen et al. (2017): "Information in the A-H Premium" (NYU Stern)
- Chan et al. (2007): "The A-H Share Premium Puzzle"

---

## Next Steps

1. Download A-share and H-share prices
2. Calculate historical premium range
3. Test mean reversion speed
4. Evaluate tradeability for international investors

---

*Requires access to both markets or ETF proxies.*
