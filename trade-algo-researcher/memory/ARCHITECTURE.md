# Memory Architecture Specification

**Version:** 2.0 — Daily Partition Architecture  
**Date:** 2026-02-16  
**Purpose:** Sliding window memory system with nightly consolidation for quantitative research agent

---

## Core Principle: The Financial Ledger Model

Like a financial ledger, memory is partitioned by day and consolidated nightly:

1. **Daily Log (YYYY-MM-DD.md):** Raw news, scrapes, events for TODAY only
2. **Nightly Wrap:** Summarize day's log into 5-10 "Durable Facts"
3. **Durable Memory (MEMORY.md):** Only consolidated facts (curated, weighted)
4. **Sliding Window:** Full access to Today + Yesterday raw logs only
5. **Archive:** Raw logs >48 hours compressed and archived

**Why this works:**
- **Speed:** Agent reads only today's log + MEMORY.md (not weeks of noise)
- **Cleanliness:** Delete/fix one day's file without breaking the system
- **Accuracy:** Mistakes don't compound; each day starts fresh

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    TIER 1: WORKING MEMORY (Hot)                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │ context.md   │  │ Today +      │  │ MEMORY.md            │  │
│  │ (scratchpad) │  │ Yesterday    │  │ (Durable Facts only) │  │
│  │              │  │ Raw Logs     │  │                      │  │
│  └──────────────┘  └──────────────┘  └──────────────────────┘  │
│  LOADED EVERY SESSION — MAX 48h RAW + CURATED FACTS              │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                TIER 2: NIGHTLY CONSOLIDATION                     │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ Nightly Wrap Process (automated at US Close 05:00 HKT): │    │
│  │ 1. Read Today's raw log                                 │    │
│  │ 2. Extract 5-10 Durable Facts                           │    │
│  │ 3. Validate against price action (if market data avail) │    │
│  │ 4. Append to MEMORY.md with weight + expiry             │    │
│  │ 5. Archive raw log to /memory/archive/daily/            │    │
│  │ 6. Run fact_store.py decay --apply                      │    │
│  └─────────────────────────────────────────────────────────┘    │
│  EXECUTES AUTOMATICALLY — NO MANUAL INTERVENTION                 │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                TIER 3: LONG-TERM STORAGE (Cold)                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │ Archive      │  │ Facts DB     │  │ Gold Metrics         │  │
│  │ /daily/      │  │ (JSONL)      │  │ (PostgreSQL)         │  │
│  │              │  │              │  │                      │  │
│  └──────────────┘  └──────────────┘  └──────────────────────┘  │
│  SEARCH-ONLY — NEVER LOADED WHOLE                                │
└─────────────────────────────────────────────────────────────────┘
```

---

## Tier 1: Working Memory (Always Loaded)

### 1. context.md (Scratchpad)
**Purpose:** Active thought stream—highly condensed, single-screen readable  
**Content:** Core thesis, active hypotheses, immediate priorities, constraints  
**Update:** Real-time during session  
**Access:** Always loaded

### 2. Daily Raw Logs (Sliding Window: 48 Hours)
**Location:**
- `/memory/2026-02-16.md` (Today)
- `/memory/2026-02-15.md` (Yesterday)

**Purpose:** Raw news, scrapes, "Key Person" events, price action observations  
**Content:** Unfiltered observations, hypotheses being tested, temporary notes  
**Access:** Full read/write for Today + Yesterday only  
**Auto-archive:** Raw logs >48 hours moved to `/memory/archive/daily/`

**Daily Log Schema:**
```markdown
# Daily Log: 2026-02-16

## Raw News & Events
- [Time] Event description (source)
- [Time] Price observation (ticker, move, context)

## Key Person Moves
- [Name] [Company] [Action] (sale/purchase/announcement)

## Hypotheses Being Tested
- Hypothesis: [Description]
- Test: [How to validate]
- Expected outcome: [Prediction]

## Price Action Notes
- Ticker: Observation

