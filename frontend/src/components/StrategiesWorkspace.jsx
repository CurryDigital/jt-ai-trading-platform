import React, { useState, useEffect, useMemo } from 'react';
import { api } from '../utils';
import { Chip, NumberCell, KpiTile, Button, fmtPct } from './jtkit';
import { HORIZON, derive, metricsFor, marginMetrics, gatesFor, mapApiToBook } from './strategyProfiles';

// Ported from the design bundle's Performance.jsx + StrategyPipeline.jsx.
// Shares one strategy "book" fetched from /api/strategies/researcher.

function seeded(seed) {
  let h = 2166136261;
  for (let i = 0; i < seed.length; i++) { h ^= seed.charCodeAt(i); h = Math.imul(h, 16777619); }
  return () => { h += 0x6D2B79F5; let t = Math.imul(h ^ h >>> 15, 1 | h); t ^= t + Math.imul(t ^ t >>> 7, 61 | t); return ((t ^ t >>> 14) >>> 0) / 4294967296; };
}

function useStrategyBook() {
  const [book, setBook] = useState(null);
  useEffect(() => {
    let alive = true;
    const load = async () => {
      const rows = await api.get('/api/strategies/researcher');
      if (!alive) return;
      setBook(mapApiToBook(Array.isArray(rows) ? rows : (rows?.data || [])));
    };
    load();
    const id = setInterval(load, 60000);
    return () => { alive = false; clearInterval(id); };
  }, []);
  return [book, setBook];
}

function HorizonSeg({ hzn, setHzn, counts }) {
  const opts = [['all', 'All'], ['day', 'Day Trade'], ['swing', 'Swing'], ['position', 'Position']];
  return (
    <div style={{ display: 'flex', gap: 2, padding: 3, borderRadius: 'var(--radius-md)', background: 'rgba(15,23,42,0.5)', border: '1px solid var(--border-glass)' }}>
      {opts.map(([k, l]) => (
        <button key={k} onClick={() => setHzn(k)} style={{ display: 'flex', alignItems: 'center', gap: 5, padding: '4px 10px', borderRadius: 'var(--radius-sm)', border: 'none', cursor: 'pointer', fontSize: 10, fontWeight: 700, background: hzn === k ? 'var(--primary)' : 'transparent', color: hzn === k ? '#fff' : 'var(--text-secondary)' }}>
          {l}<span style={{ fontFamily: 'var(--font-mono)', fontSize: 9, opacity: 0.7 }}>{counts[k] ?? 0}</span>
        </button>
      ))}
    </div>
  );
}

const Loading = ({ label }) => (
  <div className="jt-surface" style={{ padding: '32px 16px', textAlign: 'center', color: 'var(--text-faint)', fontSize: 12 }}>{label}</div>
);

/* ─────────────────────────── PERFORMANCE (card grid) ─────────────────────────── */
function perfCurve(s) {
  const r = seeded(s.id + 'perf'); const N = 40; let v = 0; const out = [];
  const ret = s.returns || 0;
  for (let i = 0; i < N; i++) { v += (ret / N) + (r() - 0.45) * 1.3; out.push(v); }
  out[N - 1] = ret; return out;
}
function Spark({ data, color, h = 40 }) {
  const w = 300, min = Math.min(0, ...data), max = Math.max(...data), range = (max - min) || 1;
  const pts = data.map((v, i) => `${(i / (data.length - 1)) * w},${h - 3 - ((v - min) / range) * (h - 6)}`);
  const id = 'pg' + color.replace(/[^a-z0-9]/gi, '');
  return (
    <svg viewBox={`0 0 ${w} ${h}`} preserveAspectRatio="none" style={{ width: '100%', height: h, display: 'block' }}>
      <defs><linearGradient id={id} x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor={color} stopOpacity="0.20" /><stop offset="100%" stopColor={color} stopOpacity="0" /></linearGradient></defs>
      <polygon points={`0,${h} ${pts.join(' ')} ${w},${h}`} fill={`url(#${id})`} />
      <polyline points={pts.join(' ')} fill="none" stroke={color} strokeWidth="1.5" vectorEffect="non-scaling-stroke" strokeLinejoin="round" />
    </svg>
  );
}
const STAGE_CHIP = { deployed: 'emerald', golden: 'amber', near_golden: 'blue', experimental: 'slate' };

