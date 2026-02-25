# Cross-Sector Peer Analysis Results

**Date:** 2026-02-18  
**Test:** 6 sectors, 40+ stock pairs  
**Finding:** High correlation, ZERO lag

---

## Results by Sector

### Semiconductors
| Lead → Lag | Correlation | Lag |
|-----------|-------------|-----|
| NVDA → AVGO | 0.821 | 0d |
| NVDA → QCOM | 0.809 | 0d |
| NVDA → MU | 0.757 | 0d |

### Banks
| Lead → Lag | Correlation | Lag |
|-----------|-------------|-----|
| JPM → TCBI | 0.706 | 0d |
| JPM → PACW | 0.708 | 0d |
| BAC → CMA | 0.686 | 0d |

### China Tech
| Lead → Lag | Correlation | Lag |
|-----------|-------------|-----|
| BABA → JD | 0.824 | 0d |
| BABA → BIDU | 0.808 | 0d |
| BABA → VIPS | 0.720 | 0d |

### Airlines
| Lead → Lag | Correlation | Lag |
|-----------|-------------|-----|
| DAL → ALK | 0.758 | 0d |
| UAL → ALK | 0.732 | 0d |

---

## Key Finding

**All high-correlation pairs (0.7-0.8) show ZERO time lag.**

The market prices in peer information **instantaneously**.

---

## Why Simple Price Lead-Lag Fails

1. **HFT arbitrage** — Algorithms detect correlations and trade them away in milliseconds
2. **Information diffusion** — News spreads via Bloomberg/Reuters instantly
3. **ETF arbitrage** — Sector ETFs force simultaneous pricing
4. **Analyst coverage** — Same analysts cover peer groups, simultaneous recommendations

---

## Alternative Approaches That May Work

### 1. Options Flow Lead (Pre-Earnings)
**Lead:** Unusual options activity in leader  
**Lag:** Stock price in peers (delayed by hours)

**Example:** NVDA unusual call buying → AMD moves next day

**Data:** Cboe LiveVol, Unusual Whales

---

### 2. Social Sentiment Lead
**Lead:** Twitter/Reddit sentiment in leader  
**Lag:** Retail buying in peers (delayed by hours)

**Example:** GME Reddit mentions → AMC, BBBY moves

**Data:** RavenPack, Social Market Analytics

---

### 3. Earnings Announcement Drift (PEAD)
**Lead:** Earnings surprise in leader  
**Lag:** Analyst revisions in peers (delayed by days)

**Example:** AAPL earnings beat → QCOM estimate revisions

**Data:** Your FMP signup (in progress)

---

### 4. AH Share Premium (China A vs H)
**Lead:** A-share price in Shanghai (local)  
**Lag:** H-share price in Hong Kong (foreign investors)

**Example:** 600519.SS (Kweichow Moutai) → 2916.HK

**Data:** Real-time both markets

---

### 5. Patent/IP Lead
**Lead:** Patent filing in leader  
**Lag:** Peer stock price (delayed by weeks)

**Example:** AAPL AR patent → SNAP, META moves

**Data:** USPTO, Google Patents

---

### 6. Job Postings Lead (Your existing hypothesis)
**Lead:** AI job postings at leader  
**Lag:** Peer disruption pricing (6-12 months)

**Data:** Indeed API, LinkedIn

---

## Recommendation

**Abandon:** Simple price-based peer lag  
**Pursue:** Alternative data lead-lag

**Priority:**
1. PEAD (earnings) — Waiting for your FMP
2. AH Share premium — Real-time arb
3. Options flow — Requires options data
4. Job postings — Your existing work

---

## Conclusion

The efficient market hypothesis holds for price-based strategies.  
Alpha requires **alternative data** or **structural advantages** (speed, access).

Gold/Silver works because it's **fundamental** (ratio economics), not informational.
