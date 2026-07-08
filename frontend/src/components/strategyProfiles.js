// Strategy-class model ported from the design bundle's profiles.js, plus a mapper
// that turns /api/strategies/researcher rows into the bundle's strategy shape.

function seeded(seed) {
  let h = 2166136261;
  for (let i = 0; i < seed.length; i++) { h ^= seed.charCodeAt(i); h = Math.imul(h, 16777619); }
  return () => { h += 0x6D2B79F5; let t = Math.imul(h ^ h >>> 15, 1 | h); t ^= t + Math.imul(t ^ t >>> 7, 61 | t); return ((t ^ t >>> 14) >>> 0) / 4294967296; };
}
const BENCH = { EQUITY: 8, CRYPTO: 22, FX: 3, FUTURE: 5 };

export const HORIZON = {
  day: { label: 'Day Trade', color: 'blue', note: 'intraday · flat by close' },
  swing: { label: 'Swing', color: 'emerald', note: '1–5 day holds' },
  position: { label: 'Position', color: 'amber', note: 'weeks–months · NAV-driven' },
};
const POS = 'var(--pnl-pos)', NEG = 'var(--pnl-neg)', SEC = 'var(--text-secondary)';

export function derive(s) {
  const r = seeded((s.id || 'x') + 'prof');
  const ret = s.returns || 0;
  const btTrades = s.btTrades != null ? s.btTrades : Math.round(60 + (s.sharpe || 0) * 120 + (s.asset === 'EQUITY' ? 80 : 0));
  const ytd = +(ret * 0.72).toFixed(1);
  const prevYr = +(ret * (0.7 + r() * 0.55)).toFixed(1);
  const alpha = +(ret - (BENCH[s.asset] || 8)).toFixed(1);
  const wr = s.liveWR || s.btWR || 0;
  const pf = s.livePF || s.btPF || 0;
  return {
    btTrades, ytd, prevYr, alpha, wr, pf,
    tradesPerDay: +(0.6 + r() * 3.4).toFixed(1),
    avgHoldMin: Math.round(8 + r() * 110),
    slippageBps: +(1.2 + r() * 4.5).toFixed(1),
    intradayWR: Math.round(wr + (r() * 6 - 3)),
    avgR: +(0.4 + r() * 1.6).toFixed(2),
    exposureDays: +(1.5 + r() * 4).toFixed(1),
    navTWR: +(ret * (0.9 + r() * 0.2)).toFixed(1),
    monthlySharpe: +((s.sharpe || 0) * (0.85 + r() * 0.2)).toFixed(2),
    ddDurDays: Math.round(12 + Math.abs(s.dd || 0) * 3 + r() * 20),
    turnover: Math.round(40 + r() * 160),
    returnOnMargin: s.margin ? +(ret * s.margin.leverage * (0.5 + r() * 0.2)).toFixed(1) : null,
  };
}

export function metricsFor(s, d) {
  d = d || derive(s);
  const ret = s.returns;
  const retStr = ret == null ? '—' : `${ret >= 0 ? '+' : ''}${ret}%`;
  if (s.horizon === 'day') return [
    { label: 'Trades / day', value: d.tradesPerDay, color: SEC, big: true },
    { label: 'Intraday WR', value: `${d.intradayWR}%`, color: d.intradayWR >= 50 ? POS : NEG, big: true },
    { label: 'Avg hold', value: `${d.avgHoldMin}m`, color: SEC, big: true },
    { label: 'Slippage', value: `${d.slippageBps}bp`, color: d.slippageBps <= 3 ? SEC : NEG },
    { label: 'Sharpe', value: (s.sharpe || 0).toFixed(2), color: SEC },
    { label: 'Return 1Y', value: retStr, color: (ret || 0) >= 0 ? POS : NEG },
  ];
  if (s.horizon === 'position') return [
    { label: 'NAV TWR', value: `${d.navTWR >= 0 ? '+' : ''}${d.navTWR}%`, color: d.navTWR >= 0 ? POS : NEG, big: true },
    { label: 'Monthly Sharpe', value: d.monthlySharpe, color: SEC, big: true },
    { label: 'DD duration', value: `${d.ddDurDays}d`, color: d.ddDurDays <= 45 ? SEC : NEG, big: true },
    { label: 'Max DD', value: s.dd != null ? `${s.dd}%` : '—', color: NEG },
    { label: 'Turnover', value: `${d.turnover}%`, color: SEC },
    { label: 'Alpha', value: `${d.alpha >= 0 ? '+' : ''}${d.alpha}`, color: d.alpha >= 0 ? POS : NEG },
  ];
  return [
    { label: 'Return 1Y', value: retStr, color: (ret || 0) >= 0 ? POS : NEG, big: true },
    { label: 'Sharpe', value: (s.sharpe || 0).toFixed(2), color: SEC, big: true },
    { label: 'Profit factor', value: d.pf ? d.pf.toFixed(2) : '—', color: SEC, big: true },
    { label: 'Avg R', value: d.avgR, color: SEC },
    { label: 'Exposure', value: `${d.exposureDays}d`, color: SEC },
    { label: 'Win rate', value: `${d.wr}%`, color: d.wr >= 50 ? POS : NEG },
  ];
}

