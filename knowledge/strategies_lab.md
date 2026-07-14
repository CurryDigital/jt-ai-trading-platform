# Strategies › Lab

**Purpose:** the strategy screener/launchpad — browse the research-validated
registry with backtest-vs-live comparison, filter by asset class / win rate /
search, and one-click deploy a strategy into a capital pool.

**Component:** `frontend/src/components/StrategyLab.jsx` — `usePoll` 60s
(strategies + live stats), visibility-paused. One-click deploy asks for
confirmation (guards against an accidental $100k pool).

## APIs

### `GET /api/strategies/researcher` — the shared strategy book
(15s server cache; `?fresh=1` bypass). Response:
```jsonc
{ "strategies": [ {
    "id":"S9_MACD_Momentum_V2","name":"...","asset_class":"EQUITY|ETF|FX|CRYPTO|COMMODITY|quant",
    "execution_mode":"SIMULATION|PAPER_TRADING|LIVE_TRADING","status":"...","priority":"EXPERIMENTAL|NEAR_GOLDEN|GOLDEN",
    "sharpe_ratio":1.42,"max_drawdown":0.121,"win_rate":0.6792,        // FRACTIONS
    "trade_count_oos":218,"conviction_score":7.5,
    "assigned_capital":..., "in_market_capital":...,
    "signal_logic":"...","exit_logic":"...","universe":[...tickers],
    "yearly_backtest": { "2026": { "return_pct":0.238,"trades":218,"sharpe":...,"win_rate":... } },
    "top_tickers":[{"ticker":"NVDA","signal":"BUY","confidence":0.86}],
    "signal_family_key":"Momentum Breakout|null"
  } ], "count": N }
```
Backing: `gold.strategy_registry` + `gold.strategy_backtest_runs` (latest row
per strategy overlays stale registry OOS fields) + `gold.strategy_signals` +
`gold.signal_families` + `gold.strategy_templates`.

### `GET /api/strategies/stats`
`{ "success":true, "stats": { "<id>": { strategy_id, strategy_name,
total_positions, active_positions, total_invested, total_allocated,
total_pnl, actual_win_rate, total_trades } }, "count":N }`
Fields are **snake_case**; `actual_win_rate` is already a **percent** (0–100,
`winning/active × 100`), not a fraction. Live per-strategy stats from
`consumption.portfolio_positions_current`. (The Lab previously read camelCase
keys here — `actualWinRate` etc. — so the entire Live column was blank; fixed.)

### `POST /api/strategies/deploy-with-pool`
Body `{ strategy_id, tickers[], total_pool }` → creates the capital pool and
activates the strategy. Response `{ success, ... }`.

## Known gaps
- `win_rate`/`max_drawdown`/`yearly_backtest.return_pct` are **fractions** —
  every consumer must ×100 (Lab and the workspace mapper already do).
- Registry OOS fields go stale after each backtest run; the endpoint overlays
  `strategy_backtest_runs` latest — keep that contract if refactoring.
