import React, { useMemo, useState, useEffect, useRef } from 'react';
import { useParams, useSearchParams } from 'react-router-dom';
import { api, usePoll, fmtK, fmtKCcy, fmtPct, fmtAge, pnlCl, marketClock, marketStatus } from '../utils';

// Command home — decision-first trading operations dashboard (redesign
// 2026-11-10, v5). Information hierarchy is strict: STATE -> ACTION -> RISK ->
// EVIDENCE. One status bar answers "which environment, is it healthy, is the
// data current"; one alert strip answers "what needs me now"; one KPI row
// answers "am I making or losing money"; everything below is evidence, in
// operational order: positions, orders/fills, P&L curve, then opportunities
// and market context as compact, visually subordinate modules.
//
// A SIM | PAPER | UAT | LIVE toggle in the status bar scopes the ENTIRE page,
// persisted in the URL (?env=). EnvBook mounts with key={env} so switching
// remounts and refetches every section from the selected environment only —
// never mixed, never relabeled; unsupported data renders an explicit no-data
// state (UAT: no round-trip P&L ledger -> no chart; SIM: no order book;
// UAT/LIVE: no signal-universe opportunities).
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
// Typography scale (no microscopic text): panel titles 12px semibold
// uppercase, table headers 11px, body/table 13px, KPI values 26px tabular
// mono. Spacing rides an 8px rhythm (8/16/24). Restrained palette: colour
// carries meaning only — rose = critical severity, emerald/rose text =
// signed P&L (pnlCl), blue = links, everything else neutral slate/white.

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
// separate DAYS HELD column (and the header freshness readout).
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
  <button onClick={onClick} className="text-[12px] font-semibold text-blue-400 hover:text-blue-300">{children}</button>
);

const Panel = ({ title, action, children, className = '' }) => (
  <div className={`qr-surface overflow-hidden ${className}`}>
    <div className="flex items-center justify-between gap-3 px-4 py-2.5 border-b border-white/[0.05]">
      <span className="text-[12px] font-bold uppercase tracking-wider text-slate-300 flex items-center gap-2">{title}</span>
      {action}
    </div>
    {children}
  </div>
);

// Environment badge chip used inside panel titles.
const EnvChip = ({ env }) => (
  <span className="qr-chip qr-chip-slate" title={ENV_META[env].tip}>{ENV_META[env].badge}</span>
);

// Honest no-data state: an environment that lacks supported data says so
// explicitly — another environment's data is never relabeled into the gap.
const NoData = ({ children }) => (
  <div className="px-4 py-3 text-[13px] text-slate-500">{children}</div>
);

// One-line compact strip for empty/unsupported secondary modules.
const InlineNote = ({ title, children }) => (
  <div className="qr-surface px-4 py-2.5 flex items-baseline gap-2.5 flex-wrap">
    <span className="text-[12px] font-bold uppercase tracking-wider text-slate-400 flex-none">{title}</span>
    <span className="text-[13px] text-slate-500">{children}</span>
  </div>
);

// Small as-of tag sourced from the payload's own timestamp.
const AsOf = ({ ts }) => {
  if (!ts) return null;
  return <span className="font-mono text-[11px] text-slate-600 normal-case tracking-normal" title={`Payload as_of ${tsTip(ts)}`}>upd {fmtAge(ts)}</span>;
};

// ---------------------------------------------------------------------------
// 1. STATE — status bar. One bar answers: which environment, is trading
// halted, is the feed/session alive, how fresh is the data. Market clocks
// live here (right edge) instead of a separate ticker band.
// ---------------------------------------------------------------------------
const EnvToggle = ({ env, onChange }) => (
  <span className="flex items-center rounded-md overflow-hidden border border-white/[0.10] flex-none" role="tablist" aria-label="Environment">
    {ENVS.map(e => (
      <button key={e} role="tab" aria-selected={env === e} onClick={() => onChange(e)} title={ENV_META[e].tip}
        className={`px-3.5 py-1.5 text-[13px] font-bold font-mono transition-colors ${env === e ? 'bg-white/[0.10] text-white' : 'text-slate-500 hover:text-slate-300'}`}>
        {ENV_META[e].badge}
      </button>
    ))}
  </span>
);

const StatusItem = ({ label, children, tip }) => (
  <span className="flex items-center gap-2 flex-none" title={tip}>
    <span className="text-[11px] uppercase tracking-wider text-slate-500">{label}</span>
    {children}
  </span>
);

const StatusDivider = () => <span className="w-px h-5 bg-white/[0.08] flex-none" />;

// Per-environment session status for the status bar. `sess` is env-tagged so
// a stale payload from a previous environment is never shown.
const SessionItem = ({ env, sess }) => {
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
  // live
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

const Clock = ({ label, t, open }) => (
  <span className="flex items-center gap-1.5" title={open ? 'session open' : 'session closed'}>
    <span className={`w-1.5 h-1.5 rounded-full ${open ? 'bg-emerald-400' : 'bg-slate-600'}`} />
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
    <span className="flex items-center gap-3 text-[11px] flex-none">
      <Clock label="HKT" t={c.hkt} open={s.hk} />
      <Clock label="LON" t={c.lon} open={s.lon} />
      <Clock label="NYC" t={c.nyc} open={s.nyc} />
    </span>
  );
};

