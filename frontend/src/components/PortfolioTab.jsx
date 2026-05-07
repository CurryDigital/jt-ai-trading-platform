import React, { useState, useMemo, useEffect, Suspense, lazy } from 'react';
import { api, fmt, fmtK, fmtPct, pnlCl } from '../utils';

const CandlestickChart = lazy(() => import('./CandlestickChart'));

const KPI = ({ l, v, sub, pos, hint }) => (
  <div className="px-3 py-2 qr-surface min-w-0" title={hint}>
    <div className="qr-label truncate">{l}</div>
    <div className="qr-num text-[15px] font-bold text-white leading-tight mt-0.5">{v}</div>
    {sub && <div className={`qr-num text-[10px] mt-0.5 ${pos != null ? (pos ? 'qr-pnl-pos' : 'qr-pnl-neg') : 'text-slate-500'}`}>{sub}</div>}
  </div>
);

const Pill = ({ c = 'slate', children }) => (
  <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-bold bg-${c}-500/15 text-${c}-400 ring-1 ring-${c}-500/20`}>{children}</span>
);

const ALERT_STYLE = {
  critical: 'ring-rose-500/30 bg-rose-500/10 text-rose-300',
  warning: 'ring-amber-500/30 bg-amber-500/10 text-amber-300',
};

const classLabels = {
  STOCK: { label: 'Stocks', icon: '📈', color: 'blue' },
  FX: { label: 'FX', icon: '💱', color: 'emerald' },
  CRYPTO: { label: 'Crypto', icon: '₿', color: 'amber' },
  BOND: { label: 'Bonds', icon: '📋', color: 'slate' },
  ETF: { label: 'ETFs', icon: '📊', color: 'violet' },
  OPTION: { label: 'Options', icon: '⚡', color: 'rose' },
  FUTURE: { label: 'Futures', icon: '⏳', color: 'orange' },
  CASH: { label: 'Cash', icon: '💵', color: 'emerald' },
  OTHER: { label: 'Other', icon: '💼', color: 'slate' },
};

const assetClasses = ['STOCK', 'FX', 'CRYPTO', 'BOND', 'ETF', 'OPTION', 'FUTURE', 'OTHER'];

const CashSummaryWidget = () => {
  const [cash, setCash] = useState(null);
  const [expanded, setExpanded] = useState(false);

  useEffect(() => {
    (async () => {
      const res = await api.get('/api/positions/cash-summary');
      if (res && !res.error) setCash(res);
    })();
  }, []);

  if (!cash) return null;

  const fxPositions = Object.entries(cash.fx_positions || {}).sort((a, b) => Math.abs(b[1]) - Math.abs(a[1]));
  const totalFx = fxPositions.reduce((s, [, v]) => s + Math.abs(v), 0);

  return (
    <div className="qr-surface overflow-hidden">
      <div
        className="px-3 py-2 flex items-center justify-between cursor-pointer hover:bg-white/[0.02] transition-colors"
        onClick={() => setExpanded(e => !e)}
      >
        <div className="flex items-center gap-2">
          <span className="qr-label">Cash & FX</span>
          <span className="text-[9px] text-slate-500">{cash.base_currency}</span>
        </div>
        <div className="flex items-center gap-3">
          <span className="qr-num text-[12px] font-bold text-white">{fmtK(cash.base_balance)}</span>
          {cash.total_trades > 0 && (
            <span className="qr-chip qr-chip-amber">{cash.total_trades} to close</span>
          )}
          <span className="text-[9px] text-slate-600">{expanded ? '▲' : '▼'}</span>
        </div>
      </div>

      {expanded && (
        <div className="px-3 pb-3 border-t border-white/[0.05]">
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-x-4 gap-y-1.5 mt-2">
            {fxPositions.map(([ccy, amt]) => (
              <div key={ccy} className="flex items-center justify-between">
                <span className="text-[10px] font-mono text-slate-400">{ccy}</span>
                <span className={`text-[10px] font-mono font-bold ${amt >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                  {fmtK(amt)}
                </span>
              </div>
            ))}
          </div>

          {cash.trades_to_close?.length > 0 && (
            <div className="mt-2 pt-2 border-t border-white/[0.05]">
              <div className="qr-label mb-1.5">FX Trades to Flatten</div>
              <div className="space-y-1">
                {cash.trades_to_close.map(t => (
                  <div key={t.pair} className="flex items-center justify-between text-[10px]">
                    <div className="flex items-center gap-2">
                      <span className={`qr-chip ${t.action === 'BUY' ? 'qr-chip-emerald' : 'qr-chip-rose'}`}>{t.action}</span>
                      <span className="font-mono text-white">{t.pair}</span>
                    </div>
                    <span className="font-mono text-slate-400">{fmtK(t.quantity)}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

const PositionChart = ({ ticker }) => {
  const [chartData, setChartData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      const res = await api.get(`/api/stocks/${encodeURIComponent(ticker)}?timeframe=3m`);
      if (res?.chart_data) setChartData(res.chart_data);
      setLoading(false);
    })();
  }, [ticker]);

  if (loading) return (
    <div className="flex items-center justify-center py-8">
      <div className="w-4 h-4 border-2 border-slate-700 border-t-blue-500 rounded-full animate-spin" />
    </div>
  );
  if (!chartData?.length) return (
    <div className="py-6 text-center text-[11px] text-slate-600">No chart data available for {ticker}</div>
  );

  return (
    <Suspense fallback={<div className="flex items-center justify-center py-8"><div className="w-4 h-4 border-2 border-slate-700 border-t-blue-500 rounded-full animate-spin" /></div>}>
      <CandlestickChart ticker={ticker} data={chartData} />
    </Suspense>
  );
};

const PositionTable = ({ positions, title, icon, color }) => {
  const [expandedTicker, setExpandedTicker] = useState(null);

  const colorMap = {
    blue: 'border-blue-500/20 bg-blue-500/5',
    emerald: 'border-emerald-500/20 bg-emerald-500/5',
    amber: 'border-amber-500/20 bg-amber-500/5',
    slate: 'border-slate-500/20 bg-slate-500/5',
    violet: 'border-violet-500/20 bg-violet-500/5',
    rose: 'border-rose-500/20 bg-rose-500/5',
    orange: 'border-orange-500/20 bg-orange-500/5',
  };

  const grpValue = positions.reduce((s, p) => s + (p.market_value || 0), 0);
  const grpPnL = positions.reduce((s, p) => s + (p.unrealized_pnl || p.pnl || 0), 0);

  return (
    <div className={`rounded-xl border ${colorMap[color] || colorMap.slate} overflow-hidden mb-4`}>
      <div className="px-3 py-2.5 border-b border-white/[0.06] flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="text-sm">{icon}</span>
          <span className="text-xs font-bold text-white uppercase tracking-wider">{title}</span>
          <span className="text-[10px] text-slate-500">{positions.length} positions</span>
        </div>
        <div className="flex items-center gap-3">
          <span className="text-[11px] font-mono text-slate-400">{fmtK(grpValue)}</span>
          <span className={`text-[11px] font-mono font-bold ${pnlCl(grpPnL)}`}>{grpPnL >= 0 ? '+' : ''}{fmtK(grpPnL)}</span>
        </div>
      </div>

      <table className="w-full text-xs">
        <thead className="bg-slate-900/80">
          <tr className="text-[9px] text-slate-500 uppercase">
            {['Ticker', 'Name', 'Side', 'Qty', 'Entry', 'Current', 'Value', 'P&L', 'P&L %'].map(h =>
              <th key={h} className="text-right py-2 px-2 first:text-left">{h}</th>)}
          </tr>
        </thead>
        <tbody className="divide-y divide-white/5">
          {positions.map(p => {
            const entry = p.avg_entry_price || p.entry_price || 0;
            const current = p.current_price || 0;
            const pnlPct = entry > 0 ? ((current - entry) / entry * 100 * (p.side === 'SHORT' ? -1 : 1)) : 0;
            const isExpanded = expandedTicker === p.ticker;
            return (
              <React.Fragment key={p.id || p.ticker}>
                <tr
                  className={`hover:bg-white/[0.03] transition-colors cursor-pointer ${isExpanded ? 'bg-white/[0.03]' : ''}`}
                  onClick={() => setExpandedTicker(isExpanded ? null : p.ticker)}
                >
                  <td className="py-2 px-2 font-bold text-white">
                    <span className="flex items-center gap-1">
                      <span className={`text-[8px] text-slate-600 transition-transform ${isExpanded ? 'rotate-90' : ''}`}>&#9654;</span>
                      {p.ticker}
                    </span>
                  </td>
                  <td className="py-2 px-2 text-slate-400 text-[10px] max-w-[120px] truncate">{p.name || p.strategy || '—'}</td>
                  <td className="py-2 px-2 text-center">
                    <span className={`text-[9px] font-bold px-1.5 py-0.5 rounded ${p.side === 'LONG' ? 'bg-emerald-500/20 text-emerald-400' : p.side === 'SHORT' ? 'bg-rose-500/20 text-rose-400' : 'bg-slate-500/20 text-slate-400'}`}>{p.side || '—'}</span>
                  </td>
                  <td className="py-2 px-2 text-right font-mono">{fmt(p.quantity, 0)}</td>
                  <td className="py-2 px-2 text-right font-mono text-slate-400">${fmt(entry)}</td>
                  <td className="py-2 px-2 text-right font-mono text-white">${fmt(current)}</td>
                  <td className="py-2 px-2 text-right font-mono">{fmtK(p.market_value)}</td>
                  <td className={`py-2 px-2 text-right font-mono font-bold ${pnlCl(p.unrealized_pnl || p.pnl)}`}>{fmtK(p.unrealized_pnl || p.pnl)}</td>
                  <td className={`py-2 px-2 text-right font-mono ${pnlCl(pnlPct)}`}>{fmtPct(pnlPct)}</td>
                </tr>
                {isExpanded && (
                  <tr>
                    <td colSpan={9} className="p-0">
                      <div className="px-3 py-2 bg-slate-900/40">
                        <PositionChart ticker={p.ticker} />
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
  );
};

const CorrelationHeatmap = ({ data }) => {
  if (!data?.strategies?.length || !data?.matrix?.length) return null;
  const ids = data.strategies;
  const cell = (v) => {
    const intensity = Math.min(1, Math.abs(v));
    const bg = v > 0.7 ? `rgba(244,63,94,${0.15 + intensity * 0.5})`
             : v > 0.4 ? `rgba(251,146,60,${0.15 + intensity * 0.4})`
             : v > 0.1 ? `rgba(250,204,21,${0.1 + intensity * 0.3})`
             : 'rgba(100,116,139,0.05)';
    return bg;
  };
  return (
    <div className="qr-surface p-3">
      <div className="flex items-center justify-between mb-2">
        <span className="qr-label">Strategy Correlation (ticker overlap)</span>
        <span className="text-[10px] text-slate-500">{ids.length} strategies</span>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr>
              <th className="py-0.5 px-1"></th>
              {ids.map(id => (
                <th key={id} className="qr-label text-[8px] font-mono text-slate-500 px-1 pb-1 truncate max-w-[60px]" title={id}>
                  {id.length > 6 ? id.slice(0, 6) : id}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {data.matrix.map((row, i) => (
              <tr key={ids[i]}>
                <td className="qr-label text-[9px] font-mono text-slate-400 pr-2 text-right truncate max-w-[80px]" title={ids[i]}>
                  {ids[i].length > 8 ? ids[i].slice(0, 8) : ids[i]}
                </td>
                {row.map((v, j) => (
                  <td
                    key={j}
                    className="text-center text-[9px] font-mono"
                    style={{ background: cell(v), color: v > 0.5 ? '#fff' : '#94a3b8', minWidth: 28, height: 22 }}
                    title={`${ids[i]} ↔ ${ids[j]}: ${(v * 100).toFixed(0)}%`}
                  >
                    {i === j ? '·' : v > 0.05 ? (v * 100).toFixed(0) : ''}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="mt-2 text-[9px] text-slate-600">
        Higher values (red) = strategies share more tickers, increasing correlated risk.
      </div>
    </div>
  );
};

const RiskDashboard = ({ risk }) => {
  if (!risk) return null;
  const { summary, var: varData, concentration, alerts, correlations } = risk;

  return (
    <div className="space-y-3">
      {/* Risk Alerts */}
      {alerts && alerts.length > 0 && (
        <div className="space-y-1.5">
          {alerts.map((a, i) => (
            <div key={i} className={`px-3 py-2 rounded-lg ring-1 text-[11px] font-semibold ${ALERT_STYLE[a.level] || ALERT_STYLE.warning}`}>
              {a.level === 'critical' ? '🚨' : '⚠️'} {a.message}
            </div>
          ))}
        </div>
      )}

      {/* Summary metrics */}
      {summary && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
          <KPI l="Total Invested" v={fmtK(summary.total_invested)} />
          <KPI l="Unrealized P&L" v={fmtK(summary.total_unrealized_pnl)} pos={summary.total_unrealized_pnl >= 0} />
          <KPI l="Realized P&L" v={fmtK(summary.total_realized_pnl)} pos={summary.total_realized_pnl >= 0} />
          <KPI l="Net Exposure" v={fmtK(summary.net_exposure)} />
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        {/* VaR */}
        {varData && varData.n_observations > 0 && (
          <div className="qr-surface p-3">
            <div className="qr-label mb-2">Value at Risk ({(varData.confidence * 100).toFixed(0)}% confidence)</div>
            <div className="grid grid-cols-2 gap-2">
              <div>
                <div className="text-[10px] text-slate-500">Daily VaR</div>
                <div className={`qr-num text-[13px] font-bold ${pnlCl(varData.daily_var)}`}>{fmtK(varData.daily_var)}</div>
              </div>
              <div>
                <div className="text-[10px] text-slate-500">Monthly VaR</div>
                <div className={`qr-num text-[13px] font-bold ${pnlCl(varData.monthly_var)}`}>{fmtK(varData.monthly_var)}</div>
              </div>
              <div>
                <div className="text-[10px] text-slate-500">Max Loss Observed</div>
                <div className="qr-num text-[12px] text-rose-300">{fmtK(varData.max_loss_observed)}</div>
              </div>
              <div>
                <div className="text-[10px] text-slate-500">Avg Daily P&L</div>
                <div className={`qr-num text-[12px] ${pnlCl(varData.avg_daily_pnl)}`}>{fmtK(varData.avg_daily_pnl)}</div>
              </div>
            </div>
            <div className="mt-2 text-[9px] text-slate-600">{varData.n_observations} observations</div>
          </div>
        )}

        {/* Concentration */}
        {concentration && (
          <div className="qr-surface p-3">
            <div className="flex items-center justify-between mb-2">
              <span className="qr-label">Concentration Risk</span>
              <span className={`qr-chip ${concentration.hhi_ticker > 2500 ? 'qr-chip-amber' : 'qr-chip-emerald'}`}>
                HHI {Math.round(concentration.hhi_ticker || 0)}
              </span>
            </div>
            <div className="mb-2">
              <div className="text-[10px] text-slate-500 mb-1">Top 5 = {fmtPct(concentration.top_5_concentration)} of portfolio</div>
              <div className="h-2 rounded-full bg-slate-800 overflow-hidden">
                <div
                  className={`h-full rounded-full ${(concentration.top_5_concentration || 0) > 80 ? 'bg-rose-500' : (concentration.top_5_concentration || 0) > 60 ? 'bg-amber-500' : 'bg-emerald-500'}`}
                  style={{ width: `${Math.min(100, concentration.top_5_concentration || 0)}%` }}
                />
              </div>
            </div>
            {concentration.by_ticker?.slice(0, 5).map((t, i) => (
              <div key={t.ticker} className="flex items-center justify-between py-0.5">
                <span className="text-[10px] font-mono text-slate-300">{i + 1}. {t.ticker}</span>
                <span className="text-[10px] font-mono text-slate-400">{fmtPct(t.weight_pct)}</span>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Correlation matrix */}
      {correlations && correlations.strategies?.length > 1 && (
        <CorrelationHeatmap data={correlations} />
      )}

      {/* Concentration breakdowns by strategy + asset class */}
      {concentration && (concentration.by_strategy?.length || concentration.by_asset_class?.length) && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {concentration.by_strategy?.length > 0 && (
            <div className="qr-surface p-3">
              <div className="qr-label mb-2">By Strategy ({concentration.by_strategy.length})</div>
              <div className="space-y-1 max-h-48 overflow-y-auto">
                {concentration.by_strategy.slice(0, 10).map(s => (
                  <div key={s.strategy_id} className="flex items-center justify-between gap-2">
                    <span className="text-[10px] font-mono text-slate-300 truncate flex-1">{s.strategy_id}</span>
                    <span className="text-[10px] font-mono text-slate-400">{fmtPct(s.weight_pct)}</span>
                    <div className="w-16 h-1.5 rounded-full bg-slate-800 overflow-hidden">
                      <div className="h-full bg-violet-500" style={{ width: `${Math.min(100, s.weight_pct || 0)}%` }} />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
          {concentration.by_asset_class?.length > 0 && (
            <div className="qr-surface p-3">
              <div className="qr-label mb-2">By Asset Class</div>
              <div className="space-y-1.5">
                {concentration.by_asset_class.map(c => (
                  <div key={c.asset_class} className="flex items-center justify-between gap-2">
                    <span className="text-[11px] font-bold text-slate-200">{c.asset_class || 'OTHER'}</span>
                    <span className="text-[10px] font-mono text-slate-400">{fmtPct(c.weight_pct)}</span>
                    <div className="w-24 h-1.5 rounded-full bg-slate-800 overflow-hidden">
                      <div className="h-full bg-blue-500" style={{ width: `${Math.min(100, c.weight_pct || 0)}%` }} />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export const PortfolioTab = ({ data, onNavigate }) => {
  const [search, setSearch] = useState('');
  const [activeFilter, setActiveFilter] = useState('ALL');
  const [orderSymbol, setOrderSymbol] = useState('');
  const [orderQty, setOrderQty] = useState(1);
  const [orderType, setOrderType] = useState('MKT');
  const [orderLoading, setOrderLoading] = useState(false);
  const [orderMsg, setOrderMsg] = useState(null);
  const [risk, setRisk] = useState(null);
  const [riskView, setRiskView] = useState(false);

  useEffect(() => {
    (async () => {
      const res = await api.get('/api/portfolio/dashboard');
      if (res && !res.error) setRisk(res);
    })();
  }, []);

  const placeOrder = async (action) => {
    if (!orderSymbol) { setOrderMsg({ type: 'error', text: 'Enter a symbol' }); return; }
    setOrderLoading(true);
    setOrderMsg(null);
    try {
      const res = await fetch('/api/ib/place-order', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ symbol: orderSymbol.toUpperCase(), action, quantity: parseInt(orderQty) || 1, order_type: orderType })
      });
      const d = await res.json();
      if (d.success) {
        setOrderMsg({ type: 'success', text: d.message || `${action} order placed` });
        setOrderSymbol('');
        setOrderQty(1);
      } else {
        setOrderMsg({ type: 'error', text: d.detail || 'Order failed' });
      }
    } catch (e) {
      setOrderMsg({ type: 'error', text: e.message || 'Network error' });
    } finally {
      setOrderLoading(false);
    }
  };

  const positions = useMemo(() =>
    (data.positions || []).filter(p => {
      const matchesSearch = !search || p.ticker?.toLowerCase().includes(search.toLowerCase());
      const matchesFilter = activeFilter === 'ALL' || p.asset_class === activeFilter;
      return matchesSearch && matchesFilter;
    }),
    [data.positions, search, activeFilter]
  );

  const byAssetClass = useMemo(() => {
    const groups = {};
    for (const p of positions) {
      const cls = p.asset_class || 'OTHER';
      if (!groups[cls]) groups[cls] = [];
      groups[cls].push(p);
    }
    return groups;
  }, [positions]);

  const activeClasses = assetClasses.filter(c => byAssetClass[c]?.length > 0);
  const totalValue = positions.reduce((s, p) => s + (p.market_value || 0), 0);
  const totalPnL = positions.reduce((s, p) => s + (p.unrealized_pnl || p.pnl || 0), 0);

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-sm font-bold text-white">Portfolio</h2>
          <p className="text-[10px] text-slate-500">Live positions & P&L by asset class</p>
        </div>
        <div className="flex items-center gap-2">
          {riskView && <button onClick={() => onNavigate?.('risk_limits')} className="qr-btn-ghost text-[10px]">Configure Limits</button>}
          <button
            onClick={() => setRiskView(v => !v)}
            className={`px-2.5 py-1 rounded text-[10px] font-semibold transition-colors ${riskView ? 'bg-violet-500/20 text-violet-300 ring-1 ring-violet-500/30' : 'text-slate-400 hover:text-white'}`}
          >
            {riskView ? '← Positions' : 'Risk Dashboard →'}
          </button>
          <Pill c={totalPnL >= 0 ? 'emerald' : 'rose'}>{totalPnL >= 0 ? '+' : ''}{fmtK(totalPnL)}</Pill>
        </div>
      </div>

      {/* Cash & FX Exposure Widget */}
      <CashSummaryWidget />

      {riskView ? (
        <RiskDashboard risk={risk} />
      ) : (
        <>
          {/* Summary Cards */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
            <KPI l="Total Value" v={fmtK(totalValue)} />
            <KPI l="Positions" v={positions.length} />
            <KPI l="Asset Classes" v={activeClasses.length} />
            <KPI l="Unrealized P&L" v={fmtK(totalPnL)} pos={totalPnL >= 0} />
          </div>

          {/* Manual Order */}
          <div className="p-3 rounded-xl bg-slate-900/50 border border-white/[0.06]">
            <div className="flex items-center gap-2 mb-2">
              <span className="text-xs font-bold text-white">Quick Order</span>
              {orderMsg && (
                <span className={`text-[10px] ${orderMsg.type === 'success' ? 'text-emerald-400' : 'text-rose-400'}`}>{orderMsg.text}</span>
              )}
            </div>
            <div className="flex items-center gap-2">
              <input
                type="text"
                value={orderSymbol}
                onChange={e => setOrderSymbol(e.target.value.toUpperCase())}
                placeholder="Symbol"
                className="px-2 py-1.5 bg-slate-800/80 border border-white/10 rounded-lg text-xs text-white w-24 placeholder-slate-600 focus:outline-none focus:border-blue-500/50"
              />
              <input
                type="number"
                value={orderQty}
                onChange={e => setOrderQty(Math.max(1, parseInt(e.target.value) || 1))}
                min="1"
                className="px-2 py-1.5 bg-slate-800/80 border border-white/10 rounded-lg text-xs text-white w-16 placeholder-slate-600 focus:outline-none focus:border-blue-500/50"
              />
              <select
                value={orderType}
                onChange={e => setOrderType(e.target.value)}
                className="px-2 py-1.5 bg-slate-800/80 border border-white/10 rounded-lg text-xs text-white focus:outline-none focus:border-blue-500/50"
              >
                <option value="MKT">MKT</option>
                <option value="LMT">LMT</option>
                <option value="STP">STP</option>
              </select>
              <button
                onClick={() => placeOrder('BUY')}
                disabled={orderLoading}
                className="px-3 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 disabled:bg-slate-700 text-white text-[10px] font-black uppercase transition-all"
              >
                {orderLoading ? '...' : 'BUY'}
              </button>
              <button
                onClick={() => placeOrder('SELL')}
                disabled={orderLoading}
                className="px-3 py-1.5 rounded-lg bg-rose-600 hover:bg-rose-500 disabled:bg-slate-700 text-white text-[10px] font-black uppercase transition-all"
              >
                {orderLoading ? '...' : 'SELL'}
              </button>
            </div>
          </div>

          {/* Asset Class Filter */}
          <div className="flex gap-1 p-1 rounded-lg bg-slate-900/50 border border-white/[0.06] overflow-x-auto">
            <button
              onClick={() => setActiveFilter('ALL')}
              className={`px-3 py-1.5 rounded-md text-[10px] font-bold transition-colors whitespace-nowrap ${activeFilter === 'ALL' ? 'bg-blue-500 text-white' : 'text-slate-400 hover:text-white'}`}
            >
              All ({positions.length})
            </button>
            {activeClasses.map(cls => (
              <button
                key={cls}
                onClick={() => setActiveFilter(cls)}
                className={`px-3 py-1.5 rounded-md text-[10px] font-bold transition-colors whitespace-nowrap ${activeFilter === cls ? 'bg-blue-500 text-white' : 'text-slate-400 hover:text-white'}`}
              >
                {classLabels[cls]?.icon} {classLabels[cls]?.label} ({byAssetClass[cls].length})
              </button>
            ))}
          </div>

          {/* Search */}
          <div className="flex items-center gap-2">
            <input
              value={search}
              onChange={e => setSearch(e.target.value)}
              placeholder="Filter by ticker..."
              className="px-3 py-2 bg-slate-800/80 border border-white/10 rounded-lg text-xs text-white w-48 placeholder-slate-600 focus:outline-none focus:border-blue-500/50"
            />
          </div>

          {/* Positions by Asset Class */}
          {activeFilter === 'ALL' ? (
            activeClasses.map(cls => (
              <PositionTable
                key={cls}
                positions={byAssetClass[cls]}
                title={classLabels[cls]?.label || cls}
                icon={classLabels[cls]?.icon || '💼'}
                color={classLabels[cls]?.color || 'slate'}
              />
            ))
          ) : (
            byAssetClass[activeFilter] && (
              <PositionTable
                positions={byAssetClass[activeFilter]}
                title={classLabels[activeFilter]?.label || activeFilter}
                icon={classLabels[activeFilter]?.icon || '💼'}
                color={classLabels[activeFilter]?.color || 'slate'}
              />
            )
          )}

          {!positions.length && (
            <div className="py-12 text-center text-slate-600 text-sm bg-slate-900/30 rounded-xl border border-white/[0.06]">
              No positions found
            </div>
          )}
        </>
      )}
    </div>
  );
};

export default PortfolioTab;
