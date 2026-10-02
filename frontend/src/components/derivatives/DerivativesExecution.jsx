import {
  DerivPanel, DerivEmptyState, DerivKpiStrip, DerivTableShell, DerivChipSkeleton,
  TASK_DERIV_LEDGERS, TASK_FUTURES_DATA,
} from './shared.jsx';

// Derivatives ▸ Execution — positions/fills for derivative strategies.
// Read-only by design: NO order placement here until explicitly approved.
// Phase 1: wireframe skeleton — PENDING placeholders naming the blocking
// ledger task (t_15d7e66a, qr_etl). Phase 2 wires GET /api/derivatives/positions;
// Phase 3 renders real books from gold.derivatives_positions / _fills
// (separate ledgers — never gold.paper_trades* / trade_executions).

const POSITION_COLS = [
  { label: 'Contract',    tip: 'Full contract id (e.g. option OCC symbol / futures contract month)' },
  { label: 'Strategy',    tip: 'Originating derivative strategy' },
  { label: 'Book',        tip: 'deriv_sim / deriv_paper — separate from the equity books' },
  { label: 'Side',        tip: 'LONG / SHORT' },
  { label: 'Qty',         tip: 'Contracts' },
  { label: 'Entry',       tip: 'Entry premium/price' },
  { label: 'Mark',        tip: 'Latest mark — futures contract-month marks depend on qr_etl t_822b6365 (Databento ingest)' },
  { label: 'Unrealized',  tip: 'Mark-to-market P&L — null marks render unscored, never $0' },
];

const FILL_COLS = [
  { label: 'Time',     tip: 'Fill time (UTC)' },
  { label: 'Contract', tip: 'Full contract id' },
  { label: 'Side',     tip: 'BUY / SELL' },
  { label: 'Qty',      tip: 'Contracts' },
  { label: 'Price',    tip: 'Fill price' },
  { label: 'Strategy', tip: 'Originating derivative strategy' },
];

export function DerivativesExecution() {
  return (
    <div className="space-y-3">
      <div className="qr-surface px-3 py-2 text-[10px] text-slate-500">
        Read-only by design — no order placement for derivatives until explicitly approved.
        Derivatives positions live in their own ledgers and never feed the Sim / Paper / UAT / Live
        books or Command P&L aggregates.
      </div>

      <DerivChipSkeleton
        groups={[
          { label: 'Book', options: ['SIM', 'PAPER'], task: TASK_DERIV_LEDGERS },
        ]}
      />

      <DerivKpiStrip
        task={TASK_DERIV_LEDGERS}
        tiles={[
          { label: 'Open',           tip: 'Open derivative positions' },
          { label: 'Gross notional', tip: 'Gross notional exposure across open positions' },
          { label: 'Unrealized',     tip: 'Open mark-to-market P&L — null when no marks, never $0' },
          { label: 'Realized YTD',   tip: 'Current-year realized P&L — null when no closed trades' },
          { label: 'Fills today',    tip: 'Fill count today (UTC)' },
        ]}
      />

      <DerivPanel
        title="Derivative Positions"
        endpoint="GET /api/derivatives/positions"
        task={TASK_DERIV_LEDGERS}
        note="Open positions per derivatives book. Futures marks additionally depend on the contract-month data build."
      >
        <DerivTableShell
          cols={POSITION_COLS}
          empty="No derivative positions yet — derivatives ledger pending."
          sub={`Blocked by qr_etl ${TASK_DERIV_LEDGERS} (ledgers) · futures marks by ${TASK_FUTURES_DATA} (Databento).`}
        />
      </DerivPanel>

      <DerivPanel
        title="Derivative Fills"
        endpoint="GET /api/derivatives/positions"
        task={TASK_DERIV_LEDGERS}
        note="Fill blotter per derivatives book — from gold.derivatives_fills once it exists."
      >
        <DerivTableShell
          cols={FILL_COLS}
          empty="No derivative fills yet — fills ledger pending."
          sub={`Blocked by qr_etl ${TASK_DERIV_LEDGERS} (gold.derivatives_fills).`}
        />
      </DerivPanel>
    </div>
  );
}
