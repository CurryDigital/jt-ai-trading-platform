// Command center — pure aggregation, currency, and normalization utilities.
// No React imports; every function is unit-testable in isolation. Currency
// rule: values in different currencies are NEVER netted — mixed-currency sets
// are reported as per-currency segments.

import { api } from '../../utils';
import { fmtDate, tsTip, daysHeld } from './format';
import { MARKET_LABEL, NO_ENTRY_TIPS, NO_STRAT_TIPS, NO_FILL_PNL_TIP, NO_FILL_STRAT_TIP, NO_ORDER_DATE_TIP } from './meta';

// ---------------------------------------------------------------------------
// Drawdown — peak-to-trough of a curve series [{equity}]. Derived from the
// displayed series only; callers must label it with the series basis
// (realized P&L curve vs genuine equity curve) and the window.
// ---------------------------------------------------------------------------
export const maxDrawdown = (data) => {
  if (!data || data.length < 2) return null;
  let peak = -Infinity, dd = 0;
  for (const p of data) {
    if (p.equity > peak) peak = p.equity;
    const d = p.equity - peak;
    if (d < dd) dd = d;
  }
  return dd; // <= 0, in curve units
};

// ---------------------------------------------------------------------------
// Currency-safe summation: sums per currency, never across currencies.
// ---------------------------------------------------------------------------
export const sumByCcy = (rows, field, defCcy) => {
  const acc = new Map();
  let skipped = 0;
  for (const r of rows || []) {
    const v = r[field];
    if (v == null || isNaN(v)) { skipped += 1; continue; }
    const c = r.ccy || defCcy;
    acc.set(c, (acc.get(c) || 0) + v);
  }
  return { sums: [...acc.entries()], skipped };
};

export const perCcyUnrealized = (rows, defCcy = 'USD') => {
  if (!rows) return null;
  const acc = new Map();
  for (const p of rows) {
    if (p.unreal == null || isNaN(p.unreal)) continue;
    const c = p.ccy || defCcy;
    acc.set(c, (acc.get(c) || 0) + p.unreal);
  }
  return acc.size > 0 ? [...acc.entries()] : null;
};

// ---------------------------------------------------------------------------
// Gross open market value + concentration + per-strategy allocation.
// Mixed-currency books return { mixed: true } and nothing is netted.
// ---------------------------------------------------------------------------
export const bookGrossStats = (posRows, defCcy = 'USD') => {
  if (!posRows) return null;
  const marked = posRows.filter(p => p.mv != null && !isNaN(p.mv));
  if (marked.length === 0) return { mixed: false, gross: 0, ccy: defCcy, top1: null, top3: null, top1Name: null, alloc: [] };
  const ccys = new Set(marked.map(p => p.ccy || defCcy));
  if (ccys.size !== 1) return { mixed: true };
  const gross = marked.reduce((s, p) => s + Math.abs(p.mv), 0);
  const byMv = [...marked].sort((x, y) => Math.abs(y.mv) - Math.abs(x.mv));
  const top1 = gross > 0 && byMv[0] ? Math.abs(byMv[0].mv) / gross * 100 : null;
  const top3 = gross > 0 ? byMv.slice(0, 3).reduce((s, p) => s + Math.abs(p.mv), 0) / gross * 100 : null;
  const byStrat = new Map();
  for (const p of marked) {
    const k = p.strategy || 'Unattributed';
    byStrat.set(k, (byStrat.get(k) || 0) + Math.abs(p.mv));
  }
  const alloc = [...byStrat.entries()].map(([name, value]) => ({ name, value })).sort((x, y) => y.value - x.value);
  return { mixed: false, gross, ccy: [...ccys][0], top1, top3, top1Name: byMv[0]?.symbol, alloc };
};

// ---------------------------------------------------------------------------
// Contribution: a percentage of the book total is only meaningful when the
// total is positive and not near zero — with a zero/negative/tiny total the
// percentage explodes or flips sign and misleads. In those cases the caller
// shows the signed CURRENCY contribution instead of a percentage.
// ---------------------------------------------------------------------------
export const CONTRIB_MIN_BASE = 1; // currency units; below this a % is noise

