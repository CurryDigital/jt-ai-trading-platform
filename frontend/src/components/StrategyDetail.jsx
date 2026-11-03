import React, { useMemo, useRef, useState } from 'react';
import { api, usePoll, fmt, fmtK, fmtAge, pnlCl } from '../utils';
import { PromotionPanel } from './PromotionPanel';
import { CapitalAllocationPanel } from './CapitalAllocationPanel';
import { RiskWatchPanel } from './RiskWatchPanel';
import { haltedLabel } from './strategyProfiles';

// UTC-date helpers for the SIM "Signals" rule-mirror watchlist (HK IPO strategies).
const TODAY_ISO = new Date().toISOString().slice(0, 10);
const addDaysISO = (d, n) => {
  const dt = new Date(`${d}T00:00:00Z`);
  dt.setUTCDate(dt.getUTCDate() + n);
  return dt.toISOString().slice(0, 10);
};

// Tiny inline SVG equity curve --------------------------------------------
// Hover targets carry per-point values (native <title> tooltips) so the curve
// stays readable without a chart library. Cumulative realized P&L by exit
// date — days without exits are carried flat by the line, never interpolated
// into fake data points.
const EquityCurve = ({ points, height = 88 }) => {
  if (!points?.length) {
    return <div className="text-[10px] text-slate-600 text-center py-4">No closed trades in this window · curve appears after the first exit</div>;
  }
  const ys = points.map(p => p.cum_pnl);
  const min = Math.min(0, ...ys);
  const max = Math.max(0, ...ys);
  const range = (max - min) || 1;
  const w = 600;
  const h = height;
  const step = points.length > 1 ? w / (points.length - 1) : 0;
  const yOf = (v) => h - ((v - min) / range) * h;
  const path = points.map((p, i) => `${i === 0 ? 'M' : 'L'}${(i * step).toFixed(1)},${yOf(p.cum_pnl).toFixed(1)}`).join(' ');
  const last = points[points.length - 1];
  const positive = last.cum_pnl >= 0;
  const stroke = positive ? '#34d399' : '#fb7185';
  const fill = positive ? 'rgba(52,211,153,0.12)' : 'rgba(251,113,133,0.12)';
  const zeroY = yOf(0);
  const area = `${path} L${(points.length - 1) * step},${zeroY} L0,${zeroY} Z`;
  return (
    <svg viewBox={`0 0 ${w} ${h}`} preserveAspectRatio="none" className="w-full block" style={{ height }}>
      <line x1="0" y1={zeroY} x2={w} y2={zeroY} stroke="rgba(255,255,255,0.06)" strokeDasharray="3,3" />
      <path d={area} fill={fill} />
      <path d={path} stroke={stroke} strokeWidth="1.5" fill="none" />
      {points.map((p, i) => (
        <circle key={`${p.date}-${i}`} cx={i * step} cy={yOf(p.cum_pnl)} r={10} fill="transparent" style={{ pointerEvents: 'all' }}>
          <title>{`${p.date} · cum ${p.cum_pnl >= 0 ? '+' : ''}${fmtK(p.cum_pnl)} · day ${p.pnl >= 0 ? '+' : ''}${fmtK(p.pnl)}`}</title>
        </circle>
      ))}
    </svg>
  );
};

