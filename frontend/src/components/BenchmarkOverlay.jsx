import React, { useState, useEffect, useMemo, useRef } from 'react';
import { api, fmtK, fmtPct, pnlCl } from '../utils';

const BENCHMARKS = [
  { key: 'spx',  ticker: '^GSPC',   label: 'S&P 500',   color: '#3b82f6', chip: 'qr-chip-blue'   },
  { key: 'hsi',  ticker: '^HSI',    label: 'Hang Seng',  color: '#f59e0b', chip: 'qr-chip-amber'  },
  { key: 'btc',  ticker: 'BTC-USD', label: 'Bitcoin',    color: '#8b5cf6', chip: 'qr-chip-violet' },
];
const PORTFOLIO = { key: 'portfolio', label: 'Portfolio', color: '#22c55e', chip: 'qr-chip-emerald' };

const TIMEFRAMES = [
  { key: '1M',  days: 30  },
  { key: '3M',  days: 90  },
  { key: '6M',  days: 180 },
  { key: 'YTD', days: null },
  { key: '1Y',  days: 365 },
];

const ytdDays = () => {
  const now = new Date();
  const jan1 = new Date(now.getFullYear(), 0, 1);
  return Math.ceil((now - jan1) / 86400000);
};

const timeframeParam = (key) => {
  if (key === 'YTD') return 'ytd';
  if (key === '1Y') return '1y';
  if (key === '6M') return '6m';
  if (key === '3M') return '3m';
  return '1m';
};

const daysForTf = (key) => {
  const found = TIMEFRAMES.find(t => t.key === key);
  if (!found) return 30;
  return found.days ?? ytdDays();
};

// --- Math helpers ---
const stddev = (arr) => {
  if (arr.length < 2) return 0;
  const mean = arr.reduce((a, b) => a + b, 0) / arr.length;
  const sq = arr.reduce((a, v) => a + (v - mean) ** 2, 0) / (arr.length - 1);
  return Math.sqrt(sq);
};

const maxDrawdown = (series) => {
  let peak = -Infinity;
  let dd = 0;
  for (const v of series) {
    if (v > peak) peak = v;
    const cur = (v - peak) / Math.max(Math.abs(peak), 1e-12);
    if (cur < dd) dd = cur;
  }
  return dd * 100;
};

const correlation = (a, b) => {
  const n = Math.min(a.length, b.length);
  if (n < 3) return 0;
  const ma = a.slice(0, n).reduce((s, v) => s + v, 0) / n;
  const mb = b.slice(0, n).reduce((s, v) => s + v, 0) / n;
  let num = 0, da = 0, db = 0;
  for (let i = 0; i < n; i++) {
    const xa = a[i] - ma, xb = b[i] - mb;
    num += xa * xb;
    da += xa * xa;
    db += xb * xb;
  }
  const denom = Math.sqrt(da * db);
  return denom < 1e-12 ? 0 : num / denom;
};

const dailyReturns = (values) => {
  const ret = [];
  for (let i = 1; i < values.length; i++) {
    ret.push(values[i - 1] !== 0 ? (values[i] - values[i - 1]) / Math.abs(values[i - 1]) : 0);
  }
  return ret;
};

// Normalize series to percentage change from first value
const normalize = (values) => {
  if (!values.length) return [];
  const base = values[0];
  if (base === 0) return values.map(() => 0);
  return values.map(v => ((v / base) - 1) * 100);
};

// --- SVG Chart ---
const CHART_W = 800;
const CHART_H = 300;
const PAD = { top: 20, right: 60, bottom: 30, left: 55 };
const INNER_W = CHART_W - PAD.left - PAD.right;
const INNER_H = CHART_H - PAD.top - PAD.bottom;

