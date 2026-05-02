import React, { useEffect, useMemo, useState } from 'react';
import { api, fmt, fmtK, fmtPct, pnlCl } from '../utils';

// Color palette for up to 6 strategies
const COLORS = ['#60a5fa', '#34d399', '#f59e0b', '#a78bfa', '#fb7185', '#22d3ee'];

const PRIORITY_STYLE = {
  GOLDEN: 'qr-chip-amber',
  NEAR_GOLDEN: 'qr-chip-blue',
  EXPERIMENTAL: 'qr-chip-slate',
};
const MODE_STYLE = {
  LIVE_TRADING: 'qr-chip-rose',
  PAPER_TRADING: 'qr-chip-amber',
  SIMULATION: 'qr-chip-blue',
};

// Overlaid equity curves
const OverlayCurves = ({ strategies, height = 180 }) => {
  // Build a unified date axis from the union of all dates
  const allPoints = strategies.flatMap(s => (s.equity_curve || []).map(p => ({ sid: s.strategy_id, ...p })));
  if (!allPoints.length) {
    return <div className="text-[10px] text-slate-600 text-center py-12">No live trades yet for any selected strategy</div>;
  }

  const allCum = strategies.flatMap(s => (s.equity_curve || []).map(p => p.cum_pnl));
  const min = Math.min(0, ...allCum);
  const max = Math.max(0, ...allCum);
  const range = (max - min) || 1;

  const allDates = Array.from(new Set(allPoints.map(p => p.date))).sort();
  const w = 800;
  const h = height;
  const step = allDates.length > 1 ? w / (allDates.length - 1) : 0;
  const dateIdx = new Map(allDates.map((d, i) => [d, i]));
  const zeroY = h - ((0 - min) / range) * h;

  return (
    <div>
      <svg viewBox={`0 0 ${w} ${h}`} preserveAspectRatio="none" className="w-full block" style={{ height }}>
        <line x1="0" y1={zeroY} x2={w} y2={zeroY} stroke="rgba(255,255,255,0.06)" strokeDasharray="3,3" />
        {strategies.map((s, idx) => {
          const points = s.equity_curve || [];
          if (!points.length) return null;
          const path = points.map((p, i) => {
            const x = (dateIdx.get(p.date) || 0) * step;
            const y = h - ((p.cum_pnl - min) / range) * h;
            return `${i === 0 ? 'M' : 'L'}${x.toFixed(1)},${y.toFixed(1)}`;
          }).join(' ');
          const color = COLORS[idx % COLORS.length];
          return <path key={s.strategy_id} d={path} stroke={color} strokeWidth="1.5" fill="none" />;
        })}
      </svg>
      {/* Legend */}
      <div className="flex items-center flex-wrap gap-x-3 gap-y-1 mt-2 px-1">
        {strategies.map((s, idx) => (
          <div key={s.strategy_id} className="flex items-center gap-1.5">
            <span className="inline-block w-3 h-px" style={{ background: COLORS[idx % COLORS.length], height: 2 }} />
            <span className="text-[10px] text-slate-300 font-mono truncate max-w-[140px]" title={s.name}>{s.name}</span>
            <span className={`qr-num text-[10px] font-bold ${pnlCl(s.metrics.live.total_pnl)}`}>{fmtK(s.metrics.live.total_pnl)}</span>
          </div>
        ))}
      </div>
    </div>
  );
};

// Comparison metric grid
const MetricRow = ({ label, values, fmtFn = (v) => v == null ? '—' : v.toFixed(2), highlight = 'max' }) => {
  // Determine best vs worst for color hinting
  const valid = values.map(v => v == null ? -Infinity : v);
  const best = highlight === 'max' ? Math.max(...valid) : Math.min(...valid);
  const worst = highlight === 'max' ? Math.min(...valid) : Math.max(...valid);
  return (
    <tr className="qr-tr-hover">
      <td className="py-1.5 px-2 qr-label text-left">{label}</td>
      {values.map((v, i) => {
        const isBest = v != null && v === (highlight === 'max' ? best : worst) && best !== worst;
        const isWorst = v != null && v === (highlight === 'max' ? worst : best) && best !== worst;
        return (
          <td key={i} className={`py-1.5 px-2 qr-num text-right text-[11px] font-bold ${
            isBest ? 'text-emerald-300' : isWorst ? 'text-rose-300' : 'text-slate-200'
          }`}>
            {fmtFn(v)}
          </td>
        );
      })}
    </tr>
  );
};

