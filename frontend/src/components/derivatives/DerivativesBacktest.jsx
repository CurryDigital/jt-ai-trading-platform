import { DerivPanel, DerivEmptyState } from './shared.jsx';

// Derivatives ▸ Backtest — backtest runs for derivative strategies.
// Phase 1: honest PENDING shell. Phase 2 wires GET /api/derivatives/backtests;
// Phase 3 renders run table + per-run detail once qr_etl lands
// gold.derivatives_backtest_runs / _trades.
export function DerivativesBacktest() {
  return (
    <div className="space-y-3">
      <DerivPanel
        title="Backtest Runs"
        endpoint="GET /api/derivatives/backtests"
        note="Backtest results for derivative strategies — separate tables from equity strategy backtests, so existing performance views are unaffected."
      >
        <DerivEmptyState line="No backtest runs yet — derivatives backtest ledger pending." />
      </DerivPanel>
    </div>
  );
}
