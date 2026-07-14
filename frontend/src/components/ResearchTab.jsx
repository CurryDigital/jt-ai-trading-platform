import React, { useState, useMemo } from 'react';
import { api, usePoll, pnlCl, fmtPct } from '../utils';

// Research > Screener — one filterable, sortable table across the whole signal
// universe (all markets). Complements the per-market card views (Signals) and
// the regime/macro views (Macro) with a single "slice & rank everything" surface.

const MARKET_META = {
  US:     { label: 'US',     hex: '#3b82f6' },
  HK:     { label: 'HK',     hex: '#f43f5e' },
  ETF:    { label: 'ETF',    hex: '#8b5cf6' },
  CRYPTO: { label: 'Crypto', hex: '#14b8a6' },
  FX:     { label: 'FX',     hex: '#0ea5e9' },
  METAL:  { label: 'Metals', hex: '#eab308' },
};
const MARKETS = Object.keys(MARKET_META);

const HORIZONS = [
  { key: 'fwd_5d',  label: '5D' },
  { key: 'fwd_20d', label: '20D' },
  { key: 'fwd_1q',  label: '1Q' },
];

const signedPct = (v) => (v == null ? '—' : `${v >= 0 ? '+' : ''}${Number(v).toFixed(2)}%`);

const COLUMNS = [
  { key: 'ticker',     label: 'Ticker',    align: 'left'  },
  { key: 'market',     label: 'Market',    align: 'left'  },
  { key: 'direction',  label: 'Dir',       align: 'left'  },
  { key: 'potential',  label: 'Score',     align: 'right' },
  { key: 'change_pct', label: 'Today',     align: 'right' },
  { key: 'fwd_5d',     label: '5D',        align: 'right' },
  { key: 'fwd_20d',    label: '20D',       align: 'right' },
  { key: 'fwd_1q',     label: '1Q',        align: 'right' },
  { key: 'note',       label: 'Rationale', align: 'left'  },
];

