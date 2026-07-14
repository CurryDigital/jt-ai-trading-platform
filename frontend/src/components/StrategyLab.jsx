import React, { useState, useMemo } from 'react';
import { api, usePoll } from '../utils';

/**
 * Strategy Lab — backtest screener with live-performance comparison.
 * Real data only; no placeholders. Backtest metrics come from
 * /api/strategies/researcher, live metrics from /api/strategies/stats.
 */

const ASSET_CLASSES = [
  { id: 'ALL', label: 'All' },
  { id: 'EQUITY', label: 'Equity' },
  { id: 'ETF', label: 'ETF' },
  { id: 'FX', label: 'FX' },
  { id: 'CRYPTO', label: 'Crypto' },
  { id: 'COMMODITY', label: 'Commodity' },
];

const CLASS_CHIP = {
  EQUITY: 'bg-blue-500/20 text-blue-300',
  ETF: 'bg-violet-500/20 text-violet-300',
  FX: 'bg-sky-500/20 text-sky-300',
  CRYPTO: 'bg-teal-500/20 text-teal-300',
  COMMODITY: 'bg-amber-500/20 text-amber-300',
};

const DEFAULT_POOL = 100000;

const normalizeAssetClass = (raw) => {
  const v = (raw || '').toUpperCase();
  if (['STOCK', 'EQUITY', 'EQUITY_INDEX', 'QUANT'].includes(v)) return 'EQUITY';
  if (v === 'ETF') return 'ETF';
  if (v === 'FX') return 'FX';
  if (v === 'CRYPTO') return 'CRYPTO';
  if (['COMMODITY', 'COMMODITIES', 'FUTURE'].includes(v)) return 'COMMODITY';
  return 'EQUITY';
};

const num = (n, d = 1) => (n == null || isNaN(n) ? null : Number(n).toFixed(d));
const pct = (n) => (n == null || isNaN(n) ? null : (Number(n) * 100).toFixed(1)); // fraction → percent
const money = (n) => {
  if (n == null || isNaN(n)) return null;
  const a = Math.abs(n);
  if (a >= 1e6) return `$${(n / 1e6).toFixed(2)}M`;
  if (a >= 1e3) return `$${(n / 1e3).toFixed(1)}k`;
  return `$${n.toFixed(0)}`;
};

