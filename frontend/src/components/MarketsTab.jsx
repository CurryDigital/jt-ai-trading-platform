import React, { useState, useEffect } from 'react';

// PnL Badge Component
const PnLBadge = ({ value, size = 'md' }) => {
  if (value === null || value === undefined) return <span className="text-slate-500">---</span>;
  
  const isPositive = value >= 0;
  const sizeClasses = size === 'sm' ? 'text-xs px-1.5 py-0.5' : 'text-sm px-2 py-1';
  
  return (
    <span className={`inline-flex items-center gap-0.5 rounded font-bold ${sizeClasses} ${
      isPositive ? 'bg-emerald-500/20 text-emerald-400' : 'bg-rose-500/20 text-rose-400'
    }`}>
      {isPositive ? '▲' : '▼'}
      {Math.abs(value).toFixed(2)}%
    </span>
  );
};

// Enhanced Markets Tab with Comprehensive Market Intelligence
export const MarketsTab = ({ onTickerClick }) => {
  const [activeView, setActiveView] = useState('overview');
  const [marketData, setMarketData] = useState({
    indices: [],
    gainers: [],
    losers: [],
    volumeLeaders: [],
    sectors: [],
    global: []
  });
  const [marketBreadth, setMarketBreadth] = useState({
    advancing: 0,
    declining: 0,
    unchanged: 0,
    newHighs: 0,
    newLows: 0
  });
  const [marketBreadthHK, setMarketBreadthHK] = useState({
    advancing: 0,
    declining: 0,
    unchanged: 0,
    newHighs: 0,
    newLows: 0
  });
  const [marketBreadthCN, setMarketBreadthCN] = useState({
    advancing: 0,
    declining: 0,
    unchanged: 0,
    newHighs: 0,
    newLows: 0
  });
  const [sentiment, setSentiment] = useState({
    fearGreed: null,
    fearGreedLabel: null,
    vix: null,
    putCall: null
  });
  const [sentimentHK, setSentimentHK] = useState({
    fearGreed: null,
    fearGreedLabel: null,
    vix: null,
    putCall: null
  });
  const [sentimentCN, setSentimentCN] = useState({
    fearGreed: null,
    fearGreedLabel: null,
    vix: null,
    putCall: null
  });
  const [loading, setLoading] = useState(true);
  const [selectedTimeframe, setSelectedTimeframe] = useState('1D');
  const [selectedMarket, setSelectedMarket] = useState('ALL'); // ALL, US, HK, CN, etc.

  // Helper to detect market from ticker
  const getMarketFromTicker = (ticker) => {
    if (!ticker) return 'US';
    if (ticker.endsWith('.HK')) return 'HK';
    if (ticker.startsWith('0') && ticker.length === 6) return 'CN'; // Shanghai/Shenzhen
    if (ticker.endsWith('.SS') || ticker.endsWith('.SZ')) return 'CN';
    if (ticker.endsWith('.TO') || ticker.endsWith('.V')) return 'CA';
    if (ticker.endsWith('.L')) return 'UK';
    if (ticker.endsWith('.DE') || ticker.endsWith('.XETRA')) return 'DE';
    if (ticker.endsWith('.PA') || ticker.endsWith('.EPA')) return 'FR';
    if (ticker.endsWith('.JP')) return 'JP';
    if (ticker.endsWith('.AU')) return 'AU';
    if (ticker.endsWith('.SG')) return 'SG';
    return 'US';
  };

  const marketFlags = {
    'US': '🇺🇸', 'HK': '🇭🇰', 'CN': '🇨🇳', 'JP': '🇯🇵', 'AU': '🇦🇺',
    'UK': '🇬🇧', 'DE': '🇩🇪', 'FR': '🇫🇷', 'CA': '🇨🇦', 'SG': '🇸🇬'
  };

  // Group stocks by market
  const groupByMarket = (stocks) => {
    const grouped = {};
    stocks.forEach(stock => {
      const market = getMarketFromTicker(stock.ticker);
      if (!grouped[market]) grouped[market] = [];
      grouped[market].push(stock);
    });
    return grouped;
  };

  useEffect(() => {
    fetchMarketData();
    const interval = setInterval(fetchMarketData, 60000);
    return () => clearInterval(interval);
  }, [selectedTimeframe]);

  const fetchMarketData = async () => {
    try {
      // Fetch indices
      const indicesRes = await fetch(`/api/market/indices?timeframe=${selectedTimeframe}`);
      const indices = indicesRes.ok ? await indicesRes.json() : [];

      // Fetch movers per market (US, HK, CN) to ensure each region has its own gainers/losers
      const [usMovers, hkMovers, cnMovers] = await Promise.all([
        fetch(`/api/market/movers?timeframe=${selectedTimeframe}&market=US`).then(r => r.ok ? r.json() : { gainers: [], losers: [] }),
        fetch(`/api/market/movers?timeframe=${selectedTimeframe}&market=HK`).then(r => r.ok ? r.json() : { gainers: [], losers: [] }),
        fetch(`/api/market/movers?timeframe=${selectedTimeframe}&market=CN`).then(r => r.ok ? r.json() : { gainers: [], losers: [] }),
      ]);

      // Combine all gainers and losers for the movers view
      const allGainers = [
        ...(usMovers.gainers || []),
        ...(hkMovers.gainers || []),
        ...(cnMovers.gainers || []),
      ];
      const allLosers = [
        ...(usMovers.losers || []),
        ...(hkMovers.losers || []),
        ...(cnMovers.losers || []),
      ];

      // Fetch sectors
      const sectorsRes = await fetch('/api/market/sectors');
      const sectors = sectorsRes.ok ? await sectorsRes.json() : [];

      // Fetch volume leaders
      const volumeRes = await fetch('/api/market/volume-leaders');
      const volumeLeaders = volumeRes.ok ? await volumeRes.json() : [];

      // Fetch global markets with cache-busting
      const globalRes = await fetch(`/api/market/global?_t=${Date.now()}`);
      const global = globalRes.ok ? await globalRes.json() : [];

      setMarketData({
        indices: indices.data || [],
        gainers: allGainers,
        losers: allLosers,
        volumeLeaders: volumeLeaders.data || [],
        sectors: sectors.data || [],
        global: global.data || []
      });

      // Fetch market breadth for US, HK, CN in parallel
      const [breadthUSRes, breadthHKRes, breadthCNRes] = await Promise.all([
        fetch('/api/market/breadth?country=US'),
        fetch('/api/market/breadth?country=HK'),
        fetch('/api/market/breadth?country=CN')
      ]);
      if (breadthUSRes.ok) setMarketBreadth(await breadthUSRes.json());
      if (breadthHKRes.ok) setMarketBreadthHK(await breadthHKRes.json());
      if (breadthCNRes.ok) setMarketBreadthCN(await breadthCNRes.json());

      // Fetch sentiment for US, HK, CN in parallel
      const [sentimentUSRes, sentimentHKRes, sentimentCNRes] = await Promise.all([
        fetch('/api/market/sentiment?country=US'),
        fetch('/api/market/sentiment?country=HK'),
        fetch('/api/market/sentiment?country=CN')
      ]);
      if (sentimentUSRes.ok) setSentiment(await sentimentUSRes.json());
      if (sentimentHKRes.ok) setSentimentHK(await sentimentHKRes.json());
      if (sentimentCNRes.ok) setSentimentCN(await sentimentCNRes.json());

      setLoading(false);
    } catch (e) {
      console.error('Failed to fetch market data:', e);
      setLoading(false);
    }
  };

  const timeframes = [
    { label: '1D', value: '1D' },
    { label: '1W', value: '1W' },
    { label: '1M', value: '1M' },
    { label: 'YTD', value: 'YTD' },
  ];

  const views = [
    { id: 'overview', label: '📊 Overview', desc: 'Indices & Sentiment' },
    { id: 'movers', label: '🚀 Movers', desc: 'Gainers & Losers' },
    { id: 'sectors', label: '🏭 Sectors', desc: 'Industry Performance' },
    { id: 'global', label: '🌍 Global', desc: 'World Markets' },
    { id: 'breadth', label: '📈 Breadth', desc: 'Market Internals' },
    { id: 'calendar', label: '📅 Calendar', desc: 'Economic Events' },
  ];

  // Helper for color coding
  const getPerformanceColor = (change) => {
    if (change > 5) return 'text-emerald-400';
    if (change > 2) return 'text-emerald-300';
    if (change > 0) return 'text-emerald-200';
    if (change < -5) return 'text-rose-400';
    if (change < -2) return 'text-rose-300';
    if (change < 0) return 'text-rose-200';
    return 'text-slate-400';
  };

  const getPerformanceBg = (change) => {
    if (change > 5) return 'bg-emerald-500/20';
    if (change > 2) return 'bg-emerald-500/10';
    if (change > 0) return 'bg-emerald-500/5';
    if (change < -5) return 'bg-rose-500/20';
    if (change < -2) return 'bg-rose-500/10';
    if (change < 0) return 'bg-rose-500/5';
    return 'bg-slate-500/10';
  };

  return (
    <div className="space-y-4 animate-in fade-in duration-500">
      {/* Header with Timeframe Selector */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-black text-white flex items-center gap-2">
            <span>📈</span> Market Intelligence
          </h2>
          <p className="text-sm text-slate-400">Real-time market data & analysis</p>
        </div>

        <div className="flex items-center gap-2 p-1 rounded-xl bg-slate-900/50 border border-white/5">
          {timeframes.map(tf => (
            <button
              key={tf.value}
              onClick={() => setSelectedTimeframe(tf.value)}
              className={`px-4 py-2 rounded-lg text-xs font-bold transition-all ${
                selectedTimeframe === tf.value
                  ? 'bg-blue-500 text-white'
                  : 'text-slate-400 hover:text-white hover:bg-white/5'
              }`}
            >
              {tf.label}
            </button>
          ))}
        </div>
      </div>

      {/* View Navigation */}
      <div className="grid grid-cols-3 md:grid-cols-6 gap-2">
        {views.map(view => (
          <button
            key={view.id}
            onClick={() => setActiveView(view.id)}
            className={`p-3 rounded-xl border text-left transition-all ${
              activeView === view.id
                ? 'bg-blue-500/20 border-blue-500/50'
                : 'bg-slate-900/50 border-white/5 hover:border-white/20'
            }`}
          >
            <span className="text-lg block mb-1">{view.label.split(' ')[0]}</span>
            <span className={`text-xs font-bold block ${activeView === view.id ? 'text-blue-400' : 'text-white'}`}>
              {view.label.split(' ')[1]}
            </span>
            <span className="text-[10px] text-slate-500">{view.desc}</span>
          </button>
        ))}
      </div>

      {/* OVERVIEW VIEW */}
      {activeView === 'overview' && (
        <div className="space-y-4">
          {/* Major Indices */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {marketData.indices.map(index => (
              <div 
                key={index.symbol}
                className={`p-4 rounded-xl border ${getPerformanceBg(index.change_percent)} ${getPerformanceColor(index.change_percent).replace('text-', 'border-')}/30`}
              >
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-bold text-slate-400 uppercase">{index.name}</span>
                  {index.change_percent > 0 ? (
                    <span className="text-emerald-400">▲</span>
                  ) : index.change_percent < 0 ? (
                    <span className="text-rose-400">▼</span>
                  ) : (
                    <span className="text-slate-400">—</span>
                  )}
                </div>
                <div className="text-2xl font-black text-white mb-1">
                  {index.price?.toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 0 })}
                </div>
                <div className={`text-sm font-bold ${getPerformanceColor(index.change_percent)}`}>
                  {index.change_percent > 0 ? '+' : ''}{index.change_percent?.toFixed(2)}%
                </div>
                <div className="text-xs text-slate-500 mt-1">
                  {index.change > 0 ? '+' : ''}{index.change?.toFixed(2)} pts
                </div>
              </div>
            ))}

            {/* Loading placeholders */}
            {marketData.indices.length === 0 && [1,2,3,4].map(i => (
              <div key={i} className="p-4 rounded-xl bg-slate-900/50 border border-white/10 animate-pulse">
                <div className="h-4 bg-slate-700 rounded w-20 mb-2"></div>
                <div className="h-8 bg-slate-700 rounded w-32 mb-1"></div>
                <div className="h-4 bg-slate-700 rounded w-16"></div>
              </div>
            ))}
          </div>

          {/* Country-Specific Market Health */}
          <div className="space-y-3">
            {/* US Market Health */}
            <div className="p-3 rounded-xl bg-slate-900/50 border border-white/[0.06]">
              <div className="flex items-center gap-2 mb-3">
                <span className="text-base">🇺🇸</span>
                <span className="text-xs font-bold text-white">US Market Health</span>
              </div>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                {/* Fear & Greed */}
                <div className="p-2 bg-slate-800/50 rounded-lg">
                  <div className="text-[9px] text-slate-500 uppercase mb-1">Fear & Greed</div>
                  <div className={`text-lg font-bold ${sentiment.fearGreed != null ? 'text-white' : 'text-slate-600'}`}>
                    {sentiment.fearGreed != null ? sentiment.fearGreed : '—'}
                  </div>
                  <div className={`text-[10px] ${sentiment.fearGreedLabel ? (sentiment.fearGreed >= 75 ? 'text-emerald-400' : sentiment.fearGreed >= 55 ? 'text-emerald-300' : sentiment.fearGreed >= 45 ? 'text-blue-400' : sentiment.fearGreed >= 25 ? 'text-rose-400' : 'text-rose-500') : 'text-slate-600'}`}>
                    {sentiment.fearGreedLabel || (sentiment.fearGreed != null ? (sentiment.fearGreed >= 75 ? 'Extreme Greed' : sentiment.fearGreed >= 55 ? 'Greed' : sentiment.fearGreed >= 45 ? 'Neutral' : sentiment.fearGreed >= 25 ? 'Fear' : 'Extreme Fear') : 'Loading…')}
                  </div>
                </div>
                {/* VIX */}
                <div className="p-2 bg-slate-800/50 rounded-lg">
                  <div className="text-[9px] text-slate-500 uppercase mb-1">VIX</div>
                  <div className={`text-lg font-bold ${sentiment.vix != null ? (sentiment.vix > 30 ? 'text-rose-400' : sentiment.vix > 20 ? 'text-amber-400' : 'text-emerald-400') : 'text-slate-600'}`}>
                    {sentiment.vix != null ? sentiment.vix.toFixed(2) : '—'}
                  </div>
                  <div className={`text-[10px] ${sentiment.vix != null ? 'text-slate-500' : 'text-slate-600'}`}>
                    {sentiment.vix != null ? (sentiment.vix > 30 ? 'High Fear' : sentiment.vix > 20 ? 'Elevated' : 'Low Vol') : 'Loading…'}
                  </div>
                </div>
                {/* 52W Highs/Lows */}
                <div className="p-2 bg-slate-800/50 rounded-lg">
                  <div className="text-[9px] text-slate-500 uppercase mb-1">52W Extremes</div>
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-bold text-emerald-400">
                      {marketBreadth.newHighs != null ? marketBreadth.newHighs : 'N/A'}
                    </span>
                    <span className="text-slate-500">/</span>
                    <span className="text-sm font-bold text-rose-400">
                      {marketBreadth.newLows != null ? marketBreadth.newLows : 'N/A'}
                    </span>
                  </div>
                  <div className="text-[10px] text-slate-500">Highs / Lows</div>
                </div>
                {/* MA % */}
                <div className="p-2 bg-slate-800/50 rounded-lg">
                  <div className="text-[9px] text-slate-500 uppercase mb-1">Above MA</div>
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-bold text-blue-400">
                      {marketBreadth.above50MA != null ? `${marketBreadth.above50MA}%` : 'N/A'}
                    </span>
                    <span className="text-slate-500">/</span>
                    <span className="text-sm font-bold text-indigo-400">
                      {marketBreadth.above200MA != null ? `${marketBreadth.above200MA}%` : 'N/A'}
                    </span>
                  </div>
                  <div className="text-[10px] text-slate-500">50d / 200d</div>
                </div>
              </div>
            </div>

            {/* HK & CN Row - Compact */}
            <div className="grid grid-cols-2 gap-2">
              {/* HK Market Health */}
              <div className="p-2.5 rounded-xl bg-slate-900/50 border border-white/[0.06]">
                <div className="flex items-center gap-2 mb-2">
                  <span className="text-base">🇭🇰</span>
                  <span className="text-xs font-bold text-white">HK</span>
                </div>
                <div className="space-y-1.5">
                  <div className="flex items-center justify-between">
                    <span className="text-[9px] text-slate-500">F&G Index</span>
                    <span className={`text-[11px] font-bold ${sentimentHK.fearGreed != null ? (sentimentHK.fearGreed >= 55 ? 'text-emerald-400' : sentimentHK.fearGreed >= 45 ? 'text-blue-400' : 'text-rose-400') : 'text-slate-600'}`}>
                      {sentimentHK.fearGreed != null ? sentimentHK.fearGreed : '—'}
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-[9px] text-slate-500">Adv/Dec</span>
                    <span className="text-[10px] text-emerald-400">
                      {marketBreadthHK.advancing}/{marketBreadthHK.declining}
                    </span>
                  </div>
                </div>
              </div>

              {/* CN Market Health */}
              <div className="p-2.5 rounded-xl bg-slate-900/50 border border-white/[0.06]">
                <div className="flex items-center gap-2 mb-2">
                  <span className="text-base">🇨🇳</span>
                  <span className="text-xs font-bold text-white">CN</span>
                </div>
                <div className="space-y-1.5">
                  <div className="flex items-center justify-between">
                    <span className="text-[9px] text-slate-500">F&G Index</span>
                    <span className={`text-[11px] font-bold ${sentimentCN.fearGreed != null ? (sentimentCN.fearGreed >= 55 ? 'text-emerald-400' : sentimentCN.fearGreed >= 45 ? 'text-blue-400' : 'text-rose-400') : 'text-slate-600'}`}>
                      {sentimentCN.fearGreed != null ? sentimentCN.fearGreed : '—'}
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-[9px] text-slate-500">Adv/Dec</span>
                    <span className="text-[10px] text-emerald-400">
                      {marketBreadthCN.advancing}/{marketBreadthCN.declining}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Country-Specific Market Sections */}
          <div className="space-y-2">
            {/* US Market */}
            <div className="p-2.5 rounded-xl bg-slate-900/50 border border-white/[0.06]">
              <div className="flex items-center gap-2 mb-2">
                <span className="text-base">🇺🇸</span>
                <span className="text-xs font-bold text-white">US Markets</span>
                <span className="text-[9px] text-slate-500 ml-auto">{(groupByMarket(marketData.gainers)['US'] || []).length} gainers • {(groupByMarket(marketData.losers)['US'] || []).length} losers</span>
              </div>
              <div className="grid grid-cols-2 gap-2">
                {/* US Gainers */}
                <div className="space-y-1">
                  <h4 className="text-[9px] font-bold text-emerald-400/70 uppercase">Gainers</h4>
                  {(groupByMarket(marketData.gainers)['US'] || []).slice(0, 3).map((stock) => (
                    <div key={stock.ticker} onClick={() => onTickerClick?.(stock.ticker)} className="flex items-center justify-between px-2 py-1 bg-emerald-500/5 rounded cursor-pointer hover:bg-emerald-500/10">
                      <div className="min-w-0">
                        <span className="text-[10px] font-bold text-white">{stock.ticker}</span>
                        <p className="text-[7px] text-slate-500 truncate">{stock.name}</p>
                      </div>
                      <span className="text-[9px] font-bold text-emerald-400">+{stock.change_percent?.toFixed(1)}%</span>
                    </div>
                  ))}
                  {(groupByMarket(marketData.gainers)['US'] || []).length === 0 && <p className="text-[8px] text-slate-500 py-1">No gainers</p>}
                </div>
                {/* US Losers */}
                <div className="space-y-1">
                  <h4 className="text-[9px] font-bold text-rose-400/70 uppercase">Losers</h4>
                  {(groupByMarket(marketData.losers)['US'] || []).slice(0, 3).map((stock) => (
                    <div key={stock.ticker} onClick={() => onTickerClick?.(stock.ticker)} className="flex items-center justify-between px-2 py-1 bg-rose-500/5 rounded cursor-pointer hover:bg-rose-500/10">
                      <div className="min-w-0">
                        <span className="text-[10px] font-bold text-white">{stock.ticker}</span>
                        <p className="text-[7px] text-slate-500 truncate">{stock.name}</p>
                      </div>
                      <span className="text-[9px] font-bold text-rose-400">{stock.change_percent?.toFixed(2)}%</span>
                    </div>
                  ))}
                  {(groupByMarket(marketData.losers)['US'] || []).length === 0 && <p className="text-[8px] text-slate-500 py-1">No losers</p>}
                </div>
              </div>
            </div>

            {/* HK & CN Row */}
            <div className="grid grid-cols-2 gap-2">
              {/* HK Market */}
              <div className="p-2.5 rounded-xl bg-slate-900/50 border border-white/[0.06]">
                <div className="flex items-center gap-2 mb-2">
                  <span className="text-base">🇭🇰</span>
                  <span className="text-xs font-bold text-white">HK</span>
                  <span className="text-[9px] text-slate-500 ml-auto">{(groupByMarket(marketData.gainers)['HK'] || []).length}/{(groupByMarket(marketData.losers)['HK'] || []).length}</span>
                </div>
                <div className="space-y-1">
                  {(groupByMarket(marketData.gainers)['HK'] || []).slice(0, 2).map((stock) => (
                    <div key={stock.ticker} onClick={() => onTickerClick?.(stock.ticker)} className="flex items-center justify-between px-2 py-1 bg-emerald-500/5 rounded cursor-pointer hover:bg-emerald-500/10">
                      <span className="text-[10px] font-bold text-white">{stock.ticker}</span>
                      <span className="text-[9px] font-bold text-emerald-400">+{stock.change_percent?.toFixed(2)}%</span>
                    </div>
                  ))}
                  {(groupByMarket(marketData.losers)['HK'] || []).slice(0, 2).map((stock) => (
                    <div key={stock.ticker} onClick={() => onTickerClick?.(stock.ticker)} className="flex items-center justify-between px-2 py-1 bg-rose-500/5 rounded cursor-pointer hover:bg-rose-500/10">
                      <span className="text-[10px] font-bold text-white">{stock.ticker}</span>
                      <span className="text-[9px] font-bold text-rose-400">{stock.change_percent?.toFixed(2)}%</span>
                    </div>
                  ))}
                  {(groupByMarket(marketData.gainers)['HK'] || []).length === 0 && (groupByMarket(marketData.losers)['HK'] || []).length === 0 && (
                    <p className="text-[8px] text-slate-500 py-2 text-center">No HK data</p>
                  )}
                </div>
              </div>

              {/* CN Market */}
              <div className="p-2.5 rounded-xl bg-slate-900/50 border border-white/[0.06]">
                <div className="flex items-center gap-2 mb-2">
                  <span className="text-base">🇨🇳</span>
                  <span className="text-xs font-bold text-white">CN</span>
                  <span className="text-[9px] text-slate-500 ml-auto">{(groupByMarket(marketData.gainers)['CN'] || []).length}/{(groupByMarket(marketData.losers)['CN'] || []).length}</span>
                </div>
                <div className="space-y-1">
                  {(groupByMarket(marketData.gainers)['CN'] || []).slice(0, 2).map((stock) => (
                    <div key={stock.ticker} onClick={() => onTickerClick?.(stock.ticker)} className="flex items-center justify-between px-2 py-1 bg-emerald-500/5 rounded cursor-pointer hover:bg-emerald-500/10">
                      <span className="text-[10px] font-bold text-white">{stock.ticker}</span>
                      <span className="text-[9px] font-bold text-emerald-400">+{stock.change_percent?.toFixed(2)}%</span>
                    </div>
                  ))}
                  {(groupByMarket(marketData.losers)['CN'] || []).slice(0, 2).map((stock) => (
                    <div key={stock.ticker} onClick={() => onTickerClick?.(stock.ticker)} className="flex items-center justify-between px-2 py-1 bg-rose-500/5 rounded cursor-pointer hover:bg-rose-500/10">
                      <span className="text-[10px] font-bold text-white">{stock.ticker}</span>
                      <span className="text-[9px] font-bold text-rose-400">{stock.change_percent?.toFixed(2)}%</span>
                    </div>
                  ))}
                  {(groupByMarket(marketData.gainers)['CN'] || []).length === 0 && (groupByMarket(marketData.losers)['CN'] || []).length === 0 && (
                    <p className="text-[8px] text-slate-500 py-2 text-center">No CN data</p>
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* MOVERS VIEW */}
      {activeView === 'movers' && (
        <div className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {/* All Gainers */}
            <div className="p-4 rounded-xl bg-slate-900/50 border border-white/10">
              <h3 className="text-sm font-black text-emerald-400 uppercase mb-4">Top Gainers</h3>
              <div className="space-y-2 max-h-[500px] overflow-y-auto">
                {marketData.gainers.map((stock, idx) => (
                  <div 
                    key={stock.ticker}
                    onClick={() => onTickerClick && onTickerClick(stock.ticker)}
                    className="flex items-center justify-between p-3 bg-emerald-500/5 rounded-lg cursor-pointer hover:bg-emerald-500/10 transition-colors"
                  >
                    <div className="flex items-center gap-3">
                      <span className="text-xs text-slate-500 w-6">{idx + 1}</span>
                      <div>
                        <span className="text-sm font-bold text-white">{stock.ticker}</span>
                        <p className="text-xs text-slate-500">{stock.name}</p>
                      </div>
                    </div>
                    <div className="text-right">
                      <span className="text-lg font-bold text-emerald-400">+{stock.change_percent?.toFixed(2)}%</span>
                      <div className="flex items-center gap-2 text-xs text-slate-500">
                        <span>${stock.price?.toFixed(2)}</span>
                        <span>•</span>
                        <span>Vol: {(stock.volume / 1e6).toFixed(1)}M</span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* All Losers */}
            <div className="p-4 rounded-xl bg-slate-900/50 border border-white/10">
              <h3 className="text-sm font-black text-rose-400 uppercase mb-4">Top Losers</h3>
              <div className="space-y-2 max-h-[500px] overflow-y-auto">
                {marketData.losers.map((stock, idx) => (
                  <div 
                    key={stock.ticker}
                    onClick={() => onTickerClick && onTickerClick(stock.ticker)}
                    className="flex items-center justify-between p-3 bg-rose-500/5 rounded-lg cursor-pointer hover:bg-rose-500/10 transition-colors"
                  >
                    <div className="flex items-center gap-3">
                      <span className="text-xs text-slate-500 w-6">{idx + 1}</span>
                      <div>
                        <span className="text-sm font-bold text-white">{stock.ticker}</span>
                        <p className="text-xs text-slate-500">{stock.name}</p>
                      </div>
                    </div>
                    <div className="text-right">
                      <span className="text-lg font-bold text-rose-400">{stock.change_percent?.toFixed(2)}%</span>
                      <div className="flex items-center gap-2 text-xs text-slate-500">
                        <span>${stock.price?.toFixed(2)}</span>
                        <span>•</span>
                        <span>Vol: {(stock.volume / 1e6).toFixed(1)}M</span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Volume Leaders */}
          <div className="p-4 rounded-xl bg-slate-900/50 border border-white/10">
            <h3 className="text-sm font-black text-blue-400 uppercase mb-4">Volume Leaders (Unusual Activity)</h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              {marketData.volumeLeaders.map(stock => (
                <div 
                  key={stock.ticker}
                  onClick={() => onTickerClick && onTickerClick(stock.ticker)}
                  className="p-3 bg-slate-800/50 rounded-lg cursor-pointer hover:bg-slate-700/50 transition-colors"
                >
                  <div className="flex items-center justify-between mb-1">
                    <span className="font-bold text-white">{stock.ticker}</span>
                    <span className={`text-xs font-bold ${getPerformanceColor(stock.change_percent)}`}>
                      {stock.change_percent > 0 ? '+' : ''}{stock.change_percent?.toFixed(2)}%
                    </span>
                  </div>
                  <p className="text-xs text-slate-500 mb-2">{stock.name}</p>
                  <div className="flex items-center gap-2">
                    <div className="flex-1 h-1.5 bg-slate-700 rounded-full overflow-hidden">
                      <div 
                        className="h-full bg-blue-500 rounded-full"
                        style={{ width: `${Math.min((stock.volume_ratio || 1) * 10, 100)}%` }}
                      />
                    </div>
                    <span className="text-xs text-blue-400">{stock.volume_ratio?.toFixed(1)}x avg</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* SECTORS VIEW */}
      {activeView === 'sectors' && (
        <div className="space-y-3">
          {/* Regional Markets - Compact 4 Box Layout */}
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-2">
            {/* US */}
            <div className="p-3 rounded-lg bg-slate-900/50 border border-white/5 hover:border-white/10 transition-colors">
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-1.5">
                  <span className="text-base">🇺🇸</span>
                  <span className="text-xs font-bold text-white">US</span>
                </div>
                <span className="text-[10px] text-emerald-400 font-bold">+0.85%</span>
              </div>
              <div className="space-y-1 text-[10px]">
                <div className="flex justify-between">
                  <span className="text-slate-500">S&P 500</span>
                  <span className="text-emerald-400">+0.72%</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500">Nasdaq</span>
                  <span className="text-emerald-400">+1.15%</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500">Russell</span>
                  <span className="text-rose-400">-0.23%</span>
                </div>
              </div>
            </div>

            {/* HK */}
            <div className="p-3 rounded-lg bg-slate-900/50 border border-white/5 hover:border-white/10 transition-colors">
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-1.5">
                  <span className="text-base">🇭🇰</span>
                  <span className="text-xs font-bold text-white">HK</span>
                </div>
                <span className="text-[10px] text-rose-400 font-bold">-0.45%</span>
              </div>
              <div className="space-y-1 text-[10px]">
                <div className="flex justify-between">
                  <span className="text-slate-500">HSI</span>
                  <span className="text-rose-400">-0.52%</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500">Tech Index</span>
                  <span className="text-rose-400">-0.89%</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500">HSCEI</span>
                  <span className="text-rose-400">-0.31%</span>
                </div>
              </div>
            </div>

            {/* CN */}
            <div className="p-3 rounded-lg bg-slate-900/50 border border-white/5 hover:border-white/10 transition-colors">
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-1.5">
                  <span className="text-base">🇨🇳</span>
                  <span className="text-xs font-bold text-white">CN</span>
                </div>
                <span className="text-[10px] text-emerald-400 font-bold">+0.32%</span>
              </div>
              <div className="space-y-1 text-[10px]">
                <div className="flex justify-between">
                  <span className="text-slate-500">Shanghai</span>
                  <span className="text-emerald-400">+0.45%</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500">Shenzhen</span>
                  <span className="text-emerald-400">+0.28%</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500">CSI 300</span>
                  <span className="text-emerald-400">+0.15%</span>
                </div>
              </div>
            </div>

            {/* SG */}
            <div className="p-3 rounded-lg bg-slate-900/50 border border-white/5 hover:border-white/10 transition-colors">
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-1.5">
                  <span className="text-base">🇸🇬</span>
                  <span className="text-xs font-bold text-white">SG</span>
                </div>
                <span className="text-[10px] text-emerald-400 font-bold">+0.18%</span>
              </div>
              <div className="space-y-1 text-[10px]">
                <div className="flex justify-between">
                  <span className="text-slate-500">STI</span>
                  <span className="text-emerald-400">+0.22%</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500">REITs</span>
                  <span className="text-emerald-400">+0.45%</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500">Banks</span>
                  <span className="text-rose-400">-0.12%</span>
                </div>
              </div>
            </div>
          </div>

          {/* FX, Commodities, Crypto - Compact Row */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-2">
            {/* FX */}
            <div className="p-3 rounded-lg bg-slate-900/50 border border-white/5">
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-bold text-white">💱 FX</span>
                <span className="text-[10px] text-slate-500">Live</span>
              </div>
              <div className="space-y-1 text-[10px]">
                <div className="flex justify-between">
                  <span className="text-slate-500">EUR/USD</span>
                  <span className="text-white font-mono">1.0852</span>
                  <span className="text-emerald-400">+0.12%</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500">USD/JPY</span>
                  <span className="text-white font-mono">149.82</span>
                  <span className="text-rose-400">-0.08%</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500">GBP/USD</span>
                  <span className="text-white font-mono">1.2734</span>
                  <span className="text-emerald-400">+0.23%</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500">USD/HKD</span>
                  <span className="text-white font-mono">7.8234</span>
                  <span className="text-slate-400">0.00%</span>
                </div>
              </div>
            </div>

            {/* Commodities */}
            <div className="p-3 rounded-lg bg-slate-900/50 border border-white/5">
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-bold text-white">⛽ Commodities</span>
                <span className="text-[10px] text-slate-500">Live</span>
              </div>
              <div className="space-y-1 text-[10px]">
                <div className="flex justify-between">
                  <span className="text-slate-500">Gold</span>
                  <span className="text-white font-mono">$2,845</span>
                  <span className="text-emerald-400">+0.45%</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500">Crude Oil</span>
                  <span className="text-white font-mono">$73.42</span>
                  <span className="text-rose-400">-1.23%</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500">Silver</span>
                  <span className="text-white font-mono">$31.85</span>
                  <span className="text-emerald-400">+0.78%</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500">Copper</span>
                  <span className="text-white font-mono">$4.12</span>
                  <span className="text-rose-400">-0.34%</span>
                </div>
              </div>
            </div>

            {/* Crypto */}
            <div className="p-3 rounded-lg bg-slate-900/50 border border-white/5">
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-bold text-white">₿ Crypto</span>
                <span className="text-[10px] text-slate-500">24h</span>
              </div>
              <div className="space-y-1 text-[10px]">
                <div className="flex justify-between">
                  <span className="text-slate-500">BTC</span>
                  <span className="text-white font-mono">$62,340</span>
                  <span className="text-emerald-400">+2.15%</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500">ETH</span>
                  <span className="text-white font-mono">$3,425</span>
                  <span className="text-emerald-400">+1.89%</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500">SOL</span>
                  <span className="text-white font-mono">$142.50</span>
                  <span className="text-rose-400">-0.45%</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500">XRP</span>
                  <span className="text-white font-mono">$0.62</span>
                  <span className="text-emerald-400">+0.32%</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* GLOBAL VIEW */}
      {activeView === 'global' && (
        <div className="space-y-3">
          {/* HKT Time Header with Bull/Bear Indicator */}
          <div className="flex items-center justify-between p-3 rounded-lg bg-slate-900/50 border border-white/5">
            <div className="flex items-center gap-3">
              <span className="text-xs text-slate-400">HKT</span>
              <span className="text-lg font-bold text-white font-mono">
                {new Date().toLocaleTimeString('en-US', { 
                  timeZone: 'Asia/Hong_Kong', 
                  hour: '2-digit', 
                  minute: '2-digit',
                  hour12: false 
                })}
              </span>
              <span className="text-xs text-slate-500">
                {new Date().toLocaleDateString('en-US', { 
                  timeZone: 'Asia/Hong_Kong',
                  month: 'short', 
                  day: 'numeric' 
                })}
              </span>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-xs text-slate-400">Global Sentiment</span>
              <div className="flex items-center gap-1 px-2 py-1 rounded bg-emerald-500/20 border border-emerald-500/30">
                <span className="text-sm">🐂</span>
                <span className="text-xs font-bold text-emerald-400">Bull</span>
              </div>
            </div>
          </div>

          {/* US Markets */}
          <div className="p-3 rounded-lg bg-slate-900/50 border border-white/5">
            <div className="flex items-center gap-2 mb-2">
              <span className="text-base">🇺🇸</span>
              <span className="text-xs font-bold text-white">US Markets</span>
              <span className="ml-auto text-[10px] px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-400">Open</span>
            </div>
            <div className="space-y-1">
              {[
                { name: 'S&P 500', price: '4,500', change1d: '+0.50', change1w: '+1.20', change1m: '+3.45' },
                { name: 'Nasdaq', price: '14,000', change1d: '+0.80', change1w: '+1.85', change1m: '+4.20' },
                { name: 'Dow Jones', price: '35,000', change1d: '+0.25', change1w: '+0.95', change1m: '+2.80' },
                { name: 'Russell 2000', price: '2,100', change1d: '-0.15', change1w: '+0.45', change1m: '+1.90' },
              ].map(m => (
                <div key={m.name} className="grid grid-cols-5 gap-2 text-[10px] items-center py-1 border-b border-white/5 last:border-0">
                  <span className="text-slate-300 font-medium">{m.name}</span>
                  <span className="text-white font-mono text-right">{m.price}</span>
                  <span className={`text-right font-mono ${parseFloat(m.change1d) >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                    1D {parseFloat(m.change1d) >= 0 ? '+' : ''}{m.change1d}%
                  </span>
                  <span className={`text-right font-mono ${parseFloat(m.change1w) >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                    1W {parseFloat(m.change1w) >= 0 ? '+' : ''}{m.change1w}%
                  </span>
                  <span className={`text-right font-mono ${parseFloat(m.change1m) >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                    1M {parseFloat(m.change1m) >= 0 ? '+' : ''}{m.change1m}%
                  </span>
                </div>
              ))}
            </div>
          </div>

          {/* Europe Markets */}
          <div className="p-3 rounded-lg bg-slate-900/50 border border-white/5">
            <div className="flex items-center gap-2 mb-2">
              <span className="text-base">🇪🇺</span>
              <span className="text-xs font-bold text-white">Europe</span>
              <span className="ml-auto text-[10px] px-2 py-0.5 rounded bg-slate-700 text-slate-400">Closed</span>
            </div>
            <div className="space-y-1">
              {[
                { name: 'FTSE 100', price: '7,500', change1d: '-0.20', change1w: '+0.85', change1m: '+1.50' },
                { name: 'DAX', price: '16,000', change1d: '+0.30', change1w: '+1.10', change1m: '+2.30' },
                { name: 'CAC 40', price: '7,200', change1d: '+0.15', change1w: '+0.95', change1m: '+1.80' },
                { name: 'STOXX 600', price: '460', change1d: '+0.10', change1w: '+0.75', change1m: '+1.60' },
              ].map(m => (
                <div key={m.name} className="grid grid-cols-5 gap-2 text-[10px] items-center py-1 border-b border-white/5 last:border-0">
                  <span className="text-slate-300 font-medium">{m.name}</span>
                  <span className="text-white font-mono text-right">{m.price}</span>
                  <span className={`text-right font-mono ${parseFloat(m.change1d) >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                    1D {parseFloat(m.change1d) >= 0 ? '+' : ''}{m.change1d}%
                  </span>
                  <span className={`text-right font-mono ${parseFloat(m.change1w) >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                    1W {parseFloat(m.change1w) >= 0 ? '+' : ''}{m.change1w}%
                  </span>
                  <span className={`text-right font-mono ${parseFloat(m.change1m) >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                    1M {parseFloat(m.change1m) >= 0 ? '+' : ''}{m.change1m}%
                  </span>
                </div>
              ))}
            </div>
          </div>

          {/* Asia Markets */}
          <div className="p-3 rounded-lg bg-slate-900/50 border border-white/5">
            <div className="flex items-center gap-2 mb-2">
              <span className="text-base">🌏</span>
              <span className="text-xs font-bold text-white">Asia Pacific</span>
              <span className="ml-auto text-[10px] px-2 py-0.5 rounded bg-slate-700 text-slate-400">Closed</span>
            </div>
            <div className="space-y-1">
              {[
                { name: 'Nikkei 225', price: '29,000', change1d: '+1.20', change1w: '+2.50', change1m: '+5.30' },
                { name: 'Hang Seng', price: '17,000', change1d: '-0.50', change1w: '-1.20', change1m: '+0.80' },
                { name: 'Shanghai', price: '3,200', change1d: '+0.10', change1w: '-0.30', change1m: '+1.10' },
                { name: 'ASX 200', price: '7,200', change1d: '+0.40', change1w: '+0.85', change1m: '+2.10' },
                { name: 'Kospi', price: '2,550', change1d: '+0.65', change1w: '+1.40', change1m: '+2.80' },
              ].map(m => (
                <div key={m.name} className="grid grid-cols-5 gap-2 text-[10px] items-center py-1 border-b border-white/5 last:border-0">
                  <span className="text-slate-300 font-medium">{m.name}</span>
                  <span className="text-white font-mono text-right">{m.price}</span>
                  <span className={`text-right font-mono ${parseFloat(m.change1d) >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                    1D {parseFloat(m.change1d) >= 0 ? '+' : ''}{m.change1d}%
                  </span>
                  <span className={`text-right font-mono ${parseFloat(m.change1w) >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                    1W {parseFloat(m.change1w) >= 0 ? '+' : ''}{m.change1w}%
                  </span>
                  <span className={`text-right font-mono ${parseFloat(m.change1m) >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                    1M {parseFloat(m.change1m) >= 0 ? '+' : ''}{m.change1m}%
                  </span>
                </div>
              ))}
            </div>
          </div>

          {/* Market Hours */}
          <div className="p-4 rounded-xl bg-slate-900/50 border border-white/10">
            <h3 className="text-sm font-black text-white uppercase mb-4">Global Market Hours (HKT)</h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {(() => {
                // Get current time in HKT (UTC+8)
                const now = new Date();
                const hktOffset = 8 * 60; // HKT is UTC+8 in minutes
                const utcOffset = now.getTimezoneOffset(); // Local offset from UTC in minutes
                const hktTime = new Date(now.getTime() + (utcOffset + hktOffset) * 60000);
                const hktHour = hktTime.getHours();
                const hktMinute = hktTime.getMinutes();
                const hktDecimal = hktHour + hktMinute / 60;
                
                // Market hours in HKT
                const markets = [
                  { 
                    name: 'Tokyo (TSE)', 
                    flag: '🇯🇵', 
                    localHours: '09:00-15:00 JST',
                    hktOpen: 8.0,    // 08:00 HKT
                    hktClose: 14.0,  // 14:00 HKT
                  },
                  { 
                    name: 'Hong Kong (HKEX)', 
                    flag: '🇭🇰', 
                    localHours: '09:30-16:00 HKT',
                    hktOpen: 9.5,    // 09:30 HKT
                    hktClose: 16.0,  // 16:00 HKT
                  },
                  { 
                    name: 'London (LSE)', 
                    flag: '🇬🇧', 
                    localHours: '08:00-16:30 GMT',
                    hktOpen: 16.0,   // 16:00 HKT
                    hktClose: 24.5,  // 00:30 HKT (next day)
                  },
                  { 
                    name: 'New York (NYSE)', 
                    flag: '🇺🇸', 
                    localHours: '09:30-16:00 EST',
                    hktOpen: 22.5,   // 22:30 HKT
                    hktClose: 29.0,  // 05:00 HKT (next day, represented as 29 for calculation)
                  },
                ];
                
                return markets.map(market => {
                  let isOpen = false;
                  if (market.hktClose > 24) {
                    // Market spans midnight (NY)
                    isOpen = hktDecimal >= market.hktOpen || hktDecimal < (market.hktClose - 24);
                  } else {
                    isOpen = hktDecimal >= market.hktOpen && hktDecimal < market.hktClose;
                  }
                  
                  return (
                    <div key={market.name} className="p-3 bg-slate-800/50 rounded-lg">
                      <div className="flex items-center gap-2 mb-1">
                        <span>{market.flag}</span>
                        <span className="text-xs font-bold text-white">{market.name}</span>
                      </div>
                      <p className="text-xs text-slate-500">{market.localHours}</p>
                      <span className={`text-xs font-bold ${isOpen ? 'text-emerald-400' : 'text-slate-500'}`}>
                        {isOpen ? 'Open' : 'Closed'}
                      </span>
                    </div>
                  );
                });
              })()}
            </div>
          </div>
        </div>
      )}

      {/* BREADTH VIEW */}
      {activeView === 'breadth' && (
        <div className="space-y-4">
          {/* Advance/Decline */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="p-6 rounded-xl bg-slate-900/50 border border-white/10">
              <h3 className="text-xs font-bold text-slate-400 uppercase mb-4">Advance/Decline</h3>
              <div className="relative h-40">
                <svg className="w-full h-full" viewBox="0 0 200 100">
                  {/* Advancing */}
                  <rect x="10" y="10" width="80" height="80" fill="rgba(16, 185, 129, 0.2)" rx="8" />
                  <text x="50" y="50" textAnchor="middle" fill="#10b981" fontSize="24" fontWeight="bold">
                    {marketBreadth.advancing}
                  </text>
                  <text x="50" y="70" textAnchor="middle" fill="#10b981" fontSize="12">
                    Advancing
                  </text>
                  
                  {/* Declining */}
                  <rect x="110" y="10" width="80" height="80" fill="rgba(244, 63, 94, 0.2)" rx="8" />
                  <text x="150" y="50" textAnchor="middle" fill="#f43f5e" fontSize="24" fontWeight="bold">
                    {marketBreadth.declining}
                  </text>
                  <text x="150" y="70" textAnchor="middle" fill="#f43f5e" fontSize="12">
                    Declining
                  </text>
                </svg>
              </div>
              <div className="text-center mt-2">
                <span className="text-lg font-bold text-white">
                  A/D Ratio: {marketBreadth.declining > 0 
                    ? (marketBreadth.advancing / marketBreadth.declining).toFixed(2) 
                    : '∞'}
                </span>
              </div>
            </div>

            <div className="p-6 rounded-xl bg-slate-900/50 border border-white/10">
              <h3 className="text-xs font-bold text-slate-400 uppercase mb-4">New Highs/Lows</h3>
              <div className="space-y-4">
                <div>
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-sm text-slate-400">52-Week Highs</span>
                    <span className="text-lg font-bold text-emerald-400">{marketBreadth.newHighs}</span>
                  </div>
                  <div className="h-2 bg-slate-700 rounded-full overflow-hidden">
                    <div 
                      className="h-full bg-emerald-500 rounded-full"
                      style={{ width: `${Math.min((marketBreadth.newHighs / 100) * 100, 100)}%` }}
                    />
                  </div>
                </div>
                <div>
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-sm text-slate-400">52-Week Lows</span>
                    <span className="text-lg font-bold text-rose-400">{marketBreadth.newLows}</span>
                  </div>
                  <div className="h-2 bg-slate-700 rounded-full overflow-hidden">
                    <div 
                      className="h-full bg-rose-500 rounded-full"
                      style={{ width: `${Math.min((marketBreadth.newLows / 100) * 100, 100)}%` }}
                    />
                  </div>
                </div>
              </div>
            </div>

            <div className="p-6 rounded-xl bg-slate-900/50 border border-white/10">
              <h3 className="text-xs font-bold text-slate-400 uppercase mb-4">Moving Averages</h3>
              <div className="space-y-3">
                <div className="flex items-center justify-between p-3 bg-slate-800/50 rounded-lg">
                  <span className="text-sm text-slate-400">Above 50-day MA</span>
                  <span className="text-lg font-bold text-blue-400">{marketBreadth.above50MA || '---'}%</span>
                </div>
                <div className="flex items-center justify-between p-3 bg-slate-800/50 rounded-lg">
                  <span className="text-sm text-slate-400">Above 200-day MA</span>
                  <span className="text-lg font-bold text-blue-400">{marketBreadth.above200MA || '---'}%</span>
                </div>
                <div className="flex items-center justify-between p-3 bg-slate-800/50 rounded-lg">
                  <span className="text-sm text-slate-400">RSI {'>'} 70 (Overbought)</span>
                  <span className="text-lg font-bold text-amber-400">{marketBreadth.overbought || '---'}</span>
                </div>
                <div className="flex items-center justify-between p-3 bg-slate-800/50 rounded-lg">
                  <span className="text-sm text-slate-400">RSI {'<'} 30 (Oversold)</span>
                  <span className="text-lg font-bold text-emerald-400">{marketBreadth.oversold || '---'}</span>
                </div>
              </div>
            </div>
          </div>

          {/* McClellan Oscillator Placeholder */}
          <div className="p-4 rounded-xl bg-slate-900/50 border border-white/10">
            <h3 className="text-sm font-black text-white uppercase mb-4">McClellan Oscillator (Breadth Momentum)</h3>
            <div className="h-40 bg-slate-800/50 rounded-lg flex items-center justify-center">
              <p className="text-slate-500">Historical breadth momentum chart coming soon...</p>
            </div>
          </div>
        </div>
      )}

      {/* CALENDAR VIEW */}
      {activeView === 'calendar' && (
        <div className="space-y-4">
          <div className="p-4 rounded-xl bg-slate-900/50 border border-white/10">
            <h3 className="text-sm font-black text-white uppercase mb-4">Economic Calendar</h3>
            <div className="space-y-3">
              {[
                { time: '08:30', event: 'US Initial Jobless Claims', impact: 'high', forecast: '215K', previous: '218K' },
                { time: '10:00', event: 'US Existing Home Sales', impact: 'medium', forecast: '3.95M', previous: '3.82M' },
                { time: '14:00', event: 'Fed Chair Powell Speech', impact: 'high', forecast: '---', previous: '---' },
              ].map((item, idx) => (
                <div key={idx} className="flex items-center gap-4 p-3 bg-slate-800/50 rounded-lg">
                  <div className="w-16 text-center">
                    <span className="text-sm font-bold text-white">{item.time}</span>
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-bold text-white">{item.event}</span>
                      <span className={`text-[10px] px-2 py-0.5 rounded ${
                        item.impact === 'high' ? 'bg-rose-500/20 text-rose-400' :
                        item.impact === 'medium' ? 'bg-amber-500/20 text-amber-400' :
                        'bg-blue-500/20 text-blue-400'
                      }`}>
                        {item.impact.toUpperCase()}
                      </span>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="text-xs text-slate-500">Forecast: {item.forecast}</p>
                    <p className="text-xs text-slate-500">Previous: {item.previous}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="p-4 rounded-xl bg-slate-900/50 border border-white/10">
              <h3 className="text-sm font-black text-white uppercase mb-4">Earnings Today</h3>
              <div className="space-y-2">
                {[
                  { ticker: 'AAPL', time: 'AMC', eps: '$2.18', surprise: '+5.2%' },
                  { ticker: 'TSLA', time: 'AMC', eps: '$0.73', surprise: '-2.1%' },
                ].map((earnings, idx) => (
                  <div key={idx} className="flex items-center justify-between p-3 bg-slate-800/50 rounded-lg">
                    <div className="flex items-center gap-3">
                      <span className="font-bold text-white">{earnings.ticker}</span>
                      <span className="text-xs text-slate-500">{earnings.time}</span>
                    </div>
                    <div className="text-right">
                      <span className="text-sm font-bold text-white">{earnings.eps}</span>
                      <span className={`text-xs ml-2 ${earnings.surprise.startsWith('+') ? 'text-emerald-400' : 'text-rose-400'}`}>
                        {earnings.surprise}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div className="p-4 rounded-xl bg-slate-900/50 border border-white/10">
              <h3 className="text-sm font-black text-white uppercase mb-4">IPO Calendar</h3>
              <div className="space-y-2">
                <p className="text-xs text-slate-500 italic">No major IPOs scheduled this week</p>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default MarketsTab;
