# Execution › Paper

**Purpose:** the paper-trading book — system status bar, open paper positions
with P&L, signal proximity for paper strategies, daily run cards, trade
history, plus a Manual Ticket bound to the paper book.

**Component:** `frontend/src/components/PaperStrategiesPage.jsx` composing
`components/paper/*` (SystemStatusBar, OpenPositionsTable,
OpenPositionsPnlPanel, SignalProximityPanel, DailyRunCards,
TradeHistoryTable) with data hooks in `components/paper/usePaperData.js`.

## APIs (via usePaperData hooks, ~60s)
- `GET /api/paper-strategies` — paper strategy list + positions.
  Backing: `consumption.portfolio_positions_current` filtered to the paper
  book + registry join.
- Paper system status / daily runs / trade history / proximity endpoints as
  wired in `usePaperData.js` (each degrades to empty when its backing view
  is missing — see the hook file for exact paths).
- `POST /api/execution/manual-order` with `book:"paper"` — Manual Ticket
  (same contract as [execution_live.md](execution_live.md), no mode gate).

## Known gaps
- `/api/strategies/.../stats` shows `data_not_available` whenever
  `consumption.portfolio_positions_current` has zero ACTIVE rows — correct
  empty state, not a bug.
- Paper vs live book separation depends on qr_etl's `book`/source tagging in
  the positions view; without it both tabs show the same rows.
