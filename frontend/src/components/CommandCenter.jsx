import React, { useMemo, useState, useEffect, useRef } from 'react';
import { useParams, useSearchParams } from 'react-router-dom';
import { api, usePoll, fmtK, fmtKCcy, fmtPct, fmtAge, pnlCl, marketClock, marketStatus } from '../utils';

// Command home — environment-scoped command center (redesign 2026-11-09, v4).
// A SIM | PAPER | UAT | LIVE toggle in the header scopes the ENTIRE page:
// KPIs, chart, positions, orders, fills, alerts and opportunities all read
// from the selected environment's own ledgers — never mixed, never relabeled.
// The selection lives in the URL (?env=) and is restored on reload.
//
// Per-environment lineage:
//   SIM   — positions /api/portfolio/positions (consumption.portfolio_positions_current)
//           stats+chart /api/execution/book-overview?book=sim
//           fills /api/execution/trades?book=sim (gold.paper_trades_synthetic
//           x registry SIMULATION, closed) · NO working-order book exists
//   PAPER — positions /api/agents/paper/open-positions · stats+chart
//           book-overview?book=paper · orders /api/command/order-book
//           (source=paper) · fills /api/execution/trades?book=paper ·
//           account /api/command/overview account.books.paper
//   UAT   — session/account/positions/orders /api/ib/tws/uat/* (live gateway)
//           fills /api/execution/trades?book=uat (gold.manual_orders blotter)
//           fill totals /api/command/pnl-by-mode modes.uat · NO round-trip
//           P&L ledger exists (fills-only) => chart + realized P&L are
//           explicit no-data states
//   LIVE  — positions /api/positions/live (ibkr_snapshot) · account
//           /api/command/overview account.books.live · equity
//           /api/command/overview equity_curve (last 30 sessions, HKD) ·
//           orders /api/command/order-book (source=live) · fills
//           /api/execution/trades?book=live (gold.trade_executions)
//
// Restrained palette: colour carries meaning only.
//   rose  = critical severity   emerald/rose text = signed P&L (via pnlCl)
//   blue  = interactive links   everything else = neutral slate/white

// ---------------------------------------------------------------------------
// Environment model
// ---------------------------------------------------------------------------
const ENVS = ['sim', 'paper', 'uat', 'live'];
const ENV_META = {
  sim:   { badge: 'SIM',   tip: 'Simulation book — virtual money · synthetic fills · no IBKR' },
  paper: { badge: 'PAPER', tip: 'Paper book — virtual money · strategy rehearsal · no IBKR' },
  uat:   { badge: 'UAT',   tip: 'UAT — IBKR paper account · real order routing · paper money' },
  live:  { badge: 'LIVE',  tip: 'Live book — IBKR live account · real money' },
};

// ---------------------------------------------------------------------------
// Date helpers — absolute dates only. First table columns are YYYY-MM-DD;
// exact UTC timestamps ride in tooltips; relative age survives only as the
// separate DAYS HELD column.
// ---------------------------------------------------------------------------
const fmtDate = (v) => {
  if (!v) return null;
  const s = String(v);
  return s.length >= 10 ? s.slice(0, 10) : s;
};

const tsTip = (v) => {
  if (!v) return '';
  const s = String(v);
  const norm = s.includes('T') ? s : s.replace(' ', 'T');
  const z = /([zZ]|[+-]\d{2}:?\d{2})$/.test(norm) ? norm : `${norm}Z`;
  const d = new Date(z);
  return isNaN(d) ? s : `${d.toISOString().slice(0, 19).replace('T', ' ')} UTC`;
};

const daysHeld = (entry) => {
  if (!entry) return null;
  const s = String(entry);
  const d = new Date(s.length === 10 ? `${s}T00:00:00Z` : (s.includes('T') ? s : `${s.replace(' ', 'T')}Z`));
  if (isNaN(d)) return null;
  return Math.max(0, Math.floor((Date.now() - d.getTime()) / 86400000));
};

// ---------------------------------------------------------------------------
// Shared bits
// ---------------------------------------------------------------------------
const LinkBtn = ({ children, onClick }) => (
  <button onClick={onClick} className="text-[10px] font-semibold text-blue-400 hover:text-blue-300">{children}</button>
);

const Panel = ({ title, action, children, className = '' }) => (
  <div className={`qr-surface overflow-hidden ${className}`}>
    <div className="flex items-center justify-between px-3 py-2 border-b border-white/[0.05]">
      <span className="text-[11px] font-bold uppercase tracking-wide text-slate-300 flex items-center gap-2">{title}</span>
      {action}
    </div>
    {children}
  </div>
);

// Honest no-data state: an environment that lacks supported data says so
// explicitly — another environment's data is never relabeled into the gap.
const NoData = ({ children }) => (
  <div className="px-3 py-2.5 text-[12px] text-slate-500">{children}</div>
);

// Small as-of tag sourced from the payload's own timestamp.
const AsOf = ({ ts }) => {
  if (!ts) return null;
  return <span className="font-mono text-[9px] text-slate-600 normal-case tracking-normal" title={`Payload as_of ${tsTip(ts)}`}>upd {fmtAge(ts)}</span>;
};

// ---------------------------------------------------------------------------
// Header — "Command" + environment toggle + HALT + per-environment session
// status. One line on desktop, wraps on mobile.
// ---------------------------------------------------------------------------
const StatusItem = ({ label, children, tip }) => (
  <span className="flex items-center gap-1.5 flex-none" title={tip}>
    <span className="text-[9px] uppercase tracking-wide text-slate-500">{label}</span>
    {children}
  </span>
);

const EnvToggle = ({ env, onChange }) => (
  <span className="flex items-center rounded overflow-hidden border border-white/[0.08] flex-none" role="tablist" aria-label="Environment">
    {ENVS.map(e => (
      <button key={e} role="tab" aria-selected={env === e} onClick={() => onChange(e)} title={ENV_META[e].tip}
        className={`px-2.5 py-1 text-[10px] font-bold font-mono ${env === e ? 'bg-white/[0.08] text-white' : 'text-slate-500 hover:text-slate-300'}`}>
        {ENV_META[e].badge}
      </button>
    ))}
  </span>
);

// Per-environment session status for the header. `sess` is env-tagged so a
// stale payload from a previous environment is never shown.
const SessionItem = ({ env, sess }) => {
  if (env === 'sim') {
    return <StatusItem label="Session" tip="SIM book — virtual money, synthetic fills; no broker session exists"><span className="font-mono text-[10px] text-slate-300">n/a · virtual</span></StatusItem>;
  }
  if (env === 'paper') {
    const run = sess?.res?.last_run_type
      ? `${sess.res.last_run_type} ${sess.res.last_run_status || ''} ${sess.res.last_run_date || ''}`.trim()
      : null;
    const bad = sess?.res?.last_run_status && sess.res.last_run_status !== 'ok';
    return (
      <StatusItem label="Last run" tip="Latest paper pipeline run — /api/agents/paper/system-status">
        <span className={`font-mono text-[10px] ${bad ? 'text-rose-300' : 'text-slate-300'}`}>{sess == null || sess.env !== env ? '—' : (run || '—')}</span>
      </StatusItem>
    );
  }
  if (env === 'uat') {
    const s = sess?.env === 'uat' ? sess.res : null;
    const connected = s?.is_connected === true;
    return (
      <StatusItem label="Session" tip={s ? `${s.message || ''} · ${s.host || ''}:${s.port || ''} client ${s.client_id ?? '—'}` : 'UAT session status unavailable'}>
        <span className={`w-1.5 h-1.5 rounded-full ${s == null ? 'bg-slate-600' : connected ? 'bg-emerald-400' : 'bg-rose-400'}`} />
        <span className="font-mono text-[10px] text-slate-300">{s == null ? '—' : connected ? 'connected' : 'down'}</span>
      </StatusItem>
    );
  }
  // live
  const g = sess?.env === 'live' ? sess.res : null;
  const ok = g?.connected === true;
  const hb = g?.last_heartbeat || g?.sessions?.primary?.last_heartbeat || null;
  return (
    <StatusItem label="Gateway" tip={g ? `IBKR live gateway ${ok ? 'connected' : 'DISCONNECTED'}${hb ? ` · heartbeat ${tsTip(hb)}` : ''}` : 'Live gateway status unavailable'}>
      <span className={`w-1.5 h-1.5 rounded-full ${g == null ? 'bg-slate-600' : ok ? 'bg-emerald-400' : 'bg-rose-400'}`} />
      <span className="font-mono text-[10px] text-slate-300">{g == null ? '—' : ok ? (hb ? fmtAge(hb) : 'connected') : 'down'}</span>
    </StatusItem>
  );
};

