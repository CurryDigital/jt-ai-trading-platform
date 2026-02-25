# MEMORY ARCHITECTURE OPTIMIZATION PROPOSAL
**Date:** 2026-02-23  
**Purpose:** Streamline memory storage for efficient retrieval and prevent duplication

---

## 🎯 CURRENT PROBLEMS

### 1. Duplication
- Same discoveries in `research_log.md` AND `memory/2026-02-23.md`
- Strategy details in both strategy files AND daily logs
- Hard to know which is the "source of truth"

### 2. Growing File Sizes
- `memory/2026-02-23.md` is getting very long with multiple updates
- Hard to scan for specific findings

### 3. Poor Cross-Referencing
- Related strategies not linked
- Can't trace discovery lineage (what led to what)

### 4. No Status Tracking
- Unclear which strategies are deployed vs testing
- No "deprecated" marking for rejected strategies

---

## 🏗️ PROPOSED ARCHITECTURE

### Level 1: Daily Logs (Raw) → `memory/YYYY-MM-DD.md`
**Purpose:** Raw session notes, temporary workspace  
**Lifespan:** 48 hours, then archive  
**Content:** Quick notes, temporary findings, work-in-progress

```markdown
# 2026-02-23 - Session Notes

## Morning (09:15 HKT)
- HK Open analysis complete
- No material news

## Afternoon (14:00 HKT)
- SPY indicators calculated
- Testing regime strategies...

## Evening (21:30 HKT)
- [Link to strategy file] COIN Strong Uptrend discovered
- 93.3% win rate
```

---

### Level 2: Research Log (Chronological) → `research_log.md`
**Purpose:** Time-stamped experiment log  
**Lifespan:** Permanent, append-only  
**Content:** One line per experiment with result

```markdown
| Timestamp | Track | Hypothesis | Result | Key Finding | Strategy File |
|-----------|-------|------------|--------|-------------|---------------|
| 2026-02-23 03:30 | Refinement | COIN 100% win validation | ❌ Fluke | True rate 85.7% | [COIN_SPY_Regime] |
| 2026-02-23 05:00 | Exploration | Market regimes | ✅ Success | +7.6% improvement | [COIN_Strong_Uptrend] |
```

---

### Level 3: Strategy Master Index → `memory/STRATEGY_INDEX.md`
**Purpose:** Single source of truth for all strategies  
**Lifespan:** Permanent, updated as status changes  
**Content:** Table with links to detailed files

```markdown
# Strategy Master Index

## Golden Strategies (70%+ Win Rate)
| Strategy | Win% | Asset | Status | File |
|----------|------|-------|--------|------|
| BB+Monday GOLD | 88.9% | HK Stocks | 🟢 Deployed | [link] |
| Inside Day | 74.4% | Universal | 🟢 Deployed | [link] |
| COIN Strong Uptrend | 93.3% | Crypto | 🟡 Ready | [link] |

## Near-Golden (65-70%)
| Strategy | Win% | Asset | Status | File |
|----------|------|-------|--------|------|
| MSTR + SPY Filter | 81.2% | Crypto | 🟡 Ready | [link] |

## Validated (55-65%)
...

## Rejected
| Strategy | Win% | Reason | File |
|----------|------|--------|------|
| MARA SPY Regime | 44% | No edge | [link] |
```

---

### Level 4: Individual Strategy Files → `memory/strategies/{name}.md`
**Purpose:** Detailed documentation per strategy  
**Lifespan:** Permanent  
**Content:** Full specs, backtest results, deployment config

**Standard Template:**
```markdown
# Strategy_Name
**Asset:**  
**Status:** [Golden/Near-Golden/Validated/Rejected]  
**Discovery:** [Date + Context]

## Performance
| Metric | Value |
|--------|-------|
| Win Rate | X% |
| Trades | N |

## Entry/Exit
...

## Related Strategies
- [Links to similar strategies]

## Changelog
- 2026-02-23: Discovered
- 2026-02-24: Deployed to paper
```

---

## 🔄 WORKFLOW

### Daily Process:
1. **Work in** `memory/2026-02-23.md` (temporary notes)
2. **End of day:** Extract key findings
3. **Update** `research_log.md` (one line per experiment)
4. **Create/Update** strategy file in `memory/strategies/`
5. **Update** `STRATEGY_INDEX.md` (master table)

### Weekly Process (Mondays):
1. Archive daily logs > 7 days to `memory/archive/`
2. Consolidate duplicate entries
3. Update strategy statuses based on paper trading results

---

## 🏷️ TAGGING SYSTEM

Add tags to discoveries for easy filtering:

- `#breakthrough` — Major alpha discovery
- `#correction` — Fixed wrong previous finding
- `#exploration` — New hypothesis tested
- `#refinement` — Improved existing strategy
- `#expansion` — Cross-asset testing
- `#rejected` — Strategy didn't work

**Usage in research_log:**
```markdown
| 2026-02-23 05:00 | Exploration | Market regimes | ✅ Success | #breakthrough +7.6% improvement |
```

---

## 📁 PROPOSED DIRECTORY STRUCTURE

```
memory/
├── 2026-02-23.md                 # Daily log (temporary)
├── 2026-02-24.md                 # Daily log (temporary)
├── STRATEGY_INDEX.md             # Master index (permanent)
├── RESEARCH_LOG.md               # Chronological log (permanent)
├── KEY_INSIGHTS.md               # Curated wisdom (permanent)
├── strategies/
│   ├── BB_Monday_GOLD.md
│   ├── COIN_Strong_Uptrend_GOLD.md
│   ├── MSTR_SPY_Regime.md
│   └── Crypto_SPY_Regime.md      # Master comparison
└── archive/
    └── 2026-02-10.md             # Old daily logs (compressed)
```

---

## ✅ IMPLEMENTATION STEPS

1. **Create** `STRATEGY_INDEX.md` with current 9 strategies
2. **Refactor** `research_log.md` into table format
3. **Add tags** to recent discoveries
4. **Set up** weekly archive cron job
5. **Update** strategy files with standard template

---

## 🎯 BENEFITS

1. **Single Source of Truth** — Strategy_INDEX.md always current
2. **Fast Lookup** — Table format, easy scanning
3. **Traceability** — Research log shows evolution
4. **No Duplication** — Each fact stored once
5. **Scalable** — Won't grow unwieldy over time

---

*Proposal ready for implementation*  
*Date: 2026-02-23*