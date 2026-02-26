import React, { useState, useEffect, useRef } from 'react';

// Clean Compact Performance Tab
export const StrategyPerformance = () => {
  const [deploymentStats, setDeploymentStats] = useState(null);
  const [timeRange, setTimeRange] = useState('7d');
  const [loading, setLoading] = useState(true);
  const abortControllerRef = useRef(null);

  useEffect(() => {
    fetchData(true);
    
    let interval = null;
    const startInterval = () => {
      interval = setInterval(() => {
        if (document.visibilityState === 'visible') {
          fetchData(false);
        }
      }, 120000); // 2 minutes
    };
    startInterval();
    
    const handleVisibilityChange = () => {
      if (document.visibilityState === 'visible') {
        fetchData(false);
      }
    };
    document.addEventListener('visibilitychange', handleVisibilityChange);
    
    return () => {
      clearInterval(interval);
      document.removeEventListener('visibilitychange', handleVisibilityChange);
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, [timeRange]);

  const fetchData = async (showLoading = false) => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    abortControllerRef.current = new AbortController();
    const { signal } = abortControllerRef.current;
    
    try {
      if (showLoading) setLoading(true);
      const res = await fetch(`/api/performance/deployment-stats?range=${timeRange}`, { signal });
      if (res.ok) setDeploymentStats(await res.json());
    } catch (e) {
      if (e.name !== 'AbortError') {
        console.error('Failed:', e);
      }
    } finally {
      if (showLoading) setLoading(false);
    }
  };

  const format$ = (v) => '$' + (v || 0).toLocaleString('en-US', {maximumFractionDigits: 0});
  const formatPct = (v) => (v || 0).toFixed(1) + '%';

  const metrics = deploymentStats ? {
    real: deploymentStats.real_pnl || 0,
    potential: deploymentStats.potential_pnl || 0,
    missed: (deploymentStats.potential_pnl || 0) - (deploymentStats.real_pnl || 0),
    capture: deploymentStats.potential_pnl > 0 ? (deploymentStats.real_pnl / deploymentStats.potential_pnl) * 100 : 0,
    strategies: deploymentStats.strategies_deployed || 0,
    winRate: deploymentStats.aggregated_win_rate || 0
  } : null;

  if (loading) return <div className="p-8 text-center text-xs text-slate-500">Loading...</div>;

  return (
    <div className="p-4 space-y-4">
      {/* Header + Filter */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="text-xl">📊</span>
          <h1 className="text-lg font-bold text-white">Performance</h1>
        </div>
        
        <div className="flex bg-slate-800 rounded-lg p-1">
          {['7d', '30d', '90d', 'ytd'].map(k => (
            <button
              key={k}
              onClick={() => setTimeRange(k)}
              className={`px-3 py-1.5 rounded-md text-xs font-medium transition-colors ${
                timeRange === k ? 'bg-blue-500 text-white' : 'text-slate-400 hover:text-white'
              }`}
            >
              {k.toUpperCase()}
            </button>
          ))}
        </div>
      </div>

      {/* Summary Cards - Grid Layout */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <div className="bg-slate-900/50 border border-white/10 rounded-xl p-4">
          <div className="text-xs text-slate-500 mb-1">Strategies</div>
          <div className="text-2xl font-bold text-white">{metrics?.strategies || 0}</div>
        </div>
        
        <div className="bg-emerald-500/5 border border-emerald-500/20 rounded-xl p-4">
          <div className="text-xs text-emerald-400 mb-1">Win Rate</div>
          <div className="text-2xl font-bold text-emerald-400">{formatPct(metrics?.winRate)}</div>
        </div>
        
        <div className="bg-blue-500/5 border border-blue-500/20 rounded-xl p-4">
          <div className="text-xs text-blue-400 mb-1">P&L Capture</div>
          <div className={`text-2xl font-bold ${(metrics?.capture || 0) >= 50 ? 'text-emerald-400' : 'text-amber-400'}`}>
            {formatPct(metrics?.capture)}
          </div>
        </div>
        
        <div className="bg-slate-900/50 border border-white/10 rounded-xl p-4">
          <div className="text-xs text-slate-500 mb-1">Total P&L</div>
          <div className={`text-2xl font-bold ${(metrics?.real || 0) >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
            {format$(metrics?.real)}
          </div>
        </div>
      </div>

      {/* P&L Breakdown */}
      <div className="grid grid-cols-3 gap-3">
        <div className="bg-emerald-500/10 border border-emerald-500/30 rounded-xl p-4">
          <div className="flex items-center gap-2 mb-2">
            <span className="text-lg">💚</span>
            <span className="text-sm font-bold text-emerald-400">Realized</span>
          </div>
          <div className="text-3xl font-black text-white">{format$(metrics?.real)}</div>
          <div className="text-xs text-emerald-400/60 mt-1">From executed trades</div>
        </div>
        
        <div className="bg-blue-500/10 border border-blue-500/30 rounded-xl p-4">
          <div className="flex items-center gap-2 mb-2">
            <span className="text-lg">💙</span>
            <span className="text-sm font-bold text-blue-400">Potential</span>
          </div>
          <div className="text-3xl font-black text-white">{format$(metrics?.potential)}</div>
          <div className="text-xs text-blue-400/60 mt-1">If all signals traded</div>
        </div>
        
        <div className="bg-amber-500/10 border border-amber-500/30 rounded-xl p-4">
          <div className="flex items-center gap-2 mb-2">
            <span className="text-lg">⚠️</span>
            <span className="text-sm font-bold text-amber-400">Missed</span>
          </div>
          <div className="text-3xl font-black text-amber-400">{format$(metrics?.missed)}</div>
          <div className="text-xs text-amber-400/60 mt-1">Opportunity cost</div>
        </div>
      </div>

      {/* Progress Bar */}
      <div className="bg-slate-900/50 border border-white/10 rounded-xl p-4">
        <div className="flex justify-between text-sm mb-2">
          <span className="text-white font-medium">Signal Capture Rate</span>
          <span className={`font-bold ${(metrics?.capture || 0) >= 50 ? 'text-emerald-400' : 'text-amber-400'}`}>
            {formatPct(metrics?.capture)}
          </span>
        </div>
        <div className="h-3 bg-slate-800 rounded-full overflow-hidden">
          <div 
            className="h-full bg-gradient-to-r from-emerald-500 to-emerald-400 transition-all duration-500"
            style={{ width: `${Math.min(metrics?.capture || 0, 100)}%` }}
          />
        </div>
        <div className="flex justify-between text-xs text-slate-500 mt-2">
          <span>Realized: {format$(metrics?.real)}</span>
          <span>Missed: {format$(metrics?.missed)}</span>
        </div>
      </div>

      {/* Strategy Breakdown Table */}
      <div className="bg-slate-900/50 border border-white/10 rounded-xl overflow-hidden">
        <div className="px-4 py-3 border-b border-white/10 bg-slate-800/50">
          <span className="text-sm font-bold text-white">Strategy Breakdown</span>
        </div>
        
        <div className="divide-y divide-white/5">
          {deploymentStats?.strategy_breakdown?.map((s) => {
            const capture = s.potential_pnl > 0 ? ((s.real_pnl || 0) / s.potential_pnl) * 100 : 0;
            return (
              <div key={s.id} className="px-4 py-3 flex items-center justify-between hover:bg-white/5">
                <div className="flex items-center gap-3">
                  <span className="text-lg">{s.win_rate >= 80 ? '🥇' : '🥈'}</span>
                  <div>
                    <div className="text-sm font-medium text-white">{s.name}</div>
                    <div className="text-xs text-slate-500">{s.signals_executed || 0}/{s.signals_generated || 0} signals captured</div>
                  </div>
                </div>
                
                <div className="flex items-center gap-6">
                  <div className="text-right">
                    <div className="text-sm font-bold text-emerald-400">{formatPct(s.win_rate)}</div>
                    <div className="text-xs text-slate-500">Win Rate</div>
                  </div>
                  
                  <div className="text-right w-20">
                    <div className={`text-sm font-bold ${(s.real_pnl || 0) >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                      {format$(s.real_pnl)}
                    </div>
                    <div className="text-xs text-slate-500">Real P&L</div>
                  </div>
                  
                  <div className="w-16">
                    <div className="text-xs font-bold text-right mb-1">{formatPct(capture)}</div>
                    <div className="h-1.5 bg-slate-800 rounded-full overflow-hidden">
                      <div className="h-full bg-emerald-500" style={{ width: `${capture}%` }} />
                    </div>
                  </div>
                </div>
              </div>
            );
          }) || (
            <div className="p-8 text-center text-slate-500 text-sm">No strategy data available</div>
          )}
        </div>
      </div>
    </div>
  );
};
