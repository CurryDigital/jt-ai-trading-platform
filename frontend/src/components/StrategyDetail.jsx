import React, { useMemo, useState } from 'react';
import { api, usePoll, fmt, fmtK, fmtAge, pnlCl } from '../utils';
import { PromotionPanel } from './PromotionPanel';
import { CapitalAllocationPanel } from './CapitalAllocationPanel';
import { RiskWatchPanel } from './RiskWatchPanel';

// Tiny inline SVG sparkline / equity curve --------------------------------
const EquityCurve = ({ points, height = 80 }) => {
  if (!points?.length) {
    return <div className="text-[10px] text-slate-600 text-center py-6">No live trades yet · curve will appear after first execution</div>;
  }
  const ys = points.map(p => p.cum_pnl);
  const min = Math.min(0, ...ys);
  const max = Math.max(0, ...ys);
  const range = (max - min) || 1;
  const w = 600;
  const h = height;
  const step = points.length > 1 ? w / (points.length - 1) : 0;
  const path = points.map((p, i) => {
    const x = i * step;
    const y = h - ((p.cum_pnl - min) / range) * h;
    return `${i === 0 ? 'M' : 'L'}${x.toFixed(1)},${y.toFixed(1)}`;
  }).join(' ');
  const last = points[points.length - 1];
  const positive = last.cum_pnl >= 0;
  const stroke = positive ? '#34d399' : '#fb7185';
  const fill = positive ? 'rgba(52,211,153,0.12)' : 'rgba(251,113,133,0.12)';
  const zeroY = h - ((0 - min) / range) * h;
  const area = `${path} L${(points.length - 1) * step},${zeroY} L0,${zeroY} Z`;
  return (
    <svg viewBox={`0 0 ${w} ${h}`} preserveAspectRatio="none" className="w-full block" style={{ height }}>
      <line x1="0" y1={zeroY} x2={w} y2={zeroY} stroke="rgba(255,255,255,0.06)" strokeDasharray="3,3" />
      <path d={area} fill={fill} />
      <path d={path} stroke={stroke} strokeWidth="1.5" fill="none" />
    </svg>
  );
};

