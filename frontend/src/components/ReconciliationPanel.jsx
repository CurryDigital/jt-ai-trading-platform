import React, { useEffect, useState } from 'react';
import { api, fmt, fmtK, fmtAge, pnlCl } from '../utils';

const KIND_STYLE = {
  db_only:      { chip: 'qr-chip-amber',   label: 'DB ONLY'    },
  trades_only:  { chip: 'qr-chip-violet',  label: 'TRADES ONLY' },
  qty_mismatch: { chip: 'qr-chip-rose',    label: 'QTY MISMATCH' },
};

const MODE_STYLE = {
  SIMULATION:    'qr-chip-blue',
  PAPER_TRADING: 'qr-chip-amber',
  LIVE_TRADING:  'qr-chip-rose',
};

export const ReconciliationPanel = ({ onSelectStrategy }) => {
  const [data, setData] = useState(null);
  const [busy, setBusy] = useState(false);
  const [refreshedAt, setRefreshedAt] = useState(null);
  const [filter, setFilter] = useState('all');

  const load = async () => {
    setBusy(true);
    const res = await api.get('/api/reconciliation/positions');
    setBusy(false);
    if (res) setData(res);
    setRefreshedAt(new Date().toISOString());
  };

  useEffect(() => {
    load();
    const id = setInterval(load, 30000);
    return () => clearInterval(id);
  }, []);

  if (!data) {
    return (
      <div className="qr-surface px-3 py-6 flex items-center justify-center gap-2 text-[11px] text-slate-500">
        <div className="w-3 h-3 border-2 border-slate-700 border-t-blue-500 rounded-full animate-spin" />
        Loading reconciliation…
      </div>
    );
  }

  const s = data.summary || {};
  const breached = (s.discrepancy_count || 0) > 0;
  const visible = filter === 'all'
    ? data.discrepancies
    : data.discrepancies.filter(d => d.kind === filter);

  return (
    <div className="space-y-3">
      <div className="flex items-end justify-between flex-wrap gap-2">
        <div>
          <h2 className="text-sm font-bold text-white tracking-tight">Reconciliation</h2>
          <p className="text-[10px] text-slate-500">DB positions ↔ trade history ↔ IBKR · auto-refresh 30s</p>
        </div>
        <div className="flex items-center gap-2">
          <span className="qr-num text-[10px] text-slate-500">upd {fmtAge(refreshedAt)}</span>
          <button onClick={load} disabled={busy} className="qr-btn-ghost">{busy ? '…' : '↻'}</button>
        </div>
      </div>

      {/* Status banner */}
      <div className={`qr-surface px-3 py-2 ring-1 ${breached ? 'ring-rose-500/30 bg-rose-500/5' : 'ring-emerald-500/20 bg-emerald-500/5'}`}>
        <div className="flex items-center gap-3 flex-wrap text-[12px]">
          <span className={`qr-chip ${breached ? 'qr-chip-rose' : 'qr-chip-emerald'}`}>
            {breached ? `${s.discrepancy_count} DISCREPANCY${s.discrepancy_count > 1 ? 'IES' : ''}` : 'IN SYNC'}
          </span>
          <span className="text-slate-400">{s.db_count} DB rows</span>
          <span className="text-slate-700">·</span>
          <span className="text-slate-400">{s.trade_keys} trade keys</span>
          {breached && (
            <>
              <span className="text-slate-700">·</span>
              {s.by_kind?.qty_mismatch > 0 && <span className="text-rose-300">{s.by_kind.qty_mismatch} qty</span>}
              {s.by_kind?.db_only > 0      && <span className="text-amber-300">{s.by_kind.db_only} db-only</span>}
              {s.by_kind?.trades_only > 0  && <span className="text-violet-300">{s.by_kind.trades_only} trade-only</span>}
            </>
          )}
        </div>
      </div>

      {/* IBKR snapshot */}
      <div className="qr-surface p-3">
        <div className="flex items-center gap-2 mb-2">
          <span className="qr-label">IBKR snapshot</span>
          <span className={`qr-chip ${data.ibkr?.connected ? 'qr-chip-emerald' : 'qr-chip-slate'}`}>
            {data.ibkr?.connected ? 'CONNECTED' : 'OFFLINE'}
          </span>
        </div>
        {data.ibkr?.connected && data.ibkr.snapshot ? (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
            {Object.entries(data.ibkr.snapshot).slice(0, 8).map(([k, v]) => (
              <div key={k} className="px-2 py-1.5 rounded bg-slate-900/60 ring-1 ring-white/[0.04]">
                <div className="qr-label">{k.replace(/_/g, ' ')}</div>
                <div className="qr-num text-[12px] text-white font-bold">
                  {typeof v === 'number' ? fmtK(v) : (v ?? '—')}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-[10px] text-slate-600">
            {data.ibkr?.connected
              ? 'IBKR connected but no snapshot returned.'
              : 'IBKR gateway not reachable. Funding/positions check skipped — DB↔trade reconciliation still active.'}
          </div>
        )}
      </div>

      {/* Discrepancies table */}
      <div className="qr-surface overflow-hidden">
        <div className="px-3 py-2 border-b border-white/[0.05] flex items-center justify-between">
          <div className="flex items-center gap-1">
            {[
              { id: 'all',          label: `All (${data.discrepancies.length})` },
              { id: 'qty_mismatch', label: `Qty (${s.by_kind?.qty_mismatch || 0})` },
              { id: 'db_only',      label: `DB only (${s.by_kind?.db_only || 0})` },
              { id: 'trades_only',  label: `Trade only (${s.by_kind?.trades_only || 0})` },
            ].map(t => (
              <button
                key={t.id}
                onClick={() => setFilter(t.id)}
                className={`px-2 py-1 rounded text-[11px] font-semibold transition-colors ${
                  filter === t.id ? 'bg-white/[0.08] text-white' : 'text-slate-400 hover:text-slate-200'
                }`}
              >{t.label}</button>
            ))}
          </div>
        </div>

        <div className="overflow-x-auto max-h-96 overflow-y-auto">
          <table className="w-full">
            <thead className="qr-th-sticky">
              <tr className="border-b border-white/[0.06]">
                <th className="qr-label text-left  py-1 px-2">Kind</th>
                <th className="qr-label text-left  py-1 px-2">Strategy</th>
                <th className="qr-label text-left  py-1 px-2">Ticker</th>
                <th className="qr-label text-right py-1 px-2">Mode</th>
                <th className="qr-label text-right py-1 px-2">DB Qty</th>
                <th className="qr-label text-right py-1 px-2">Trade Qty</th>
                <th className="qr-label text-right py-1 px-2">Δ</th>
                <th className="qr-label text-right py-1 px-2">Last Fill</th>
                <th className="qr-label text-left  py-1 px-2">Note</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/[0.04]">
              {visible.map((d, i) => {
                const style = KIND_STYLE[d.kind] || { chip: 'qr-chip-slate', label: d.kind };
                return (
                  <tr key={`${d.strategy_id}-${d.ticker}-${i}`} className="qr-tr-hover">
                    <td className="py-1 px-2"><span className={`qr-chip ${style.chip}`}>{style.label}</span></td>
                    <td className="py-1 px-2 text-[10px] font-mono text-slate-300 truncate max-w-[140px]">
                      <button onClick={() => onSelectStrategy?.(d.strategy_id)} className="hover:text-blue-300">{d.strategy_id}</button>
                    </td>
                    <td className="py-1 px-2 text-[11px] font-mono text-white">{d.ticker}</td>
                    <td className="py-1 px-2 text-right">
                      <span className={`qr-chip ${MODE_STYLE[d.execution_mode] || 'qr-chip-slate'}`}>
                        {(d.execution_mode || '').replace('_TRADING','').replace('SIMULATION','SIM')}
                      </span>
                    </td>
                    <td className="py-1 px-2 qr-num text-slate-300">{fmt(d.db_qty, 4)}</td>
                    <td className="py-1 px-2 qr-num text-slate-300">{fmt(d.trade_qty, 4)}</td>
                    <td className={`py-1 px-2 qr-num font-bold ${pnlCl(d.delta_qty)}`}>{fmt(d.delta_qty, 4)}</td>
                    <td className="py-1 px-2 qr-num text-[10px] text-slate-500 text-right">{d.last_fill_at ? fmtAge(d.last_fill_at) : '—'}</td>
                    <td className="py-1 px-2 text-[10px] text-slate-400 truncate max-w-[280px]">{d.note}</td>
                  </tr>
                );
              })}
              {!visible.length && (
                <tr><td colSpan={9} className="py-8 text-center text-slate-600 text-[11px]">
                  {filter === 'all' ? 'No discrepancies — DB and trade history are consistent ✓' : `No ${filter.replace('_', ' ')} discrepancies`}
                </td></tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* DB positions table */}
      <div className="qr-surface overflow-hidden">
        <div className="px-3 py-2 border-b border-white/[0.05]">
          <span className="qr-label">DB Positions ({data.db_positions.length})</span>
        </div>
        <div className="overflow-x-auto max-h-72 overflow-y-auto">
          <table className="w-full">
            <thead className="qr-th-sticky">
              <tr className="border-b border-white/[0.06]">
                <th className="qr-label text-left  py-1 px-2">Strategy</th>
                <th className="qr-label text-left  py-1 px-2">Ticker</th>
                <th className="qr-label text-right py-1 px-2">Mode</th>
                <th className="qr-label text-right py-1 px-2">Qty</th>
                <th className="qr-label text-right py-1 px-2">Entry</th>
                <th className="qr-label text-right py-1 px-2">Invested</th>
                <th className="qr-label text-right py-1 px-2">Unreal P&L</th>
                <th className="qr-label text-right py-1 px-2">Real P&L</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/[0.04]">
              {data.db_positions.map(p => (
                <tr key={p.id} className="qr-tr-hover">
                  <td className="py-1 px-2 text-[10px] font-mono text-slate-300 truncate max-w-[140px]">
                    <button onClick={() => onSelectStrategy?.(p.strategy_id)} className="hover:text-blue-300">{p.strategy_id}</button>
                  </td>
                  <td className="py-1 px-2 text-[11px] font-mono text-white">{p.ticker}</td>
                  <td className="py-1 px-2 text-right">
                    <span className={`qr-chip ${MODE_STYLE[p.execution_mode] || 'qr-chip-slate'}`}>
                      {(p.execution_mode || '').replace('_TRADING','').replace('SIMULATION','SIM')}
                    </span>
                  </td>
                  <td className="py-1 px-2 qr-num text-slate-300">{fmt(p.implied_qty, 4)}</td>
                  <td className="py-1 px-2 qr-num text-slate-400">{fmt(p.entry_price)}</td>
                  <td className="py-1 px-2 qr-num text-slate-300">{fmtK(p.invested_capital)}</td>
                  <td className={`py-1 px-2 qr-num font-bold ${pnlCl(p.unrealized_pnl)}`}>{fmtK(p.unrealized_pnl)}</td>
                  <td className={`py-1 px-2 qr-num ${pnlCl(p.realized_pnl)}`}>{fmtK(p.realized_pnl)}</td>
                </tr>
              ))}
              {!data.db_positions.length && (
                <tr><td colSpan={8} className="py-6 text-center text-slate-600 text-[11px]">No DB positions</td></tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default ReconciliationPanel;
