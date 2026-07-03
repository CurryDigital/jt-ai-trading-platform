import React, { useState, useEffect, useMemo } from 'react';

/**
 * Strategy Lab - Advanced Strategy Screener with Backtest vs Live Comparison
 * Uses REAL data only - no placeholders
 */

const StrategyLab = () => {
  const [strategies, setStrategies] = useState([]);
  const [liveStats, setLiveStats] = useState({});
  const [loading, setLoading] = useState(true);
  
  // Filter states
  const [activeAssetClass, setActiveAssetClass] = useState('ALL');
  const [sortBy, setSortBy] = useState('win_rate');
  const [sortDirection, setSortDirection] = useState('desc');
  const [minWinRate, setMinWinRate] = useState(0);
  const [searchQuery, setSearchQuery] = useState('');
  
  // Expanded strategy for detailed view
  const [expandedStrategy, setExpandedStrategy] = useState(null);
  
  // Deploy state
  const [deployingId, setDeployingId] = useState(null);
  const [deployResult, setDeployResult] = useState(null);

  const assetClasses = [
    { id: 'ALL', label: 'All Strategies', icon: '📊' },
    { id: 'STOCK', label: 'Equity', icon: '📈' },
    { id: 'FX', label: 'FX', icon: '💱' },
    { id: 'CRYPTO', label: 'Crypto', icon: '₿' },
    { id: 'COMMODITY', label: 'Commodity', icon: '🛢️' },
  ];

  useEffect(() => {
    fetchStrategies(true);
    fetchLiveStats();
    
    // Refresh every 60 seconds
    const interval = setInterval(() => {
      fetchLiveStats();
    }, 60000);
    
    return () => clearInterval(interval);
  }, []);

  const fetchStrategies = async (isInitial = false) => {
    if (isInitial) setLoading(true);
    try {
      const res = await fetch('/api/strategies/researcher');
      if (res.ok) {
        const data = await res.json();
        setStrategies(data.strategies || []);
      }
    } catch (e) {
      console.error('Failed to fetch strategies:', e);
    }
    if (isInitial) setLoading(false);
  };

  const fetchLiveStats = async () => {
    try {
      const res = await fetch('/api/strategies/stats');
      if (res.ok) {
        const data = await res.json();
        setLiveStats(data.stats || {});
      }
    } catch (e) {
      console.error('Failed to fetch live stats:', e);
    }
  };

  // One-click deploy using strategy's universe tickers
  const handleDeploy = async (strategy) => {
    if (deployingId) return; // Prevent double clicks
    
    setDeployingId(strategy.id);
    setDeployResult(null);
    
    try {
      // Use strategy's universe tickers, fallback to empty array
      const tickers = strategy.universe || [];
      
      if (tickers.length === 0) {
        setDeployResult({ success: false, error: 'No tickers configured for this strategy' });
        return;
      }
      
      const res = await fetch('/api/strategies/deploy-with-pool', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          strategy_id: strategy.id, 
          tickers: tickers, 
          total_pool: 100000 // Default $100k pool
        })
      });
      
      const data = await res.json();
      setDeployResult({ ...data, strategyId: strategy.id });
      
      // Clear result after 3 seconds
      setTimeout(() => {
        setDeployResult(null);
      }, 3000);
      
      // Refresh if successful
      if (data.success) {
        fetchStrategies(false);
        fetchLiveStats();
      }
    } catch (e) {
      setDeployResult({ success: false, error: e.message, strategyId: strategy.id });
    } finally {
      setDeployingId(null);
    }
  };

  // Merge backtest and live data
  const mergedStrategies = useMemo(() => {
    return strategies.map(s => {
      const live = liveStats[s.id] || {};
      return {
        ...s,
        // Live/current year metrics (from actual trades)
        live_wr: live.actualWinRate,
        live_trades: live.totalTrades,
        live_pnl: live.totalPnL,
        live_positions: live.activePositions,
        live_invested: live.totalInvested,
      };
    });
  }, [strategies, liveStats]);

  // Filter and sort
  const filteredStrategies = useMemo(() => {
    let filtered = mergedStrategies;
    
    // Asset class filter
    if (activeAssetClass !== 'ALL') {
      filtered = filtered.filter(s => s.asset_class === activeAssetClass);
    }
    
    // Min win rate filter (backtest)
    if (minWinRate > 0) {
      filtered = filtered.filter(s => (s.win_rate || 0) * 100 >= minWinRate);
    }
    
    // Search filter
    if (searchQuery) {
      const q = searchQuery.toLowerCase();
      filtered = filtered.filter(s => 
        s.name?.toLowerCase().includes(q) ||
        s.id?.toLowerCase().includes(q) ||
        s.description?.toLowerCase().includes(q)
      );
    }
    
    // Sort
    filtered = [...filtered].sort((a, b) => {
      let valA, valB;
      
      switch (sortBy) {
        case 'win_rate':
          valA = a.win_rate || 0;
          valB = b.win_rate || 0;
          break;
        case 'profit_factor':
          valA = a.profit_factor || 0;
          valB = b.profit_factor || 0;
          break;
        case 'max_drawdown':
          valA = a.max_drawdown || 0;
          valB = b.max_drawdown || 0;
          break;
        case 'sharpe':
          valA = a.sharpe_ratio || 0;
          valB = b.sharpe_ratio || 0;
          break;
        case 'backtest_trades':
          valA = a.backtest_trades || 0;
          valB = b.backtest_trades || 0;
          break;
        case 'live_wr':
          valA = a.live_wr || 0;
          valB = b.live_wr || 0;
          break;
        case 'live_pnl':
          valA = a.live_pnl || 0;
          valB = b.live_pnl || 0;
          break;
        default:
          valA = a.win_rate || 0;
          valB = b.win_rate || 0;
      }
      
      return sortDirection === 'desc' ? valB - valA : valA - valB;
    });
    
    return filtered;
  }, [mergedStrategies, activeAssetClass, minWinRate, searchQuery, sortBy, sortDirection]);

  // Format helpers - return null if no data
  const formatNumber = (num, decimals = 1) => {
    if (num === null || num === undefined || isNaN(num)) return null;
    return num.toFixed(decimals);
  };

  const formatPercent = (num) => {
    if (num === null || num === undefined || isNaN(num)) return null;
    return (num * 100).toFixed(1);
  };

  const formatCurrency = (num) => {
    if (num === null || num === undefined || isNaN(num)) return null;
    if (Math.abs(num) >= 1000000) return `$${(num / 1000000).toFixed(2)}M`;
    if (Math.abs(num) >= 1000) return `$${(num / 1000).toFixed(1)}k`;
    return `$${num.toFixed(0)}`;
  };

  return (
    <div className="strategy-lab space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-sm font-bold text-white">Strategy Lab</h2>
          <p className="text-[10px] text-slate-500 mt-0.5">
            {filteredStrategies.length} strategies · real backtest data only
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => { fetchStrategies(true); fetchLiveStats(); }}
            className="qr-btn-ghost"
          >
            Refresh
          </button>
        </div>
      </div>

      {/* Asset Class Filter Tabs */}
      <div className="flex items-center gap-0.5 p-0.5 rounded-md bg-slate-900/50 border border-white/[0.05] overflow-x-auto w-fit">
        {assetClasses.map(ac => (
          <button
            key={ac.id}
            onClick={() => setActiveAssetClass(ac.id)}
            className={`flex items-center gap-1.5 px-2.5 py-1.5 rounded text-[10px] font-bold whitespace-nowrap transition-colors ${
              activeAssetClass === ac.id
                ? 'bg-white/[0.08] text-white'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <span>{ac.icon}</span>
            {ac.label}
            <span className={`ml-1 px-1.5 py-0.5 rounded text-[10px] ${
              activeAssetClass === ac.id ? 'bg-white/20' : 'bg-slate-800'
            }`}>
              {ac.id === 'ALL' 
                ? strategies.length 
                : strategies.filter(s => s.asset_class === ac.id).length}
            </span>
          </button>
        ))}
      </div>

      {/* Search and Sort Controls */}
      <div className="p-4 rounded-xl bg-slate-900/50 border border-white/10 space-y-4">
        <div className="flex flex-wrap items-center gap-4">
          {/* Search */}
          <div className="relative flex-1 min-w-[200px]">
            <span className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500">🔍</span>
            <input
              type="text"
              placeholder="Search strategies..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-4 py-2 bg-slate-800 border border-white/10 rounded-lg text-white text-sm placeholder-slate-500 focus:border-blue-500/50 focus:outline-none"
            />
          </div>
          
          {/* Sort Dropdown */}
          <div className="flex items-center gap-2">
            <label className="text-xs text-slate-400">Sort By:</label>
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value)}
              className="bg-slate-800 border border-white/10 rounded-lg px-3 py-2 text-sm text-white focus:border-blue-500/50 focus:outline-none"
            >
              <option value="win_rate">Win Rate</option>
              <option value="profit_factor">Profit Factor</option>
              <option value="max_drawdown">Max Drawdown</option>
              <option value="sharpe">Sharpe Ratio</option>
              <option value="backtest_trades">Backtest Trades</option>
              <option value="live_wr">Live Win Rate</option>
              <option value="live_pnl">Live P&L</option>
            </select>
            <button
              onClick={() => setSortDirection(d => d === 'desc' ? 'asc' : 'desc')}
              className="px-3 py-2 bg-slate-800 border border-white/10 rounded-lg text-slate-400 hover:text-white"
            >
              {sortDirection === 'desc' ? '↓' : '↑'}
            </button>
          </div>
          
          {/* Min Win Rate */}
          <div className="flex items-center gap-2">
            <label className="text-xs text-slate-400">Min WR:</label>
            <select
              value={minWinRate}
              onChange={(e) => setMinWinRate(Number(e.target.value))}
              className="bg-slate-800 border border-white/10 rounded-lg px-3 py-2 text-sm text-white"
            >
              <option value={0}>Any</option>
              <option value={50}>50%+</option>
              <option value={55}>55%+</option>
              <option value={60}>60%+</option>
              <option value={65}>65%+</option>
            </select>
          </div>
        </div>
      </div>

      {/* Strategy Table - Compact View */}
      {loading ? (
        <div className="text-center py-12">
          <div className="w-8 h-8 border-2 border-slate-600 border-t-blue-500 rounded-full animate-spin mx-auto mb-4" />
          <p className="text-sm text-slate-500">Loading strategies...</p>
        </div>
      ) : filteredStrategies.length === 0 ? (
        <div className="text-center py-12 text-slate-500">
          <div className="text-4xl mb-4">🧪</div>
          <p>No strategies match your filters</p>
        </div>
      ) : (
        <div className="rounded-xl border border-white/10 overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-slate-900/80 text-[10px] font-black text-slate-400 uppercase tracking-wider">
              <tr>
                <th className="text-left p-3">Strategy</th>
                <th className="text-center p-3">Class</th>
                <th className="text-center p-3 cursor-pointer hover:text-white" onClick={() => { setSortBy('win_rate'); setSortDirection('desc'); }}>
                  WR ↕
                </th>
                <th className="text-center p-3">PF</th>
                <th className="text-center p-3">MDD</th>
                <th className="text-center p-3">Sharpe</th>
                <th className="text-center p-3">Trades</th>
                <th className="text-center p-3 bg-emerald-900/20">Live WR</th>
                <th className="text-center p-3 bg-emerald-900/20">Live P&L</th>
                <th className="text-right p-3">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5">
              {filteredStrategies.map((s, idx) => {
                const isExpanded = expandedStrategy === s.id;
                
                return (
                  <React.Fragment key={s.id}>
                    <tr 
                      className="hover:bg-white/5 transition-colors cursor-pointer"
                      onClick={() => setExpandedStrategy(isExpanded ? null : s.id)}
                    >
                      <td className="p-3">
                        <div className="flex items-center gap-3">
                          <span className="text-xs text-slate-500 font-mono">#{idx + 1}</span>
                          <div>
                            <div className="font-bold text-white">{s.name}</div>
                            <div className="text-[10px] text-slate-500">{s.id}</div>
                          </div>
                        </div>
                      </td>
                      <td className="p-3 text-center">
                        <span className={`text-[10px] px-2 py-1 rounded ${
                          s.asset_class === 'STOCK' ? 'bg-blue-500/20 text-blue-400' :
                          s.asset_class === 'FX' ? 'bg-purple-500/20 text-purple-400' :
                          s.asset_class === 'CRYPTO' ? 'bg-amber-500/20 text-amber-400' :
                          'bg-rose-500/20 text-rose-400'
                        }`}>
                          {s.asset_class}
                        </span>
                      </td>
                      
                      {/* Backtest Metrics - Real data only */}
                      <td className="p-3 text-center">
                        {s.win_rate !== null && s.win_rate !== undefined ? (
                          <span className="font-mono text-slate-300">{formatPercent(s.win_rate)}%</span>
                        ) : (
                          <span className="text-slate-600">—</span>
                        )}
                      </td>
                      
                      <td className="p-3 text-center">
                        {s.profit_factor !== null && s.profit_factor !== undefined ? (
                          <span className="font-mono text-slate-300">{formatNumber(s.profit_factor, 2)}</span>
                        ) : (
                          <span className="text-slate-600">—</span>
                        )}
                      </td>
                      
                      <td className="p-3 text-center">
                        {s.max_drawdown !== null && s.max_drawdown !== undefined ? (
                          <span className="font-mono text-rose-400">{formatNumber(s.max_drawdown, 1)}%</span>
                        ) : (
                          <span className="text-slate-600">—</span>
                        )}
                      </td>
                      
                      <td className="p-3 text-center">
                        {s.sharpe_ratio !== null && s.sharpe_ratio !== undefined ? (
                          <span className="font-mono text-slate-300">{formatNumber(s.sharpe_ratio, 2)}</span>
                        ) : (
                          <span className="text-slate-600">—</span>
                        )}
                      </td>
                      
                      <td className="p-3 text-center">
                        {s.backtest_trades !== null && s.backtest_trades !== undefined ? (
                          <span className="font-mono text-slate-300">{s.backtest_trades}</span>
                        ) : (
                          <span className="text-slate-600">—</span>
                        )}
                      </td>
                      
                      {/* Live Metrics */}
                      <td className="p-3 text-center bg-emerald-900/10">
                        {s.live_wr !== null && s.live_wr !== undefined ? (
                          <span className="font-mono font-bold text-emerald-400">
                            {formatNumber(s.live_wr, 1)}%
                          </span>
                        ) : (
                          <span className="text-slate-600">—</span>
                        )}
                      </td>
                      
                      <td className="p-3 text-center bg-emerald-900/10">
                        {s.live_pnl !== null && s.live_pnl !== undefined ? (
                          <span className={`font-mono font-bold ${
                            s.live_pnl >= 0 ? 'text-emerald-400' : 'text-rose-400'
                          }`}>
                            {s.live_pnl >= 0 ? '+' : ''}{formatCurrency(s.live_pnl)}
                          </span>
                        ) : (
                          <span className="text-slate-600">—</span>
                        )}
                      </td>
                      
                      <td className="p-3 text-right">
                        <span className="text-xs text-slate-400">
                          {isExpanded ? '▼' : '▶'}
                        </span>
                      </td>
                    </tr>
                    
                    {/* Expanded Detail Row */}
                    {isExpanded && (
                      <tr className="bg-slate-900/30">
                        <td colSpan={11} className="p-4">
                          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            {/* Strategy Details */}
                            <div className="space-y-3">
                              <h4 className="text-xs font-bold text-slate-400 uppercase">Strategy Details</h4>
                              <p className="text-sm text-slate-300">{s.description || 'No description available'}</p>
                              
                              <div className="grid grid-cols-2 gap-2 text-xs">
                                <div className="bg-slate-800/50 p-2 rounded">
                                  <span className="text-slate-500 block">Time Horizon</span>
                                  <span className="text-white">{s.time_horizon || '—'}</span>
                                </div>
                                <div className="bg-slate-800/50 p-2 rounded">
                                  <span className="text-slate-500 block">Direction</span>
                                  <span className="text-white">{s.direction || '—'}</span>
                                </div>
                                <div className="bg-slate-800/50 p-2 rounded">
                                  <span className="text-slate-500 block">Venue</span>
                                  <span className="text-white">{s.venue || '—'}</span>
                                </div>
                                <div className="bg-slate-800/50 p-2 rounded">
                                  <span className="text-slate-500 block">Universe Count</span>
                                  <span className="text-white">{s.universe_count || '—'}</span>
                                </div>
                              </div>
                              
                              {s.universe && s.universe.length > 0 && (
                                <div>
                                  <span className="text-xs text-slate-500 block mb-1">Asset Universe</span>
                                  <div className="flex flex-wrap gap-1">
                                    {s.universe.slice(0, 10).map(t => (
                                      <span key={t} className="text-[10px] px-2 py-0.5 bg-slate-800 rounded text-slate-400">
                                        {t}
                                      </span>
                                    ))}
                                    {s.universe.length > 10 && (
                                      <span className="text-[10px] px-2 py-0.5 bg-slate-800 rounded text-slate-500">
                                        +{s.universe.length - 10}
                                      </span>
                                    )}
                                  </div>
                                </div>
                              )}
                            </div>
                            
                            {/* Entry/Exit Logic */}
                            <div className="space-y-3">
                              <h4 className="text-xs font-bold text-slate-400 uppercase">Logic</h4>
                              
                              <div className="bg-slate-800/50 p-3 rounded">
                                <span className="text-[10px] text-slate-500 block mb-1">Entry Logic</span>
                                <span className="text-sm text-white font-mono">{s.entry_logic || '—'}</span>
                              </div>
                              
                              <div className="bg-slate-800/50 p-3 rounded">
                                <span className="text-[10px] text-slate-500 block mb-1">Exit Logic</span>
                                <span className="text-sm text-white font-mono">{s.exit_logic || '—'}</span>
                              </div>
                              
                              {/* Deploy Button - One Click */}
                              <button
                                onClick={(e) => {
                                  e.stopPropagation();
                                  handleDeploy(s);
                                }}
                                disabled={deployingId === s.id}
                                className="w-full py-2 bg-emerald-500 hover:bg-emerald-400 disabled:bg-slate-700 text-white text-xs font-bold rounded-lg transition-colors flex items-center justify-center gap-2"
                              >
                                {deployingId === s.id ? (
                                  <>
                                    <span className="w-3 h-3 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                                    Deploying...
                                  </>
                                ) : deployResult?.strategyId === s.id ? (
                                  deployResult.success ? (
                                    <span className="text-emerald-100">✓ Deployed!</span>
                                  ) : (
                                    <span className="text-rose-200">✗ {deployResult.error}</span>
                                  )
                                ) : (
                                  <>Deploy Strategy ({s.universe?.length || 0} tickers)</>
                                )}
                              </button>
                            </div>
                          </div>
                        </td>
                      </tr>
                    )}
                  </React.Fragment>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
      
      {/* Legend */}
      <div className="flex flex-wrap items-center gap-4 text-[10px] text-slate-500">
        <div className="flex items-center gap-1">
          <span className="w-3 h-3 bg-slate-800/50 rounded"></span>
          <span>Backtest Metrics</span>
        </div>
        <div className="flex items-center gap-1">
          <span className="w-3 h-3 bg-emerald-900/20 rounded"></span>
          <span>Live Performance</span>
        </div>
        <div className="ml-auto">
          <span>WR = Win Rate • PF = Profit Factor • MDD = Max Drawdown • — = No Data</span>
        </div>
      </div>
    </div>
  );
};

export { StrategyLab };

export default StrategyLab;
