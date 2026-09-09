import React, { useState, useMemo, useCallback, useEffect } from 'react';
import { fmtPct, api, usePoll } from '../utils';
import { Chip, Button, ModeBadge, pnlColor } from './jtkit';
import { YearlyBars } from './StrategiesWorkspace';
import { pctAsIs, fracToPct } from './strategyProfiles';

// =================================================================
// IPO subtab (Strategies > IPO) — HK IPO only, redesign 2026-09-02
// Stage-pipeline reorg 2026-09-03 (3 stages since 2026-09-04 — PUBLIC removed:
//   once listed, names live in the normal ticker pool; a flat list of every
//   listed IPO added no value here):
//     1 ANNOUNCED (pre-subscription) — "start looking"
//     2 UNDER SUBSCRIPTION — "monitor whether to apply"
//     3 GREY MARKET — subscription closed, listing imminent; grey trend
//   One global window toggle (1M/3M/6M/YTD/2Y) drives the IPO sentiment
//   sector table (server-side window), the IPO KPI stats strip (client-side
//   listing-date filter), and the rule-mirror ticker list (entry windows
//   inside the selected window).
//   HK IPO STRATEGIES cards are compact, themed like the Strategies >
//   Performance subtab (jt-surface + jtkit + YearlyBars): backtest metrics,
//   annual bars, SIM/PAPER/UAT/LIVE mode ladder strip, engine/ledger
//   one-liners. Position/trade tables live in ACTIVE IPO BOOK and the
//   Strategy Detail page. The rule-mirror ticker list is a mechanical mirror
//   of the documented rule, labelled as such — never the engine signal.
//
// Data sources:
//   GET /api/hkex/ipos?limit=2000     enriched list: calendar + details + performance
//                                     + price range/lot/grey (silver) + day-20 (lateral
//                                     silver.unified_prices until gold.return_day20_pct
//                                     is backfilled — qr_etl t_e71cffde); NULLS LAST —
//                                     A1-/A1G- announced placeholders trail the dated rows
//   GET /api/hkex/ipos/subscription   open/upcoming subscription windows
//                                     (feed incomplete — qr_etl t_e71cffde)
//   GET /api/hkex/ipos/book           active paper-book positions in IPO names
//   GET /api/hkex/ipos/sectors        2y sector aggregates
//   GET /api/strategies/researcher    strategy book, filtered to HK IPO strategies
//   GET /api/strategies/{id}/evaluation  per-strategy mode metrics + engine signal
//
// Chinese names: gold.hk_ipo_calendar.stock_name_zh — served self-adapting on
// /api/hkex/ipos, /ipos/subscription and /ipos/book (t_437922f4, t_077987b2).
// Rows where the column is still NULL render EN primary + a quiet
// "EN only · zh pending" sub-line.
// =================================================================

const CSS = `
.ipo-panel{background:#10141c;border:1px solid #161b25;border-radius:8px;}
.ipo-head{display:flex;align-items:center;justify-content:space-between;padding:13px 16px;border-bottom:1px solid #161b25;}
.ipo-title{font-size:11px;color:#8b93a3;letter-spacing:.5px;font-weight:600;display:flex;align-items:center;gap:8px;}
.ipo-tag{font-size:9px;font-weight:700;letter-spacing:.4px;padding:2px 7px;border-radius:4px;}
.ipo-tag-live{background:#0e3630;color:#2dd4bf;}
.ipo-tag-pending{background:#1b2230;color:#8b93a3;}
.ipo-tag-paper{background:#1b2230;color:#8b93a3;}
.ipo-tag-exp{background:#1b2230;color:#8b93a3;}
.ipo-tag-watch{background:#1b2230;color:#8b93a3;}
.ipo-stat{background:#10141c;border:1px solid #161b25;border-radius:8px;padding:12px 14px;}
.ipo-tbl{width:100%;border-collapse:collapse;}
.ipo-tbl th{text-align:left;font-size:10px;color:#565e6c;letter-spacing:.3px;font-weight:600;padding:8px 10px;border-bottom:1px solid #161b25;white-space:nowrap;}
.ipo-tbl td{padding:10px;border-bottom:1px solid #161b25;font-size:12px;vertical-align:middle;white-space:nowrap;}
.ipo-tbl tr:last-child td{border-bottom:none;}
.ipo-tbl tbody tr:hover td{background:#12161f;}
.ipo-tbl th.num,.ipo-tbl td.num{text-align:right;font-family:ui-monospace,'JetBrains Mono',monospace;font-variant-numeric:tabular-nums;}
.ipo-tbl th.sortable{cursor:pointer;user-select:none;}
.ipo-tbl thead th{position:sticky;top:0;background:#10141c;z-index:1;}
.ipo-tbl th.sortable:hover{color:#8b93a3;}
.ipo-ticker{color:#e6e8eb;font-family:ui-monospace,'JetBrains Mono',monospace;font-weight:600;}
.ipo-name{color:#e6e8eb;font-size:12px;}
.ipo-name-en{color:#565e6c;font-size:10px;}
.ipo-co{color:#8b93a3;font-size:11px;}
.ipo-green{color:#34d399;} .ipo-red{color:#f87171;} .ipo-faint{color:#565e6c;}
.ipo-pill{font-size:9px;font-weight:700;padding:3px 8px;border-radius:4px;letter-spacing:.3px;white-space:nowrap;}
.ipo-st-book{background:#1b2230;color:#8b93a3;}
.ipo-st-listing{background:#1b2230;color:#8b93a3;}
.ipo-st-hold{background:#1b2230;color:#8b93a3;}
.ipo-st-exit{background:#1b2230;color:#8b93a3;}
.ipo-st-urgent{background:#331717;color:#f87171;}
.ipo-st-open{background:#1b2230;color:#8b93a3;}
.ipo-btn{font-size:11px;font-weight:600;padding:6px 12px;border-radius:6px;border:1px solid #1d2430;background:transparent;color:#8b93a3;cursor:pointer;}
.ipo-btn:hover{border-color:#565e6c;color:#e6e8eb;}
.ipo-btn:disabled{opacity:.4;cursor:not-allowed;}
.ipo-btn:disabled:hover{border-color:#1d2430;color:#8b93a3;}
.ipo-btn-primary{background:#1b2230;color:#8b93a3;border-color:#1d2430;}
.ipo-yr{font-size:11px;padding:4px 10px;border-radius:5px;border:1px solid #1d2430;color:#565e6c;cursor:pointer;background:transparent;}
.ipo-yr.active{background:#12161f;color:#e6e8eb;border-color:#565e6c;}
.ipo-note{font-size:11px;color:#565e6c;line-height:1.6;padding:12px 16px;border-top:1px solid #161b25;}
.ipo-note code{font-family:ui-monospace,monospace;color:#8b93a3;background:#12161f;padding:1px 5px;border-radius:3px;}
.ipo-sector-row{display:flex;justify-content:space-between;padding:7px 0;border-bottom:1px solid #161b25;font-size:11px;}
.ipo-sector-row:last-child{border-bottom:none;}
.ipo-stages{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:10px;padding:14px 16px;}
.ipo-split{display:grid;grid-template-columns:minmax(0,5fr) minmax(0,7fr);gap:16px;align-items:start;}
.ipo-split>*{min-width:0;}
@media (max-width:1200px){.ipo-split{grid-template-columns:minmax(0,1fr);}}
/* ticker column stays put while the 13-col table scrolls horizontally */
.ipo-tbl .ipo-stick{position:sticky;left:0;background:#10141c;z-index:2;}
.ipo-tbl thead .ipo-stick{z-index:3;}
.ipo-stage{border:1px solid #161b25;border-radius:8px;padding:10px 12px;cursor:pointer;background:#0d1118;text-align:left;}
.ipo-stage:hover{border-color:#2a3242;}
.ipo-stage.active{border-color:#565e6c;background:#12161f;}
.ipo-stage .step{font-size:9px;color:#565e6c;letter-spacing:.5px;font-weight:700;}
.ipo-stage .n{font-size:20px;font-weight:600;font-family:ui-monospace,monospace;color:#e6e8eb;margin:2px 0;}
.ipo-stage .sub{font-size:10px;color:#565e6c;line-height:1.5;}
`;

const num = (v, d = 2) => v == null || isNaN(v) ? '—' : Number(v).toLocaleString(undefined, { minimumFractionDigits: d, maximumFractionDigits: d });
const signed = (v, d = 1) => v == null ? '—' : `${v >= 0 ? '+' : ''}${Number(v).toFixed(d)}%`;
const sgnCl = (v) => v == null ? 'ipo-faint' : v >= 0 ? 'ipo-green' : 'ipo-red';
const median = (arr) => {
  if (!arr.length) return null;
  const s = [...arr].sort((a, b) => a - b);
  const m = s.length >> 1;
  return s.length % 2 ? s[m] : (s[m - 1] + s[m]) / 2;
};
const daysSince = (dateStr) => {
  if (!dateStr) return null;
  return Math.floor((Date.now() - new Date(dateStr + 'T00:00:00Z').getTime()) / 86400000);
};
const TODAY = new Date().toISOString().slice(0, 10);
const addDays = (dateStr, n) => {
  const d = new Date(dateStr + 'T00:00:00Z');
  d.setUTCDate(d.getUTCDate() + n);
  return d.toISOString().slice(0, 10);
};

