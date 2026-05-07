import React, { useState, useEffect, useMemo, useCallback } from 'react';
import { api, fmtK, fmtPct, pnlCl } from '../utils';

/* ── helpers ────────────────────────────────────────────────── */

const INPUT_CL =
  'px-2 py-1.5 bg-slate-800/80 border border-white/10 rounded-lg text-xs text-white placeholder-slate-600 focus:outline-none focus:border-blue-500/50';

const todayISO = () => new Date().toISOString().slice(0, 10);
const daysAgoISO = (n) => {
  const d = new Date();
  d.setDate(d.getDate() - n);
  return d.toISOString().slice(0, 10);
};

const POSITION_SIZES = [0.5, 1, 1.5, 2];
const FEE_OPTIONS = [0, 5, 10, 20];

const fmtDollars = (n) => {
  if (n == null || isNaN(n)) return '--';
  const abs = Math.abs(n);
  const sign = n < 0 ? '-' : n > 0 ? '+' : '';
  if (abs >= 1e6) return `${sign}$${(abs / 1e6).toFixed(2)}M`;
  if (abs >= 1e3) return `${sign}$${(abs / 1e3).toFixed(1)}K`;
  return `${sign}$${abs.toFixed(0)}`;
};

/* ── SVG chart constants ────────────────────────────────────── */

const CHART_W = 800;
const CHART_H = 260;
const PAD = { t: 16, r: 16, b: 36, l: 64 };
const PLOT_W = CHART_W - PAD.l - PAD.r;
const PLOT_H = CHART_H - PAD.t - PAD.b;

/* ── SVG line chart ─────────────────────────────────────────── */