export const contribution = (value, total) => {
  if (value == null || isNaN(value)) return { mode: 'none' };
  if (total == null || isNaN(total) || total <= 0 || Math.abs(total) < CONTRIB_MIN_BASE) {
    return { mode: 'amount', amount: value };
  }
  return { mode: 'pct', pct: value / total * 100 };
};

// ---------------------------------------------------------------------------
// Reconciliation: Σ per-strategy realized must tie to the book-level cum_pnl.
// Returns { ok, delta } — ok within rounding tolerance (values are cents).
// ---------------------------------------------------------------------------
export const reconcileRealized = (aggTotal, statsCum, tol = 0.02) => {
  if (aggTotal == null || statsCum == null) return null;
  const delta = Math.round((aggTotal - statsCum) * 100) / 100;
  return { ok: Math.abs(delta) <= tol, delta };
};

// Page-truncation detector for the reconciliation test: aggregating only the
// first `limit` rows of a ledger under-reports books larger than the limit.
export const realizedFromTrades = (trades, stratNames = {}, limit = null) => {
  const rows = limit != null ? (trades || []).slice(0, limit) : (trades || []);
  const m = {};
  for (const t of rows) {
    if (t.pnl == null || isNaN(t.pnl)) continue;
    const name = stratNames[t.strategy_id] || t.strategy_id || null;
    if (!name) continue;
    if (!m[name]) m[name] = { realized: 0, closed: 0 };
    m[name].realized += t.pnl;
    m[name].closed += 1;
  }
  return m;
};

// ---------------------------------------------------------------------------
// Strategy rows: union of open-position groups with the authoritative
// per-strategy realized aggregate (/api/execution/strategy-pnl — full ledger,
// no truncation). Split into ACTIVE (open holdings) vs HISTORICAL (closed
// ledger only) and sorted by max(|unrealized|, |realized|, |market value|).
// ---------------------------------------------------------------------------
export const buildStrategyRows = ({ posRows, stratPnl, riskBy }) => {
  const m = new Map(); // key = strategy_id || `name:<label>`
  const keyOf = (id, name) => id || `name:${name || ''}`;
  const entry = (id, name) => {
    const k = keyOf(id, name);
    if (!m.has(k)) m.set(k, { key: k, id: id || null, name: name || null, open: 0, mv: 0, mvN: 0, unreal: 0, unN: 0, realized: null, closed: null, ytdRealized: null, winRate: null });
    return m.get(k);
  };
  for (const p of posRows || []) {
    const g = entry(p.strategyId, p.strategy);
    if (p.strategyId && p.strategy && !g.name) g.name = p.strategy;
    g.open += 1;
    if (p.mv != null && !isNaN(p.mv)) { g.mv += p.mv; g.mvN += 1; }
    if (p.unreal != null && !isNaN(p.unreal)) { g.unreal += p.unreal; g.unN += 1; }
  }
  for (const s of stratPnl?.strategies || []) {
    const g = entry(s.strategy_id, s.name);
    if (!g.name) g.name = s.name;
    if (!g.id) g.id = s.strategy_id;
    g.realized = s.cum_pnl ?? null;
    g.closed = s.closed_trades ?? null;
    g.ytdRealized = s.ytd_pnl ?? null;
    g.winRate = s.win_rate ?? null;
  }
  const arr = [...m.values()].map(g => ({ ...g, risk: riskBy?.[g.name] || riskBy?.[g.id] || null }));
  const sortKey = (g) => Math.max(Math.abs(g.unreal), Math.abs(g.realized ?? 0), Math.abs(g.mv));
  arr.sort((a, b) => sortKey(b) - sortKey(a));
  const totalUn = arr.reduce((s, g) => s + g.unreal, 0);
  const totalUnN = arr.reduce((s, g) => s + g.unN, 0);
  return {
    active: arr.filter(g => g.open > 0),
    historical: arr.filter(g => g.open === 0 && (g.closed ?? 0) > 0),
    empty: arr.filter(g => g.open === 0 && !(g.closed > 0)),
    totalUn: totalUnN > 0 ? totalUn : null,
  };
};

