// Pure News feed tier logic, kept out of NewsTab.jsx so Fast Refresh can
// hot-swap the component module and tests can cover the tier invariants.

export const TIER_BORDER = {
  HIGH: { bullish: 'border-teal-400', bearish: 'border-rose-400', neutral: 'border-slate-500' },
  MEDIUM: { bullish: 'border-slate-600', bearish: 'border-slate-600', neutral: 'border-slate-600' },
  LOW: null,
};

export const TIER_SCORE_CL = { HIGH: 'text-white', MEDIUM: 'text-slate-400', LOW: 'text-slate-600' };
export const TIER_HEAD_CL = {
  HIGH: 'text-[15px] font-medium text-white',
  MEDIUM: 'text-[13px] font-normal text-slate-200',
  LOW: 'text-[13px] font-normal text-slate-500',
};

const HIGH_TIER_FLOOR = 3;
const HIGH_TIER_CAP = 4;

const dirKeyOf = (d) => {
  const v = (d || '').toLowerCase();
  return v.startsWith('bull') ? 'bullish' : v.startsWith('bear') ? 'bearish' : 'neutral';
};

export const tierBorderFor = (tier, direction) => TIER_BORDER[tier]?.[dirKeyOf(direction)] || null;

const tierScore = (c) => {
  const n = Number(c?.impact_score);
  return Number.isFinite(n) ? n : -Infinity;
};

const resolveTierBoundary = (rows, cut, minCount = 0) => {
  if (cut <= 0 || cut >= rows.length) return cut;
  const boundary = tierScore(rows[cut - 1]);
  if (boundary !== tierScore(rows[cut])) return cut;
  let start = cut - 1;
  while (start > 0 && tierScore(rows[start - 1]) === boundary) start--;
  let end = cut;
  while (end < rows.length && tierScore(rows[end]) === boundary) end++;
  const include = end;
  const exclude = start;
  if (exclude < minCount) return include;
  return Math.abs(include - cut) <= Math.abs(exclude - cut) ? include : exclude;
};

export const tierCutoffsFor = (rows) => {
  const n = rows.length;
  const hiTarget = Math.min(n, Math.max(HIGH_TIER_FLOOR, Math.min(HIGH_TIER_CAP, Math.round(n * 0.10))));
  const hi = resolveTierBoundary(rows, hiTarget, Math.min(HIGH_TIER_FLOOR, n));
  const medEnd = resolveTierBoundary(rows, hi + Math.round(n * 0.30), hi);
  return { hi, medEnd };
};
