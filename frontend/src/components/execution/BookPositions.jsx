import React from 'react';
import { fmt, fmtK, fmtPct, pnlCl } from '../../utils';

// Shared Positions section for all four Execution books (2026-09-18 goal:
// one trading UI, books differ only by mode + data source).
// The sim book's PositionTable anatomy was the best of the four implementations
// (group header with count + total value + total P&L) and is the base here.
// Positions are split into two always-present sections by measured unrealized
// P&L: Positive Return (pnl >= 0) and Negative Return (pnl < 0). Rows with no
// P&L mark (null) are unscored — never bucketed as zero; they are excluded
// from both sections and counted in an explicit note.

// ---------------------------------------------------------------------------
// Per-book row normalizers → one shared row shape:
//   { key, ticker, sub, side, qty, entry, current, value, pnl, pnlPct, raw }
// sub = secondary line (strategy / venue / source), pnlPct may be null
// (derived from entry/current when the backend does not serve one).
// ---------------------------------------------------------------------------

export const normSimPosition = (p) => ({
  key: p.id ?? p.ticker,
  ticker: p.ticker,
  sub: [p.strategy_id, p.asset_class].filter(Boolean).join(' · '),
  side: p.side,
  qty: p.quantity,
  entry: p.avg_entry_price ?? p.entry_price,
  current: p.current_price,
  value: p.market_value,
  pnl: p.unrealized_pnl ?? p.pnl ?? null,
  pnlPct: null,
  raw: p,
});

export const normPaperPosition = (p) => {
  const qty = p.shares ?? p.contracts ?? null;
  const current = p.current_price ?? null;
  return {
    key: p.id ?? p.ticker,
    ticker: p.ticker || p.instrument,
    sub: [p.strategy_id, p.hold_duration ? `held ${String(p.hold_duration).split('.')[0]}` : null].filter(Boolean).join(' · '),
    side: (p.direction || '').toUpperCase() || null,
    qty,
    entry: p.entry_price ?? null,
    current,
    value: qty != null && current != null ? qty * current : null,
    pnl: p.unrealised_pnl ?? null,
    // Backend serves unrealised_pnl_pct already percent-scaled — prefer it
    // over a frontend re-derivation.
    pnlPct: typeof p.unrealised_pnl_pct === 'number' ? p.unrealised_pnl_pct : null,
    raw: p,
  };
};

export const normUatPosition = (p) => ({
  key: p.symbol ?? p.ticker,
  ticker: p.ticker ?? p.symbol,
  sub: [p.exchange, p.currency].filter(Boolean).join(' · '),
  side: (p.qty ?? 0) >= 0 ? 'LONG' : 'SHORT',
  qty: p.qty != null ? Math.abs(p.qty) : null,
  entry: p.avg_cost ?? null,
  current: p.market_price ?? null,
  value: p.market_value ?? null,
  pnl: p.unrealized_pnl ?? null,
  pnlPct: null,
  raw: p,
});

export const normLivePosition = (p) => {
  const qty = p.quantity ?? null;
  const current = p.current_price ?? null;
  return {
    key: p.id ?? p.ticker,
    ticker: p.ticker,
    sub: (p.source || '').replace('ibkr_snapshot', 'ibkr') || null,
    side: p.side,
    qty,
    entry: p.avg_entry ?? null,
    current,
    value: qty != null && current != null ? qty * current : null,
    pnl: p.unrealized_pnl ?? null,
    pnlPct: null,
    raw: p,
  };
};

// Manual book (Execution > Manual tab): discretionary hand-entered positions
// from /api/execution/manual/positions. Same columns as Paper minus Strategy;
// the sub line carries market · held-days · notes instead.
export const normManualPosition = (p) => {
  const qty = p.qty ?? null;
  const current = p.current_price ?? null;
  return {
    key: p.id,
    ticker: p.symbol,
    sub: [p.market, p.held_days != null ? `held ${p.held_days}d` : null, p.notes]
      .filter(Boolean).join(' · '),
    side: p.side,
    qty,
    entry: p.entry_price ?? null,
    current,
    value: p.market_value ?? (qty != null && current != null ? qty * current : null),
    pnl: p.unrealized_pnl ?? null,
    pnlPct: null,  // shared helper derives % with the SHORT sign flip
    raw: p,
  };
};

// ---------------------------------------------------------------------------

const SIDE_CHIP = { LONG: 'qr-chip-emerald', SHORT: 'qr-chip-rose', BUY: 'qr-chip-emerald', SELL: 'qr-chip-rose' };

const pnlPctOf = (r) => {
  if (r.pnlPct != null) return r.pnlPct;
  if (r.entry > 0 && r.current != null) {
    return ((r.current - r.entry) / r.entry) * 100 * (r.side === 'SHORT' ? -1 : 1);
  }
  return null;
};

