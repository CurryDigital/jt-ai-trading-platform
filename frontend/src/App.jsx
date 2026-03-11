import React, { useState, useEffect, useCallback } from 'react';
import { Routes, Route, useParams, useNavigate, useLocation } from 'react-router-dom';
import { MarketsTab } from './components/MarketsTab';
import { SettingsTab } from './components/SettingsTab';
import { StrategyLab } from './components/StrategyLab';

// =============================================================================
// JTCML TRADING PLATFORM v4.1 — COMPACT AUTO-TRADING DASHBOARD
// =============================================================================

// --- UTILS ---
const fmt = (n, d = 2) => n == null || isNaN(n) ? '—' : n.toLocaleString(undefined, { minimumFractionDigits: d, maximumFractionDigits: d });
const fmtK = (n) => n == null ? '—' : Math.abs(n) >= 1e6 ? `$${(n/1e6).toFixed(1)}M` : Math.abs(n) >= 1e3 ? `$${(n/1e3).toFixed(1)}K` : `$${n.toFixed(0)}`;
const fmtPct = (n) => n == null ? '—' : `${n >= 0 ? '+' : ''}${n.toFixed(2)}%`;
const pnlCl = (v) => v == null ? 'text-slate-500' : v >= 0 ? 'text-emerald-400' : 'text-rose-400';
const pnlBg = (v) => v == null ? 'bg-slate-800' : v >= 0 ? 'bg-emerald-500/10' : 'bg-rose-500/10';

// --- MOBILE COMPONENTS ---
const MobileBottomNav = ({ view, setView, navItems }) => (
  <nav className="bottom-nav md:hidden">
    <div className="flex items-center justify-around px-2 py-1">
      {navItems.slice(0, 5).map(n => (
        <button
          key={n.id}
          onClick={() => setView(n.id)}
          className={`flex flex-col items-center gap-0.5 px-3 py-1 rounded-lg transition-all ${
            view === n.id 
              ? 'text-blue-400' 
              : 'text-slate-500'
          }`}
        >
          <span className="text-lg">{n.icon}</span>
          <span className="text-[9px] font-medium">{n.label}</span>
        </button>
      ))}
    </div>
  </nav>
);

const MobilePositionCard = ({ p, onClose }) => {
  const pnlPct = p.entry_price > 0 ? ((p.current_price - p.entry_price) / p.entry_price * 100) : 0;
  const unrealized = (p.current_price - p.entry_price) * (p.quantity || 0);
  return (
    <div className="bg-slate-900/50 rounded-lg p-3 border border-white/5 mb-2">
      <div className="flex items-center justify-between mb-2">
        <div>
          <div className="font-bold text-white">{p.ticker}</div>
          <div className="text-[10px] text-slate-500">{p.strategy_name || p.strategy_id || '—'}</div>
        </div>
        <button
          onClick={() => onClose?.(p.position_id, p.ticker)}
          className="px-2 py-1 bg-rose-600/20 text-rose-400 text-[9px] font-bold rounded"
        >
          Close
        </button>
      </div>
      <div className="grid grid-cols-3 gap-2 text-xs">
        <div>
          <div className="text-[9px] text-slate-500">Entry</div>
          <div className="font-mono text-slate-400">${fmt(p.entry_price)}</div>
        </div>
        <div>
          <div className="text-[9px] text-slate-500">Current</div>
          <div className="font-mono text-white">${fmt(p.current_price)}</div>
        </div>
        <div>
          <div className="text-[9px] text-slate-500">Qty</div>
          <div className="font-mono text-slate-400">{fmt(p.quantity, 0)}</div>
        </div>
      </div>
      <div className="flex items-center justify-between mt-2 pt-2 border-t border-white/5">
        <div>
          <span className="text-[9px] text-slate-500 mr-1">P&L:</span>
          <span className={`font-mono font-bold ${pnlCl(unrealized)}`}>{fmtK(unrealized)}</span>
        </div>
        <div className={`font-mono ${pnlCl(pnlPct)}`}>{fmtPct(pnlPct)}</div>
      </div>
    </div>
  );
};