export const StrategyCompare = ({ strategyIds, onClose, onSelectStrategy }) => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!strategyIds?.length) return;
    const fetchData = async () => {
      setLoading(true);
      const ids = strategyIds.join(',');
      const res = await api.get(`/api/strategies/compare?ids=${encodeURIComponent(ids)}`);
      setData(res);
      setLoading(false);
    };
    fetchData();
    const id = setInterval(fetchData, 30000);
    return () => clearInterval(id);
  }, [strategyIds?.join(',')]);

  if (loading) {
    return (
      <div className="flex items-center gap-2 py-12 justify-center text-slate-500 text-[11px]">
        <div className="w-3 h-3 border-2 border-slate-700 border-t-blue-500 rounded-full animate-spin" />
        Loading comparison…
      </div>
    );
  }

  const strategies = (data?.strategies || []).filter(s => s.found);

  if (!strategies.length) {
    return (
      <div className="qr-surface p-6 text-center">
        <p className="text-[12px] text-slate-400">No matching strategies found</p>
        <button onClick={onClose} className="qr-btn-ghost mt-3">← Back</button>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {/* Header */}
      <div className="qr-surface px-3 py-2.5 flex items-start justify-between gap-3 flex-wrap">
        <div>
          <button onClick={onClose} className="qr-btn-ghost mb-1.5">← Performance</button>
          <h1 className="text-[15px] font-bold text-white">Compare {strategies.length} strategies</h1>
          <p className="text-[10px] text-slate-500">Side-by-side metrics · overlaid equity curves · last {data?.window_days || 90} days live</p>
        </div>
      </div>

      {/* Strategy header chips */}
      <div className="qr-surface overflow-hidden">
        <table className="w-full">
          <thead>
            <tr className="border-b border-white/[0.06]">
              <th className="qr-label text-left py-1.5 px-2 w-32">Strategy</th>
              {strategies.map((s, idx) => (
                <th key={s.strategy_id} className="py-1.5 px-2 text-right">
                  <div className="flex items-center justify-end gap-1.5">
                    <span className="inline-block w-2 h-2 rounded-full" style={{ background: COLORS[idx % COLORS.length] }} />
                    <button
                      onClick={() => onSelectStrategy?.(s.strategy_id)}
                      className="text-[11px] font-bold text-white hover:text-blue-300 truncate max-w-[140px]"
                      title={s.name}
                    >{s.name}</button>
                  </div>
                  <div className="flex items-center justify-end gap-1 mt-1">
                    {s.priority && <span className={`qr-chip ${PRIORITY_STYLE[s.priority] || 'qr-chip-slate'}`}>{s.priority}</span>}
                    {s.execution_mode && <span className={`qr-chip ${MODE_STYLE[s.execution_mode] || 'qr-chip-slate'}`}>{s.execution_mode.replace('_TRADING','').replace('SIMULATION','SIM')}</span>}
                  </div>
                  <div className="text-[9px] text-slate-500 font-mono mt-0.5">{s.strategy_id}</div>
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-white/[0.04]">
            {/* BACKTEST METRICS */}
            <tr><td colSpan={strategies.length + 1} className="qr-label py-1.5 px-2 bg-slate-900/40">Backtest</td></tr>
            <MetricRow
              label="WR (%)"
              values={strategies.map(s => s.metrics.backtest.win_rate != null ? s.metrics.backtest.win_rate * 100 : null)}
              fmtFn={(v) => v == null ? '—' : `${v.toFixed(1)}%`}
              highlight="max"
            />
            <MetricRow
              label="Profit Factor"
              values={strategies.map(s => s.metrics.backtest.profit_factor)}
              highlight="max"
            />
            <MetricRow
              label="Sharpe"
              values={strategies.map(s => s.metrics.backtest.sharpe)}
              highlight="max"
            />
            <MetricRow
              label="Max DD (%)"
              values={strategies.map(s => s.metrics.backtest.max_drawdown)}
              fmtFn={(v) => v == null ? '—' : `${v.toFixed(1)}%`}
              highlight="max"
            />
            <MetricRow
              label="BT Trades"
              values={strategies.map(s => s.metrics.backtest.total_trades)}
              fmtFn={(v) => v == null ? '—' : Math.round(v)}
              highlight="max"
            />
            <MetricRow
              label="BT Return (%)"
              values={strategies.map(s => s.metrics.backtest.total_return)}
              fmtFn={(v) => v == null ? '—' : `${v.toFixed(1)}%`}
              highlight="max"
            />

            {/* LIVE METRICS */}
            <tr><td colSpan={strategies.length + 1} className="qr-label py-1.5 px-2 bg-slate-900/40">Live</td></tr>
            <MetricRow
              label="WR (%)"
              values={strategies.map(s => s.metrics.live.win_rate != null ? s.metrics.live.win_rate * 100 : null)}
              fmtFn={(v) => v == null ? '—' : `${v.toFixed(1)}%`}
              highlight="max"
            />
            <MetricRow
              label="Profit Factor"
              values={strategies.map(s => s.metrics.live.profit_factor)}
              highlight="max"
            />
            <MetricRow
              label="Live Trades"
              values={strategies.map(s => s.metrics.live.total_trades)}
              fmtFn={(v) => v == null ? '—' : Math.round(v)}
              highlight="max"
            />
            <MetricRow
              label="Live P&L"
              values={strategies.map(s => s.metrics.live.total_pnl)}
              fmtFn={(v) => fmtK(v)}
              highlight="max"
            />
          </tbody>
        </table>
      </div>

      {/* Equity overlay */}
      <div className="qr-surface overflow-hidden">
        <div className="px-3 py-2 border-b border-white/[0.05]">
          <span className="qr-label">Equity Curves Overlay · cumulative live P&L</span>
        </div>
        <div className="p-3">
          <OverlayCurves strategies={strategies} />
        </div>
      </div>
    </div>
  );
};

export default StrategyCompare;
