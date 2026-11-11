// Command center — ROW 1C ACTIONS. Strict operational order:
//   1. critical alerts
//   2. execution / monitoring issues (warning severity)
//   3. working orders
//   4. recent activity (fills, exits) — always with absolute timestamps;
//      older fills are never labeled "Today".

import React from 'react';
import { pnlCl } from '../../utils';
import { Panel, EnvChip } from './shared';
import { sK, tsTip } from './format';
import { SEV_DOT } from './meta';

export const ActionsPanel = ({ env, items, facts, latestFills, navigateToTab }) => {
  const critical = items.filter(i => i.sev === 'critical');
  const issues = items.filter(i => i.sev !== 'critical');
  const renderItem = (it, i) => (
    <button key={`${it.id}-${i}`} onClick={() => it.target ? navigateToTab(it.target) : undefined}
      className="w-full flex items-center gap-2.5 px-4 py-2 text-left hover:bg-white/[0.03]"
      title={it.tip || it.impact || it.title}>
      <span className={`w-2 h-2 rounded-full flex-none ${SEV_DOT[it.sev] || SEV_DOT.info}`} />
      <span className="min-w-0 flex-1">
        <span className="block text-[12px] font-bold text-slate-100 leading-snug truncate">{it.title}</span>
        {it.impact && <span className="block text-[11px] text-slate-400 leading-snug truncate">{it.impact}</span>}
      </span>
      {it.date && <span className="flex-none font-mono text-[11px] text-slate-500" title={it.dateTip || undefined}>{it.date}</span>}
      {it.target && <span className="flex-none text-[11px] text-blue-400">→</span>}
    </button>
  );
  return (
    <Panel title={<>Actions <EnvChip env={env} /></>} action={
      items.length > 0
        ? <span className="text-[11px] text-slate-400">{critical.length} critical · {issues.length} issue{issues.length === 1 ? '' : 's'}</span>
        : null
    }>
      {items.length === 0 ? (
        <div className="px-4 py-2.5 text-[12px] text-slate-500">No action required — halt clear, no environment alerts.</div>
      ) : (
        <div className="divide-y divide-white/[0.05]">
          {critical.map(renderItem)}
          {issues.length > 0 && critical.length > 0 && (
            <div className="px-4 py-1 text-[10px] uppercase tracking-wider text-slate-500 bg-white/[0.02]">Execution / monitoring issues</div>
          )}
          {issues.map(renderItem)}
        </div>
      )}
      {/* 3–4. working orders, then recent activity */}
      <div className="border-t border-white/[0.05] divide-y divide-white/[0.05]">
        {facts.map((f, i) => (
          <button key={i} onClick={() => f.target ? navigateToTab(f.target) : undefined}
            className="w-full flex items-center gap-2.5 px-4 py-2 text-left hover:bg-white/[0.03]" title={f.tip}>
            <span className="flex-1 text-[12px] text-slate-400">{f.label}</span>
            <span className={`font-mono text-[12px] text-right ${f.valueCl || 'text-slate-200'}`}>{f.value}</span>
            {f.target && <span className="flex-none text-[11px] text-blue-400">→</span>}
          </button>
        ))}
      </div>
      {latestFills && latestFills.length > 0 && (
        <div className="border-t border-white/[0.05]">
          <div className="px-4 pt-2 pb-1 text-[11px] uppercase tracking-wider text-slate-400">Recent activity · latest fills</div>
          <div className="divide-y divide-white/[0.05]">
            {latestFills.map((t, i) => (
              <button key={`${t.key}-${i}`} onClick={() => navigateToTab('execution')}
                className="w-full flex items-center gap-2 px-4 py-1.5 text-left hover:bg-white/[0.03]"
                title={t.fillTs ? `filled ${tsTip(t.fillTs)}${t.strategy ? ` · ${t.strategy}` : ''}` : undefined}>
                <span className="flex-none font-mono text-[11px] text-slate-400 w-[72px]">{t.fillDate ?? '—'}</span>
                <span className="flex-none font-mono text-[12px] font-bold text-white">{t.ticker}</span>
                <span className={`flex-none font-mono text-[11px] font-bold ${t.side === 'BUY' || t.side === 'LONG' ? 'text-emerald-400' : t.side === 'SELL' || t.side === 'SHORT' ? 'text-rose-400' : 'text-slate-400'}`}>{t.side ?? '—'}</span>
                <span className="flex-1" />
                <span className={`flex-none font-mono text-[11px] ${t.pnl != null ? pnlCl(t.pnl) : 'text-slate-600'}`}>{t.pnl != null ? sK(t.pnl) : '—'}</span>
              </button>
            ))}
          </div>
        </div>
      )}
    </Panel>
  );
};
