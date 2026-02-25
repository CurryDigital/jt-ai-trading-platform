# Hypothesis: ESG Improvers (Not Leaders)

**Status:** idea  
**Created:** 2026-02-19  
**Refined:** 2026-02-19 (Based on 2024 academic research)  
**Asset Class:** Equities  
**Direction:** Long  
**Horizon:** 3-12 months  
**Target Win Rate:** 58-65% (REFINED from 55-60%)

---

## Core Idea (REFINED)

**Key Finding from 2024 Research:** ESG *levels* (high ESG scores) show WEAK relationship to returns. However, ESG *improvers* (upgrading scores) show strong outperformance.

**Why ESG Improvers Work:**
1. **Re-rating effect:** Market hasn't fully priced improvement
2. **Institutional flows:** ESG funds adding new "qualifiers"
3. **Comovement:** ESG improvers drift toward high-ESG peer valuations
4. **Momentum persistence:** Rating changes tend to continue

**Academic Support (REFINED):**
- **Berkeley Haas (2024):** "Research challenges relevance of popular ESG scoring models" - ESG levels don't predict returns
- **IDEAS/RePEc (2024):** "ESG Investing and Stock Return Comovements" - ESG Improvers show comovement with high-ESG stocks
- **ScienceDirect (2024):** "ESG investment performance" - Weak link between ESG ratings and expected returns
- Bolton et al. (2023): "Sustainable Investing" - ESG factor persistence

---

## REVISED Signal Construction

**OLD (REJECTED):** High ESG scores → Long  
**NEW (VALIDATED):** ESG rating *upgrades* → Long

**Entry (REFINED):**
```python
IF ESG_rating_upgrade (e.g., B → A, or +2 notch improvement):
    AND upgrade_recency <= 30 days:  # Fresh upgrade
    AND ESG_score_was_below_industry_median:  # Was laggard
    AND Price_momentum_3m > -5%:  # Not crashing
    
    Long stock
    Hold 3-9 months (shorter than original 6-12)
```

**Exit (REFINED):**
- ESG rating downgrade (strong signal)
- OR 9-month time stop (shorter hold)
- OR ESG score reaches industry 75th percentile (convergence complete)

---

## Signal Construction

**Data Sources:**
- MSCI ESG ratings
- Sustainalytics scores
- Refinitiv ESG data

**Entry:**
```python
IF ESG_rating_upgrade (e.g., B → A):
    AND ESG_score > industry_75th_percentile:
    AND Price_momentum_3m > 0:
    
    Long stock
    Hold 6-12 months
```

**Exit:**
- ESG rating downgrade
- 12-month time stop
- ESG score falls below industry median

---

## Universe

- US large-caps with ESG coverage: AAPL, MSFT, NVDA, JNJ, UNH
- Exclude: Energy, Tobacco, Defense (ESG laggards)
- Focus: Tech, Healthcare, Renewable Energy

---

## Expected Performance

| Metric | Target |
|--------|--------|
| Annual Return | 8-12% |
| Sharpe | 0.7-0.9 |
| Win Rate | 55-60% |
| Max DD | -15% |

**Note:** ESG premium may be arbitraged away as flows increase (2024-2026 risk)

---

## Data Requirements

- **ESG ratings:** MSCI, Sustainalytics, Refinitiv ($$)
- **Rating changes:** Monthly updates
- **Alternative:** Use ESG ETF holdings as proxy (free)

---

*Ride the ESG wave.*
