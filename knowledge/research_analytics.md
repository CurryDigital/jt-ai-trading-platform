# Research › Analytics

**Purpose:** per-market signal quality: family hit-rates with 5-day forward
returns, proximity-to-trigger watchlist (what's about to fire), and the live
signal feed. Answers "which families are working and what fires next".

**Component:** `frontend/src/components/AnalyticsTab.jsx` — poll 5min.

## APIs (all keyed by market: US · HK · CRYPTO · FX · METAL)

### `GET /api/signals/performance?markets=...`
`{ "data": { "US": [ { "family":"Momentum Breakout","hit_rate":64,"fwd_return_5d":1.8,"n_trades":218 } ] } }`
Backing: `consumption.signal_performance`. UI colors hit_rate ≥55 green.

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