export const ResearchTab = ({ onOpenStrategy }) => {
  const [universe, setUniverse] = useState({});
  const [families, setFamilies] = useState([]);
  const [asOf, setAsOf] = useState(null);
  const [loading, setLoading] = useState(true);

  // filters
  const [marketFilter, setMarketFilter] = useState(new Set(MARKETS));
  const [dirFilter, setDirFilter] = useState('ALL'); // ALL | BUY | SELL
  const [minScore, setMinScore] = useState(0);
  const [search, setSearch] = useState('');
  const [sort, setSort] = useState({ key: 'potential', dir: 'desc' });

  usePoll(async () => {
    const [uni, fam] = await Promise.all([
      api.get(`/api/signals/universe?markets=${MARKETS.join(',')}&limit=50`),
      api.get('/api/signals/families'),
    ]);
    setUniverse(uni?.data || {});
    setAsOf(uni?.as_of || null);
    setFamilies(fam?.data || []);
    setLoading(false);
  }, 300000);

  const familyByKey = useMemo(() => {
    const m = {};
    families.forEach(f => { m[f.key] = f; });
    return m;
  }, [families]);

  const allRows = useMemo(() => {
    const rows = [];
    Object.entries(universe).forEach(([market, list]) => {
      (list || []).forEach(s => rows.push({ ...s, market }));
    });
    return rows;
  }, [universe]);

  const filtered = useMemo(() => {
    const q = search.trim().toUpperCase();
    let rows = allRows.filter(r =>
      marketFilter.has(r.market) &&
      (dirFilter === 'ALL' || r.direction === dirFilter) &&
      (r.potential == null || r.potential >= minScore) &&
      (!q || (r.ticker || '').toUpperCase().includes(q) || (r.name || '').toUpperCase().includes(q))
    );
    const { key, dir } = sort;
    const mul = dir === 'asc' ? 1 : -1;
    rows.sort((a, b) => {
      let av = a[key], bv = b[key];
      if (key === 'ticker' || key === 'market' || key === 'direction' || key === 'note') {
        av = (av || '').toString(); bv = (bv || '').toString();
        return av.localeCompare(bv) * mul;
      }
      av = av == null ? -Infinity : av; bv = bv == null ? -Infinity : bv;
      return (av - bv) * mul;
    });
    return rows;
  }, [allRows, marketFilter, dirFilter, minScore, search, sort]);

  const toggleMarket = (m) => {
    setMarketFilter(prev => {
      const next = new Set(prev);
      if (next.has(m)) next.delete(m); else next.add(m);
      return next.size === 0 ? new Set(MARKETS) : next;
    });
  };

  const onSort = (key) => {
    setSort(prev => prev.key === key
      ? { key, dir: prev.dir === 'asc' ? 'desc' : 'asc' }
      : { key, dir: key === 'ticker' || key === 'market' ? 'asc' : 'desc' });
  };

  const openRow = (r) => {
    const fam = familyByKey[r.families?.[0]];
    if (fam?.strategy_id) onOpenStrategy?.(fam.strategy_id);
  };

  return (
    <div className="space-y-3">
      <div className="flex items-end justify-between">
        <div>
          <h2 className="text-sm font-bold text-white">Screener</h2>
          <p className="text-[10px] text-slate-500">Filter &amp; rank the full signal universe · score is 0–100 signal strength, not a return</p>
        </div>
        {asOf && <span className="text-[9px] text-slate-600">as of {new Date(asOf).toLocaleTimeString()}</span>}
      </div>

      {/* Filter bar */}
      <div className="jt-surface-strong px-3 py-2.5 flex flex-wrap items-center gap-x-4 gap-y-2">
        <div className="flex items-center gap-1.5">
          {MARKETS.map(m => {
            const on = marketFilter.has(m);
            const meta = MARKET_META[m];
            return (
              <button
                key={m}
                onClick={() => toggleMarket(m)}
                className="text-[10px] font-bold px-2 py-1 rounded transition-colors"
                style={on
                  ? { background: `${meta.hex}22`, color: meta.hex, border: `1px solid ${meta.hex}55` }
                  : { background: 'rgba(255,255,255,0.03)', color: '#64748b', border: '1px solid transparent' }}
              >{meta.label}</button>
            );
          })}
        </div>

        <div className="flex bg-slate-900/60 rounded-md p-0.5 border border-white/[0.06]">
          {['ALL', 'BUY', 'SELL'].map(d => (
            <button
              key={d}
              onClick={() => setDirFilter(d)}
              className={`px-2.5 py-1 text-[10px] font-bold rounded ${dirFilter === d ? (d === 'BUY' ? 'bg-emerald-500 text-white' : d === 'SELL' ? 'bg-rose-500 text-white' : 'bg-blue-500 text-white') : 'text-slate-400 hover:text-white'}`}
            >{d}</button>
          ))}
        </div>

        <label className="flex items-center gap-2 text-[10px] text-slate-400">
          <span>Min score</span>
          <input
            type="range" min="0" max="100" step="5" value={minScore}
            onChange={e => setMinScore(Number(e.target.value))}
            className="w-24 accent-blue-500"
          />
          <span className="font-mono font-bold text-white w-6">{minScore}</span>
        </label>

        <input
          type="text" value={search} onChange={e => setSearch(e.target.value)}
          placeholder="Search ticker…"
          className="ml-auto bg-slate-900/60 border border-white/[0.08] rounded-md px-2.5 py-1 text-[11px] text-white placeholder:text-slate-600 focus:outline-none focus:border-blue-500/50 w-40"
        />
        <span className="text-[10px] text-slate-500 font-mono">{filtered.length} / {allRows.length}</span>
      </div>

      {loading ? (
        <div className="qr-surface px-3 py-8 flex items-center justify-center gap-2 text-[11px] text-slate-500">
          <div className="w-3 h-3 border-2 border-slate-700 border-t-blue-500 rounded-full animate-spin" />
          Loading universe…
        </div>
      ) : (
        <div className="jt-surface-strong overflow-x-auto">
          <table className="w-full text-[11px] border-collapse">
            <thead>
              <tr className="border-b border-white/[0.08]">
                {COLUMNS.map(c => (
                  <th
                    key={c.key}
                    onClick={() => onSort(c.key)}
                    className={`px-3 py-2 text-[9px] uppercase tracking-wide text-slate-500 font-bold cursor-pointer hover:text-slate-300 select-none whitespace-nowrap ${c.align === 'right' ? 'text-right' : 'text-left'}`}
                  >
                    {c.label}
                    {sort.key === c.key && <span className="ml-1 text-blue-400">{sort.dir === 'asc' ? '▲' : '▼'}</span>}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {filtered.map((r, i) => {
                const fam = familyByKey[r.families?.[0]];
                const clickable = Boolean(fam?.strategy_id);
                const meta = MARKET_META[r.market] || {};
                return (
                  <tr
                    key={`${r.market}-${r.ticker}-${i}`}
                    onClick={() => openRow(r)}
                    className={`border-b border-white/[0.04] hover:bg-white/[0.03] ${clickable ? 'cursor-pointer' : ''}`}
                  >
                    <td className="px-3 py-1.5 font-bold text-white whitespace-nowrap">
                      {r.ticker}
                      {(r.families || []).length > 1 && <span className="ml-1 text-[8px] text-amber-400" title={`${r.families.length} families agree`}>★{r.families.length}</span>}
                    </td>
                    <td className="px-3 py-1.5">
                      <span className="text-[9px] font-bold px-1.5 py-0.5 rounded" style={{ background: `${meta.hex}22`, color: meta.hex }}>{meta.label || r.market}</span>
                    </td>
                    <td className="px-3 py-1.5">
                      <span className={`qr-chip ${r.direction === 'BUY' ? 'qr-chip-emerald' : 'qr-chip-rose'}`}>{r.direction || '—'}</span>
                    </td>
                    <td className="px-3 py-1.5 text-right font-mono font-bold text-white">
                      {r.potential != null ? r.potential.toFixed(1) : '—'}
                    </td>
                    <td className={`px-3 py-1.5 text-right font-mono ${r.change_pct != null ? pnlCl(r.change_pct) : 'text-slate-600'}`}>
                      {r.change_pct != null ? fmtPct(r.change_pct) : '—'}
                    </td>
                    {HORIZONS.map(h => (
                      <td key={h.key} className={`px-3 py-1.5 text-right font-mono ${r[h.key] != null ? pnlCl(r[h.key]) : 'text-slate-600'}`}>
                        {signedPct(r[h.key])}
                      </td>
                    ))}
                    <td className="px-3 py-1.5 text-slate-400 max-w-[220px] truncate" title={r.note || ''}>{r.note || '—'}</td>
                  </tr>
                );
              })}
              {filtered.length === 0 && (
                <tr><td colSpan={COLUMNS.length} className="px-3 py-8 text-center text-slate-600">No setups match these filters</td></tr>
              )}
            </tbody>
          </table>
        </div>
      )}
      {!loading && HORIZONS.every(h => allRows.every(r => r[h.key] == null)) && allRows.length > 0 && (
        <p className="text-[9px] text-slate-600">5D / 20D / 1Q forecasts are pending qr_etl backfill on <code>consumption.signal_setups</code>.</p>
      )}
    </div>
  );
};

export default ResearchTab;
