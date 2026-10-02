import {
  DerivPanel, DerivEmptyState, DerivKpiStrip, DerivTableShell,
  TASK_DERIV_LEDGERS,
} from './shared.jsx';

// Derivatives ▸ Backtest — backtest runs for derivative strategies.
// Phase 1: wireframe skeleton — PENDING placeholders naming the blocking
// ledger task (t_15d7e66a, qr_etl). Phase 2 wires GET /api/derivatives/backtests;
// Phase 3 renders the run table + per-run detail once
// gold.derivatives_backtest_runs / _trades land.

const RUN_COLS = [
  { label: 'Run date',  tip: 'Backtest run timestamp (UTC)' },
  { label: 'Strategy',  tip: 'Derivative strategy id' },
  { label: 'Type',      tip: 'OPTION / FUTURE' },
  { label: 'Window',    tip: 'IS/OOS span, e.g. OOS 2024-01→2026-09 — bars honesty markers as in the equity Sim cards' },
  { label: 'Sharpe',    tip: 'Out-of-sample Sharpe' },
  { label: 'Return',    tip: 'Out-of-sample return — per-field unit contract pinned before serving' },
  { label: 'Win %',     tip: 'Out-of-sample win rate' },
  { label: 'MDD',       tip: 'Out-of-sample max drawdown' },
  { label: 'PF',        tip: 'Profit factor' },
  { label: 'Trades',    tip: 'Out-of-sample trade count' },
];

export function DerivativesBacktest() {
  return (
    <div className="space-y-3">
      <DerivKpiStrip
        task={TASK_DERIV_LEDGERS}
        tiles={[
          { label: 'Runs',            tip: 'Total derivative backtest runs' },
          { label: 'Strategies',      tip: 'Strategies with at least one run' },
          { label: 'Latest run',      tip: 'Most recent run date' },
          { label: 'Best Sharpe OOS', tip: 'Best out-of-sample Sharpe across runs' },
        ]}
      />

      <DerivPanel
        title="Backtest Runs"
        endpoint="GET /api/derivatives/backtests"
        task={TASK_DERIV_LEDGERS}
        note="Backtest results for derivative strategies — separate tables from equity strategy backtests, so existing performance views are unaffected."
      >
        <DerivTableShell
          cols={RUN_COLS}
          empty="No backtest runs yet — derivatives backtest ledger pending."
          sub="Blocked by qr_etl t_15d7e66a (gold.derivatives_backtest_runs / _trades)."
        />
      </DerivPanel>

      <DerivPanel
        title="Run Detail"
        endpoint="GET /api/derivatives/backtests"
        task={TASK_DERIV_LEDGERS}
        note="Per-run drill-down — activates when a run is selected above."
      >
        <div className="grid grid-cols-1 xl:grid-cols-2 gap-3">
          <DerivEmptyState
            line="Equity curve renders here once a run is selected."
            sub="OOS daily curve from gold.derivatives_backtest_runs — pending qr_etl t_15d7e66a."
          />
          <DerivEmptyState
            line="Annual returns + trade ledger render here."
            sub="Per-year bars and round-trip ledger from gold.derivatives_backtest_trades — pending qr_etl t_15d7e66a."
          />
        </div>
      </DerivPanel>
    </div>
  );
}
