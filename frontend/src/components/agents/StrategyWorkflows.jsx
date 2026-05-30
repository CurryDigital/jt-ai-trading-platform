import React from 'react';
import { STATUS_COLORS, extractSymbols, formatTimeAgo } from './utils';

export function StrategyWorkflows({ workflows, onSelectStrategy }) {
  if (!workflows.length) {
    return (
      <div className="text-center p-12 text-slate-500">
        <div className="text-3xl mb-3">🔗</div>
        <p className="text-sm font-medium text-slate-400">No workflows yet</p>
        <p className="text-[11px] text-slate-600 mt-1">Strategy workflows will appear here as the pipeline processes ideas.</p>
      </div>
    );
  }

  return (
    <div className="divide-y divide-white/5 max-h-[600px] overflow-y-auto">
      {workflows.map(w => {
        const statusClass = STATUS_COLORS[w.status] || STATUS_COLORS.pending;
        const symbols = extractSymbols(w.name);
        return (
          <button
            key={w.strategy_id}
            onClick={() => onSelectStrategy(w.strategy_id)}
            className="p-4 text-left hover:bg-white/[0.02] transition-colors w-full"
          >
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-2 flex-wrap">
                <span className="text-xs font-bold text-white">{w.name || w.strategy_id}</span>
                <span className={`text-[9px] px-1.5 py-0.5 rounded font-bold uppercase tracking-wider ${statusClass}`}>
                  {w.status}
                </span>
                {symbols.length > 0 && (
                  <div className="flex gap-1">
                    {symbols.map(s => (
                      <span key={s} className="text-[8px] px-1 py-0.5 rounded bg-amber-500/15 text-amber-400 font-mono font-bold">{s}</span>
                    ))}
                  </div>
                )}
              </div>
              <span className="text-[10px] text-slate-600">{formatTimeAgo(w.updated_at)}</span>
            </div>
            <div className="flex items-center gap-3 text-[10px] text-slate-500">
              {w.assigned_to && (
                <span>Assigned: <span className="text-slate-400">{w.assigned_to}</span></span>
              )}
              {w.latest_sharpe != null && (
                <span>Sharpe: <span className="text-white font-mono">{w.latest_sharpe.toFixed(2)}</span></span>
              )}
              <span>{w.event_count ?? 0} events</span>
            </div>
          </button>
        );
      })}
    </div>
  );
}
