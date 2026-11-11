// Command center — ROW 0 status header: environment selector, HALT,
// session/feed, data freshness, market clocks. One compact bar.

import React, { useState, useEffect } from 'react';
import { marketClock, marketStatus, fmtAge } from '../../utils';
import { tsTip } from './format';
import { ENVS, ENV_META } from './meta';

export const EnvToggle = ({ env, onChange }) => (
  <span className="flex items-center rounded-md overflow-hidden border border-white/[0.10] flex-none" role="tablist" aria-label="Environment">
    {ENVS.map(e => (
      <button key={e} role="tab" aria-selected={env === e} onClick={() => onChange(e)} title={ENV_META[e].tip}
        className={`px-3.5 py-1.5 text-[13px] font-bold font-mono transition-colors ${env === e ? 'bg-white/[0.10] text-white' : 'text-slate-500 hover:text-slate-300'}`}>
        {ENV_META[e].badge}
      </button>
    ))}
  </span>
);

export const StatusItem = ({ label, children, tip }) => (
  <span className="flex items-center gap-2 flex-none" title={tip}>
    <span className="text-[11px] uppercase tracking-wider text-slate-400">{label}</span>
    {children}
  </span>
);

export const StatusDivider = () => <span className="w-px h-5 bg-white/[0.08] flex-none" />;

// Per-environment session status. `sess` is env-tagged so a stale payload
// from a previous environment is never shown.
export const SessionItem = ({ env, sess }) => {
  if (env === 'sim') {
    return <StatusItem label="Session" tip="SIM book — virtual money, synthetic fills; no broker session exists"><span className="font-mono text-[12px] text-slate-400">n/a · virtual</span></StatusItem>;
  }
  if (env === 'paper') {
    const s = sess?.env === 'paper' ? sess.res : null;
    const run = s?.last_run_type
      ? `${s.last_run_type} ${s.last_run_status || ''} ${s.last_run_date || ''}`.trim()
      : null;
    const bad = s?.last_run_status && s.last_run_status !== 'ok';
    return (
      <StatusItem label="Last run" tip="Latest paper pipeline run — /api/agents/paper/system-status">
        <span className={`font-mono text-[12px] ${bad ? 'text-rose-300' : 'text-slate-300'}`}>{s == null ? '—' : (run || '—')}</span>
      </StatusItem>
    );
  }
  if (env === 'uat') {
    const s = sess?.env === 'uat' ? sess.res : null;
    const connected = s?.is_connected === true;
    return (
      <StatusItem label="Session" tip={s ? `${s.message || ''} · ${s.host || ''}:${s.port || ''} client ${s.client_id ?? '—'}` : 'UAT session status unavailable'}>
        <span className={`w-2 h-2 rounded-full ${s == null ? 'bg-slate-600' : connected ? 'bg-emerald-400' : 'bg-rose-400'}`} />
        <span className="font-mono text-[12px] text-slate-300">{s == null ? '—' : connected ? 'connected' : 'down'}</span>
      </StatusItem>
    );
  }
  const g = sess?.env === 'live' ? sess.res : null;
  const ok = g?.connected === true;
  const hb = g?.last_heartbeat || g?.sessions?.primary?.last_heartbeat || null;
  return (
    <StatusItem label="Gateway" tip={g ? `IBKR live gateway ${ok ? 'connected' : 'DISCONNECTED'}${hb ? ` · heartbeat ${tsTip(hb)}` : ''}` : 'Live gateway status unavailable'}>
      <span className={`w-2 h-2 rounded-full ${g == null ? 'bg-slate-600' : ok ? 'bg-emerald-400' : 'bg-rose-400'}`} />
      <span className="font-mono text-[12px] text-slate-300">{g == null ? '—' : ok ? (hb ? fmtAge(hb) : 'connected') : 'down'}</span>
    </StatusItem>
  );
};

export const Clock = ({ label, t, open }) => (
  <span className="flex items-center gap-1.5" title={open ? 'session open' : 'session closed'}>
    <span className={`w-1.5 h-1.5 rounded-full ${open ? 'bg-emerald-400' : 'bg-slate-600'}`} />
    <span className="text-slate-400">{label}</span>
    <span className="font-mono text-slate-300">{t}</span>
  </span>
);

export const Clocks = () => {
  const [, setTick] = useState(0);
  useEffect(() => {
    const id = setInterval(() => setTick(t => t + 1), 1000);
    return () => clearInterval(id);
  }, []);
  const c = marketClock();
  const s = marketStatus();
  return (
    <span className="flex items-center gap-3 text-[11px] flex-none">
      <Clock label="HKT" t={c.hkt} open={s.hk} />
      <Clock label="LON" t={c.lon} open={s.lon} />
      <Clock label="NYC" t={c.nyc} open={s.nyc} />
    </span>
  );
};

export const StatusBar = ({ env, onEnv, limits, sess, dataAsOf }) => {
  const halted = !!limits?.global_halt;
  return (
    <div className="qr-surface px-4 py-2.5">
      <div className="flex items-center gap-x-5 gap-y-2 flex-wrap">
        <span className="flex items-center gap-3.5 flex-none">
          <h1 className="text-[15px] font-bold text-white tracking-tight">Command</h1>
          <EnvToggle env={env} onChange={onEnv} />
        </span>
        <StatusDivider />
        <StatusItem label="HALT" tip={halted ? 'Global halt is ACTIVE — gold.risk_limits.global_halt (applies to every environment)' : 'No global halt — gold.risk_limits.global_halt = false'}>
          <span className={`font-mono text-[12px] font-bold ${halted ? 'text-rose-300' : 'text-slate-300'}`}>
            {limits == null ? '—' : halted ? 'HALTED' : 'off'}
          </span>
        </StatusItem>
        <SessionItem env={env} sess={sess} />
        <StatusItem label="Data" tip={dataAsOf?.ts ? `Positions payload as of ${tsTip(dataAsOf.ts)}` : 'Positions payload not loaded yet'}>
          <span className={`font-mono text-[12px] ${dataAsOf?.stale ? 'text-rose-300 font-bold' : 'text-slate-300'}`}>{dataAsOf?.ts ? fmtAge(dataAsOf.ts) : '—'}</span>
        </StatusItem>
        <span className="flex-1" />
        <Clocks />
      </div>
    </div>
  );
};