// 4-stage lifecycle classification from the calendar fields the API already serves
const stageOf = (r) => {
  const ld = r.listing_date, as = r.application_start, ae = r.application_end;
  if (ld && ld <= TODAY) return 'public';
  if (as && ae && as <= TODAY && TODAY <= ae) return 'subscription';
  if (ae && ae < TODAY) return 'grey';
  return 'announced';
};
const STAGES = [
  { key: 'announced',    step: 'STAGE 1', label: 'ANNOUNCED',          hint: 'pre-subscription · start looking' },
  { key: 'subscription', step: 'STAGE 2', label: 'UNDER SUBSCRIPTION', hint: 'window open · decide whether to apply' },
  { key: 'grey',         step: 'STAGE 3', label: 'GREY MARKET',        hint: 'closed · listing imminent · grey trend' },
];

// Global window toggle — drives IPO SENTIMENT (server-side) + IPO KPIs (client-side).
const WINDOWS = [
  { k: '1m', label: '1M' },
  { k: '3m', label: '3M · last Q' },
  { k: '6m', label: '6M · 1H' },
  { k: 'ytd', label: 'YTD' },
  { k: '2y', label: '2Y · all' },
];
const windowCutoff = (k) => {
  const d = new Date();
  if (k === 'ytd') return `${d.getUTCFullYear()}-01-01`;
  if (k === '1m') d.setUTCMonth(d.getUTCMonth() - 1);
  else if (k === '3m') d.setUTCMonth(d.getUTCMonth() - 3);
  else if (k === '6m') d.setUTCMonth(d.getUTCMonth() - 6);
  else d.setUTCFullYear(d.getUTCFullYear() - 2); // 2y
  return d.toISOString().slice(0, 10);
};

const Panel = ({ title, tag, right, note, children, scroll }) => (
  <div className="ipo-panel">
    <div className="ipo-head">
      <div className="ipo-title">{title}{tag}</div>
      {right && <div style={{ fontSize: 10, color: '#565e6c' }}>{right}</div>}
    </div>
    {scroll ? <div style={{ overflowX: 'auto' }}>{children}</div> : children}
    {note && <div className="ipo-note">{note}</div>}
  </div>
);

const Tag = ({ kind, children }) => <span className={`ipo-tag ipo-tag-${kind}`}>{children}</span>;

const Stat = ({ label, value, sub, green }) => (
  <div className="ipo-stat">
    <div style={{ fontSize: 10, color: '#565e6c', letterSpacing: '.4px', marginBottom: 8 }}>{label}</div>
    <div className={green ? 'ipo-green' : ''} style={{ fontSize: 20, fontWeight: 600, fontFamily: 'ui-monospace,monospace' }}>{value}</div>
    <div style={{ fontSize: 10, color: '#565e6c', marginTop: 4 }}>{sub || ' '}</div>
  </div>
);

const NameCell = ({ zh, en }) => (
  <td>
    <div className="ipo-name">{zh || en || '—'}</div>
    {zh && en
      ? <div className="ipo-name-en">{en}</div>
      : !zh && en && <div className="ipo-name-en" title="Chinese name pending upstream — qr_etl t_437922f4">EN only · zh pending</div>}
  </td>
);

// Min investment for one board lot at top of range, incl. ~0.77% brokerage/levies estimate
const minInvestment = (r) => {
  const px = r.fixed_price ? r.offer_price : (r.offer_price_high ?? r.offer_price);
  if (px == null || !r.lot_size) return null;
  return Math.round(px * r.lot_size * 1.0077);
};

const OfferRangeCell = ({ r }) => (
  <td className="num">
    {r.fixed_price
      ? `${num(r.offer_price)} (fixed)`
      : r.offer_price_low != null
        ? `${num(r.offer_price_low)}–${num(r.offer_price_high)}`
        : r.offer_price != null
          ? num(r.offer_price)
          : <span className="ipo-faint" title="Offer range not published upstream — qr_etl t_90585bf2">—</span>}
  </td>
);

// ---- HK IPO strategy card ----------------------------------------------
// Actionable card: backtest block, annual returns, SIM/PAPER/UAT/LIVE mode
// ladder (mirrors the Strategy Detail tab), engine state, and an
// entry-window watchlist that mechanically mirrors the documented rule
// (oversub 100–500x · enter +20 trading days · hold 20 trading days).
// The watchlist is labelled as a rule mirror — the engine's actual signal
// state is shown separately from the evaluation endpoint.

const DRIFT_RULE = { bandLo: 100, bandHi: 500, entryTd: 20, holdTd: 20, d1Lo: 0.9, d1Hi: 1.3 };

// Card display order in HK IPO STRATEGIES — deterministic regardless of the
// researcher book's row order: day-1 momentum first, then the post-listing
// drift lineage (V3 frozen baseline, then the P2 deal-health variant).
// Unknown HK IPO strategies trail, sorted by id.
const STRATEGY_ORDER = {
  hk_ipo_day1_green_momentum_v1: 0,
  hk_ipo_postlisting_drift_p1_v3: 1,
  hk_ipo_postlisting_drift_p2: 2,
};

// Short column tags for the per-strategy decision columns in the ticker list —
// one column per HK IPO strategy, in card order. Full name + rule ride in
// tooltips; the cell itself answers "is it a buy, and when".
const STRAT_COLS = [
  { id: 'hk_ipo_day1_green_momentum_v1',     tag: 'D1', name: 'HK IPO Day-1 Green Momentum V1',
    rule: 'buy at day-1 close if Main-board · oversub ≥500x · green day-1 · no-chase ≤1.5× offer — exit listing+5td' },
  { id: 'hk_ipo_postlisting_drift_p1_v3',    tag: 'V3', name: 'HK IPO Post-Listing Drift V3',
    rule: 'buy at listing+20td close if oversub 100–500x · entry px within 0.9–1.3× day-1 close — exit +40td' },
  { id: 'hk_ipo_postlisting_drift_p2',       tag: 'P2', name: 'HK IPO Post-Listing Drift P2',
    rule: 'buy at listing+20td close if Main-board · oversub 100–500x · day-1 close ≥ offer — exit −10% stop or +40td · max 1 per listing-week' },
];

// Per-strategy engine-convention notes, rendered on the card. The mirror legs
// ARE the engine bar convention since 2026-09-07 (OFFSET 20/40 after the
// offset-19/39 off-by-one was fixed in hkex.py); remaining divergence is
// mechanics only (stop, weekly cap). Signal text stays research-owned
// (registry description/exit_logic, rendered verbatim).
const ENGINE_NOTES = {
  hk_ipo_postlisting_drift_p2:
    'Engine legs match the mirror columns (bar 20 entry / bar 40 exit). −10% stop can exit earlier; max 1 per listing-week.',
};

const watchRow = (r) => {
  // entry = 20th trading day after listing, exit = 40th (enter +20td, hold 20td).
  // API serves measured day20/day40 closes; dates fall back to ≈ calendar estimates.
  const entry = r.day20_date || (r.listing_date ? addDays(r.listing_date, 28) : null); // ≈20td
  if (!entry) return null;
  const exit = r.day40_date || addDays(entry, 28); // ≈ +20td hold
  const estimated = !r.day20_date;
  const exitEstimated = !r.day40_date;
  const chg = r.current_price != null && r.offer_price ? (r.current_price / r.offer_price - 1) * 100 : null;
  let phase, daysToEntry = null, daysToListing = null;
  if (r.listing_date && r.listing_date > TODAY) {
    // not yet listed — the whole entry/exit timeline is a calendar estimate
    phase = 'pre_listing'; daysToListing = -daysSince(r.listing_date);
  } else if (TODAY < entry) { phase = 'ahead'; daysToEntry = -daysSince(entry); }
  else if (TODAY <= exit) phase = 'in_hold';
  else phase = 'passed';
  const ipoPx = r.offer_price ?? r.offer_price_high ?? null;
  const entryPx = r.day20_price ?? null;
  const exitPx = r.day40_price ?? null;
  // trade P&L of the rule-mirror round trip: entry close -> exit close.
  // realized once the exit day has traded; mark-to-current while in the hold window.
  let pnl = null, pnlKind = null;
  if (phase === 'passed' && entryPx && exitPx) { pnl = (exitPx / entryPx - 1) * 100; pnlKind = 'realized'; }
  else if (phase === 'in_hold' && entryPx && r.current_price) { pnl = (r.current_price / entryPx - 1) * 100; pnlKind = 'open'; }
  // V3 D1-close band: entry px must sit within [0.90, 1.30]x the first-day close
  // (registry description, verified against engine fills 2026-09-07). Decidable only
  // once the entry leg is measured — ahead/pre-listing rows stay d1Out=false.
  const d1Ratio = entryPx != null && r.first_day_close ? entryPx / r.first_day_close : null;
  const d1Out = d1Ratio != null && (d1Ratio < DRIFT_RULE.d1Lo || d1Ratio > DRIFT_RULE.d1Hi);
  return { ...r, entry, exit, entryEstimated: estimated, exitEstimated, phase, daysToEntry, daysToListing, chg, ipoPx, entryPx, exitPx, pnl, pnlKind, d1Ratio, d1Out };
};

