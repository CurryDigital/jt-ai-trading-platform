# Backend Database Changes — Required by Data Engineering Agent

This document specifies the **exact DDL changes** the DE agent needs to apply to the
PostgreSQL RDS instance so that the modernized JTCML platform can fully populate the
quant-researcher workspace.

The platform itself is **read-only** by contract — it consumes the gold/consumption
schemas. The DE agent owns ingestion, refresh schedules, and view materialization.
Until these objects exist, the platform falls back to empty data via `safe_query()`
(see `backend/app/db/safe_query.py`), but several views are needed for the UI to be
useful.

---

## Severity Legend

| Symbol | Meaning |
|--------|---------|
| 🔴 | **Blocker** — UI feature is non-functional without it |
| 🟡 | **Important** — UI shows empty state but the feature works degraded |
| 🟢 | **Nice-to-have** — UI shows fallback values |

---

## 1. `gold.strategy_registry` 🔴

**Used by:** `/api/strategies/researcher`, `/api/strategies/pipeline-summary`, Strategies tab, Pipeline visualization in Command Center.

**Status:** **MISSING** — model exists in `backend/app/db/session.py` but no DDL in DB.

**DDL** (already drafted in `db_setup/create_strategy_registry.sql`):

```sql
CREATE TABLE IF NOT EXISTS gold.strategy_registry (
    strategy_id   VARCHAR(10) PRIMARY KEY,
    strategy_name VARCHAR(100),
    version       VARCHAR(10),
    status        VARCHAR(20) DEFAULT 'TESTING',     -- ACTIVE | TESTING | DEPRECATED
    priority      VARCHAR(20) DEFAULT 'EXPERIMENTAL',-- GOLDEN | NEAR_GOLDEN | EXPERIMENTAL
    win_rate      DECIMAL(5,2),                      -- 0–100, percent
    entry_logic   TEXT,                              -- human-readable entry conditions
    exit_logic    TEXT,                              -- human-readable exit conditions
    target_assets TEXT,                              -- comma-separated tickers
    created_at    TIMESTAMP DEFAULT (CURRENT_TIMESTAMP AT TIME ZONE 'UTC' + INTERVAL '8 hours'),
    updated_at    TIMESTAMP DEFAULT now(),
    approved_at   TIMESTAMP,                         -- set when user approves for deploy
    approved_by   VARCHAR(50)                        -- audit trail
);

ALTER TABLE gold.strategy_registry OWNER TO openclaw_user;

CREATE INDEX IF NOT EXISTS idx_strategy_registry_status   ON gold.strategy_registry (status);
CREATE INDEX IF NOT EXISTS idx_strategy_registry_priority ON gold.strategy_registry (priority);
CREATE INDEX IF NOT EXISTS idx_strategy_registry_updated  ON gold.strategy_registry (updated_at DESC);
```

**DE responsibility:**
- Populate from the OpenClaw pipeline whenever `qa_approved` events are emitted.
- Promotion path: `EXPERIMENTAL → NEAR_GOLDEN → GOLDEN`.

---

## 2. Consumption layer views 🔴

These are **read-only views** the platform queries. They do not exist in the current DB.
Each entry below specifies the exact `CREATE VIEW` signature the platform expects.

### 2.1 `consumption.Strategies_Signals_Current` 🔴

**Used by:** `/api/signals/1`, `/api/performance/strategy`, `/api/strategies/{id}/auto-deploy`.

**Expected schema:**

```sql
CREATE OR REPLACE VIEW consumption.Strategies_Signals_Current AS
SELECT
    strategy_id        VARCHAR,    -- FK to gold.strategy_definitions.strategy_id
    ticker             VARCHAR,
    signal             VARCHAR,    -- 'BUY' | 'SELL' | 'HOLD'
    signal_strength    NUMERIC,    -- 0.0 to 1.0
    confidence_score   NUMERIC,    -- 0.0 to 1.0
    entry_price        NUMERIC,
    current_price      NUMERIC,
    stop_loss          NUMERIC,
    take_profit        NUMERIC,
    win_rate           NUMERIC,    -- 0.0 to 1.0
    updated_at         TIMESTAMP
FROM ( ... );  -- DE to source from kpis_metrics + strategy_signal_criteria
```

**DE responsibility:**
- One row per `(strategy_id, ticker)` representing the latest signal evaluation.
- Refresh on KPI ingest cadence (15-min or hourly).

---

### 2.2 `consumption.Strategies_Backtest_Results` 🔴

