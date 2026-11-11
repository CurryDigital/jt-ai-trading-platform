// Command center — Signals / Opportunities (SIM/PAPER only, dock Signals
// tab).

import React, { useMemo } from 'react';
import { fmtK, fmtPct } from '../../utils';
import { NoData, LinkBtn } from './shared';
import { fmtDate, tsTip } from './format';
import { ENV_META, MARKET_LABEL, SCORE_TIP } from './meta';

export const Opportunities = ({ env, picks, positions, orders, navigateToTab }) => {
  const held = useMemo(() => new Set((positions || []).map(p => p.symbol)), [positions]);
  const pending = useMemo(() => new Set((orders || []).map(o => o.ticker)), [orders]);
  if (env === 'uat' || env === 'live') {
    return (
      <NoData>
        No signal attribution for the {ENV_META[env].badge} book — the signal universe (consumption.signal_setups) is not mapped to this environment. SIM and PAPER show their signal-driven candidates.
      </NoData>
    );
  }
  return (
    <div>
      <div className="flex items-center justify-end gap-3 px-4 pt-2">
        <span className="text-[11px] text-slate-500" title={SCORE_TIP}>best per class · heuristic score ⓘ</span>
        <LinkBtn onClick={() => navigateToTab('research')}>Signals →</LinkBtn>
      </div>
      <div className="divide-y divide-white/[0.05]">
        {picks.map((p, i) => {
          const isHeld = held.has(p.ticker);
          const hasPending = pending.has(p.ticker);
          return (
            <div key={`${p.market}-${p.ticker}`} className="flex items-center gap-3 px-4 py-2"
              title={`${p.reason || ''}${p.signalDate ? ` · signal ${tsTip(p.signalDate)}` : ''}${p.price != null ? ` · px ${fmtK(p.price)}` : ''}${p.changePct != null ? ` · 1d ${fmtPct(p.changePct)}` : ''}`}>
              <span className="font-mono text-[11px] text-slate-500 w-5 flex-none">#{i + 1}</span>
              <div className="flex-none w-[110px] min-w-0">
                <div className="font-mono text-[13px] font-black text-white leading-tight truncate">{p.ticker}</div>
                <div className="text-[11px] text-slate-400 truncate">{p.name || MARKET_LABEL[p.market] || p.market}</div>
              </div>
              <div className="flex-none w-[72px]">
                <div className="flex items-baseline gap-1" title={SCORE_TIP}>
                  <span className="font-mono text-[13px] font-bold text-slate-100">{p.potential != null ? p.potential.toFixed(0) : '—'}</span>
                  <span className="text-[10px] text-slate-500">/100</span>
                </div>
                <div className="h-0.5 mt-1 rounded bg-white/[0.06] overflow-hidden">
                  <div className="h-full bg-slate-300" style={{ width: `${Math.max(0, Math.min(100, p.potential ?? 0))}%` }} />
                </div>
              </div>
              <div className="flex-1 min-w-0">
                <div className="text-[12px] font-bold text-slate-200 truncate">{p.strategyName || '—'}</div>
                <div className="text-[11px] text-slate-400 truncate">{p.direction || 'BUY'}{p.signalDate ? ` · ${fmtDate(p.signalDate)}` : ''}</div>
              </div>
              <span className="flex-none flex items-center gap-1">
                {isHeld && <span className="qr-chip qr-chip-slate" title="Already held in this environment's book">held</span>}
                {hasPending && <span className="qr-chip qr-chip-slate" title="A working order for this ticker is in this environment's order book">pending</span>}
              </span>
            </div>
          );
        })}
        {picks.length === 0 && (
          <NoData>No active BUY candidates across asset classes</NoData>
        )}
      </div>
    </div>
  );
};
