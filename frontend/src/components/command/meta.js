// Command center — shared constants. Plain .js so non-component exports are
// lint-clean (react-refresh/only-export-components).

export const ENVS = ['sim', 'paper', 'uat', 'live'];

export const ENV_META = {
  sim:   { badge: 'SIM',   tip: 'Simulation book — virtual money · synthetic fills · no IBKR' },
  paper: { badge: 'PAPER', tip: 'Paper book — virtual money · strategy rehearsal · no IBKR' },
  uat:   { badge: 'UAT',   tip: 'UAT — IBKR paper account · real order routing · paper money' },
  live:  { badge: 'LIVE',  tip: 'Live book — IBKR live account · real money' },
};

export const SEV_DOT = { critical: 'bg-rose-400', warning: 'bg-slate-400', info: 'bg-slate-600' };
export const SEV_TAG = { critical: 'text-rose-300 border-rose-500/40', warning: 'text-slate-300 border-white/[0.15]' };

export const NO_ENTRY_TIPS = {
  uat: 'Entry dates are unavailable for UAT gateway positions; no entry timestamp is inferred.',
  live: 'No entry attribution is available for this ledger-fallback position; no matching open-lot fill was found.',
};
export const NO_STRAT_TIPS = {
  uat: 'Not served: the IBKR portfolio payload has no strategy attribution — the UAT fills ledger is per-fill and cannot be uniquely mapped to an aggregated position.',
  live: 'Manual/untagged fill — no strategy attribution across the open lots (never fabricated).',
};
export const NO_FILL_PNL_TIP = 'Per-fill realized P&L is not served for this environment (fills blotter, not round-trips).';
export const NO_FILL_STRAT_TIP = 'This fills blotter has no strategy attribution.';
export const NO_ORDER_DATE_TIP = 'The UAT gateway does not provide an order submission timestamp.';

export const POSITIONS_PAGE = 16;

export const POSITIONS_HEAD = [
  { k: 'entry', label: 'Entry date', align: 'left' },
  { k: 'symbol', label: 'Symbol', align: 'left' },
  { k: 'strategy', label: 'Strategy', align: 'left' },
  { k: 'side', label: 'Side', align: 'left' },
  { k: 'qty', label: 'Qty', align: 'right' },
  { k: 'entryPx', label: 'Entry price', align: 'right' },
  { k: 'curPx', label: 'Current price', align: 'right' },
  { k: 'unreal', label: 'Unrealized P&L', align: 'right' },
  { k: 'mv', label: 'Market value', align: 'right' },
  { k: 'days', label: 'Days held', align: 'right' },
];

export const SORTS = {
  entry:  { label: 'Entry date ↓', fn: (a, b) => (b.entryDate || '').localeCompare(a.entryDate || '') },
  unreal: { label: 'Unrealized ↓', fn: (a, b) => (b.unreal ?? -Infinity) - (a.unreal ?? -Infinity) },
  mv:     { label: 'Mkt value ↓',  fn: (a, b) => (b.mv ?? -Infinity) - (a.mv ?? -Infinity) },
  days:   { label: 'Days held ↓',  fn: (a, b) => (b.days ?? -1) - (a.days ?? -1) },
};

export const MARKET_LABEL = { US: 'US Equity', HK: 'HK Equity', CRYPTO: 'Crypto', FX: 'FX', METAL: 'Metals' };

export const SCORE_TIP = 'Engine conviction score (0–100). '
  + 'The signal pipeline publishes no formula or component breakdown for this field — '
  + 'treat it as a heuristic ranking, not a decomposable model output.';

export const REGIME_MEANING = {
  TREND: 'Trending tape — momentum and trend-following books should keep working; fade entries get run over.',
  MEAN_REV: 'Mean-reverting tape — moves fade; breakout entries underperform.',
  CARRY: 'Carry / range tape — low-vol grind; income-style books favoured over breakouts.',
  EVENT: 'Event-driven stress — expect gaps and vol spikes; gross exposure earns less.',
  FLAT: 'No dominant regime — weak signal environment; neutral sizing.',
};

export const RISK_CELL = (v) => v == null ? 'bg-white/[0.04] text-slate-600'
  : v >= 60 ? 'bg-emerald-500/15 text-emerald-300'
  : v <= 40 ? 'bg-rose-500/15 text-rose-300'
  : 'bg-white/[0.06] text-slate-300';
