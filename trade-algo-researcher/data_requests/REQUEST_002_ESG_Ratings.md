## DATA REQUEST - ESG Ratings History

**From:** Trade Algo Researcher  
**To:** JT Trading Agent (via Jacky)  
**Date:** 2026-02-20  
**Priority:** MEDIUM (hypothesis in TESTING phase)

---

### Data Required

**Table/Schema:** `gold.esg_ratings` (new table needed)  
**Columns:**
- `ticker` (VARCHAR)
- `date` (DATE) - rating date
- `esg_score` (NUMERIC) - overall score
- `environment_score` (NUMERIC)
- `social_score` (NUMERIC)
- `governance_score` (NUMERIC)
- `rating_change` (VARCHAR) - 'upgrade', 'downgrade', 'stable'

**Time Period:** 2018-01-01 to 2024-12-31  
**Frequency:** Monthly or quarterly  
**Universe:** S&P 500, Russell 1000

---

### Purpose

Testing **ESG Improvers hypothesis** (Berkeley Haas 2024 research):
- ESG rating *upgrades* predict outperformance
- NOT ESG levels (which don't work - per 2024 research)
- Need historical rating changes to validate

---

### Blocking Status

☑️ **BLOCKING** - Cannot proceed without this data

Current approach using ESG ETF holdings is a **proxy** and violates policy.

---

### Suggested Source

**Option 1:** MSCI ESG Direct
- Cost: $2,000-5,000/month
- Quality: Gold standard
- History: 10+ years

**Option 2:** Sustainalytics (Morningstar)
- Cost: $1,000-3,000/month
- Quality: Good
- History: 5+ years

**Option 3:** Refinitiv ESG
- Cost: $1,500-4,000/month
- Quality: Good
- History: 7+ years

**Option 4:** Free proxy (REJECTED)
- ❌ ESG ETF holdings - NOT ACCEPTABLE per policy

---

### Acceptance Criteria

- [ ] Monthly/quarterly rating changes for 5+ years
- [ ] Coverage > 80% of S&P 500
- [ ] Clear upgrade/downgrade definitions
- [ ] No survivorship bias

---

### Cost-Benefit

**Cost:** $12,000-60,000/year  
**Benefit:** Validate 1 hypothesis (target Sharpe 0.90)  
**Decision:** User approval required before subscription

---

**Status:** AWAITING BUDGET APPROVAL
