# Strategies › Performance

**Purpose:** compare the whole strategy book at a glance — sortable card grid
(Return / Sharpe / Win rate / Trades) with per-card real metrics, annual
backtest bars, and mode badges. Click a card → full Strategy Detail.

**Component:** `frontend/src/components/StrategiesWorkspace.jsx`
(`StrategyPerformanceGrid` + shared `StrategyCard`) — book poll 60s.

## Data
Single source: `GET /api/strategies/researcher` (shape + backing objects in
[strategies_lab.md](strategies_lab.md)). Card fields:

| Card metric | API field | Notes |
|---|---|---|
| Return (BT) | `yearly_backtest.<latest>.return_pct` | fraction → ×100 in mapper |
| Sharpe | `sharpe_ratio` | from latest backtest run overlay |
| Win rate | `win_rate` | fraction → ×100 |
| Max DD | `max_drawdown` | fraction → −% |
| Trades (OOS) | `trade_count_oos` | |
| Conviction | `conviction_score` | 0–10 |
| Annual bars | `yearly_backtest` per year | |
| Mode badge | `execution_mode` | SIM/PAPER/LIVE |

KPI header row: strategy count, avg BT win rate, live count, best performer.
Horizon segmentation (Day/Swing/Position) is inferred from asset class in
`strategyProfiles.js` — classification only, not a data field.

## Strategy Detail (click-through)
`GET /api/strategies/{id}/evaluation` returns the full detail payload used by
`StrategyDetail.jsx` (poll 30s):

- Header: `strategy_id`, `name`, `status`, `priority`, `asset_class`, `direction`,
  `time_horizon`, `execution_mode`, `venue`, `entry_logic`, `exit_logic`,
  `description`, `assigned_capital`, `in_market_capital`, `conviction_score`,
  `created_at`, `updated_at`.
- Universe: `universe` (ticker list), `universe_count`.
- Metrics: `metrics.backtest` + `metrics.live` with `win_rate`, `profit_factor`,
  `sharpe`, `max_drawdown`, `total_trades`, `total_pnl`, `last_trade_at`.
- Divergence: `divergence.verdict`, `win_rate_delta_pp`, `profit_factor_delta`.
- Equity: `equity_curve[]` (`date`, `pnl`, `cum_pnl`).
- Returns: `monthly_returns[]` (`year`, `month`, `return`).
- Trades: `recent_trades[]` (`ts`, `ticker`, `side`, `quantity`, `price`, `pnl`, `mode`).
- Signals: `recent_signals[]` (`ticker`, `signal`, `strength`, `confidence`, `price`, `ts`).
- Window: `window_days`.

### Risk watch endpoints
`GET /api/strategies/{id}/risk-status` returns the current demote-rule evaluation
without taking action. `POST /api/strategies/{id}/auto-demote-check` triggers an
immediate check and, if breached and in `LIVE_TRADING`, demotes the strategy to
PAPER. Both are consumed by `RiskWatchPanel.jsx`.

### CASH handling
`CASH` is a strategy cash-bucket placeholder (e.g., from "move to 100% cash"
exit logic). It is **not** a tradeable ticker and is filtered from the universe
list, recent trades, recent signals, equity curve, live performance summary, and
risk-rule calculations. The frontend also defensively hides any CASH rows.

## Known gaps
- No fabricated metrics remain by design — if a field is missing the card
  shows "—". Cards with no `yearly_backtest` show "No annual backtest data
  yet" → backfill `gold.strategy_backtest_runs`. Owner: qr_etl.
- Compare view (`StrategyCompare.jsx`) exists but has no entry point since
  the card-grid rebuild — re-adding multi-select compare is an open
  qr_frontend task.