// Monthly returns heatmap ------------------------------------------------
// rows: [{year, month, return}] with return as DECIMAL FRACTION (0.037 = +3.7%).
// Cells render percent; YTD compounds the fractions (never a naive sum).
const MonthlyHeatmap = ({ rows }) => {
  // bucket into year -> {1..12 -> pct}
  const grid = useMemo(() => {
    const m = new Map();
    for (const r of rows || []) {
      if (!m.has(r.year)) m.set(r.year, {});
      m.get(r.year)[r.month] = (r.return || 0) * 100;
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
      <table className="w-full table-fixed">
        <thead>
          <tr>
            <th className="qr-label text-left pl-1 py-1 w-8">YR</th>
            {months.map((m, i) => (
              <th key={i} className="qr-label text-center py-1">{m}</th>
            ))}
            <th className="qr-label text-right pr-1 py-1 w-9">YTD</th>
          </tr>
        </thead>
        <tbody>
          {grid.map(([year, mp]) => {
            // compound the year's monthly fractions — a simple sum overstates
            // chained returns and breaks reconciliation with the yearly figures
            const ytd = (Object.values(mp).reduce((acc, v) => acc * (1 + (v || 0) / 100), 1) - 1) * 100;
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

// Yearly returns box -------------------------------------------------------
// yearly: {YYYY: fraction}. Sits beside the monthly heatmap; the two
// reconcile by construction (SIM: monthly compounds to the published annual;
// paper: simple sum over fixed assigned capital).
const YearlyReturns = ({ yearly, emptyNote }) => {
  const years = Object.keys(yearly || {}).map(Number).sort((a, b) => b - a);
  if (!years.length) {
    return <div className="text-[10px] text-slate-600 text-center py-4">{emptyNote || 'No yearly return data'}</div>;
  }
  return (
    <table className="w-full">
      <thead>
        <tr>
          <th className="qr-label text-left py-1">YR</th>
          <th className="qr-label text-right py-1">RETURN</th>
        </tr>
      </thead>
      <tbody>
        {years.map(y => {
          const v = yearly[y] ?? yearly[String(y)];
          return (
            <tr key={y} className="border-t border-white/[0.04]">
              <td className="qr-num text-[10px] text-slate-400 py-1">{y}</td>
              <td className={`qr-num text-[11px] py-1 text-right font-bold ${pnlCl(v)}`}>
                {v != null ? `${v >= 0 ? '+' : ''}${(v * 100).toFixed(1)}%` : '—'}
              </td>
            </tr>
          );
        })}
      </tbody>
    </table>
  );
};

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

// Paper-book skip surface (consumption.strategy_paper_skips_current) -------
// Human-readable note per skip_kind; reason text from the table is the
// fallback. Palette rule: neutral slate — a skipped fill is a warning, not
// a critical severity.
const SKIP_NOTE = {
  BELOW_ONE_LOT: 'below one lot at slot capital',
  UNSUPPORTED_ASSET_CLASS: 'asset class unsupported in paper trading',
  NO_PRICE: 'no latest price to size the order',
};
const fmtDollar = (v) => {
  const n = Number(v);
  return v != null && Number.isFinite(n) ? `$${Math.round(n).toLocaleString('en-US')}` : null;
};

// Unified statistics row ---------------------------------------------------
// One row of the SIM-vs-PAPER comparison table. Every value is rendered from
// the evaluation payload verbatim (formatting only) — nothing is summed or
// averaged across the two evidence classes, and missing data renders '—'
// with the reason in the tooltip, never a fabricated zero.
const CmpRow = ({ label, tip, simText, simCl, simTip, paperText, paperCl, paperTip, deltaText, deltaCl, deltaTip }) => (
  <tr className="border-t border-white/[0.04]">
    <td className="py-1.5 px-2 sm:px-3 text-[10px] text-slate-400 whitespace-nowrap" title={tip}>{label}</td>
    <td className={`py-1.5 px-2 sm:px-3 qr-num text-[12px] font-bold whitespace-nowrap ${simText == null ? 'text-slate-600' : simCl || 'text-slate-200'}`} title={simTip}>{simText ?? '—'}</td>
    <td className={`py-1.5 px-2 sm:px-3 qr-num text-[12px] font-bold whitespace-nowrap ${paperText == null ? 'text-slate-600' : paperCl || 'text-slate-200'}`} title={paperTip}>{paperText ?? '—'}</td>
    <td className={`py-1.5 px-2 sm:px-3 qr-num text-[11px] whitespace-nowrap ${deltaText == null ? 'text-slate-600' : deltaCl || 'text-slate-300'}`} title={deltaTip}>{deltaText ?? '—'}</td>
  </tr>
);

// One book's ledger panel (paper or live) ----------------------------------
// Extracted from the old mode-toggle view so BOTH ledgers can stay on screen
// at once. Owns its sub-tab state (Rebalances / Allocation / Ledger).
const BookLedgerPanel = ({ label, source, payload, loading, isPaper, activeSignals, watchSignals, assignedCapital, skipMap, skipsCount }) => {
  const [tab, setTab] = useState('rebalances');

  // Group the book's trade events by day into rebalance groups (sells first,
  // then buys), tracking the held set across groups.
  const rebalances = useMemo(() => {
    const groups = new Map();
    for (const t of (payload && payload.recent_trades) || []) {
      const key = t.ts ? t.ts.slice(0, 10) : '—';
      if (!groups.has(key)) groups.set(key, { date: key, sells: [], buys: [], pnl: 0 });
      const g = groups.get(key);
      if (t.side === 'SELL') { g.sells.push(t); g.pnl += (t.pnl || 0); }
      else g.buys.push(t);
    }
    const ascending = Array.from(groups.values()).sort((a, b) => a.date.localeCompare(b.date));
    let prev = new Set();
    for (const g of ascending) {
      const sellSet = new Set(g.sells.map(t => t.ticker));
      const held = new Set(prev);
      for (const s of sellSet) held.delete(s);
      g.held = Array.from(held).sort();
      prev = new Set(held);
      for (const b of g.buys) prev.add(b.ticker);
    }
    return ascending.reverse();
  }, [payload && payload.recent_trades]);

  // Net cost basis per ticker from the ledger, plus `since` — the first BUY
  // timestamp of the current holding (reset whenever the position goes flat).
  const positionMap = useMemo(() => {
    const map = {};
    // recent_trades arrives DESC by ts; walk oldest→newest so `since` tracks
    // the start of the current holding.
    const trades = [...((payload && payload.recent_trades) || [])].reverse();
    for (const t of trades) {
      if (!t.ticker) continue;
      const entry = map[t.ticker] || (map[t.ticker] = { qty: 0, cost: 0, since: null });
      const qty = Number(t.quantity) || 0;
      const price = Number(t.price) || 0;
      if (t.side === 'SELL') {
        entry.qty -= qty;
        entry.cost -= qty * price;
        if (entry.qty <= 0) { entry.qty = 0; entry.cost = 0; entry.since = null; }
      } else {
        if (entry.qty <= 0) entry.since = t.ts || null;
        entry.qty += qty;
        entry.cost += qty * price;
      }
    }
    return map;
  }, [payload && payload.recent_trades]);

  return (
    <div className="qr-surface overflow-hidden">
      <div className="px-3 py-1.5 border-b border-white/[0.05] flex items-center gap-2">
        <span className="qr-label" title={source}>{label}</span>
        {isPaper && skipsCount > 0 && (
          <span className="qr-chip qr-chip-slate text-[9px]" title="BUY signals the paper rebalancer could not fill — see Allocation tab">
            {skipsCount} unfilled
          </span>
        )}
        {payload && (
          <span className="qr-chip qr-chip-slate text-[9px] ml-auto">{payload.recent_trades.length} events</span>
        )}
      </div>

      {payload == null ? (
        <div className="flex items-center gap-2 py-8 justify-center text-slate-500 text-[11px]">
          <div className={`w-3 h-3 border-2 border-slate-700 border-t-blue-500 rounded-full ${loading ? 'animate-spin' : ''}`} />
          {loading ? `Loading ${label.toLowerCase()}…` : 'Ledger not loaded'}
        </div>
      ) : (
        <>
          <div className="px-3 py-1 border-b border-white/[0.05] flex items-center gap-1">
            {[
              { id: 'rebalances', label: `Rebalances (${rebalances.length})` },
              { id: 'allocation', label: `Allocation (${activeSignals.length})` },
              { id: 'trades',     label: `Ledger (${payload.recent_trades.length})` },
            ].map(t => (
              <button
                key={t.id}
                onClick={() => setTab(t.id)}
                className={`px-2 py-1 rounded text-[11px] font-semibold transition-colors ${tab === t.id ? 'bg-white/[0.08] text-white' : 'text-slate-400 hover:text-slate-200'}`}
              >{t.label}</button>
            ))}
          </div>

          {tab === 'rebalances' && (
            <div className="max-h-[520px] overflow-auto">
              {rebalances.length === 0 && (
                <div className="py-6 text-center text-slate-600 text-[11px]">No rebalance history yet</div>
              )}
              {rebalances.map((g) => {
                const realized = g.sells.length > 0 ? g.pnl : null;
                return (
                  <div key={g.date} className="border-b border-white/[0.04] last:border-0">
                    <div className="px-3 py-2 flex items-center justify-between bg-white/[0.02] sticky top-0">
                      <div className="flex items-center gap-2">
                        <span className="qr-num text-[11px] font-bold text-white">{new Date(g.date).toLocaleDateString('en-GB', { month: '2-digit', day: '2-digit', year: '2-digit' })}</span>
                        <span className="qr-label">Rebalance</span>
                        <span className="qr-chip qr-chip-slate text-[9px]">-{g.sells.length} / +{g.buys.length}</span>
                        {g.held.length > 0 && <span className="qr-chip qr-chip-slate text-[9px]">held {g.held.length}</span>}
                      </div>
                      <div className={`qr-num text-[11px] font-bold ${realized != null ? pnlCl(realized) : 'text-slate-500'}`}>{realized != null ? `${realized >= 0 ? '+' : ''}${fmtK(realized)}` : '—'}</div>
                    </div>
                    <div className="overflow-x-auto">
                      <table className="w-full">
                        <tbody className="divide-y divide-white/[0.04]">
                          {g.held.length > 0 && (
                            <tr className="qr-tr-hover">
                              <td className="py-1 px-2 qr-label text-[9px] text-slate-500 w-16">HELD</td>
                              <td className="py-1 px-2 text-[10px] text-slate-300 font-mono" colSpan={6}>{g.held.join(' ')}</td>
                            </tr>
                          )}
                          {g.sells.map((t, i) => (
                            <tr key={`${t.ts}-${t.ticker}-sell-${i}`} className="qr-tr-hover">
                              <td className="py-1 px-2 qr-label text-[9px] text-rose-400 w-16">SELL</td>
                              <td className="py-1 px-2 text-white text-[11px] font-mono w-24">{t.ticker}</td>
                              <td className="py-1 px-2 qr-num text-slate-300 text-right">{fmt(t.quantity, 0)}</td>
                              <td className="py-1 px-2 qr-num text-slate-300 text-right">@{fmt(t.price)}</td>
                              <td className={`py-1 px-2 qr-num text-right font-bold ${pnlCl(t.pnl)}`}>{t.pnl != null ? fmtK(t.pnl) : '—'}</td>
                              <td className="py-1 px-2 text-right text-[9px] text-slate-500 w-32">dropped from top 5</td>
                            </tr>
                          ))}
                          {g.buys.map((t, i) => (
                            <tr key={`${t.ts}-${t.ticker}-buy-${i}`} className="qr-tr-hover">
                              <td className="py-1 px-2 qr-label text-[9px] text-emerald-400 w-16">BUY</td>
                              <td className="py-1 px-2 text-white text-[11px] font-mono w-24">{t.ticker}</td>
                              <td className="py-1 px-2 qr-num text-slate-300 text-right">{fmt(t.quantity, 0)}</td>
                              <td className="py-1 px-2 qr-num text-slate-300 text-right">@{fmt(t.price)}</td>
                              <td className="py-1 px-2 qr-num text-right text-slate-500">—</td>
                              <td className="py-1 px-2 text-right text-[9px] text-slate-500 w-32">entered top 5</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                );
              })}
            </div>
          )}

          {tab === 'allocation' && (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-white/[0.06]">
                    <th className="qr-label text-left  py-1 px-2">Ticker</th>
                    <th className="qr-label text-right py-1 px-2">Weight</th>
                    <th className="qr-label text-right py-1 px-2">Signal</th>
                    <th className="qr-label text-right py-1 px-2" title="Average fill price of the current holding, from the ledger">Buy</th>
                    <th className="qr-label text-right py-1 px-2" title="Latest price (consumption.strategies_signals_current)">Current</th>
                    <th className="qr-label text-right py-1 px-2" title="Qty × current price">Value</th>
                    <th className="qr-label text-right py-1 px-2">Qty</th>
                    <th className="qr-label text-right py-1 px-2" title="Mark-to-market: qty × (current − avg buy)">P&amp;L</th>
                    <th className="qr-label text-right py-1 px-2" title="First BUY date of the current holding, from the ledger">Purchased</th>
                    <th className="qr-label text-right py-1 px-2" title="Signal batch refresh time">Generated</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/[0.04]">
                  {activeSignals.map(s => {
                    // Weight / value / qty come from the actual ledger position,
                    // NOT from signal_strength — that field is a raw momentum
                    // score (e.g. 0.0033), not a portfolio weight, and rendered
                    // a bogus 0% / $0 before.
                    const pos = positionMap[s.ticker];
                    const qty = pos && pos.qty > 0 ? Math.round(pos.qty) : null;
                    const buyPrice = qty != null && pos.cost > 0 ? pos.cost / pos.qty : null;
                    const purchasedAt = qty != null ? pos.since : null;
                    const value = qty != null && s.price ? qty * s.price : null;
                    const weight = value != null && assignedCapital ? value / assignedCapital : null;
                    const pnl = pos && pos.qty > 0 && s.price ? pos.qty * s.price - pos.cost : null;
                    // Signal with no ledger position: the rebalancer skipped it.
                    // When consumption.strategy_paper_skips_current has a row for
                    // this ticker, show the recorded reason (e.g. slot below one
                    // lot, unsupported asset class, no price) instead of the
                    // generic note. Explicit zeros stay — the signal is real and
                    // the position is zero; both facts should be visible.
                    const unfilled = qty == null;
                    const skip = isPaper && unfilled ? skipMap[s.ticker] : null;
                    return (
                      <tr key={s.ticker} className="qr-tr-hover">
                        <td className="py-1 px-2 text-white text-[11px] font-mono">
                          {s.ticker}
                          {unfilled && (
                            skip ? (
                              <>
                                <div className="text-[9px] text-slate-500">Not filled — {SKIP_NOTE[skip.skip_kind] || skip.reason || 'skipped by rebalancer'}</div>
                                {skip.skip_kind === 'BELOW_ONE_LOT' && fmtDollar(skip.slot_notional) && fmtDollar(skip.lot_cost) && (
                                  <div className="text-[9px] text-slate-600">slot {fmtDollar(skip.slot_notional)} &lt; 1 lot {fmtDollar(skip.lot_cost)}</div>
                                )}
                              </>
                            ) : (
                              <div className="text-[9px] text-slate-500">signal only · no fill</div>
                            )
                          )}
                        </td>
                        <td className="py-1 px-2 qr-num text-right">{weight != null ? `${(weight * 100).toFixed(0)}%` : unfilled ? '0%' : '—'}</td>
                        <td className="py-1 px-2 text-right"><span className="qr-chip qr-chip-emerald">BUY</span></td>
                        <td className="py-1 px-2 qr-num text-right">{buyPrice != null ? fmt(buyPrice) : '—'}</td>
                        <td className="py-1 px-2 qr-num text-right">{fmt(s.price)}</td>
                        <td className="py-1 px-2 qr-num text-right">{value != null ? fmtK(value) : unfilled ? '$0' : '—'}</td>
                        <td className="py-1 px-2 qr-num text-right">{qty != null ? fmt(qty, 0) : unfilled ? '0' : '—'}</td>
                        <td className={`py-1 px-2 qr-num text-right font-bold ${pnl == null ? 'text-slate-500' : pnl >= 0 ? 'qr-pnl-pos' : 'qr-pnl-neg'}`}>{pnl == null ? '—' : `${pnl >= 0 ? '+' : ''}${fmtK(pnl)}`}</td>
                        <td className="py-1 px-2 qr-num text-slate-400 text-[10px] text-right">{purchasedAt ? new Date(purchasedAt).toLocaleDateString('en-GB', { day: '2-digit', month: '2-digit', year: 'numeric' }) : '—'}</td>
                        <td className="py-1 px-2 qr-num text-slate-500 text-[10px] text-right">{s.ts ? fmtAge(s.ts) : '—'}</td>
                      </tr>
                    );
                  })}
                  {!activeSignals.length && (
                    <tr><td colSpan={10} className="py-6 text-center text-slate-600 text-[11px]">No active positions</td></tr>
                  )}
                </tbody>
              </table>
              {watchSignals.length > 0 && (
                <div className="px-3 py-2 border-t border-white/[0.05]">
                  <div className="qr-label text-[10px] mb-1">Universe watchlist ({watchSignals.length})</div>
                  <div className="flex flex-wrap gap-1">
                    {watchSignals.map(s => (
                      <span key={s.ticker} className="qr-chip qr-chip-slate text-[10px] font-mono" title={`${s.ticker} @ ${fmt(s.price)}`}>{s.ticker}</span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {tab === 'trades' && (
            <div className="overflow-x-auto max-h-[520px] overflow-auto">
              <table className="w-full">
                <thead className="sticky top-0 bg-slate-900 z-10">
                  <tr className="border-b border-white/[0.06]">
                    <th className="qr-label text-left py-1 px-2">Time</th>
                    <th className="qr-label text-left py-1 px-2">Ticker</th>
                    <th className="qr-label text-right py-1 px-2">Side</th>
                    <th className="qr-label text-right py-1 px-2">Qty</th>
                    <th className="qr-label text-right py-1 px-2">Price</th>
                    <th className="qr-label text-right py-1 px-2">P&L</th>
                    <th className="qr-label text-right py-1 px-2">Mode</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/[0.04]">
                  {payload.recent_trades.map((t, i) => (
                    <tr key={`${t.ts}-${t.ticker}-${i}`} className={`qr-tr-hover ${t.non_strategy ? 'opacity-50' : ''}`} title={t.non_strategy ? `Non-strategy bookkeeping — ${t.non_strategy_label?.skip_kind || 'cleanse closure'}${t.non_strategy_label?.reason ? `: ${t.non_strategy_label.reason}` : ''} · excluded from all performance figures` : undefined}>
                      <td className="py-1 px-2 qr-num text-slate-400 text-[10px]">{t.ts ? new Date(t.ts).toLocaleString('en-GB', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' }) : '—'}</td>
                      <td className="py-1 px-2 text-white text-[11px] font-mono">{t.ticker}{t.non_strategy && <span className="qr-chip qr-chip-slate text-[8px] ml-1" title="Cleanse-closure leg — excluded from strategy performance">bookkeeping</span>}</td>
                      <td className="py-1 px-2 text-right">
                        <span className={`qr-chip ${t.side === 'BUY' || t.side === 'LONG' ? 'qr-chip-emerald' : 'qr-chip-rose'}`}>{t.side}</span>
                      </td>
                      <td className="py-1 px-2 qr-num text-slate-300">{fmt(t.quantity, 0)}</td>
                      <td className="py-1 px-2 qr-num text-slate-300">{fmt(t.price)}</td>
                      <td className={`py-1 px-2 qr-num font-bold ${pnlCl(t.pnl)}`}>{t.pnl == null ? '—' : fmtK(t.pnl)}</td>
                      <td className="py-1 px-2 text-right text-[9px] text-slate-500">{t.mode || '—'}</td>
                    </tr>
                  ))}
                  {!payload.recent_trades.length && (
                    <tr><td colSpan={7} className="py-6 text-center text-slate-600 text-[11px]">No trades in this book yet</td></tr>
                  )}
                </tbody>
              </table>
            </div>
          )}
        </>
      )}
    </div>
  );
};

// Main component --------------------------------------------------------
export const StrategyDetail = ({ strategyId, onBack }) => {
  const [data, setData] = useState(null);        // book=auto payload (header, signals, sim, strip)
  const [altBooks, setAltBooks] = useState({});  // { paper|live: payload } for the non-auto ledger
  const [loading, setLoading] = useState(true);
  const [bookLoading, setBookLoading] = useState(false);
  const [simTab, setSimTab] = useState('rebalances');
  const [ipoWatch, setIpoWatch] = useState(null);  // HK IPO rule-mirror forward watchlist feed
  const [refreshedAt, setRefreshedAt] = useState(null);
  const altRef = useRef({});

  const normalize = (d) => (d && typeof d === 'object'
    ? {
        ...d,
        metrics: d.metrics || { backtest: {}, live: {} },
        metrics_by_mode: d.metrics_by_mode || { sim: {}, paper: {}, uat: {}, live: {} },
        divergence: d.divergence || { verdict: 'no_backtest_baseline', win_rate_delta_pp: null, profit_factor_delta: null },
        equity_curve: d.equity_curve || [],
        monthly_returns: d.monthly_returns || [],
        monthly_returns_paper: d.monthly_returns_paper || [],
        yearly_returns: d.yearly_returns || { sim: {}, paper: {} },
        uat_fills: (d.uat_fills || []).filter(f => f?.ticker?.toUpperCase?.() !== 'CASH'),
        // CASH is a cash-bucket placeholder, not a tradeable ticker; filter it defensively
        // so it never appears in the Universe, Trades, or Signals tables.
        recent_trades: (d.recent_trades || []).filter(t => t?.ticker?.toUpperCase?.() !== 'CASH'),
        recent_signals: (d.recent_signals || []).filter(s => s?.ticker?.toUpperCase?.() !== 'CASH'),
        universe: (d.universe || []).filter(t => t && t.toUpperCase() !== 'CASH'),
        // Paper-book skip surface (consumption.strategy_paper_skips_current):
        // BUY signals the paper rebalancer sized to zero, with the reason.
        paper_skips: (d.paper_skips || []).filter(sk => sk?.ticker?.toUpperCase?.() !== 'CASH'),
      }
    : null);

  // Fetch a specific ledger (paper|live) — the unified layout needs BOTH books
  // on screen at once, so the non-auto book is fetched eagerly on load (not on
  // a toggle click, which no longer exists).
  const fetchBook = async (b) => {
    setBookLoading(true);
    const d = normalize(await api.get(`/api/strategies/${encodeURIComponent(strategyId)}/evaluation?trade_limit=1000&book=${b}`));
    if (d) {
      altRef.current = { ...altRef.current, [b]: d };
      setAltBooks(altRef.current);
    }
    setBookLoading(false);
    return d;
  };

  const load = async () => {
    const d = normalize(await api.get(`/api/strategies/${encodeURIComponent(strategyId)}/evaluation?trade_limit=1000`));
    setData(d);
    setRefreshedAt(new Date().toISOString());
    setLoading(false);
    // Forward "what to buy" feed for HK IPO strategies — rule mirror over the
    // IPO calendar (/api/hkex/ipos), refreshed alongside the evaluation poll.
    if (strategyId.startsWith('hk_ipo')) {
      api.get('/api/hkex/ipos?limit=400')
        .then(res => setIpoWatch((res && res.ipos) || []))
        .catch(() => {});
    }
    if (d) {
      // Single-view layout: the paper book must be on screen even when the
      // deployment mode's auto book is live, and vice versa.
      if (d.book !== 'paper' && !altRef.current.paper) await fetchBook('paper');
      const liveN = (d.metrics_by_mode && d.metrics_by_mode.live && d.metrics_by_mode.live.total_trades) || 0;
      if (d.book !== 'live' && liveN > 0 && !altRef.current.live) await fetchBook('live');
    }
    return d;
  };

  // Visibility-paused poll. The parent remounts this via key={strategyId},
  // so mount handles the initial load + spinner; usePoll drives the 30s refresh.
  // Keep the hook call as a standalone statement so aggressive minifiers cannot
  // fold it into the following `if (loading)` guard as a sequence expression.
  usePoll(async () => {
    const d = await load();
    const autoBook = d?.book;
    for (const b of Object.keys(altRef.current)) {
      if (b !== autoBook) await fetchBook(b);
    }
  }, 30000);

  // Memoised data transforms must be top-level hooks so they run on every
  // render and never after an early return (that would break Rules of Hooks).

  // Simulation side: group OOS backtest trades by exit date (positions closed
  // on the same day form one "rebalance" group).
  const simRebalances = useMemo(() => {
    const groups = new Map();
    for (const t of (data && data.backtest_trades) || []) {
      if (!t.exit_date) continue;
      const key = t.exit_date.slice(0, 10);
      if (!groups.has(key)) groups.set(key, { date: key, closed: [] });
      groups.get(key).closed.push(t);
    }
    return Array.from(groups.values()).sort((a, b) => b.date.localeCompare(a.date));
  }, [data && data.backtest_trades]);

  // Simulation side: current positions = OOS backtest trades still open at the
  // end of the backtest window (no exit_date). Shown in the Allocation tab of
  // the Simulation ledger, mirroring the paper/UAT ledger layout. holding_days
  // on these rows is measured to the backtest as-of date, not to today.
  const simOpen = useMemo(() =>
    ((data && data.backtest_trades) || []).filter(t => !t.exit_date)
      .sort((a, b) => (b.entry_date || '').localeCompare(a.entry_date || '')),
  [data && data.backtest_trades]);

  // SIM "Signals" tab: forward-looking rule mirror for HK IPO drift strategies —
  // queued/undecided only. Full gate chain still runs (mirrors IpoTab.stratDecision
  // 1:1) but SKIP/ENTERED rows are dropped from the display — the user only
  // wants BUY ON (actionable) and WATCH (band not decidable yet) rows
  // (2026-09-25 request). Gate semantics kept for reference:
  //   ENTERED  — in oversub band and the +20td entry day has traded (mirror open)
  //   BUY ON   — all gates pass, entry still ahead (queued); date measured, else est.
  //   WATCH    — band undecidable (pre-listing; retail oversub lands at allotment)
  //              or the day-1 close is not published yet
  //   SKIP     — oversub outside 100–500x, D1 close < offer (D1 red), or the
  //              measured entry px outside 0.9–1.3x the D1 close
  const simBuyWatch = useMemo(() => {
    if (!ipoWatch) return null;
    const rows = [];
    for (const r of ipoWatch) {
      if (!r.listing_date) continue;
      const entry = r.day20_date || addDaysISO(r.listing_date, 28);  // ≈20td
      const exit = r.day40_date || addDaysISO(entry, 28);            // +20td hold
      let phase;
      if (r.listing_date > TODAY_ISO) phase = 'pre_listing';
      else if (TODAY_ISO < entry) phase = 'ahead';
      else if (TODAY_ISO <= exit) phase = 'in_hold';
      else continue;  // passed — history, shown in the Ledger tab
      // Gate chain mirrors IpoTab.stratDecision (IPO-page canonical) 1:1 —
      // 2026-09-25 misalignment: this list used to apply ONLY the oversub band,
      // so D1-red names (e.g. 2041.HK, D1 close 8.80 < offer 15.42) showed
      // BUY ON here while the IPO page said SKIP. Keep the two in sync.
      const ov = r.oversubscription_retail;
      const d1c = r.first_day_close;
      const offer = r.offer_price ?? r.offer_price_high ?? null;  // same basis as IpoTab ipoPx
      const entryPx = r.day20_price ?? null;
      const d1Ratio = entryPx != null && d1c ? entryPx / d1c : null;
      const oversubPending = ov == null
        ? (phase === 'pre_listing' ? 'band at allotment' : 'oversub pending (t_90585bf2)')
        : null;
      let word, sub;
      if (oversubPending) {
        word = 'WATCH'; sub = oversubPending;
      } else if (ov < 100 || ov > 500) {
        word = 'SKIP'; sub = `${Math.round(ov)}x outside 100–500x`;
      } else if (d1c != null && offer != null && d1c < offer) {
        // C1 deal-health gate: day-1 close must hold the offer.
        word = 'SKIP'; sub = `D1 red — close ${d1c} < offer ${offer}`;
      } else if (d1c == null && phase !== 'pre_listing') {
        word = 'WATCH'; sub = 'awaiting D1 close';
      } else if (d1Ratio != null && (d1Ratio < 0.9 || d1Ratio > 1.3)) {
        // C1 entry/D1-close band, decidable once the +20td entry leg is measured.
        word = 'SKIP'; sub = `entry/D1 ${d1Ratio.toFixed(2)} outside 0.9–1.3×`;
      } else if (phase === 'ahead' || phase === 'pre_listing') {
        word = 'BUY ON'; sub = `${entry}${r.day20_date ? '' : ' (est)'}`;
      } else {
        word = 'ENTERED'; sub = `${entry} · exit ${exit}${r.day40_date ? '' : ' (est)'}`;
      }
      // Display filter: BUY ON (queued) and WATCH (undecidable yet) only —
      // SKIP (gate failed) and ENTERED (already in hold; see Ledger/Allocation)
      // are noise for this list (2026-09-25 request).
      if (word !== 'BUY ON' && word !== 'WATCH') continue;
      rows.push({ ticker: r.ticker, name: r.stock_name || r.stock_name_zh || '',
        listing: r.listing_date, entry, exit, oversub: ov, phase, word, sub });
    }
    const order = { in_hold: 0, ahead: 1, pre_listing: 2 };
    return rows.sort((a, b) => order[a.phase] - order[b.phase] || a.entry.localeCompare(b.entry));
  }, [ipoWatch]);

  const activeSignals = useMemo(() =>
    ((data && data.recent_signals) || []).filter(s => s.signal === 'BUY').sort((a, b) => a.ticker.localeCompare(b.ticker)),
  [data && data.recent_signals]);

  const watchSignals = useMemo(() =>
    ((data && data.recent_signals) || []).filter(s => s.signal !== 'BUY').sort((a, b) => a.ticker.localeCompare(b.ticker)),
  [data && data.recent_signals]);

  // Paper-book skips keyed by ticker: joined to the allocation rows at render
  // time so an unfilled BUY signal explains itself (slot vs lot cost, or why
  // the rebalancer refused the order). Read from the API payload — never
  // synthesized by diffing signals vs positions.
  const skipMap = useMemo(() => {
    const m = {};
    for (const sk of (data && data.paper_skips) || []) {
      if (sk && sk.ticker) m[sk.ticker] = sk;
    }
    return m;
  }, [data && data.paper_skips]);

  // Render the body inside an IIFE so the `if (loading)` guard is not
  // syntactically adjacent to the hook call above, which prevents minifiers
  // from rewriting it as `if ((usePoll(...), loading)) return ...`.
  const body = (() => {
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

    const metricsMissing = !data.metrics || !data.metrics.backtest || !data.metrics.live;
    if (metricsMissing) {
      return (
        <div className="qr-surface p-6 text-center space-y-3">
          <p className="text-[12px] text-slate-400">
            Strategy <span className="font-mono text-white">{strategyId}</span> loaded, but evaluation metrics are missing.
          </p>
          <p className="text-[11px] text-slate-500">
            The backend did not return backtest/live metrics for this strategy. It may be a bare strategy record or the evaluation endpoint returned the wrong shape.
          </p>
          <div className="flex items-center justify-center gap-2">
            <button onClick={load} className="qr-btn-ghost">↻ Retry</button>
            <button onClick={onBack} className="qr-btn-ghost">← Back</button>
          </div>
        </div>
      );
    }

    const mbm = data.metrics_by_mode || {};
    const simM = mbm.sim || {};
    const paperM = mbm.paper || {};
    const uatM = mbm.uat || mbm.paper_uat || {};
    const liveM = mbm.live || {};
    const verdict = VERDICT_STYLE[data.divergence.verdict] || VERDICT_STYLE.no_backtest_baseline;
    const execMode = (data.execution_mode || '').toUpperCase();

    // Both ledgers stay on screen. The auto-book payload covers one of them;
    // the other is the eager-fetched alt book (null while in flight → panel
    // renders its own loading state).
    const paperPayload = data.book === 'paper' ? data : (altBooks.paper || null);
    const livePayload = data.book === 'live' ? data : (altBooks.live || null);
    // Paper avg holding days: metrics_by_mode.paper carries it when paper is
    // the auto book; for live-mode strategies it comes from the fetched paper
    // payload's live block (gold.paper_trades_synthetic closed round-trips).
    const paperAvgHold = paperM.avg_holding_days ?? (paperPayload && paperPayload.metrics && paperPayload.metrics.live && paperPayload.metrics.live.avg_holding_days);

    // Δ column — Paper − SIM, only where the two values are directly
    // comparable. Win-rate and profit-factor deltas are served by the backend
    // (divergence.*) when paper is the auto book; otherwise derived from the
    // two served values on screen. Counts/returns get no delta: different
    // sample windows make the arithmetic meaningless.
    const div = data.divergence || {};
    const wrDelta = (data.book === 'paper' && div.win_rate_delta_pp != null)
      ? div.win_rate_delta_pp
      : (paperM.win_rate != null && simM.win_rate != null ? (paperM.win_rate - simM.win_rate) * 100 : null);
    const pfDelta = (data.book === 'paper' && div.profit_factor_delta != null)
      ? div.profit_factor_delta
      : (paperM.profit_factor != null && simM.profit_factor != null ? paperM.profit_factor - simM.profit_factor : null);
    const holdDelta = (paperAvgHold != null && simM.avg_holding_days != null) ? paperAvgHold - simM.avg_holding_days : null;

    // Value formatters — fixed units per field, never magnitude-sniffed.
    // SIM metrics arrive as fractions; paper P&L arrives in dollars.
    const pctText = (v) => (v != null ? `${(v * 100).toFixed(1)}%` : null);
    const signedPctText = (v) => (v != null ? `${v >= 0 ? '+' : ''}${(v * 100).toFixed(1)}%` : null);
    const signedKText = (v) => (v != null ? `${v >= 0 ? '+' : ''}${fmtK(v)}` : null);

    const uatHas = (uatM.total_fills || 0) > 0 || execMode.includes('UAT');
    const liveHas = (liveM.total_trades || 0) > 0 || execMode === 'LIVE_TRADING';

    return (
      <div className="space-y-3">
        {/* Header — identity, status, and essential config on two lines */}
        <div className="qr-surface px-3 py-2">
          <div className="flex items-start justify-between gap-3 flex-wrap">
            <div className="min-w-0">
              <button onClick={onBack} className="qr-btn-ghost mb-1">← Strategies</button>
              <div className="flex items-center gap-2 flex-wrap">
                <h1 className="text-[15px] font-bold text-white tracking-tight truncate max-w-[420px]" title={data.name}>{data.name}</h1>
                {data.priority && <span className={`qr-chip ${PRIORITY_STYLE[data.priority] || 'qr-chip-slate'}`}>{data.priority}</span>}
                {data.status && <span className={`qr-chip ${STATUS_STYLE[data.status] || 'qr-chip-slate'}`}>{data.status}</span>}
                {data.execution_mode && <span className={`qr-chip ${MODE_STYLE[data.execution_mode] || 'qr-chip-slate'}`} title="Current deployment mode — the operational ladder is managed in Mode Promotion below">{data.execution_mode.replace('_TRADING','').replace('SIMULATION','SIM')}</span>}
                {data.version && <span className="qr-chip qr-chip-slate">v{data.version}</span>}
              </div>
              <div className="flex items-center gap-x-3 gap-y-1 mt-1 text-[10px] text-slate-500 flex-wrap">
                <span><span className="qr-label">ID</span> <span className="qr-num text-slate-300">{strategyId}</span></span>
                <span><span className="qr-label">ASSET</span> <span className="text-slate-300">{data.asset_class}</span></span>
                <span><span className="qr-label">DIR</span> <span className="text-slate-300">{data.direction}</span></span>
                <span><span className="qr-label">UNIVERSE</span> <span className="qr-num text-slate-300">{data.universe_count}</span></span>
                <span><span className="qr-label">VENUE</span> <span className="text-slate-300">{data.venue}</span></span>
                <span title="Assigned capital pool (gold.strategy_registry.assigned_capital)"><span className="qr-label">CAPITAL</span> <span className="qr-num text-slate-300">{data.assigned_capital != null ? fmtK(data.assigned_capital) : '—'}</span></span>
                <span title="Current in-market exposure (gold.strategy_registry.in_market_capital)"><span className="qr-label">IN MKT</span> <span className="qr-num text-slate-300">{data.in_market_capital != null ? fmtK(data.in_market_capital) : '—'}</span></span>
                <span><span className="qr-label">UPD</span> <span className="qr-num text-slate-300">{fmtAge(refreshedAt)}</span></span>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <span className={`qr-chip ${verdict.cls}`} title="Backend divergence verdict — paper/live vs SIM baseline">{verdict.label}</span>
              <button onClick={load} className="qr-btn-ghost">↻ Refresh</button>
            </div>
          </div>
        </div>

        {/* CLEANSE-1 (t_070590de): halted-book banner — registry PAUSED /
            PENDING (paused + 'PENDING —' reason prefix) / RETIRED with the
            operator's reason text. The page must never read as a live book. */}
        {(() => {
          const halted = haltedLabel(data.status, data.retirement_reason);
          if (!halted) return null;
          const rose = halted.k === 'RETIRED';
          return (
            <div className={`qr-surface px-3 py-2 border-l-2 ${rose ? 'border-rose-500/60' : 'border-slate-500/60'}`}>
              <div className="flex items-center gap-2 flex-wrap">
                <span className={`qr-chip ${rose ? 'qr-chip-rose' : 'qr-chip-slate'}`}>{halted.k}</span>
                <span className="text-[10px] text-slate-400">Registry-halted — not trading. Metrics below are historical; paper aggregates exclude cleanse-closure bookkeeping.</span>
              </div>
              {halted.reason && (
                <p className="text-[10px] text-slate-400 leading-relaxed mt-1 whitespace-pre-line">{halted.reason}</p>
              )}
            </div>
          );
        })()}

        {/* CLEANSE-1 (t_070590de): non-strategy bookkeeping disclosure — legs
            labeled RESET_STALE_SIGNAL/CLEANSE1_CLOSURE are excluded from every
            aggregate on this page; the held-back amount is disclosed, never
            silently dropped and never quoted as strategy performance. */}
        {(data.non_strategy_excluded?.legs || 0) > 0 && (
          <div className="qr-surface px-3 py-2">
            <div className="text-[10px] text-slate-500 leading-relaxed" title="Closure legs labeled RESET_STALE_SIGNAL (flattened) / CLEANSE1_CLOSURE in consumption.strategy_paper_skips_current — operator bookkeeping from the 2026-10-28 cleanse">
              <span className="qr-chip qr-chip-slate text-[9px] mr-2">NON-STRATEGY BOOKKEEPING</span>
              {data.non_strategy_excluded.legs} cleanse-closure leg{data.non_strategy_excluded.legs === 1 ? '' : 's'}
              {data.non_strategy_excluded.pnl != null && <> totaling <span className={`qr-num font-bold ${pnlCl(data.non_strategy_excluded.pnl)}`}>{data.non_strategy_excluded.pnl >= 0 ? '+' : ''}{fmtK(data.non_strategy_excluded.pnl)}</span></>}
              {' '}excluded from all performance figures on this page — orphan-holding flatten per operator directive, not strategy performance.
            </div>
          </div>
        )}

        {/* ================= UNIFIED STATISTICS (SIM vs PAPER) ==============
            One comparison table, both evidence classes on screen at once —
            the old SIM/PAPER statistics-view toggle is gone. Values are never
            summed or averaged across books; each column keeps its source label
            and unit, and the Δ column is filled only where the two values are
            directly comparable. */}
        <div className="qr-surface overflow-hidden">
          <div className="px-3 py-1.5 border-b border-white/[0.05] flex items-center gap-2 flex-wrap">
            <span className="qr-label">Performance · SIM backtest vs Paper</span>
            <span className="text-[9px] text-slate-600">side by side — never aggregated; Δ = Paper − SIM where comparable</span>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full min-w-[320px] table-fixed">
              <thead>
                <tr className="border-b border-white/[0.06]">
                  <th className="qr-label text-left py-1.5 px-2 sm:px-3">Metric</th>
                  <th className="qr-label text-right py-1.5 px-2 sm:px-3 w-[86px] sm:w-[128px]" title="OOS backtest baseline · gold.strategy_backtest_runs (fractions → %)">SIM · Backtest</th>
                  <th className="qr-label text-right py-1.5 px-2 sm:px-3 w-[86px] sm:w-[128px]" title="Synthetic paper ledger · gold.paper_trades_synthetic closed round-trips">Paper</th>
                  <th className="qr-label text-right py-1.5 px-2 sm:px-3 w-[72px] sm:w-[96px]" title="Paper − SIM, only where directly comparable">Δ</th>
                </tr>
              </thead>
              <tbody>
                <CmpRow
                  label="OOS Return" tip="Total out-of-sample backtest return (fraction → %). Paper has no served total-return figure — its realized $ P&L is the row below; monthly realized returns are in the Returns section."
                  simText={signedPctText(simM.total_return)} simCl={pnlCl(simM.total_return)}
                  paperText={null} paperTip="No paper total-return figure served by the API — not derived client-side"
                  deltaText={null} deltaTip="Return vs $ P&L measure different things — no delta" />
                <CmpRow
                  label="Net P&L" tip="Realized net P&L in dollars"
                  simText={null} simTip="Backtests store per-trade pnl_pct, not dollars — no $ P&L exists for SIM"
                  paperText={signedKText(paperM.total_pnl)} paperCl={pnlCl(paperM.total_pnl)} paperTip="gold.paper_trades_synthetic · closed round-trips, cleanse-closure legs excluded"
                  deltaText={null} deltaTip="SIM has no $ P&L — no delta" />
                <CmpRow
                  label="Win Rate" tip="Closed-trade win rate"
                  simText={pctText(simM.win_rate)} simTip="OOS backtest win rate (fraction → %)"
                  paperText={pctText(paperM.win_rate)} paperTip="Paper closed round-trip win rate (fraction → %)"
                  deltaText={wrDelta != null ? `${wrDelta >= 0 ? '+' : ''}${wrDelta.toFixed(1)}pp` : null}
                  deltaCl={pnlCl(wrDelta)}
                  deltaTip={wrDelta != null ? `Paper − SIM in percentage points${data.book === 'paper' ? ' · backend divergence.win_rate_delta_pp' : ''}` : 'Both win rates required for a delta'} />
                <CmpRow
                  label="Profit Factor" tip="Gross win ÷ gross loss over closed trades"
                  simText={simM.profit_factor != null ? simM.profit_factor.toFixed(2) : null}
                  paperText={paperM.profit_factor != null ? paperM.profit_factor.toFixed(2) : null}
                  deltaText={pfDelta != null ? `${pfDelta >= 0 ? '+' : ''}${pfDelta.toFixed(2)}` : null}
                  deltaCl={pnlCl(pfDelta)}
                  deltaTip={pfDelta != null ? `Paper − SIM${data.book === 'paper' ? ' · backend divergence.profit_factor_delta' : ''}` : 'Both profit factors required for a delta'} />
                <CmpRow
                  label="Max Drawdown" tip="OOS backtest max drawdown (fraction → %)"
                  simText={signedPctText(simM.max_drawdown)} simCl="qr-pnl-neg"
                  paperText={null} paperTip="No paper max-drawdown figure served by the API"
                  deltaText={null} />
                <CmpRow
                  label="Sharpe" tip="OOS backtest Sharpe ratio"
                  simText={simM.sharpe != null ? simM.sharpe.toFixed(2) : null}
                  paperText={null} paperTip="No paper Sharpe figure served by the API"
                  deltaText={null} />
                <CmpRow
                  label="Closed Trades" tip="SIM: OOS backtest trades · Paper: closed round-trips — different sample windows, so no count delta"
                  simText={simM.total_trades != null ? String(simM.total_trades) : null} simTip="OOS backtest trades (latest run)"
                  paperText={paperM.total_trades != null && paperM.total_trades > 0 ? String(paperM.total_trades) : (paperM.total_trades === 0 ? '0' : null)} paperTip="Closed paper round-trips"
                  deltaText={null} deltaTip="Different sample windows — a count delta is not meaningful" />
                <CmpRow
                  label="Avg Hold" tip="Average holding period of closed trades (calendar days)"
                  simText={simM.avg_holding_days != null ? `${simM.avg_holding_days}d` : null} simTip={simM.avg_holding_days == null ? 'No per-trade OOS rows — aggregate-only backtest' : 'OOS closed trades'}
                  paperText={paperAvgHold != null ? `${paperAvgHold}d` : null} paperTip={paperAvgHold == null ? 'No closed paper round-trips' : 'Closed paper round-trips · gold.paper_trades_synthetic'}
                  deltaText={holdDelta != null ? `${holdDelta >= 0 ? '+' : ''}${holdDelta.toFixed(1)}d` : null}
                  deltaCl={pnlCl(holdDelta)}
                  deltaTip={holdDelta != null ? 'Paper − SIM, calendar days' : 'Both averages required for a delta'} />
                <CmpRow
                  label="Last Trade" tip="Most recent closed trade in each book"
                  simText={null} simTip="Not served as a headline metric — see the Simulation ledger below for per-trade dates"
                  paperText={paperM.last_trade_at ? fmtAge(paperM.last_trade_at) : null} paperTip={paperM.last_trade_at ? `Last closed paper trade ${paperM.last_trade_at}` : 'No closed paper trades yet'}
                  deltaText={null} />
              </tbody>
            </table>
          </div>
          {(uatHas || liveHas) && (
            <div className="px-3 py-1.5 border-t border-white/[0.05] flex items-center gap-x-4 gap-y-1 flex-wrap text-[10px] text-slate-500">
              {(liveM.total_trades || 0) > 0 && (
                <span title="gold.trade_executions">
                  <span className="qr-label mr-1">LIVE</span>
                  <span className="qr-num text-slate-300">{liveM.total_trades} exec</span>
                  {liveM.win_rate != null && <> · WR <span className="qr-num text-slate-300">{(liveM.win_rate * 100).toFixed(1)}%</span></>}
                  {liveM.total_pnl != null && <> · P&L <span className={`qr-num font-bold ${pnlCl(liveM.total_pnl)}`}>{liveM.total_pnl >= 0 ? '+' : ''}{fmtK(liveM.total_pnl)}</span></>}
                  {liveM.last_trade_at && <> · last {fmtAge(liveM.last_trade_at)}</>}
                </span>
              )}
              {uatHas && (
                <span title="IBKR broker rehearsal · gold.paper_uat_fills — fills carry no per-fill P&L">
                  <span className="qr-label mr-1">UAT</span>
                  {(uatM.total_fills || 0) > 0
                    ? <><span className="qr-num text-slate-300">{uatM.total_fills} fills</span>{uatM.last_trade_at && <> · last {fmtAge(uatM.last_trade_at)}</>} · WR/P&L pending round-trip ledger</>
                    : <>no strategy fills yet · UAT live 2026-08-24</>}
                </span>
              )}
            </div>
          )}
        </div>

        {/* ===================== EQUITY & RETURNS ==========================
            Paper (and live, when it has rows) realized curves side by side.
            SIM has no served equity series — backtests publish monthly/yearly
            returns instead, shown below next to the paper realized series. */}
        <div className={`grid grid-cols-1 ${liveHas && (liveM.total_trades || 0) > 0 ? 'lg:grid-cols-2' : ''} gap-3`}>
          <div className="qr-surface overflow-hidden">
            <div className="px-3 py-1.5 border-b border-white/[0.05] flex items-center justify-between gap-2">
              <span className="qr-label" title="gold.paper_trades_synthetic · cumulative realized P&L by exit date">Equity · Paper · realized cum P&L · last {paperPayload?.window_days ?? data.window_days}d</span>
              <span className={`qr-num text-[11px] font-bold ${paperM.total_pnl != null ? pnlCl(paperM.total_pnl) : 'text-slate-500'}`}>{paperM.total_pnl != null ? `${paperM.total_pnl >= 0 ? '+' : ''}${fmtK(paperM.total_pnl)}` : '—'}</span>
            </div>
            <div className="p-2">
              {paperPayload == null ? (
                <div className="flex items-center gap-2 py-4 justify-center text-slate-500 text-[11px]">
                  <div className={`w-3 h-3 border-2 border-slate-700 border-t-blue-500 rounded-full ${bookLoading ? 'animate-spin' : ''}`} />
                  Loading paper curve…
                </div>
              ) : (
                <EquityCurve points={paperPayload.equity_curve} />
              )}
              <div className="text-[9px] text-slate-600 mt-0.5">Cumulative realized P&L by exit date · flat segments = days with no exits (carried, not interpolated) · hover points for values</div>
            </div>
          </div>
          {liveHas && (liveM.total_trades || 0) > 0 && (
            <div className="qr-surface overflow-hidden">
              <div className="px-3 py-1.5 border-b border-white/[0.05] flex items-center justify-between gap-2">
                <span className="qr-label" title="gold.trade_executions · cumulative realized P&L by execution date">Equity · Live · realized cum P&L · last {livePayload?.window_days ?? data.window_days}d</span>
                <span className={`qr-num text-[11px] font-bold ${liveM.total_pnl != null ? pnlCl(liveM.total_pnl) : 'text-slate-500'}`}>{liveM.total_pnl != null ? `${liveM.total_pnl >= 0 ? '+' : ''}${fmtK(liveM.total_pnl)}` : '—'}</span>
              </div>
              <div className="p-2">
                {livePayload == null ? (
                  <div className="flex items-center gap-2 py-4 justify-center text-slate-500 text-[11px]">
                    <div className={`w-3 h-3 border-2 border-slate-700 border-t-blue-500 rounded-full ${bookLoading ? 'animate-spin' : ''}`} />
                    Loading live curve…
                  </div>
                ) : (
                  <EquityCurve points={livePayload.equity_curve} />
                )}
                <div className="text-[9px] text-slate-600 mt-0.5">Cumulative realized P&L by execution date · hover points for values</div>
              </div>
            </div>
          )}
        </div>

        {/* Monthly + yearly returns — both series side by side, each labeled
            with its own basis. SIM: portfolio-level OOS monthly returns
            (consumption.strategy_monthly_returns, compounded YTD). Paper:
            realized P&L by exit month as a fraction of assigned capital
            (simple sum, fixed capital base). Different bases — presented
            adjacent, never merged. */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-3">
          <div className="qr-surface overflow-hidden">
            <div className="px-3 py-1.5 border-b border-white/[0.05] flex items-center gap-2">
              <span className="qr-label" title="consumption.strategy_monthly_returns · portfolio-level OOS monthly returns (decimal fractions, compounded YTD)">Monthly Returns (%) · SIM · OOS backtest</span>
              <span className="qr-chip qr-chip-slate text-[9px] ml-auto">{(data.monthly_returns || []).length} mo</span>
            </div>
            <div className="p-2 grid grid-cols-1 xl:grid-cols-[1fr_104px] gap-2">
              <div>
                {(data.monthly_returns || []).length === 0 ? (
                  <div className="text-[10px] text-slate-600 text-center py-4" title="Monthly aggregation task t_fdfdf106">
                    {(data.backtest_trades || []).length > 0
                      ? 'No monthly return series published for this run — per-trade OOS ledger exists; monthly aggregation pending'
                      : 'No monthly return data — this backtest stored aggregate metrics only'}
                  </div>
                ) : (
                  <MonthlyHeatmap rows={data.monthly_returns} />
                )}
              </div>
              <div className="xl:border-l xl:border-white/[0.05] xl:pl-2">
                <div className="qr-label pb-1" title="gold.strategy_backtest_runs annual_pnl_* · same run as the metrics above">Yearly (%)</div>
                <YearlyReturns
                  yearly={(data.yearly_returns || {}).sim}
                  emptyNote="No annual figures on the backtest run"
                />
              </div>
            </div>
          </div>
          <div className="qr-surface overflow-hidden">
            <div className="px-3 py-1.5 border-b border-white/[0.05] flex items-center gap-2">
              <span className="qr-label" title={`gold.paper_trades_synthetic closed rows by exit month · % of assigned capital${data.assigned_capital ? ` ($${Math.round(data.assigned_capital).toLocaleString()})` : ' (not set)'}`}>Monthly Returns (%) · Paper realized</span>
              <span className="qr-chip qr-chip-slate text-[9px] ml-auto">{(data.monthly_returns_paper || []).length} mo</span>
            </div>
            <div className="p-2 grid grid-cols-1 xl:grid-cols-[1fr_104px] gap-2">
              <div>
                {(data.monthly_returns_paper || []).length === 0 ? (
                  <div className="text-[10px] text-slate-600 text-center py-4">
                    {!data.assigned_capital
                      ? 'No assigned capital — set a capital pool before paper returns can be computed'
                      : 'No closed paper trades yet — realized returns appear after the first exit'}
                  </div>
                ) : (
                  <MonthlyHeatmap rows={data.monthly_returns_paper} />
                )}
              </div>
              <div className="xl:border-l xl:border-white/[0.05] xl:pl-2">
                <div className="qr-label pb-1" title="Realized P&L per exit year · % of assigned capital (simple sum, fixed capital base)">Yearly (%)</div>
                <YearlyReturns
                  yearly={(data.yearly_returns || {}).paper}
                  emptyNote="No realized yearly returns yet"
                />
              </div>
            </div>
          </div>
        </div>

        {/* ===================== LEDGERS (both on screen) ================== */}
        <BookLedgerPanel
          label="Paper ledger"
          source="gold.paper_trades_synthetic"
          payload={paperPayload}
          loading={bookLoading}
          isPaper
          activeSignals={activeSignals}
          watchSignals={watchSignals}
          assignedCapital={data.assigned_capital}
          skipMap={skipMap}
          skipsCount={(data.paper_skips || []).length}
        />

        {/* Simulation ledger — per-trade OOS backtest records (gold.strategy_backtest_trades) */}
        <div className="qr-surface overflow-hidden">
          <div className="px-3 py-1.5 border-b border-white/[0.05] flex items-center gap-2">
            <span className="qr-label" title="gold.strategy_backtest_trades · OOS rows of the latest run">Simulation ledger · OOS backtest</span>
            <span className="qr-chip qr-chip-slate text-[9px] ml-auto">{(data.backtest_trades || []).length} trades</span>
          </div>
          <div className="px-3 py-1 border-b border-white/[0.05] flex items-center gap-1">
            {[
              { id: 'rebalances', label: `Rebalances (${simRebalances.length})` },
              { id: 'allocation', label: `Allocation (${simOpen.length})` },
              { id: 'trades',     label: `Ledger (${(data.backtest_trades || []).length})` },
              { id: 'signals',    label: `Signals (${strategyId.startsWith('hk_ipo') ? (simBuyWatch || []).length : activeSignals.length})` },
            ].map(t => (
              <button
                key={t.id}
                onClick={() => setSimTab(t.id)}
                className={`px-2 py-1 rounded text-[11px] font-semibold transition-colors ${simTab === t.id ? 'bg-white/[0.08] text-white' : 'text-slate-400 hover:text-slate-200'}`}
              >{t.label}</button>
            ))}
          </div>

          {simTab === 'rebalances' && (
            <div className="max-h-[520px] overflow-auto">
              {simRebalances.length === 0 && (
                <div className="py-6 text-center text-slate-600 text-[11px] px-4">No per-trade backtest records — this strategy's backtest stored aggregate metrics only</div>
              )}
              {simRebalances.map((g) => {
                const pnls = g.closed.map(t => t.pnl_pct).filter(v => v != null);
                const avg = pnls.length ? pnls.reduce((s, v) => s + v, 0) / pnls.length : null;
                return (
                  <div key={g.date} className="border-b border-white/[0.04] last:border-0">
                    <div className="px-3 py-2 flex items-center justify-between bg-white/[0.02] sticky top-0">
                      <div className="flex items-center gap-2">
                        <span className="qr-num text-[11px] font-bold text-white">{new Date(g.date).toLocaleDateString('en-GB', { month: '2-digit', day: '2-digit', year: '2-digit' })}</span>
                        <span className="qr-chip qr-chip-slate text-[9px]">{g.closed.length} closed</span>
                      </div>
                      <div className={`qr-num text-[11px] font-bold ${avg != null ? pnlCl(avg) : 'text-slate-500'}`}>{avg != null ? `${avg >= 0 ? '+' : ''}${(avg * 100).toFixed(1)}% avg` : '—'}</div>
                    </div>
                    <div className="overflow-x-auto">
                      <table className="w-full">
                        <tbody className="divide-y divide-white/[0.04]">
                          {g.closed.map((t, i) => (
                            <tr key={`${t.ticker}-${t.entry_date}-${i}`} className="qr-tr-hover">
                              <td className="py-1 px-2 text-white text-[11px] font-mono w-20">{t.ticker}</td>
                              <td className="py-1 px-2 qr-num text-slate-400 text-[10px]">{t.entry_date ? new Date(t.entry_date).toLocaleDateString('en-GB', { month: '2-digit', day: '2-digit' }) : '—'} → {t.exit_date ? new Date(t.exit_date).toLocaleDateString('en-GB', { month: '2-digit', day: '2-digit' }) : 'open'}</td>
                              <td className="py-1 px-2 qr-num text-slate-300 text-right">{fmt(t.entry_price)}</td>
                              <td className="py-1 px-2 qr-num text-slate-300 text-right">→ {fmt(t.exit_price)}</td>
                              <td className={`py-1 px-2 qr-num text-right font-bold ${pnlCl(t.pnl_pct)}`}>{t.pnl_pct != null ? `${t.pnl_pct >= 0 ? '+' : ''}${(t.pnl_pct * 100).toFixed(1)}%` : '—'}</td>
                              <td className="py-1 px-2 text-right text-[9px] text-slate-500 w-28">{t.exit_reason || '—'}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                );
              })}
            </div>
          )}

          {simTab === 'allocation' && (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="sticky top-0 bg-slate-900 z-10">
                  <tr className="border-b border-white/[0.06]">
                    <th className="qr-label text-left py-1 px-2">Ticker</th>
                    <th className="qr-label text-right py-1 px-2">Entry</th>
                    <th className="qr-label text-right py-1 px-2">Entry px</th>
                    <th className="qr-label text-right py-1 px-2" title="Latest close (silver.unified_prices, gold.daily_ohlcv fallback)">Current px</th>
                    <th className="qr-label text-right py-1 px-2" title="Calendar days held at the backtest as-of date">Days</th>
                    <th className="qr-label text-right py-1 px-2" title="Open positions: unrealized P&L marked to the latest close (◦)">P&L %</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/[0.04]">
                  {simOpen.map((t, i) => (
                    <tr key={`${t.ticker}-${t.entry_date}-${i}`} className="qr-tr-hover">
                      <td className="py-1 px-2 text-white text-[11px] font-mono w-24">{t.ticker}</td>
                      <td className="py-1 px-2 qr-num text-slate-400 text-[10px]">{t.entry_date || '—'}</td>
                      <td className="py-1 px-2 qr-num text-slate-300 text-right">{fmt(t.entry_price)}</td>
                      <td className="py-1 px-2 qr-num text-slate-300 text-right" title={t.current_price_date ? `Close ${t.current_price_date} · ${t.price_source || ''}` : undefined}>{t.current_price != null ? fmt(t.current_price) : '—'}</td>
                      <td className="py-1 px-2 qr-num text-slate-300 text-right">{t.holding_days ?? '—'}</td>
                      <td className={`py-1 px-2 qr-num text-right font-bold ${t.unrealized_pnl_pct != null ? pnlCl(t.unrealized_pnl_pct) : 'text-slate-500'}`} title={t.unrealized_pnl_pct != null ? `Unrealized — marked to latest close ${t.current_price_date || ''}` : 'No current price available'}>{t.unrealized_pnl_pct != null ? `${t.unrealized_pnl_pct >= 0 ? '+' : ''}${(t.unrealized_pnl_pct * 100).toFixed(1)}% ◦` : 'open'}</td>
                    </tr>
                  ))}
                  {!simOpen.length && (
                    <tr><td colSpan={6} className="py-6 text-center text-slate-600 text-[11px]">No open positions — every OOS backtest trade is closed</td></tr>
                  )}
                </tbody>
              </table>
              {simOpen.length > 0 && (
                <div className="px-3 py-2 border-t border-white/[0.05] text-[10px] text-slate-600">
                  Open at the OOS backtest as-of date · days held measured to that date · ◦ = unrealized, marked to the latest close
                </div>
              )}
            </div>
          )}

          {simTab === 'trades' && (
            <div className="overflow-x-auto max-h-[520px] overflow-auto">
              <table className="w-full">
                <thead className="sticky top-0 bg-slate-900 z-10">
                  <tr className="border-b border-white/[0.06]">
                    <th className="qr-label text-right py-1 px-2">Entry</th>
                    <th className="qr-label text-right py-1 px-2">Exit</th>
                    <th className="qr-label text-left py-1 px-2">Ticker</th>
                    <th className="qr-label text-right py-1 px-2">Entry px</th>
                    <th className="qr-label text-right py-1 px-2">Exit px</th>
                    <th className="qr-label text-right py-1 px-2">P&L %</th>
                    <th className="qr-label text-right py-1 px-2">Days</th>
                    <th className="qr-label text-right py-1 px-2">Reason</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/[0.04]">
                  {(data.backtest_trades || []).map((t, i) => {
                    const mtmPnl = t.pnl_pct != null ? t.pnl_pct : t.unrealized_pnl_pct;
                    const isMtm = t.pnl_pct == null && t.unrealized_pnl_pct != null;
                    return (
                    <tr key={`${t.ticker}-${t.entry_date}-${i}`} className="qr-tr-hover">
                      <td className="py-1 px-2 qr-num text-slate-400 text-[10px]">{t.entry_date || '—'}</td>
                      <td className="py-1 px-2 qr-num text-slate-400 text-[10px]">{t.exit_date || 'open'}</td>
                      <td className="py-1 px-2 text-white text-[11px] font-mono">{t.ticker}</td>
                      <td className="py-1 px-2 qr-num text-slate-300 text-right">{fmt(t.entry_price)}</td>
                      <td className="py-1 px-2 qr-num text-slate-300 text-right" title={isMtm && t.current_price_date ? `Latest close ${t.current_price_date} · ${t.price_source || ''}` : undefined}>{t.exit_price != null ? fmt(t.exit_price) : (t.current_price != null ? `${fmt(t.current_price)} ◦` : '—')}</td>
                      <td className={`py-1 px-2 qr-num text-right font-bold ${pnlCl(mtmPnl)}`} title={isMtm ? `Unrealized — marked to latest close ${t.current_price_date || ''}` : undefined}>{mtmPnl != null ? `${mtmPnl >= 0 ? '+' : ''}${(mtmPnl * 100).toFixed(1)}%${isMtm ? ' ◦' : ''}` : '—'}</td>
                      <td className="py-1 px-2 qr-num text-slate-300 text-right">{t.holding_days ?? '—'}</td>
                      <td className="py-1 px-2 text-right text-[9px] text-slate-500">{t.exit_reason || '—'}</td>
                    </tr>
                    );
                  })}
                  {!(data.backtest_trades || []).length && (
                    <tr><td colSpan={8} className="py-6 text-center text-slate-600 text-[11px]">No per-trade backtest records</td></tr>
                  )}
                </tbody>
              </table>
            </div>
          )}

          {simTab === 'signals' && (
            strategyId.startsWith('hk_ipo') ? (
              <div className="overflow-x-auto max-h-[520px] overflow-auto">
                <table className="w-full">
                  <thead className="sticky top-0 bg-slate-900 z-10">
                    <tr className="border-b border-white/[0.06]">
                      <th className="qr-label text-left py-1 px-2">Decision</th>
                      <th className="qr-label text-left py-1 px-2">Ticker</th>
                      <th className="qr-label text-left py-1 px-2">Name</th>
                      <th className="qr-label text-right py-1 px-2">Listing</th>
                      <th className="qr-label text-right py-1 px-2" title="20th trading day after listing (measured close date; calendar estimate until then)">Entry +20td</th>
                      <th className="qr-label text-right py-1 px-2">Exit +40td</th>
                      <th className="qr-label text-right py-1 px-2" title="Retail oversubscription — the 100–500x band is the trade filter">Oversub</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-white/[0.04]">
                    {(simBuyWatch || []).map((r, i) => (
                      <tr key={`${r.ticker}-${i}`} className="qr-tr-hover">
                        <td className="py-1 px-2 w-40">
                          <span className={`text-[10px] font-bold ${r.word === 'BUY ON' || r.word === 'ENTERED' ? 'text-white' : r.word === 'WATCH' ? 'text-slate-400' : 'text-slate-600'}`}>{r.word}</span>
                          <span className="block text-[9px] text-slate-500">{r.sub}</span>
                        </td>
                        <td className="py-1 px-2 text-white text-[11px] font-mono w-20">{r.ticker}</td>
                        <td className="py-1 px-2 text-slate-300 text-[10px] max-w-[180px] truncate" title={r.name}>{r.name || '—'}</td>
                        <td className="py-1 px-2 qr-num text-slate-400 text-[10px]">{r.listing}</td>
                        <td className="py-1 px-2 qr-num text-slate-300 text-[10px]">{r.entry}</td>
                        <td className="py-1 px-2 qr-num text-slate-400 text-[10px]">{r.exit}</td>
                        <td className="py-1 px-2 qr-num text-slate-300 text-right">{r.oversub != null ? `${Math.round(r.oversub)}x` : '—'}</td>
                      </tr>
                    ))}
                    {simBuyWatch && !simBuyWatch.length && (
                      <tr><td colSpan={7} className="py-6 text-center text-slate-600 text-[11px]">No IPOs in an entry window — nothing to buy or queue right now</td></tr>
                    )}
                    {!simBuyWatch && (
                      <tr><td colSpan={7} className="py-6 text-center text-slate-600 text-[11px]">Loading IPO calendar…</td></tr>
                    )}
                  </tbody>
                </table>
                <div className="px-3 py-2 border-t border-white/[0.05] text-[10px] text-slate-600">
                  RULE MIRROR of the documented entry rule (oversub 100–500x · D1 close ≥ offer · entry px 0.9–1.3× D1 close · enter +20td, hold 20td) over /api/hkex/ipos — not an engine signal. The 0.9–1.3× D1-close band decides at the entry close; slot cap not modelled.
                </div>
              </div>
            ) : (
              <div className="overflow-x-auto max-h-[520px] overflow-auto">
                <table className="w-full">
                  <thead className="sticky top-0 bg-slate-900 z-10">
                    <tr className="border-b border-white/[0.06]">
                      <th className="qr-label text-left py-1 px-2">Ticker</th>
                      <th className="qr-label text-left py-1 px-2">Signal</th>
                      <th className="qr-label text-right py-1 px-2">Strength</th>
                      <th className="qr-label text-right py-1 px-2">Price</th>
                      <th className="qr-label text-right py-1 px-2">As of</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-white/[0.04]">
                    {activeSignals.map((s, i) => (
                      <tr key={`${s.ticker}-${i}`} className="qr-tr-hover">
                        <td className="py-1 px-2 text-white text-[11px] font-mono w-24">{s.ticker}</td>
                        <td className="py-1 px-2 text-white text-[10px] font-bold">{s.signal}</td>
                        <td className="py-1 px-2 qr-num text-slate-300 text-right">{s.strength != null ? Number(s.strength).toFixed(2) : '—'}</td>
                        <td className="py-1 px-2 qr-num text-slate-300 text-right">{fmt(s.price)}</td>
                        <td className="py-1 px-2 qr-num text-slate-500 text-right text-[10px]">{s.ts ? fmtAge(s.ts) : '—'}</td>
                      </tr>
                    ))}
                    {!activeSignals.length && (
                      <tr><td colSpan={5} className="py-6 text-center text-slate-600 text-[11px]">No current BUY signals from the engine (consumption.strategies_signals_current)</td></tr>
                    )}
                  </tbody>
                </table>
              </div>
            )
          )}
        </div>

        {/* Live ledger — only when the live book has real executions or the
            strategy is deployed LIVE. Same panel anatomy as the paper ledger. */}
        {liveHas && (
          <BookLedgerPanel
            label="Live ledger"
            source="gold.trade_executions"
            payload={livePayload}
            loading={bookLoading}
            isPaper={false}
            activeSignals={activeSignals}
            watchSignals={watchSignals}
            assignedCapital={data.assigned_capital}
            skipMap={skipMap}
            skipsCount={0}
          />
        )}

        {/* UAT fills — broker rehearsal. Shown when the book has fills or the
            strategy is deployed to UAT; fills carry no per-fill P&L. */}
        {uatHas && (
          <div className="qr-surface overflow-hidden">
            <div className="px-3 py-1.5 border-b border-white/[0.05] flex items-center gap-2">
              <span className="qr-label" title="gold.paper_uat_fills · IBKR UAT session broker rehearsal">UAT · broker rehearsal fills</span>
              <span className="qr-chip qr-chip-slate text-[9px] ml-auto">{(data.uat_fills || []).length} fills</span>
            </div>
            {(data.uat_fills || []).length === 0 ? (
              <div className="py-8 text-center px-6 space-y-1.5">
                <div className="text-slate-500 text-[11px]">No strategy-attributed UAT fills yet — <span className="font-mono text-slate-400">gold.paper_uat_fills</span> is empty for this strategy.</div>
                <div className="text-slate-600 text-[10px]">The UAT book went live 2026-08-24. Fills appear here after the first broker-rehearsal execution attributed to this strategy; win rate and P&amp;L need a round-trip ledger (fills carry no per-fill P&amp;L).</div>
              </div>
            ) : (
              <div className="overflow-x-auto max-h-[520px] overflow-auto">
                <table className="w-full">
                  <thead className="sticky top-0 bg-slate-900 z-10">
                    <tr className="border-b border-white/[0.06]">
                      <th className="qr-label text-left py-1 px-2">Time</th>
                      <th className="qr-label text-left py-1 px-2">Symbol</th>
                      <th className="qr-label text-right py-1 px-2">Side</th>
                      <th className="qr-label text-right py-1 px-2">Qty</th>
                      <th className="qr-label text-right py-1 px-2">Price</th>
                      <th className="qr-label text-right py-1 px-2">Ccy</th>
                      <th className="qr-label text-right py-1 px-2">Order Ref</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-white/[0.04]">
                    {data.uat_fills.map((f, i) => (
                      <tr key={f.exec_id || i} className="qr-tr-hover">
                        <td className="py-1 px-2 qr-num text-slate-400 text-[10px]">{f.ts ? new Date(f.ts).toLocaleString('en-GB', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' }) : '—'}</td>
                        <td className="py-1 px-2 text-white text-[11px] font-mono">{f.ticker}</td>
                        <td className="py-1 px-2 text-right">
                          <span className={`qr-chip ${f.side === 'BUY' || f.side === 'BOT' ? 'qr-chip-emerald' : 'qr-chip-rose'}`}>{f.side}</span>
                        </td>
                        <td className="py-1 px-2 qr-num text-slate-300">{fmt(f.quantity, 0)}</td>
                        <td className="py-1 px-2 qr-num text-slate-300">{fmt(f.price)}</td>
                        <td className="py-1 px-2 qr-num text-slate-500 text-[10px]">{f.currency || '—'}</td>
                        <td className="py-1 px-2 text-right text-[9px] text-slate-500">{f.order_ref || '—'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}

        {/* Research notes & disclosures — the registry description verbatim
            (research-owned text). For EXPERIMENTAL rows this carries the audit
            trail and caveats. Kept below the performance data; scrolls when long. */}
        {data.description && (
          <div className="qr-surface px-3 py-2">
            <div className="qr-label mb-1">Research notes &amp; disclosures</div>
            <p className="text-[10px] text-slate-400 leading-relaxed whitespace-pre-line max-h-32 overflow-auto">{data.description}</p>
          </div>
        )}

        {/* Logic + Universe — mode-independent configuration detail */}
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

        {/* Ops panels — act on the strategy's real deployment mode. The removed
            statistics-view toggle never touched these; promotion gates are
            unchanged. */}
        <PromotionPanel
          strategyId={strategyId}
          currentMode={data.execution_mode || 'SIMULATION'}
          onPromoted={() => load()}
        />

        <CapitalAllocationPanel
          strategyId={strategyId}
          executionMode={data.execution_mode || 'SIMULATION'}
          activeSignalCount={activeSignals.length}
        />

        <RiskWatchPanel
          strategyId={strategyId}
          executionMode={data.execution_mode || 'SIMULATION'}
          onDemoted={() => load()}
        />
      </div>
    );
  })();

  return body;
};

export default StrategyDetail;
