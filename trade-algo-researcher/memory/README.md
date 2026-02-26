# Memory System — OPTIMIZED (2026-02-26)

## Quick Navigation

| File | Purpose | Updated |
|------|---------|---------|
| [KEY_INSIGHTS.md](KEY_INSIGHTS.md) | Curated wisdom, principles, lessons | Daily |
| [LESSONS_LEARNED.md](LESSONS_LEARNED.md) | Critical errors and how to avoid | As needed |
| [STRATEGY_INDEX.md](STRATEGY_INDEX.md) | Master table of all strategies | After each batch |
| [RESEARCH_LOG_OPTIMIZED.md](RESEARCH_LOG_OPTIMIZED.md) | Chronological experiment log | Daily |
| `2026-02-25.md` | Today's raw log | Real-time |

---

## Directory Structure

```
memory/
├── README.md                    ← You are here
├── KEY_INSIGHTS.md              ← Curated principles (Durable Facts)
├── LESSONS_LEARNED.md           ← Critical errors to avoid
├── STRATEGY_INDEX.md            ← Master strategy table
├── RESEARCH_LOG_OPTIMIZED.md    ← Chronological log
├── 2026-02-25.md                ← Today's raw notes
├── 2026-02-24.md                ← Yesterday (read-only)
│
├── strategies/                  ← Individual strategy files
│   ├── golden/                  ← Golden strategies (70%+ WR)
│   ├── validated/               ← Validated (55-70% WR)
│   ├── pending/                 ← Under test
│   └── rejected/                ← Failed hypotheses
│
└── archive/                     ← Old files (searchable)
    ├── daily/                   ← Old daily logs (>48h)
    ├── REJECTED_HYPOTHESES_CONSOLIDATED.md
    └── [old implementation docs]
```

---

## Daily Workflow

**Write to:** `2026-02-25.md` (current day)  
**Read for context:** `2026-02-24.md` (yesterday)  
**Reference:** `KEY_INSIGHTS.md`, `STRATEGY_INDEX.md`

**Nightly (automated):**
- Archive `2026-02-25.md` → `archive/daily/`
- Extract 5-10 facts → Append to `KEY_INSIGHTS.md`
- Create new `2026-02-26.md`

---

## File Retention

| Type | Location | Retention |
|------|----------|-----------|
| Daily logs | Root | 2 days (today + yesterday) |
| Daily logs | archive/daily/ | 90 days |
| Strategy files | strategies/ | Permanent |
| Curated facts | KEY_INSIGHTS.md | Permanent |

---

## Optimizations Made (2026-02-26)

✅ **Consolidated:** 3 REJECTED_HYPOTHESES files → 1 consolidated  
✅ **Archived:** Old daily logs (2026-02-20, 21, 22, 23 evening, etc.)  
✅ **Archived:** Implementation summaries, architecture docs  
✅ **Organized:** Strategy files into golden/validated/pending/rejected/  
✅ **Created:** This README for navigation  

---

**Next purge:** 2026-03-01 (archive Feb files >7 days)