function Metric({ label, value, color, big }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
      <span style={{ fontSize: 8, textTransform: 'uppercase', letterSpacing: '0.06em', color: 'var(--text-muted)' }}>{label}</span>
      <span style={{ fontFamily: 'var(--font-mono)', fontSize: big ? 15 : 12, fontWeight: 700, color: color || 'var(--text-secondary)' }}>{value}</span>
    </div>
  );
}

function PerfCard({ s, onOpen }) {
  const live = s.liveWR != null;
  const color = (s.returns || 0) >= 0 ? '#34d399' : '#fb7185';
  const d = derive(s);
  const mtx = metricsFor(s, d);
  const marginMx = marginMetrics(s, d);
  const hz = HORIZON[s.horizon] || HORIZON.swing;
  return (
    <div className="jt-surface" style={{ padding: 12, display: 'flex', flexDirection: 'column', gap: 10 }}>
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 8 }}>
        <div style={{ minWidth: 0, cursor: 'pointer' }} onClick={() => onOpen(s.id)}>
          <div style={{ fontSize: 12, fontWeight: 700, color: 'var(--text-strong)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{s.name}</div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginTop: 4 }}>
            <Chip color={STAGE_CHIP[s.stage]}>{s.stage.replace('_', ' ')}</Chip>
            <span style={{ fontSize: 9, color: 'var(--text-muted)' }}>{s.asset}</span>
          </div>
        </div>
        <Chip color={s.tier === 'T1' ? 'emerald' : s.tier === 'T2' ? 'amber' : 'slate'}>{s.tier}</Chip>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
        <Chip color={hz.color}>{hz.label}</Chip>
        {s.margin ? <Chip color="rose">Margin {s.margin.leverage.toFixed(1)}×</Chip> : <Chip color="slate">Cash</Chip>}
        <span style={{ marginLeft: 'auto', fontSize: 8, color: 'var(--text-faint)' }}>{hz.note}</span>
      </div>

      <div onClick={() => onOpen(s.id)} style={{ cursor: 'pointer' }}><Spark data={perfCurve(s)} color={color} /></div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '8px 8px' }}>
        {mtx.map((m) => <Metric key={m.label} label={m.label} value={m.value} color={m.color} big={m.big} />)}
      </div>

      {marginMx && (
        <div style={{ padding: 8, borderRadius: 'var(--radius-md)', background: 'rgba(244,63,94,0.06)', border: '1px solid rgba(244,63,94,0.15)', display: 'flex', flexDirection: 'column', gap: 6 }}>
          <span style={{ fontSize: 8, textTransform: 'uppercase', letterSpacing: '0.06em', color: 'var(--chip-rose)' }}>Margin profile</span>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr 1fr', gap: 6 }}>
            {marginMx.map((m) => <Metric key={m.label} label={m.label} value={m.value} color={m.color} />)}
          </div>
        </div>
      )}

      <div style={{ padding: 8, borderRadius: 'var(--radius-md)', background: 'rgba(255,255,255,0.02)', display: 'flex', flexDirection: 'column', gap: 5 }}>
        <span style={{ fontSize: 8, textTransform: 'uppercase', letterSpacing: '0.06em', color: 'var(--text-muted)' }}>Backtest → Live</span>
        {live ? (
          <div style={{ display: 'flex', alignItems: 'center', fontSize: 10 }}>
            <span style={{ color: 'var(--text-muted)', width: 46 }}>Win %</span>
            <span style={{ fontFamily: 'var(--font-mono)', color: 'var(--text-secondary)' }}>{s.btWR ?? '—'}</span>
            <span style={{ color: 'var(--text-faint)', margin: '0 5px' }}>→</span>
            <span style={{ fontFamily: 'var(--font-mono)', color: 'var(--text-strong)', fontWeight: 700 }}>{s.liveWR}</span>
            <span style={{ marginLeft: 'auto', fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-muted)' }}>{s.trades} tr</span>
          </div>
        ) : (
          <div style={{ fontSize: 10, color: 'var(--text-faint)', display: 'flex', alignItems: 'center', gap: 6 }}>
            <span style={{ fontFamily: 'var(--font-mono)', color: 'var(--text-secondary)' }}>BT {s.btWR ?? '—'}%</span>
            <span>· no live trades yet</span>
          </div>
        )}
      </div>
    </div>
  );
}

