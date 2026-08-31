import React, { useState, useEffect, useCallback } from 'react';
import { api, usePoll } from '../utils';
import { Chip, KpiTile, Button, ModeBadge, fmtPct, fmtK } from './jtkit';
import { HORIZON, mapApiToBook, pctOrRatio } from './strategyProfiles';

// Strategies workspace — Performance card grid + Pipeline mode-ladder board.
// Universe = the quality-gated pipeline feed (gold.v_pipeline_ui_feed), the
// SAME source Strategy Lab uses, so Lab / Pipeline / Performance always show
// the same strategies. Metrics come from /api/strategies/researcher (no
// synthetic data), filtered to the gated ids. Promote/demote goes through the
// backend's real gate engine:
//   POST /api/strategies/{id}/promote/check  → gates preview
//   POST /api/strategies/{id}/promote        → apply (LIVE needs typed phrase)

const MODE_LABEL = { SIMULATION: 'Simulation', PAPER_TRADING: 'Paper', UAT: 'UAT', LIVE_TRADING: 'Live' };
const NEXT_MODE = { SIMULATION: 'PAPER_TRADING', PAPER_TRADING: 'UAT', UAT: 'LIVE_TRADING' };
const PREV_MODE = { LIVE_TRADING: 'UAT', UAT: 'PAPER_TRADING', PAPER_TRADING: 'SIMULATION' };
const PERF_MODES = [
  { k: 'sim', l: 'Sim', desc: 'Backtest / OOS' },
  { k: 'paper', l: 'Paper', desc: 'Paper-trading' },
  { k: 'uat', l: 'UAT', desc: 'Broker rehearsal' },
  { k: 'live', l: 'Live', desc: 'Live capital' },
];
const STAGE_CHIP = { deployed: 'emerald', uat: 'slate', golden: 'amber', near_golden: 'blue', experimental: 'slate' };

