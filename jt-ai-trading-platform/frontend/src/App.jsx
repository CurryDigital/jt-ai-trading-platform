import React, { useState, useEffect, useMemo, useCallback } from 'react';
import { ProfessionalLiveTrading } from './ProfessionalLiveTrading';
import { ProfessionalSimulationLab } from './ProfessionalSimulationLab';
import { StockDetailModal } from './components/StockDetailModal';
import { StrategyDashboard } from './components/StrategyDashboard';
import { GoldenStrategies } from './components/GoldenStrategies';
import { ResearchTab } from './components/ResearchTab';
import { MarketsTab } from './components/MarketsTab';
import { StrategyPerformance } from './components/StrategyPerformance';
import { GlobalExecutionToggle } from './components/GlobalExecutionToggle';
import { SettingsTab } from './components/SettingsTab';

// =============================================================================
// JT AI TRADING PLATFORM v3.0 - QUANT REVAMP
// =============================================================================

// --- UTILS & HELPERS ---
const formatNumber = (num, decimals = 2) => {
  if (num === null || num === undefined || isNaN(num)) return '---';
  return num.toLocaleString(undefined, { minimumFractionDigits: decimals, maximumFractionDigits: decimals });
};

const formatCurrency = (num, currency = '$') => {
  if (num === null || num === undefined || isNaN(num)) return '---';
  const absVal = Math.abs(num);
  if (absVal >= 1e9) return `${currency}${(num / 1e9).toFixed(2)}B`;
  if (absVal >= 1e6) return `${currency}${(num / 1e6).toFixed(2)}M`;
  if (absVal >= 1e3) return `${currency}${(num / 1e3).toFixed(2)}K`;
  return `${currency}${num.toFixed(2)}`;
};

const formatPercent = (num, decimals = 2) => {
  if (num === null || num === undefined || isNaN(num)) return '---';
  const sign = num >= 0 ? '+' : '';
  return `${sign}${num.toFixed(decimals)}%`;
};

const getPnLColor = (val) => {
  if (val === null || val === undefined) return 'text-slate-400';
  return val >= 0 ? 'text-emerald-400' : 'text-rose-400';
};

const getPnLBg = (val) => {
  if (val === null || val === undefined) return 'bg-slate-500/10';
  return val >= 0 ? 'bg-emerald-500/10' : 'bg-rose-500/10';
};

// --- ICONS (SVG Components) ---
const Icons = {
  Dashboard: () => (
    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18c-4.41 0-8-3.59-8-8s3.59-8 8-8 8 3.59 8 8-3.59 8-8 8zm0-14c-3.31 0-6 2.69-6 6s2.69 6 6 6 6-2.69 6-6-2.69-6-6-6zm0 10c-2.21 0-4-1.79-4-4s1.79-4 4-4 4 1.79 4 4-1.79 4-4 4z" />
    </svg>
  ),
  Portfolio: () => (
    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01" />
    </svg>
  ),
  Research: () => (
    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
    </svg>
  ),
  Markets: () => (
    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 002 2h2a2 2 0 002-2z" />
    </svg>
  ),
  Strategies: () => (
    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z" />
    </svg>
  ),
  Settings: () => (
    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
    </svg>
  ),
  Alert: () => (
    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
    </svg>
  ),
  TrendUp: () => (
    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
    </svg>
  ),
  TrendDown: () => (
    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 17h8m0 0V9m0 8l-8-8-4 4-6-6" />
    </svg>
  ),
  Chart: () => (
    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
    </svg>
  ),
  Performance: () => (
    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 002 2h2a2 2 0 002-2z" />
    </svg>
  ),
  Menu: () => (
    <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
    </svg>
  ),
  Close: () => (
    <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
    </svg>
  ),
};

// --- ANALYST TARGET COMPONENT ---
const AnalystTargetCell = ({ ticker }) => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!ticker) return;
    
    fetch(`/api/stocks/${ticker}/institutional`)
      .then(r => r.json())
      .then(d => {
        setData(d.consensus);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, [ticker]);

  if (loading) return <span className="text-xs text-slate-500">...</span>;
  if (!data || !data.target_mean) return <span className="text-xs text-slate-500">—</span>;

  const upside = data.upside_pct;
  const color = upside > 20 ? 'text-emerald-400' : upside > 0 ? 'text-blue-400' : 'text-rose-400';
  
  return (
    <div className="flex flex-col items-center">
      <span className="text-xs font-mono text-white">${data.target_mean.toFixed(0)}</span>
      <span className={`text-[10px] ${color}`}>{upside > 0 ? '+' : ''}{upside.toFixed(1)}%</span>
      <span className="text-[9px] text-slate-500">{data.total_analysts} analysts</span>
    </div>
  );
};

