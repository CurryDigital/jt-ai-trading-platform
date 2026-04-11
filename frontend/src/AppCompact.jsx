import React, { useState, useEffect, useMemo } from 'react';
import { useParams, useNavigate, useLocation } from 'react-router-dom';
import { MarketsTab } from './components/MarketsTab';
import { SettingsTab } from './components/SettingsTab';
import { StrategyLab } from './components/StrategyLab';
import { ResearchTab } from './components/ResearchTab';
import { fmt, fmtK, fmtPct, pnlCl, pnlBg, api } from './utils';

// Icons
const Icons = {
  Dashboard: '📊', Strategies: '🎯', Chart: '📈', Research: '🔬',
  Performance: '📈', Portfolio: '💼', Markets: '🌐', Settings: '⚙️'
};

// Compact UI Components
const Pill = ({ c, children }) => {
  const colors = { emerald: 'bg-emerald-500/15 text-emerald-400', rose: 'bg-rose-500/15 text-rose-400', blue: 'bg-blue-500/15 text-blue-400', amber: 'bg-amber-500/15 text-amber-400', slate: 'bg-slate-700/50 text-slate-400' };
  return <span className={`px-1.5 py-0.5 rounded text-[10px] font-bold uppercase ${colors[c] || colors.slate}`}>{children}</span>;
};

const Dot = ({ on }) => <span className={`inline-block w-1.5 h-1.5 rounded-full ${on ? 'bg-emerald-400 animate-pulse' : 'bg-rose-500'}`} />;

const KPI = ({ l, v, sub, pos }) => (
  <div className="px-3 py-2 bg-slate-900/60 rounded-lg border border-white/5 min-w-0">
    <div className="text-[9px] text-slate-500 uppercase tracking-wider truncate">{l}</div>
    <div className="text-base font-bold text-white font-mono leading-tight mt-0.5">{v}</div>
    {sub && <div className={`text-[10px] mt-0.5 ${pos != null ? (pos ? 'text-emerald-400' : 'text-rose-400') : 'text-slate-500'}`}>{sub}</div>}
  </div>
);