const SectionCard = ({ title, rows, renderAction }) => {
  const totValue = rows.reduce((s, r) => s + (r.value || 0), 0);
  const totPnl = rows.reduce((s, r) => s + (r.pnl || 0), 0);
  return (
    <div className="qr-surface overflow-hidden">
      <div className="px-3 py-2 border-b border-white/[0.05] flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="qr-label">{title}</span>
          <span className="text-[10px] text-slate-500">{rows.length} positions</span>
        </div>
        <div className="flex items-center gap-3">
          <span className="qr-num text-[11px] text-slate-400">{fmtK(totValue)}</span>
          <span className={`qr-num text-[11px] font-bold ${pnlCl(totPnl)}`}>{totPnl >= 0 ? '+' : ''}{fmtK(totPnl)}</span>
        </div>
      </div>
      {rows.length === 0 ? (
        <div className="py-4 text-center text-slate-600 text-[11px]">None</div>
      ) : (
        <div className="overflow-x-auto max-h-72 overflow-y-auto">
          <table className="w-full">
            <thead className="qr-th-sticky">
              <tr className="border-b border-white/[0.06]">
                {['Ticker', 'Side', 'Qty', 'Entry', 'Current', 'Value', 'P&L', 'P&L %'].map(h =>
                  <th key={h} className="qr-label text-right py-1 px-2 first:text-left">{h}</th>)}
                {renderAction && <th className="qr-label text-right py-1 px-2"></th>}
              </tr>
            </thead>
            <tbody className="divide-y divide-white/[0.04]">
              {rows.map((r, i) => {
                const pct = pnlPctOf(r);
                return (
                  <tr key={`${r.key}-${i}`} className="qr-tr-hover">
                    <td className="py-1 px-2">
                      <span className="text-[11px] font-mono text-white">{r.ticker || '—'}</span>
                      {r.sub && <span className="ml-1.5 text-[9px] text-slate-500">{r.sub}</span>}
                    </td>
                    <td className="py-1 px-2 text-right">
                      <span className={`qr-chip ${SIDE_CHIP[r.side] || 'qr-chip-slate'}`}>{r.side || '—'}</span>
                    </td>
                    <td className="py-1 px-2 qr-num text-slate-300">{fmt(r.qty, 0)}</td>
                    <td className="py-1 px-2 qr-num text-slate-400">{r.entry != null ? `$${fmt(r.entry)}` : '—'}</td>
                    <td className="py-1 px-2 qr-num text-slate-300">{r.current != null ? `$${fmt(r.current)}` : '—'}</td>
                    <td className="py-1 px-2 qr-num text-slate-300">{r.value != null ? fmtK(r.value) : '—'}</td>
                    <td className={`py-1 px-2 qr-num font-bold ${pnlCl(r.pnl)}`}>{r.pnl != null ? fmtK(r.pnl) : '—'}</td>
                    <td className={`py-1 px-2 qr-num ${pnlCl(pct)}`}>{pct != null ? fmtPct(pct) : '—'}</td>
                    {renderAction && (
                      <td className="py-1 px-2 text-right whitespace-nowrap">{renderAction(r)}</td>
                    )}
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};

// rows: normalized rows (use the norm*Position helpers above).
// renderAction(row): optional per-row action cell (book-specific close wiring
// stays in the book panel — safeguards are not shared UI).
// strip: optional thin book-level line above the sections (source/stale notes).
// Sections are ordered by P&L % return: winners best-first, losers
// worst-first; rows with no derivable % sink to the bottom of their section.
export const PositionsByReturn = ({ rows, renderAction, strip }) => {
  const byPct = (dir) => (a, b) => {
    const pa = pnlPctOf(a), pb = pnlPctOf(b);
    if (pa == null && pb == null) return 0;
    if (pa == null) return 1;
    if (pb == null) return -1;
    return dir === 'desc' ? pb - pa : pa - pb;
  };
  const winners = rows.filter(r => r.pnl != null && r.pnl >= 0).sort(byPct('desc'));
  const losers = rows.filter(r => r.pnl != null && r.pnl < 0).sort(byPct('asc'));
  const unscored = rows.length - winners.length - losers.length;
  return (
    <>
      {strip && <div className="flex items-center justify-end gap-2 px-1">{strip}</div>}
      <SectionCard title="Positive Return" rows={winners} renderAction={renderAction} />
      <SectionCard title="Negative Return" rows={losers} renderAction={renderAction} />
      {unscored > 0 && (
        <div className="px-1 text-[9px] text-slate-600" title="These rows have no P&L mark from the source — excluded from both sections rather than counted as zero">
          {unscored} position{unscored === 1 ? '' : 's'} unscored — no P&L mark
        </div>
      )}
    </>
  );
};

export default PositionsByReturn;
