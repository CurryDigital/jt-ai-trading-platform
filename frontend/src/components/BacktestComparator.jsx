import React, { useEffect, useState, useMemo } from 'react';
import { api, fmt, fmtPct, fmtK, pnlCl } from '../utils';

const METRIC_DEFS = [
  { key: 'avg_win_rate',   label: 'Win Rate',       format: v => fmtPct(v), best: 'max' },
  { key: 'avg_sharpe',     label: 'Sharpe',         format: v => fmt(v, 2),  best: 'max' },
  { key: 'avg_score',      label: 'Score',           format: v => fmt(v, 1),  best: 'max' },
  { key: 'total_return',   label: 'Total Return',    format: v => fmtPct(v), best: 'max' },
  { key: 'max_drawdown',   label: 'Max Drawdown',    format: v => fmtPct(v), best: 'min_abs' },
  { key: 'ticker_count',   label: 'Tickers',         format: v => v ?? '—',  best: 'max' },
];

const bestIdx = (vals, mode) => {
  if (!vals.length) return -1;
  const nums = vals.map(v => (v == null || isNaN(v)) ? null : Number(v));
  if (nums.every(v => v === null)) return -1;
  if (mode === 'min_abs') {
    let best = Infinity, idx = -1;
    nums.forEach((v, i) => { if (v !== null && Math.abs(v) < best) { best = Math.abs(v); idx = i; } });
    return idx;
  }
  let best = -Infinity, idx = -1;
  nums.forEach((v, i) => { if (v !== null && v > best) { best = v; idx = i; } });
  return idx;
};

const COLORS = ['blue', 'violet', 'amber', 'emerald', 'rose', 'cyan'];
const colorCl = (i) => `text-${COLORS[i % COLORS.length]}-400`;

