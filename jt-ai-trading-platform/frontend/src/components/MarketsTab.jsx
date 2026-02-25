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
  const [activeView, setActiveView] = useState('overview'); // overview, movers, sectors, global
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
  const [sentiment, setSentiment] = useState({
    fearGreed: 50,
    vix: 20,
    putCall: 1.0
  });
  const [loading, setLoading] = useState(true);
  const [selectedTimeframe, setSelectedTimeframe] = useState('1D'); // 1D, 1W, 1M, YTD

  useEffect(() => {
    fetchMarketData(true); // Initial load with spinner
    const interval = setInterval(() => fetchMarketData(false), 120000); // 2 minutes, silent refresh
    return () => clearInterval(interval);
  }, [selectedTimeframe]);

  const fetchMarketData = async (showLoading = false) => {
    try {
      if (showLoading) setLoading(true);
      // Fetch indices
      const indicesRes = await fetch(`/api/market/indices?timeframe=${selectedTimeframe}`);
      const indices = indicesRes.ok ? await indicesRes.json() : [];

      // Fetch movers
      const moversRes = await fetch(`/api/market/movers?timeframe=${selectedTimeframe}`);
      const movers = moversRes.ok ? await moversRes.json() : { gainers: [], losers: [] };

      // Fetch sectors
      const sectorsRes = await fetch('/api/market/sectors');
      const sectors = sectorsRes.ok ? await sectorsRes.json() : [];

      // Fetch volume leaders
      const volumeRes = await fetch('/api/market/volume-leaders');
      const volumeLeaders = volumeRes.ok ? await volumeRes.json() : [];

      // Fetch global markets
      const globalRes = await fetch('/api/market/global');
      const global = globalRes.ok ? await globalRes.json() : [];

      setMarketData({
        indices: indices.data || [],
        gainers: movers.gainers || [],
        losers: movers.losers || [],
        volumeLeaders: volumeLeaders.data || [],
        sectors: sectors.data || [],
        global: global.data || []
      });

      // Fetch market breadth
      const breadthRes = await fetch('/api/market/breadth');
      if (breadthRes.ok) {
        setMarketBreadth(await breadthRes.json());
      }

      // Fetch sentiment
      const sentimentRes = await fetch('/api/market/sentiment');
      if (sentimentRes.ok) {
        setSentiment(await sentimentRes.json());
      }

      if (showLoading) setLoading(false);
    } catch (e) {
      console.error('Failed to fetch market data:', e);
      if (showLoading) setLoading(false);
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

          {/* Fear & Greed + Market Stats */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* Fear & Greed Index */}
            <div className="p-4 rounded-xl bg-slate-900/50 border border-white/10">
              <h3 className="text-xs font-bold text-slate-400 uppercase mb-3">Fear & Greed Index</h3>
              <div className="flex items-center gap-4">
                <div className="relative w-24 h-24">
                  <svg className="w-full h-full transform -rotate-90">
                    <circle cx="48" cy="48" r="40" stroke="#334155" strokeWidth="8" fill="none" />
                    <circle 
                      cx="48" cy="48" r="40" 
                      stroke={sentiment.fearGreed > 75 ? '#10b981' : sentiment.fearGreed > 50 ? '#3b82f6' : sentiment.fearGreed > 25 ? '#f59e0b' : '#f43f5e'}
                      strokeWidth="8" 
                      fill="none"
                      strokeDasharray={`${sentiment.fearGreed * 2.51} 251`}
                      strokeLinecap="round"
                    />
                  </svg>
                  <div className="absolute inset-0 flex items-center justify-center">
                    <span className="text-xl font-black text-white">{sentiment.fearGreed}</span>
                  </div>
                </div>
                <div>
                  <div className={`text-sm font-bold ${
                    sentiment.fearGreed > 75 ? 'text-emerald-400' : 
                    sentiment.fearGreed > 50 ? 'text-blue-400' : 
                    sentiment.fearGreed > 25 ? 'text-amber-400' : 'text-rose-400'
                  }`}>
                    {sentiment.fearGreed > 75 ? 'Extreme Greed' : 
                     sentiment.fearGreed > 55 ? 'Greed' : 
                     sentiment.fearGreed > 45 ? 'Neutral' : 
                     sentiment.fearGreed > 25 ? 'Fear' : 'Extreme Fear'}
                  </div>
                  <p className="text-xs text-slate-500 mt-1">Market sentiment indicator</p>
                </div>
              </div>
            </div>

            {/* VIX & Put/Call */}
            <div className="p-4 rounded-xl bg-slate-900/50 border border-white/10">
              <h3 className="text-xs font-bold text-slate-400 uppercase mb-3">Volatility</h3>
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-slate-400">VIX</span>
                  <div className="text-right">
                    <span className={`text-lg font-bold ${sentiment.vix > 30 ? 'text-rose-400' : sentiment.vix > 20 ? 'text-amber-400' : 'text-emerald-400'}`}>
                      {sentiment.vix?.toFixed(2)}
                    </span>
                    <p className="text-xs text-slate-500">
                      {sentiment.vix > 30 ? 'High Fear' : sentiment.vix > 20 ? 'Elevated' : 'Low Volatility'}
                    </p>
                  </div>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-slate-400">Put/Call Ratio</span>
                  <div className="text-right">
                    <span className={`text-lg font-bold ${sentiment.putCall > 1.2 ? 'text-rose-400' : sentiment.putCall < 0.8 ? 'text-emerald-400' : 'text-blue-400'}`}>
                      {sentiment.putCall?.toFixed(2)}
                    </span>
                    <p className="text-xs text-slate-500">
                      {sentiment.putCall > 1.2 ? 'Bearish' : sentiment.putCall < 0.8 ? 'Bullish' : 'Neutral'}
                    </p>
                  </div>
                </div>
              </div>
            </div>

            {/* Market Summary */}
            <div className="p-4 rounded-xl bg-slate-900/50 border border-white/10">
              <h3 className="text-xs font-bold text-slate-400 uppercase mb-3">Market Summary</h3>
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-slate-400">52W Highs</span>
                  <span className="text-sm font-bold text-emerald-400">{marketBreadth.newHighs}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-slate-400">52W Lows</span>
                  <span className="text-sm font-bold text-rose-400">{marketBreadth.newLows}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-slate-400">Above 200 MA</span>
                  <span className="text-sm font-bold text-blue-400">{marketBreadth.above200MA || '---'}%</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-slate-400">Above 50 MA</span>
                  <span className="text-sm font-bold text-blue-400">{marketBreadth.above50MA || '---'}%</span>
                </div>
              </div>
            </div>
          </div>

          {/* Top Movers Preview */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Top Gainers */}
            <div className="p-4 rounded-xl bg-slate-900/50 border border-white/10">
              <h3 className="text-xs font-bold text-emerald-400 uppercase mb-3 flex items-center gap-2">
                🚀 Top Gainers
                <span className="text-slate-500 font-normal">{selectedTimeframe}</span>
              </h3>
              <div className="space-y-2">
                {marketData.gainers.slice(0, 5).map((stock, idx) => (
                  <div 
                    key={stock.ticker}
                    onClick={() => onTickerClick && onTickerClick(stock.ticker)}
                    className="flex items-center justify-between p-2 bg-emerald-500/5 rounded-lg cursor-pointer hover:bg-emerald-500/10 transition-colors"
                  >
                    <div className="flex items-center gap-3">
                      <span className="text-xs text-slate-500 w-4">{idx + 1}</span>
                      <div>
                        <span className="text-sm font-bold text-white">{stock.ticker}</span>
                        <p className="text-[10px] text-slate-500">{stock.name}</p>
                      </div>
                    </div>
                    <div className="text-right">
                      <span className="text-sm font-bold text-emerald-400">+{stock.change_percent?.toFixed(2)}%</span>
                      <p className="text-[10px] text-slate-500">${stock.price?.toFixed(2)}</p>
                    </div>
                  </div>
                ))}
                {marketData.gainers.length === 0 && (
                  <p className="text-xs text-slate-500 text-center py-4">No gainers data</p>
                )}
              </div>
            </div>

            {/* Top Losers */}
            <div className="p-4 rounded-xl bg-slate-900/50 border border-white/10">
              <h3 className="text-xs font-bold text-rose-400 uppercase mb-3 flex items-center gap-2">
                📉 Top Losers
                <span className="text-slate-500 font-normal">{selectedTimeframe}</span>
              </h3>
              <div className="space-y-2">
                {marketData.losers.slice(0, 5).map((stock, idx) => (
                  <div 
                    key={stock.ticker}
                    onClick={() => onTickerClick && onTickerClick(stock.ticker)}
                    className="flex items-center justify-between p-2 bg-rose-500/5 rounded-lg cursor-pointer hover:bg-rose-500/10 transition-colors"
                  >
                    <div className="flex items-center gap-3">
                      <span className="text-xs text-slate-500 w-4">{idx + 1}</span>
                      <div>
                        <span className="text-sm font-bold text-white">{stock.ticker}</span>
                        <p className="text-[10px] text-slate-500">{stock.name}</p>
                      </div>
                    </div>
                    <div className="text-right">
                      <span className="text-sm font-bold text-rose-400">{stock.change_percent?.toFixed(2)}%</span>
                      <p className="text-[10px] text-slate-500">${stock.price?.toFixed(2)}</p>
                    </div>
                  </div>
                ))}
                {marketData.losers.length === 0 && (
                  <p className="text-xs text-slate-500 text-center py-4">No losers data</p>
                )}
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
        <div className="space-y-4">
          {/* Sector Heat Map */}
          <div className="p-4 rounded-xl bg-slate-900/50 border border-white/10">
            <h3 className="text-sm font-black text-white uppercase mb-4">Sector Performance Heat Map</h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              {marketData.sectors.map(sector => (
                <div 
                  key={sector.name}
                  className={`p-4 rounded-lg cursor-pointer transition-all hover:scale-105 ${getPerformanceBg(sector.change_percent)}`}
                >
                  <div className="flex items-center gap-2 mb-2">
                    <span className="text-lg">{sector.icon}</span>
                    <span className="text-xs font-bold text-white">{sector.name}</span>
                  </div>
                  <div className={`text-2xl font-black ${getPerformanceColor(sector.change_percent)}`}>
                    {sector.change_percent > 0 ? '+' : ''}{sector.change_percent?.toFixed(2)}%
                  </div>
                  <p className="text-xs text-slate-500 mt-1">{sector.top_mover}</p>
                </div>
              ))}
            </div>
          </div>

          {/* Sector Details */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {marketData.sectors.slice(0, 4).map(sector => (
              <div key={sector.name} className="p-4 rounded-xl bg-slate-900/50 border border-white/10">
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-2">
                    <span className="text-xl">{sector.icon}</span>
                    <h4 className="text-sm font-bold text-white">{sector.name}</h4>
                  </div>
                  <span className={`text-lg font-bold ${getPerformanceColor(sector.change_percent)}`}>
                    {sector.change_percent > 0 ? '+' : ''}{sector.change_percent?.toFixed(2)}%
                  </span>
                </div>
                
                <div className="space-y-2">
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-slate-500">Top Gainer</span>
                    <span className="text-emerald-400 font-bold">{sector.top_gainer} +{sector.top_gainer_change?.toFixed(2)}%</span>
                  </div>
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-slate-500">Biggest Loser</span>
                    <span className="text-rose-400 font-bold">{sector.top_loser} {sector.top_loser_change?.toFixed(2)}%</span>
                  </div>
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-slate-500">Market Cap</span>
                    <span className="text-white">${(sector.market_cap / 1e12).toFixed(2)}T</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* GLOBAL VIEW */}
      {activeView === 'global' && (
        <div className="space-y-4">
          {/* World Markets Overview */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {marketData.global.map(market => (
              <div 
                key={market.name}
                className="p-4 rounded-xl bg-slate-900/50 border border-white/10"
              >
                <div className="flex items-center gap-2 mb-2">
                  <span className="text-lg">{market.flag}</span>
                  <span className="text-xs font-bold text-slate-400">{market.region}</span>
                </div>
                <h4 className="text-sm font-bold text-white mb-1">{market.name}</h4>
                <div className="text-xl font-black text-white mb-1">
                  {market.price?.toLocaleString()}
                </div>
                <div className={`text-sm font-bold ${getPerformanceColor(market.change_percent)}`}>
                  {market.change_percent > 0 ? '+' : ''}{market.change_percent?.toFixed(2)}%
                </div>
                <div className="text-xs text-slate-500 mt-1">
                  Status: {market.status}
                </div>
              </div>
            ))}
          </div>

          {/* Market Hours */}
          <div className="p-4 rounded-xl bg-slate-900/50 border border-white/10">
            <h3 className="text-sm font-black text-white uppercase mb-4">Global Market Hours</h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {[
                { name: 'Tokyo (TSE)', open: '09:00', close: '15:00', status: 'Closed', flag: '🇯🇵' },
                { name: 'Hong Kong (HKEX)', open: '09:30', close: '16:00', status: 'Closed', flag: '🇭🇰' },
                { name: 'London (LSE)', open: '08:00', close: '16:30', status: 'Closed', flag: '🇬🇧' },
                { name: 'New York (NYSE)', open: '09:30', close: '16:00', status: 'Open', flag: '🇺🇸' },
              ].map(exchange => (
                <div key={exchange.name} className="p-3 bg-slate-800/50 rounded-lg">
                  <div className="flex items-center gap-2 mb-1">
                    <span>{exchange.flag}</span>
                    <span className="text-xs font-bold text-white">{exchange.name}</span>
                  </div>
                  <p className="text-xs text-slate-500">{exchange.open} - {exchange.close} Local</p>
                  <span className={`text-xs font-bold ${exchange.status === 'Open' ? 'text-emerald-400' : 'text-slate-500'}`}>
                    {exchange.status}
                  </span>
                </div>
              ))}
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