const LineChart = ({ data, title, yFormatter = fmtDollars }) => {
  const [hover, setHover] = useState(null);

  const { xScale, yScale, yMin, yMax, yTicks } = useMemo(() => {
    if (!data || data.length === 0)
      return { xScale: () => 0, yScale: () => 0, yMin: 0, yMax: 0, yTicks: [] };

    const allVals = data.flatMap((d) => [d.original, d.adjusted].filter((v) => v != null));
    let mn = Math.min(0, ...allVals);
    let mx = Math.max(0, ...allVals);
    if (mn === mx) { mn -= 1; mx += 1; }
    const margin = (mx - mn) * 0.08;
    mn -= margin;
    mx += margin;

    const xs = (i) => PAD.l + (i / Math.max(1, data.length - 1)) * PLOT_W;
    const ys = (v) => PAD.t + PLOT_H - ((v - mn) / (mx - mn)) * PLOT_H;

    const tickCount = 5;
    const step = (mx - mn) / (tickCount - 1);
    const ticks = Array.from({ length: tickCount }, (_, i) => mn + step * i);

    return { xScale: xs, yScale: ys, yMin: mn, yMax: mx, yTicks: ticks };
  }, [data]);

  if (!data || data.length === 0) return null;

  const origPoints = data.map((d, i) => `${xScale(i)},${yScale(d.original)}`).join(' ');
  const adjPoints = data.map((d, i) => `${xScale(i)},${yScale(d.adjusted)}`).join(' ');

  // polygon for delta fill between the two lines
  const fillPoints =
    data.map((d, i) => `${xScale(i)},${yScale(d.original)}`).join(' ') +
    ' ' +
    data
      .map((d, i) => `${xScale(data.length - 1 - i)},${yScale(data[data.length - 1 - i].adjusted)}`)
      .join(' ');

  // date labels on x-axis
  const labelEvery = Math.max(1, Math.floor(data.length / 8));
  const dateLabels = data.filter((_, i) => i % labelEvery === 0 || i === data.length - 1);
  const dateLabelIndices = data
    .map((_, i) => i)
    .filter((i) => i % labelEvery === 0 || i === data.length - 1);

  const handleMouseMove = useCallback(
    (e) => {
      const svg = e.currentTarget;
      const rect = svg.getBoundingClientRect();
      const x = ((e.clientX - rect.left) / rect.width) * CHART_W;
      const idx = Math.round(((x - PAD.l) / PLOT_W) * (data.length - 1));
      if (idx >= 0 && idx < data.length) setHover(idx);
    },
    [data]
  );

  return (
    <div className="qr-surface p-3">
      <div className="flex items-center justify-between mb-2">
        <span className="text-sm font-bold text-white">{title}</span>
        {hover != null && data[hover] && (
          <div className="flex items-center gap-3 text-[10px]">
            <span className="text-slate-400">{data[hover].date}</span>
            <span className="text-blue-400">Orig {yFormatter(data[hover].original)}</span>
            <span className="text-amber-400">Adj {yFormatter(data[hover].adjusted)}</span>
          </div>
        )}
      </div>
      <svg
        viewBox={`0 0 ${CHART_W} ${CHART_H}`}
        className="w-full"
        onMouseMove={handleMouseMove}
        onMouseLeave={() => setHover(null)}
      >
        {/* grid lines */}
        {yTicks.map((t, i) => (
          <g key={i}>
            <line
              x1={PAD.l}
              y1={yScale(t)}
              x2={CHART_W - PAD.r}
              y2={yScale(t)}
              stroke="rgba(255,255,255,0.04)"
              strokeWidth="1"
            />
            <text
              x={PAD.l - 6}
              y={yScale(t) + 3}
              textAnchor="end"
              fill="#94a3b8"
              fontSize="9"
            >
              {yFormatter(t)}
            </text>
          </g>
        ))}

        {/* zero line */}
        {yMin < 0 && yMax > 0 && (
          <line
            x1={PAD.l}
            y1={yScale(0)}
            x2={CHART_W - PAD.r}
            y2={yScale(0)}
            stroke="rgba(255,255,255,0.08)"
            strokeWidth="1"
            strokeDasharray="4,3"
          />
        )}

        {/* x-axis date labels */}
        {dateLabelIndices.map((idx) => (
          <text
            key={idx}
            x={xScale(idx)}
            y={CHART_H - 4}
            textAnchor="middle"
            fill="#64748b"
            fontSize="8"
          >
            {data[idx].date.slice(5)}
          </text>
        ))}

        {/* delta fill */}
        <polygon points={fillPoints} fill="rgba(251,191,36,0.06)" />

        {/* original line */}
        <polyline points={origPoints} fill="none" stroke="#3b82f6" strokeWidth="2" />

        {/* adjusted line */}
        <polyline points={adjPoints} fill="none" stroke="#f59e0b" strokeWidth="2" strokeDasharray="6,3" />

        {/* hover crosshair */}
        {hover != null && (
          <>
            <line
              x1={xScale(hover)}
              y1={PAD.t}
              x2={xScale(hover)}
              y2={PAD.t + PLOT_H}
              stroke="rgba(255,255,255,0.15)"
              strokeWidth="1"
            />
            <circle cx={xScale(hover)} cy={yScale(data[hover].original)} r="3" fill="#3b82f6" />
            <circle cx={xScale(hover)} cy={yScale(data[hover].adjusted)} r="3" fill="#f59e0b" />
          </>
        )}
      </svg>
      <div className="flex items-center gap-4 mt-1.5 ml-16 text-[9px]">
        <span className="flex items-center gap-1">
          <span className="inline-block w-3 h-0.5 bg-blue-500 rounded" />
          <span className="text-slate-500">Original</span>
        </span>
        <span className="flex items-center gap-1">
          <span className="inline-block w-3 h-0.5 bg-amber-500 rounded border-dashed" />
          <span className="text-slate-500">Adjusted</span>
        </span>
      </div>
    </div>
  );
};

/* ── bar chart (daily comparison) ───────────────────────────── */

const BAR_H = 180;

