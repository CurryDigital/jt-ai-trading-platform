import React from 'react';
import { CloseButton } from '../execution/ExecScaffold';
import { pnlCl } from '../../utils';

export default function OpenPositionsTable({ data, onClose, closeState, loading, error }) {
  const positions = data?.positions || [];
  // Distinguish measured-empty from source-failure (backend returns
  // {positions: [], error} on exception; the hook surfaces transport errors).
  const sourceError = error || data?.error;

  return (
    <div className="qr-surface overflow-hidden">
      <div className="px-3 py-2 border-b border-white/[0.05] flex items-center justify-between">
        <span className="qr-label">Open Positions{positions.length ? ` (${positions.length})` : ''}</span>
        {positions.length > 0 && onClose && (
          <span className="text-[9px] text-slate-600">Close = DB close at latest mark · no IBKR</span>
        )}
      </div>
      {sourceError ? (
        <div className="py-6 text-center text-[11px] text-slate-500">
          <span className="qr-chip qr-chip-rose mr-2">PENDING</span>
          Position source error — auto-retrying · <span className="font-mono text-[10px]">{String(sourceError).slice(0, 120)}</span>
        </div>
      ) : loading && !data ? (
        <div className="py-6 text-center text-slate-600 text-[11px]">Loading positions…</div>
      ) : !positions.length ? (
        <div className="py-6 text-center text-slate-600 text-[11px]">No open positions</div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-[11px]">
            <thead className="bg-white/[0.02]">
              <tr className="border-b border-white/[0.06]">
                <th className="qr-label text-left py-1.5 px-2">Strategy</th>
                <th className="qr-label text-left py-1.5 px-2">Instrument</th>
                <th className="qr-label text-right py-1.5 px-2">Dir</th>
                <th className="qr-label text-right py-1.5 px-2">Entry</th>
                <th className="qr-label text-right py-1.5 px-2">Current</th>
                <th className="qr-label text-right py-1.5 px-2">Size</th>
                <th className="qr-label text-right py-1.5 px-2">Unrealised PnL</th>
                <th className="qr-label text-right py-1.5 px-2">Regime</th>
                <th className="qr-label text-right py-1.5 px-2">Hold</th>
                {onClose && <th className="qr-label text-right py-1.5 px-2"></th>}
              </tr>
            </thead>
            <tbody className="divide-y divide-white/[0.04]">
              {positions.map((p, i) => (
                <tr key={`${p.id}-${i}`} className="qr-tr-hover">
                  <td className="py-1.5 px-2 text-[10px] font-mono text-slate-300 truncate max-w-[120px]">{p.strategy_id}</td>
                  <td className="py-1.5 px-2 font-mono text-white">{p.ticker || p.instrument}</td>
                  <td className="py-1.5 px-2 text-right">
                    <span className={`qr-chip ${p.direction === 'long' ? 'qr-chip-emerald' : p.direction === 'short' ? 'qr-chip-rose' : 'qr-chip-slate'}`}>
                      {p.direction}
                    </span>
                  </td>
                  <td className="py-1.5 px-2 text-right qr-num text-slate-400">{p.entry_price?.toFixed(2) || '—'}</td>
                  <td className="py-1.5 px-2 text-right qr-num text-white">{p.current_price?.toFixed(2) || '—'}</td>
                  <td className="py-1.5 px-2 text-right qr-num text-slate-300">{p.contracts || p.shares || '—'}</td>
                  <td className={`py-1.5 px-2 text-right qr-num font-bold ${pnlCl(p.unrealised_pnl)}`}>
                    {p.unrealised_pnl?.toFixed(2) || '—'}
                  </td>
                  <td className="py-1.5 px-2 text-right text-slate-400">{p.regime_at_entry || '—'}</td>
                  <td className="py-1.5 px-2 text-right text-slate-500">{p.hold_duration ? p.hold_duration.split('.')[0] : '—'}</td>
                  {onClose && (
                    <td className="py-1.5 px-2 text-right whitespace-nowrap">
                      <CloseButton
                        busy={closeState?.id === p.id && closeState.busy}
                        onClick={() => onClose(p)}
                      />
                      {closeState?.id === p.id && closeState.msg && (
                        <div className={`text-[9px] mt-0.5 ${closeState.msg.type === 'success' ? 'text-emerald-400' : 'text-rose-400'}`}>
                          {closeState.msg.text}
                        </div>
                      )}
                    </td>
                  )}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
