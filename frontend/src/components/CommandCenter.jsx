import React, { useMemo, useState, useEffect, useRef } from 'react';
import { api, usePoll, fmtK, fmtKCcy, fmtPct, fmtAge, pnlCl, marketClock, marketStatus } from '../utils';
import { FR, FR_NAME, PANEL_SOURCES, panelFreshness, useFreshness, fmtAgeSec } from '../freshness';

// Command home — PAPER trading command center (redesign 2026-11-03).
// Information hierarchy first: one header, one KPI row, then an operational
// grid. Layout top-to-bottom:
//   1) Command header — title, PAPER environment chip, HALT / feed / data
//      freshness status, slim market ticker (reduced prominence)
//   2) Environment status strip — one compact row SIM · PAPER · UAT · LIVE
//      (replaces the four oversized mode cards; PAPER carries no repeated
//      figures — it is the book detailed below)
//   3) Primary KPI row (shown ONCE): today P&L · cumulative realized P&L ·
//      unrealized P&L + exposure · open positions · working orders · risk
//   4) Operational grid — LEFT ~65%: compact cumulative realized chart
//      (≤240px) + Open Positions table. RIGHT ~35%: Action Required +
//      Top Opportunities.
//   5) Working Orders + Recent Fills (compact, single-line empty states)
//   6) Market Context — compact regime forecast
// The Action Center lives in Settings ▸ Alerts; this page surfaces its
// critical/warning items under Action Required.
//
// Restrained palette: colour carries meaning only.
//   rose  = critical severity   emerald/rose text = signed P&L (via pnlCl)
//   blue  = interactive links   everything else = neutral slate/white

// Cumulative P&L chart. Width tracks the container via ResizeObserver so the
// chart truly spans its panel (a fixed viewBox + preserveAspectRatio would
// letterbox); height is fixed by prop — kept ≤ 240px so it never dominates.
function EquityCurve({ data, color, height = 240, emptyLabel = 'No equity history yet' }) {
  const ref = useRef(null);
  const [width, setWidth] = useState(600);
  useEffect(() => {
    if (!ref.current) return undefined;
    const ro = new ResizeObserver((entries) => {
      setWidth(Math.max(320, Math.round(entries[0].contentRect.width)));
    });
    ro.observe(ref.current);
    return () => ro.disconnect();
  }, []);

  if (!data || data.length < 2) {
    return <div className="flex items-center justify-center text-[11px] text-slate-600" style={{ height: 96 }}>{emptyLabel}</div>;
  }
  const margin = { left: 46, right: 10, top: 8, bottom: 22 };
  const values = data.map(d => d.equity);
  const min = Math.min(...values), max = Math.max(...values), range = (max - min) || 1;
  const w = width, h = height;
  const plotW = w - margin.left - margin.right;
  const plotH = h - margin.top - margin.bottom;
  const x = (i) => margin.left + (i / (values.length - 1)) * plotW;
  const y = (v) => margin.top + plotH - ((v - min) / range) * plotH;
  const line = values.map((v, i) => `${x(i)},${y(v)}`).join(' ');
  const area = `${margin.left},${margin.top + plotH} ${line} ${margin.left + plotW},${margin.top + plotH}`;
  const id = 'jt-eq-grad';
  const yTicks = [min, (min + max) / 2, max];
  const monthTicks = data.map((d, i) => ({ i, label: d.d, date: new Date(d.d + 'T00:00:00') })).filter((d, i, arr) => {
    if (i === 0) return true;
    const prev = arr[i - 1].date;
    return d.date.getMonth() !== prev.getMonth() || d.date.getFullYear() !== prev.getFullYear();
  });
  return (
    <div ref={ref}>
      <svg viewBox={`0 0 ${w} ${h}`} className="w-full block" style={{ height: h }}>
        <defs>
          <linearGradient id={id} x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={color} stopOpacity="0.28" />
            <stop offset="100%" stopColor={color} stopOpacity="0" />
          </linearGradient>
        </defs>
        {[0, 0.5, 1].map(f => {
          const gy = margin.top + plotH * f;
          return <line key={f} x1={margin.left} y1={gy} x2={margin.left + plotW} y2={gy} stroke="rgba(255,255,255,0.08)" strokeWidth="1" vectorEffect="non-scaling-stroke" />;
        })}
        <polygon points={area} fill={`url(#${id})`} />
        <polyline points={line} fill="none" stroke={color} strokeWidth="2" strokeLinejoin="round" strokeLinecap="round" vectorEffect="non-scaling-stroke" />
        <line x1={margin.left} y1={margin.top} x2={margin.left} y2={margin.top + plotH} stroke="rgba(255,255,255,0.15)" strokeWidth="1" vectorEffect="non-scaling-stroke" />
        <line x1={margin.left} y1={margin.top + plotH} x2={margin.left + plotW} y2={margin.top + plotH} stroke="rgba(255,255,255,0.15)" strokeWidth="1" vectorEffect="non-scaling-stroke" />
        {yTicks.map((v, i) => (
          <text key={i} x={margin.left - 5} y={y(v) + 3} textAnchor="end" fill="rgba(148,163,184,0.8)" fontSize="9" fontFamily="ui-monospace, SFMono-Regular, Menlo, monospace">
            {fmtK(v)}
          </text>
        ))}
        {monthTicks.map((t, i) => (
          <text key={i} x={x(t.i)} y={h - 6} textAnchor="middle" fill="rgba(148,163,184,0.8)" fontSize="9" fontFamily="ui-monospace, SFMono-Regular, Menlo, monospace">
            {t.date.toLocaleDateString('en-US', { month: 'short' })}
          </text>
        ))}
      </svg>
    </div>
  );
}

// Freshness tag colors — palette rule: rose = bad states, teal = aging,
// everything else neutral slate. No amber/violet.
const FR_TAG_CL = {
  [FR.FRESH]: 'text-slate-600',
  [FR.LAGGING]: 'text-teal-300',
  [FR.UNKNOWN]: 'text-slate-600',
  [FR.STALE]: 'text-rose-400',
  [FR.DISCONNECTED]: 'text-rose-300',
};

// Per-panel as-of tag. Tooltip names the culprit source and its configured
// staleness budget so a stale panel explains itself.
const FreshTag = ({ fresh }) => {
  if (!fresh) return null;
  const { state, asOfSec, culprit } = fresh;
  const tip = culprit
    ? `${FR_NAME[state]} — source ${culprit.name}${culprit.budgetH != null ? ` (budget ${culprit.budgetH}h)` : ''}`
    : FR_NAME[state];
  const text = state === FR.UNKNOWN ? 'upd ?'
    : state === FR.DISCONNECTED ? 'no feed'
    : `upd ${fmtAgeSec(asOfSec)}`;
  return <span className={`font-mono text-[9px] normal-case tracking-normal ${FR_TAG_CL[state]}`} title={tip}>{text}</span>;
};