// ---------------------------------------------------------------------------
// Unrealized P&L drivers: ranked over OPEN positions with marks, segmented
// per currency (never netted).
// ---------------------------------------------------------------------------
export const driverSegments = (rows, defCcy = 'USD') => {
  if (!rows) return { loading: true };
  const marked = rows.filter(p => p.unreal != null && !isNaN(p.unreal));
  if (marked.length === 0) return { empty: true };
  const ccys = new Set(marked.map(p => p.ccy || defCcy));
  if (ccys.size > 1) {
    const segs = [...ccys].map(c => ({ ccy: c, rows: marked.filter(p => (p.ccy || defCcy) === c) }));
    return { mixed: segs };
  }
  return { single: { ccy: [...ccys][0], rows: marked } };
};

export const rankDrivers = (segRows) => {
  const sorted = [...segRows].sort((a, b) => b.unreal - a.unreal);
  const pos = sorted.filter(d => d.unreal > 0).slice(0, 3);
  const neg = sorted.filter(d => d.unreal < 0).slice(-3).reverse();
  const maxAbs = Math.max(1, ...sorted.map(d => Math.abs(d.unreal)));
  return { pos, neg, maxAbs };
};

// ---------------------------------------------------------------------------
// Action items: critical alerts FIRST, then execution/monitoring issues
// (warnings), then info. Environment-scoped; HALT is global.
// ---------------------------------------------------------------------------
const SEV_RANK = { critical: 0, warning: 1, info: 2 };

export const buildActionItems = ({ env, limits, overview, positions }) => {
  const items = [];
  if (limits?.global_halt) {
    items.push({ id: 'halt', sev: 'critical', title: 'Global HALT active', impact: 'Order firing halted in every environment — gold.risk_limits.global_halt', target: 'settings' });
  }
  if (env === 'paper') {
    const risks = overview?.strategy_risks || [];
    const attn = (overview?.attention || []).filter(a => !String(a.id || '').startsWith('live_'));
    for (const r of risks) {
      items.push({
        id: `risk-${r.strategy_id}`, sev: r.sev || 'warning',
        title: `${r.name || r.strategy_id}: risk trigger`,
        impact: (r.triggers || []).join(' · '), target: 'strategies',
      });
    }
    for (const a of attn) {
      if (a.sev === 'info') continue;
      items.push({
        id: a.id, sev: a.sev || 'info', title: a.title, impact: a.impact,
        target: a.target || null,
        date: fmtDate(a.created_at), dateTip: a.created_at ? tsTip(a.created_at) : null,
      });
    }
    if ((overview?.monitoring_gap || 0) > 0) {
      items.push({ id: 'gap', sev: 'warning', title: `${overview.monitoring_gap} position${overview.monitoring_gap === 1 ? '' : 's'} without monitoring`, impact: 'Open paper legs not actively monitored', target: 'execution' });
    }
  }
  if (env === 'uat' && positions && positions.connected === false) {
    items.push({ id: 'uat-down', sev: 'critical', title: 'UAT session disconnected', impact: 'No order routing or portfolio feed on the UAT session', target: 'execution' });
  }
  if (env === 'live') {
    const attn = (overview?.attention || []).filter(a => String(a.id || '').startsWith('live_'));
    for (const a of attn) {
      if (a.sev === 'info') continue;
      items.push({
        id: a.id, sev: a.sev || 'info', title: a.title, impact: a.impact,
        target: a.target || null,
        date: fmtDate(a.created_at), dateTip: a.created_at ? tsTip(a.created_at) : null,
      });
    }
    const health = Array.isArray(overview?.deployed_health) ? overview.deployed_health : [];
    for (const h of health) {
      items.push({ id: `health-${h.strategy_id || h.name}`, sev: h.sev || 'warning', title: h.title || `${h.name || h.strategy_id}: health`, impact: h.impact || null, target: 'strategies' });
    }
  }
  items.sort((a, b) => (SEV_RANK[a.sev] ?? 3) - (SEV_RANK[b.sev] ?? 3));
  return items;
};

