# Research Architecture: Three-Layer Framework

**Version:** 1.0  
**Date:** 2026-02-16  
**Purpose:** Separate production strategies from research hypotheses and market intelligence

---

## The Three Layers

```
┌─────────────────────────────────────────────────────────────────┐
│  LAYER 1: STRATEGIES (Golden) — Ready for Deployment           │
│  Status: Backtested → Paper → Live                             │
│  Format: Deployment-ready with full specifications             │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  LAYER 2: HYPOTHESES (Research) — Work in Progress             │
│  Status: Idea → Testing → Validation → Strategy candidacy      │
│  Format: Experimental, notes, partial data                     │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  LAYER 3: NEWS (Market Intelligence) — Raw Signal Feed         │
│  Status: Continuous monitoring → Hypothesis trigger            │
│  Format: Events, macro, key people, geopolitical               │
└─────────────────────────────────────────────────────────────────┘
```

---

## Layer 1: Strategies (Golden)

**Definition:** Production-ready strategies with complete validation  
**Location:** `/strategies/golden/`  
**Status Levels:**
- `backtested` — Validated on historical data
- `paper` — Deployed on IBKR paper account
- `live` — Deployed on live account

### Required Components

Each golden strategy must include:

```
strategies/golden/
├── [strategy_name]/
│   ├── strategy_spec.md       # Complete specification
│   ├── implementation.py      # Production code
│   ├── backtest_results.json  # Historical performance
│   ├── performance_live.json  # Live/paper results (if deployed)
│   └── deployment_config.yaml # JT platform integration
```

### Strategy Spec Template

```markdown
# Strategy: [Name]

## Status: [backtested/paper/live]

## Performance Metrics
- Sharpe Ratio: [X.X]
- Max Drawdown: [X%]
- Win Rate: [X%]
- Capacity: [$X million]
- Last Updated: [YYYY-MM-DD]

## Thesis
[Why this works]

## Logic & Rules
[Entry/exit conditions]

## Risk Management
[Position sizing, stops, limits]

## JT Integration
[How to deploy on JT platform]

## Weekly Verification Checklist
- [ ] Performance vs backtest
- [ ] Regime validity check
- [ ] Capacity constraints
- [ ] Correlation drift
```

### Current Golden Strategies

| Strategy | Status | Sharpe | Max DD | Weekly Check |
|----------|--------|--------|--------|--------------|
| ARASO Factor Model | backtested | 2.1-2.6 | <12% | [Pending] |
| Information Arbitrage — Secondary | backtested | 1.5-2.0 | <15% | [Pending] |
| Information Arbitrage — Tertiary | backtested | 1.2-1.8 | <18% | [Pending] |
| DVS Disruption Shorts | hypothesis | — | — | [Pending validation] |

---

## Layer 2: Hypotheses (Research)

**Definition:** Experimental ideas under development  
**Location:** `/hypotheses/active/` and `/hypotheses/archive/`  
**Status Levels:**
- `idea` — Concept only, no data
- `testing` — Being validated with data
- `validated` — Evidence supports thesis
- `rejected` — Evidence contradicts thesis
- `promoted` — Advanced to Strategy candidacy

### Required Components

```
hypotheses/
├── active/
│   └── [hypothesis_name].md
├── validated/
│   └── [hypothesis_name].md
├── rejected/
│   └── [hypothesis_name].md
└── promoted/
    └── [strategy_name]/
        └── strategy_proposal.md
```

### Hypothesis Template

```markdown
# Hypothesis: [Title]

## Status: [idea/testing/validated/rejected/promoted]

## Core Idea
[What we think might be true]

## Evidence So Far
- [Observation 1]
- [Observation 2]

## Testing Plan
1. [Step 1]
2. [Step 2]

## Validation Criteria
[What would prove/disprove this]

## Next Actions
- [ ] [Action 1]
- [ ] [Action 2]

## Confidence
Current weight: [0.0-1.0]
```

### Current Active Hypotheses

| Hypothesis | Status | Weight | Notes |
|------------|--------|--------|-------|
| Job postings lead earnings by 6-12 months | testing | 0.40 | Building dataset |
| Lead-lag sector timing adds 0.3 Sharpe | testing | 0.60 | Needs backtest |
| Panama network effects predictable | idea | 0.50 | Monitoring only |
| Macro regime scaling > stop losses | validated | 0.75 | Ready for promotion |

---

## Layer 3: News (Market Intelligence)

**Definition:** Continuous monitoring of market-moving events  
**Location:** `/news/YYYY-MM/` and `/news/sources/`  
**Categories:**
- **Macro:** Fed, CPI, rates, employment
- **Key People:** Trump, Musk, executives, central bankers
- **Geopolitical:** US-China, elections, conflicts, trade
- **Sector:** AI, semiconductors, energy, finance
- **Corporate:** Earnings, M&A, guidance changes