const StatusBar = ({ env, onEnv, limits, sess, dataAsOf }) => {
  const halted = !!limits?.global_halt;
  return (
    <div className="qr-surface px-4 py-3">
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

// ---------------------------------------------------------------------------
// 2. ACTION — alert strip directly under the status bar. Clear state is one
// muted line; alerts render as a banner with a rose left border when any
// item is critical. Environment-scoped alerts only; HALT is global and
// shows in every environment.
// ---------------------------------------------------------------------------
const SEV_DOT = { critical: 'bg-rose-400', warning: 'bg-slate-400', info: 'bg-slate-600' };

const AlertStrip = ({ env, items, emptyText, navigateToTab }) => {
  if (items.length === 0) {
    return (
      <div className="qr-surface px-4 py-2.5 flex items-baseline gap-2.5 flex-wrap">
        <span className="text-[12px] font-bold uppercase tracking-wider text-slate-400 flex-none">Action Required · {ENV_META[env].badge}</span>
        <span className="text-[13px] text-slate-500">{emptyText}</span>
      </div>
    );
  }
  const nCrit = items.filter(i => i.sev === 'critical').length;
  return (
    <div className={`qr-surface overflow-hidden border-l-2 ${nCrit > 0 ? 'border-l-rose-500/70' : 'border-l-white/[0.15]'}`}>
      <div className="flex items-center justify-between gap-3 px-4 py-2.5 border-b border-white/[0.05]">
        <span className={`text-[12px] font-bold uppercase tracking-wider ${nCrit > 0 ? 'text-rose-300' : 'text-slate-300'}`}>
          Action Required · {ENV_META[env].badge}
        </span>
        <span className="text-[11px] text-slate-500">{nCrit} critical · {items.filter(i => i.sev === 'warning').length} warning</span>
      </div>
      <div className="divide-y divide-white/[0.05]">
        {items.map((it, i) => (
          <button key={`${it.id}-${i}`} onClick={() => it.target ? navigateToTab(it.target) : undefined}
            className="w-full flex items-center gap-3 px-4 py-2 text-left hover:bg-white/[0.03]"
            title={it.tip || it.impact || it.title}>
            <span className={`w-2 h-2 rounded-full flex-none ${SEV_DOT[it.sev] || SEV_DOT.info}`} />
            <span className="text-[13px] font-bold text-slate-100 whitespace-nowrap">{it.title}</span>
            {it.impact && <span className="text-[12px] text-slate-500 truncate flex-1 min-w-0">{it.impact}</span>}
            {it.date && <span className="flex-none font-mono text-[11px] text-slate-500" title={it.dateTip || undefined}>{it.date}</span>}
          </button>
        ))}
      </div>
    </div>
  );
};

// ---------------------------------------------------------------------------
// 3. RISK — one KPI row. 4–6 essential, non-duplicated metrics; today vs
// cumulative and realized vs unrealized are separated by label and sub-line.
// Consistent units, explicit signs, tabular numerals.
// ---------------------------------------------------------------------------
const Kpi = ({ label, value, valueCl = 'text-white', sub, tip }) => (
  <div className="qr-surface px-4 py-3.5 flex flex-col justify-center min-w-0" title={tip}>
    <div className="text-[11px] font-semibold uppercase tracking-wider text-slate-500 truncate">{label}</div>
    <div className={`font-mono text-[26px] font-bold leading-none mt-2 truncate ${valueCl}`} style={{ fontVariantNumeric: 'tabular-nums' }}>{value}</div>
    {sub != null && <div className="text-[11px] text-slate-500 leading-snug mt-2">{sub}</div>}
  </div>
);

// ---------------------------------------------------------------------------
// 4. EVIDENCE — Open Positions: the primary operational table. Full page
// width, ENTRY DATE leftmost (YYYY-MM-DD, newest first where served), sticky
// header, 36–40px rows at 13px, right-aligned tabular numerals. The first
// POSITIONS_PAGE rows render inline (no trapped scroll box); a Show-all
// control reveals the rest. A totals footer sums unrealized P&L and market
// value per currency (mixed-currency books show one segment per currency).
// ---------------------------------------------------------------------------
const POSITIONS_PAGE = 18;

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

// Sum a numeric field per currency; null ccy falls back to the book default.
const sumByCcy = (rows, field, defCcy) => {
  const acc = new Map();
  let skipped = 0;
  for (const r of rows) {
    const v = r[field];
    if (v == null || isNaN(v)) { skipped += 1; continue; }
    const c = r.ccy || defCcy;
    acc.set(c, (acc.get(c) || 0) + v);
  }
  return { sums: [...acc.entries()], skipped };
};

const fmtCcySum = (v, ccy) => `${v >= 0 ? '+' : ''}${fmtKCcy(v, ccy)}`;

const PositionsTotals = ({ rows, defCcy }) => {
  const unreal = sumByCcy(rows, 'unreal', defCcy);
  const mv = sumByCcy(rows, 'mv', defCcy);
  if (unreal.sums.length === 0 && mv.sums.length === 0) return null;
  return (
    <div className="flex items-center gap-x-5 gap-y-1 flex-wrap px-4 py-2.5 border-t border-white/[0.06] bg-white/[0.02] text-[12px]">
      <span className="text-slate-500">{rows.length} open</span>
      {unreal.sums.length > 0 && (
        <span className="flex items-center gap-1.5" title={unreal.skipped > 0 ? `${unreal.skipped} position(s) without a mark excluded` : 'Sum of unrealized P&L over open positions'}>
          <span className="text-slate-500 uppercase tracking-wider text-[11px]">Unrealized Σ</span>
          {unreal.sums.map(([c, v]) => (
            <span key={c} className={`font-mono font-bold ${pnlCl(v)}`}>{fmtCcySum(v, c)}</span>
          ))}
        </span>
      )}
      {mv.sums.length > 0 && (
        <span className="flex items-center gap-1.5" title={mv.skipped > 0 ? `${mv.skipped} position(s) without a market value excluded` : 'Sum of market value over open positions'}>
          <span className="text-slate-500 uppercase tracking-wider text-[11px]">Market value Σ</span>
          {mv.sums.map(([c, v]) => (
            <span key={c} className="font-mono text-slate-200">{fmtKCcy(v, c)}</span>
          ))}
        </span>
      )}
    </div>
  );
};

const OpenPositions = ({ env, rows, count, asOf, headTip, note, emptyText, defCcy, navigateToTab }) => {
  const [showAll, setShowAll] = useState(false);
  const visible = rows == null ? null : (showAll ? rows : rows.slice(0, POSITIONS_PAGE));
  const hidden = rows != null ? rows.length - (visible?.length ?? 0) : 0;
  return (
    <Panel title={<>Open Positions <EnvChip env={env} /></>} action={
      <span className="flex items-center gap-3">
        <span className="text-[11px] text-slate-500" title={headTip}>{count != null ? `${count} open` : ''}{note ? ` · ${note}` : ''}</span>
        <AsOf ts={asOf} />
        <LinkBtn onClick={() => navigateToTab('execution')}>Execution →</LinkBtn>
      </span>
    }>
      {rows == null ? (
        <NoData>Loading…</NoData>
      ) : rows.length > 0 ? (
        <div className="overflow-x-auto">
          <table className="w-full min-w-[980px]">
            <thead className="sticky top-0 z-10">
              <tr className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider">
                {POSITIONS_HEAD.map(h => (
                  <th key={h.k} className={`bg-[#0a0d12] ${h.align === 'right' ? 'text-right' : 'text-left'} ${h.k === 'entry' ? 'px-4' : 'px-3'} py-2 ${h.k === 'days' ? 'pr-4' : ''}`}
                    title={h.k === 'entry' || h.k === 'days' ? 'Absolute entry date (YYYY-MM-DD), newest first where the environment serves entry dates' : undefined}>
                    {h.label}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {visible.map((p, i) => (
                <tr key={p.key || `${p.symbol}-${i}`} className="border-t border-white/[0.05] text-[13px] leading-5 hover:bg-white/[0.02]">
                  <td className="px-4 py-2 font-mono text-slate-300 whitespace-nowrap" title={p.entryTip || undefined}>
                    {p.entryDate ?? '—'}
                  </td>
                  <td className="px-3 py-2 font-mono font-bold text-white whitespace-nowrap">
                    {p.symbol}
                    {p.ccy && <span className="text-[11px] font-normal text-slate-500 ml-1.5">{p.ccy}</span>}
                  </td>
                  <td className="px-3 py-2 text-[12px] text-slate-400 max-w-[260px] truncate" title={p.strategyTip || p.strategy || undefined}>
                    {p.strategy ?? '—'}
                  </td>
                  <td className="px-3 py-2 font-mono font-bold text-slate-300">{p.side ?? '—'}</td>
                  <td className="px-3 py-2 text-right font-mono text-slate-200" style={{ fontVariantNumeric: 'tabular-nums' }}>{p.qty != null ? Math.abs(p.qty).toLocaleString() : '—'}</td>
                  <td className="px-3 py-2 text-right font-mono text-slate-300" style={{ fontVariantNumeric: 'tabular-nums' }}>{p.entryPx != null ? p.entryPx.toLocaleString(undefined, { maximumFractionDigits: 2 }) : '—'}</td>
                  <td className="px-3 py-2 text-right font-mono text-slate-300" style={{ fontVariantNumeric: 'tabular-nums' }} title={p.curTip || undefined}>
                    {p.curPx != null ? p.curPx.toLocaleString(undefined, { maximumFractionDigits: 2 }) : '—'}
                  </td>
                  <td className={`px-3 py-2 text-right font-mono font-bold whitespace-nowrap ${p.unreal != null ? pnlCl(p.unreal) : 'text-slate-600'}`} style={{ fontVariantNumeric: 'tabular-nums' }}>
                    {p.unreal != null ? `${p.unreal >= 0 ? '+' : ''}${fmtK(p.unreal)}` : '—'}
                  </td>
                  <td className="px-3 py-2 text-right font-mono text-slate-300" style={{ fontVariantNumeric: 'tabular-nums' }}>{p.mv != null ? fmtK(p.mv) : '—'}</td>
                  <td className="px-3 pr-4 py-2 text-right font-mono text-[12px] text-slate-500" title={p.entryTip || undefined}>
                    {p.days != null ? p.days : '—'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          <PositionsTotals rows={rows} defCcy={defCcy} />
          {hidden > 0 && (
            <button onClick={() => setShowAll(true)}
              className="w-full px-4 py-2.5 text-[13px] font-semibold text-blue-400 hover:text-blue-300 text-center border-t border-white/[0.05]">
              Show all {rows.length} positions ({hidden} more) ↓
            </button>
          )}
          {showAll && rows.length > POSITIONS_PAGE && (
            <button onClick={() => setShowAll(false)}
              className="w-full px-4 py-2.5 text-[13px] font-semibold text-slate-500 hover:text-slate-300 text-center border-t border-white/[0.05]">
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
const WorkingOrders = ({ env, rows, asOf, headTip, emptyText, unsupportedText, navigateToTab }) => {
  if (unsupportedText) {
    return <InlineNote title={<>Working Orders · {ENV_META[env].badge}</>}>{unsupportedText}</InlineNote>;
  }
  if (rows != null && rows.length === 0) {
    return <InlineNote title={<>Working Orders · {ENV_META[env].badge}</>}>{emptyText}</InlineNote>;
  }
  return (
    <Panel title={<>Working Orders <EnvChip env={env} /></>} action={
      <span className="flex items-center gap-3">
        <span className="text-[11px] text-slate-500" title={headTip}>{rows != null ? `${rows.length} working` : ''}</span>
        <AsOf ts={asOf} />
        <LinkBtn onClick={() => navigateToTab('execution')}>Orders →</LinkBtn>
      </span>
    }>
      {rows == null ? (
        <NoData>Loading…</NoData>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full min-w-[640px]">
            <thead>
              <tr className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider bg-white/[0.02]">
                <th className="text-left px-4 py-2" title="Absolute order date (YYYY-MM-DD), newest first where served">Order date</th>
                <th className="text-left px-3 py-2">Ticker</th>
                <th className="text-left px-3 py-2">Side</th>
                <th className="text-right px-3 py-2">Qty</th>
                <th className="text-right px-3 py-2">Limit / type</th>
                <th className="text-left px-3 py-2">Strategy</th>
                <th className="text-left px-4 py-2">Status</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((o, i) => (
                <tr key={o.key || `${o.ticker}-${i}`} className="border-t border-white/[0.05] text-[13px] leading-5 hover:bg-white/[0.02]">
                  <td className="px-4 py-2 font-mono text-slate-300 whitespace-nowrap" title={o.orderTs ? tsTip(o.orderTs) : o.orderTip || undefined}>
                    {o.orderDate ?? '—'}
                  </td>
                  <td className="px-3 py-2 font-mono font-bold text-white">{o.ticker}</td>
                  <td className={`px-3 py-2 font-mono font-bold ${o.side === 'BUY' ? 'text-emerald-400' : o.side === 'SELL' || o.side === 'CLOSE' ? 'text-rose-400' : 'text-slate-400'}`}>{o.side ?? '—'}</td>
                  <td className="px-3 py-2 text-right font-mono text-slate-200" style={{ fontVariantNumeric: 'tabular-nums' }}>{o.qty != null ? o.qty.toLocaleString() : '—'}</td>
                  <td className="px-3 py-2 text-right font-mono text-slate-300">{o.limitOrType ?? '—'}</td>
                  <td className="px-3 py-2 text-[12px] text-slate-400 max-w-[200px] truncate" title={o.strategy || undefined}>{o.strategy ?? '—'}</td>
                  <td className="px-4 py-2"><span className="text-[11px] px-1.5 py-0.5 rounded bg-white/[0.06] text-slate-300">{o.status ?? '—'}</span></td>
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
    return <InlineNote title={<>Recent Fills · {ENV_META[env].badge}</>}>{emptyText}</InlineNote>;
  }
  return (
    <Panel title={<>Recent Fills <EnvChip env={env} /></>} action={
      <span className="flex items-center gap-3">
        <span className="text-[11px] text-slate-500" title={headTip}>{rows != null ? `${rows.length} shown` : ''}</span>
        <AsOf ts={asOf} />
      </span>
    }>
      {rows == null ? (
        <NoData>Loading…</NoData>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full min-w-[700px]">
            <thead>
              <tr className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider bg-white/[0.02]">
                <th className="text-left px-4 py-2" title="Absolute fill date (YYYY-MM-DD), newest first; exact UTC timestamp in row tooltip">Fill date</th>
                <th className="text-left px-3 py-2">Ticker</th>
                <th className="text-left px-3 py-2">Strategy</th>
                <th className="text-left px-3 py-2">Side</th>
                <th className="text-right px-3 py-2">Qty</th>
                <th className="text-right px-3 py-2">Price</th>
                <th className="text-right px-4 py-2">Realized P&L</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((t, i) => (
                <tr key={t.key || `${t.fillTs}-${t.ticker}-${i}`} className="border-t border-white/[0.05] text-[13px] leading-5 hover:bg-white/[0.02]" title={t.fillTs ? `filled ${tsTip(t.fillTs)}` : undefined}>
                  <td className="px-4 py-2 font-mono text-slate-300 whitespace-nowrap">{t.fillDate ?? '—'}</td>
                  <td className="px-3 py-2 font-mono font-bold text-white">{t.ticker}</td>
                  <td className="px-3 py-2 text-[12px] text-slate-400 max-w-[220px] truncate" title={t.strategyTip || t.strategy || undefined}>{t.strategy ?? '—'}</td>
                  <td className={`px-3 py-2 font-mono font-bold ${t.side === 'BUY' || t.side === 'LONG' ? 'text-emerald-400' : t.side === 'SELL' || t.side === 'SHORT' ? 'text-rose-400' : 'text-slate-400'}`}>{t.side ?? '—'}</td>
                  <td className="px-3 py-2 text-right font-mono text-slate-200" style={{ fontVariantNumeric: 'tabular-nums' }}>{t.qty != null ? t.qty.toLocaleString() : '—'}</td>
                  <td className="px-3 py-2 text-right font-mono text-slate-300" style={{ fontVariantNumeric: 'tabular-nums' }}>{t.price != null ? t.price.toLocaleString(undefined, { maximumFractionDigits: 2 }) : '—'}</td>
                  <td className={`px-4 py-2 text-right font-mono font-bold whitespace-nowrap ${t.pnl != null ? pnlCl(t.pnl) : 'text-slate-600'}`} style={{ fontVariantNumeric: 'tabular-nums' }}
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
// P&L curve — secondary evidence. ~240px tall, y-grid + value ticks, month
// axis, zero line when the range crosses zero, and a hover crosshair with an
// exact date/value tooltip. Width tracks the container via ResizeObserver.
// ---------------------------------------------------------------------------
function EquityCurve({ data, color, height = 240, emptyLabel = 'No history yet' }) {
  const ref = useRef(null);
  const [width, setWidth] = useState(600);
  const [hover, setHover] = useState(null); // index into data
  useEffect(() => {
    if (!ref.current) return undefined;
    const ro = new ResizeObserver((entries) => {
      setWidth(Math.max(320, Math.round(entries[0].contentRect.width)));
    });
    ro.observe(ref.current);
    return () => ro.disconnect();
  }, []);

  if (!data || data.length < 2) {
    return <div className="flex items-center justify-center text-[13px] text-slate-600" style={{ height: 120 }}>{emptyLabel}</div>;
  }
  const margin = { left: 52, right: 12, top: 10, bottom: 24 };
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
  const crossesZero = min < 0 && max > 0;
  const monthTicks = data.map((d, i) => ({ i, label: d.d, date: new Date(d.d + 'T00:00:00') })).filter((d, i, arr) => {
    if (i === 0) return true;
    const prev = arr[i - 1].date;
    return d.date.getMonth() !== prev.getMonth() || d.date.getFullYear() !== prev.getFullYear();
  });

  const onMove = (e) => {
    const r = ref.current?.getBoundingClientRect();
    if (!r || r.width === 0) return;
    const px = (e.clientX - r.left) * (w / r.width);
    const frac = (px - margin.left) / plotW;
    const i = Math.round(frac * (values.length - 1));
    setHover(Math.max(0, Math.min(values.length - 1, i)));
  };

  const hd = hover != null ? data[hover] : null;

  return (
    <div ref={ref} className="relative" onMouseMove={onMove} onMouseLeave={() => setHover(null)}>
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
        {crossesZero && (
          <line x1={margin.left} y1={y(0)} x2={margin.left + plotW} y2={y(0)} stroke="rgba(255,255,255,0.30)" strokeWidth="1" strokeDasharray="4 3" vectorEffect="non-scaling-stroke" />
        )}
        <polygon points={area} fill={`url(#${id})`} />
        <polyline points={line} fill="none" stroke={color} strokeWidth="2" strokeLinejoin="round" strokeLinecap="round" vectorEffect="non-scaling-stroke" />
        <line x1={margin.left} y1={margin.top} x2={margin.left} y2={margin.top + plotH} stroke="rgba(255,255,255,0.15)" strokeWidth="1" vectorEffect="non-scaling-stroke" />
        <line x1={margin.left} y1={margin.top + plotH} x2={margin.left + plotW} y2={margin.top + plotH} stroke="rgba(255,255,255,0.15)" strokeWidth="1" vectorEffect="non-scaling-stroke" />
        {yTicks.map((v, i) => (
          <text key={i} x={margin.left - 6} y={y(v) + 3.5} textAnchor="end" fill="rgba(148,163,184,0.85)" fontSize="10" fontFamily="ui-monospace, SFMono-Regular, Menlo, monospace">
            {fmtK(v)}
          </text>
        ))}
        {monthTicks.map((t, i) => (
          <text key={i} x={x(t.i)} y={h - 8} textAnchor="middle" fill="rgba(148,163,184,0.85)" fontSize="10" fontFamily="ui-monospace, SFMono-Regular, Menlo, monospace">
            {t.date.toLocaleDateString('en-US', { month: 'short' })}
          </text>
        ))}
        {hover != null && (
          <>
            <line x1={x(hover)} y1={margin.top} x2={x(hover)} y2={margin.top + plotH} stroke="rgba(255,255,255,0.25)" strokeWidth="1" vectorEffect="non-scaling-stroke" />
            <circle cx={x(hover)} cy={y(values[hover])} r="3.5" fill={color} stroke="#0a0d12" strokeWidth="1.5" />
          </>
        )}
      </svg>
      {hd && (
        <div className="absolute pointer-events-none rounded bg-[#0a0d12] border border-white/[0.12] px-2 py-1 text-[11px] font-mono whitespace-nowrap"
          style={{ left: Math.min(Math.max(x(hover), 60), w - 110), top: 2, transform: 'translateX(-50%)' }}>
          <span className="text-slate-500">{hd.d}</span>
          <span className={`ml-2 font-bold ${pnlCl(hd.equity)}`}>{hd.equity >= 0 ? '+' : ''}{fmtK(hd.equity)}</span>
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Top Opportunities — SIM/PAPER only (the signal universe drives those two
// books). Compact and visually subordinate to the operational tables.
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
      <InlineNote title={<>Top Opportunities · {ENV_META[env].badge}</>}>
        No signal attribution for the {ENV_META[env].badge} book — the signal universe (consumption.signal_setups) is not mapped to this environment. SIM and PAPER show their signal-driven candidates.
      </InlineNote>
    );
  }
  return (
    <Panel title={<>Top Opportunities <EnvChip env={env} /></>} action={
      <span className="flex items-center gap-2.5">
        <span className="text-[10px] text-slate-600" title={SCORE_TIP}>best per class · heuristic score ⓘ</span>
        <LinkBtn onClick={() => navigateToTab('research')}>Signals →</LinkBtn>
      </span>
    }>
      <div className="divide-y divide-white/[0.05]">
        {picks.map((p, i) => {
          const isHeld = held.has(p.ticker);
          const hasPending = pending.has(p.ticker);
          return (
            <div key={`${p.market}-${p.ticker}`} className="flex items-center gap-3 px-4 py-2"
              title={`${p.reason || ''}${p.signalDate ? ` · signal ${tsTip(p.signalDate)}` : ''}${p.price != null ? ` · px ${fmtK(p.price)}` : ''}${p.changePct != null ? ` · 1d ${fmtPct(p.changePct)}` : ''}`}>
              <span className="font-mono text-[11px] text-slate-600 w-5 flex-none">#{i + 1}</span>
              <div className="flex-none w-[110px] min-w-0">
                <div className="font-mono text-[13px] font-black text-white leading-tight truncate">{p.ticker}</div>
                <div className="text-[11px] text-slate-500 truncate">{p.name || MARKET_LABEL[p.market] || p.market}</div>
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
                <div className="text-[11px] text-slate-500 truncate">{p.direction || 'BUY'}{p.signalDate ? ` · ${fmtDate(p.signalDate)}` : ''}</div>
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
// Market Context — compact, visually subordinate: one index strip (quotes +
// sentiment) and one regime strip (HMM daily + 7d nowcast). Fetches its own
// market overview so the operational sections above stay untouched.
// ---------------------------------------------------------------------------
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
    <div className="px-4 py-2.5">
      <div className="flex items-baseline gap-2.5 flex-wrap">
        <span className="font-mono text-[11px] font-black text-white flex-none">{region}</span>
        <span className="text-[13px] font-bold text-slate-100" title={`${chg?.source || ''}${regime ? `\n${REGIME_MEANING[regime] || ''}` : ''}`}>
          {regime ?? '—'}
        </span>
        <span className="font-mono text-[10px] text-slate-400"
          title={region === 'US' ? 'HMM posterior probability of the current regime (gold.regime_label)' : 'No regime posterior for HK — the HMM is US-scope (SPY/VIX features)'}>
          P {fmtConf(chg?.confidence)}
        </span>
        <span className="text-[10px] font-mono text-slate-500 truncate" title={chg?.source || ''}>{changeLine ?? '—'}</span>
      </div>
      {days.length > 0 && (
        <div className="grid grid-cols-7 gap-1 mt-2">
          {days.map((d, i) => (
            <div key={d.date || i}
              className={`rounded px-1 py-1 text-center ${RISK_CELL(d.risk_on)}`}
              title={`${d.date ?? ''} · ${d.risk_on != null ? `${d.risk_on.toFixed(1)}%` : '—'} risk-on — momentum_nowcast (consumption.macro_regime_7d)${allSame ? ' · flat carry-forward nowcast' : ''}`}>
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

const MarketContext = ({ fc, chg }) => {
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
    <Panel title="Market Context" action={
      <span className="text-[10px] text-slate-600"
        title="Environment-agnostic market data. Indices: /api/markets/overview. Regime: consumption.market_sentiment (canonical) + HMM posterior from gold.regime_label (US, SPY/VIX features). 7-day strip: momentum_nowcast (consumption.macro_regime_7d). Legend: ≥60% risk-on = emerald · ≤40% = rose · else neutral.">
        secondary · HMM daily + 7d nowcast
      </span>
    }>
      <div className="flex items-center gap-4 px-4 py-2.5 overflow-x-auto text-[12px] text-slate-500 border-b border-white/[0.05]">
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
    </Panel>
  );
};

// ---------------------------------------------------------------------------
// Per-environment normalization
// ---------------------------------------------------------------------------
const NO_ENTRY_TIPS = {
  uat: 'Not served: the IBKR portfolio payload (/api/ib/tws/uat/positions) has no entry timestamp — a UAT positions ledger with entry dates is a backend/ETL gap.',
  live: 'No attribution for this row — ledger-fallback position or no matching fills in the DUP825942 fills ledger (gold.paper_uat_fills, horizon 2026-08-25).',
};
const NO_STRAT_TIPS = {
  uat: 'Not served: the IBKR portfolio payload has no strategy attribution — the UAT fills ledger is per-fill and cannot be uniquely mapped to an aggregated position.',
  live: 'Manual/untagged fill — no strategy attribution across the open lots (never fabricated).',
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
    entryDate: fmtDate(p.entry_date),
    entryTip: p.entry_date
      ? `entry ${fmtDate(p.entry_date)}${p.qty_reconciled === false ? ' · unreconciled ledger' : ''}`
      : NO_ENTRY_TIPS.live,
    symbol: p.ticker, ccy: null,
    strategy: p.strategy_id ? (stratNames[p.strategy_id] || p.strategy_name || p.strategy_id) : null,
    strategyTip: p.strategy_id ? null : NO_STRAT_TIPS.live,
    side: (p.side || '').toUpperCase() || null,
    qty: p.quantity, entryPx: p.avg_entry, curPx: p.current_price,
    unreal: p.unrealized_pnl,
    mv: (p.quantity != null && p.current_price != null) ? p.quantity * p.current_price : null,
    days: daysHeld(p.entry_date),
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
// EnvBook — everything below the status bar, scoped to ONE environment.
// Mounted with key={env}: switching environments remounts this subtree so no
// stale figure from another environment can linger.
// ---------------------------------------------------------------------------
const EnvBook = ({ env, limits, onDataAsOf, navigateToTab }) => {
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
    if (res) {
      setPositions(res);
      // Feed the status bar freshness readout: prefer the payload's own
      // as_of; fall back to the client-side fetch time (labeled in tooltip).
      // Staleness (>1h) is computed here in the poll callback — impure
      // clock reads are not allowed during render (react-hooks/purity).
      const ts = res.as_of || new Date().toISOString();
      const t = new Date(String(ts).includes('T') ? String(ts) : `${String(ts).replace(' ', 'T')}Z`);
      onDataAsOf?.({ ts, stale: isNaN(t) ? false : (Date.now() - t.getTime()) > 3600000 });
    }
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
  const simUnreal = useMemo(() => {
    if (!isSim || !posRows) return null;
    let sum = 0, n = 0;
    for (const p of posRows) if (p.unreal != null && !isNaN(p.unreal)) { sum += p.unreal; n += 1; }
    return n > 0 ? sum : null;
  }, [isSim, posRows]);
  const uatUnreal = useMemo(() => {
    if (!isUat || !posRows) return null;
    const acc = new Map();
    for (const p of posRows) {
      if (p.unreal == null || isNaN(p.unreal)) continue;
      const c = p.ccy || 'USD';
      acc.set(c, (acc.get(c) || 0) + p.unreal);
    }
    return acc.size > 0 ? [...acc.entries()] : null;
  }, [isUat, posRows]);

  const kpis = [];
  if (isSim || isPaper) {
    const acct = isPaper ? paperAcct : null;
    kpis.push(
      { label: 'Today · realized', tip: `Realized P&L from today's exits, ${ENV_META[env].badge} book ledger (USD)`, value: st?.today ? `${st.today.pnl >= 0 ? '+' : ''}${fmtK(st.today.pnl)}` : '—', valueCl: st?.today ? pnlCl(st.today.pnl) : 'text-slate-600', sub: st?.today ? `${st.today.trades} exit${st.today.trades === 1 ? '' : 's'} today` : 'no exits today' },
      { label: 'Cumulative · realized', tip: `All-time cumulative realized P&L, ${ENV_META[env].badge} book (USD)`, value: st?.cum_pnl != null ? `${st.cum_pnl >= 0 ? '+' : ''}${fmtK(st.cum_pnl)}` : '—', valueCl: st?.cum_pnl != null ? pnlCl(st.cum_pnl) : 'text-slate-600', sub: st ? `${st.closed_trades ?? 0} closed · WR ${st.win_rate ?? '—'}% · YTD ${st.ytd_pnl != null ? `${st.ytd_pnl >= 0 ? '+' : ''}${fmtK(st.ytd_pnl)}` : '—'}` : null },
      isPaper
        ? { label: 'Unrealized · open', tip: 'Open P&L, paper book (consumption.account_summary) · exposure = gross % of equity', value: acct?.open_pnl != null ? `${acct.open_pnl >= 0 ? '+' : ''}${fmtKCcy(acct.open_pnl, acct.currency || 'USD')}` : '—', valueCl: acct?.open_pnl != null ? pnlCl(acct.open_pnl) : 'text-slate-600', sub: acct?.gross_exp_pct != null ? `exposure ${acct.gross_exp_pct.toFixed(1)}% gross` : null }
        : { label: 'Unrealized · open', tip: 'Open P&L, SIM book — sum over open positions (consumption.portfolio_positions_current, USD)', value: simUnreal != null ? `${simUnreal >= 0 ? '+' : ''}${fmtK(simUnreal)}` : '—', valueCl: simUnreal != null ? pnlCl(simUnreal) : 'text-slate-600', sub: posRows ? `over ${posRows.length} open` : null },
      { label: 'Open positions', tip: `Open positions in the ${ENV_META[env].badge} book`, value: posRows ? posRows.length : '—', valueCl: posRows ? 'text-white' : 'text-slate-600', sub: `${ENV_META[env].badge} book` },
      isPaper
        ? { label: 'Working orders', tip: 'Pending orders in the paper order book', value: orderRows && !orderRows.unsupported ? orderRows.length : '—', sub: 'pending execution' }
        : { label: 'Working orders', tip: 'The SIM book has no working-order book — synthetic fills execute at signal', value: '—', valueCl: 'text-slate-600', sub: 'no SIM order book' },
      { label: 'Risk status', tip: 'Global halt (gold.risk_limits) — applies to every environment', value: halted ? 'HALTED' : 'OK', valueCl: halted ? 'text-rose-300' : 'text-white', sub: halted ? 'global halt active' : 'halt clear' },
    );
  } else if (isUat) {
    const ccy = a?.net_liquidation_currency || a?.currency;
    const uatDown = positions && positions.connected === false;
    kpis.push(
      { label: 'Net liquidation', tip: 'UAT paper account net liquidation — /api/ib/tws/uat/account (live gateway)', value: a?.net_liquidation != null ? fmtKCcy(a.net_liquidation, ccy) : '—', sub: a?.net_liquidation_usd != null ? `≈ ${fmtKCcy(a.net_liquidation_usd, 'USD')}` : null },
      { label: 'Buying power', tip: 'UAT paper account buying power — /api/ib/tws/uat/account', value: a?.buying_power != null ? fmtKCcy(a.buying_power, a.buying_power_currency || ccy) : '—', sub: a?.available_funds != null ? `avail ${fmtKCcy(a.available_funds, a.available_funds_currency || ccy)}` : null },
      { label: 'Unrealized · open', tip: 'Sum of unrealized P&L over the UAT gateway portfolio (per-currency segments)', value: uatUnreal ? uatUnreal.map(([c, v]) => `${v >= 0 ? '+' : ''}${fmtKCcy(v, c)}`).join(' · ') : '—', valueCl: uatUnreal ? pnlCl(uatUnreal.reduce((s, [, v]) => s + v, 0)) : 'text-slate-600', sub: posRows?.length > 0 ? `over ${posRows.length} open` : null },
      { label: 'Open positions', tip: 'UAT gateway portfolio — /api/ib/tws/uat/positions', value: posRows ? posRows.length : '—', sub: 'gateway portfolio' },
      { label: 'Working orders', tip: 'Unfilled orders on the UAT session — /api/ib/tws/uat/open-orders', value: orderRows && !orderRows.unsupported ? orderRows.length : '—', sub: pnlMode ? `fills ${pnlMode.fills ?? 0} · today ${pnlMode.fills_today ?? 0}` : 'pending execution' },
      { label: 'Risk status', tip: 'Global halt + UAT session state', value: halted ? 'HALTED' : uatDown ? 'SESSION DOWN' : 'OK', valueCl: halted || uatDown ? 'text-rose-300' : 'text-white', sub: halted ? 'global halt active' : 'halt clear' },
    );
  } else {
    // live
    const liveOrdersCount = orderRows && !orderRows.unsupported ? orderRows.length : null;
    kpis.push(
      { label: 'Equity', tip: 'Live account net liquidation — /api/command/overview account.books.live', value: liveAcct?.equity_native != null ? fmtKCcy(liveAcct.equity_native, liveAcct.native_currency) : '—', sub: liveAcct?.equity_usd != null ? `≈ ${fmtKCcy(liveAcct.equity_usd, 'USD')}` : null },
      { label: 'Today · day P&L', tip: 'Live account day P&L', value: liveAcct?.day_pnl != null ? `${liveAcct.day_pnl >= 0 ? '+' : ''}${fmtK(liveAcct.day_pnl)}` : '—', valueCl: liveAcct?.day_pnl != null ? pnlCl(liveAcct.day_pnl) : 'text-slate-600', sub: liveAcct?.day_pnl_pct != null ? fmtPct(liveAcct.day_pnl_pct) : null },
      { label: 'Unrealized · open', tip: 'Live unrealized P&L · gross/net exposure = % of equity (backend fields; see qr_etl ticket for the gross-vs-attention inconsistency)', value: liveAcct?.open_pnl != null ? `${liveAcct.open_pnl >= 0 ? '+' : ''}${fmtK(liveAcct.open_pnl)}` : '—', valueCl: liveAcct?.open_pnl != null ? pnlCl(liveAcct.open_pnl) : 'text-slate-600', sub: liveAcct?.gross_exp_pct != null ? `gross ${liveAcct.gross_exp_pct.toFixed(1)}%${liveAcct?.net_exp_pct != null ? ` · net ${liveAcct.net_exp_pct.toFixed(1)}%` : ''} of equity` : null },
      { label: 'Open positions', tip: 'Live book — /api/positions/live (ibkr_snapshot)', value: posRows ? posRows.length : '—', sub: 'ibkr snapshot' },
      { label: 'Working orders', tip: 'Live order book — /api/command/order-book (source=live)', value: liveOrdersCount ?? '—', sub: 'pending execution' },
      { label: 'Risk status', tip: 'Global halt (gold.risk_limits) — applies to every environment', value: halted ? 'HALTED' : 'OK', valueCl: halted ? 'text-rose-300' : 'text-white', sub: halted ? 'global halt active' : 'halt clear' },
    );
  }

  // ----- chart per environment (secondary evidence, ~240px) -----
  const chartPanel = (() => {
    if (isSim || isPaper) {
      const curve = (bookOv?.ytd_curve || []).map(p => ({ d: p.d, equity: p.cum }));
      return (
        <Panel title={<>Cumulative Realized P&L · YTD <EnvChip env={env} /></>} action={
          st?.win_rate != null
            ? <span className="font-mono text-[11px] text-slate-400" title="Win rate over closed trades">WR {st.win_rate}%</span>
            : null
        }>
          <EquityCurve data={curve} color="#94a3b8" height={240}
            emptyLabel={bookOv == null ? 'Loading book…' : `No realized P&L this year in the ${ENV_META[env].badge} book`} />
        </Panel>
      );
    }
    if (isUat) {
      return (
        <Panel title={<>P&L Curve <EnvChip env="uat" /></>}>
          <NoData>No UAT round-trip P&L ledger exists — gold.paper_uat_fills is fills-only, so there is no honest curve to draw. (Round-trip UAT ledgering is a backend/ETL gap, not hidden data.)</NoData>
        </Panel>
      );
    }
    const curve = (overview?.equity_curve || []).map(p => ({ d: p.d, equity: p.equity }));
    return (
      <Panel title={<>Live Equity · Last 30 Sessions{overview?.equity_curve_currency ? ` · ${overview.equity_curve_currency}` : ''}</>} action={
        <span className="text-[10px] text-slate-600" title="consumption.account_equity_curve serves the last 30 sessions, not the calendar year">30-session window</span>
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

  // Default currency for position totals. SIM/PAPER books are USD; UAT rows
  // carry their own currency; LIVE position P&L is reported in the
  // instrument currency — the live book is US instruments, and the account
  // open_pnl KPI matches the USD sum, so USD is the consistent label.
  const defCcy = 'USD';

  return (
    <>
      {/* 2 — ACTION: alert strip (one line when clear) */}
      <AlertStrip env={env} items={actionItems} emptyText={alertsEmpty} navigateToTab={navigateToTab} />

      {/* 3 — RISK: one KPI row, 6 essential metrics */}
      <div className="grid grid-cols-2 sm:grid-cols-3 xl:grid-cols-6 gap-3">
        {kpis.map((k) => <Kpi key={k.label} {...k} />)}
      </div>

      {/* 4 — EVIDENCE: Open Positions, the primary operational table,
              full width directly under the KPIs. */}
      <OpenPositions env={env} rows={posRows}
        count={posRows ? posRows.length : null}
        asOf={positions?.as_of}
        headTip={
          isSim ? 'SIM book — consumption.portfolio_positions_current. Entry date leftmost (YYYY-MM-DD), newest first.'
          : isPaper ? 'Paper book — /api/agents/paper/open-positions. Entry date leftmost (YYYY-MM-DD), newest first. Market value = qty × last px (native ccy).'
          : isUat ? 'Live IBKR UAT paper-account portfolio (ib.portfolio()). Entry price = IBKR average cost. No entry dates served — rows keep gateway order.'
          : 'Live book — /api/positions/live (ibkr_snapshot). Entry = earliest FIFO open lot from the DUP825942 fills ledger (gold.paper_uat_fills), as-of the snapshot row.'
        }
        note={isUat ? 'no entry dates served' : null}
        emptyText={
          isSim ? 'SIM book flat — 0 open positions'
          : isPaper ? 'No open positions in the paper book'
          : isUat ? (positions && positions.connected === false
              ? 'UAT session disconnected — positions unavailable (PENDING). Reconnect from Execution ▸ UAT.'
              : `UAT book flat — 0 open positions at the gateway${positions?.as_of ? ` (as of ${tsTip(positions.as_of)})` : ''}`)
          : 'Live book flat — 0 open positions in the snapshot'
        }
        defCcy={defCcy}
        navigateToTab={navigateToTab} />

      {/* 5 — Working orders + recent fills: side by side only when both have
              data; otherwise full-width content-height panels/one-liners */}
      {hasOrders && hasFills ? (
        <div className="grid grid-cols-1 xl:grid-cols-2 gap-4 items-start">
          {ordersNode}
          {fillsNode}
        </div>
      ) : (
        <div className="space-y-4">
          {ordersNode}
          {fillsNode}
        </div>
      )}

      {/* 6 — Secondary evidence: P&L curve (65%) + top opportunities (35%) */}
      <div className="grid grid-cols-1 lg:grid-cols-[minmax(0,65fr)_minmax(0,35fr)] gap-4 items-start">
        <div className="min-w-0">{chartPanel}</div>
        <div className="min-w-0">
          <Opportunities env={env} picks={oppPicks} positions={posRows || []} orders={Array.isArray(orderRows) ? orderRows : []} navigateToTab={navigateToTab} />
        </div>
      </div>
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
  const [dataAsOf, setDataAsOf] = useState(null);
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

  // Market context (environment-agnostic, bottom of page).
  usePoll(async () => {
    const res = await api.get('/api/command/regime-forecast');
    if (res) setRegimeFc(res.markets || {});
  }, 300000, 6000);

  usePoll(async () => {
    const res = await api.get('/api/command/regime-change');
    if (res) setRegimeChg(res.regions || {});
  }, 300000, 6500);

  return (
    <div className="space-y-4">
      {/* 1 — STATE: status bar (env toggle, HALT, session, freshness, clocks) */}
      <StatusBar env={env} onEnv={setEnv} limits={limits} sess={sess} dataAsOf={dataAsOf} />

      {/* 2..6 — environment-scoped book. key={env} remounts on switch so every
                 section refetches from the selected environment and no stale
                 figure from another environment can linger. */}
      <EnvBook key={env} env={env} limits={limits} onDataAsOf={setDataAsOf} navigateToTab={navigateToTab} />

      {/* 7 — Market context (environment-agnostic, bottom of page) */}
      <MarketContext fc={regimeFc} chg={regimeChg} />
    </div>
  );
};

export default CommandCenter;