const NormalizedChart = ({ allSeries, dates, enabled }) => {
  const svgRef = useRef(null);
  const [hover, setHover] = useState(null);

  const visible = useMemo(
    () => allSeries.filter(s => enabled.has(s.key) && s.values.length > 0),
    [allSeries, enabled]
  );

  const normalized = useMemo(
    () => visible.map(s => ({ ...s, norm: normalize(s.values) })),
    [visible]
  );

  const { minY, maxY, yTicks } = useMemo(() => {
    let mn = 0, mx = 0;
    for (const s of normalized) {
      for (const v of s.norm) {
        if (v < mn) mn = v;
        if (v > mx) mx = v;
      }
    }
    const margin = Math.max(Math.abs(mx - mn) * 0.1, 5);
    mn = Math.floor((mn - margin) / 5) * 5;
    mx = Math.ceil((mx + margin) / 5) * 5;
    const ticks = [];
    const step = Math.max(5, Math.round((mx - mn) / 8 / 5) * 5) || 5;
    for (let v = mn; v <= mx; v += step) ticks.push(v);
    return { minY: mn, maxY: mx, yTicks: ticks };
  }, [normalized]);

  const n = dates.length;

  const toX = (i) => PAD.left + (n > 1 ? (i / (n - 1)) * INNER_W : INNER_W / 2);
  const toY = (v) => PAD.top + INNER_H - ((v - minY) / (maxY - minY || 1)) * INNER_H;

  const polyline = (norm, color) => {
    if (norm.length === 0) return null;
    const pts = norm.map((v, i) => `${toX(i).toFixed(1)},${toY(v).toFixed(1)}`).join(' ');
    return <polyline key={color} points={pts} fill="none" stroke={color} strokeWidth="1.5" strokeLinejoin="round" />;
  };

  const handleMouse = (e) => {
    const svg = svgRef.current;
    if (!svg || n === 0) return;
    const rect = svg.getBoundingClientRect();
    const scaleX = CHART_W / rect.width;
    const mx = (e.clientX - rect.left) * scaleX;
    const idx = Math.round(((mx - PAD.left) / INNER_W) * (n - 1));
    if (idx >= 0 && idx < n) {
      setHover(idx);
    }
  };

  const xLabelStep = Math.max(1, Math.floor(n / 8));

  return (
    <div className="qr-surface p-3">
      <svg
        ref={svgRef}
        viewBox={`0 0 ${CHART_W} ${CHART_H}`}
        className="w-full"
        style={{ maxHeight: 340 }}
        onMouseMove={handleMouse}
        onMouseLeave={() => setHover(null)}
      >
        {/* grid lines */}
        {yTicks.map(v => (
          <g key={v}>
            <line
              x1={PAD.left} x2={CHART_W - PAD.right}
              y1={toY(v)} y2={toY(v)}
              stroke={v === 0 ? 'rgba(148,163,184,0.25)' : 'rgba(148,163,184,0.08)'}
              strokeWidth={v === 0 ? 1 : 0.5}
              strokeDasharray={v === 0 ? '' : '4 3'}
            />
            <text
              x={PAD.left - 6} y={toY(v) + 3}
              textAnchor="end"
              fill="#64748b"
              fontSize="9"
              fontFamily="JetBrains Mono, monospace"
            >
              {v >= 0 ? '+' : ''}{v}%
            </text>
          </g>
        ))}

        {/* x-axis labels */}
        {dates.map((d, i) =>
          i % xLabelStep === 0 ? (
            <text
              key={i}
              x={toX(i)} y={CHART_H - 6}
              textAnchor="middle"
              fill="#64748b"
              fontSize="8"
              fontFamily="JetBrains Mono, monospace"
            >
              {d.slice(5)}
            </text>
          ) : null
        )}

        {/* series lines */}
        {normalized.map(s => polyline(s.norm, s.color))}

        {/* crosshair */}
        {hover != null && hover >= 0 && hover < n && (
          <>
            <line
              x1={toX(hover)} x2={toX(hover)}
              y1={PAD.top} y2={PAD.top + INNER_H}
              stroke="rgba(148,163,184,0.3)"
              strokeWidth="1"
              strokeDasharray="3 2"
            />
            {/* tooltip background */}
            <rect
              x={toX(hover) + (hover > n * 0.7 ? -140 : 8)}
              y={PAD.top + 4}
              width="130"
              height={18 + normalized.length * 14}
              rx="4"
              fill="rgba(10,13,18,0.92)"
              stroke="rgba(148,163,184,0.15)"
              strokeWidth="0.5"
            />
            <text
              x={toX(hover) + (hover > n * 0.7 ? -132 : 16)}
              y={PAD.top + 17}
              fill="#94a3b8"
              fontSize="9"
              fontFamily="JetBrains Mono, monospace"
            >
              {dates[hover]}
            </text>
            {normalized.map((s, si) => {
              const val = hover < s.norm.length ? s.norm[hover] : null;
              return val != null ? (
                <g key={s.key}>
                  <circle
                    cx={toX(hover) + (hover > n * 0.7 ? -132 : 16)}
                    cy={PAD.top + 30 + si * 14}
                    r="3"
                    fill={s.color}
                  />
                  <text
                    x={toX(hover) + (hover > n * 0.7 ? -122 : 26)}
                    y={PAD.top + 34 + si * 14}
                    fill={s.color}
                    fontSize="9"
                    fontFamily="JetBrains Mono, monospace"
                  >
                    {s.label}: {val >= 0 ? '+' : ''}{val.toFixed(2)}%
                  </text>
                </g>
              ) : null;
            })}
          </>
        )}
      </svg>
    </div>
  );
};