**Used by:** `/api/strategies/researcher` (enrichment), `/api/performance/strategy`, `/api/strategies/{id}/score`.

**Expected schema:**

```sql
CREATE OR REPLACE VIEW consumption.Strategies_Backtest_Results AS
SELECT
    strategy_id        VARCHAR,
    win_rate           NUMERIC,    -- 0.0 to 1.0
    profit_factor      NUMERIC,    -- gross_profit / gross_loss
    max_drawdown_pct   NUMERIC,    -- positive number (5.2 = 5.2%)
    sharpe_ratio       NUMERIC,
    total_trades       INTEGER,
    total_return_pct   NUMERIC
FROM gold.strategy_backtests;  -- already exists, DE to expose as view
```

**DE responsibility:**
- Wrap the existing `gold.strategy_backtests` table or extend with rolling window calculations.

---

### 2.3 `consumption.Performance_Strategy_Attribution` 🔴

**Used by:** `/api/performance/strategy`, Performance tab.

**Expected schema:**

```sql
CREATE OR REPLACE VIEW consumption.Performance_Strategy_Attribution AS
SELECT
    strategy_id              VARCHAR,
    strategy_name            VARCHAR,
    portfolio_type           VARCHAR,  -- 'SIMULATION' | 'PAPER' | 'LIVE'
    allocated_capital_pct    NUMERIC,
    contribution_pct         NUMERIC,
    return_pct               NUMERIC,
    num_trades               INTEGER,
    win_rate                 NUMERIC,
    sharpe_ratio             NUMERIC
FROM ( ... );  -- DE to derive from gold.paper_strategies + gold.trade_executions
```

---

### 2.4 `consumption.Performance_Monthly_Returns` 🟡

**Used by:** `/api/performance/strategy` (monthly chart).

**Expected schema:**

```sql
CREATE OR REPLACE VIEW consumption.Performance_Monthly_Returns AS
SELECT
    portfolio_type   VARCHAR,
    year             INTEGER,
    month            INTEGER,
    return_pct       NUMERIC
FROM ( ... );
```

---

### 2.5 `consumption.Performance_Portfolio_Summary` 🟡

**Used by:** `/api/performance/strategy` (summary card).

**Expected schema:**

```sql
CREATE OR REPLACE VIEW consumption.Performance_Portfolio_Summary AS
SELECT
    portfolio_type     VARCHAR,
    total_pnl_pct      NUMERIC,
    sharpe_ratio       NUMERIC,
    max_drawdown_pct   NUMERIC,
    win_rate           NUMERIC,         -- 0.0 to 1.0
    total_trades       INTEGER
FROM ( ... );
```

---

### 2.6 `consumption.Portfolio_Positions_Current` 🔴

**Used by:** Portfolio tab, `/api/portfolio/positions`, `/api/inventory/evaluate`.

**Expected schema:**

```sql
CREATE OR REPLACE VIEW consumption.Portfolio_Positions_Current AS
SELECT
    position_id          VARCHAR,
    ticker               VARCHAR,
    name                 VARCHAR,
    asset_class          VARCHAR,
    side                 VARCHAR,    -- 'LONG' | 'SHORT'
    quantity             NUMERIC,
    avg_entry_price      NUMERIC,
    current_price        NUMERIC,
    market_value         NUMERIC,
    weight_pct           NUMERIC,
    unrealized_pnl       NUMERIC,
    unrealized_pnl_pct   NUMERIC,
    strategy_id          VARCHAR,
    strategy_name        VARCHAR,
    days_held            INTEGER,
    entry_date           TIMESTAMP
FROM gold.positions
LEFT JOIN ... ;  -- enrich with current_price from latest market data
```

---

### 2.7 `consumption.Markets_Stocks_Overview` 🟡

**Used by:** `/api/stocks/all`, `/api/signals/1` (LEFT JOIN).

**Expected schema:**

```sql
CREATE OR REPLACE VIEW consumption.Markets_Stocks_Overview AS
SELECT
    ticker, name, sector, market,
    price                    NUMERIC,
    change_pct               NUMERIC,
    volume                   BIGINT,
    trend                    VARCHAR,        -- 'UP' | 'DOWN' | 'NEUTRAL'
    rsi_14                   NUMERIC,
    top_strategy_score       NUMERIC,        -- 0.0 to 1.0
    signal                   VARCHAR,        -- 'BUY' | 'SELL' | 'HOLD'
    signal_strength          NUMERIC,
    pe_ratio                 NUMERIC,
    market_cap               BIGINT
FROM ( ... );
```

