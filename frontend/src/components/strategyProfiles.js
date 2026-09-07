// Strategy-book model: maps /api/strategies/researcher rows into the shape the
// Strategies workspace renders. Every field here is derived from real API data —
// the old bundle-ported synthetic metric generators (seeded PRNG "slippage",
// "intraday WR", fabricated gate checklists) were removed; promotion gates now
// come from the backend engine via /api/strategies/{id}/promote/check.

export const HORIZON = {
  day: { label: 'Day Trade', color: 'blue', note: 'intraday · flat by close' },
  swing: { label: 'Swing', color: 'emerald', note: '1–5 day holds' },
  position: { label: 'Position', color: 'amber', note: 'weeks–months · NAV-driven' },
};

// ---- map /api/strategies/researcher rows to the workspace strategy shape ----
const ASSET_MAP = { STOCK: 'EQUITY', EQUITY: 'EQUITY', ETF: 'EQUITY', EQUITY_INDEX: 'EQUITY', QUANT: 'EQUITY', FX: 'FX', CRYPTO: 'CRYPTO', COMMODITY: 'FUTURE', COMMODITIES: 'FUTURE', FUTURE: 'FUTURE' };
const HORIZON_BY_ASSET = { EQUITY: 'swing', FX: 'swing', CRYPTO: 'position', FUTURE: 'position' };
const DEPLOYED_STATUS = new Set(['approved', 'active', 'live', 'deployed']);

// Finer asset-class label for filtering UI: keeps ETF distinct from single-stock
// equity (ASSET_MAP above folds ETF into EQUITY for horizon/profile grouping).
function assetClassFor(row) {
  const v = (row.asset_class || '').toUpperCase();
  if (v === 'ETF') return 'ETF';
  if (v === 'FX') return 'FX';
  if (v === 'CRYPTO') return 'CRYPTO';
  if (v === 'COMMODITY' || v === 'COMMODITIES' || v === 'FUTURE') return 'COMMODITY';
  return 'EQUITY'; // STOCK, EQUITY, EQUITY_INDEX, QUANT, or unknown
}

function normalizeMode(row) {
  const em = (row.execution_mode || row.mode || '').toUpperCase();
  if (em === 'LIVE_TRADING' || em === 'LIVE') return 'LIVE_TRADING';
  if (em === 'UAT' || em === 'PAPER_UAT') return 'UAT';
  if (em === 'PAPER_TRADING' || em === 'PAPER') {
    // Registry execution_mode can be stale (rows left at PAPER after Stop).
    // The API's is_paper_monitoring flag (ETL-owned gold.strategy_paper_monitoring)
    // is authoritative: an explicit false means the paper monitor is off, so the
    // row belongs on the simulation rung. Undefined leaves the mode untouched
    // for endpoints that don't expose the flag.
    if (row.is_paper_monitoring === false) return 'SIMULATION';
    return 'PAPER_TRADING';
  }
  if (em === 'SIMULATION' || em === 'SIM') return 'SIMULATION';
  // Fallback for rows that report live monitoring status without an explicit mode.
  if (row.is_paper_monitoring === true) return 'PAPER_TRADING';
  return null;
}

