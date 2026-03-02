import React, { useState, useEffect, useCallback } from 'react';

// =============================================================================
// JTCML TRADING PLATFORM v4.0 — COMPACT AUTO-TRADING DASHBOARD
// =============================================================================

// --- UTILS ---
const fmt = (n, d = 2) => n == null || isNaN(n) ? '—' : n.toLocaleString(undefined, { minimumFractionDigits: d, maximumFractionDigits: d });
const fmtK = (n) => n == null ? '—' : Math.abs(n) >= 1e6 ? `$${(n/1e6).toFixed(1)}M` : Math.abs(n) >= 1e3 ? `$${(n/1e3).toFixed(1)}K` : `$${n.toFixed(0)}`;
const fmtPct = (n) => n == null ? '—' : `${n >= 0 ? '+' : ''}${n.toFixed(2)}%`;
const pnlCl = (v) => v == null ? 'text-slate-500' : v >= 0 ? 'text-emerald-400' : 'text-rose-400';
const pnlBg = (v) => v == null ? 'bg-slate-800' : v >= 0 ? 'bg-emerald-500/10' : 'bg-rose-500/10';

// --- MINI COMPONENTS ---
const Pill = ({ children, color = 'slate' }) => {
  const cls = { emerald: 'bg-emerald-500/15 text-emerald-400', rose: 'bg-rose-500/15 text-rose-400', blue: 'bg-blue-500/15 text-blue-400', amber: 'bg-amber-500/15 text-amber-400', slate: 'bg-slate-700/50 text-slate-400', violet: 'bg-violet-500/15 text-violet-400' };
  return <span className={`px-1.5 py-0.5 rounded text-[10px] font-bold uppercase ${cls[color] || cls.slate}`}>{children}</span>;
};

const Dot = ({ on }) => <span className={`inline-block w-1.5 h-1.5 rounded-full ${on ? 'bg-emerald-400 animate-pulse' : 'bg-rose-500'}`} />;

const MiniBar = ({ value, max = 100, color = 'blue' }) => {
  const pct = Math.min(100, Math.max(0, (value / max) * 100));
  const c = { blue: 'bg-blue-500', emerald: 'bg-emerald-500', rose: 'bg-rose-500', amber: 'bg-amber-500' };
  return (
    <div className="w-full h-1 bg-slate-800 rounded-full overflow-hidden">
      <div className={`h-full rounded-full ${c[color] || c.blue}`} style={{ width: `${pct}%` }} />
    </div>
  );
};

const SparkBars = ({ data = [], height = 24 }) => {
  if (!data.length) return <div className="h-6 text-[10px] text-slate-600 flex items-center">No data</div>;
  const mx = Math.max(...data.map(d => Math.abs(d)), 1);
  return (
    <div className="flex items-end gap-px" style={{ height }}>
      {data.map((v, i) => (
        <div key={i} className={`flex-1 rounded-t ${v >= 0 ? 'bg-emerald-500' : 'bg-rose-500'}`}
          style={{ height: `${Math.max(8, (Math.abs(v) / mx) * 100)}%`, minWidth: 3 }}
          title={`$${v.toFixed(0)}`} />
      ))}
    </div>
  );
};

// --- KPI CARD ---
const KPI = ({ label, value, sub, positive }) => (
  <div className="px-3 py-2 bg-slate-900/60 rounded-lg border border-white/5 min-w-0">
    <div className="text-[9px] text-slate-500 uppercase tracking-wider truncate">{label}</div>
    <div className="text-base font-bold text-white font-mono leading-tight mt-0.5">{value}</div>
    {sub && <div className={`text-[10px] mt-0.5 ${positive != null ? (positive ? 'text-emerald-400' : 'text-rose-400') : 'text-slate-500'}`}>{sub}</div>}
  </div>
);

