# Research › Macro

**Purpose:** top-down regime read per market before touching any trade:
US & HK equity deep cards, Crypto/FX/Metals compact cards, ETF strategy-book
card — laid out 2×2×2. Each card: price/KPIs, 7-day regime forecast with a
plain-language trading bias, sectors, calendar, news.

**Component:** `frontend/src/components/MacroTab.jsx` — poll 15min.

## Reading the 7-Day Regime Forecast
`P(risk-on) %` = model probability each of the next 7 days favors risk-on
positioning. Thresholds (aligned with `research.py`): **≥55 risk-on** (long
setups favored, adds OK) · **45–55 neutral** (no regime edge — trade setups,
not the tape) · **≤45 risk-off** (reduce exposure, tighten stops, defensive).
The UI also prints trend (↗ strengthening / ↘ fading / → steady = last vs
first day) and the bias line under the bars. A fading 57→53 series means the
risk-on edge is decaying toward neutral — not yet a sell signal.

## APIs

### `GET /api/macro/regions`
```jsonc
{ "data": [ { "key":"US","index_sym":"SPX","index_name":"S&P 500","last":5982.4,"change_pct":0.62,
    "regime_7d":[57.1,56.2,...7 values],                       // P(risk-on) per day
    "kpis":[["VIX","13.8"],["Breadth","312A/188D"]],           // display strings
    "events":[{"event":"CPI (May)","date":"Jun 25","importance":"High|Med|Low"}],
    "sectors":[{"sector":"Technology","perf_pct":1.4}] } ], "as_of":"..." }
```
Backing: `consumption.macro_regime_7d`, `.macro_kpis`, `.macro_sectors`,
`.macro_events`, `.dashboard_indices`. Cadence 15–60min (qr_etl).

### `GET /api/macro/global`
Same shape per `key ∈ {CRYPTO, FX, METAL}` plus
`"news": {"headline": "...", "tone": "bull|bear|neu"}` (FX tone = USD
direction). Backing adds `consumption.market_news`.

### `GET /api/news?markets=US,HK`
`{ "data": { "US": [ {headline, source, tone, impact, tags[], published_at} ] } }`
Backing: `consumption.market_news`.

### `GET /api/strategies/researcher` (shared) — feeds the ETF card
(strategy book filtered to `asset_class = 'ETF'`).

### `GET /api/research/regime-forecast/all?horizon=7d` (used by Screener too)
`{ "horizon":"7d","count":N,"forecasts":[{region,risk_on_pct,dominant_regime,...}] }`
Backing: `gold.regime_forecast`.

## Known gaps
- `macro_kpis`/`macro_events` coverage per scope depends on qr_etl backfill —
  cards render "—" rows when absent.
- Regime model confidence is not stored (`regime_confidence` always null) —
  would strengthen the bias line if qr_etl adds it to `gold.regime_forecast`.