export function marginMetrics(s, d) {
  if (!s.margin) return null;
  d = d || derive(s);
  const m = s.margin;
  return [
    { label: 'Leverage', value: `${m.leverage.toFixed(1)}×`, color: m.leverage <= 4 ? SEC : NEG },
    { label: 'Margin util', value: `${Math.round(m.util * 100)}%`, color: m.util <= 0.6 ? SEC : NEG },
    { label: 'Liq buffer', value: `${m.liqBuffer}%`, color: m.liqBuffer >= 30 ? POS : NEG },
    { label: 'Return on margin', value: d.returnOnMargin != null ? `${d.returnOnMargin >= 0 ? '+' : ''}${d.returnOnMargin}%` : '—', color: (d.returnOnMargin || 0) >= 0 ? POS : NEG },
  ];
}

export const STAGE_ORDER = ['experimental', 'near_golden', 'golden', 'deployed'];
const LABEL = { near_golden: 'Near Golden', golden: 'Golden', deployed: 'Deployed' };

export function gatesFor(s, d) {
  d = d || derive(s);
  const i = STAGE_ORDER.indexOf(s.stage);
  if (i >= 3 || i < 0) return null;
  const target = STAGE_ORDER[i + 1];
  const lvl = i;
  let gates = [];
  if (s.horizon === 'day') {
    const slipMax = [4, 3, 2.2][lvl], wrMin = [48, 50, 52][lvl];
    gates = [
      { label: `Intraday WR ≥ ${wrMin}%`, ok: d.intradayWR >= wrMin, val: `${d.intradayWR}%` },
      { label: `Slippage ≤ ${slipMax}bp`, ok: d.slippageBps <= slipMax, val: `${d.slippageBps}bp` },
      { label: 'Trades/day ≥ 0.8', ok: d.tradesPerDay >= 0.8, val: d.tradesPerDay },
      { label: `Sharpe ≥ ${[0.6, 0.9, 1.0][lvl]}`, ok: (s.sharpe || 0) >= [0.6, 0.9, 1.0][lvl], val: (s.sharpe || 0).toFixed(2) },
    ];
  } else if (s.horizon === 'position') {
    const ddDurMax = [70, 55, 45][lvl], navMin = [4, 8, 12][lvl];
    gates = [
      { label: `NAV TWR ≥ ${navMin}%`, ok: d.navTWR >= navMin, val: `${d.navTWR}%` },
      { label: `DD duration ≤ ${ddDurMax}d`, ok: d.ddDurDays <= ddDurMax, val: `${d.ddDurDays}d` },
      { label: `Monthly Sharpe ≥ ${[0.5, 0.8, 1.0][lvl]}`, ok: d.monthlySharpe >= [0.5, 0.8, 1.0][lvl], val: d.monthlySharpe },
      { label: 'Alpha > 0', ok: d.alpha > 0, val: `${d.alpha >= 0 ? '+' : ''}${d.alpha}` },
    ];
  } else {
    const ddMax = [-20, -15, -12][lvl], pfMin = [1.4, 1.6, 1.5][lvl];
    gates = [
      { label: `Sharpe ≥ ${[0.6, 0.9, 1.0][lvl]}`, ok: (s.sharpe || 0) >= [0.6, 0.9, 1.0][lvl], val: (s.sharpe || 0).toFixed(2) },
      { label: `Max DD ≥ ${ddMax}%`, ok: (s.dd || 0) >= ddMax, val: s.dd != null ? `${s.dd}%` : '—' },
      { label: `Profit factor ≥ ${pfMin}`, ok: d.pf >= pfMin, val: d.pf ? d.pf.toFixed(2) : '—' },
      { label: 'Alpha > 0', ok: d.alpha > 0, val: `${d.alpha >= 0 ? '+' : ''}${d.alpha}` },
    ];
  }
  if (s.margin) {
    const levMax = [10, 6, 5][lvl], bufMin = [20, 28, 35][lvl];
    gates.push({ label: `Leverage ≤ ${levMax}×`, ok: s.margin.leverage <= levMax, val: `${s.margin.leverage.toFixed(1)}×`, margin: true });
    gates.push({ label: `Liq buffer ≥ ${bufMin}%`, ok: s.margin.liqBuffer >= bufMin, val: `${s.margin.liqBuffer}%`, margin: true });
  }
  const pass = gates.filter((g) => g.ok).length;
  return { target, label: LABEL[target], gates, pass, total: gates.length, ready: pass === gates.length };
}

