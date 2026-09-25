import React, { useState, useEffect, useMemo, useCallback, lazy, Suspense } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { LoginPage } from './components/LoginPage';
import { ExecScaffold, ExecStat } from './components/execution/ExecScaffold';
import { BookOverview } from './components/execution/BookOverview';
import { PositionsByReturn, normSimPosition } from './components/execution/BookPositions';
import { useEventStream } from './hooks/useEventStream';
import { useToasts, ToastContainer } from './components/Toasts';
import { fmt, fmtK, fmtPct, pnlCl, api, usePoll, getToken, setToken, clearToken, onUnauthorized, fetchWithTimeout } from './utils';
import { FR, FR_NAME, classifySource, useFreshness, fmtAgeSec } from './freshness';

// Tab-level code splitting: each view loads on first visit instead of shipping
// one ~470kB monolith on initial paint. Vite emits a chunk per component.
//
// lazyRetry: deploys replace hashed chunks (rsync --delete), so an app shell
// opened before a deploy can request a chunk that no longer exists — the
// dynamic import rejects and, with no error boundary, the page went BLANK
// (reported 2026-08-18: Lab → strategy Detail ↗). On import failure, force
// one full reload to fetch the fresh index + chunks; if the chunk still fails
// after that reload, render an explicit error box instead of a white screen.
const lazyRetry = (factory, name) => lazy(async () => {
  try {
    return await factory();
  } catch (err) {
    const key = `lazy-retry:${name}`;
    if (typeof sessionStorage !== 'undefined' && !sessionStorage.getItem(key)) {
      sessionStorage.setItem(key, '1');
      window.location.reload();
      return new Promise(() => {}); // suspend; the reload replaces the page
    }
    console.error(`[lazyRetry] chunk ${name} failed to load after reload`, err);
    return {
      default: () => (
        <div className="qr-surface px-3 py-8 text-center text-[11px] text-slate-500">
          This view failed to load — the app was updated while it was open.{' '}
          <button onClick={() => window.location.reload()} className="text-blue-400 hover:text-blue-300 font-bold">Refresh</button>
        </div>
      ),
    };
  }
});

const CommandCenter = lazyRetry(() => import('./components/CommandCenter').then(m => ({ default: m.CommandCenter })), 'CommandCenter');
const SettingsTab = lazyRetry(() => import('./components/SettingsTab').then(m => ({ default: m.SettingsTab })), 'SettingsTab');
const StrategyLab = lazyRetry(() => import('./components/StrategyLab').then(m => ({ default: m.StrategyLab })), 'StrategyLab');
const ResearchTab = lazyRetry(() => import('./components/ResearchTab').then(m => ({ default: m.ResearchTab })), 'ResearchTab');
const StrategyDetail = lazyRetry(() => import('./components/StrategyDetail').then(m => ({ default: m.StrategyDetail })), 'StrategyDetail');
const StrategyPerformance = lazyRetry(() => import('./components/StrategyPerformance').then(m => ({ default: m.StrategyPerformance })), 'StrategyPerformance');
const StrategyCompare = lazyRetry(() => import('./components/StrategyCompare').then(m => ({ default: m.StrategyCompare })), 'StrategyCompare');
const LiveOpsPanel = lazyRetry(() => import('./components/LiveOpsPanel').then(m => ({ default: m.LiveOpsPanel })), 'LiveOpsPanel');
const PaperStrategiesPage = lazyRetry(() => import('./components/PaperStrategiesPage'), 'PaperStrategiesPage');
const UatPanel = lazyRetry(() => import('./components/execution/UatPanel').then(m => ({ default: m.UatPanel })), 'UatPanel');
const ManualPanel = lazyRetry(() => import('./components/execution/ManualPanel').then(m => ({ default: m.ManualPanel })), 'ManualPanel');
const SignalsTab = lazyRetry(() => import('./components/SignalsTab').then(m => ({ default: m.SignalsTab })), 'SignalsTab');
const MacroTab = lazyRetry(() => import('./components/MacroTab').then(m => ({ default: m.MacroTab })), 'MacroTab');
const AnalyticsTab = lazyRetry(() => import('./components/AnalyticsTab').then(m => ({ default: m.AnalyticsTab })), 'AnalyticsTab');
const NewsTab = lazyRetry(() => import('./components/NewsTab').then(m => ({ default: m.NewsTab })), 'NewsTab');
const StrategiesWorkspace = lazyRetry(() => import('./components/StrategiesWorkspace').then(m => ({ default: m.StrategiesWorkspace })), 'StrategiesWorkspace');
const IpoTab = lazyRetry(() => import('./components/IpoTab').then(m => ({ default: m.IpoTab })), 'IpoTab');

const TabFallback = () => (
  <div className="qr-surface px-3 py-8 flex items-center justify-center gap-2 text-[11px] text-slate-500">
    <div className="w-3 h-3 border-2 border-slate-700 border-t-blue-500 rounded-full animate-spin" />
    Loading view…
  </div>
);

