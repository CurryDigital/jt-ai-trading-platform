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
`GET /api/strategies/{id}/detail` → registry row + positions + signals for
the detail view (`StrategyDetail.jsx`, poll 30s).

## Known gaps
- No fabricated metrics remain by design — if a field is missing the card
  shows "—". Cards with no `yearly_backtest` show "No annual backtest data
  yet" → backfill `gold.strategy_backtest_runs`. Owner: qr_etl.
- Compare view (`StrategyCompare.jsx`) exists but has no entry point since
  the card-grid rebuild — re-adding multi-select compare is an open
  qr_frontend task.
