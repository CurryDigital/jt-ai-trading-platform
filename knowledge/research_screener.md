# Research › Screener

**Purpose:** one filterable, sortable master table over the **entire signal
universe** (all markets in a single view) — the "slice & rank everything"
surface. Complements the per-market card view (Signals) and the regime/macro
views (Macro); it deliberately does **not** duplicate them any more.

Filters: market multi-select chips, direction (ALL/BUY/SELL), a min-score
slider (0–100), and a ticker/name search box. Every column header sorts
(toggles asc/desc). A row whose first signal family resolves to a deployed
`strategy_id` is clickable → opens Strategy Detail.

**Component:** `frontend/src/components/ResearchTab.jsx` — poll 5min
(`usePoll`), fetches with `limit=50` so the table has depth to filter.

## APIs

### `GET /api/signals/universe?markets=US,HK,ETF,CRYPTO,FX,METAL&limit=50`
Same endpoint and payload as [research_signals.md](research_signals.md)
(ticker, name, families[], direction, `potential` 0–100 signal score,
change_pct, note, fwd_5d/fwd_20d/fwd_1q). The screener flattens all markets
into one array and applies client-side filter/sort.

### `GET /api/signals/families`
Family → strategy vocabulary (see research_signals.md) — used to resolve a
row's click-through to a strategy.

## Notes / gaps
- `potential` is labeled in the UI as a 0–100 **signal score, not a return**
  (consistent with Signals). Forecast columns (5D/20D/1Q) show "—" and a
  footnote until qr_etl backfills `fwd_*` on `consumption.signal_setups`.
- Previous version rendered a second copy of the Signals cards + Macro regime
  strip (with a "HK Crypto" label bug and debug text exposing the raw API
  path). Replaced by the table; the regime view lives solely in Macro now,
  so `/api/research/regime-forecast/all` and `/api/stocks/all` are no longer
  called from this tab.
- All data-quality guards from the universe endpoint (market reclassification,
  JSON-note flattening, crypto dedupe) apply here automatically. Owner: qr_etl
  for the upstream fixes.
