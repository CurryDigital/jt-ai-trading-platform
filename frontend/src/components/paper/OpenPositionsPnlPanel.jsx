import React from 'react';

export default function OpenPositionsPnlPanel({ data }) {
  const positions = data?.positions || [];

  if (!positions.length) {
    // Hide entirely when no open positions (as spec'd)
    return null;
  }

  return (
    <div className="rounded-lg bg-slate-800/50 border border-slate-700/50 p-4 mb-6">
      <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-3">
        Open Positions ({positions.length})
      </h3>
      <div className="overflow-x-auto">
        <table className="w-full text-[11px]">
          <thead>
            <tr className="text-slate-500 border-b border-slate-700/50">
              <th className="text-left py-1.5 pr-3">Instrument</th>
              <th className="text-left py-1.5 pr-3">Strategy</th>
              <th className="text-left py-1.5 pr-3">Dir</th>
              <th className="text-right py-1.5 pr-3">Entry</th>
              <th className="text-right py-1.5 pr-3">Current</th>
              <th className="text-right py-1.5 pr-3">Unrealised PnL</th>
              <th className="text-right py-1.5">Days Held</th>
            </tr>
          </thead>
          <tbody>
            {positions.map((p) => (
              <tr key={`${p.strategy_id}-${p.ticker || p.instrument}`} className="border-b border-slate-800/50 hover:bg-slate-800/30">
                <td className="py-1.5 pr-3">
                  <span className="text-[10px] px-1.5 py-0.5 rounded bg-slate-700/50 text-slate-300 font-mono">
                    {p.ticker || p.instrument}
                  </span>
                </td>
                <td className="py-1.5 pr-3 text-slate-300">{p.strategy_id}</td>
                <td className="py-1.5 pr-3">
                  <span className={`text-[10px] px-1.5 py-0.5 rounded ${
                    p.direction === 'long' ? 'bg-emerald-500/20 text-emerald-400' :
                    p.direction === 'short' ? 'bg-rose-500/20 text-rose-400' :
                    'bg-slate-600/20 text-slate-400'
                  }`}>
                    {p.direction?.toUpperCase()}
                  </span>
                </td>
                <td className="py-1.5 pr-3 text-right font-mono text-slate-300">
                  {p.entry_price?.toFixed(2) || '—'}
                </td>
                <td className="py-1.5 pr-3 text-right font-mono text-slate-300">
                  {p.current_price?.toFixed(2) || '—'}
                </td>
                <td className={`py-1.5 pr-3 text-right font-mono font-bold ${
                  p.unrealised_pnl_usd > 0 ? 'text-emerald-400' :
                  p.unrealised_pnl_usd < 0 ? 'text-rose-400' :
                  'text-slate-400'
                }`}>
                  {p.unrealised_pnl_usd?.toFixed(2) || '—'}
                </td>
                <td className="py-1.5 text-right text-slate-500">
                  {p.days_held != null ? `${p.days_held}d` : '—'}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