const CommandHeader = ({ env, onEnv, limits, sess }) => {
  const halted = !!limits?.global_halt;
  return (
    <div className="qr-surface px-3 py-2">
      <div className="flex items-center gap-x-4 gap-y-1 flex-wrap">
        <span className="flex items-center gap-2.5 flex-none">
          <h1 className="text-sm font-bold text-white">Command</h1>
          <EnvToggle env={env} onChange={onEnv} />
        </span>
        <StatusItem label="Env" tip={ENV_META[env].tip}>
          <span className="qr-chip qr-chip-slate">{ENV_META[env].badge}</span>
        </StatusItem>
        <StatusItem label="HALT" tip={halted ? 'Global halt is ACTIVE — gold.risk_limits.global_halt (applies to every environment)' : 'No global halt — gold.risk_limits.global_halt = false'}>
          <span className={`font-mono text-[10px] font-bold ${halted ? 'text-rose-300' : 'text-slate-300'}`}>
            {limits == null ? '—' : halted ? 'HALTED' : 'off'}
          </span>
        </StatusItem>
        <SessionItem env={env} sess={sess} />
      </div>
    </div>
  );
};

// ---------------------------------------------------------------------------
// Slim market ticker — visually subordinate, environment-agnostic market data.
// ---------------------------------------------------------------------------
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

const Clock = ({ label, t, open }) => (
  <span className="flex items-center gap-1" title={open ? 'session open' : 'session closed'}>
    <span className={`w-1 h-1 rounded-full ${open ? 'bg-emerald-400' : 'bg-slate-600'}`} />
    <span className="text-slate-500">{label}</span>
    <span className="font-mono text-slate-300">{t}</span>
  </span>
);

const Clocks = () => {
  const [, setTick] = useState(0);
  useEffect(() => {
    const id = setInterval(() => setTick(t => t + 1), 1000);
    return () => clearInterval(id);
  }, []);
  const c = marketClock();
  const s = marketStatus();
  return (
    <span className="flex items-center gap-2.5 text-[9px] flex-none">
      <Clock label="HKT" t={c.hkt} open={s.hk} />
      <Clock label="LON" t={c.lon} open={s.lon} />
      <Clock label="NYC" t={c.nyc} open={s.nyc} />
    </span>
  );
};

function MarketTicker() {
  const [ov, setOv] = useState(null);
  const load = async () => {
    const res = await api.get('/api/markets/overview?regions=US,HK');
    if (res) setOv(res);
  };
  usePoll(load, 30000, 800);

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
    </div>
  );
}

// ---------------------------------------------------------------------------
// KPI row — compact tiles, per-environment values.
// ---------------------------------------------------------------------------
const Kpi = ({ label, value, valueCl = 'text-white', sub, tip }) => (
  <div className="qr-surface px-3 py-2.5 flex flex-col justify-center min-w-0" title={tip}>
    <div className="text-[10px] font-semibold uppercase tracking-wide text-slate-500 truncate">{label}</div>
    <div className={`font-mono text-[22px] font-bold leading-tight mt-1 truncate ${valueCl}`}>{value}</div>
    {sub != null && <div className="text-[10px] text-slate-500 leading-tight mt-1 truncate">{sub}</div>}
  </div>
);