---

### 2.8 `consumption.Markets_FX_Overview` 🟡

```sql
CREATE OR REPLACE VIEW consumption.Markets_FX_Overview AS
SELECT
    pair                  VARCHAR,
    bid                   NUMERIC,
    change_pct            NUMERIC,
    trend                 VARCHAR,
    signal                VARCHAR,
    signal_strength       NUMERIC,
    rsi_14                NUMERIC,
    carry_annual_pct      NUMERIC,
    updated_at            TIMESTAMP
FROM gold.fx_metrics ... ;
```

### 2.9 `consumption.Markets_Crypto_Overview` 🟡

```sql
CREATE OR REPLACE VIEW consumption.Markets_Crypto_Overview AS
SELECT
    ticker, name,
    price                 NUMERIC,
    change_pct            NUMERIC,
    change_24h_pct        NUMERIC,
    volume_24h            NUMERIC,
    market_cap            NUMERIC,
    market_cap_rank       INTEGER,
    trend                 VARCHAR,
    signal                VARCHAR,
    signal_strength       NUMERIC,
    rsi_14                NUMERIC,
    funding_rate          NUMERIC,
    fear_greed_index      INTEGER,
    updated_at            TIMESTAMP
FROM gold.crypto_metrics ... ;
```

### 2.10 `consumption.Markets_Commodities_Overview` 🟡

```sql
CREATE OR REPLACE VIEW consumption.Markets_Commodities_Overview AS
SELECT
    ticker, name,
    category              VARCHAR,
    exchange              VARCHAR,
    price                 NUMERIC,
    change_pct            NUMERIC,
    trend                 VARCHAR,
    signal                VARCHAR,
    signal_strength       NUMERIC,
    current_month_bias    VARCHAR,
    next_month_bias       VARCHAR,
    seasonal_strength     NUMERIC,
    updated_at            TIMESTAMP
FROM gold.commodity_metrics ... ;
```

---

### 2.11 `consumption.Dashboard_Market_Overview` 🟢

**Used by:** `/api/macro/pulse` (Command Center macro pulse).

```sql
CREATE OR REPLACE VIEW consumption.Dashboard_Market_Overview AS
SELECT
    region            VARCHAR,    -- 'US' | 'HK' | 'EU' | 'JP'
    index_name        VARCHAR,
    current_value     NUMERIC,
    change_pct        NUMERIC,
    trend             VARCHAR,
    sentiment_score   NUMERIC
FROM gold.index_metrics ... ;
```

---

## 3. OpenClaw `openclaw_researcher` schema 🟢

The Agentic Research tab queries `openclaw_researcher.*` tables that already exist
(see backend rewrite in commit `63553ff`). No changes required, but the DE agent should
ensure these are kept in sync:

- `strategy_workflow` — lifecycle status per strategy
- `events` — append-only event log
- `event_processing` — per-agent processing record
- `routing_rules` — event-to-agent routing
- `strategy_lineage` — experiment reproducibility
- `agent_work_queue` — per-agent pending tasks
- `gold_layer_state` — singleton freshness tracker

---

## 4. New columns the DE agent should add 🟢

### 4.1 `gold.strategy_registry` extra columns

The platform now expects these in `gold.strategy_registry` for richer UX:

| Column | Type | Purpose |
|--------|------|---------|
| `asset_class` | VARCHAR(20) | STOCK / FX / CRYPTO / COMMODITY |
| `direction` | VARCHAR(10) | LONG / SHORT / NEUTRAL |
| `time_horizon` | VARCHAR(20) | 1D / 1W / 1M |
| `max_position_pct` | NUMERIC | Risk cap per position |

These are referenced in `main.py:get_researcher_strategies` with `# TODO: DE to add` comments. The platform will tolerate missing columns (returns `null`), but populating them would surface them in the UI.

### 4.2 Optional: `gold.strategy_definitions.tier`

The Performance tab uses `tier` (e.g., 'T1', 'T2', 'T3', 'T4') for color-coded strategy tiering. Currently sourced from a non-existent column; defaulting to 'T4'. If the DE pipeline can compute a tier (e.g., based on Sharpe + win rate buckets), please add:

```sql
ALTER TABLE gold.strategy_definitions
  ADD COLUMN IF NOT EXISTS tier VARCHAR(4);
```

---

## 5. Performance & freshness expectations

