import React, { useState, useEffect } from 'react';

// Research Tab — uses /api/stocks/all (available) instead of broken endpoints
export const ResearchTab = ({ onTickerClick }) => {
  const [activeSection, setActiveSection] = useState('screener'); // screener, signals, movers
  const [stocks, setStocks] = useState([]);
  const [signals, setSignals] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const [filters, setFilters] = useState({
    market: 'ALL',
    action: 'ALL',
    minScore: 0,
    sortBy: 'score',
    searchQuery: '',
    sector: 'ALL',
  });

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    setLoading(true);
    setError(null);
    try {
      // Primary: /api/stocks/all — returns real stock data from consumption layer
      const stocksRes = await fetch('/api/stocks/all');
      if (stocksRes.ok) {
        const data = await stocksRes.json();
        // Defensive: API returns array directly, but guard against object wrappers
        const arr = Array.isArray(data) ? data : (data && Array.isArray(data.data)) ? data.data : [];
        setStocks(arr);
      } else {
        setError('Failed to load stock data (HTTP ' + stocksRes.status + ')');
      }

      // Secondary: /api/signals/1 — may be empty but we try
      const signalsRes = await fetch('/api/signals/1');
      if (signalsRes.ok) {
        const data = await signalsRes.json();
        const arr = Array.isArray(data) ? data : (data && Array.isArray(data.data)) ? data.data : [];
        setSignals(arr);
      }
    } catch (e) {
      console.error('ResearchTab fetch error:', e);
      setError(e.message || 'Network error');
    }
    setLoading(false);
  };

  // Guard: ensure stocks is always an array before filtering
  const safeStocks = Array.isArray(stocks) ? stocks : [];

  // Filter stocks
  const filteredStocks = safeStocks.filter(stock => {
    if (!stock || typeof stock !== 'object') return false;
    const ticker = (stock.ticker || '').toUpperCase();
    const name = (stock.name || '').toLowerCase();
    const q = filters.searchQuery.toLowerCase();
    if (q && !ticker.includes(q) && !name.includes(q)) return false;
    if (filters.market !== 'ALL' && stock.market !== filters.market) return false;
    if (filters.sector !== 'ALL' && (stock.sector || 'Unknown') !== filters.sector) return false;
    if (filters.action !== 'ALL' && stock.action !== filters.action) return false;
    if ((stock.score || 0) < filters.minScore) return false;
    return true;
  }).sort((a, b) => {
    if (filters.sortBy === 'score') return (b.score || 0) - (a.score || 0);
    if (filters.sortBy === 'change') return (b.change || 0) - (a.change || 0);
    if (filters.sortBy === 'price') return (b.price || 0) - (a.price || 0);
    if (filters.sortBy === 'name') return (a.ticker || '').localeCompare(b.ticker || '');
    return 0;
  });

  // Top movers (biggest % change)
  const movers = [...safeStocks]
    .filter(s => s && s.change != null)
    .sort((a, b) => Math.abs(b.change || 0) - Math.abs(a.change || 0))
    .slice(0, 20);

  // Sectors for filter
  const sectors = [...new Set(safeStocks.map(s => s.sector).filter(Boolean))].sort();

  const sections = [
    { id: 'screener', label: '🔍 Stock Screener' },
    { id: 'signals', label: '⚡ Signals' },
    { id: 'movers', label: '📈 Top Movers' },
  ];

  const fmt = (n, d = 2) => {
    if (n == null || n === '' || Number.isNaN(Number(n))) return '—';
    return Number(n).toFixed(d);
  };
  const pnlCl = (v) => (v == null ? 'text-slate-500' : Number(v) >= 0 ? 'text-emerald-400' : 'text-rose-400');

  // Defensive: don't render table if safeStocks is not an array
  if (!Array.isArray(safeStocks)) {
    return (
      <div className="p-6 text-center text-rose-300 text-sm">
        ⚠️ Data error: stocks is not an array. <button onClick={fetchData} className="underline">Retry</button>
      </div>
    );
  }

  return (
    <div className="space-y-4 animate-in fade-in duration-300">
      {/* Section Tabs */}
      <div className="flex items-center gap-1 p-1 rounded-lg bg-slate-900/50 border border-white/[0.06]">
        {sections.map(sec => (
          <button
            key={sec.id}
            onClick={() => setActiveSection(sec.id)}
            className={`flex-1 px-3 py-2 rounded-md text-[11px] font-bold transition-all ${
              activeSection === sec.id
                ? 'bg-blue-500 text-white shadow-lg'
                : 'text-slate-400 hover:text-white hover:bg-white/5'
            }`}
          >
            {sec.label}
          </button>
        ))}
      </div>

      {/* Error banner */}
      {error && (
        <div className="p-3 rounded-lg bg-rose-500/10 border border-rose-500/20 text-rose-300 text-xs">
          ⚠️ {error}
          <button onClick={fetchData} className="ml-2 underline hover:text-rose-200">Retry</button>
        </div>
      )}

      {/* === STOCK SCREENER === */}
      {activeSection === 'screener' && (
        <div className="space-y-3">
          {/* Filters */}
          <div className="p-3 rounded-xl bg-slate-900/50 border border-white/[0.06] space-y-3">
            <div className="relative">
              <span className="absolute left-2.5 top-1/2 -translate-y-1/2 text-slate-500 text-xs">🔍</span>
              <input
                type="text"
                placeholder="Search ticker or name..."
                value={filters.searchQuery}
                onChange={e => setFilters({...filters, searchQuery: e.target.value})}
                className="w-full pl-8 pr-3 py-1.5 bg-slate-800/80 border border-white/10 rounded-lg text-xs text-white placeholder-slate-600 focus:border-blue-500/50 focus:outline-none"
              />
            </div>
            <div className="flex flex-wrap items-center gap-2">
              <select
                value={filters.market}
                onChange={e => setFilters({...filters, market: e.target.value})}
                className="bg-slate-800/80 border border-white/10 rounded px-2 py-1 text-[11px] text-white"
              >
                <option value="ALL">All Markets</option>
                <option value="US">US</option>
                <option value="HK">HK</option>
              </select>
              <select
                value={filters.sector}
                onChange={e => setFilters({...filters, sector: e.target.value})}
                className="bg-slate-800/80 border border-white/10 rounded px-2 py-1 text-[11px] text-white"
              >
                <option value="ALL">All Sectors</option>
                {sectors.map(s => <option key={s} value={s}>{s}</option>)}
              </select>
              <select
                value={filters.action}
                onChange={e => setFilters({...filters, action: e.target.value})}
                className="bg-slate-800/80 border border-white/10 rounded px-2 py-1 text-[11px] text-white"
              >
                <option value="ALL">All Actions</option>
                <option value="BUY">Buy</option>
                <option value="SELL">Sell</option>
                <option value="HOLD">Hold</option>
              </select>
              <select
                value={filters.sortBy}
                onChange={e => setFilters({...filters, sortBy: e.target.value})}
                className="bg-slate-800/80 border border-white/10 rounded px-2 py-1 text-[11px] text-white"
              >
                <option value="score">Sort: Score</option>
                <option value="change">Sort: Change %</option>
                <option value="price">Sort: Price</option>
                <option value="name">Sort: Name</option>
              </select>
              <button
                onClick={fetchData}
                className="ml-auto px-3 py-1 bg-blue-500 hover:bg-blue-400 text-white text-[10px] font-bold rounded-md transition-colors"
              >
                🔄 Refresh
              </button>
            </div>
          </div>

          {/* Results count */}
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-bold text-white">{filteredStocks.length} stocks</span>
            <span className="text-[10px] text-slate-500">{stocks.length} total in DB</span>
          </div>

          {/* Stock table */}
          {loading ? (
            <div className="text-center py-12">
              <div className="w-6 h-6 border-2 border-slate-600 border-t-blue-500 rounded-full animate-spin mx-auto mb-2" />
              <p className="text-xs text-slate-500">Loading stocks...</p>
            </div>
          ) : filteredStocks.length === 0 ? (
            <div className="text-center py-12 text-slate-500 text-sm">
              <div className="text-3xl mb-2">🔍</div>
              <p>No stocks match filters</p>
            </div>
          ) : (
            <div className="rounded-xl border border-white/[0.06] overflow-hidden">
              <table className="w-full text-[11px]">
                <thead className="bg-slate-900/80">
                  <tr className="text-[9px] font-bold text-slate-500 uppercase tracking-wider">
                    {['Ticker', 'Name', 'Sector', 'Price', 'Change', 'Score', 'RSI', 'Trend', 'Action'].map(h =>
                      <th key={h} className="text-right py-2 px-2 first:text-left">{h}</th>)}
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/5">
                  {filteredStocks.map(stock => (
                    <tr
                      key={stock.ticker}
                      onClick={() => onTickerClick && onTickerClick(stock.ticker)}
                      className="hover:bg-white/[0.03] transition-colors cursor-pointer"
                    >
                      <td className="py-2 px-2 font-bold text-white">{stock.ticker}</td>
                      <td className="py-2 px-2 text-slate-400 max-w-[140px] truncate">{stock.name || '—'}</td>
                      <td className="py-2 px-2 text-slate-500">{stock.sector || '—'}</td>
                      <td className="py-2 px-2 text-right font-mono text-white">${fmt(stock.price)}</td>
                      <td className={`py-2 px-2 text-right font-mono font-bold ${pnlCl(stock.change)}`}>
                        {stock.change >= 0 ? '+' : ''}{fmt(stock.change)}%
                      </td>
                      <td className="py-2 px-2 text-right font-mono text-white">{Math.round(stock.score || 0)}</td>
                      <td className="py-2 px-2 text-right font-mono text-slate-400">{fmt(stock.rsi, 1)}</td>
                      <td className="py-2 px-2 text-right">
                        <span className={`text-[9px] font-bold px-1.5 py-0.5 rounded ${
                          stock.trend === 'bullish' ? 'bg-emerald-500/15 text-emerald-400' :
                          stock.trend === 'bearish' ? 'bg-rose-500/15 text-rose-400' :
                          'bg-slate-500/15 text-slate-400'
                        }`}>{stock.trend || '—'}</span>
                      </td>
                      <td className="py-2 px-2 text-right">
                        <span className={`text-[9px] font-bold px-1.5 py-0.5 rounded ${
                          stock.action === 'BUY' ? 'bg-emerald-500/15 text-emerald-400' :
                          stock.action === 'SELL' ? 'bg-rose-500/15 text-rose-400' :
                          'bg-amber-500/15 text-amber-400'
                        }`}>{stock.action || 'HOLD'}</span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* === SIGNALS === */}
      {activeSection === 'signals' && (
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-bold text-white">{signals.length} signals from /api/signals/1</span>
            <button onClick={fetchData} className="px-3 py-1 bg-blue-500 hover:bg-blue-400 text-white text-[10px] font-bold rounded-md">🔄 Refresh</button>
          </div>

          {loading ? (
            <div className="text-center py-12">
              <div className="w-6 h-6 border-2 border-slate-600 border-t-blue-500 rounded-full animate-spin mx-auto mb-2" />
              <p className="text-xs text-slate-500">Loading signals...</p>
            </div>
          ) : signals.length === 0 ? (
            <div className="text-center py-12 text-slate-500 text-sm">
              <div className="text-3xl mb-2">⚡</div>
              <p>No signals available</p>
              <p className="text-[10px] text-slate-600 mt-1">Consumption layer may be empty or DE pipeline not run</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
              {signals.slice(0, 50).map((sig, idx) => (
                <div
                  key={`${sig.ticker}-${idx}`}
                  onClick={() => onTickerClick && onTickerClick(sig.ticker)}
                  className="p-3 rounded-xl bg-slate-900/50 border border-white/[0.06] hover:border-blue-500/40 cursor-pointer transition-all"
                >
                  <div className="flex items-start justify-between mb-2">
                    <div>
                      <h4 className="text-sm font-bold text-white">{sig.ticker}</h4>
                      <p className="text-[10px] text-slate-500">{sig.category} · {sig.asset}</p>
                    </div>
                    <span className={`text-[9px] font-bold px-1.5 py-0.5 rounded ${
                      sig.action === 'BUY' ? 'bg-emerald-500/15 text-emerald-400' :
                      sig.action === 'SELL' ? 'bg-rose-500/15 text-rose-400' :
                      'bg-amber-500/15 text-amber-400'
                    }`}>{sig.action || 'HOLD'}</span>
                  </div>
                  <div className="grid grid-cols-2 gap-2">
                    <div className="bg-slate-800/50 rounded p-1.5">
                      <span className="text-[9px] text-slate-500 block">Price</span>
                      <span className="text-xs font-bold text-white">${fmt(sig.price)}</span>
                    </div>
                    <div className="bg-slate-800/50 rounded p-1.5">
                      <span className="text-[9px] text-slate-500 block">Confidence</span>
                      <span className={`text-xs font-bold ${(sig.total_confidence || 0) >= 70 ? 'text-emerald-400' : (sig.total_confidence || 0) >= 50 ? 'text-blue-400' : 'text-amber-400'}`}>
                        {fmt(sig.total_confidence)}%
                      </span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* === TOP MOVERS === */}
      {activeSection === 'movers' && (
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-bold text-white">Top 20 Movers by % Change</span>
            <button onClick={fetchData} className="px-3 py-1 bg-blue-500 hover:bg-blue-400 text-white text-[10px] font-bold rounded-md">🔄 Refresh</button>
          </div>

          {loading ? (
            <div className="text-center py-12">
              <div className="w-6 h-6 border-2 border-slate-600 border-t-blue-500 rounded-full animate-spin mx-auto mb-2" />
              <p className="text-xs text-slate-500">Loading...</p>
            </div>
          ) : movers.length === 0 ? (
            <div className="text-center py-12 text-slate-500 text-sm">
              <div className="text-3xl mb-2">📈</div>
              <p>No mover data available</p>
            </div>
          ) : (
            <div className="rounded-xl border border-white/[0.06] overflow-hidden">
              <table className="w-full text-[11px]">
                <thead className="bg-slate-900/80">
                  <tr className="text-[9px] font-bold text-slate-500 uppercase tracking-wider">
                    {['#', 'Ticker', 'Name', 'Price', 'Change %', 'Volume', 'Action'].map(h =>
                      <th key={h} className="text-right py-2 px-2 first:text-left">{h}</th>)}
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/5">
                  {movers.map((stock, idx) => (
                    <tr
                      key={stock.ticker}
                      onClick={() => onTickerClick && onTickerClick(stock.ticker)}
                      className="hover:bg-white/[0.03] transition-colors cursor-pointer"
                    >
                      <td className="py-2 px-2 text-slate-500 font-mono">{idx + 1}</td>
                      <td className="py-2 px-2 font-bold text-white">{stock.ticker}</td>
                      <td className="py-2 px-2 text-slate-400 max-w-[140px] truncate">{stock.name || '—'}</td>
                      <td className="py-2 px-2 text-right font-mono text-white">${fmt(stock.price)}</td>
                      <td className={`py-2 px-2 text-right font-mono font-bold ${pnlCl(stock.change)}`}>
                        {stock.change >= 0 ? '+' : ''}{fmt(stock.change)}%
                      </td>
                      <td className="py-2 px-2 text-right font-mono text-slate-400">{stock.volume != null ? Number(stock.volume).toLocaleString() : '—'}</td>
                      <td className="py-2 px-2 text-right">
                        <span className={`text-[9px] font-bold px-1.5 py-0.5 rounded ${
                          stock.action === 'BUY' ? 'bg-emerald-500/15 text-emerald-400' :
                          stock.action === 'SELL' ? 'bg-rose-500/15 text-rose-400' :
                          'bg-amber-500/15 text-amber-400'
                        }`}>{stock.action || 'HOLD'}</span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default ResearchTab;
