# QR_FRONTEND API → Database Table Alignment Document

Generated for qr_etl team to align on schema changes.

## Summary

The qr_frontend FastAPI backend references **49 unique tables/views** across the database.
Some tables the backend expects **DO NOT EXIST** in the current RDS schema and need to be
created, renamed, or mapped.

---

## Tables That EXIST in RDS (verified)

| Table | Schema | Status | Notes |
|-------|--------|--------|-------|
| markets_stocks_overview | consumption | EXISTS | Used by market.py, stocks.py |
| markets_commodities_overview | consumption | EXISTS | |
| markets_indices_overview | consumption | EXISTS | View |
| dashboard_market_overview | consumption | EXISTS | |
| portfolio_positions_current | consumption | EXISTS | 11 rows |
| strategy_scores_dynamic | consumption | EXISTS | 502 rows |
| commodities | consumption | EXISTS | 8 rows |
| crypto_funding_snapshot | consumption | EXISTS | 0 rows |
| hft_matrix | consumption | EXISTS | |
| inventory | consumption | EXISTS | |
| global_state | consumption | EXISTS | |
| signal_logs | consumption | EXISTS | 0 rows |
| strategy_registry | gold | EXISTS | Primary strategy table |
| trade_executions | gold | EXISTS | |
| platform_settings | gold | EXISTS | |
| stock_metrics | gold | EXISTS | View |
| crypto_metrics | gold | EXISTS | 2235 rows |
| fx_metrics | gold | EXISTS | 78995 rows |
| commodity_metrics | gold | EXISTS | |
| consensus_ratings | gold | EXISTS | |
| institutional_holdings | gold | EXISTS | |
| hk_ipo_calendar | gold | EXISTS | |
| hk_ipo_details | gold | EXISTS | |
| hk_ipo_performance | gold | EXISTS | |
| sync_schedules | gold | EXISTS | |
| unified_prices | silver | EXISTS | |

---

## Tables That DO NOT EXIST (backend expects them)

| Expected Table | Schema | Used By | Suggested Mapping / Action |
|----------------|--------|---------|---------------------------|
| stock | consumption | metadata.py (/signals/1), strategies.py | **Map to** `consumption.markets_stocks_overview` |
| market | consumption | metadata.py (/signals/1), main.py | **Map to** `consumption.dashboard_market_overview` |
| fx | consumption | metadata.py (/signals/1), fx.py (/pairs) | **Map to** `gold.fx_metrics` or create consumption view |
| crypto | consumption | metadata.py (/signals/1), crypto.py (/all) | **Map to** `gold.crypto_metrics` or create consumption view |
| commodity | consumption | metadata.py (/commodities/all) | **Map to** `consumption.commodities` (note: singular vs plural) |
| trades | consumption | strategies.py, positions.py, main.py | **Map to** `gold.trade_executions` |
| paper_strategies | gold | strategies.py, positions.py, execution.py, main.py | **Map to** `consumption.portfolio_positions_current` |
| strategy_definitions | gold | strategies.py, backtest.py, positions.py, main.py | **Map to** `gold.strategy_registry` (different schema!) |
| quant_strategies | gold | strategies.py, alerts.py, main.py | **Map to** `gold.strategy_registry` or create table |
| strategy_backtests | gold | strategies.py, main.py | **Create or map** — not found in RDS |
| strategy_templates | gold | strategies.py, main.py | **Create or map** — not found in RDS |
| strategy_configs | gold | metadata.py, main.py | **Create or map** — not found in RDS |
| strategy_thresholds | gold | main.py | **Create or map** — not found in RDS |
| strategy_ticker_scores | gold | main.py | **Create or map** — not found in RDS |
| fx_bars_5s | gold | fx.py, main.py | **Create or remove endpoint** — not found in RDS |
| fx_alerts | gold | fx.py, main.py | **Create or remove endpoint** — not found in RDS |
| positions | gold | main.py | **Map to** `consumption.portfolio_positions_current` |
| asset_registry | gold | main.py | **Create or map** — not found in RDS |
| audit_events | gold | main.py | **Create or map** — not found in RDS |
| metric_definitions | gold | main.py | **Create or map** — not found in RDS |
| ib_orders | gold | main.py | **Create or map** — not found in RDS |
| openclaw_researcher.* | openclaw_researcher | main.py (agents) | **Create schema+views or remove endpoints** |

---

## Critical Questions for qr_etl

1. **Should the backend use `gold.strategy_registry` instead of `gold.strategy_definitions`?**
   - `strategy_registry` exists but has different columns (no `jt_ready`, `direction`, `time_horizon`, etc.)

2. **Should `consumption.stock` / `consumption.market` / `consumption.fx` / `consumption.crypto` be created as views?**
   - Or should the backend query `markets_stocks_overview`, `dashboard_market_overview`, `fx_metrics`, `crypto_metrics` directly?

3. **What is the replacement for `gold.paper_strategies`?**
   - `consumption.portfolio_positions_current` has positions but no capital tracking

4. **Should `gold.trade_executions` replace `consumption.trades`?**
   - Backend uses both — should they be unified?

5. **Are the `openclaw_researcher.*` views/tables going to be created?**
   - Used by agent workflow endpoints in main.py

6. **Should missing tables like `strategy_backtests`, `strategy_templates`, `strategy_configs` be created?**
   - Or should those endpoints return static data / empty arrays?

---

## Files and Their Table Dependencies


| File | Tables Referenced |
|------|-------------------|
| alerts.py | gold.quant_strategies |
| backtest.py | gold.strategy_definitions |
| crypto.py | consumption.crypto |
| execution.py | consumption.Portfolio_Positions_Current, gold.paper_strategies, gold.platform_settings, gold.trade_executions |
| fx.py | consumption.fx, gold.fx_alerts, gold.fx_bars_5s |
| hkex.py | gold.hk_ipo_calendar, gold.hk_ipo_details, gold.hk_ipo_performance |
| ibkr.py | gold.paper_strategies, gold.trade_executions, silver.unified_prices |
| market.py | consumption.markets_stocks_overview |
| metadata.py | consumption.commodities, consumption.commodity, consumption.crypto, consumption.fx, consumption.market, consumption.stock, gold.strategy_configs, gold.sync_schedules |
| performance.py | consumption.hft_matrix, consumption.portfolio_positions_current, gold.paper_strategies, gold.strategy_registry, gold.trade_executions |
| positions.py | consumption.portfolio_positions_current, consumption.inventory, gold.paper_strategies, gold.strategy_definitions, gold.strategy_registry, gold.trade_executions, silver.unified_prices |
| stocks.py | consumption.markets_stocks_overview, gold.consensus_ratings, gold.institutional_holdings |
| strategies.py | consumption.trades, gold.paper_strategies, gold.quant_strategies, gold.strategy_definitions, gold.trade_executions |
| main.py | (46 tables — see full list above) |