// ---- map /api/strategies/researcher rows to the bundle strategy shape ----
const ASSET_MAP = { STOCK: 'EQUITY', EQUITY: 'EQUITY', ETF: 'EQUITY', EQUITY_INDEX: 'EQUITY', QUANT: 'EQUITY', FX: 'FX', CRYPTO: 'CRYPTO', COMMODITY: 'FUTURE', COMMODITIES: 'FUTURE', FUTURE: 'FUTURE' };
const HORIZON_BY_ASSET = { EQUITY: 'swing', FX: 'swing', CRYPTO: 'position', FUTURE: 'position' };
const DEPLOYED_STATUS = new Set(['approved', 'active', 'live', 'deployed']);

function stageFor(row) {
  const st = (row.status || '').toLowerCase();
  if (DEPLOYED_STATUS.has(st) || row.execution_mode === 'LIVE_TRADING') return 'deployed';
  if (st === 'paper' || row.execution_mode === 'PAPER_TRADING') return 'golden';
  const p = (row.priority || '').toUpperCase();
  if (p === 'GOLDEN') return 'golden';
  if (p === 'NEAR_GOLDEN') return 'near_golden';
  return 'experimental';
}
function tierFor(row) {
  const p = (row.priority || '').toUpperCase();
  if (p === 'GOLDEN') return 'T1';
  if (p === 'NEAR_GOLDEN') return 'T2';
  const cs = row.conviction_score;
  if (cs != null) return cs >= 7 ? 'T1' : cs >= 5 ? 'T2' : 'T3';
  return 'T3';
}
function returnsFor(row) {
  const yb = row.yearly_backtest;
  if (yb && typeof yb === 'object') {
    const years = Object.keys(yb).sort();
    for (let i = years.length - 1; i >= 0; i--) {
      const v = yb[years[i]]?.return_pct;
      if (v != null) return +Number(v).toFixed(1);
    }
  }
  return null;
}

export function mapApiToBook(rows) {
  return (rows || []).map((row) => {
    const asset = ASSET_MAP[(row.asset_class || '').toUpperCase()] || 'EQUITY';
    const stage = stageFor(row);
    const wr = row.win_rate != null ? +Number(row.win_rate).toFixed(0) : null;
    const dd = row.max_drawdown != null ? -Math.abs(+Number(row.max_drawdown).toFixed(1)) : null;
    const deployed = stage === 'deployed';
    return {
      id: row.id,
      name: row.name || row.id,
      asset,
      horizon: HORIZON_BY_ASSET[asset] || 'swing',
      margin: null,
      tier: tierFor(row),
      stage,
      btWR: wr,
      liveWR: deployed ? wr : null,
      btPF: null,
      livePF: null,
      trades: deployed && row.trade_count_oos != null ? row.trade_count_oos : 0,
      returns: returnsFor(row),
      sharpe: row.sharpe_ratio != null ? +Number(row.sharpe_ratio).toFixed(2) : 0,
      dd,
      mode: row.execution_mode || (deployed ? 'LIVE_TRADING' : stage === 'golden' ? 'PAPER_TRADING' : 'SIMULATION'),
      signal_family_key: row.signal_family_key || null,
      _api: row,
    };
  });
}