// --- Summary Table ---
const calcStats = (values) => {
  if (!values || values.length < 2) return { ret: null, mdd: null, vol: null, sharpe: null };
  const norm = normalize(values);
  const ret = norm[norm.length - 1];
  const mdd = maxDrawdown(values);
  const dr = dailyReturns(values);
  const vol = stddev(dr) * 100;
  const meanDr = dr.reduce((a, b) => a + b, 0) / dr.length;
  const volRaw = stddev(dr);
  const sharpe = volRaw > 1e-12 ? (meanDr / volRaw) * Math.sqrt(252) : 0;
  return { ret, mdd, vol, sharpe };
};

const SummaryTable = ({ allSeries, enabled }) => {
  const rows = useMemo(() => {
    const visible = allSeries.filter(s => enabled.has(s.key) && s.values.length > 1);
    return visible.map(s => ({ ...s, stats: calcStats(s.values) }));
  }, [allSeries, enabled]);

  if (rows.length === 0) return null;

  const bestReturn = Math.max(...rows.map(r => r.stats.ret ?? -Infinity));

  return (
    <div className="qr-surface overflow-hidden">
      <div className="px-3 py-2">
        <span className="qr-label">Performance Summary</span>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="border-t border-white/[0.06]">
              <th className="qr-label py-1.5 px-3 text-left">Benchmark</th>
              <th className="qr-label py-1.5 px-3 text-right">Return %</th>
              <th className="qr-label py-1.5 px-3 text-right">Max DD</th>
              <th className="qr-label py-1.5 px-3 text-right">Volatility</th>
              <th className="qr-label py-1.5 px-3 text-right">Sharpe</th>
            </tr>
          </thead>
          <tbody>
            {rows.map(r => (
              <tr key={r.key} className="qr-tr-hover border-t border-white/[0.06]">
                <td className="py-1.5 px-3">
                  <div className="flex items-center gap-2">
                    <span className="inline-block w-2 h-2 rounded-full" style={{ background: r.color }} />
                    <span className="text-[11px] font-semibold text-slate-200">{r.label}</span>
                    {r.stats.ret != null && r.stats.ret === bestReturn && (
                      <span className="qr-chip-emerald" style={{ fontSize: 8, padding: '0 4px' }}>BEST</span>
                    )}
                  </div>
                </td>
                <td className={`qr-num py-1.5 px-3 text-[11px] font-bold ${pnlCl(r.stats.ret)}`}>
                  {r.stats.ret != null ? fmtPct(r.stats.ret) : '--'}
                </td>
                <td className="qr-num py-1.5 px-3 text-[11px] font-bold text-rose-400">
                  {r.stats.mdd != null ? `${r.stats.mdd.toFixed(2)}%` : '--'}
                </td>
                <td className="qr-num py-1.5 px-3 text-[11px] font-bold text-slate-300">
                  {r.stats.vol != null ? `${r.stats.vol.toFixed(2)}%` : '--'}
                </td>
                <td className={`qr-num py-1.5 px-3 text-[11px] font-bold ${pnlCl(r.stats.sharpe)}`}>
                  {r.stats.sharpe != null ? r.stats.sharpe.toFixed(2) : '--'}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

// --- Correlation Matrix ---
const CorrelationMatrix = ({ allSeries, enabled }) => {
  const visible = useMemo(
    () => allSeries.filter(s => enabled.has(s.key) && s.values.length > 2),
    [allSeries, enabled]
  );

  const matrix = useMemo(() => {
    const drs = visible.map(s => dailyReturns(s.values));
    const n = visible.length;
    const mat = Array.from({ length: n }, () => Array(n).fill(0));
    for (let i = 0; i < n; i++) {
      for (let j = 0; j < n; j++) {
        mat[i][j] = i === j ? 1 : correlation(drs[i], drs[j]);
      }
    }
    return mat;
  }, [visible]);

  if (visible.length < 2) return null;

  const cellBg = (v) => {
    const abs = Math.abs(v);
    if (abs > 0.7) return `rgba(244,63,94,${0.15 + abs * 0.5})`;
    if (abs > 0.4) return `rgba(251,146,60,${0.15 + abs * 0.4})`;
    if (abs > 0.1) return `rgba(250,204,21,${0.1 + abs * 0.3})`;
    return 'rgba(100,116,139,0.05)';
  };

  return (
    <div className="qr-surface p-3">
      <div className="flex items-center justify-between mb-2">
        <span className="qr-label">Return Correlation Matrix</span>
        <span className="text-[10px] text-slate-500">{visible.length} series</span>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr>
              <th className="py-0.5 px-1"></th>
              {visible.map(s => (
                <th key={s.key} className="qr-label text-[8px] font-mono text-slate-500 px-1 pb-1 truncate max-w-[60px]" title={s.label}>
                  {s.label.length > 8 ? s.label.slice(0, 8) : s.label}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {visible.map((s, i) => (
              <tr key={s.key}>
                <td className="qr-label text-[9px] font-mono text-slate-400 pr-2 text-right truncate max-w-[80px]" title={s.label}>
                  {s.label.length > 10 ? s.label.slice(0, 10) : s.label}
                </td>
                {matrix[i].map((v, j) => (
                  <td
                    key={j}
                    className="text-center text-[9px] font-mono"
                    style={{ background: cellBg(v), color: Math.abs(v) > 0.5 ? '#fff' : '#94a3b8', minWidth: 32, height: 24 }}
                    title={`${visible[i].label} / ${visible[j].label}: ${(v * 100).toFixed(0)}%`}
                  >
                    {i === j ? '--' : (v * 100).toFixed(0)}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="mt-2 text-[9px] text-slate-600">
        Values show Pearson correlation (%) of daily returns. Higher absolute values indicate co-movement.
      </div>
    </div>
  );
};

// --- Main Component ---
export const BenchmarkOverlay = ({ onBack }) => {
  const [tf, setTf] = useState('3M');
  const [enabled, setEnabled] = useState(new Set(['portfolio', 'spx', 'hsi', 'btc']));
  const [benchData, setBenchData] = useState({});
  const [portfolioData, setPortfolioData] = useState(null);
  const [loading, setLoading] = useState(true);

  const toggle = (key) => {
    setEnabled(prev => {
      const next = new Set(prev);
      if (next.has(key)) next.delete(key);
      else next.add(key);
      return next;
    });
  };

  // Fetch data when timeframe changes
  useEffect(() => {
    let cancelled = false;
    setLoading(true);

    const fetchAll = async () => {
      const days = daysForTf(tf);
      const tfParam = timeframeParam(tf);

      // Fetch portfolio PnL
      const pnlPromise = api.get(`/api/performance/daily-pnl?days=${days}`);

      // Fetch benchmark data via stocks endpoint
      const benchPromises = BENCHMARKS.map(b =>
        api.get(`/api/stocks/${encodeURIComponent(b.ticker)}?timeframe=${tfParam}`)
      );

      const [pnl, ...benchResults] = await Promise.all([pnlPromise, ...benchPromises]);

      if (cancelled) return;

      // Process portfolio
      if (pnl?.daily) {
        setPortfolioData(pnl.daily);
      }

      // Process benchmarks
      const bd = {};
      BENCHMARKS.forEach((b, i) => {
        const res = benchResults[i];
        if (res?.chart_data?.length) {
          bd[b.key] = res.chart_data;
        }
      });
      setBenchData(bd);
      setLoading(false);
    };

    fetchAll();
    return () => { cancelled = true; };
  }, [tf]);

  // Build unified series with aligned dates
  const { allSeries, dates } = useMemo(() => {
    // Collect all date sets
    const benchSeries = BENCHMARKS.map(b => {
      const raw = benchData[b.key] || [];
      const dateMap = {};
      raw.forEach(d => { dateMap[d.date] = d.close; });
      return { ...b, dateMap };
    });

    // Portfolio cumulative PnL as "value" series
    const portRaw = portfolioData || [];
    const portDateMap = {};
    let cum = 0;
    // Build cumulative values; use 10000 as nominal base equity
    const BASE_EQUITY = 10000;
    portRaw.forEach(d => {
      cum += (d.pnl || 0);
      portDateMap[d.date] = BASE_EQUITY + cum;
    });

    // Gather all dates across all series and sort
    const allDates = new Set();
    benchSeries.forEach(s => Object.keys(s.dateMap).forEach(d => allDates.add(d)));
    Object.keys(portDateMap).forEach(d => allDates.add(d));
    const sortedDates = [...allDates].sort();

    if (sortedDates.length === 0) {
      return { allSeries: [], dates: [] };
    }

    // Build value arrays aligned to dates
    const buildValues = (dateMap) => {
      const vals = [];
      let last = null;
      for (const d of sortedDates) {
        if (dateMap[d] != null) {
          last = dateMap[d];
        }
        if (last != null) vals.push({ date: d, value: last });
      }
      // Re-align to only include dates where we have data
      return vals;
    };

    const portValues = buildValues(portDateMap);
    const series = [
      { ...PORTFOLIO, values: portValues.map(v => v.value) },
      ...benchSeries.map(b => {
        const bv = buildValues(b.dateMap);
        return { key: b.key, label: b.label, color: b.color, chip: b.chip, values: bv.map(v => v.value) };
      }),
    ];

    // Use sorted dates for x-axis
    return { allSeries: series, dates: sortedDates };
  }, [benchData, portfolioData]);

  return (
    <div className="space-y-3">
      {/* Header */}
      <div className="flex items-end justify-between flex-wrap gap-2">
        <div>
          <h2 className="text-sm font-bold text-white">Benchmark Comparison</h2>
          <p className="text-[10px] text-slate-500">Portfolio returns vs market indices -- normalized view</p>
        </div>
        <div className="flex items-center gap-2">
          {/* Timeframe pills */}
          {TIMEFRAMES.map(t => (
            <button
              key={t.key}
              onClick={() => setTf(t.key)}
              className={tf === t.key ? 'qr-btn-primary' : 'qr-btn-ghost'}
            >
              {t.key}
            </button>
          ))}
          {onBack && (
            <button onClick={onBack} className="qr-btn-ghost ml-2">
              Back
            </button>
          )}
        </div>
      </div>

      {/* Benchmark selector */}
      <div className="flex items-center gap-3 flex-wrap">
        <span className="qr-label">Series</span>
        {[PORTFOLIO, ...BENCHMARKS].map(b => {
          const active = enabled.has(b.key);
          return (
            <label
              key={b.key}
              className="flex items-center gap-1.5 cursor-pointer select-none"
              title={b.ticker || 'Portfolio PnL'}
            >
              <input
                type="checkbox"
                checked={active}
                onChange={() => toggle(b.key)}
                className="sr-only"
              />
              <span
                className="inline-block w-3 h-3 rounded border transition-colors"
                style={{
                  borderColor: b.color,
                  background: active ? b.color : 'transparent',
                }}
              />
              <span className={`text-[10px] font-semibold ${active ? 'text-slate-200' : 'text-slate-600'}`}>
                {b.label}
              </span>
            </label>
          );
        })}
      </div>

      {/* Loading */}
      {loading && (
        <div className="flex items-center justify-center py-12">
          <div className="w-5 h-5 border-2 border-slate-700 border-t-blue-500 rounded-full animate-spin" />
        </div>
      )}

      {/* Chart */}
      {!loading && dates.length > 0 && (
        <NormalizedChart allSeries={allSeries} dates={dates} enabled={enabled} />
      )}

      {!loading && dates.length === 0 && (
        <div className="qr-surface p-6 text-center">
          <span className="text-[11px] text-slate-500">No data available for the selected timeframe.</span>
        </div>
      )}

      {/* Legend */}
      {!loading && dates.length > 0 && (
        <div className="flex items-center gap-4 flex-wrap px-1">
          {allSeries.filter(s => enabled.has(s.key) && s.values.length > 0).map(s => {
            const norm = normalize(s.values);
            const last = norm.length > 0 ? norm[norm.length - 1] : null;
            return (
              <div key={s.key} className="flex items-center gap-1.5">
                <span className="inline-block w-2 h-2 rounded-full" style={{ background: s.color }} />
                <span className="text-[10px] font-semibold text-slate-300">{s.label}</span>
                <span className={`text-[10px] font-mono font-bold ${pnlCl(last)}`}>
                  {last != null ? fmtPct(last) : '--'}
                </span>
              </div>
            );
          })}
        </div>
      )}

      {/* Summary Table */}
      {!loading && allSeries.length > 0 && (
        <SummaryTable allSeries={allSeries} enabled={enabled} />
      )}

      {/* Correlation Matrix */}
      {!loading && allSeries.length > 0 && (
        <CorrelationMatrix allSeries={allSeries} enabled={enabled} />
      )}
    </div>
  );
};

export default BenchmarkOverlay;
