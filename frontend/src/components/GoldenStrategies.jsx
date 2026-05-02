import React, { useState, useEffect } from 'react';

// Strategy Capital Pool Component with Enhanced UI
const StrategyCapitalPool = ({ strategyId, strategyName, onUpdate }) => {
  const [pool, setPool] = useState({
    total_assigned: 100000,
    used: 0,
    available: 100000,
    active_positions: 0,
    max_positions: 4
  });
  const [editing, setEditing] = useState(false);
  const [newTotal, setNewTotal] = useState(100000);
  const [loading, setLoading] = useState(false);

  useEffect(() => { fetchPool(); }, [strategyId]);

  const fetchPool = async () => {
    try {
      const res = await fetch(`/api/strategies/${encodeURIComponent(strategyId)}/capital-pool`);
      if (res.ok) {
        const data = await res.json();
        setPool(data);
        setNewTotal(data.total_assigned);
      }
    } catch (e) { console.error('Failed to fetch pool:', e); }
  };

  const updatePool = async () => {
    setLoading(true);
    try {
      const res = await fetch(`/api/strategies/${encodeURIComponent(strategyId)}/capital-pool`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ total_assigned: newTotal })
      });
      if (res.ok) {
        await fetchPool();
        setEditing(false);
        if (onUpdate) onUpdate();
      }
    } catch (e) { console.error('Failed to update pool:', e); }
    finally { setLoading(false); }
  };

  const usagePct = pool.total_assigned > 0 ? (pool.used / pool.total_assigned) * 100 : 0;
  const canTrade = pool.available >= (pool.total_assigned * 0.25);

  // Quick preset amounts
  const presets = [50000, 100000, 250000, 500000, 1000000];

  return (
    <div className="bg-slate-800/50 rounded-lg p-4 mb-4 border border-blue-500/20">
      <div className="flex items-center justify-between mb-3">
        <h4 className="text-xs font-bold text-blue-400 uppercase tracking-wider flex items-center gap-2">
          💰 Capital Pool (Shared)
        </h4>
        <button onClick={() => setEditing(!editing)} className="text-xs text-blue-400 hover:text-blue-300">
          {editing ? 'Cancel' : 'Edit'}
        </button>
      </div>

      {editing ? (
        <div className="space-y-3">
          {/* Quick Presets */}
          <div className="flex flex-wrap gap-2">
            {presets.map(preset => (
              <button
                key={preset}
                onClick={() => setNewTotal(preset)}
                className={`px-3 py-1.5 text-xs rounded-lg border transition-all ${
                  newTotal === preset 
                    ? 'bg-blue-500 border-blue-500 text-white' 
                    : 'bg-slate-900 border-white/10 text-slate-400 hover:border-blue-500/50'
                }`}
              >
                ${(preset/1000).toFixed(0)}k
              </button>
            ))}
          </div>
          
          {/* Custom Input with Slider */}
          <div>
            <label className="text-xs text-slate-400 block mb-1">Custom Amount ($)</label>
            <input 
              type="range"
              min="10000"
              max="2000000"
              step="10000"
              value={newTotal}
              onChange={(e) => setNewTotal(Number(e.target.value))}
              className="w-full h-2 bg-slate-700 rounded-lg appearance-none cursor-pointer mb-2"
            />
            <div className="flex items-center gap-2">
              <span className="text-slate-500 text-xs">$10k</span>
              <input 
                type="number" 
                value={newTotal} 
                onChange={(e) => setNewTotal(Number(e.target.value))}
                className="flex-1 bg-slate-900 border border-white/10 rounded-lg px-3 py-2 text-white text-sm text-center font-bold"
                min="10000" step="1000"
              />
              <span className="text-slate-500 text-xs">$2M</span>
            </div>
          </div>
          
          <button 
            onClick={updatePool} 
            disabled={loading}
            className="w-full bg-emerald-500 hover:bg-emerald-400 disabled:bg-slate-700 text-white text-xs font-bold py-2 rounded-lg"
          >
            {loading ? 'Saving...' : `Save $${newTotal.toLocaleString()}`}
          </button>
        </div>
      ) : (
        <div className="space-y-3">
          {/* Progress Bar */}
          <div>
            <div className="flex justify-between text-xs mb-1">
              <span className="text-slate-400">Pool Usage: {usagePct.toFixed(1)}%</span>
              <span className={canTrade ? 'text-emerald-400' : 'text-rose-400'}>
                {canTrade ? `🟢 Can Trade (${pool.active_positions}/${pool.max_positions})` : '🔴 Pool Exhausted'}
              </span>
            </div>
            <div className="h-2 rounded-full bg-slate-700 overflow-hidden">
              <div 
                className={`h-full rounded-full transition-all ${
                  usagePct >= 100 ? 'bg-rose-500' : usagePct > 75 ? 'bg-amber-500' : 'bg-emerald-500'
                }`}
                style={{ width: `${Math.min(usagePct, 100)}%` }}
              />
            </div>
          </div>

          {/* Numbers */}
          <div className="grid grid-cols-3 gap-3">
            <div className="bg-slate-900/50 rounded p-2 text-center">
              <span className="text-[10px] text-slate-500 block">Total Pool</span>
              <span className="text-sm font-bold text-white">${pool.total_assigned.toLocaleString()}</span>
            </div>
            
            <div className="bg-slate-900/50 rounded p-2 text-center">
              <span className="text-[10px] text-slate-500 block">Used</span>
              <span className="text-sm font-bold text-blue-400">${pool.used.toLocaleString()}</span>
            </div>
            
            <div className="bg-slate-900/50 rounded p-2 text-center">
              <span className="text-[10px] text-slate-500 block">Available</span>
              <span className={`text-sm font-bold ${pool.available > 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                ${pool.available.toLocaleString()}
              </span>
            </div>
          </div>

          {/* Trade Size Info */}
          <div className="p-2 bg-blue-500/10 rounded text-xs text-blue-400">
            <div className="flex justify-between">
              <span>Trade Size (25% of pool):</span>
              <span className="font-bold">${(pool.total_assigned * 0.25).toLocaleString()}</span>
            </div>
            <div className="flex justify-between mt-1">
              <span>Max Positions:</span>
              <span className="font-bold">{pool.max_positions}</span>
            </div>
            <div className="flex justify-between mt-1">
              <span>Active Positions:</span>
              <span className={`font-bold ${pool.active_positions >= pool.max_positions ? 'text-rose-400' : 'text-emerald-400'}`}>
                {pool.active_positions}
              </span>
            </div>
          </div>

          {!canTrade && (
            <div className="p-2 bg-rose-500/10 border border-rose-500/30 rounded text-xs text-rose-400">
              ⚠️ Cannot open new positions. Capital pool exhausted or below 25% threshold.
            </div>
          )}
        </div>
      )}
    </div>
  );
};

// Daily P&L Bar Chart Component
const DailyPnLChart = ({ strategyId }) => {
  const [dailyData, setDailyData] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchDailyPnL();
  }, [strategyId]);

  const fetchDailyPnL = async () => {
    try {
      // Get last 7 days of data from paper strategies endpoint
      const res = await fetch(`/api/paper-strategies/${strategyId}/daily-pnl?days=7`);
      if (res.ok) {
        const data = await res.json();
        // Sort by date ascending
        const sorted = (data.daily || []).sort((a, b) => new Date(a.date) - new Date(b.date));
        setDailyData(sorted.slice(-7)); // Last 7 days
      }
    } catch (e) {
      console.error('Failed to fetch daily P&L:', e);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="bg-slate-800/30 rounded-lg p-3 h-32 flex items-center justify-center">
        <span className="text-xs text-slate-500">Loading chart...</span>
      </div>
    );
  }

  if (dailyData.length === 0) {
    return (
      <div className="bg-slate-800/30 rounded-lg p-3">
        <span className="text-xs text-slate-400 block mb-2">Daily P&L (Last 7 Days)</span>
        <div className="h-24 flex items-center justify-center text-xs text-slate-500">
          No daily data available
        </div>
      </div>
    );
  }

  // Calculate max value for scaling
  const maxValue = Math.max(
    ...dailyData.map(d => Math.abs(d.realized_pnl || 0)),
    ...dailyData.map(d => Math.abs(d.unrealized_pnl || 0)),
    1
  );

  const formatDate = (dateStr) => {
    const d = new Date(dateStr);
    return `${d.getMonth() + 1}/${d.getDate()}`;
  };

  return (
    <div className="bg-slate-800/30 rounded-lg p-3">
      <div className="flex items-center justify-between mb-2">
        <span className="text-xs text-slate-400">Daily P&L (Last 7 Days)</span>
        <div className="flex gap-3 text-[10px]">
          <span className="flex items-center gap-1">
            <span className="w-2 h-2 rounded-sm bg-blue-500"></span>
            Unrealized
          </span>
          <span className="flex items-center gap-1">
            <span className="w-2 h-2 rounded-sm bg-emerald-500"></span>
            Realized
          </span>
        </div>
      </div>
      
      <div className="h-32 flex items-end justify-between gap-1">
        {dailyData.map((day, idx) => {
          const unrealized = day.unrealized_pnl || 0;
          const realized = day.realized_pnl || 0;
          const unrealizedHeight = Math.min((Math.abs(unrealized) / maxValue) * 100, 100);
          const realizedHeight = Math.min((Math.abs(realized) / maxValue) * 100, 100);
          
          return (
            <div key={idx} className="flex-1 flex flex-col items-center gap-1">
              <div className="w-full flex items-end justify-center gap-0.5 h-24">
                {/* Unrealized Bar */}
                <div
                  className={`w-3 rounded-t-sm transition-all ${
                    unrealized >= 0 ? 'bg-blue-500' : 'bg-rose-500'
                  }`}
                  style={{ 
                    height: `${unrealizedHeight}%`,
                    minHeight: unrealized !== 0 ? '2px' : '0'
                  }}
                  title={`Unrealized: $${unrealized.toFixed(2)}`}
                />
                {/* Realized Bar */}
                <div
                  className={`w-3 rounded-t-sm transition-all ${
                    realized >= 0 ? 'bg-emerald-500' : 'bg-rose-400'
                  }`}
                  style={{ 
                    height: `${realizedHeight}%`,
                    minHeight: realized !== 0 ? '2px' : '0'
                  }}
                  title={`Realized: $${realized.toFixed(2)}`}
                />
              </div>
              <span className="text-[9px] text-slate-500">{formatDate(day.date)}</span>
            </div>
          );
        })}
      </div>
      
      {/* Zero line */}
      <div className="mt-1 border-t border-slate-600/50"></div>
    </div>
  );
};

// Deployed Strategy Card with Live Stats
const DeployedStrategyCard = ({ strategyId, data, onRefresh, onDeactivateStrategy }) => {
  const [liveStats, setLiveStats] = useState(null);
  const [expanded, setExpanded] = useState(false);
  const [currentSignal, setCurrentSignal] = useState(null);
  const [strategyDetails, setStrategyDetails] = useState(null);

  useEffect(() => {
    fetchLiveStats();
    fetchCurrentSignal();
    fetchStrategyDetails();
  }, [strategyId]);

  const fetchStrategyDetails = async () => {
    try {
      const res = await fetch(`/api/strategies/${encodeURIComponent(strategyId)}`);
      if (res.ok) {
        const data = await res.json();
        setStrategyDetails(data);
      }
    } catch (e) { console.error('Failed to fetch strategy details:', e); }
  };

  const fetchCurrentSignal = async () => {
    try {
      // Get current signal from performance API
      const res = await fetch('/api/performance/strategy');
      if (res.ok) {
        const perfData = await res.json();
        const strategyPerf = perfData.strategies?.find(s => s.strategy_id === strategyId);
        if (strategyPerf?.current_signal) {
          setCurrentSignal(strategyPerf.current_signal);
        }
      }
    } catch (e) { console.error('Failed to fetch signal:', e); }
  };

  const fetchLiveStats = async () => {
    try {
      // Fetch actual performance data for this strategy
      const res = await fetch(`/api/paper-strategies`);
      if (res.ok) {
        const allData = await res.json();
        const positions = allData.strategies?.filter(p => p.strategy_id === strategyId) || [];
        
        // Calculate live stats
        const activePositions = positions.filter(p => p.trades_count > 0);
        const totalTrades = positions.reduce((sum, p) => sum + (p.trades_count || 0), 0);
        const totalRealized = positions.reduce((sum, p) => sum + (p.realized_pnl || 0), 0);
        const totalUnrealized = positions.reduce((sum, p) => sum + (p.unrealized_pnl || 0), 0);
        const totalInvested = positions.reduce((sum, p) => sum + (p.invested_capital || 0), 0);
        
        // Calculate actual win rate based on P&L
        const winningPositions = activePositions.filter(p => 
          (p.unrealized_pnl || 0) + (p.realized_pnl || 0) > 0
        ).length;
        const actualWinRate = activePositions.length > 0 
          ? (winningPositions / activePositions.length) * 100 
          : 0;
        
        setLiveStats({
          totalPositions: positions.length,
          activePositions: activePositions.length,
          pendingPositions: positions.length - activePositions.length,
          totalTrades,
          totalInvested,
          totalRealized,
          totalUnrealized,
          totalPnL: totalRealized + totalUnrealized,
          actualWinRate,
          positions: positions
        });
      }
    } catch (e) { console.error('Failed to fetch live stats:', e); }
  };

  const pnl = liveStats?.totalPnL || 0;
  const isProfitable = pnl >= 0;

  return (
    <div className="bg-slate-900/50 rounded-xl border border-emerald-500/20 overflow-hidden">
      <div 
        onClick={() => setExpanded(!expanded)}
        className="p-4 cursor-pointer hover:bg-slate-800/50 transition-colors"
      >
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className={`w-3 h-3 rounded-full ${liveStats?.activePositions > 0 ? 'bg-emerald-500 animate-pulse' : 'bg-amber-500'}`} />
            <div>
              <h3 className="text-sm font-bold text-white">{data.strategy_name}</h3>
              <p className="text-xs text-slate-400">
                {liveStats?.activePositions || 0} active • {liveStats?.pendingPositions || 0} pending
              </p>
            </div>
          </div>
          
          <div className="text-right">
            <div className={`text-sm font-bold ${isProfitable ? 'text-emerald-400' : 'text-rose-400'}`}>
              {isProfitable ? '+' : ''}${pnl.toLocaleString(undefined, {maximumFractionDigits: 0})}
            </div>
            <div className="text-xs text-slate-500">
              ${data.total_capital.toLocaleString()} allocated
            </div>
          </div>
        </div>
        
        {/* Current Signal Badge - CRITICAL KEY */}
        {currentSignal && (
          <div className={`mt-3 p-2 rounded-lg border ${
            currentSignal.action === 'BUY' 
              ? 'bg-emerald-500/10 border-emerald-500/30' 
              : 'bg-rose-500/10 border-rose-500/30'
          }`}>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="text-lg">{currentSignal.action === 'BUY' ? '🟢' : '🔴'}</span>
                <div>
                  <span className={`text-xs font-bold ${
                    currentSignal.action === 'BUY' ? 'text-emerald-400' : 'text-rose-400'
                  }`}>
                    {currentSignal.action} {currentSignal.ticker}
                  </span>
                  <span className="text-[10px] text-slate-400 block">
                    Strength: {currentSignal.strength}% | Confidence: {currentSignal.confidence}%
                  </span>
                </div>
              </div>
              <span className="text-sm font-mono text-white">
                ${currentSignal.price?.toFixed(2) || '--'}
              </span>
            </div>
          </div>
        )}
        
        {/* Signal Logic - Simplified */}
        {strategyDetails && (
          <div className="mt-2 p-2 bg-slate-800/30 rounded border border-white/5">
            <div className="flex items-center gap-3 text-xs">
              <span className="text-emerald-400">🟢 BUY: {strategyDetails.buy_signal?.substring(0, 40) || 'See details'}...</span>
            </div>
            <div className="flex items-center gap-2 mt-1 text-[10px]">
              <span className="text-emerald-400/70">WIN: +5%</span>
              <span className="text-slate-500">|</span>
              <span className="text-rose-400/70">LOSS: -5%</span>
            </div>
          </div>
        )}
        
        {/* Active Positions - Compact */}
        {liveStats?.activePositions > 0 && (
          <div className="mt-2 p-2 bg-blue-500/10 rounded border border-blue-500/20">
            <div className="flex items-center justify-between text-xs mb-1">
              <span className="text-blue-400 font-bold">{liveStats.activePositions} Active</span>
              <span className="text-[10px] text-slate-400">TP: +5% | SL: -5%</span>
            </div>
            <div className="flex flex-wrap gap-1">
              {liveStats.positions?.filter(p => p.trades_count > 0).slice(0, 3).map(pos => (
                <span key={pos.ticker} className={`text-[10px] px-1.5 py-0.5 rounded ${(pos.unrealized_pnl || 0) >= 0 ? 'bg-emerald-500/20 text-emerald-400' : 'bg-rose-500/20 text-rose-400'}`}>
                  {pos.ticker} {(pos.unrealized_pnl || 0) >= 0 ? '+' : ''}${(pos.unrealized_pnl || 0).toFixed(0)}
                </span>
              ))}
              {liveStats.positions?.filter(p => p.trades_count > 0).length > 3 && (
                <span className="text-[10px] text-slate-500">+{liveStats.positions.filter(p => p.trades_count > 0).length - 3} more</span>
              )}
            </div>
          </div>
        )}
        
        {/* Quick Stats Row - Simplified */}
        <div className="flex items-center gap-4 mt-3">
          <div className="flex items-center gap-1.5">
            <span className="text-[10px] text-slate-500">Win Rate:</span>
            <span className={`text-xs font-bold ${(liveStats?.actualWinRate || 0) >= 50 ? 'text-emerald-400' : 'text-amber-400'}`}>
              {(liveStats?.actualWinRate || 0).toFixed(0)}%
            </span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="text-[10px] text-slate-500">Trades:</span>
            <span className="text-xs font-bold text-blue-400">{liveStats?.totalTrades || 0}</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="text-[10px] text-slate-500">Deployed:</span>
            <span className="text-xs font-bold text-white">
              {data.total_capital > 0 ? ((liveStats?.totalInvested || 0) / data.total_capital * 100).toFixed(0) : 0}%
            </span>
          </div>
        </div>
        
        {/* Position Pills - Limited */}
        <div className="flex flex-wrap gap-1 mt-2">
          {data.tickers.slice(0, 4).map(t => (
            <span key={t} className="text-[10px] px-2 py-0.5 rounded-full bg-slate-800 text-slate-400 border border-white/5">
              {t}
            </span>
          ))}
          {data.tickers.length > 4 && (
            <span className="text-[10px] px-2 py-0.5 rounded-full bg-slate-800 text-slate-500">
              +{data.tickers.length - 4}
            </span>
          )}
        </div>
      </div>
      
      {expanded && liveStats && (
        <div className="px-4 pb-4 border-t border-white/10">
          {/* Simplified Performance Dashboard */}
          <div className="mt-4 space-y-3">
            
            {/* Main P&L Display */}
            <div className={`p-3 rounded-lg border ${isProfitable ? 'bg-emerald-500/10 border-emerald-500/30' : 'bg-rose-500/10 border-rose-500/30'}`}>
              <div className="flex items-center justify-between">
                <div>
                  <span className="text-[10px] text-slate-400 block">Total P&L</span>
                  <span className={`text-xl font-bold ${isProfitable ? 'text-emerald-400' : 'text-rose-400'}`}>
                    {isProfitable ? '+' : ''}${pnl.toLocaleString(undefined, {maximumFractionDigits: 0})}
                  </span>
                </div>
                <div className="text-right">
                  <span className="text-[10px] text-slate-400 block">Return</span>
                  <span className={`text-sm font-bold ${liveStats.totalInvested > 0 ? (pnl / liveStats.totalInvested * 100 >= 0 ? 'text-emerald-400' : 'text-rose-400') : 'text-slate-400'}`}>
                    {liveStats.totalInvested > 0 ? (pnl / liveStats.totalInvested * 100).toFixed(2) : '0.00'}%
                  </span>
                </div>
              </div>
              
              {/* Realized vs Unrealized */}
              <div className="flex gap-4 mt-2 pt-2 border-t border-white/10">
                <div>
                  <span className="text-[9px] text-slate-500 block">Realized</span>
                  <span className={`text-xs font-bold ${liveStats.totalRealized >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                    {liveStats.totalRealized >= 0 ? '+' : ''}${liveStats.totalRealized.toLocaleString(undefined, {maximumFractionDigits: 0})}
                  </span>
                </div>
                <div>
                  <span className="text-[9px] text-slate-500 block">Unrealized</span>
                  <span className={`text-xs font-bold ${liveStats.totalUnrealized >= 0 ? 'text-blue-400' : 'text-rose-400'}`}>
                    {liveStats.totalUnrealized >= 0 ? '+' : ''}${liveStats.totalUnrealized.toLocaleString(undefined, {maximumFractionDigits: 0})}
                  </span>
                </div>
              </div>
            </div>

            {/* Key Metrics - Single Row */}
            <div className="grid grid-cols-4 gap-2">
              <div className="bg-slate-800/50 p-2 rounded text-center">
                <span className="text-[9px] text-slate-400 block">Win Rate</span>
                <span className={`text-sm font-bold ${liveStats.actualWinRate >= 50 ? 'text-emerald-400' : 'text-amber-400'}`}>
                  {liveStats.actualWinRate.toFixed(0)}%
                </span>
              </div>
              <div className="bg-slate-800/50 p-2 rounded text-center">
                <span className="text-[9px] text-slate-400 block">Trades</span>
                <span className="text-sm font-bold text-blue-400">{liveStats.totalTrades}</span>
              </div>
              <div className="bg-slate-800/50 p-2 rounded text-center">
                <span className="text-[9px] text-slate-400 block">Active</span>
                <span className="text-sm font-bold text-white">{liveStats.activePositions}</span>
              </div>
              <div className="bg-slate-800/50 p-2 rounded text-center">
                <span className="text-[9px] text-slate-400 block">Pending</span>
                <span className="text-sm font-bold text-slate-400">{liveStats.pendingPositions}</span>
              </div>
            </div>

            {/* Capital Deployment Bar */}
            <div className="bg-slate-800/30 p-2 rounded-lg">
              <div className="flex justify-between text-[10px] mb-1">
                <span className="text-slate-400">Deployed</span>
                <span className="text-slate-300">${liveStats.totalInvested.toLocaleString()} / ${data.total_capital.toLocaleString()}</span>
              </div>
              <div className="h-1.5 rounded-full bg-slate-700 overflow-hidden">
                <div 
                  className="h-full rounded-full bg-blue-500 transition-all"
                  style={{ width: `${data.total_capital > 0 ? (liveStats.totalInvested / data.total_capital) * 100 : 0}%` }}
                />
              </div>
            </div>

            {/* Actions - Compact */}
            <div className="flex gap-2 pt-2">
              <button
                onClick={(e) => { e.stopPropagation(); onDeactivateStrategy(strategyId, 'close'); }}
                className="flex-1 py-2 bg-rose-500/20 hover:bg-rose-500/30 border border-rose-500/30 rounded-lg text-xs font-medium text-rose-400 transition-colors"
              >
                Close All
              </button>
              <button
                onClick={(e) => { e.stopPropagation(); onDeactivateStrategy(strategyId, 'keep'); }}
                className="flex-1 py-2 bg-amber-500/20 hover:bg-amber-500/30 border border-amber-500/30 rounded-lg text-xs font-medium text-amber-400 transition-colors"
              >
                Pause
              </button>
              <button 
                onClick={(e) => { e.stopPropagation(); fetchLiveStats(); }}
                className="px-3 py-2 text-xs text-slate-400 hover:text-white bg-slate-800/50 rounded-lg"
              >
                🔄
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

// Capital Allocation Slider Component
const CapitalAllocationSlider = ({ value, onChange, strategyName }) => {
  const presets = [
    { label: '$50k', value: 50000 },
    { label: '$100k', value: 100000 },
    { label: '$250k', value: 250000 },
    { label: '$500k', value: 500000 },
    { label: '$1M', value: 1000000 },
  ];
  
  const tradeSize = Math.floor(value * 0.25);
  const maxPositions = 4;

  return (
    <div className="bg-slate-800/50 rounded-lg p-4 space-y-4">
      <div className="flex items-center justify-between">
        <label className="text-xs font-bold text-blue-400 uppercase">Capital Allocation</label>
        <span className="text-lg font-bold text-white">${value.toLocaleString()}</span>
      </div>
      
      {/* Quick Presets */}
      <div className="flex gap-2">
        {presets.map(preset => (
          <button
            key={preset.value}
            onClick={() => onChange(preset.value)}
            className={`flex-1 py-2 text-xs rounded-lg border transition-all ${
              value === preset.value
                ? 'bg-blue-500 border-blue-500 text-white'
                : 'bg-slate-900 border-white/10 text-slate-400 hover:border-blue-500/50'
            }`}
          >
            {preset.label}
          </button>
        ))}
      </div>
      
      {/* Slider */}
      <div className="space-y-2">
        <input
          type="range"
          min="10000"
          max="2000000"
          step="10000"
          value={value}
          onChange={(e) => onChange(Number(e.target.value))}
          className="w-full h-3 bg-slate-700 rounded-lg appearance-none cursor-pointer accent-blue-500"
        />
        <div className="flex justify-between text-xs text-slate-500">
          <span>$10k</span>
          <span>$500k</span>
          <span>$1M</span>
          <span>$2M</span>
        </div>
      </div>
      
      {/* Allocation Breakdown */}
      <div className="grid grid-cols-2 gap-3 pt-2 border-t border-white/10">
        <div className="text-center p-2 bg-slate-900/50 rounded">
          <span className="text-[10px] text-slate-500 block">Per Trade (25%)</span>
          <span className="text-sm font-bold text-emerald-400">${tradeSize.toLocaleString()}</span>
        </div>
        <div className="text-center p-2 bg-slate-900/50 rounded">
          <span className="text-[10px] text-slate-500 block">Max Positions</span>
          <span className="text-sm font-bold text-blue-400">{maxPositions}</span>
        </div>
      </div>
    </div>
  );
};

export const GoldenStrategies = ({ onDeployStrategy, onSelectStrategy }) => {
  const [strategies, setStrategies] = useState([]);
  const [paperStrategies, setPaperStrategies] = useState([]);
  const [strategyStats, setStrategyStats] = useState({});
  const [loading, setLoading] = useState(true);
  const [expandedStrategy, setExpandedStrategy] = useState(null);
  const [deploying, setDeploying] = useState(null);
  const [showPaperSection, setShowPaperSection] = useState(true);
  const [activeTab, setActiveTab] = useState('deploy'); // 'deploy' or 'available'
  const [executionMode, setExecutionMode] = useState('SIMULATION');
  
  // Pipeline summary
  const [pipelineSummary, setPipelineSummary] = useState(null);

  // Search and Filter State
  const [searchQuery, setSearchQuery] = useState('');
  const [filterPriority, setFilterPriority] = useState('ALL');
  const [filterAssetClass, setFilterAssetClass] = useState('ALL');
  const [filterMarket, setFilterMarket] = useState('ALL');
  const [filterMinWinRate, setFilterMinWinRate] = useState(0);
  const [filterSignalType, setFilterSignalType] = useState('ALL');
  
  // Multi-select and custom pool size - persisted in localStorage
  const [selectedStrategies, setSelectedStrategies] = useState(() => {
    if (typeof window !== 'undefined') {
      const saved = localStorage.getItem('goldenStrategies_selected');
      return saved ? new Set(JSON.parse(saved)) : new Set();
    }
    return new Set();
  });
  
  const [customPools, setCustomPools] = useState(() => {
    if (typeof window !== 'undefined') {
      const saved = localStorage.getItem('goldenStrategies_pools');
      return saved ? JSON.parse(saved) : {};
    }
    return {};
  });
  
  const [defaultPoolSize, setDefaultPoolSize] = useState(() => {
    if (typeof window !== 'undefined') {
      const saved = localStorage.getItem('goldenStrategies_defaultPool');
      return saved ? parseInt(saved) : 100000;
    }
    return 100000;
  });

  // Persist selections to localStorage
  useEffect(() => {
    localStorage.setItem('goldenStrategies_selected', JSON.stringify([...selectedStrategies]));
  }, [selectedStrategies]);

  useEffect(() => {
    localStorage.setItem('goldenStrategies_pools', JSON.stringify(customPools));
  }, [customPools]);

  useEffect(() => {
    localStorage.setItem('goldenStrategies_defaultPool', defaultPoolSize.toString());
  }, [defaultPoolSize]);

  useEffect(() => {
    fetchStrategies();
    fetchPaperStrategies();
    fetchStrategyStats();
    fetchPipelineSummary();

    // Refresh every 60 seconds
    const interval = setInterval(() => {
      fetchPaperStrategies();
      fetchStrategyStats();
      fetchPipelineSummary();
    }, 60000);
    return () => clearInterval(interval);
  }, []);

  const fetchStrategies = () => {
    fetch('/api/strategies/researcher?priority=ALL')
      .then(r => r.json())
      .then(data => {
        if (data.strategies) {
          const enriched = data.strategies.map(s => ({
            ...s,
            sharpe: s.sharpe_ratio || 1.0,
            win_rate: s.win_rate || 55,
            avg_hold_days: parseInt(s.time_horizon) || 5,
            capacity: '$50M',
            max_dd: s.max_drawdown ? `${s.max_drawdown}%` : '-10%',
            assetCount: s.universe?.length || 0,
            tradeSize: Math.floor((customPools[s.id] || defaultPoolSize) * 0.25)
          }));
          setStrategies(enriched);
        }
        setLoading(false);
      })
      .catch(() => setLoading(false));
  };

  const fetchPipelineSummary = () => {
    fetch('/api/strategies/pipeline-summary')
      .then(r => r.json())
      .then(data => setPipelineSummary(data))
      .catch(e => console.error('Failed to fetch pipeline summary:', e));
  };

  const fetchPaperStrategies = () => {
    fetch('/api/paper-strategies')
      .then(r => r.json())
      .then(data => { 
        if (data.strategies) setPaperStrategies(data.strategies);
        if (data.execution_mode) setExecutionMode(data.execution_mode);
      })
      .catch(e => console.error('Failed to fetch:', e));
  };
  
  const fetchStrategyStats = async () => {
    try {
      // Fetch all paper strategies and calculate actual stats
      const res = await fetch('/api/paper-strategies');
      if (res.ok) {
        const data = await res.json();
        const stats = {};
        
        // Group by strategy and calculate actual win rates
        data.strategies?.forEach(pos => {
          if (!stats[pos.strategy_id]) {
            stats[pos.strategy_id] = {
              totalPositions: 0,
              activePositions: 0,
              winningPositions: 0,
              totalPnL: 0,
              totalInvested: 0
            };
          }
          
          stats[pos.strategy_id].totalPositions++;
          stats[pos.strategy_id].totalInvested += pos.invested_capital || 0;
          
          if (pos.trades_count > 0) {
            stats[pos.strategy_id].activePositions++;
            const posPnL = (pos.unrealized_pnl || 0) + (pos.realized_pnl || 0);
            stats[pos.strategy_id].totalPnL += posPnL;
            if (posPnL > 0) {
              stats[pos.strategy_id].winningPositions++;
            }
          }
        });
        
        // Calculate actual win rates
        Object.keys(stats).forEach(key => {
          const s = stats[key];
          s.actualWinRate = s.activePositions > 0 
            ? (s.winningPositions / s.activePositions) * 100 
            : 0;
        });
        
        setStrategyStats(stats);
      }
    } catch (e) { console.error('Failed to fetch stats:', e); }
  };
  
  const toggleSelection = (strategyId) => {
    setSelectedStrategies(prev => {
      const newSet = new Set(prev);
      if (newSet.has(strategyId)) newSet.delete(strategyId);
      else newSet.add(strategyId);
      return newSet;
    });
  };
  
  const toggleAll = () => {
    if (selectedStrategies.size === strategies.length) setSelectedStrategies(new Set());
    else setSelectedStrategies(new Set(strategies.map(s => s.id)));
  };

  const handleMultiDeploy = async () => {
    setDeploying('multi');
    const results = [];
    
    for (const strategyId of selectedStrategies) {
      const strategy = strategies.find(s => s.id === strategyId);
      if (!strategy) continue;
      
      const poolSize = customPools[strategyId] || defaultPoolSize;
      
      try {
        // Use deploy-auto: deploys full universe with BUY signals only, max 5 positions
        const res = await fetch('/api/strategies/deploy-auto', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            strategy_id: strategyId,
            total_pool: poolSize,
            trade_size_pct: 0.25,
            max_positions: 5
          })
        });
        
        const data = await res.json();
        if (res.ok && data.success) {
          results.push({ 
            strategy: strategy.name, 
            status: 'success',
            deployed: data.positions_created,
            tickers: data.tickers_deployed
          });
        } else {
          results.push({ 
            strategy: strategy.name, 
            status: 'error', 
            error: data.error || 'Deploy failed'
          });
        }
      } catch (e) {
        results.push({ strategy: strategy.name, status: 'error', error: e.message });
      }
    }
    
    setDeploying(null);
    setSelectedStrategies(new Set());
    fetchPaperStrategies();
    fetchStrategyStats();
    
    // Show detailed results
    const successCount = results.filter(r => r.status === 'success').length;
    const detailMsg = results.map(r => {
      if (r.status === 'success') {
        return `✅ ${r.strategy}: ${r.deployed} positions (${r.tickers?.join(', ')})`;
      } else {
        return `❌ ${r.strategy}: ${r.error}`;
      }
    }).join('\n');
    
    alert(`Deployed ${successCount}/${results.length} strategies:\n\n${detailMsg}`);
    if (onDeployStrategy) onDeployStrategy();
  };

  // Handle strategy deactivation
  const handleDeactivateStrategy = async (strategyId, action) => {
    const actionText = action === 'close' ? 'close all positions and deactivate' : 'pause (keep positions)';
    if (!confirm(`Are you sure you want to ${actionText} this strategy?`)) return;

    try {
      const res = await fetch(`/api/strategies/${strategyId}/deactivate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action }) // 'close' or 'keep'
      });

      if (res.ok) {
        const data = await res.json();
        alert(`✅ Strategy ${action === 'close' ? 'closed' : 'paused'} successfully!${data.positions_closed ? ` (${data.positions_closed} positions closed)` : ''}`);
        fetchPaperStrategies();
        fetchStrategyStats();
        if (onDeployStrategy) onDeployStrategy();
      } else {
        const err = await res.json();
        alert(`❌ Failed: ${err.detail || 'Unknown error'}`);
      }
    } catch (e) {
      console.error('Failed to deactivate strategy:', e);
      alert('❌ Network error. Please try again.');
    }
  };

  const groupedPaperStrategies = paperStrategies.reduce((acc, ps) => {
    if (!acc[ps.strategy_id]) acc[ps.strategy_id] = { strategy_name: ps.strategy_name, tickers: [], total_capital: 0 };
    acc[ps.strategy_id].tickers.push(ps.ticker);
    acc[ps.strategy_id].total_capital += ps.capital;
    return acc;
  }, {});

  if (loading) {
    return (
      <div className="p-12 text-center text-slate-500">
        <div className="w-8 h-8 border-2 border-slate-600 border-t-blue-500 rounded-full animate-spin mx-auto mb-4" />
        Loading {strategies.length} JT-Ready Strategies...
      </div>
    );
  }

  return (
    <div className="golden-strategies space-y-4">
      {/* Tab Navigation */}
      <div className="flex items-center gap-2 mb-6 bg-slate-900/50 p-1 rounded-lg">
        <button
          onClick={() => setActiveTab('deploy')}
          className={`flex-1 py-2 px-4 rounded-md text-sm font-bold transition-all ${
            activeTab === 'deploy' 
              ? 'bg-blue-500 text-white' 
              : 'text-slate-400 hover:text-white'
          }`}
        >
          📋 Deployed ({Object.keys(groupedPaperStrategies).length})
        </button>
        <button
          onClick={() => setActiveTab('available')}
          className={`flex-1 py-2 px-4 rounded-md text-sm font-bold transition-all ${
            activeTab === 'available' 
              ? 'bg-blue-500 text-white' 
              : 'text-slate-400 hover:text-white'
          }`}
        >
          🏆 Available ({strategies.length})
        </button>
      </div>

      {/* Pipeline Stage Summary */}
      {pipelineSummary && (
        <div className="flex items-center gap-1 p-1 bg-slate-900/50 rounded-xl border border-white/5">
          {[
            { key: 'experimental', label: 'Experimental', color: 'slate', icon: '🧪' },
            { key: 'near_golden', label: 'Near Golden', color: 'blue', icon: '🔵' },
            { key: 'golden', label: 'Golden', color: 'amber', icon: '⭐' },
            { key: 'deployed', label: 'Deployed', color: 'emerald', icon: '🚀' },
          ].map((stage, i) => (
            <React.Fragment key={stage.key}>
              {i > 0 && <span className="text-slate-700 text-xs">→</span>}
              <div className={`flex-1 text-center py-2 px-2 rounded-lg transition-all ${
                stage.key === 'experimental' ? 'bg-slate-800/50' :
                stage.key === 'near_golden' ? 'bg-blue-500/10' :
                stage.key === 'golden' ? 'bg-amber-500/10' :
                'bg-emerald-500/10'
              }`}>
                <div className="text-lg font-bold text-white">{pipelineSummary[stage.key] || 0}</div>
                <div className="text-[9px] text-slate-400 uppercase tracking-wider">{stage.label}</div>
              </div>
            </React.Fragment>
          ))}
        </div>
      )}

      {/* DEPLOYED TAB */}
      {activeTab === 'deploy' && (
        <div className="space-y-4">
          {Object.keys(groupedPaperStrategies).length === 0 ? (
            <div className="text-center p-12 text-slate-500">
              <div className="text-4xl mb-4">📋</div>
              <p className="text-lg font-bold text-white mb-2">No Strategies Deployed</p>
              <p className="text-sm mb-4">
                {executionMode === 'SIMULATION' 
                  ? "No simulation strategies. Switch to 'Available' tab to deploy."
                  : executionMode === 'PAPER_TRADING'
                  ? "No paper trading strategies. Deploy from 'Available' tab to trade with IBKR Paper."
                  : "No live strategies. Deploy from 'Available' tab to trade with real money."
                }
              </p>
              <div className={`inline-flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-bold ${
                executionMode === 'SIMULATION' ? 'bg-emerald-500/20 text-emerald-400' :
                executionMode === 'PAPER_TRADING' ? 'bg-amber-500/20 text-amber-400' :
                'bg-rose-500/20 text-rose-400'
              }`}>
                🧪 {executionMode.replace('_', ' ')}
              </div>
              <p className="text-[10px] text-slate-600 mt-3 max-w-md mx-auto">
                Strategies are isolated by execution mode. Deploying in {executionMode.replace('_', ' ')} 
                will not affect strategies in other modes.
              </p>
            </div>
          ) : (
            <>
              {/* Summary Stats - What Really Matters */}
              {(() => {
                // Calculate key metrics
                // Count strategies with actual positions (trades_count > 0)
                const activeWithPositions = Object.entries(strategyStats).filter(
                  ([id, stats]) => stats.activePositions > 0
                ).length;
                
                const strategiesWithPnl = Object.entries(strategyStats).map(([id, stats]) => ({
                  id,
                  pnl: stats.totalPnL || 0,
                  active: stats.activePositions || 0
                }));
                
                const winningStrategies = strategiesWithPnl.filter(s => s.pnl > 0).length;
                const losingStrategies = strategiesWithPnl.filter(s => s.pnl < 0).length;
                const flatStrategies = strategiesWithPnl.filter(s => s.pnl === 0).length;
                
                const totalPnl = strategiesWithPnl.reduce((sum, s) => sum + s.pnl, 0);
                
                return (
                  <div className="grid grid-cols-4 gap-3 mb-6">
                    <div className="bg-slate-900/50 rounded-xl p-4 text-center border border-white/10">
                      <span className="text-2xl font-bold text-white">{Object.keys(groupedPaperStrategies).length}</span>
                      <span className="text-xs text-slate-500 block">Total Strategies</span>
                    </div>
                    <div className="bg-slate-900/50 rounded-xl p-4 text-center border border-white/10">
                      <span className="text-2xl font-bold text-blue-400">{activeWithPositions}</span>
                      <span className="text-xs text-slate-500 block">In Market (Active)</span>
                    </div>
                    <div className="bg-slate-900/50 rounded-xl p-4 text-center border border-white/10">
                      <div className="flex items-center justify-center gap-2">
                        <span className="text-xl font-bold text-emerald-400">{winningStrategies}</span>
                        <span className="text-slate-600">/</span>
                        <span className="text-xl font-bold text-rose-400">{losingStrategies}</span>
                      </div>
                      <span className="text-xs text-slate-500 block">Winning / Losing</span>
                    </div>
                    <div className={`rounded-xl p-4 text-center border ${
                      totalPnl >= 0 ? 'bg-emerald-900/20 border-emerald-500/30' : 'bg-rose-900/20 border-rose-500/30'
                    }`}>
                      <span className={`text-2xl font-bold ${totalPnl >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                        {totalPnl >= 0 ? '+' : ''}${Math.abs(totalPnl).toLocaleString(undefined, {maximumFractionDigits: 0})}
                      </span>
                      <span className="text-xs text-slate-500 block">Total Strategy P&L</span>
                    </div>
                  </div>
                );
              })()}
              
              {/* Deployed Strategy Cards */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                {Object.entries(groupedPaperStrategies).map(([strategyId, data]) => (
                  <DeployedStrategyCard 
                    key={strategyId}
                    strategyId={strategyId}
                    data={data}
                    onRefresh={fetchPaperStrategies}
                    onDeactivateStrategy={handleDeactivateStrategy}
                  />
                ))}
              </div>
            </>
          )}
        </div>
      )}

      {/* AVAILABLE TAB */}
      {activeTab === 'available' && (
        <>
          {/* Multi-Deploy Header */}
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-xl font-black text-white flex items-center gap-2">
                <span className="text-2xl">🏆</span>
                {strategies.length} JT-Ready Strategies
              </h2>
              <p className="text-sm text-slate-400 mt-1">Research-validated strategies across US, HK, CN, SG markets</p>
            </div>

            <div className="flex items-center gap-2">
              {selectedStrategies.size > 0 && (
                <button
                  onClick={handleMultiDeploy}
                  disabled={deploying === 'multi'}
                  className="px-4 py-2 bg-emerald-500 hover:bg-emerald-400 disabled:bg-slate-700 text-white text-sm font-bold rounded-lg"
                >
                  {deploying === 'multi' ? 'Deploying...' : `Deploy ${selectedStrategies.size} Selected`}
                </button>
              )}
              <button
                onClick={toggleAll}
                className="px-3 py-2 text-xs text-slate-400 hover:text-white border border-white/10 rounded-lg"
              >
                {selectedStrategies.size === strategies.length ? 'Deselect All' : 'Select All'}
              </button>
            </div>
          </div>

          {/* Priority Filter Pills */}
          <div className="flex items-center gap-2 mb-4">
            {[
              { key: 'ALL', label: 'All', badgeClass: 'bg-slate-700/50 text-slate-300' },
              { key: 'GOLDEN', label: 'Golden', badgeClass: 'bg-amber-500/20 text-amber-400 ring-1 ring-amber-500/30' },
              { key: 'NEAR_GOLDEN', label: 'Near Golden', badgeClass: 'bg-blue-500/20 text-blue-400 ring-1 ring-blue-500/30' },
              { key: 'EXPERIMENTAL', label: 'Experimental', badgeClass: 'bg-slate-600/20 text-slate-400 ring-1 ring-slate-500/30' },
            ].map(p => {
              const count = p.key === 'ALL'
                ? strategies.length
                : strategies.filter(s => s.priority === p.key).length;
              return (
                <button
                  key={p.key}
                  onClick={() => setFilterPriority(p.key)}
                  className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all ${
                    filterPriority === p.key
                      ? p.key === 'ALL' ? 'bg-white/10 text-white ring-1 ring-white/20' : p.badgeClass
                      : 'text-slate-500 hover:text-slate-300'
                  }`}
                >
                  {p.label} ({count})
                </button>
              );
            })}
          </div>
          
          {/* Default Capital Setting */}
          <CapitalAllocationSlider 
            value={defaultPoolSize}
            onChange={setDefaultPoolSize}
            strategyName="Default"
          />

          {/* Search and Filters */}
          <div className="mt-6 p-4 bg-slate-900/50 rounded-xl border border-white/10 space-y-4">
            {/* Search Bar */}
            <div className="relative">
              <span className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500">🔍</span>
              <input
                type="text"
                placeholder="Search strategies by name, ticker, or description..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-10 pr-4 py-2 bg-slate-800 border border-white/10 rounded-lg text-white text-sm placeholder-slate-500 focus:border-blue-500/50 focus:outline-none"
              />
            </div>
            
            {/* Filter Row */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              {/* Asset Class Filter */}
              <div>
                <label className="text-[10px] text-slate-500 uppercase block mb-1">Asset Class</label>
                <select
                  value={filterAssetClass}
                  onChange={(e) => setFilterAssetClass(e.target.value)}
                  className="w-full bg-slate-800 border border-white/10 rounded-lg px-3 py-2 text-sm text-white focus:border-blue-500/50 focus:outline-none"
                >
                  <option value="ALL">All Classes</option>
                  <option value="STOCK">Stocks</option>
                  <option value="FX">FX</option>
                  <option value="CRYPTO">Crypto</option>
                  <option value="COMMODITY">Commodities</option>
                </select>
              </div>
              
              {/* Market Filter */}
              <div>
                <label className="text-[10px] text-slate-500 uppercase block mb-1">Market</label>
                <select
                  value={filterMarket}
                  onChange={(e) => setFilterMarket(e.target.value)}
                  className="w-full bg-slate-800 border border-white/10 rounded-lg px-3 py-2 text-sm text-white focus:border-blue-500/50 focus:outline-none"
                >
                  <option value="ALL">All Markets</option>
                  <option value="US">US</option>
                  <option value="HK">Hong Kong</option>
                  <option value="CN">China</option>
                  <option value="SG">Singapore</option>
                </select>
              </div>
              
              {/* Min Win Rate Filter */}
              <div>
                <label className="text-[10px] text-slate-500 uppercase block mb-1">Min Win Rate</label>
                <select
                  value={filterMinWinRate}
                  onChange={(e) => setFilterMinWinRate(Number(e.target.value))}
                  className="w-full bg-slate-800 border border-white/10 rounded-lg px-3 py-2 text-sm text-white focus:border-blue-500/50 focus:outline-none"
                >
                  <option value={0}>Any</option>
                  <option value={50}>50%+</option>
                  <option value={60}>60%+</option>
                  <option value={70}>70%+</option>
                  <option value={80}>80%+</option>
                </select>
              </div>
              
              {/* Signal Type Filter */}
              <div>
                <label className="text-[10px] text-slate-500 uppercase block mb-1">Signal</label>
                <select
                  value={filterSignalType}
                  onChange={(e) => setFilterSignalType(e.target.value)}
                  className="w-full bg-slate-800 border border-white/10 rounded-lg px-3 py-2 text-sm text-white focus:border-blue-500/50 focus:outline-none"
                >
                  <option value="ALL">All Signals</option>
                  <option value="BUY">Buy Only</option>
                  <option value="SELL">Sell Only</option>
                  <option value="HOLD">Hold/None</option>
                </select>
              </div>
            </div>
            
            {/* Clear Filters */}
            {(searchQuery || filterPriority !== 'ALL' || filterAssetClass !== 'ALL' || filterMarket !== 'ALL' || filterMinWinRate > 0 || filterSignalType !== 'ALL') && (
              <div className="flex items-center justify-between">
                <button
                  onClick={() => {
                    setSearchQuery('');
                    setFilterPriority('ALL');
                    setFilterAssetClass('ALL');
                    setFilterMarket('ALL');
                    setFilterMinWinRate(0);
                    setFilterSignalType('ALL');
                  }}
                  className="text-xs text-slate-400 hover:text-white underline"
                >
                  Clear all filters
                </button>
                <span className="text-xs text-slate-500">
                  {strategies.filter(s => {
                    const searchLower = searchQuery.toLowerCase();
                    const matchesSearch = !searchQuery || 
                      s.name?.toLowerCase().includes(searchLower) ||
                      s.id?.toLowerCase().includes(searchLower) ||
                      s.description?.toLowerCase().includes(searchLower) ||
                      s.universe?.some(t => t.toLowerCase().includes(searchLower));
                    const matchesAsset = filterAssetClass === 'ALL' || s.asset_class === filterAssetClass;
                    const matchesMarket = filterMarket === 'ALL' || s.market === filterMarket;
                    const matchesWinRate = (s.win_rate || 0) >= filterMinWinRate;
                    return matchesSearch && matchesAsset && matchesMarket && matchesWinRate;
                  }).length} of {strategies.length} strategies
                </span>
              </div>
            )}
          </div>

          {/* Strategy Cards Grid */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 mt-6">
            {strategies.filter(strategy => {
              // Search filter
              const searchLower = searchQuery.toLowerCase();
              const matchesSearch = !searchQuery || 
                strategy.name?.toLowerCase().includes(searchLower) ||
                strategy.id?.toLowerCase().includes(searchLower) ||
                strategy.description?.toLowerCase().includes(searchLower) ||
                strategy.universe?.some(t => t.toLowerCase().includes(searchLower));
              
              // Asset class filter
              const matchesAsset = filterAssetClass === 'ALL' || strategy.asset_class === filterAssetClass;
              
              // Market filter
              const matchesMarket = filterMarket === 'ALL' || strategy.market === filterMarket;
              
              // Win rate filter
              const matchesWinRate = (strategy.win_rate || 0) >= filterMinWinRate;
              
              // Signal type filter (would need current signal data)
              const matchesSignal = filterSignalType === 'ALL'; // Simplified for now

              // Priority filter
              const matchesPriority = filterPriority === 'ALL' || strategy.priority === filterPriority;

              return matchesSearch && matchesAsset && matchesMarket && matchesWinRate && matchesSignal && matchesPriority;
            }).map(strategy => {
              const isSelected = selectedStrategies.has(strategy.id);
              const isExpanded = expandedStrategy === strategy.id;
              const poolSize = customPools[strategy.id] || defaultPoolSize;
              const tradeSize = Math.floor(poolSize * 0.25);
              const actualStats = strategyStats[strategy.id];
              
              return (
                <div key={strategy.id} 
                  className={`rounded-xl border transition-all ${
                    isSelected ? 'border-emerald-500 bg-emerald-500/5' : 'border-white/10 bg-slate-900/50'
                  }`}
                >
                  <div className="p-4">
                    <div className="flex items-start justify-between">
                      <div className="flex items-start gap-3">
                        <input 
                          type="checkbox" 
                          checked={isSelected} 
                          onChange={() => toggleSelection(strategy.id)}
                          className="mt-1 w-4 h-4 rounded border-slate-600 text-emerald-500"
                        />
                        
                        <div>
                          <div className="flex items-center gap-2">
                            <h3 className="text-sm font-bold text-white">{strategy.name}</h3>
                            <span className={`text-[9px] px-1.5 py-0.5 rounded-md font-bold uppercase tracking-wider ${
                              strategy.priority === 'GOLDEN' ? 'bg-amber-500/20 text-amber-400 ring-1 ring-amber-500/30' :
                              strategy.priority === 'NEAR_GOLDEN' ? 'bg-blue-500/20 text-blue-400 ring-1 ring-blue-500/30' :
                              'bg-slate-600/30 text-slate-400 ring-1 ring-slate-500/30'
                            }`}>
                              {strategy.priority === 'NEAR_GOLDEN' ? 'Near Golden' : strategy.priority?.toLowerCase() || 'experimental'}
                            </span>
                          </div>
                          <p className="text-xs text-slate-400 mt-1 line-clamp-2">{strategy.description}</p>

                          <div className="flex flex-wrap gap-2 mt-2">
                            <span className="text-[10px] px-2 py-0.5 rounded bg-blue-500/20 text-blue-400">
                              {strategy.sharpe?.toFixed(2)} Sharpe
                            </span>
                            <span className="text-[10px] px-2 py-0.5 rounded bg-purple-500/20 text-purple-400">
                              {strategy.assetCount} assets
                            </span>
                            {actualStats ? (
                              <span className={`text-[10px] px-2 py-0.5 rounded ${
                                actualStats.actualWinRate >= 50 
                                  ? 'bg-emerald-500/20 text-emerald-400' 
                                  : 'bg-amber-500/20 text-amber-400'
                              }`}>
                                {actualStats.actualWinRate.toFixed(1)}% Actual Win
                              </span>
                            ) : (
                              <span className="text-[10px] px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-400">
                                {strategy.win_rate}% Backtest Win
                              </span>
                            )}
                          </div>
                        </div>
                      </div>
                      
                      <div className="flex items-center gap-1">
                        {onSelectStrategy && (
                          <button
                            onClick={(e) => { e.stopPropagation(); onSelectStrategy(strategy.id); }}
                            className="text-[10px] px-2 py-1 rounded bg-blue-500/15 text-blue-300 ring-1 ring-blue-500/25 hover:bg-blue-500/25 font-semibold"
                            title="Open detail"
                          >
                            Detail →
                          </button>
                        )}
                        <button
                          onClick={() => setExpandedStrategy(isExpanded ? null : strategy.id)}
                          className="text-slate-400 hover:text-white px-1"
                        >
                          {isExpanded ? '▼' : '▶'}
                        </button>
                      </div>
                    </div>
                    
                    {/* Custom Capital Allocation when Selected */}
                    {isSelected && (
                      <div className="mt-3">
                        <CapitalAllocationSlider 
                          value={poolSize}
                          onChange={(val) => setCustomPools(prev => ({ ...prev, [strategy.id]: val }))}
                          strategyName={strategy.name}
                        />
                      </div>
                    )}
                  </div>

                  {isExpanded && (
                    <div className="px-4 pb-4 border-t border-white/10 pt-4">
                      <StrategyCapitalPool
                        strategyId={strategy.id}
                        strategyName={strategy.name}
                        onUpdate={fetchPaperStrategies}
                      />

                      {/* Review Panel - Win Rate Gauge */}
                      {strategy.win_rate != null && (
                        <div className="mb-4 p-3 bg-slate-800/50 rounded-lg border border-white/5">
                          <div className="flex items-center justify-between mb-2">
                            <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider">Backtest Win Rate</h4>
                            <span className={`text-lg font-black font-mono ${
                              strategy.win_rate >= 60 ? 'text-emerald-400' : strategy.win_rate >= 50 ? 'text-amber-400' : 'text-rose-400'
                            }`}>{typeof strategy.win_rate === 'number' ? strategy.win_rate.toFixed(1) : strategy.win_rate}%</span>
                          </div>
                          <div className="w-full h-2 bg-slate-700 rounded-full overflow-hidden">
                            <div
                              className={`h-full rounded-full transition-all ${
                                strategy.win_rate >= 60 ? 'bg-emerald-500' : strategy.win_rate >= 50 ? 'bg-amber-500' : 'bg-rose-500'
                              }`}
                              style={{ width: `${Math.min(strategy.win_rate, 100)}%` }}
                            />
                          </div>
                        </div>
                      )}

                      {/* Entry & Exit Logic */}
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-3 mb-4">
                        <div className="bg-emerald-500/10 border border-emerald-500/30 rounded-lg p-3">
                          <h4 className="text-xs font-bold text-emerald-400 uppercase tracking-wider mb-2 flex items-center gap-1">
                            Entry Logic
                          </h4>
                          <p className="text-sm text-slate-300 whitespace-pre-wrap">{strategy.entry_logic || strategy.signal_logic || 'See strategy description'}</p>
                        </div>

                        <div className="bg-rose-500/10 border border-rose-500/30 rounded-lg p-3">
                          <h4 className="text-xs font-bold text-rose-400 uppercase tracking-wider mb-2 flex items-center gap-1">
                            Exit Logic
                          </h4>
                          <p className="text-sm text-slate-300 whitespace-pre-wrap">{strategy.exit_logic || 'Take profit or stop loss hit'}</p>
                        </div>
                      </div>

                      {/* Universe */}
                      <div className="mb-4">
                        <h4 className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">
                          Asset Universe ({strategy.assetCount})
                        </h4>
                        <div className="flex flex-wrap gap-1">
                          {strategy.universe?.slice(0, 20).map(t => (
                            <span key={t} className="text-[10px] px-2 py-1 rounded bg-slate-800 text-slate-300">{t}</span>
                          ))}
                          {strategy.universe?.length > 20 && (
                            <span className="text-[10px] px-2 py-1 rounded bg-slate-800 text-slate-500">
                              +{strategy.universe.length - 20} more
                            </span>
                          )}
                        </div>
                      </div>

                      {/* Approve / Reject Actions */}
                      {strategy.status === 'TESTING' && (
                        <div className="flex items-center gap-3 pt-3 border-t border-white/5">
                          <button
                            onClick={async () => {
                              try {
                                const res = await fetch(`/api/strategies/${encodeURIComponent(strategy.id)}/approve`, { method: 'POST' });
                                if (res.ok) {
                                  fetchStrategies();
                                  fetchPipelineSummary();
                                }
                              } catch (e) { console.error('Approve failed:', e); }
                            }}
                            className="flex-1 py-2 px-4 bg-emerald-500/20 hover:bg-emerald-500/30 text-emerald-400 text-sm font-bold rounded-lg border border-emerald-500/30 transition-all"
                          >
                            Approve for Deployment
                          </button>
                          <button
                            onClick={async () => {
                              if (!confirm('Reject this strategy? It will be marked as DEPRECATED.')) return;
                              try {
                                const res = await fetch(`/api/strategies/${encodeURIComponent(strategy.id)}/reject`, { method: 'POST' });
                                if (res.ok) {
                                  fetchStrategies();
                                  fetchPipelineSummary();
                                }
                              } catch (e) { console.error('Reject failed:', e); }
                            }}
                            className="py-2 px-4 bg-rose-500/10 hover:bg-rose-500/20 text-rose-400 text-sm font-bold rounded-lg border border-rose-500/20 transition-all"
                          >
                            Reject
                          </button>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </>
      )}
    </div>
  );
};

export default GoldenStrategies;