const BarChart = ({ data, title }) => {
  const [hover, setHover] = useState(null);

  const { yMin, yMax, yScale, yTicks, barW } = useMemo(() => {
    if (!data || data.length === 0)
      return { yMin: 0, yMax: 0, yScale: () => 0, yTicks: [], barW: 0 };

    const allVals = data.flatMap((d) => [d.original, d.adjusted]);
    let mn = Math.min(0, ...allVals);
    let mx = Math.max(0, ...allVals);
    if (mn === mx) { mn -= 1; mx += 1; }
    const margin = (mx - mn) * 0.1;
    mn -= margin;
    mx += margin;

    const ys = (v) => PAD.t + (BAR_H - PAD.t - PAD.b) - ((v - mn) / (mx - mn)) * (BAR_H - PAD.t - PAD.b);
    const bw = Math.max(2, PLOT_W / data.length / 2.6);

    const tickCount = 5;
    const step = (mx - mn) / (tickCount - 1);
    const ticks = Array.from({ length: tickCount }, (_, i) => mn + step * i);

    return { yMin: mn, yMax: mx, yScale: ys, yTicks: ticks, barW: bw };
  }, [data]);

  if (!data || data.length === 0) return null;

  const zero = yScale(0);
  const labelEvery = Math.max(1, Math.floor(data.length / 10));

  return (
    <div className="qr-surface p-3">
      <div className="flex items-center justify-between mb-2">
        <span className="text-sm font-bold text-white">{title}</span>
        {hover != null && data[hover] && (
          <div className="flex items-center gap-3 text-[10px]">
            <span className="text-slate-400">{data[hover].date}</span>
            <span className="text-blue-400">Orig {fmtDollars(data[hover].original)}</span>
            <span className="text-amber-400">Adj {fmtDollars(data[hover].adjusted)}</span>
          </div>
        )}
      </div>
      <svg
        viewBox={`0 0 ${CHART_W} ${BAR_H}`}
        className="w-full"
        onMouseMove={(e) => {
          const rect = e.currentTarget.getBoundingClientRect();
          const x = ((e.clientX - rect.left) / rect.width) * CHART_W;
          const idx = Math.round(((x - PAD.l) / PLOT_W) * (data.length - 1));
          if (idx >= 0 && idx < data.length) setHover(idx);
        }}
        onMouseLeave={() => setHover(null)}
      >
        {yTicks.map((t, i) => (
          <g key={i}>
            <line
              x1={PAD.l}
              y1={yScale(t)}
              x2={CHART_W - PAD.r}
              y2={yScale(t)}
              stroke="rgba(255,255,255,0.04)"
            />
            <text x={PAD.l - 6} y={yScale(t) + 3} textAnchor="end" fill="#94a3b8" fontSize="9">
              {fmtDollars(t)}
            </text>
          </g>
        ))}

        {/* zero line */}
        <line
          x1={PAD.l}
          y1={zero}
          x2={CHART_W - PAD.r}
          y2={zero}
          stroke="rgba(255,255,255,0.08)"
          strokeWidth="1"
        />

        {data.map((d, i) => {
          const cx = PAD.l + (i / Math.max(1, data.length - 1)) * PLOT_W;
          const origH = Math.abs(yScale(d.original) - zero);
          const adjH = Math.abs(yScale(d.adjusted) - zero);
          const origY = d.original >= 0 ? zero - origH : zero;
          const adjY = d.adjusted >= 0 ? zero - adjH : zero;

          return (
            <g key={i} opacity={hover != null && hover !== i ? 0.35 : 1}>
              <rect
                x={cx - barW - 0.5}
                y={origY}
                width={barW}
                height={Math.max(0.5, origH)}
                fill={d.original >= 0 ? '#3b82f6' : '#3b82f680'}
                rx="1"
              />
              <rect
                x={cx + 0.5}
                y={adjY}
                width={barW}
                height={Math.max(0.5, adjH)}
                fill={d.adjusted >= 0 ? '#f59e0b' : '#f59e0b80'}
                rx="1"
              />
            </g>
          );
        })}

        {/* x-axis labels */}
        {data.map(
          (d, i) =>
            (i % labelEvery === 0 || i === data.length - 1) && (
              <text
                key={i}
                x={PAD.l + (i / Math.max(1, data.length - 1)) * PLOT_W}
                y={BAR_H - 4}
                textAnchor="middle"
                fill="#64748b"
                fontSize="8"
              >
                {d.date.slice(5)}
              </text>
            )
        )}

        {/* hover highlight */}
        {hover != null && (
          <line
            x1={PAD.l + (hover / Math.max(1, data.length - 1)) * PLOT_W}
            y1={PAD.t}
            x2={PAD.l + (hover / Math.max(1, data.length - 1)) * PLOT_W}
            y2={BAR_H - PAD.b}
            stroke="rgba(255,255,255,0.1)"
            strokeWidth="1"
          />
        )}
      </svg>
    </div>
  );
};