export function stageFor(row) {
  const st = (row.status || '').toLowerCase();
  const mode = normalizeMode(row);
  const researchStatus = (row.research_status || '').toLowerCase();
  if (researchStatus === 'rejected' || researchStatus === 'retired') return 'experimental';
  if (st === 'live' || mode === 'LIVE_TRADING') return 'deployed';
  // Broker rehearsal (IBKR UAT session, paper money) sits between golden and deployed.
  if (mode === 'UAT' || mode === 'PAPER_UAT') return 'uat';
  // A row marked paper but not actively monitored is staged/approved, not live.
  if (st === 'paper' && mode === 'PAPER_TRADING') return 'golden';
  const p = (row.priority || '').toUpperCase();
  if (p === 'GOLDEN') return 'golden';
  if (p === 'NEAR_GOLDEN') return 'near_golden';
  return 'experimental';
}
function tierFor(row) {
  const p = (row.priority || '').toUpperCase();
  if (p === 'GOLDEN') return 'T1';
  if (p === 'NEAR_GOLDEN') return 'T2';
  return 'T3';
}
function horizonFor(row) {
  const f = (row.frequency || '').toLowerCase();
  if (['daily','intraday','hourly','4h','1d','day'].includes(f)) return 'day';
  if (['weekly','1w','week','swing'].includes(f)) return 'swing';
  if (['monthly','1m','month','quarterly','position'].includes(f)) return 'position';
  const asset = (row.asset_class || '').toUpperCase();
  if (asset.includes('ETF')) return 'position';
  if (asset.includes('FX') || asset.includes('CRYPTO')) return 'swing';
  if (asset.includes('FUTURE') || asset.includes('COMMODITY')) return 'position';
  return 'swing';
}
function returnsFor(row) {
  const oos = row.returns_oos;
  if (oos != null) return +Number(oos * 100).toFixed(1);
  const yb = row.yearly_backtest;
  if (yb && typeof yb === 'object') {
    const years = Object.keys(yb).sort();
    for (let i = years.length - 1; i >= 0; i--) {
      const v = yb[years[i]]?.return_pct;
      if (v != null) return fracToPct(v, 1);
    }
  }
  return null;
}
function btPF(row) {
  if (row.profit_factor != null) return +Number(row.profit_factor).toFixed(2);
  if (row.profit_factor_oos != null) return +Number(row.profit_factor_oos).toFixed(2);
  return null;
}

// Unit contract for /api/strategies/researcher fields (verified live 2026-09-07
// across all 24 rows): win_rate / max_drawdown arrive ALREADY percent-scaled
// (61.54 / -5.69); returns_oos and yearly_backtest[].return_pct arrive as
// FRACTIONS (0.1405 / 1.4546). NEVER sniff units from magnitude — a +145.5%
// OOS return (1.4546) must not be mistaken for an already-percent value, and
// a 0.5% win rate must not be multiplied by 100.
export function pctAsIs(value, digits = 1) {
  if (value == null) return null;
  const n = Number(value);
  if (Number.isNaN(n)) return null;
  return +n.toFixed(digits);
}
export function fracToPct(value, digits = 1) {
  if (value == null) return null;
  const n = Number(value);
  if (Number.isNaN(n)) return null;
  return +(n * 100).toFixed(digits);
}

export function mapApiToBook(rows) {
  return (rows || []).map((row) => {
    const asset = ASSET_MAP[(row.asset_class || '').toUpperCase()] || 'EQUITY';
    const stage = stageFor(row);
    const wr = row.win_rate != null ? pctAsIs(row.win_rate, 0) : null;
    const dd = row.max_drawdown != null ? -Math.abs(pctAsIs(row.max_drawdown, 1)) : null;
    const deployed = stage === 'deployed';
    const paperWr = row.paper_wr != null ? +Number(row.paper_wr).toFixed(1) : null;
    const paperPf = row.paper_pf != null ? +Number(row.paper_pf).toFixed(2) : null;
    const paperPnl = row.paper_pnl != null ? +Number(row.paper_pnl) : null;
    return {
      id: row.id,
      name: row.name || row.id,
      asset,
      assetClass: assetClassFor(row),
      horizon: horizonFor(row),
      margin: null,
      tier: tierFor(row),
      stage,
      btWR: wr,
      liveWR: deployed ? wr : null,
      btPF: btPF(row),
      livePF: deployed ? btPF(row) : null,
      paperWR: paperWr,
      paperPF: paperPf,
      paperPNL: paperPnl,
      paperTrades: row.paper_trades != null ? row.paper_trades : 0,
      trades: row.trade_count_oos != null ? row.trade_count_oos : 0,
      returns: returnsFor(row),
      sharpe: row.sharpe_ratio != null ? +Number(row.sharpe_ratio).toFixed(2) : 0,
      dd,
      mode: normalizeMode(row) || 'SIMULATION',
      signal_family_key: row.signal_family_key || null,
      _api: row,
    };
  });
}