// Panel: when DISCONNECTED the numbers are masked ('--') and the muted
// footer keeps the last-known value visible; when STALE the body desaturates
// and gets a diagonal hatch so no figure reads as live.
const Panel = ({ title, action, children, className = '', fresh }) => {
  const stale = fresh?.state === FR.STALE;
  const disc = fresh?.state === FR.DISCONNECTED;
  return (
    <div className={`qr-surface overflow-hidden ${className}`}>
      <div className="flex items-center justify-between px-3 py-1.5 border-b border-white/[0.05]">
        <span className="qr-label flex items-center gap-2">{title}{fresh && <FreshTag fresh={fresh} />}</span>
        {action}
      </div>
      {disc ? (
        <div className="px-3 py-4">
          <div className="font-mono text-lg text-slate-600">--</div>
          <div className="text-[9px] text-slate-600 mt-1">
            feed disconnected · last known {fresh.lastKnown ?? '—'}{fresh.culprit ? ` · ${fresh.culprit.name}` : ''}
          </div>
        </div>
      ) : (
        <div className={`relative ${stale ? 'qr-fresh-desat' : ''}`}>
          {children}
          {stale && <div className="qr-hatch absolute inset-0 pointer-events-none" />}
        </div>
      )}
    </div>
  );
};

const LinkBtn = ({ children, onClick }) => (
  <button onClick={onClick} className="text-[10px] font-semibold text-blue-400 hover:text-blue-300">{children}</button>
);

// ---------------------------------------------------------------------------
// Header — compact command header: title · PAPER environment · HALT / feed /
// data-freshness status. One line on desktop, wraps on mobile.
// ---------------------------------------------------------------------------
const StatusItem = ({ label, children, tip }) => (
  <span className="flex items-center gap-1.5 flex-none" title={tip}>
    <span className="text-[9px] uppercase tracking-wide text-slate-500">{label}</span>
    {children}
  </span>
);

const CommandHeader = ({ limits, gateway, sysStatus, dataFresh }) => {
  const halted = !!limits?.global_halt;
  const feedOk = gateway?.connected === true;
  const hb = gateway?.last_heartbeat || gateway?.sessions?.primary?.last_heartbeat || null;
  const run = sysStatus?.last_run_type
    ? `${sysStatus.last_run_type} ${sysStatus.last_run_status || ''} ${sysStatus.last_run_date || ''}`.trim()
    : null;
  const runBad = sysStatus?.last_run_status && sysStatus.last_run_status !== 'ok';
  return (
    <div className="qr-surface px-3 py-2">
      <div className="flex items-center gap-x-4 gap-y-1 flex-wrap">
        <span className="flex items-baseline gap-2 flex-none">
          <h1 className="text-sm font-bold text-white">Command</h1>
          <span className="qr-chip qr-chip-slate" title={`Global execution mode: ${gateway?.global_mode || 'PAPER_TRADING'} (/api/execution/gateway)`}>PAPER</span>
        </span>
        <StatusItem label="HALT" tip={halted ? 'Global halt is ACTIVE — gold.risk_limits.global_halt' : 'No global halt — gold.risk_limits.global_halt = false'}>
          <span className={`font-mono text-[10px] font-bold ${halted ? 'text-rose-300' : 'text-slate-300'}`}>
            {limits == null ? '—' : halted ? 'HALTED' : 'off'}
          </span>
        </StatusItem>
        <StatusItem label="Feed" tip={hb ? `IBKR gateway ${feedOk ? 'connected' : 'DISCONNECTED'} · last heartbeat ${hb}` : 'IBKR gateway status unavailable'}>
          <span className={`w-1.5 h-1.5 rounded-full ${gateway == null ? 'bg-slate-600' : feedOk ? 'bg-emerald-400' : 'bg-rose-400'}`} />
          <span className="font-mono text-[10px] text-slate-300">{gateway == null ? '—' : feedOk ? (hb ? fmtAge(hb) : 'connected') : 'down'}</span>
        </StatusItem>
        <StatusItem label="Last run" tip="Latest paper pipeline run — /api/agents/paper/system-status">
          <span className={`font-mono text-[10px] ${runBad ? 'text-rose-300' : 'text-slate-300'}`}>{run || '—'}</span>
        </StatusItem>
        <StatusItem label="Data" tip="Worst freshness state across the sources feeding this page">
          <FreshTag fresh={dataFresh} />
        </StatusItem>
      </div>
    </div>
  );
};

// Slim market ticker — kept, but visually subordinate: no panel chrome,
// small muted type, horizontally scrollable on narrow screens.
const StripSpark = ({ values }) => {
  if (!values || values.length < 2) return null;
  const min = Math.min(...values), max = Math.max(...values), range = (max - min) || 1;
  const w = 40, h = 12;
  const line = values.map((v, i) => `${((i / (values.length - 1)) * w).toFixed(1)},${(h - 1 - ((v - min) / range) * (h - 2)).toFixed(1)}`).join(' ');
  return (
    <svg viewBox={`0 0 ${w} ${h}`} className="block opacity-70" style={{ width: w, height: h }}>
      <polyline points={line} fill="none" stroke="rgba(148,163,184,0.8)" strokeWidth="1" vectorEffect="non-scaling-stroke" />
    </svg>
  );
};

const Clocks = () => {
  const [, setTick] = useState(0);
  useEffect(() => {
    const id = setInterval(() => setTick(t => t + 1), 1000);
    return () => clearInterval(id);
  }, []);
  const c = marketClock();
  const s = marketStatus();
  const Clock = ({ label, t, open }) => (
    <span className="flex items-center gap-1" title={open ? 'session open' : 'session closed'}>
      <span className={`w-1 h-1 rounded-full ${open ? 'bg-emerald-400' : 'bg-slate-600'}`} />
      <span className="text-slate-500">{label}</span>
      <span className="font-mono text-slate-300">{t}</span>
    </span>
  );
  return (
    <span className="flex items-center gap-2.5 text-[9px] flex-none">
      <Clock label="HKT" t={c.hkt} open={s.hk} />
      <Clock label="LON" t={c.lon} open={s.lon} />
      <Clock label="NYC" t={c.nyc} open={s.nyc} />
    </span>
  );
};