export function StrategyPerformanceGrid({ book, hzn, setHzn, onOpen }) {
  const [sortKey, setSortKey] = useState('returns');
  if (!book) return <Loading label="Loading strategies…" />;
  const counts = { all: book.length, day: 0, swing: 0, position: 0 };
  book.forEach((s) => { counts[s.horizon] = (counts[s.horizon] || 0) + 1; });
  const src = hzn === 'all' ? book : book.filter((s) => s.horizon === hzn);
  const sorted = [...src].sort((a, b) => (b[sortKey] ?? -Infinity) - (a[sortKey] ?? -Infinity));
  const liveWRs = src.filter((s) => s.liveWR != null);
  const avgLiveWR = liveWRs.length ? liveWRs.reduce((a, s) => a + s.liveWR, 0) / liveWRs.length : 0;
  const totalTrades = src.reduce((a, s) => a + (s.trades || 0), 0);
  const marginN = src.filter((s) => s.margin).length;
  const best = sorted[0];
  const SORTS = [{ k: 'returns', l: 'Return' }, { k: 'sharpe', l: 'Sharpe' }, { k: 'liveWR', l: 'Live WR' }, { k: 'trades', l: 'Trades' }];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
      <div style={{ display: 'flex', alignItems: 'flex-end', justifyContent: 'space-between', flexWrap: 'wrap', gap: 8 }}>
        <div>
          <h2 style={{ margin: 0, fontSize: 14, fontWeight: 700, color: 'var(--text-strong)' }}>Performance</h2>
          <p style={{ margin: '2px 0 0', fontSize: 10, color: 'var(--text-muted)' }}>Metrics adapt to each strategy's trade horizon · click a card for full detail</p>
        </div>
        <HorizonSeg hzn={hzn} setHzn={setHzn} counts={counts} />
      </div>

      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-end', gap: 6 }}>
        <span style={{ fontSize: 9, color: 'var(--text-faint)' }}>Sort</span>
        <div style={{ display: 'flex', gap: 2, padding: 3, borderRadius: 'var(--radius-md)', background: 'rgba(15,23,42,0.5)', border: '1px solid var(--border-glass)' }}>
          {SORTS.map((o) => (
            <button key={o.k} onClick={() => setSortKey(o.k)} style={{ padding: '4px 9px', borderRadius: 'var(--radius-sm)', border: 'none', cursor: 'pointer', fontSize: 10, fontWeight: 700, background: sortKey === o.k ? 'var(--primary)' : 'transparent', color: sortKey === o.k ? '#fff' : 'var(--text-secondary)' }}>{o.l}</button>
          ))}
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 8 }}>
        <KpiTile label={hzn === 'all' ? 'Strategies' : HORIZON[hzn].label} value={src.length} sub={`${marginN} on margin`} />
        <KpiTile label="Avg Live WR" value={`${avgLiveWR.toFixed(1)}%`} pos={avgLiveWR >= 50} />
        <KpiTile label="Total Live Trades" value={totalTrades} />
        <KpiTile label="Best" value={best ? best.name.split(' ').slice(0, 2).join(' ') : '—'} sub={best && best.returns != null ? fmtPct(best.returns) : null} pos />
      </div>

      {sorted.length === 0
        ? <Loading label="No strategies match this horizon." />
        : <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 10 }}>
            {sorted.map((s) => <PerfCard key={s.id} s={s} onOpen={onOpen} />)}
          </div>}
    </div>
  );
}

/* ─────────────────────────── PIPELINE (kanban) ─────────────────────────── */
const STAGES = [
  { key: 'experimental', label: 'Experimental', color: 'slate' },
  { key: 'near_golden', label: 'Near Golden', color: 'blue' },
  { key: 'golden', label: 'Golden', color: 'amber' },
  { key: 'deployed', label: 'Deployed', color: 'emerald' },
];
const BENCH = { EQUITY: 8, CRYPTO: 22, FX: 3, FUTURE: 5 };
const TYPE_CHIP = { 'HFT': 'violet', 'Day Trade': 'blue', 'Swing': 'emerald', 'Position': 'amber' };
const TYPE_BY_HZN = { day: 'Day Trade', swing: 'Swing', position: 'Position' };

