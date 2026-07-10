# Settings

**Purpose:** system & broker configuration behind a left-nav: IBKR
Connection, Trading Config, Risk Config, Notifications, Data Sync, Data
Sources, System Health, Audit Log, Display.

**Component:** `frontend/src/components/SettingsTab.jsx` (+
`IbkrGatewayTester.jsx`, `AuditLog.jsx`).

## APIs

### `GET /api/settings` · `PUT /api/settings/{section}`
Sections: `ibkr_connection, risk_config, execution_mode, notifications,
data_sources, auth, trading_config`. GET returns `{ <section>: {field:value} }`;
PUT body is the section's fields. Storage: `gold.platform_settings` keys
namespaced `settings.<section>.<field>` (JSON values); every PUT logs a
`settings.update` row to `gold.audit_events`.
`risk_config` fields the UI edits: `max_drawdown, min_sharpe_oos,
high_turnover, low_trade_count`.

### `GET /api/settings/data-sources`
`[ { id, category, data_type, primary_source, frequency, last_refreshed, status } ]`
Backing: `consumption.settings_data_sources` (qr_etl) — powers the
last-refreshed freshness table.

### `GET /api/sync/status` · `POST /api/sync/{component}`
Last-sync timestamps per component (stocks/fx/crypto/commodities/earnings/
consensus) from `gold.platform_settings` `last_sync_*` keys; POST triggers a
background refresh.

### `GET /api/execution/global-mode` · `POST /api/execution/global-mode`
Global mode read/write (SIMULATION default). `POST /api/simulation/reset`
wipes sim positions/trades (guarded to SIMULATION mode).

### `GET /api/system/health` — app shell 15s
`{ status, latency_ms, counts:{...}, pipeline:{...} }` — powers the ribbon
latency dot and the System Health section.

## Known gaps
- **Risk Config fields are stored but not consumed** by the promotion gate
  engine (hardcoded `PROMOTION_GATES` in `backend/app/main.py`) nor by the
  auto-demote scanner — wiring them is an open qr_frontend task (documented
  also in strategies_pipeline.md).
- Display section toggles are cosmetic placeholders (not persisted).
