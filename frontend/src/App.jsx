import React, { useState, useEffect, useMemo } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { MarketsTab } from './components/MarketsTab';
import { SettingsTab } from './components/SettingsTab';
import { StrategyLab } from './components/StrategyLab';
import { ResearchTab } from './components/ResearchTab';
import { GlobalExecutionToggle } from './components/GlobalExecutionToggle';
import { GoldenStrategies } from './components/GoldenStrategies';
import { StrategyPerformance } from './components/StrategyPerformance';
import { AgenticResearch } from './components/AgenticResearch';
import { fmt, fmtK, fmtPct, pnlCl, api } from './utils';

// SVG Icon Components
const Icon = {
  Command: () => (
    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zm10 0a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zm10 0a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z" />
    </svg>
  ),
  Lab: () => (
    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z" />
    </svg>
  ),
  Research: () => (
    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
    </svg>
  ),
  Performance: () => (
    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
    </svg>
  ),
  Portfolio: () => (
    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M21 13.255A23.931 23.931 0 0112 15c-3.183 0-6.22-.62-9-1.745M16 6V4a2 2 0 00-2-2h-4a2 2 0 00-2 2v2m4 6h.01M5 20h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
    </svg>
  ),
  Markets: () => (
    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M3.055 11H5a2 2 0 012 2v1a2 2 0 002 2 2 2 0 012 2v2.945M8 3.935V5.5A2.5 2.5 0 0010.5 8h.5a2 2 0 012 2 2 2 0 104 0 2 2 0 012-2h1.064M15 20.488V18a2 2 0 012-2h3.064M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
    </svg>
  ),
  Settings: () => (
    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.066 2.573c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.573 1.066c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.066-2.573c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
      <path strokeLinecap="round" strokeLinejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
    </svg>
  ),
  Strategies: () => (
    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z" />
    </svg>
  ),
  Agents: () => (
    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
    </svg>
  ),
};

// Compact UI Components
const Pill = ({ c, children }) => {
  const colors = {
    emerald: 'bg-emerald-500/15 text-emerald-400 ring-1 ring-emerald-500/20',
    rose: 'bg-rose-500/15 text-rose-400 ring-1 ring-rose-500/20',
    blue: 'bg-blue-500/15 text-blue-400 ring-1 ring-blue-500/20',
    amber: 'bg-amber-500/15 text-amber-400 ring-1 ring-amber-500/20',
    slate: 'bg-slate-700/50 text-slate-400 ring-1 ring-slate-500/20',
  };
  return <span className={`px-2 py-0.5 rounded-md text-[10px] font-bold uppercase tracking-wide ${colors[c] || colors.slate}`}>{children}</span>;
};

const KPI = ({ l, v, sub, pos }) => (
  <div className="px-4 py-3 bg-slate-900/60 rounded-xl border border-white/[0.06] hover:border-white/10 transition-colors min-w-0">
    <div className="text-[10px] text-slate-500 uppercase tracking-wider font-medium truncate">{l}</div>
    <div className="text-lg font-bold text-white font-mono leading-tight mt-1">{v}</div>
    {sub && <div className={`text-[11px] mt-1 font-medium ${pos != null ? (pos ? 'text-emerald-400' : 'text-rose-400') : 'text-slate-500'}`}>{sub}</div>}
  </div>
);

