import React from 'react';
import { ManualTicket } from '../ManualTicket';

// Shared anatomy for the 4 Execution subtabs (Sim / Paper / UAT / Live):
// one header strip (mode badge + stats) and one grid (content + right rail with
// the same ManualTicket). Mode semantics per user model 2026-08-24:
//   sim   = virtual money, synthetic fills, no IBKR, no close
//   paper = virtual money, strategy rehearsal, no IBKR, DB close
//   uat   = IBKR paper account, real order firing, paper money
//   live  = IBKR live account, real money
export const EXEC_MODE_META = {
  sim:   { badge: 'SIM',   title: 'Simulated Book', note: 'virtual money · synthetic fills · no IBKR' },
  paper: { badge: 'PAPER', title: 'Paper Book',     note: 'virtual money · strategy rehearsal · no IBKR' },
  uat:   { badge: 'UAT',   title: 'UAT',            note: 'IBKR paper account · real order routing · paper money' },
  live:  { badge: 'LIVE',  title: 'Live Book',      note: 'IBKR live account · real money' },
};

export const ExecStat = ({ l, v, tone }) => (
  <div className="text-right">
    <div className="qr-label">{l}</div>
    <div className={`qr-num text-[12px] font-bold leading-tight ${tone || 'text-white'}`}>{v}</div>
  </div>
);

export const ExecScaffold = ({ mode, book, stats, overview, children, railExtra, hideTicket }) => {
  const meta = EXEC_MODE_META[mode];
  return (
    <div className="space-y-3">
      <div className="qr-surface px-3 py-2 flex items-center justify-between flex-wrap gap-2">
        <div className="flex items-center gap-2.5 min-w-0">
          <span className="qr-chip qr-chip-slate flex-none">{meta.badge}</span>
          <div className="min-w-0">
            <div className="text-[12px] font-bold text-white leading-tight">{meta.title}</div>
            <div className="text-[9px] text-slate-500 truncate">{meta.note}</div>
          </div>
        </div>
        {stats && <div className="flex items-center gap-4 flex-wrap">{stats}</div>}
      </div>
      {/* Full-width overview slot (strategy performance + YTD curve) — renders
          above the content/rail grid so the chart spans the whole page. */}
      {overview}
      <div className="grid grid-cols-1 lg:grid-cols-[1fr_300px] gap-3 items-start">
        <div className="space-y-3 min-w-0">{children}</div>
        <div className="space-y-3">
          {!hideTicket && <ManualTicket book={book} />}
          {railExtra}
        </div>
      </div>
    </div>
  );
};

// Shared tab strip for the unified Execution anatomy (live book is the base):
// one qr-surface per subtab, strip on top, tab body below. Tabs are
// { id, label, badge? } — badge is an optional qr-chip class for alerts.
export const ExecTabs = ({ tabs, active, onChange, right }) => (
  <div className="px-3 py-2 border-b border-white/[0.05] flex items-center justify-between flex-wrap gap-2">
    <div className="flex items-center gap-1 flex-wrap">
      {tabs.map(t => (
        <button
          key={t.id}
          onClick={() => onChange(t.id)}
          className={`px-2 py-1 rounded text-[11px] font-semibold transition-colors ${
            active === t.id ? 'bg-white/[0.08] text-white' : 'text-slate-400 hover:text-slate-200'
          }`}
        >
          {t.label}
          {t.badge && <span className={`qr-chip ml-1.5 ${t.badge}`}>{t.badgeText || '!'}</span>}
        </button>
      ))}
    </div>
    {right && <div className="flex items-center gap-2 flex-wrap">{right}</div>}
  </div>
);

// Per-row close action — neutral slate (colour = meaning: no severity here).
export const CloseButton = ({ onClick, busy, disabled, title }) => (
  <button
    onClick={onClick}
    disabled={busy || disabled}
    title={title}
    className="px-2 py-0.5 rounded text-[9px] font-bold uppercase tracking-wide bg-slate-700/80 text-slate-200 hover:bg-slate-600 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
  >
    {busy ? '…' : 'Close'}
  </button>
);

export default ExecScaffold;
