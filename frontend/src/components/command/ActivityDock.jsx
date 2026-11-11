// Command center — ROW 4 ACTIVITY DOCK (secondary): Orders | Fills |
// Signals | Context. Nothing analytical hides behind these tabs.

import React from 'react';
import { pnlCl } from '../../utils';
import { sK, tsTip } from './format';

export const OrdersTable = ({ rows }) => (
  <div className="overflow-x-auto">
    <table className="w-full min-w-[640px]">
      <thead>
        <tr className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider bg-white/[0.02]">
          <th className="text-left px-4 py-2" title="Absolute order date (YYYY-MM-DD), newest first where served">Order date</th>
          <th className="text-left px-3 py-2">Ticker</th>
          <th className="text-left px-3 py-2">Side</th>
          <th className="text-right px-3 py-2">Qty</th>
          <th className="text-right px-3 py-2">Limit / type</th>
          <th className="text-left px-3 py-2">Strategy</th>
          <th className="text-left px-4 py-2">Status</th>
        </tr>
      </thead>
      <tbody>
        {rows.map((o, i) => (
          <tr key={o.key || `${o.ticker}-${i}`} className="border-t border-white/[0.05] text-[13px] leading-5 hover:bg-white/[0.02]">
            <td className="px-4 py-2 font-mono text-slate-300 whitespace-nowrap" title={o.orderTs ? tsTip(o.orderTs) : o.orderTip || undefined}>
              {o.orderDate ?? '—'}
            </td>
            <td className="px-3 py-2 font-mono font-bold text-white">{o.ticker}</td>
            <td className={`px-3 py-2 font-mono font-bold ${o.side === 'BUY' ? 'text-emerald-400' : o.side === 'SELL' || o.side === 'CLOSE' ? 'text-rose-400' : 'text-slate-400'}`}>{o.side ?? '—'}</td>
            <td className="px-3 py-2 text-right font-mono text-slate-200" style={{ fontVariantNumeric: 'tabular-nums' }}>{o.qty != null ? o.qty.toLocaleString() : '—'}</td>
            <td className="px-3 py-2 text-right font-mono text-slate-300">{o.limitOrType ?? '—'}</td>
            <td className="px-3 py-2 text-[12px] text-slate-400 max-w-[200px] truncate" title={o.strategy || undefined}>{o.strategy ?? '—'}</td>
            <td className="px-4 py-2"><span className="text-[11px] px-1.5 py-0.5 rounded bg-white/[0.06] text-slate-300">{o.status ?? '—'}</span></td>
          </tr>
        ))}
      </tbody>
    </table>
  </div>
);

export const FillsTable = ({ rows }) => (
  <div className="overflow-x-auto">
    <table className="w-full min-w-[700px]">
      <thead>
        <tr className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider bg-white/[0.02]">
          <th className="text-left px-4 py-2" title="Absolute fill date (YYYY-MM-DD), newest first; exact UTC timestamp in row tooltip">Fill date</th>
          <th className="text-left px-3 py-2">Ticker</th>
          <th className="text-left px-3 py-2">Strategy</th>
          <th className="text-left px-3 py-2">Side</th>
          <th className="text-right px-3 py-2">Qty</th>
          <th className="text-right px-3 py-2">Price</th>
          <th className="text-right px-4 py-2">Realized P&L</th>
        </tr>
      </thead>
      <tbody>
        {rows.map((t, i) => (
          <tr key={t.key || `${t.fillTs}-${t.ticker}-${i}`} className="border-t border-white/[0.05] text-[13px] leading-5 hover:bg-white/[0.02]" title={t.fillTs ? `filled ${tsTip(t.fillTs)}` : undefined}>
            <td className="px-4 py-2 font-mono text-slate-300 whitespace-nowrap">{t.fillDate ?? '—'}</td>
            <td className="px-3 py-2 font-mono font-bold text-white">{t.ticker}</td>
            <td className="px-3 py-2 text-[12px] text-slate-400 max-w-[220px] truncate" title={t.strategyTip || t.strategy || undefined}>{t.strategy ?? '—'}</td>
            <td className={`px-3 py-2 font-mono font-bold ${t.side === 'BUY' || t.side === 'LONG' ? 'text-emerald-400' : t.side === 'SELL' || t.side === 'SHORT' ? 'text-rose-400' : 'text-slate-400'}`}>{t.side ?? '—'}</td>
            <td className="px-3 py-2 text-right font-mono text-slate-200" style={{ fontVariantNumeric: 'tabular-nums' }}>{t.qty != null ? t.qty.toLocaleString() : '—'}</td>
            <td className="px-3 py-2 text-right font-mono text-slate-300" style={{ fontVariantNumeric: 'tabular-nums' }}>{t.price != null ? t.price.toLocaleString(undefined, { maximumFractionDigits: 2 }) : '—'}</td>
            <td className={`px-4 py-2 text-right font-mono font-bold whitespace-nowrap ${t.pnl != null ? pnlCl(t.pnl) : 'text-slate-600'}`} style={{ fontVariantNumeric: 'tabular-nums' }}
              title={t.pnl == null ? (t.pnlTip || undefined) : undefined}>
              {t.pnl != null ? sK(t.pnl) : '—'}
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  </div>
);

export const ActivityDock = ({ tab, onTab, tabs, children }) => (
  <div className="qr-surface overflow-hidden">
    <div className="flex items-center gap-1 px-2 border-b border-white/[0.06] overflow-x-auto" role="tablist" aria-label="Activity">
      <span className="px-2 py-2.5 text-[11px] font-bold uppercase tracking-wider text-slate-400 flex-none">Activity</span>
      {tabs.map(t => (
        <button key={t.k} role="tab" aria-selected={tab === t.k} onClick={() => onTab(t.k)}
          className={`px-3 py-2.5 text-[12px] font-bold uppercase tracking-wider whitespace-nowrap border-b-2 -mb-px transition-colors ${tab === t.k ? 'text-white border-white/70' : 'text-slate-500 border-transparent hover:text-slate-300'}`}>
          {t.label}
          {t.count != null && <span className="ml-1.5 font-mono text-[11px] font-normal text-slate-400">{t.count}</span>}
        </button>
      ))}
    </div>
    {children}
  </div>
);