const MobileStrategyRow = ({ s, onDeploy, onViewDetail }) => {
  const wr = s.live_win_rate ?? s.backtest_win_rate;
  const sig = s.current_signal;
  return (
    <div className="bg-slate-900/50 rounded-lg p-3 border border-white/5 mb-2" onClick={() => onViewDetail?.(s)}>
      <div className="flex items-center justify-between mb-2">
        <div>
          <div className="font-bold text-white text-sm">{s.strategy_name || s.strategy_id}</div>
          <div className="text-[10px] text-slate-500">{s.asset_class || '—'}</div>
        </div>
        <button
          onClick={e => { e.stopPropagation(); onDeploy?.(s); }}
          className="px-3 py-1.5 bg-blue-600 text-white text-[10px] font-bold rounded"
        >
          Deploy
        </button>
      </div>
      <div className="grid grid-cols-4 gap-2 text-xs mb-2">
        <div className="text-center p-1.5 bg-slate-800/30 rounded">
          <div className="text-[9px] text-slate-500">WR</div>
          <div className={`font-mono font-bold ${pnlCl(wr != null ? wr - 50 : null)}`}>
            {wr != null ? `${wr.toFixed(0)}%` : '—'}
          </div>
        </div>
        <div className="text-center p-1.5 bg-slate-800/30 rounded">
          <div className="text-[9px] text-slate-500">Sharpe</div>
          <div className="font-mono text-slate-300">{s.sharpe_ratio ? s.sharpe_ratio.toFixed(2) : '—'}</div>
        </div>
        <div className="text-center p-1.5 bg-slate-800/30 rounded">
          <div className="text-[9px] text-slate-500">Trades</div>
          <div className="font-mono text-slate-300">{s.live_trades || 0}</div>
        </div>
        <div className="text-center p-1.5 bg-slate-800/30 rounded">
          <div className="text-[9px] text-slate-500">Return</div>
          <div className={`font-mono font-bold ${pnlCl(s.returns)}`}>
            {s.returns != null ? fmtPct(s.returns) : '—'}
          </div>
        </div>
      </div>
      {sig && (
        <div className="flex items-center gap-2 pt-2 border-t border-white/5">
          <span className="text-[10px] text-slate-500">Signal:</span>
          <Pill color={sig.action === 'BUY' ? 'emerald' : sig.action === 'SELL' ? 'rose' : 'slate'}>{sig.action}</Pill>
          <span className="text-[10px] text-slate-500 font-mono">{sig.ticker}</span>
        </div>
      )}
    </div>
  );
};
const Pill = ({ children, color = 'slate' }) => {
  const cls = { emerald: 'bg-emerald-500/15 text-emerald-400', rose: 'bg-rose-500/15 text-rose-400', blue: 'bg-blue-500/15 text-blue-400', amber: 'bg-amber-500/15 text-amber-400', slate: 'bg-slate-700/50 text-slate-400', violet: 'bg-violet-500/15 text-violet-400' };
  return <span className={`px-1.5 py-0.5 rounded text-[10px] font-bold uppercase ${cls[color] || cls.slate}`}>{children}</span>;
};