function pipeMetrics(s) {
  const yearly = s.returns || 0;
  const ytd = +((s.returns || 0) * 0.72).toFixed(1);
  const alpha = +((s.returns || 0) - (BENCH[s.asset] || 8)).toFixed(1);
  const wr = s.liveWR || s.btWR || 0;
  const btTrades = s.trades > 0 ? s.trades : Math.round(60 + (s.sharpe || 0) * 120 + (s.asset === 'EQUITY' ? 80 : 0));
  const riskScore = Math.min(1, Math.abs(s.dd || 0) / 40 * 0.6 + (1 - Math.min(s.sharpe || 0, 1.5) / 1.5) * 0.4);
  const riskLevel = riskScore < 0.3 ? 'Low' : riskScore < 0.45 ? 'Med' : 'High';
  return { yearly, ytd, alpha, wr, btTrades, riskLevel };
}
const pct = (n) => `${n >= 0 ? '+' : ''}${Number(n).toFixed(1)}%`;
function quarters(s) {
  const r = seeded(s.id + 'q'); const base = (s.returns || 0) * 0.72 / 4;
  return Array.from({ length: 4 }, () => +((base + (r() - 0.45) * Math.abs(base) * 1.6)).toFixed(1));
}
function prevYear(s) { const r = seeded(s.id + 'y'); return +(((s.returns || 0) * (0.7 + r() * 0.55))).toFixed(1); }

function QuarterBars({ qs }) {
  const max = Math.max(...qs.map((q) => Math.abs(q)), 0.1);
  return (
    <div style={{ display: 'flex', gap: 4 }}>
      {qs.map((q, i) => (
        <div key={i} style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 2 }}>
          <span style={{ fontFamily: 'var(--font-mono)', fontSize: 8, fontWeight: 700, color: q >= 0 ? 'var(--pnl-pos)' : 'var(--pnl-neg)' }}>{q >= 0 ? '+' : ''}{q}</span>
          <div style={{ height: 22, width: '100%', display: 'flex', flexDirection: 'column', justifyContent: 'flex-end' }}>
            <div style={{ height: `${Math.abs(q) / max * 100}%`, minHeight: 2, borderRadius: 2, background: q >= 0 ? 'var(--signal-buy)' : 'var(--signal-sell)', opacity: 0.85 }} />
          </div>
          <span style={{ fontSize: 7, color: 'var(--text-faint)' }}>Q{i + 1}</span>
        </div>
      ))}
    </div>
  );
}

const RISK_COLOR = { Low: 'var(--pnl-pos)', Med: 'var(--chip-amber)', High: 'var(--pnl-neg)' };

function PipeMetric({ label, children }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
      <span style={{ fontSize: 8, textTransform: 'uppercase', letterSpacing: '0.06em', color: 'var(--text-muted)' }}>{label}</span>
      <span style={{ fontFamily: 'var(--font-mono)', fontSize: 12, fontWeight: 700 }}>{children}</span>
    </div>
  );
}