// ---------------------------------------------------------------------------
// Per-environment row normalizers.
// Unified position row: { key, entryDate, entryTip, symbol, ccy, strategyId,
// strategy, strategyTip, side, qty, entryPx, curPx, curTip, unreal, mv, days }
// ---------------------------------------------------------------------------
export function normPositions(env, raw, stratNames = {}, now = undefined) {
  if (env === 'sim') {
    return (raw || []).map(p => ({
      key: `sim-${p.id}`,
      entryDate: fmtDate(p.entry_date),
      entryTip: p.entry_date ? `entry ${fmtDate(p.entry_date)}` : null,
      symbol: p.ticker, ccy: null,
      strategyId: p.strategy_id || null,
      strategy: stratNames[p.strategy_id] || p.strategy_id,
      side: (p.side || '').toUpperCase() || null,
      qty: p.quantity, entryPx: p.entry_price, curPx: p.current_price,
      curTip: p.updated_at ? `marked ${tsTip(p.updated_at)}` : null,
      unreal: p.unrealized_pnl, mv: p.market_value,
      days: daysHeld(p.entry_date, now),
    }));
  }
  if (env === 'paper') {
    return (raw || []).map(p => ({
      key: `paper-${p.id}`,
      entryDate: fmtDate(p.opened_at),
      entryTip: p.opened_at ? `entry ${fmtDate(p.opened_at)}` : null,
      symbol: p.ticker, ccy: null,
      strategyId: p.strategy_id || null,
      strategy: stratNames[p.strategy_id] || p.strategy_id,
      side: (p.direction || '').toUpperCase() || null,
      qty: p.shares, entryPx: p.entry_price, curPx: p.current_price,
      curTip: p.price_as_of ? `price as of ${fmtDate(p.price_as_of)}` : null,
      unreal: p.unrealised_pnl,
      mv: (p.shares != null && p.current_price != null) ? p.shares * p.current_price : null,
      days: daysHeld(p.opened_at, now),
    }));
  }
  if (env === 'uat') {
    return (raw || []).map((p, i) => ({
      key: `uat-${p.symbol}-${p.currency}-${i}`,
      entryDate: null, entryTip: NO_ENTRY_TIPS.uat,
      symbol: p.ticker || p.symbol, ccy: p.currency || null,
      strategyId: null,
      strategy: null, strategyTip: NO_STRAT_TIPS.uat,
      side: p.qty != null ? (p.qty >= 0 ? 'LONG' : 'SHORT') : null,
      qty: p.qty, entryPx: p.avg_cost, curPx: p.market_price,
      curTip: p.market_price == null ? 'no mark from gateway' : null,
      unreal: p.unrealized_pnl, mv: p.market_value,
      days: null,
    }));
  }
  // live
  return (raw || []).map((p, i) => ({
    key: `live-${p.id ?? p.ticker}-${i}`,
    entryDate: fmtDate(p.entry_date),
    entryTip: p.entry_date
      ? `entry ${fmtDate(p.entry_date)}${p.qty_reconciled === false ? ' · unreconciled ledger' : ''}`
      : NO_ENTRY_TIPS.live,
    symbol: p.ticker, ccy: null,
    strategyId: p.strategy_id || null,
    strategy: p.strategy_id ? (stratNames[p.strategy_id] || p.strategy_name || p.strategy_id) : null,
    strategyTip: p.strategy_id ? null : NO_STRAT_TIPS.live,
    side: (p.side || '').toUpperCase() || null,
    qty: p.quantity, entryPx: p.avg_entry, curPx: p.current_price,
    unreal: p.unrealized_pnl,
    mv: (p.quantity != null && p.current_price != null) ? p.quantity * p.current_price : null,
    days: daysHeld(p.entry_date, now),
  }));
}