const Dot = ({ on }) => <span className={`inline-block w-1.5 h-1.5 rounded-full ${on ? 'bg-emerald-400 animate-pulse' : 'bg-rose-500'}`} />;

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
  const sig = s.current_signal;

  return (
    <div className="grid grid-cols-12 gap-2 items-center px-3 py-2 hover:bg-white/[0.02] border-b border-white/5 text-xs cursor-pointer"
      onClick={() => onViewDetail?.(s)}>
      <div className="col-span-3 min-w-0">
        <div className="font-bold text-white truncate">{s.strategy_name || s.strategy_id}</div>
        <div className="text-[10px] text-slate-500">{s.asset_class || '—'}</div>
      </div>
      <div className="col-span-1 text-right">
        <span className={`font-mono font-bold ${pnlCl(wr != null ? wr - 50 : null)}`}>{wr != null ? `${wr.toFixed(0)}%` : '—'}</span>
      </div>
      <div className="col-span-1 text-right font-mono text-slate-300">{s.sharpe_ratio ? s.sharpe_ratio.toFixed(2) : '—'}</div>
      <div className="col-span-1 text-right font-mono text-slate-400">{s.live_trades || 0}</div>
      <div className="col-span-1 text-right">
        <span className={`font-mono font-bold ${pnlCl(s.returns)}`}>{s.returns != null ? fmtPct(s.returns) : '—'}</span>
      </div>
      <div className="col-span-1 text-right text-slate-500 font-mono">{s.backtest_win_rate != null ? `${s.backtest_win_rate.toFixed(0)}%` : '—'}</div>
      <div className="col-span-2 text-center">
        {sig ? (
          <div className="flex items-center gap-1 justify-center">
            <Pill color={sig.action === 'BUY' ? 'emerald' : sig.action === 'SELL' ? 'rose' : 'slate'}>{sig.action}</Pill>
            <span className="text-[10px] text-slate-500 font-mono">{sig.ticker}</span>
          </div>
        ) : <span className="text-slate-600">—</span>}
      </div>
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
// POSITION TABLE — Live positions with P&L (Responsive: cards on mobile)
// =============================================================================
const PositionTable = ({ positions = [], onClose }) => (
  <div className="overflow-x-auto">
    {/* Desktop Table */}
    <table className="w-full text-xs hidden md:table">
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
    
    {/* Mobile Cards */}
    <div className="md:hidden">
      {positions.map((p, i) => (
        <MobilePositionCard key={p.position_id || i} p={p} onClose={onClose} />
      ))}
      {!positions.length && (
        <div className="py-6 text-center text-slate-600 text-xs">No positions</div>
      )}
    </div>
  </div>
);

// =============================================================================
// P&L SUMMARY — Daily / Weekly / Monthly breakdown
// =============================================================================
const PnLSummary = ({ dailyPnl = [], trades = [] }) => {
  const today = new Date();
  const weekAgo = new Date(today); weekAgo.setDate(weekAgo.getDate() - 7);
  const monthAgo = new Date(today); monthAgo.setDate(monthAgo.getDate() - 30);

  const todayPnl = dailyPnl.find(d => d.date === today.toISOString().slice(0, 10))?.pnl || 0;
  const weekPnl = dailyPnl.filter(d => new Date(d.date) >= weekAgo).reduce((s, d) => s + (d.pnl || 0), 0);
  const monthPnl = dailyPnl.filter(d => new Date(d.date) >= monthAgo).reduce((s, d) => s + (d.pnl || 0), 0);
  const totalRealized = trades.reduce((s, t) => s + (t.pnl || 0), 0);

  return (
    <>
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
    </>
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
            {detail?.description && (
              <p className="text-xs text-slate-400 leading-relaxed">{detail.description}</p>
            )}

            <div className="grid grid-cols-3 gap-2">
              <KPI label="Win Rate" value={strategy.live_win_rate != null ? `${strategy.live_win_rate.toFixed(0)}%` : '—'} sub={strategy.backtest_win_rate != null ? `BT: ${strategy.backtest_win_rate.toFixed(0)}%` : undefined} />
              <KPI label="Sharpe" value={strategy.sharpe_ratio?.toFixed(2) || '—'} />
              <KPI label="Returns" value={fmtPct(strategy.returns)} positive={strategy.returns >= 0} />
            </div>

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

            <div className="bg-slate-900/50 rounded-lg p-3 border border-white/5">
              <div className="text-[9px] text-slate-500 uppercase mb-2">Daily P&L (30D)</div>
              <SparkBars data={dailyPnl.map(d => d.total_pnl || d.pnl || 0)} height={40} />
            </div>

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
// DEPLOY MODAL
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
// MAIN APP - URL Based Routing
// =============================================================================
function App() {
  const navigate = useNavigate();
  const location = useLocation();
  const { mode: urlMode, tab: urlTab } = useParams();
  
  const [data, setData] = useState({
    strategies: [], positions: [], paperStrategies: [],
    dailyPnl: [], trades: [], summary: {},
    mode: 'SIMULATION', ibStatus: {}
  });
  const [loading, setLoading] = useState(true);
  const [detailStrategy, setDetailStrategy] = useState(null);
  const [deployStrategy, setDeployStrategy] = useState(null);
  const [tickerModal, setTickerModal] = useState(null);

  // Derive current view from URL or default
  const pathParts = location.pathname.split('/').filter(Boolean);
  const currentMode = pathParts[0] || 'sim'; // 'paper' or 'sim'
  const currentTab = pathParts[1] || 'command'; // 'command', 'lab', 'portfolio', etc.

  // Sync URL mode with backend mode on load
  useEffect(() => {
    const syncMode = async () => {
      try {
        const res = await fetch('/api/execution/global-mode');
        const modeData = await res.json();
        const backendMode = modeData.execution_mode || 'SIMULATION';
        
        // Determine what mode the URL represents
        const urlRepresentsMode = currentMode === 'paper' ? 'PAPER_TRADING' : 'SIMULATION';
        
        // If mismatch, switch backend mode to match URL
        if (backendMode !== urlRepresentsMode && urlRepresentsMode !== 'SIMULATION') {
          await fetch('/api/execution/global-mode', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ mode: urlRepresentsMode })
          });
        }
      } catch (e) {
        console.error('Mode sync error:', e);
      }
    };
    syncMode();
  }, [currentMode]);

    fetchData();
    const interval = setInterval(fetchData, 60000); // Refresh every 60s
    return () => clearInterval(interval);
  }, []);

  // --- TAB CONFIGURATION ---
  const tabs = [
    { id: 'dashboard', label: 'Dashboard', icon: Icons.Dashboard },
    { id: 'strategies', label: 'Strategies', icon: Icons.Strategies },
    { id: 'lab', label: 'Lab', icon: Icons.Chart },
    { id: 'research', label: 'Research', icon: Icons.Research },
    { id: 'performance', label: 'Performance', icon: Icons.Performance },
    { id: 'portfolio', label: 'Portfolio', icon: Icons.Portfolio },
    { id: 'markets', label: 'Markets', icon: Icons.Markets },
    { id: 'settings', label: 'Settings', icon: Icons.Settings },
  ];

  const handleTickerClick = (ticker) => {
    setTickerModal(ticker);
  };

  if (loading) return (
    <div className="min-h-screen bg-slate-950 flex items-center justify-center">
      <div className="text-slate-500 flex items-center gap-2">
        <div className="w-4 h-4 border-2 border-slate-600 border-t-blue-500 rounded-full animate-spin" />
        <span className="text-xs">Loading platform...</span>
      </div>
    </div>
  );

  // View components map
  const renderView = () => {
    switch (currentTab) {
      case 'strategies': return <LabView />;
      case 'performance': return <PerformanceView />;
      case 'portfolio': return <PortfolioView />;
      case 'markets': return <MarketsTab onTickerClick={handleTickerClick} />;
      case 'settings': return <SettingsTab />;
      case 'command':
      default: return <CommandView />;
    }
  };

  // =============================================================================
  // COMMAND CENTER VIEW
  // =============================================================================
  const CommandView = () => (
    <div className="space-y-3 pb-16 md:pb-0">
      {/* Execution Mode Toggle */}
      <GlobalExecutionToggle />

      {/* KPI Strip - Mobile: 2 cols, Desktop: 6 cols */}
      <div className="grid grid-cols-2 md:grid-cols-6 gap-2">
        <KPI label="Portfolio" value={fmtK(portfolioValue)} sub={data.mode.replace(/_/g, ' ')} />
        <KPI label="Unrealized P&L" value={fmtK(totalUnrealized)} sub={fmtPct(portfolioValue > 0 ? totalUnrealized / portfolioValue * 100 : 0)} positive={totalUnrealized >= 0} />
        <KPI label="Realized P&L" value={fmtK(totalRealized)} positive={totalRealized >= 0} />
        <KPI label="Active Strategies" value={activeStrategies} sub={`of ${data.strategies.length}`} />
        <KPI label="Win Rate" value={data.summary.win_rate != null ? `${data.summary.win_rate.toFixed(0)}%` : '—'} />
        <KPI label="Sharpe" value={data.summary.sharpe?.toFixed(2) || '—'} />
      </div>

      {/* P&L Breakdown - Mobile: 2 cols, Desktop: 4 cols */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
        <PnLSummary dailyPnl={data.dailyPnl} trades={data.trades} />
      </div>

      {/* P&L Chart + Strategies */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-3">
        <div className="bg-slate-900/50 rounded-lg border border-white/5 p-3">
          <div className="text-[9px] text-slate-500 uppercase mb-2">30-Day P&L Trend</div>
          <SparkBars data={data.dailyPnl.map(d => d.pnl || 0)} height={80} />
          <div className="flex justify-between text-[9px] text-slate-600 mt-1">
            <span>{data.dailyPnl[0]?.date?.slice(5) || ''}</span>
            <span>Today</span>
          </div>
        </div>

        <div className="lg:col-span-2 bg-slate-900/50 rounded-lg border border-white/5 overflow-hidden">
          <div className="px-3 py-2 border-b border-white/5 flex items-center justify-between">
            <span className="text-[10px] text-slate-500 uppercase font-bold tracking-wider">Strategy Performance</span>
            <span className="text-[10px] text-slate-600">{data.strategies.length} strategies</span>
          </div>
          
          {/* Desktop Header */}
          <div className="hidden md:grid grid-cols-12 gap-2 px-3 py-1.5 text-[9px] text-slate-500 uppercase tracking-wider border-b border-white/10">
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
            {/* Desktop Table Rows */}
            <div className="hidden md:block">
              {data.strategies.map((s, i) => (
                <StrategyRow key={s.strategy_id || i} s={s}
                  onDeploy={setDeployStrategy} onViewDetail={setDetailStrategy} />
              ))}
            </div>
            
            {/* Mobile Cards */}
            <div className="md:hidden p-2">
              {data.strategies.map((s, i) => (
                <MobileStrategyRow key={s.strategy_id || i} s={s}
                  onDeploy={setDeployStrategy} onViewDetail={setDetailStrategy} />
              ))}
            </div>
            
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
  // STRATEGY LAB VIEW - Simplified: Available + Deployed with Signals
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

    // Filter out already deployed strategies from available list
    // Handle both string and potential ID format differences
    const deployedIds = new Set(
      data.strategies
        .map(s => s.strategy_id)
        .filter(Boolean)
        .map(id => String(id).toUpperCase().trim())
    );
    
    const availableResearchers = researchers.filter(r => {
      const rid = String(r.id || r.strategy_id || '').toUpperCase().trim();
      const isDeployed = deployedIds.has(rid);
      return !isDeployed;
    });
    
    // Debug logging - remove after fix confirmed
    console.log('[LabView] Deployed IDs:', Array.from(deployedIds).slice(0, 10), `...(${deployedIds.size} total)`);
    console.log('[LabView] Available after filter:', availableResearchers.length, 'of', researchers.length);

    // Helper to get tier color
    const getTierColor = (tier) => {
      if (tier === 'T1' || tier === 1) return 'emerald';
      if (tier === 'T2' || tier === 2) return 'amber';
      if (tier === 'T3' || tier === 3) return 'blue';
      return 'slate';
    };

    const getTierLabel = (tier) => {
      if (tier === 'T1' || tier === 1) return 'T1';
      if (tier === 'T2' || tier === 2) return 'T2';
      if (tier === 'T3' || tier === 3) return 'T3';
      return 'T4';
    };

    return (
      <div className="space-y-4">
        {/* DEPLOYED STRATEGIES - All from performance endpoint */}
        <div className="bg-slate-900/50 rounded-lg border border-white/5 overflow-hidden">
          <div className="px-3 py-2 border-b border-white/5 flex items-center justify-between">
            <span className="text-xs font-bold text-white">🚀 Deployed Strategies</span>
            <span className="text-[10px] text-slate-500">{data.strategies.length} active</span>
          </div>
          
          {data.strategies.length === 0 ? (
            <div className="py-6 text-center text-slate-600 text-xs">No strategies deployed yet</div>
          ) : (
            <div className="divide-y divide-white/5">
              {data.strategies.map((s, i) => (
                <div key={s.strategy_id || i} className="p-3 hover:bg-white/[0.02]">
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-bold text-white">{s.strategy_name || s.strategy_id}</span>
                      <Pill color={getTierColor(s.tier)}>{getTierLabel(s.tier)}</Pill>
                      <span className="text-[10px] text-slate-500">{s.asset_class}</span>
                    </div>
                    <div className="flex items-center gap-2">
                      {s.current_signal && (
                        <Pill color={s.current_signal.action === 'BUY' ? 'emerald' : s.current_signal.action === 'SELL' ? 'rose' : 'slate'}>
                          {s.current_signal.action} {s.current_signal.ticker}
                        </Pill>
                      )}
                      <button 
                        onClick={() => setDetailStrategy(s)}
                        className="text-[10px] text-blue-400 hover:text-blue-300"
                      >
                        Details →
                      </button>
                    </div>
                  </div>
                  
                  {/* Tickers with signals */}
                  <div className="flex flex-wrap gap-1.5 mb-2">
                    {s.tickers?.map((t, idx) => (
                      <span 
                        key={idx} 
                        className={`px-2 py-0.5 rounded text-[10px] font-medium ${
                          t.signal === 'BUY' ? 'bg-emerald-500/20 text-emerald-400' :
                          t.signal === 'SELL' ? 'bg-rose-500/20 text-rose-400' :
                          'bg-slate-700 text-slate-400'
                        }`}
                      >
                        {t.ticker}
                        {t.signal && <span className="ml-1 opacity-70">{t.signal === 'BUY' ? '▲' : t.signal === 'SELL' ? '▼' : '—'}</span>}
                      </span>
                    )) || <span className="text-[10px] text-slate-600">No tickers assigned</span>}
                  </div>
                  
                  {/* Signal Preview - Same format as Available */}
                  <div className="pt-2 border-t border-white/5 text-[10px]">
                    <div className="flex gap-4">
                      <span className="text-emerald-400 truncate max-w-[200px]" title={s.buy_signal}>▲ {s.buy_signal?.slice(0, 30) || '—'}</span>
                      <span className="text-rose-400 truncate max-w-[200px]" title={s.sell_signal}>▼ {s.sell_signal?.slice(0, 30) || '—'}</span>
                    </div>
                  </div>
                  
                  {/* Quick stats */}
                  <div className="flex gap-4 mt-2 text-[10px] text-slate-500">
                    <span>Live Trades: <span className="text-slate-300">{s.live_trades || 0}</span></span>
                    <span>Win Rate: <span className={s.live_win_rate >= 50 ? 'text-emerald-400' : 'text-rose-400'}>{s.live_win_rate?.toFixed(0) || 0}%</span></span>
                    <span>Returns: <span className={s.returns >= 0 ? 'text-emerald-400' : 'text-rose-400'}>{fmtPct(s.returns)}</span></span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* AVAILABLE STRATEGIES - JT Ready to Deploy */}
        <div className="bg-slate-900/50 rounded-lg border border-white/5 overflow-hidden">
          <div className="px-3 py-2 border-b border-white/5 flex items-center justify-between">
            <div>
              <span className="text-xs font-bold text-white">📦 Available Strategies</span>
              <span className="text-[10px] text-slate-500 ml-2">JT-Ready ({availableResearchers.length})</span>
            </div>
            <div className="flex gap-2 text-[9px]">
              <span className="flex items-center gap-1"><span className="w-2 h-2 rounded bg-emerald-500"></span>T1</span>
              <span className="flex items-center gap-1"><span className="w-2 h-2 rounded bg-amber-500"></span>T2</span>
              <span className="flex items-center gap-1"><span className="w-2 h-2 rounded bg-blue-500"></span>T3</span>
            </div>
          </div>
          
          {loadingR ? (
            <div className="py-6 text-center text-slate-600 text-xs">Loading...</div>
          ) : (
            <div className="divide-y divide-white/5">
              {availableResearchers.map((s, i) => (
                <div key={s.id || i} className="p-3 hover:bg-white/[0.02]">
                  <div className="flex items-start justify-between gap-3">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <span className="text-sm font-bold text-white">{s.name}</span>
                        <Pill color={getTierColor(s.tier)}>{getTierLabel(s.tier)}</Pill>
                      </div>
                      <div className="text-[10px] text-slate-500 mb-2">
                        {s.market || s.asset_class} • {s.universe_count || 0} tickers • {s.time_horizon}
                      </div>
                      
                      {/* Key Metrics - Compact */}
                      <div className="flex gap-3 text-[10px]">
                        <span className="text-slate-500">N/yr: <span className="text-slate-300">{s.trades_per_year || s.n_count || '—'}</span></span>
                        <span className="text-slate-500">WR: <span className={((s.win_rate || 0) * 100) >= 55 ? 'text-emerald-400' : 'text-slate-300'}>{((s.win_rate || 0) * 100).toFixed(0)}%</span></span>
                        <span className="text-slate-500">PF: <span className={(s.profit_factor || 0) >= 1.5 ? 'text-emerald-400' : 'text-slate-300'}>{s.profit_factor?.toFixed(2) || '—'}</span></span>
                        <span className="text-slate-500">MDD: <span className={(s.max_drawdown || 0) <= 0.1 ? 'text-emerald-400' : 'text-rose-400'}>{s.max_drawdown ? `${(s.max_drawdown * 100).toFixed(0)}%` : '—'}</span></span>
                      </div>
                    </div>
                    
                    <div className="flex flex-col items-end gap-2">
                      <button 
                        onClick={() => setDeployStrategy(s)}
                        className="px-3 py-1.5 bg-emerald-600 hover:bg-emerald-500 text-[10px] font-bold rounded transition-colors whitespace-nowrap"
                      >
                        Deploy →
                      </button>
                      <button 
                        onClick={() => setDetailStrategy(s)}
                        className="text-[9px] text-blue-400 hover:text-blue-300"
                      >
                        View Details
                      </button>
                    </div>
                  </div>
                  
                  {/* Signal Preview */}
                  <div className="mt-2 pt-2 border-t border-white/5 text-[10px]">
                    <div className="flex gap-4">
                      <span className="text-emerald-400 truncate max-w-[200px]" title={s.buy_signal}>▲ {s.buy_signal?.slice(0, 30) || '—'}</span>
                      <span className="text-rose-400 truncate max-w-[200px]" title={s.sell_signal}>▼ {s.sell_signal?.slice(0, 30) || '—'}</span>
                    </div>
                  </div>
                </div>
              ))}
              {!availableResearchers.length && (
                <div className="py-8 text-center text-slate-600 text-xs">No strategies available — all deployed</div>
              )}
            </div>
          )}
        </div>
      </div>
    );
  };

  // =============================================================================
  // PORTFOLIO VIEW
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
          <KPI label="Mode" value={data.mode.replace(/_/g, ' ')} />
        </div>

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

        {/* Paper Strategies */}
        <div className="bg-slate-900/50 rounded-lg border border-white/5 overflow-hidden">
          <div className="px-3 py-2 border-b border-white/5">
            <span className="text-[10px] text-slate-500 uppercase font-bold tracking-wider">
              Paper Positions ({paperStrats.length})
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
  // PERFORMANCE VIEW - Backtest vs Live Comparison
  // =============================================================================
  const PerformanceView = () => {
    const [timeframe, setTimeframe] = useState('1M'); // 1W, 1M, 3M, 1Y, ALL

    return (
      <div className="space-y-4">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-sm font-bold text-white">Strategy Performance</h2>
            <p className="text-[10px] text-slate-500">Backtest vs Live tracking</p>
          </div>
          <div className="flex gap-1 p-1 rounded-lg bg-slate-900/50 border border-white/5">
            {['1W', '1M', '3M', '1Y', 'ALL'].map(tf => (
              <button
                key={tf}
                onClick={() => setTimeframe(tf)}
                className={`px-3 py-1 rounded text-[10px] font-bold transition-all ${
                  timeframe === tf ? 'bg-blue-500 text-white' : 'text-slate-400 hover:text-white'
                }`}
              >
                {tf}
              </button>
            ))}
          </div>
        </div>

        {/* Summary Cards */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
          <div className="p-3 rounded-lg bg-slate-900/50 border border-white/5">
            <div className="text-[9px] text-slate-500 uppercase">Active Strategies</div>
            <div className="text-xl font-bold text-white">{data.strategies.filter(s => s.live_trades > 0).length}</div>
          </div>
          <div className="p-3 rounded-lg bg-slate-900/50 border border-white/5">
            <div className="text-[9px] text-slate-500 uppercase">Avg Live Win Rate</div>
            <div className="text-xl font-bold text-emerald-400">
              {(data.strategies.filter(s => s.live_win_rate).reduce((a, s) => a + (s.live_win_rate || 0), 0) / 
                Math.max(1, data.strategies.filter(s => s.live_win_rate).length)).toFixed(0)}%
            </div>
          </div>
          <div className="p-3 rounded-lg bg-slate-900/50 border border-white/5">
            <div className="text-[9px] text-slate-500 uppercase">Total Live Trades</div>
            <div className="text-xl font-bold text-white">
              {data.strategies.reduce((a, s) => a + (s.live_trades || 0), 0)}
            </div>
          </div>
          <div className="p-3 rounded-lg bg-slate-900/50 border border-white/5">
            <div className="text-[9px] text-slate-500 uppercase">Best Performer</div>
            <div className="text-sm font-bold text-emerald-400 truncate">
              {data.strategies.length > 0 
                ? data.strategies.sort((a, b) => (b.returns || 0) - (a.returns || 0))[0]?.strategy_name || '—'
                : '—'}
            </div>
          </div>
        </div>

        {/* Performance Table */}
        <div className="bg-slate-900/50 rounded-lg border border-white/5 overflow-hidden">
          <div className="px-3 py-2 border-b border-white/5">
            <span className="text-[10px] text-slate-500 uppercase font-bold tracking-wider">Strategy Comparison</span>
          </div>
          <table className="w-full text-xs">
            <thead>
              <tr className="text-[9px] text-slate-500 uppercase tracking-wider border-b border-white/10 bg-slate-900/30">
                <th className="text-left py-2 px-3">Strategy</th>
                <th className="text-right py-2 px-3">Tier</th>
                <th className="text-right py-2 px-3">BT WR</th>
                <th className="text-right py-2 px-3">Live WR</th>
                <th className="text-right py-2 px-3">Δ WR</th>
                <th className="text-right py-2 px-3">BT PF</th>
                <th className="text-right py-2 px-3">Live PF</th>
                <th className="text-right py-2 px-3">BT N</th>
                <th className="text-right py-2 px-3">Live N</th>
                <th className="text-right py-2 px-3">Returns</th>
              </tr>
            </thead>
            <tbody>
              {data.strategies.map((s, i) => {
                const deltaWR = s.backtest_win_rate != null && s.live_win_rate != null 
                  ? s.live_win_rate - s.backtest_win_rate 
                  : null;
                return (
                  <tr key={i} className="border-b border-white/5 hover:bg-white/[0.02] cursor-pointer"
                    onClick={() => setDetailStrategy(s)}>
                    <td className="py-2 px-3">
                      <div className="font-bold text-white">{s.strategy_name || s.strategy_id}</div>
                      <div className="text-[9px] text-slate-500">{s.asset_class}</div>
                    </td>
                    <td className="py-2 px-3 text-right">
                      <span className={`text-[10px] font-bold ${
                        s.tier === 'T1' || s.tier === 1 ? 'text-emerald-400' :
                        s.tier === 'T2' || s.tier === 2 ? 'text-amber-400' :
                        s.tier === 'T3' || s.tier === 3 ? 'text-blue-400' : 'text-slate-400'
                      }`}>
                        {s.tier === 'T1' || s.tier === 1 ? 'T1' :
                         s.tier === 'T2' || s.tier === 2 ? 'T2' :
                         s.tier === 'T3' || s.tier === 3 ? 'T3' : 'T4'}
                      </span>
                    </td>
                    <td className="py-2 px-3 text-right font-mono text-slate-400">
                      {s.backtest_win_rate != null ? `${s.backtest_win_rate.toFixed(0)}%` : '—'}
                    </td>
                    <td className={`py-2 px-3 text-right font-mono font-bold ${pnlCl(s.live_win_rate != null ? s.live_win_rate - 50 : null)}`}>
                      {s.live_win_rate != null ? `${s.live_win_rate.toFixed(0)}%` : '—'}
                    </td>
                    <td className={`py-2 px-3 text-right font-mono ${pnlCl(deltaWR)}`}>
                      {deltaWR != null ? `${deltaWR >= 0 ? '+' : ''}${deltaWR.toFixed(0)}pp` : '—'}
                    </td>
                    <td className="py-2 px-3 text-right font-mono text-slate-400">
                      {s.backtest_pf?.toFixed(2) || s.backtest_profit_factor?.toFixed(2) || '—'}
                    </td>
                    <td className={`py-2 px-3 text-right font-mono ${pnlCl((s.live_profit_factor || 0) - 1.5)}`}>
                      {s.live_profit_factor?.toFixed(2) || '—'}
                    </td>
                    <td className="py-2 px-3 text-right font-mono text-slate-500">{s.backtest_trades || 0}</td>
                    <td className="py-2 px-3 text-right font-mono text-slate-300">{s.live_trades || 0}</td>
                    <td className={`py-2 px-3 text-right font-mono font-bold ${pnlCl(s.returns)}`}>
                      {s.returns != null ? fmtPct(s.returns) : '—'}
                    </td>
                  </tr>
                );
              })}
              {data.strategies.length === 0 && (
                <tr>
                  <td colSpan="10" className="py-8 text-center text-slate-600 text-xs">No strategies loaded</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        {/* Strategy Cards - Detailed View */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {data.strategies.slice(0, 6).map((s, i) => (
            <div key={i} className="p-3 rounded-lg bg-slate-900/50 border border-white/5">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-bold text-white">{s.strategy_name || s.strategy_id}</span>
                <div className="flex gap-2">
                  <span className={`text-[10px] font-bold ${
                    s.tier === 'T1' || s.tier === 1 ? 'text-emerald-400' :
                    s.tier === 'T2' || s.tier === 2 ? 'text-amber-400' :
                    s.tier === 'T3' || s.tier === 3 ? 'text-blue-400' : 'text-slate-400'
                  }`}>
                    {s.tier === 'T1' || s.tier === 1 ? 'T1' :
                     s.tier === 'T2' || s.tier === 2 ? 'T2' :
                     s.tier === 'T3' || s.tier === 3 ? 'T3' : 'T4'}
                  </span>
                </div>
              </div>
              
              <div className="grid grid-cols-4 gap-2 mb-2">
                <div className="text-center p-1.5 bg-slate-800/30 rounded">
                  <div className="text-[9px] text-slate-500">Win Rate</div>
                  <div className={`text-sm font-bold font-mono ${pnlCl(s.live_win_rate != null ? s.live_win_rate - 50 : null)}`}>
                    {s.live_win_rate != null ? `${s.live_win_rate.toFixed(0)}%` : '—'}
                  </div>
                </div>
                <div className="text-center p-1.5 bg-slate-800/30 rounded">
                  <div className="text-[9px] text-slate-500">PF</div>
                  <div className={`text-sm font-bold font-mono ${pnlCl((s.live_profit_factor || 0) - 1.5)}`}>
                    {s.live_profit_factor?.toFixed(2) || '—'}
                  </div>
                </div>
                <div className="text-center p-1.5 bg-slate-800/30 rounded">
                  <div className="text-[9px] text-slate-500">Trades</div>
                  <div className="text-sm font-bold font-mono text-white">{s.live_trades || 0}</div>
                </div>
                <div className="text-center p-1.5 bg-slate-800/30 rounded">
                  <div className="text-[9px] text-slate-500">Return</div>
                  <div className={`text-sm font-bold font-mono ${pnlCl(s.returns)}`}>
                    {s.returns != null ? fmtPct(s.returns) : '—'}
                  </div>
                </div>
              </div>
              
              {s.current_signal && (
                <div className="flex items-center gap-2 text-[10px]">
                  <span className="text-slate-500">Current Signal:</span>
                  <Pill color={s.current_signal.action === 'BUY' ? 'emerald' : s.current_signal.action === 'SELL' ? 'rose' : 'slate'}>
                    {s.current_signal.action} {s.current_signal.ticker}
                  </Pill>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    );
  };

  // =============================================================================
  // RENDER
  // =============================================================================
  return (
    <div className="min-h-screen bg-slate-950 text-white font-sans">
      {/* Top Bar - Mobile optimized */}
      <header className="fixed top-0 left-0 right-0 z-40 border-b border-white/5 bg-slate-950/90 backdrop-blur-xl safe-top">
        <div className="flex items-center justify-between px-3 py-2 max-w-[1800px] mx-auto">
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2">
              <div className="w-7 h-7 rounded bg-gradient-to-br from-blue-500 to-violet-600 flex items-center justify-center text-[11px] font-black">JT</div>
              <span className="text-xs font-bold text-white hidden md:inline">JTCML</span>
            </div>
            {/* Desktop Nav - URL based */}
            <nav className="hidden md:flex gap-1">
              {navItems.map(n => (
                <button key={n.id} onClick={() => navigateToTab(n.id)}
                  className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-bold transition-all ${currentTab === n.id ? 'bg-white text-black' : 'text-slate-400 hover:text-white hover:bg-white/5'}`}>
                  <span>{n.icon}</span>
                  <span>{n.label}</span>
                </button>
              ))}
            </nav>
          </div>

          <div className="flex items-center gap-2">
            <Pill color={modeColor}>{data.mode.replace('_TRADING', '').replace('_', ' ')}</Pill>
            <div className="flex items-center gap-1">
              <Dot on={isConnected} />
              <span className="text-[10px] text-slate-500 hidden sm:inline">IBKR</span>
            </div>
            <span className="text-[10px] text-slate-600 hidden lg:inline">{new Date().toLocaleTimeString()}</span>
          </div>
        </div>
      </header>

      {/* Main Content - Mobile Optimized Padding */}
      <main className="pt-16 md:pt-20 pb-20 md:pb-6 px-3 md:px-6 max-w-[1600px] mx-auto">
        {loading && !data.signals.length ? (
          <div className="flex items-center justify-center h-[60vh]">
            <div className="flex items-center gap-3 text-slate-500">
              <div className="w-5 h-5 border-2 border-slate-600 border-t-blue-500 rounded-full animate-spin" />
              <span className="text-sm">Loading market data...</span>
            </div>
          </div>
        ) : (
          <>
            {activeTab === 'dashboard' && <DashboardTab />}
            {activeTab === 'strategies' && <StrategiesTabContent />}
            {activeTab === 'lab' && <StrategyLab />}
            {activeTab === 'research' && <ResearchTab key="research-tab" onTickerClick={handleTickerClick} />}
            {activeTab === 'performance' && <StrategyPerformance />}
            {activeTab === 'portfolio' && <PortfolioTab />}
            {activeTab === 'markets' && <MarketsTab onTickerClick={handleTickerClick} />}
            {activeTab === 'settings' && <SettingsTab />}
          </>
        )}
      </main>

      {/* Mobile Bottom Navigation - URL based */}
      <MobileBottomNav view={currentTab} setView={navigateToTab} navItems={navItems} />

      {/* Modals */}
      {detailStrategy && <StrategyDetail strategy={detailStrategy} onClose={() => setDetailStrategy(null)} />}
      {deployStrategy && <DeployModal strategy={deployStrategy} onClose={() => setDeployStrategy(null)} onDone={fetchAll} />}

      {/* Footer - Hidden on mobile */}
      <footer className="hidden md:block fixed bottom-0 left-0 right-0 z-40 border-t border-white/5 bg-slate-950/80 backdrop-blur py-1 px-3">
        <div className="flex items-center justify-between text-[9px] text-slate-600 max-w-[1800px] mx-auto">
          <span>v4.1 • Platform Mode</span>
          <span>JTCML Trading Systems</span>
        </div>
      </footer>
    </div>
  );
}

export default App;