### Required Components

```
news/
├── 2026-02/
│   ├── 2026-02-16_macro.md
│   ├── 2026-02-16_people.md
│   ├── 2026-02-16_geopolitical.md
│   └── 2026-02-16_sector.md
├── sources/
│   ├── fed_calendar.md
│   ├── earnings_whisper.md
│   └── key_person_tracker.md
└── alerts/
    └── disruption_signals.md
```

### News Entry Template

```markdown
# News: [Category] — [Date]

## Macro
- [Time] [Event] [Impact] [Source]

## Key People
- [Name] [Action] [Relevance] [Source]

## Geopolitical
- [Event] [Region] [Market Impact] [Source]

## Sector
- [Sector] [News] [Affected Tickers] [Source]

## Hypothesis Triggers
[Which hypotheses does this news activate?]

## Strategy Implications
[Which golden strategies should respond?]
```

### Key People Tracker

```markdown
# Key People Monitor

## Donald Trump
- Watch: Policy announcements, tariffs, trade
- Sectors: Manufacturing, exporters, trade-sensitive
- Last Update: [Date]

## Elon Musk
- Watch: TSLA, X, AI ventures, government contracts
- Sectors: EV, space, social media
- Last Update: [Date]

## [Add others as needed]
```

---

## Interactions Between Layers

### News → Hypothesis
```
News Event Detected
    ↓
Matches active hypothesis pattern?
    ↓ YES
Update hypothesis weight
Add evidence to hypothesis file
    ↓
Trigger validation if sufficient evidence
```

### Hypothesis → Strategy
```
Hypothesis validated (weight > 0.8)
    ↓
Create strategy_proposal.md
    ↓
Backtest required
    ↓
Backtest results positive (Sharpe > 1.5)
    ↓
Promote to Golden Strategy
Create strategy folder in /strategies/golden/
```

### News → Strategy (Direct)
```
News Event
    ↓
Matches golden strategy activation criteria?
    ↓ YES
Generate trading signal
Update position recommendations
Alert in Telegram summary
```

---

## Weekly Verification Protocol

### Every Monday 09:00 HKT

#### 1. Golden Strategies Review
For each strategy in `/strategies/golden/`:
- [ ] Compare live/paper performance vs backtest
- [ ] Check regime validity (VIX, yield curve, correlations)
- [ ] Verify capacity constraints not exceeded
- [ ] Test correlation drift vs benchmark
- [ ] Update strategy status if needed

#### 2. Hypotheses Review
For each hypothesis in `/hypotheses/active/`:
- [ ] Update weight based on new evidence
- [ ] Check if validation criteria met
- [ ] Promote to `validated` or `rejected`
- [ ] Archive if rejected

#### 3. News Sources Check
- [ ] Update macro calendar
- [ ] Review key people activity
- [ ] Scan for disruption signals
- [ ] Generate hypothesis triggers

---

## Cron Job Integration

### Daily Triggers

**21:30 HKT — US Market Open:**
1. Scan News layer for overnight events
2. Check if News triggers any Hypotheses
3. Generate signals from Golden Strategies
4. Post summary to Telegram

**09:15 HKT — HK Market Open:**
1. Review full US session News
2. Update Hypotheses with new evidence
3. Execute Golden Strategy signals
4. Post summary to Telegram

### Weekly Trigger

**Monday 09:00 HKT — Weekly Verification:**
1. Run full Golden Strategies review
2. Promote validated Hypotheses
3. Archive rejected Hypotheses
4. Generate weekly research report

---

## Directory Structure Summary

```
trade-algo-researcher/
├── strategies/
│   ├── golden/              # Production-ready strategies
│   │   ├── araso_factor_model/
│   │   ├── information_arbitrage_secondary/
│   │   └── information_arbitrage_tertiary/
│   └── archive/             # Deprecated strategies
├── hypotheses/
│   ├── active/              # Work in progress
│   ├── validated/           # Evidence supports
│   ├── rejected/            # Evidence contradicts
│   └── promoted/            # Moving to strategy
├── news/
│   ├── 2026-02/             # Monthly news logs
│   ├── sources/             # Tracking lists
│   └── alerts/              # Disruption signals
└── research_docs/
    └── three_layer_framework.md  # This file
```

---

## Implementation Checklist

- [ ] Create `/strategies/golden/` directory
- [ ] Move ARASO to golden status
- [ ] Create `/hypotheses/active/` directory
- [ ] Migrate existing hypotheses
- [ ] Create `/news/` directory structure
- [ ] Set up Key People tracker
- [ ] Update cron jobs for three-layer flow
- [ ] Create weekly verification script
- [ ] Document promotion criteria

---

*Framework Version: 1.0*  
*Principle: Clear separation between production, research, and intelligence*
