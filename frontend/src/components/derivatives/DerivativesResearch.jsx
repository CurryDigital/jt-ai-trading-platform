import { useEffect, useMemo, useState } from 'react';
import { api, fmtNum } from '../../utils.js';
import {
  DerivPanel, DerivEmptyState, DerivKpiStrip, DerivTable, DerivChipFilter,
  TASK_RESEARCH_REGISTRY,
} from './shared.jsx';

// Derivatives ▸ Research — derivative strategy research surface.
// Phase 2 (2026-10-02, t_d67907e4): LIVE on GET /api/derivatives/strategies
// (gold.derivatives_strategies, qr_research t_736850c6 — 9 rows). Per-row
// status / data_blocker carry the honest pre-backtest state; OOS metric
// columns stay '—' until gold.derivatives_backtest_runs has rows (the
// endpoint serves the latest run's metrics per strategy, null today).

const STRATEGY_COLS = [
  { label: 'Strategy', tip: 'Registry display name + id (research-owned prose)',
    render: r => (
      <span>
        <span className="text-slate-100 font-semibold">{r.name || r.strategy_id}</span>
        <span className="block text-[9px] text-slate-500 font-mono">{r.strategy_id}</span>
      </span>
    ) },
  { label: 'Type', tip: 'OPTION / FUTURE — own asset classes, never folded into the equity ASSET_MAP', key: 'instrument' },
  { label: 'Underlying', tip: 'Underlying universe', render: r => (r.underlyings || []).join(', ') },
  { label: 'Venue', tip: 'US / HK', key: 'venue' },
  { label: 'Rank', tip: 'Research priority rank (qr_research ordering)', key: 'research_rank', cl: 'text-slate-400 font-mono' },
  { label: 'Stage', tip: 'Registry status + research phase',
    render: r => (
      <span className="flex items-center gap-1">
        <span className={`qr-chip ${r.status === 'parked' ? 'qr-chip-slate opacity-70' : 'qr-chip-slate'}`}>{r.status || '—'}</span>
        {r.phase && r.phase !== r.status && <span className="text-[9px] text-slate-500">{r.phase}</span>}
      </span>
    ),
    cellTip: r => r.data_blocker ? `Data blocker: ${r.data_blocker}` : undefined },
  { label: 'Sharpe OOS', tip: 'Out-of-sample Sharpe from gold.derivatives_backtest_runs — null until the first run lands',
    render: r => fmtNum(r.sharpe_oos), cl: 'text-slate-400 font-mono' },
  { label: 'Ret OOS', tip: 'Out-of-sample return — per-field unit contract pins with the first run', render: r => fmtNum(r.returns_oos), cl: 'text-slate-400 font-mono' },
  { label: 'Win %', tip: 'Out-of-sample win rate', render: r => fmtNum(r.win_rate_oos), cl: 'text-slate-400 font-mono' },
  { label: 'MDD', tip: 'Out-of-sample max drawdown', render: r => fmtNum(r.max_drawdown_oos), cl: 'text-slate-400 font-mono' },
  { label: 'Trades', tip: 'Out-of-sample trade count', key: 'trade_count_oos', cl: 'text-slate-400 font-mono' },
];

