import React, { useState, useEffect, useMemo, useRef } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { MarketsTab } from './components/MarketsTab';
import { SettingsTab } from './components/SettingsTab';
import { StrategyLab } from './components/StrategyLab';
import { ResearchTab } from './components/ResearchTab';
import { GlobalExecutionToggle } from './components/GlobalExecutionToggle';
import { GoldenStrategies } from './components/GoldenStrategies';
import { StrategyPerformance } from './components/StrategyPerformance';
import { AgenticResearch } from './components/AgenticResearch';
import { StrategyDetail } from './components/StrategyDetail';
import { fmt, fmtK, fmtPct, pnlCl, api, marketClock, marketStatus, fmtAge } from './utils';

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
  Agents: () => (<svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" /></svg>),
};

// =================================================================
// Workspace Ribbon — sticky strip below the navbar showing live state
// market clocks, P&L, win rate, model heartbeat, last refresh time
// =================================================================
const WorkspaceRibbon = ({ summary, dailyPnl, lastRefresh, latencyMs, mode, healthOk }) => {
  const [clocks, setClocks] = useState(marketClock());
  const [statuses, setStatuses] = useState(marketStatus());

  useEffect(() => {
    const id = setInterval(() => {
      setClocks(marketClock());
      setStatuses(marketStatus());
    }, 1000);
    return () => clearInterval(id);
  }, []);

  const todayPnL = dailyPnl?.[0]?.pnl ?? null;
  const winRate = (summary?.win_rate || 0) * 100;
  const totalTrades = summary?.total_trades || 0;

  const Cell = ({ label, value, valClass = 'text-slate-200', extra }) => (
    <div className="flex items-baseline gap-1.5 px-3 border-r border-white/[0.05] last:border-r-0">
      <span className="qr-label">{label}</span>
      <span className={`qr-num text-[12px] font-bold ${valClass}`}>{value}</span>
      {extra}
    </div>
  );

  const Clock = ({ city, time, open }) => (
    <div className="flex items-center gap-1.5 px-3 border-r border-white/[0.05]">
      <span className={`qr-dot ${open ? 'qr-dot-live animate-pulse-dot' : 'qr-dot-idle'}`} />
      <span className="qr-label">{city}</span>
      <span className="qr-num text-[11px] text-slate-300 font-semibold">{time}</span>
    </div>
  );

  return (
    <div className="border-b border-white/[0.05] bg-[#0a0d12]/80 backdrop-blur-xl">
      <div className="flex items-center justify-between max-w-[1800px] mx-auto h-7 overflow-x-auto no-scrollbar">
        {/* Left: market clocks + system health */}
        <div className="flex items-center h-full">
          <Clock city="HK"  time={clocks.hkt} open={statuses.hk}  />
          <Clock city="LON" time={clocks.lon} open={statuses.lon} />
          <Clock city="NYC" time={clocks.nyc} open={statuses.nyc} />
          <div className="flex items-center gap-1.5 px-3 border-r border-white/[0.05]">
            <span className={`qr-dot ${healthOk ? 'qr-dot-live' : 'qr-dot-down'}`} />
            <span className="qr-label">API</span>
            <span className="qr-num text-[11px] text-slate-400">{latencyMs != null ? `${latencyMs}ms` : '—'}</span>
          </div>
        </div>

        {/* Right: live P&L + summary */}
        <div className="flex items-center h-full">
          <Cell
            label="MODE"
            value={mode === 'LIVE_TRADING' ? 'LIVE' : mode === 'PAPER_TRADING' ? 'PAPER' : 'SIM'}
            valClass={mode === 'LIVE_TRADING' ? 'text-rose-400' : mode === 'PAPER_TRADING' ? 'text-amber-400' : 'text-blue-400'}
          />
          <Cell label="P&L D" value={todayPnL != null ? fmtK(todayPnL) : '—'} valClass={todayPnL == null ? 'text-slate-500' : todayPnL >= 0 ? 'qr-pnl-pos' : 'qr-pnl-neg'} />
          <Cell label="WR"  value={`${winRate.toFixed(1)}%`} valClass={winRate >= 50 ? 'qr-pnl-pos' : 'qr-pnl-neg'} />
          <Cell label="TR"  value={totalTrades} />
          <Cell label="UPD" value={fmtAge(lastRefresh)} valClass="text-slate-400" />
        </div>
      </div>
    </div>
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

// =================================================================
// Sortable column header
// =================================================================
const SortableHeader = ({ label, sortKey, current, onSort, align = 'right' }) => {
  const active = current?.key === sortKey;
  const asc = active && current?.dir === 'asc';
  return (
    <th
      onClick={() => onSort(sortKey)}
      className={`py-1.5 px-2 cursor-pointer select-none qr-label hover:text-slate-200 ${align === 'left' ? 'text-left' : 'text-right'}`}
    >
      <span className={active ? 'text-blue-300' : ''}>{label}</span>
      {active && <span className="ml-0.5 text-[8px]">{asc ? '▲' : '▼'}</span>}
    </th>
  );
};

const useSort = (initialKey, initialDir = 'desc') => {
  const [sort, setSort] = useState({ key: initialKey, dir: initialDir });
  const onSort = (key) => setSort(s => s.key === key ? { ...s, dir: s.dir === 'asc' ? 'desc' : 'asc' } : { key, dir: 'desc' });
  const sorter = (a, b) => {
    const av = a[sort.key], bv = b[sort.key];
    if (av == null && bv == null) return 0;
    if (av == null) return 1;
    if (bv == null) return -1;
    if (typeof av === 'string') return sort.dir === 'asc' ? av.localeCompare(bv) : bv.localeCompare(av);
    return sort.dir === 'asc' ? av - bv : bv - av;
  };
  return { sort, onSort, sorter };
};

// =================================================================
// Portfolio Tab — quant-dense table with sortable columns
// =================================================================
const PortfolioTab = ({ data }) => {
  const [search, setSearch] = useState('');
  const { sort, onSort, sorter } = useSort('market_value');

  const positions = useMemo(() => {
    const filtered = data.positions.filter(p => !search || p.ticker?.toLowerCase().includes(search.toLowerCase()));
    return [...filtered].sort(sorter);
  }, [data.positions, search, sort]);

  const totalValue = positions.reduce((s, p) => s + (p.market_value || 0), 0);
  const totalPnL = positions.reduce((s, p) => s + (p.pnl || 0), 0);
  const longCount = positions.filter(p => p.side === 'LONG').length;
  const shortCount = positions.filter(p => p.side === 'SHORT').length;

  return (
    <div className="space-y-3">
      <div className="flex items-end justify-between flex-wrap gap-2">
        <div>
          <h2 className="text-sm font-bold text-white tracking-tight">Portfolio</h2>
          <p className="text-[10px] text-slate-500">Live positions · sortable · P&L tracking</p>
        </div>
        <div className="flex items-center gap-2">
          <input
            value={search}
            onChange={e => setSearch(e.target.value)}
            placeholder="Filter ticker…"
            className="px-2.5 py-1 bg-slate-900/60 border border-white/[0.08] rounded-md text-[11px] text-white w-36 placeholder-slate-600 focus:outline-none focus:border-blue-500/50 font-mono"
          />
        </div>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-5 gap-2">
        <KPI l="Total Value"   v={fmtK(totalValue)} />
        <KPI l="Net P&L"       v={fmtK(totalPnL)} pos={totalPnL >= 0} sub={totalValue > 0 ? `${((totalPnL/totalValue)*100).toFixed(2)}%` : null} />
        <KPI l="Positions"     v={positions.length} sub={`${longCount}L / ${shortCount}S`} />
        <KPI l="Long Exposure" v={fmtK(positions.filter(p => p.side === 'LONG').reduce((s,p)=>s+(p.market_value||0),0))} />
        <KPI l="Short Exposure"v={fmtK(positions.filter(p => p.side === 'SHORT').reduce((s,p)=>s+(p.market_value||0),0))} />
      </div>

      <div className="qr-surface overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full hidden md:table">
            <thead>
              <tr className="border-b border-white/[0.06]">
                <SortableHeader label="Ticker"   sortKey="ticker"        current={sort} onSort={onSort} align="left" />
                <SortableHeader label="Strategy" sortKey="strategy"      current={sort} onSort={onSort} align="left" />
                <SortableHeader label="Side"     sortKey="side"          current={sort} onSort={onSort} />
                <SortableHeader label="Qty"      sortKey="quantity"      current={sort} onSort={onSort} />
                <SortableHeader label="Entry"    sortKey="entry_price"   current={sort} onSort={onSort} />
                <SortableHeader label="Last"     sortKey="current_price" current={sort} onSort={onSort} />
                <SortableHeader label="Value"    sortKey="market_value"  current={sort} onSort={onSort} />
                <SortableHeader label="P&L $"    sortKey="pnl"           current={sort} onSort={onSort} />
                <SortableHeader label="P&L %"    sortKey="pnl_pct"       current={sort} onSort={onSort} />
              </tr>
            </thead>
            <tbody className="divide-y divide-white/[0.04]">
              {positions.map(p => {
                const pnlPct = p.pnl_pct ?? (p.entry_price > 0 ? ((p.current_price - p.entry_price) / p.entry_price * 100 * (p.side === 'SHORT' ? -1 : 1)) : 0);
                return (
                  <tr key={p.id || p.ticker} className="qr-tr-hover">
                    <td className="py-1 px-2 text-[12px] font-bold text-white tracking-tight">{p.ticker}</td>
                    <td className="py-1 px-2 text-[10px] text-slate-400 truncate max-w-[160px]">{p.strategy || '—'}</td>
                    <td className="py-1 px-2 text-center">
                      <span className={`qr-chip ${p.side === 'LONG' ? 'qr-chip-emerald' : 'qr-chip-rose'}`}>{p.side}</span>
                    </td>
                    <td className="py-1 px-2 qr-num text-slate-200">{fmt(p.quantity, 0)}</td>
                    <td className="py-1 px-2 qr-num text-slate-400">{fmt(p.entry_price)}</td>
                    <td className="py-1 px-2 qr-num text-white">{fmt(p.current_price)}</td>
                    <td className="py-1 px-2 qr-num text-slate-200">{fmtK(p.market_value)}</td>
                    <td className={`py-1 px-2 qr-num font-bold ${pnlCl(p.pnl)}`}>{fmtK(p.pnl)}</td>
                    <td className={`py-1 px-2 qr-num ${pnlCl(pnlPct)}`}>{fmtPct(pnlPct)}</td>
                  </tr>
                );
              })}
              {!positions.length && (
                <tr><td colSpan={9} className="py-8 text-center text-slate-600 text-[11px]">No positions · {search ? 'no matches for filter' : 'deploy a strategy from the Lab tab'}</td></tr>
              )}
            </tbody>
          </table>
        </div>

        {/* Mobile rows */}
        <div className="md:hidden divide-y divide-white/5">
          {positions.map(p => {
            const pnlPct = p.pnl_pct ?? (p.entry_price > 0 ? ((p.current_price - p.entry_price) / p.entry_price * 100 * (p.side === 'SHORT' ? -1 : 1)) : 0);
            return (
              <div key={p.id || p.ticker} className="px-3 py-2">
                <div className="flex items-center justify-between mb-1">
                  <div className="flex items-center gap-2">
                    <span className="font-bold text-white text-[13px]">{p.ticker}</span>
                    <span className={`qr-chip ${p.side === 'LONG' ? 'qr-chip-emerald' : 'qr-chip-rose'}`}>{p.side}</span>
                  </div>
                  <span className={`qr-num font-bold text-[13px] ${pnlCl(p.pnl)}`}>{fmtK(p.pnl)}</span>
                </div>
                <div className="flex items-center justify-between text-[10px] text-slate-400">
                  <span>{p.strategy || '—'}</span>
                  <span className="qr-num">{fmt(p.quantity,0)} @ {fmt(p.entry_price)}</span>
                </div>
                <div className="flex items-center justify-between text-[10px] mt-0.5">
                  <span className="text-slate-500">last <span className="text-slate-200 qr-num">{fmt(p.current_price)}</span></span>
                  <span className={`qr-num ${pnlCl(pnlPct)}`}>{fmtPct(pnlPct)}</span>
                </div>
              </div>
            );
          })}
          {!positions.length && <div className="py-6 text-center text-slate-600 text-[11px]">No positions</div>}
        </div>
      </div>
    </div>
  );
};

// =================================================================
// Performance Tab — denser comparison table
// =================================================================
const PerformanceTab = ({ data, onSelectStrategy }) => {
  const [tf, setTf] = useState('1M');
  const [view, setView] = useState('overview');
  const { sort, onSort, sorter } = useSort('returns');

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
                return (
                  <tr key={s.strategy_id} className="qr-tr-hover cursor-pointer" onClick={() => onSelectStrategy?.(s.strategy_id)}>
                    <td className="py-1 px-2">
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
                <tr><td colSpan={10} className="py-8 text-center text-slate-600 text-[11px]">No deployed strategies · approve from the Strategies tab</td></tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

// =================================================================
// Command Center — quant overview at-a-glance
// =================================================================
const CommandCenter = ({ data, pipelineSummary, navigateToTab, healthData, onSelectStrategy }) => {
  const totalPositionValue = data.positions.reduce((s, p) => s + (p.market_value || 0), 0);
  const totalPnLOpen = data.positions.reduce((s, p) => s + (p.pnl || 0), 0);
  const sortedStrategies = useMemo(() =>
    [...(data.strategies || [])].sort((a, b) => (b.returns || 0) - (a.returns || 0)),
    [data.strategies]
  );
  const top5 = sortedStrategies.slice(0, 5);

  return (
    <div className="space-y-3">
      <div className="flex items-end justify-between">
        <div>
          <h1 className="text-sm font-bold text-white">Command Center</h1>
          <p className="text-[10px] text-slate-500">Platform overview · {data.strategies.length} strategies · {data.positions.length} positions</p>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="qr-label">SHORTCUTS</span>
          {[
            { key: '1', tab: 'command', label: 'Cmd' },
            { key: '2', tab: 'lab', label: 'Lab' },
            { key: '3', tab: 'strategies', label: 'Strat' },
            { key: '4', tab: 'agentic_research', label: 'Agents' },
            { key: '5', tab: 'performance', label: 'Perf' },
          ].map(s => (
            <button key={s.key} onClick={() => navigateToTab(s.tab)} className="flex items-center gap-1 hover:opacity-80">
              <span className="qr-kbd">{s.key}</span>
              <span className="text-[9px] text-slate-500">{s.label}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Top KPIs */}
      <div className="grid grid-cols-2 md:grid-cols-6 gap-2">
        <KPI l="Strategies"  v={data.strategies.length} sub={`${data.strategies.filter(s => s.live_trades > 0).length} live`} hint="Total researcher strategies" />
        <KPI l="Positions"   v={data.positions.length} sub={fmtK(totalPositionValue)} hint="Open positions market value" />
        <KPI l="Open P&L"    v={fmtK(totalPnLOpen)} pos={totalPnLOpen >= 0} sub={totalPositionValue > 0 ? `${((totalPnLOpen/totalPositionValue)*100).toFixed(2)}%` : null} />
        <KPI l="P&L Today"   v={fmtK(data.dailyPnl[0]?.pnl)} pos={data.dailyPnl[0]?.pnl >= 0} sub={data.dailyPnl[0]?.trades ? `${data.dailyPnl[0].trades} trades` : null} />
        <KPI l="Win Rate"    v={`${((data.summary?.win_rate || 0) * 100).toFixed(1)}%`} pos={(data.summary?.win_rate || 0) > 0.5} sub={data.summary?.total_trades ? `${data.summary.total_trades} tr` : null} />
        <KPI l="DB Latency"  v={healthData?.latency_ms != null ? `${healthData.latency_ms}ms` : '—'} sub={healthData?.status || 'unknown'} pos={healthData?.status === 'healthy'} />
      </div>

      {/* Two-column layout: Pipeline + Top Strategies */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-3">
        {/* Pipeline */}
        {pipelineSummary && (
          <div className="qr-surface overflow-hidden">
            <div className="px-3 py-2 border-b border-white/[0.05] flex items-center justify-between">
              <span className="qr-label">Strategy Pipeline</span>
              <button onClick={() => navigateToTab('strategies')} className="text-[10px] text-blue-400 hover:text-blue-300 font-semibold">Manage →</button>
            </div>
            <div className="p-3">
              <div className="flex items-center gap-1.5">
                {[
                  { key: 'experimental', label: 'EXPERIMENTAL', cls: 'qr-chip-slate' },
                  { key: 'near_golden',  label: 'NEAR GOLDEN',  cls: 'qr-chip-blue'  },
                  { key: 'golden',       label: 'GOLDEN',       cls: 'qr-chip-amber' },
                  { key: 'deployed',     label: 'DEPLOYED',     cls: 'qr-chip-emerald'},
                ].map((stage, i) => (
                  <React.Fragment key={stage.key}>
                    {i > 0 && <span className="text-slate-700 text-[10px]">→</span>}
                    <div className={`flex-1 text-center py-2 px-1 rounded-md ${stage.cls.replace('qr-chip-', 'bg-').replace('emerald', 'emerald-500/10').replace('amber', 'amber-500/10').replace('blue', 'blue-500/10').replace('slate', 'slate-700/30')}`}>
                      <div className="qr-num text-[15px] font-bold">{pipelineSummary[stage.key] || 0}</div>
                      <div className="text-[8px] text-slate-500 uppercase tracking-wider mt-0.5">{stage.label}</div>
                    </div>
                  </React.Fragment>
                ))}
              </div>
              <div className="mt-2 flex items-center justify-between text-[10px] text-slate-500">
                <span>Total: <span className="qr-num text-slate-300">{pipelineSummary.total || 0}</span></span>
                <span>Last DE update: <span className="qr-num text-slate-300">{fmtAge(pipelineSummary.last_update)}</span></span>
              </div>
            </div>
          </div>
        )}

        {/* Top strategies */}
        {top5.length > 0 && (
          <div className="qr-surface overflow-hidden">
            <div className="px-3 py-2 border-b border-white/[0.05] flex items-center justify-between">
              <span className="qr-label">Top 5 Strategies</span>
              <button onClick={() => navigateToTab('performance')} className="text-[10px] text-blue-400 hover:text-blue-300 font-semibold">All →</button>
            </div>
            <table className="w-full">
              <tbody className="divide-y divide-white/[0.04]">
                {top5.map(s => (
                  <tr key={s.strategy_id || s.id} className="qr-tr-hover cursor-pointer" onClick={() => onSelectStrategy?.(s.strategy_id || s.id)}>
                    <td className="py-1 px-3">
                      <div className="font-bold text-white text-[11px] truncate max-w-[200px] hover:text-blue-300">{s.strategy_name || s.name || s.strategy_id}</div>
                      <div className="text-[9px] text-slate-500">{s.asset_class || '—'} · {s.priority || ''}</div>
                    </td>
                    <td className="py-1 px-2 qr-num text-slate-400 text-[10px]">{s.win_rate != null ? `${(s.win_rate * 100).toFixed(0)}%` : '—'}</td>
                    <td className={`py-1 px-2 qr-num font-bold ${pnlCl(s.returns)}`}>{s.returns != null ? fmtPct(s.returns) : '—'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Quick action bar - dense pill row */}
      <div className="qr-surface px-3 py-2 flex items-center gap-1.5 overflow-x-auto no-scrollbar">
        <span className="qr-label flex-shrink-0">QUICK</span>
        <span className="qr-divider-v h-3" />
        {[
          { tab: 'lab',         label: 'Strategy Lab',     IconComponent: Icon.Lab,         color: 'blue' },
          { tab: 'strategies',  label: 'Golden Strategies',IconComponent: Icon.Strategies,  color: 'amber' },
          { tab: 'agentic_research', label: 'Agentic Research', IconComponent: Icon.Agents, color: 'violet' },
          { tab: 'research',    label: 'Signals & Earnings', IconComponent: Icon.Research,  color: 'blue' },
          { tab: 'portfolio',   label: 'Portfolio',         IconComponent: Icon.Portfolio,  color: 'emerald' },
          { tab: 'markets',     label: 'Markets',           IconComponent: Icon.Markets,    color: 'amber' },
        ].map(item => (
          <button key={item.tab} onClick={() => navigateToTab(item.tab)} className="qr-btn-ghost flex-shrink-0">
            <item.IconComponent />
            <span>{item.label}</span>
          </button>
        ))}
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
  const [executionMode, setExecutionMode] = useState('SIMULATION');
  const [ibkrConnected, setIbkrConnected] = useState(false);
  const [pipelineSummary, setPipelineSummary] = useState(null);
  const [lastRefresh, setLastRefresh] = useState(null);
  const [latencyMs, setLatencyMs] = useState(null);
  const [healthData, setHealthData] = useState(null);
  const [navOpen, setNavOpen] = useState(false);
  const [selectedStrategyId, setSelectedStrategyId] = useState(null);

  const pathParts = location.pathname.split('/').filter(Boolean);
  const currentMode = pathParts[0] || 'sim';
  const currentTab = pathParts[1] || 'command';

  const openStrategyDetail = (id) => {
    if (!id) return;
    setSelectedStrategyId(id);
    if (currentTab !== 'strategy_detail') navigate(`/${currentMode}/strategy_detail`);
  };
  const closeStrategyDetail = () => {
    setSelectedStrategyId(null);
    navigate(`/${currentMode}/performance`);
  };

  const navItems = useMemo(() => [
    { id: 'command',          label: 'Command',  short: 'Cmd',     IconComponent: Icon.Command,     key: '1' },
    { id: 'lab',              label: 'Lab',      short: 'Lab',     IconComponent: Icon.Lab,         key: '2' },
    { id: 'strategies',       label: 'Strategies', short: 'Strat', IconComponent: Icon.Strategies,  key: '3' },
    { id: 'agentic_research', label: 'Agents',   short: 'Agt',     IconComponent: Icon.Agents,      key: '4' },
    { id: 'performance',      label: 'Performance', short: 'Perf', IconComponent: Icon.Performance, key: '5' },
    { id: 'research',         label: 'Research', short: 'Res',     IconComponent: Icon.Research,    key: '6' },
    { id: 'portfolio',        label: 'Portfolio', short: 'Port',   IconComponent: Icon.Portfolio,   key: '7' },
    { id: 'markets',          label: 'Markets',  short: 'Mkt',     IconComponent: Icon.Markets,     key: '8' },
    { id: 'settings',         label: 'Settings', short: 'Set',     IconComponent: Icon.Settings,    key: '9' },
  ], []);

  const navigateToTab = (tab) => navigate(`/${currentMode}/${tab}`);

  // Keyboard shortcut: 1-9 to switch tabs
  useEffect(() => {
    const handler = (e) => {
      if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;
      if (e.metaKey || e.ctrlKey || e.altKey) return;
      const item = navItems.find(n => n.key === e.key);
      if (item) {
        e.preventDefault();
        navigateToTab(item.id);
      }
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [navItems, currentMode]);

  // Mode + IBKR status
  useEffect(() => {
    const fetchMode = async () => {
      const modeData = await api.get('/api/execution/global-mode');
      if (modeData) {
        setExecutionMode(modeData.execution_mode || 'SIMULATION');
        setIbkrConnected(modeData.ibkr_connected || false);
      }
    };
    fetchMode();
    const id = setInterval(fetchMode, 30000);
    return () => clearInterval(id);
  }, []);

  // Pipeline summary
  useEffect(() => {
    const fetch = async () => {
      const ps = await api.get('/api/strategies/pipeline-summary');
      if (ps) setPipelineSummary(ps);
    };
    fetch();
    const id = setInterval(fetch, 60000);
    return () => clearInterval(id);
  }, []);

  // System health
  useEffect(() => {
    const fetch = async () => {
      const t0 = performance.now();
      const h = await api.get('/api/system/health');
      const t1 = performance.now();
      setLatencyMs(Math.round(t1 - t0));
      if (h) setHealthData(h);
    };
    fetch();
    const id = setInterval(fetch, 15000);
    return () => clearInterval(id);
  }, []);

  // Main data fetch
  useEffect(() => {
    const fetchAll = async () => {
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
        mode: executionMode,
      });
      setLastRefresh(new Date().toISOString());
      setLoading(false);
    };

    fetchAll();
    const id = setInterval(fetchAll, 60000);
    return () => clearInterval(id);
  }, [executionMode]);

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
            <GlobalExecutionToggle />
            <div className="hidden sm:flex items-center gap-1.5 px-1.5 py-0.5 rounded">
              <span className={`qr-dot ${ibkrConnected ? 'qr-dot-live animate-pulse-dot' : 'qr-dot-idle'}`} />
              <span className="text-[9px] text-slate-500 uppercase tracking-wider">IBKR</span>
            </div>
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
          lastRefresh={lastRefresh}
          latencyMs={latencyMs}
          mode={executionMode}
          healthOk={healthData?.status === 'healthy'}
        />
      </header>

      {/* Main */}
      <main className="pt-[72px] pb-20 md:pb-4 px-3 md:px-4 max-w-[1800px] mx-auto">
        {currentTab === 'command'          && <CommandCenter data={data} pipelineSummary={pipelineSummary} navigateToTab={navigateToTab} healthData={healthData} onSelectStrategy={openStrategyDetail} />}
        {currentTab === 'portfolio'        && <PortfolioTab data={data} />}
        {currentTab === 'performance'      && <PerformanceTab data={data} onSelectStrategy={openStrategyDetail} />}
        {currentTab === 'markets'          && <MarketsTab onTickerClick={() => {}} />}
        {currentTab === 'settings'         && <SettingsTab />}
        {currentTab === 'lab'              && <StrategyLab />}
        {currentTab === 'strategies'       && <GoldenStrategies onSelectStrategy={openStrategyDetail} />}
        {currentTab === 'agentic_research' && <AgenticResearch />}
        {currentTab === 'research'         && <ResearchTab onTickerClick={() => {}} />}
        {currentTab === 'strategy_detail'  && (
          selectedStrategyId
            ? <StrategyDetail strategyId={selectedStrategyId} onBack={closeStrategyDetail} />
            : <div className="qr-surface p-6 text-center text-[11px] text-slate-500">No strategy selected · pick one from <button onClick={() => navigateToTab('performance')} className="text-blue-400 hover:text-blue-300 underline">Performance</button></div>
        )}
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
    </div>
  );
}