function MarketTicker({ fresh }) {
  const [ov, setOv] = useState(null);

  const load = async () => {
    const res = await api.get('/api/markets/overview?regions=US,HK');
    if (res) setOv(res);
  };
  useEffect(() => { load(); }, []);
  usePoll(load, 30000);

  const rawIdx = ov?.indices?.data || ov?.indices;
  const indices = Array.isArray(rawIdx) ? rawIdx : [];
  const us = indices.filter(i => i.region === 'US').slice(0, 3);
  const hk = indices.filter(i => i.region === 'HK').slice(0, 2);
  const sentiment = ov?.sentiment || {};
  const usS = sentiment?.us || sentiment;
  const hkS = sentiment?.hk;

  return (
    <div className="flex items-center gap-3 px-1 overflow-x-auto text-[10px] text-slate-500">
      <Clocks />
      <span className="w-px self-stretch bg-white/[0.07] flex-none" />
      {[...us, ...hk].map(i => (
        <span key={i.sym} className="flex items-center gap-1.5 flex-none" title={i.name}>
          <span className="font-bold text-slate-300">{i.sym}</span>
          <span className="font-mono text-slate-300">{i.last != null ? i.last.toLocaleString(undefined, { maximumFractionDigits: 1 }) : '—'}</span>
          <span className={`font-mono ${pnlCl(i.change_pct ?? i.change_1d)}`}>{fmtPct(i.change_pct ?? i.change_1d)}</span>
          <StripSpark values={i.spark} />
        </span>
      ))}
      <span className="w-px self-stretch bg-white/[0.07] flex-none" />
      <span className="flex items-center gap-1 flex-none" title="CNN Fear & Greed (US)">
        <span>US F&amp;G</span><span className="font-mono text-slate-300">{usS?.fear_greed ?? '—'}</span>
      </span>
      <span className="flex items-center gap-1 flex-none" title="Fear & Greed (HK)">
        <span>HK F&amp;G</span><span className="font-mono text-slate-300">{hkS?.fear_greed ?? '—'}</span>
      </span>
      <span className="flex items-center gap-1 flex-none" title="CBOE VIX (US)">
        <span>VIX</span><span className="font-mono text-slate-300">{usS?.vix ?? '—'}</span>
      </span>
      <FreshTag fresh={fresh} />
    </div>
  );
}

// ---------------------------------------------------------------------------
// Environment status strip — ONE compact row replacing the four big cards.
// PAPER is the active book (detailed below) so its cell carries no repeated
// figures — just the selection marker.
// ---------------------------------------------------------------------------
const EnvCell = ({ label, active, children, tip, onClick }) => (
  <button onClick={onClick} title={tip}
    className={`flex-1 min-w-0 px-3 py-1.5 text-left flex items-center gap-2 ${active ? 'bg-white/[0.05]' : 'hover:bg-white/[0.03]'}`}>
    <span className={`text-[9px] uppercase tracking-wide font-bold flex-none ${active ? 'text-white' : 'text-slate-500'}`}>{label}</span>
    <span className="min-w-0 truncate">{children}</span>
  </button>
);

const EnvStrip = ({ pnlMode, liveAcct, navigateToTab, fresh }) => {
  const m = pnlMode?.modes || {};
  const goExec = () => navigateToTab('execution');
  const pnlTxt = (v) => v != null ? `${v >= 0 ? '+' : ''}${fmtK(v)}` : '—';
  return (
    <div className="qr-surface overflow-hidden">
      <div className="flex items-stretch divide-x divide-white/[0.05] overflow-x-auto">
        <EnvCell label="SIM" onClick={goExec} tip="Simulation book — open in Execution ▸ Sim">
          <span className={`font-mono text-[10px] ${pnlCl(m.sim?.cum_pnl)}`}>{pnlTxt(m.sim?.cum_pnl)}</span>
          <span className="text-[9px] text-slate-500">{m.sim?.open_trades ?? 0} open</span>
        </EnvCell>
        <EnvCell label="PAPER" active onClick={goExec} tip="Active book — detailed below">
          <span className="text-[9px] text-slate-400">active book · detailed below</span>
          <FreshTag fresh={fresh} />
        </EnvCell>
        <EnvCell label="UAT" onClick={goExec} tip="IBKR paper rehearsal — fills-only ledger (round-trip P&L pending) · open Execution ▸ UAT">
          <span className="font-mono text-[10px] text-slate-300">{m.uat?.fills ?? 0} fills</span>
          <span className="text-[9px] text-slate-500">fills-only</span>
        </EnvCell>
        <EnvCell label="LIVE" onClick={goExec} tip="Live IBKR book — open Execution ▸ Live">
          <span className="font-mono text-[10px] text-slate-300">
            {liveAcct?.equity_native != null ? fmtKCcy(liveAcct.equity_native, liveAcct.native_currency) : '—'}
          </span>
          <span className={`font-mono text-[9px] ${pnlCl(liveAcct?.day_pnl)}`}>
            {liveAcct?.day_pnl != null ? `day ${pnlTxt(liveAcct.day_pnl)}` : ''}
          </span>
        </EnvCell>
      </div>
    </div>
  );
};

// ---------------------------------------------------------------------------
// Primary KPI row — shown ONCE. Compact tiles, label close to value.
// ---------------------------------------------------------------------------
const Kpi = ({ label, value, valueCl = 'text-white', sub, tip }) => (
  <div className="qr-surface px-2.5 py-2 flex flex-col justify-center min-w-0" title={tip}>
    <div className="qr-label truncate">{label}</div>
    <div className={`font-mono text-[15px] font-bold leading-tight mt-0.5 truncate ${valueCl}`}>{value}</div>
    {sub != null && <div className="text-[9px] text-slate-500 leading-tight mt-0.5 truncate">{sub}</div>}
  </div>
);

const KpiRow = ({ st, paperAcct, orderCount, risk, fresh }) => {
  const today = st?.today;
  const openPnl = paperAcct?.open_pnl;
  const expPct = paperAcct?.gross_exp_pct;
  const riskVal = risk.halted ? 'HALTED'
    : risk.critical > 0 ? `${risk.critical} critical`
    : risk.warning > 0 ? `${risk.warning} warning`
    : 'OK';
  const riskCl = risk.halted || risk.critical > 0 ? 'text-rose-300' : 'text-white';
  return (
    <div className={`grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-2 ${fresh?.state === FR.STALE ? 'qr-fresh-desat' : ''}`}>
      <Kpi label="Today · realized" tip="Realized P&L from today's exits (gold.paper_trades_synthetic, paper book)"
        value={today ? `${today.pnl >= 0 ? '+' : ''}${fmtK(today.pnl)}` : '—'}
        valueCl={today ? pnlCl(today.pnl) : 'text-slate-600'}
        sub={today ? `${today.trades} exit${today.trades === 1 ? '' : 's'} today` : 'no exits today'} />
      <Kpi label="Cum realized P&L" tip="All-time cumulative realized P&L, paper book"
        value={st?.cum_pnl != null ? `${st.cum_pnl >= 0 ? '+' : ''}${fmtK(st.cum_pnl)}` : '—'}
        valueCl={st?.cum_pnl != null ? pnlCl(st.cum_pnl) : 'text-slate-600'}
        sub={st ? `${st.closed_trades ?? 0} closed · WR ${st.win_rate ?? '—'}%` : null} />
      <Kpi label="Unrealized P&L" tip="Open P&L, paper book (consumption.account_summary) · exposure = gross % of equity"
        value={openPnl != null ? `${openPnl >= 0 ? '+' : ''}${fmtKCcy(openPnl, paperAcct?.currency || 'USD')}` : '—'}
        valueCl={openPnl != null ? pnlCl(openPnl) : 'text-slate-600'}
        sub={expPct != null ? `exposure ${expPct.toFixed(1)}% gross` : null} />
      <Kpi label="Open positions" tip="Actively monitored open positions, paper book"
        value={st?.open_trades ?? '—'} valueCl={st?.open_trades != null ? 'text-white' : 'text-slate-600'} />
      <Kpi label="Working orders" tip="Pending orders in the paper order book"
        value={orderCount ?? '—'} />
      <Kpi label="Risk status" tip="Global halt + critical/warning strategy risk triggers + monitoring gap"
        value={riskVal} valueCl={riskCl}
        sub={risk.gap > 0 ? `${risk.gap} unmonitored` : 'monitoring ok'} />
    </div>
  );
};

