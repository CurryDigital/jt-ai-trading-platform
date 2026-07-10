import React, { useState, useEffect, useCallback } from 'react';
import { api, usePoll } from '../utils';
import { Chip, KpiTile, Button, ModeBadge, fmtPct } from './jtkit';
import { HORIZON, mapApiToBook } from './strategyProfiles';

// Strategies workspace — Performance card grid + Pipeline mode-ladder board.
// Every number rendered here comes from /api/strategies/researcher (no synthetic
// metrics), and promote/demote goes through the backend's real gate engine:
//   POST /api/strategies/{id}/promote/check  → gates preview
//   POST /api/strategies/{id}/promote        → apply (LIVE needs typed phrase)

const MODE_LABEL = { SIMULATION: 'Simulation', PAPER_TRADING: 'Paper', LIVE_TRADING: 'Live' };
const NEXT_MODE = { SIMULATION: 'PAPER_TRADING', PAPER_TRADING: 'LIVE_TRADING' };
const PREV_MODE = { LIVE_TRADING: 'PAPER_TRADING', PAPER_TRADING: 'SIMULATION' };
const STAGE_CHIP = { deployed: 'emerald', golden: 'amber', near_golden: 'blue', experimental: 'slate' };

function useStrategyBook() {
  const [book, setBook] = useState(null);
  const [error, setError] = useState(false);
  const load = useCallback(async (fresh = false) => {
    // fresh=1 bypasses the backend's 15s researcher cache — used right after a
    // confirmed promote so the new mode is visible immediately.
    const rows = await api.get(`/api/strategies/researcher${fresh ? '?fresh=1' : ''}`);
    if (rows == null) { setError(true); return; }
    setError(false);
    const raw = Array.isArray(rows) ? rows : (rows?.strategies || rows?.data || []);
    setBook(mapApiToBook(raw));
  }, []);
  usePoll(load, 60000);
  const reload = useCallback(() => load(true), [load]);
  return { book, reload, error };
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

const Placeholder = ({ label, hint }) => (
  <div className="jt-surface" style={{ padding: '32px 16px', textAlign: 'center' }}>
    <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>{label}</div>
    {hint && <div style={{ fontSize: 10, color: 'var(--text-faint)', marginTop: 6 }}>{hint}</div>}
  </div>
);

function Metric({ label, value, color, big }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
      <span style={{ fontSize: 8, textTransform: 'uppercase', letterSpacing: '0.06em', color: 'var(--text-muted)' }}>{label}</span>
      <span style={{ fontFamily: 'var(--font-mono)', fontSize: big ? 15 : 12, fontWeight: 700, color: color || 'var(--text-secondary)' }}>{value}</span>
    </div>
  );
}

// Real annual backtest returns from gold.strategy_backtest_runs (via the API's
// yearly_backtest map) — replaces the old fabricated quarter bars.
function YearlyBars({ yearly }) {
  const years = Object.keys(yearly || {}).sort();
  const entries = years.map((y) => ({ y, v: yearly[y]?.return_pct })).filter((e) => e.v != null).map((e) => ({ ...e, v: Number(e.v) * 100 }));
  if (!entries.length) {
    return <div style={{ padding: '6px 0', fontSize: 9, color: 'var(--text-faint)', textAlign: 'center' }}>No annual backtest data yet</div>;
  }
  const max = Math.max(...entries.map((e) => Math.abs(e.v)), 0.1);
  return (
    <div style={{ display: 'flex', gap: 4 }}>
      {entries.map(({ y, v }) => (
        <div key={y} style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 2 }}>
          <span style={{ fontFamily: 'var(--font-mono)', fontSize: 8, fontWeight: 700, color: v >= 0 ? 'var(--pnl-pos)' : 'var(--pnl-neg)' }}>{v >= 0 ? '+' : ''}{Number(v).toFixed(1)}%</span>
          <div style={{ height: 22, width: '100%', display: 'flex', flexDirection: 'column', justifyContent: 'flex-end' }}>
            <div style={{ height: `${Math.abs(v) / max * 100}%`, minHeight: 2, borderRadius: 2, background: v >= 0 ? 'var(--signal-buy)' : 'var(--signal-sell)', opacity: 0.85 }} />
          </div>
          <span style={{ fontSize: 7, color: 'var(--text-faint)' }}>{y}</span>
        </div>
      ))}
    </div>
  );
}

