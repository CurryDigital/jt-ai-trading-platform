// Command center — Market Context (dock Context tab): index strip + regime
// strip. Environment-agnostic market data.

import React, { useState } from 'react';
import { api, usePoll, fmtPct, pnlCl } from '../../utils';
import { fmtConf } from './format';
import { RISK_CELL, REGIME_MEANING } from './meta';

const StripSpark = ({ values }) => {
  if (!values || values.length < 2) return null;
  const clean = values.filter(v => v != null);
  if (clean.length < 2) return null;
  const min = Math.min(...clean), max = Math.max(...clean), range = (max - min) || 1;
  const w = 44, h = 14;
  const line = clean.map((v, i) => `${((i / (clean.length - 1)) * w).toFixed(1)},${(h - 1 - ((v - min) / range) * (h - 2)).toFixed(1)}`).join(' ');
  return (
    <svg viewBox={`0 0 ${w} ${h}`} className="block opacity-70" style={{ width: w, height: h }}>
      <polyline points={line} fill="none" stroke="rgba(148,163,184,0.8)" strokeWidth="1" vectorEffect="non-scaling-stroke" />
    </svg>
  );
};

const RegimeRegion = ({ region, fc, chg }) => {
  const days = fc?.days || [];
  const regime = chg?.regime ?? null;
  const allSame = days.length > 1 && days.every(d => d.risk_on === days[0].risk_on);
  let changeLine = null;
  if (chg) {
    if (!chg.history) {
      changeLine = 'no daily history — latest snapshot only';
    } else if (chg.prev_regime == null) {
      changeLine = `${regime} for ${chg.days_in_regime ?? '—'}+ days`;
    } else if (chg.days_in_regime === 1) {
      changeLine = `changed today: ${chg.prev_regime} → ${regime}`;
    } else {
      changeLine = `${chg.prev_regime} → ${regime} on ${chg.changed_on} · ${chg.days_in_regime}d in regime`;
    }
  }
  return (
    <div className="px-4 py-2.5">
      <div className="flex items-baseline gap-2.5 flex-wrap">
        <span className="font-mono text-[11px] font-black text-white flex-none">{region}</span>
        <span className="text-[13px] font-bold text-slate-100" title={`${chg?.source || ''}${regime ? `\n${REGIME_MEANING[regime] || ''}` : ''}`}>
          {regime ?? '—'}
        </span>
        <span className="font-mono text-[11px] text-slate-400"
          title={region === 'US' ? 'HMM posterior probability of the current regime' : 'No regime posterior for HK — the HMM is US-scope (SPY/VIX features)'}>
          P {fmtConf(chg?.confidence)}
        </span>
        <span className="text-[11px] font-mono text-slate-400 truncate" title={chg?.source || ''}>{changeLine ?? '—'}</span>
      </div>
      {days.length > 0 && (
        <div className="grid grid-cols-7 gap-1 mt-2">
          {days.map((d, i) => (
            <div key={d.date || i}
              className={`rounded px-1 py-1 text-center ${RISK_CELL(d.risk_on)}`}
              title={`${d.date ?? ''} · ${d.risk_on != null ? `${d.risk_on.toFixed(1)}%` : '—'} risk-on — 7-day momentum nowcast${allSame ? ' · flat carry-forward nowcast' : ''}`}>
              <div className="text-[9px] font-mono opacity-80">
                {d.date ? new Date(d.date + 'T00:00:00').toLocaleDateString('en-US', { weekday: 'narrow' }) : '·'}
              </div>
              <div className="text-[10px] font-mono font-bold">
                {d.risk_on != null ? `${d.risk_on.toFixed(0)}%` : '—'}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export const MarketContext = ({ fc, chg }) => {
  const [ov, setOv] = useState(null);
  usePoll(async () => {
    const res = await api.get('/api/markets/overview?regions=US,HK');
    if (res) setOv(res);
  }, 30000, 800);

  const rawIdx = ov?.indices?.data || ov?.indices;
  const indices = Array.isArray(rawIdx) ? rawIdx : [];
  const us = indices.filter(i => i.region === 'US').slice(0, 3);
  const hk = indices.filter(i => i.region === 'HK').slice(0, 2);
  const sentiment = ov?.sentiment || {};
  const usS = sentiment?.us || sentiment;
  const hkS = sentiment?.hk;

  return (
    <div>
      <div className="flex items-center gap-4 px-4 py-2.5 overflow-x-auto text-[12px] text-slate-400 border-b border-white/[0.05]">
        {[...us, ...hk].map(i => (
          <span key={i.sym} className="flex items-center gap-1.5 flex-none" title={i.name}>
            <span className="font-bold text-slate-300">{i.sym}</span>
            <span className="font-mono text-slate-300">{i.last != null ? i.last.toLocaleString(undefined, { maximumFractionDigits: 1 }) : '—'}</span>
            <span className={`font-mono ${pnlCl(i.change_pct ?? i.change_1d)}`}>{fmtPct(i.change_pct ?? i.change_1d)}</span>
            <StripSpark values={i.spark} />
          </span>
        ))}
        <span className="w-px self-stretch bg-white/[0.07] flex-none" />
        <span className="flex items-center gap-1.5 flex-none" title="CNN Fear & Greed (US)">
          <span>US F&amp;G</span><span className="font-mono text-slate-300">{usS?.fear_greed ?? '—'}</span>
        </span>
        <span className="flex items-center gap-1.5 flex-none" title="Fear & Greed (HK)">
          <span>HK F&amp;G</span><span className="font-mono text-slate-300">{hkS?.fear_greed ?? '—'}</span>
        </span>
        <span className="flex items-center gap-1.5 flex-none" title="CBOE VIX (US)">
          <span>VIX</span><span className="font-mono text-slate-300">{usS?.vix ?? '—'}</span>
        </span>
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-2 divide-y sm:divide-y-0 sm:divide-x divide-white/[0.05]">
        <RegimeRegion region="US" fc={fc?.US} chg={chg?.US} />
        <RegimeRegion region="HK" fc={fc?.HK} chg={chg?.HK} />
      </div>
      <div className="px-4 py-1.5 text-[11px] text-slate-500 border-t border-white/[0.05]"
        title="Market context is shared across environments. Regime probability uses US SPY/VIX features; the 7-day strip uses a momentum nowcast. Legend: ≥60% risk-on = emerald · ≤40% = rose · else neutral.">
        environment-agnostic · HMM daily + 7d nowcast
      </div>
    </div>
  );
};
