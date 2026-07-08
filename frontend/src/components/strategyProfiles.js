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