// Monthly returns heatmap ------------------------------------------------
const MonthlyHeatmap = ({ rows }) => {
  // bucket into year -> {1..12 -> pct}
  const grid = useMemo(() => {
    const m = new Map();
    for (const r of rows || []) {
      if (!m.has(r.year)) m.set(r.year, {});
      m.get(r.year)[r.month] = r.return;
    }
    return Array.from(m.entries()).sort((a, b) => b[0] - a[0]);
  }, [rows]);

  if (!grid.length) {
    return <div className="text-[10px] text-slate-600 text-center py-4">No monthly return data</div>;
  }

  const cellColor = (v) => {
    if (v == null) return 'bg-slate-800/30 text-slate-700';
    if (v >= 5) return 'bg-emerald-500/40 text-emerald-100';
    if (v >= 1) return 'bg-emerald-500/20 text-emerald-300';
    if (v > -1) return 'bg-slate-700/40 text-slate-300';
    if (v > -5) return 'bg-rose-500/20 text-rose-300';
    return 'bg-rose-500/40 text-rose-100';
  };
  const months = ['J','F','M','A','M','J','J','A','S','O','N','D'];

  return (
    <div className="overflow-x-auto">
      <table className="w-full">
        <thead>
          <tr>
            <th className="qr-label text-left pl-1 py-1 w-10">YR</th>
            {months.map((m, i) => (
              <th key={i} className="qr-label text-center py-1">{m}</th>
            ))}
            <th className="qr-label text-right pr-1 py-1 w-10">YTD</th>
          </tr>
        </thead>
        <tbody>
          {grid.map(([year, mp]) => {
            const ytd = Object.values(mp).reduce((s, v) => s + (v || 0), 0);
            return (
              <tr key={year}>
                <td className="qr-num text-[10px] text-slate-400 pl-1 py-0.5">{year}</td>
                {Array.from({ length: 12 }, (_, i) => i + 1).map(mo => {
                  const v = mp[mo];
                  return (
                    <td key={mo} className="px-px py-px">
                      <div className={`qr-num text-[9px] py-1 rounded text-center ${cellColor(v)}`}>
                        {v == null ? '·' : v.toFixed(1)}
                      </div>
                    </td>
                  );
                })}
                <td className={`qr-num text-[10px] pr-1 py-0.5 text-right font-bold ${pnlCl(ytd)}`}>
                  {ytd >= 0 ? '+' : ''}{ytd.toFixed(1)}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
};

// Metric tile ------------------------------------------------------------
const Metric = ({ label, value, sub, valClass = 'text-white' }) => (
  <div className="qr-surface px-3 py-2">
    <div className="qr-label">{label}</div>
    <div className={`qr-num text-[15px] font-bold leading-tight mt-0.5 ${valClass}`}>{value}</div>
    {sub != null && <div className="qr-num text-[10px] text-slate-500 mt-0.5">{sub}</div>}
  </div>
);

const VERDICT_STYLE = {
  outperforming:           { cls: 'qr-chip-emerald', label: 'OUTPERFORMING' },
  in_line:                 { cls: 'qr-chip-blue',    label: 'IN LINE' },
  underperforming:         { cls: 'qr-chip-rose',    label: 'UNDERPERFORMING' },
  insufficient_live_data:  { cls: 'qr-chip-slate',   label: 'INSUFFICIENT DATA' },
  no_backtest_baseline:    { cls: 'qr-chip-slate',   label: 'NO BASELINE' },
};

const PRIORITY_STYLE = {
  GOLDEN:        'qr-chip-amber',
  NEAR_GOLDEN:   'qr-chip-blue',
  EXPERIMENTAL:  'qr-chip-slate',
};

const STATUS_STYLE = {
  ACTIVE:        'qr-chip-emerald',
  TESTING:       'qr-chip-blue',
  DEPRECATED:    'qr-chip-slate',
};

const MODE_STYLE = {
  LIVE_TRADING:  'qr-chip-rose',
  PAPER_TRADING: 'qr-chip-amber',
  SIMULATION:    'qr-chip-blue',
};

// Main component --------------------------------------------------------
export const StrategyDetail = ({ strategyId, onBack }) => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [tab, setTab] = useState('trades');
  const [refreshedAt, setRefreshedAt] = useState(null);

  const load = async () => {
    const d = await api.get(`/api/strategies/${encodeURIComponent(strategyId)}/evaluation`);
    setData(d);
    setRefreshedAt(new Date().toISOString());
    setLoading(false);
  };

  // Visibility-paused poll. The parent remounts this via key={strategyId},
  // so mount handles the initial load + spinner; usePoll drives the 30s refresh.
  usePoll(load, 30000);

  if (loading) {
    return (
      <div className="flex items-center gap-2 py-12 justify-center text-slate-500 text-[11px]">
        <div className="w-3 h-3 border-2 border-slate-700 border-t-blue-500 rounded-full animate-spin" />
        Loading evaluation…
      </div>
    );
  }

  if (!data) {
    return (
      <div className="qr-surface p-6 text-center">
        <p className="text-[12px] text-slate-400">Strategy <span className="font-mono text-white">{strategyId}</span> not found</p>
        <button onClick={onBack} className="qr-btn-ghost mt-3">← Back</button>
      </div>
    );
  }

  const bt = data.metrics.backtest;
  const lv = data.metrics.live;
  const verdict = VERDICT_STYLE[data.divergence.verdict] || VERDICT_STYLE.no_backtest_baseline;
  const wrDelta = data.divergence.win_rate_delta_pp;
  const pfDelta = data.divergence.profit_factor_delta;

  return (
    <div className="space-y-3">
      {/* Header */}
      <div className="qr-surface px-3 py-2.5">
        <div className="flex items-start justify-between gap-3 flex-wrap">
          <div className="min-w-0">
            <button onClick={onBack} className="qr-btn-ghost mb-1.5">← Strategies</button>
            <div className="flex items-center gap-2 flex-wrap">
              <h1 className="text-[15px] font-bold text-white tracking-tight truncate max-w-[420px]" title={data.name}>{data.name}</h1>
              {data.priority && <span className={`qr-chip ${PRIORITY_STYLE[data.priority] || 'qr-chip-slate'}`}>{data.priority}</span>}
              {data.status && <span className={`qr-chip ${STATUS_STYLE[data.status] || 'qr-chip-slate'}`}>{data.status}</span>}
              {data.execution_mode && <span className={`qr-chip ${MODE_STYLE[data.execution_mode] || 'qr-chip-slate'}`}>{data.execution_mode.replace('_TRADING','').replace('SIMULATION','SIM')}</span>}
              {data.version && <span className="qr-chip qr-chip-slate">v{data.version}</span>}
            </div>
            <div className="flex items-center gap-3 mt-1 text-[10px] text-slate-500">
              <span><span className="qr-label">ID</span> <span className="qr-num text-slate-300">{data.strategy_id}</span></span>
              <span><span className="qr-label">ASSET</span> <span className="text-slate-300">{data.asset_class}</span></span>
              <span><span className="qr-label">DIR</span> <span className="text-slate-300">{data.direction}</span></span>
              <span><span className="qr-label">UNIVERSE</span> <span className="qr-num text-slate-300">{data.universe_count}</span></span>
              <span><span className="qr-label">VENUE</span> <span className="text-slate-300">{data.venue}</span></span>
              <span><span className="qr-label">UPD</span> <span className="qr-num text-slate-300">{fmtAge(refreshedAt)}</span></span>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <span className={`qr-chip ${verdict.cls}`}>{verdict.label}</span>
            <button onClick={load} className="qr-btn-ghost">↻ Refresh</button>
          </div>
        </div>
      </div>

      {/* Metrics grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-8 gap-2">
        <Metric label="BT WR"
          value={bt.win_rate != null ? `${(bt.win_rate * 100).toFixed(1)}%` : '—'}
          sub={bt.total_trades != null ? `${bt.total_trades} tr` : null}
          valClass="text-slate-200" />
        <Metric label="Live WR"
          value={lv.win_rate != null ? `${(lv.win_rate * 100).toFixed(1)}%` : '—'}
          sub={lv.total_trades ? `${lv.total_trades} tr` : 'no trades'}
          valClass={lv.win_rate == null ? 'text-slate-500' : (lv.win_rate >= (bt.win_rate ?? 0)) ? 'qr-pnl-pos' : 'qr-pnl-neg'} />
        <Metric label="Δ WR"
          value={wrDelta != null ? `${wrDelta >= 0 ? '+' : ''}${wrDelta.toFixed(1)}pp` : '—'}
          valClass={wrDelta == null ? 'text-slate-500' : wrDelta >= 0 ? 'qr-pnl-pos' : 'qr-pnl-neg'} />
        <Metric label="BT PF"
          value={bt.profit_factor != null ? bt.profit_factor.toFixed(2) : '—'}
          valClass="text-slate-200" />
        <Metric label="Live PF"
          value={lv.profit_factor != null ? lv.profit_factor.toFixed(2) : '—'}
          valClass={lv.profit_factor == null ? 'text-slate-500' : lv.profit_factor >= 1.5 ? 'qr-pnl-pos' : lv.profit_factor >= 1 ? 'text-amber-300' : 'qr-pnl-neg'} />
        <Metric label="BT Sharpe"
          value={bt.sharpe != null ? bt.sharpe.toFixed(2) : '—'}
          valClass="text-slate-200" />
        <Metric label="Max DD"
          value={bt.max_drawdown != null ? `${bt.max_drawdown.toFixed(1)}%` : '—'}
          valClass="qr-pnl-neg" />
        <Metric label="Live P&L"
          value={fmtK(lv.total_pnl)}
          sub={lv.last_trade_at ? `last ${fmtAge(lv.last_trade_at)}` : null}
          valClass={pnlCl(lv.total_pnl)} />
      </div>

      {/* Promotion gate panel */}
      <PromotionPanel
        strategyId={data.strategy_id}
        currentMode={data.execution_mode || 'SIMULATION'}
        onPromoted={() => load()}
      />

      {/* Capital allocation panel */}
      <CapitalAllocationPanel
        strategyId={data.strategy_id}
        executionMode={data.execution_mode || 'SIMULATION'}
      />

      {/* Risk watch — auto-demote rules */}
      <RiskWatchPanel
        strategyId={data.strategy_id}
        executionMode={data.execution_mode || 'SIMULATION'}
        onDemoted={() => load()}
      />

      {/* Chart + Heatmap */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-3">
        <div className="qr-surface lg:col-span-2 overflow-hidden">
          <div className="px-3 py-2 border-b border-white/[0.05] flex items-center justify-between">
            <span className="qr-label">Equity Curve · live cum P&L · last {data.window_days}d</span>
            <span className={`qr-num text-[11px] font-bold ${pnlCl(lv.total_pnl)}`}>{fmtK(lv.total_pnl)}</span>
          </div>
          <div className="p-3">
            <EquityCurve points={data.equity_curve} />
          </div>
        </div>
        <div className="qr-surface overflow-hidden">
          <div className="px-3 py-2 border-b border-white/[0.05]">
            <span className="qr-label">Monthly Returns (%)</span>
          </div>
          <div className="p-2">
            <MonthlyHeatmap rows={data.monthly_returns} />
          </div>
        </div>
      </div>

      {/* Logic + Universe */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-3">
        <div className="qr-surface px-3 py-2">
          <div className="qr-label mb-1">Entry Logic</div>
          <p className="text-[11px] text-slate-300 whitespace-pre-wrap leading-relaxed">{data.entry_logic || '—'}</p>
        </div>
        <div className="qr-surface px-3 py-2">
          <div className="qr-label mb-1">Exit Logic</div>
          <p className="text-[11px] text-slate-300 whitespace-pre-wrap leading-relaxed">{data.exit_logic || '—'}</p>
        </div>
        <div className="qr-surface px-3 py-2">
          <div className="qr-label mb-1">Universe ({data.universe_count})</div>
          <div className="flex flex-wrap gap-1 max-h-32 overflow-auto no-scrollbar">
            {data.universe.length === 0 && <span className="text-[10px] text-slate-600">No tickers configured</span>}
            {data.universe.map(t => (
              <span key={t} className="qr-chip qr-chip-slate font-mono">{t}</span>
            ))}
          </div>
        </div>
      </div>

      {/* Tabs: trades / signals */}
      <div className="qr-surface overflow-hidden">
        <div className="px-3 py-2 border-b border-white/[0.05] flex items-center gap-1">
          {[
            { id: 'trades',  label: `Trades (${data.recent_trades.length})`  },
            { id: 'signals', label: `Signals (${data.recent_signals.length})` },
          ].map(t => (
            <button
              key={t.id}
              onClick={() => setTab(t.id)}
              className={`px-2 py-1 rounded text-[11px] font-semibold transition-colors ${tab === t.id ? 'bg-white/[0.08] text-white' : 'text-slate-400 hover:text-slate-200'}`}
            >{t.label}</button>
          ))}
          {pfDelta != null && (
            <span className="ml-auto qr-num text-[10px] text-slate-500">
              ΔPF <span className={`font-bold ${pfDelta >= 0 ? 'qr-pnl-pos' : 'qr-pnl-neg'}`}>{pfDelta >= 0 ? '+' : ''}{pfDelta.toFixed(2)}</span>
            </span>
          )}
        </div>

        {tab === 'trades' && (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-white/[0.06]">
                  <th className="qr-label text-left  py-1 px-2">Time</th>
                  <th className="qr-label text-left  py-1 px-2">Ticker</th>
                  <th className="qr-label text-right py-1 px-2">Side</th>
                  <th className="qr-label text-right py-1 px-2">Qty</th>
                  <th className="qr-label text-right py-1 px-2">Price</th>
                  <th className="qr-label text-right py-1 px-2">P&L</th>
                  <th className="qr-label text-right py-1 px-2">Mode</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/[0.04]">
                {data.recent_trades.map((t, i) => (
                  <tr key={i} className="qr-tr-hover">
                    <td className="py-1 px-2 qr-num text-slate-400 text-[10px]">{t.ts ? new Date(t.ts).toLocaleString('en-GB', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' }) : '—'}</td>
                    <td className="py-1 px-2 text-white text-[11px] font-mono">{t.ticker}</td>
                    <td className="py-1 px-2 text-right">
                      <span className={`qr-chip ${t.side === 'BUY' || t.side === 'LONG' ? 'qr-chip-emerald' : 'qr-chip-rose'}`}>{t.side}</span>
                    </td>
                    <td className="py-1 px-2 qr-num text-slate-300">{fmt(t.quantity, 0)}</td>
                    <td className="py-1 px-2 qr-num text-slate-300">{fmt(t.price)}</td>
                    <td className={`py-1 px-2 qr-num font-bold ${pnlCl(t.pnl)}`}>{t.pnl == null ? '—' : fmtK(t.pnl)}</td>
                    <td className="py-1 px-2 text-right text-[9px] text-slate-500">{t.mode || '—'}</td>
                  </tr>
                ))}
                {!data.recent_trades.length && (
                  <tr><td colSpan={7} className="py-6 text-center text-slate-600 text-[11px]">No live trades yet</td></tr>
                )}
              </tbody>
            </table>
          </div>
        )}

        {tab === 'signals' && (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-white/[0.06]">
                  <th className="qr-label text-left  py-1 px-2">Ticker</th>
                  <th className="qr-label text-right py-1 px-2">Signal</th>
                  <th className="qr-label text-right py-1 px-2">Strength</th>
                  <th className="qr-label text-right py-1 px-2">Confidence</th>
                  <th className="qr-label text-right py-1 px-2">Price</th>
                  <th className="qr-label text-right py-1 px-2">Generated</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/[0.04]">
                {data.recent_signals.map((s, i) => (
                  <tr key={i} className="qr-tr-hover">
                    <td className="py-1 px-2 text-white text-[11px] font-mono">{s.ticker}</td>
                    <td className="py-1 px-2 text-right">
                      <span className={`qr-chip ${s.signal === 'BUY' ? 'qr-chip-emerald' : s.signal === 'SELL' ? 'qr-chip-rose' : 'qr-chip-slate'}`}>{s.signal}</span>
                    </td>
                    <td className="py-1 px-2 qr-num text-slate-300">{s.strength != null ? `${(s.strength * 100).toFixed(0)}%` : '—'}</td>
                    <td className="py-1 px-2 qr-num text-slate-300">{s.confidence != null ? `${(s.confidence * 100).toFixed(0)}%` : '—'}</td>
                    <td className="py-1 px-2 qr-num text-slate-300">{fmt(s.price)}</td>
                    <td className="py-1 px-2 qr-num text-slate-500 text-[10px] text-right">{s.ts ? fmtAge(s.ts) : '—'}</td>
                  </tr>
                ))}
                {!data.recent_signals.length && (
                  <tr><td colSpan={6} className="py-6 text-center text-slate-600 text-[11px]">No active signals · DE pipeline may not have populated yet</td></tr>
                )}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};

export default StrategyDetail;
