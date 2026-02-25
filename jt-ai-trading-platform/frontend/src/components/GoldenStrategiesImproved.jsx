import React, { useState, useEffect } from 'react';

// ============================================================================
// GOLDEN STRATEGIES COMPACT V3 - JT Tech Pack G001-G015
// 2 per row layout, smaller fonts, compact design
// ============================================================================

const SignalGauge = ({ score, size = 'sm' }) => {
  let color = 'bg-slate-600';
  let emoji = '○';
  
  if (score >= 80) { color = 'bg-emerald-500'; emoji = '●'; }
  else if (score >= 50) { color = 'bg-amber-500'; emoji = '◐'; }
  else if (score > 0) { color = 'bg-rose-500'; emoji = '○'; }
  
  const width = size === 'xs' ? 'w-10' : 'w-12';
  
  return (
    <div className="flex items-center gap-1">
      <div className={`${width} h-1.5 bg-slate-700 rounded-full overflow-hidden`}>
        <div className={`h-full ${color}`} style={{ width: `${Math.min(score, 100)}%` }} />
      </div>
      <span className="text-[10px] font-bold text-slate-400">{score}</span>
    </div>
  );
};

const YearlyWinRate = ({ yearlyData }) => {
  if (!yearlyData || Object.keys(yearlyData).length === 0) return null;
  const years = Object.entries(yearlyData).sort((a, b) => b[0] - a[0]).slice(0, 3);
  
  return (
    <div className="flex items-center gap-1">
      {years.map(([year, rate]) => (
        <span key={year} className={`text-[9px] ${rate >= 50 ? 'text-emerald-400' : 'text-rose-400'}`}>
          {year}:{rate}%
        </span>
      ))}
    </div>
  );
};

const formatSignal = (signalText) => {
  if (!signalText) return 'Not specified';
  let text = signalText.replace(/^BUY:\s*/i, '').replace(/^SELL:\s*/i, '');
  const parts = text.split(/\s*(?:\d\.\s+|OR|at\s+FIRST\s+of:?)\s*/i).filter(p => p.trim());
  if (parts.length <= 1) return <span className="text-[10px] text-slate-400">{text.substring(0, 80)}</span>;
  return parts.slice(0, 2).map((part, i) => (
    <div key={i} className="text-[10px] text-slate-400 leading-tight">{i + 1}. {part.trim().substring(0, 40)}</div>
  ));
};

const extractExitKPIs = (exitLogic) => {
  if (!exitLogic) return { profit: null, loss: null, days: null };
  const profitMatch = exitLogic.match(/≥\+?(\d+%)/);
  const lossMatch = exitLogic.match(/≤-?(\d+%)/);
  const daysMatch = exitLogic.match(/≥?(\d+)\s+days?/i);
  return {
    profit: profitMatch ? profitMatch[1] : null,
    loss: lossMatch ? lossMatch[1] : null,
    days: daysMatch ? daysMatch[1] : null
  };
};

