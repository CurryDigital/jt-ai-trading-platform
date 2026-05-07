import React, { useState, useEffect, useMemo } from 'react';
import { api, fmtK, fmtPct, pnlCl } from '../utils';

const TIMEFRAMES = ['1W', '1M', '3M', 'YTD', 'ALL'];
const TF_DAYS = { '1W': 7, '1M': 30, '3M': 90, 'YTD': 365, 'ALL': 9999 };

const KPI = ({ l, v, sub, pos }) => (
  <div className="px-3 py-2 qr-surface min-w-0">
    <div className="qr-label truncate">{l}</div>
    <div className="qr-num text-[15px] font-bold text-white leading-tight mt-0.5">{v}</div>
    {sub && <div className={`qr-num text-[10px] mt-0.5 ${pos != null ? (pos ? 'text-emerald-400' : 'text-rose-400') : 'text-slate-500'}`}>{sub}</div>}
  </div>
);

const useSort = (defaultKey = 'absContrib') => {
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

// Waterfall chart rendered with CSS flexbox + absolute positioning
const WaterfallChart = ({ bars }) => {
  if (!bars.length) return null;

  // Compute layout: each bar has { label, value, cumStart, cumEnd }
  // We need to map cumulative values to pixel offsets
  const allValues = bars.flatMap(b => [b.cumStart, b.cumEnd]);
  const minVal = Math.min(0, ...allValues);
  const maxVal = Math.max(0, ...allValues);
  const range = maxVal - minVal || 1;

  const valToPercent = (v) => ((v - minVal) / range) * 100;
  const zeroPos = valToPercent(0);

  return (
    <div className="qr-surface p-3 space-y-0">
      {bars.map((bar, i) => {
        const left = Math.min(valToPercent(bar.cumStart), valToPercent(bar.cumEnd));
        const width = Math.abs(valToPercent(bar.cumEnd) - valToPercent(bar.cumStart));
        const isPositive = bar.value >= 0;
        const isTotal = bar.type === 'total';
        const isBaseline = bar.type === 'baseline';

        // Connector line from previous bar end to current bar start
        const showConnector = i > 0 && !isTotal;
        const connectorLeft = valToPercent(bar.cumStart);

        return (
          <div key={bar.label} className="relative" style={{ height: 36 }}>
            {/* Connector line */}
            {showConnector && (
              <div
                className="absolute top-0 border-l border-dashed border-slate-600"
                style={{ left: `${connectorLeft}%`, height: 6 }}
              />
            )}
            {/* Bar row */}
            <div className="absolute inset-0 flex items-center" style={{ top: showConnector ? 4 : 0, bottom: 0 }}>
              {/* Label on the left side */}
              <div className="absolute left-0 flex items-center gap-1.5 z-10 pointer-events-none" style={{ top: '50%', transform: 'translateY(-50%)' }}>
                <span className="text-[10px] text-slate-400 font-mono w-[100px] text-right truncate pr-1">{bar.label}</span>
              </div>
              {/* Bar area */}
              <div className="absolute right-0" style={{ left: 110 }}>
                <div className="relative w-full" style={{ height: 24 }}>
                  {/* Zero line */}
                  <div
                    className="absolute top-0 bottom-0 border-l border-slate-700/50"
                    style={{ left: `${zeroPos}%` }}
                  />
                  {/* Bar */}
                  <div
                    className={`absolute top-0.5 rounded-sm transition-all ${
                      isBaseline ? 'bg-slate-600' :
                      isTotal ? (isPositive ? 'bg-emerald-500/80' : 'bg-rose-500/80') :
                      isPositive ? 'bg-emerald-500/60' : 'bg-rose-500/60'
                    }`}
                    style={{
                      left: `${left}%`,
                      width: `${Math.max(width, 0.3)}%`,
                      height: 20,
                    }}
                  />
                  {/* Value label on bar */}
                  <div
                    className="absolute top-0 flex items-center pointer-events-none"
                    style={{
                      left: `${left + width}%`,
                      height: 22,
                      paddingLeft: 4,
                    }}
                  >
                    <span className={`text-[10px] font-mono font-bold whitespace-nowrap ${
                      isBaseline ? 'text-slate-300' : pnlCl(bar.value)
                    }`}>
                      {isBaseline ? fmtK(bar.value) : `${bar.value >= 0 ? '+' : ''}${fmtK(bar.value)}`}
                      {bar.pct != null && !isBaseline && <span className="text-slate-500 ml-1">({fmtPct(bar.pct)})</span>}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
};

// Simple daily P&L bar chart
const DailyPnlChart = ({ daily, height = 120 }) => {
  if (!daily || !daily.length) return <div className="text-[10px] text-slate-600 text-center py-8">No daily P&L data</div>;

  const maxAbs = Math.max(...daily.map(d => Math.abs(d.pnl)), 1);
  const barWidth = Math.max(1, Math.min(6, Math.floor(600 / daily.length) - 1));
  const w = daily.length * (barWidth + 1);
  const h = height;
  const mid = h / 2;

  return (
    <div className="qr-surface p-3">
      <div className="flex items-center justify-between mb-2">
        <span className="text-[10px] text-slate-500 font-mono">Daily P&L</span>
        <span className="text-[10px] text-slate-600">{daily.length} days</span>
      </div>
      <div className="overflow-x-auto">
        <svg viewBox={`0 0 ${w} ${h}`} preserveAspectRatio="none" className="w-full block" style={{ height, minWidth: Math.max(w, 200) }}>
          {/* Zero line */}
          <line x1="0" y1={mid} x2={w} y2={mid} stroke="rgba(255,255,255,0.06)" strokeDasharray="3,3" />
          {daily.map((d, i) => {
            const barH = (Math.abs(d.pnl) / maxAbs) * (mid - 4);
            const x = i * (barWidth + 1);
            const y = d.pnl >= 0 ? mid - barH : mid;
            return (
              <rect
                key={i}
                x={x}
                y={y}
                width={barWidth}
                height={Math.max(barH, 0.5)}
                rx={0.5}
                fill={d.pnl >= 0 ? 'rgba(52,211,153,0.7)' : 'rgba(251,113,133,0.7)'}
              >
                <title>{d.date}: {fmtK(d.pnl)}</title>
              </rect>
            );
          })}
        </svg>
      </div>
    </div>
  );
};

export const PnlWaterfall = ({ onBack }) => {
  const [tf, setTf] = useState('1M');
  const [stratData, setStratData] = useState(null);
  const [dailyData, setDailyData] = useState(null);
  const [loading, setLoading] = useState(true);
  const { sort, onSort, sorter } = useSort('absContrib');

  useEffect(() => {
    let cancelled = false;
    const load = async () => {
      setLoading(true);
      const [strats, daily] = await Promise.all([
        api.get('/api/performance/strategy'),
        api.get(`/api/performance/daily-pnl?days=${TF_DAYS[tf]}`),
      ]);
      if (!cancelled) {
        setStratData(strats);
        setDailyData(daily);
        setLoading(false);
      }
    };
    load();
    const interval = setInterval(load, 60000);
    return () => { cancelled = true; clearInterval(interval); };
  }, [tf]);

  // Build waterfall bars from strategy contributions
  const { bars, sortedStrategies, totalPnl, bestStrat, worstStrat } = useMemo(() => {
    if (!stratData?.strategies?.length) return { bars: [], sortedStrategies: [], totalPnl: 0, bestStrat: null, worstStrat: null };

    const strategies = stratData.strategies.map(s => ({
      ...s,
      contrib: s.contribution || 0,
      absContrib: Math.abs(s.contribution || 0),
      alloc: s.allocation || 0,
      ret: s.returns || 0,
      wr: s.win_rate ?? s.live_win_rate ?? null,
    }));

    // Sort by absolute contribution descending for waterfall
    const byAbsContrib = [...strategies].sort((a, b) => b.absContrib - a.absContrib);
    const totalPnl = byAbsContrib.reduce((sum, s) => sum + s.contrib, 0);

    // Starting equity: use a reasonable baseline; contribution is relative
    const startEquity = 1000000; // $1M baseline
    const endEquity = startEquity + totalPnl;

    const result = [];
    // Starting equity bar
    result.push({
      label: 'Starting Equity',
      value: startEquity,
      cumStart: 0,
      cumEnd: startEquity,
      type: 'baseline',
      pct: null,
    });

    // Strategy contribution bars
    let cumulative = startEquity;
    byAbsContrib.forEach(s => {
      const start = cumulative;
      cumulative += s.contrib;
      result.push({
        label: s.strategy_name || s.strategy_id,
        value: s.contrib,
        cumStart: start,
        cumEnd: cumulative,
        type: 'strategy',
        pct: startEquity ? (s.contrib / startEquity) * 100 : 0,
      });
    });

    // Net P&L total bar
    result.push({
      label: 'Net P&L',
      value: totalPnl,
      cumStart: startEquity,
      cumEnd: endEquity,
      type: 'total',
      pct: startEquity ? (totalPnl / startEquity) * 100 : 0,
    });

    const best = byAbsContrib.reduce((a, b) => (b.contrib > a.contrib ? b : a), byAbsContrib[0]);
    const worst = byAbsContrib.reduce((a, b) => (b.contrib < a.contrib ? b : a), byAbsContrib[0]);

    return { bars: result, sortedStrategies: strategies, totalPnl, bestStrat: best, worstStrat: worst };
  }, [stratData]);

  // Sort strategies for table
  const tableStrategies = useMemo(() => [...(sortedStrategies || [])].sort(sorter), [sortedStrategies, sorter]);

  // Daily data for chart
  const dailyBars = useMemo(() => dailyData?.daily || [], [dailyData]);
  const dailySummary = dailyData?.summary;

  if (loading && !stratData) {
    return (
      <div className="flex items-center justify-center py-16">
        <div className="w-5 h-5 border-2 border-slate-700 border-t-blue-500 rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {/* Header */}
      <div className="flex items-end justify-between flex-wrap gap-2">
        <div>
          <h2 className="text-sm font-bold text-white">PnL Attribution</h2>
          <p className="text-[10px] text-slate-500">Waterfall breakdown by strategy contribution</p>
        </div>
        <div className="flex items-center gap-2">
          {onBack && <button onClick={onBack} className="qr-btn-ghost">&larr; Back</button>}
          <div className="flex gap-0.5 p-0.5 rounded-md bg-slate-900/50 border border-white/[0.06]">
            {TIMEFRAMES.map(t => (
              <button
                key={t}
                onClick={() => setTf(t)}
                className={`px-2 py-1 rounded text-[10px] font-bold transition-colors ${
                  tf === t ? 'bg-blue-500 text-white' : 'text-slate-400 hover:text-white'
                }`}
              >{t}</button>
            ))}
          </div>
        </div>
      </div>

      {/* KPI row */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
        <KPI
          l="Total P&L"
          v={fmtK(totalPnl)}
          sub={fmtPct(stratData?.summary?.total_return)}
          pos={totalPnl >= 0}
        />
        <KPI
          l="Best Strategy"
          v={bestStrat ? (bestStrat.strategy_name || bestStrat.strategy_id || '').slice(0, 14) : '--'}
          sub={bestStrat ? fmtK(bestStrat.contrib) : null}
          pos={bestStrat ? bestStrat.contrib >= 0 : null}
        />
        <KPI
          l="Worst Strategy"
          v={worstStrat ? (worstStrat.strategy_name || worstStrat.strategy_id || '').slice(0, 14) : '--'}
          sub={worstStrat ? fmtK(worstStrat.contrib) : null}
          pos={worstStrat ? worstStrat.contrib >= 0 : null}
        />
        <KPI
          l="Strategies"
          v={sortedStrategies.length}
          sub={`Sharpe ${stratData?.summary?.sharpe != null ? stratData.summary.sharpe.toFixed(2) : '--'}`}
        />
      </div>

      {/* Waterfall chart */}
      <WaterfallChart bars={bars} />

      {/* Daily P&L chart */}
      <DailyPnlChart daily={dailyBars} />

      {/* Breakdown table */}
      <div className="qr-surface overflow-hidden">
        <div className="px-3 py-2 border-b border-white/[0.06]">
          <span className="text-[10px] text-slate-500 font-mono">Strategy Breakdown</span>
          {dailySummary && (
            <span className="text-[10px] text-slate-600 ml-3">Avg daily: {fmtK(dailySummary.avg_daily_pnl)}</span>
          )}
        </div>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-white/[0.06]">
                <SortableHeader label="Strategy" sortKey="strategy_name" current={sort} onSort={onSort} align="left" />
                <SortableHeader label="Contribution" sortKey="contrib" current={sort} onSort={onSort} />
                <SortableHeader label="|Contrib|" sortKey="absContrib" current={sort} onSort={onSort} />
                <SortableHeader label="Alloc %" sortKey="alloc" current={sort} onSort={onSort} />
                <SortableHeader label="Return %" sortKey="ret" current={sort} onSort={onSort} />
                <SortableHeader label="Win Rate" sortKey="wr" current={sort} onSort={onSort} />
              </tr>
            </thead>
            <tbody className="divide-y divide-white/[0.04]">
              {tableStrategies.map(s => (
                <tr key={s.strategy_id} className="qr-tr-hover">
                  <td className="py-1.5 px-2 text-left">
                    <span className="text-[11px] text-slate-200 font-mono truncate block max-w-[160px]">
                      {s.strategy_name || s.strategy_id}
                    </span>
                  </td>
                  <td className="py-1.5 px-2 text-right">
                    <span className={`qr-num text-[11px] font-bold ${pnlCl(s.contrib)}`}>{fmtK(s.contrib)}</span>
                  </td>
                  <td className="py-1.5 px-2 text-right">
                    <span className="qr-num text-[11px] text-slate-400">{fmtK(s.absContrib)}</span>
                  </td>
                  <td className="py-1.5 px-2 text-right">
                    <span className="qr-num text-[11px] text-slate-300">{fmtPct(s.alloc)}</span>
                  </td>
                  <td className="py-1.5 px-2 text-right">
                    <span className={`qr-num text-[11px] font-bold ${pnlCl(s.ret)}`}>{fmtPct(s.ret)}</span>
                  </td>
                  <td className="py-1.5 px-2 text-right">
                    {s.wr != null ? (
                      <span className={`qr-chip text-[10px] ${s.wr >= 50 ? 'qr-chip-emerald' : 'qr-chip-rose'}`}>
                        {s.wr.toFixed(1)}%
                      </span>
                    ) : (
                      <span className="text-[10px] text-slate-600">--</span>
                    )}
                  </td>
                </tr>
              ))}
              {tableStrategies.length === 0 && (
                <tr><td colSpan={6} className="py-6 text-center text-[10px] text-slate-600">No strategy data</td></tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default PnlWaterfall;
