import React, { useState, useMemo, useCallback, useEffect } from 'react';
import { fmtPct, api, usePoll } from '../utils';

// =================================================================
// IPO subtab (Strategies > IPO) — HK IPO only, redesign 2026-09-02
// Stage-pipeline reorg 2026-09-03 (3 stages since 2026-09-04 — PUBLIC removed:
//   once listed, names live in the normal ticker pool; a flat list of every
//   listed IPO added no value here):
//     1 ANNOUNCED (pre-subscription) — "start looking"
//     2 UNDER SUBSCRIPTION — "monitor whether to apply"
//     3 GREY MARKET — subscription closed, listing imminent; grey trend
//   One global window toggle (1M/3M/6M/YTD/2Y) drives both the IPO sentiment
//   sector table (server-side window) and the IPO KPI stats strip
//   (client-side listing-date filter).
//   HK IPO STRATEGIES cards are actionable: backtest metrics + annual
//   returns + SIM/PAPER/UAT/LIVE mode ladder + engine state + an
//   entry-window watchlist (mechanical mirror of the documented rule,
//   labelled as such — never presented as the engine signal).
//
// Data sources:
//   GET /api/hkex/ipos?limit=400      enriched list: calendar + details + performance
//                                     + price range/lot/grey (silver) + day-20 (lateral
//                                     silver.unified_prices until gold.return_day20_pct
//                                     is backfilled — qr_etl t_e71cffde)
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
.ipo-btn-danger{border-color:#4a2323;color:#f87171;}
.ipo-yr{font-size:11px;padding:4px 10px;border-radius:5px;border:1px solid #1d2430;color:#565e6c;cursor:pointer;background:transparent;}
.ipo-yr.active{background:#12161f;color:#e6e8eb;border-color:#565e6c;}
.ipo-note{font-size:11px;color:#565e6c;line-height:1.6;padding:12px 16px;border-top:1px solid #161b25;}
.ipo-note code{font-family:ui-monospace,monospace;color:#8b93a3;background:#12161f;padding:1px 5px;border-radius:3px;}
.ipo-sector-row{display:flex;justify-content:space-between;padding:7px 0;border-bottom:1px solid #161b25;font-size:11px;}
.ipo-sector-row:last-child{border-bottom:none;}
.ipo-stages{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;padding:14px 16px;}
.ipo-stage{border:1px solid #161b25;border-radius:8px;padding:10px 12px;cursor:pointer;background:#0d1118;text-align:left;}
.ipo-stage:hover{border-color:#2a3242;}
.ipo-stage.active{border-color:#565e6c;background:#12161f;}
.ipo-stage .step{font-size:9px;color:#565e6c;letter-spacing:.5px;font-weight:700;}
.ipo-stage .n{font-size:20px;font-weight:600;font-family:ui-monospace,monospace;color:#e6e8eb;margin:2px 0;}
.ipo-stage .sub{font-size:10px;color:#565e6c;line-height:1.5;}
.ipo-ladder{display:grid;grid-template-columns:repeat(4,1fr);gap:10px;}
.ipo-mode{border:1px solid #161b25;border-radius:8px;padding:10px 12px;background:#0d1118;}
.ipo-mode.active{border-color:#565e6c;background:#12161f;}
.ipo-mode .ml{font-size:9px;color:#565e6c;letter-spacing:.5px;font-weight:700;display:flex;justify-content:space-between;}
.ipo-mode .mv{font-size:15px;font-weight:600;font-family:ui-monospace,monospace;color:#e6e8eb;margin-top:4px;}
.ipo-mode .ms{font-size:10px;color:#565e6c;margin-top:2px;}
.ipo-yrchips{display:flex;gap:8px;flex-wrap:wrap;}
.ipo-yrchip{border:1px solid #161b25;border-radius:6px;padding:6px 10px;background:#0d1118;min-width:86px;}
.ipo-yrchip .y{font-size:9px;color:#565e6c;letter-spacing:.4px;}
.ipo-yrchip .r{font-size:13px;font-weight:600;font-family:ui-monospace,monospace;margin-top:2px;}
`;

const num = (v, d = 2) => v == null || isNaN(v) ? '—' : Number(v).toLocaleString(undefined, { minimumFractionDigits: d, maximumFractionDigits: d });
const signed = (v, d = 1) => v == null ? '—' : `${v >= 0 ? '+' : ''}${Number(v).toFixed(d)}%`;
const sgnCl = (v) => v == null ? 'ipo-faint' : v >= 0 ? 'ipo-green' : 'ipo-red';
const pctOrRatio = (v, d = 1) => {
  if (v == null || isNaN(v)) return null;
  const n = Number(v);
  return Math.abs(n) > 1 ? +n.toFixed(d) : +(n * 100).toFixed(d);
};
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

const DRIFT_RULE = { bandLo: 100, bandHi: 500, entryTd: 20, holdTd: 20 };

const watchRow = (r) => {
  // entry = 20th trading day after listing, exit = 40th (enter +20td, hold 20td).
  // API serves measured day20/day40 closes; dates fall back to ≈ calendar estimates.
  const entry = r.day20_date || (r.listing_date ? addDays(r.listing_date, 28) : null); // ≈20td
  if (!entry) return null;
  const exit = r.day40_date || addDays(entry, 28); // ≈ +20td hold
  const estimated = !r.day20_date;
  const exitEstimated = !r.day40_date;
  const chg = r.current_price != null && r.offer_price ? (r.current_price / r.offer_price - 1) * 100 : null;
  let phase, daysToEntry = null;
  if (TODAY < entry) { phase = 'ahead'; daysToEntry = -daysSince(entry); }
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
  return { ...r, entry, exit, entryEstimated: estimated, exitEstimated, phase, daysToEntry, chg, ipoPx, entryPx, exitPx, pnl, pnlKind };
};

const IpoStrategyCard = ({ s, ev, ipos, onOpen, onAdjust, onPause }) => {
  const bt = ev?.metrics?.backtest || {};
  const modes = ev?.metrics_by_mode || {};
  const latestSignal = (ev?.recent_signals || []).slice().sort((a, b) => (b.ts || '').localeCompare(a.ts || ''))[0];
  const activeMode = (() => {
    const em = (s.execution_mode || '').toUpperCase();
    if (em === 'LIVE_TRADING' || em === 'LIVE') return 'live';
    if (em === 'PAPER_TRADING' || em === 'PAPER') return 'paper';
    return 'sim';
  })();
  const flat = (ev?.in_market_capital ?? 0) === 0 && (modes.paper?.total_trades ?? 0) === 0;

  const watch = useMemo(() => {
    if (!ipos) return null;
    const rows = ipos
      .filter(r => r.listing_date && r.listing_date <= TODAY)
      .filter(r => r.oversubscription_retail != null && r.oversubscription_retail >= DRIFT_RULE.bandLo && r.oversubscription_retail <= DRIFT_RULE.bandHi)
      .map(watchRow)
      .filter(Boolean)
      .filter(r => r.entry >= addDays(TODAY, -120)); // only recent windows
    const inHold = rows.filter(r => r.phase === 'in_hold').sort((a, b) => a.exit.localeCompare(b.exit));
    const ahead = rows.filter(r => r.phase === 'ahead').sort((a, b) => a.entry.localeCompare(b.entry));
    const passed = rows.filter(r => r.phase === 'passed').sort((a, b) => b.exit.localeCompare(a.exit));
    const closed = passed.filter(r => r.pnl != null);
    const wins = closed.filter(r => r.pnl > 0).length;
    const sum = closed.reduce((a, r) => a + r.pnl, 0);
    return {
      all: [...inHold, ...ahead, ...passed],
      counts: { inHold: inHold.length, ahead: ahead.length, passed: passed.length },
      stats: closed.length ? {
        n: closed.length, wins,
        winRate: wins / closed.length * 100,
        avg: sum / closed.length, sum,
      } : null,
    };
  }, [ipos]);

  const wr = pctOrRatio(s.win_rate);
  const mdd = pctOrRatio(s.max_drawdown);
  const ret = pctOrRatio(s.returns_oos);
  const years = Object.entries(s.yearly_backtest || {}).sort(([a], [b]) => a.localeCompare(b));

  const ModeTile = ({ k, label, active, children }) => (
    <div className={`ipo-mode ${active ? 'active' : ''}`}>
      <div className="ml"><span>{label}</span>{active && <span style={{ color: '#8b93a3' }}>ACTIVE</span>}</div>
      {children}
    </div>
  );

  const PxDate = ({ px, date, estimated, faint }) => (
    <td className="num" title={estimated ? 'Estimated: trading-day close not measured yet — calendar approximation' : 'Measured trading-day close (silver.unified_prices)'}>
      <div className={faint ? 'ipo-faint' : ''}>{px != null ? num(px) : '—'}</div>
      <div style={{ fontSize: 9, color: '#565e6c' }}>{date}{estimated ? ' ≈' : ''}</div>
    </td>
  );

  const WatchTable = ({ rows }) => (
    <table className="ipo-tbl">
      <thead>
        <tr>
          <th>Ticker</th><th>Name</th><th className="num">Oversub</th>
          <th className="num" title="Offer price">IPO px</th>
          <th className="num" title="First-day close">D1 close</th>
          <th className="num" title="Entry leg: 20th trading-day close">Entry +20td</th>
          <th className="num" title="Exit leg: 40th trading-day close (entry + 20td hold)">Exit +40td</th>
          <th className="num">Current</th>
          <th className="num" title="Rule-mirror round trip: exit vs entry (open trades marked to current)">Trade P&amp;L</th>
          <th>Phase</th>
        </tr>
      </thead>
      <tbody>
        {rows.map(r => (
          <tr key={r.ticker}>
            <td className="ipo-ticker">{r.ticker}</td>
            <NameCell zh={r.stock_name_zh} en={r.stock_name} />
            <td className="num">{num(r.oversubscription_retail, 1)}x</td>
            <td className="num">{r.ipoPx != null ? num(r.ipoPx) : '—'}</td>
            <td className="num">{num(r.first_day_close)}</td>
            <PxDate px={r.entryPx} date={r.entry} estimated={r.entryEstimated} faint={r.phase === 'ahead'} />
            <PxDate px={r.exitPx} date={r.exit} estimated={r.exitEstimated} faint={r.phase !== 'passed'} />
            <td className="num">{num(r.current_price)}</td>
            <td className={`num ${sgnCl(r.pnl)}`} title={r.pnlKind === 'open' ? 'Open — marked to current price, exit day not reached yet' : r.pnlKind === 'realized' ? 'Realized — exit at 40th trading-day close' : 'Not entered'}>
              {r.pnl != null ? <>{signed(r.pnl)}{r.pnlKind === 'open' ? ' ◦' : ''}</> : '—'}
            </td>
            <td>{r.phase === 'in_hold'
              ? <span className="ipo-pill ipo-st-hold">IN HOLD WINDOW</span>
              : r.phase === 'ahead'
                ? <span className="ipo-pill ipo-st-open">ENTRY IN {r.daysToEntry}d</span>
                : <span className="ipo-pill ipo-st-exit">CLOSED {r.exit}</span>}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );

  return (
    <div style={{ border: '1px solid #161b25', borderRadius: 8, padding: 16, background: '#0d1118' }}>
      <div style={{ fontSize: 14, fontWeight: 600, marginBottom: 8 }}>{s.name || s.id}</div>
      <div style={{ display: 'flex', gap: 6, marginBottom: 14, flexWrap: 'wrap' }}>
        {s.status && <Tag kind="paper">{String(s.status).toUpperCase()}</Tag>}
        {s.priority && <Tag kind="exp">{s.priority}</Tag>}
        {s.is_paper_monitoring && <Tag kind="watch">PAPER · {String(s.paper_state || 'watching').toUpperCase()}</Tag>}
        {flat && <Tag kind="pending">BOOK FLAT</Tag>}
      </div>

      {/* backtest block */}
      <div style={{ fontSize: 10, color: '#565e6c', letterSpacing: '.4px', marginBottom: 8 }}>BACKTEST · OOS 2024-01 → 2026-08 (per registry)</div>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(6,1fr)', gap: 18, marginBottom: 12 }}>
        <div><div style={{ fontSize: 10, color: '#565e6c', marginBottom: 4 }}>SHARPE</div>
          <div style={{ fontSize: 16, fontWeight: 600, fontFamily: 'ui-monospace,monospace' }}>{s.sharpe_ratio == null ? '—' : Number(s.sharpe_ratio).toFixed(2)}</div></div>
        <div><div style={{ fontSize: 10, color: '#565e6c', marginBottom: 4 }}>OOS RET</div>
          <div className={ret == null ? '' : sgnCl(ret)} style={{ fontSize: 16, fontWeight: 600, fontFamily: 'ui-monospace,monospace' }}>{ret == null ? '—' : fmtPct(ret)}</div></div>
        <div><div style={{ fontSize: 10, color: '#565e6c', marginBottom: 4 }}>WIN</div>
          <div style={{ fontSize: 16, fontWeight: 600, fontFamily: 'ui-monospace,monospace' }}>{wr == null ? '—' : `${wr.toFixed(0)}%`}</div></div>
        <div><div style={{ fontSize: 10, color: '#565e6c', marginBottom: 4 }}>MDD</div>
          <div className={mdd == null ? '' : sgnCl(mdd)} style={{ fontSize: 16, fontWeight: 600, fontFamily: 'ui-monospace,monospace' }}>{mdd == null ? '—' : fmtPct(mdd)}</div></div>
        <div><div style={{ fontSize: 10, color: '#565e6c', marginBottom: 4 }}>PROFIT FACTOR</div>
          <div style={{ fontSize: 16, fontWeight: 600, fontFamily: 'ui-monospace,monospace' }}>{bt.profit_factor == null ? '—' : Number(bt.profit_factor).toFixed(2)}</div></div>
        <div><div style={{ fontSize: 10, color: '#565e6c', marginBottom: 4 }}>OOS TRADES</div>
          <div style={{ fontSize: 16, fontWeight: 600, fontFamily: 'ui-monospace,monospace' }}>{bt.total_trades ?? s.backtest_trades ?? s.trade_count_oos ?? '—'}</div></div>
      </div>
      {years.length > 0 && (
        <div className="ipo-yrchips" style={{ marginBottom: 14 }}>
          {years.map(([y, v]) => {
            const rp = pctOrRatio(v?.return_pct);
            return (
              <div key={y} className="ipo-yrchip">
                <div className="y">ANNUAL BT {y}</div>
                <div className={`r ${sgnCl(rp)}`}>{rp == null ? '—' : signed(rp)}</div>
              </div>
            );
          })}
        </div>
      )}

      {/* mode ladder */}
      <div style={{ fontSize: 10, color: '#565e6c', letterSpacing: '.4px', marginBottom: 8 }}>MODE LADDER</div>
      <div className="ipo-ladder" style={{ marginBottom: 14 }}>
        <ModeTile k="sim" label="SIM · BACKTEST" active={activeMode === 'sim'}>
          <div className="mv">{modes.sim?.win_rate != null ? `${(modes.sim.win_rate * 100).toFixed(1)}%` : '—'}</div>
          <div className="ms">win rate · {modes.sim?.total_trades ?? '—'} OOS trades</div>
        </ModeTile>
        <ModeTile k="paper" label="PAPER" active={activeMode === 'paper'}>
          <div className="mv">{modes.paper?.total_pnl != null ? `$${Number(modes.paper.total_pnl).toLocaleString()}` : '—'}</div>
          <div className="ms">{modes.paper ? `${modes.paper.total_trades ?? 0} closed round-trips${flat ? ' · flat (CASH)' : ''}` : 'stage not reached'}</div>
        </ModeTile>
        <ModeTile k="uat" label="UAT" active={activeMode === 'uat'}>
          <div className="mv">{modes.uat?.total_fills != null && modes.uat.total_fills > 0 ? modes.uat.total_fills : '—'}</div>
          <div className="ms">{modes.uat?.total_fills ? 'fills booked' : 'stage not reached'}</div>
        </ModeTile>
        <ModeTile k="live" label="LIVE" active={activeMode === 'live'}>
          <div className="mv">{modes.live?.total_trades ? `$${Number(modes.live.total_pnl ?? 0).toLocaleString()}` : '—'}</div>
          <div className="ms">{modes.live?.total_trades ? `${modes.live.total_trades} trades` : 'stage not reached'}</div>
        </ModeTile>
      </div>

      {/* engine state */}
      <div style={{ fontSize: 11, color: '#565e6c', marginBottom: 14, lineHeight: 1.6 }}>
        Engine: {latestSignal
          ? <>latest signal <span style={{ fontFamily: 'ui-monospace,monospace', color: '#8b93a3' }}>{latestSignal.ticker} · {latestSignal.signal}</span> at {(latestSignal.ts || '').replace('T', ' ').slice(0, 16)} UTC — {flat ? 'book flat (all CASH), waiting for an in-band entry event' : 'book active'}</>
          : ev ? 'no signals returned by the evaluation endpoint' : 'evaluation endpoint unreachable — engine state unknown'}
        {' · '}{s.assigned_capital != null ? `$${Number(s.assigned_capital).toLocaleString()} assigned` : 'capital unassigned'}
      </div>

      {/* SIM rule-mirror trades — what the strategy would have traded */}
      <div style={{ fontSize: 10, color: '#565e6c', letterSpacing: '.4px', marginBottom: 8 }}>
        SIM · RULE-MIRROR TRADES — what the strategy would have traded (oversub {DRIFT_RULE.bandLo}–{DRIFT_RULE.bandHi}x · enter +{DRIFT_RULE.entryTd}td · hold {DRIFT_RULE.holdTd}td)
      </div>
      {watch && watch.all.length > 0 ? (
        <div style={{ overflowX: 'auto', marginBottom: 6 }}>
          {watch.stats && (
            <div style={{ display: 'flex', gap: 18, fontSize: 10, color: '#8b93a3', fontFamily: 'ui-monospace,monospace', marginBottom: 8, flexWrap: 'wrap' }}>
              <span>{watch.stats.n} closed round-trips</span>
              <span>win {watch.stats.wins}/{watch.stats.n} ({watch.stats.winRate.toFixed(0)}%)</span>
              <span>avg <span className={sgnCl(watch.stats.avg)}>{signed(watch.stats.avg)}</span></span>
              <span>sum <span className={sgnCl(watch.stats.sum)}>{signed(watch.stats.sum)}</span></span>
              {watch.counts.inHold > 0 && <span>{watch.counts.inHold} open (marked to current)</span>}
              {watch.counts.ahead > 0 && <span>{watch.counts.ahead} awaiting entry</span>}
            </div>
          )}
          <WatchTable rows={watch.all} />
        </div>
      ) : (
        <div style={{ fontSize: 11, color: '#565e6c', marginBottom: 6 }}>
          {watch ? 'No listed IPOs currently inside the oversub band and entry window.' : 'Loading watchlist…'}
        </div>
      )}
      <div style={{ fontSize: 10, color: '#565e6c', lineHeight: 1.5, marginBottom: 14 }}>
        Mechanical replay of the documented rule over the IPO calendar using measured closes (entry = 20th trading day, exit = 40th) — <span style={{ color: '#8b93a3' }}>not the engine signal</span>. The engine decides entries itself and is currently flat (CASH); these windows pre-date strategy creation 2026-08-31, so they show what SIM would have traded, not what was traded. ◦ = open, marked to current price.
      </div>

      <div style={{ display: 'flex', gap: 8 }}>
        <button className="ipo-btn" onClick={() => onOpen && onOpen(s.id)}>View detail ↗</button>
        <button className="ipo-btn" onClick={() => onAdjust(s)}>Adjust allocation</button>
        <button className="ipo-btn ipo-btn-danger" onClick={() => onPause(s)}>Pause strategy</button>
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
  const [actionMsg, setActionMsg] = useState(null);

  const load = useCallback(async () => {
    const [lst, strat, sub, bk] = await Promise.all([
      api.get('/api/hkex/ipos?limit=400'),
      api.get('/api/strategies/researcher'),
      api.get('/api/hkex/ipos/subscription'),
      api.get('/api/hkex/ipos/book'),
    ]);
    setIpos(Array.isArray(lst?.ipos) ? lst.ipos : []);
    const bookRows = Array.isArray(strat?.strategies) ? strat.strategies : (Array.isArray(strat?.data) ? strat.data : []);
    const ipoStrats = bookRows.filter(s =>
      (s.asset_class || '').toLowerCase().includes('ipo') || (s.id || '').toLowerCase().startsWith('hk_ipo')
    );
    setStrategies(ipoStrats);
    setSubs(Array.isArray(sub?.ipos) ? sub.ipos : []);
    setBook(Array.isArray(bk?.positions) ? bk.positions : []);
    // per-strategy evaluation (mode ladder + engine signal) — best effort
    const evPairs = await Promise.all(ipoStrats.map(async s => [s.id, await api.get(`/api/strategies/${s.id}/evaluation`)]));
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
        <div style={{ fontSize: 10, color: '#565e6c', letterSpacing: '.4px', fontWeight: 600 }}>WINDOW — APPLIES TO IPO SENTIMENT &amp; IPO KPIS</div>
        <span style={{ display: 'flex', gap: 6 }}>
          {WINDOWS.map(w => (
            <button key={w.k} className={`ipo-yr ${ipoWindow === w.k ? 'active' : ''}`} onClick={() => setIpoWindow(w.k)}>
              {w.label}
            </button>
          ))}
        </span>
      </div>

      {/* IPO sentiment — sector breakdown, top of page */}
      <Panel
        title="IPO SENTIMENT · SECTOR BREAKDOWN"
        tag={<Tag kind="live">LIVE</Tag>}
        right={`window: ${activeWindowLabel}`}
        scroll
        note={<span>Average returns vs IPO offer price over the selected window (D1 = first-day close, D20 = 20th trading-day close, Now = latest price). Win = share of IPOs with a positive first-day return. Cell tooltips show measurement coverage — a thin window means a thin sample, not a strong signal.</span>}
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
                <th className="num" title="Average current return vs offer price">Now %</th>
                <th className="num" title="Share of IPOs with first-day return > 0">Win D1</th>
              </tr>
            </thead>
            <tbody>
              {sectorView.named.map(s => (
                <tr key={s.sector}>
                  <td style={{ color: '#8b93a3' }}>{s.sector}</td>
                  <td className="num">{s.ipo_count}</td>
                  <td className={`num ${sgnCl(s.avg_first_day_return)}`}>{s.avg_first_day_return == null ? '—' : fmtPct(s.avg_first_day_return)}</td>
                  <td className={`num ${sgnCl(s.avg_day20_return)}`} title={`measured on ${s.day20_n ?? '?'} of ${s.ipo_count}`}>
                    {s.avg_day20_return == null ? '—' : fmtPct(s.avg_day20_return)}
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

      {/* stats strip — IPO KPIs, filtered by the global window */}
      {stats && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(6,1fr)', gap: 12 }}>
          <Stat label={`IPOS · ${activeWindowLabel}`} value={stats.n} sub={stats.window} />
          <Stat label="AVG FIRST-DAY" value={stats.fdAvg == null ? '—' : fmtPct(stats.fdAvg)} sub={`measured on ${stats.fdN} of ${stats.n}`} green={stats.fdAvg > 0} />
          <Stat label="MEDIAN FIRST-DAY" value={stats.fdMed == null ? '—' : fmtPct(stats.fdMed)} sub="median, measured rows" green={stats.fdMed > 0} />
          <Stat label="FIRST-DAY WIN RATE" value={stats.fdWin == null ? '—' : `${stats.fdWin.toFixed(0)}%`} sub={`${stats.fdN} priced`} />
          <Stat label="AVG DAY-30" value={stats.d30Avg == null ? '—' : fmtPct(stats.d30Avg)} sub={`measured on ${stats.d30N} of ${stats.n}`} green={stats.d30Avg > 0} />
          <Stat label="IN PIPELINE" value={staged ? staged.announced.length + staged.subscription.length + staged.grey.length : '—'}
                sub={staged ? `${staged.announced.length} announced · ${staged.subscription.length} subscribing · ${staged.grey.length} grey` : ''} />
        </div>
      )}

      {/* stage pipeline */}
      <Panel
        title="IPO PIPELINE — BY STAGE"
        tag={<Tag kind="live">LIVE</Tag>}
        right={`${TODAY} UTC`}
        scroll
        note={<span>Stages are classified client-side from the calendar fields the API serves (application window vs listing date, {TODAY} UTC). The pre-subscription forward calendar is thin upstream — an empty ANNOUNCED stage means &quot;no tracked rows&quot;, not &quot;no HK IPOs filed&quot; (<code>qr_etl t_e71cffde</code>); oversubscription for open windows is pending upstream (<code>qr_etl t_90585bf2</code>).</span>}
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
              No announced (pre-subscription) IPOs tracked — the forward calendar feed is incomplete upstream, so this reads "no tracked rows", not "nothing filed" (qr_etl t_e71cffde).
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

      {/* strategy book */}
      <Panel title="HK IPO STRATEGIES" tag={<Tag kind="live">LIVE</Tag>}>
        <div style={{ padding: 16, display: 'flex', flexDirection: 'column', gap: 16 }}>
          {strategies.length === 0 ? (
            <div style={{ fontSize: 11, color: '#565e6c' }}>No HK IPO strategies registered in the strategy book.</div>
          ) : strategies.map(s => (
            <IpoStrategyCard
              key={s.id}
              s={s}
              ev={evals[s.id]}
              ipos={ipos}
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
            No open IPO positions — the drift book is event-driven and currently flat (paper · watching). Exits are managed from the Execution tab.
          </div>
        )}
      </Panel>
    </div>
  );

  return body;
}

export default IpoTab;
