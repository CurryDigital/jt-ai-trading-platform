// Command center — shared presentational primitives. Component-only exports
// (plus one string constant) for react-refresh/only-export-components.

import React from 'react';
import { fmtAge } from '../../utils';
import { tsTip } from './format';
import { ENV_META } from './meta';

export const selectCl = 'bg-[#0a0d12] border border-white/[0.10] rounded px-2 py-1 text-[12px] text-slate-300';

export const LinkBtn = ({ children, onClick }) => (
  <button onClick={onClick} className="text-[12px] font-semibold text-blue-400 hover:text-blue-300">{children}</button>
);

// Panel — section headings are primary readability targets: 13px bold,
// high-contrast slate-200 (v7.1 readability pass).
export const Panel = ({ title, action, children, className = '' }) => (
  <div className={`qr-surface overflow-hidden ${className}`}>
    <div className="flex items-center justify-between gap-3 px-4 py-2.5 border-b border-white/[0.05]">
      <span className="text-[13px] font-bold uppercase tracking-wider text-slate-200 flex items-center gap-2">{title}</span>
      {action}
    </div>
    {children}
  </div>
);

export const EnvChip = ({ env }) => (
  <span className="qr-chip qr-chip-slate" title={ENV_META[env].tip}>{ENV_META[env].badge}</span>
);

// Honest no-data state: an environment that lacks supported data says so
// explicitly — another environment's data is never relabeled into the gap.
export const NoData = ({ children }) => (
  <div className="px-4 py-3 text-[13px] text-slate-500">{children}</div>
);

export const AsOf = ({ ts }) => {
  if (!ts) return null;
  return <span className="font-mono text-[11px] text-slate-500 normal-case tracking-normal" title={`Payload as_of ${tsTip(ts)}`}>upd {fmtAge(ts)}</span>;
};

// Compact secondary stat: readable 11px slate-400 label, 18px value.
export const Stat = ({ label, value, valueCl = 'text-slate-100', sub, tip }) => (
  <div className="min-w-0" title={tip}>
    <div className="text-[11px] uppercase tracking-wider text-slate-400">{label}</div>
    <div className={`font-mono text-[18px] font-bold leading-tight mt-0.5 truncate ${valueCl}`} style={{ fontVariantNumeric: 'tabular-nums' }}>{value}</div>
    {sub != null && <div className="text-[11px] text-slate-500 leading-snug mt-0.5">{sub}</div>}
  </div>
);

// Thin horizontal share bar (neutral slate; magnitude is the message).
export const HBar = ({ pct }) => (
  <div className="h-1 rounded bg-white/[0.06] overflow-hidden w-full">
    <div className="h-full bg-slate-400/70" style={{ width: `${Math.max(0, Math.min(100, pct))}%` }} />
  </div>
);

export const PageBtn = ({ disabled, onClick, children }) => (
  <button disabled={disabled} onClick={onClick}
    className="px-2.5 py-1 text-[12px] font-semibold rounded border border-white/[0.10] text-slate-300 hover:bg-white/[0.06] disabled:opacity-40 disabled:hover:bg-transparent disabled:cursor-default">
    {children}
  </button>
);
