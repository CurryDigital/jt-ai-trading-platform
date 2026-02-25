# Hypothesis: Supply Chain Information Diffusion (Complementary Firms)

**Status:** testing  
**Created:** 2026-02-18  
**Asset Class:** Equities  
**Direction:** Long/Short  
**Horizon:** 1-7 days  
**Target Win Rate:** 60-70%

---

## Core Idea

Customer companies announce earnings that reveal supplier demand. Suppliers haven't reported yet, creating information lag. Market slowly adjusts supplier price over 1-7 days.

**Academic Foundation:**
- **Cohen & Frazzini (2008):** "Economic Links and Predictable Returns"
- Customer earnings predict supplier returns with 1-4 day lag
- 60-70% win rate on supply chain pairs

---

## Supply Chain Pairs

### 1. Cloud AI Demand → GPU Suppliers
| Customer (Lead) | Signal | Supplier (Lag) |
|-----------------|--------|----------------|
| MSFT (Azure AI) | AI capex +50% | NVDA, AMD |
| GOOGL (Cloud) | TPU demand | NVDA |
| AMZN (AWS) | ML training spend | NVDA |
| META | AI infrastructure | NVDA, AMD |

**Mechanism:** Cloud giants report GPU purchases → NVDA demand confirmed → NVDA moves 1-3 days later

---

### 2. E-commerce Growth → Logistics
| Customer (Lead) | Signal | Supplier (Lag) |
|-----------------|--------|----------------|
| AMZN | Shipping volume +20% | UPS, FDX |
| SHOP | Merchant growth | UPS, FDX |
| ETSY | Package volume | UPS |

**Mechanism:** AMZN reports shipping volume → UPS/FDX volume confirmed → Logistics stocks adjust

---

### 3. Streaming Subscribers → Content Creators
| Customer (Lead) | Signal | Supplier (Lag) |
|-----------------|--------|----------------|
| NFLX | Content spend +$10B | PARA, WBD, DIS |
| DIS+ | Subscriber growth | PARA, WBD |
| SPOT | Podcast investment | SIRI, iHeart |

**Mechanism:** NFLX reports spend on content → Studios benefit → Studio stocks lag 1-5 days

---

### 4. Semiconductor Production → Equipment
| Customer (Lead) | Signal | Supplier (Lag) |
|-----------------|--------|----------------|
| TSM | Capex +30% | AMAT, LRCX, KLAC |
| INTC | Fab buildout | AMAT, LRCX |
| MU | Memory capacity | AMAT |

**Mechanism:** TSMC reports capex → Equipment orders confirmed → AMAT/LRCX lag

---

### 5. Travel Booking → Hotels/Airlines
| Customer (Lead) | Signal | Supplier (Lag) |
|-----------------|--------|----------------|
| ABNB | Nights booked +25% | MAR, HLT, HST |
| EXPE | Hotel bookings | MAR, HLT |
| BKNG | Europe demand | Accor (AC.PA) |

**Mechanism:** ABNB reports travel demand → Hotel occupancy confirmed → Hotel REITs adjust

---

### 6. Auto Deliveries → Parts Suppliers
| Customer (Lead) | Signal | Supplier (Lag) |
|-----------------|--------|----------------|
| TSLA | Deliveries +40% | APTV, MGA, BWA |
| GM | EV ramp | APTV, MGA |
| F | F-150 Lightning | Suppliers |

**Mechanism:** TSLA reports deliveries → Auto parts demand → Suppliers lag 1-3 days

---

### 7. Retail Sales → Mall REITs
| Customer (Lead) | Signal | Supplier (Lag) |
|-----------------|--------|----------------|
| TGT | Foot traffic +15% | SPG, BXMT, MAC |
| WMT | Store traffic | SPG, MAC |
| COST | Member visits | BXMT |

**Mechanism:** TGT reports traffic → Mall occupancy confirmed → REITs adjust

---

## Signal Construction

### Entry Rules
1. **Customer earnings beat on key metric** (AI growth, shipping volume, subscribers)
2. **Metric >20% surprise** (strong signal)
3. **T+1 after customer earnings:** Enter long supplier
4. **Hold:** 3-7 days for information diffusion

### Exit Rules
- Time stop: 7 days
- Profit target: 5%
- Stop loss: -3%

---

## Example Trade

**Date:** NVDA reports blowout quarter (AI demand)
**Action:** Long AMD (also benefits, hasn't reported)
**Hold:** 3 days
**Expected:** AMD rises as market digests NVDA's demand signal

---

## Data Requirements

| Data | Source | Frequency |
|------|--------|-----------|
| Earnings dates | yfinance / FMP | Quarterly |
| Earnings surprises | FMP | Real-time |
| Segment reporting | 10-Q filings | Quarterly |
| Supply chain maps | Manual / Bloomberg | Static |

---

## Expected Performance

| Metric | Target |
|--------|--------|
| Win Rate | 60-70% |
| Avg Return | 2-4% per trade |
| Hold Time | 3-7 days |
| Sharpe | 1.2-1.8 |

---

## Risk Factors

1. **Simultaneous reporting:** Both report same day (no lag)
2. **Market efficiency:** Information prices in immediately
3. **Confounding news:** Supplier has own news
4. **Correlation breakdown:** Historical link breaks

---

## Why This Works (When Peer Lag Failed)

**Peer lag failed** because:
- Same sector, same analysts
- Simultaneous news coverage
- ETF arbitrage

**Supply chain works** because:
- Different reporting calendars
- Different analyst coverage
- Real economic dependency
- Information takes time to diffuse

---

## Next Steps

1. Map all supply chain relationships
2. Collect 5 years of earnings data
3. Measure lag between customer and supplier moves
4. Backtest top 10 supply chain pairs

---

## Academic Citations

- Cohen, L., & Frazzini, A. (2008). "Economic Links and Predictable Returns." *The Journal of Finance*, 63(4), 1977-2011.
- Barrot, J.N., & Sauvagnat, J. (2016). "Input Specificity and the Propagation of Idiosyncratic Shocks." *Quarterly Journal of Economics*.

---

*This is the peer lag strategy done right — use economic links, not just sector similarity.*