function useStrategyBook() {
  const [book, setBook] = useState(null);
  const [error, setError] = useState(false);
  const load = useCallback(async (fresh = false) => {
    // fresh=1 bypasses the backend's 15s researcher cache — used right after a
    // confirmed promote so the new mode is visible immediately.
    const [rows, feed] = await Promise.all([
      api.get(`/api/strategies/researcher${fresh ? '?fresh=1' : ''}`),
      api.get('/api/strategies/pipeline-feed'),
    ]);
    if (rows == null) { setError(true); return; }
    setError(false);
    const raw = Array.isArray(rows) ? rows : (rows?.strategies || rows?.data || []);
    // Canonical universe = quality-gated feed ids (same set Strategy Lab
    // renders). Registry rows failing the metric gates are dropped here so the
    // Pipeline and Performance tabs can never drift from the Lab count. If the
    // feed call fails, fall back to the full registry rather than an empty tab.
    const feedIds = new Set((feed?.data || []).map((r) => r.id));
    const gated = feedIds.size ? raw.filter((r) => feedIds.has(r.id)) : raw;
    setBook(mapApiToBook(gated));
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

function ModeSeg({ mode, setMode }) {
  return (
    <div style={{ display: 'flex', gap: 2, padding: 3, borderRadius: 'var(--radius-md)', background: 'rgba(15,23,42,0.5)', border: '1px solid var(--border-glass)' }}>
      {PERF_MODES.map((o) => (
        <button key={o.k} onClick={() => setMode(o.k)} style={{ padding: '4px 9px', borderRadius: 'var(--radius-sm)', border: 'none', cursor: 'pointer', fontSize: 10, fontWeight: 700, background: mode === o.k ? 'var(--primary)' : 'transparent', color: mode === o.k ? '#fff' : 'var(--text-secondary)' }}>{o.l}</button>
      ))}
    </div>
  );
}

// Asset-class filter segment — options are built from whatever classes are
// actually present in the book so the toggle never shows dead filters.
function AssetSeg({ asset, setAsset, opts, counts }) {
  return (
    <div style={{ display: 'flex', gap: 2, padding: 3, borderRadius: 'var(--radius-md)', background: 'rgba(15,23,42,0.5)', border: '1px solid var(--border-glass)' }}>
      {opts.map((k) => (
        <button key={k} onClick={() => setAsset(k)} style={{ display: 'flex', alignItems: 'center', gap: 5, padding: '4px 10px', borderRadius: 'var(--radius-sm)', border: 'none', cursor: 'pointer', fontSize: 10, fontWeight: 700, background: asset === k ? 'var(--primary)' : 'transparent', color: asset === k ? '#fff' : 'var(--text-secondary)' }}>
          {k === 'all' ? 'All Assets' : k}<span style={{ fontFamily: 'var(--font-mono)', fontSize: 9, opacity: 0.7 }}>{counts[k] ?? 0}</span>
        </button>
      ))}
    </div>
  );
}

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
// normalize=true applies pctOrRatio (backtest rows mix ratio / pp scaling);
// paper_yearly is emitted in percentage points already, so paper mode passes
// normalize=false to avoid a 0.5% bar rendering as +50%.
// openBar (paper mode only): mark-to-market OPEN book, rendered as a dashed
// outline bar labelled 'open' — visibly distinct from solid realized bars so
// unrealized P&L is never mistaken for a closed-trade return.
function YearlyBars({ yearly, emptyLabel = 'No annual backtest data yet', normalize = true, openBar = null }) {
  const years = Object.keys(yearly || {}).sort();
  const entries = years
    .map((y) => ({ y, v: normalize ? pctOrRatio(yearly[y]?.return_pct, 1) : (yearly[y]?.return_pct != null ? +Number(yearly[y].return_pct).toFixed(1) : null) }))
    .filter((e) => e.v != null);
  const showOpen = openBar && openBar.v != null;
  if (!entries.length && !showOpen) {
    return <div style={{ padding: '6px 0', fontSize: 9, color: 'var(--text-faint)', textAlign: 'center' }}>{emptyLabel}</div>;
  }
  // Scale floor of 5%: without it a single small bar (e.g. paper +1.1%) is
  // normalized to full height, which reads as a huge return. With the floor,
  // bars below 5% render proportionally small; anything larger still scales
  // to the biggest value in the set.
  const max = Math.max(...entries.map((e) => Math.abs(e.v)), showOpen ? Math.abs(openBar.v) : 0, 5);
  return (
    <div style={{ display: 'flex', gap: 4 }}>
      {entries.map(({ y, v }) => (
        <div
          key={y}
          // Fixed slot width: with flex:1 a single year of data stretched to
          // the full strip width and read as one giant block.
          style={{ flex: '0 0 28px', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 2 }}
          title={yearly[y]?.pnl != null ? `$${Number(yearly[y].pnl).toLocaleString(undefined, { maximumFractionDigits: 0 })} · ${yearly[y].trades ?? 0} closed trade${yearly[y].trades === 1 ? '' : 's'}` : undefined}
        >
          <span style={{ fontFamily: 'var(--font-mono)', fontSize: 8, fontWeight: 700, color: v >= 0 ? 'var(--pnl-pos)' : 'var(--pnl-neg)' }}>{v >= 0 ? '+' : ''}{Number(v).toFixed(1)}%</span>
          <div style={{ height: 22, width: '100%', display: 'flex', flexDirection: 'column', justifyContent: 'flex-end' }}>
            <div style={{ height: `${Math.abs(v) / max * 100}%`, minHeight: 2, borderRadius: 2, background: v >= 0 ? 'var(--signal-buy)' : 'var(--signal-sell)', opacity: 0.85 }} />
          </div>
          <span style={{ fontSize: 7, color: 'var(--text-faint)' }}>{y}</span>
        </div>
      ))}
      {showOpen && (
        <div
          key="open"
          style={{ flex: '0 0 28px', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 2 }}
          title={`$${Number(openBar.pnl).toLocaleString(undefined, { maximumFractionDigits: 0 })} unrealized · ${openBar.positions} open position${openBar.positions === 1 ? '' : 's'} · mark-to-market, not yet realized`}
        >
          <span style={{ fontFamily: 'var(--font-mono)', fontSize: 8, fontWeight: 700, color: openBar.v >= 0 ? 'var(--pnl-pos)' : 'var(--pnl-neg)' }}>{openBar.v >= 0 ? '+' : ''}{Number(openBar.v).toFixed(1)}%</span>
          <div style={{ height: 22, width: '100%', display: 'flex', flexDirection: 'column', justifyContent: 'flex-end' }}>
            <div style={{ height: `${Math.abs(openBar.v) / max * 100}%`, minHeight: 2, borderRadius: 2, boxSizing: 'border-box', border: `1px dashed ${openBar.v >= 0 ? 'var(--signal-buy)' : 'var(--signal-sell)'}`, opacity: 0.9 }} />
          </div>
          <span style={{ fontSize: 7, color: 'var(--text-faint)' }}>open</span>
        </div>
      )}
    </div>
  );
}

// Core metric block rendered for a given performance view (sim / paper / live).
function RealMetrics({ s, mode }) {
  const conviction = s._api?.conviction_score;
  const liveActive = s.mode === 'LIVE_TRADING';

  if (mode === 'paper') {
    const pnl = s.paperPNL;
    // Monitoring state semantics (kanban t_1f3bee9f):
    //   engaged  = paper monitor running AND open paper positions right now.
    //   watching = monitor running but flat book (all-SELL scores, or a
    //              mostly-cash design like COMM_GoldSilver) — NOT an error.
    //   off      = paper monitor not running.
    // Fallback for backends that predate paper_state: engaged iff the old
    // is_paper_monitoring flag is set, otherwise off.
    const paperState = s._api?.paper_state ?? (s._api?.is_paper_monitoring ? 'engaged' : 'off');
    const stateLabel = paperState === 'engaged' ? 'Engaged' : paperState === 'watching' ? 'Watching' : 'Off';
    // Colour carries meaning only: emerald = actively in market; Watching and
    // Off are neutral states (Watching is default text, Off is muted).
    const stateColor = paperState === 'engaged' ? 'var(--pnl-pos)' : paperState === 'off' ? 'var(--text-muted)' : undefined;
    return (
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '8px 8px', padding: '7px 8px', borderRadius: 'var(--radius-md)', background: 'rgba(255,255,255,0.02)' }}>
        <Metric label="P&L" value={pnl != null ? fmtK(pnl) : '—'} color={pnl == null ? undefined : pnl >= 0 ? 'var(--pnl-pos)' : 'var(--pnl-neg)'} big />
        <Metric label="Profit factor" value={s.paperPF != null ? s.paperPF.toFixed(2) : '—'} big />
        <Metric label="Win rate" value={s.paperWR != null ? `${s.paperWR}%` : '—'} color={s.paperWR == null ? undefined : s.paperWR >= 50 ? 'var(--pnl-pos)' : 'var(--pnl-neg)'} big />
        <Metric label="Trades" value={s.paperTrades ?? '—'} />
        <Metric label="Monitoring" value={stateLabel} color={stateColor} />
        <Metric label="Conviction" value={conviction != null ? Number(conviction).toFixed(1) : '—'} />
      </div>
    );
  }

  if (mode === 'uat') {
    // Broker rehearsal book: positions/fills live at the IBKR UAT session, not
    // in any DB ledger. Fills-based metrics (count, realized P&L, slippage)
    // arrive with the qr_etl mirror (kanban t_b64f7302) — render honest
    // pending slots until then, never backtest numbers dressed as rehearsal.
    return (
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '8px 8px', padding: '7px 8px', borderRadius: 'var(--radius-md)', background: 'rgba(255,255,255,0.02)' }}>
        <Metric label="Realized P&L" value="—" big />
        <Metric label="Fills" value="—" big />
        <Metric label="Avg slippage" value="—" big />
        <Metric label="Source" value="IBKR UAT" />
        <Metric label="Metrics" value="Pending" color="var(--text-muted)" />
        <Metric label="Conviction" value={conviction != null ? Number(conviction).toFixed(1) : '—'} />
      </div>
    );
  }

  if (mode === 'live') {
    return (
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '8px 8px', padding: '7px 8px', borderRadius: 'var(--radius-md)', background: 'rgba(255,255,255,0.02)' }}>
        <Metric label="P&L" value="—" big />
        <Metric label="Profit factor" value="—" big />
        <Metric label="Win rate" value="—" big />
        <Metric label="Trades" value="—" />
        <Metric label="Status" value={liveActive ? 'Active' : '—'} color={liveActive ? 'var(--pnl-pos)' : 'var(--text-muted)'} />
        <Metric label="Conviction" value={conviction != null ? Number(conviction).toFixed(1) : '—'} />
      </div>
    );
  }

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
              {isPromotion ? (isLive ? 'Deploy to Live' : `Promote to ${MODE_LABEL[targetMode]}`) : `Demote to ${MODE_LABEL[targetMode]}`}
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
              {targetMode === 'UAT' && (
                <div style={{ padding: '8px 10px', borderRadius: 'var(--radius-md)', fontSize: 10, color: 'var(--text-secondary)', background: 'rgba(100,116,139,0.12)', border: '1px solid rgba(100,116,139,0.3)' }}>
                  Broker rehearsal: orders route to the IBKR UAT paper session (real routing, paper money).
                  Signal→order firing for UAT strategies is wired by qr_etl (kanban t_2027d985);
                  until it lands, UAT strategies show signals but orders route via the UAT ticket only.
                </div>
              )}
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
function StrategyCard({ s, onOpen, onAction, showLadder, viewMode = 'sim' }) {
  const hz = HORIZON[s.horizon] || HORIZON.swing;
  const live = s.mode === 'LIVE_TRADING';
  const next = NEXT_MODE[s.mode];
  const prev = PREV_MODE[s.mode];
  // UAT → Live is engine-blocked until qr_research defines the gate criteria
  // (kanban t_b64f7302) — show the rung but keep it disabled, no fake affordance.
  const nextBlocked = s.mode === 'UAT' && next === 'LIVE_TRADING';
  const NEXT_CTA = { PAPER_TRADING: 'Promote to Paper →', UAT: 'Promote to UAT →', LIVE_TRADING: 'Deploy Live →' };
  const barsLabel = viewMode === 'paper' ? 'Paper returns · % of assigned capital (solid realized · outline open book)'
    : viewMode === 'live' ? 'Live returns'
    : viewMode === 'uat' ? 'Broker rehearsal — fills-based metrics pending qr_etl mirror'
    : 'Annual backtest returns';
  const barsData = viewMode === 'sim' ? s._api?.yearly_backtest : viewMode === 'paper' ? s._api?.paper_yearly : null;
  const barsNormalize = viewMode === 'sim';
  const openBar = viewMode === 'paper' && s._api?.paper_open?.return_pct != null
    ? { v: +Number(s._api.paper_open.return_pct).toFixed(1), pnl: s._api.paper_open.unrealized_pnl, positions: s._api.paper_open.positions }
    : null;
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

      <RealMetrics s={s} mode={viewMode} />

      <div style={{ padding: '7px 8px', borderRadius: 'var(--radius-md)', background: 'rgba(255,255,255,0.02)', display: 'flex', flexDirection: 'column', gap: 6 }}>
        <span style={{ fontSize: 8, textTransform: 'uppercase', letterSpacing: '0.06em', color: 'var(--text-muted)' }}>{barsLabel}</span>
        <YearlyBars yearly={barsData} normalize={barsNormalize} openBar={openBar} emptyLabel={viewMode === 'paper' ? 'No closed paper trades yet' : viewMode === 'live' ? 'No live returns yet' : viewMode === 'uat' ? 'Book lives at the IBKR UAT session — see Execution → UAT' : undefined} />
      </div>

      {showLadder && (
        <div style={{ display: 'flex', gap: 6, marginTop: 1 }}>
          {next && (
            <Button variant={next === 'LIVE_TRADING' ? 'danger' : 'primary'} size="sm" style={{ flex: 1, justifyContent: 'center' }}
              disabled={nextBlocked}
              title={nextBlocked ? 'UAT → Live gate criteria pending qr_research/QA (kanban t_b64f7302)' : undefined}
              onClick={() => !nextBlocked && onAction(s, next)}>
              {NEXT_CTA[next] || 'Promote →'}
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
  const [perfMode, setPerfMode] = useState('sim');
  const [sortKey, setSortKey] = useState('returns');
  const [assetFilter, setAssetFilter] = useState('all');
  if (!book) return <Placeholder label={error ? 'Could not load strategies — backend unreachable.' : 'Loading strategies…'} />;

  const counts = { all: book.length, day: 0, swing: 0, position: 0 };
  book.forEach((s) => { counts[s.horizon] = (counts[s.horizon] || 0) + 1; });

  // Mode ladder (cumulative): Sim shows every strategy, Paper shows
  // paper/uat/live deployments, UAT shows rehearsal + live, Live shows live capital only.
  const MODE_FILTER = {
    sim: () => true,
    paper: (s) => s.mode === 'PAPER_TRADING' || s.mode === 'UAT' || s.mode === 'LIVE_TRADING',
    uat: (s) => s.mode === 'UAT' || s.mode === 'LIVE_TRADING',
    live: (s) => s.mode === 'LIVE_TRADING',
  };

  // Asset-class options from the classes actually present in the book.
  const assetCounts = { all: book.length };
  book.forEach((s) => { const k = s.assetClass || 'EQUITY'; assetCounts[k] = (assetCounts[k] || 0) + 1; });
  const assetOpts = ['all', ...Object.keys(assetCounts).filter((k) => k !== 'all').sort()];

  const src = book
    .filter((s) => hzn === 'all' || s.horizon === hzn)
    .filter(MODE_FILTER[perfMode] || (() => true))
    .filter((s) => assetFilter === 'all' || (s.assetClass || 'EQUITY') === assetFilter);

  const SORTS = {
    sim: [{ k: 'returns', l: 'Return' }, { k: 'sharpe', l: 'Sharpe' }, { k: 'btWR', l: 'Win rate' }, { k: 'trades', l: 'Trades' }],
    paper: [{ k: 'paperPNL', l: 'P&L' }, { k: 'paperPF', l: 'Profit factor' }, { k: 'paperWR', l: 'Win rate' }, { k: 'paperTrades', l: 'Trades' }],
    uat: [{ k: 'returns', l: 'Return' }, { k: 'btWR', l: 'Win rate' }, { k: 'trades', l: 'Trades' }],
    live: [{ k: 'returns', l: 'Return' }, { k: 'btWR', l: 'Win rate' }, { k: 'trades', l: 'Trades' }],
  };

  // keep sort key valid across mode switches
  const currentSorts = SORTS[perfMode];
  const effectiveSort = currentSorts.find((o) => o.k === sortKey) ? sortKey : currentSorts[0].k;

  const sorted = [...src].sort((a, b) => (b[effectiveSort] ?? -Infinity) - (a[effectiveSort] ?? -Infinity));
  const simWRs = src.filter((s) => s.btWR != null);
  const avgSimWR = simWRs.length ? simWRs.reduce((a, s) => a + s.btWR, 0) / simWRs.length : null;
  const paperWRs = src.filter((s) => s.paperWR != null);
  const avgPaperWR = paperWRs.length ? paperWRs.reduce((a, s) => a + s.paperWR, 0) / paperWRs.length : null;
  const liveN = src.filter((s) => s.mode === 'LIVE_TRADING').length;
  const paperN = src.filter((s) => s.mode === 'PAPER_TRADING').length;
  const uatN = src.filter((s) => s.mode === 'UAT').length;
  const best = sorted.find((s) => s[effectiveSort] != null);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
      <div style={{ display: 'flex', alignItems: 'flex-end', justifyContent: 'space-between', flexWrap: 'wrap', gap: 8 }}>
        <div>
          <h2 style={{ margin: 0, fontSize: 14, fontWeight: 700, color: 'var(--text-strong)' }}>Performance</h2>
          <p style={{ margin: '2px 0 0', fontSize: 10, color: 'var(--text-muted)' }}>Backtest, paper &amp; live metrics from the strategy registry · click a card for full detail</p>
        </div>
        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
          <ModeSeg mode={perfMode} setMode={setPerfMode} />
          <AssetSeg asset={assetFilter} setAsset={setAssetFilter} opts={assetOpts} counts={assetCounts} />
          <HorizonSeg hzn={hzn} setHzn={setHzn} counts={counts} />
        </div>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-end', gap: 6 }}>
        <span style={{ fontSize: 9, color: 'var(--text-faint)' }}>Sort</span>
        <div style={{ display: 'flex', gap: 2, padding: 3, borderRadius: 'var(--radius-md)', background: 'rgba(15,23,42,0.5)', border: '1px solid var(--border-glass)' }}>
          {currentSorts.map((o) => (
            <button key={o.k} onClick={() => setSortKey(o.k)} style={{ padding: '4px 9px', borderRadius: 'var(--radius-sm)', border: 'none', cursor: 'pointer', fontSize: 10, fontWeight: 700, background: sortKey === o.k ? 'var(--primary)' : 'transparent', color: sortKey === o.k ? '#fff' : 'var(--text-secondary)' }}>{o.l}</button>
          ))}
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 8 }}>
        {perfMode === 'sim' && (
          <>
            <KpiTile label={hzn === 'all' ? 'Strategies' : HORIZON[hzn].label} value={src.length} sub={`${liveN} live · ${uatN} uat · ${paperN} paper`} />
            <KpiTile label="Avg BT Win Rate" value={avgSimWR != null ? `${avgSimWR.toFixed(1)}%` : '—'} pos={avgSimWR != null ? avgSimWR >= 50 : undefined} />
            <KpiTile label="Live Strategies" value={liveN} pos={liveN > 0} />
            <KpiTile label="Best (Return)" value={best ? best.name.split(' ').slice(0, 2).join(' ') : '—'} sub={best ? fmtPct(best.returns) : null} pos />
          </>
        )}
        {perfMode === 'paper' && (
          <>
            <KpiTile label="Paper Strategies" value={src.length} sub={liveN > 0 ? `${paperN} paper · ${liveN} live` : null} />
            <KpiTile label="Avg Paper WR" value={avgPaperWR != null ? `${avgPaperWR.toFixed(1)}%` : '—'} pos={avgPaperWR != null ? avgPaperWR >= 50 : undefined} />
            <KpiTile label="Paper Active" value={src.filter((s) => s.mode === 'PAPER_TRADING').length} pos />
            <KpiTile label="Best Paper P&L" value={best ? best.name.split(' ').slice(0, 2).join(' ') : '—'} sub={best && best.paperPNL != null ? fmtK(best.paperPNL) : null} pos={best && best.paperPNL != null ? best.paperPNL >= 0 : undefined} />
          </>
        )}
        {perfMode === 'uat' && (
          <>
            <KpiTile label="UAT Strategies" value={uatN} pos={uatN > 0} sub={liveN > 0 ? `${liveN} live also in view` : null} />
            <KpiTile label="Broker Fills" value="—" />
            <KpiTile label="Avg Slippage" value="—" />
            <KpiTile label="Fills Metrics" value="Pending" sub="qr_etl mirror · t_b64f7302" />
          </>
        )}
        {perfMode === 'live' && (
          <>
            <KpiTile label="Live Strategies" value={liveN} pos={liveN > 0} />
            <KpiTile label="Avg Live WR" value="—" />
            <KpiTile label="Live Trades" value="—" />
            <KpiTile label="Best Live P&L" value="—" />
          </>
        )}
      </div>

      {sorted.length === 0
        ? <Placeholder label="No strategies match these filters." hint="Try another mode, asset class, or horizon — or deploy strategies from the Lab." />
        : <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: 10 }}>
            {sorted.map((s) => <StrategyCard key={s.id} s={s} onOpen={onOpen} onAction={onAction} showLadder={false} viewMode={perfMode} />)}
          </div>}
    </div>
  );
}