// Core real-metric block shared by both views: return / sharpe / WR / DD / trades / conviction.
function RealMetrics({ s }) {
  const conviction = s._api?.conviction_score;
  return (
    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '8px 8px', padding: '7px 8px', borderRadius: 'var(--radius-md)', background: 'rgba(255,255,255,0.02)' }}>
      <Metric label="Return (BT)" value={s.returns != null ? `${s.returns >= 0 ? '+' : ''}${s.returns}%` : '—'} color={s.returns == null ? undefined : s.returns >= 0 ? 'var(--pnl-pos)' : 'var(--pnl-neg)'} big />
      <Metric label="Sharpe" value={s.sharpe ? s.sharpe.toFixed(2) : '—'} big />
      <Metric label="Win rate" value={s.btWR != null ? `${s.btWR}%` : '—'} color={s.btWR == null ? undefined : s.btWR >= 50 ? 'var(--pnl-pos)' : 'var(--pnl-neg)'} big />
      <Metric label="Max DD" value={s.dd != null ? `${s.dd}%` : '—'} color="var(--pnl-neg)" />
      <Metric label="Trades (OOS)" value={s._api?.trade_count_oos ?? '—'} />
      <Metric label="Conviction" value={conviction != null ? Number(conviction).toFixed(1) : '—'} />
    </div>
  );
}