| Endpoint | SLA (P95) | Refresh cadence |
|----------|-----------|-----------------|
| `/api/system/health` | < 100ms | n/a (live) |
| `/api/strategies/researcher` | < 500ms | DE views every 15min |
| `/api/performance/strategy` | < 800ms | DE views every 15min |
| `/api/signals/1` | < 1s | DE views every 5min |
| `/api/macro/pulse` | < 500ms | DE views every 60min |

The frontend ribbon polls `/api/system/health` every 15s, so DB latency must remain low.

---

## 6. Cleanup tasks

The DE agent should also:

1. **Verify `consumption.global_state`** has rows for `category IN ('index','fx','crypto','commodity','stock')` with `timestamp` updated within the last 5 minutes — the platform uses these for the maintenance status indicators.
2. **Drop or alias deprecated views** that are referenced as fallbacks in legacy code:
   - `consumption.Performance_Trades_History` (dropped, code already migrated to `gold.trade_executions`)

---

## 6.1. `gold.audit_events` 🟡

**Used by:** `POST /api/strategies/{id}/promote` and any future write endpoint that mutates platform state (mode changes, capital allocation edits, kill-switch invocations, override-gate overrides).

**Status:** **MISSING** — platform writes to it on mode promotion/demotion. If the table doesn't exist, the platform falls back to a Python `logger.info` line so the operation still succeeds, but the audit history is lost across restarts.

**DDL:**

```sql
CREATE TABLE IF NOT EXISTS gold.audit_events (
    id           BIGSERIAL PRIMARY KEY,
    event_type   VARCHAR(64) NOT NULL,    -- e.g. 'strategy.mode_change', 'kill_switch.fire'
    strategy_id  VARCHAR(32),             -- nullable for global events
    actor        VARCHAR(64),             -- user/agent (NULL for system)
    payload      JSONB NOT NULL,          -- structured event details
    created_at   TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS audit_events_strategy_idx  ON gold.audit_events (strategy_id, created_at DESC);
CREATE INDEX IF NOT EXISTS audit_events_type_idx      ON gold.audit_events (event_type, created_at DESC);
ALTER TABLE gold.audit_events OWNER TO openclaw_user;
```

**Sample payload from `strategy.mode_change`:**

```json
{
  "from": "PAPER_TRADING",
  "to": "LIVE_TRADING",
  "is_promotion": true,
  "gates_passed": true,
  "override_gates": false,
  "metrics": { "backtest": {...}, "live": {...} }
}
```

**Retention:** No platform-side cleanup. Recommend DE keep ≥ 365 days for compliance/post-mortems, archive older to cold storage.

---

## 6.2. `gold.strategy_backtests` 🔴

**Used by:** `/api/backtests/strategies`, `/api/backtests/strategy/{id}`, `/api/backtests/compare`, `/api/strategies/{id}/score`, Backtest Comparator UI tab.

**Status:** **Exists in DB** (created by OpenClaw pipeline), but DE must ensure the schema includes all expected columns.

**Expected schema:**

```sql
CREATE TABLE IF NOT EXISTS gold.strategy_backtests (
    id                BIGSERIAL PRIMARY KEY,
    strategy_id       VARCHAR(32) NOT NULL,
    ticker            VARCHAR(20) NOT NULL,
    market            VARCHAR(20),            -- e.g. 'NYSE', 'HKEX', 'CRYPTO'
    win_rate          NUMERIC,                -- 0.0 to 1.0
    sharpe_ratio      NUMERIC,
    profit_factor     NUMERIC,                -- gross_profit / gross_loss
    total_return      NUMERIC,                -- decimal pct (e.g. 0.15 = 15%)
    max_drawdown      NUMERIC,                -- decimal pct (positive = bad)
    num_trades        INTEGER,
    avg_trade_return  NUMERIC,                -- decimal pct per trade
    current_signal    VARCHAR(10),            -- 'BUY' | 'SELL' | 'HOLD' | NULL
    signal_strength   NUMERIC,                -- 0.0 to 1.0
    entry_price       NUMERIC,                -- suggested entry
    stop_loss         NUMERIC,                -- suggested stop
    target_price      NUMERIC,                -- suggested take-profit
    strategy_score    NUMERIC,                -- 0.0 to 100.0 composite score
    rationale         TEXT,                   -- AI-generated explanation
    calculated_at     TIMESTAMP DEFAULT NOW(),

    CONSTRAINT uq_backtest_strat_ticker UNIQUE (strategy_id, ticker)
);

CREATE INDEX IF NOT EXISTS idx_backtests_strategy   ON gold.strategy_backtests (strategy_id);
CREATE INDEX IF NOT EXISTS idx_backtests_score      ON gold.strategy_backtests (strategy_score DESC NULLS LAST);
CREATE INDEX IF NOT EXISTS idx_backtests_calculated ON gold.strategy_backtests (calculated_at DESC);
ALTER TABLE gold.strategy_backtests OWNER TO openclaw_user;
```

