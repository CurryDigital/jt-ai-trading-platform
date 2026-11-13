// Command center — ROW 1B EXPOSURE & RISK.

import React from 'react';
import { fmtKCcy } from '../../utils';
import { Panel, EnvChip, Stat, HBar } from './shared';

// Strategy-allocation bars: top five plus a single "Other" roll-up.
export const AllocBars = ({ rows, total, defCcy, label = 'strategy' }) => {
  if (!rows || rows.length === 0 || !total) return null;
  const top = rows.slice(0, 5);
  const restSum = rows.slice(5).reduce((s, r) => s + r.value, 0);
  const items = restSum > 0 ? [...top, { name: `Other · ${rows.length - 5} more`, value: restSum }] : top;
  return (
    <div className="space-y-1.5">
      {items.map(a => (
        <div key={a.name} className="flex items-center gap-2" title={`${a.name}: ${fmtKCcy(a.value, defCcy)} of ${fmtKCcy(total, defCcy)} gross open market value (${(a.value / total * 100).toFixed(1)}%)`}>
          <span className="w-[120px] flex-none text-[12px] text-slate-300 truncate">{a.name}</span>
          <span className="flex-1"><HBar pct={a.value / total * 100} /></span>
          <span className="flex-none font-mono text-[11px] text-slate-300 w-[38px] text-right">{(a.value / total * 100).toFixed(0)}%</span>
        </div>
      ))}
      <div className="text-[11px] text-slate-500">share of gross open market value, by {label}</div>
    </div>
  );
};

// dd: null when no honest drawdown exists; otherwise
// { value, label, sub, tip } — label/tip name the series basis (realized P&L
// curve vs genuine equity history) and the window.
export const ExposurePanel = ({ env, stats, alloc, dd, util, conc }) => (
  <Panel title={<>Exposure &amp; Risk <EnvChip env={env} /></>}>
    <div className="grid grid-cols-2 gap-x-4 gap-y-2.5 px-4 py-3">
      {stats.map(s => <Stat key={s.label} {...s} />)}
      {dd != null && (
        <Stat label={dd.label} value={dd.value} valueCl="text-slate-100" tip={dd.tip} sub={dd.sub} />
      )}
      {conc && (
        <Stat label="Concentration" value={conc.top1 != null ? `${conc.top1.toFixed(0)}% / ${conc.top3?.toFixed(0) ?? '—'}%` : '—'}
          tip={`Top position ${conc.top1Name || ''} = ${conc.top1?.toFixed(1) ?? '—'}% of gross open market value; top 3 = ${conc.top3?.toFixed(1) ?? '—'}%`}
          sub="top 1 / top 3 of gross MV" />
      )}
    </div>
    {util && util.length > 0 && (
      <div className="px-4 py-2.5 border-t border-white/[0.05]">
        <div className="text-[11px] uppercase tracking-wider text-slate-400 mb-1.5">Risk utilization · capital caps</div>
        <div className="space-y-1">
          {util.map(u => (
            <div key={u.strategy_id} className="flex items-center gap-2 text-[12px]" title="Per-strategy capital cap and current utilization">
              <span className="flex-1 text-slate-400 truncate">{u.name}</span>
              <span className="font-mono text-slate-300">{u.used_pct != null ? `${u.used_pct.toFixed(1)}%` : '—'} used</span>
              <span className="font-mono text-slate-500">of {u.capital_cap_pct}%</span>
            </div>
          ))}
        </div>
      </div>
    )}
    <div className="px-4 py-3 border-t border-white/[0.05]">
      <div className="text-[11px] uppercase tracking-wider text-slate-400 mb-2">Allocation</div>
      {alloc}
    </div>
  </Panel>
);
