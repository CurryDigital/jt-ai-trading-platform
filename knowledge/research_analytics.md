# Research › Analytics

**Purpose:** per-market signal quality: family hit-rates with 5-day forward
returns, proximity-to-trigger watchlist (what's about to fire), and the live
signal feed. Answers "which families are working and what fires next".

**Component:** `frontend/src/components/AnalyticsTab.jsx` — poll 5min.
Layout: one `lg:grid-cols-2` grid (2×2×2, METAL last full row on lg).
Section semantics (shown as hints in the UI): **Performance** = past signal
quality per family; **Proximity** = setups that have NOT fired yet (distance
to trigger); **Feed** = signals that already fired, newest first.

## APIs (all keyed by market: US · HK · CRYPTO · FX · METAL)

### `GET /api/signals/performance?markets=...`
`{ "data": { "US": [ { "family":"Momentum Breakout","hit_rate":64.0,"fwd_return_5d":1.8,"n_trades":218 } ] } }`
Backing: `consumption.signal_performance`. UI colors hit_rate ≥55 green.
`hit_rate` is normalized server-side via `_pct()` (`signals.py`): ETL
currently writes a fraction (0.62) — values ≤1.5 are ×100 so the API always
returns percent. `fwd_return_5d` is signed percent (UI renders +/− with
green/red). The UI additionally guards both `hit_rate` and feed `confidence`
against mixed scales.

### `GET /api/signals/proximity?markets=...`
`{ "data": { "US": [ { "ticker":"AMD","family":"Momentum Breakout","distance_pct":8,"direction":"BUY" } ] } }`
`distance_pct` = % move still required to trigger; UI highlights <15 amber.
Backing: `consumption.signal_proximity`.

### `GET /api/signals/feed?markets=...&limit=4`
`{ "data": { "US": [ { "ts":"14:31","signal":"BUY","ticker":"NVDA","strategy":"Momentum Breakout","confidence":0.86 } ] } }`
Backing: `consumption.signal_feed` (wraps `consumption.signal_logs` with a
market discriminator).

## Known gaps
- Families named here must match `gold.signal_families.family_key` exactly or
  rows render without family context. Owner: qr_etl consistency.
- No click-to-ticket wiring from proximity/feed rows yet (bundle design had
  prefill into the Manual Ticket) — candidate qr_frontend enhancement.