// Compact Strategy Card
const CompactStrategyCard = ({ strategy, signalData, onDeploy, isDeployed, isSelected, onSelect }) => {
  const topSignals = signalData?.signals || [];
  const triggeredCount = signalData?.triggered_count ?? 0;
  const watchingCount = signalData?.watching_count ?? 0;
  const universeCount = signalData?.universe_count || strategy.universe_count || 0;
  
  const closestTo100 = topSignals
    .filter(s => !s.triggered && s.signal_score > 0)
    .sort((a, b) => b.signal_score - a.signal_score)
    .slice(0, 3);
  
  const triggeredSignals = topSignals.filter(s => s.triggered);
  
  if (isDeployed) {
    return (
      <div className="bg-slate-900/80 border border-emerald-500/30 rounded-lg overflow-hidden">
        {/* Header */}
        <div className="p-2 border-b border-white/5 bg-emerald-500/5">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="text-sm">{strategy.win_rate >= 80 ? '🥇' : '🥈'}</span>
              <div>
                <h3 className="text-xs font-bold text-white truncate max-w-[140px]">{strategy.name}</h3>
                <div className="flex items-center gap-2">
                  <span className="text-[9px] text-emerald-400">● {universeCount} tickers</span>
                  <YearlyWinRate yearlyData={strategy.yearly_win_rates} />
                </div>
              </div>
            </div>
            <div className="text-right">
              <div className="text-sm font-bold text-emerald-400">{strategy.win_rate}%</div>
              <div className="text-[9px] text-slate-500">{strategy.actual_win_rate > 0 ? 'Live' : 'Backtest'}</div>
            </div>
          </div>
        </div>
        
        {/* Stats Row */}
        <div className="px-2 py-1.5 border-b border-white/5 flex justify-between text-[10px]">
          <span className="text-emerald-400">🎯 {triggeredCount} Triggered</span>
          <span className="text-amber-400">👀 {watchingCount} Watching</span>
        </div>
        
        {/* BUY Signal Logic */}
        <div className="px-2 py-1.5 border-b border-white/5 bg-emerald-500/5">
          <div className="text-[9px] text-emerald-400 font-bold mb-1">🟢 BUY SIGNAL</div>
          <div className="text-[10px] text-slate-300">{strategy.signal_logic || 'RSI < 25'}</div>
        </div>
        
        {/* SELL Signal Logic */}
        <div className="px-2 py-1.5 border-b border-white/5 bg-rose-500/5">
          <div className="text-[9px] text-rose-400 font-bold mb-1">🔴 SELL SIGNAL</div>
          <div className="text-[10px] text-slate-300">{strategy.exit_logic || 'Time-based exit'}</div>
        </div>
        
        {/* Triggered Signals */}
        {triggeredSignals.length > 0 && (
          <div className="px-2 py-1 border-b border-white/5 bg-emerald-500/10">
            <div className="text-[9px] text-emerald-400 font-bold mb-1">💥 TRIGGERED NOW</div>
            {triggeredSignals.map((sig, i) => (
              <div key={i} className="flex items-center justify-between py-0.5">
                <span className="text-[10px] text-emerald-400 font-medium">🎯 {sig.ticker}</span>
                <span className="text-[10px] text-slate-400">${sig.current_price?.toFixed(2)}</span>
              </div>
            ))}
          </div>
        )}
        
        {/* Top 3 Closest to Trigger */}
        {closestTo100.length > 0 && (
          <div className="px-2 py-1 border-b border-white/5">
            <div className="text-[9px] text-amber-400 font-bold mb-1">📊 TOP 3 CLOSEST TO SIGNAL</div>
            {closestTo100.map((sig, i) => (
              <div key={i} className="flex items-center justify-between py-0.5">
                <span className="text-[10px] text-slate-400">#{i+1} {sig.ticker}</span>
                <div className="flex items-center gap-2">
                  <span className="text-[10px] text-slate-500">${sig.current_price?.toFixed(2)}</span>
                  <SignalGauge score={sig.signal_score} size="xs" />
                </div>
              </div>
            ))}
          </div>
        )}
        
        {/* Exit KPIs */}
        <div className="px-2 py-1.5 flex gap-2 text-[9px]">
          {exitKPIs.profit && <span className="text-emerald-400">TP:+{exitKPIs.profit}</span>}
          {exitKPIs.loss && <span className="text-rose-400">SL:-{exitKPIs.loss}</span>}
          {exitKPIs.days && <span className="text-slate-400">{exitKPIs.days}d</span>}
        </div>
      </div>
    );
  }
  
  // Not deployed
  return (
    <div className="bg-slate-900/50 border border-white/10 rounded-lg overflow-hidden hover:border-blue-500/30 transition-all">
      <div className="p-2 border-b border-white/5">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <input 
              type="checkbox" 
              checked={isSelected}
              onChange={() => onSelect(strategy.id)}
              className="w-4 h-4 rounded border-slate-600 bg-slate-800"
            />
            <span className="text-sm">{strategy.win_rate >= 80 ? '🥇' : '🥈'}</span>
            <div>
              <h3 className="text-xs font-bold text-white truncate max-w-[120px]">{strategy.name}</h3>
              <span className="text-[9px] text-slate-500">{universeCount} tickers</span>
            </div>
          </div>
          <div className="text-right">
            <div className="text-sm font-bold text-emerald-400">{strategy.win_rate}%</div>
            <div className="text-[9px] text-slate-500">Win Rate</div>
          </div>
        </div>
      </div>
      
      {closestTo100.length > 0 && (
        <div className="px-2 py-1 border-b border-white/5">
          <div className="text-[9px] text-slate-500 mb-1">Closest to trigger:</div>
          {closestTo100.map((sig, i) => (
            <div key={i} className="flex items-center justify-between py-0.5">
              <span className="text-[10px] text-slate-400">{sig.ticker}</span>
              <SignalGauge score={sig.signal_score} size="xs" />
            </div>
          ))}
        </div>
      )}
      
      <div className="px-2 py-1.5">
        <button
          onClick={() => onDeploy(strategy.id)}
          className="w-full py-1.5 bg-blue-500/20 hover:bg-blue-500/30 border border-blue-500/30 rounded text-[10px] font-medium text-blue-400 transition-colors"
        >
          Deploy
        </button>
      </div>
    </div>
  );
};

