# Backend Database Changes v2 — Required by Data Engineering Agent (qr_etl)

Companion to the original `BACKEND_DB_CHANGES.md`. This file specifies the **new and changed**
DB objects the **redesigned** JTCML workspace needs (Command home, Research Macro/Signals/Analytics
across US·HK·Crypto·FX·Metals, Execution Live/Paper/Ops, Settings).

Same contract as before: the **platform is read-only** over `gold` / `consumption`. The DE agent
(qr_etl) owns ingestion, refresh schedules, and view materialization. Until these objects exist,
the platform degrades through `safe_query()` to empty data (HTTP 200), so nothing 500s — but the
new surfaces stay empty.

Endpoint mapping for every object below is in the companion **`API_SPEC_v2.md`**.

---

## Severity Legend

| Symbol | Meaning |
|--------|---------|
| 🔴 | **Blocker** — UI feature is non-functional without it |
| 🟡 | **Important** — UI shows empty state but the feature works degraded |
| 🟢 | **Nice-to-have** — UI shows fallback values |

All objects are owned by `openclaw_user` and live in `gold` (source-of-truth tables) or
`consumption` (read-only views the platform queries). Timestamps follow the existing
`CURRENT_TIMESTAMP AT TIME ZONE 'UTC'` convention.

---

## 1. Command / Home

### 1.1 `consumption.account_summary` 🔴
**Used by:** `GET /api/command/overview`, `/api/account/*`.

```sql
CREATE OR REPLACE VIEW consumption.account_summary AS
SELECT
    book               VARCHAR,     -- 'live' | 'paper'
    equity             NUMERIC,
    day_pnl            NUMERIC,
    day_pnl_pct        NUMERIC,     -- percent (1.68 = 1.68%)
    open_pnl           NUMERIC,
    buying_power       NUMERIC,
    cash_pct           NUMERIC,
    gross_exp_pct      NUMERIC,
    net_exp_pct        NUMERIC,
    positions          INTEGER,
    updated_at         TIMESTAMP
FROM ( ... );   -- DE: derive from positions + cash ledger per book
```

### 1.2 `gold.account_nav_daily` 🔴 (table) + `consumption.account_equity_curve` (view)
**Used by:** equity-curve hero on Command. Need ≥ 30 trailing sessions.

```sql
CREATE TABLE IF NOT EXISTS gold.account_nav_daily (
    book        VARCHAR(10) NOT NULL,         -- 'live' | 'paper'
    as_of_date  DATE        NOT NULL,
    equity      NUMERIC     NOT NULL,
    pnl         NUMERIC,
    PRIMARY KEY (book, as_of_date)
);
ALTER TABLE gold.account_nav_daily OWNER TO openclaw_user;

CREATE OR REPLACE VIEW consumption.account_equity_curve AS
SELECT book, as_of_date AS d, equity
FROM gold.account_nav_daily
ORDER BY book, as_of_date;
```
**DE responsibility:** append one row per book at session close (snapshot NAV).

### 1.3 `consumption.attention_queue` 🔴
**Used by:** the Action Center (`/api/command/overview`). This is the single biggest UX win of
the redesign — it must carry **structured severity + impact + CTA target**, not free text.

```sql
CREATE OR REPLACE VIEW consumption.attention_queue AS
SELECT
    item_id       VARCHAR,
    severity      VARCHAR,   -- 'critical' | 'warning' | 'info'
    tag           VARCHAR,   -- 'RISK BREACH' | 'APPROVAL' | 'EXPOSURE' | 'DATA' | 'RESEARCH'
    title         VARCHAR,   -- one-line headline
    impact        VARCHAR,   -- one-line consequence / detail
    target        VARCHAR,   -- 'strategies'|'execution'|'settings'|'research'|'command'
    ref_id        VARCHAR,   -- nullable: strategy_id / order_id the CTA opens
    created_at    TIMESTAMP
FROM ( ... );
```
**DE responsibility:** union the sources the platform already emits/derives —
risk breaches & auto-demotes (from `gold.audit_events` where `event_type='strategy.mode_change'`
with `is_promotion=false`), QA-passed strategies awaiting deploy (`gold.strategy_registry`
where `priority='GOLDEN' AND approved_at IS NULL`), exposure-cap proximity (risk engine),
stale data feeds (`consumption.global_state` freshness), and new research hypotheses
(`openclaw_researcher.agent_work_queue`). Severity/tag/target are assigned per source.

