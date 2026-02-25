# Memory Directory README
**Optimized 4-Level Memory Architecture**  
**Last Updated:** 2026-02-23

---

## 📁 Directory Structure

```
memory/
├── README.md                    ← This file
├── STRATEGY_INDEX.md            ← Master strategy table (START HERE)
├── RESEARCH_LOG_OPTIMIZED.md    ← Experiment chronology
├── KEY_INSIGHTS.md              ← Curated wisdom
├── 2026-02-23.md                ← Current daily log
├── strategies/                  ← Individual strategy files
│   ├── COIN_Strong_Uptrend_GOLD.md
│   ├── MSTR_SPY_Regime.md
│   └── ... (9 more)
├── archive/                     ← Old files (>7 days)
│   ├── 2026-02-23_RAW.md
│   ├── AGGREGATED_*.md
│   └── ...
└── deployments/                 ← Deployment specs
```

---

## 🎯 How to Use This Structure

### For Quick Status Check
→ **Start with:** `STRATEGY_INDEX.md`

Shows all 12 strategies in table format with win rates, status, and links.

---

### For Understanding What Happened Today
→ **Read:** `2026-02-23.md`

Brief daily notes with links to detailed files. No duplication.

---

### For Finding a Specific Experiment
→ **Search:** `RESEARCH_LOG_OPTIMIZED.md`

Table format with tags (#breakthrough, #correction, etc.). Filter by track or outcome.

---

### For Learning General Principles
→ **Study:** `KEY_INSIGHTS.md`

Curated wisdom that applies across strategies. "Why things work" not "what works."

---

### For Strategy Details
→ **Open:** `strategies/{strategy_name}.md`

Individual files with full specs, backtests, deployment configs.

---

## 📊 File Purposes

| File | Purpose | Update Frequency | Lifespan |
|------|---------|------------------|----------|
| `STRATEGY_INDEX.md` | Master table of all strategies | After each discovery | Permanent |
| `RESEARCH_LOG_OPTIMIZED.md` | Experiment chronology | After each test | Permanent |
| `KEY_INSIGHTS.md` | Generalizable learnings | When insights emerge | Permanent |
| `2026-02-23.md` | Today's notes | Throughout day | 7 days → archive |
| `strategies/*.md` | Detailed strategy docs | When strategy changes | Permanent |
| `archive/*` | Old files | Weekly (Mondays) | Permanent but hidden |

---

## 🏷️ Tag System

Use tags for filtering in RESEARCH_LOG:

- `#breakthrough` — Major alpha discovery (e.g., COIN 93.3%)
- `#correction` — Fixed wrong finding (e.g., 100% → 85.7%)
- `#exploration` — New hypothesis tested
- `#refinement` — Improved existing strategy
- `#expansion` — Cross-asset testing
- `#rejected` — Didn't work (important to log!)

---

## 🔄 Workflow

### Daily (During Session)
1. Take notes in `2026-02-23.md` (brief, links only)
2. Update `STRATEGY_INDEX.md` if new strategy discovered
3. Add row to `RESEARCH_LOG_OPTIMIZED.md` per experiment

### End of Day
1. Update any changed strategy files in `strategies/`
2. Add to `KEY_INSIGHTS.md` if generalizable learning
3. Commit/push changes

### Weekly (Monday 09:00 HKT)
1. Archive daily logs > 7 days to `archive/`
2. Update strategy statuses (testing → deployed, etc.)
3. Verify paper trading vs backtest results
4. Promote validated → Golden if threshold met

---

## 📈 Current Status (2026-02-23)

| Metric | Count |
|--------|-------|
| Golden Strategies (70%+) | 6 |
| Near-Golden (65-70%) | 3 |
| Validated (55-65%) | 3 |
| **Total Working** | **12** |
| Rejected | 4 |
| Experiments Logged | 15 |
| Breakthroughs | 3 |

---

## 🔗 Quick Links

**Start Here:**
- [STRATEGY_INDEX.md](STRATEGY_INDEX.md) — All strategies

**Today's Work:**
- [2026-02-23.md](2026-02-23.md) — Session notes

**Learn From Past:**
- [RESEARCH_LOG_OPTIMIZED.md](RESEARCH_LOG_OPTIMIZED.md) — All experiments
- [KEY_INSIGHTS.md](KEY_INSIGHTS.md) — General principles

**Strategy Details:**
- [strategies/COIN_Strong_Uptrend_GOLD.md](strategies/COIN_Strong_Uptrend_GOLD.md) — Newest (93.3%)
- [strategies/Crypto_SPY_Regime.md](strategies/Crypto_SPY_Regime.md) — Comparison

**Archive:**
- [archive/](archive/) — Old files

---

## ✅ Migration Complete

**Old Files Archived:**
- `2026-02-23_RAW.md` (bloated original)
- `AGGREGATED_*.md` (duplicates)
- Various appendices (consolidated)

**New Files Created:**
- `STRATEGY_INDEX.md` — Master table
- `RESEARCH_LOG_OPTIMIZED.md` — Experiment log
- `KEY_INSIGHTS.md` — Curated wisdom
- `2026-02-23.md` — Clean daily notes

**Preserved:**
- All strategy files in `strategies/`
- All research findings
- All backtest results

---

*Optimized structure reduces duplication and improves findability*  
*Questions? See MEMORY_OPTIMIZATION_PROPOSAL.md for rationale*