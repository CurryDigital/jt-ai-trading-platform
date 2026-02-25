import React, { useState, useEffect } from 'react';

// Enhanced Research Tab with Stock Screener & Analyst Data
export const ResearchTab = ({ onTickerClick }) => {
  const [activeSection, setActiveSection] = useState('signals'); // signals, screener, earnings
  const [signals, setSignals] = useState([]);
  const [analystData, setAnalystData] = useState([]);
  const [earnings, setEarnings] = useState([]);
  const [loading, setLoading] = useState(true);
  const [signalFilters, setSignalFilters] = useState({
    market: 'ALL',
    action: 'ALL',
    minConfidence: 0
  });
  const [filters, setFilters] = useState({
    market: 'ALL',
    minUpside: 0,
    minAnalysts: 5,
    maxPE: 50,
    sortBy: 'upside',
    searchQuery: '',
    assetClass: 'ALL'
  });

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    setLoading(true);
    try {
      // Fetch trading signals (all markets)
      const signalsRes = await fetch('/api/signals/1');
      if (signalsRes.ok) {
        const data = await signalsRes.json();
        setSignals(data || []);
      }

      // Fetch stocks with consensus data
      const stocksRes = await fetch('/api/stocks/consensus/top-upside?limit=50');
      if (stocksRes.ok) {
        const data = await stocksRes.json();
        setAnalystData(data);
      }

      // Fetch upcoming earnings
      const earningsRes = await fetch('/api/earnings/upcoming');
      if (earningsRes.ok) {
        const data = await earningsRes.json();
        setEarnings(data.earnings || []);
      }
    } catch (e) {
      console.error('Failed to fetch research data:', e);
    }
    setLoading(false);
  };

  // Filter and sort stocks
  const filteredStocks = analystData.filter(stock => {
    // Search by ticker
    if (filters.searchQuery && !stock.ticker.toLowerCase().includes(filters.searchQuery.toLowerCase())) return false;
    // Market filter
    if (filters.market !== 'ALL' && !stock.ticker.endsWith(filters.market)) return false;
    // Asset class filter (basic detection from ticker suffix)
    if (filters.assetClass !== 'ALL') {
      const isCrypto = stock.ticker.match(/^(BTC|ETH|SOL|COIN)/);
      const isFX = stock.ticker.includes('=') || stock.ticker.includes('/');
      const isStock = !isCrypto && !isFX;
      if (filters.assetClass === 'CRYPTO' && !isCrypto) return false;
      if (filters.assetClass === 'FX' && !isFX) return false;
      if (filters.assetClass === 'STOCK' && !isStock) return false;
    }
    if (stock.upside_pct < filters.minUpside) return false;
    if (stock.analysts < filters.minAnalysts) return false;
    return true;
  }).sort((a, b) => {
    if (filters.sortBy === 'upside') return b.upside_pct - a.upside_pct;
    if (filters.sortBy === 'analysts') return b.analysts - a.analysts;
    return 0;
  });

  // Filter signals
  const filteredSignals = signals.filter(sig => {
    if (signalFilters.market !== 'ALL' && sig.market !== signalFilters.market) return false;
    if (signalFilters.action !== 'ALL' && sig.action !== signalFilters.action) return false;
    if (sig.total_conf < signalFilters.minConfidence) return false;
    return true;
  });

  const sections = [
    { id: 'signals', label: '⚡ Trading Signals', icon: '⚡' },
    { id: 'screener', label: '🔍 Analyst Ratings', icon: '🔍' },
    { id: 'earnings', label: '📅 Earnings Calendar', icon: '📅' },
  ];

  return (
    <div className="space-y-6 animate-in fade-in duration-500">
      {/* Section Tabs */}
      <div className="flex items-center gap-2 p-1 rounded-xl bg-slate-900/50 border border-white/5">
        {sections.map(section => (
          <button
            key={section.id}
            onClick={() => setActiveSection(section.id)}
            className={`flex-1 px-4 py-2.5 rounded-lg text-xs font-bold transition-all ${
              activeSection === section.id
                ? 'bg-blue-500 text-white shadow-lg'
                : 'text-slate-400 hover:text-white hover:bg-white/5'
            }`}
          >
            {section.label}
          </button>
        ))}
      </div>

      {/* TRADING SIGNALS - All Markets */}
      {activeSection === 'signals' && (
        <div className="space-y-4">
          {/* Signal Filters */}
          <div className="p-4 rounded-xl bg-slate-900/50 border border-white/10">
            <div className="flex flex-wrap items-center gap-4">
              <div className="flex items-center gap-2">
                <label className="text-xs text-slate-400">Market:</label>
                <select 
                  value={signalFilters.market}
                  onChange={(e) => setSignalFilters({...signalFilters, market: e.target.value})}
                  className="bg-slate-800 border border-white/10 rounded px-3 py-1.5 text-sm text-white"
                >
                  <option value="ALL">All Markets</option>
                  <option value="US">US</option>
                  <option value="HK">Hong Kong</option>
                  <option value="CN">China</option>
                </select>
              </div>
              
              <div className="flex items-center gap-2">
                <label className="text-xs text-slate-400">Action:</label>
                <select
                  value={signalFilters.action}
                  onChange={(e) => setSignalFilters({...signalFilters, action: e.target.value})}
                  className="bg-slate-800 border border-white/10 rounded px-3 py-1.5 text-sm text-white"
                >
                  <option value="ALL">All</option>
                  <option value="BUY">Buy</option>
                  <option value="SELL">Sell</option>
                </select>
              </div>
              
              <div className="flex items-center gap-2">
                <label className="text-xs text-slate-400">Min Confidence:</label>
                <select
                  value={signalFilters.minConfidence}
                  onChange={(e) => setSignalFilters({...signalFilters, minConfidence: Number(e.target.value)})}
                  className="bg-slate-800 border border-white/10 rounded px-3 py-1.5 text-sm text-white"
                >
                  <option value={0}>Any</option>
                  <option value={60}>60%+</option>
                  <option value={70}>70%+</option>
                  <option value={80}>80%+</option>
                </select>
              </div>

              <button
                onClick={fetchData}
                className="ml-auto px-4 py-1.5 bg-blue-500 hover:bg-blue-400 text-white text-xs font-bold rounded-lg"
              >
                🔄 Refresh
              </button>
            </div>          
          </div>

          {/* Results Count */}
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-black text-white">
              {filteredSignals.length} Active Signals
            </h3>            
            <div className="flex items-center gap-4 text-xs text-slate-500">
              <span>US: {signals.filter(s => s.market === 'US').length}</span>
              <span>HK: {signals.filter(s => s.market === 'HK').length}</span>
              <span>CN: {signals.filter(s => s.market === 'CN').length}</span>
            </div>
          </div>

          {/* Signals Grid */}
          {loading ? (
            <div className="text-center py-12">
              <div className="w-8 h-8 border-2 border-slate-600 border-t-blue-500 rounded-full animate-spin mx-auto mb-4" />
              <p className="text-sm text-slate-500">Loading signals...</p>
            </div>
          ) : filteredSignals.length === 0 ? (
            <div className="text-center py-12 text-slate-500">
              <div className="text-4xl mb-4">⚡</div>
              <p>No signals match your filters</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {filteredSignals.map((sig, idx) => (
                <div 
                  key={`${sig.ticker}-${idx}`}
                  onClick={() => onTickerClick && onTickerClick(sig.ticker)}
                  className="p-4 rounded-xl bg-slate-900/50 border border-white/10 hover:border-blue-500/50 cursor-pointer transition-all hover:scale-[1.02]"
                >
                  <div className="flex items-start justify-between mb-3">
                    <div>
                      <h4 className="text-lg font-bold text-white">{sig.ticker}</h4>
                      <p className="text-xs text-slate-500">{sig.market} · {sig.horizon}</p>
                    </div>
                    <div className={`px-2 py-1 rounded text-xs font-bold ${
                      sig.action === 'BUY' ? 'bg-emerald-500/20 text-emerald-400' :
                      sig.action === 'SELL' ? 'bg-rose-500/20 text-rose-400' :
                      'bg-amber-500/20 text-amber-400'
                    }`}>
                      {sig.action}
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-3 mb-3">
                    <div className="bg-slate-800/50 rounded p-2">
                      <span className="text-[10px] text-slate-500 block">Price</span>
                      <span className="text-sm font-bold text-white">${sig.price?.toFixed(2) || '---'}</span>
                    </div>
                    <div className="bg-slate-800/50 rounded p-2">
                      <span className="text-[10px] text-slate-500 block">Confidence</span>
                      <span className={`text-sm font-bold ${
                        sig.total_conf >= 70 ? 'text-emerald-400' : 
                        sig.total_conf >= 60 ? 'text-blue-400' : 'text-amber-400'
                      }`}>
                        {sig.total_conf?.toFixed(1)}%
                      </span>
                    </div>
                  </div>

                  <div className="flex items-center justify-between">
                    <div>
                      <span className="text-[10px] text-slate-500 block">Win Rate</span>
                      <span className="text-sm font-mono text-white">{sig.win_rate?.toFixed(1)}%</span>
                    </div>                    
                    <div className="text-right">
                      <span className="text-[10px] text-slate-500 block">Change</span>
                      <span className={`text-sm font-bold ${
                        (sig.change || 0) >= 0 ? 'text-emerald-400' : 'text-rose-400'
                      }`}>
                        {(sig.change || 0) >= 0 ? '+' : ''}{sig.change?.toFixed(2)}%
                      </span>
                    </div>
                  </div>
                  
                  {sig.tags && sig.tags.length > 0 && (
                    <div className="mt-3 flex flex-wrap gap-1">
                      {sig.tags.slice(0, 2).map((tag, i) => (
                        <span key={i} className="text-[10px] px-1.5 py-0.5 bg-slate-800 rounded text-slate-400">
                          {tag.replace(/_/g, ' ')}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* STOCK SCREENER */}
      {activeSection === 'screener' && (
        <div className="space-y-4">
          {/* Filters */}
          <div className="p-4 rounded-xl bg-slate-900/50 border border-white/10">
            {/* Search Bar */}
            <div className="relative mb-4">
              <span className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500">🔍</span>
              <input
                type="text"
                placeholder="Search ticker symbol..."
                value={filters.searchQuery}
                onChange={(e) => setFilters({...filters, searchQuery: e.target.value})}
                className="w-full pl-10 pr-4 py-2 bg-slate-800 border border-white/10 rounded-lg text-white text-sm placeholder-slate-500 focus:border-blue-500/50 focus:outline-none"
              />
            </div>
            
            <div className="flex flex-wrap items-center gap-4">
              <div className="flex items-center gap-2">
                <label className="text-xs text-slate-400">Market:</label>
                <select 
                  value={filters.market}
                  onChange={(e) => setFilters({...filters, market: e.target.value})}
                  className="bg-slate-800 border border-white/10 rounded px-3 py-1.5 text-sm text-white"
                >
                  <option value="ALL">All Markets</option>
                  <option value=".HK">Hong Kong</option>
                  <option value=".SI">Singapore</option>
                  <option value=".T">Japan</option>
                </select>
              </div>
              
              <div className="flex items-center gap-2">
                <label className="text-xs text-slate-400">Asset Class:</label>
                <select
                  value={filters.assetClass}
                  onChange={(e) => setFilters({...filters, assetClass: e.target.value})}
                  className="bg-slate-800 border border-white/10 rounded px-3 py-1.5 text-sm text-white"
                >
                  <option value="ALL">All</option>
                  <option value="STOCK">Stocks</option>
                  <option value="CRYPTO">Crypto</option>
                  <option value="FX">FX</option>
                </select>
              </div>

              <div className="flex items-center gap-2">
                <label className="text-xs text-slate-400">Min Upside:</label>
                <input
                  type="range"
                  min="0"
                  max="50"
                  value={filters.minUpside}
                  onChange={(e) => setFilters({...filters, minUpside: Number(e.target.value)})}
                  className="w-24"
                />
                <span className="text-xs text-white w-10">{filters.minUpside}%</span>
              </div>

              <div className="flex items-center gap-2">
                <label className="text-xs text-slate-400">Min Analysts:</label>
                <select
                  value={filters.minAnalysts}
                  onChange={(e) => setFilters({...filters, minAnalysts: Number(e.target.value)})}
                  className="bg-slate-800 border border-white/10 rounded px-3 py-1.5 text-sm text-white"
                >
                  <option value={3}>3+</option>
                  <option value={5}>5+</option>
                  <option value={10}>10+</option>
                  <option value={20}>20+</option>
                </select>
              </div>

              <div className="flex items-center gap-2">
                <label className="text-xs text-slate-400">Sort By:</label>
                <select
                  value={filters.sortBy}
                  onChange={(e) => setFilters({...filters, sortBy: e.target.value})}
                  className="bg-slate-800 border border-white/10 rounded px-3 py-1.5 text-sm text-white"
                >
                  <option value="upside">Upside Potential</option>
                  <option value="analysts">Analyst Coverage</option>
                </select>
              </div>

              <button
                onClick={fetchData}
                className="ml-auto px-4 py-1.5 bg-blue-500 hover:bg-blue-400 text-white text-xs font-bold rounded-lg"
              >
                🔄 Refresh
              </button>
            </div>
          </div>

          {/* Results Count */}
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-black text-white">
              {filteredStocks.length} Stocks Match Filters
            </h3>
            <span className="text-xs text-slate-500">
              Showing top analyst picks with consensus data
            </span>
          </div>

          {/* Stock Grid */}
          {loading ? (
            <div className="text-center py-12">
              <div className="w-8 h-8 border-2 border-slate-600 border-t-blue-500 rounded-full animate-spin mx-auto mb-4" />
              <p className="text-sm text-slate-500">Loading stock data...</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {filteredStocks.map((stock, idx) => (
                <div 
                  key={stock.ticker}
                  onClick={() => onTickerClick && onTickerClick(stock.ticker)}
                  className="p-4 rounded-xl bg-slate-900/50 border border-white/10 hover:border-blue-500/50 cursor-pointer transition-all hover:scale-[1.02]"
                >
                  <div className="flex items-start justify-between mb-3">
                    <div>
                      <h4 className="text-lg font-bold text-white">{stock.ticker}</h4>
                      <p className="text-xs text-slate-500">{stock.analysts} analysts covering</p>
                    </div>
                    <div className={`px-2 py-1 rounded text-xs font-bold ${
                      stock.rating === 'STRONG_BUY' ? 'bg-emerald-500/20 text-emerald-400' :
                      stock.rating === 'BUY' ? 'bg-blue-500/20 text-blue-400' :
                      'bg-amber-500/20 text-amber-400'
                    }`}>
                      {stock.rating}
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-3 mb-3">
                    <div className="bg-slate-800/50 rounded p-2">
                      <span className="text-[10px] text-slate-500 block">Current</span>
                      <span className="text-sm font-bold text-white">${stock.current?.toFixed(2) || '---'}</span>
                    </div>
                    <div className="bg-slate-800/50 rounded p-2">
                      <span className="text-[10px] text-slate-500 block">Target</span>
                      <span className="text-sm font-bold text-emerald-400">${stock.target?.toFixed(2) || '---'}</span>
                    </div>
                  </div>

                  <div className="flex items-center justify-between">
                    <div>
                      <span className="text-[10px] text-slate-500 block">Upside Potential</span>
                      <span className={`text-lg font-bold ${stock.upside_pct > 20 ? 'text-emerald-400' : stock.upside_pct > 10 ? 'text-blue-400' : 'text-amber-400'}`}>
                        +{stock.upside_pct?.toFixed(1)}%
                      </span>
                    </div>
                    
                    {/* Analyst Breakdown */}
                    <div className="flex items-center gap-1">
                      <div className="flex flex-col items-center">
                        <span className="text-[10px] text-emerald-400 font-bold">{stock.buy}</span>
                        <span className="w-4 h-1 bg-emerald-500 rounded-full" />
                      </div>
                      <div className="flex flex-col items-center">
                        <span className="text-[10px] text-amber-400 font-bold">{stock.hold}</span>
                        <span className="w-4 h-1 bg-amber-500 rounded-full" />
                      </div>
                      <div className="flex flex-col items-center">
                        <span className="text-[10px] text-rose-400 font-bold">{stock.sell}</span>
                        <span className="w-4 h-1 bg-rose-500 rounded-full" />
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* ANALYST RATINGS */}
      {activeSection === 'analyst' && (
        <div className="space-y-4">
          <div className="p-4 rounded-xl bg-slate-900/50 border border-white/10">
            <h3 className="text-sm font-black text-white mb-2">Top Analyst Recommendations</h3>
            <p className="text-xs text-slate-500">
              Stocks with highest consensus ratings and strong upside potential
            </p>
          </div>

          <div className="rounded-xl border border-white/10 overflow-hidden">
            <table className="w-full">
              <thead className="bg-slate-900/50">
                <tr className="text-[10px] font-black text-slate-500 uppercase tracking-wider">
                  <th className="text-left p-3">Rank</th>
                  <th className="text-left p-3">Ticker</th>
                  <th className="text-right p-3">Current</th>
                  <th className="text-right p-3">Target</th>
                  <th className="text-right p-3">Upside</th>
                  <th className="text-center p-3">Rating</th>
                  <th className="text-center p-3">Analysts</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5">
                {filteredStocks.slice(0, 20).map((stock, idx) => (
                  <tr 
                    key={stock.ticker}
                    onClick={() => onTickerClick && onTickerClick(stock.ticker)}
                    className="hover:bg-white/5 transition-colors cursor-pointer"
                  >
                    <td className="p-3">
                      <span className="text-xs font-mono text-slate-500">#{idx + 1}</span>
                    </td>
                    <td className="p-3">
                      <span className="text-sm font-bold text-white">{stock.ticker}</span>
                    </td>
                    <td className="p-3 text-right">
                      <span className="text-sm font-mono text-white">${stock.current?.toFixed(2)}</span>
                    </td>
                    <td className="p-3 text-right">
                      <span className="text-sm font-mono text-emerald-400">${stock.target?.toFixed(2)}</span>
                    </td>
                    <td className="p-3 text-right">
                      <span className={`text-sm font-bold ${stock.upside_pct > 20 ? 'text-emerald-400' : 'text-blue-400'}`}>
                        +{stock.upside_pct?.toFixed(1)}%
                      </span>
                    </td>
                    <td className="p-3 text-center">
                      <span className={`px-2 py-1 rounded text-[10px] font-bold ${
                        stock.rating === 'STRONG_BUY' ? 'bg-emerald-500/20 text-emerald-400' :
                        stock.rating === 'BUY' ? 'bg-blue-500/20 text-blue-400' :
                        'bg-amber-500/20 text-amber-400'
                      }`}>
                        {stock.rating}
                      </span>
                    </td>
                    <td className="p-3 text-center">
                      <span className="text-sm font-mono text-white">{stock.analysts}</span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* EARNINGS CALENDAR */}
      {activeSection === 'earnings' && (
        <div className="space-y-4">
          <div className="p-4 rounded-xl bg-slate-900/50 border border-white/10">
            <h3 className="text-sm font-black text-white mb-2">Upcoming Earnings</h3>
            <p className="text-xs text-slate-500">
              Earnings announcements for the next 7 days
            </p>
          </div>

          {earnings.length === 0 ? (
            <div className="text-center py-12 text-slate-500">
              <div className="text-4xl mb-4">📅</div>
              <p>No upcoming earnings data available</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {earnings.map((item, idx) => (
                <div key={idx} className="p-4 rounded-xl bg-slate-900/50 border border-white/10">
                  <div className="flex items-center justify-between mb-3">
                    <h4 className="text-lg font-bold text-white">{item.ticker}</h4>
                    <span className="text-xs text-slate-500">{item.date}</span>
                  </div>
                  
                  <div className="grid grid-cols-2 gap-3">
                    <div className="bg-slate-800/50 rounded p-2">
                      <span className="text-[10px] text-slate-500 block">EPS Estimate</span>
                      <span className="text-sm font-bold text-white">${item.eps_estimate || '---'}</span>
                    </div>
                    <div className="bg-slate-800/50 rounded p-2">
                      <span className="text-[10px] text-slate-500 block">Revenue Est</span>
                      <span className="text-sm font-bold text-white">${item.revenue_estimate ? (item.revenue_estimate / 1e9).toFixed(2) + 'B' : '---'}</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default ResearchTab;