export function DerivativesResearch() {
  const [data, setData] = useState(null);       // null = not loaded / failed
  const [loaded, setLoaded] = useState(false);
  const [fInst, setFInst] = useState('ALL');
  const [fVenue, setFVenue] = useState('ALL');
  const [fStage, setFStage] = useState('ALL');

  useEffect(() => {
    let dead = false;
    api.get('/api/derivatives/strategies').then(d => {
      if (dead) return;
      // Defensive shape guard — accept only the documented contract.
      setData(d && Array.isArray(d.strategies) ? d : null);
      setLoaded(true);
    });
    return () => { dead = true; };
  }, []);

  const rows = useMemo(() => (data?.strategies || []).filter(r => {
    if (fInst !== 'ALL' && (r.instrument || '').toUpperCase() !== fInst) return false;
    if (fVenue !== 'ALL' && (r.venue || '').toUpperCase() !== fVenue) return false;
    if (fStage === 'BACKTESTED') return r.latest_run_id != null;
    if (fStage === 'RESEARCH') return r.latest_run_id == null;
    return true;
  }), [data, fInst, fVenue, fStage]);

  const sum = data?.summary || {};
  const failed = loaded && !data;

  return (
    <div className="space-y-3">
      <DerivKpiStrip
        tiles={[
          { label: 'Strategies', tip: 'Registered derivative strategies (gold.derivatives_strategies)', value: sum.total ?? null, sub: 'registry live' },
          { label: 'Options', tip: 'Strategies with instrument = OPTION', value: sum.options ?? null, sub: 'instrument' },
          { label: 'Futures', tip: 'Strategies with instrument = FUTURE', value: sum.futures ?? null, sub: 'instrument' },
          { label: 'US venue', tip: 'Strategies on US underlyings', value: sum.us ?? null, sub: 'venue' },
          { label: 'HK venue', tip: 'Strategies on HK underlyings', value: sum.hk ?? null, sub: 'venue' },
          { label: 'Backtested', tip: 'Strategies with at least one OOS backtest run (gold.derivatives_backtest_runs)', value: sum.backtested ?? null, sub: 'no runs yet' },
        ]}
      />

      <DerivChipFilter
        groups={[
          { label: 'Instrument', value: fInst, onChange: setFInst, options: ['ALL', 'OPTION', 'FUTURE'] },
          { label: 'Venue', value: fVenue, onChange: setFVenue, options: ['ALL', 'US', 'HK'] },
          { label: 'Stage', value: fStage, onChange: setFStage, options: ['ALL', 'RESEARCH', 'BACKTESTED'] },
        ]}
      />

      <DerivPanel
        title="Derivative Strategies"
        endpoint="GET /api/derivatives/strategies"
        task={TASK_RESEARCH_REGISTRY}
        live={!!data}
        failed={failed}
        note="Options/futures strategy research — kept out of the shared equity strategy universe (Lab / Pipeline / Performance) by design. OOS metric columns are '—' until the first backtest run lands."
      >
        <DerivTable
          cols={STRATEGY_COLS}
          rows={rows}
          rowKey={r => r.strategy_id}
          empty={failed ? 'Feed unavailable — see badge tooltip.' : 'No strategies match the active filters.'}
          sub={data ? `${data.count ?? rows.length} registered · ${rows.length} shown` : undefined}
        />
      </DerivPanel>

      <DerivPanel
        title="Research Notes & Disclosures"
        endpoint="GET /api/derivatives/strategies"
        task={TASK_RESEARCH_REGISTRY}
        live={!!data}
        failed={failed}
        note="Research-owned prose per registered strategy (thesis / entry / exit / data blocker) — rendered verbatim from the registry, never synthesized."
      >
        {rows.length === 0 ? (
          <DerivEmptyState
            line={failed ? 'Feed unavailable — see badge tooltip.' : 'No strategies match the active filters.'}
          />
        ) : (
          <div className="space-y-2" style={{ maxHeight: 340, overflowY: 'auto' }}>
            {rows.map(r => (
              <div key={r.strategy_id} className="rounded border border-white/[0.06] px-3 py-2">
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-[11px] font-semibold text-slate-200">{r.name || r.strategy_id}</span>
                  <span className="text-[9px] text-slate-500 font-mono">{r.strategy_id}</span>
                </div>
                {r.thesis && <div className="text-[10px] text-slate-400 mb-1"><span className="qr-label mr-1">Thesis</span>{r.thesis}</div>}
                {r.entry_logic && <div className="text-[10px] text-slate-400 mb-1"><span className="qr-label mr-1">Entry</span>{r.entry_logic}</div>}
                {r.exit_logic && <div className="text-[10px] text-slate-400 mb-1"><span className="qr-label mr-1">Exit</span>{r.exit_logic}</div>}
                {r.data_blocker && <div className="text-[10px] text-slate-500"><span className="qr-label mr-1">Data blocker</span>{r.data_blocker}</div>}
              </div>
            ))}
          </div>
        )}
      </DerivPanel>
    </div>
  );
}