## Errors/Mistakes
- What went wrong: [Description]
- Lesson: [Takeaway]
```

### 3. MEMORY.md (Durable Facts Only)
**Purpose:** Curated, validated facts with weights and expiry  
**Content:** Only consolidated facts from Nightly Wrap (not raw noise)  
**Update:** Nightly only (via automated consolidation)  
**Access:** Always loaded

**Durable Fact Format:**
```markdown
- **[2026-02-16]** Fact statement (validated against price action) | Weight: 0.85 | Expiry: 2026-08-16
```

---

## Tier 2: Nightly Consolidation (Automated)

### Nightly Wrap Process
**Trigger:** 05:00 HKT (after US market close) via cron  
**Duration:** ~5-10 minutes  
**Output:** 5-10 Durable Facts appended to MEMORY.md

**Consolidation Steps:**

1. **Read Today's Raw Log**
   - Parse `/memory/2026-02-16.md`
   - Extract all observations, events, hypotheses

2. **Validate Against Price Action**
   - Query `aitrading_schema` for today's closes
   - Compare predictions vs actuals
   - Mark validated vs invalidated observations

3. **Extract Durable Facts (5-10 max)**
   - Must be atomic (subject_verb_object)
   - Must have temporal specificity
   - Must be verifiable
   - Examples:
     - ✅ "Adobe dropped 15% on AI fears within 4 hours of Sora announcement"
     - ❌ "AI is disrupting creative software" (too vague)

4. **Assign Metadata**
   - Weight: Based on validation confidence (0.0-1.0)
   - Expiry: When fact becomes stale (3-6 months typical)
   - Source: validation method (price action, earnings, etc.)

5. **Append to MEMORY.md**
   - Add to "Durable Facts" section
   - Maintain chronological order (newest first)

6. **Archive Raw Log**
   - Move `/memory/2026-02-16.md` to `/memory/archive/daily/`
   - Compress (gzip) to save space

7. **Run Fact Decay**
   - Execute `python fact_store.py decay --apply`
   - Archive facts with weight < 0.3

**Consolidation Rules:**
- Maximum 10 facts per day (forced brevity)
- No duplicates (check against existing MEMORY.md)
- Invalidated hypotheses get weight = 0 and archived
- Price-action-validated facts get weight boost (+0.1)

---

## Tier 3: Long-Term Storage (Search-Only)

### 1. Daily Archive
**Location:** `/memory/archive/daily/2026-02-16.md.gz`  
**Content:** Compressed raw logs older than 48 hours  
**Access:** Search-only (never loaded whole)  
**Retention:** 90 days then auto-delete (or move to cold storage)

### 2. Fact Store (JSONL)
**Location:** `/memory/facts/YYYY-MM-DD.jsonl`  
**Format:** Structured atomic facts with metadata  
**Content:** Same as MEMORY.md but machine-readable for queries  
**Access:** `fact_store.py query` command only

**Schema:**
```json
{
  "timestamp": "2026-02-16T16:00:00Z",
  "fact_type": "market_event|hypothesis_validated|disruption_signal|geopolitical_event",
  "entity": "ADBE|TEAM|CKH|NVDA",
  "fact": "Atomic validated statement",
  "confidence": 0.85,
  "validation_method": "price_action|earnings|news_confirmation",
  "weight": 0.85,
  "expiry": "2026-08-16",
  "day_log_ref": "2026-02-16.md:line_42"
}
```

### 3. Gold Metrics (PostgreSQL)
**Location:** `aitrading_schema` in AWS RDS  
**Content:** Computed signals, backtest results, performance metrics  
**Access:** SQL queries only  
**Constraint:** MUST query before finalizing any recommendation

---

## Sliding Window Protocol

### What the Agent Can Access

| Time Window | Access Level | Location |
|-------------|--------------|----------|
| Today (0-24h) | Full R/W | `/memory/2026-02-16.md` |
| Yesterday (24-48h) | Read-only | `/memory/2026-02-15.md` |
| 48h - 90 days | Search-only | `/memory/archive/daily/` (compressed) |
| >90 days | Deleted/archived to cold storage | N/A |

### Daily Workflow

**During HK Open Task (09:15 HKT):**
1. Read `context.md` (always)
2. Read `/memory/2026-02-16.md` (Today's raw log — may be empty)
3. Read `/memory/2026-02-15.md` (Yesterday's raw log)
4. Read `MEMORY.md` (Durable facts)
5. Append observations to Today's raw log
6. Query `aitrading_schema` for gold/FX metrics

**During US Close Task (05:00 HKT):**
1. Execute Nightly Wrap (consolidation)
2. Archive Today's raw log
3. Clear working memory for next cycle

---

## Evidence-Weighted Pruning (Enhanced)

### For Durable Facts (MEMORY.md)

**Initial Weight Assignment:**
```
weight = base_confidence * validation_boost

