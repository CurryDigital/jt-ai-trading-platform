// Formatters, constants and pure helpers for the Derivatives vertical.
// Split from shared.jsx (2026-10-17) because react-refresh/only-export-components
// forbids non-component exports from component modules.

// Publishable-gate threshold (backend strategies.py researcher feed:
// sharpe>=0.5, |mdd|<=20%, trades>=30, returns present). The thin-sample
// badge keys on INDEPENDENT EPISODES once stored (weekly re-entry makes raw
// trades overlap — e.g. 90 trades ≈ 36 episodes); until the trade ledger
// lands, episodes render as 'pending', never a clean state.
export const PUBLISHABLE_MIN_TRADES = 30;

// Derivatives run metrics are stored as FRACTIONS (verified live 2026-10-17:
// returns_oos 0.01783, win_rate 0.533, max_drawdown 0.02499). Deterministic
// per-field conversion — never magnitude-sniffing.
export const fpct = (v, d = 1) => v == null ? null : `${(Number(v) * 100) >= 0 ? '+' : ''}${(Number(v) * 100).toFixed(d)}%`;
export const fpctBare = (v, d = 1) => v == null ? null : `${(Number(v) * 100).toFixed(d)}%`;
// Drawdowns are stored positive; display as a negative (a drawdown is a loss).
export const fmdd = (v, d = 1) => v == null ? null : `−${Math.abs(Number(v) * 100).toFixed(d)}%`;

// Variant display labels (parameters_used.variant: twin / v1 / v2).
export const VARIANT_LABEL = { twin: 'twin', v1: 'V1', v2: 'V2' };
export const variantLabel = (v) => VARIANT_LABEL[(v || '').toLowerCase()] || (v ? String(v).toUpperCase() : '—');

// Named stress windows used for the OOS-coverage note: if a run's OOS window
// overlaps none of these, the page must say so (stress evidence then accrues
// forward only — 2026-10-17 no-paid-data policy).
export const NAMED_STRESS_WINDOWS = [
  { name: 'COVID crash', start: '2020-02-19', end: '2020-04-30' },
  { name: '2022 bear', start: '2022-01-03', end: '2022-10-31' },
];
export function oosCoversNamedStress(oosStart, oosEnd) {
  if (!oosStart || !oosEnd) return false;
  return NAMED_STRESS_WINDOWS.some(w => oosStart <= w.end && oosEnd >= w.start);
}