// =================================================================
// Iconography — minimal stroke icons sized for the dense UI (12px)
// =================================================================
const Icon = {
  Command: () => (<svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zm10 0a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zm10 0a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z" /></svg>),
  Lab: () => (<svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z" /></svg>),
  Research: () => (<svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" /></svg>),
  Performance: () => (<svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" /></svg>),
  Portfolio: () => (<svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M21 13.255A23.931 23.931 0 0112 15c-3.183 0-6.22-.62-9-1.745M16 6V4a2 2 0 00-2-2h-4a2 2 0 00-2 2v2m4 6h.01M5 20h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" /></svg>),
  Markets: () => (<svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M3.055 11H5a2 2 0 012 2v1a2 2 0 002 2 2 2 0 012 2v2.945M8 3.935V5.5A2.5 2.5 0 0010.5 8h.5a2 2 0 012 2 2 2 0 104 0 2 2 0 012-2h1.064M15 20.488V18a2 2 0 012-2h3.064M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>),
  Settings: () => (<svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.066 2.573c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.573 1.066c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.066-2.573c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" /><path strokeLinecap="round" strokeLinejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" /></svg>),
  Strategies: () => (<svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z" /></svg>),
};

// =================================================================
// Workspace Ribbon — sticky strip below the navbar showing live state
// P&L, win rate, model heartbeat, last refresh time
// =================================================================
const RibbonCell = ({ label, value, valClass = 'text-slate-200' }) => (
  <div className="flex items-baseline gap-1.5 px-3 border-r border-white/[0.05] last:border-r-0">
    <span className="qr-label">{label}</span>
    <span className={`qr-num text-[12px] font-bold ${valClass}`}>{value}</span>
  </div>
);

// Feed-health indicator — replaces the old single global "UPD" cell. Shows
// the WORST freshness state across all registered sources; click expands
// per-source detail (worst first). Palette: rose = STALE/DISCONNECTED,
// teal = LAGGING, slate = FRESH/UNKNOWN.
const FEED_CL = {
  [FR.FRESH]: { dot: 'bg-slate-500', text: 'text-slate-400' },
  [FR.LAGGING]: { dot: 'bg-teal-400', text: 'text-teal-300' },
  [FR.UNKNOWN]: { dot: 'bg-slate-600', text: 'text-slate-500' },
  [FR.STALE]: { dot: 'bg-rose-500', text: 'text-rose-400' },
  [FR.DISCONNECTED]: { dot: 'bg-rose-500', text: 'text-rose-300' },
};

const FeedHealth = () => {
  const [open, setOpen] = useState(false);
  const registry = useFreshness(60000);

  const rows = useMemo(() => {
    if (!registry) return [];
    return Object.values(registry)
      .map(r => ({ name: r.source, ...classifySource(r) }))
      .sort((a, b) => b.state - a.state || (b.ageSec ?? 1e15) - (a.ageSec ?? 1e15));
  }, [registry]);

  const worst = rows.length ? rows[0].state : FR.UNKNOWN;
  const bad = rows.filter(r => r.state >= FR.STALE).length;
  const cl = FEED_CL[worst];
  const label = rows.length === 0 ? 'FEEDS ?'
    : worst === FR.FRESH ? 'FEEDS OK'
    : `${FR_NAME[worst]}${bad > 1 ? ` ×${bad}` : ''}`;

  return (
    <div className="relative px-3 border-r border-white/[0.05] last:border-r-0">
      <button onClick={() => setOpen(o => !o)} className="flex items-baseline gap-1.5 group">
        <span className={`qr-dot ${cl.dot}`} />
        <span className={`qr-num text-[12px] font-bold ${cl.text}`}>{label}</span>
        <span className="text-[8px] text-slate-600 group-hover:text-slate-400 transition-colors">▾</span>
      </button>
      {open && (
        <>
          <div className="fixed inset-0 z-40" onClick={() => setOpen(false)} />
          <div className="absolute right-0 top-full mt-1 z-50 w-80 max-h-[60vh] overflow-y-auto bg-[#0e111a] border border-white/[0.08] rounded-lg shadow-xl py-1">
            <div className="px-3 py-1.5 border-b border-white/[0.06] flex items-center justify-between">
              <span className="qr-label">Source freshness</span>
              <span className="text-[9px] text-slate-600">{rows.length} sources · gold.v_source_freshness</span>
            </div>
            {rows.length === 0 && (
              <div className="px-3 py-3 text-[10px] text-slate-500">registry unavailable — treating all sources as UNKNOWN</div>
            )}
            {rows.map(r => (
              <div key={r.name} className="px-3 py-1 flex items-center gap-2 hover:bg-white/[0.03]" title={r.row?.last_error || r.row?.notes || ''}>
                <span className={`qr-dot flex-none ${FEED_CL[r.state].dot}`} />
                <span className="flex-1 min-w-0 text-[10px] font-mono text-slate-300 truncate">{r.name}</span>
                <span className={`text-[9px] font-mono flex-none ${FEED_CL[r.state].text}`}>
                  {r.state === FR.DISCONNECTED ? 'never' : fmtAgeSec(r.ageSec)}{r.budgetH != null ? ` / ${r.budgetH}h` : ''}
                </span>
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  );
};

const WorkspaceRibbon = ({ summary, dailyPnl, latencyMs, healthOk, onHalt, wsConnected }) => {
  const [haltConfirm, setHaltConfirm] = useState(false);
  const [haltPhrase, setHaltPhrase] = useState('');
  const [haltBusy, setHaltBusy] = useState(false);
  const [haltResult, setHaltResult] = useState(null);

  const todayPnL = dailyPnl?.[0]?.pnl ?? null;
  // null = unmeasured (backend returns null, never placeholder 0) -> render '—'
  const winRate = summary?.win_rate != null ? summary.win_rate * 100 : null;
  const totalTrades = summary?.total_trades ?? null;

  const doHalt = async () => {
    setHaltBusy(true);
    const res = await api.post('/api/execution/halt', { confirmation_phrase: haltPhrase });
    setHaltBusy(false);
    if (res?.success) {
      setHaltResult({ ok: true, msg: res.message });
      setHaltPhrase('');
      onHalt?.();
      setTimeout(() => { setHaltConfirm(false); setHaltResult(null); }, 3000);
    } else {
      setHaltResult({ ok: false, msg: 'Failed — check phrase or server' });
    }
  };

  return (
    <div className="border-b border-white/[0.05] bg-[#0a0d12]/80 backdrop-blur-xl">
      <div className="flex items-center justify-between max-w-[1800px] mx-auto h-7 overflow-x-auto no-scrollbar">
        {/* Left: compact status strip */}
        <div className="flex items-center h-full">
          <div className="flex items-center gap-1.5 px-3 border-r border-white/[0.05]">
            <span className={`qr-dot ${healthOk ? 'qr-dot-live' : 'qr-dot-down'}`} />
            <span className="qr-label">API</span>
            <span className="qr-num text-[11px] text-slate-400">{latencyMs != null ? `${latencyMs}ms` : '—'}</span>
          </div>
          <div className="flex items-center gap-1.5 px-3 border-r border-white/[0.05]">
            <span className={`qr-dot ${wsConnected ? 'qr-dot-live animate-pulse-dot' : 'qr-dot-idle'}`} />
            <span className="qr-label">WS</span>
          </div>
        </div>

        {/* Right: kill switch + P&L (no global MODE — every book carries its own mode) */}
        <div className="flex items-center h-full">
          {/* Kill switch — always visible; demotes LIVE strategies per-strategy (typed phrase) */}
          {!haltConfirm && (
            <div className="px-2 border-r border-white/[0.05]">
              <button
                onClick={() => setHaltConfirm(true)}
                className="px-2 py-0.5 rounded bg-rose-500/20 text-rose-300 ring-1 ring-rose-500/40 text-[10px] font-bold hover:bg-rose-500/30 animate-pulse-soft"
              >
                HALT
              </button>
            </div>
          )}

          <RibbonCell label="P&L D" value={todayPnL != null ? fmtK(todayPnL) : '—'} valClass={todayPnL == null ? 'text-slate-500' : todayPnL >= 0 ? 'qr-pnl-pos' : 'qr-pnl-neg'} />
          <RibbonCell label="WR"  value={winRate != null ? `${winRate.toFixed(1)}%` : '—'} valClass={winRate == null ? 'text-slate-500' : winRate >= 50 ? 'qr-pnl-pos' : 'qr-pnl-neg'} />
          <RibbonCell label="TR"  value={totalTrades != null ? totalTrades : '—'} valClass={totalTrades == null ? 'text-slate-500' : 'text-slate-200'} />
          <FeedHealth />
        </div>
      </div>

      {/* Kill-switch confirmation strip — drops down when active */}
      {haltConfirm && (
        <div className="bg-rose-950/80 border-t border-rose-500/30 px-3 py-1.5">
          <div className="flex items-center gap-3 max-w-[1800px] mx-auto">
            <span className="text-[11px] text-rose-200 font-semibold flex-shrink-0">Kill Switch — type <span className="font-mono text-rose-100 bg-rose-500/20 px-1 rounded">HALT LIVE</span> to confirm</span>
            <input
              autoFocus
              value={haltPhrase}
              onChange={(e) => setHaltPhrase(e.target.value)}
              onKeyDown={(e) => { if (e.key === 'Enter' && haltPhrase === 'HALT LIVE') doHalt(); if (e.key === 'Escape') { setHaltConfirm(false); setHaltPhrase(''); setHaltResult(null); } }}
              placeholder="HALT LIVE"
              className="px-2 py-1 bg-rose-950/60 border border-rose-500/30 rounded text-[11px] text-white w-32 placeholder-rose-800 focus:outline-none focus:border-rose-400 font-mono"
            />
            <button
              onClick={doHalt}
              disabled={haltPhrase !== 'HALT LIVE' || haltBusy}
              className={`px-3 py-1 rounded text-[10px] font-bold ${haltPhrase === 'HALT LIVE' && !haltBusy ? 'bg-rose-500 text-white hover:bg-rose-400' : 'bg-slate-800 text-slate-600 cursor-not-allowed'}`}
            >
              {haltBusy ? 'Halting…' : 'Confirm Halt'}
            </button>
            <button onClick={() => { setHaltConfirm(false); setHaltPhrase(''); setHaltResult(null); }} className="text-[10px] text-slate-400 hover:text-white">Cancel</button>
            {haltResult && (
              <span className={`text-[10px] font-semibold ${haltResult.ok ? 'text-emerald-300' : 'text-rose-300'}`}>{haltResult.msg}</span>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

// =================================================================
// Pill badge — compact colored label
// =================================================================
const Pill = ({ c, children }) => {
  const colorMap = {
    emerald: 'bg-emerald-500/15 text-emerald-400 border-emerald-500/20',
    rose: 'bg-rose-500/15 text-rose-400 border-rose-500/20',
    blue: 'bg-blue-500/15 text-blue-400 border-blue-500/20',
    amber: 'bg-amber-500/15 text-amber-400 border-amber-500/20',
    slate: 'bg-slate-500/15 text-slate-400 border-slate-500/20',
    violet: 'bg-violet-500/15 text-violet-400 border-violet-500/20',
  };
  return (
    <span className={`px-2 py-0.5 rounded-md text-[11px] font-bold border ${colorMap[c] || colorMap.slate}`}>
      {children}
    </span>
  );
};

// =================================================================
// Tiny KPI tile — denser than the previous one
// =================================================================
const KPI = ({ l, v, sub, pos, hint }) => (
  <div className="px-3 py-2 qr-surface min-w-0" title={hint}>
    <div className="qr-label truncate">{l}</div>
    <div className="qr-num text-[15px] font-bold text-white leading-tight mt-0.5">{v}</div>
    {sub && <div className={`qr-num text-[10px] mt-0.5 ${pos != null ? (pos ? 'qr-pnl-pos' : 'qr-pnl-neg') : 'text-slate-500'}`}>{sub}</div>}
  </div>
);

// Portfolio Component (SIM book) — unified Execution anatomy (2026-09-18):
// same sections as the other three books, differing only by mode + data source
// (/api/portfolio/positions). Strategy performance + full-width YTD curve come
// from the shared BookOverview in the scaffold's overview slot; positions use
// the shared PositionsByReturn split (positive / negative return). The old
// per-tab asset-class PositionTables and CLASS_META were removed — asset class
// now rides in each row's sub-line via normSimPosition.
const PortfolioTab = ({ data }) => {
  const positions = data.positions || [];
  const rows = positions.map(normSimPosition);

  const totalValue = positions.reduce((s, p) => s + (p.market_value || 0), 0);
  const totalPnL = positions.reduce((s, p) => s + (p.unrealized_pnl || p.pnl || 0), 0);

  return (
    <ExecScaffold
      mode="sim"
      book="sim"
      overview={<BookOverview book="sim" />}
      stats={<>
        <ExecStat l="Total Value" v={fmtK(totalValue)} />
        <ExecStat l="Positions" v={positions.length} />
        <ExecStat l="Unrealized P&L" v={`${totalPnL >= 0 ? '+' : ''}${fmtK(totalPnL)}`} tone={pnlCl(totalPnL)} />
      </>}
    >
      {positions.length === 0 ? (
        <div className="py-12 text-center text-slate-600 text-sm bg-slate-900/30 rounded-xl border border-white/[0.06]">
          No positions found
        </div>
      ) : (
        <PositionsByReturn rows={rows} />
      )}
    </ExecScaffold>
  );
};

// =================================================================
// Sortable table helpers
// =================================================================
const useSort = (defaultKey) => {
  const [sort, setSort] = useState({ key: defaultKey, dir: 'desc' });
  const onSort = (key) => {
    setSort(prev => ({ key, dir: prev.key === key && prev.dir === 'desc' ? 'asc' : 'desc' }));
  };
  const sorter = (a, b) => {
    const { key, dir } = sort;
    const av = a[key] ?? -Infinity;
    const bv = b[key] ?? -Infinity;
    if (typeof av === 'string' && typeof bv === 'string') {
      return dir === 'asc' ? av.localeCompare(bv) : bv.localeCompare(av);
    }
    return dir === 'asc' ? (av > bv ? 1 : -1) : (bv > av ? 1 : -1);
  };
  return { sort, onSort, sorter };
};

const SortableHeader = ({ label, sortKey, current, onSort, align = 'right' }) => {
  const active = current.key === sortKey;
  const arrow = active ? (current.dir === 'desc' ? ' ↓' : ' ↑') : '';
  return (
    <th
      onClick={() => onSort(sortKey)}
      className={`qr-label py-1.5 px-2 cursor-pointer select-none ${align === 'left' ? 'text-left' : 'text-right'}`}
    >
      {label}{arrow}
    </th>
  );
};

// =================================================================
// Performance Tab — denser comparison table
// =================================================================
const PerformanceTab = ({ data, onSelectStrategy, onCompare }) => {
  const [tf, setTf] = useState('1M');
  const [view, setView] = useState('overview');
  const [selected, setSelected] = useState(new Set());
  const { sort, onSort, sorter } = useSort('returns');

  const toggleSel = (id) => setSelected(prev => {
    const next = new Set(prev);
    if (next.has(id)) next.delete(id);
    else if (next.size < 6) next.add(id);
    return next;
  });
  const clearSel = () => setSelected(new Set());

  const strategies = useMemo(() => [...(data.strategies || [])].sort(sorter), [data.strategies, sort]);
  const bestStrategy = strategies[0];
  const liveCount = strategies.filter(s => s.live_trades > 0).length;
  const avgLiveWR = (() => {
    const live = strategies.filter(s => s.live_win_rate != null);
    return live.length > 0 ? live.reduce((a, s) => a + s.live_win_rate, 0) / live.length : null;
  })();
  const totalTrades = strategies.reduce((a, s) => a + (s.live_trades || 0), 0);

  if (view === 'analytics') {
    return (
      <div className="space-y-3">
        <div className="flex items-end justify-between">
          <div>
            <h2 className="text-sm font-bold text-white">Deep Analytics</h2>
            <p className="text-[10px] text-slate-500">Comprehensive strategy attribution & risk metrics</p>
          </div>
          <button onClick={() => setView('overview')} className="qr-btn-ghost">← Overview</button>
        </div>
        <StrategyPerformance />
      </div>
    );
  }

  return (
    <div className="space-y-3">
      <div className="flex items-end justify-between flex-wrap gap-2">
        <div>
          <h2 className="text-sm font-bold text-white">Performance</h2>
          <p className="text-[10px] text-slate-500">Backtest vs live attribution · sortable comparison</p>
        </div>
        <div className="flex items-center gap-2">
          {selected.size > 0 && (
            <>
              <span className="text-[10px] text-slate-500">{selected.size} selected</span>
              <button onClick={clearSel} className="qr-btn-ghost">Clear</button>
              <button
                onClick={() => onCompare?.(Array.from(selected))}
                disabled={selected.size < 2}
                className={`qr-btn-primary ${selected.size < 2 ? 'opacity-50 cursor-not-allowed' : ''}`}
              >Compare ({selected.size}) →</button>
            </>
          )}
          <button onClick={() => setView('analytics')} className="qr-btn-primary">Deep Analytics →</button>
          <div className="flex gap-0.5 p-0.5 rounded-md bg-slate-900/50 border border-white/[0.06]">
            {['1W', '1M', '3M', '1Y', 'ALL'].map(t =>
              <button key={t} onClick={() => setTf(t)} className={`px-2 py-1 rounded text-[10px] font-bold transition-colors ${tf === t ? 'bg-blue-500 text-white' : 'text-slate-400 hover:text-white'}`}>{t}</button>
            )}
          </div>
        </div>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
        <KPI l="Active Strategies" v={liveCount} sub={`of ${strategies.length}`} />
        <KPI l="Avg Live WR" v={avgLiveWR != null ? `${avgLiveWR.toFixed(1)}%` : '—'} pos={avgLiveWR != null && avgLiveWR >= 50} />
        <KPI l="Total Trades" v={totalTrades} sub={tf} />
        <KPI l="Best" v={bestStrategy?.strategy_name?.slice(0, 12) || '—'} sub={bestStrategy?.returns != null ? fmtPct(bestStrategy.returns) : null} pos={(bestStrategy?.returns || 0) >= 0} />
      </div>

      <div className="qr-surface overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-white/[0.06]">
                <th className="qr-label py-1.5 px-2 w-6"></th>
                <SortableHeader label="Strategy"  sortKey="strategy_name"      current={sort} onSort={onSort} align="left" />
                <SortableHeader label="Asset"     sortKey="asset_class"        current={sort} onSort={onSort} align="left" />
                <SortableHeader label="Tier"      sortKey="tier"               current={sort} onSort={onSort} />
                <SortableHeader label="BT WR"     sortKey="backtest_win_rate"  current={sort} onSort={onSort} />
                <SortableHeader label="Live WR"   sortKey="live_win_rate"      current={sort} onSort={onSort} />
                <SortableHeader label="Δ WR"      sortKey="wr_delta"           current={sort} onSort={onSort} />
                <SortableHeader label="BT PF"     sortKey="backtest_pf"        current={sort} onSort={onSort} />
                <SortableHeader label="Live PF"   sortKey="live_profit_factor" current={sort} onSort={onSort} />
                <SortableHeader label="Trades"    sortKey="live_trades"        current={sort} onSort={onSort} />
                <SortableHeader label="Returns"   sortKey="returns"            current={sort} onSort={onSort} />
              </tr>
            </thead>
            <tbody className="divide-y divide-white/[0.04]">
              {strategies.map(s => {
                const delta = s.backtest_win_rate != null && s.live_win_rate != null ? s.live_win_rate - s.backtest_win_rate : null;
                const isSel = selected.has(s.strategy_id);
                return (
                  <tr key={s.strategy_id} className="qr-tr-hover">
                    <td className="py-1 px-2 text-center" onClick={(e) => { e.stopPropagation(); toggleSel(s.strategy_id); }}>
                      <input
                        type="checkbox"
                        checked={isSel}
                        onChange={() => {}}
                        disabled={!isSel && selected.size >= 6}
                        className="w-3 h-3 accent-blue-500 cursor-pointer"
                      />
                    </td>
                    <td className="py-1 px-2 cursor-pointer" onClick={() => onSelectStrategy?.(s.strategy_id)}>
                      <div className="font-bold text-white text-[12px] truncate max-w-[200px] hover:text-blue-300">{s.strategy_name || s.strategy_id}</div>
                      {s.priority && <div className="qr-label">{s.priority}</div>}
                    </td>
                    <td className="py-1 px-2 text-[10px] text-slate-400">{s.asset_class || '—'}</td>
                    <td className="py-1 px-2 text-right">
                      <span className={`qr-chip ${s.tier?.includes('T1') ? 'qr-chip-emerald' : s.tier?.includes('T2') ? 'qr-chip-amber' : 'qr-chip-slate'}`}>{s.tier || 'T4'}</span>
                    </td>
                    <td className="py-1 px-2 qr-num text-slate-400">{s.backtest_win_rate != null ? `${s.backtest_win_rate.toFixed(0)}%` : '—'}</td>
                    <td className={`py-1 px-2 qr-num font-bold ${pnlCl((s.live_win_rate || 0) - 50)}`}>{s.live_win_rate != null ? `${s.live_win_rate.toFixed(0)}%` : '—'}</td>
                    <td className={`py-1 px-2 qr-num ${pnlCl(delta)}`}>{delta != null ? `${delta >= 0 ? '+' : ''}${delta.toFixed(0)}pp` : '—'}</td>
                    <td className="py-1 px-2 qr-num text-slate-400">{s.backtest_pf?.toFixed(2) || '—'}</td>
                    <td className={`py-1 px-2 qr-num ${pnlCl(s.live_profit_factor != null ? s.live_profit_factor - 1.5 : null)}`}>{s.live_profit_factor?.toFixed(2) || '—'}</td>
                    <td className="py-1 px-2 qr-num text-slate-300">{s.live_trades || 0}</td>
                    <td className={`py-1 px-2 qr-num font-bold ${pnlCl(s.returns)}`}>{s.returns != null ? fmtPct(s.returns) : '—'}</td>
                  </tr>
                );
              })}
              {!strategies.length && (
                <tr><td colSpan={11} className="py-8 text-center text-slate-600 text-[11px]">No deployed strategies · approve from the Strategies tab</td></tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

// =================================================================
// Main App
// =================================================================
export default function App() {
  const navigate = useNavigate();
  const location = useLocation();

  const [data, setData] = useState({ strategies: [], positions: [], paperStrategies: [], dailyPnl: [], trades: [], summary: {}, mode: 'SIMULATION' });
  const [loading, setLoading] = useState(true);
  const [ibkrConnected, setIbkrConnected] = useState(false);
  const [latencyMs, setLatencyMs] = useState(null);
  const [healthData, setHealthData] = useState(null);
  const [navOpen, setNavOpen] = useState(false);
  const [selectedStrategyId, setSelectedStrategyId] = useState(null);
  const [compareIds, setCompareIds] = useState([]);

  // Auth state — if backend has JTCML_AUTH=1, /api/auth/me returns auth_enabled=true
  const [authEnabled, setAuthEnabled] = useState(false);
  const [authChecked, setAuthChecked] = useState(false);
  const [authed, setAuthed] = useState(!!getToken());

  useEffect(() => {
    onUnauthorized(() => { clearToken(); setAuthed(false); });
    (async () => {
      try {
        const res = await fetchWithTimeout('/api/auth/me', {
          headers: getToken() ? { Authorization: `Bearer ${getToken()}` } : {},
        });
        const data = await res.json().catch(() => ({}));
        setAuthEnabled(!!data.auth_enabled);
        setAuthed(!data.auth_enabled || !!data.authenticated);
      } catch {
        setAuthEnabled(false);
        setAuthed(true);
      } finally {
        setAuthChecked(true);
      }
    })();
  }, []);

  const handleLogin = (token) => { setToken(token); setAuthed(true); };
  const handleLogout = () => { clearToken(); setAuthed(false); };

  // Toast notifications + WebSocket event stream
  const { toasts, push: pushToast, dismiss: dismissToast } = useToasts();

  const handleWsEvent = useCallback((event) => {
    const d = event.data || {};
    switch (event.type) {
      case 'kill_switch':
        pushToast(`Kill switch fired — ${d.halted || 0} strategies halted`, 'error', 10000);
        break;
      case 'mode_change':
        pushToast(`${d.name || d.strategy_id} → ${(d.to || '').replace('_TRADING', '')}`, d.is_promotion ? 'warning' : 'info');
        break;
      case 'auto_demote':
        pushToast(`Auto-demote: ${d.name || d.strategy_id} → PAPER (${(d.breaches || []).join(', ')})`, 'error', 12000);
        break;
      case 'global_mode_change':
        pushToast(`Global mode → ${(d.mode || '').replace('_TRADING', '').replace('SIMULATION', 'SIM')}`, 'info');
        break;
      case 'fill':
        pushToast(`Fill: ${d.side} ${d.quantity} ${d.ticker} @ ${d.price}`, d.side === 'BUY' ? 'success' : 'warning');
        break;
      case 'order_placed':
        pushToast(`Order: ${d.side} ${d.quantity} ${d.ticker} (${(d.execution_mode || '').replace('_TRADING','').replace('SIMULATION','SIM')})`, 'info', 4000);
        break;
      case 'signal':
        pushToast(`Signal: ${d.signal} ${d.ticker} (${d.strategy_id})`, 'info');
        break;
      default:
        break;
    }
  }, [pushToast]);

  const { connected: wsConnected } = useEventStream(handleWsEvent);

  const pathParts = location.pathname.split('/').filter(Boolean);
  const currentMode = pathParts[0] || 'sim';
  const currentTab = pathParts[1] || 'command';

  // Redirect old tab URLs to new structure (post-reorganization compatibility)
  useEffect(() => {
    const redirects = {
      'portfolio':        { tab: 'execution', sub: 'portfolio' },
      'performance':      { tab: 'strategies', sub: 'performance' },
      'agentic_research': { tab: 'research', sub: 'signals' },
      'paper_strategies': { tab: 'execution', sub: 'paper_strategies' },
    };
    const r = redirects[currentTab];
    if (r) {
      navigate(`/${currentMode}/${r.tab}`, { replace: true });
      setActiveSubTabs(prev => ({ ...prev, [r.tab]: r.sub }));
    }
  }, [currentTab, currentMode, navigate]);

  // lazyRetry guard reset: once the app has been alive for 30s the shell is
  // healthy, so clear the one-shot reload guards — a later deploy then gets
  // one fresh reload attempt instead of the static error box. NOT cleared at
  // module load: that would loop reloads while chunks are still 404.
  useEffect(() => {
    const t = setTimeout(() => {
      try {
        Object.keys(sessionStorage)
          .filter(k => k.startsWith('lazy-retry:'))
          .forEach(k => sessionStorage.removeItem(k));
      } catch { /* storage unavailable */ }
    }, 30000);
    return () => clearTimeout(t);
  }, []);

  const openStrategyDetail = (id) => {
    if (!id) return;
    setSelectedStrategyId(id);
    if (currentTab !== 'strategy_detail') navigate(`/${currentMode}/strategy_detail`);
  };
  const closeStrategyDetail = () => {
    setSelectedStrategyId(null);
    navigate(`/${currentMode}/strategies`);
  };

  const openCompare = (ids) => {
    if (!ids?.length) return;
    setCompareIds(ids);
    navigate(`/${currentMode}/compare`);
  };
  const closeCompare = () => {
    setCompareIds([]);
    navigate(`/${currentMode}/strategies`);
  };

  // =================================================================
  // 5-tab navigation — each tab has a clear intent:
  //   Command    -> platform overview & quick navigation
  //   Research   -> find trade ideas (markets, signals, agentic research)
  //   Strategies -> manage strategy lifecycle (lab, pipeline, performance)
  //   Execution  -> track positions & trades (sim, paper, paper uat, live)
  //   Settings   -> system configuration
  // =================================================================
  const navItems = useMemo(() => [
    { id: 'command',    label: 'Command',   short: 'Cmd',  IconComponent: Icon.Command,     key: '1' },
    { id: 'research',   label: 'Research',  short: 'Res',  IconComponent: Icon.Research,    key: '2' },
    { id: 'strategies', label: 'Strategies', short: 'Str',  IconComponent: Icon.Strategies,  key: '3' },
    { id: 'execution',  label: 'Execution', short: 'Exec', IconComponent: Icon.Portfolio,   key: '4' },
    { id: 'settings',   label: 'Settings',  short: 'Set',  IconComponent: Icon.Settings,    key: '5' },
  ], []);

  // Global header alert badge (2026-09-18): the Action Center moved to
  // Settings ▸ Alerts; this badge keeps the live count + worst severity
  // visible from every tab and deep-links into that section.
  const [alertBadge, setAlertBadge] = useState(null); // { total, critical, warning }
  const [settingsDeepLink, setSettingsDeepLink] = useState(null); // { section, n }
  usePoll(async () => {
    const res = await api.get('/api/command/overview');
    if (!res) return;
    const attn = res.attention || [];
    const risks = res.strategy_risks || [];
    const gap = (res.monitoring_gap || 0) > 0 ? 1 : 0;
    const crit = attn.filter(a => a.sev === 'critical').length + risks.filter(r => r.sev === 'critical').length;
    const warn = attn.filter(a => a.sev === 'warning').length + risks.filter(r => r.sev === 'warning').length;
    setAlertBadge({ total: attn.length + risks.length + gap, critical: crit, warning: warn });
  }, 60000);
  const openAlerts = () => {
    setSettingsDeepLink({ section: 'alerts', n: Date.now() });
    navigateToTab('settings');
  };

  // Sub-tab configs — each main tab has a clear intent:
  //   Research  -> find trade ideas (markets, signals, agents)
  //   Strategies -> manage lifecycle (lab, pipeline, performance)
  //   Execution -> track positions & trades (sim, paper, paper uat, live)
  // Sub-tab hotkeys: q/w/e/r for left-hand easy access
  const subTabConfig = useMemo(() => ({
    research: [
      { id: 'macro',            label: 'Macro',       short: 'Mac',  IconComponent: Icon.Markets,     key: 'q' },
      { id: 'signals',          label: 'Signals',     short: 'Sig',  IconComponent: Icon.Strategies,  key: 'w' },
      { id: 'analytics',        label: 'Analytics',   short: 'Ana',  IconComponent: Icon.Performance, key: 'e' },
      { id: 'research',         label: 'Screener',    short: 'Scr',  IconComponent: Icon.Research,    key: 'r' },
      { id: 'news',             label: 'News',        short: 'News', IconComponent: Icon.Markets,     key: 't' },
    ],
    strategies: [
      { id: 'lab',              label: 'Lab',         short: 'Lab',  IconComponent: Icon.Lab,         key: 'q' },
      { id: 'strategies',       label: 'Pipeline',    short: 'Pipe', IconComponent: Icon.Strategies,  key: 'w' },
      { id: 'performance',      label: 'Performance', short: 'Perf', IconComponent: Icon.Performance, key: 'e' },
      { id: 'ipo',              label: 'IPO',         short: 'IPO',  IconComponent: Icon.Markets,     key: 'r' },
    ],
    execution: [
      { id: 'portfolio',        label: 'Sim',       short: 'Sim', IconComponent: Icon.Portfolio,   key: 'q' },
      { id: 'paper_strategies', label: 'Paper',     short: 'Ppr', IconComponent: Icon.Portfolio,   key: 'w' },
      { id: 'uat',              label: 'UAT', short: 'UAT', IconComponent: Icon.Command,     key: 'e' },
      { id: 'live_ops',         label: 'Live',      short: 'Live', IconComponent: Icon.Command,    key: 'r' },
      { id: 'manual',           label: 'Manual',    short: 'Man', IconComponent: Icon.Portfolio,   key: 't' },
    ],
  }), []);

  const navigateToTab = (tab) => navigate(`/${currentMode}/${tab}`);

  // Sub-tab state — default to the first sub-tab of each merged section
  const [activeSubTabs, setActiveSubTabs] = useState({
    research:   'macro',
    strategies: 'lab',
    execution:  'portfolio',
  });
  const currentSubTabs = subTabConfig[currentTab];
  const activeSubTab = activeSubTabs[currentTab] || (currentSubTabs?.[0]?.id);

  const setSubTab = (tab, sub) => {
    setActiveSubTabs(prev => ({ ...prev, [tab]: sub }));
  };

  // Keyboard shortcut: 1-5 for main tabs, letter keys for sub-tabs
  useEffect(() => {
    const handler = (e) => {
      if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;
      if (e.metaKey || e.ctrlKey || e.altKey) return;
      // Main tabs 1-5
      const item = navItems.find(n => n.key === e.key);
      if (item) {
        e.preventDefault();
        navigateToTab(item.id);
        return;
      }
      // Sub-tabs for current merged tab
      const subs = subTabConfig[currentTab];
      if (subs) {
        const sub = subs.find(s => s.key === e.key);
        if (sub) {
          e.preventDefault();
          setSubTab(currentTab, sub.id);
        }
      }
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [navItems, currentTab, subTabConfig]);

  // IBKR primary-session status (paused while the browser tab is hidden).
  // The old /api/execution/global-mode poll is gone — there is no global mode;
  // every book (sim/paper/uat/live) carries its own execution state.
  usePoll(async () => {
    const st = await api.get('/api/ib/tws/status');
    if (st) setIbkrConnected(!!st.is_connected);
  }, 30000);

  // System health
  usePoll(async () => {
    const t0 = performance.now();
    const h = await api.get('/api/system/health');
    const t1 = performance.now();
    setLatencyMs(Math.round(t1 - t0));
    if (h) setHealthData(h);
  }, 15000);

  // Main data fetch
  usePoll(async () => {
    const [strategies, positions, performance, paper] = await Promise.all([
      api.get('/api/strategies/researcher'),
      api.get('/api/portfolio/positions'),
      api.get('/api/performance/strategy'),
      api.get('/api/paper-strategies')
    ]);

    setData({
      strategies: strategies?.strategies || [],
      positions: positions?.positions || positions || [],
      paperStrategies: paper?.strategies || [],
      dailyPnl: performance?.monthly_returns || [],
      monthlyReturns: performance?.monthly_returns || [],
      trades: [],
      summary: performance?.summary || {},
    });
    setLoading(false);
  }, 60000);

  // Block UI behind auth gate when enabled
  if (!authChecked) return (
    <div className="min-h-screen bg-[#05070a] flex items-center justify-center">
      <div className="w-3 h-3 border-2 border-slate-700 border-t-blue-500 rounded-full animate-spin" />
    </div>
  );
  if (authEnabled && !authed) return <LoginPage onLogin={handleLogin} />;

  if (loading) return (
    <div className="min-h-screen bg-[#05070a] flex items-center justify-center">
      <div className="text-slate-500 flex flex-col items-center gap-3">
        <div className="w-8 h-8 rounded-md bg-gradient-to-br from-blue-500 to-violet-600 flex items-center justify-center text-[10px] font-black text-white animate-pulse">JT</div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 border-2 border-slate-700 border-t-blue-500 rounded-full animate-spin" />
          <span className="text-[11px] text-slate-500">Loading workspace…</span>
        </div>
      </div>
    </div>
  );

  return (
    <div className="min-h-screen bg-[#05070a] text-white font-sans">
      {/* Top bar — compact, dense */}
      <header className="fixed top-0 left-0 right-0 z-40 border-b border-white/[0.05] bg-[#05070a]/85 backdrop-blur-xl">
        <div className="flex items-center justify-between px-3 h-10 max-w-[1800px] mx-auto">
          <div className="flex items-center gap-3">
            {/* Logo */}
            <div className="flex items-center gap-2">
              <div className="w-6 h-6 rounded-md bg-gradient-to-br from-blue-500 to-violet-600 flex items-center justify-center text-[10px] font-black shadow-md shadow-blue-500/20">JT</div>
              <div className="hidden md:block leading-none">
                <span className="text-[12px] font-bold text-white tracking-tight">JTCML</span>
                <span className="text-[9px] text-slate-500 block">Quant Workspace</span>
              </div>
            </div>

            {/* Desktop Nav — dense pill row with kbd hints */}
            <nav className="hidden md:flex gap-px p-0.5 rounded-md bg-slate-900/50 border border-white/[0.05]">
              {navItems.map(n => (
                <button
                  key={n.id}
                  onClick={() => navigateToTab(n.id)}
                  className={`flex items-center gap-1.5 px-2 py-1 rounded text-[11px] font-semibold transition-all relative ${
                    currentTab === n.id
                      ? 'bg-white/[0.08] text-white'
                      : 'text-slate-400 hover:text-slate-200 hover:bg-white/[0.04]'
                  }`}
                  title={`${n.label} (${n.key})`}
                >
                  <n.IconComponent />
                  <span>{n.label}</span>
                  <span className="hidden lg:inline qr-kbd ml-0.5">{n.key}</span>
                </button>
              ))}
            </nav>

            {/* Mobile hamburger */}
            <button onClick={() => setNavOpen(o => !o)} className="md:hidden qr-btn-ghost">≡</button>
          </div>

          <div className="flex items-center gap-2">
            {alertBadge && (
              <button
                onClick={openAlerts}
                className={`flex items-center gap-1 px-1.5 py-0.5 rounded font-mono text-[10px] font-bold transition-colors ${
                  alertBadge.critical > 0
                    ? 'text-rose-300 bg-rose-500/15 hover:bg-rose-500/25'
                    : alertBadge.total > 0
                      ? 'text-slate-300 bg-white/[0.07] hover:bg-white/[0.12]'
                      : 'text-slate-500 hover:text-slate-300'
                }`}
                title={alertBadge.total > 0
                  ? `${alertBadge.total} open alert${alertBadge.total === 1 ? '' : 's'}${alertBadge.critical ? ` (${alertBadge.critical} critical)` : ''}${alertBadge.warning ? ` (${alertBadge.warning} warning)` : ''} — Alerts · Action Center (Settings)`
                  : 'No open alerts — Alerts · Action Center (Settings)'}
              >
                ⚠ {alertBadge.total}
              </button>
            )}
            <div className="hidden sm:flex items-center gap-1.5 px-1.5 py-0.5 rounded">
              <span className={`qr-dot ${ibkrConnected ? 'qr-dot-live animate-pulse-dot' : 'qr-dot-idle'}`} />
              <span className="text-[9px] text-slate-500 uppercase tracking-wider">IBKR</span>
            </div>
            {authEnabled && (
              <button
                onClick={handleLogout}
                className="hidden sm:inline-flex qr-btn-ghost"
                title="Logout"
              >
                ⏻
              </button>
            )}
          </div>
        </div>

        {/* Mobile expanded menu */}
        {navOpen && (
          <div className="md:hidden border-t border-white/[0.05] bg-[#0a0d12] px-2 py-2 grid grid-cols-3 gap-1">
            {navItems.map(n => (
              <button
                key={n.id}
                onClick={() => { navigateToTab(n.id); setNavOpen(false); }}
                className={`flex items-center gap-1.5 px-2 py-1.5 rounded text-[11px] font-semibold ${currentTab === n.id ? 'bg-white/[0.08] text-white' : 'text-slate-400'}`}
              >
                <n.IconComponent />
                <span>{n.label}</span>
              </button>
            ))}
          </div>
        )}

        {/* Workspace ribbon */}
        <WorkspaceRibbon
          summary={data.summary}
          dailyPnl={data.dailyPnl}
          latencyMs={latencyMs}
          healthOk={healthData?.status === 'healthy'}
          wsConnected={wsConnected}
        />
      </header>

      {/* Main */}
      <main className="pt-[72px] pb-20 md:pb-4 px-3 md:px-4 max-w-[1800px] mx-auto">
        {/* Sub-tab bar for merged tabs */}
        {currentSubTabs && (
          <div className="flex items-center gap-1 mb-3 p-1 rounded-md bg-slate-900/50 border border-white/[0.05] w-fit max-w-full overflow-x-auto" style={{ scrollbarWidth: 'none' }}>
            {currentSubTabs.map(sub => (
              <button
                key={sub.id}
                onClick={() => setSubTab(currentTab, sub.id)}
                className={`flex items-center gap-1.5 px-2.5 py-1 rounded text-[11px] font-semibold transition-all shrink-0 whitespace-nowrap ${
                  activeSubTab === sub.id
                    ? 'bg-blue-500/20 text-blue-300 ring-1 ring-blue-500/30'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-white/[0.04]'
                }`}
                title={`${sub.label} (${sub.key})`}
              >
                <sub.IconComponent />
                <span>{sub.label}</span>
                <span className="hidden lg:inline qr-kbd ml-0.5">{sub.key}</span>
              </button>
            ))}
          </div>
        )}

        <Suspense fallback={<TabFallback />}>
        {currentTab === 'command'          && <CommandCenter data={data} navigateToTab={navigateToTab} onSelectStrategy={openStrategyDetail} />}
        {currentTab === 'settings'         && <SettingsTab healthData={healthData} latencyMs={latencyMs} wsConnected={wsConnected} initialSection={settingsDeepLink} navigateToTab={navigateToTab} onSelectStrategy={openStrategyDetail} />}

        {/* Research tab — find trade ideas */}
        {currentTab === 'research' && (
          <>
            {activeSubTab === 'macro'            && <MacroTab />}
            {activeSubTab === 'signals'          && <SignalsTab onOpenStrategy={openStrategyDetail} />}
            {activeSubTab === 'analytics'        && <AnalyticsTab />}
            {activeSubTab === 'research'         && <ResearchTab key="research-tab" onOpenStrategy={openStrategyDetail} />}
            {activeSubTab === 'news'             && <NewsTab />}
          </>
        )}

        {/* Strategies tab — manage lifecycle */}
        {currentTab === 'strategies' && (
          <>
            {activeSubTab === 'lab'              && <StrategyLab onOpen={openStrategyDetail} />}
            {activeSubTab === 'strategies'       && <StrategiesWorkspace sub="pipeline" onOpen={openStrategyDetail} />}
            {activeSubTab === 'performance'      && <StrategiesWorkspace sub="performance" onOpen={openStrategyDetail} />}
            {activeSubTab === 'ipo'              && <IpoTab onOpen={openStrategyDetail} />}
          </>
        )}

        {/* Execution tab — track positions & trades */}
        {currentTab === 'execution' && (
          <>
            {activeSubTab === 'portfolio'        && <PortfolioTab data={data} />}
            {activeSubTab === 'paper_strategies' && <PaperStrategiesPage />}
            {activeSubTab === 'uat'              && <UatPanel />}
            {activeSubTab === 'live_ops'         && <LiveOpsPanel onSelectStrategy={openStrategyDetail} />}
            {activeSubTab === 'manual'           && <ManualPanel />}
          </>
        )}

        {currentTab === 'strategy_detail'  && (
          selectedStrategyId
            ? <StrategyDetail key={selectedStrategyId} strategyId={selectedStrategyId} onBack={closeStrategyDetail} />
            : <div className="qr-surface p-6 text-center text-[11px] text-slate-500">No strategy selected · pick one from <button onClick={() => { navigateToTab('strategies'); setSubTab('strategies', 'performance'); }} className="text-blue-400 hover:text-blue-300 underline">Performance</button></div>
        )}
        {currentTab === 'compare'          && (
          compareIds.length >= 2
            ? <StrategyCompare strategyIds={compareIds} onClose={closeCompare} onSelectStrategy={openStrategyDetail} />
            : <div className="qr-surface p-6 text-center text-[11px] text-slate-500">No strategies selected · pick 2–6 from <button onClick={() => { navigateToTab('strategies'); setSubTab('strategies', 'performance'); }} className="text-blue-400 hover:text-blue-300 underline">Performance</button> and click Compare</div>
        )}
        </Suspense>
      </main>

      {/* Mobile bottom nav */}
      <nav className="bottom-nav md:hidden">
        <div className="flex items-center justify-around px-1 py-1">
          {navItems.slice(0, 5).map(n => (
            <button key={n.id} onClick={() => navigateToTab(n.id)}
              className={`flex flex-col items-center gap-0.5 px-1.5 py-1 rounded min-w-0 transition-colors ${
                currentTab === n.id ? 'text-blue-400' : 'text-slate-500'
              }`}
            >
              <n.IconComponent />
              <span className="text-[8px] font-medium truncate">{n.short}</span>
            </button>
          ))}
        </div>
      </nav>

      {/* Toast notifications — floating bottom-right */}
      <ToastContainer toasts={toasts} dismiss={dismissToast} />
    </div>
  );
}
