import React from 'react';

export default function TradeHistoryTable({ history, summary }) {
  const trades = history?.trades || [];

  return (
    <div className="rounded-lg bg-slate-800/50 border border-slate-700/50 p-4 mb-6">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider">
          Trade History (30d)
        </h3>
        {summary && (
          <div className="flex items-center gap-4 text-[11px]">
            <span className="text-slate-500">
              Trades: <span className="text-slate-300 font-mono">{summary.total_trades || 0}</span>
            </span>
            <span className="text-slate-500">
              Win Rate: <span className={`font-mono ${summary.win_rate_pct >= 50 ? 'text-emerald-400' : 'text-rose-400'}`}>
                {summary.win_rate_pct?.toFixed(1) || 0}%
              </span>
            </span>
            <span className="text-slate-500">
              Total PnL: <span className={`font-mono font-bold ${summary.total_pnl >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                {summary.total_pnl?.toFixed(2) || '0.00'}
              </span>
            </span>
            <span className="text-slate-500">
              Avg: <span className="font-mono text-slate-300">{summary.avg_pnl?.toFixed(2) || '0.00'}</span>
            </span>
            <span className="text-slate-500">
              Max DD: <span className="font-mono text-rose-400">{summary.max_drawdown_pct?.toFixed(2) || '0.00'}%</span>
            </span>
          </div>
        )}
      </div>

      {trades.length === 0 ? (
        <p className="text-sm text-slate-500">No trades in last 30 days</p>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-[11px]">
            <thead>
              <tr className="text-slate-500 border-b border-slate-700/50">
                <th className="text-left py-1.5 pr-3">Strategy</th>
                <th className="text-left py-1.5 pr-3">Instrument</th>
                <th className="text-left py-1.5 pr-3">Dir</th>
                <th className="text-right py-1.5 pr-3">Entry</th>
                <th className="text-right py-1.5 pr-3">Exit</th>
                <th className="text-right py-1.5 pr-3">Size</th>
                <th className="text-right py-1.5 pr-3">PnL</th>
                <th className="text-right py-1.5 pr-3">PnL %</th>
                <th className="text-right py-1.5 pr-3">Hold</th>
                <th className="text-right py-1.5">Closed</th>
              </tr>
            </thead>
            <tbody>
              {trades.map((t) => (
                <tr key={t.id} className="border-b border-slate-800/50 hover:bg-slate-800/30">
                  <td className="py-1.5 pr-3 text-slate-300">{t.strategy_id}</td>
                  <td className="py-1.5 pr-3 text-slate-300">{t.ticker || t.instrument}</td>
                  <td className="py-1.5 pr-3">
                    <span className={`text-[10px] px-1.5 py-0.5 rounded ${
                      t.direction === 'long' ? 'bg-emerald-500/20 text-emerald-400' :
                      t.direction === 'short' ? 'bg-rose-500/20 text-rose-400' :
                      'bg-slate-600/20 text-slate-400'
                    }`}>
                      {t.direction}
                    </span>
                  </td>
                  <td className="py-1.5 pr-3 text-right font-mono text-slate-300">
                    {t.entry_price?.toFixed(2) || '—'}
                  </td>
                  <td className="py-1.5 pr-3 text-right font-mono text-slate-300">
                    {t.exit_price?.toFixed(2) || '—'}
                  </td>
                  <td className="py-1.5 pr-3 text-right font-mono text-slate-300">
                    {t.contracts || t.shares || '—'}
                  </td>
                  <td className={`py-1.5 pr-3 text-right font-mono font-bold ${
                    t.pnl > 0 ? 'text-emerald-400' : t.pnl < 0 ? 'text-rose-400' : 'text-slate-400'
                  }`}>
                    {t.pnl?.toFixed(2) || '—'}
                  </td>
                  <td className={`py-1.5 pr-3 text-right font-mono ${
                    t.pnl_pct > 0 ? 'text-emerald-400' : t.pnl_pct < 0 ? 'text-rose-400' : 'text-slate-400'
                  }`}>
                    {t.pnl_pct?.toFixed(2) || '—'}%
                  </td>
                  <td className="py-1.5 pr-3 text-right text-slate-400">
                    {t.hold_days ? `${t.hold_days}d` : '—'}
                  </td>
                  <td className="py-1.5 text-right text-slate-500">
                    {t.closed_at ? new Date(t.closed_at).toLocaleDateString() : '—'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