> `pipeline` counts and `deployed_health` reuse the existing `gold.strategy_registry` /
> `pipeline-summary` objects — **no change**.

---

## 2. Market Status band

### 2.1 `consumption.dashboard_indices` 🟡
**Used by:** `/api/markets/indices`. Extends the existing `dashboard_market_overview` with a
**region** discriminator and an intraday sparkline.

```sql
CREATE OR REPLACE VIEW consumption.dashboard_indices AS
SELECT
    sym             VARCHAR,    -- 'SPX','NDX','HSI','HSTECH'
    name            VARCHAR,
    region          VARCHAR,    -- 'US' | 'HK'
    last            NUMERIC,
    change_pct      NUMERIC,
    spark           NUMERIC[],  -- ~12 intraday points, last ≈ last
    updated_at      TIMESTAMP
FROM gold.index_metrics ... ;
```
Redesign is **US + HK only** — drop the prior world-index rows (N225/SX5E/DJI) from the feed.

### 2.2 `consumption.market_breadth` 🟡
**Used by:** `/api/markets/breadth`. Now needs **both** US and HK.

```sql
CREATE OR REPLACE VIEW consumption.market_breadth AS
SELECT region, advancing, declining, unchanged, new_highs, new_lows, updated_at
FROM ( ... );   -- region IN ('US','HK')
```

### 2.3 `consumption.market_sentiment` 🟢 & `consumption.market_movers` 🟢
```sql
CREATE OR REPLACE VIEW consumption.market_sentiment AS
SELECT fear_greed INTEGER, fear_greed_label VARCHAR, vix NUMERIC,
       vix_change_pct NUMERIC, put_call NUMERIC, updated_at TIMESTAMP
FROM ( ... );

CREATE OR REPLACE VIEW consumption.market_movers AS
SELECT direction VARCHAR,   -- 'gainer' | 'loser'
       ticker VARCHAR, change_pct NUMERIC, rank INTEGER, updated_at TIMESTAMP
FROM ( ... );
```

---

## 3. Research → Macro

### 3.1 `consumption.macro_regime_7d` 🔴
**Used by:** `/api/macro/regions`, `/api/macro/global`. Drives the 7-day risk-on bar charts for
**US, HK, CRYPTO, FX, METAL**.

```sql
CREATE OR REPLACE VIEW consumption.macro_regime_7d AS
SELECT
    scope         VARCHAR,   -- 'US'|'HK'|'CRYPTO'|'FX'|'METAL'
    day_offset    INTEGER,   -- 0..6 (Mon→Sun)
    risk_on_pct   NUMERIC,   -- 0..100 ; 50 = neutral
    forecast_date DATE,
    updated_at    TIMESTAMP
FROM gold.regime_forecast ... ;   -- DE: model output (next 7 days)
```

### 3.2 `consumption.macro_kpis` 🟡
```sql
CREATE OR REPLACE VIEW consumption.macro_kpis AS
SELECT scope VARCHAR, ord INTEGER, label VARCHAR, value VARCHAR, updated_at TIMESTAMP
FROM ( ... );   -- e.g. US: ('VIX','13.8'), HK: ('Turnover','HK$118B'), CRYPTO: ('Funding','+12bps')
```
`value` is a **display string** (already unit-formatted) so the UI renders it verbatim.

### 3.3 `consumption.macro_sectors` 🟡
```sql
CREATE OR REPLACE VIEW consumption.macro_sectors AS
SELECT region VARCHAR, sector VARCHAR, perf_pct NUMERIC, ord INTEGER, updated_at TIMESTAMP
FROM ( ... );   -- region IN ('US','HK'); ~9 sectors each, signed daily perf
```