base_confidence:
- Direct observation: 0.7
- Price action validated: 0.9
- Third-party confirmed: 0.8
- Hypothesis only: 0.5

validation_boost:
- Price action matched prediction: +0.1
- Contradicted by price action: -0.3
- Unvalidated after 7 days: -0.2
```

**Decay Schedule:**
```
weight_today = weight_created * exp(-λ * days)
where λ = 0.01 (69-day half-life)
```

**Archive Thresholds:**
- Weight < 0.3: Move to `/memory/archive/low_confidence/`
- Expiry reached: Move to `/memory/archive/expired/`
- Superseded by new fact: Move to `/memory/archive/superseded/`

---

## Implementation for Developer

### OpenClaw Configuration

Add to `openclaw.json`:
```json
{
  "memory": {
    "type": "sliding_window",
    "window_hours": 48,
    "consolidation": {
      "enabled": true,
      "trigger": "cron",
      "schedule": "0 5 * * *",
      "timezone": "Asia/Hong_Kong",
      "max_facts_per_day": 10,
      "archive_raw_logs": true
    },
    "tiers": {
      "hot": ["context.md", "MEMORY.md", "today_raw", "yesterday_raw"],
      "warm": ["facts_jsonl"],
      "cold": ["archive_daily", "archive_facts"]
    },
    "constraints": {
      "query_database_before_recommendation": "aitrading_schema",
      "max_raw_log_age_hours": 48,
      "auto_archive": true
    }
  }
}
```

### File System Layout

```
memory/
├── 2026-02-16.md              # Today (hot) — R/W
├── 2026-02-15.md              # Yesterday (hot) — Read-only
├── context.md                 # Working scratchpad (hot)
├── MEMORY.md                  # Durable facts (hot)
├── facts/
│   ├── 2026-02-16.jsonl      # Today's facts (warm)
│   └── index.json            # Fact index
├── archive/
│   ├── daily/
│   │   ├── 2026-02-14.md.gz  # Compressed raw logs (cold)
│   │   └── 2026-02-13.md.gz
│   ├── low_confidence/       # Decayed facts
│   ├── expired/              # Past expiry
│   └── superseded/           # Better evidence exists
└── episodes/                 # Special events (rare)
    └── index.md
```

### Agent Prompt (System Message)

```
You are a quantitative research agent with sliding window memory.

HOT MEMORY (Always Loaded):
- context.md: Your working scratchpad
- MEMORY.md: Durable facts only (consolidated nightly)
- Today + Yesterday raw logs: 48h window

CONSTRAINTS:
1. You have FULL ACCESS to Today and Yesterday's raw logs
2. Anything older than 48 hours is ARCHIVED — search only, never load whole
3. Before finalizing recommendations, QUERY aitrading_schema for latest gold/FX metrics
4. At US Close (05:00 HKT), you automatically run Nightly Wrap:
   - Extract 5-10 Durable Facts from today's raw log
   - Validate against price action
   - Append to MEMORY.md
   - Archive today's raw log
   - Run fact decay

NEVER assume continuity across days. Each session is fresh.
```

---

## Migration from v1.0 to v2.0

### For Existing Agents

1. **Archive existing old logs:**
   ```bash
   # Compress all logs >48 hours
   find memory/ -name "2026-*.md" -mtime +2 -exec gzip {} \;
   mv *.gz memory/archive/daily/
   ```

2. **Consolidate existing facts:**
   ```bash
   # Review last 7 days, extract best facts
   python fact_store.py consolidate --days 7 --output MEMORY.md
   ```

3. **Enable nightly cron:**
   ```bash
   openclaw cron add --name "Nightly_Wrap" --cron "0 5 * * *" --message "Execute nightly consolidation"
   ```

---

*Architecture Version: 2.0 — Daily Partition with Sliding Window*  
*Last Updated: 2026-02-16*  
*Next Review: After 30 days operational experience*