// Portfolio Component — Split by Asset Class
const PortfolioTab = ({ data }) => {
  const [search, setSearch] = useState('');
  const [activeFilter, setActiveFilter] = useState('ALL');

  const positions = useMemo(() =>
    (data.positions || []).filter(p => {
      const matchesSearch = !search || p.ticker?.toLowerCase().includes(search.toLowerCase());
      const matchesFilter = activeFilter === 'ALL' || p.asset_class === activeFilter;
      return matchesSearch && matchesFilter;
    }),
    [data.positions, search, activeFilter]
  );

  // Group by asset class
  const byAssetClass = useMemo(() => {
    const groups = {};
    for (const p of positions) {
      const cls = p.asset_class || 'OTHER';
      if (!groups[cls]) groups[cls] = [];
      groups[cls].push(p);
    }
    return groups;
  }, [positions]);

  const assetClasses = ['STOCK', 'FX', 'CRYPTO', 'BOND', 'ETF', 'OPTION', 'FUTURE', 'OTHER'];
  const activeClasses = assetClasses.filter(c => byAssetClass[c]?.length > 0);

  const totalValue = positions.reduce((s, p) => s + (p.market_value || 0), 0);
  const totalPnL = positions.reduce((s, p) => s + (p.unrealized_pnl || p.pnl || 0), 0);

  // Summary by class
  const classSummary = useMemo(() => {
    const summary = {};
    for (const cls of activeClasses) {
      const grp = byAssetClass[cls];
      summary[cls] = {
        count: grp.length,
        value: grp.reduce((s, p) => s + (p.market_value || 0), 0),
        pnl: grp.reduce((s, p) => s + (p.unrealized_pnl || p.pnl || 0), 0),
      };
    }
    return summary;
  }, [byAssetClass, activeClasses]);

  const classLabels = {
    STOCK: { label: 'Stocks', icon: '📈', color: 'blue' },
    FX: { label: 'FX', icon: '💱', color: 'emerald' },
    CRYPTO: { label: 'Crypto', icon: '₿', color: 'amber' },
    BOND: { label: 'Bonds', icon: '📋', color: 'slate' },
    ETF: { label: 'ETFs', icon: '📊', color: 'violet' },
    OPTION: { label: 'Options', icon: '⚡', color: 'rose' },
    FUTURE: { label: 'Futures', icon: '⏳', color: 'orange' },
    CASH: { label: 'Cash', icon: '💵', color: 'emerald' },
    OTHER: { label: 'Other', icon: '💼', color: 'slate' },
  };

  const PositionTable = ({ positions, title, icon, color }) => {
    const colorMap = {
      blue: 'border-blue-500/20 bg-blue-500/5',
      emerald: 'border-emerald-500/20 bg-emerald-500/5',
      amber: 'border-amber-500/20 bg-amber-500/5',
      slate: 'border-slate-500/20 bg-slate-500/5',
      violet: 'border-violet-500/20 bg-violet-500/5',
      rose: 'border-rose-500/20 bg-rose-500/5',
      orange: 'border-orange-500/20 bg-orange-500/5',
    };

    const grpValue = positions.reduce((s, p) => s + (p.market_value || 0), 0);
    const grpPnL = positions.reduce((s, p) => s + (p.unrealized_pnl || p.pnl || 0), 0);

    return (
      <div className={`rounded-xl border ${colorMap[color] || colorMap.slate} overflow-hidden mb-4`}>
        <div className="px-3 py-2.5 border-b border-white/[0.06] flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="text-sm">{icon}</span>
            <span className="text-xs font-bold text-white uppercase tracking-wider">{title}</span>
            <span className="text-[10px] text-slate-500">{positions.length} positions</span>
          </div>
          <div className="flex items-center gap-3">
            <span className="text-[11px] font-mono text-slate-400">{fmtK(grpValue)}</span>
            <span className={`text-[11px] font-mono font-bold ${pnlCl(grpPnL)}`}>{grpPnL >= 0 ? '+' : ''}{fmtK(grpPnL)}</span>
          </div>
        </div>

        <table className="w-full text-xs">
          <thead className="bg-slate-900/80">
            <tr className="text-[9px] text-slate-500 uppercase">
              {['Ticker', 'Name', 'Side', 'Qty', 'Entry', 'Current', 'Value', 'P&L', 'P&L %'].map(h =>
                <th key={h} className="text-right py-2 px-2 first:text-left">{h}</th>)}
            </tr>
          </thead>
          <tbody className="divide-y divide-white/5">
            {positions.map(p => {
              const entry = p.avg_entry_price || p.entry_price || 0;
              const current = p.current_price || 0;
              const pnlPct = entry > 0 ? ((current - entry) / entry * 100 * (p.side === 'SHORT' ? -1 : 1)) : 0;
              return (
                <tr key={p.id || p.ticker} className="hover:bg-white/[0.03] transition-colors">
                  <td className="py-2 px-2 font-bold text-white">{p.ticker}</td>
                  <td className="py-2 px-2 text-slate-400 text-[10px] max-w-[120px] truncate">{p.name || p.strategy || '—'}</td>
                  <td className="py-2 px-2 text-center">
                    <span className={`text-[9px] font-bold px-1.5 py-0.5 rounded ${p.side === 'LONG' ? 'bg-emerald-500/20 text-emerald-400' : p.side === 'SHORT' ? 'bg-rose-500/20 text-rose-400' : 'bg-slate-500/20 text-slate-400'}`}>{p.side || '—'}</span>
                  </td>
                  <td className="py-2 px-2 text-right font-mono">{fmt(p.quantity, 0)}</td>
                  <td className="py-2 px-2 text-right font-mono text-slate-400">${fmt(entry)}</td>
                  <td className="py-2 px-2 text-right font-mono text-white">${fmt(current)}</td>
                  <td className="py-2 px-2 text-right font-mono">{fmtK(p.market_value)}</td>
                  <td className={`py-2 px-2 text-right font-mono font-bold ${pnlCl(p.unrealized_pnl || p.pnl)}`}>{fmtK(p.unrealized_pnl || p.pnl)}</td>
                  <td className={`py-2 px-2 text-right font-mono ${pnlCl(pnlPct)}`}>{fmtPct(pnlPct)}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    );
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-sm font-bold text-white">Portfolio</h2>
          <p className="text-[10px] text-slate-500">Live positions & P&L by asset class</p>
        </div>
        <Pill c={totalPnL >= 0 ? 'emerald' : 'rose'}>{totalPnL >= 0 ? '+' : ''}{fmtK(totalPnL)}</Pill>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
        <KPI l="Total Value" v={fmtK(totalValue)} />
        <KPI l="Positions" v={positions.length} />
        <KPI l="Asset Classes" v={activeClasses.length} />
        <KPI l="Unrealized P&L" v={fmtK(totalPnL)} pos={totalPnL >= 0} />
      </div>

      {/* Asset Class Filter */}
      <div className="flex gap-1 p-1 rounded-lg bg-slate-900/50 border border-white/[0.06] overflow-x-auto">
        <button
          onClick={() => setActiveFilter('ALL')}
          className={`px-3 py-1.5 rounded-md text-[10px] font-bold transition-colors whitespace-nowrap ${activeFilter === 'ALL' ? 'bg-blue-500 text-white' : 'text-slate-400 hover:text-white'}`}
        >
          All ({positions.length})
        </button>
        {activeClasses.map(cls => (
          <button
            key={cls}
            onClick={() => setActiveFilter(cls)}
            className={`px-3 py-1.5 rounded-md text-[10px] font-bold transition-colors whitespace-nowrap ${activeFilter === cls ? 'bg-blue-500 text-white' : 'text-slate-400 hover:text-white'}`}
          >
            {classLabels[cls]?.icon} {classLabels[cls]?.label} ({byAssetClass[cls].length})
          </button>
        ))}
      </div>

      {/* Search */}
      <div className="flex items-center gap-2">
        <input
          value={search}
          onChange={e => setSearch(e.target.value)}
          placeholder="Filter by ticker..."
          className="px-3 py-2 bg-slate-800/80 border border-white/10 rounded-lg text-xs text-white w-48 placeholder-slate-600 focus:outline-none focus:border-blue-500/50"
        />
      </div>

      {/* Positions by Asset Class */}
      {activeFilter === 'ALL' ? (
        activeClasses.map(cls => (
          <PositionTable
            key={cls}
            positions={byAssetClass[cls]}
            title={classLabels[cls]?.label || cls}
            icon={classLabels[cls]?.icon || '💼'}
            color={classLabels[cls]?.color || 'slate'}
          />
        ))
      ) : (
        byAssetClass[activeFilter] && (
          <PositionTable
            positions={byAssetClass[activeFilter]}
            title={classLabels[activeFilter]?.label || activeFilter}
            icon={classLabels[activeFilter]?.icon || '💼'}
            color={classLabels[activeFilter]?.color || 'slate'}
          />
        )
      )}

      {!positions.length && (
        <div className="py-12 text-center text-slate-600 text-sm bg-slate-900/30 rounded-xl border border-white/[0.06]">
          No positions found
        </div>
      )}
    </div>
  );
};

// Performance Component
const PerformanceTab = ({ data }) => {
  const [tf, setTf] = useState('1M');
  const [view, setView] = useState('overview'); // 'overview' or 'analytics'
  const strategies = data.strategies || [];

  // Sort without mutating state - use spread to create a new array
  const bestStrategy = useMemo(() => {
    return [...strategies].sort((a, b) => (b.returns || 0) - (a.returns || 0))[0];
  }, [strategies]);

  if (view === 'analytics') {
    return (
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div><h2 className="text-sm font-bold text-white">Deep Analytics</h2><p className="text-[10px] text-slate-500">Comprehensive strategy performance</p></div>
          <button onClick={() => setView('overview')} className="px-3 py-1.5 rounded-lg text-[10px] font-bold bg-slate-900/50 border border-white/[0.06] text-slate-400 hover:text-white transition-colors">
            Back to Overview
          </button>
        </div>
        <StrategyPerformance />
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div><h2 className="text-sm font-bold text-white">Performance</h2><p className="text-[10px] text-slate-500">Backtest vs Live</p></div>
        <div className="flex items-center gap-2">
          <button onClick={() => setView('analytics')} className="px-3 py-1.5 rounded-lg text-[10px] font-bold bg-blue-500/10 border border-blue-500/20 text-blue-400 hover:bg-blue-500/20 transition-colors">
            Deep Analytics
          </button>
          <div className="flex gap-1 p-1 rounded-lg bg-slate-900/50 border border-white/[0.06]">
            {['1W', '1M', '3M', '1Y', 'ALL'].map(t =>
              <button key={t} onClick={() => setTf(t)} className={`px-3 py-1.5 rounded-md text-[10px] font-bold transition-colors ${tf === t ? 'bg-blue-500 text-white shadow-sm' : 'text-slate-400 hover:text-white'}`}>{t}</button>)}
          </div>
        </div>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
        <KPI l="Active" v={strategies.filter(s => s.live_trades > 0).length} />
        <KPI l="Avg Live WR" v={`${(strategies.filter(s => s.live_win_rate).reduce((a, s) => a + (s.live_win_rate || 0), 0) / Math.max(1, strategies.filter(s => s.live_win_rate).length)).toFixed(0)}%`} pos={true} />
        <KPI l="Total Trades" v={strategies.reduce((a, s) => a + (s.live_trades || 0), 0)} />
        <KPI l="Best" v={bestStrategy?.strategy_name?.slice(0, 10) || '\u2014'} pos={true} />
      </div>

      <div className="bg-slate-900/50 rounded-xl border border-white/[0.06] overflow-hidden">
        <div className="px-3 py-2.5 border-b border-white/[0.06]">
          <span className="text-[10px] text-slate-500 uppercase font-bold tracking-wider">Strategy Comparison</span>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-xs">
            <thead className="text-[9px] text-slate-500 uppercase border-b border-white/10 bg-slate-900/30">
              <tr>
                {['Strategy', 'Tier', 'BT WR', 'Live WR', '\u0394 WR', 'BT PF', 'Live PF', 'Returns'].map(h =>
                  <th key={h} className="text-right py-2 px-2 first:text-left">{h}</th>)}
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5">
              {strategies.map(s => {
                const delta = s.backtest_win_rate != null && s.live_win_rate != null ? s.live_win_rate - s.backtest_win_rate : null;
                return (
                  <tr key={s.strategy_id} className="hover:bg-white/[0.02] transition-colors">
                    <td className="py-2 px-2">
                      <div className="font-bold text-white">{s.strategy_name || s.strategy_id}</div>
                      <div className="text-[9px] text-slate-500">{s.asset_class}</div>
                    </td>
                    <td className="py-2 px-2 text-right">
                      <span className={`text-[10px] font-bold ${s.tier?.includes('T1') ? 'text-emerald-400' : s.tier?.includes('T2') ? 'text-amber-400' : 'text-slate-400'}`}>{s.tier || 'T4'}</span>
                    </td>
                    <td className="py-2 px-2 text-right font-mono text-slate-400">{s.backtest_win_rate != null ? `${s.backtest_win_rate.toFixed(0)}%` : '\u2014'}</td>
                    <td className={`py-2 px-2 text-right font-mono font-bold ${pnlCl(s.live_win_rate - 50)}`}>{s.live_win_rate != null ? `${s.live_win_rate.toFixed(0)}%` : '\u2014'}</td>
                    <td className={`py-2 px-2 text-right font-mono ${pnlCl(delta)}`}>{delta != null ? `${delta >= 0 ? '+' : ''}${delta.toFixed(0)}pp` : '\u2014'}</td>
                    <td className="py-2 px-2 text-right font-mono text-slate-400">{s.backtest_pf?.toFixed(2) || '\u2014'}</td>
                    <td className={`py-2 px-2 text-right font-mono ${pnlCl(s.live_profit_factor - 1.5)}`}>{s.live_profit_factor?.toFixed(2) || '\u2014'}</td>
                    <td className={`py-2 px-2 text-right font-mono font-bold ${pnlCl(s.returns)}`}>{s.returns != null ? fmtPct(s.returns) : '\u2014'}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

// Main App
export default function App() {
  const navigate = useNavigate();
  const location = useLocation();

  const [data, setData] = useState({ strategies: [], positions: [], paperStrategies: [], dailyPnl: [], trades: [], summary: {}, mode: 'SIMULATION' });
  const [loading, setLoading] = useState(true);
  const [detail, setDetail] = useState(null);
  const [executionMode, setExecutionMode] = useState('SIMULATION');
  const [ibkrConnected, setIbkrConnected] = useState(false);
  const [pipelineSummary, setPipelineSummary] = useState(null);

  const pathParts = location.pathname.split('/').filter(Boolean);
  const currentMode = pathParts[0] || 'sim';
  const currentTab = pathParts[1] || 'command';

  // Fetch execution mode and IBKR status
  useEffect(() => {
    const fetchMode = async () => {
      const modeData = await api.get('/api/execution/global-mode');
      if (modeData) {
        setExecutionMode(modeData.execution_mode || 'SIMULATION');
        setIbkrConnected(modeData.ibkr_connected || false);
      }
    };
    fetchMode();
    const interval = setInterval(fetchMode, 30000);
    return () => clearInterval(interval);
  }, []);

  // Fetch pipeline summary
  useEffect(() => {
    const fetchPipeline = async () => {
      const ps = await api.get('/api/strategies/pipeline-summary');
      if (ps) setPipelineSummary(ps);
    };
    fetchPipeline();
    const interval = setInterval(fetchPipeline, 60000);
    return () => clearInterval(interval);
  }, []);

  // Fetch data
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
      setLoading(false);
    };

    fetchAll();
    const interval = setInterval(fetchAll, 60000);
    return () => clearInterval(interval);
  }, [executionMode]);

  const navItems = [
    { id: 'command', label: 'Command', IconComponent: Icon.Command },
    { id: 'lab', label: 'Lab', IconComponent: Icon.Lab },
    { id: 'strategies', label: 'Strategies', IconComponent: Icon.Strategies },
    { id: 'agentic_research', label: 'Agentic Research', IconComponent: Icon.Agents },
    { id: 'research', label: 'Research', IconComponent: Icon.Research },
    { id: 'performance', label: 'Performance', IconComponent: Icon.Performance },
    { id: 'portfolio', label: 'Portfolio', IconComponent: Icon.Portfolio },
    { id: 'markets', label: 'Markets', IconComponent: Icon.Markets },
    { id: 'settings', label: 'Settings', IconComponent: Icon.Settings },
  ];

  const navigateToTab = (tab) => navigate(`/${currentMode}/${tab}`);

  if (loading) return (
    <div className="min-h-screen bg-[#05070a] flex items-center justify-center">
      <div className="text-slate-500 flex flex-col items-center gap-3">
        <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-blue-500 to-violet-600 flex items-center justify-center text-[11px] font-black text-white animate-pulse">JT</div>
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 border-2 border-slate-700 border-t-blue-500 rounded-full animate-spin" />
          <span className="text-xs text-slate-500">Loading platform...</span>
        </div>
      </div>
    </div>
  );

  return (
    <div className="min-h-screen bg-[#05070a] text-white font-sans">
      {/* Header */}
      <header className="fixed top-0 left-0 right-0 z-40 border-b border-white/[0.06] bg-[#05070a]/80 backdrop-blur-xl">
        <div className="flex items-center justify-between px-4 py-2.5 max-w-[1800px] mx-auto">
          <div className="flex items-center gap-4">
            {/* Logo */}
            <div className="flex items-center gap-2.5">
              <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-blue-500 to-violet-600 flex items-center justify-center text-[11px] font-black shadow-lg shadow-blue-500/20">JT</div>
              <div className="hidden md:block">
                <span className="text-sm font-bold text-white tracking-tight">JTCML</span>
                <span className="text-[10px] text-slate-500 block -mt-0.5">Trading Platform</span>
              </div>
            </div>

            {/* Desktop Nav */}
            <nav className="hidden md:flex gap-0.5 p-1 rounded-xl bg-slate-900/40 border border-white/[0.04]">
              {navItems.map(n => (
                <button key={n.id} onClick={() => navigateToTab(n.id)}
                  className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all duration-200 ${
                    currentTab === n.id
                      ? 'bg-white/10 text-white shadow-sm'
                      : 'text-slate-400 hover:text-slate-200 hover:bg-white/[0.04]'
                  }`}
                >
                  <n.IconComponent />
                  <span>{n.label}</span>
                </button>
              ))}
            </nav>
          </div>

          {/* Right side status */}
          <div className="flex items-center gap-3">
            <GlobalExecutionToggle />
            <div className="hidden sm:flex items-center gap-1.5 px-2 py-1 rounded-md">
              <span className={`inline-block w-1.5 h-1.5 rounded-full ${ibkrConnected ? 'bg-emerald-400 animate-pulse' : 'bg-slate-600'}`} />
              <span className="text-[10px] text-slate-500">IBKR</span>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="pt-16 md:pt-14 pb-20 md:pb-6 px-3 md:px-6 max-w-[1600px] mx-auto">
        {currentTab === 'portfolio' && <PortfolioTab data={data} />}
        {currentTab === 'performance' && <PerformanceTab data={data} />}
        {currentTab === 'markets' && <MarketsTab onTickerClick={t => setDetail(t)} />}
        {currentTab === 'settings' && <SettingsTab />}
        {currentTab === 'lab' && <StrategyLab />}
        {currentTab === 'strategies' && <GoldenStrategies />}
        {currentTab === 'agentic_research' && <AgenticResearch />}
        {currentTab === 'research' && <ResearchTab onTickerClick={t => setDetail(t)} />}
        {currentTab === 'command' && (
          <div className="space-y-6">
            {/* Welcome header */}
            <div>
              <h1 className="text-lg font-bold text-white">Command Center</h1>
              <p className="text-xs text-slate-500 mt-0.5">Platform overview and key metrics</p>
            </div>

            {/* Top KPIs */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              <KPI l="Strategies" v={data.strategies.length} sub={`${data.strategies.filter(s => s.live_trades > 0).length} active`} />
              <KPI l="Positions" v={data.positions.length} sub={data.positions.length > 0 ? `${fmtK(data.positions.reduce((s, p) => s + (p.market_value || 0), 0))} value` : 'No open positions'} />
              <KPI l="P&L Today" v={fmtK(data.dailyPnl[0]?.pnl)} pos={data.dailyPnl[0]?.pnl >= 0} sub={data.dailyPnl[0]?.pnl != null ? (data.dailyPnl[0].pnl >= 0 ? 'Profitable' : 'Loss') : 'No data'} />
              <KPI l="Win Rate" v={`${((data.summary?.win_rate || 0) * 100).toFixed(1)}%`} pos={(data.summary?.win_rate || 0) > 0.5} sub={data.summary?.total_trades ? `${data.summary.total_trades} trades` : 'No trades'} />
            </div>

            {/* Quick actions */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              {[
                { tab: 'strategies', label: 'Golden Strategies', desc: 'Review & deploy AI strategies', IconComponent: Icon.Strategies, color: 'amber' },
                { tab: 'lab', label: 'Strategy Lab', desc: 'Screen & deploy strategies', IconComponent: Icon.Lab, color: 'blue' },
                { tab: 'research', label: 'Research', desc: 'Signals & analyst ratings', IconComponent: Icon.Research, color: 'violet' },
                { tab: 'portfolio', label: 'Portfolio', desc: 'Active positions & P&L', IconComponent: Icon.Portfolio, color: 'emerald' },
                { tab: 'markets', label: 'Markets', desc: 'Market intelligence', IconComponent: Icon.Markets, color: 'amber' },
              ].map(item => (
                <button
                  key={item.tab}
                  onClick={() => navigateToTab(item.tab)}
                  className="p-4 rounded-xl bg-slate-900/40 border border-white/[0.06] hover:border-white/10 text-left transition-all group"
                >
                  <div className="flex items-center gap-2 mb-2">
                    <div className="text-slate-400 group-hover:text-white transition-colors">
                      <item.IconComponent />
                    </div>
                    <span className="text-sm font-bold text-white">{item.label}</span>
                  </div>
                  <p className="text-[11px] text-slate-500">{item.desc}</p>
                </button>
              ))}
            </div>

            {/* Strategy Pipeline Card */}
            {pipelineSummary && (
              <div className="bg-slate-900/40 rounded-xl border border-white/[0.06] overflow-hidden">
                <div className="px-4 py-3 border-b border-white/[0.06] flex items-center justify-between">
                  <span className="text-xs font-bold text-white">Strategy Pipeline</span>
                  <button onClick={() => navigateToTab('strategies')} className="text-[10px] text-blue-400 hover:text-blue-300 font-medium">Manage</button>
                </div>
                <div className="p-4">
                  <div className="flex items-center gap-2">
                    {[
                      { key: 'experimental', label: 'Experimental', bg: 'bg-slate-700/50', text: 'text-slate-300' },
                      { key: 'near_golden', label: 'Near Golden', bg: 'bg-blue-500/15', text: 'text-blue-400' },
                      { key: 'golden', label: 'Golden', bg: 'bg-amber-500/15', text: 'text-amber-400' },
                      { key: 'deployed', label: 'Deployed', bg: 'bg-emerald-500/15', text: 'text-emerald-400' },
                    ].map((stage, i) => (
                      <React.Fragment key={stage.key}>
                        {i > 0 && <span className="text-slate-700 text-[10px]">&rarr;</span>}
                        <div className={`flex-1 text-center py-2 px-1 rounded-lg ${stage.bg}`}>
                          <div className={`text-sm font-bold ${stage.text}`}>{pipelineSummary[stage.key] || 0}</div>
                          <div className="text-[8px] text-slate-500 uppercase tracking-wider">{stage.label}</div>
                        </div>
                      </React.Fragment>
                    ))}
                  </div>
                </div>
              </div>
            )}

            {/* Strategy overview */}
            {data.strategies.length > 0 && (
              <div className="bg-slate-900/40 rounded-xl border border-white/[0.06] overflow-hidden">
                <div className="px-4 py-3 border-b border-white/[0.06] flex items-center justify-between">
                  <span className="text-xs font-bold text-white">Top Strategies</span>
                  <button onClick={() => navigateToTab('lab')} className="text-[10px] text-blue-400 hover:text-blue-300 font-medium">View all</button>
                </div>
                <div className="divide-y divide-white/5">
                  {[...data.strategies].sort((a, b) => (b.returns || 0) - (a.returns || 0)).slice(0, 5).map(s => (
                    <div key={s.strategy_id || s.id} className="px-4 py-2.5 flex items-center justify-between hover:bg-white/[0.02] transition-colors">
                      <div>
                        <span className="text-xs font-bold text-white">{s.strategy_name || s.name || s.strategy_id || s.id}</span>
                        <span className="text-[10px] text-slate-500 ml-2">{s.asset_class}</span>
                      </div>
                      <div className="flex items-center gap-3">
                        {s.win_rate != null && <span className="text-[10px] text-slate-400 font-mono">WR {(s.win_rate * 100).toFixed(0)}%</span>}
                        <span className={`text-xs font-bold font-mono ${pnlCl(s.returns)}`}>
                          {s.returns != null ? fmtPct(s.returns) : '\u2014'}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </main>

      {/* Mobile Bottom Nav */}
      <nav className="bottom-nav md:hidden">
        <div className="flex items-center justify-around px-1 py-1">
          {navItems.map(n => (
            <button key={n.id} onClick={() => navigateToTab(n.id)}
              className={`flex flex-col items-center gap-0.5 px-2 py-1.5 rounded-lg min-w-0 transition-colors ${
                currentTab === n.id ? 'text-blue-400' : 'text-slate-500'
              }`}
            >
              <n.IconComponent />
              <span className="text-[8px] font-medium truncate">{n.label}</span>
            </button>
          ))}
        </div>
      </nav>
    </div>
  );
}