/* ─────────────── Promote / demote modal — real gate engine ─────────────── */
function PromoteModal({ strategy, targetMode, onClose, onDone }) {
  const isPromotion = NEXT_MODE[strategy.mode] === targetMode;
  const isLive = targetMode === 'LIVE_TRADING';
  const [check, setCheck] = useState(null);      // /promote/check response
  const [phrase, setPhrase] = useState('');
  const [override, setOverride] = useState(false);
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState(null);    // {ok, message, gates?}

  useEffect(() => {
    let alive = true;
    api.post(`/api/strategies/${strategy.id}/promote/check`, { target_mode: targetMode })
      .then((r) => { if (alive) setCheck(r || { error: true }); });
    return () => { alive = false; };
  }, [strategy.id, targetMode]);

  const gates = check?.gates || [];
  const failed = gates.filter((g) => g.required && !g.pass);
  const phraseNeeded = !!check?.requires_confirmation_phrase;
  const phraseOk = !phraseNeeded || phrase === (check?.confirmation_phrase || 'PROMOTE TO LIVE');
  const canConfirm = !busy && check && !check.error && phraseOk && (check.passed || !isPromotion || override);

  const confirm = async () => {
    setBusy(true);
    setResult(null);
    const body = { target_mode: targetMode };
    if (phraseNeeded) body.confirmation_phrase = phrase;
    if (override) body.override_gates = true;
    const r = await api.post(`/api/strategies/${strategy.id}/promote`, body);
    setBusy(false);
    if (r && (r.success || r.no_op)) {
      setResult({ ok: true, message: r.message || `${strategy.name} → ${MODE_LABEL[targetMode]}` });
      onDone();
      setTimeout(onClose, 1200);
    } else {
      setResult({ ok: false, message: r?.message || 'Request failed — mode unchanged', gates: r?.gates });
    }
  };

  const GateRow = ({ g }) => (
    <div style={{ display: 'flex', alignItems: 'center', gap: 7, fontSize: 10, padding: '4px 0' }}>
      <span style={{ width: 13, height: 13, borderRadius: '50%', flex: 'none', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 9, fontWeight: 900, background: g.pass ? 'rgba(16,185,129,0.18)' : 'rgba(244,63,94,0.18)', color: g.pass ? 'var(--pnl-pos)' : 'var(--pnl-neg)' }}>{g.pass ? '✓' : '✕'}</span>
      <span style={{ color: g.pass ? 'var(--text-secondary)' : 'var(--text-strong)', flex: 1 }}>{g.label}</span>
      <span style={{ fontFamily: 'var(--font-mono)', color: g.pass ? 'var(--text-muted)' : 'var(--pnl-neg)', fontWeight: 700, flex: 'none' }}>
        {g.actual != null ? g.actual : '—'}
      </span>
    </div>
  );

  return (
    <div onClick={onClose} style={{ position: 'fixed', inset: 0, zIndex: 90, background: 'rgba(0,0,0,0.65)', backdropFilter: 'blur(3px)', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 16 }}>
      <div onClick={(e) => e.stopPropagation()} className="jt-surface-strong" style={{ width: 420, maxWidth: '100%', maxHeight: '85vh', overflowY: 'auto', padding: 0 }}>
        <div style={{ padding: '12px 16px', borderBottom: '1px solid var(--border-glass)', display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 8 }}>
          <div>
            <div style={{ fontSize: 13, fontWeight: 700, color: 'var(--text-strong)' }}>
              {isPromotion ? (isLive ? 'Deploy to Live' : 'Promote to Paper') : `Demote to ${MODE_LABEL[targetMode]}`}
            </div>
            <div style={{ fontSize: 10, color: 'var(--text-muted)', marginTop: 2 }}>{strategy.name}</div>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            <ModeBadge mode={strategy.mode} />
            <span style={{ color: 'var(--text-faint)', fontSize: 11 }}>→</span>
            <ModeBadge mode={targetMode} />
          </div>
        </div>

        <div style={{ padding: 16, display: 'flex', flexDirection: 'column', gap: 12 }}>
          {!check && <div style={{ fontSize: 11, color: 'var(--text-muted)', textAlign: 'center', padding: '12px 0' }}>Checking promotion gates…</div>}
          {check?.error && <div style={{ fontSize: 11, color: 'var(--pnl-neg)', textAlign: 'center', padding: '12px 0' }}>Gate check failed — backend unreachable.</div>}

          {check && !check.error && (
            <>
              {gates.length > 0 ? (
                <div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                    <span className="jt-label">Promotion gates</span>
                    <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10, fontWeight: 700, color: check.passed ? 'var(--pnl-pos)' : 'var(--chip-amber)' }}>
                      {gates.filter((g) => g.pass).length}/{gates.length} passing
                    </span>
                  </div>
                  {gates.map((g) => <GateRow key={g.id} g={g} />)}
                  {failed.length > 0 && failed[0].reason && (
                    <div style={{ marginTop: 6, fontSize: 9, color: 'var(--text-muted)' }}>{failed.map((g) => g.reason).filter(Boolean).join(' · ')}</div>
                  )}
                </div>
              ) : (
                <div style={{ fontSize: 11, color: 'var(--text-secondary)' }}>
                  {isPromotion ? 'No gates for this transition.' : 'Demotion has no gate requirements. The strategy stops routing to its current book immediately.'}
                </div>
              )}

              {isPromotion && !check.passed && (
                <label style={{ display: 'flex', alignItems: 'flex-start', gap: 8, padding: '8px 10px', borderRadius: 'var(--radius-md)', background: 'rgba(245,158,11,0.08)', border: '1px solid rgba(245,158,11,0.25)', cursor: 'pointer' }}>
                  <input type="checkbox" checked={override} onChange={(e) => setOverride(e.target.checked)} style={{ marginTop: 2, accentColor: '#f59e0b' }} />
                  <span style={{ fontSize: 10, color: 'var(--text-secondary)' }}>
                    <b style={{ color: 'var(--chip-amber)' }}>Override failing gates.</b> The promotion is recorded in the audit log with the metrics at time of override.
                  </span>
                </label>
              )}

              {phraseNeeded && (
                <div>
                  <div className="jt-label" style={{ marginBottom: 5 }}>Type <span style={{ fontFamily: 'var(--font-mono)', color: 'var(--pnl-neg)' }}>{check.confirmation_phrase || 'PROMOTE TO LIVE'}</span> to confirm live deployment</div>
                  <input value={phrase} onChange={(e) => setPhrase(e.target.value)} placeholder="confirmation phrase" autoFocus
                    style={{ width: '100%', boxSizing: 'border-box', padding: '8px 10px', fontSize: 12, fontFamily: 'var(--font-mono)', color: 'var(--text-strong)', background: 'rgba(15,23,42,0.6)', border: `1px solid ${phraseOk && phrase ? 'rgba(52,211,153,0.4)' : 'var(--border-glass)'}`, borderRadius: 'var(--radius-sm)', outline: 'none' }} />
                </div>
              )}

              {result && (
                <div style={{ padding: '8px 10px', borderRadius: 'var(--radius-md)', fontSize: 11, fontWeight: 600, background: result.ok ? 'rgba(16,185,129,0.12)' : 'rgba(244,63,94,0.12)', color: result.ok ? 'var(--pnl-pos)' : 'var(--pnl-neg)' }}>
                  {result.ok ? '✓ ' : ''}{result.message}
                </div>
              )}

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 8, marginTop: 2 }}>
                <Button variant="ghost" size="md" onClick={onClose}>Cancel</Button>
                <Button variant={isLive ? 'danger' : 'primary'} size="md" disabled={!canConfirm} onClick={confirm}>
                  {busy ? 'Applying…' : isPromotion ? (isLive ? 'Deploy Live' : 'Promote') : 'Demote'}
                </Button>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}

