import React, { useState, useEffect } from 'react';

// Clean Portfolio Tab with Tables
export const PortfolioTab = () => {
  const [positions, setPositions] = useState([]);
  const [dbPositions, setDbPositions] = useState([]);
  const [ibkrPortfolio, setIbkrPortfolio] = useState(null);
  const [strategies, setStrategies] = useState({});
  const [pendingOrders, setPendingOrders] = useState([]);
  const [executedOrders, setExecutedOrders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [closingPositions, setClosingPositions] = useState({});
  const [marketFilter, setMarketFilter] = useState('ALL');

  useEffect(() => {
    fetchData(true); // Initial load with spinner
    const interval = setInterval(() => fetchData(false), 120000); // 2 minutes, silent refresh
    return () => clearInterval(interval);
  }, []);

  const fetchData = async (showLoading = false) => {
    try {
      if (showLoading) setLoading(true);
      const [ibkrRes, posRes, stratRes, ordersRes] = await Promise.all([
        fetch('/api/ibkr/portfolio'),
        fetch('/api/portfolio/positions'),
        fetch('/api/strategies/researcher'),
        fetch('/api/ib/pending-orders')
      ]);
      
      if (ibkrRes.ok) {
        const data = await ibkrRes.json();
        setIbkrPortfolio(data);
        const stocks = data.positions?.filter(p => 
          p.secType === 'STK' || p.exchange !== 'IDEALPRO' || p.symbol?.includes('.')
        ) || [];
        setPositions(stocks);
      }
      
      if (posRes.ok) setDbPositions((await posRes.json()).positions || []);
      if (stratRes.ok) {
        const data = await stratRes.json();
        const map = {};
        data.strategies?.forEach(s => map[s.id] = s);
        setStrategies(map);
      }
      if (ordersRes.ok) {
        const data = await ordersRes.json();
        const allOrders = data.orders || [];
        // Split into pending and executed
        const pending = allOrders.filter(o => 
          ['PendingSubmit', 'PreSubmitted', 'Submitted', 'PendingCancel'].includes(o.status)
        );
        const executed = allOrders.filter(o => 
          o.status === 'Filled'
        );
        setPendingOrders(pending);
        setExecutedOrders(executed);
      }
      
      // Also fetch from consumption.pending_orders
      const consumptionOrdersRes = await fetch('/api/orders/pending');
      if (consumptionOrdersRes.ok) {
        const data = await consumptionOrdersRes.json();
        const allConsumptionOrders = data.orders || [];
        
        // Pending orders
        const consumptionPending = allConsumptionOrders
          .filter(o => ['Submitted', 'PreSubmitted', 'PendingSubmit'].includes(o.status))
          .map(o => ({
            ticker: o.ticker,
            symbol: o.ticker,
            action: o.action,
            quantity: o.quantity,
            total_quantity: o.quantity,
            price: o.avg_fill_price,
            status: o.status,
            display_status: o.display_status,
            strategy_name: o.strategy_name,
            submit_time: o.submit_time
          }));
        
        // Executed orders (filled today)
        const consumptionExecuted = allConsumptionOrders
          .filter(o => o.status === 'Filled')
          .map(o => ({
            ticker: o.ticker,
            symbol: o.ticker,
            action: o.action,
            quantity: o.filled || o.quantity,
            price: o.avg_fill_price,
            status: 'Filled',
            strategy_name: o.strategy_name,
            execution_time: o.execution_time
          }));
        
        // Merge pending
        setPendingOrders(prev => {
          const existing = new Set(prev.map(p => `${p.ticker}-${p.action}`));
          const newOrders = consumptionPending.filter(o => !existing.has(`${o.ticker}-${o.action}`));
          return [...prev, ...newOrders];
        });
        
        // Set executed
        setExecutedOrders(prev => {
          const existing = new Set(prev.map(p => `${p.ticker}-${p.action}`));
          const newOrders = consumptionExecuted.filter(o => !existing.has(`${o.ticker}-${o.action}`));
          return [...newOrders, ...prev].slice(0, 10); // Keep last 10
        });
      }
    } catch (e) {
      console.error('Fetch error:', e);
    } finally {
      if (showLoading) setLoading(false);
    }
  };

  const getMarket = (ticker) => {
    if (ticker?.endsWith('.HK')) return 'HK';
    if (ticker?.endsWith('.SS') || ticker?.endsWith('.SZ')) return 'CN';
    if (ticker?.endsWith('.SI')) return 'SG';
    return 'US';
  };

  const getStrategy = (sym) => {
    const p = dbPositions.find(x => x.ticker === sym);
    return p?.strategy_id ? { id: p.strategy_id, name: strategies[p.strategy_id]?.name } : null;
  };

  const handleClose = async (sym, qty) => {
    setClosingPositions(p => ({ ...p, [sym]: true }));
    try {
      await fetch('/api/ib/place-order', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ symbol: sym, action: qty > 0 ? 'SELL' : 'BUY', quantity: Math.abs(qty), order_type: 'MKT', strategy_id: 'manual' })
      });
      setTimeout(fetchData, 2000);
    } catch (e) {}
    setClosingPositions(p => ({ ...p, [sym]: false }));
  };

  const format$ = (v) => '$' + (v || 0).toLocaleString('en-US', {maximumFractionDigits: 0});
  
  const markets = [
    { key: 'ALL', label: 'All', flag: '🌍' },
    { key: 'US', label: 'US', flag: '🇺🇸' },
    { key: 'HK', label: 'HK', flag: '🇭🇰' },
    { key: 'CN', label: 'CN', flag: '🇨🇳' },
    { key: 'SG', label: 'SG', flag: '🇸🇬' }
  ];
  
  const filteredPositions = marketFilter === 'ALL' 
    ? positions 
    : positions.filter(p => getMarket(p.symbol) === marketFilter);
    
  const filteredPending = marketFilter === 'ALL'
    ? pendingOrders
    : pendingOrders.filter(o => getMarket(o.ticker || o.symbol) === marketFilter);

  // Use IBKR prices directly - no frontend calculations needed
  const totalValue = filteredPositions.reduce((sum, p) => {
    const price = p.marketPrice > 0 ? p.marketPrice : p.avgCost;
    return sum + (p.position * price);
  }, 0);
  
  const pendingValue = filteredPending.reduce((sum, o) => {
    return sum + ((o.quantity || o.total_quantity || 0) * (o.price || 0));
  }, 0);
  
  const totalPnl = filteredPositions.reduce((sum, p) => {
    const price = p.marketPrice > 0 ? p.marketPrice : p.avgCost;
    return sum + ((price - p.avgCost) * p.position);
  }, 0);

  if (loading) return <div className="p-8 text-center text-xs text-slate-500">Loading...</div>;

  return (
    <div className="p-4 space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="text-xl">👑</span>
          <div>
            <h1 className="text-lg font-bold text-white">Portfolio</h1>
            <p className="text-xs text-slate-500">{ibkrPortfolio?.account}</p>
          </div>
        </div>
        
        <div className="text-right">
          <div className="text-2xl font-bold text-white">{format$(ibkrPortfolio?.total_value)}</div>
          <div className={`text-sm font-medium ${(ibkrPortfolio?.unrealized_pnl || 0) >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
            {(ibkrPortfolio?.unrealized_pnl || 0) >= 0 ? '+' : ''}{format$(ibkrPortfolio?.unrealized_pnl)} unrealized
          </div>
        </div>
      </div>

      {/* Market Filter */}
      <div className="flex bg-slate-800 rounded-xl p-1">
        {markets.map(m => (
          <button
            key={m.key}
            onClick={() => setMarketFilter(m.key)}
            className={`flex-1 flex items-center justify-center gap-1.5 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
              marketFilter === m.key ? 'bg-blue-500 text-white' : 'text-slate-400 hover:text-white'
            }`}
          >
            <span>{m.flag}</span>
            <span>{m.label}</span>
          </button>
        ))}
      </div>

      {/* Filtered Summary */}
      {(marketFilter !== 'ALL' || filteredPositions.length > 0 || filteredPending.length > 0) && (
        <div className="grid grid-cols-4 gap-3">
          <div className="bg-slate-900/50 border border-white/10 rounded-xl p-3">
            <div className="text-xs text-slate-500">Positions</div>
            <div className="text-xl font-bold text-white">{filteredPositions.length}</div>
          </div>
          <div className="bg-amber-500/5 border border-amber-500/20 rounded-xl p-3">
            <div className="text-xs text-amber-400">Pending</div>
            <div className="text-xl font-bold text-amber-400">{filteredPending.length}</div>
            <div className="text-[10px] text-amber-400/60">{format$(pendingValue)}</div>
          </div>
          <div className="bg-slate-900/50 border border-white/10 rounded-xl p-3">
            <div className="text-xs text-slate-500">Value</div>
            <div className="text-xl font-bold text-white">{format$(totalValue)}</div>
          </div>
          <div className={`${totalPnl >= 0 ? 'bg-emerald-500/5 border-emerald-500/20' : 'bg-rose-500/5 border-rose-500/20'} border rounded-xl p-3`}>
            <div className={`text-xs ${totalPnl >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>P&L</div>
            <div className={`text-xl font-bold ${totalPnl >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
              {totalPnl >= 0 ? '+' : ''}{format$(totalPnl)}
            </div>
          </div>
        </div>
      )}

      {/* Pending Orders */}
      {filteredPending.length > 0 && (
        <div className="bg-amber-500/5 border border-amber-500/30 rounded-xl overflow-hidden">
          <div className="px-4 py-3 bg-amber-500/10 border-b border-amber-500/20 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="text-lg">⏳</span>
              <span className="text-sm font-bold text-amber-400">Pending Orders ({filteredPending.length})</span>
            </div>
            <span className="text-xs text-amber-400/60">Awaiting execution</span>
          </div>
          
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-slate-900/30 text-xs text-slate-500">
                <tr>
                  <th className="text-left px-4 py-2">Symbol</th>
                  <th className="text-center px-4 py-2">Action</th>
                  <th className="text-right px-4 py-2">Qty</th>
                  <th className="text-right px-4 py-2">Price</th>
                  <th className="text-right px-4 py-2">Est. Value</th>
                  <th className="text-center px-4 py-2">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5 text-sm">
                {filteredPending.map((o, i) => (
                  <tr key={i} className="hover:bg-white/5">
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-2">
                        <span className="font-medium text-white">{o.ticker || o.symbol}</span>
                        <span className="text-xs text-slate-500">
                          {getMarket(o.ticker || o.symbol) === 'US' && '🇺🇸'}
                          {getMarket(o.ticker || o.symbol) === 'HK' && '🇭🇰'}
                          {getMarket(o.ticker || o.symbol) === 'CN' && '🇨🇳'}
                          {getMarket(o.ticker || o.symbol) === 'SG' && '🇸🇬'}
                        </span>
                      </div>
                    </td>
                    <td className="px-4 py-3 text-center">
                      <span className={`px-2 py-1 rounded text-xs font-bold ${
                        o.action === 'BUY' ? 'bg-emerald-500/20 text-emerald-400' : 'bg-rose-500/20 text-rose-400'
                      }`}>
                        {o.action}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-right font-mono">{o.quantity || o.total_quantity}</td>
                    <td className="px-4 py-3 text-right font-mono text-slate-400">
                      {o.price ? `$${o.price.toFixed(2)}` : 'MKT'}
                    </td>
                    <td className="px-4 py-3 text-right font-mono text-amber-400">
                      {o.price ? `$${((o.quantity || o.total_quantity) * o.price).toLocaleString()}` : '--'}
                    </td>
                    <td className="px-4 py-3 text-center">
                      <span className="px-2 py-1 rounded bg-amber-500/20 text-amber-400 text-xs animate-pulse">
                        ⏳ Pending
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Recently Executed Orders */}
      {executedOrders.length > 0 && (
        <div className="bg-emerald-500/5 border border-emerald-500/30 rounded-xl overflow-hidden">
          <div className="px-4 py-3 bg-emerald-500/10 border-b border-emerald-500/20 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="text-lg">✅</span>
              <span className="text-sm font-bold text-emerald-400">Recently Executed ({executedOrders.length})</span>
            </div>
            <span className="text-xs text-emerald-400/60">Filled today - should appear in positions</span>
          </div>
          
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-slate-900/30 text-xs text-slate-500">
                <tr>
                  <th className="text-left px-4 py-2">Symbol</th>
                  <th className="text-center px-4 py-2">Action</th>
                  <th className="text-right px-4 py-2">Qty</th>
                  <th className="text-right px-4 py-2">Fill Price</th>
                  <th className="text-right px-4 py-2">Total Value</th>
                  <th className="text-center px-4 py-2">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5 text-sm">
                {executedOrders.map((o, i) => (
                  <tr key={i} className="hover:bg-white/5">
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-2">
                        <span className="font-medium text-white">{o.ticker || o.symbol}</span>
                        <span className="text-xs text-slate-500">
                          {getMarket(o.ticker || o.symbol) === 'US' && '🇺🇸'}
                          {getMarket(o.ticker || o.symbol) === 'HK' && '🇭🇰'}
                          {getMarket(o.ticker || o.symbol) === 'CN' && '🇨🇳'}
                          {getMarket(o.ticker || o.symbol) === 'SG' && '🇸🇬'}
                        </span>
                      </div>
                    </td>
                    <td className="px-4 py-3 text-center">
                      <span className={`px-2 py-1 rounded text-xs font-bold ${
                        o.action === 'BUY' ? 'bg-emerald-500/20 text-emerald-400' : 'bg-rose-500/20 text-rose-400'
                      }`}>
                        {o.action}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-right font-mono">{o.quantity || o.filled}</td>
                    <td className="px-4 py-3 text-right font-mono text-emerald-400">
                      {o.price ? `$${o.price.toFixed(2)}` : '--'}
                    </td>
                    <td className="px-4 py-3 text-right font-mono text-emerald-400">
                      {o.price ? `$${((o.quantity || o.filled) * o.price).toLocaleString()}` : '--'}
                    </td>
                    <td className="px-4 py-3 text-center">
                      <span className="px-2 py-1 rounded bg-emerald-500/20 text-emerald-400 text-xs">
                        ✅ Filled
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Positions Table */}
      {filteredPositions.length > 0 ? (
        <div className="bg-slate-900/50 border border-white/10 rounded-xl overflow-hidden">
          <div className="px-4 py-3 bg-slate-800/50 border-b border-white/10 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="text-lg">📈</span>
              <span className="text-sm font-bold text-white">Positions ({filteredPositions.length})</span>
            </div>
            
            <button
              onClick={() => filteredPositions.forEach(p => handleClose(p.symbol, p.position))}
              className="px-3 py-1.5 rounded-lg bg-rose-500/20 text-rose-400 text-xs font-medium hover:bg-rose-500/30"
            >
              Close All
            </button>
          </div>
          
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-slate-900/30 text-xs text-slate-500">
                <tr>
                  <th className="text-left px-4 py-2">Symbol</th>
                  <th className="text-center px-4 py-2">Strategy</th>
                  <th className="text-right px-4 py-2">Position</th>
                  <th className="text-right px-4 py-2">Avg Cost</th>
                  <th className="text-right px-4 py-2">Market</th>
                  <th className="text-right px-4 py-2">Value</th>
                  <th className="text-right px-4 py-2">P&L</th>
                  <th className="text-center px-4 py-2">Close</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5 text-sm">
                {filteredPositions.map(p => {
                  // Use IBKR price directly from position data
                  const price = p.marketPrice > 0 ? p.marketPrice : p.avgCost;
                  const isEstimated = p.marketPrice <= 0;
                  
                  const value = p.position * price;
                  const pnl = (price - p.avgCost) * p.position;
                  const pnlPct = p.avgCost ? ((price - p.avgCost) / p.avgCost) * 100 : 0;
                  const strat = getStrategy(p.symbol);
                  const isClosing = closingPositions[p.symbol];
                  
                  return (
                    <tr key={p.symbol} className="hover:bg-white/5">
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-2">
                          <span className="font-bold text-white">{p.symbol}</span>
                          <span className="text-xs text-slate-500">
                            {getMarket(p.symbol) === 'US' && '🇺🇸'}
                            {getMarket(p.symbol) === 'HK' && '🇭🇰'}
                            {getMarket(p.symbol) === 'CN' && '🇨🇳'}
                            {getMarket(p.symbol) === 'SG' && '🇸🇬'}
                          </span>
                        </div>
                      </td>
                      
                      <td className="px-4 py-3 text-center">
                        {strat ? (
                          <span className="px-2 py-1 rounded bg-blue-500/20 text-blue-400 text-xs">
                            {strat.name}
                          </span>
                        ) : (
                          <span className="text-xs text-slate-600">-</span>
                        )}
                      </td>
                      
                      <td className="px-4 py-3 text-right">
                        <span className={`font-mono font-medium ${p.position > 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                          {p.position > 0 ? '+' : ''}{p.position}
                        </span>
                      </td>
                      
                      <td className="px-4 py-3 text-right font-mono text-slate-400">
                        ${p.avgCost?.toFixed(2)}
                      </td>
                      
                      <td className="px-4 py-3 text-right font-mono">
                        <span className={isEstimated ? 'text-amber-400' : 'text-white'}>
                          ${price?.toFixed(2)}
                        </span>
                        {isEstimated && (
                          <span className="text-[10px] text-amber-400/60 ml-1">(est)</span>
                        )}
                      </td>
                      
                      <td className="px-4 py-3 text-right font-mono text-white">
                        {format$(value)}
                      </td>
                      
                      <td className="px-4 py-3 text-right">
                        <div className={`font-mono font-medium ${pnl >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                          {pnl >= 0 ? '+' : ''}{format$(pnl)}
                        </div>
                        <div className={`text-xs ${pnlPct >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                          {pnlPct >= 0 ? '+' : ''}{pnlPct.toFixed(1)}%
                        </div>
                      </td>
                      
                      <td className="px-4 py-3 text-center">
                        {isClosing ? (
                          <span className="text-xs text-amber-400 animate-pulse">Closing...</span>
                        ) : (
                          <button
                            onClick={() => handleClose(p.symbol, p.position)}
                            className="px-3 py-1.5 rounded-lg bg-rose-500/20 text-rose-400 text-xs font-medium hover:bg-rose-500/30"
                          >
                            Close
                          </button>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      ) : (
        <div className="text-center py-12 text-slate-500">
          <div className="text-4xl mb-2">📭</div>
          <div className="text-sm">No positions in {marketFilter === 'ALL' ? 'portfolio' : marketFilter}</div>
        </div>
      )}
    </div>
  );
};
