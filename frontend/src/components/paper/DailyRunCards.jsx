import React from 'react';

export default function DailyRunCards({ data }) {
  const runs = data?.runs || [];

  if (!runs.length) {
    return (
      <div className="rounded-lg bg-slate-800/50 border border-slate-700/50 p-4 mb-6">
        <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">
          Today's Runs
        </h3>
        <p className="text-sm text-slate-500">No runs today</p>
      </div>
    );
  }

  return (
    <div className="mb-6">
      <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-3">
        Today's Runs ({runs.length})
      </h3>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
        {runs.map((run, i) => (
          <div
            key={i}
            className="rounded-lg bg-slate-800/50 border border-slate-700/50 p-3 hover:border-slate-600/50 transition-colors"
          >
            <div className="flex items-center justify-between mb-2">
              <span className="text-[10px] uppercase tracking-wider text-slate-500">
                {run.run_type}
              </span>
              <span
                className={`text-[10px] px-1.5 py-0.5 rounded ${
                  run.status === 'ok'
                    ? 'bg-emerald-500/20 text-emerald-400'
                    : 'bg-rose-500/20 text-rose-400'
                }`}
              >
                {run.status}
              </span>
            </div>
            <div className="grid grid-cols-2 gap-2 text-[11px]">
              <div>
                <p className="text-slate-500">Signals</p>
                <p className="font-mono text-slate-300">{run.signals_eval || 0}</p>
              </div>
              <div>
                <p className="text-slate-500">Placed</p>
                <p className="font-mono text-emerald-400">{run.orders_placed || 0}</p>
              </div>
              <div>
                <p className="text-slate-500">Skipped</p>
                <p className="font-mono text-amber-400">{run.orders_skipped || 0}</p>
              </div>
              <div>
                <p className="text-slate-500">PnL</p>
                <p
                  className={`font-mono font-bold ${
                    run.total_pnl > 0
                      ? 'text-emerald-400'
                      : run.total_pnl < 0
                      ? 'text-rose-400'
                      : 'text-slate-400'
                  }`}
                >
                  {run.total_pnl?.toFixed(2) || '—'}
                </p>
              </div>
            </div>
            {run.gate_reasons && (
              <p className="mt-2 text-[10px] text-slate-500 truncate" title={run.gate_reasons}>
                {run.gate_reasons}
              </p>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
