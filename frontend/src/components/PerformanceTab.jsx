import React, { useState, useMemo, Suspense, lazy } from 'react';
import { fmtPct, pnlCl } from '../utils';

const StrategyPerformance = lazy(() => import('./StrategyPerformance'));

const TabSpinner = () => (
  <div className="flex items-center justify-center py-16">
    <div className="w-5 h-5 border-2 border-slate-700 border-t-blue-500 rounded-full animate-spin" />
  </div>
);

const KPI = ({ l, v, sub, pos, hint }) => (
  <div className="px-3 py-2 qr-surface min-w-0" title={hint}>
    <div className="qr-label truncate">{l}</div>
    <div className="qr-num text-[15px] font-bold text-white leading-tight mt-0.5">{v}</div>
    {sub && <div className={`qr-num text-[10px] mt-0.5 ${pos != null ? (pos ? 'qr-pnl-pos' : 'qr-pnl-neg') : 'text-slate-500'}`}>{sub}</div>}
  </div>
);

const useSort = (defaultKey = 'name') => {
  const [sort, setSort] = useState({ key: defaultKey, dir: 'desc' });
  const onSort = (key) => setSort(prev => ({ key, dir: prev.key === key && prev.dir === 'desc' ? 'asc' : 'desc' }));
  const sorter = (a, b) => {
    const av = a[sort.key], bv = b[sort.key];
    if (av == null && bv == null) return 0;
    if (av == null) return 1;
    if (bv == null) return -1;
    const cmp = typeof av === 'string' ? av.localeCompare(bv) : av - bv;
    return sort.dir === 'asc' ? cmp : -cmp;
  };
  return { sort, onSort, sorter };
};

const SortableHeader = ({ label, sortKey, current, onSort, align = 'right' }) => (
  <th
    className={`qr-label py-1.5 px-2 cursor-pointer select-none hover:text-white transition-colors text-${align}`}
    onClick={() => onSort(sortKey)}
  >
    {label}
    {current.key === sortKey && <span className="ml-0.5 text-blue-400">{current.dir === 'asc' ? '↑' : '↓'}</span>}
  </th>
);