// Portfolio Component
const PortfolioTab = ({ data }) => {
  const [search, setSearch] = useState('');
  const positions = useMemo(() => 
    data.positions.filter(p => !search || p.ticker?.toLowerCase().includes(search.toLowerCase())),
    [data.positions, search]
  );
  
  const totalValue = positions.reduce((s, p) => s + (p.market_value || 0), 0);
  const totalPnL = positions.reduce((s, p) => s + (p.pnl || 0), 0);
  const longVal = positions.filter(p => p.side === 'LONG').reduce((s, p) => s + (p.market_value || 0), 0);
  const shortVal = positions.filter(p => p.side === 'SHORT').reduce((s, p) => s + (p.market_value || 0), 0);

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div><h2 className="text-sm font-bold text-white">Portfolio</h2><p className="text-[10px] text-slate-500">Live positions & P&L</p></div>
        <Pill c={totalPnL >= 0 ? 'emerald' : 'rose'}>{totalPnL >= 0 ? '+' : ''}{fmtK(totalPnL)}</Pill>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
        <KPI l="Total Value" v={fmtK(totalValue)} />
        <KPI l="Positions" v={positions.length} />
        <KPI l="Long" v={fmtK(longVal)} pos={true} />
        <KPI l="Short" v={fmtK(shortVal)} pos={false} />
      </div>

      <div className="bg-slate-900/50 rounded-lg border border-white/5 overflow-hidden">
        <div className="px-3 py-2 border-b border-white/5 flex items-center justify-between">
          <span className="text-[10px] text-slate-500 uppercase font-bold tracking-wider">Positions</span>
          <input value={search} onChange={e => setSearch(e.target.value)} placeholder="Filter..." 
            className="px-2 py-1 bg-slate-800 border border-white/10 rounded text-[10px] text-white w-28" />
        </div>
        
        <table className="w-full text-xs hidden md:table">
          <thead className="bg-slate-900/80">
            <tr className="text-[9px] text-slate-500 uppercase">
              {['Ticker', 'Strategy', 'Side', 'Qty', 'Entry', 'Current', 'Value', 'P&L', 'P&L %'].map(h => 
                <th key={h} className="text-right py-2 px-2">{h}</th>)}
            </tr>
          </thead>
          <tbody className="divide-y divide-white/5">
            {positions.map(p => {
              const pnlPct = p.entry_price > 0 ? ((p.current_price - p.entry_price) / p.entry_price * 100 * (p.side === 'SHORT' ? -1 : 1)) : 0;
              return (
                <tr key={p.id || p.ticker} className="hover:bg-white/5">
                  <td className="py-2 px-2 font-bold text-white">{p.ticker}</td>
                  <td className="py-2 px-2 text-slate-400">{p.strategy}</td>
                  <td className="py-2 px-2 text-center">
                    <span className={`text-[9px] font-bold px-1.5 py-0.5 rounded ${p.side === 'LONG' ? 'bg-emerald-500/20 text-emerald-400' : 'bg-rose-500/20 text-rose-400'}`}>{p.side}</span>
                  </td>
                  <td className="py-2 px-2 text-right font-mono">{fmt(p.quantity, 0)}</td>
                  <td className="py-2 px-2 text-right font-mono text-slate-400">${fmt(p.entry_price)}</td>
                  <td className="py-2 px-2 text-right font-mono text-white">${fmt(p.current_price)}</td>
                  <td className="py-2 px-2 text-right font-mono">{fmtK(p.market_value)}</td>
                  <td className={`py-2 px-2 text-right font-mono font-bold ${pnlCl(p.pnl)}`}>{fmtK(p.pnl)}</td>
                  <td className={`py-2 px-2 text-right font-mono ${pnlCl(pnlPct)}`}>{fmtPct(pnlPct)}</td>
                </tr>
              );
            })}
            {!positions.length && <tr><td colSpan={9} className="py-6 text-center text-slate-600">No positions</td></tr>}
          </tbody>
        </table>
      </div>
    </div>
  );
};