export const BacktestComparator = ({ onSelectStrategy }) => {
  const [strategies, setStrategies] = useState([]);
  const [selected, setSelected] = useState([]);
  const [comparison, setComparison] = useState(null);
  const [busy, setBusy] = useState(false);
  const [loadingList, setLoadingList] = useState(true);
  const [search, setSearch] = useState('');
  const [view, setView] = useState('browse');

  useEffect(() => {
    (async () => {
      const res = await api.get('/api/backtests/strategies');
      if (res?.strategies) setStrategies(res.strategies);
      setLoadingList(false);
    })();
  }, []);

  const filtered = useMemo(() => {
    if (!search) return strategies;
    const q = search.toLowerCase();
    return strategies.filter(s =>
      s.strategy_id?.toLowerCase().includes(q) ||
      s.strategy_name?.toLowerCase().includes(q) ||
      s.asset_class?.toLowerCase().includes(q)
    );
  }, [strategies, search]);

  const toggleSelect = (id) => {
    setSelected(prev =>
      prev.includes(id)
        ? prev.filter(x => x !== id)
        : prev.length < 6 ? [...prev, id] : prev
    );
  };

  const doCompare = async () => {
    if (selected.length < 2) return;
    setBusy(true);
    const res = await api.get(`/api/backtests/compare?ids=${selected.join(',')}`);
    setBusy(false);
    if (res?.strategies) {
      setComparison(res);
      setView('compare');
    }
  };

  if (loadingList) {
    return (
      <div className="qr-surface px-3 py-6 flex items-center justify-center gap-2 text-[11px] text-slate-500">
        <div className="w-3 h-3 border-2 border-slate-700 border-t-blue-500 rounded-full animate-spin" />
        Loading backtest data…
      </div>
    );
  }

  if (view === 'compare' && comparison) {
    const strats = comparison.strategies;
    return (
      <div className="space-y-3">
        <div className="flex items-end justify-between flex-wrap gap-2">
          <div>
            <h2 className="text-sm font-bold text-white tracking-tight">Backtest Comparison</h2>
            <p className="text-[10px] text-slate-500">Side-by-side metrics for {strats.length} strategies</p>
          </div>
          <button onClick={() => setView('browse')} className="qr-btn-ghost text-[11px]">← Back to list</button>
        </div>

        {/* Metrics comparison table */}
        <div className="qr-surface overflow-hidden">
          <div className="px-3 py-2 border-b border-white/[0.05]">
            <span className="qr-label">Aggregate Metrics</span>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="qr-th-sticky">
                <tr className="border-b border-white/[0.06]">
                  <th className="qr-label text-left py-1.5 px-3">Metric</th>
                  {strats.map((s, i) => (
                    <th key={s.strategy_id} className={`qr-label text-right py-1.5 px-3 ${colorCl(i)}`}>
                      <button onClick={() => onSelectStrategy?.(s.strategy_id)} className="hover:underline">
                        {s.strategy_id}
                      </button>
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-white/[0.04]">
                <tr className="qr-tr-hover">
                  <td className="py-1.5 px-3 text-[11px] text-slate-400">Strategy Name</td>
                  {strats.map((s, i) => (
                    <td key={s.strategy_id} className={`py-1.5 px-3 text-[11px] text-right font-mono ${colorCl(i)}`}>
                      {s.strategy_name || '—'}
                    </td>
                  ))}
                </tr>
                {METRIC_DEFS.map(m => {
                  const vals = strats.map(s => s.aggregate?.[m.key]);
                  const best = bestIdx(vals, m.best);
                  return (
                    <tr key={m.key} className="qr-tr-hover">
                      <td className="py-1.5 px-3 text-[11px] text-slate-400">{m.label}</td>
                      {strats.map((s, i) => (
                        <td key={s.strategy_id} className={`py-1.5 px-3 qr-num text-right ${i === best ? 'text-white font-bold' : 'text-slate-400'}`}>
                          {m.format(s.aggregate?.[m.key])}
                        </td>
                      ))}
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>

        {/* Per-strategy ticker drilldowns */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-3">
          {strats.map((s, si) => (
            <div key={s.strategy_id} className="qr-surface overflow-hidden">
              <div className="px-3 py-2 border-b border-white/[0.05] flex items-center justify-between">
                <span className={`qr-label ${colorCl(si)}`}>{s.strategy_id} — Top Tickers</span>
                <span className="text-[10px] text-slate-500">{s.tickers?.length || 0} tickers</span>
              </div>
              <div className="overflow-x-auto max-h-60 overflow-y-auto">
                <table className="w-full">
                  <thead className="qr-th-sticky">
                    <tr className="border-b border-white/[0.06]">
                      <th className="qr-label text-left py-1 px-2">Ticker</th>
                      <th className="qr-label text-right py-1 px-2">Win Rate</th>
                      <th className="qr-label text-right py-1 px-2">Sharpe</th>
                      <th className="qr-label text-right py-1 px-2">Score</th>
                      <th className="qr-label text-right py-1 px-2">Return</th>
                      <th className="qr-label text-right py-1 px-2">DD</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-white/[0.04]">
                    {(s.tickers || []).map(t => (
                      <tr key={t.ticker} className="qr-tr-hover">
                        <td className="py-1 px-2 text-[11px] font-mono text-white">{t.ticker}</td>
                        <td className={`py-1 px-2 qr-num ${pnlCl(t.win_rate != null ? t.win_rate - 50 : null)}`}>{fmtPct(t.win_rate)}</td>
                        <td className={`py-1 px-2 qr-num ${pnlCl(t.sharpe)}`}>{fmt(t.sharpe, 2)}</td>
                        <td className="py-1 px-2 qr-num text-slate-300">{fmt(t.score, 1)}</td>
                        <td className={`py-1 px-2 qr-num ${pnlCl(t.total_return)}`}>{fmtPct(t.total_return)}</td>
                        <td className="py-1 px-2 qr-num text-rose-300">{fmtPct(t.max_drawdown)}</td>
                      </tr>
                    ))}
                    {!s.tickers?.length && (
                      <tr><td colSpan={6} className="py-4 text-center text-slate-600 text-[11px]">No ticker data</td></tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      <div className="flex items-end justify-between flex-wrap gap-2">
        <div>
          <h2 className="text-sm font-bold text-white tracking-tight">Backtest Comparator</h2>
          <p className="text-[10px] text-slate-500">Select 2–6 strategies to compare backtest metrics side-by-side</p>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-[10px] text-slate-500">{selected.length}/6 selected</span>
          <button
            onClick={doCompare}
            disabled={selected.length < 2 || busy}
            className={`px-3 py-1 rounded text-[11px] font-semibold transition-colors ${
              selected.length >= 2
                ? 'bg-blue-500/20 text-blue-300 hover:bg-blue-500/30 ring-1 ring-blue-500/30'
                : 'bg-slate-800 text-slate-500 cursor-not-allowed'
            }`}
          >
            {busy ? 'Loading…' : `Compare (${selected.length})`}
          </button>
        </div>
      </div>

      {/* Search */}
      <div className="qr-surface px-3 py-2">
        <input
          type="text"
          value={search}
          onChange={e => setSearch(e.target.value)}
          placeholder="Filter strategies…"
          className="w-full bg-transparent text-[11px] text-white placeholder:text-slate-600 outline-none"
        />
      </div>

      {/* Strategy list */}
      <div className="qr-surface overflow-hidden">
        <div className="px-3 py-2 border-b border-white/[0.05]">
          <span className="qr-label">Strategies with Backtest Data ({filtered.length})</span>
        </div>
        <div className="overflow-x-auto max-h-[500px] overflow-y-auto">
          <table className="w-full">
            <thead className="qr-th-sticky">
              <tr className="border-b border-white/[0.06]">
                <th className="py-1.5 px-2 w-6"></th>
                <th className="qr-label text-left py-1.5 px-2">Strategy</th>
                <th className="qr-label text-left py-1.5 px-2">Name</th>
                <th className="qr-label text-left py-1.5 px-2">Asset</th>
                <th className="qr-label text-right py-1.5 px-2">Tickers</th>
                <th className="qr-label text-right py-1.5 px-2">Avg WR</th>
                <th className="qr-label text-right py-1.5 px-2">Avg Sharpe</th>
                <th className="qr-label text-right py-1.5 px-2">Avg Score</th>
                <th className="qr-label text-right py-1.5 px-2">Best WR</th>
                <th className="qr-label text-right py-1.5 px-2">Best Ticker</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/[0.04]">
              {filtered.map(s => {
                const checked = selected.includes(s.strategy_id);
                return (
                  <tr
                    key={s.strategy_id}
                    onClick={() => toggleSelect(s.strategy_id)}
                    className={`qr-tr-hover cursor-pointer ${checked ? 'bg-blue-500/[0.06]' : ''}`}
                  >
                    <td className="py-1.5 px-2 text-center">
                      <div className={`w-3.5 h-3.5 rounded border ${checked ? 'bg-blue-500 border-blue-400' : 'border-slate-600'} flex items-center justify-center`}>
                        {checked && <span className="text-[9px] text-white font-bold">✓</span>}
                      </div>
                    </td>
                    <td className="py-1.5 px-2 text-[10px] font-mono text-slate-300 truncate max-w-[120px]">
                      <button onClick={e => { e.stopPropagation(); onSelectStrategy?.(s.strategy_id); }} className="hover:text-blue-300">
                        {s.strategy_id}
                      </button>
                    </td>
                    <td className="py-1.5 px-2 text-[11px] text-white truncate max-w-[180px]">{s.strategy_name || '—'}</td>
                    <td className="py-1.5 px-2 text-[10px] text-slate-400">{s.asset_class || '—'}</td>
                    <td className="py-1.5 px-2 qr-num text-slate-300">{s.ticker_count}</td>
                    <td className={`py-1.5 px-2 qr-num ${pnlCl(s.avg_win_rate != null ? s.avg_win_rate - 50 : null)}`}>{fmtPct(s.avg_win_rate)}</td>
                    <td className={`py-1.5 px-2 qr-num ${pnlCl(s.avg_sharpe)}`}>{fmt(s.avg_sharpe, 2)}</td>
                    <td className="py-1.5 px-2 qr-num text-slate-300">{fmt(s.avg_score, 1)}</td>
                    <td className={`py-1.5 px-2 qr-num font-bold ${pnlCl(s.best_win_rate != null ? s.best_win_rate - 50 : null)}`}>{fmtPct(s.best_win_rate)}</td>
                    <td className="py-1.5 px-2 text-[10px] font-mono text-slate-400">{s.best_ticker || '—'}</td>
                  </tr>
                );
              })}
              {!filtered.length && (
                <tr><td colSpan={10} className="py-8 text-center text-slate-600 text-[11px]">
                  {strategies.length ? 'No strategies match filter' : 'No backtest data available'}
                </td></tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default BacktestComparator;