/* ── summary card ───────────────────────────────────────────── */

const SummaryCard = ({ label, value, sub, positive }) => (
  <div className="qr-surface px-3 py-2.5 min-w-0">
    <div className="qr-label truncate">{label}</div>
    <div
      className={`text-[15px] font-bold leading-tight mt-0.5 ${
        positive == null ? 'text-white' : positive ? 'text-emerald-400' : 'text-rose-400'
      }`}
    >
      {value}
    </div>
    {sub && <div className="text-[10px] text-slate-500 mt-0.5">{sub}</div>}
  </div>
);

/* ── spinner ────────────────────────────────────────────────── */

const Spinner = ({ text }) => (
  <div className="qr-surface px-3 py-6 flex items-center justify-center gap-2 text-[11px] text-slate-500">
    <div className="w-3 h-3 border-2 border-slate-700 border-t-blue-500 rounded-full animate-spin" />
    {text}
  </div>
);

/* ══════════════════════════════════════════════════════════════
   TradeReplay
   ══════════════════════════════════════════════════════════════ */

export const TradeReplay = ({ onBack }) => {
  /* ── configuration state ──────────────────────────────────── */
  const [startDate, setStartDate] = useState(daysAgoISO(30));
  const [endDate, setEndDate] = useState(todayISO());
  const [strategies, setStrategies] = useState([]);
  const [selectedIds, setSelectedIds] = useState(new Set());
  const [posMultiplier, setPosMultiplier] = useState(1);
  const [feeBps, setFeeBps] = useState(0);
  const [stopLossPct, setStopLossPct] = useState('');

  /* ── data state ───────────────────────────────────────────── */
  const [loadingStrategies, setLoadingStrategies] = useState(true);
  const [running, setRunning] = useState(false);
  const [rawData, setRawData] = useState(null); // { [strategy_id]: [{ date, pnl }] }
  const [hasRun, setHasRun] = useState(false);

  /* ── fetch strategy list on mount ─────────────────────────── */
  useEffect(() => {
    (async () => {
      const res = await api.get('/api/strategies/researcher');
      if (res?.strategies) {
        setStrategies(res.strategies);
        // auto-select all
        setSelectedIds(new Set(res.strategies.map((s) => s.strategy_id)));
      }
      setLoadingStrategies(false);
    })();
  }, []);

  /* ── toggle strategy selection ────────────────────────────── */
  const toggleStrategy = useCallback((id) => {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }, []);

  const selectAll = useCallback(() => {
    setSelectedIds(new Set(strategies.map((s) => s.strategy_id)));
  }, [strategies]);

  const selectNone = useCallback(() => {
    setSelectedIds(new Set());
  }, []);

  /* ── run replay ───────────────────────────────────────────── */
  const runReplay = useCallback(async () => {
    if (selectedIds.size === 0) return;
    setRunning(true);

    const results = {};

    await Promise.all(
      Array.from(selectedIds).map(async (id) => {
        // try strategy-specific PnL first, fall back to paper
        let res = await api.get(
          `/api/strategies/${encodeURIComponent(id)}/daily-pnl?start_date=${startDate}&end_date=${endDate}`
        );
        if (!res?.daily) {
          res = await api.get(`/api/paper-strategies/${encodeURIComponent(id)}/daily-pnl`);
        }
        if (res?.daily) {
          results[id] = res.daily
            .filter((d) => d.date >= startDate && d.date <= endDate)
            .sort((a, b) => a.date.localeCompare(b.date));
        }
      })
    );

    setRawData(results);
    setHasRun(true);
    setRunning(false);
  }, [selectedIds, startDate, endDate]);

  /* ── compute adjusted data ────────────────────────────────── */
  const replayResults = useMemo(() => {
    if (!rawData) return null;

    // aggregate daily PnL across all selected strategies
    const dateMap = {};
    Object.values(rawData).forEach((days) => {
      days.forEach((d) => {
        if (!dateMap[d.date]) dateMap[d.date] = 0;
        dateMap[d.date] += d.pnl || 0;
      });
    });

    const sortedDates = Object.keys(dateMap).sort();
    if (sortedDates.length === 0) return null;

    const stopLoss = stopLossPct !== '' ? parseFloat(stopLossPct) : null;
    // assume a baseline equity of the total absolute PnL * 10 or at least 100k
    const totalAbsPnl = sortedDates.reduce((s, dt) => s + Math.abs(dateMap[dt]), 0);
    const startingEquity = Math.max(100000, totalAbsPnl * 10);

    let cumOrig = 0;
    let cumAdj = 0;
    let maxCumOrig = 0;
    let maxCumAdj = 0;
    let stopped = false;

    const daily = sortedDates.map((date) => {
      const origPnl = dateMap[date];

      let adjPnl;
      if (stopped) {
        adjPnl = 0;
      } else {
        adjPnl = origPnl * posMultiplier;
        adjPnl -= Math.abs(origPnl) * posMultiplier * (feeBps / 10000);

        // check stop loss
        const tentativeCum = cumAdj + adjPnl;
        if (stopLoss != null && tentativeCum < -(stopLoss / 100) * startingEquity) {
          stopped = true;
          adjPnl = -(stopLoss / 100) * startingEquity - cumAdj; // clamp to exactly the stop level
        }
      }

      cumOrig += origPnl;
      cumAdj += adjPnl;

      maxCumOrig = Math.max(maxCumOrig, cumOrig);
      maxCumAdj = Math.max(maxCumAdj, cumAdj);

      const ddOrig = cumOrig - maxCumOrig;
      const ddAdj = cumAdj - maxCumAdj;

      return {
        date,
        origPnl,
        adjPnl,
        cumOrig,
        cumAdj,
        ddOrig,
        ddAdj,
      };
    });

    const totalOrig = daily[daily.length - 1].cumOrig;
    const totalAdj = daily[daily.length - 1].cumAdj;
    const delta = totalAdj - totalOrig;
    const maxDdOrig = Math.min(...daily.map((d) => d.ddOrig));
    const maxDdAdj = Math.min(...daily.map((d) => d.ddAdj));

    return {
      daily,
      totalOrig,
      totalAdj,
      delta,
      maxDdOrig,
      maxDdAdj,
      startingEquity,
    };
  }, [rawData, posMultiplier, feeBps, stopLossPct]);

  /* ── chart-ready arrays ───────────────────────────────────── */
  const cumData = useMemo(() => {
    if (!replayResults) return [];
    return replayResults.daily.map((d) => ({
      date: d.date,
      original: d.cumOrig,
      adjusted: d.cumAdj,
    }));
  }, [replayResults]);

  const dailyData = useMemo(() => {
    if (!replayResults) return [];
    return replayResults.daily.map((d) => ({
      date: d.date,
      original: d.origPnl,
      adjusted: d.adjPnl,
    }));
  }, [replayResults]);

  const ddData = useMemo(() => {
    if (!replayResults) return [];
    return replayResults.daily.map((d) => ({
      date: d.date,
      original: d.ddOrig,
      adjusted: d.ddAdj,
    }));
  }, [replayResults]);

  /* ── render ───────────────────────────────────────────────── */
  return (
    <div className="space-y-3">
      {/* header */}
      <div className="flex items-end justify-between flex-wrap gap-2">
        <div>
          <h2 className="text-sm font-bold text-white tracking-tight">Trade Replay</h2>
          <p className="text-[10px] text-slate-500">
            Scenario testing -- replay historical fills with adjusted parameters
          </p>
        </div>
        {onBack && (
          <button onClick={onBack} className="qr-btn-ghost text-[11px]">
            &larr; Back
          </button>
        )}
      </div>

      {/* ── configuration panel ─────────────────────────────── */}
      <div className="qr-surface p-3 space-y-3">
        <span className="qr-label">Configuration</span>

        {/* date range */}
        <div className="flex flex-wrap items-end gap-3">
          <div>
            <label className="text-[10px] text-slate-500 block mb-0.5">Start Date</label>
            <input
              type="date"
              value={startDate}
              onChange={(e) => setStartDate(e.target.value)}
              className={INPUT_CL}
            />
          </div>
          <div>
            <label className="text-[10px] text-slate-500 block mb-0.5">End Date</label>
            <input
              type="date"
              value={endDate}
              onChange={(e) => setEndDate(e.target.value)}
              className={INPUT_CL}
            />
          </div>
        </div>

        {/* strategy selector */}
        <div>
          <div className="flex items-center gap-2 mb-1">
            <label className="text-[10px] text-slate-500">Strategies</label>
            <button onClick={selectAll} className="text-[9px] text-blue-400 hover:text-blue-300">
              All
            </button>
            <button onClick={selectNone} className="text-[9px] text-slate-500 hover:text-slate-400">
              None
            </button>
          </div>
          {loadingStrategies ? (
            <Spinner text="Loading strategies..." />
          ) : strategies.length === 0 ? (
            <div className="text-[11px] text-slate-500">No strategies found</div>
          ) : (
            <div className="flex flex-wrap gap-1.5 max-h-28 overflow-y-auto pr-1">
              {strategies.map((s) => {
                const checked = selectedIds.has(s.strategy_id);
                return (
                  <label
                    key={s.strategy_id}
                    className={`flex items-center gap-1 px-2 py-1 rounded-md cursor-pointer text-[10px] transition-colors ${
                      checked
                        ? 'bg-blue-500/15 text-blue-300 border border-blue-500/30'
                        : 'bg-slate-800/60 text-slate-400 border border-white/5 hover:border-white/10'
                    }`}
                  >
                    <input
                      type="checkbox"
                      checked={checked}
                      onChange={() => toggleStrategy(s.strategy_id)}
                      className="sr-only"
                    />
                    <span
                      className={`w-2.5 h-2.5 rounded-sm border flex items-center justify-center ${
                        checked ? 'border-blue-400 bg-blue-500/30' : 'border-slate-600 bg-slate-800'
                      }`}
                    >
                      {checked && (
                        <svg viewBox="0 0 10 10" className="w-2 h-2 text-blue-300">
                          <polyline
                            points="2,5 4,7.5 8,2.5"
                            fill="none"
                            stroke="currentColor"
                            strokeWidth="1.8"
                            strokeLinecap="round"
                            strokeLinejoin="round"
                          />
                        </svg>
                      )}
                    </span>
                    {s.strategy_name || s.strategy_id}
                  </label>
                );
              })}
            </div>
          )}
        </div>

        {/* scenario adjustments */}
        <div className="flex flex-wrap items-end gap-4">
          {/* position size multiplier */}
          <div>
            <label className="text-[10px] text-slate-500 block mb-1">Position Multiplier</label>
            <div className="flex gap-1">
              {POSITION_SIZES.map((m) => (
                <button
                  key={m}
                  onClick={() => setPosMultiplier(m)}
                  className={`px-2.5 py-1 rounded-md text-[10px] font-medium transition-colors ${
                    posMultiplier === m
                      ? 'bg-blue-500/20 text-blue-300 border border-blue-500/40'
                      : 'bg-slate-800/60 text-slate-400 border border-white/5 hover:border-white/10'
                  }`}
                >
                  {m}x
                </button>
              ))}
            </div>
          </div>

          {/* fee adjustment */}
          <div>
            <label className="text-[10px] text-slate-500 block mb-1">Fee Adjustment</label>
            <div className="flex gap-1">
              {FEE_OPTIONS.map((f) => (
                <button
                  key={f}
                  onClick={() => setFeeBps(f)}
                  className={`px-2.5 py-1 rounded-md text-[10px] font-medium transition-colors ${
                    feeBps === f
                      ? 'bg-amber-500/20 text-amber-300 border border-amber-500/40'
                      : 'bg-slate-800/60 text-slate-400 border border-white/5 hover:border-white/10'
                  }`}
                >
                  {f}bps
                </button>
              ))}
            </div>
          </div>

          {/* stop loss override */}
          <div>
            <label className="text-[10px] text-slate-500 block mb-1">Stop Loss Override (%)</label>
            <input
              type="number"
              min="0"
              max="100"
              step="0.5"
              placeholder="e.g. 5"
              value={stopLossPct}
              onChange={(e) => setStopLossPct(e.target.value)}
              className={`${INPUT_CL} w-24`}
            />
          </div>
        </div>

        {/* run button */}
        <div className="flex items-center gap-3 pt-1">
          <button
            onClick={runReplay}
            disabled={running || selectedIds.size === 0}
            className={`qr-btn-primary px-4 py-1.5 text-xs font-medium ${
              running || selectedIds.size === 0 ? 'opacity-50 cursor-not-allowed' : ''
            }`}
          >
            {running ? 'Running...' : 'Run Replay'}
          </button>
          <span className="text-[10px] text-slate-500">
            {selectedIds.size} strateg{selectedIds.size === 1 ? 'y' : 'ies'} selected
          </span>
        </div>
      </div>

      {/* ── loading state ───────────────────────────────────── */}
      {running && <Spinner text="Fetching historical data and computing replay..." />}

      {/* ── empty state ─────────────────────────────────────── */}
      {hasRun && !running && !replayResults && (
        <div className="qr-surface px-3 py-6 text-center text-[11px] text-slate-500">
          No PnL data found for the selected strategies and date range.
        </div>
      )}

      {/* ── results ─────────────────────────────────────────── */}
      {replayResults && !running && (
        <div className="space-y-3">
          {/* summary cards */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
            <SummaryCard
              label="Original P&L"
              value={fmtDollars(replayResults.totalOrig)}
              sub={`${replayResults.daily.length} trading days`}
              positive={replayResults.totalOrig >= 0}
            />
            <SummaryCard
              label="Adjusted P&L"
              value={fmtDollars(replayResults.totalAdj)}
              sub={`${posMultiplier}x size, ${feeBps}bps fee`}
              positive={replayResults.totalAdj >= 0}
            />
            <SummaryCard
              label="Delta"
              value={fmtDollars(replayResults.delta)}
              sub={
                replayResults.totalOrig !== 0
                  ? fmtPct(((replayResults.delta) / Math.abs(replayResults.totalOrig)) * 100)
                  : '--'
              }
              positive={replayResults.delta >= 0}
            />
            <SummaryCard
              label="Max Drawdown"
              value={fmtDollars(replayResults.maxDdAdj)}
              sub={`Orig: ${fmtDollars(replayResults.maxDdOrig)}`}
              positive={null}
            />
          </div>

          {/* cumulative P&L chart */}
          <LineChart data={cumData} title="Cumulative P&L" />

          {/* daily comparison bars */}
          <BarChart data={dailyData} title="Daily P&L Comparison" />

          {/* drawdown chart */}
          <LineChart data={ddData} title="Drawdown" />
        </div>
      )}
    </div>
  );
};

export default TradeReplay;