// ---------------------------------------------------------------------------
// Open Positions (paper book) — the operational table under the chart.
// ---------------------------------------------------------------------------
const ageDays = (openedAt) => {
  if (!openedAt) return null;
  const t = new Date(openedAt.length === 10 ? openedAt + 'T00:00:00Z' : openedAt);
  if (isNaN(t)) return null;
  return Math.max(0, Math.floor((Date.now() - t.getTime()) / 86400000));
};

const OpenPositions = ({ rows, stratNames, fresh, navigateToTab }) => (
  <Panel title="Open Positions" fresh={fresh} action={
    <span className="flex items-center gap-2">
      <span className="text-[9px] text-slate-600">{rows.length} open · mkt value = qty × last px (native ccy)</span>
      <LinkBtn onClick={() => navigateToTab('execution')}>Execution →</LinkBtn>
    </span>
  }>
    {rows.length > 0 ? (
      <div className="max-h-[300px] overflow-y-auto overflow-x-auto">
        <table className="w-full min-w-[640px]">
          <thead className="sticky top-0 bg-[#10141f]">
            <tr className="text-[8px] font-semibold text-slate-500 uppercase tracking-wide">
              <th className="text-left px-3 py-1">Symbol</th>
              <th className="text-left px-2 py-1">Strategy</th>
              <th className="text-right px-2 py-1">Qty</th>
              <th className="text-right px-2 py-1">Entry</th>
              <th className="text-right px-2 py-1">Current</th>
              <th className="text-right px-2 py-1">Unreal P&L</th>
              <th className="text-right px-2 py-1">Mkt value</th>
              <th className="text-right px-3 py-1">Age</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((p, i) => {
              const mv = (p.shares != null && p.current_price != null) ? p.shares * p.current_price : null;
              const age = ageDays(p.opened_at);
              return (
                <tr key={`${p.id || p.ticker}-${i}`} className="border-t border-white/[0.05] text-[11px]">
                  <td className="px-3 py-1.5 font-mono font-bold text-white whitespace-nowrap">{p.ticker}</td>
                  <td className="px-2 py-1.5 text-[10px] text-slate-400 max-w-[150px] truncate" title={stratNames[p.strategy_id] || p.strategy_id}>
                    {stratNames[p.strategy_id] || p.strategy_id}
                  </td>
                  <td className="px-2 py-1.5 text-right font-mono text-slate-200">{p.shares != null ? p.shares.toLocaleString() : '—'}</td>
                  <td className="px-2 py-1.5 text-right font-mono text-slate-300">{p.entry_price != null ? p.entry_price.toLocaleString(undefined, { maximumFractionDigits: 2 }) : '—'}</td>
                  <td className="px-2 py-1.5 text-right font-mono text-slate-300" title={p.price_as_of ? `price as of ${p.price_as_of}` : undefined}>
                    {p.current_price != null ? p.current_price.toLocaleString(undefined, { maximumFractionDigits: 2 }) : '—'}
                  </td>
                  <td className={`px-2 py-1.5 text-right font-mono font-bold whitespace-nowrap ${p.unrealised_pnl != null ? pnlCl(p.unrealised_pnl) : 'text-slate-600'}`}
                    title={p.unrealised_pnl_pct != null ? `${p.unrealised_pnl_pct >= 0 ? '+' : ''}${p.unrealised_pnl_pct.toFixed(2)}% on entry` : 'no mark'}>
                    {p.unrealised_pnl != null ? `${p.unrealised_pnl >= 0 ? '+' : ''}${fmtK(p.unrealised_pnl)}` : '—'}
                  </td>
                  <td className="px-2 py-1.5 text-right font-mono text-slate-300">{mv != null ? fmtK(mv) : '—'}</td>
                  <td className="px-3 py-1.5 text-right font-mono text-[10px] text-slate-500">{age != null ? `${age}d` : '—'}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    ) : (
      <div className="px-3 py-2 text-[11px] text-slate-600">No open positions in the paper book</div>
    )}
  </Panel>
);

// ---------------------------------------------------------------------------
// Action Required — HALT, risk breaches, stale feeds, gateway, monitoring
// gaps, platform attention items. One compact empty state when clear.
// ---------------------------------------------------------------------------
const SEV_DOT = { critical: 'bg-rose-400', warning: 'bg-slate-400', info: 'bg-slate-600' };

const ActionRequired = ({ items, fresh, navigateToTab }) => (
  <Panel title="Action Required" fresh={fresh} action={
    items.length > 0
      ? <span className="text-[9px] text-slate-500">{items.filter(i => i.sev === 'critical').length} critical · {items.filter(i => i.sev === 'warning').length} warning</span>
      : null
  }>
    {items.length === 0 ? (
      <div className="px-3 py-2 text-[11px] text-slate-500">No action required — halt clear, feeds fresh, no risk breaches</div>
    ) : (
      <div className="divide-y divide-white/[0.05] max-h-[260px] overflow-y-auto">
        {items.map((it, i) => (
          <button key={`${it.id}-${i}`} onClick={() => it.target ? navigateToTab(it.target) : undefined}
            className="w-full flex items-start gap-2 px-3 py-1.5 text-left hover:bg-white/[0.03]"
            title={it.tip || it.impact || it.title}>
            <span className={`w-1.5 h-1.5 rounded-full mt-1 flex-none ${SEV_DOT[it.sev] || SEV_DOT.info}`} />
            <span className="flex-1 min-w-0">
              <span className="block text-[11px] font-bold text-slate-100 truncate">{it.title}</span>
              {it.impact && <span className="block text-[9px] text-slate-500 truncate">{it.impact}</span>}
            </span>
            {it.age && <span className="flex-none font-mono text-[9px] text-slate-500 mt-0.5">{it.age}</span>}
          </button>
        ))}
      </div>
    )}
  </Panel>
);

// ---------------------------------------------------------------------------
// Top Opportunities (compact) — symbol · strategy · score · state · time.
// Score honesty: the displayed score is the signal engine's raw 'potential'
// field (consumption.signal_setups, 0–100), a heuristic ranking with no
// published formula — the tooltip says so instead of inventing a breakdown.
// ---------------------------------------------------------------------------
const MARKET_LABEL = { US: 'US Equity', HK: 'HK Equity', CRYPTO: 'Crypto', FX: 'FX', METAL: 'Metals' };

const SCORE_TIP = 'Engine conviction score (consumption.signal_setups.potential, 0–100). '
  + 'The signal pipeline publishes no formula or component breakdown for this field — '
  + 'treat it as a heuristic ranking, not a decomposable model output.';

const Opportunities = ({ picks, positions, orders, navigateToTab, fresh }) => {
  const held = useMemo(() => new Set((positions || []).map(p => p.ticker)), [positions]);
  const pending = useMemo(() => new Set((orders || []).map(o => o.ticker)), [orders]);
  return (
    <Panel title="Top Opportunities" fresh={fresh} action={
      <span className="flex items-center gap-2">
        <span className="text-[9px] text-slate-600" title={SCORE_TIP}>best per class · heuristic score ⓘ</span>
        <LinkBtn onClick={() => navigateToTab('research')}>Signals →</LinkBtn>
      </span>
    }>
      <div className="divide-y divide-white/[0.05]">
        {picks.map((p, i) => {
          const isHeld = held.has(p.ticker);
          const hasPending = pending.has(p.ticker);
          return (
            <div key={`${p.market}-${p.ticker}`} className="flex items-center gap-2 px-3 py-1.5"
              title={`${p.reason || ''}${p.signalDate ? ` · signal ${p.signalDate.slice(0, 10)} ${p.signalDate.slice(11, 16)}Z` : ''}${p.price != null ? ` · px ${fmtK(p.price)}` : ''}${p.changePct != null ? ` · 1d ${fmtPct(p.changePct)}` : ''}`}>
              <span className="font-mono text-[9px] text-slate-600 w-3 flex-none">#{i + 1}</span>
              <div className="flex-none w-[86px] min-w-0">
                <div className="font-mono text-[12px] font-black text-white leading-tight truncate">{p.ticker}</div>
                <div className="text-[8px] text-slate-500 truncate">{p.name || MARKET_LABEL[p.market] || p.market}</div>
              </div>
              <div className="flex-none w-[64px]">
                <div className="flex items-baseline gap-1" title={SCORE_TIP}>
                  <span className="font-mono text-[12px] font-bold text-slate-100">{p.potential != null ? p.potential.toFixed(0) : '—'}</span>
                  <span className="text-[8px] text-slate-500">/100</span>
                </div>
                <div className="h-0.5 mt-0.5 rounded bg-white/[0.06] overflow-hidden">
                  <div className="h-full bg-slate-300" style={{ width: `${Math.max(0, Math.min(100, p.potential ?? 0))}%` }} />
                </div>
              </div>
              <div className="flex-1 min-w-0">
                <div className="text-[10px] font-bold text-slate-200 truncate">{p.strategyName || '—'}</div>
                <div className="text-[8px] text-slate-500 truncate">{p.direction || 'BUY'}{p.signalDate ? ` · ${p.signalDate.slice(0, 10)}` : ''}</div>
              </div>
              <span className="flex-none flex items-center gap-1">
                {isHeld && <span className="qr-chip qr-chip-slate" title="Already held in the book">held</span>}
                {hasPending && <span className="qr-chip qr-chip-slate" title="A working order for this ticker is in the order book">pending</span>}
              </span>
            </div>
          );
        })}
        {picks.length === 0 && (
          <div className="px-3 py-2 text-[11px] text-slate-600">No active BUY candidates across asset classes</div>
        )}
      </div>
    </Panel>
  );
};

// ---------------------------------------------------------------------------
// Working Orders (paper book) — compact table, single-line empty state.
// ---------------------------------------------------------------------------
const WorkingOrders = ({ orders, fresh, navigateToTab }) => (
  <Panel title="Working Orders" fresh={fresh} action={
    <span className="flex items-center gap-2">
      <span className="text-[9px] text-slate-600" title="Working orders in the paper book. Est gain = limit vs latest daily close; blank for market orders.">
        {orders.length} working · paper book
      </span>
      <LinkBtn onClick={() => navigateToTab('execution')}>Orders →</LinkBtn>
    </span>
  }>
    {orders.length > 0 ? (
      <div className="max-h-[220px] overflow-y-auto overflow-x-auto">
        <table className="w-full min-w-[560px]">
          <thead className="sticky top-0 bg-[#10141f]">
            <tr className="text-[8px] font-semibold text-slate-500 uppercase tracking-wide">
              <th className="text-left px-3 py-1">Ticker</th>
              <th className="text-left px-2 py-1">Side</th>
              <th className="text-right px-2 py-1">Qty</th>
              <th className="text-right px-2 py-1">Limit</th>
              <th className="text-right px-2 py-1">Last</th>
              <th className="text-right px-2 py-1">Est Gain</th>
              <th className="text-left px-2 py-1">Strategy</th>
              <th className="text-right px-3 py-1">Age</th>
            </tr>
          </thead>
          <tbody>
            {orders.map((o, i) => (
              <tr key={`${o.source}-${o.ticker}-${i}`} className="border-t border-white/[0.05] text-[11px]">
                <td className="px-3 py-1 font-mono font-bold text-white">{o.ticker}</td>
                <td className={`px-2 py-1 font-mono font-bold ${o.side === 'BUY' ? 'text-emerald-400' : o.side === 'SELL' || o.side === 'CLOSE' ? 'text-rose-400' : 'text-slate-400'}`}>{o.side ?? '—'}</td>
                <td className="px-2 py-1 text-right font-mono text-slate-200">{o.qty != null ? o.qty.toLocaleString() : '—'}</td>
                <td className="px-2 py-1 text-right font-mono text-slate-300">{o.limit_price != null ? o.limit_price.toLocaleString() : 'MKT'}</td>
                <td className="px-2 py-1 text-right font-mono text-slate-300" title={o.last_price_as_of ? `daily close as of ${o.last_price_as_of}` : 'no daily close for this ticker'}>
                  {o.last_price != null ? o.last_price.toLocaleString(undefined, { maximumFractionDigits: 2 }) : '—'}
                </td>
                <td className={`px-2 py-1 text-right font-mono font-bold ${o.est_gain != null ? pnlCl(o.est_gain) : 'text-slate-600'}`}>
                  {o.est_gain != null ? `${o.est_gain >= 0 ? '+' : ''}${fmtK(o.est_gain)}` : '—'}
                </td>
                <td className="px-2 py-1 text-[10px] text-slate-400 max-w-[140px] truncate" title={o.strategy_name || o.venue}>
                  {o.strategy_name || o.venue}
                </td>
                <td className="px-3 py-1 text-right font-mono text-[10px] text-slate-500">{o.submitted_at ? fmtAge(o.submitted_at) : '—'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    ) : (
      <div className="px-3 py-2 text-[11px] text-slate-600">No working orders in the paper book</div>
    )}
  </Panel>
);

// ---------------------------------------------------------------------------
// Recent Fills (paper book) — closed trades, last 30 days
// (gold.v_paper_trade_history). Single-line empty state.
// ---------------------------------------------------------------------------
const RecentFills = ({ trades, fresh }) => (
  <Panel title="Recent Fills" fresh={fresh} action={
    <span className="text-[9px] text-slate-600" title="Closed paper trades, last 30 days (gold.v_paper_trade_history)">closed trades · 30d</span>
  }>
    {trades.length > 0 ? (
      <div className="max-h-[220px] overflow-y-auto overflow-x-auto">
        <table className="w-full min-w-[560px]">
          <thead className="sticky top-0 bg-[#10141f]">
            <tr className="text-[8px] font-semibold text-slate-500 uppercase tracking-wide">
              <th className="text-left px-3 py-1">Ticker</th>
              <th className="text-left px-2 py-1">Strategy</th>
              <th className="text-left px-2 py-1">Dir</th>
              <th className="text-right px-2 py-1">Qty</th>
              <th className="text-right px-2 py-1">Entry → Exit</th>
              <th className="text-right px-2 py-1">Realized P&L</th>
              <th className="text-right px-3 py-1">Closed</th>
            </tr>
          </thead>
          <tbody>
            {trades.map((t, i) => (
              <tr key={`${t.id || t.ticker}-${i}`} className="border-t border-white/[0.05] text-[11px]">
                <td className="px-3 py-1 font-mono font-bold text-white">{t.ticker}</td>
                <td className="px-2 py-1 text-[10px] text-slate-400 max-w-[140px] truncate" title={t.strategy_id}>{t.strategy_id}</td>
                <td className="px-2 py-1 font-mono text-slate-300 uppercase">{t.direction ?? '—'}</td>
                <td className="px-2 py-1 text-right font-mono text-slate-200">{t.shares != null ? t.shares.toLocaleString() : '—'}</td>
                <td className="px-2 py-1 text-right font-mono text-slate-300 whitespace-nowrap">
                  {t.entry_price != null ? t.entry_price.toLocaleString(undefined, { maximumFractionDigits: 2 }) : '—'}
                  {' → '}
                  {t.exit_price != null ? t.exit_price.toLocaleString(undefined, { maximumFractionDigits: 2 }) : '—'}
                </td>
                <td className={`px-2 py-1 text-right font-mono font-bold whitespace-nowrap ${t.pnl != null ? pnlCl(t.pnl) : 'text-slate-600'}`}
                  title={t.pnl_pct != null ? `${t.pnl_pct >= 0 ? '+' : ''}${t.pnl_pct.toFixed(2)}% · held ${t.hold_days ?? '—'}d` : undefined}>
                  {t.pnl != null ? `${t.pnl >= 0 ? '+' : ''}${fmtK(t.pnl)}` : '—'}
                </td>
                <td className="px-3 py-1 text-right font-mono text-[10px] text-slate-500">{t.closed_at ? fmtAge(t.closed_at) : '—'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    ) : (
      <div className="px-3 py-2 text-[11px] text-slate-600">No closed paper trades in the last 30 days</div>
    )}
  </Panel>
);

// ---------------------------------------------------------------------------
// Market Context — compact regime forecast near the bottom.
//   current regime label  — consumption.market_sentiment (canonical, US + HK)
//   probability           — HMM posterior, gold.regime_label (US scope only)
//   change vs yesterday   — /api/command/regime-change (US HMM daily history)
//   7-day strip           — consumption.macro_regime_7d, momentum_nowcast
// ---------------------------------------------------------------------------
const REGIME_MEANING = {
  TREND: 'Trending tape — momentum and trend-following books should keep working; fade entries get run over.',
  MEAN_REV: 'Mean-reverting tape — moves fade; breakout entries underperform.',
  CARRY: 'Carry / range tape — low-vol grind; income-style books favoured over breakouts.',
  EVENT: 'Event-driven stress — expect gaps and vol spikes; gross exposure earns less.',
  FLAT: 'No dominant regime — weak signal environment; neutral sizing.',
};

const RISK_CELL = (v) => v == null ? 'bg-white/[0.04] text-slate-600'
  : v >= 60 ? 'bg-emerald-500/15 text-emerald-300'
  : v <= 40 ? 'bg-rose-500/15 text-rose-300'
  : 'bg-white/[0.06] text-slate-300';

const fmtConf = (c) => c == null ? '—' : c >= 0.99995 ? '>99.99%' : `${(c * 100).toFixed(1)}%`;

const RegimeRegion = ({ region, fc, chg }) => {
  const days = fc?.days || [];
  const regime = chg?.regime ?? null;
  const allSame = days.length > 1 && days.every(d => d.risk_on === days[0].risk_on);
  let changeLine = null;
  if (chg) {
    if (!chg.history) {
      changeLine = 'no daily history — latest snapshot only';
    } else if (chg.prev_regime == null) {
      changeLine = `${regime} for ${chg.days_in_regime ?? '—'}+ days (120d window)`;
    } else if (chg.days_in_regime === 1) {
      changeLine = `changed today: ${chg.prev_regime} → ${regime}`;
    } else {
      changeLine = `${chg.prev_regime} → ${regime} on ${chg.changed_on} · ${chg.days_in_regime}d in regime`;
    }
  }
  return (
    <div className="px-3 py-2">
      <div className="flex items-baseline gap-2 flex-wrap">
        <span className="font-mono text-[10px] font-black text-white flex-none">{region}</span>
        <span className="text-[12px] font-bold text-slate-100" title={`${chg?.source || ''}${regime ? `\n${REGIME_MEANING[regime] || ''}` : ''}`}>
          {regime ?? '—'}
        </span>
        <span className="font-mono text-[9px] text-slate-400"
          title={region === 'US' ? 'HMM posterior probability of the current regime (gold.regime_label)' : 'No regime posterior for HK — the HMM is US-scope (SPY/VIX features)'}>
          P {fmtConf(chg?.confidence)}
        </span>
        <span className="text-[9px] font-mono text-slate-500 truncate" title={chg?.source || ''}>{changeLine ?? '—'}</span>
      </div>
      {days.length > 0 && (
        <div className="grid grid-cols-7 gap-0.5 mt-1.5">
          {days.map((d, i) => (
            <div key={d.date || i}
              className={`rounded px-0.5 py-0.5 text-center ${RISK_CELL(d.risk_on)}`}
              title={`${d.date ?? ''} · ${d.risk_on != null ? `${d.risk_on.toFixed(1)}%` : '—'} risk-on — momentum_nowcast (consumption.macro_regime_7d)${allSame ? ' · flat carry-forward nowcast' : ''}`}>
              <div className="text-[8px] font-mono opacity-80">
                {d.date ? new Date(d.date + 'T00:00:00').toLocaleDateString('en-US', { weekday: 'narrow' }) : '·'}
              </div>
              <div className="text-[9px] font-mono font-bold">
                {d.risk_on != null ? `${d.risk_on.toFixed(0)}%` : '—'}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

const MarketContext = ({ fc, chg, fresh }) => (
  <Panel title="Market Context · Regime" fresh={fresh} action={
    <span className="text-[9px] text-slate-600"
      title="Current regime: consumption.market_sentiment (canonical) + HMM posterior from gold.regime_label (US, SPY/VIX features). 7-day strip: momentum_nowcast (consumption.macro_regime_7d). Legend: ≥60% risk-on = emerald · ≤40% = rose · else neutral.">
      HMM daily + 7d nowcast · ≥60% on / ≤40% off
    </span>
  }>
    <div className="grid grid-cols-1 sm:grid-cols-2 divide-y sm:divide-y-0 sm:divide-x divide-white/[0.05]">
      <RegimeRegion region="US" fc={fc?.US} chg={chg?.US} />
      <RegimeRegion region="HK" fc={fc?.HK} chg={chg?.HK} />
    </div>
  </Panel>
);

// ---------------------------------------------------------------------------
// Command page — PAPER trading command center
// ---------------------------------------------------------------------------
export const CommandCenter = ({ navigateToTab }) => {
  const [overview, setOverview] = useState(null);
  const [pnlMode, setPnlMode] = useState(null);
  const [orders, setOrders] = useState(null);
  const [regimeFc, setRegimeFc] = useState(null);
  const [regimeChg, setRegimeChg] = useState(null);
  const [oppPicks, setOppPicks] = useState([]);
  const [bookOv, setBookOv] = useState(null);
  const [limits, setLimits] = useState(null);
  const [gateway, setGateway] = useState(null);
  const [sysStatus, setSysStatus] = useState(null);
  const [paperPos, setPaperPos] = useState(null);
  const [stratNames, setStratNames] = useState({});
  const [fills, setFills] = useState(null);
  const registry = useFreshness();

  usePoll(async () => {
    const res = await api.get('/api/command/overview');
    if (res) setOverview(res);
  }, 60000, 4500);

  usePoll(async () => {
    const res = await api.get('/api/command/pnl-by-mode');
    if (res) setPnlMode(res);
  }, 60000);

  // Paper book stats + YTD realized curve (fixed scope — this page is the
  // PAPER command center; other modes ride in the env strip).
  usePoll(async () => {
    const res = await api.get('/api/execution/book-overview?book=paper');
    if (res) setBookOv(res);
  }, 60000);

  usePoll(async () => {
    const res = await api.get('/api/command/order-book');
    if (res) setOrders(res.orders || []);
  }, 60000, 1500);

  usePoll(async () => {
    const res = await api.get('/api/execution/limits');
    if (res) setLimits(res);
  }, 60000, 3000);

  usePoll(async () => {
    const res = await api.get('/api/execution/gateway');
    if (res) setGateway(res);
  }, 60000, 1600);

  usePoll(async () => {
    const res = await api.get('/api/agents/paper/system-status');
    if (res) setSysStatus(res);
  }, 60000, 3200);

  usePoll(async () => {
    const res = await api.get('/api/agents/paper/open-positions');
    if (res) setPaperPos(Array.isArray(res?.positions) ? res.positions : []);
  }, 60000, 3400);

  // strategy_id → display name map for the positions table.
  useEffect(() => {
    let cancelled = false;
    const t = setTimeout(() => {
      api.get('/api/paper-strategies').then(res => {
        const rows = Array.isArray(res) ? res : (res?.strategies || res?.data || []);
        if (!cancelled && Array.isArray(rows)) {
          const map = {};
          for (const r of rows) if (r.strategy_id && r.strategy_name) map[r.strategy_id] = r.strategy_name;
          setStratNames(map);
        }
      });
    }, 6000);
    return () => { cancelled = true; clearTimeout(t); };
  }, []);

  usePoll(async () => {
    const res = await api.get('/api/agents/paper/trade-history?limit=12');
    if (res) setFills(Array.isArray(res?.trades) ? res.trades : []);
  }, 60000, 4600);

  usePoll(async () => {
    const res = await api.get('/api/command/regime-forecast');
    if (res) setRegimeFc(res.markets || {});
  }, 300000, 7000);

  // Change-vs-yesterday per region: US from the HMM daily series, HK honestly
  // reports no daily history.
  usePoll(async () => {
    const res = await api.get('/api/command/regime-change');
    if (res) setRegimeChg(res.regions || {});
  }, 300000, 7400);

  usePoll(async () => {
    const [u, fams] = await Promise.all([
      api.get('/api/signals/universe?markets=US,HK,CRYPTO,FX,METAL&limit=10'),
      api.get('/api/signals/families'),
    ]);
    if (!u) return;
    const famMap = {};
    for (const f of (fams?.data || [])) famMap[f.key] = f;
    const data = u.data || u;
    const picks = [];
    for (const [mkt, rows] of Object.entries(data)) {
      if (!Array.isArray(rows)) continue;
      const buys = rows.filter(r => r.direction === 'BUY' && !r.exit_to_cash)
        .sort((a, b) => (b.potential ?? -1) - (a.potential ?? -1));
      const top = buys[0];
      if (!top) continue;
      const fam = (top.families || []).map(k => famMap[k]).find(Boolean);
      const note = top.note && top.note !== '—' ? top.note : null;
      picks.push({
        market: mkt,
        ticker: top.ticker,
        name: top.name || null,
        potential: top.potential ?? null,
        direction: top.direction || null,
        price: top.price ?? null,
        changePct: top.change_pct ?? null,
        strategyName: fam?.strategy_name || null,
        reason: note || (fam ? `${fam.label} family signal` : `${MARKET_LABEL[mkt] || mkt} BUY signal`),
      });
    }
    picks.sort((a, b) => (b.potential ?? -1) - (a.potential ?? -1));
    const top3 = picks.slice(0, 3);
    // Signal dates: the universe endpoint does not project updated_at — the
    // read-only /api/command/signal-freshness lookup serves it per ticker.
    const dates = top3.length
      ? await api.get(`/api/command/signal-freshness?tickers=${top3.map(p => encodeURIComponent(p.ticker)).join(',')}`)
      : null;
    const dateMap = dates?.dates || {};
    setOppPicks(top3.map(p => ({ ...p, signalDate: dateMap[p.ticker.toUpperCase()] || null })));
  }, 120000, 8000);

  // Per-panel freshness from the source→panel dependency map (never tagged
  // by hand — panels inherit the worst state of their upstream sources).
  const fMarket = panelFreshness(PANEL_SOURCES.market, registry);
  const fBook = panelFreshness(PANEL_SOURCES.myBook, registry);
  const fPnlMode = panelFreshness(PANEL_SOURCES.pnlByMode, registry);
  const fOrders = panelFreshness(PANEL_SOURCES.orderBook, registry);
  const fOpps = panelFreshness(PANEL_SOURCES.opportunities, registry);
  const fRegime = panelFreshness(PANEL_SOURCES.regime, registry);
  const fPos = panelFreshness(PANEL_SOURCES.paperBookAsset, registry);
  const fAttn = panelFreshness(PANEL_SOURCES.attention, registry);

  // Header data-freshness = worst state across the panels on this page.
  const FR_RANK = { [FR.DISCONNECTED]: 4, [FR.STALE]: 3, [FR.LAGGING]: 2, [FR.UNKNOWN]: 1, [FR.FRESH]: 0 };
  const dataFresh = [fMarket, fBook, fPnlMode, fOrders, fOpps, fRegime, fPos]
    .filter(Boolean)
    .sort((a, b) => (FR_RANK[b.state] ?? 0) - (FR_RANK[a.state] ?? 0))[0] || null;

  // Paper-scoped working orders (this is the PAPER command center).
  const paperOrders = useMemo(() => (orders || []).filter(o => o.source === 'paper'), [orders]);

  // Open positions sorted by market value desc.
  const posRows = useMemo(() => {
    const rows = (paperPos || []).slice();
    rows.sort((a, b) => ((b.shares ?? 0) * (b.current_price ?? 0)) - ((a.shares ?? 0) * (a.current_price ?? 0)));
    return rows;
  }, [paperPos]);

  // Risk rollup for the KPI tile.
  const risks = useMemo(() => overview?.strategy_risks || [], [overview]);
  const attn = useMemo(() => overview?.attention || [], [overview]);
  const risk = {
    halted: !!limits?.global_halt,
    critical: risks.filter(r => r.sev === 'critical').length + attn.filter(a => a.sev === 'critical').length,
    warning: risks.filter(r => r.sev === 'warning').length + attn.filter(a => a.sev === 'warning').length,
    gap: overview?.monitoring_gap || 0,
  };

  // Action Required items — operational issues only, severity-ordered.
  const actionItems = useMemo(() => {
    const items = [];
    if (limits?.global_halt) {
      items.push({ id: 'halt', sev: 'critical', title: 'Global HALT active', impact: 'Working orders cancelled and book flattened — gold.risk_limits.global_halt', target: 'settings' });
    }
    if (gateway && gateway.connected === false) {
      items.push({ id: 'gw', sev: 'critical', title: 'IBKR gateway disconnected', impact: 'No order routing or account feed', target: 'settings' });
    }
    if (sysStatus?.last_run_status && sysStatus.last_run_status !== 'ok') {
      items.push({ id: 'run', sev: 'warning', title: `Last paper run: ${sysStatus.last_run_status}`, impact: `${sysStatus.last_run_type || ''} run ${sysStatus.last_run_date || ''}`.trim(), target: 'execution' });
    }
    for (const r of risks) {
      items.push({
        id: `risk-${r.strategy_id}`, sev: r.sev || 'warning',
        title: `${r.name || r.strategy_id}: risk trigger`,
        impact: (r.triggers || []).join(' · '), target: 'strategies',
      });
    }
    for (const a of attn) {
      if (a.sev === 'info') continue;
      items.push({
        id: a.id, sev: a.sev || 'info', title: a.title, impact: a.impact,
        target: a.target || null, age: a.created_at ? fmtAge(a.created_at) : null,
      });
    }
    if ((overview?.monitoring_gap || 0) > 0) {
      items.push({ id: 'gap', sev: 'warning', title: `${overview.monitoring_gap} position${overview.monitoring_gap === 1 ? '' : 's'} without monitoring`, impact: 'Open legs not actively monitored', target: 'execution' });
    }
    if (dataFresh && (dataFresh.state === FR.STALE || dataFresh.state === FR.DISCONNECTED)) {
      items.push({
        id: 'stale', sev: 'warning',
        title: `Data ${dataFresh.state === FR.STALE ? 'stale' : 'disconnected'}${dataFresh.culprit ? `: ${dataFresh.culprit.name}` : ''}`,
        impact: dataFresh.culprit?.budgetH != null ? `staleness budget ${dataFresh.culprit.budgetH}h exceeded` : 'source refresh overdue',
        target: 'settings',
      });
    }
    const rank = { critical: 0, warning: 1, info: 2 };
    items.sort((a, b) => (rank[a.sev] ?? 3) - (rank[b.sev] ?? 3));
    return items;
  }, [limits, gateway, sysStatus, risks, attn, overview, dataFresh]);

  const st = bookOv?.stats;
  const boCurve = (bookOv?.ytd_curve || []).map(p => ({ d: p.d, equity: p.cum }));
  const paperAcct = overview?.account?.books?.paper;
  const liveAcct = overview?.account?.books?.live;

  return (
    <div className="space-y-2.5">
      {/* 1 — Command header + slim market ticker */}
      <CommandHeader limits={limits} gateway={gateway} sysStatus={sysStatus} dataFresh={dataFresh} />
      <MarketTicker fresh={fMarket} />

      {/* 2 — Environment status strip (replaces the four big mode cards) */}
      <EnvStrip pnlMode={pnlMode} liveAcct={liveAcct} navigateToTab={navigateToTab} fresh={fPnlMode} />

      {/* 3 — Primary KPI row (shown once) */}
      <KpiRow st={st} paperAcct={paperAcct} orderCount={orders == null ? null : paperOrders.length} risk={risk} fresh={fBook} />

      {/* 4 — Operational grid: chart + positions (left, ~65%) · actions +
              opportunities (right, ~35%) */}
      <div className="grid grid-cols-1 lg:grid-cols-[minmax(0,65fr)_minmax(0,35fr)] gap-2.5">
        <div className="space-y-2.5 min-w-0">
          <Panel title="Cumulative Realized P&L · YTD" fresh={fBook} action={
            st?.win_rate != null
              ? <span className="font-mono text-[10px] text-slate-400" title="Win rate over closed trades">WR {st.win_rate}%</span>
              : null
          }>
            <EquityCurve data={boCurve} color="#60a5fa" height={240}
              emptyLabel={bookOv == null ? 'Loading book…' : 'No realized P&L this year'} />
          </Panel>
          <OpenPositions rows={posRows} stratNames={stratNames} fresh={fPos} navigateToTab={navigateToTab} />
        </div>
        <div className="space-y-2.5 min-w-0">
          <ActionRequired items={actionItems} fresh={fAttn} navigateToTab={navigateToTab} />
          <Opportunities picks={oppPicks} positions={paperPos || []} orders={paperOrders} navigateToTab={navigateToTab} fresh={fOpps} />
        </div>
      </div>

      {/* 5 — Working orders + recent fills, compact side by side */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-2.5">
        <WorkingOrders orders={paperOrders} fresh={fOrders} navigateToTab={navigateToTab} />
        <RecentFills trades={fills || []} fresh={fOrders} />
      </div>

      {/* 6 — Market context (compact regime forecast) */}
      <MarketContext fc={regimeFc} chg={regimeChg} fresh={fRegime} />
    </div>
  );
};

export default CommandCenter;
