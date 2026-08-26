import React from 'react';

// JTCML Quant Workspace design-system primitives.
// Reconstructed from the design bundle (window.JTCMLQuantDesignSystem_a05c87) so the
// ported workspace screens render with the exact tokens defined in index.css.

// ---- formatters (ported from bundle data.js) ----
export const fmtK = (n) => n == null ? '—' : (n < 0 ? '−' : '') + (
  Math.abs(n) >= 1e6 ? `$${(Math.abs(n) / 1e6).toFixed(1)}M`
  : Math.abs(n) >= 1e3 ? `$${(Math.abs(n) / 1e3).toFixed(1)}K`
  : `$${Math.abs(n).toFixed(0)}`);
export const fmtPct = (n) => n == null ? '—' : `${n >= 0 ? '+' : '−'}${Math.abs(n).toFixed(2)}%`;
export const fmtNum = (n, d = 2) => n == null ? '—' : Number(n).toFixed(d);
export const pnlColor = (v) => v == null ? 'var(--pnl-nul)' : v >= 0 ? 'var(--pnl-pos)' : 'var(--pnl-neg)';

const CHIP_COLORS = {
  emerald: { bg: 'rgba(52,211,153,0.15)', fg: '#6ee7b7', ring: 'rgba(52,211,153,0.25)' },
  rose:    { bg: 'rgba(244,63,94,0.15)',  fg: '#fda4af', ring: 'rgba(244,63,94,0.25)' },
  blue:    { bg: 'rgba(59,130,246,0.15)', fg: '#93c5fd', ring: 'rgba(59,130,246,0.25)' },
  amber:   { bg: 'rgba(245,158,11,0.15)', fg: '#fcd34d', ring: 'rgba(245,158,11,0.25)' },
  violet:  { bg: 'rgba(139,92,246,0.15)', fg: '#c4b5fd', ring: 'rgba(139,92,246,0.25)' },
  slate:   { bg: 'rgba(100,116,139,0.22)', fg: '#cbd5e1', ring: 'rgba(100,116,139,0.2)' },
};

export const Chip = ({ color = 'slate', children, style }) => {
  const c = CHIP_COLORS[color] || CHIP_COLORS.slate;
  return (
    <span style={{
      display: 'inline-flex', alignItems: 'center', gap: 4, padding: '1px 6px',
      borderRadius: 'var(--radius-sm)', fontSize: 9, fontWeight: 700, letterSpacing: '0.04em',
      textTransform: 'uppercase', lineHeight: 1.3, whiteSpace: 'nowrap',
      background: c.bg, color: c.fg, boxShadow: `inset 0 0 0 1px ${c.ring}`, ...style,
    }}>{children}</span>
  );
};

export const Pill = ({ color = 'slate', children, style }) => {
  const c = CHIP_COLORS[color] || CHIP_COLORS.slate;
  return (
    <span style={{
      display: 'inline-flex', alignItems: 'center', gap: 5, padding: '3px 10px',
      borderRadius: 999, fontSize: 11, fontWeight: 700, background: c.bg, color: c.fg,
      boxShadow: `inset 0 0 0 1px ${c.ring}`, ...style,
    }}>{children}</span>
  );
};

// value renderer: kind = 'pct' | 'currency' | undefined(plain)
export const NumberCell = ({ value, kind, digits = 2, colored = true, strong = false, style }) => {
  let text;
  if (value == null || (typeof value === 'number' && isNaN(value))) text = '—';
  else if (kind === 'pct') text = fmtPct(value);
  else if (kind === 'currency') text = (value < 0 ? '−' : '') + fmtK(Math.abs(value)).replace('−', '');
  else text = Number(value).toFixed(digits);
  const color = !colored ? (strong ? 'var(--text-strong)' : 'var(--text-secondary)') : pnlColor(value);
  return (
    <span style={{
      fontFamily: 'var(--font-mono)', fontVariantNumeric: 'tabular-nums',
      fontWeight: strong ? 700 : 600, color, ...style,
    }}>{text}</span>
  );
};

export const KpiTile = ({ label, value, sub, pos }) => (
  <div className="jt-surface" style={{ padding: '10px 12px', display: 'flex', flexDirection: 'column', gap: 2, minWidth: 0 }}>
    <span className="jt-label">{label}</span>
    <span style={{ fontFamily: 'var(--font-mono)', fontSize: 15, fontWeight: 700, color: pos == null ? 'var(--text-strong)' : (pos ? 'var(--pnl-pos)' : 'var(--pnl-neg)'), lineHeight: 1.1 }}>{value}</span>
    {sub != null && <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-muted)' }}>{sub}</span>}
  </div>
);

const BTN_VARIANTS = {
  primary: { bg: 'var(--primary)', fg: '#fff', ring: 'transparent' },
  ghost:   { bg: 'transparent', fg: 'var(--text-secondary)', ring: 'var(--border-strong)' },
  danger:  { bg: 'var(--signal-sell)', fg: '#fff', ring: 'transparent' },
  buy:     { bg: 'var(--signal-buy)', fg: '#fff', ring: 'transparent' },
  sell:    { bg: 'var(--signal-sell)', fg: '#fff', ring: 'transparent' },
};

