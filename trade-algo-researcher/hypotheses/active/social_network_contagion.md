# Hypothesis: Social Network Contagion (LinkedIn for Alpha)

**Status:** testing  
**Created:** 2026-02-18  
**Asset Class:** Equities  
**Direction:** Long hiring momentum  
**Horizon:** 3-6 months  
**Target Win Rate:** 60-65%

---

## Core Idea

LinkedIn job postings predict company growth 6-12 months before earnings reflect it. Hiring surges = growth acceleration. Hiring freezes = slowdown.

**The Edge:**
- Job postings are leading indicator
- LinkedIn data available before earnings
- Most investors don't track hiring
- Works for growth stocks especially

---

## Signal Construction

**Growth Signal:**
```
IF job_postings_3m_change > 30% AND
   job_categories include "Engineering" AND
   vs_sector_avg > 2x
THEN long (growth acceleration)
```

**Slowdown Signal:**
```
IF job_postings_3m_change < -20% AND
   was hiring heavily before
THEN short (growth deceleration)
```

---

## Expected Performance

| Metric | Target |
|--------|--------|
| Win Rate | 60-65% |
| Lead Time | 3-6 months |
| Avg Return | 15-25% over 6 months |
| Sharpe | 1.0-1.5 |

---

## Data Sources

- LinkedIn job postings API
- Indeed hiring data
- Company career pages (scraping)
- Competing job post intelligence (Burning Glass)

---

## Why It Works

1. **Hiring precedes revenue** — Need people to execute growth
2. **Budget approval required** — Hiring = management confidence
3. **Persistent signal** — Can't fake hiring (expensive)
4. **Early warning** — Before earnings guide down

---

## Best For

- Tech growth stocks (hiring = growth)
- Cyclicals (hiring = recovery)
- Avoid: Mature industrials (hiring less predictive)

---

*LinkedIn knows before the CEO tells the street.*