/* ─────────────── PIPELINE (mode-ladder board) ─────────────── */
const LADDER = [
  { mode: 'SIMULATION', label: 'Simulation', color: 'blue', desc: 'DB-only backtests · zero risk',
    empty: 'No strategies in simulation — create one in the Lab' },
  { mode: 'PAPER_TRADING', label: 'Paper', color: 'amber', desc: 'DB paper ledger · live signals',
    empty: 'Nothing on paper — promote a simulated strategy when its gates pass' },
  { mode: 'UAT', label: 'UAT', color: 'slate', desc: 'IBKR UAT session · real routing, paper money',
    empty: 'Nothing in rehearsal — promote a paper strategy to rehearse at the broker' },
  { mode: 'LIVE_TRADING', label: 'Live', color: 'emerald', desc: 'Real capital via IBKR',
    empty: 'Nothing live — UAT → Live gates pending qr_research' },
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
          <p style={{ margin: '2px 0 0', fontSize: 10, color: 'var(--text-muted)' }}>Simulation → Paper → UAT → Live · promotions run the backend gate engine and are audited · live deployment requires typed confirmation</p>
        </div>
        <HorizonSeg hzn={hzn} setHzn={setHzn} counts={counts} />
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 10, alignItems: 'start' }}>
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
                {items.map((s) => <StrategyCard key={s.id} s={s} onOpen={onOpen} onAction={onAction} showLadder viewMode={st.mode === 'PAPER_TRADING' ? 'paper' : st.mode === 'UAT' ? 'uat' : st.mode === 'LIVE_TRADING' ? 'live' : 'sim'} />)}
                {items.length === 0 && (
                  <div style={{ padding: '14px 6px', textAlign: 'center', fontSize: 9, color: 'var(--text-faint)' }}>
                    {st.empty}
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