/* ─────────────── shared card ─────────────── */
function StrategyCard({ s, onOpen, onAction, showLadder }) {
  const hz = HORIZON[s.horizon] || HORIZON.swing;
  const live = s.mode === 'LIVE_TRADING';
  const next = NEXT_MODE[s.mode];
  const prev = PREV_MODE[s.mode];
  return (
    <div className="jt-surface" style={{ padding: 12, display: 'flex', flexDirection: 'column', gap: 9 }}>
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 8 }}>
        <div style={{ minWidth: 0, cursor: 'pointer' }} onClick={() => onOpen(s.id)} title="Open strategy detail">
          <div style={{ fontSize: 12, fontWeight: 700, color: 'var(--text-strong)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{s.name}</div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginTop: 4 }}>
            <Chip color={STAGE_CHIP[s.stage]}>{s.stage.replace('_', ' ')}</Chip>
            <span style={{ fontSize: 9, color: 'var(--text-muted)' }}>{s.asset}</span>
          </div>
        </div>
        <ModeBadge mode={s.mode} />
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
        <Chip color={hz.color}>{hz.label}</Chip>
        <Chip color={s.tier === 'T1' ? 'emerald' : s.tier === 'T2' ? 'amber' : 'slate'}>{s.tier}</Chip>
        {live && s.trades > 0 && <span style={{ marginLeft: 'auto', fontFamily: 'var(--font-mono)', fontSize: 9, color: 'var(--pnl-pos)' }}>{s.trades} live trades</span>}
      </div>

      <RealMetrics s={s} />

      <div style={{ padding: '7px 8px', borderRadius: 'var(--radius-md)', background: 'rgba(255,255,255,0.02)', display: 'flex', flexDirection: 'column', gap: 6 }}>
        <span style={{ fontSize: 8, textTransform: 'uppercase', letterSpacing: '0.06em', color: 'var(--text-muted)' }}>Annual backtest returns</span>
        <YearlyBars yearly={s._api?.yearly_backtest} />
      </div>

      {showLadder && (
        <div style={{ display: 'flex', gap: 6, marginTop: 1 }}>
          {next && (
            <Button variant={next === 'LIVE_TRADING' ? 'danger' : 'primary'} size="sm" style={{ flex: 1, justifyContent: 'center' }}
              onClick={() => onAction(s, next)}>
              {next === 'LIVE_TRADING' ? 'Deploy Live →' : 'Promote to Paper →'}
            </Button>
          )}
          {prev && (
            <Button variant="ghost" size="sm" style={{ flex: next ? 'none' : 1, justifyContent: 'center' }}
              onClick={() => onAction(s, prev)}>
              Demote
            </Button>
          )}
        </div>
      )}
    </div>
  );
}

/* ─────────────── PERFORMANCE (card grid) ─────────────── */
export function StrategyPerformanceGrid({ book, error, hzn, setHzn, onOpen, onAction }) {
  const [sortKey, setSortKey] = useState('returns');
  if (!book) return <Placeholder label={error ? 'Could not load strategies — backend unreachable.' : 'Loading strategies…'} />;
  const counts = { all: book.length, day: 0, swing: 0, position: 0 };
  book.forEach((s) => { counts[s.horizon] = (counts[s.horizon] || 0) + 1; });
  const src = hzn === 'all' ? book : book.filter((s) => s.horizon === hzn);
  const sorted = [...src].sort((a, b) => (b[sortKey] ?? -Infinity) - (a[sortKey] ?? -Infinity));
  const withWR = src.filter((s) => s.btWR != null);
  const avgWR = withWR.length ? withWR.reduce((a, s) => a + s.btWR, 0) / withWR.length : null;
  const liveN = src.filter((s) => s.mode === 'LIVE_TRADING').length;
  const paperN = src.filter((s) => s.mode === 'PAPER_TRADING').length;
  const best = sorted.find((s) => s.returns != null);
  const SORTS = [{ k: 'returns', l: 'Return' }, { k: 'sharpe', l: 'Sharpe' }, { k: 'btWR', l: 'Win rate' }, { k: 'trades', l: 'Trades' }];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
      <div style={{ display: 'flex', alignItems: 'flex-end', justifyContent: 'space-between', flexWrap: 'wrap', gap: 8 }}>
        <div>
          <h2 style={{ margin: 0, fontSize: 14, fontWeight: 700, color: 'var(--text-strong)' }}>Performance</h2>
          <p style={{ margin: '2px 0 0', fontSize: 10, color: 'var(--text-muted)' }}>Backtest &amp; live metrics from the strategy registry · click a card for full detail</p>
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
        <KpiTile label={hzn === 'all' ? 'Strategies' : HORIZON[hzn].label} value={src.length} sub={`${liveN} live · ${paperN} paper`} />
        <KpiTile label="Avg BT Win Rate" value={avgWR != null ? `${avgWR.toFixed(1)}%` : '—'} pos={avgWR != null ? avgWR >= 50 : undefined} />
        <KpiTile label="Live Strategies" value={liveN} pos={liveN > 0} />
        <KpiTile label="Best (Return)" value={best ? best.name.split(' ').slice(0, 2).join(' ') : '—'} sub={best ? fmtPct(best.returns) : null} pos />
      </div>

      {sorted.length === 0
        ? <Placeholder label="No strategies match this horizon." hint="Switch the horizon filter back to All, or deploy strategies from the Lab." />
        : <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: 10 }}>
            {sorted.map((s) => <StrategyCard key={s.id} s={s} onOpen={onOpen} onAction={onAction} showLadder={false} />)}
          </div>}
    </div>
  );
}

