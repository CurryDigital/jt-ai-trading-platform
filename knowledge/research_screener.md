# Research › Screener

**Purpose:** flat, filterable universe screener (score/action/market/sector)
plus the all-regions regime strip — the legacy idea-scanning surface kept
alongside the redesigned Macro/Signals/Analytics views.

**Component:** `frontend/src/components/ResearchTab.jsx` — fetch on mount.

## APIs

### `GET /api/stocks/all`
Array (or `{data:[...]}`) of screener rows from the consumption layer:
ticker, name, market, sector, score/action fields, price, change. Backing:
`consumption.stock` / `consumption.markets_stocks_overview` (qr_etl).

### `GET /api/research/regime-forecast/all?horizon=7d`
`{ "horizon":"7d","count":N,"forecasts":[ { "region":"US","forecast_date":"...",
"risk_on_pct":57.1,"risk_off_pct":42.9,"dominant_regime":"RISK_ON|NEUTRAL|RISK_OFF" } ] }`
Backing: `gold.regime_forecast` (`scope`, `day_offset`, `risk_on_pct`).
Classification thresholds: ≥55 RISK_ON, ≤45 RISK_OFF.

### `GET /api/signals/universe?markets=...` (shared with Signals — see
[research_signals.md](research_signals.md)).

## Known gaps
- Screener depends on `consumption.stock` freshness; stale rows show old
  prices with no staleness indicator. Candidate improvement: surface
  `updated_at` per row. Owner: qr_etl (expose column) + qr_frontend (render).