### 3.4 `consumption.macro_events` 🟢
```sql
CREATE OR REPLACE VIEW consumption.macro_events AS
SELECT region VARCHAR, event VARCHAR, event_date VARCHAR, importance VARCHAR, updated_at TIMESTAMP
FROM gold.economic_calendar ... ;   -- importance IN ('High','Med','Low')
```

### 3.5 `consumption.market_news` 🟡
**Used by:** `/api/news`, plus the one-line headline on each Crypto/FX/Metals macro box.

```sql
CREATE OR REPLACE VIEW consumption.market_news AS
SELECT
    market        VARCHAR,    -- 'US'|'HK'|'CRYPTO'|'FX'|'METAL'
    headline      VARCHAR,
    source        VARCHAR,
    tone          VARCHAR,    -- 'bull'|'bear'|'neu'  (FX tone read as USD direction)
    impact        VARCHAR,    -- 'High'|'Med'|'Low'
    tags          VARCHAR[],  -- e.g. {'SPX','NDX'}
    published_at  TIMESTAMP
FROM gold.news_sentiment ... ;
```

---

## 4. Research → Signals & Analytics

### 4.1 `gold.signal_families` 🔴 (table) — the vocabulary bridge
**Used by:** `/api/signals/families`. This is what makes Research and Strategies speak one language.

```sql
CREATE TABLE IF NOT EXISTS gold.signal_families (
    family_key     VARCHAR(40) PRIMARY KEY,   -- 'Momentum Breakout','Mean Reversion',...
    label          VARCHAR(40),               -- short strategy name shown on tags, e.g. 'Seasonal SUE'
    strategy_id    VARCHAR(10),               -- FK→gold.strategy_registry; NULL = candidate pattern
    deployed       BOOLEAN DEFAULT false,
    color          VARCHAR(9),                -- hex for the UI tag
    updated_at     TIMESTAMP DEFAULT now()
);
ALTER TABLE gold.signal_families OWNER TO openclaw_user;
```
Seed mapping (current UI): Momentum Breakout→s019, Earnings Drift→s102, Gap Reversal→s044,
Regime Carry→s071, Macro Breakout→s088; Mean Reversion→(none, `deployed=false`).

### 4.2 `consumption.signal_setups` 🔴
**Used by:** `/api/signals/universe`. Top-N ranked setups per market, **multi-family** (confluence).

```sql
CREATE OR REPLACE VIEW consumption.signal_setups AS
SELECT
    market         VARCHAR,    -- 'US'|'HK'|'CRYPTO'|'FX'|'METAL'
    ticker         VARCHAR,
    name           VARCHAR,
    families       VARCHAR[],  -- ≥1 family_key from gold.signal_families
    direction      VARCHAR,    -- 'BUY'|'SELL'
    potential      NUMERIC,    -- 0..100 ranking score
    change_pct     NUMERIC,
    note           VARCHAR,    -- short rationale, e.g. '20d breakout · RVOL 2.4×'
    updated_at     TIMESTAMP
FROM ( ... );   -- DE: pivot per-ticker signal evaluations into a families[] array
```
`families` as an **array** is the key change — a ticker triggering ≥2 families gets the
confluence badge. UI sorts by `potential` desc and shows top `limit` (default 8).

**4.2.1 Forecast horizon columns (NEW, 🟡)** — add to `consumption.signal_setups`:

```sql
    fwd_5d         NUMERIC,    -- forecast % return over 5 trading days (signed, 1.2 = +1.2%)
    fwd_20d        NUMERIC,    -- forecast % return over 20 trading days
    fwd_1q         NUMERIC,    -- forecast % return over one quarter (~63 sessions)
```
The `/api/signals/universe` endpoint already selects these opportunistically and
degrades to nulls until they exist; the Signals UI renders a Today/5D/20D/1Q grid
in the signal detail modal. Use the model's expected-return output per horizon
(NULL when the model doesn't produce one — do not backfill with zeros).

**4.2.2 Data-quality fixes (🟡, currently patched server-side in `signals.py`):**
- `market` classification: `.HK`-suffixed tickers (e.g. `2800.HK` from
  ETF_HK_Balanced_Trend) currently arrive with `market='US'`.
- `note` must be a short human-readable rationale — some rows currently ship a
  raw JSON blob (`{"seasonality_score": null, ...}`).
- One ticker format per asset — `consumption.crypto` mixes `ADAUSDT` and
  `ADA-USD` for the same coin, producing conflicting BUY/SELL rows.
- `potential` must always be the 0–100 score; HK rows currently arrive with
  unpopulated scoring fields.

### 4.3 `consumption.signal_performance` 🟡
```sql
CREATE OR REPLACE VIEW consumption.signal_performance AS
SELECT market VARCHAR, family VARCHAR, hit_rate NUMERIC, fwd_return_5d NUMERIC,
       n_trades INTEGER, updated_at TIMESTAMP
FROM ( ... );   -- family ∈ gold.signal_families.family_key
```

### 4.4 `consumption.signal_proximity` 🟡
```sql
CREATE OR REPLACE VIEW consumption.signal_proximity AS
SELECT market VARCHAR, ticker VARCHAR, family VARCHAR,
       distance_pct NUMERIC,   -- % move still required to trigger (UI flags < 15)
       direction VARCHAR, updated_at TIMESTAMP
FROM ( ... );
```

### 4.5 `consumption.signal_feed` 🟡
```sql
CREATE OR REPLACE VIEW consumption.signal_feed AS
SELECT market VARCHAR, fired_at TIMESTAMP, signal VARCHAR, ticker VARCHAR,
       strategy VARCHAR, confidence NUMERIC   -- 0.0..1.0
FROM consumption.signal_logs ... ;   -- wrap existing signal_logs, add market discriminator
```

---

## 5. Execution

### 5.1 `gold.manual_orders` 🔴 — **the only platform-write target**
**Used by:** `POST /api/execution/manual-order`, `/api/execution/trades`,
`/api/portfolio/positions` (source='manual').

```sql
CREATE TABLE IF NOT EXISTS gold.manual_orders (
    order_id     VARCHAR(32) PRIMARY KEY,    -- 'm'+epoch from platform
    book         VARCHAR(10) NOT NULL,       -- 'live' | 'paper'
    ticker       VARCHAR(20) NOT NULL,
    market       VARCHAR(8),                 -- 'US' | 'HK'
    asset_class  VARCHAR(12),                -- 'STOCK'|'CRYPTO'|'FX'
    side         VARCHAR(6),                 -- 'LONG'|'SHORT'
    qty          NUMERIC NOT NULL,
    entry_price  NUMERIC,
    limit_price  NUMERIC,                    -- null = market
    status       VARCHAR(16) DEFAULT 'accepted',
    note         VARCHAR(200),
    created_by   VARCHAR(50),
    created_at   TIMESTAMP DEFAULT (CURRENT_TIMESTAMP AT TIME ZONE 'UTC' + INTERVAL '8 hours')
);
ALTER TABLE gold.manual_orders OWNER TO openclaw_user;
CREATE INDEX IF NOT EXISTS manual_orders_book_idx ON gold.manual_orders (book, created_at DESC);
```
**DE responsibility:** fold `manual_orders` into the position/P&L views so manual fills roll into
`consumption.portfolio_positions_current` and the blotter alongside algo positions
(add a `source VARCHAR -- 'algo'|'manual'` column to that view).

### 5.2 Live Ops views 🟡 *(read-only; source from IBKR sync)*
```sql
CREATE OR REPLACE VIEW consumption.execution_order_queue AS
SELECT order_id, ticker, side, qty, order_type, status,   -- pending|working|partially_filled
       venue, submitted_at FROM gold.ib_orders ... ;

CREATE OR REPLACE VIEW consumption.execution_fills AS
SELECT fill_id, order_id, ticker, qty, price, broker_ref,
       matched BOOLEAN,                                    -- reconciled vs broker statement
       filled_at FROM gold.trade_executions ... ;

CREATE OR REPLACE VIEW consumption.ib_gateway_state AS
SELECT connected BOOLEAN, host, port, latency_ms, account, last_heartbeat
FROM gold.ib_gateway_heartbeat ... ;     -- singleton-ish, latest row

CREATE OR REPLACE VIEW consumption.risk_limits AS
SELECT halt_phrase_set BOOLEAN, global_halt BOOLEAN,
       strategy_id, capital_cap_pct, used_pct, updated_at
FROM gold.risk_limits ... ;              -- one row per strategy + a global row
```
> `gold.ib_orders` and `gold.audit_events` were already flagged "create or map" in the original
> doc — they're now **required** (🔴 for `ib_orders` via the Order Queue panel).

---

## 6. Settings

No new tables — Settings reads/writes `gold.platform_settings` (exists) and logs to
`gold.audit_events` (DDL in original doc §6.1). Ensure `platform_settings` has rows for the
sections the UI edits: `ibkr_connection`, `risk_config` (keys: `max_drawdown`, `min_sharpe_oos`,
`high_turnover`, `low_trade_count`), `execution_mode`, `notifications`, `data_sources`, `auth`.

---

## 7. Changed / deprecated

| Object | Change |
|---|---|
| `consumption.dashboard_market_overview` | Add `region` + `spark`; restrict to US/HK → superseded by `dashboard_indices`. Keep as alias one release. |
| `/api/macro/pulse` source | Split into `macro_regime_7d` + `macro_kpis` + `market_news`. |
| `consumption.portfolio_positions_current` | Add `source VARCHAR ('algo'|'manual')`; union in `gold.manual_orders`. |
| `consumption.signal_logs` | Wrap as `signal_feed` with a `market` discriminator. |

---

## 8. Verification checklist

```sql
-- New objects exist
SELECT table_schema, table_name FROM information_schema.tables
WHERE (table_schema, table_name) IN (
  ('consumption','account_summary'), ('gold','account_nav_daily'),
  ('consumption','account_equity_curve'), ('consumption','attention_queue'),
  ('consumption','dashboard_indices'), ('consumption','market_breadth'),
  ('consumption','market_sentiment'), ('consumption','market_movers'),
  ('consumption','macro_regime_7d'), ('consumption','macro_kpis'),
  ('consumption','macro_sectors'), ('consumption','macro_events'),
  ('consumption','market_news'), ('gold','signal_families'),
  ('consumption','signal_setups'), ('consumption','signal_performance'),
  ('consumption','signal_proximity'), ('consumption','signal_feed'),
  ('gold','manual_orders'), ('consumption','execution_order_queue'),
  ('consumption','execution_fills'), ('consumption','ib_gateway_state'),
  ('consumption','risk_limits')
) ORDER BY 1,2;

-- Smoke test: key feeds return rows
SELECT 'indices' v, COUNT(*) FROM consumption.dashboard_indices
UNION ALL SELECT 'breadth(US,HK)', COUNT(*) FROM consumption.market_breadth WHERE region IN ('US','HK')
UNION ALL SELECT 'regime_7d×5',    COUNT(DISTINCT scope) FROM consumption.macro_regime_7d
UNION ALL SELECT 'setups',         COUNT(*) FROM consumption.signal_setups
UNION ALL SELECT 'families',       COUNT(*) FROM gold.signal_families
UNION ALL SELECT 'nav_days',       COUNT(*) FROM gold.account_nav_daily;
```

Expectations: `regime_7d×5` = 5 scopes (US/HK/CRYPTO/FX/METAL), `nav_days` ≥ 30,
`families` ≥ 6, each market in `signal_setups` has rows.

---

## 9. Refresh cadence (DE-owned)

| Object(s) | Cadence |
|---|---|
| account_summary, manual_orders fold-in | 1 min |
| dashboard_indices, market_breadth, sentiment, movers | 15–60 s |
| macro_regime_7d, macro_kpis, macro_sectors, macro_events, market_news | 15–60 min |
| signal_setups, signal_performance, signal_proximity, signal_feed | 5 min |
| account_nav_daily | once at session close |
| execution_* , ib_gateway_state, risk_limits | live (IBKR sync) |
| attention_queue | event-driven (on emit) |