const StrategyLab = () => {
  const [strategies, setStrategies] = useState([]);
  const [liveStats, setLiveStats] = useState({});
  const [loading, setLoading] = useState(true);

  const [activeAssetClass, setActiveAssetClass] = useState('ALL');
  const [sortBy, setSortBy] = useState('win_rate');
  const [sortDirection, setSortDirection] = useState('desc');
  const [minWinRate, setMinWinRate] = useState(0);
  const [searchQuery, setSearchQuery] = useState('');
  const [expandedStrategy, setExpandedStrategy] = useState(null);

  const [deployingId, setDeployingId] = useState(null);
  const [deployResult, setDeployResult] = useState(null);

  const fetchStrategies = async () => {
    const data = await api.get('/api/strategies/researcher');
    setStrategies(data?.strategies || []);
  };
  const fetchLiveStats = async () => {
    const data = await api.get('/api/strategies/stats');
    setLiveStats(data?.stats || {});
  };

  usePoll(async () => {
    await Promise.all([fetchStrategies(), fetchLiveStats()]);
    setLoading(false);
  }, 60000);

  const handleDeploy = async (strategy) => {
    if (deployingId) return;
    const tickers = strategy.universe || [];
    if (tickers.length === 0) {
      setDeployResult({ success: false, error: 'No tickers configured', strategyId: strategy.id });
      setTimeout(() => setDeployResult(null), 3000);
      return;
    }
    if (!window.confirm(`Deploy "${strategy.name}" with a ${money(DEFAULT_POOL)} capital pool across ${tickers.length} ticker(s)?`)) return;

    setDeployingId(strategy.id);
    setDeployResult(null);
    try {
      const res = await fetch('/api/strategies/deploy-with-pool', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ strategy_id: strategy.id, tickers, total_pool: DEFAULT_POOL }),
      });
      const data = res.ok ? await res.json().catch(() => ({})) : { success: false, error: res.statusText || 'Deploy failed' };
      setDeployResult({ ...data, strategyId: strategy.id });
      setTimeout(() => setDeployResult(null), 3000);
      if (data.success) { fetchStrategies(); fetchLiveStats(); }
    } catch (e) {
      setDeployResult({ success: false, error: e.message, strategyId: strategy.id });
    } finally {
      setDeployingId(null);
    }
  };

  const merged = useMemo(() => strategies.map(s => {
    const live = liveStats[s.id] || {};
    return {
      ...s,
      live_wr: live.actual_win_rate,       // already a percent (0–100)
      live_trades: live.total_trades,
      live_pnl: live.total_pnl,
      live_positions: live.active_positions,
      live_invested: live.total_invested,
    };
  }), [strategies, liveStats]);

  const filtered = useMemo(() => {
    let rows = merged;
    if (activeAssetClass !== 'ALL') rows = rows.filter(s => normalizeAssetClass(s.asset_class) === activeAssetClass);
    if (minWinRate > 0) rows = rows.filter(s => (s.win_rate || 0) * 100 >= minWinRate);
    if (searchQuery) {
      const q = searchQuery.toLowerCase();
      rows = rows.filter(s => s.name?.toLowerCase().includes(q) || s.id?.toLowerCase().includes(q) || s.description?.toLowerCase().includes(q));
    }
    const field = {
      win_rate: s => s.win_rate || 0,
      profit_factor: s => s.profit_factor || 0,
      max_drawdown: s => s.max_drawdown || 0,
      sharpe: s => s.sharpe_ratio || 0,
      backtest_trades: s => s.backtest_trades || 0,
      live_wr: s => s.live_wr || 0,
      live_pnl: s => s.live_pnl || 0,
    }[sortBy] || (s => s.win_rate || 0);
    return [...rows].sort((a, b) => (sortDirection === 'desc' ? field(b) - field(a) : field(a) - field(b)));
  }, [merged, activeAssetClass, minWinRate, searchQuery, sortBy, sortDirection]);

  const Cell = ({ v }) => v != null ? <span className="font-mono text-slate-300">{v}</span> : <span className="text-slate-600">—</span>;

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-sm font-bold text-white">Strategy Lab</h2>
          <p className="text-[10px] text-slate-500 mt-0.5">{filtered.length} strategies · backtest vs. live · real data only</p>
        </div>
      </div>

      {/* Asset-class filter */}
      <div className="flex items-center gap-0.5 p-0.5 rounded-md bg-slate-900/60 border border-white/[0.06] w-fit overflow-x-auto">
        {ASSET_CLASSES.map(ac => {
          const count = ac.id === 'ALL' ? strategies.length : strategies.filter(s => normalizeAssetClass(s.asset_class) === ac.id).length;
          return (
            <button
              key={ac.id}
              onClick={() => setActiveAssetClass(ac.id)}
              className={`flex items-center gap-1.5 px-2.5 py-1.5 rounded text-[10px] font-bold whitespace-nowrap transition-colors ${activeAssetClass === ac.id ? 'bg-white/[0.08] text-white' : 'text-slate-400 hover:text-slate-200'}`}
            >
              {ac.label}
              <span className={`px-1.5 py-0.5 rounded text-[9px] ${activeAssetClass === ac.id ? 'bg-white/20' : 'bg-slate-800'}`}>{count}</span>
            </button>
          );
        })}
      </div>

      {/* Controls */}
      <div className="jt-surface-strong px-3 py-2.5 flex flex-wrap items-center gap-3">
        <input
          type="text" value={searchQuery} onChange={e => setSearchQuery(e.target.value)}
          placeholder="Search strategies…"
          className="flex-1 min-w-[180px] bg-slate-900/60 border border-white/[0.08] rounded-md px-3 py-1.5 text-[11px] text-white placeholder:text-slate-600 focus:outline-none focus:border-blue-500/50"
        />
        <div className="flex items-center gap-2">
          <label className="text-[10px] text-slate-400">Sort</label>
          <select value={sortBy} onChange={e => setSortBy(e.target.value)} className="bg-slate-900/60 border border-white/[0.08] rounded-md px-2 py-1.5 text-[11px] text-white focus:outline-none focus:border-blue-500/50">
            <option value="win_rate">Win Rate</option>
            <option value="profit_factor">Profit Factor</option>
            <option value="max_drawdown">Max Drawdown</option>
            <option value="sharpe">Sharpe Ratio</option>
            <option value="backtest_trades">Backtest Trades</option>
            <option value="live_wr">Live Win Rate</option>
            <option value="live_pnl">Live P&amp;L</option>
          </select>
          <button onClick={() => setSortDirection(d => d === 'desc' ? 'asc' : 'desc')} className="px-2.5 py-1.5 bg-slate-900/60 border border-white/[0.08] rounded-md text-slate-400 hover:text-white text-[11px]">
            {sortDirection === 'desc' ? '↓' : '↑'}
          </button>
        </div>
        <div className="flex items-center gap-2">
          <label className="text-[10px] text-slate-400">Min WR</label>
          <select value={minWinRate} onChange={e => setMinWinRate(Number(e.target.value))} className="bg-slate-900/60 border border-white/[0.08] rounded-md px-2 py-1.5 text-[11px] text-white focus:outline-none focus:border-blue-500/50">
            <option value={0}>Any</option>
            <option value={50}>50%+</option>
            <option value={55}>55%+</option>
            <option value={60}>60%+</option>
            <option value={65}>65%+</option>
          </select>
        </div>
      </div>

      {loading ? (
        <div className="qr-surface px-3 py-10 flex items-center justify-center gap-2 text-[11px] text-slate-500">
          <div className="w-3 h-3 border-2 border-slate-700 border-t-blue-500 rounded-full animate-spin" />
          Loading strategies…
        </div>
      ) : filtered.length === 0 ? (
        <div className="qr-surface px-3 py-10 text-center text-[11px] text-slate-500">No strategies match your filters</div>
      ) : (
        <div className="jt-surface-strong overflow-x-auto">
          <table className="w-full text-[11px]">
            <thead className="text-[9px] font-black text-slate-500 uppercase tracking-wide border-b border-white/[0.08]">
              <tr>
                <th className="text-left p-2.5">Strategy</th>
                <th className="text-center p-2.5">Class</th>
                <th className="text-center p-2.5">WR</th>
                <th className="text-center p-2.5">PF</th>
                <th className="text-center p-2.5">MDD</th>
                <th className="text-center p-2.5">Sharpe</th>
                <th className="text-center p-2.5">Trades</th>
                <th className="text-center p-2.5 bg-emerald-900/20">Live WR</th>
                <th className="text-center p-2.5 bg-emerald-900/20">Live P&amp;L</th>
                <th className="text-right p-2.5" />
              </tr>
            </thead>
            <tbody>
              {filtered.map((s, idx) => {
                const isExpanded = expandedStrategy === s.id;
                const ac = normalizeAssetClass(s.asset_class);
                return (
                  <React.Fragment key={s.id}>
                    <tr className="border-b border-white/[0.04] hover:bg-white/[0.03] cursor-pointer" onClick={() => setExpandedStrategy(isExpanded ? null : s.id)}>
                      <td className="p-2.5">
                        <div className="flex items-center gap-2.5">
                          <span className="text-[10px] text-slate-600 font-mono">#{idx + 1}</span>
                          <div>
                            <div className="font-bold text-white">{s.name}</div>
                            <div className="text-[9px] text-slate-500">{s.id}</div>
                          </div>
                        </div>
                      </td>
                      <td className="p-2.5 text-center">
                        <span className={`text-[9px] px-2 py-0.5 rounded font-bold ${CLASS_CHIP[ac] || 'bg-slate-500/20 text-slate-300'}`} title={s.asset_class || ''}>{ac}</span>
                      </td>
                      <td className="p-2.5 text-center"><Cell v={pct(s.win_rate) != null ? `${pct(s.win_rate)}%` : null} /></td>
                      <td className="p-2.5 text-center"><Cell v={num(s.profit_factor, 2)} /></td>
                      <td className="p-2.5 text-center">{s.max_drawdown != null ? <span className="font-mono text-rose-400">{pct(s.max_drawdown)}%</span> : <span className="text-slate-600">—</span>}</td>
                      <td className="p-2.5 text-center"><Cell v={num(s.sharpe_ratio, 2)} /></td>
                      <td className="p-2.5 text-center"><Cell v={s.backtest_trades != null ? String(s.backtest_trades) : null} /></td>
                      <td className="p-2.5 text-center bg-emerald-900/10">
                        {s.live_wr != null ? <span className="font-mono font-bold text-emerald-400">{num(s.live_wr, 1)}%</span> : <span className="text-slate-600">—</span>}
                      </td>
                      <td className="p-2.5 text-center bg-emerald-900/10">
                        {s.live_pnl != null ? <span className={`font-mono font-bold ${s.live_pnl >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>{s.live_pnl >= 0 ? '+' : ''}{money(s.live_pnl)}</span> : <span className="text-slate-600">—</span>}
                      </td>
                      <td className="p-2.5 text-right text-slate-500">{isExpanded ? '▼' : '▶'}</td>
                    </tr>

                    {isExpanded && (
                      <tr className="bg-slate-900/30">
                        <td colSpan={10} className="p-4">
                          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div className="space-y-3">
                              <h4 className="text-[9px] font-bold text-slate-500 uppercase tracking-wide">Details</h4>
                              <p className="text-[12px] text-slate-300">{s.description || 'No description available'}</p>
                              <div className="grid grid-cols-2 gap-2 text-[11px]">
                                {[['Time Horizon', s.time_horizon], ['Direction', s.direction], ['Venue', s.venue], ['Universe', s.universe_count || (s.universe || []).length]].map(([k, v]) => (
                                  <div key={k} className="bg-slate-800/50 p-2 rounded">
                                    <span className="text-slate-500 block text-[9px]">{k}</span>
                                    <span className="text-white">{v ?? '—'}</span>
                                  </div>
                                ))}
                              </div>
                              {s.universe && s.universe.length > 0 && (
                                <div>
                                  <span className="text-[9px] text-slate-500 block mb-1">Asset Universe</span>
                                  <div className="flex flex-wrap gap-1">
                                    {s.universe.slice(0, 10).map(t => <span key={t} className="text-[10px] px-2 py-0.5 bg-slate-800 rounded text-slate-400">{t}</span>)}
                                    {s.universe.length > 10 && <span className="text-[10px] px-2 py-0.5 bg-slate-800 rounded text-slate-500">+{s.universe.length - 10}</span>}
                                  </div>
                                </div>
                              )}
                            </div>
                            <div className="space-y-3">
                              <h4 className="text-[9px] font-bold text-slate-500 uppercase tracking-wide">Logic</h4>
                              <div className="bg-slate-800/50 p-3 rounded">
                                <span className="text-[9px] text-slate-500 block mb-1">Entry</span>
                                <span className="text-[12px] text-white font-mono">{s.entry_logic || '—'}</span>
                              </div>
                              <div className="bg-slate-800/50 p-3 rounded">
                                <span className="text-[9px] text-slate-500 block mb-1">Exit</span>
                                <span className="text-[12px] text-white font-mono">{s.exit_logic || '—'}</span>
                              </div>
                              <button
                                onClick={(e) => { e.stopPropagation(); handleDeploy(s); }}
                                disabled={deployingId === s.id}
                                className="w-full py-2 bg-emerald-500 hover:bg-emerald-400 disabled:bg-slate-700 text-white text-[11px] font-bold rounded-lg transition-colors flex items-center justify-center gap-2"
                              >
                                {deployingId === s.id ? (
                                  <><span className="w-3 h-3 border-2 border-white/30 border-t-white rounded-full animate-spin" />Deploying…</>
                                ) : deployResult?.strategyId === s.id ? (
                                  deployResult.success ? <span className="text-emerald-100">✓ Deployed</span> : <span className="text-rose-200">✗ {deployResult.error}</span>
                                ) : (
                                  <>Deploy · {money(DEFAULT_POOL)} pool · {s.universe?.length || 0} tickers</>
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

      <div className="flex flex-wrap items-center gap-4 text-[9px] text-slate-500">
        <div className="flex items-center gap-1"><span className="w-3 h-3 bg-emerald-900/20 rounded" /><span>Live performance (green)</span></div>
        <span className="ml-auto">WR = Win Rate · PF = Profit Factor · MDD = Max Drawdown · — = No Data</span>
      </div>
    </div>
  );
};

export { StrategyLab };
export default StrategyLab;
