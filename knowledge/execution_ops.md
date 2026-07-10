# Execution › Ops

**Purpose:** execution control & broker reconciliation — active order queue,
today's fills, live signals, IBKR gateway state, and the global kill switch
with per-strategy capital caps.

**Component:** `frontend/src/components/LiveOpsPanel.jsx` — main poll 10s,
Gateway/Kill-Switch panels 15s (all visibility-paused).

## APIs

### `GET /api/operations/live` — poll 10s (orders/fills/signals tabs)
`{ "summary": { active_order_count, todays_fill_count, active_signal_count,
today_pnl, today_winners, today_losers },
"active_orders":[{id,strategy_id,ticker,side,quantity,price,order_type,status,execution_mode,submitted_at}],
"todays_fills":[{id,strategy_id,ticker,side,quantity,price,pnl,execution_mode,filled_at}],
"signals":[{strategy_id,ticker,signal,strength,confidence,price,ts}] }`
Backing: `gold.ib_orders`/order queue views, `gold.trade_executions`,
`gold.strategy_signals`.

### `GET /api/execution/gateway` — Gateway tab, 15s
`{ connected, host, port, latency_ms, account, last_heartbeat, global_mode }`
Backing: `consumption.ib_gateway_state` + `gold.platform_settings`
(`global_execution_mode`).

### `GET /api/execution/limits` — Kill Switch tab, 15s
`{ halt_phrase_set, global_halt, per_strategy:[{strategy_id,capital_cap_pct,used_pct}] }`
Backing: `gold.risk_limits` (strategy_id NULL = the global row).

### `POST /api/execution/kill-switch`
`{ phrase: "HALT ALL" }` (exact) → sets `global_halt=true` in
`gold.risk_limits` + writes `gold.audit_events`. 422 on wrong phrase.

### `GET /api/execution/orders` · `/fills` · `/trades`
Standalone panels' data (order queue, reconciliation fills with
`matched:bool`, combined algo+manual trade log). Backing:
`consumption.execution_order_queue`, `.execution_fills`,
`gold.trade_executions` + `gold.manual_orders`.

## Known gaps
- Kill-switch only sets the flag — actual order-cancel/flatten execution is
  the trading engine's responsibility on reading `global_halt`. Verify that
  consumer exists before relying on it in anger. Owner: qr_frontend/engine.
- Reconciliation `matched` depends on broker-statement ingestion
  (`execution_fills.broker_ref`) — qr_etl cadence "live (IBKR sync)".