// =============================================================================
// STRATEGY ROW — Compact card for each strategy
// =============================================================================
const StrategyRow = ({ s, onDeploy, onViewDetail }) => {
  const wr = s.live_win_rate ?? s.backtest_win_rate;
  const wrColor = wr > 60 ? 'emerald' : wr > 45 ? 'amber' : 'rose';
  const sig = s.current_signal;

  return (
    <div className="grid grid-cols-12 gap-2 items-center px-3 py-2 hover:bg-white/[0.02] border-b border-white/5 text-xs cursor-pointer"
      onClick={() => onViewDetail?.(s)}>
      {/* Name + Asset */}
      <div className="col-span-3 min-w-0">
        <div className="font-bold text-white truncate">{s.strategy_name || s.strategy_id}</div>
        <div className="text-[10px] text-slate-500">{s.asset_class || '—'}</div>
      </div>
      {/* Win Rate */}
      <div className="col-span-1 text-right">
        <span className={`font-mono font-bold ${pnlCl(wr - 50)}`}>{wr != null ? `${wr.toFixed(0)}%` : '—'}</span>
      </div>
      {/* Sharpe */}
      <div className="col-span-1 text-right font-mono text-slate-300">{s.sharpe_ratio ? s.sharpe_ratio.toFixed(2) : '—'}</div>
      {/* Live Trades */}
      <div className="col-span-1 text-right font-mono text-slate-400">{s.live_trades || 0}</div>
      {/* Returns */}
      <div className="col-span-1 text-right">
        <span className={`font-mono font-bold ${pnlCl(s.returns)}`}>{s.returns != null ? fmtPct(s.returns) : '—'}</span>
      </div>
      {/* Backtest WR */}
      <div className="col-span-1 text-right text-slate-500 font-mono">{s.backtest_win_rate != null ? `${s.backtest_win_rate.toFixed(0)}%` : '—'}</div>
      {/* Signal */}
      <div className="col-span-2 text-center">
        {sig ? (
          <div className="flex items-center gap-1 justify-center">
            <Pill color={sig.action === 'BUY' ? 'emerald' : sig.action === 'SELL' ? 'rose' : 'slate'}>{sig.action}</Pill>
            <span className="text-[10px] text-slate-500 font-mono">{sig.ticker}</span>
          </div>
        ) : <span className="text-slate-600">—</span>}
      </div>
      {/* Deploy */}
      <div className="col-span-2 text-right">
        <button onClick={e => { e.stopPropagation(); onDeploy?.(s); }}
          className="px-2 py-1 bg-blue-600 hover:bg-blue-500 text-[10px] font-bold rounded transition-colors">
          Deploy
        </button>
      </div>
    </div>
  );
};

// =============================================================================
// POSITION TABLE — Live positions with P&L
// =============================================================================
const PositionTable = ({ positions = [], onClose }) => (
  <div className="overflow-x-auto">
    <table className="w-full text-xs">
      <thead>
        <tr className="text-[9px] text-slate-500 uppercase tracking-wider border-b border-white/10">
          <th className="text-left py-1.5 px-2">Ticker</th>
          <th className="text-left py-1.5 px-2">Strategy</th>
          <th className="text-right py-1.5 px-2">Entry</th>
          <th className="text-right py-1.5 px-2">Current</th>
          <th className="text-right py-1.5 px-2">Qty</th>
          <th className="text-right py-1.5 px-2">Unrealized</th>
          <th className="text-right py-1.5 px-2">%</th>
          <th className="text-right py-1.5 px-2">Days</th>
          <th className="text-center py-1.5 px-2"></th>
        </tr>
      </thead>
      <tbody>
        {positions.map((p, i) => {
          const pnlPct = p.entry_price > 0 ? ((p.current_price - p.entry_price) / p.entry_price * 100) : 0;
          const unrealized = (p.current_price - p.entry_price) * (p.quantity || 0);
          return (
            <tr key={p.position_id || i} className="border-b border-white/5 hover:bg-white/[0.02]">
              <td className="py-1.5 px-2 font-bold text-white">{p.ticker}</td>
              <td className="py-1.5 px-2 text-slate-400 truncate max-w-[100px]">{p.strategy_name || p.strategy_id || '—'}</td>
              <td className="py-1.5 px-2 text-right font-mono text-slate-400">${fmt(p.entry_price)}</td>
              <td className="py-1.5 px-2 text-right font-mono text-white">${fmt(p.current_price)}</td>
              <td className="py-1.5 px-2 text-right font-mono text-slate-400">{fmt(p.quantity, 0)}</td>
              <td className={`py-1.5 px-2 text-right font-mono font-bold ${pnlCl(unrealized)}`}>{fmtK(unrealized)}</td>
              <td className={`py-1.5 px-2 text-right font-mono ${pnlCl(pnlPct)}`}>{fmtPct(pnlPct)}</td>
              <td className="py-1.5 px-2 text-right font-mono text-slate-500">{p.holding_days ?? '—'}</td>
              <td className="py-1.5 px-2 text-center">
                <button onClick={() => onClose?.(p.position_id, p.ticker)}
                  className="px-1.5 py-0.5 bg-rose-600/20 hover:bg-rose-600 text-rose-400 hover:text-white text-[9px] font-bold rounded transition-all">
                  ✕
                </button>
              </td>
            </tr>
          );
        })}
        {!positions.length && (
          <tr><td colSpan={9} className="py-6 text-center text-slate-600">No positions</td></tr>
        )}
      </tbody>
    </table>
  </div>
);