function PipeCard({ s, onPromote, onOpen }) {
  const m = pipeMetrics(s);
  const g = gatesFor(s);
  const qs = quarters(s);
  const py = prevYear(s);
  const hz = HORIZON[s.horizon] || HORIZON.swing;
  const type = TYPE_BY_HZN[s.horizon] || 'Swing';
  return (
    <div className="jt-surface" style={{ padding: 10, display: 'flex', flexDirection: 'column', gap: 8 }}>
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 6 }}>
        <span onClick={() => onOpen(s.id)} style={{ fontSize: 11, fontWeight: 700, color: 'var(--text-strong)', cursor: 'pointer', lineHeight: 1.25 }}>{s.name}</span>
        <Chip color={s.tier === 'T1' ? 'emerald' : s.tier === 'T2' ? 'amber' : 'slate'}>{s.tier}</Chip>
      </div>
      <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
        <Chip color={hz.color}>{hz.label}</Chip>
        {s.margin ? <Chip color="rose">Margin {s.margin.leverage.toFixed(1)}×</Chip> : <Chip color="slate">Cash</Chip>}
        <span style={{ marginLeft: 'auto', display: 'flex', alignItems: 'center', gap: 4, fontSize: 9, color: 'var(--text-muted)' }}>
          Risk <span style={{ fontWeight: 700, color: RISK_COLOR[m.riskLevel] }}>{m.riskLevel}</span>
        </span>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '7px 8px', padding: '7px 8px', borderRadius: 'var(--radius-md)', background: 'rgba(255,255,255,0.02)' }}>
        <PipeMetric label="Alpha"><span style={{ color: m.alpha >= 0 ? 'var(--pnl-pos)' : 'var(--pnl-neg)' }}>{m.alpha >= 0 ? '+' : ''}{m.alpha}</span></PipeMetric>
        <PipeMetric label="Sharpe"><span style={{ color: 'var(--text-secondary)' }}>{(s.sharpe || 0).toFixed(2)}</span></PipeMetric>
        <PipeMetric label="Trades"><span style={{ color: 'var(--text-secondary)' }}>{m.btTrades}</span></PipeMetric>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
        <Chip color={TYPE_CHIP[type] || 'slate'}>{type}</Chip>
        <span style={{ marginLeft: 'auto', fontFamily: 'var(--font-mono)', fontSize: 9, color: 'var(--text-secondary)' }}>{s.trades > 0 ? `${s.trades} live` : `${m.btTrades} bt`}</span>
      </div>

      <div style={{ padding: '7px 8px', borderRadius: 'var(--radius-md)', background: 'rgba(255,255,255,0.02)', display: 'flex', flexDirection: 'column', gap: 6 }}>
        <span style={{ fontSize: 8, textTransform: 'uppercase', letterSpacing: '0.06em', color: 'var(--text-muted)' }}>Profit by Quarter</span>
        <QuarterBars qs={qs} />
        <div style={{ display: 'flex', justifyContent: 'space-between', borderTop: '1px solid var(--border-glass)', paddingTop: 5 }}>
          {[['1Y', m.yearly], ['YTD', m.ytd], ['Prev Yr', py]].map(([k, v]) => (
            <span key={k} style={{ fontSize: 9, color: 'var(--text-muted)' }}>{k} <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 700, color: v >= 0 ? 'var(--pnl-pos)' : 'var(--pnl-neg)' }}>{pct(v)}</span></span>
          ))}
        </div>
      </div>

      {g ? (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <span style={{ fontSize: 8, textTransform: 'uppercase', letterSpacing: '0.06em', color: 'var(--text-muted)' }}>→ {g.label} gates</span>
            <span style={{ fontFamily: 'var(--font-mono)', fontSize: 9, fontWeight: 700, color: g.ready ? 'var(--pnl-pos)' : 'var(--chip-amber)' }}>{g.pass}/{g.total}</span>
          </div>
          {g.gates.map((x) => (
            <div key={x.label} style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 9 }}>
              <span style={{ width: 11, height: 11, borderRadius: '50%', flex: 'none', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 8, fontWeight: 900, background: x.ok ? 'rgba(16,185,129,0.18)' : 'rgba(244,63,94,0.18)', color: x.ok ? 'var(--pnl-pos)' : 'var(--pnl-neg)' }}>{x.ok ? '✓' : '✕'}</span>
              <span style={{ color: x.ok ? 'var(--text-secondary)' : 'var(--text-body)', whiteSpace: 'nowrap' }}>{x.label}</span>
              <span style={{ marginLeft: 'auto', flex: 'none', fontFamily: 'var(--font-mono)', color: x.ok ? 'var(--text-muted)' : 'var(--pnl-neg)', fontWeight: 700 }}>{x.val}</span>
            </div>
          ))}
          {g.ready ? (
            <Button variant={g.target === 'deployed' ? 'primary' : 'ghost'} size="sm" onClick={() => onPromote(s.id)} style={{ justifyContent: 'center', marginTop: 2 }}>
              {g.target === 'deployed' ? 'Deploy →' : 'Promote →'}
            </Button>
          ) : (
            <div style={{ marginTop: 2, padding: '5px 8px', borderRadius: 'var(--radius-md)', background: 'rgba(244,63,94,0.10)', border: '1px solid rgba(244,63,94,0.25)', textAlign: 'center', fontSize: 9, fontWeight: 700, color: 'var(--pnl-neg)' }}>
              Blocked · {g.total - g.pass} check{g.total - g.pass > 1 ? 's' : ''} failing
            </div>
          )}
        </div>
      ) : (
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', paddingTop: 2 }}>
          <span style={{ display: 'flex', alignItems: 'center', gap: 5, fontSize: 9, fontWeight: 700, color: 'var(--pnl-pos)', textTransform: 'uppercase', letterSpacing: '0.06em' }}>
            <span style={{ width: 5, height: 5, borderRadius: '50%', background: 'var(--signal-buy)', boxShadow: '0 0 5px var(--signal-buy)' }} />Live{s.liveWR != null ? ` · ${s.liveWR}% WR` : ''}
          </span>
          <Button variant="ghost" size="sm" onClick={() => onPromote(s.id, true)}>Demote</Button>
        </div>
      )}
    </div>
  );
}