// Performance Component
const PerformanceTab = ({ data }) => {
  const [tf, setTf] = useState('1M');
  const strategies = data.strategies || [];
  
  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div><h2 className="text-sm font-bold text-white">Performance</h2><p className="text-[10px] text-slate-500">Backtest vs Live</p></div>
        <div className="flex gap-1 p-1 rounded-lg bg-slate-900/50 border border-white/5">
          {['1W', '1M', '3M', '1Y', 'ALL'].map(t => 
            <button key={t} onClick={() => setTf(t)} className={`px-3 py-1 rounded text-[10px] font-bold ${tf === t ? 'bg-blue-500 text-white' : 'text-slate-400'}`}>{t}</button>)}
        </div>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
        <KPI l="Active" v={strategies.filter(s => s.live_trades > 0).length} />
        <KPI l="Avg Live WR" v={`${(strategies.filter(s => s.live_win_rate).reduce((a, s) => a + (s.live_win_rate || 0), 0) / Math.max(1, strategies.filter(s => s.live_win_rate).length)).toFixed(0)}%`} pos={true} />
        <KPI l="Total Trades" v={strategies.reduce((a, s) => a + (s.live_trades || 0), 0)} />
        <KPI l="Best" v={strategies.sort((a, b) => (b.returns || 0) - (a.returns || 0))[0]?.strategy_name?.slice(0, 10) || '—'} pos={true} />
      </div>

      <div className="bg-slate-900/50 rounded-lg border border-white/5 overflow-hidden">
        <div className="px-3 py-2 border-b border-white/5">
          <span className="text-[10px] text-slate-500 uppercase font-bold">Strategy Comparison</span>
        </div>
        <table className="w-full text-xs">
          <thead className="text-[9px] text-slate-500 uppercase border-b border-white/10 bg-slate-900/30">
            <tr>
              {['Strategy', 'Tier', 'BT WR', 'Live WR', 'Δ WR', 'BT PF', 'Live PF', 'Returns'].map(h => 
                <th key={h} className="text-right py-2 px-2">{h}</th>)}
            </tr>
          </thead>
          <tbody className="divide-y divide-white/5">
            {strategies.map(s => {
              const delta = s.backtest_win_rate != null && s.live_win_rate != null ? s.live_win_rate - s.backtest_win_rate : null;
              return (
                <tr key={s.strategy_id} className="hover:bg-white/[0.02]">
                  <td className="py-2 px-2">
                    <div className="font-bold text-white">{s.strategy_name || s.strategy_id}</div>
                    <div className="text-[9px] text-slate-500">{s.asset_class}</div>
                  </td>
                  <td className="py-2 px-2 text-right">
                    <span className={`text-[10px] font-bold ${s.tier?.includes('T1') ? 'text-emerald-400' : s.tier?.includes('T2') ? 'text-amber-400' : 'text-slate-400'}`}>{s.tier || 'T4'}</span>
                  </td>
                  <td className="py-2 px-2 text-right font-mono text-slate-400">{s.backtest_win_rate != null ? `${s.backtest_win_rate.toFixed(0)}%` : '—'}</td>
                  <td className={`py-2 px-2 text-right font-mono font-bold ${pnlCl(s.live_win_rate - 50)}`}>{s.live_win_rate != null ? `${s.live_win_rate.toFixed(0)}%` : '—'}</td>
                  <td className={`py-2 px-2 text-right font-mono ${pnlCl(delta)}`}>{delta != null ? `${delta >= 0 ? '+' : ''}${delta.toFixed(0)}pp` : '—'}</td>
                  <td className="py-2 px-2 text-right font-mono text-slate-400">{s.backtest_pf?.toFixed(2) || '—'}</td>
                  <td className={`py-2 px-2 text-right font-mono ${pnlCl(s.live_profit_factor - 1.5)}`}>{s.live_profit_factor?.toFixed(2) || '—'}</td>
                  <td className={`py-2 px-2 text-right font-mono font-bold ${pnlCl(s.returns)}`}>{s.returns != null ? fmtPct(s.returns) : '—'}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
};

// Main App
export default function App() {
  const navigate = useNavigate();
  const location = useLocation();
  const { mode: urlMode } = useParams();
  
  const [data, setData] = useState({ strategies: [], positions: [], paperStrategies: [], dailyPnl: [], trades: [], summary: {}, mode: 'SIMULATION' });
  const [loading, setLoading] = useState(true);
  const [detail, setDetail] = useState(null);
  const [deploy, setDeploy] = useState(null);

  const pathParts = location.pathname.split('/').filter(Boolean);
  const currentMode = pathParts[0] || 'sim';
  const currentTab = pathParts[1] || 'command';

  // Sync mode with backend
  useEffect(() => {
    const sync = async () => {
      const modeData = await api.get('/api/execution/global-mode');
      const backendMode = modeData?.execution_mode || 'SIMULATION';
      const urlMode = currentMode === 'paper' ? 'PAPER_TRADING' : 'SIMULATION';
      if (backendMode !== urlMode && urlMode !== 'SIMULATION') {
        await api.post('/api/execution/global-mode', { execution_mode: urlMode });
      }
    };
    sync();
  }, [currentMode]);

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
        mode: 'SIMULATION'
      });
      setLoading(false);
    };
    
    fetchAll();
    const interval = setInterval(fetchAll, 60000);
    return () => clearInterval(interval);
  }, []);

  const navItems = [
    { id: 'command', label: 'Command', icon: Icons.Dashboard },
    { id: 'strategies', label: 'Strategies', icon: Icons.Strategies },
    { id: 'lab', label: 'Lab', icon: Icons.Chart },
    { id: 'research', label: 'Research', icon: Icons.Research },
    { id: 'performance', label: 'Performance', icon: Icons.Performance },
    { id: 'portfolio', label: 'Portfolio', icon: Icons.Portfolio },
    { id: 'markets', label: 'Markets', icon: Icons.Markets },
    { id: 'settings', label: 'Settings', icon: Icons.Settings },
  ];

  const navigateToTab = (tab) => navigate(`/${currentMode}/${tab}`);
  const modeColor = data.mode === 'LIVE_TRADING' ? 'rose' : data.mode === 'PAPER_TRADING' ? 'amber' : 'emerald';
  const isConnected = data.ibStatus?.connected;

  if (loading) return (
    <div className="min-h-screen bg-slate-950 flex items-center justify-center">
      <div className="text-slate-500 flex items-center gap-2">
        <div className="w-4 h-4 border-2 border-slate-600 border-t-blue-500 rounded-full animate-spin" />
        <span className="text-xs">Loading...</span>
      </div>
    </div>
  );

  return (
    <div className="min-h-screen bg-slate-950 text-white font-sans">
      <header className="fixed top-0 left-0 right-0 z-40 border-b border-white/5 bg-slate-950/90 backdrop-blur-xl">
        <div className="flex items-center justify-between px-3 py-2 max-w-[1800px] mx-auto">
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2">
              <div className="w-7 h-7 rounded bg-gradient-to-br from-blue-500 to-violet-600 flex items-center justify-center text-[11px] font-black">JT</div>
              <span className="text-xs font-bold text-white hidden md:inline">JTCML</span>
            </div>
            <nav className="hidden md:flex gap-1">
              {navItems.map(n => (
                <button key={n.id} onClick={() => navigateToTab(n.id)}
                  className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-bold transition-all ${currentTab === n.id ? 'bg-white text-black' : 'text-slate-400 hover:text-white hover:bg-white/5'}`}
                >
                  <span>{n.icon}</span><span>{n.label}</span>
                </button>
              ))}
            </nav>
          </div>
          <div className="flex items-center gap-2">
            <Pill c={modeColor}>{data.mode.replace('_TRADING', '').replace('_', ' ')}</Pill>
            <div className="flex items-center gap-1"><Dot on={isConnected} /><span className="text-[10px] text-slate-500 hidden sm:inline">IBKR</span></div>
            <span className="text-[10px] text-slate-600 hidden lg:inline">{new Date().toLocaleTimeString()}</span>
          </div>
        </div>
      </header>

      <main className="pt-16 md:pt-20 pb-20 md:pb-6 px-3 md:px-6 max-w-[1600px] mx-auto">
        {currentTab === 'portfolio' && <PortfolioTab data={data} />}
        {currentTab === 'performance' && <PerformanceTab data={data} />}
        {currentTab === 'markets' && <MarketsTab onTickerClick={t => setDetail(t)} />}
        {currentTab === 'settings' && <SettingsTab />}
        {currentTab === 'lab' && <StrategyLab />}
        {currentTab === 'research' && <ResearchTab onTickerClick={t => setDetail(t)} />}
        {currentTab === 'command' && (
          <div className="space-y-4">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
              <KPI l="Strategies" v={data.strategies.length} />
              <KPI l="Positions" v={data.positions.length} />
              <KPI l="P&L Today" v={fmtK(data.dailyPnl[0]?.pnl)} pos={data.dailyPnl[0]?.pnl >= 0} />
              <KPI l="Win Rate" v={`${(data.summary?.win_rate * 100 || 0).toFixed(1)}%`} pos={data.summary?.win_rate > 0.5} />
            </div>
          </div>
        )}
      </main>

      <nav className="bottom-nav md:hidden">
        <div className="flex items-center justify-around px-2 py-1">
          {navItems.slice(0, 5).map(n => (
            <button key={n.id} onClick={() => navigateToTab(n.id)} className={`flex flex-col items-center gap-0.5 px-3 py-1 rounded-lg ${currentTab === n.id ? 'text-blue-400' : 'text-slate-500'}`}>
              <span className="text-lg">{n.icon}</span><span className="text-[9px] font-medium">{n.label}</span>
            </button>
          ))}
        </div>
      </nav>
    </div>
  );
}
