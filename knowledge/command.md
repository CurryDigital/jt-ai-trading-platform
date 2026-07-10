# Command (home)

**Purpose:** one-glance state of the whole operation — market backdrop (US/HK),
account book, strategy pipeline counts, deployed-strategy health, and a
severity-ranked Action Center of items needing a human decision.

**Component:** `frontend/src/components/CommandCenter.jsx`
Zones: MarketBand → My Book (equity curve + KPI tiles) → Pipeline funnel +
Deployed Health → Needs Attention.

## APIs

### `GET /api/markets/overview?regions=US,HK` — poll 15s (12s server cache)
One-call aggregate for the Market Status band. Response:
```jsonc
{
  "indices":  { "data": [ { "sym":"^GSPC","name":"S&P 500","region":"US","last":7483.24,"change_pct":0.0,"spark":[...] } ], "as_of":"..." },
  "breadth":  { "us": { "advancing":1,"declining":2,"unchanged":0,"new_highs":0,"new_lows":0 }, "hk": {...} },
  "sentiment":{ "us": { "fear_greed":70,"fear_greed_label":"Greed","vix":16.05,"vix_change_pct":null,"put_call":null,"regime":"CARRY" }, "hk": {...} },
  "movers":   { "gainers":[{"ticker":"CYBR","change_pct":153.02}], "losers":[...] },
  "as_of": "ISO-8601"
}
```
Backing: `consumption.dashboard_indices`, `consumption.market_breadth`,
`consumption.market_sentiment`, `consumption.market_movers` (qr_etl, 15–60s).

### `GET /api/command/overview` — poll 60s
```jsonc
{
  "account": { "equity":403116.11,"day_pnl":0,"day_pnl_pct":0,"buying_power":...,
               "cash_pct":39.07,"open_pnl":6071.25,"gross_exp_pct":...,"net_exp_pct":...,"positions":10 },
  "equity_curve": [ { "d":"2026-06-05","equity":399084.95 } ],           // 30 sessions asc
  "pipeline": { "experimental":8,"near_golden":2,"golden":0,"deployed":6,"total":30 },
  "deployed_health": [ { "strategy_id":"...","name":"...","asset":"EQUITY",
                         "live_trades":53,"live_win_rate":67.9,"sharpe":9.18 } ],  // WR already percent
  "attention": [ { "sev":"critical|warning|info","tag":"DATA","title":"...","impact":"...",
                   "target":"command|research|strategies|execution|settings","ref_id":null,"created_at":"..." } ],
  "as_of": "ISO-8601"
}
```
Backing: `consumption.account_summary`, `consumption.account_equity_curve`
(over `gold.account_nav_daily`), `gold.strategy_registry`
(`priority`/`approved_at`), `consumption.attention_queue`.

Positions count/exposure tiles also reuse the app-shell fetch of
`GET /api/portfolio/positions`.

## Known gaps
- **Equity curve early spikes** (drops to ~$10K): bogus early rows in
  `gold.account_nav_daily` — the 30-session return headline is distorted.
  Owner: qr_etl (clean/rebuild early NAV snapshots).
- `deployed_health.sharpe` values ~9 look implausible for OOS Sharpe —
  verify `strategy_registry.sharpe_oos` units. Owner: qr_etl.
- Attention `impact` sometimes carries raw SQL error text (UI truncates
  with tooltip) — the feed itself should store human summaries. Owner: qr_etl.
- HK `vix`/`put_call` are null (no HK feed wired) — UI shows "N/A". Accepted.