// =============================================================================
// P&L SUMMARY — Daily / Weekly / Monthly breakdown
// =============================================================================
const PnLSummary = ({ dailyPnl = [], trades = [] }) => {
  // Group by week and month
  const today = new Date();
  const weekAgo = new Date(today); weekAgo.setDate(weekAgo.getDate() - 7);
  const monthAgo = new Date(today); monthAgo.setDate(monthAgo.getDate() - 30);

  const todayPnl = dailyPnl.find(d => d.date === today.toISOString().slice(0, 10))?.pnl || 0;
  const weekPnl = dailyPnl.filter(d => new Date(d.date) >= weekAgo).reduce((s, d) => s + (d.pnl || 0), 0);
  const monthPnl = dailyPnl.filter(d => new Date(d.date) >= monthAgo).reduce((s, d) => s + (d.pnl || 0), 0);
  const totalRealized = trades.reduce((s, t) => s + (t.pnl || 0), 0);

  return (
    <div className="grid grid-cols-4 gap-2">
      <div className={`rounded-lg px-2.5 py-2 ${pnlBg(todayPnl)} border border-white/5`}>
        <div className="text-[9px] text-slate-500 uppercase">Today</div>
        <div className={`text-sm font-bold font-mono ${pnlCl(todayPnl)}`}>{fmtK(todayPnl)}</div>
      </div>
      <div className={`rounded-lg px-2.5 py-2 ${pnlBg(weekPnl)} border border-white/5`}>
        <div className="text-[9px] text-slate-500 uppercase">This Week</div>
        <div className={`text-sm font-bold font-mono ${pnlCl(weekPnl)}`}>{fmtK(weekPnl)}</div>
      </div>
      <div className={`rounded-lg px-2.5 py-2 ${pnlBg(monthPnl)} border border-white/5`}>
        <div className="text-[9px] text-slate-500 uppercase">This Month</div>
        <div className={`text-sm font-bold font-mono ${pnlCl(monthPnl)}`}>{fmtK(monthPnl)}</div>
      </div>
      <div className={`rounded-lg px-2.5 py-2 ${pnlBg(totalRealized)} border border-white/5`}>
        <div className="text-[9px] text-slate-500 uppercase">Realized</div>
        <div className={`text-sm font-bold font-mono ${pnlCl(totalRealized)}`}>{fmtK(totalRealized)}</div>
      </div>
    </div>
  );
};

