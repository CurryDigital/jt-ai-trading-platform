# Research › Signals

**Purpose:** stock-level trade candidates per market (US · HK · Crypto · FX ·
Metals), ranked by potential, tagged with the signal families (deployed
strategies) that triggered them. Multi-family confluence gets a ★ badge.
Clicking a row with a deployed family opens that strategy's detail.

**Component:** `frontend/src/components/SignalsTab.jsx` — poll 5min.

## APIs

### `GET /api/signals/universe?markets=US,HK,CRYPTO,FX,METAL&limit=8`
```jsonc
{ "data": { "US": [ { "ticker":"NVDA","name":"NVIDIA",
    "families":["Momentum Breakout","Earnings Drift"],   // keys into /families
    "direction":"BUY|SELL","potential":91,               // 0–100 rank score
    "change_pct":2.1,"note":"20d breakout · RVOL 2.4×" } ] }, "as_of":"..." }
```
Backing: `consumption.signal_setups` (qr_etl, 5min). **Fallback:** when a
market has no `signal_setups` rows, the endpoint derives candidates from
`consumption.stock` (HK), `.crypto`, `.fx`, `.commodities` directly — real
data, heuristic scoring (see `signals.py`). Remove the fallback once
`signal_setups` covers all five markets. Owner: qr_etl.

### `GET /api/signals/families`
```jsonc
{ "data": [ { "key":"Momentum Breakout","label":"Seasonal SUE","strategy_id":"s019",
    "strategy_name":"...","deployed":true,"color":"#3b82f6" } ] }
```
Backing: `gold.signal_families` — the vocabulary bridge between Research and
the strategy registry. `strategy_id` null ⇒ candidate pattern (rendered
muted, no click-through).

## Known gaps
- Fallback-derived rows use generic family tags ("momentum"/"tactical") that
  don't exist in `gold.signal_families` → they render with default color and
  no strategy click-through. Resolves when signal_setups is backfilled.
- `potential` scale differs between real rows (0–100) and some fallback rows
  (tiny fractions bumped to 0.5) — normalize in the ETL, not the UI.
