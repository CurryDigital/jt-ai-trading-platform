# Research › Signals

**Purpose:** stock-level trade candidates per market (US · HK · ETF · Crypto ·
FX · Metals), ranked by **signal score** (0–100 strength from the signal
engine — explicitly *not* a forecast return; the UI labels it so). Rows are
tagged with the signal families (deployed strategies) that triggered them;
multi-family confluence gets a ★ badge. **Every row is clickable** → a signal
detail modal (score, today/5D/20D/1Q forecast grid, full reasoning note,
family list) with an "Open strategy →" button when a family resolves to a
`strategy_id` in `gold.signal_families`.

Rows scoring **< 40** are grouped under a collapsed, dimmed "lower conviction"
section so weak setups aren't presented as top opportunities (they auto-expand
only when a market has no strong rows).

**Component:** `frontend/src/components/SignalsTab.jsx` — poll 5min.
Layout: 2×2×2 (`US/HK · ETF/METAL · CRYPTO/FX`).

## APIs

### `GET /api/signals/universe?markets=US,HK,ETF,CRYPTO,FX,METAL&limit=8`
```jsonc
{ "data": { "US": [ { "ticker":"NVDA","name":"NVIDIA",
    "families":["Momentum Breakout","Earnings Drift"],   // keys into /families
    "direction":"BUY|SELL","potential":91,               // 0–100 signal score
    "change_pct":2.1,"note":"20d breakout · RVOL 2.4×",
    "fwd_5d":1.2,"fwd_20d":3.4,"fwd_1q":8.1 } ] },        // signed %, nullable
  "as_of":"..." }
```
Backing: `consumption.signal_setups` (qr_etl, 5min).
- `fwd_5d / fwd_20d / fwd_1q` are selected **opportunistically**: the endpoint
  tries them and degrades to the base columns (nulls in the payload) until
  qr_etl adds them — see DB_CHANGES_v2.md §4.4.
- **Server-side guards over ETL data quality** (remove once fixed upstream):
  `.HK`-suffixed tickers misfiled under `market='US'` are reclassified to HK;
  JSON blobs in `note`/`reasoning` are flattened to readable text
  (`_human_note`); crypto fallback dedupes ticker formats (ADAUSDT vs ADA-USD)
  keeping the strongest row per base asset; unpopulated HK scores are sent as
  `null` (never a fabricated 0.5).
- **Fallback:** when a market has no `signal_setups` rows, the endpoint
  derives candidates from `consumption.stock` (HK), `.crypto`, `.fx`,
  `.commodities` — real data, heuristic scoring (see `signals.py`). Remove
  once `signal_setups` covers all markets. Owner: qr_etl.

### `GET /api/signals/families`
```jsonc
{ "data": [ { "key":"Momentum Breakout","label":"Seasonal SUE","strategy_id":"s019",
    "strategy_name":"...","deployed":true,"color":"#3b82f6" } ] }
```
Backing: `gold.signal_families` — the vocabulary bridge between Research and
the strategy registry. `strategy_id` null ⇒ candidate pattern (modal shows
"candidate pattern — no strategy yet", no click-through).

## Known gaps
- **Forecast horizons are all null** until qr_etl adds `fwd_5d/fwd_20d/fwd_1q`
  to `consumption.signal_setups` (the modal says so explicitly). Owner: qr_etl.
- Fallback-derived rows use generic family tags ("momentum"/"tactical") that
  don't exist in `gold.signal_families` → default color, no strategy
  click-through. Resolves when signal_setups is backfilled.
- `families[]` values in signal_setups (e.g. "Tactical", "ETF Paper V2") must
  match `gold.signal_families.family_key` exactly, or the strategy
  click-through can't resolve. Owner: qr_etl consistency.
- Market classification (`2800.HK` under US) and crypto ticker-format
  duplication are patched server-side but should be fixed at the source.
  Owner: qr_etl.
