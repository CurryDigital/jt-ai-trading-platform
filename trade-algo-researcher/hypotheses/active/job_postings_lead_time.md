# Hypothesis: Job Postings Predict AI Disruption 6-12 Months Early

**Status:** testing  
**Created:** 2026-02-16  
**Last Updated:** 2026-02-16

---

## Core Idea

Job postings for AI-related roles at legacy companies predict 6-12 month product launches. Companies hiring "Principal AI Scientist — Video Generation" are likely building generative AI products that will disrupt their existing business models.

---

## Evidence So Far

- **Adobe case:** Job postings for AI video roles 6 months before Sora announcement
- **Hypothesis:** High-seniority + specific technology = near-term product launch
- **Signal strength:** Seniority × Technology specificity × Role type

---

## Testing Plan

1. **Dataset Building (Weeks 1-4)**
   - Scrape LinkedIn/Bright for AI job postings
   - Track by company, role, seniority, technology
   - Build historical database

2. **Validation (Weeks 5-12)**
   - Correlate job postings with subsequent product announcements
   - Measure time lag (target: 6-12 months)
   - Calculate prediction accuracy

3. **Strategy Development (If Validated)**
   - Build DVS adjustment based on job posting signals
   - Trade companies with high AI hiring + high DVS

---

## Validation Criteria

**Validated if:**
- >70% of high-relevance job postings (score >7/10) result in AI product launch within 6-12 months
- False positive rate <30%

**Rejected if:**
- <50% prediction accuracy
- No correlation between job postings and product launches

---

## Next Actions

- [ ] Deploy job scraper for 20-company watchlist
- [ ] Collect 3 months of job posting data
- [ ] Track product announcements
- [ ] Calculate correlation

---

## Confidence

**Current weight:** 0.40  
**Trend:** Increasing with initial data collection  
**Target for promotion:** 0.80

---

*This hypothesis is in active testing phase. Not ready for strategy promotion.*
