import { DerivPanel, DerivEmptyState } from './shared.jsx';

// Derivatives ▸ Execution — positions/fills for derivative strategies.
// Read-only by design: NO order placement here until explicitly approved.
// Phase 1: honest PENDING shell. Phase 2 wires GET /api/derivatives/positions;
// Phase 3 renders real books from gold.derivatives_positions / _fills
// (separate ledgers — never gold.paper_trades* / trade_executions).
export function DerivativesExecution() {
  return (
    <div className="space-y-3">
      <DerivPanel
        title="Derivative Positions"
        endpoint="GET /api/derivatives/positions"
        note="Read-only book view. Derivatives positions live in their own ledgers and do not feed the Sim / Paper / UAT / Live books or Command P&L aggregates."
      >
        <DerivEmptyState line="No derivative positions yet — derivatives ledger pending." />
      </DerivPanel>
    </div>
  );
}