/* ─────────────── PIPELINE (mode-ladder board) ─────────────── */
const LADDER = [
  { mode: 'SIMULATION', label: 'Simulation', color: 'blue', desc: 'DB-only backtests · zero risk' },
  { mode: 'PAPER_TRADING', label: 'Paper', color: 'amber', desc: 'IBKR paper account · live signals' },
  { mode: 'LIVE_TRADING', label: 'Live', color: 'emerald', desc: 'Real capital via IBKR' },
];

export function StrategyPipelineBoard({ book, error, hzn, setHzn, onOpen, onAction }) {
  if (!book) return <Placeholder label={error ? 'Could not load strategies — backend unreachable.' : 'Loading pipeline…'} />;
  const counts = { all: book.length, day: 0, swing: 0, position: 0 };
  book.forEach((s) => { counts[s.horizon] = (counts[s.horizon] || 0) + 1; });
  const view = hzn === 'all' ? book : book.filter((s) => s.horizon === hzn);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
      <div style={{ display: 'flex', alignItems: 'flex-end', justifyContent: 'space-between', flexWrap: 'wrap', gap: 8 }}>
        <div>
          <h2 style={{ margin: 0, fontSize: 14, fontWeight: 700, color: 'var(--text-strong)' }}>Deployment Pipeline</h2>
          <p style={{ margin: '2px 0 0', fontSize: 10, color: 'var(--text-muted)' }}>Simulation → Paper → Live · promotions run the backend gate engine and are audited · live deployment requires typed confirmation</p>
        </div>
        <HorizonSeg hzn={hzn} setHzn={setHzn} counts={counts} />
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 10, alignItems: 'start' }}>
        {LADDER.map((st, i) => {
          const items = view.filter((s) => s.mode === st.mode);
          return (
            <div key={st.mode} style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '6px 4px' }}>
                <span style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                  <Chip color={st.color}>{st.label}</Chip>
                  <span style={{ fontSize: 9, color: 'var(--text-faint)' }}>{st.desc}</span>
                </span>
                <span style={{ fontFamily: 'var(--font-mono)', fontSize: 12, fontWeight: 700, color: 'var(--text-secondary)' }}>{items.length}</span>
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 8, minHeight: 60, padding: 6, borderRadius: 'var(--radius-lg)', background: 'rgba(255,255,255,0.012)', border: '1px solid var(--border-glass)' }}>
                {items.map((s) => <StrategyCard key={s.id} s={s} onOpen={onOpen} onAction={onAction} showLadder />)}
                {items.length === 0 && (
                  <div style={{ padding: '14px 6px', textAlign: 'center', fontSize: 9, color: 'var(--text-faint)' }}>
                    {i === 0 ? 'No strategies in simulation — create one in the Lab' : i === 1 ? 'Nothing on paper — promote a simulated strategy when its gates pass' : 'Nothing live — deploy from Paper once live gates pass'}
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

/* ─────────────── shared wrapper ─────────────── */
export function StrategiesWorkspace({ sub, onOpen }) {
  const { book, reload, error } = useStrategyBook();
  const [hzn, setHzn] = useState('all');
  const [action, setAction] = useState(null); // { strategy, targetMode }
  const onAction = (strategy, targetMode) => setAction({ strategy, targetMode });

  return (
    <>
      {sub === 'pipeline'
        ? <StrategyPipelineBoard book={book} error={error} hzn={hzn} setHzn={setHzn} onOpen={onOpen} onAction={onAction} />
        : <StrategyPerformanceGrid book={book} error={error} hzn={hzn} setHzn={setHzn} onOpen={onOpen} onAction={onAction} />}
      {action && (
        <PromoteModal
          strategy={action.strategy}
          targetMode={action.targetMode}
          onClose={() => setAction(null)}
          onDone={reload}
        />
      )}
    </>
  );
}

export default StrategiesWorkspace;