// Main Component
export const GoldenStrategiesImproved = () => {
  const [strategies, setStrategies] = useState([]);
  const [signals, setSignals] = useState({});
  const [loading, setLoading] = useState(true);
  const [selectedStrategies, setSelectedStrategies] = useState(new Set());
  const [activeTab, setActiveTab] = useState('active'); // 'active' | 'available'
  const [searchTerm, setSearchTerm] = useState('');

  useEffect(() => {
    fetchStrategies(true); // Initial load with spinner
    const interval = setInterval(() => fetchStrategies(false), 300000); // 5 minutes
    return () => clearInterval(interval);
  }, []);

  const fetchStrategies = async (showLoading = false) => {
    try {
      if (showLoading) setLoading(true);
      const res = await fetch('/api/strategies/researcher');
      if (res.ok) {
        const data = await res.json();
        setStrategies(data.strategies || []);
        
        // Fetch signals for each deployed strategy
        const deployed = data.strategies?.filter(s => s.is_deployed) || [];
        const signalData = {};
        
        await Promise.all(
          deployed.map(async (s) => {
            try {
              const res = await fetch(`/api/strategies/${s.id}/top-signals?limit=5`);
              if (res.ok) {
                signalData[s.id] = await res.json();
              }
            } catch (e) {}
          })
        );
        
        setSignals(signalData);
      }
    } catch (e) {
      console.error('Failed to fetch strategies:', e);
    } finally {
      if (showLoading) setLoading(false);
    }
  };

  const handleDeploy = async (strategyId) => {
    try {
      const res = await fetch('/api/strategies/deploy-monitoring', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ strategy_id: strategyId, mode: 'MONITORING', capital_per_trade: 25000, max_positions: 4 })
      });
      
      if (res.ok) {
        fetchStrategies(true); // Initial load with spinner
      }
    } catch (e) {
      console.error('Deploy failed:', e);
    }
  };

  const handleBatchDeploy = async () => {
    const promises = Array.from(selectedStrategies).map(id => handleDeploy(id));
    await Promise.all(promises);
    setSelectedStrategies(new Set());
  };

  const toggleSelection = (id) => {
    const newSet = new Set(selectedStrategies);
    if (newSet.has(id)) newSet.delete(id);
    else newSet.add(id);
    setSelectedStrategies(newSet);
  };

  const filteredStrategies = strategies.filter(s => {
    const matchesSearch = s.name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         s.id?.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesTab = activeTab === 'active' ? s.is_deployed : !s.is_deployed;
    return matchesSearch && matchesTab;
  });

  const activeCount = strategies.filter(s => s.is_deployed).length;
  const availableCount = strategies.filter(s => !s.is_deployed).length;

  if (loading) {
    return (
      <div className="p-8 text-center text-slate-500">
        <div className="w-6 h-6 border-2 border-slate-600 border-t-blue-500 rounded-full animate-spin mx-auto mb-2" />
        <span className="text-sm">Loading strategies...</span>
      </div>
    );
  }

  return (
    <div className="p-3 space-y-3">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="text-xl">🎯</span>
          <div>
            <h2 className="text-base font-bold text-white">Golden Strategies</h2>
            <p className="text-[10px] text-slate-500">JT Tech Pack G001-G015</p>
          </div>
        </div>
        <div className="flex gap-1 text-[10px]">
          <button
            onClick={() => setActiveTab('active')}
            className={`px-3 py-1.5 rounded ${activeTab === 'active' ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30' : 'text-slate-400 hover:text-white'}`}
          >
            Active ({activeCount})
          </button>
          <button
            onClick={() => setActiveTab('available')}
            className={`px-3 py-1.5 rounded ${activeTab === 'available' ? 'bg-blue-500/20 text-blue-400 border border-blue-500/30' : 'text-slate-400 hover:text-white'}`}
          >
            Available ({availableCount})
          </button>
        </div>
      </div>

      {/* Search */}
      <div className="relative">
        <input
          type="text"
          placeholder="Search strategies..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="w-full bg-slate-900/50 border border-white/10 rounded-lg px-3 py-2 text-xs text-white placeholder-slate-600 focus:border-blue-500/50 focus:outline-none"
        />
      </div>

      {/* Batch Deploy Button */}
      {activeTab === 'available' && selectedStrategies.size > 0 && (
        <div className="flex justify-end">
          <button
            onClick={handleBatchDeploy}
            className="px-4 py-2 bg-blue-500 hover:bg-blue-600 rounded-lg text-xs font-medium text-white transition-colors"
          >
            Deploy Selected ({selectedStrategies.size})
          </button>
        </div>
      )}

      {/* Strategies Grid - 2 per row */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        {filteredStrategies.map(strategy => (
          <CompactStrategyCard
            key={strategy.id}
            strategy={strategy}
            signalData={signals[strategy.id]}
            onDeploy={handleDeploy}
            isDeployed={strategy.is_deployed}
            isSelected={selectedStrategies.has(strategy.id)}
            onSelect={toggleSelection}
          />
        ))}
      </div>

      {filteredStrategies.length === 0 && (
        <div className="text-center py-8 text-slate-500 text-sm">
          {activeTab === 'active' ? 'No active strategies. Deploy some first.' : 'All strategies deployed!'}
        </div>
      )}
    </div>
  );
};