export const PerformanceTab = ({ data, onSelectStrategy, onCompare, onNavigate }) => {
  const [tf, setTf] = useState('1M');
  const [view, setView] = useState('overview');
  const [selected, setSelected] = useState(new Set());
  const { sort, onSort, sorter } = useSort('returns');

  const toggleSel = (id) => setSelected(prev => {
    const next = new Set(prev);
    if (next.has(id)) next.delete(id);
    else if (next.size < 6) next.add(id);
    return next;
  });
  const clearSel = () => setSelected(new Set());

  const strategies = useMemo(() => [...(data.strategies || [])].sort(sorter), [data.strategies, sort]);
  const bestStrategy = strategies[0];
  const liveCount = strategies.filter(s => s.live_trades > 0).length;
  const avgLiveWR = (() => {
    const live = strategies.filter(s => s.live_win_rate != null);
    return live.length > 0 ? live.reduce((a, s) => a + s.live_win_rate, 0) / live.length : null;
  })();
  const totalTrades = strategies.reduce((a, s) => a + (s.live_trades || 0), 0);

  if (view === 'analytics') {
    return (
      <div className="space-y-3">
        <div className="flex items-end justify-between">
          <div>
            <h2 className="text-sm font-bold text-white">Deep Analytics</h2>
            <p className="text-[10px] text-slate-500">Comprehensive strategy attribution & risk metrics</p>
          </div>
          <button onClick={() => setView('overview')} className="qr-btn-ghost">← Overview</button>
        </div>
        <Suspense fallback={<TabSpinner />}><StrategyPerformance /></Suspense>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      <div className="flex items-end justify-between flex-wrap gap-2">
        <div>
          <h2 className="text-sm font-bold text-white">Performance</h2>
          <p className="text-[10px] text-slate-500">Backtest vs live attribution · sortable comparison</p>
        </div>
        <div className="flex items-center gap-2">
          {selected.size > 0 && (
            <>
              <span className="text-[10px] text-slate-500">{selected.size} selected</span>
              <button onClick={clearSel} className="qr-btn-ghost">Clear</button>
              <button
                onClick={() => onCompare?.(Array.from(selected))}
                disabled={selected.size < 2}
                className={`qr-btn-primary ${selected.size < 2 ? 'opacity-50 cursor-not-allowed' : ''}`}
              >Compare ({selected.size}) →</button>
            </>
          )}
          <button onClick={() => onNavigate?.('hft')} className="qr-btn-ghost">HFT Matrix</button>
          <button onClick={() => setView('analytics')} className="qr-btn-primary">Deep Analytics →</button>
          <div className="flex gap-0.5 p-0.5 rounded-md bg-slate-900/50 border border-white/[0.06]">
            {['1W', '1M', '3M', '1Y', 'ALL'].map(t =>
              <button key={t} onClick={() => setTf(t)} className={`px-2 py-1 rounded text-[10px] font-bold transition-colors ${tf === t ? 'bg-blue-500 text-white' : 'text-slate-400 hover:text-white'}`}>{t}</button>
            )}
          </div>
        </div>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
        <KPI l="Active Strategies" v={liveCount} sub={`of ${strategies.length}`} />
        <KPI l="Avg Live WR" v={avgLiveWR != null ? `${avgLiveWR.toFixed(1)}%` : '—'} pos={avgLiveWR != null && avgLiveWR >= 50} />
        <KPI l="Total Trades" v={totalTrades} sub={tf} />
        <KPI l="Best" v={bestStrategy?.strategy_name?.slice(0, 12) || '—'} sub={bestStrategy?.returns != null ? fmtPct(bestStrategy.returns) : null} pos={(bestStrategy?.returns || 0) >= 0} />
      </div>

      <div className="qr-surface overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-white/[0.06]">
                <th className="qr-label py-1.5 px-2 w-6"></th>
                <SortableHeader label="Strategy"  sortKey="strategy_name"      current={sort} onSort={onSort} align="left" />
                <SortableHeader label="Asset"     sortKey="asset_class"        current={sort} onSort={onSort} align="left" />
                <SortableHeader label="Tier"      sortKey="tier"               current={sort} onSort={onSort} />
                <SortableHeader label="BT WR"     sortKey="backtest_win_rate"  current={sort} onSort={onSort} />
                <SortableHeader label="Live WR"   sortKey="live_win_rate"      current={sort} onSort={onSort} />
                <SortableHeader label="Δ WR"      sortKey="wr_delta"           current={sort} onSort={onSort} />
                <SortableHeader label="BT PF"     sortKey="backtest_pf"        current={sort} onSort={onSort} />
                <SortableHeader label="Live PF"   sortKey="live_profit_factor" current={sort} onSort={onSort} />
                <SortableHeader label="Trades"    sortKey="live_trades"        current={sort} onSort={onSort} />
                <SortableHeader label="Returns"   sortKey="returns"            current={sort} onSort={onSort} />
              </tr>
            </thead>
            <tbody className="divide-y divide-white/[0.04]">
              {strategies.map(s => {
                const delta = s.backtest_win_rate != null && s.live_win_rate != null ? s.live_win_rate - s.backtest_win_rate : null;
                const isSel = selected.has(s.strategy_id);
                return (
                  <tr key={s.strategy_id} className="qr-tr-hover">
                    <td className="py-1 px-2 text-center" onClick={(e) => { e.stopPropagation(); toggleSel(s.strategy_id); }}>
                      <input
                        type="checkbox"
                        checked={isSel}
                        onChange={() => {}}
                        disabled={!isSel && selected.size >= 6}
                        className="w-3 h-3 accent-blue-500 cursor-pointer"
                      />
                    </td>
                    <td className="py-1 px-2 cursor-pointer" onClick={() => onSelectStrategy?.(s.strategy_id)}>
                      <div className="font-bold text-white text-[12px] truncate max-w-[200px] hover:text-blue-300">{s.strategy_name || s.strategy_id}</div>
                      {s.priority && <div className="qr-label">{s.priority}</div>}
                    </td>
                    <td className="py-1 px-2 text-[10px] text-slate-400">{s.asset_class || '—'}</td>
                    <td className="py-1 px-2 text-right">
                      <span className={`qr-chip ${s.tier?.includes('T1') ? 'qr-chip-emerald' : s.tier?.includes('T2') ? 'qr-chip-amber' : 'qr-chip-slate'}`}>{s.tier || 'T4'}</span>
                    </td>
                    <td className="py-1 px-2 qr-num text-slate-400">{s.backtest_win_rate != null ? `${s.backtest_win_rate.toFixed(0)}%` : '—'}</td>
                    <td className={`py-1 px-2 qr-num font-bold ${pnlCl((s.live_win_rate || 0) - 50)}`}>{s.live_win_rate != null ? `${s.live_win_rate.toFixed(0)}%` : '—'}</td>
                    <td className={`py-1 px-2 qr-num ${pnlCl(delta)}`}>{delta != null ? `${delta >= 0 ? '+' : ''}${delta.toFixed(0)}pp` : '—'}</td>
                    <td className="py-1 px-2 qr-num text-slate-400">{s.backtest_pf?.toFixed(2) || '—'}</td>
                    <td className={`py-1 px-2 qr-num ${pnlCl(s.live_profit_factor != null ? s.live_profit_factor - 1.5 : null)}`}>{s.live_profit_factor?.toFixed(2) || '—'}</td>
                    <td className="py-1 px-2 qr-num text-slate-300">{s.live_trades || 0}</td>
                    <td className={`py-1 px-2 qr-num font-bold ${pnlCl(s.returns)}`}>{s.returns != null ? fmtPct(s.returns) : '—'}</td>
                  </tr>
                );
              })}
              {!strategies.length && (
                <tr><td colSpan={11} className="py-8 text-center text-slate-600 text-[11px]">No deployed strategies · approve from the Strategies tab</td></tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default PerformanceTab;
