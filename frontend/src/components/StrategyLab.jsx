import React, { useState, useMemo } from 'react';
import { api, usePoll } from '../utils';
import { stageFor } from './strategyProfiles';

/**
 * Strategy Lab — backtest screener with live pipeline metrics.
 * Table data comes from /api/strategies/pipeline-feed (gold.v_pipeline_ui_feed).
 * Rich strategy details (description, universe, logic) are fetched from
 * /api/strategies/researcher so the deploy/detail panel still works.
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

// Hard gates enforced by gold.v_pipeline_ui_feed (s.publishable). Lab shows
// only strategies passing all of them; the Pipeline tab shows the full
// research universe (no metric gates). Counts below are derived from the two
// live endpoints, not hard-coded.
const QUALITY_GATES =
  'Quality gates (gold.v_pipeline_ui_feed): OOS Sharpe ≥ 0.5 · |OOS max drawdown| ≤ 20% · OOS trades ≥ 30 · OOS returns present · research not rejected/retired. Lab, Pipeline and Performance all show this same gated universe.';

const normalizeAssetClass = (raw) => {
  const v = (raw || '').toUpperCase();
  if (v.includes('STOCK') || v.includes('EQUITY') || v.includes('QUANT')) return 'EQUITY';
  if (v === 'ETF' || v.includes('ETF')) return 'ETF';
  if (v === 'FX' || v.includes('CURRENCY')) return 'FX';
  if (v === 'CRYPTO' || v.includes('CRYPTO')) return 'CRYPTO';
  if (v.includes('COMMODITY') || v.includes('FUTURE') || v.includes('VOLATILITY')) return 'COMMODITY';
  return 'EQUITY';
};

const num = (n, d = 1) => (n == null || isNaN(n) ? null : Number(n).toFixed(d));
const pct = (n) => {
  if (n == null || isNaN(n)) return null;
  const v = Number(n);
  const normalized = Math.abs(v) <= 1 ? v * 100 : v;
  return normalized.toFixed(1);
};
const money = (n) => {
  if (n == null || isNaN(n)) return null;
  const a = Math.abs(n);
  if (a >= 1e6) return `$${(n / 1e6).toFixed(2)}M`;
  if (a >= 1e3) return `$${(n / 1e3).toFixed(1)}k`;
  return `$${n.toFixed(0)}`;
};

const StrategyLab = ({ onOpen }) => {
  const [strategies, setStrategies] = useState([]);
  const [detailsMap, setDetailsMap] = useState({});
  const [loading, setLoading] = useState(true);

  const [activeAssetClass, setActiveAssetClass] = useState('ALL');
  const [sortBy, setSortBy] = useState('btwr');
  const [sortDirection, setSortDirection] = useState('desc');
  const [minWinRate, setMinWinRate] = useState(0);
  const [searchQuery, setSearchQuery] = useState('');
  const [expandedStrategy, setExpandedStrategy] = useState(null);

  const [deployingId, setDeployingId] = useState(null);
  const [deployResult, setDeployResult] = useState(null);
  const [stoppingId, setStoppingId] = useState(null);
  const [stopResult, setStopResult] = useState(null);

  const fetchPipeline = async () => {
    const data = await api.get('/api/strategies/pipeline-feed');
    setStrategies(data?.data || []);
  };

  const fetchDetails = async () => {
    const data = await api.get('/api/strategies/researcher');
    const rows = data?.strategies || [];
    setDetailsMap(Object.fromEntries(rows.map(s => [s.id, s])));
  };

  usePoll(async () => {
    await Promise.all([fetchPipeline(), fetchDetails()]);
    setLoading(false);
  }, 60000);

  const refresh = () => { fetchPipeline(); fetchDetails(); };

  const handleDeploy = async (strategy) => {
    if (deployingId || stoppingId) return;
    if (strategy.db_status === 'rejected') {
      setDeployResult({ success: false, error: 'Rejected strategies cannot be deployed', strategyId: strategy.id });
      setTimeout(() => setDeployResult(null), 3000);
      return;
    }
    const tickers = strategy.universe || [];
    if (tickers.length === 0) {
      setDeployResult({ success: false, error: 'No tickers configured', strategyId: strategy.id });
      setTimeout(() => setDeployResult(null), 3000);
      return;
    }
    if (!window.confirm(`Deploy "${strategy.name}" to PAPER TRADING with a ${money(DEFAULT_POOL)} capital pool across ${tickers.length} ticker(s)?`)) return;

    setDeployingId(strategy.id);
    setDeployResult(null);
    try {
      const data = await api.post('/api/strategies/deploy-with-pool', {
        strategy_id: strategy.id,
        tickers,
        total_pool: DEFAULT_POOL,
        mode: 'PAPER_TRADING',
      });
      setDeployResult({ ...data, strategyId: strategy.id });
      setTimeout(() => setDeployResult(null), 3000);
      if (data.success) { refresh(); }
    } catch (e) {
      setDeployResult({ success: false, error: e.message, strategyId: strategy.id });
    } finally {
      setDeployingId(null);
    }
  };

  const handleStop = async (strategy) => {
    if (deployingId || stoppingId) return;
    if (!window.confirm(`Stop paper-trading monitoring for "${strategy.name}"? This will close positions and purge paper-trading records.`)) return;

    setStoppingId(strategy.id);
    setStopResult(null);
    try {
      const data = await api.post(`/api/strategies/${encodeURIComponent(strategy.id)}/deactivate`, {
        action: 'close',
      });
      setStopResult({ ...data, strategyId: strategy.id });
      setTimeout(() => setStopResult(null), 3000);
      if (data.success) { refresh(); }
    } catch (e) {
      setStopResult({ success: false, error: e.message, strategyId: strategy.id });
    } finally {
      setStoppingId(null);
    }
  };

  const merged = useMemo(() => strategies.map(s => {
    const d = detailsMap[s.id] || {};
    // Lifecycle stage must be derived with the same rule used by the Pipeline
    // and Performance sub-tabs (stageFor in strategyProfiles.js): golden
    // requires status='paper' AND execution_mode='PAPER_TRADING'. The feed
    // view (gold.v_pipeline_ui_feed) computes stage from status alone, which
    // made this tab show "golden" while Pipeline showed "experimental" for
    // the same registry row. Prefer the registry-backed details row; fall
    // back to the feed's stage only when no registry row is available.
    const stage = d.id ? stageFor({ ...d, mode: s.mode }) : s.stage;
    return {
      ...d,
      ...s,
      id: s.id,
      name: s.name,
      asset_class: s.asset,
      // Simulation (backtest) metrics — left-hand block.
      win_rate: s.sim_wr,
      profit_factor: s.btpf,
      backtest_trades: s.trades,
      sharpe_ratio: s.sharpe,
      max_drawdown: s.dd,
      // Live / paper-trading metrics — only populated when is_paper_monitoring is true.
      is_paper_monitoring: s.is_paper_monitoring,
      paper_state: s.paper_state,
      paper_open_positions: s.paper_open_positions,
      live_wr: s.paper_wr,
      live_pf: s.paper_pf,
      live_pnl: s.paper_pnl,
      live_pnl_realized: s.paper_pnl_realized,
      live_pnl_unrealized: s.paper_pnl_unrealized,
      live_unpriced: s.paper_unpriced,
      live_trades: s.paper_trades,
      // Legacy aliases kept in case downstream code still references them.
      db_status: s.db_status,
      mode: s.mode,
      stage,
      tier: s.tier,
      horizon: s.horizon,
    };
  }), [strategies, detailsMap]);

  // Full research universe = /api/strategies/researcher rows (same source as
  // the Pipeline tab). Used for the "N of M pass quality gates" header copy.
  const pipelineUniverse = useMemo(() => Object.keys(detailsMap).length, [detailsMap]);

  const filtered = useMemo(() => {
    let rows = merged;
    if (activeAssetClass !== 'ALL') rows = rows.filter(s => normalizeAssetClass(s.asset_class) === activeAssetClass);
    if (minWinRate > 0) rows = rows.filter(s => (s.win_rate || 0) >= minWinRate);
    if (searchQuery) {
      const q = searchQuery.toLowerCase();
      rows = rows.filter(s => s.name?.toLowerCase().includes(q) || s.id?.toLowerCase().includes(q) || s.description?.toLowerCase().includes(q));
    }
    const field = {
      btwr: s => s.win_rate || 0,
      profit_factor: s => s.profit_factor || 0,
      max_drawdown: s => s.max_drawdown || 0,
      sharpe: s => s.sharpe_ratio || 0,
      backtest_trades: s => s.backtest_trades || 0,
      live_wr: s => s.live_wr || 0,
      live_pf: s => s.live_pf || 0,
      live_pnl: s => s.live_pnl || 0,
    }[sortBy] || (s => s.win_rate || 0);
    return [...rows].sort((a, b) => (sortDirection === 'desc' ? field(b) - field(a) : field(a) - field(b)));
  }, [merged, activeAssetClass, minWinRate, searchQuery, sortBy, sortDirection]);

  const Cell = ({ v }) => v != null ? <span className="font-mono text-slate-300">{v}</span> : <span className="text-slate-600">—</span>;

  const statusBadge = (status) => {
    if (!status) return null;
    if (status === 'rejected') return <span className="ml-2 px-1.5 py-0.5 rounded text-[9px] font-bold bg-rose-500/20 text-rose-300 uppercase">Rejected</span>;
    if (status === 'approved') return <span className="ml-2 px-1.5 py-0.5 rounded text-[9px] font-bold bg-emerald-500/20 text-emerald-300 uppercase">Approved</span>;
    return <span className="ml-2 px-1.5 py-0.5 rounded text-[9px] font-bold bg-slate-700 text-slate-300 uppercase">{status}</span>;
  };

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-sm font-bold text-white">Strategy Lab</h2>
            <span
              className="px-1.5 py-0.5 rounded text-[9px] font-bold bg-slate-800 text-slate-400 uppercase tracking-wide cursor-help"
              title={QUALITY_GATES}
            >
              Quality-gated ⓘ
            </span>
          </div>
          <p className="text-[10px] text-slate-500 mt-0.5">
            {strategies.length} of {pipelineUniverse || '…'} research strategies pass quality gates · Pipeline & Performance show the same gated set · backtest vs. paper · real data only
          </p>
        </div>
      </div>

      {/* Asset-class filter */}
      <div className="flex items-center gap-0.5 p-0.5 rounded-md bg-slate-900/60 border border-white/[0.06] w-fit overflow-x-auto">
        {ASSET_CLASSES.map(ac => {
          const count = ac.id === 'ALL' ? strategies.length : strategies.filter(s => normalizeAssetClass(s.asset) === ac.id).length;
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
            <option value="btwr">Win Rate</option>
            <option value="profit_factor">Profit Factor</option>
            <option value="max_drawdown">Max Drawdown</option>
            <option value="sharpe">Sharpe Ratio</option>
            <option value="backtest_trades">Backtest Trades</option>
            <option value="live_wr">Paper Win Rate</option>
            <option value="live_pf">Paper Profit Factor</option>
            <option value="live_pnl">Paper P&amp;L</option>
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
                <th className="text-center p-2.5">WR (Sim)</th>
                <th className="text-center p-2.5">PF</th>
                <th className="text-center p-2.5">MDD</th>
                <th className="text-center p-2.5">Sharpe</th>
                <th className="text-center p-2.5">Trades</th>
                <th className="text-center p-2.5 bg-emerald-900/20" title="Closed paper trades only">Paper WR</th>
                <th className="text-center p-2.5 bg-emerald-900/20" title="Closed paper trades only">Paper PF</th>
                <th className="text-center p-2.5 bg-emerald-900/20" title="Realized P&L — closed paper trades only; this is what's actually banked (gold.paper_trades_synthetic)">Closed P&amp;L</th>
                <th className="text-center p-2.5 bg-emerald-900/20" title="Unrealized P&L — open positions marked to the latest signal price; theoretical, not yet banked">Open P&amp;L</th>
                <th className="text-right p-2.5" />
              </tr>
            </thead>
            <tbody>
              {filtered.map((s, idx) => {
                const isExpanded = expandedStrategy === s.id;
                const ac = normalizeAssetClass(s.asset_class);
                const isRejected = s.db_status === 'rejected';
                return (
                  <React.Fragment key={s.id}>
                    <tr className={`border-b border-white/[0.04] hover:bg-white/[0.03] cursor-pointer ${isRejected ? 'opacity-70' : ''}`} onClick={() => setExpandedStrategy(isExpanded ? null : s.id)}>
                      <td className="p-2.5">
                        <div className="flex items-center gap-2.5">
                          <span className="text-[10px] text-slate-600 font-mono">#{idx + 1}</span>
                          <div>
                            <div className="font-bold text-white">{s.name}{statusBadge(s.db_status)}{s.paper_skip_count > 0 && (
                              <span
                                className="ml-2 px-1.5 py-0.5 rounded text-[9px] font-bold bg-slate-700 text-slate-300 uppercase cursor-help"
                                title={`${s.paper_skip_count} BUY signal${s.paper_skip_count === 1 ? '' : 's'} not filled in the paper book — open Strategy Detail for reasons`}
                              >{s.paper_skip_count} unfilled</span>
                            )}</div>
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
                        {s.live_pf != null ? <span className="font-mono font-bold text-emerald-400">{num(s.live_pf, 2)}</span> : <span className="text-slate-600">—</span>}
                      </td>
                      <td className="p-2.5 text-center bg-emerald-900/10">
                        {s.live_pnl != null ? (
                          <span
                            className={`font-mono font-bold ${(s.live_pnl_realized || 0) >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}
                            title={`realized across ${s.live_trades || 0} closed paper trade(s) — actually banked · total incl. open ${s.live_pnl >= 0 ? '+' : ''}${money(s.live_pnl)}`}
                          >{s.live_pnl_realized != null ? `${s.live_pnl_realized >= 0 ? '+' : ''}${money(s.live_pnl_realized)}` : '$0'}</span>
                        ) : <span className="text-slate-600">—</span>}
                      </td>
                      <td className="p-2.5 text-center bg-emerald-900/10">
                        {s.live_pnl != null ? (
                          <span
                            className={`font-mono font-bold ${(s.live_pnl_unrealized || 0) >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}
                            title={[
                              'unrealized — open positions marked to latest signal price (theoretical)',
                              s.live_unpriced > 0 ? `${s.live_unpriced} position(s) without a current price` : null,
                            ].filter(Boolean).join(' · ')}
                          >{s.live_pnl_unrealized != null ? `${s.live_pnl_unrealized >= 0 ? '+' : ''}${money(s.live_pnl_unrealized)}` : '$0'}</span>
                        ) : <span className="text-slate-600">—</span>}
                      </td>
                      <td className="p-2.5 text-right text-slate-500 whitespace-nowrap">
                        {onOpen && (
                          <button
                            onClick={(e) => { e.stopPropagation(); onOpen(s.id); }}
                            className="mr-2 text-[10px] font-bold text-blue-400 hover:text-blue-300 transition-colors"
                            title="Open full strategy detail page"
                          >Detail ↗</button>
                        )}
                        {isExpanded ? '▼' : '▶'}
                      </td>
                    </tr>

                    {isExpanded && (
                      <tr className="bg-slate-900/30">
                        <td colSpan={12} className="p-4">
                          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div className="space-y-3">
                              <h4 className="text-[9px] font-bold text-slate-500 uppercase tracking-wide">Details</h4>
                              <p className="text-[12px] text-slate-300">{s.description || 'No description available'}</p>
                              <div className="grid grid-cols-2 gap-2 text-[11px]">
                                {[['Time Horizon', s.time_horizon || s.horizon], ['Direction', s.direction], ['Venue', s.venue], ['Tier', s.tier], ['Stage', s.stage], ['Mode', s.mode], ['Universe', s.universe_count || (s.universe || []).length]].map(([k, v]) => (
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
                              {onOpen && (
                                <button
                                  onClick={(e) => { e.stopPropagation(); onOpen(s.id); }}
                                  className="w-full py-2 border border-white/10 hover:border-blue-400/40 text-blue-400 hover:text-blue-300 text-[11px] font-bold rounded-lg transition-colors"
                                >Open full strategy detail page ↗</button>
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
                              {s.is_paper_monitoring ? (
                                <button
                                  onClick={(e) => { e.stopPropagation(); handleStop(s); }}
                                  disabled={stoppingId === s.id || deployingId === s.id}
                                  className="w-full py-2 bg-rose-500 hover:bg-rose-400 disabled:bg-slate-700 text-white text-[11px] font-bold rounded-lg transition-colors flex items-center justify-center gap-2"
                                >
                                  {stoppingId === s.id ? (
                                    <><span className="w-3 h-3 border-2 border-white/30 border-t-white rounded-full animate-spin" />Stopping…</>
                                  ) : stopResult?.strategyId === s.id ? (
                                    stopResult.success ? <span className="text-rose-100">✓ Stopped</span> : <span className="text-rose-200">✗ {stopResult.error}</span>
                                  ) : (
                                    <>Stop paper trading · purge records</>
                                  )}
                                </button>
                              ) : (
                                <button
                                  onClick={(e) => { e.stopPropagation(); handleDeploy(s); }}
                                  disabled={deployingId === s.id || stoppingId === s.id || isRejected}
                                  className="w-full py-2 bg-emerald-500 hover:bg-emerald-400 disabled:bg-slate-700 text-white text-[11px] font-bold rounded-lg transition-colors flex items-center justify-center gap-2"
                                >
                                  {deployingId === s.id ? (
                                    <><span className="w-3 h-3 border-2 border-white/30 border-t-white rounded-full animate-spin" />Deploying…</>
                                  ) : deployResult?.strategyId === s.id ? (
                                    deployResult.success ? <span className="text-emerald-100">✓ Deployed to paper trading</span> : <span className="text-rose-200">✗ {deployResult.error}</span>
                                  ) : isRejected ? (
                                    <>Rejected · cannot deploy</>
                                  ) : (
                                    <>Deploy to paper trading · {money(DEFAULT_POOL)} pool · {s.universe?.length || 0} tickers</>
                                  )}
                                </button>
                              )}
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
        <div className="flex items-center gap-1"><span className="w-3 h-3 bg-emerald-900/20 rounded" /><span>Paper-trading performance (green)</span></div>
        <span className="ml-auto">Sim = backtest simulation · Paper = paper trading · — = No Data</span>
      </div>
    </div>
  );
};

export { StrategyLab };
export default StrategyLab;
