// Command center — ROW 2B UNREALIZED P&L DRIVERS. Ranked horizontal bars
// over OPEN positions — mark-to-market contribution, never labeled daily
// attribution. Mixed-currency books render per-currency segments and are
// never netted.

import React, { useMemo } from 'react';
import { fmtK, fmtKCcy, pnlCl } from '../../utils';
import { Panel, EnvChip, NoData, HBar } from './shared';
import { sK, sCcy } from './format';
import { driverSegments, rankDrivers } from './aggregate';

const DriverRow = ({ d, maxAbs, defCcy }) => (
  <div className="flex items-center gap-2.5 py-1" title={`${d.symbol}${d.strategy ? ` · ${d.strategy}` : ''} · MV ${d.mv != null ? fmtKCcy(d.mv, d.ccy || defCcy) : '—'} · unrealized ${sCcy(d.unreal, d.ccy || defCcy)}`}>
    <span className="w-[150px] flex-none min-w-0">
      <span className="block font-mono text-[12px] font-bold text-white truncate">{d.symbol}</span>
      <span className="block text-[11px] text-slate-400 truncate">{d.strategy || '—'}</span>
    </span>
    <span className="flex-none font-mono text-[11px] text-slate-400 w-[52px] text-right" title="Market value (exposure)">{d.mv != null ? fmtK(d.mv) : '—'}</span>
    <span className="flex-1"><HBar pct={Math.abs(d.unreal) / maxAbs * 100} /></span>
    <span className={`flex-none font-mono text-[12px] font-bold w-[64px] text-right ${pnlCl(d.unreal)}`}>{sK(d.unreal)}</span>
  </div>
);

export const DriversPanel = ({ env, rows, defCcy, noDataText }) => {
  const content = useMemo(() => driverSegments(rows, defCcy), [rows, defCcy]);

  const renderSeg = (seg) => {
    const { pos, neg, maxAbs } = rankDrivers(seg.rows);
    return (
      <div key={seg.ccy}>
        {seg.label && <div className="text-[11px] font-mono text-slate-400 uppercase tracking-wider mb-1">{seg.label}</div>}
        {pos.length > 0 && (
          <div className="mb-2">
            <div className="text-[11px] uppercase tracking-wider text-slate-400 mb-0.5">Contributors</div>
            {pos.map(d => <DriverRow key={`p-${d.key}`} d={d} maxAbs={maxAbs} defCcy={defCcy} />)}
          </div>
        )}
        {neg.length > 0 && (
          <div>
            <div className="text-[11px] uppercase tracking-wider text-slate-400 mb-0.5">Detractors</div>
            {neg.map(d => <DriverRow key={`n-${d.key}`} d={d} maxAbs={maxAbs} defCcy={defCcy} />)}
          </div>
        )}
        {pos.length === 0 && neg.length === 0 && <NoData>All open marks are flat.</NoData>}
      </div>
    );
  };

  return (
    <Panel title={<>Unrealized P&L Drivers <EnvChip env={env} /></>} action={
      <span className="text-[11px] text-slate-500" title="Ranked by unrealized (mark-to-market) P&L over the open positions below. This is NOT daily attribution — no daily per-instrument P&L series is served.">open positions · not daily attribution ⓘ</span>
    }>
      <div className="px-4 py-3">
        {noDataText ? <span className="text-[13px] text-slate-500">{noDataText}</span>
          : content.loading ? <span className="text-[13px] text-slate-500">Loading…</span>
          : content.empty ? <span className="text-[13px] text-slate-500">No marked open positions — nothing to rank.</span>
          : content.mixed ? (
            <div className="space-y-4">
              <div className="text-[12px] text-slate-400">Mixed-currency book — segments are reported separately and never netted.</div>
              {content.mixed.map(seg => renderSeg({ ...seg, label: `${seg.ccy} segment` }))}
            </div>
          ) : renderSeg(content.single)}
      </div>
    </Panel>
  );
};