// --- SPARKLINE COMPONENT ---
const Sparkline = ({ data, color = "#10b981", width = 80, height = 28 }) => {
  if (!data || data.length === 0) return <div style={{width, height}} className="bg-slate-800/50 rounded" />;
  const min = Math.min(...data);
  const max = Math.max(...data);
  const range = max - min || 1;
  const points = data.map((val, i) => 
    `${(i / (data.length - 1)) * width},${height - ((val - min) / range) * height}`
  ).join(' ');
  const isPositive = data[data.length - 1] >= data[0];
  const strokeColor = isPositive ? '#10b981' : '#f43f5e';
  return (
    <svg width={width} height={height} className="overflow-visible">
      <defs>
        <linearGradient id={`grad-${color}`} x1="0%" y1="0%" x2="0%" y2="100%">
          <stop offset="0%" stopColor={strokeColor} stopOpacity="0.3" />
          <stop offset="100%" stopColor={strokeColor} stopOpacity="0" />
        </linearGradient>
      </defs>
      <polygon 
        points={`0,${height} ${points} ${width},${height}`} 
        fill={`url(#grad-${color})`} 
      />
      <polyline 
        fill="none" 
        stroke={strokeColor} 
        strokeWidth="2" 
        points={points} 
        strokeLinejoin="round" 
        strokeLinecap="round" 
      />
    </svg>
  );
};

// --- METRIC CARD COMPONENT ---
const MetricCard = ({ label, value, subtext, trend, isPositive, icon: Icon, color = 'blue', large = false }) => {
  const colorClasses = {
    blue: 'from-blue-500/20 to-blue-600/5 border-blue-500/30',
    emerald: 'from-emerald-500/20 to-emerald-600/5 border-emerald-500/30',
    rose: 'from-rose-500/20 to-rose-600/5 border-rose-500/30',
    amber: 'from-amber-500/20 to-amber-600/5 border-amber-500/30',
    violet: 'from-violet-500/20 to-violet-600/5 border-violet-500/30',
  }[color];

  return (
    <div className={`relative overflow-hidden rounded-xl bg-gradient-to-br ${colorClasses} border p-4 ${large ? 'p-6' : ''}`}>
      <div className="flex items-start justify-between">
        <div>
          <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">{label}</p>
          <p className={`${large ? 'text-3xl' : 'text-xl'} font-black text-white mt-1 font-mono tracking-tight`}>
            {value}
          </p>
          {subtext && (
            <p className={`text-xs mt-1 font-medium ${isPositive !== undefined ? (isPositive ? 'text-emerald-400' : 'text-rose-400') : 'text-slate-400'}`}>
              {subtext}
            </p>
          )}
        </div>
        {Icon && (
          <div className={`p-2 rounded-lg bg-white/5 ${isPositive !== undefined ? (isPositive ? 'text-emerald-400' : 'text-rose-400') : 'text-slate-400'}`}>
            <Icon />
          </div>
        )}
      </div>
      {trend && (
        <div className="absolute bottom-0 left-0 right-0 h-16 opacity-20">
          <Sparkline data={trend} width={200} height={64} />
        </div>
      )}
    </div>
  );
};

// --- P&L BADGE ---
const PnLBadge = ({ value, size = 'md', showSign = true }) => {
  const isPos = value >= 0;
  const sizeClasses = {
    sm: 'text-xs px-2 py-0.5',
    md: 'text-sm px-2.5 py-1',
    lg: 'text-base px-3 py-1.5'
  };
  return (
    <span className={`inline-flex items-center gap-1 font-mono font-bold rounded-lg ${sizeClasses[size]} ${
      isPos ? 'bg-emerald-500/20 text-emerald-400' : 'bg-rose-500/20 text-rose-400'
    }`}>
      {isPos ? '▲' : '▼'}
      {showSign && isPos ? '+' : ''}{formatPercent(value)}
    </span>
  );
};

