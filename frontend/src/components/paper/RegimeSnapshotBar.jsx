import React from 'react';

export default function RegimeSnapshotBar({ systemStatus, strategyBook, upcomingEvents, dailyRuns }) {
  const regime = systemStatus?.regime_label || '—';
  const confidence = systemStatus?.regime_confidence;
  const override = systemStatus?.regime_override;
  const strategies = strategyBook?.strategies || [];
  const events = upcomingEvents?.events || [];
  const runs = dailyRuns?.runs || [];

  const regimeColor =
    regime === 'TREND' ? 'text-emerald-400 border-emerald-500/20 bg-emerald-500/10' :
    regime === 'MEAN_REV' ? 'text-blue-400 border-blue-500/20 bg-blue-500/10' :
    regime === 'CARRY' ? 'text-amber-400 border-amber-500/20 bg-amber-500/10' :
    regime === 'HIGH_VOL' ? 'text-rose-400 border-rose-500/20 bg-rose-500/10' :
    'text-slate-400 border-slate-500/20 bg-slate-500/10';

  const PAPER_NAV_USD = 32000;
  const tradeableCount = strategies.filter(s => s.min_nav_usd == null || s.min_nav_usd <= PAPER_NAV_USD).length;
  const notFundedCount = strategies.length - tradeableCount;
  const nextEvent = events[0];

  const lastRun = runs[0];
  const runStatus = lastRun?.status;

  return (
    <div className="grid grid-cols-5 gap-2 mb-4">
      {/* Tile 1 — REGIME */}
      <div className={`rounded-lg border p-3 ${regimeColor}`}>
        <div className="text-[9px] uppercase tracking-wider opacity-70 mb-1">Regime</div>
        <div className="text-sm font-bold">{regime}</div>
        <div className="text-[10px] mt-1 flex items-center gap-1">
          <span className={`w-1.5 h-1.5 rounded-full ${override ? 'bg-amber-400 animate-pulse' : 'bg-current'}`} />
          conf {confidence != null ? confidence.toFixed(2) : '—'}
        </div>
      </div>

      {/* Tile 2 — ACTIVE SIGNALS */}
      <div className="rounded-lg border border-slate-700/50 bg-slate-800/50 p-3">
        <div className="text-[9px] uppercase tracking-wider text-slate-500 mb-1">Active Signals</div>
        <div className="text-sm font-bold text-slate-200">{strategies.filter(s => s.status === 'approved').length} of {strategies.length}</div>
        <div className="text-[10px] text-slate-400 mt-1 truncate">
          {strategies.filter(s => s.status === 'approved').slice(0, 3).map(s => s.display_name || s.strategy_id).join(', ') || '—'}
        </div>
      </div>

      {/* Tile 3 — NEXT EVENT */}
      <div className={`rounded-lg border p-3 ${
        nextEvent?.days_away <= 1 ? 'border-rose-500/20 bg-rose-500/10 text-rose-400' :
        nextEvent?.days_away <= 3 ? 'border-amber-500/20 bg-amber-500/10 text-amber-400' :
        'border-slate-700/50 bg-slate-800/50 text-slate-400'
      }`}>
        <div className="text-[9px] uppercase tracking-wider opacity-70 mb-1">Next Event</div>
        <div className="text-sm font-bold">{nextEvent?.event_label || '—'}</div>
        <div className="text-[10px] mt-1">
          {nextEvent ? `${nextEvent.event_date} · ${nextEvent.days_away}d` : '—'}
        </div>
      </div>

      {/* Tile 4 — STRATEGIES */}
      <div className="rounded-lg border border-slate-700/50 bg-slate-800/50 p-3">
        <div className="text-[9px] uppercase tracking-wider text-slate-500 mb-1">Strategies</div>
        <div className="text-sm font-bold text-slate-200">{strategies.length} total</div>
        <div className="text-[10px] text-slate-400 mt-1">
          <span className="text-emerald-400">{tradeableCount} tradeable</span> · <span className="text-rose-400/70">{notFundedCount} not funded</span>
        </div>
      </div>

      {/* Tile 5 — LAST CYCLE */}
      <div className={`rounded-lg border p-3 ${
        runStatus === 'ok' ? 'border-emerald-500/20 bg-emerald-500/10 text-emerald-400' :
        'border-rose-500/20 bg-rose-500/10 text-rose-400'
      }`}>
        <div className="text-[9px] uppercase tracking-wider opacity-70 mb-1">Last Cycle</div>
        <div className="text-sm font-bold">{lastRun?.run_type || '—'}</div>
        <div className="text-[10px] mt-1">
          {lastRun ? `${lastRun.status} · ${lastRun.orders_placed || 0} fills` : '—'}
        </div>
      </div>
    </div>
  );
}