// =============================================================================
// STRATEGY DETAIL PANEL — Slide-out detail view
// =============================================================================
const StrategyDetail = ({ strategy, onClose }) => {
  const [detail, setDetail] = useState(null);
  const [positions, setPositions] = useState([]);
  const [dailyPnl, setDailyPnl] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!strategy) return;
    const sid = encodeURIComponent(strategy.strategy_id);
    Promise.all([
      fetch(`/api/strategies/${sid}`).then(r => r.json()).catch(() => null),
      fetch(`/api/paper-strategies/${sid}/daily-pnl?days=30`).then(r => r.json()).catch(() => null),
      fetch(`/api/portfolio/positions`).then(r => r.json()).catch(() => []),
    ]).then(([det, pnl, pos]) => {
      setDetail(det);
      setDailyPnl(pnl?.daily || []);
      const allPos = Array.isArray(pos) ? pos : (pos?.positions || pos || []);
      setPositions(allPos.filter(p => p.strategy_id === strategy.strategy_id));
      setLoading(false);
    });
  }, [strategy]);

  if (!strategy) return null;

  return (
    <div className="fixed inset-0 z-50 flex">
      <div className="flex-1 bg-black/60" onClick={onClose} />
      <div className="w-full max-w-lg bg-slate-950 border-l border-white/10 overflow-y-auto">
        <div className="sticky top-0 bg-slate-950/95 backdrop-blur border-b border-white/10 p-3 flex items-center justify-between">
          <div>
            <h3 className="text-sm font-bold text-white">{strategy.strategy_name || strategy.strategy_id}</h3>
            <div className="flex items-center gap-2 mt-0.5">
              <Pill color="blue">{strategy.asset_class || '—'}</Pill>
              <Pill>{strategy.direction || '—'}</Pill>
            </div>
          </div>
          <button onClick={onClose} className="text-slate-400 hover:text-white p-1">✕</button>
        </div>

        {loading ? (
          <div className="p-8 text-center text-slate-500">Loading...</div>
        ) : (
          <div className="p-3 space-y-4">
            {/* Description */}
            {detail?.description && (
              <p className="text-xs text-slate-400 leading-relaxed">{detail.description}</p>
            )}

            {/* Key Metrics */}
            <div className="grid grid-cols-3 gap-2">
              <KPI label="Win Rate" value={strategy.live_win_rate != null ? `${strategy.live_win_rate.toFixed(0)}%` : '—'} sub={strategy.backtest_win_rate != null ? `BT: ${strategy.backtest_win_rate.toFixed(0)}%` : undefined} />
              <KPI label="Sharpe" value={strategy.sharpe_ratio?.toFixed(2) || '—'} />
              <KPI label="Returns" value={fmtPct(strategy.returns)} positive={strategy.returns >= 0} />
            </div>

            {/* Signal Logic */}
            {detail?.signal_logic && (
              <div className="bg-slate-900/50 rounded-lg p-3 border border-white/5">
                <div className="text-[9px] text-slate-500 uppercase mb-1">Buy Signal</div>
                <div className="text-xs text-emerald-400">{detail.signal_logic}</div>
                {detail?.exit_logic && (
                  <>
                    <div className="text-[9px] text-slate-500 uppercase mt-2 mb-1">Exit Logic</div>
                    <div className="text-xs text-rose-400">{detail.exit_logic}</div>
                  </>
                )}
              </div>
            )}

            {/* P&L Trend */}
            <div className="bg-slate-900/50 rounded-lg p-3 border border-white/5">
              <div className="text-[9px] text-slate-500 uppercase mb-2">Daily P&L (30D)</div>
              <SparkBars data={dailyPnl.map(d => d.total_pnl || d.pnl || 0)} height={40} />
            </div>

            {/* Active Positions */}
            <div>
              <div className="text-[9px] text-slate-500 uppercase mb-1">Active Positions ({positions.length})</div>
              <PositionTable positions={positions} />
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

// =============================================================================
// DEPLOY MODAL — Quick deploy strategy
// =============================================================================
const DeployModal = ({ strategy, onClose, onDone }) => {
  const [tickers, setTickers] = useState('');
  const [pool, setPool] = useState(100000);
  const [deploying, setDeploying] = useState(false);
  const [result, setResult] = useState(null);

  if (!strategy) return null;

  const handleDeploy = async () => {
    setDeploying(true);
    try {
      const tickerList = tickers.split(',').map(t => t.trim().toUpperCase()).filter(Boolean);
      const res = await fetch('/api/strategies/deploy-with-pool', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ strategy_id: strategy.strategy_id, tickers: tickerList, total_pool: pool })
      });
      const data = await res.json();
      setResult(data);
      if (data.success) setTimeout(() => { onDone?.(); onClose(); }, 1500);
    } catch (e) { setResult({ success: false, error: e.message }); }
    finally { setDeploying(false); }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60" onClick={onClose}>
      <div className="bg-slate-900 border border-white/10 rounded-xl p-4 w-full max-w-md" onClick={e => e.stopPropagation()}>
        <h3 className="text-sm font-bold text-white mb-1">Deploy: {strategy.strategy_name || strategy.strategy_id}</h3>
        <p className="text-[10px] text-slate-500 mb-3">{strategy.asset_class} • Sharpe {strategy.sharpe_ratio?.toFixed(2)} • WR {strategy.backtest_win_rate?.toFixed(0)}%</p>

        <label className="text-[10px] text-slate-400 uppercase">Tickers (comma separated)</label>
        <input value={tickers} onChange={e => setTickers(e.target.value)} placeholder="AAPL, MSFT, GOOGL"
          className="w-full mt-1 mb-3 px-3 py-2 bg-slate-800 border border-white/10 rounded-lg text-xs text-white placeholder-slate-600 focus:border-blue-500/50 focus:outline-none" />

        <label className="text-[10px] text-slate-400 uppercase">Capital Pool</label>
        <div className="flex gap-2 mt-1 mb-3">
          {[50000, 100000, 250000, 500000].map(v => (
            <button key={v} onClick={() => setPool(v)}
              className={`flex-1 py-1.5 text-[10px] font-bold rounded-lg border transition-all ${pool === v ? 'bg-blue-500 border-blue-500 text-white' : 'bg-slate-800 border-white/10 text-slate-400 hover:border-blue-500/50'}`}>
              {fmtK(v)}
            </button>
          ))}
        </div>

        {result && (
          <div className={`mb-3 p-2 rounded-lg text-xs ${result.success ? 'bg-emerald-500/10 text-emerald-400' : 'bg-rose-500/10 text-rose-400'}`}>
            {result.success ? `✓ Deployed ${result.positions_created} positions` : `✗ ${result.error}`}
          </div>
        )}

        <div className="flex gap-2">
          <button onClick={onClose} className="flex-1 py-2 bg-slate-800 text-slate-400 text-xs font-bold rounded-lg hover:bg-slate-700">Cancel</button>
          <button onClick={handleDeploy} disabled={deploying || !tickers}
            className="flex-1 py-2 bg-blue-600 hover:bg-blue-500 disabled:bg-slate-700 text-white text-xs font-bold rounded-lg transition-colors">
            {deploying ? 'Deploying...' : 'Deploy'}
          </button>
        </div>
      </div>
    </div>
  );
};

