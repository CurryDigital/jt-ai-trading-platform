import {
  DerivPanel, DerivEmptyState, DerivKpiStrip, DerivTableShell, DerivChipSkeleton,
  TASK_RESEARCH_REGISTRY,
} from './shared.jsx';

// Derivatives ▸ Research — derivative strategy research surface.
// Phase 1: wireframe skeleton — every box is an honest PENDING placeholder
// naming the blocking research-registry task (t_736850c6, qr_research).
// Phase 2 wires GET /api/derivatives/strategies; Phase 3 renders real rows.

const STRATEGY_COLS = [
  { label: 'Strategy',  tip: 'Registry id + display name (research-owned prose)' },
  { label: 'Type',      tip: 'OPTION / FUTURE — own asset classes, never folded into the equity ASSET_MAP' },
  { label: 'Underlying', tip: 'Underlying universe (index, single names, commodities…)' },
  { label: 'Venue',     tip: 'US / HK' },
  { label: 'Horizon',   tip: 'Intended holding period from the research spec' },
  { label: 'Stage',     tip: 'RESEARCH → BACKTESTED → (paper, only after explicit approval)' },
  { label: 'Sharpe OOS', tip: 'Out-of-sample Sharpe from gold.derivatives_backtest_runs' },
  { label: 'Ret OOS',   tip: 'Out-of-sample return — unit contract pinned before serving (fraction vs pct)' },
  { label: 'Win %',     tip: 'Out-of-sample win rate' },
  { label: 'MDD',       tip: 'Out-of-sample max drawdown' },
  { label: 'Trades',    tip: 'Out-of-sample trade count' },
];

export function DerivativesResearch() {
  return (
    <div className="space-y-3">
      <DerivKpiStrip
        task={TASK_RESEARCH_REGISTRY}
        tiles={[
          { label: 'Strategies',  tip: 'Registered derivative strategies' },
          { label: 'Options',     tip: 'Strategies with instrument = OPTION' },
          { label: 'Futures',     tip: 'Strategies with instrument = FUTURE' },
          { label: 'US venue',    tip: 'Strategies on US underlyings' },
          { label: 'HK venue',    tip: 'Strategies on HK underlyings' },
          { label: 'Backtested',  tip: 'Strategies with at least one OOS backtest run' },
        ]}
      />

      <DerivChipSkeleton
        groups={[
          { label: 'Instrument', options: ['ALL', 'OPTIONS', 'FUTURES'], task: TASK_RESEARCH_REGISTRY },
          { label: 'Venue',      options: ['ALL', 'US', 'HK'],           task: TASK_RESEARCH_REGISTRY },
          { label: 'Stage',      options: ['ALL', 'RESEARCH', 'BACKTESTED'], task: TASK_RESEARCH_REGISTRY },
        ]}
      />

      <DerivPanel
        title="Derivative Strategies"
        endpoint="GET /api/derivatives/strategies"
        task={TASK_RESEARCH_REGISTRY}
        note="Options/futures strategy research — kept out of the shared equity strategy universe (Lab / Pipeline / Performance) by design. Column contract below is the intended shape; the feed is pending."
      >
        <DerivTableShell
          cols={STRATEGY_COLS}
          empty="No derivative strategies yet — research registry feed pending."
          sub="Blocked by qr_research t_736850c6 (registry) — never synthetic rows."
        />
      </DerivPanel>

      <DerivPanel
        title="Research Notes & Disclosures"
        endpoint="GET /api/derivatives/strategies"
        task={TASK_RESEARCH_REGISTRY}
        note="Research-owned prose per registered strategy (entry/exit logic, caveats, audit trail) — rendered verbatim, never synthesized."
      >
        <DerivEmptyState
          line="No research notes yet — registry prose arrives with the research feed."
          sub="Blocked by qr_research t_736850c6."
        />
      </DerivPanel>
    </div>
  );
}