// ---------------------------------------------------------------------------
// Cumulative chart. Width tracks the container via ResizeObserver so the
// chart truly spans its panel; height fixed by prop.
// ---------------------------------------------------------------------------
function EquityCurve({ data, color, height = 240, emptyLabel = 'No history yet' }) {
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

// ---------------------------------------------------------------------------
// Open Positions — the primary FULL-WIDTH section, directly under the KPI
// row. ENTRY DATE leftmost (YYYY-MM-DD), then SYMBOL | STRATEGY | SIDE | QTY
// | ENTRY PRICE | CURRENT PRICE | UNREALIZED P&L | MARKET VALUE | DAYS HELD.
// No trapped scroll box: the first POSITIONS_PAGE rows render inline and a
// Show More control reveals the rest — every position stays accessible.
// Unsupported fields render an honest '—' with a tooltip.
// ---------------------------------------------------------------------------
const POSITIONS_PAGE = 25;

const POSITIONS_HEAD = [
  { k: 'entry', label: 'Entry date', align: 'left' },
  { k: 'symbol', label: 'Symbol', align: 'left' },
  { k: 'strategy', label: 'Strategy', align: 'left' },
  { k: 'side', label: 'Side', align: 'left' },
  { k: 'qty', label: 'Qty', align: 'right' },
  { k: 'entryPx', label: 'Entry price', align: 'right' },
  { k: 'curPx', label: 'Current price', align: 'right' },
  { k: 'unreal', label: 'Unrealized P&L', align: 'right' },
  { k: 'mv', label: 'Market value', align: 'right' },
  { k: 'days', label: 'Days held', align: 'right' },
];

const OpenPositions = ({ env, rows, count, asOf, headTip, note, emptyText, navigateToTab }) => {
  const [showAll, setShowAll] = useState(false);
  const visible = rows == null ? null : (showAll ? rows : rows.slice(0, POSITIONS_PAGE));
  const hidden = rows != null ? rows.length - (visible?.length ?? 0) : 0;
  return (
    <Panel title={`Open Positions · ${ENV_META[env].badge}`} action={
      <span className="flex items-center gap-3">
        <span className="text-[10px] text-slate-500" title={headTip}>{count != null ? `${count} open` : ''}{note ? ` · ${note}` : ''}</span>
        <AsOf ts={asOf} />
        <LinkBtn onClick={() => navigateToTab('execution')}>Execution →</LinkBtn>
      </span>
    }>
      {rows == null ? (
        <NoData>Loading…</NoData>
      ) : rows.length > 0 ? (
        <div className="overflow-x-auto">
          <table className="w-full min-w-[960px]">
            <thead className="bg-white/[0.02]">
              <tr className="text-[10px] font-semibold text-slate-500 uppercase tracking-wide">
                {POSITIONS_HEAD.map(h => (
                  <th key={h.k} className={`${h.align === 'right' ? 'text-right' : 'text-left'} ${h.k === 'entry' ? 'px-3' : 'px-2'} py-2 ${h.k === 'days' ? 'px-3' : ''}`}
                    title={h.k === 'entry' || h.k === 'days' ? 'Absolute entry date (YYYY-MM-DD), newest first where the environment serves entry dates' : undefined}>
                    {h.label}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {visible.map((p, i) => (
                <tr key={p.key || `${p.symbol}-${i}`} className="border-t border-white/[0.05] text-[13px] leading-snug">
                  <td className="px-3 py-2 font-mono text-slate-300 whitespace-nowrap" title={p.entryTip || undefined}>
                    {p.entryDate ?? '—'}
                  </td>
                  <td className="px-2 py-2 font-mono font-bold text-white whitespace-nowrap">
                    {p.symbol}
                    {p.ccy && <span className="text-[10px] font-normal text-slate-500 ml-1">{p.ccy}</span>}
                  </td>
                  <td className="px-2 py-2 text-[12px] text-slate-400 max-w-[240px] truncate" title={p.strategyTip || p.strategy || undefined}>
                    {p.strategy ?? '—'}
                  </td>
                  <td className="px-2 py-2 font-mono font-bold text-slate-300">{p.side ?? '—'}</td>
                  <td className="px-2 py-2 text-right font-mono text-slate-200">{p.qty != null ? Math.abs(p.qty).toLocaleString() : '—'}</td>
                  <td className="px-2 py-2 text-right font-mono text-slate-300">{p.entryPx != null ? p.entryPx.toLocaleString(undefined, { maximumFractionDigits: 2 }) : '—'}</td>
                  <td className="px-2 py-2 text-right font-mono text-slate-300" title={p.curTip || undefined}>
                    {p.curPx != null ? p.curPx.toLocaleString(undefined, { maximumFractionDigits: 2 }) : '—'}
                  </td>
                  <td className={`px-2 py-2 text-right font-mono font-bold whitespace-nowrap ${p.unreal != null ? pnlCl(p.unreal) : 'text-slate-600'}`}>
                    {p.unreal != null ? `${p.unreal >= 0 ? '+' : ''}${fmtK(p.unreal)}` : '—'}
                  </td>
                  <td className="px-2 py-2 text-right font-mono text-slate-300">{p.mv != null ? fmtK(p.mv) : '—'}</td>
                  <td className="px-3 py-2 text-right font-mono text-[12px] text-slate-500" title={p.entryTip || undefined}>
                    {p.days != null ? p.days : '—'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {hidden > 0 && (
            <button onClick={() => setShowAll(true)}
              className="w-full px-3 py-2 text-[12px] font-semibold text-blue-400 hover:text-blue-300 text-center border-t border-white/[0.05]">
              Show all {rows.length} positions ({hidden} more) ↓
            </button>
          )}
          {showAll && rows.length > POSITIONS_PAGE && (
            <button onClick={() => setShowAll(false)}
              className="w-full px-3 py-2 text-[12px] font-semibold text-slate-500 hover:text-slate-300 text-center border-t border-white/[0.05]">
              Show first {POSITIONS_PAGE} ↑
            </button>
          )}
        </div>
      ) : (
        <NoData>{emptyText}</NoData>
      )}
    </Panel>
  );
};

// ---------------------------------------------------------------------------
// Working Orders — ORDER DATE leftmost where supported. Card height follows
// content; empty/unsupported renders a one-line strip, never a big empty box.
// ---------------------------------------------------------------------------
const InlineNote = ({ title, children }) => (
  <div className="qr-surface px-3 py-2 flex items-baseline gap-2 flex-wrap">
    <span className="text-[11px] font-bold uppercase tracking-wide text-slate-400 flex-none">{title}</span>
    <span className="text-[12px] text-slate-500">{children}</span>
  </div>
);

const WorkingOrders = ({ env, rows, asOf, headTip, emptyText, unsupportedText, navigateToTab }) => {
  if (unsupportedText) {
    return <InlineNote title={`Working Orders · ${ENV_META[env].badge}`}>{unsupportedText}</InlineNote>;
  }
  if (rows != null && rows.length === 0) {
    return <InlineNote title={`Working Orders · ${ENV_META[env].badge}`}>{emptyText}</InlineNote>;
  }
  return (
    <Panel title={`Working Orders · ${ENV_META[env].badge}`} action={
      <span className="flex items-center gap-3">
        <span className="text-[10px] text-slate-500" title={headTip}>{rows != null ? `${rows.length} working` : ''}</span>
        <AsOf ts={asOf} />
        <LinkBtn onClick={() => navigateToTab('execution')}>Orders →</LinkBtn>
      </span>
    }>
      {rows == null ? (
        <NoData>Loading…</NoData>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full min-w-[620px]">
            <thead className="bg-white/[0.02]">
              <tr className="text-[10px] font-semibold text-slate-500 uppercase tracking-wide">
                <th className="text-left px-3 py-2" title="Absolute order date (YYYY-MM-DD), newest first where served">Order date</th>
                <th className="text-left px-2 py-2">Ticker</th>
                <th className="text-left px-2 py-2">Side</th>
                <th className="text-right px-2 py-2">Qty</th>
                <th className="text-right px-2 py-2">Limit / type</th>
                <th className="text-left px-2 py-2">Strategy</th>
                <th className="text-left px-3 py-2">Status</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((o, i) => (
                <tr key={o.key || `${o.ticker}-${i}`} className="border-t border-white/[0.05] text-[13px] leading-snug">
                  <td className="px-3 py-2 font-mono text-slate-300 whitespace-nowrap" title={o.orderTs ? tsTip(o.orderTs) : o.orderTip || undefined}>
                    {o.orderDate ?? '—'}
                  </td>
                  <td className="px-2 py-2 font-mono font-bold text-white">{o.ticker}</td>
                  <td className={`px-2 py-2 font-mono font-bold ${o.side === 'BUY' ? 'text-emerald-400' : o.side === 'SELL' || o.side === 'CLOSE' ? 'text-rose-400' : 'text-slate-400'}`}>{o.side ?? '—'}</td>
                  <td className="px-2 py-2 text-right font-mono text-slate-200">{o.qty != null ? o.qty.toLocaleString() : '—'}</td>
                  <td className="px-2 py-2 text-right font-mono text-slate-300">{o.limitOrType ?? '—'}</td>
                  <td className="px-2 py-2 text-[12px] text-slate-400 max-w-[180px] truncate" title={o.strategy || undefined}>{o.strategy ?? '—'}</td>
                  <td className="px-3 py-2"><span className="text-[10px] px-1.5 py-0.5 rounded bg-white/[0.06] text-slate-300">{o.status ?? '—'}</span></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </Panel>
  );
};

// ---------------------------------------------------------------------------
// Recent Fills — FILL DATE leftmost, then TICKER | STRATEGY | SIDE | QTY |
// PRICE | REALIZED P&L where supported. Newest first. Card height follows
// content; empty renders a one-line strip.
// ---------------------------------------------------------------------------
const RecentFills = ({ env, rows, asOf, headTip, emptyText }) => {
  if (rows != null && rows.length === 0) {
    return <InlineNote title={`Recent Fills · ${ENV_META[env].badge}`}>{emptyText}</InlineNote>;
  }
  return (
    <Panel title={`Recent Fills · ${ENV_META[env].badge}`} action={
      <span className="flex items-center gap-3">
        <span className="text-[10px] text-slate-500" title={headTip}>{rows != null ? `${rows.length} shown` : ''}</span>
        <AsOf ts={asOf} />
      </span>
    }>
      {rows == null ? (
        <NoData>Loading…</NoData>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full min-w-[680px]">
            <thead className="bg-white/[0.02]">
              <tr className="text-[10px] font-semibold text-slate-500 uppercase tracking-wide">
                <th className="text-left px-3 py-2" title="Absolute fill date (YYYY-MM-DD), newest first; exact UTC timestamp in row tooltip">Fill date</th>
                <th className="text-left px-2 py-2">Ticker</th>
                <th className="text-left px-2 py-2">Strategy</th>
                <th className="text-left px-2 py-2">Side</th>
                <th className="text-right px-2 py-2">Qty</th>
                <th className="text-right px-2 py-2">Price</th>
                <th className="text-right px-3 py-2">Realized P&L</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((t, i) => (
                <tr key={t.key || `${t.fillTs}-${t.ticker}-${i}`} className="border-t border-white/[0.05] text-[13px] leading-snug" title={t.fillTs ? `filled ${tsTip(t.fillTs)}` : undefined}>
                  <td className="px-3 py-2 font-mono text-slate-300 whitespace-nowrap">{t.fillDate ?? '—'}</td>
                  <td className="px-2 py-2 font-mono font-bold text-white">{t.ticker}</td>
                  <td className="px-2 py-2 text-[12px] text-slate-400 max-w-[200px] truncate" title={t.strategyTip || t.strategy || undefined}>{t.strategy ?? '—'}</td>
                  <td className={`px-2 py-2 font-mono font-bold ${t.side === 'BUY' || t.side === 'LONG' ? 'text-emerald-400' : t.side === 'SELL' || t.side === 'SHORT' ? 'text-rose-400' : 'text-slate-400'}`}>{t.side ?? '—'}</td>
                  <td className="px-2 py-2 text-right font-mono text-slate-200">{t.qty != null ? t.qty.toLocaleString() : '—'}</td>
                  <td className="px-2 py-2 text-right font-mono text-slate-300">{t.price != null ? t.price.toLocaleString(undefined, { maximumFractionDigits: 2 }) : '—'}</td>
                  <td className={`px-3 py-2 text-right font-mono font-bold whitespace-nowrap ${t.pnl != null ? pnlCl(t.pnl) : 'text-slate-600'}`}
                    title={t.pnl == null ? (t.pnlTip || undefined) : undefined}>
                    {t.pnl != null ? `${t.pnl >= 0 ? '+' : ''}${fmtK(t.pnl)}` : '—'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </Panel>
  );
};

// ---------------------------------------------------------------------------
// Action Required — environment-scoped alerts only. HALT is a global platform
// control and shows in every environment; book-specific items come only from
// the selected environment's own feeds. Full-width compact strip: one line
// when clear (no empty card), compact rows only when genuine alerts exist.
// ---------------------------------------------------------------------------
const SEV_DOT = { critical: 'bg-rose-400', warning: 'bg-slate-400', info: 'bg-slate-600' };

const ActionRequired = ({ env, items, emptyText, navigateToTab }) => {
  if (items.length === 0) {
    return (
      <div className="qr-surface px-3 py-2 flex items-baseline gap-2 flex-wrap">
        <span className="text-[11px] font-bold uppercase tracking-wide text-slate-400 flex-none">Action Required · {ENV_META[env].badge}</span>
        <span className="text-[12px] text-slate-500">{emptyText}</span>
      </div>
    );
  }
  return (
    <Panel title={`Action Required · ${ENV_META[env].badge}`} action={
      <span className="text-[10px] text-slate-500">{items.filter(i => i.sev === 'critical').length} critical · {items.filter(i => i.sev === 'warning').length} warning</span>
    }>
      <div className="divide-y divide-white/[0.05]">
        {items.map((it, i) => (
          <button key={`${it.id}-${i}`} onClick={() => it.target ? navigateToTab(it.target) : undefined}
            className="w-full flex items-center gap-2.5 px-3 py-2 text-left hover:bg-white/[0.03]"
            title={it.tip || it.impact || it.title}>
            <span className={`w-1.5 h-1.5 rounded-full flex-none ${SEV_DOT[it.sev] || SEV_DOT.info}`} />
            <span className="text-[13px] font-bold text-slate-100 whitespace-nowrap">{it.title}</span>
            {it.impact && <span className="text-[11px] text-slate-500 truncate flex-1 min-w-0">{it.impact}</span>}
            {it.date && <span className="flex-none font-mono text-[10px] text-slate-500" title={it.dateTip || undefined}>{it.date}</span>}
          </button>
        ))}
      </div>
    </Panel>
  );
};

// ---------------------------------------------------------------------------
// Top Opportunities — SIM/PAPER only (the signal universe drives those two
// books). UAT/LIVE get an explicit no-data state: no signal attribution
// exists for those environments.
// ---------------------------------------------------------------------------
const MARKET_LABEL = { US: 'US Equity', HK: 'HK Equity', CRYPTO: 'Crypto', FX: 'FX', METAL: 'Metals' };

const SCORE_TIP = 'Engine conviction score (consumption.signal_setups.potential, 0–100). '
  + 'The signal pipeline publishes no formula or component breakdown for this field — '
  + 'treat it as a heuristic ranking, not a decomposable model output.';

const Opportunities = ({ env, picks, positions, orders, navigateToTab }) => {
  const held = useMemo(() => new Set((positions || []).map(p => p.symbol)), [positions]);
  const pending = useMemo(() => new Set((orders || []).map(o => o.ticker)), [orders]);
  if (env === 'uat' || env === 'live') {
    return (
      <Panel title={`Top Opportunities · ${ENV_META[env].badge}`}>
        <NoData>No signal attribution for the {ENV_META[env].badge} book — the signal universe (consumption.signal_setups) is not mapped to this environment. SIM and PAPER show their signal-driven candidates.</NoData>
      </Panel>
    );
  }
  return (
    <Panel title={`Top Opportunities · ${ENV_META[env].badge}`} action={
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
              title={`${p.reason || ''}${p.signalDate ? ` · signal ${tsTip(p.signalDate)}` : ''}${p.price != null ? ` · px ${fmtK(p.price)}` : ''}${p.changePct != null ? ` · 1d ${fmtPct(p.changePct)}` : ''}`}>
              <span className="font-mono text-[10px] text-slate-600 w-4 flex-none">#{i + 1}</span>
              <div className="flex-none w-[96px] min-w-0">
                <div className="font-mono text-[13px] font-black text-white leading-tight truncate">{p.ticker}</div>
                <div className="text-[9px] text-slate-500 truncate">{p.name || MARKET_LABEL[p.market] || p.market}</div>
              </div>
              <div className="flex-none w-[64px]">
                <div className="flex items-baseline gap-1" title={SCORE_TIP}>
                  <span className="font-mono text-[13px] font-bold text-slate-100">{p.potential != null ? p.potential.toFixed(0) : '—'}</span>
                  <span className="text-[9px] text-slate-500">/100</span>
                </div>
                <div className="h-0.5 mt-0.5 rounded bg-white/[0.06] overflow-hidden">
                  <div className="h-full bg-slate-300" style={{ width: `${Math.max(0, Math.min(100, p.potential ?? 0))}%` }} />
                </div>
              </div>
              <div className="flex-1 min-w-0">
                <div className="text-[11px] font-bold text-slate-200 truncate">{p.strategyName || '—'}</div>
                <div className="text-[9px] text-slate-500 truncate">{p.direction || 'BUY'}{p.signalDate ? ` · ${fmtDate(p.signalDate)}` : ''}</div>
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
    </Panel>
  );
};

// ---------------------------------------------------------------------------
// Market Context — compact regime forecast (environment-agnostic market data).
// ---------------------------------------------------------------------------
const RISK_CELL = (v) => v == null ? 'bg-white/[0.04] text-slate-600'
  : v >= 60 ? 'bg-emerald-500/15 text-emerald-300'
  : v <= 40 ? 'bg-rose-500/15 text-rose-300'
  : 'bg-white/[0.06] text-slate-300';

const fmtConf = (c) => c == null ? '—' : c >= 0.99995 ? '>99.99%' : `${(c * 100).toFixed(1)}%`;

const REGIME_MEANING = {
  TREND: 'Trending tape — momentum and trend-following books should keep working; fade entries get run over.',
  MEAN_REV: 'Mean-reverting tape — moves fade; breakout entries underperform.',
  CARRY: 'Carry / range tape — low-vol grind; income-style books favoured over breakouts.',
  EVENT: 'Event-driven stress — expect gaps and vol spikes; gross exposure earns less.',
  FLAT: 'No dominant regime — weak signal environment; neutral sizing.',
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

const MarketContext = ({ fc, chg }) => (
  <Panel title="Market Context · Regime" action={
    <span className="text-[9px] text-slate-600"
      title="Current regime: consumption.market_sentiment (canonical) + HMM posterior from gold.regime_label (US, SPY/VIX features). 7-day strip: momentum_nowcast (consumption.macro_regime_7d). Environment-agnostic market data. Legend: ≥60% risk-on = emerald · ≤40% = rose · else neutral.">
      HMM daily + 7d nowcast
    </span>
  }>
    <div className="grid grid-cols-1 sm:grid-cols-2 divide-y sm:divide-y-0 sm:divide-x divide-white/[0.05]">
      <RegimeRegion region="US" fc={fc?.US} chg={chg?.US} />
      <RegimeRegion region="HK" fc={fc?.HK} chg={chg?.HK} />
    </div>
  </Panel>
);

// ---------------------------------------------------------------------------
// Per-environment normalization
// ---------------------------------------------------------------------------
const NO_ENTRY_TIPS = {
  uat: 'Not served: the IBKR portfolio payload (/api/ib/tws/uat/positions) has no entry timestamp — a UAT positions ledger with entry dates is a backend/ETL gap.',
  live: 'Not served: /api/positions/live (ibkr_snapshot) has no entry timestamp.',
};
const NO_STRAT_TIPS = {
  uat: 'Not served: the IBKR portfolio payload has no strategy attribution — the UAT fills ledger is per-fill and cannot be uniquely mapped to an aggregated position.',
  live: 'Not served: the live IBKR position snapshot has no strategy attribution.',
};

// Unified position row: { key, entryDate, entryTip, symbol, ccy, strategy,
// strategyTip, side, qty, entryPx, curPx, curTip, unreal, mv, days }
function normPositions(env, raw, stratNames) {
  if (env === 'sim') {
    return (raw || []).map(p => ({
      key: `sim-${p.id}`,
      entryDate: fmtDate(p.entry_date),
      entryTip: p.entry_date ? `entry ${fmtDate(p.entry_date)}` : null,
      symbol: p.ticker, ccy: null,
      strategy: stratNames[p.strategy_id] || p.strategy_id,
      side: (p.side || '').toUpperCase() || null,
      qty: p.quantity, entryPx: p.entry_price, curPx: p.current_price,
      curTip: p.updated_at ? `marked ${tsTip(p.updated_at)}` : null,
      unreal: p.unrealized_pnl, mv: p.market_value,
      days: daysHeld(p.entry_date),
    }));
  }
  if (env === 'paper') {
    return (raw || []).map(p => ({
      key: `paper-${p.id}`,
      entryDate: fmtDate(p.opened_at),
      entryTip: p.opened_at ? `entry ${fmtDate(p.opened_at)}` : null,
      symbol: p.ticker, ccy: null,
      strategy: stratNames[p.strategy_id] || p.strategy_id,
      side: (p.direction || '').toUpperCase() || null,
      qty: p.shares, entryPx: p.entry_price, curPx: p.current_price,
      curTip: p.price_as_of ? `price as of ${fmtDate(p.price_as_of)}` : null,
      unreal: p.unrealised_pnl,
      mv: (p.shares != null && p.current_price != null) ? p.shares * p.current_price : null,
      days: daysHeld(p.opened_at),
    }));
  }
  if (env === 'uat') {
    return (raw || []).map((p, i) => ({
      key: `uat-${p.symbol}-${p.currency}-${i}`,
      entryDate: null, entryTip: NO_ENTRY_TIPS.uat,
      symbol: p.ticker || p.symbol, ccy: p.currency || null,
      strategy: null, strategyTip: NO_STRAT_TIPS.uat,
      side: p.qty != null ? (p.qty >= 0 ? 'LONG' : 'SHORT') : null,
      qty: p.qty, entryPx: p.avg_cost, curPx: p.market_price,
      curTip: p.market_price == null ? 'no mark from gateway' : null,
      unreal: p.unrealized_pnl, mv: p.market_value,
      days: null,
    }));
  }
  // live
  return (raw || []).map((p, i) => ({
    key: `live-${p.id ?? p.ticker}-${i}`,
    entryDate: null, entryTip: NO_ENTRY_TIPS.live,
    symbol: p.ticker, ccy: null,
    strategy: null, strategyTip: NO_STRAT_TIPS.live,
    side: (p.side || '').toUpperCase() || null,
    qty: p.quantity, entryPx: p.avg_entry, curPx: p.current_price,
    unreal: p.unrealized_pnl,
    mv: (p.quantity != null && p.current_price != null) ? p.quantity * p.current_price : null,
    days: null,
  }));
}

// Unified fill row: { key, fillDate, fillTs, ticker, strategy, strategyTip,
// side, qty, price, pnl, pnlTip }
const NO_FILL_PNL_TIP = 'Per-fill realized P&L is not served for this environment (fills blotter, not round-trips).';
const NO_FILL_STRAT_TIP = 'This fills blotter has no strategy attribution.';

function normFills(env, raw, stratNames) {
  return (raw || []).map((t, i) => ({
    key: `${env}-${t.t}-${t.ticker}-${i}`,
    fillDate: fmtDate(t.t),
    fillTs: t.t,
    ticker: t.ticker,
    strategy: (env === 'sim' || env === 'paper') ? (stratNames[t.strategy_id] || t.strategy_id || null) : null,
    strategyTip: (env === 'uat' || env === 'live') ? NO_FILL_STRAT_TIP : null,
    side: (t.side || '').toUpperCase() || null,
    qty: t.qty, price: t.price,
    pnl: t.pnl ?? null,
    pnlTip: t.pnl == null ? NO_FILL_PNL_TIP : null,
  }));
}

// Unified order row: { key, orderDate, orderTs, orderTip, ticker, side, qty,
// limitOrType, strategy, status }
const NO_ORDER_DATE_TIP = 'Not served: ib.openTrades() on the UAT session carries no order submission timestamp.';

function normOrders(env, raw, stratNames) {
  if (env === 'uat') {
    return (raw || []).map((o, i) => ({
      key: `uat-${o.order_id ?? o.perm_id}-${i}`,
      orderDate: null, orderTs: null, orderTip: NO_ORDER_DATE_TIP,
      ticker: o.local_symbol || o.symbol,
      side: (o.action || '').toUpperCase() || null,
      qty: o.qty,
      limitOrType: o.order_type ?? '—',
      strategy: null,
      status: o.status,
    }));
  }
  return (raw || []).map((o, i) => ({
    key: `${env}-${o.source}-${o.ticker}-${i}`,
    orderDate: fmtDate(o.submitted_at),
    orderTs: o.submitted_at,
    ticker: o.ticker,
    side: (o.side || '').toUpperCase() || null,
    qty: o.qty,
    limitOrType: o.limit_price != null ? o.limit_price.toLocaleString() : (o.order_type || 'MKT'),
    strategy: o.strategy_name || stratNames[o.strategy_id] || o.strategy_id || o.venue || null,
    status: o.status,
  }));
}

// ---------------------------------------------------------------------------
// Opportunities loader (SIM/PAPER only) — shared fetch + normalize.
// ---------------------------------------------------------------------------
async function fetchOpportunities() {
  const [u, fams] = await Promise.all([
    api.get('/api/signals/universe?markets=US,HK,CRYPTO,FX,METAL&limit=10'),
    api.get('/api/signals/families'),
  ]);
  if (!u) return null;
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
  const dates = top3.length
    ? await api.get(`/api/command/signal-freshness?tickers=${top3.map(p => encodeURIComponent(p.ticker)).join(',')}`)
    : null;
  const dateMap = dates?.dates || {};
  return top3.map(p => ({ ...p, signalDate: dateMap[p.ticker.toUpperCase()] || null }));
}

// ---------------------------------------------------------------------------
// EnvBook — everything below the header/ticker, scoped to ONE environment.
// Mounted with key={env}: switching environments remounts this subtree so no
// stale figure from another environment can linger.
// ---------------------------------------------------------------------------
const EnvBook = ({ env, limits, navigateToTab }) => {
  const [bookOv, setBookOv] = useState(null);       // sim/paper
  const [positions, setPositions] = useState(null); // raw payload per env
  const [orders, setOrders] = useState(null);
  const [fills, setFills] = useState(null);
  const [overview, setOverview] = useState(null);   // paper/live
  const [pnlMode, setPnlMode] = useState(null);
  const [uatAcct, setUatAcct] = useState(null);     // uat
  const [stratNames, setStratNames] = useState({});
  const [oppPicks, setOppPicks] = useState([]);

  const isSim = env === 'sim', isPaper = env === 'paper', isUat = env === 'uat', isLive = env === 'live';

  // Wave 1: positions — the primary content.
  usePoll(async () => {
    let res = null;
    if (isSim) res = await api.get('/api/portfolio/positions');
    else if (isPaper) res = await api.get('/api/agents/paper/open-positions');
    else if (isUat) res = await api.get('/api/ib/tws/uat/positions');
    else res = await api.get('/api/positions/live');
    if (res) setPositions(res);
  }, 30000);

  // Wave 2: stats + chart (sim/paper), account (uat), overview (paper/live).
  usePoll(async () => {
    if (!isSim && !isPaper) return;
    const res = await api.get(`/api/execution/book-overview?book=${env}`);
    if (res) setBookOv(res);
  }, 60000, 1200);

  usePoll(async () => {
    if (!isUat) return;
    const res = await api.get('/api/ib/tws/uat/account');
    if (res) setUatAcct(res);
  }, 60000, 1200);

  usePoll(async () => {
    if (!isPaper && !isLive) return;
    const res = await api.get('/api/command/overview');
    if (res) setOverview(res);
  }, 60000, 1400);

  // Wave 3: orders + fills + mode P&L.
  usePoll(async () => {
    if (isSim) { setOrders({ unsupported: true }); return; }
    let res = null;
    if (isUat) res = await api.get('/api/ib/tws/uat/open-orders');
    else res = await api.get('/api/command/order-book');
    if (res) setOrders(res);
  }, 30000, 2600);

  usePoll(async () => {
    const res = await api.get(`/api/execution/trades?book=${env}&limit=15`);
    if (res) setFills(res);
  }, 60000, 2800);

  usePoll(async () => {
    const res = await api.get('/api/command/pnl-by-mode');
    if (res) setPnlMode(res?.modes?.[env] || null);
  }, 60000, 3000);

  // strategy_id → display name map (sim/paper rows carry strategy_id).
  useEffect(() => {
    if (!isSim && !isPaper) return undefined;
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
  }, [env, isSim, isPaper]);

  // Opportunities (SIM/PAPER books are signal-driven).
  usePoll(async () => {
    if (!isSim && !isPaper) return;
    const picks = await fetchOpportunities();
    if (picks) setOppPicks(picks);
  }, 120000, 8000);

  // ----- normalized, environment-scoped rows -----
  const posRaw = isSim || isLive ? positions?.positions
    : isPaper ? positions?.positions
    : positions?.data;
  const posRows = useMemo(() => {
    if (posRaw == null) return null;
    const rows = normPositions(env, posRaw, stratNames);
    // Newest entry first where the environment serves entry dates; books
    // without entry timestamps keep source order (noted in the header tip).
    if (isSim || isPaper) rows.sort((a, b) => (b.entryDate || '').localeCompare(a.entryDate || ''));
    return rows;
  }, [posRaw, env, stratNames, isSim, isPaper]);

  const orderRows = useMemo(() => {
    if (orders == null || orders.unsupported) return orders;
    const raw = isUat ? orders.data : (orders.orders || []).filter(o => o.source === env);
    return normOrders(env, raw, stratNames)
      .sort((a, b) => (b.orderTs || '').localeCompare(a.orderTs || ''));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [orders, env, stratNames]);

  const fillRows = useMemo(() => {
    if (fills == null) return null;
    return normFills(env, fills.data || [], stratNames)
      .sort((a, b) => (b.fillTs || '').localeCompare(a.fillTs || ''));
     
  }, [fills, env, stratNames]);

  // ----- environment-scoped alerts -----
  const actionItems = useMemo(() => {
    const items = [];
    if (limits?.global_halt) {
      items.push({ id: 'halt', sev: 'critical', title: 'Global HALT active', impact: 'Order firing halted in every environment — gold.risk_limits.global_halt', target: 'settings' });
    }
    if (isPaper) {
      const risks = overview?.strategy_risks || [];
      const attn = (overview?.attention || []).filter(a => !String(a.id || '').startsWith('live_'));
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
          target: a.target || null,
          date: fmtDate(a.created_at), dateTip: a.created_at ? tsTip(a.created_at) : null,
        });
      }
      if ((overview?.monitoring_gap || 0) > 0) {
        items.push({ id: 'gap', sev: 'warning', title: `${overview.monitoring_gap} position${overview.monitoring_gap === 1 ? '' : 's'} without monitoring`, impact: 'Open paper legs not actively monitored', target: 'execution' });
      }
    }
    if (isUat && positions && positions.connected === false) {
      items.push({ id: 'uat-down', sev: 'critical', title: 'UAT session disconnected', impact: 'No order routing or portfolio feed on the UAT session', target: 'execution' });
    }
    if (isLive) {
      const attn = (overview?.attention || []).filter(a => String(a.id || '').startsWith('live_'));
      for (const a of attn) {
        if (a.sev === 'info') continue;
        items.push({
          id: a.id, sev: a.sev || 'info', title: a.title, impact: a.impact,
          target: a.target || null,
          date: fmtDate(a.created_at), dateTip: a.created_at ? tsTip(a.created_at) : null,
        });
      }
      const health = Array.isArray(overview?.deployed_health) ? overview.deployed_health : [];
      for (const h of health) {
        items.push({ id: `health-${h.strategy_id || h.name}`, sev: h.sev || 'warning', title: h.title || `${h.name || h.strategy_id}: health`, impact: h.impact || null, target: 'strategies' });
      }
    }
    const rank = { critical: 0, warning: 1, info: 2 };
    items.sort((a, b) => (rank[a.sev] ?? 3) - (rank[b.sev] ?? 3));
    return items;
  }, [limits, overview, positions, isPaper, isUat, isLive]);

  // ----- KPI tiles per environment -----
  const halted = !!limits?.global_halt;
  const st = bookOv?.stats;
  const paperAcct = overview?.account?.books?.paper;
  const liveAcct = overview?.account?.books?.live;
  const a = uatAcct?.data;
  const kpis = [];
  if (isSim || isPaper) {
    const acct = isPaper ? paperAcct : null;
    kpis.push(
      { label: 'Today · realized', tip: `Realized P&L from today's exits (${env} book ledger)`, value: st?.today ? `${st.today.pnl >= 0 ? '+' : ''}${fmtK(st.today.pnl)}` : '—', valueCl: st?.today ? pnlCl(st.today.pnl) : 'text-slate-600', sub: st?.today ? `${st.today.trades} exit${st.today.trades === 1 ? '' : 's'} today` : 'no exits today' },
      { label: 'Cum realized P&L', tip: `All-time cumulative realized P&L, ${ENV_META[env].badge} book`, value: st?.cum_pnl != null ? `${st.cum_pnl >= 0 ? '+' : ''}${fmtK(st.cum_pnl)}` : '—', valueCl: st?.cum_pnl != null ? pnlCl(st.cum_pnl) : 'text-slate-600', sub: st ? `${st.closed_trades ?? 0} closed · WR ${st.win_rate ?? '—'}%` : null },
      isPaper
        ? { label: 'Unrealized P&L', tip: 'Open P&L, paper book (consumption.account_summary) · exposure = gross % of equity', value: acct?.open_pnl != null ? `${acct.open_pnl >= 0 ? '+' : ''}${fmtKCcy(acct.open_pnl, acct.currency || 'USD')}` : '—', valueCl: acct?.open_pnl != null ? pnlCl(acct.open_pnl) : 'text-slate-600', sub: acct?.gross_exp_pct != null ? `exposure ${acct.gross_exp_pct.toFixed(1)}% gross` : null }
        : { label: 'YTD realized', tip: 'Realized P&L since Jan 1, SIM book ledger', value: st?.ytd_pnl != null ? `${st.ytd_pnl >= 0 ? '+' : ''}${fmtK(st.ytd_pnl)}` : '—', valueCl: st?.ytd_pnl != null ? pnlCl(st.ytd_pnl) : 'text-slate-600', sub: st ? `${st.ytd_trades ?? 0} closed YTD` : null },
      { label: 'Open positions', tip: `Open positions in the ${ENV_META[env].badge} book`, value: posRows ? posRows.length : '—', valueCl: posRows ? 'text-white' : 'text-slate-600' },
      isPaper
        ? { label: 'Working orders', tip: 'Pending orders in the paper order book', value: orderRows && !orderRows.unsupported ? orderRows.length : '—' }
        : { label: 'Working orders', tip: 'The SIM book has no working-order book — synthetic fills execute at signal', value: '—', valueCl: 'text-slate-600', sub: 'no SIM order book' },
      { label: 'Risk status', tip: 'Global halt (gold.risk_limits) — applies to every environment', value: halted ? 'HALTED' : 'OK', valueCl: halted ? 'text-rose-300' : 'text-white', sub: halted ? 'global halt active' : 'halt clear' },
    );
  } else if (isUat) {
    const ccy = a?.net_liquidation_currency || a?.currency;
    const uatDown = positions && positions.connected === false;
    kpis.push(
      { label: 'Net liquidation', tip: 'UAT paper account net liquidation — /api/ib/tws/uat/account (live gateway)', value: a?.net_liquidation != null ? fmtKCcy(a.net_liquidation, ccy) : '—', sub: a?.net_liquidation_usd != null ? `≈ ${fmtKCcy(a.net_liquidation_usd, 'USD')}` : null },
      { label: 'Buying power', tip: 'UAT paper account buying power — /api/ib/tws/uat/account', value: a?.buying_power != null ? fmtKCcy(a.buying_power, a.buying_power_currency || ccy) : '—', sub: a?.available_funds != null ? `avail ${fmtKCcy(a.available_funds, a.available_funds_currency || ccy)}` : null },
      { label: 'Open positions', tip: 'UAT gateway portfolio — /api/ib/tws/uat/positions', value: posRows ? posRows.length : '—' },
      { label: 'Working orders', tip: 'Unfilled orders on the UAT session — /api/ib/tws/uat/open-orders', value: orderRows && !orderRows.unsupported ? orderRows.length : '—' },
      { label: 'Fills', tip: 'Broker-rehearsal fills ledger (gold.paper_uat_fills) — fills, not round-trips; no per-fill P&L exists', value: pnlMode?.fills ?? '—', sub: pnlMode ? `today ${pnlMode.fills_today ?? 0} · last ${pnlMode.last_fill_at ? fmtAge(pnlMode.last_fill_at) : '—'}` : null },
      { label: 'Risk status', tip: 'Global halt + UAT session state', value: halted ? 'HALTED' : uatDown ? 'SESSION DOWN' : 'OK', valueCl: halted || uatDown ? 'text-rose-300' : 'text-white', sub: halted ? 'global halt active' : 'halt clear' },
    );
  } else {
    // live
    const liveOrdersCount = orderRows && !orderRows.unsupported ? orderRows.length : null;
    kpis.push(
      { label: 'Equity', tip: 'Live account net liquidation — /api/command/overview account.books.live', value: liveAcct?.equity_native != null ? fmtKCcy(liveAcct.equity_native, liveAcct.native_currency) : '—', sub: liveAcct?.equity_usd != null ? `≈ ${fmtKCcy(liveAcct.equity_usd, 'USD')}` : null },
      { label: 'Day P&L', tip: 'Live account day P&L', value: liveAcct?.day_pnl != null ? `${liveAcct.day_pnl >= 0 ? '+' : ''}${fmtK(liveAcct.day_pnl)}` : '—', valueCl: liveAcct?.day_pnl != null ? pnlCl(liveAcct.day_pnl) : 'text-slate-600', sub: liveAcct?.day_pnl_pct != null ? fmtPct(liveAcct.day_pnl_pct) : null },
      { label: 'Open P&L', tip: 'Live unrealized P&L · exposure = gross % of equity', value: liveAcct?.open_pnl != null ? `${liveAcct.open_pnl >= 0 ? '+' : ''}${fmtK(liveAcct.open_pnl)}` : '—', valueCl: liveAcct?.open_pnl != null ? pnlCl(liveAcct.open_pnl) : 'text-slate-600', sub: liveAcct?.gross_exp_pct != null ? `exposure ${liveAcct.gross_exp_pct.toFixed(1)}% gross` : null },
      { label: 'Open positions', tip: 'Live book — /api/positions/live (ibkr_snapshot)', value: posRows ? posRows.length : '—' },
      { label: 'Working orders', tip: 'Live order book — /api/command/order-book (source=live)', value: liveOrdersCount ?? '—' },
      { label: 'Risk status', tip: 'Global halt (gold.risk_limits) — applies to every environment', value: halted ? 'HALTED' : 'OK', valueCl: halted ? 'text-rose-300' : 'text-white', sub: halted ? 'global halt active' : 'halt clear' },
    );
  }

  // ----- chart per environment -----
  const chartPanel = (() => {
    if (isSim || isPaper) {
      const curve = (bookOv?.ytd_curve || []).map(p => ({ d: p.d, equity: p.cum }));
      return (
        <Panel title={`Cumulative Realized P&L · YTD · ${ENV_META[env].badge}`} action={
          st?.win_rate != null
            ? <span className="font-mono text-[10px] text-slate-400" title="Win rate over closed trades">WR {st.win_rate}%</span>
            : null
        }>
          <EquityCurve data={curve} color="#94a3b8" height={240}
            emptyLabel={bookOv == null ? 'Loading book…' : `No realized P&L this year in the ${ENV_META[env].badge} book`} />
        </Panel>
      );
    }
    if (isUat) {
      return (
        <Panel title={`P&L Curve · ${ENV_META.uat.badge}`}>
          <NoData>No UAT round-trip P&L ledger exists — gold.paper_uat_fills is fills-only, so there is no honest curve to draw. (Round-trip UAT ledgering is a backend/ETL gap, not hidden data.)</NoData>
        </Panel>
      );
    }
    const curve = (overview?.equity_curve || []).map(p => ({ d: p.d, equity: p.equity }));
    return (
      <Panel title={`Live Equity · Last 30 Sessions · ${overview?.equity_curve_currency || ''}`.trim()} action={
        <span className="text-[9px] text-slate-600" title="consumption.account_equity_curve serves the last 30 sessions, not the calendar year">30-session window</span>
      }>
        <EquityCurve data={curve} color="#94a3b8" height={240}
          emptyLabel={overview == null ? 'Loading account…' : 'No live equity history served'} />
      </Panel>
    );
  })();

  const alertsEmpty = isSim
    ? 'none — the SIM book is virtual; only the global HALT applies.'
    : isPaper ? 'none — halt clear, no paper-book risk breaches.'
    : isUat ? 'none — halt clear, UAT session connected.'
    : 'none — halt clear, no live-book alerts.';

  // Orders + fills: side by side only when BOTH panels carry rows; otherwise
  // each follows its own content height (compact one-liners when empty).
  const hasOrders = Array.isArray(orderRows) && orderRows.length > 0;
  const hasFills = Array.isArray(fillRows) && fillRows.length > 0;

  const ordersNode = (
    <WorkingOrders env={env}
      rows={orders == null ? null : orders.unsupported ? [] : orderRows}
      unsupportedText={orders?.unsupported ? 'Not supported for SIM — synthetic fills execute at signal; the SIM ledger records closed trades only.' : null}
      asOf={orders?.as_of}
      headTip={isUat ? 'ib.openTrades() on the UAT session — unfilled/cancellable orders; no submission timestamps served' : `Order book — /api/command/order-book (source=${env})`}
      emptyText={`No working orders in the ${ENV_META[env].badge} book.`}
      navigateToTab={navigateToTab} />
  );
  const fillsNode = (
    <RecentFills env={env} rows={fillRows} asOf={fills?.as_of}
      headTip={
        isSim ? 'Closed SIM trades — gold.paper_trades_synthetic × registry SIMULATION, newest exit first'
        : isPaper ? 'Closed paper trades — gold.paper_trades_synthetic × registry PAPER, newest exit first'
        : isUat ? 'UAT blotter — gold.manual_orders book=uat. Fills, not round-trips; per-fill P&L is not served.'
        : 'Live fills — gold.trade_executions ∪ gold.manual_orders book=live, newest first'
      }
      emptyText={`No fills in the ${ENV_META[env].badge} book.`} />
  );

  return (
    <>
      {/* 1 — KPI row */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-2">
        {kpis.map((k) => <Kpi key={k.label} {...k} />)}
      </div>

      {/* 2 — Open Positions: the primary operational table, FULL WIDTH,
              directly under the KPIs. Never trapped in a side column. */}
      <OpenPositions env={env} rows={posRows}
        count={posRows ? posRows.length : null}
        asOf={positions?.as_of}
        headTip={
          isSim ? 'SIM book — consumption.portfolio_positions_current. Entry date leftmost (YYYY-MM-DD), newest first.'
          : isPaper ? 'Paper book — /api/agents/paper/open-positions. Entry date leftmost (YYYY-MM-DD), newest first. Market value = qty × last px (native ccy).'
          : isUat ? 'Live IBKR UAT paper-account portfolio (ib.portfolio()). Entry price = IBKR average cost. No entry dates served — rows keep gateway order.'
          : 'Live book — /api/positions/live (ibkr_snapshot). No entry dates served — rows keep snapshot order.'
        }
        note={isUat || isLive ? 'no entry dates served' : null}
        emptyText={
          isSim ? 'SIM book flat — 0 open positions'
          : isPaper ? 'No open positions in the paper book'
          : isUat ? (positions && positions.connected === false
              ? 'UAT session disconnected — positions unavailable (PENDING). Reconnect from Execution ▸ UAT.'
              : `UAT book flat — 0 open positions at the gateway${positions?.as_of ? ` (as of ${tsTip(positions.as_of)})` : ''}`)
          : 'Live book flat — 0 open positions in the snapshot'
        }
        navigateToTab={navigateToTab} />

      {/* 3 — Action Required: compact full-width strip (one line when clear) */}
      <ActionRequired env={env} items={actionItems} emptyText={alertsEmpty} navigateToTab={navigateToTab} />

      {/* 4 — Chart + opportunities, 65/35 */}
      <div className="grid grid-cols-1 lg:grid-cols-[minmax(0,65fr)_minmax(0,35fr)] gap-2.5">
        <div className="min-w-0">{chartPanel}</div>
        <div className="min-w-0">
          <Opportunities env={env} picks={oppPicks} positions={posRows || []} orders={Array.isArray(orderRows) ? orderRows : []} navigateToTab={navigateToTab} />
        </div>
      </div>

      {/* 5 — Working orders + recent fills: side by side only when both have
              data; otherwise full-width content-height panels/one-liners */}
      {hasOrders && hasFills ? (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-2.5 items-start">
          {ordersNode}
          {fillsNode}
        </div>
      ) : (
        <div className="space-y-2.5">
          {ordersNode}
          {fillsNode}
        </div>
      )}
    </>
  );
};

// ---------------------------------------------------------------------------
// Command page — environment-scoped command center. The environment lives in
// the URL (?env=sim|paper|uat|live) and is restored on reload; absent the
// param, the route mode seeds the default (/sim/command → SIM).
// ---------------------------------------------------------------------------
export const CommandCenter = ({ navigateToTab }) => {
  const { mode } = useParams();
  const [searchParams, setSearchParams] = useSearchParams();
  const rawEnv = (searchParams.get('env') || '').toLowerCase();
  const routeEnv = ENVS.includes((mode || '').toLowerCase()) ? mode.toLowerCase() : null;
  const env = ENVS.includes(rawEnv) ? rawEnv : (routeEnv || 'paper');
  const setEnv = (e) => {
    const next = new URLSearchParams(searchParams);
    next.set('env', e);
    setSearchParams(next, { replace: true });
  };

  const [limits, setLimits] = useState(null);
  const [sess, setSess] = useState(null); // { env, res } — env-tagged
  const [regimeFc, setRegimeFc] = useState(null);
  const [regimeChg, setRegimeChg] = useState(null);

  usePoll(async () => {
    const res = await api.get('/api/execution/limits');
    if (res) setLimits(res);
  }, 60000, 3000);

  // Header session status for the ACTIVE environment only. The fnRef pattern
  // in usePoll picks up the new env on the next tick; we also fire immediately
  // on env change via the effect below so a switch never shows stale state.
  useEffect(() => {
    let cancelled = false;
    const load = async () => {
      let res = null;
      if (env === 'uat') res = await api.get('/api/ib/tws/uat/status');
      else if (env === 'live') res = await api.get('/api/execution/gateway');
      else if (env === 'paper') res = await api.get('/api/agents/paper/system-status');
      if (!cancelled) setSess({ env, res });
    };
    load();
    const id = setInterval(load, 60000);
    return () => { cancelled = true; clearInterval(id); };
  }, [env]);

  // Market context (environment-agnostic, loads last).
  usePoll(async () => {
    const res = await api.get('/api/command/regime-forecast');
    if (res) setRegimeFc(res.markets || {});
  }, 300000, 6000);

  usePoll(async () => {
    const res = await api.get('/api/command/regime-change');
    if (res) setRegimeChg(res.regions || {});
  }, 300000, 6500);

  return (
    <div className="space-y-2.5">
      {/* 1 — Command header: environment toggle + HALT + per-env session */}
      <CommandHeader env={env} onEnv={setEnv} limits={limits} sess={sess} />
      <MarketTicker />

      {/* 2 — Environment-scoped book. key={env} remounts on switch so every
              section refetches from the selected environment and no stale
              figure from another environment can linger. */}
      <EnvBook key={env} env={env} limits={limits} navigateToTab={navigateToTab} />

      {/* 3 — Market context (environment-agnostic, bottom of page) */}
      <MarketContext fc={regimeFc} chg={regimeChg} />
    </div>
  );
};

export default CommandCenter;
