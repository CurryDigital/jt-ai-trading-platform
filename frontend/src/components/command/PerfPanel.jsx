// Command center — ROW 1A PERFORMANCE. Primary P&L focal at 30px; realized /
// unrealized / day separated where supported; curve visible; period + env +
// currency labels on every figure.

import React from 'react';
import { Panel, EnvChip, Stat } from './shared';
import { EquityCurve } from './EquityCurve';

export const PerfPanel = ({ env, footnote, curve, curveNote, curveEmpty, focal, focalCl, focalSub, secondaries }) => (
  <Panel title={<>Performance <EnvChip env={env} /></>} action={
    <span className="text-[11px] text-slate-500">{curveNote}</span>
  }>
    <div className="px-4 pt-3 pb-1">
      <div className="text-[11px] uppercase tracking-wider text-slate-400">{focal.label}</div>
      <div className={`font-mono text-[30px] font-bold leading-none mt-1 ${focalCl}`} style={{ fontVariantNumeric: 'tabular-nums' }} title={focal.tip}>
        {focal.value}
      </div>
      {focalSub && <div className="text-[12px] text-slate-400 mt-1.5">{focalSub}</div>}
    </div>
    <div className="grid grid-cols-3 gap-3 px-4 py-2.5 border-t border-white/[0.05]">
      {secondaries.map(s => <Stat key={s.label} {...s} />)}
    </div>
    <div className="border-t border-white/[0.05] pt-1.5">
      <EquityCurve data={curve} color="#94a3b8" height={170} emptyLabel={curveEmpty} />
      <div className="px-4 pb-2 text-[11px] text-slate-500">{footnote}</div>
    </div>
  </Panel>
);