// Rule-mirror watch list. Shows ALL IPOs in the selected window — the
// oversub band (100–500x) is the strategy's trade filter, not a list
// filter. Rows are flagged in-band/out-of-band instead of dropped, so hot
// names (>500x) and quiet ones (<100x) stay visible with the reason they
// sit outside the strategy; headline stats still describe the in-band
// cohort only. PLUS names not yet listed (listing_date in the future) so
// the listing → +20td entry → +40td exit timeline is visible before the
// fact. Pre-listing rows bypass the oversub band: retail oversubscription
// is only published at allotment (~1 trading day before listing) —
// qr_etl t_90585bf2 — so band membership is undecidable until then and the
// row says so.
// With a sector selected (click a row in IPO SENTIMENT): ALL of that
// sector's IPOs in the selected window, same columns, oversub band
// not applied.
const computeWatch = (ipos, sectorFilter, ipoWindow) => {
  if (!ipos) return null;
  const base = ipos.filter(r => r.listing_date && r.listing_date <= TODAY);
  const cutoff = windowCutoff(ipoWindow);
  const rows = (sectorFilter
    ? base.filter(r => r.sector === sectorFilter && r.listing_date >= cutoff)
    : base)
    .map(watchRow)
    .filter(Boolean)
    .map(r => ({ ...r, inBand: r.oversubscription_retail != null && r.oversubscription_retail >= DRIFT_RULE.bandLo && r.oversubscription_retail <= DRIFT_RULE.bandHi && !r.d1Out }))
    // listed in the window OR entering in the window — recently listed
    // names whose +20td entry is still ahead must stay visible.
    .filter(r => sectorFilter || r.listing_date >= cutoff || r.entry >= cutoff);
  // upcoming (not yet listed) — band undecidable until allotment, always shown
  const pre = ipos
    .filter(r => r.listing_date && r.listing_date > TODAY && (!sectorFilter || r.sector === sectorFilter))
    .map(watchRow)
    .filter(Boolean)
    .sort((a, b) => a.listing_date.localeCompare(b.listing_date));
  const inHold = rows.filter(r => r.phase === 'in_hold').sort((a, b) => a.exit.localeCompare(b.exit));
  const ahead = rows.filter(r => r.phase === 'ahead').sort((a, b) => a.entry.localeCompare(b.entry));
  const passed = rows.filter(r => r.phase === 'passed').sort((a, b) => b.exit.localeCompare(a.exit));
  // Strategy-cohort stats: in-band names only (the band is what V3 trades);
  // in sector drill-down the band is not applied, so stats cover all rows.
  const cohort = sectorFilter ? passed : passed.filter(r => r.inBand);
  const closed = cohort.filter(r => r.pnl != null);
  const wins = closed.filter(r => r.pnl > 0).length;
  const sum = closed.reduce((a, r) => a + r.pnl, 0);
  return {
    // Ordered by IPO listing date, newest first (upcoming listings on top) —
    // the list is a chronological tape of the window, not phase-grouped.
    all: [...inHold, ...ahead, ...pre, ...passed]
      .sort((a, b) => (b.listing_date || '').localeCompare(a.listing_date || '')),
    counts: { inHold: inHold.length, ahead: ahead.length, preListing: pre.length, passed: passed.length },
    bandCount: sectorFilter ? null : rows.filter(r => r.inBand).length,
    rowCount: rows.length,
    stats: closed.length ? {
      n: closed.length, wins,
      winRate: wins / closed.length * 100,
      avg: sum / closed.length, sum,
    } : null,
  };
};

// ---- per-strategy round-trips (rule mirror) --------------------------------
// Deterministic mirror of the registry rules (research-owned text lives on the
// cards). Answers per ticker, per strategy: does it enter the market, and if
// so the exact BUY date and SELL date for THAT strategy, plus the P&L % once
// the exit signal has triggered (◦ = still open, marked to current). word:
// BUY (rule fires — entry date is when to buy) · BOUGHT (entry leg already
// measured/passed) · SKIP (a rule condition fails) · WATCH (a required input
// is not published yet — retail oversub lands at allotment, qr_etl
// t_90585bf2). Where the engine's own backtest ledger has a round-trip in the
// name, the cell shows the engine trade instead (see StratDecisionCell) —
// engine truth beats the mirror.
const D1_RULE = { bandLo: 500, chaseHi: 1.5, holdTd: 5 };

const mmdd = (d) => (d || '').slice(5).replace('-', '/');
// HK GEM board codes are 8xxx; all three IPO strategies are Main-board only
// (D1/P2 say so verbatim in the registry).
const isGem = (t) => /^8\d{3}\./.test(t || '');

const stratDecision = (stratId, r) => {
  const oversub = r.oversubscription_retail;
  const d1c = r.first_day_close;
  const offer = r.ipoPx;
  const oversubPending = oversub == null
    ? (r.phase === 'pre_listing' ? 'band at allotment' : 'oversub pending (t_90585bf2)')
    : null;

  if (stratId === 'hk_ipo_day1_green_momentum_v1') {
    const tip = `Day-1 Green Momentum V1 — ${STRAT_COLS[0].rule}`;
    if (isGem(r.ticker)) return { word: 'SKIP', sub: 'GEM · main-board only', tip };
    if (oversubPending) return { word: 'WATCH', date: r.listing_date, sub: oversubPending, tip: `${tip}. Decision is the day-1 close on ${r.listing_date}.` };
    if (oversub < D1_RULE.bandLo) return { word: 'SKIP', sub: `${num(oversub, 0)}x <500x`, tip };
    if (d1c == null || offer == null) return { word: 'WATCH', date: r.listing_date, sub: 'awaiting D1 close', tip };
    if (d1c <= offer) return { word: 'SKIP', sub: 'D1 red', tip: `${tip}. Day-1 close ${num(d1c)} ≤ offer ${num(offer)}.` };
    if (d1c > offer * D1_RULE.chaseHi) return { word: 'SKIP', sub: 'chase >1.5×', tip: `${tip}. Day-1 close ${num(d1c)} > 1.5× offer ${num(offer)}.` };
    // enter at the day-1 close, exit at the bar-5 close (hold 5td). Exit leg is
    // the measured day5_price when available, else a calendar estimate.
    const sellD = r.day5_date || addDays(r.listing_date, D1_RULE.holdTd + 2); // ≈ listing+5td
    let pnl = null, pnlKind = null;
    if (r.day5_price != null && d1c) { pnl = (r.day5_price / d1c - 1) * 100; pnlKind = 'realized'; }
    else if (r.current_price != null && r.listing_date <= TODAY && TODAY <= addDays(sellD, 10)) { pnl = (r.current_price / d1c - 1) * 100; pnlKind = 'open'; }
    return { word: 'BUY', date: r.listing_date,
      tip: `${tip}. All conditions met — buy the ${r.listing_date} close @ ${num(d1c)}, exit the bar-5 close${r.day5_price != null ? ` @ ${num(r.day5_price)}` : ''} (${sellD}). Close-to-close, gross of costs.`,
      trade: { buy: r.listing_date, sell: sellD, sellEst: !r.day5_date, pnl, pnlKind } };
  }

  const isP2 = stratId === 'hk_ipo_postlisting_drift_p2';
  const tip = `${isP2 ? 'Post-Listing Drift P2' : 'Post-Listing Drift V3'} — ${(STRAT_COLS.find(c => c.id === stratId) || {}).rule}`;
  if (isP2 && isGem(r.ticker)) return { word: 'SKIP', sub: 'GEM · main-board only', tip };
  if (oversubPending) return { word: 'WATCH', date: r.entry, sub: oversubPending, tip: `${tip}. Entry decision at the ${r.entry} close.` };
  if (oversub < DRIFT_RULE.bandLo || oversub > DRIFT_RULE.bandHi)
    return { word: 'SKIP', sub: oversub > DRIFT_RULE.bandHi ? `${num(oversub, 0)}x >${DRIFT_RULE.bandHi}x` : `${num(oversub, 0)}x <${DRIFT_RULE.bandLo}x`, tip };
  if (isP2) {
    if (d1c != null && offer != null && d1c < offer)
      return { word: 'SKIP', sub: 'D1 red', tip: `${tip}. Day-1 close ${num(d1c)} < offer ${num(offer)}.` };
    if (d1c == null && r.phase !== 'pre_listing')
      return { word: 'WATCH', date: r.entry, sub: 'awaiting D1 close', tip };
  } else if (r.entryPx != null && r.d1Out) {
    return { word: 'SKIP', sub: `entry/D1 ${r.d1Ratio.toFixed(2)} out`, tip: `${tip}. Entry/D1 ${r.d1Ratio.toFixed(2)} outside ${DRIFT_RULE.d1Lo}–${DRIFT_RULE.d1Hi}.` };
  }
  // Rule fires (or fired): enter at the +20td close, exit at the +40td close.
  // r.pnl / r.pnlKind already carry the mirror round-trip — realized once the
  // exit leg has traded, marked-to-current (◦) inside the hold window.
  const legsTip = `${tip}. Entry ${num(r.entryPx)} @ ${r.entry} · exit ${num(r.exitPx)} @ ${r.exit} — close-to-close, gross of costs (engine nets ~0.3pp).${isP2 ? ' −10% stop can exit before the mirror sell date; max 1 per listing-week.' : ''}`;
  const trade = { buy: r.entry, sell: r.exit, sellEst: r.exitEstimated, pnl: r.pnl, pnlKind: r.pnlKind };
  if (r.phase === 'in_hold')
    return { word: 'BOUGHT', date: r.entry, tip: legsTip, trade };
  if (r.phase === 'passed')
    return { word: 'BOUGHT', date: r.entry, tip: legsTip, trade };
  // ahead / pre_listing with the band already known to pass — the date is the buy
  return { word: 'BUY', date: r.entry,
    sub: !isP2 && r.entryPx == null ? `if entry/D1 ${DRIFT_RULE.d1Lo}–${DRIFT_RULE.d1Hi}×` : (isP2 ? 'stop −10% · +40td exit' : ''),
    tip: `${legsTip} Entry decision at the ${r.entry} close${r.entryEstimated ? ' (calendar estimate)' : ''}.`,
    trade };
};

