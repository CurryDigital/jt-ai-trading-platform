import React, { useState, useEffect, useMemo, useCallback } from 'react';
import { ProfessionalLiveTrading } from './ProfessionalLiveTrading';
import { ProfessionalSimulationLab } from './ProfessionalSimulationLab';
import { StockDetailModal } from './components/StockDetailModal';
import { StrategyDashboard } from './components/StrategyDashboard';
import { GoldenStrategiesImproved } from './components/GoldenStrategiesImproved';
import { DashboardTab } from './components/DashboardTab';
import { PortfolioTab } from './components/PortfolioTab';
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

  // =============================================================================
  // PORTFOLIO TAB - Fixed with Close Position Feature
  // =============================================================================
  // Signal Gauge Component
  const SignalGauge = ({ score }) => {
    let color = 'bg-slate-600';
    let emoji = '⚪';
    
    if (score >= 80) { color = 'bg-emerald-500'; emoji = '🟢'; }
    else if (score >= 50) { color = 'bg-amber-500'; emoji = '🟡'; }
    else if (score > 0) { color = 'bg-rose-500'; emoji = '🔴'; }
    
    return (
      <div className="flex items-center gap-2">
        <div className="w-16 h-2 bg-slate-700 rounded-full overflow-hidden">
          <div className={`h-full ${color}`} style={{ width: `${Math.min(score, 100)}%` }} />
        </div>
        <span className="text-xs font-bold text-white w-8">{emoji} {score}</span>
      </div>
    );
  };


  // --- STRATEGIES TAB - Uses Improved GoldenStrategies Component ---
  const StrategiesTabContent = () => {
    return <GoldenStrategiesImproved />;
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
