# Execution › Live

**Purpose:** the live book — open positions grouped by asset class with
search/filter, portfolio KPIs, a quick IBKR order form, and the Manual
Ticket for hand-entered fills.

**Component:** `PortfolioTab` (inline in `frontend/src/App.jsx`) +
`frontend/src/components/ManualTicket.jsx`. Positions come from the app
shell's 60s poll.

## APIs

### `GET /api/portfolio/positions` — app-shell poll 60s
`{ "positions": [ { id, strategy_id, ticker, side, entry_date, entry_price,
current_price, quantity, market_value, weight_pct, unrealized_pnl,
realized_pnl, status, asset_class } ], "total_value":..., "total_pnl":... }`
Backing: `consumption.portfolio_positions_current` (status='ACTIVE').

### `POST /api/ib/place-order` — Quick Order (IBKR)
`{ symbol, action:"BUY|SELL", quantity, order_type:"MKT|LMT|STP" }` →
`{ success, message }`. Routes through `ib_service` to TWS/Gateway. The UI
shows a confirm dialog before sending (direct broker route — real money).

### `POST /api/execution/manual-order` — Manual Ticket
`{ book:"live|paper", ticker, market:"US|HK", asset:"STOCK|CRYPTO|FX",
side:"LONG|SHORT", qty, entry }` → 201
`{ order_id, status:"accepted", filled_qty, avg_price, created_at }`.
409 `{error:"mode_mismatch"}` when book=live but global mode ≠ LIVE_TRADING.
Writes `gold.manual_orders` (the platform's only DB write besides settings/
audit). qr_etl folds manual fills into `portfolio_positions_current` with
`source='manual'`.

### `GET /api/execution/global-mode` — mode pill (app shell, 30s)

## Known gaps
- Manual fills appear in the blotter only after qr_etl's fold-in job runs —
  there's a lag between ticket 201 and the position showing. Documented,
  not a bug.
- `GET /api/execution/trades` (fills log) exists but isn't rendered on this
  page yet — candidate to add a trade-log panel. Owner: qr_frontend.