// Per-strategy cell: the strategy's round-trip in the name. When the engine's
// backtest ledger has a trade it wins; otherwise the rule-mirror legs. Entered
// strategies show B <buy date> → S <sell date> and the P&L % once the exit
// signal has triggered (◦ = still open, marked to current). SKIP = a rule
// condition fails · WATCH = a required input is not published yet.
const StratDecisionCell = ({ r, tr, strat }) => {
  if (tr) {
    const pnl = tr.pnl_pct != null ? tr.pnl_pct : tr.unrealized_pnl_pct;
    const open = tr.exit_date == null;
    const tip = `${strat.name}: engine bought ${tr.entry_date}${open ? ' · position open' : ` · sold ${tr.exit_date}`}${pnl != null ? ` · P&L ${pnl >= 0 ? '+' : ''}${(pnl * 100).toFixed(1)}%${tr.pnl_pct == null ? ' (unrealized)' : ''}` : ''}`;
    return (
      <td className="num" title={tip}>
        <div style={{ fontWeight: 600 }}>B {mmdd(tr.entry_date)} → {open ? 'open' : `S ${mmdd(tr.exit_date)}`}</div>
        <div className={sgnCl(pnl != null ? pnl * 100 : null)} style={{ fontSize: 9 }}>
          {pnl != null ? <>{pnl >= 0 ? '+' : ''}{(pnl * 100).toFixed(1)}%{tr.pnl_pct == null ? ' ◦' : ''}</> : '—'}
        </div>
      </td>
    );
  }
  const d = stratDecision(strat.id, r);
  if (d.trade) {
    const t = d.trade;
    return (
      <td className="num" title={d.tip}>
        <div style={{ fontWeight: 600 }}>B {mmdd(t.buy)} → S {mmdd(t.sell)}{t.sellEst ? ' ≈' : ''}</div>
        <div className={sgnCl(t.pnl)} style={{ fontSize: 9 }}>
          {t.pnl != null
            ? <>{signed(t.pnl)}{t.pnlKind === 'open' ? ' ◦' : ''}</>
            : <span style={{ color: '#565e6c' }}>{d.sub || (r.phase === 'ahead' || r.phase === 'pre_listing' ? 'awaiting entry' : '—')}</span>}
        </div>
      </td>
    );
  }
  const color = d.word === 'SKIP' ? '#565e6c' : '#8b93a3';
  return (
    <td className="num" title={d.tip}>
      <div style={{ fontWeight: 600, color }}>{d.word}{d.date ? ` ${mmdd(d.date)}` : ''}</div>
      {d.sub ? <div style={{ fontSize: 9, color: '#565e6c' }}>{d.sub}</div> : null}
    </td>
  );
};

const WatchTable = ({ rows, stratTrades = {} }) => (
  <table className="ipo-tbl">
    <thead>
      <tr>
        <th className="ipo-stick">Ticker</th><th>Name</th><th className="num">Oversub</th>
        <th className="num" title="Offer price">IPO px</th>
        <th className="num" title="First-day close">D1 close</th>
        <th className="num">Current</th>
        {STRAT_COLS.map(c => (
          <th key={c.id} className="num" title={`${c.name} — ${c.rule}. Cell: the strategy's round-trip — B <buy date> → S <sell date> plus P&L % once the exit has triggered (◦ = open, marked to current; engine ledger trade when one exists, else rule mirror) · SKIP = condition fails · WATCH = input not published yet.`}>{c.tag}</th>
        ))}
        <th>Phase</th>
      </tr>
    </thead>
    <tbody>
      {rows.map(r => (
        <tr key={r.ticker}>
          <td className="ipo-ticker ipo-stick">{r.ticker}
            <div style={{ fontSize: 9, color: '#565e6c', fontWeight: 400 }} title="Listing date — the list is ordered by this, newest first">listed {r.listing_date}</div>
          </td>
          <NameCell zh={r.stock_name_zh} en={r.stock_name} />
          <td className="num">{r.oversubscription_retail != null
            ? <>
                {num(r.oversubscription_retail, 1)}x
                {r.inBand === false && (
                  <div style={{ fontSize: 9, color: '#565e6c' }} title={`The V3 drift strategy only trades the ${DRIFT_RULE.bandLo}–${DRIFT_RULE.bandHi}x retail-oversub band — this row is shown for reference, the rule skips it`}>
                    {r.oversubscription_retail > DRIFT_RULE.bandHi ? `>${DRIFT_RULE.bandHi}x · out of band` : `<${DRIFT_RULE.bandLo}x · out of band`}
                  </div>
                )}
              </>
            : r.phase === 'pre_listing'
              ? <span className="ipo-faint" title="Retail oversubscription is published at allotment (~1 trading day before listing) — the 100–500x band is undecidable until then (qr_etl t_90585bf2)">band at allotment</span>
              : '—'}</td>
          <td className="num">{r.ipoPx != null ? num(r.ipoPx) : '—'}</td>
          <td className="num">{num(r.first_day_close)}</td>
          <td className="num">{num(r.current_price)}</td>
          {STRAT_COLS.map(c => (
            <StratDecisionCell key={c.id} r={r} tr={(stratTrades[c.id] || {})[r.ticker]} strat={c} />
          ))}
          <td>{r.phase === 'in_hold'
            ? <span className="ipo-pill ipo-st-hold">IN HOLD WINDOW</span>
            : r.phase === 'ahead'
              ? <span className="ipo-pill ipo-st-open">ENTRY IN {r.daysToEntry}d</span>
              : r.phase === 'pre_listing'
                ? <div>
                    <span className="ipo-pill ipo-st-listing">{r.daysToListing === 0 ? 'LISTS TODAY' : `LISTS IN ${r.daysToListing}d`}</span>
                    <div style={{ fontSize: 9, color: '#565e6c', marginTop: 3 }}>listing {r.listing_date}</div>
                  </div>
                : <span className="ipo-pill ipo-st-exit">CLOSED {r.exit}</span>}</td>
        </tr>
      ))}
    </tbody>
  </table>
);

