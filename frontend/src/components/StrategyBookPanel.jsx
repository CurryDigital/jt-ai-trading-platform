import React from 'react';

export default function StrategyBookPanel({ data }) {
  const strategies = data?.strategies || [];

  if (!strategies.length) {
    return (
      <div className="rounded-lg bg-slate-800/50 border border-slate-700/50 p-4 mb-6">
        <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">
          Strategy Book
        </h3>
        <p className="text-sm text-slate-500">No strategies</p>
      </div>
    );
  }

  const statusColors = {
    approved: 'bg-emerald-500/20 text-emerald-400',
    backtesting: 'bg-blue-500/20 text-blue-400',
    rejected: 'bg-rose-500/20 text-rose-400',
    pending: 'bg-slate-600/20 text-slate-400',
  };

  return (
    <div className="mb-6">
      <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-3">
        Strategy Book ({strategies.length})
      </h3>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
        {strategies.map((s) => (
          <div
            key={s.strategy_id}
            className="rounded-lg bg-slate-800/50 border border-slate-700/50 p-3 hover:border-slate-600/50 transition-colors"
          >
            <div className="flex items-center justify-between mb-2">
              <span className="text-[11px] font-mono text-slate-300 truncate" title={s.strategy_id}>
                {s.strategy_id}
              </span>
              <span className={`text-[10px] px-1.5 py-0.5 rounded ${statusColors[s.status] || 'bg-slate-600/20 text-slate-400'}`}>
                {s.status}
              </span>
            </div>
            <p className="text-xs text-slate-400 mb-2 truncate" title={s.name}>
              {s.name}
            </p>
            <div className="grid grid-cols-3 gap-2 text-[10px] mb-2">
              <div>
                <p className="text-slate-500">Sharpe</p>
                <p className="font-mono text-slate-300">{s.sharpe_ratio?.toFixed(2) || '—'}</p>
              </div>
              <div>
                <p className="text-slate-500">Win Rate</p>
                <p className="font-mono text-slate-300">{s.win_rate ? `${(s.win_rate * 100).toFixed(0)}%` : '—'}</p>
              </div>
              <div>
                <p className="text-slate-500">Asset</p>
                <p className="text-slate-300">{s.asset_class || '—'}</p>
              </div>
            </div>
            <div className="flex items-center justify-between text-[10px]">
              <span className="text-slate-500">Source: <span className="text-slate-400">{s.agent_source}</span></span>
              {s.last_traded_at && (
                <span className="text-slate-500">
                  Last: {new Date(s.last_traded_at).toLocaleDateString()}
                </span>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