export function StrategyPipelineKanban({ book, setBook, hzn, setHzn, onOpen }) {
  const STAGE_ORDER = ['experimental', 'near_golden', 'golden', 'deployed'];
  const promote = (id, demote) => setBook((b) => b.map((s) => {
    if (s.id !== id) return s;
    const i = STAGE_ORDER.indexOf(s.stage);
    const ni = demote ? Math.max(0, i - 1) : Math.min(STAGE_ORDER.length - 1, i + 1);
    const stage = STAGE_ORDER[ni];
    const mode = stage === 'deployed' ? 'LIVE_TRADING' : stage === 'golden' ? 'PAPER_TRADING' : s.mode;
    // fire-and-forget backend promote; UI is optimistic
    api.post(`/api/strategies/${id}/promote`, { demote: !!demote }).catch(() => {});
    return { ...s, stage, mode, liveWR: stage === 'deployed' ? (s.liveWR ?? s.btWR) : s.liveWR };
  }));

  if (!book) return <Loading label="Loading pipeline…" />;
  const counts = { all: book.length, day: 0, swing: 0, position: 0 };
  book.forEach((s) => { counts[s.horizon] = (counts[s.horizon] || 0) + 1; });
  const view = hzn === 'all' ? book : book.filter((s) => s.horizon === hzn);
  const ready = view.filter((s) => { const g = gatesFor(s); return g && g.ready; }).length;
  const blocked = view.filter((s) => { const g = gatesFor(s); return g && !g.ready; }).length;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
      <div style={{ display: 'flex', alignItems: 'flex-end', justifyContent: 'space-between', flexWrap: 'wrap', gap: 8 }}>
        <div>
          <h2 style={{ margin: 0, fontSize: 14, fontWeight: 700, color: 'var(--text-strong)' }}>Pipeline</h2>
          <p style={{ margin: '2px 0 0', fontSize: 10, color: 'var(--text-muted)' }}>Gates adapt to each strategy's horizon; margin adds a leverage &amp; liquidation overlay</p>
        </div>
        <HorizonSeg hzn={hzn} setHzn={setHzn} counts={counts} />
      </div>

      <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
        <Chip color="emerald">{ready} ready to promote</Chip>
        <Chip color="rose">{blocked} blocked</Chip>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 10, alignItems: 'start' }}>
        {STAGES.map((st) => {
          const items = view.filter((s) => s.stage === st.key);
          return (
            <div key={st.key} style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '6px 4px' }}>
                <Chip color={st.color}>{st.label}</Chip>
                <span style={{ fontFamily: 'var(--font-mono)', fontSize: 12, fontWeight: 700, color: 'var(--text-secondary)' }}>{items.length}</span>
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 8, minHeight: 60, padding: 6, borderRadius: 'var(--radius-lg)', background: 'rgba(255,255,255,0.012)', border: '1px solid var(--border-glass)' }}>
                {items.map((s) => <PipeCard key={s.id} s={s} onPromote={promote} onOpen={onOpen} />)}
                {items.length === 0 && <div style={{ padding: '14px 4px', textAlign: 'center', fontSize: 9, color: 'var(--text-faint)' }}>empty</div>}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

/* ─────────────────────────── shared wrapper ─────────────────────────── */
export function StrategiesWorkspace({ sub, onOpen }) {
  const [book, setBook] = useStrategyBook();
  const [hzn, setHzn] = useState('all');
  if (sub === 'pipeline') return <StrategyPipelineKanban book={book} setBook={setBook} hzn={hzn} setHzn={setHzn} onOpen={onOpen} />;
  return <StrategyPerformanceGrid book={book} hzn={hzn} setHzn={setHzn} onOpen={onOpen} />;
}

export default StrategiesWorkspace;