// Compact metric cell — same visual language as the Performance subtab's
// RealMetrics block (8px uppercase muted label over a mono value).
const Metric = ({ label, value, color, big }) => (
  <div style={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
    <span style={{ fontSize: 8, textTransform: 'uppercase', letterSpacing: '0.06em', color: 'var(--text-muted)' }}>{label}</span>
    <span style={{ fontFamily: 'var(--font-mono)', fontSize: big ? 15 : 12, fontWeight: 700, color: color || 'var(--text-secondary)' }}>{value}</span>
  </div>
);

const money0 = (v) => v == null ? '—' : `${v >= 0 ? '+' : '−'}$${Math.abs(Number(v)).toLocaleString(undefined, { maximumFractionDigits: 0 })}`;

// HK IPO strategy card — compact, themed like the Strategies > Performance
// subtab cards (jt-surface + jtkit chips/badges/buttons + YearlyBars). The
// heavy tables (open positions, past trades) live on the ACTIVE IPO BOOK
// panel and the Strategy Detail page; the card carries one-line engine /
// ledger summaries instead.
const IpoStrategyCard = ({ s, ev, positions = [], onOpen, onAdjust, onPause }) => {
  const bt = ev?.metrics?.backtest || {};
  const modes = ev?.metrics_by_mode || {};
  const latestSignal = (ev?.recent_signals || []).slice().sort((a, b) => (b.ts || '').localeCompare(a.ts || ''))[0];
  const activeMode = (() => {
    const em = (s.execution_mode || '').toUpperCase();
    if (em === 'LIVE_TRADING' || em === 'LIVE') return 'live';
    if (em === 'UAT' || em === 'PAPER_UAT') return 'uat';
    if (em === 'PAPER_TRADING' || em === 'PAPER') return 'paper';
    return 'sim';
  })();
  const flat = (ev?.in_market_capital ?? 0) === 0 && (modes.paper?.total_trades ?? 0) === 0;
  const tradeEvents = Array.isArray(ev?.recent_trades) ? ev.recent_trades.length : 0;

  // researcher-endpoint units: win_rate / max_drawdown are already percent;
  // returns_oos is a fraction — deterministic conversion, no magnitude sniffing.
  const wr = pctAsIs(s.win_rate, 1);
  const mdd = pctAsIs(s.max_drawdown, 1);
  const ret = fracToPct(s.returns_oos, 1);

  const ladder = [
    { k: 'sim', label: 'SIM · BACKTEST',
      value: modes.sim?.win_rate != null ? `${(modes.sim.win_rate * 100).toFixed(1)}%` : '—',
      sub: `${modes.sim?.total_trades ?? '—'} OOS trades` },
    { k: 'paper', label: 'PAPER',
      value: modes.paper ? money0(modes.paper.total_pnl) : '—',
      color: modes.paper?.total_pnl != null ? pnlColor(modes.paper.total_pnl) : undefined,
      sub: modes.paper ? `${modes.paper.total_trades ?? 0} closed${flat ? ' · flat' : ''}` : 'not reached' },
    { k: 'uat', label: 'UAT',
      value: modes.uat?.total_fills ? String(modes.uat.total_fills) : '—',
      sub: modes.uat?.total_fills ? 'fills booked' : 'not reached' },
    { k: 'live', label: 'LIVE',
      value: modes.live?.total_trades ? money0(modes.live.total_pnl ?? 0) : '—',
      color: modes.live?.total_pnl != null ? pnlColor(modes.live.total_pnl) : undefined,
      sub: modes.live?.total_trades ? `${modes.live.total_trades} trades` : 'not reached' },
  ];

  return (
    <div className="jt-surface" style={{ padding: 12, display: 'flex', flexDirection: 'column', gap: 9 }}>
      {/* header — name + chips, mode badge right (Performance card layout) */}
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 8 }}>
        <div style={{ minWidth: 0, cursor: 'pointer' }} onClick={() => onOpen && onOpen(s.id)} title="Open strategy detail">
          <div style={{ fontSize: 12, fontWeight: 700, color: 'var(--text-strong)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{s.name || s.id}</div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginTop: 4, flexWrap: 'wrap' }}>
            {s.status && <Chip color="slate">{String(s.status).toUpperCase()}</Chip>}
            {s.priority && <Chip color="slate">{s.priority}</Chip>}
            {s.is_paper_monitoring && <Chip color="slate">PAPER · {String(s.paper_state || 'watching').toUpperCase()}</Chip>}
            {flat && <Chip color="slate">BOOK FLAT</Chip>}
          </div>
        </div>
        <ModeBadge mode={s.execution_mode} />
      </div>

      {/* backtest metrics — RealMetrics-style grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, minmax(0,1fr))', gap: '8px 8px', padding: '7px 8px', borderRadius: 'var(--radius-md)', background: 'rgba(255,255,255,0.02)' }}>
        <Metric label="Sharpe" value={s.sharpe_ratio == null ? '—' : Number(s.sharpe_ratio).toFixed(2)} big />
        <Metric label="OOS ret" value={ret == null ? '—' : fmtPct(ret)} color={ret == null ? undefined : pnlColor(ret)} big />
        <Metric label="Win" value={wr == null ? '—' : `${wr.toFixed(0)}%`} color={wr == null ? undefined : wr >= 50 ? 'var(--pnl-pos)' : 'var(--pnl-neg)'} big />
        <Metric label="MDD" value={mdd == null ? '—' : fmtPct(mdd)} color={mdd == null ? undefined : pnlColor(mdd)} />
        <Metric label="Profit factor" value={bt.profit_factor == null ? '—' : Number(bt.profit_factor).toFixed(2)} />
        <Metric label="OOS trades" value={bt.total_trades ?? s.backtest_trades ?? s.trade_count_oos ?? '—'} />
      </div>

      {/* annual backtest bars — the exact Performance subtab component */}
      <div style={{ padding: '7px 8px', borderRadius: 'var(--radius-md)', background: 'rgba(255,255,255,0.02)', display: 'flex', flexDirection: 'column', gap: 6 }}>
        <span style={{ fontSize: 8, textTransform: 'uppercase', letterSpacing: '0.06em', color: 'var(--text-muted)' }}>Annual backtest returns</span>
        <YearlyBars yearly={s.yearly_backtest} normalize />
      </div>

      {/* mode ladder — compact strip */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4,minmax(0,1fr))', gap: 4 }}>
        {ladder.map(c => (
          <div key={c.k} style={{ padding: '5px 7px', borderRadius: 'var(--radius-md)', background: 'rgba(255,255,255,0.02)', boxShadow: activeMode === c.k ? 'inset 0 0 0 1px var(--border-strong)' : 'none' }}>
            <div style={{ fontSize: 8, textTransform: 'uppercase', letterSpacing: '0.06em', color: 'var(--text-muted)', display: 'flex', justifyContent: 'space-between', gap: 4 }}>
              <span>{c.label}</span>{activeMode === c.k && <span style={{ color: 'var(--text-secondary)' }}>ACTIVE</span>}
            </div>
            <div style={{ fontFamily: 'var(--font-mono)', fontSize: 11, fontWeight: 700, color: c.color || 'var(--text-secondary)', marginTop: 2 }}>{c.value}</div>
            <div style={{ fontSize: 8, color: 'var(--text-faint)', marginTop: 1 }}>{c.sub}</div>
          </div>
        ))}
      </div>

      {/* entry mechanics — verbatim from the strategy registry so the entry
          venue (subscription vs grey market vs on-exchange) is never ambiguous;
          text is research-owned, clamped to 3 lines with the full text on hover */}
      {(s.description || s.exit_logic) && (
        <div style={{ padding: '7px 8px', borderRadius: 'var(--radius-md)', background: 'rgba(255,255,255,0.02)', fontSize: 9, color: 'var(--text-muted)', lineHeight: 1.55 }}>
          {s.description && (
            <div title={s.description}
                 style={{ display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical', overflow: 'hidden' }}>
              <span style={{ fontSize: 8, textTransform: 'uppercase', letterSpacing: '0.06em', color: 'var(--text-faint)' }}>How it trades — </span>
              {s.description}
            </div>
          )}
          {s.exit_logic && (
            <div style={{ marginTop: 3 }} title={s.exit_logic}>
              <span style={{ fontSize: 8, textTransform: 'uppercase', letterSpacing: '0.06em', color: 'var(--text-faint)' }}>Exit — </span>
              {s.exit_logic}
            </div>
          )}
        </div>
      )}

      {/* engine-convention flag — only for strategies whose engine bar
          indexing differs from the rule-mirror ticker list's OFFSET legs
          (currently P2: engine 20/40 vs mirror 19/39) */}
      {ENGINE_NOTES[s.id] && (
        <div style={{ padding: '7px 8px', borderRadius: 'var(--radius-md)', background: 'rgba(255,255,255,0.02)', fontSize: 9, color: 'var(--text-muted)', lineHeight: 1.55 }}>
          <span style={{ fontSize: 8, textTransform: 'uppercase', letterSpacing: '0.06em', color: 'var(--text-faint)' }}>Engine convention — </span>
          {ENGINE_NOTES[s.id]}
        </div>
      )}

      {/* engine + ledger one-liners */}
      <div style={{ fontSize: 9, color: 'var(--text-muted)', lineHeight: 1.5 }}>
        Engine: {latestSignal
          ? <>latest signal <span style={{ fontFamily: 'var(--font-mono)', color: 'var(--text-secondary)' }}>{latestSignal.ticker} · {latestSignal.signal}</span> at {(latestSignal.ts || '').replace('T', ' ').slice(0, 16)} UTC{flat ? ' — book flat' : ''}</>
          : ev ? 'no signals returned by the evaluation endpoint' : 'evaluation endpoint unreachable — engine state unknown'}
        {' · '}{s.assigned_capital != null ? `$${Number(s.assigned_capital).toLocaleString()} assigned` : 'capital unassigned'}
      </div>
      <div style={{ fontSize: 9, color: 'var(--text-muted)', lineHeight: 1.5 }}>
        Paper ledger: {positions.length} open · {tradeEvents} trades — tables in ACTIVE IPO BOOK &amp; detail page.
      </div>

      <div style={{ display: 'flex', gap: 6 }}>
        <Button variant="primary" size="sm" style={{ flex: 1 }} onClick={() => onOpen && onOpen(s.id)}>View detail ↗</Button>
        <Button variant="ghost" size="sm" onClick={() => onAdjust(s)}>Adjust allocation</Button>
        <Button variant="ghost" size="sm" onClick={() => onPause(s)}>Pause</Button>
      </div>
    </div>
  );
};

// ---- main tab -----------------------------------------------------------

export function IpoTab({ onOpen }) {
  const [ipos, setIpos] = useState(null);
  const [strategies, setStrategies] = useState([]);
  const [evals, setEvals] = useState({});
  const [sectors, setSectors] = useState([]);
  const [ipoWindow, setIpoWindow] = useState('3m'); // global: sentiment + KPIs
  const [subs, setSubs] = useState(null);
  const [book, setBook] = useState(null);
  const [stage, setStage] = useState(null); // null = auto-pick once data lands
  const [sectorFilter, setSectorFilter] = useState(null); // click a sector row → filters the strategy rule-mirror list
  const [actionMsg, setActionMsg] = useState(null);

  const load = useCallback(async () => {
    const [lst, strat, sub, bk] = await Promise.all([
      // limit must cover BOTH the dated calendar (~1.5k) and the A1-/A1G- announced
      // placeholders (~380, listing_date null, sorted last server-side)
      api.get('/api/hkex/ipos?limit=2000'),
      api.get('/api/strategies/researcher'),
      api.get('/api/hkex/ipos/subscription'),
      api.get('/api/hkex/ipos/book'),
    ]);
    setIpos(Array.isArray(lst?.ipos) ? lst.ipos : []);
    const bookRows = Array.isArray(strat?.strategies) ? strat.strategies : (Array.isArray(strat?.data) ? strat.data : []);
    const ipoStrats = bookRows.filter(s =>
      (s.asset_class || '').toLowerCase().includes('ipo') || (s.id || '').toLowerCase().startsWith('hk_ipo')
    );
    // deterministic card order — day-1 momentum, V3 baseline, P2 variant,
    // unknown HK IPO strategies trailing by id (API row order is not stable)
    ipoStrats.sort((a, b) =>
      (STRATEGY_ORDER[a.id] ?? 99) - (STRATEGY_ORDER[b.id] ?? 99) || (a.id || '').localeCompare(b.id || '')
    );
    setStrategies(ipoStrats);
    setSubs(Array.isArray(sub?.ipos) ? sub.ipos : []);
    setBook(Array.isArray(bk?.positions) ? bk.positions : []);
    // per-strategy evaluation (mode ladder + engine signal + engine trade
    // ledger for the ticker-list strategy columns) — best effort
    const evPairs = await Promise.all(ipoStrats.map(async s => [s.id, await api.get(`/api/strategies/${s.id}/evaluation?trade_limit=1000`)]));
    const evMap = {};
    evPairs.forEach(([id, ev]) => { if (ev && !ev.error) evMap[id] = ev; });
    setEvals(evMap);
  }, []);

  usePoll(load, 120000);

  // sector sentiment is window-driven — refetch only this panel on toggle
  useEffect(() => {
    let dead = false;
    api.get(`/api/hkex/ipos/sectors?window=${ipoWindow}`).then(sec => {
      if (!dead) setSectors(Array.isArray(sec?.sectors) ? sec.sectors : []);
    });
    return () => { dead = true; };
  }, [ipoWindow]);

  const staged = useMemo(() => {
    if (!ipos) return null;
    const g = { announced: [], subscription: [], grey: [], public: [] };
    ipos.forEach(r => g[stageOf(r)].push(r));
    g.announced.sort((a, b) => (a.listing_date || '').localeCompare(b.listing_date || ''));
    g.subscription.sort((a, b) => (a.application_end || '').localeCompare(b.application_end || ''));
    g.grey.sort((a, b) => (a.listing_date || '').localeCompare(b.listing_date || ''));
    g.public.sort((a, b) => (b.listing_date || '').localeCompare(a.listing_date || ''));
    return g;
  }, [ipos]);

  const activeStage = stage || (() => {
    if (!staged) return 'announced';
    for (const k of ['subscription', 'grey', 'announced']) if (staged[k].length) return k;
    return 'announced';
  })();

  // IPO KPIs — recomputed over the global window (client-side listing-date filter)
  const stats = useMemo(() => {
    if (!ipos || !ipos.length) return null;
    const cutoff = windowCutoff(ipoWindow);
    const win = ipos.filter(r => r.listing_date && r.listing_date >= cutoff);
    const fd = win.map(r => r.first_day_return).filter(v => v != null);
    const d30 = win.map(r => r.return_day30).filter(v => v != null);
    return {
      n: win.length,
      window: `${cutoff} → ${TODAY}`,
      fdN: fd.length,
      fdAvg: fd.length ? fd.reduce((a, b) => a + b, 0) / fd.length : null,
      fdMed: median(fd),
      fdWin: fd.length ? (fd.filter(v => v > 0).length / fd.length) * 100 : null,
      d30N: d30.length,
      d30Avg: d30.length ? d30.reduce((a, b) => a + b, 0) / d30.length : null,
    };
  }, [ipos, ipoWindow]);

  const sectorView = useMemo(() => ({
    named: sectors.filter(s => s.sector),
    unclassified: sectors.find(s => !s.sector),
  }), [sectors]);

  const activeWindowLabel = WINDOWS.find(w => w.k === ipoWindow)?.label || ipoWindow;

  // ticker list (rule-mirror windows, or sector drill-down when a sector row is clicked)
  const watch = useMemo(() => computeWatch(ipos, sectorFilter, ipoWindow), [ipos, sectorFilter, ipoWindow]);

  // Per-strategy engine round-trips keyed by ticker, from each strategy's OOS
  // backtest ledger (gold.strategy_backtest_trades via the evaluation
  // endpoint). Feeds the D1 / V3 / P2 columns of the ticker list. If a ticker
  // was traded more than once, the latest round-trip wins.
  const stratTrades = useMemo(() => {
    const map = {};
    for (const c of STRAT_COLS) {
      const byTicker = {};
      for (const t of (evals[c.id]?.backtest_trades || [])) {
        if (!t.ticker) continue;
        const cur = byTicker[t.ticker];
        if (!cur || (t.entry_date || '') > (cur.entry_date || '')) byTicker[t.ticker] = t;
      }
      map[c.id] = byTicker;
    }
    return map;
  }, [evals]);

  const adjustAllocation = async (s) => {
    const cur = s.assigned_capital != null ? Number(s.assigned_capital) : null;
    const input = window.prompt(`New total assigned capital for ${s.id} (current ${cur != null ? '$' + cur.toLocaleString() : 'unassigned'}):`, cur ?? '');
    if (input == null) return;
    const val = Number(input);
    if (!isFinite(val) || val < 0) { setActionMsg('Invalid amount — allocation unchanged'); return; }
    const res = await api.post(`/api/strategies/${s.id}/capital-pool`, { total_assigned: val });
    setActionMsg(res && (res.success !== false) ? `Allocation updated to $${val.toLocaleString()}` : `Allocation update failed: ${res?.error || 'no response'}`);
    load();
  };

  const pauseStrategy = async (s) => {
    if (!window.confirm(`Pause ${s.id}? This closes the paper book and stops monitoring (same as Stop in the Lab).`)) return;
    const res = await api.post(`/api/strategies/${s.id}/deactivate`, { action: 'close' });
    setActionMsg(res && res.success ? 'Strategy paused' : `Pause failed: ${res?.error || res?.message || 'no response'}`);
    load();
  };

  if (ipos === null) {
    return (
      <div className="ipo-panel" style={{ padding: '32px 16px', textAlign: 'center', fontSize: 11, color: '#565e6c' }}>
        <style>{CSS}</style>Loading HK IPO book…
      </div>
    );
  }

  const GreyCell = ({ r }) => {
    const greyPct = r.grey_close != null && (r.offer_price_high ?? r.offer_price)
      ? (r.grey_close / (r.offer_price_high ?? r.offer_price) - 1) * 100 : null;
    return (
      <td className={`num ${sgnCl(greyPct)}`}>
        {r.grey_close != null
          ? <>{num(r.grey_close)}{greyPct != null && <span style={{ marginLeft: 6 }}>{signed(greyPct, 0)}</span>}</>
          : <span className="ipo-faint" title="Grey-market session is the trading day before listing — not held yet">—</span>}
      </td>
    );
  };

  const body = (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
      <style>{CSS}</style>

      {actionMsg && (
        <div className="ipo-panel" style={{ padding: '8px 16px', fontSize: 11, color: '#8b93a3' }}>
          {actionMsg} <button className="ipo-btn" style={{ marginLeft: 8, padding: '2px 8px' }} onClick={() => setActionMsg(null)}>×</button>
        </div>
      )}

      {/* global window toggle — drives IPO SENTIMENT (server-side) and the IPO KPIs strip (client-side) */}
      <div className="ipo-panel" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '10px 16px', gap: 12, flexWrap: 'wrap' }}>
        <div style={{ fontSize: 10, color: '#565e6c', letterSpacing: '.4px', fontWeight: 600 }}>WINDOW — APPLIES TO ALL PANELS</div>
        <span style={{ display: 'flex', gap: 6 }}>
          {WINDOWS.map(w => (
            <button key={w.k} className={`ipo-yr ${ipoWindow === w.k ? 'active' : ''}`} onClick={() => setIpoWindow(w.k)}>
              {w.label}
            </button>
          ))}
        </span>
      </div>

      {/* stats strip — IPO KPIs, filtered by the global window */}
      {stats && (
        <div className="ipo-kpi-grid">
          <Stat label={`IPOS · ${activeWindowLabel}`} value={stats.n} sub={stats.window} />
          <Stat label="AVG FIRST-DAY" value={stats.fdAvg == null ? '—' : fmtPct(stats.fdAvg)} sub={`measured on ${stats.fdN} of ${stats.n}`} green={stats.fdAvg > 0} />
          <Stat label="MEDIAN FIRST-DAY" value={stats.fdMed == null ? '—' : fmtPct(stats.fdMed)} sub="median, measured rows" green={stats.fdMed > 0} />
          <Stat label="FIRST-DAY WIN RATE" value={stats.fdWin == null ? '—' : `${stats.fdWin.toFixed(0)}%`} sub={`${stats.fdN} priced`} />
          <Stat label="AVG DAY-30" value={stats.d30Avg == null ? '—' : fmtPct(stats.d30Avg)} sub={`measured on ${stats.d30N} of ${stats.n}`} green={stats.d30Avg > 0} />
          <Stat label="IN PIPELINE" value={staged ? staged.announced.length + staged.subscription.length + staged.grey.length : '—'}
                sub={staged ? `${staged.announced.length} announced · ${staged.subscription.length} subscribing · ${staged.grey.length} grey` : ''} />
        </div>
      )}

      {/* side-by-side analysis: sentiment sectors (left) + ticker list (right) */}
      <div className="ipo-split">
      {/* IPO sentiment — sector breakdown */}
      <Panel
        title="IPO SENTIMENT · SECTOR BREAKDOWN"
        tag={<Tag kind="live">LIVE</Tag>}
        right={`window: ${activeWindowLabel}`}
        scroll
        note={<span>Average returns vs offer price (D1 / D20 / D40 / latest). Click a sector to list its IPOs on the right.</span>}
      >
        {sectorView.named.length === 0 ? (
          <div style={{ fontSize: 11, color: '#565e6c', padding: '14px 16px' }}>No classified sectors returned for this window.</div>
        ) : (
          <table className="ipo-tbl">
            <thead>
              <tr>
                <th>Sector</th><th className="num">IPOs</th>
                <th className="num" title="Average first-day return vs offer price">D1 %</th>
                <th className="num" title="Average 20th-trading-day return vs offer price">D20 %</th>
                <th className="num" title="Average 40th-trading-day return vs offer price (post-listing drift exit leg)">D40 %</th>
                <th className="num" title="Average current return vs offer price">Now %</th>
                <th className="num" title="Share of IPOs with first-day return > 0">Win D1</th>
              </tr>
            </thead>
            <tbody>
              {sectorView.named.map(s => (
                <tr key={s.sector}
                    onClick={() => setSectorFilter(f => f === s.sector ? null : s.sector)}
                    title={sectorFilter === s.sector ? 'Clear sector filter' : "Show this sector's IPOs in the ticker list"}
                    style={{ cursor: 'pointer', background: sectorFilter === s.sector ? '#12161f' : undefined }}>
                  <td style={{ color: sectorFilter === s.sector ? '#e6e8eb' : '#8b93a3' }}>
                    <span style={{ marginRight: 6, color: '#565e6c' }}>{sectorFilter === s.sector ? '▾' : '▸'}</span>{s.sector}
                  </td>
                  <td className="num">{s.ipo_count}</td>
                  <td className={`num ${sgnCl(s.avg_first_day_return)}`}>{s.avg_first_day_return == null ? '—' : fmtPct(s.avg_first_day_return)}</td>
                  <td className={`num ${sgnCl(s.avg_day20_return)}`} title={`measured on ${s.day20_n ?? '?'} of ${s.ipo_count}`}>
                    {s.avg_day20_return == null ? '—' : fmtPct(s.avg_day20_return)}
                  </td>
                  <td className={`num ${sgnCl(s.avg_day40_return)}`} title={`measured on ${s.day40_n ?? '?'} of ${s.ipo_count}`}>
                    {s.avg_day40_return == null ? '—' : fmtPct(s.avg_day40_return)}
                  </td>
                  <td className={`num ${sgnCl(s.avg_current_return)}`} title={`measured on ${s.current_n ?? '?'} of ${s.ipo_count}`}>
                    {s.avg_current_return == null ? '—' : fmtPct(s.avg_current_return)}
                  </td>
                  <td className="num" style={{ color: '#8b93a3' }}>{s.win_rate == null ? '—' : `${s.win_rate.toFixed(0)}%`}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
        {sectorView.unclassified && (
          <div style={{ fontSize: 9, color: '#565e6c', padding: '8px 16px 12px', lineHeight: 1.5 }}>
            {sectorView.unclassified.ipo_count} IPO{sectorView.unclassified.ipo_count === 1 ? '' : 's'} in this window carry no sector classification upstream
            {sectorView.unclassified.avg_first_day_return != null && <> (avg D1 {fmtPct(sectorView.unclassified.avg_first_day_return)}, win {sectorView.unclassified.win_rate?.toFixed(0)}%)</>} — excluded above, not treated as a sector.
          </div>
        )}
      </Panel>

      {/* ticker list — rule-mirror windows; sector drill-down when a sector row is clicked */}
      <Panel
        title={sectorFilter ? `IPO TICKER LIST · ${sectorFilter}` : 'IPO TICKER LIST · RULE-MIRROR WINDOWS'}
        tag={<Tag kind="live">LIVE</Tag>}
        right={sectorFilter ? (
          <span className="ipo-pill" style={{ background: '#12161f', color: '#8b93a3', cursor: 'pointer' }} onClick={() => setSectorFilter(null)} title="Clear sector filter">
            sector filter ×
          </span>
        ) : (watch ? `${watch.all.length} names` : '')}
        note={sectorFilter
          ? `All ${sectorFilter} IPOs listed in the ${activeWindowLabel} window — band not applied here. ◦ = open, marked to current.`
          : `Rule mirror: oversub ${DRIFT_RULE.bandLo}–${DRIFT_RULE.bandHi}x · entry/D1 ${DRIFT_RULE.d1Lo}–${DRIFT_RULE.d1Hi}x · enter +${DRIFT_RULE.entryTd}td · hold ${DRIFT_RULE.holdTd}td — not the engine signal; P&L gross of costs (engine nets ~0.3pp). All ${activeWindowLabel} IPOs shown; band flagged per row. ◦ = open, marked to current. D1/V3/P2 columns: per-strategy buy decision + when (engine round-trip when the ledger has one; hover a cell for the full rule).`}
      >
        {watch && watch.all.length > 0 ? (
          <div style={{ marginBottom: 6 }}>
            {watch.bandCount != null && (
              <div style={{ display: 'flex', gap: 18, fontSize: 10, color: '#8b93a3', fontFamily: 'ui-monospace,monospace', margin: '8px 16px 0', flexWrap: 'wrap' }}>
                <span title={`${watch.bandCount} of ${watch.rowCount} listed names pass the V3 rule filters (${DRIFT_RULE.bandLo}–${DRIFT_RULE.bandHi}x retail oversub · entry/D1 ${DRIFT_RULE.d1Lo}–${DRIFT_RULE.d1Hi}x)`}>
                  {watch.bandCount} of {watch.rowCount} listed in band ({DRIFT_RULE.bandLo}–{DRIFT_RULE.bandHi}x · entry/D1 {DRIFT_RULE.d1Lo}–{DRIFT_RULE.d1Hi})
                </span>
              </div>
            )}
            {watch.stats && (
              <div style={{ display: 'flex', gap: 18, fontSize: 10, color: '#8b93a3', fontFamily: 'ui-monospace,monospace', margin: '8px 16px', flexWrap: 'wrap' }}>
                <span title="Closed rule-mirror round-trips, in-band cohort only">{watch.stats.n} in-band closed round-trips</span>
                <span>win {watch.stats.wins}/{watch.stats.n} ({watch.stats.winRate.toFixed(0)}%)</span>
                <span>avg <span className={sgnCl(watch.stats.avg)}>{signed(watch.stats.avg)}</span></span>
                <span>sum <span className={sgnCl(watch.stats.sum)}>{signed(watch.stats.sum)}</span></span>
                {watch.counts.inHold > 0 && <span>{watch.counts.inHold} open (marked to current)</span>}
                {watch.counts.ahead > 0 && <span>{watch.counts.ahead} awaiting entry</span>}
                {watch.counts.preListing > 0 && <span>{watch.counts.preListing} not yet listed</span>}
              </div>
            )}
            <div style={{ maxHeight: 560, overflow: 'auto' }}>
              <WatchTable rows={watch.all} stratTrades={stratTrades} />
            </div>
          </div>
        ) : (
          <div style={{ fontSize: 11, color: '#565e6c', padding: '14px 16px' }}>
            {watch
              ? (sectorFilter ? `No ${sectorFilter} IPOs listed in the selected window.` : 'No listed IPOs in the selected window.')
              : 'Loading watchlist…'}
          </div>
        )}
      </Panel>
      </div>

      {/* stage pipeline */}
      <Panel
        title="IPO PIPELINE — BY STAGE"
        tag={<Tag kind="live">LIVE</Tag>}
        right={`${TODAY} UTC`}
        scroll
        note={<span>Stages classified from application window vs listing date. ANNOUNCED = A1/PHIP filings (<code>qr_etl t_59228b1e</code>); open-window oversub pending (<code>qr_etl t_90585bf2</code>).</span>}
      >
        <div className="ipo-stages">
          {STAGES.map((st, i) => {
            const rows = staged ? staged[st.key] : [];
            const tickers = rows.slice(0, 3).map(r => r.ticker).join(' · ');
            return (
              <button key={st.key} className={`ipo-stage ${activeStage === st.key ? 'active' : ''}`} onClick={() => setStage(st.key)}>
                <div className="step">{st.step}{i < 2 ? ' →' : ''}</div>
                <div className="n">{rows.length}</div>
                <div style={{ fontSize: 11, color: '#8b93a3', fontWeight: 600 }}>{st.label}</div>
                <div className="sub">{st.hint}{tickers ? <><br />{tickers}{rows.length > 3 ? ` +${rows.length - 3}` : ''}</> : ''}</div>
              </button>
            );
          })}
        </div>

        {/* STAGE 1 — announced */}
        {activeStage === 'announced' && (
          staged.announced.length > 0 ? (
            <table className="ipo-tbl">
              <thead>
                <tr>
                  <th>Ticker</th><th>Name</th><th>Sector</th>
                  <th className="num">Listing</th><th>Subscription opens</th>
                  <th className="num">Price range</th><th className="num">Lot size</th><th className="num">Min. investment</th>
                </tr>
              </thead>
              <tbody>
                {staged.announced.map(r => (
                  <tr key={r.ticker}>
                    <td className="ipo-ticker">{r.ticker}</td>
                    <NameCell zh={r.stock_name_zh} en={r.stock_name} />
                    <td className="ipo-co">{r.sector || '—'}</td>
                    <td className="num">{r.listing_date || 'TBC'}</td>
                    <td>{r.application_start ? `${r.application_start} → ${r.application_end || '?'}` : <span className="ipo-pill ipo-st-book">WINDOW TBC</span>}</td>
                    <OfferRangeCell r={r} />
                    <td className="num">{r.lot_size ? `${r.lot_size} sh` : '—'}</td>
                    <td className="num">{minInvestment(r) != null ? minInvestment(r).toLocaleString() : '—'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <div style={{ padding: 16, fontSize: 11, color: '#565e6c' }}>
              No announced IPOs — A1/PHIP filings feed (qr_etl t_59228b1e) returned none active.
            </div>
          )
        )}

        {/* STAGE 2 — under subscription */}
        {activeStage === 'subscription' && (
          staged.subscription.length > 0 ? (
            <table className="ipo-tbl">
              <thead>
                <tr>
                  <th>Ticker</th><th>Name</th><th>Sector</th>
                  <th className="num">Price range</th><th className="num">Lot size</th><th className="num">Min. investment</th>
                  <th>Subscription window</th><th className="num">Closes</th><th className="num">Oversub (retail)</th>
                  <th className="num">Listing</th><th>Action</th>
                </tr>
              </thead>
              <tbody>
                {staged.subscription.map(r => {
                  const closesIn = daysSince(r.application_end) != null ? -daysSince(r.application_end) : null;
                  const closed = closesIn != null && closesIn < 0;
                  const urgent = !closed && closesIn != null && closesIn <= 1;
                  return (
                    <tr key={r.ticker}>
                      <td className="ipo-ticker">{r.ticker}</td>
                      <NameCell zh={r.stock_name_zh} en={r.stock_name} />
                      <td className="ipo-co">{r.sector || '—'}</td>
                      <OfferRangeCell r={r} />
                      <td className="num">{r.lot_size ? `${r.lot_size} sh` : '—'}</td>
                      <td className="num">{minInvestment(r) != null ? minInvestment(r).toLocaleString() : <span className="ipo-faint" title="Needs the offer range — not published upstream yet">—</span>}</td>
                      <td>{r.application_end
                        ? <div>
                            <span className={`ipo-pill ${closed ? 'ipo-st-book' : urgent ? 'ipo-st-urgent' : 'ipo-st-open'}`}>{closed ? 'CLOSED' : urgent ? 'CLOSES SOON' : 'OPEN'}</span>
                            <div className="ipo-name-en" style={{ marginTop: 4 }}>{r.application_start || '?'} → {r.application_end}</div>
                          </div>
                        : <span className="ipo-pill ipo-st-book">WINDOW TBC</span>}</td>
                      <td className="num">{r.application_end || '—'}</td>
                      <td className="num">{r.oversubscription_retail != null ? `${num(r.oversubscription_retail, 1)}x` : <span className="ipo-faint" title="Retail oversubscription not published upstream yet — qr_etl t_90585bf2">—</span>}</td>
                      <td className="num">{r.listing_date || '—'}</td>
                      <td><button className="ipo-btn ipo-btn-primary" disabled title="IPO subscription is not wired to a broker route">Apply ↗</button></td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          ) : (
            <div style={{ padding: 16, fontSize: 11, color: '#565e6c' }}>
              No IPOs currently in an open subscription window.
            </div>
          )
        )}

        {/* STAGE 3 — grey market */}
        {activeStage === 'grey' && (
          staged.grey.length > 0 ? (
            <table className="ipo-tbl">
              <thead>
                <tr>
                  <th>Ticker</th><th>Name</th><th>Sector</th>
                  <th className="num">Listing</th><th className="num">In</th>
                  <th className="num">Offer px</th><th className="num">Oversub (retail)</th>
                  <th className="num">Grey session</th><th className="num">Grey close (vs offer)</th>
                </tr>
              </thead>
              <tbody>
                {staged.grey.map(r => {
                  const toList = r.listing_date ? -daysSince(r.listing_date) : null;
                  return (
                    <tr key={r.ticker}>
                      <td className="ipo-ticker">{r.ticker}</td>
                      <NameCell zh={r.stock_name_zh} en={r.stock_name} />
                      <td className="ipo-co">{r.sector || '—'}</td>
                      <td className="num">{r.listing_date || 'TBC'}</td>
                      <td className="num">{toList != null ? (toList === 0 ? 'today' : `${toList}d`) : '—'}</td>
                      <OfferRangeCell r={r} />
                      <td className="num">{r.oversubscription_retail != null ? `${num(r.oversubscription_retail, 1)}x` : <span className="ipo-faint" title="Retail oversubscription not published upstream yet — qr_etl t_90585bf2">—</span>}</td>
                      <td className="num">{r.grey_session_date || <span className="ipo-faint" title="Grey-market session is the trading day before listing — not held yet">—</span>}</td>
                      <GreyCell r={r} />
                    </tr>
                  );
                })}
              </tbody>
            </table>
          ) : (
            <div style={{ padding: 16, fontSize: 11, color: '#565e6c' }}>
              No IPOs between subscription close and listing right now.
            </div>
          )
        )}
      </Panel>

      {/* strategy book — compact cards in a grid, Performance-subtab theme */}
      <Panel title="HK IPO STRATEGIES" tag={<Tag kind="live">LIVE</Tag>}>
        <div className="ipo-card-grid">
          {strategies.length === 0 ? (
            <div style={{ fontSize: 11, color: '#565e6c' }}>No HK IPO strategies registered in the strategy book.</div>
          ) : strategies.map(s => (
            <IpoStrategyCard
              key={s.id}
              s={s}
              ev={evals[s.id]}
              positions={(book || []).filter(r => r.strategy_id === s.id)}
              onOpen={onOpen}
              onAdjust={adjustAllocation}
              onPause={pauseStrategy}
            />
          ))}
        </div>
      </Panel>

      {/* active IPO book — positions, metrics only */}
      <Panel
        title="ACTIVE IPO BOOK"
        tag={<Tag kind="live">LIVE</Tag>}
        right={book ? `${book.length} tracked` : ''}
        scroll
      >
        {book && book.length > 0 ? (
          <table className="ipo-tbl">
            <thead>
              <tr>
                <th>Ticker</th><th>Name</th><th>Status</th>
                <th className="num" title="Shares held">Qty</th>
                <th className="num" title="Entry (buy) price">Buy px</th>
                <th className="num" title="IPO offer price">IPO px</th>
                <th className="num">Current</th>
                <th className="num" title="Current vs buy price">vs Buy</th>
                <th className="num" title="Current vs IPO offer price">vs IPO</th>
                <th className="num" title="Market value">Mkt value</th>
                <th className="num" title="Unrealized P&amp;L">P&amp;L</th>
              </tr>
            </thead>
            <tbody>
              {book.map(r => {
                const held = daysSince(r.entry_date);
                const d = daysSince(r.listing_date);
                const vsBuy = r.current_price != null && r.entry_price ? (r.current_price / r.entry_price - 1) * 100 : null;
                const vsIpo = r.current_price != null && r.offer_price ? (r.current_price / r.offer_price - 1) * 100 : null;
                const pill = d === 0
                  ? <span className="ipo-pill ipo-st-listing">LISTING TODAY</span>
                  : d != null && d >= 28
                    ? <span className="ipo-pill ipo-st-exit">HOLD COMPLETE · D+{d}</span>
                    : <span className="ipo-pill ipo-st-hold">HOLDING{held != null ? ` · ${held}d held` : ''}</span>;
                return (
                  <tr key={`${r.strategy_id}-${r.ticker}`}>
                    <td className="ipo-ticker">{r.ticker}</td>
                    <NameCell zh={r.stock_name_zh} en={r.stock_name} />
                    <td>{pill}</td>
                    <td className="num">{r.quantity != null ? Number(r.quantity).toLocaleString() : '—'}</td>
                    <td className="num" title={r.entry_date ? `bought ${r.entry_date}` : undefined}>{num(r.entry_price)}</td>
                    <td className="num">{num(r.offer_price)}</td>
                    <td className="num" title={r.last_price_date ? `as of ${r.last_price_date}` : undefined}>{num(r.current_price)}</td>
                    <td className={`num ${sgnCl(vsBuy)}`}>{vsBuy != null ? signed(vsBuy) : '—'}</td>
                    <td className={`num ${sgnCl(vsIpo)}`}>{vsIpo != null ? signed(vsIpo) : '—'}</td>
                    <td className="num">{r.market_value != null ? `$${Number(r.market_value).toLocaleString()}` : '—'}</td>
                    <td className={`num ${sgnCl(r.unrealized_pnl)}`}>{r.unrealized_pnl != null ? `${r.unrealized_pnl >= 0 ? '+' : '-'}$${Math.abs(Number(r.unrealized_pnl)).toLocaleString()}` : '—'}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        ) : (
          <div style={{ padding: 16, fontSize: 11, color: '#565e6c' }}>
            No open IPO positions — the drift book is event-driven and currently flat.
          </div>
        )}
      </Panel>
    </div>
  );

  return body;
}

export default IpoTab;