**DE responsibility:**
- Populate from OpenClaw backtest pipeline. One row per `(strategy_id, ticker)`.
- Re-run on schedule (daily or on strategy update).
- The platform reads ALL columns above — missing columns will cause query failures.
- `strategy_score` is the primary sort key for UI ranking.

---

## 6.3. Reconciliation Feature — Table Dependencies 🟢

**Used by:** `/api/reconciliation/positions`, Reconciliation UI tab.

The reconciliation feature cross-checks positions across three sources:
1. `gold.paper_strategies` — **EXISTS** (platform-owned, always populated)
2. `gold.trade_executions` — **EXISTS** (platform writes on fills)
3. IBKR broker account — live connection (optional, not a DB dependency)

**No new DDL required** for reconciliation, but DE should ensure:

- `gold.trade_executions` has columns: `strategy_id`, `ticker`, `execution_mode`, `action` (BUY/SELL), `quantity`, `executed_at`, `pnl`
- `gold.paper_strategies` has columns: `id`, `strategy_id`, `ticker`, `execution_mode`, `entry_price`, `invested_capital`, `unrealized_pnl`, `realized_pnl`, `status`, `created_at`

Both tables are populated by the platform itself on trade events. DE does not need to populate them, but should **not** drop or alter their schemas.

---

## 7. Verification checklist

After DE applies the changes, run these from `psql`:

```sql
-- All required tables/views exist
SELECT table_schema, table_name FROM information_schema.tables
WHERE table_schema IN ('gold', 'consumption')
  AND table_name IN (
    'strategy_registry',
    'strategy_backtests',
    'audit_events',
    'Strategies_Signals_Current',
    'Strategies_Backtest_Results',
    'Performance_Strategy_Attribution',
    'Performance_Monthly_Returns',
    'Performance_Portfolio_Summary',
    'Portfolio_Positions_Current',
    'Markets_Stocks_Overview',
    'Markets_FX_Overview',
    'Markets_Crypto_Overview',
    'Markets_Commodities_Overview',
    'Dashboard_Market_Overview'
  )
ORDER BY 1, 2;

-- Quick smoke test: each view/table returns ≥1 row
SELECT 'registry'    AS v, COUNT(*) FROM gold.strategy_registry
UNION ALL SELECT 'backtests_gold', COUNT(*) FROM gold.strategy_backtests
UNION ALL SELECT 'signals',        COUNT(*) FROM consumption.Strategies_Signals_Current
UNION ALL SELECT 'backtests_view', COUNT(*) FROM consumption.Strategies_Backtest_Results
UNION ALL SELECT 'attribution',    COUNT(*) FROM consumption.Performance_Strategy_Attribution;

-- Verify backtest table has all expected columns
SELECT column_name, data_type FROM information_schema.columns
WHERE table_schema = 'gold' AND table_name = 'strategy_backtests'
ORDER BY ordinal_position;
-- Expected: strategy_id, ticker, market, win_rate, sharpe_ratio, profit_factor,
--           total_return, max_drawdown, num_trades, avg_trade_return,
--           current_signal, signal_strength, entry_price, stop_loss,
--           target_price, strategy_score, rationale, calculated_at

-- Verify trade_executions columns for reconciliation
SELECT column_name FROM information_schema.columns
WHERE table_schema = 'gold' AND table_name = 'trade_executions'
  AND column_name IN ('strategy_id','ticker','execution_mode','action','quantity','executed_at','pnl');
-- Should return 7 rows
```

After verification, the platform's `/api/system/health` should show `status: "healthy"` and populated `counts`.

### API endpoint smoke tests (run from shell):

```bash
# Reconciliation — should return 200 with discrepancy list
curl -s http://localhost:8000/api/reconciliation/positions | jq '.summary'

# Backtest strategies list
curl -s http://localhost:8000/api/backtests/strategies | jq '.count'

# Backtest comparison (use real strategy IDs from above)
curl -s "http://localhost:8000/api/backtests/compare?ids=STR001,STR002" | jq '.strategies | length'
```