export const Button = ({ variant = 'ghost', size = 'sm', disabled, onClick, children, style }) => {
  const v = BTN_VARIANTS[variant] || BTN_VARIANTS.ghost;
  const pad = size === 'md' ? '6px 12px' : '4px 9px';
  const fs = size === 'md' ? 11 : 10;
  return (
    <button onClick={onClick} disabled={disabled} style={{
      display: 'inline-flex', alignItems: 'center', justifyContent: 'center', gap: 5,
      padding: pad, fontSize: fs, fontWeight: 700, borderRadius: 'var(--radius-md)',
      border: 'none', cursor: disabled ? 'not-allowed' : 'pointer', background: v.bg, color: v.fg,
      boxShadow: v.ring === 'transparent' ? 'none' : `inset 0 0 0 1px ${v.ring}`,
      opacity: disabled ? 0.4 : 1, transition: 'background .15s, opacity .15s', whiteSpace: 'nowrap', ...style,
    }}>{children}</button>
  );
};

const MODE_STYLE = {
  LIVE_TRADING:   { label: 'LIVE', color: '#fb7185', bg: 'rgba(244,63,94,0.15)', ring: 'rgba(244,63,94,0.4)', pulse: true },
  PAPER_TRADING:  { label: 'PAPER', color: '#fcd34d', bg: 'rgba(245,158,11,0.15)', ring: 'rgba(245,158,11,0.35)' },
  // UAT = broker rehearsal (paper money). Neutral slate per palette rule —
  // no severity/sign/link meaning to carry.
  PAPER_UAT:      { label: 'UAT', color: '#cbd5e1', bg: 'rgba(100,116,139,0.22)', ring: 'rgba(100,116,139,0.4)' },
  SIMULATION:     { label: 'SIM', color: '#93c5fd', bg: 'rgba(59,130,246,0.15)', ring: 'rgba(59,130,246,0.35)' },
  PAPER:          { label: 'PAPER', color: '#fcd34d', bg: 'rgba(245,158,11,0.15)', ring: 'rgba(245,158,11,0.35)' },
  SIM:            { label: 'SIM', color: '#93c5fd', bg: 'rgba(59,130,246,0.15)', ring: 'rgba(59,130,246,0.35)' },
};

export const ModeBadge = ({ mode = 'SIMULATION', size = 'sm' }) => {
  const m = MODE_STYLE[mode] || MODE_STYLE.SIMULATION;
  const fs = size === 'md' ? 11 : 9;
  return (
    <span style={{
      display: 'inline-flex', alignItems: 'center', gap: 4, padding: size === 'md' ? '3px 9px' : '2px 7px',
      borderRadius: 'var(--radius-sm)', fontSize: fs, fontWeight: 800, letterSpacing: '0.06em',
      background: m.bg, color: m.color, boxShadow: `inset 0 0 0 1px ${m.ring}`,
    }}>
      <span style={{ width: 5, height: 5, borderRadius: '50%', background: m.color, animation: m.pulse ? 'jt-pulse-dot 1.4s infinite' : 'none' }} />
      {m.label}
    </span>
  );
};

const DOT_COLOR = { live: 'var(--signal-buy)', idle: 'var(--signal-hold)', stale: 'var(--signal-warning)', down: 'var(--signal-sell)' };

export const StatusDot = ({ status = 'idle', pulse, label, style }) => {
  const color = DOT_COLOR[status] || DOT_COLOR.idle;
  return (
    <span style={{ display: 'inline-flex', alignItems: 'center', gap: 6, ...style }}>
      <span style={{ width: 7, height: 7, borderRadius: '50%', background: color, flex: 'none', boxShadow: status === 'live' ? `0 0 6px ${color}` : 'none', animation: pulse ? 'jt-pulse-dot 1.6s infinite' : 'none' }} />
      {label && <span style={{ fontSize: 9, fontWeight: 700, letterSpacing: '0.04em', textTransform: 'uppercase', color: 'var(--text-muted)' }}>{label}</span>}
    </span>
  );
};

export const Kbd = ({ children }) => (
  <span style={{
    display: 'inline-flex', alignItems: 'center', justifyContent: 'center', minWidth: 14,
    padding: '0 4px', height: 14, borderRadius: 3, fontFamily: 'var(--font-mono)', fontSize: 9,
    color: 'var(--text-muted)', background: 'rgba(15,23,42,0.8)', border: '1px solid var(--border-glass)', lineHeight: 1,
  }}>{children}</span>
);

const inputBase = (size) => ({
  width: '100%', boxSizing: 'border-box', padding: size === 'sm' ? '5px 8px' : '7px 10px',
  fontSize: size === 'sm' ? 11 : 12, fontFamily: 'var(--font-mono)', color: 'var(--text-strong)',
  background: 'var(--bg-input)', border: '1px solid var(--border-glass)', borderRadius: 'var(--radius-sm)', outline: 'none',
});

export const Input = ({ label, size = 'sm', wrapStyle, ...props }) => (
  <div style={wrapStyle}>
    {label && <label style={{ display: 'block', marginBottom: 3, fontSize: 8, fontWeight: 600, letterSpacing: '0.05em', textTransform: 'uppercase', color: 'var(--text-muted)' }}>{label}</label>}
    <input {...props} style={inputBase(size)} />
  </div>
);

export const Select = ({ label, options = [], size = 'sm', wrapStyle, ...props }) => (
  <div style={wrapStyle}>
    {label && <label style={{ display: 'block', marginBottom: 3, fontSize: 8, fontWeight: 600, letterSpacing: '0.05em', textTransform: 'uppercase', color: 'var(--text-muted)' }}>{label}</label>}
    <select {...props} style={inputBase(size)}>
      {options.map(o => <option key={o} value={o}>{o}</option>)}
    </select>
  </div>
);
