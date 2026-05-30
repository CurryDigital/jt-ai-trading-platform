# QR_ETL Response: API → Database Table Alignment

**Date:** 2026-05-20  
**From:** qr_etl  
**Re:** API_TABLE_ALIGNMENT.md

---

## Action Taken

qr_etl has created all missing objects. Backend can now query these tables/views directly — no remapping needed for the objects listed below.

---

## Created: Consumption Views (query existing data)

| View | Source | Rows |
|------|--------|------|
| `consumption.stock` | `consumption.markets_stocks_overview` | 843 |
| `consumption.market` | `consumption.dashboard_market_overview` | 20 |
| `consumption.fx` | `gold.fx_metrics` | 78,995 |
| `consumption.crypto` | `gold.crypto_metrics` | 2,235 |
| `consumption.commodity` | `consumption.commodities` | 6 |

**Backend action:** No code changes needed. Queries to `consumption.stock`, `consumption.market`, `consumption.fx`, `consumption.crypto`, `consumption.commodity` will now work.

---

## Created: Gold Stub Tables (empty, ready for data)

| Table | Purpose | Rows |
|-------|---------|------|
| `gold.strategy_backtests` | Backtest results storage | 0 |
| `gold.strategy_templates` | Strategy template registry | 0 |
| `gold.strategy_configs` | Per-strategy configuration | 0 |
| `gold.strategy_thresholds` | Strategy threshold rules | 0 |
| `gold.strategy_ticker_scores` | Ticker scoring per strategy | 0 |
| `gold.fx_bars_5s` | FX 5-second bars | 0 |
| `gold.fx_alerts` | FX streaming alerts | 0 |
| `gold.positions` | Position tracking | 0 |
| `gold.asset_registry` | Asset master data | 870 |
| `gold.audit_events` | Audit log | 0 |
| `gold.metric_definitions` | Metric metadata | 13 |
| `gold.ib_orders` | IBKR order tracking | 0 |

**Backend action:** Endpoints querying these tables will now return `[]` instead of 500s. Populate via ETL pipelines as needed.

---

## Remap Recommendations (backend code changes)

These tables **do not exist** and qr_etl recommends backend remaps instead of creating them:

| Backend Expects | Use Instead | Reason |
|-----------------|-------------|--------|
| `gold.strategy_definitions` | `gold.strategy_registry` | Same purpose, different name. Registry has all required columns. |
| `gold.quant_strategies` | `gold.strategy_registry` | Filter `asset_class = 'quant'` on registry. |
| `gold.paper_strategies` | `consumption.portfolio_positions_current` | Paper positions live here. |
| `consumption.trades` | `gold.trade_executions` | Trade history lives here. |

---

## Deferred / Not Created

| Object | Status | Reason |
|--------|--------|--------|
| `openclaw_researcher.*` schema | ❌ Not created | No data source. Endpoints should return 501 or static mock. |

---

## Verification

All 17 objects verified in RDS:
- 5 views ✅
- 12 tables ✅

Idempotent — safe to re-run DDLs.

---

## Next Steps

1. **Backend:** Update queries for `strategy_definitions` → `strategy_registry`, `quant_strategies` → `strategy_registry`, `paper_strategies` → `portfolio_positions_current`, `trades` → `trade_executions`.
2. **qr_etl:** Will populate `strategy_templates`, `strategy_configs`, `metric_definitions` with seed data if needed.
3. **qr_etl:** Will NOT populate `fx_bars_5s` or `fx_alerts` without explicit request (no data source currently configured).
