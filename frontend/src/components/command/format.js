// Command center — date/time and signed-number formatting helpers.
// Plain .js: impure clock reads live HERE (outside component files) so the
// react-hooks/purity rule is satisfied at render sites.

import { fmtK, fmtKCcy } from '../../utils';

// Absolute date only (YYYY-MM-DD); exact UTC timestamps ride in tooltips.
export const fmtDate = (v) => {
  if (!v) return null;
  const s = String(v);
  return s.length >= 10 ? s.slice(0, 10) : s;
};

export const tsTip = (v) => {
  if (!v) return '';
  const s = String(v);
  const norm = s.includes('T') ? s : s.replace(' ', 'T');
  const z = /([zZ]|[+-]\d{2}:?\d{2})$/.test(norm) ? norm : `${norm}Z`;
  const d = new Date(z);
  return isNaN(d) ? s : `${d.toISOString().slice(0, 19).replace('T', ' ')} UTC`;
};

export const daysHeld = (entry, now = Date.now()) => {
  if (!entry) return null;
  const s = String(entry);
  const d = new Date(s.length === 10 ? `${s}T00:00:00Z` : (s.includes('T') ? s : `${s.replace(' ', 'T')}Z`));
  if (isNaN(d)) return null;
  return Math.max(0, Math.floor((now - d.getTime()) / 86400000));
};

// Signed formatters (explicit sign for P&L values).
export const sK = (v) => `${v >= 0 ? '+' : ''}${fmtK(v)}`;
export const sCcy = (v, ccy) => `${v >= 0 ? '+' : ''}${fmtKCcy(v, ccy)}`;

export const fmtConf = (c) => c == null ? '—' : c >= 0.99995 ? '>99.99%' : `${(c * 100).toFixed(1)}%`;