// --- STATUS BADGE ---
const StatusBadge = ({ status, text }) => {
  const colors = {
    live: 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30',
    paper: 'bg-blue-500/20 text-blue-400 border-blue-500/30',
    simulation: 'bg-amber-500/20 text-amber-400 border-amber-500/30',
    offline: 'bg-slate-500/20 text-slate-400 border-slate-500/30',
    error: 'bg-rose-500/20 text-rose-400 border-rose-500/30',
  };
  return (
    <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[10px] font-black uppercase tracking-wider border ${colors[status] || colors.offline}`}>
      <span className={`w-1.5 h-1.5 rounded-full ${status === 'live' ? 'animate-pulse bg-emerald-400' : 'bg-current'}`} />
      {text || status}
    </span>
  );
};

// =============================================================================
// MAIN APP COMPONENT
// =============================================================================

function App() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [marketAsset, setMarketAsset] = useState('fx'); // fx, crypto, commodities, stocks
  const [timeRange, setTimeRange] = useState('1D');
  const [data, setData] = useState({
    portfolio: { value: 0, pnl: 0, positions: [] },
    signals: [],
    fx: [],
    crypto: [],
    commodities: [],
    macro: {},
    performance: {}
  });
  const [loading, setLoading] = useState(true);
  const [lastUpdate, setLastUpdate] = useState(null);
  const [ibStatus, setIbStatus] = useState({ socket: 'Offline', web: 'Unauthorized' });
  const [recentTrades, setRecentTrades] = useState([]);
  const [dailyPnL, setDailyPnL] = useState([]);
  const [tradePrices, setTradePrices] = useState({}); // Store current prices for recent trades
  
  // Stock detail modal state
  const [selectedTicker, setSelectedTicker] = useState(null);
  const [isDetailModalOpen, setIsDetailModalOpen] = useState(false);
  
  // Mobile menu state
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  // Memoized handlers to prevent re-renders
  const handleTickerClick = useCallback((ticker) => {
    setSelectedTicker(ticker);
    setIsDetailModalOpen(true);
  }, []);

  // --- DATA FETCHING ---
  useEffect(() => {
    const fetchData = async () => {
      try {
        const endpoints = [
          'macro/pulse', 'signals/1', 'fx/pairs', 'crypto/pairs', 
          'commodities/all', 'inventory/evaluate', 'performance/strategy',
          'velocity/ib/status', 'velocity/summary', 'velocity/trades', 'performance/daily-pnl'
        ];
        const responses = await Promise.all(
          endpoints.map(e => fetch(`/api/${e}`).then(r => r.json()).catch(() => null))
        );
        
        setData({
          macro: responses[0] || {},
          signals: responses[1] || [],
          fx: responses[2] || [],
          crypto: responses[3] || [],
          commodities: responses[4] || [],
          portfolio: { positions: responses[5] || [], ...responses[7] },
          performance: responses[6] || {},
          ibStatus: responses[7] || { socket: 'Offline', web: 'Unauthorized' }
        });
        setIbStatus(responses[7] || { socket: 'Offline', web: 'Unauthorized' });
        
        // Recent trades (last 10)
        const trades = responses[9] || [];
        setRecentTrades(trades.slice(-10).reverse());
        
        // Fetch current prices for recent trades
        const tradeTickers = [...new Set(trades.slice(-10).map(t => t.ticker))];
        if (tradeTickers.length > 0) {
          fetch(`/api/market-data?tickers=${tradeTickers.join(',')}`)
            .then(r => r.json())
            .then(priceData => {
              const prices = {};
              priceData.data?.forEach(item => {
                prices[item.ticker] = item.price;
              });
              setTradePrices(prices);
            })
            .catch(() => {});
        }
        
        // Daily P&L
        const pnlData = responses[10] || {};
        setDailyPnL(pnlData.daily || []);
        
        setLastUpdate(new Date());
      } catch (e) {
        console.error('Data fetch error:', e);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
    const interval = setInterval(fetchData, 30000);
    return () => clearInterval(interval);
  }, []);

  // --- TAB CONFIGURATION ---
  const tabs = [
    { id: 'dashboard', label: 'Dashboard', icon: Icons.Dashboard },
    { id: 'strategies', label: 'Strategies', icon: Icons.Strategies },
    { id: 'research', label: 'Research', icon: Icons.Research },
    { id: 'performance', label: 'Performance', icon: Icons.Performance },
    { id: 'portfolio', label: 'Portfolio', icon: Icons.Portfolio },
    { id: 'markets', label: 'Markets', icon: Icons.Markets },
    { id: 'settings', label: 'Settings', icon: Icons.Settings },
  ];

  // =============================================================================
  // DASHBOARD TAB - Executive Overview
  // =============================================================================
  const DashboardTab = () => {
    const portfolioValue = data.portfolio?.inventory_value || 0;
    const todayPnl = data.portfolio?.today_pnl || 0;
    const pnlPercent = portfolioValue > 0 ? (todayPnl / portfolioValue) * 100 : 0;
    const activePositions = data.portfolio?.active_positions || 0;
    
    return (
      <div className="space-y-6 animate-in fade-in duration-500">
        {/* Header Status Bar */}
        <div className="flex flex-wrap items-center justify-between gap-4 p-4 rounded-xl bg-slate-900/50 border border-white/5">
          <div className="flex items-center gap-6">
            <div className="flex items-center gap-2">
              <div className={`w-2 h-2 rounded-full ${ibStatus.socket === 'Connected' ? 'bg-emerald-500 animate-pulse' : 'bg-rose-500'}`} />
              <span className="text-xs font-medium text-slate-400">IBKR</span>
              <StatusBadge 
                status={ibStatus.socket === 'Connected' ? 'live' : 'offline'} 
                text={ibStatus.socket === 'Connected' ? 'Live' : 'Disconnected'} 
              />
            </div>
            <div className="h-4 w-px bg-white/10" />
            <div className="flex items-center gap-2">
              <span className="text-xs font-medium text-slate-400">Market Status</span>
              <StatusBadge status="live" text="Open" />
            </div>
            <div className="h-4 w-px bg-white/10" />
            <div className="text-xs text-slate-500">
              Last Update: {lastUpdate?.toLocaleTimeString() || '---'}
            </div>
          </div>
          <div className="flex items-center gap-2">
            {['1D', '1W', '1M', '3M', 'YTD'].map(range => (
              <button
                key={range}
                onClick={() => setTimeRange(range)}
                className={`px-3 py-1.5 rounded-lg text-[10px] font-bold uppercase tracking-wider transition-all ${
                  timeRange === range 
                    ? 'bg-white text-black' 
                    : 'text-slate-400 hover:text-white hover:bg-white/5'
                }`}
              >
                {range}
              </button>
            ))}
          </div>
        </div>

        {/* Key Metrics Grid */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <MetricCard
            label="Portfolio Value"
            value={formatCurrency(portfolioValue)}
            subtext={pnlPercent !== 0 ? formatPercent(pnlPercent) + ' today' : undefined}
            isPositive={pnlPercent >= 0}
            icon={Icons.Portfolio}
            color={pnlPercent >= 0 ? 'emerald' : 'rose'}
            large
          />
          <MetricCard
            label="Today's P&L"
            value={formatCurrency(todayPnl)}
            subtext="Realized + Unrealized"
            isPositive={todayPnl >= 0}
            icon={todayPnl >= 0 ? Icons.TrendUp : Icons.TrendDown}
            color={todayPnl >= 0 ? 'emerald' : 'rose'}
            large
          />
          <MetricCard
            label="Active Positions"
            value={activePositions}
            subtext="Across all asset classes"
            icon={Icons.Dashboard}
            color="blue"
            large
          />
          
          {/* Mini P&L Trend */}
          <div className="bg-slate-900/50 border border-white/10 rounded-xl p-4 flex flex-col justify-between">
            <div className="flex items-center justify-between">
              <span className="text-xs text-slate-500 uppercase">P&L Trend</span>
              <Icons.Chart className="w-4 h-4 text-slate-400" />
            </div>
            
            {dailyPnL.length > 0 ? (
              <>
                <div className="flex items-end gap-1 h-12 mt-2">
                  {dailyPnL.slice(-7).map((day, idx) => {
                    const maxPnL = Math.max(...dailyPnL.slice(-7).map(d => Math.abs(d.pnl)), 100);
                    const height = Math.max(15, (Math.abs(day.pnl) / maxPnL) * 100);
                    return (
                      <div
                        key={idx}
                        className={`flex-1 rounded-t ${day.pnl >= 0 ? 'bg-emerald-500' : 'bg-rose-500'}`}
                        style={{ height: `${height}%`, minHeight: '4px' }}
                        title={`${day.date}: ${day.pnl >= 0 ? '+' : ''}$${day.pnl.toFixed(2)}`}
                      />
                    );
                  })}
                </div>
                <div className="flex justify-between text-[10px] text-slate-500 mt-1">
                  <span>{dailyPnL.slice(-7)[0]?.date?.slice(5)}</span>
                  <span>Today</span>
                </div>
              </>
            ) : (
              <div className="flex items-center justify-center h-12 text-xs text-slate-500">
                No data yet
              </div>
            )}
          </div>
        </div>

        {/* Main Content Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Top Signals */}
          <div className="lg:col-span-2 space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-black text-white uppercase tracking-wider flex items-center gap-2">
                <span className="w-1.5 h-1.5 rounded-full bg-blue-500" />
                Top Alpha Signals
              </h3>
              <button 
                onClick={() => setActiveTab('research')}
                className="text-xs text-blue-400 hover:text-blue-300 font-medium"
              >
                View All →
              </button>
            </div>
            <div className="space-y-2">
              {data.signals.slice(0, 5).map((signal, idx) => (
                <div key={idx} className="flex items-center justify-between p-3 rounded-lg bg-slate-900/50 border border-white/5 hover:border-white/10 transition-colors">
                  <div className="flex items-center gap-4">
                    <span className="text-xs font-mono text-slate-500 w-8">{idx + 1}</span>
                    <div>
                      <p className="text-sm font-bold text-white">{signal.ticker}</p>
                      <p className="text-xs text-slate-500">{signal.market || 'Global'}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-6">
                    <div className="text-right">
                      <p className="text-sm font-mono text-white">${signal.price}</p>
                      <PnLBadge value={signal.change} size="sm" />
                    </div>
                    <div className="text-right w-20">
                      <p className="text-xs text-slate-400">Confidence</p>
                      <p className={`text-sm font-bold ${signal.total_conf > 80 ? 'text-emerald-400' : signal.total_conf > 60 ? 'text-blue-400' : 'text-amber-400'}`}>
                        {signal.total_conf}%
                      </p>
                    </div>
                    <div className={`px-3 py-1.5 rounded-lg text-xs font-bold uppercase ${
                      signal.action === 'BUY' ? 'bg-emerald-500/20 text-emerald-400' : 
                      signal.action === 'SELL' ? 'bg-rose-500/20 text-rose-400' : 
                      'bg-amber-500/20 text-amber-400'
                    }`}>
                      {signal.action}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Side Panel */}
          <div className="space-y-4">
            {/* Market Mood */}
            <div className="p-4 rounded-xl bg-slate-900/50 border border-white/5">
              <h4 className="text-xs font-black text-slate-400 uppercase tracking-wider mb-3">Market Mood</h4>
              <div className="flex items-center justify-between mb-2">
                <span className="text-2xl font-black text-white">{data.macro?.market_mood || 'Neutral'}</span>
                <div className="flex gap-1">
                  {[1,2,3,4,5].map(i => (
                    <div key={i} className={`w-2 h-6 rounded-full ${i <= 3 ? 'bg-emerald-500' : 'bg-slate-700'}`} />
                  ))}
                </div>
              </div>
              <p className="text-xs text-slate-500 leading-relaxed">
                {data.macro?.swarm_conclusion?.slice(0, 100) || 'Market analysis pending...'}
              </p>
            </div>

            {/* Quick Stats - Calculated from actual positions */}
            <div className="p-4 rounded-xl bg-slate-900/50 border border-white/5 space-y-3">
              <h4 className="text-xs font-black text-slate-400 uppercase tracking-wider">Performance</h4>
              
              {/* Only show if positions exist */}
              {data.portfolio?.positions?.length > 0 ? (
                <>
                  <div className="flex justify-between items-center">
                    <span className="text-xs text-slate-500">Active Positions</span>
                    <span className="text-sm font-mono font-bold text-white">{data.portfolio.positions.length}</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-xs text-slate-500">Avg Win Rate</span>
                    <span className="text-sm font-mono font-bold text-blue-400">
                      {(data.signals.reduce((acc, s) => acc + (s.win_rate || 0), 0) / (data.signals.length || 1) * 100).toFixed(1)}%
                    </span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-xs text-slate-500">Avg AI Confidence</span>
                    <span className="text-sm font-mono font-bold text-violet-400">
                      {(data.signals.reduce((acc, s) => acc + (s.total_conf || 0), 0) / (data.signals.length || 1) * 100).toFixed(1)}%
                    </span>
                  </div>
                </>
              ) : (
                <p className="text-xs text-slate-500 italic">Add positions to see performance metrics</p>
              )}
            </div>

            {/* Alerts */}
            <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/20">
              <div className="flex items-center gap-2 mb-2">
                <Icons.Alert />
                <span className="text-xs font-black text-rose-400 uppercase tracking-wider">Risk Alerts</span>
              </div>
              <p className="text-xs text-slate-400">No active alerts. All systems operational.</p>
            </div>
            
            {/* Recent Trades Widget */}
            <div className="p-4 rounded-xl bg-slate-900/50 border border-white/5">
              <div className="flex items-center justify-between mb-3">
                <h4 className="text-xs font-black text-slate-400 uppercase tracking-wider">Recent Activity</h4>
                <button 
                  onClick={() => setActiveTab('performance')}
                  className="text-[10px] text-blue-400 hover:text-blue-300"
                >
                  View All →
                </button>
              </div>
              
              {recentTrades.length > 0 ? (
                <div className="space-y-2">
                  {recentTrades.slice(0, 5).map((trade, idx) => {
                    const currentPrice = tradePrices[trade.ticker];
                    const entryPrice = trade.entry_price;
                    const pnlPct = currentPrice && entryPrice 
                      ? ((currentPrice - entryPrice) / entryPrice) * 100 
                      : null;
                    
                    return (
                      <div key={idx} className="flex items-center justify-between py-2 border-b border-white/5 last:border-0">
                        <div className="flex items-center gap-2">
                          <span className={`text-[10px] px-1.5 py-0.5 rounded font-bold ${
                            trade.side === 'BUY' ? 'bg-emerald-500/20 text-emerald-400' : 'bg-rose-500/20 text-rose-400'
                          }`}>
                            {trade.side}
                          </span>
                          <span className="text-xs font-bold text-white">{trade.ticker}</span>
                        </div>
                        <div className="flex items-center gap-3">
                          {/* Entry Price */}
                          <div className="text-right">
                            <span className="text-[9px] text-slate-500 block">Entry</span>
                            <span className="text-[10px] text-slate-400">${entryPrice?.toFixed(2)}</span>
                          </div>
                          
                          {/* Current Price */}
                          {currentPrice ? (
                            <div className="text-right">
                              <span className="text-[9px] text-slate-500 block">Now</span>
                              <span className="text-[10px] text-white">${currentPrice.toFixed(2)}</span>
                            </div>
                          ) : (
                            <div className="text-right">
                              <span className="text-[9px] text-slate-500 block">Now</span>
                              <span className="text-[10px] text-slate-600">--</span>
                            </div>
                          )}
                          
                          {/* P&L % */}
                          {pnlPct !== null ? (
                            <div className="text-right w-14">
                              <span className="text-[9px] text-slate-500 block">P&L</span>
                              <span className={`text-[10px] font-bold ${pnlPct >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                                {pnlPct >= 0 ? '+' : ''}{pnlPct.toFixed(1)}%
                              </span>
                            </div>
                          ) : (
                            <div className="text-right w-14">
                              <span className="text-[9px] text-slate-500 block">P&L</span>
                              <span className="text-[10px] text-slate-600">--</span>
                            </div>
                          )}
                        </div>
                      </div>
                    );
                  })}
                </div>
              ) : (
                <p className="text-xs text-slate-500 italic">No recent trades</p>
              )}
            </div>
          </div>
        </div>
      </div>
    );
  };

  // =============================================================================
  // PORTFOLIO TAB - Fixed with Close Position Feature
  // =============================================================================
  const PortfolioTab = () => {
    const [positions, setPositions] = useState([]);
    const [loading, setLoading] = useState(true);
    const [totals, setTotals] = useState({ total_value: 0, total_pnl: 0, total_positions: 0 });
    const [closingPosition, setClosingPosition] = useState(null);
    const [closeMessage, setCloseMessage] = useState(null);
    
    // Search and filter state
    const [positionSearch, setPositionSearch] = useState('');
    const [positionAssetFilter, setPositionAssetFilter] = useState('ALL');
    const [positionMarketFilter, setPositionMarketFilter] = useState('ALL');

    // Fetch positions from new API
    useEffect(() => {
      fetchPositions();
    }, []);

    const fetchPositions = async () => {
      try {
        const res = await fetch('/api/portfolio/positions');
        if (res.ok) {
          const data = await res.json();
          setPositions(data.positions || []);
          setTotals({
            total_value: data.total_value || 0,
            total_pnl: data.total_pnl || 0,
            total_positions: data.total_positions || 0
          });
        }
      } catch (e) {
        console.error('Failed to fetch positions:', e);
      } finally {
        setLoading(false);
      }
    };

    // Close position handler
    const handleClosePosition = async (positionId, ticker) => {
      if (!confirm(`Are you sure you want to close position ${ticker}?`)) return;
      
      setClosingPosition(positionId);
      try {
        const res = await fetch(`/api/positions/${positionId}/close`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' }
        });
        
        if (res.ok) {
          const result = await res.json();
          setCloseMessage({ type: 'success', text: result.message });
          // Refresh positions
          fetchPositions();
          // Also refresh strategy data
          setTimeout(() => window.location.reload(), 2000);
        } else {
          const err = await res.json();
          setCloseMessage({ type: 'error', text: err.detail || 'Failed to close position' });
        }
      } catch (e) {
        setCloseMessage({ type: 'error', text: 'Network error' });
      } finally {
        setClosingPosition(null);
        setTimeout(() => setCloseMessage(null), 5000);
      }
    };

    // Filter positions
    const filteredPositions = positions.filter(pos => {
      if (positionSearch && !pos.ticker?.toLowerCase().includes(positionSearch.toLowerCase())) return false;
      if (positionAssetFilter !== 'ALL' && pos.asset_class !== positionAssetFilter) return false;
      if (positionMarketFilter !== 'ALL') {
        const ticker = pos.ticker || '';
        const isHK = ticker.endsWith('.HK');
        const isCN = ticker.endsWith('.SS') || ticker.endsWith('.SZ');
        const isSG = ticker.endsWith('.SI');
        const isUS = !isHK && !isCN && !isSG;
        if (positionMarketFilter === 'HK' && !isHK) return false;
        if (positionMarketFilter === 'CN' && !isCN) return false;
        if (positionMarketFilter === 'SG' && !isSG) return false;
        if (positionMarketFilter === 'US' && !isUS) return false;
      }
      return true;
    });

    if (loading) {
      return (
        <div className="p-12 text-center text-slate-500">
          <div className="w-8 h-8 border-2 border-slate-600 border-t-blue-500 rounded-full animate-spin mx-auto mb-4" />
          Loading Portfolio...
        </div>
      );
    }

    return (
      <div className="space-y-6 animate-in fade-in duration-500">
        {/* Close Message */}
        {closeMessage && (
          <div className={`p-4 rounded-xl ${closeMessage.type === 'success' ? 'bg-emerald-500/10 border border-emerald-500/30' : 'bg-rose-500/10 border border-rose-500/30'}`}>
            <p className={`text-sm ${closeMessage.type === 'success' ? 'text-emerald-400' : 'text-rose-400'}`}>
              {closeMessage.text}
            </p>
          </div>
        )}

        {/* Portfolio Header */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-slate-900/50 border border-white/10 rounded-xl p-4">
            <span className="text-xs text-slate-500 uppercase">Total Portfolio Value</span>
            <p className="text-2xl font-bold text-white mt-1">{formatCurrency(totals.total_value)}</p>
          </div>
          <div className="bg-slate-900/50 border border-white/10 rounded-xl p-4">
            <span className="text-xs text-slate-500 uppercase">Total Unrealized P&L</span>
            <p className={`text-2xl font-bold mt-1 ${totals.total_pnl >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
              {totals.total_pnl >= 0 ? '+' : ''}{formatCurrency(totals.total_pnl)}
            </p>
          </div>
          <div className="bg-slate-900/50 border border-white/10 rounded-xl p-4">
            <span className="text-xs text-slate-500 uppercase">Active Positions</span>
            <p className="text-2xl font-bold text-white mt-1">{totals.total_positions}</p>
          </div>
        </div>

        {/* Positions Table */}
        <div className="rounded-xl border border-white/10 overflow-hidden">
          <div className="p-4 border-b border-white/10 bg-slate-900/50">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
              <h3 className="text-sm font-black text-white uppercase tracking-wider">All Positions</h3>
              
              {/* Search and Filters */}
              <div className="flex flex-wrap items-center gap-3">
                <div className="relative">
                  <span className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500 text-xs">🔍</span>
                  <input
                    type="text"
                    placeholder="Search ticker..."
                    value={positionSearch}
                    onChange={(e) => setPositionSearch(e.target.value)}
                    className="pl-8 pr-3 py-1.5 bg-slate-800 border border-white/10 rounded-lg text-white text-xs placeholder-slate-500 focus:border-blue-500/50 focus:outline-none w-32"
                  />
                </div>
                
                <select
                  value={positionAssetFilter}
                  onChange={(e) => setPositionAssetFilter(e.target.value)}
                  className="bg-slate-800 border border-white/10 rounded-lg px-3 py-1.5 text-xs text-white focus:border-blue-500/50 focus:outline-none"
                >
                  <option value="ALL">All Assets</option>
                  <option value="STOCK">Stocks</option>
                  <option value="FX">FX</option>
                  <option value="CRYPTO">Crypto</option>
                  <option value="COMMODITY">Commodities</option>
                </select>
                
                <select
                  value={positionMarketFilter}
                  onChange={(e) => setPositionMarketFilter(e.target.value)}
                  className="bg-slate-800 border border-white/10 rounded-lg px-3 py-1.5 text-xs text-white focus:border-blue-500/50 focus:outline-none"
                >
                  <option value="ALL">All Markets</option>
                  <option value="US">US</option>
                  <option value="HK">Hong Kong</option>
                  <option value="CN">China</option>
                  <option value="SG">Singapore</option>
                </select>
                
                <span className="text-xs text-slate-500">
                  {filteredPositions.length} of {positions.length}
                </span>
              </div>
            </div>
          </div>
          
          <table className="w-full">
            <thead className="bg-slate-900/30">
              <tr className="text-[10px] font-black text-slate-500 uppercase tracking-wider">
                <th className="text-left p-3">Asset</th>
                <th className="text-left p-3">Strategy</th>
                <th className="text-right p-3">Qty</th>
                <th className="text-right p-3">Entry</th>
                <th className="text-right p-3">Current</th>
                <th className="text-right p-3">Value</th>
                <th className="text-right p-3">P&L</th>
                <th className="text-center p-3">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5">
              {filteredPositions.map((pos) => (
                <tr key={pos.id} className="hover:bg-white/5 transition-colors">
                  <td className="p-3">
                    <div className="flex items-center gap-3">
                      <div className="w-8 h-8 rounded-lg bg-slate-800 flex items-center justify-center text-xs font-bold text-slate-400">
                        {pos.ticker?.slice(0, 2)}
                      </div>
                      <div>
                        <p className="text-sm font-bold text-white">{pos.ticker}</p>
                        <p className="text-[10px] text-slate-500 uppercase">{pos.asset_class}</p>
                      </div>
                    </div>
                  </td>
                  <td className="p-3">
                    <p className="text-xs text-slate-400 truncate max-w-[120px]">{pos.strategy}</p>
                  </td>
                  <td className="p-3 text-right">
                    <p className="text-sm font-mono text-white">{formatNumber(pos.quantity, 2)}</p>
                  </td>
                  <td className="p-3 text-right">
                    <p className="text-sm font-mono text-slate-400">${formatNumber(pos.entry_price)}</p>
                  </td>
                  <td className="p-3 text-right">
                    <p className="text-sm font-mono text-white">${formatNumber(pos.current_price)}</p>
                  </td>
                  <td className="p-3 text-right">
                    <p className="text-sm font-mono text-white">{formatCurrency(pos.market_value)}</p>
                  </td>
                  <td className="p-3 text-right">
                    <div className={`text-sm font-bold ${pos.pnl >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                      {pos.pnl >= 0 ? '+' : ''}{formatCurrency(pos.pnl)}
                    </div>
                    <div className={`text-[10px] ${pos.pnl_pct >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                      {pos.pnl_pct >= 0 ? '+' : ''}{pos.pnl_pct?.toFixed(2) || '0.00'}%
                    </div>
                  </td>
                  <td className="p-3 text-center">
                    <button
                      onClick={() => handleClosePosition(pos.id, pos.ticker)}
                      disabled={closingPosition === pos.id}
                      className="px-3 py-1.5 bg-rose-600 hover:bg-rose-500 disabled:bg-slate-700 text-white text-[10px] font-bold rounded-lg transition-colors"
                    >
                      {closingPosition === pos.id ? 'Closing...' : 'SELL'}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          
          {filteredPositions.length === 0 && (
            <div className="p-12 text-center text-slate-500">
              <div className="text-4xl mb-4">📭</div>
              <p>No positions found</p>
            </div>
          )}
        </div>
      </div>
    );
  };

  // --- STRATEGIES TAB - Uses GoldenStrategies Component ---
  const StrategiesTabContent = () => {
    return <GoldenStrategies />;
  };

  // =============================================================================
  // MAIN RENDER
  // =============================================================================
  return (
    <div className="min-h-screen bg-slate-950 text-white font-sans selection:bg-blue-500/30">
      {/* Header - Mobile Optimized */}
      <header className="fixed top-0 left-0 right-0 z-50 border-b border-white/5 bg-slate-950/80 backdrop-blur-xl">
        <div className="flex items-center justify-between px-3 md:px-6 py-2 md:py-3">
          {/* Logo */}
          <div className="flex items-center gap-2 md:gap-3">
            <div className="w-7 h-7 md:w-8 md:h-8 rounded-lg bg-gradient-to-br from-blue-500 to-violet-600 flex items-center justify-center">
              <span className="text-xs md:text-sm font-black">JT</span>
            </div>
            <div className="hidden md:block">
              <h1 className="text-sm font-black tracking-tight">AI Trading Platform</h1>
              <p className="text-[10px] text-slate-500">Quantitative Research & Execution</p>
            </div>
            <div className="md:hidden">
              <h1 className="text-xs font-black tracking-tight">JT Trading</h1>
            </div>
          </div>

          {/* Desktop Navigation */}
          <nav className="hidden md:flex items-center gap-1">
            {tabs.map(tab => {
              const Icon = tab.icon;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-bold uppercase tracking-wider transition-all ${
                    activeTab === tab.id
                      ? 'bg-white text-black shadow-lg'
                      : 'text-slate-400 hover:text-white hover:bg-white/5'
                  }`}
                >
                  <Icon />
                  <span>{tab.label}</span>
                </button>
              );
            })}
          </nav>

          {/* Mobile Menu Button & Status */}
          <div className="flex items-center gap-2 md:gap-3">
            <div className="hidden md:block">
              <GlobalExecutionToggle />
            </div>
            
            <div className={`w-2 h-2 rounded-full ${ibStatus.socket === 'Connected' ? 'bg-emerald-500 animate-pulse' : 'bg-rose-500'}`} />
            <span className="text-[10px] md:text-xs text-slate-500 hidden sm:inline">
              {loading ? 'Syncing...' : 'Live'}
            </span>
            
            {/* Mobile Menu Toggle */}
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="md:hidden p-2 rounded-lg text-slate-400 hover:text-white hover:bg-white/5"
            >
              {mobileMenuOpen ? <Icons.Close /> : <Icons.Menu />}
            </button>
          </div>
        </div>
        
        {/* Mobile Navigation Drawer */}
        {mobileMenuOpen && (
          <nav className="md:hidden border-t border-white/5 bg-slate-950/95 backdrop-blur-xl">
            <div className="py-2 px-3">
              {tabs.map(tab => {
                const Icon = tab.icon;
                return (
                  <button
                    key={tab.id}
                    onClick={() => {
                      setActiveTab(tab.id);
                      setMobileMenuOpen(false);
                    }}
                    className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-bold transition-all mb-1 ${
                      activeTab === tab.id
                        ? 'bg-white text-black'
                        : 'text-slate-400 hover:text-white hover:bg-white/5'
                    }`}
                  >
                    <Icon />
                    <span>{tab.label}</span>
                  </button>
                );
              })}
              {/* Execution Mode Toggle for Mobile */}
              <div className="mt-3 pt-3 border-t border-white/10">
                <p className="text-[10px] text-slate-500 uppercase px-4 mb-2">Execution Mode</p>
                <div className="px-2">
                  <GlobalExecutionToggle />
                </div>
              </div>
            </div>
          </nav>
        )}
      </header>

      {/* Main Content - Mobile Optimized Padding */}
      <main className="pt-16 md:pt-20 pb-20 md:pb-6 px-3 md:px-6 max-w-[1600px] mx-auto">
        {loading && !data.signals.length ? (
          <div className="flex items-center justify-center h-[60vh]">
            <div className="flex items-center gap-3 text-slate-500">
              <div className="w-5 h-5 border-2 border-slate-600 border-t-blue-500 rounded-full animate-spin" />
              <span className="text-sm">Loading market data...</span>
            </div>
          </div>
        ) : (
          <>
            {activeTab === 'dashboard' && <DashboardTab />}
            {activeTab === 'strategies' && <StrategiesTabContent />}
            {activeTab === 'research' && <ResearchTab key="research-tab" onTickerClick={handleTickerClick} />}
            {activeTab === 'performance' && <StrategyPerformance />}
            {activeTab === 'portfolio' && <PortfolioTab />}
            {activeTab === 'markets' && <MarketsTab onTickerClick={handleTickerClick} />}
            {activeTab === 'settings' && <SettingsTab />}
          </>
        )}
      </main>

      {/* Mobile Bottom Navigation */}
      <nav className="md:hidden fixed bottom-0 left-0 right-0 z-50 border-t border-white/5 bg-slate-950/95 backdrop-blur-xl">
        <div className="flex items-center justify-around py-1">
          {tabs.slice(0, 5).map(tab => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex flex-col items-center gap-0.5 py-2 px-3 rounded-lg transition-all ${
                  isActive
                    ? 'text-white'
                    : 'text-slate-500 hover:text-slate-300'
                }`}
              >
                <div className={isActive ? "scale-110 transition-transform" : "transition-transform"}>
                  <Icon />
                </div>
                <span className="text-[9px] font-medium">{tab.label}</span>
              </button>
            );
          })}
        </div>
      </nav>

      {/* Stock Detail Modal */}
      <StockDetailModal 
        ticker={selectedTicker}
        isOpen={isDetailModalOpen}
        onClose={() => setIsDetailModalOpen(false)}
      />

      {/* Footer - Hidden on mobile since we have bottom nav */}
      <footer className="hidden md:block fixed bottom-0 left-0 right-0 border-t border-white/5 bg-slate-950/80 backdrop-blur-xl py-2 px-4 md:px-6">
        <div className="flex items-center justify-between text-[10px] text-slate-600">
          <div className="flex items-center gap-4">
            <span>v3.0 Quant Edition</span>
            <span className="hidden md:inline">•</span>
            <span className="hidden md:inline">Latency: 23ms</span>
          </div>
          <div className="flex items-center gap-4">
            <span>Last Update: {lastUpdate?.toLocaleTimeString() || '---'}</span>
            <span className="hidden md:inline">•</span>
            <span className="hidden md:inline text-slate-500">JTCML Trading Systems</span>
          </div>
        </div>
      </footer>
    </div>
  );
}

export default App;