// =============================================================================
// MAIN APP
// =============================================================================
function App() {
  const [view, setView] = useState('command'); // command | lab | portfolio
  const [data, setData] = useState({
    strategies: [], positions: [], paperStrategies: [],
    dailyPnl: [], trades: [], summary: {},
    mode: 'SIMULATION', ibStatus: {}
  });
  const [loading, setLoading] = useState(true);
  const [detailStrategy, setDetailStrategy] = useState(null);
  const [deployStrategy, setDeployStrategy] = useState(null);

  const fetchAll = useCallback(async () => {
    try {
      const [perf, positions, paper, pnl, trades, mode, ib] = await Promise.all([
        fetch('/api/performance/strategy').then(r => r.json()).catch(() => ({})),
        fetch('/api/portfolio/positions').then(r => r.json()).catch(() => []),
        fetch('/api/paper-strategies').then(r => r.json()).catch(() => ({})),
        fetch('/api/performance/daily-pnl?days=30').then(r => r.json()).catch(() => ({})),
        fetch('/api/velocity/trades').then(r => r.json()).catch(() => []),
        fetch('/api/execution/global-mode').then(r => r.json()).catch(() => ({})),
        fetch('/api/velocity/ib/status').then(r => r.json()).catch(() => ({})),
      ]);
      setData({
        strategies: perf.strategies || [],
        summary: perf.summary || {},
        positions: Array.isArray(positions) ? positions : [],
        paperStrategies: paper.strategies || [],
        dailyPnl: pnl.daily || [],
        trades: Array.isArray(trades) ? trades : [],
        mode: mode.execution_mode || 'SIMULATION',
        simCapital: mode.simulation_capital || 100000,
        simUsed: mode.simulation_used || 0,
        ibStatus: ib,
        ibBalance: mode.account_balance || mode.net_liquidation,
        monthlyReturns: perf.monthly_returns || [],
      });
    } catch (e) { console.error('Fetch error:', e); }
    finally { setLoading(false); }
  }, []);

  useEffect(() => { fetchAll(); const t = setInterval(fetchAll, 30000); return () => clearInterval(t); }, [fetchAll]);

  // Derived data
  const totalUnrealized = data.positions.reduce((s, p) => s + (p.unrealized_pnl || 0), 0);
  const totalRealized = data.trades.reduce((s, t) => s + (t.pnl || 0), 0);
  const activeStrategies = data.strategies.filter(s => s.live_trades > 0).length;
  const portfolioValue = data.ibBalance || data.simCapital || 0;
  const isConnected = data.ibStatus?.socket === 'Connected' || data.ibStatus?.status === 'Connected';
  const modeColor = data.mode === 'LIVE_TRADING' ? 'rose' : data.mode === 'PAPER_TRADING' ? 'blue' : 'amber';

  // --- NAV ITEMS ---
  const navItems = [
    { id: 'command', icon: '⚡', label: 'Command' },
    { id: 'lab', icon: '🧪', label: 'Lab' },
    { id: 'portfolio', icon: '📊', label: 'Portfolio' },
  ];

  if (loading) return (
    <div className="min-h-screen bg-slate-950 flex items-center justify-center">
      <div className="text-slate-500 flex items-center gap-2">
        <div className="w-4 h-4 border-2 border-slate-600 border-t-blue-500 rounded-full animate-spin" />
        <span className="text-xs">Loading platform...</span>
      </div>
    </div>
  );

  // =============================================================================
  // COMMAND CENTER VIEW
  // =============================================================================
  const CommandView = () => (
    <div className="space-y-3">
      {/* KPI Strip */}
      <div className="grid grid-cols-2 md:grid-cols-6 gap-2">
        <KPI label="Portfolio" value={fmtK(portfolioValue)} sub={data.mode} />
        <KPI label="Unrealized P&L" value={fmtK(totalUnrealized)} sub={fmtPct(portfolioValue > 0 ? totalUnrealized / portfolioValue * 100 : 0)} positive={totalUnrealized >= 0} />
        <KPI label="Realized P&L" value={fmtK(totalRealized)} positive={totalRealized >= 0} />
        <KPI label="Active Strategies" value={activeStrategies} sub={`of ${data.strategies.length}`} />
        <KPI label="Win Rate" value={data.summary.win_rate != null ? `${data.summary.win_rate.toFixed(0)}%` : '—'} />
        <KPI label="Sharpe" value={data.summary.sharpe?.toFixed(2) || '—'} />
      </div>

      {/* P&L Breakdown */}
      <PnLSummary dailyPnl={data.dailyPnl} trades={data.trades} />

      {/* P&L Chart + Strategies split */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-3">
        {/* P&L Trend */}
        <div className="bg-slate-900/50 rounded-lg border border-white/5 p-3">
          <div className="text-[9px] text-slate-500 uppercase mb-2">30-Day P&L Trend</div>
          <SparkBars data={data.dailyPnl.map(d => d.pnl || 0)} height={80} />
          <div className="flex justify-between text-[9px] text-slate-600 mt-1">
            <span>{data.dailyPnl[0]?.date?.slice(5) || ''}</span>
            <span>Today</span>
          </div>
        </div>

        {/* Strategies Table */}
        <div className="lg:col-span-2 bg-slate-900/50 rounded-lg border border-white/5 overflow-hidden">
          <div className="px-3 py-2 border-b border-white/5 flex items-center justify-between">
            <span className="text-[10px] text-slate-500 uppercase font-bold tracking-wider">Strategy Performance</span>
            <span className="text-[10px] text-slate-600">{data.strategies.length} strategies</span>
          </div>
          {/* Header */}
          <div className="grid grid-cols-12 gap-2 px-3 py-1.5 text-[9px] text-slate-500 uppercase tracking-wider border-b border-white/10">
            <div className="col-span-3">Strategy</div>
            <div className="col-span-1 text-right">WR</div>
            <div className="col-span-1 text-right">Sharpe</div>
            <div className="col-span-1 text-right">Trades</div>
            <div className="col-span-1 text-right">Return</div>
            <div className="col-span-1 text-right">BT WR</div>
            <div className="col-span-2 text-center">Signal</div>
            <div className="col-span-2 text-right">Action</div>
          </div>
          <div className="max-h-[300px] overflow-y-auto">
            {data.strategies.map((s, i) => (
              <StrategyRow key={s.strategy_id || i} s={s}
                onDeploy={setDeployStrategy} onViewDetail={setDetailStrategy} />
            ))}
            {!data.strategies.length && (
              <div className="py-8 text-center text-slate-600 text-xs">No strategies loaded</div>
            )}
          </div>
        </div>
      </div>

      {/* Active Positions */}
      <div className="bg-slate-900/50 rounded-lg border border-white/5 overflow-hidden">
        <div className="px-3 py-2 border-b border-white/5 flex items-center justify-between">
          <span className="text-[10px] text-slate-500 uppercase font-bold tracking-wider">
            Live Positions ({data.positions.length})
          </span>
          <div className="flex items-center gap-2">
            <Dot on={isConnected} />
            <span className="text-[10px] text-slate-500">IBKR {isConnected ? 'Connected' : 'Offline'}</span>
          </div>
        </div>
        <PositionTable positions={data.positions} onClose={async (id, ticker) => {
          if (!confirm(`Close ${ticker}?`)) return;
          await fetch(`/api/positions/${id}/close`, { method: 'POST' });
          fetchAll();
        }} />
      </div>
    </div>
  );

  // =============================================================================
  // STRATEGY LAB VIEW — Pre-deploy analysis
  // =============================================================================
  const LabView = () => {
    const [researchers, setResearchers] = useState([]);
    const [loadingR, setLoadingR] = useState(true);

    useEffect(() => {
      fetch('/api/strategies/researcher')
        .then(r => r.json())
        .then(d => setResearchers(d.strategies || []))
        .catch(() => {})
        .finally(() => setLoadingR(false));
    }, []);

    return (
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-sm font-bold text-white">Strategy Lab</h2>
            <p className="text-[10px] text-slate-500">Review backtests and signals before deploying</p>
          </div>
        </div>

        {/* Researcher Strategies — Ready to Deploy */}
        <div className="bg-slate-900/50 rounded-lg border border-white/5 overflow-hidden">
          <div className="px-3 py-2 border-b border-white/5">
            <span className="text-[10px] text-slate-500 uppercase font-bold tracking-wider">JT-Ready Strategies</span>
          </div>
          {loadingR ? (
            <div className="py-6 text-center text-slate-600 text-xs">Loading...</div>
          ) : (
            <div className="divide-y divide-white/5">
              {researchers.map((s, i) => (
                <div key={s.id || i} className="grid grid-cols-12 gap-2 items-center px-3 py-2 hover:bg-white/[0.02] text-xs">
                  <div className="col-span-3 min-w-0">
                    <div className="font-bold text-white truncate">{s.name}</div>
                    <div className="text-[10px] text-slate-500">{s.asset_class} • {s.direction} • {s.time_horizon}</div>
                  </div>
                  <div className="col-span-1 text-right">
                    <span className={`font-mono font-bold ${pnlCl((s.win_rate || 0) * 100 - 50)}`}>
                      {((s.win_rate || 0) * 100).toFixed(0)}%
                    </span>
                    <div className="text-[9px] text-slate-600">WR</div>
                  </div>
                  <div className="col-span-1 text-right font-mono text-slate-300">
                    {s.sharpe_ratio?.toFixed(2) || '—'}
                    <div className="text-[9px] text-slate-600">Sharpe</div>
                  </div>
                  <div className="col-span-1 text-right font-mono text-slate-400">
                    {s.max_drawdown ? `${(s.max_drawdown * 100).toFixed(0)}%` : '—'}
                    <div className="text-[9px] text-slate-600">MaxDD</div>
                  </div>
                  <div className="col-span-3">
                    <div className="text-[10px] text-slate-400 truncate">{s.description?.slice(0, 80)}</div>
                    <div className="text-[10px] text-slate-600">{s.universe_count || 0} tickers</div>
                  </div>
                  <div className="col-span-1 text-center">
                    <Pill color={s.status === 'active' ? 'emerald' : 'slate'}>{s.status || 'ready'}</Pill>
                  </div>
                  <div className="col-span-2 text-right">
                    <button onClick={() => setDeployStrategy(s)}
                      className="px-3 py-1 bg-emerald-600 hover:bg-emerald-500 text-[10px] font-bold rounded transition-colors">
                      Deploy →
                    </button>
                  </div>
                </div>
              ))}
              {!researchers.length && (
                <div className="py-8 text-center text-slate-600 text-xs">No researcher strategies found</div>
              )}
            </div>
          )}
        </div>

        {/* Backtest Comparison — Existing strategies */}
        <div className="bg-slate-900/50 rounded-lg border border-white/5 overflow-hidden">
          <div className="px-3 py-2 border-b border-white/5">
            <span className="text-[10px] text-slate-500 uppercase font-bold tracking-wider">Backtest vs Live Comparison</span>
          </div>
          <table className="w-full text-xs">
            <thead>
              <tr className="text-[9px] text-slate-500 uppercase tracking-wider border-b border-white/10">
                <th className="text-left py-1.5 px-3">Strategy</th>
                <th className="text-right py-1.5 px-3">BT Win Rate</th>
                <th className="text-right py-1.5 px-3">Live Win Rate</th>
                <th className="text-right py-1.5 px-3">Δ</th>
                <th className="text-right py-1.5 px-3">BT Return</th>
                <th className="text-right py-1.5 px-3">Live Return</th>
                <th className="text-right py-1.5 px-3">BT Trades</th>
                <th className="text-right py-1.5 px-3">Live Trades</th>
              </tr>
            </thead>
            <tbody>
              {data.strategies.map((s, i) => {
                const btWr = s.backtest_win_rate;
                const liveWr = s.live_win_rate;
                const delta = btWr != null && liveWr != null ? liveWr - btWr : null;
                return (
                  <tr key={i} className="border-b border-white/5 hover:bg-white/[0.02] cursor-pointer"
                    onClick={() => setDetailStrategy(s)}>
                    <td className="py-1.5 px-3 font-bold text-white">{s.strategy_name || s.strategy_id}</td>
                    <td className="py-1.5 px-3 text-right font-mono text-slate-400">{btWr != null ? `${btWr.toFixed(0)}%` : '—'}</td>
                    <td className={`py-1.5 px-3 text-right font-mono font-bold ${pnlCl(liveWr != null ? liveWr - 50 : null)}`}>{liveWr != null ? `${liveWr.toFixed(0)}%` : '—'}</td>
                    <td className={`py-1.5 px-3 text-right font-mono ${pnlCl(delta)}`}>{delta != null ? `${delta >= 0 ? '+' : ''}${delta.toFixed(0)}pp` : '—'}</td>
                    <td className="py-1.5 px-3 text-right font-mono text-slate-400">{s.backtest_return != null ? fmtPct(s.backtest_return) : '—'}</td>
                    <td className={`py-1.5 px-3 text-right font-mono font-bold ${pnlCl(s.returns)}`}>{s.returns != null ? fmtPct(s.returns) : '—'}</td>
                    <td className="py-1.5 px-3 text-right font-mono text-slate-500">{s.backtest_trades || 0}</td>
                    <td className="py-1.5 px-3 text-right font-mono text-slate-400">{s.live_trades || 0}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    );
  };

  // =============================================================================
  // PORTFOLIO VIEW — Post-deploy IBKR positions + P&L
  // =============================================================================
  const PortfolioView = () => {
    const [paperStrats, setPaperStrats] = useState([]);
    const [search, setSearch] = useState('');

    useEffect(() => {
      fetch('/api/paper-strategies').then(r => r.json()).then(d => setPaperStrats(d.strategies || [])).catch(() => {});
    }, []);

    const filtered = data.positions.filter(p => !search || p.ticker?.toLowerCase().includes(search.toLowerCase()));

    return (
      <div className="space-y-3">
        {/* Portfolio Summary */}
        <div className="grid grid-cols-2 md:grid-cols-5 gap-2">
          <KPI label="Portfolio Value" value={fmtK(portfolioValue)} />
          <KPI label="Unrealized" value={fmtK(totalUnrealized)} positive={totalUnrealized >= 0} />
          <KPI label="Realized" value={fmtK(totalRealized)} positive={totalRealized >= 0} />
          <KPI label="Positions" value={data.positions.length} />
          <KPI label="Mode" value={data.mode.replace('_', ' ')} />
        </div>

        {/* P&L Breakdown */}
        <PnLSummary dailyPnl={data.dailyPnl} trades={data.trades} />

        {/* Monthly Returns */}
        {data.monthlyReturns.length > 0 && (
          <div className="bg-slate-900/50 rounded-lg border border-white/5 p-3">
            <div className="text-[9px] text-slate-500 uppercase mb-2">Monthly Returns</div>
            <div className="grid grid-cols-6 md:grid-cols-12 gap-1">
              {data.monthlyReturns.slice(0, 12).map((m, i) => (
                <div key={i} className={`text-center rounded px-1 py-1.5 ${pnlBg(m.return)}`}>
                  <div className="text-[9px] text-slate-500">{['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'][m.month - 1]}</div>
                  <div className={`text-[10px] font-bold font-mono ${pnlCl(m.return)}`}>{m.return >= 0 ? '+' : ''}{m.return.toFixed(1)}%</div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Positions */}
        <div className="bg-slate-900/50 rounded-lg border border-white/5 overflow-hidden">
          <div className="px-3 py-2 border-b border-white/5 flex items-center justify-between">
            <span className="text-[10px] text-slate-500 uppercase font-bold tracking-wider">Positions</span>
            <input value={search} onChange={e => setSearch(e.target.value)} placeholder="Search ticker..."
              className="px-2 py-1 bg-slate-800 border border-white/10 rounded text-[10px] text-white placeholder-slate-600 focus:outline-none focus:border-blue-500/50 w-28" />
          </div>
          <PositionTable positions={filtered} onClose={async (id, ticker) => {
            if (!confirm(`Close ${ticker}?`)) return;
            await fetch(`/api/positions/${id}/close`, { method: 'POST' });
            fetchAll();
          }} />
        </div>

        {/* Paper Strategies by Strategy */}
        <div className="bg-slate-900/50 rounded-lg border border-white/5 overflow-hidden">
          <div className="px-3 py-2 border-b border-white/5">
            <span className="text-[10px] text-slate-500 uppercase font-bold tracking-wider">
              Paper Positions ({paperStrats.length}) — {data.mode}
            </span>
          </div>
          <div className="max-h-[400px] overflow-y-auto">
            <table className="w-full text-xs">
              <thead>
                <tr className="text-[9px] text-slate-500 uppercase tracking-wider border-b border-white/10">
                  <th className="text-left py-1.5 px-2">Ticker</th>
                  <th className="text-left py-1.5 px-2">Strategy</th>
                  <th className="text-right py-1.5 px-2">Capital</th>
                  <th className="text-right py-1.5 px-2">Invested</th>
                  <th className="text-right py-1.5 px-2">Unrealized</th>
                  <th className="text-right py-1.5 px-2">Realized</th>
                  <th className="text-right py-1.5 px-2">Trades</th>
                  <th className="text-center py-1.5 px-2">Status</th>
                </tr>
              </thead>
              <tbody>
                {paperStrats.map((ps, i) => (
                  <tr key={ps.id || i} className="border-b border-white/5 hover:bg-white/[0.02]">
                    <td className="py-1.5 px-2 font-bold text-white">{ps.ticker}</td>
                    <td className="py-1.5 px-2 text-slate-400 truncate max-w-[100px]">{ps.strategy_name || ps.strategy_id}</td>
                    <td className="py-1.5 px-2 text-right font-mono text-slate-400">{fmtK(ps.capital)}</td>
                    <td className="py-1.5 px-2 text-right font-mono text-white">{fmtK(ps.invested_capital)}</td>
                    <td className={`py-1.5 px-2 text-right font-mono font-bold ${pnlCl(ps.unrealized_pnl)}`}>{fmtK(ps.unrealized_pnl)}</td>
                    <td className={`py-1.5 px-2 text-right font-mono ${pnlCl(ps.realized_pnl)}`}>{fmtK(ps.realized_pnl)}</td>
                    <td className="py-1.5 px-2 text-right font-mono text-slate-500">{ps.trades_count || 0}</td>
                    <td className="py-1.5 px-2 text-center">
                      <Pill color={ps.status === 'ACTIVE' ? 'emerald' : 'slate'}>{ps.status}</Pill>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    );
  };

  // =============================================================================
  // RENDER
  // =============================================================================
  return (
    <div className="min-h-screen bg-slate-950 text-white font-sans">
      {/* Top Bar — Compact */}
      <header className="fixed top-0 left-0 right-0 z-40 border-b border-white/5 bg-slate-950/90 backdrop-blur-xl">
        <div className="flex items-center justify-between px-3 py-1.5 max-w-[1800px] mx-auto">
          {/* Left — Logo + Nav */}
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              <div className="w-6 h-6 rounded bg-gradient-to-br from-blue-500 to-violet-600 flex items-center justify-center text-[10px] font-black">JT</div>
              <span className="text-xs font-bold text-white hidden md:inline">JTCML</span>
            </div>
            <nav className="flex gap-1">
              {navItems.map(n => (
                <button key={n.id} onClick={() => setView(n.id)}
                  className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-bold transition-all ${view === n.id ? 'bg-white text-black' : 'text-slate-400 hover:text-white hover:bg-white/5'}`}>
                  <span>{n.icon}</span>
                  <span className="hidden md:inline">{n.label}</span>
                </button>
              ))}
            </nav>
          </div>

          {/* Right — Status */}
          <div className="flex items-center gap-3">
            <Pill color={modeColor}>{data.mode.replace('_TRADING', '').replace('_', ' ')}</Pill>
            <div className="flex items-center gap-1">
              <Dot on={isConnected} />
              <span className="text-[10px] text-slate-500 hidden sm:inline">IBKR</span>
            </div>
            <span className="text-[10px] text-slate-600 hidden md:inline">{new Date().toLocaleTimeString()}</span>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="pt-12 pb-4 px-3 max-w-[1800px] mx-auto">
        {view === 'command' && <CommandView />}
        {view === 'lab' && <LabView />}
        {view === 'portfolio' && <PortfolioView />}
      </main>

      {/* Modals */}
      {detailStrategy && <StrategyDetail strategy={detailStrategy} onClose={() => setDetailStrategy(null)} />}
      {deployStrategy && <DeployModal strategy={deployStrategy} onClose={() => setDeployStrategy(null)} onDone={fetchAll} />}

      {/* Footer */}
      <footer className="fixed bottom-0 left-0 right-0 border-t border-white/5 bg-slate-950/80 backdrop-blur py-1 px-3">
        <div className="flex items-center justify-between text-[9px] text-slate-600 max-w-[1800px] mx-auto">
          <span>v4.0 • Platform Mode</span>
          <span>JTCML Trading Systems</span>
        </div>
      </footer>
    </div>
  );
}

export default App;
