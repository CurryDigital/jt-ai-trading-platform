# Hypothesis: Supply Chain Reshoring Rotation

**Status:** idea  
**Created:** 2026-02-19  
**Source:** Post-COVID supply chain research (2022-2026 geopolitical trends)  
**Asset Class:** Equities  
**Direction:** Sector rotation  
**Horizon:** 6-18 months  
**Target Win Rate:** 60-65%

---

## Core Idea

Geopolitical tensions (US-China, Russia-Ukraine) + COVID supply shocks = massive reshoring/nearshoring trend. Companies relocating supply chains to friendly countries (Mexico, Vietnam, India, Eastern Europe) benefit from:
1. Government subsidies (CHIPS Act, IRA)
2. Lower geopolitical risk
3. Faster logistics
4. ESG compliance

**Academic Support:**
- Baldwin (2022): "Globalization 2.0" - supply chain restructuring
- IMF (2023): "Geo-economic Fragmentation"
- BIS (2024): "Supply chains and inflation"

---

## Signal Construction

**Reshoring Proxies:**
- Capital expenditure announcements (new US/Mexico facilities)
- Government contract wins (CHIPS Act beneficiaries)
- Mexico industrial real estate (FIBRA data)
- Vietnam manufacturing PMI

**Entry:**
```python
IF company_announces new US/Mexico/Vietnam facility:
    OR wins CHIPS Act / IRA subsidy:
    OR supply_chain_score improves (S&P Global data):
    
    Long stock
    Hold 12-18 months
```

**Sectors:**
- Semiconductors (TSM, NVDA, INTC building US fabs)
- EVs (TSLA, NIO nearshoring)
- Industrials (GE, CAT reshoring)
- Mexico REITs (FIBRAs)

---

## Expected Performance

| Metric | Target |
|--------|--------|
| Annual Return | 15-25% |
| Sharpe | 0.9-1.2 |
| Win Rate | 60-65% |
| Theme Duration | 3-5 years (2023-2028) |

---

## Data Requirements

- **Earnings calls:** Reshoring mentions (NLP)
- **Gov contracts:** CHIPS Act awards (public)
- **Construction data:** Dodge Data & Analytics
- **Trade data:** US-Mexico freight volumes

---

*The great rebalancing.*