// Unified fill row: { key, fillDate, fillTs, ticker, strategy, strategyTip,
// side, qty, price, pnl, pnlTip }
export function normFills(env, raw, stratNames = {}) {
  return (raw || []).map((t, i) => ({
    key: `${env}-${t.t}-${t.ticker}-${i}`,
    fillDate: fmtDate(t.t),
    fillTs: t.t,
    ticker: t.ticker,
    strategy: (env === 'sim' || env === 'paper') ? (stratNames[t.strategy_id] || t.strategy_id || null) : null,
    strategyTip: (env === 'uat' || env === 'live') ? NO_FILL_STRAT_TIP : null,
    side: (t.side || '').toUpperCase() || null,
    qty: t.qty, price: t.price,
    pnl: t.pnl ?? null,
    pnlTip: t.pnl == null ? NO_FILL_PNL_TIP : null,
  }));
}

// Unified order row: { key, orderDate, orderTs, orderTip, ticker, side, qty,
// limitOrType, strategy, status }
export function normOrders(env, raw, stratNames = {}) {
  if (env === 'uat') {
    return (raw || []).map((o, i) => ({
      key: `uat-${o.order_id ?? o.perm_id}-${i}`,
      orderDate: null, orderTs: null, orderTip: NO_ORDER_DATE_TIP,
      ticker: o.local_symbol || o.symbol,
      side: (o.action || '').toUpperCase() || null,
      qty: o.qty,
      limitOrType: o.order_type ?? '—',
      strategy: null,
      status: o.status,
    }));
  }
  return (raw || []).map((o, i) => ({
    key: `${env}-${o.source}-${o.ticker}-${i}`,
    orderDate: fmtDate(o.submitted_at),
    orderTs: o.submitted_at,
    ticker: o.ticker,
    side: (o.side || '').toUpperCase() || null,
    qty: o.qty,
    limitOrType: o.limit_price != null ? o.limit_price.toLocaleString() : (o.order_type || 'MKT'),
    strategy: o.strategy_name || stratNames[o.strategy_id] || o.strategy_id || o.venue || null,
    status: o.status,
  }));
}

// ---------------------------------------------------------------------------
// Opportunities loader (SIM/PAPER only) — shared fetch + normalize.
// ---------------------------------------------------------------------------
export async function fetchOpportunities() {
  const [u, fams] = await Promise.all([
    api.get('/api/signals/universe?markets=US,HK,CRYPTO,FX,METAL&limit=10'),
    api.get('/api/signals/families'),
  ]);
  if (!u) return null;
  const famMap = {};
  for (const f of (fams?.data || [])) famMap[f.key] = f;
  const data = u.data || u;
  const picks = [];
  for (const [mkt, rows] of Object.entries(data)) {
    if (!Array.isArray(rows)) continue;
    const buys = rows.filter(r => r.direction === 'BUY' && !r.exit_to_cash)
      .sort((a, b) => (b.potential ?? -1) - (a.potential ?? -1));
    const top = buys[0];
    if (!top) continue;
    const fam = (top.families || []).map(k => famMap[k]).find(Boolean);
    const note = top.note && top.note !== '—' ? top.note : null;
    picks.push({
      market: mkt,
      ticker: top.ticker,
      name: top.name || null,
      potential: top.potential ?? null,
      direction: top.direction || null,
      price: top.price ?? null,
      changePct: top.change_pct ?? null,
      strategyName: fam?.strategy_name || null,
      reason: note || (fam ? `${fam.label} family signal` : `${MARKET_LABEL[mkt] || mkt} BUY signal`),
    });
  }
  picks.sort((a, b) => (b.potential ?? -1) - (a.potential ?? -1));
  const top3 = picks.slice(0, 3);
  const dates = top3.length
    ? await api.get(`/api/command/signal-freshness?tickers=${top3.map(p => encodeURIComponent(p.ticker)).join(',')}`)
    : null;
  const dateMap = dates?.dates || {};
  return top3.map(p => ({ ...p, signalDate: dateMap[p.ticker.toUpperCase()] || null }));
}
