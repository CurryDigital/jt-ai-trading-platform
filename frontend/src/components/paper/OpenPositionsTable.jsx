import React from 'react';

export default function OpenPositionsTable({ data }) {
  const positions = data?.positions || [];

  if (!positions.length) {
    return (
      <div className="rounded-lg bg-slate-800/50 border border-slate-700/50 p-4 mb-6">
        <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">Open Positions</h3>
        <p className="text-sm text-slate-500">No open positions</p>
      </div>
    );
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
              <th className="text-left py-1.5 pr-3">Strategy</th>
              <th className="text-left py-1.5 pr-3">Instrument</th>
              <th className="text-left py-1.5 pr-3">Dir</th>
              <th className="text-right py-1.5 pr-3">Entry</th>
              <th className="text-right py-1.5 pr-3">Current</th>
              <th className="text-right py-1.5 pr-3">Size</th>
              <th className="text-right py-1.5 pr-3">Unrealised PnL</th>
              <th className="text-right py-1.5 pr-3">Regime</th>
              <th className="text-right py-1.5">Hold</th>
            </tr>
          </thead>
          <tbody>
            {positions.map((p) => (
              <tr key={p.id} className="border-b border-slate-800/50 hover:bg-slate-800/30">
                <td className="py-1.5 pr-3 text-slate-300">{p.strategy_id}</td>
                <td className="py-1.5 pr-3 text-slate-300">{p.ticker || p.instrument}</td>
                <td className="py-1.5 pr-3">
                  <span className={`text-[10px] px-1.5 py-0.5 rounded ${
                    p.direction === 'long' ? 'bg-emerald-500/20 text-emerald-400' :
                    p.direction === 'short' ? 'bg-rose-500/20 text-rose-400' :
                    'bg-slate-600/20 text-slate-400'
                  }`}>
                    {p.direction}
                  </span>
                </td>
                <td className="py-1.5 pr-3 text-right font-mono text-slate-300">
                  {p.entry_price?.toFixed(2) || '—'}
                </td>
                <td className="py-1.5 pr-3 text-right font-mono text-slate-300">
                  {p.current_price?.toFixed(2) || '—'}
                </td>
                <td className="py-1.5 pr-3 text-right font-mono text-slate-300">
                  {p.contracts || p.shares || '—'}
                </td>
                <td className={`py-1.5 pr-3 text-right font-mono font-bold ${
                  p.unrealised_pnl > 0 ? 'text-emerald-400' :
                  p.unrealised_pnl < 0 ? 'text-rose-400' :
                  'text-slate-400'
                }`}>
                  {p.unrealised_pnl?.toFixed(2) || '—'}
                </td>
                <td className="py-1.5 pr-3 text-right text-slate-400">{p.regime_at_entry}</td>
                <td className="py-1.5 text-right text-slate-500">
                  {p.hold_duration ? p.hold_duration.split('.')[0] : '—'}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
