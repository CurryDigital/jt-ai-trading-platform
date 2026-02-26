import React, { useState, useEffect, useRef } from 'react';

// Compact Dashboard
export const DashboardTab = () => {
  const [inventoryData, setInventoryData] = useState(null);
  const [marketOverview, setMarketOverview] = useState(null);
  const [strategies, setStrategies] = useState([]);
  const [signals, setSignals] = useState([]);
  const [loading, setLoading] = useState(true);
  const [timePeriod, setTimePeriod] = useState('daily');
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
  }, [timePeriod]);

  const fetchData = async (showLoading = false) => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    abortControllerRef.current = new AbortController();
    const { signal } = abortControllerRef.current;
    
    try {
      if (showLoading) setLoading(true);
      
      // Fetch data in parallel with short timeouts - use FAST endpoints
      const [inventoryRes, marketRes, stratRes, signalsRes] = await Promise.all([
        fetch('/api/inventory/evaluate', { signal }).then(r => r.ok ? r.json() : null).catch(() => null),
        fetch('/api/market/indices', { signal }).then(r => r.ok ? r.json() : null).catch(() => null),
        fetch('/api/strategies/researcher', { signal }).then(r => r.ok ? r.json() : null).catch(() => null),
        fetch('/api/signals/1', { signal }).then(r => r.ok ? r.json() : null).catch(() => null)
      ]);
      
      if (inventoryRes) setInventoryData(inventoryRes);
      if (marketRes) setMarketOverview(marketRes);
      if (stratRes) setStrategies(stratRes.strategies || []);
      if (signalsRes) setSignals(signalsRes.signals?.slice(0, 3) || []);
      
    } catch (e) {
      if (e.name !== 'AbortError') {
        console.error('Dashboard fetch error:', e);
      }
    } finally {
      if (showLoading) setLoading(false);
    }
  };

  const formatCurrency = (val) => {
    if (!val && val !== 0) return '$0';
    return '$' + val.toLocaleString('en-US', {maximumFractionDigits: 0});
  };

  const getMarketStatus = (market) => {
    const hour = new Date().getHours();
    const hours = { US: { open: 21, close: 4 }, HK: { open: 9, close: 16 }, CN: { open: 9, close: 15 }, SG: { open: 9, close: 17 } };
    const m = hours[market];
    if (!m) return { open: false };
    const isOpen = m.close < m.open ? (hour >= m.open || hour < m.close) : (hour >= m.open && hour < m.close);
    return { open: isOpen };
  };

  const getGainersByMarket = () => {
    if (!inventoryData?.positions) return {};
    const byMarket = { US: [], HK: [], CN: [], SG: [] };
    inventoryData.positions.forEach(pos => {
      let m = 'US';
      if (pos.ticker?.endsWith('.HK')) m = 'HK';
      else if (pos.ticker?.endsWith('.SS') || pos.ticker?.endsWith('.SZ')) m = 'CN';
      else if (pos.ticker?.endsWith('.SI')) m = 'SG';
      // Use inventory data directly (already has P&L calculated)
      byMarket[m].push({ 
        symbol: pos.ticker, 
        pnl: pos.pnl || 0,
        market_value: pos.market_value || 0
      });
    });
    Object.keys(byMarket).forEach(m => {
      byMarket[m] = byMarket[m].sort((a, b) => b.pnl - a.pnl).slice(0, 2);
    });
    return byMarket;
  };

  const gainersByMarket = getGainersByMarket();

  if (loading) {
    return (
      <div className="p-8 text-center text-slate-500">
        <div className="w-6 h-6 border-2 border-slate-600 border-t-blue-500 rounded-full animate-spin mx-auto mb-2" />
        <span className="text-xs">Loading...</span>
      </div>
    );
  }

  return (
    <div className="p-3 space-y-3">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="text-lg">📊</span>
          <div>
            <h2 className="text-sm font-bold text-white">Dashboard</h2>
            <p className="text-[10px] text-slate-500">Overview</p>
          </div>
        </div>
        
        <div className="flex gap-0.5">
          {['daily', 'weekly', 'monthly'].map((k) => (
            <button
              key={k}
              onClick={() => setTimePeriod(k)}
              className={`px-2 py-1 rounded text-[10px] font-bold capitalize ${
                timePeriod === k ? 'bg-blue-500 text-white' : 'text-slate-400 hover:bg-white/5'
              }`}
            >
              {k}
            </button>
          ))}
        </div>
      </div>

      {/* Indices */}
      <div className="grid grid-cols-4 gap-2">
        {[
          { s: '^HSI', n: 'HSI', f: '🇭🇰', m: 'HK' },
          { s: '^DJI', n: 'Dow', f: '🇺🇸', m: 'US' },
          { s: '^GSPC', n: 'S&P', f: '🇺🇸', m: 'US' },
          { s: '^STI', n: 'STI', f: '🇸🇬', m: 'SG' },
        ].map(idx => {
          const d = marketOverview?.indices?.find(i => i.symbol === idx.s);
          const chg = d?.change_pct || 0;
          return (
            <div key={idx.s} className="bg-slate-900/50 border border-white/10 rounded-lg p-2">
              <div className="flex items-center justify-between">
                <span className="text-xs">{idx.f}</span>
                <span className={`w-1.5 h-1.5 rounded-full ${getMarketStatus(idx.m).open ? 'bg-emerald-500' : 'bg-rose-500'}`} />
              </div>
              <div className="text-sm font-bold text-white">{d?.price?.toFixed(0) || '---'}</div>
              <div className={`text-[10px] ${chg >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                {chg >= 0 ? '+' : ''}{chg.toFixed(1)}%
              </div>
            </div>
          );
        })}
      </div>

      {/* Portfolio Summary */}
      <div className="grid grid-cols-4 gap-2">
        <div className="bg-blue-500/5 border border-blue-500/20 rounded-lg p-2">
          <div className="text-[9px] text-blue-400">Total Value</div>
          <div className="text-sm font-bold text-white">{inventoryData ? formatCurrency(inventoryData.inventory_value) : <span className="text-slate-500">--</span>}</div>
        </div>
        <div className="bg-emerald-500/5 border border-emerald-500/20 rounded-lg p-2">
          <div className="text-[9px] text-emerald-400">Positions</div>
          <div className="text-sm font-bold text-emerald-400">{inventoryData ? inventoryData.active_positions : <span className="text-slate-500">--</span>}</div>
        </div>
        <div className={`${(inventoryData?.positions?.reduce((sum, p) => sum + (p.pnl || 0), 0) || 0) >= 0 ? 'bg-emerald-500/5 border-emerald-500/20' : 'bg-rose-500/5 border-rose-500/20'} border rounded-lg p-2`}>
          <div className={`text-[9px] ${(inventoryData?.positions?.reduce((sum, p) => sum + (p.pnl || 0), 0) || 0) >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>P&L</div>
          <div className={`text-sm font-bold ${(inventoryData?.positions?.reduce((sum, p) => sum + (p.pnl || 0), 0) || 0) >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
            {inventoryData ? formatCurrency(inventoryData.positions?.reduce((sum, p) => sum + (p.pnl || 0), 0) || 0) : <span className="text-slate-500">--</span>}
          </div>
        </div>
        <div className="bg-purple-500/5 border border-purple-500/20 rounded-lg p-2">
          <div className="text-[9px] text-purple-400">Strategies</div>
          <div className="text-sm font-bold text-white">{strategies.length}</div>
        </div>
      </div>
      
      {!inventoryData && (
        <div className="text-[10px] text-amber-400/60 text-center">
          ⚠️ No inventory data - portfolio information unavailable
        </div>
      )}

      {/* Top Gainers */}
      <div className="space-y-2">
        <div className="text-xs font-bold text-white">Top Gainers by Market</div>
        
        <div className="grid grid-cols-2 gap-2">
          {['US', 'HK', 'CN', 'SG'].map(m => {
            const gainers = gainersByMarket[m] || [];
            const flags = { US: '🇺🇸', HK: '🇭🇰', CN: '🇨🇳', SG: '🇸🇬' };
            return (
              <div key={m} className="bg-slate-900/30 border border-white/5 rounded-lg overflow-hidden">
                <div className="px-2 py-1 bg-slate-800/50 text-[10px] font-bold text-white">
                  {flags[m]} {m}
                </div>
                <div className="divide-y divide-white/5">
                  {gainers.length > 0 ? gainers.map((pos, i) => (
                    <div key={i} className="px-2 py-1 flex justify-between text-xs">
                      <span className="text-white">{pos.symbol}</span>
                      <span className={pos.pnl >= 0 ? 'text-emerald-400' : 'text-rose-400'}>
                        {pos.pnl >= 0 ? '+' : ''}{formatCurrency(pos.pnl)}
                      </span>
                    </div>
                  )) : (
                    <div className="px-2 py-2 text-center text-[10px] text-slate-500">No positions</div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Recent Signals */}
      {signals.length > 0 && (
        <div className="space-y-2">
          <div className="text-xs font-bold text-white">Recent Signals</div>
          <div className="space-y-1">
            {signals.map((sig, i) => (
              <div key={i} className="flex items-center justify-between px-2 py-1 bg-slate-900/30 rounded-lg">
                <div className="flex items-center gap-2">
                  <span className={`w-2 h-2 rounded-full ${sig.signal === 'BUY' ? 'bg-emerald-500' : 'bg-rose-500'}`} />
                  <span className="text-xs font-medium text-white">{sig.ticker}</span>
                </div>
                <span className="text-[10px] text-slate-400">{sig.strategy_name || sig.strategy_id}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
