import React, { useState, useEffect, useCallback } from 'react';
import { api, usePoll } from '../utils';
import { Chip, KpiTile, Button, ModeBadge, fmtPct, fmtK } from './jtkit';
import { HORIZON, mapApiToBook, fracToPct, haltedLabel } from './strategyProfiles';
import ArchivePanel from './ArchivePanel';

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
  // Archive FIRST (PORTFOLIO-PRUNE-1, 2026-11-02): retired books live in a
  // first-class registry view, excluded from active counts and rankings.
  { k: 'archive', l: 'Archive', desc: 'Retired · evidence record' },
  { k: 'sim', l: 'Sim', desc: 'Backtest / OOS' },
  { k: 'paper', l: 'Paper', desc: 'Paper-trading' },
  { k: 'uat', l: 'UAT', desc: 'Broker rehearsal' },
  { k: 'live', l: 'Live', desc: 'Live capital' },
];
const STAGE_CHIP = { deployed: 'emerald', uat: 'slate', golden: 'amber', near_golden: 'blue', experimental: 'slate', halted: 'rose' };

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
    const feedRows = feed?.data || [];
    const feedIds = new Set(feedRows.map((r) => r.id));
    const gated = feedIds.size ? raw.filter((r) => feedIds.has(r.id)) : raw;
    // CLEANSE-1 (t_070590de): overlay the feed's authoritative registry status
    // + reason + skip detail + non-strategy bookkeeping onto researcher rows,
    // and append halted feed rows that have no researcher row at all (retired
    // books are excluded from /researcher) so a halted book never vanishes.
    const feedById = new Map(feedRows.map((r) => [r.id, r]));
    const merged = gated.map((r) => {
      const f = feedById.get(r.id);
      if (!f) return r;
      return {
        ...r,
        registry_status: f.registry_status,
        retirement_reason: f.retirement_reason ?? r.retirement_reason,
        paper_skips: f.paper_skips ?? r.paper_skips,
        paper_skip_count: f.paper_skip_count ?? r.paper_skip_count,
        non_strategy_pnl: f.non_strategy_pnl ?? r.non_strategy_pnl,
        non_strategy_legs: f.non_strategy_legs ?? r.non_strategy_legs,
        non_strategy_unrealized: f.non_strategy_unrealized ?? r.non_strategy_unrealized,
        non_strategy_phantom_positions: f.non_strategy_phantom_positions ?? r.non_strategy_phantom_positions,
      };
    });
    const inMerged = new Set(merged.map((r) => r.id));
    const feedOnly = feedRows.filter((r) => !inMerged.has(r.id) && r.stage === 'halted');
    setBook(mapApiToBook([...merged, ...feedOnly]));
  }, []);
  usePoll(load, 60000);
  const reload = useCallback(() => load(true), [load]);
  return { book, reload, error };
}

function HorizonSeg({ hzn, setHzn, counts }) {
  const opts = [['all', 'All'], ['day', 'Day Trade'], ['swing', 'Swing'], ['position', 'Position']];
  return (
    <div className="strat-seg" style={{ display: 'flex', gap: 2, padding: 3, borderRadius: 'var(--radius-md)', background: 'rgba(15,23,42,0.5)', border: '1px solid var(--border-glass)' }}>
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
    <div className="strat-seg" style={{ display: 'flex', gap: 2, padding: 3, borderRadius: 'var(--radius-md)', background: 'rgba(15,23,42,0.5)', border: '1px solid var(--border-glass)' }}>
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
    <div className="strat-seg" style={{ display: 'flex', gap: 2, padding: 3, borderRadius: 'var(--radius-md)', background: 'rgba(15,23,42,0.5)', border: '1px solid var(--border-glass)' }}>
      {opts.map((k) => (
        <button key={k} onClick={() => setAsset(k)} style={{ display: 'flex', alignItems: 'center', gap: 5, padding: '4px 10px', borderRadius: 'var(--radius-sm)', border: 'none', cursor: 'pointer', fontSize: 10, fontWeight: 700, background: asset === k ? 'var(--primary)' : 'transparent', color: asset === k ? '#fff' : 'var(--text-secondary)' }}>
          {k === 'all' ? 'All Assets' : k}<span style={{ fontFamily: 'var(--font-mono)', fontSize: 9, opacity: 0.7 }}>{counts[k] ?? 0}</span>
        </button>
      ))}
    </div>
  );
}

// Exported 2026-10-17 (derivatives_page_alignment_v1): the Derivatives tab
// reuses this exact Performance-card metric cell — no lookalike copies.
export function Metric({ label, value, color, big, tip, sub }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 1 }} title={tip || undefined}>
      <span style={{ fontSize: 8, textTransform: 'uppercase', letterSpacing: '0.06em', color: 'var(--text-muted)' }}>{label}</span>
      <span style={{ fontFamily: 'var(--font-mono)', fontSize: big ? 15 : 12, fontWeight: 700, color: color || 'var(--text-secondary)' }}>{value}</span>
      {sub && <span style={{ fontFamily: 'var(--font-mono)', fontSize: 8, color: 'var(--text-faint)' }}>{sub}</span>}
    </div>
  );
}

// Real annual backtest returns from gold.strategy_backtest_runs (via the API's
// yearly_backtest map) — replaces the old fabricated quarter bars.
// normalize=true applies fracToPct (backtest yearly return_pct is ALWAYS a
// fraction — 0.3281 = +32.8%); paper_yearly is emitted in percentage points
// already, so paper mode passes normalize=false to avoid a 0.5% bar rendering
// as +50%.
// openBar (paper mode only): mark-to-market OPEN book, rendered as a dashed
// outline bar labelled 'open' — visibly distinct from solid realized bars so
// unrealized P&L is never mistaken for a closed-trade return.
// oosStart/oosEnd (sim mode, ISO dates from the latest backtest run):
//   - a bar year BEFORE the OOS window is an in-sample year → hatched fill +
//     tooltip disclosure, so IS values are never read as OOS performance.
//   - the year containing oos_end is partial → YTD tag under the year label.
//   - OOS years with no stored annual return stay absent (never estimated);
//     the coverage gap is disclosed on the section label's tooltip.
export function YearlyBars({ yearly, emptyLabel = 'No annual backtest data yet', normalize = true, openBar = null, oosStart = null, oosEnd = null }) {
  const years = Object.keys(yearly || {}).sort();
  const entries = years
    .map((y) => ({ y, v: normalize ? fracToPct(yearly[y]?.return_pct, 1) : (yearly[y]?.return_pct != null ? +Number(yearly[y].return_pct).toFixed(1) : null) }))
    .filter((e) => e.v != null);
  const oosStartYear = oosStart ? Number(String(oosStart).slice(0, 4)) : null;
  // Partial when the window closes before Dec 31 of that year.
  const ytdYear = oosEnd && String(oosEnd).slice(5, 10) < '12-31' ? Number(String(oosEnd).slice(0, 4)) : null;
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
      {entries.map(({ y, v }) => {
        const isIS = oosStartYear != null && Number(y) < oosStartYear;
        const isYTD = ytdYear != null && Number(y) === ytdYear;
        const barColor = v >= 0 ? 'var(--signal-buy)' : 'var(--signal-sell)';
        const tipParts = [];
        if (isIS) tipParts.push(`in-sample year — OOS window starts ${oosStart}`);
        if (isYTD) tipParts.push(`year-to-date through ${oosEnd}`);
        if (yearly[y]?.pnl != null) tipParts.push(`$${Number(yearly[y].pnl).toLocaleString(undefined, { maximumFractionDigits: 0 })} · ${yearly[y].trades ?? 0} closed trade${yearly[y].trades === 1 ? '' : 's'}`);
        return (
        <div
          key={y}
          // Fixed slot width: with flex:1 a single year of data stretched to
          // the full strip width and read as one giant block.
          style={{ flex: '0 0 28px', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 2 }}
          title={tipParts.length ? tipParts.join(' · ') : undefined}
        >
          <span style={{ fontFamily: 'var(--font-mono)', fontSize: 8, fontWeight: 700, color: v >= 0 ? 'var(--pnl-pos)' : 'var(--pnl-neg)' }}>{v >= 0 ? '+' : ''}{Number(v).toFixed(1)}%</span>
          <div style={{ height: 22, width: '100%', display: 'flex', flexDirection: 'column', justifyContent: 'flex-end' }}>
            <div style={{
              height: `${Math.abs(v) / max * 100}%`, minHeight: 2, borderRadius: 2, opacity: isIS ? 0.55 : 0.85,
              background: isIS ? `repeating-linear-gradient(45deg, ${barColor} 0 2px, transparent 2px 5px)` : barColor,
            }} />
          </div>
          <span style={{ fontSize: 7, color: 'var(--text-faint)' }}>{y}{isIS ? '·IS' : ''}</span>
          {isYTD && <span style={{ fontSize: 6, fontWeight: 700, letterSpacing: '0.08em', color: 'var(--text-muted)', marginTop: -2 }}>YTD</span>}
        </div>
        );
      })}
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
  const [skipsOpen, setSkipsOpen] = useState(false);

  if (mode === 'paper') {
    // Realized vs open separation (PORTFOLIO-PRUNE-1, 2026-11-02): closed net
    // P&L is the primary figure; open P&L is secondary and explicitly
    // unrealized. They are never combined into one headline number.
    const realized = s._api?.paper_pnl_realized != null ? Number(s._api.paper_pnl_realized) : null;
    const openPnl = s._api?.paper_pnl_unrealized != null ? Number(s._api.paper_pnl_unrealized) : null;
    const closedN = s.paperTrades ?? 0;
    // Thin forward sample: with <20 closed cost-true trades, WR/PF are noise,
    // not evidence — render them muted with an explicit insufficiency note.
    const thinSample = closedN < 20;
    const evidenceColor = thinSample ? 'var(--text-muted)' : undefined;
    const evidenceTip = thinSample
      ? `Insufficient forward sample — ${closedN} closed cost-true trade${closedN === 1 ? '' : 's'} (<20). Not validation evidence.`
      : undefined;
    // Non-strategy bookkeeping (CLEANSE-1, t_070590de): cleanse-closure and
    // stale-orphan flatten legs are excluded from every aggregate on this
    // block; the held-back amount is disclosed, never silently dropped.
    const nsLegs = s._api?.non_strategy_legs || 0;
    const nsPnl = s._api?.non_strategy_pnl;
    const nsPhantom = s._api?.non_strategy_phantom_positions || 0;
    const nsUnr = s._api?.non_strategy_unrealized;
    const skipRows = s._api?.paper_skips || [];
    const skipCount = s._api?.paper_skip_count || 0;
    const nsTip = [
      nsLegs ? `${nsLegs} closure leg${nsLegs === 1 ? '' : 's'} labeled RESET_STALE_SIGNAL/CLEANSE1_CLOSURE in the skip log — operator bookkeeping from the 2026-10-28 cleanse, not strategy performance` : null,
      nsPhantom ? `${nsPhantom} phantom ETL-cache position${nsPhantom === 1 ? '' : 's'} excluded from open P&L` : null,
    ].filter(Boolean).join(' · ');
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
    // Per-book paper deployment ratio (kanban t_786a7c6e; ETL
    // consumption.strategy_paper_deployment_current). NULL/absent (PAPER_UAT
    // or pre-run) → no chip, never 0%. Colour thresholds per spec: ≥98%
    // green, 90–98% amber, <90% red — this is the whole-lot + cap
    // quantization cash drag the badge exists to expose.
    const dep = s._api?.paper_deployment;
    const depPct = dep?.deployment_ratio != null ? Number(dep.deployment_ratio) * 100 : null;
    let depChip = null;
    if (depPct != null) {
      const depColor = depPct >= 98 ? 'emerald' : depPct >= 90 ? 'amber' : 'rose';
      const capPct = dep.max_position_pct != null ? `${Math.round(Number(dep.max_position_pct) * 100)}%` : '20%';
      const tipParts = [
        `committed $${Number(dep.committed_notional ?? 0).toLocaleString(undefined, { maximumFractionDigits: 0 })} of $${Number(dep.target_notional ?? 0).toLocaleString(undefined, { maximumFractionDigits: 0 })} target (whole-lot + ${capPct} cap drag)`,
      ];
      const cuPct = dep.capital_utilization != null ? Number(dep.capital_utilization) * 100 : null;
      if (cuPct != null && Math.abs(cuPct - depPct) >= 0.05) {
        tipParts.push(`capital utilization ${cuPct.toFixed(1)}% of assigned (gap incl. designed CASH residual)`);
      }
      const skips = Object.entries(dep.skips_by_kind || {});
      if (skips.length) tipParts.push(`skips: ${skips.map(([k, n]) => `${k} ×${n}`).join(', ')}`);
      if (dep.run_date) tipParts.push(`rebalancer run ${dep.run_date}`);
      depChip = (
        <span title={tipParts.join(' · ')} style={{ cursor: 'help' }}>
          <Chip color={depColor}>Deployed {depPct.toFixed(1)}%</Chip>
        </span>
      );
    }
    return (
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, minmax(0,1fr))', gap: '8px 8px', padding: '7px 8px', borderRadius: 'var(--radius-md)', background: 'rgba(255,255,255,0.02)' }}>
        <Metric label="Closed net P&L" value={realized != null ? fmtK(realized) : '—'} color={realized == null ? undefined : realized >= 0 ? 'var(--pnl-pos)' : 'var(--pnl-neg)'} big tip={`Realized P&L of ${closedN} closed trade${closedN === 1 ? '' : 's'}, net of the declared cost model, excl. non-strategy bookkeeping`} />
        <Metric label="Open P&L · unrealized" value={openPnl != null ? fmtK(openPnl) : '—'} color={openPnl == null ? undefined : openPnl >= 0 ? 'var(--pnl-pos)' : 'var(--pnl-neg)'} tip="Mark-to-market open book — NOT realized, not validation evidence" sub={s._api?.paper_open?.positions != null ? `${s._api.paper_open.positions} open` : null} />
        <Metric label="Win rate" value={s.paperWR != null ? `${s.paperWR}%` : '—'} color={thinSample ? evidenceColor : s.paperWR == null ? undefined : s.paperWR >= 50 ? 'var(--pnl-pos)' : 'var(--pnl-neg)'} big tip={evidenceTip} sub={`n=${closedN} closed`} />
        <Metric label="Profit factor" value={s.paperPF != null ? s.paperPF.toFixed(2) : '—'} big color={evidenceColor} tip={evidenceTip} sub={`n=${closedN} closed`} />
        <Metric label="Closed trades" value={s.paperTrades ?? '—'} />
        <Metric label="Monitoring" value={stateLabel} color={stateColor} />
        {thinSample && (s.paperWR != null || s.paperPF != null) && (
          <div style={{ gridColumn: '1 / -1', fontSize: 8, color: 'var(--text-muted)', lineHeight: 1.4 }}>
            Insufficient forward sample ({closedN} &lt; 20 closed) — WR/PF shown for reference, not evidence.
          </div>
        )}
        {depChip && <div style={{ gridColumn: '1 / -1' }}>{depChip}</div>}
        {(nsLegs > 0 || nsPhantom > 0) && (
          <div style={{ gridColumn: '1 / -1', fontSize: 8, color: 'var(--text-faint)', lineHeight: 1.4 }} title={nsTip}>
            excl. {nsPnl != null ? fmtK(nsPnl) : '—'} non-strategy bookkeeping{nsLegs ? ` (${nsLegs} cleanse-closure leg${nsLegs === 1 ? '' : 's'})` : ''}{nsPhantom ? ` · ${nsPhantom} phantom position${nsPhantom === 1 ? '' : 's'}${nsUnr != null ? ` (${fmtK(nsUnr)})` : ''}` : ''}
          </div>
        )}
        {skipCount > 0 && (
          <div style={{ gridColumn: '1 / -1' }}>
            <button
              onClick={(e) => { e.stopPropagation(); setSkipsOpen(!skipsOpen); }}
              style={{ border: 'none', cursor: 'pointer', padding: '1px 6px', borderRadius: 4, fontSize: 9, fontWeight: 700, background: 'rgba(100,116,139,0.25)', color: 'var(--text-secondary)' }}
              title="BUY signals the paper rebalancer could not fill — click for the per-ticker reasons"
            >{skipCount} unfilled {skipsOpen ? '▴' : '▾'}</button>
            {skipsOpen && (
              <div style={{ marginTop: 4, display: 'flex', flexDirection: 'column', gap: 2, maxHeight: 140, overflowY: 'auto' }}>
                {skipRows.slice(0, 12).map((sk, i) => (
                  <div key={i} style={{ fontSize: 8, color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }} title={sk.reason || ''}>
                    {sk.ticker} · {sk.skip_kind} · {sk.skip_date}{(sk.reason || '').length > 0 ? ` — ${(sk.reason || '').slice(0, 70)}` : ''}
                  </div>
                ))}
                {skipRows.length > 12 && <div style={{ fontSize: 8, color: 'var(--text-faint)' }}>+{skipRows.length - 12} more — open strategy detail</div>}
              </div>
            )}
          </div>
        )}
      </div>
    );
  }

  if (mode === 'uat') {
    // Broker rehearsal book: positions/fills live at the IBKR UAT session, not
    // in any DB ledger. Fills-based metrics (count, realized P&L, slippage)
    // arrive with the qr_etl mirror (kanban t_b64f7302) — render honest
    // pending slots until then, never backtest numbers dressed as rehearsal.
    return (
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, minmax(0,1fr))', gap: '8px 8px', padding: '7px 8px', borderRadius: 'var(--radius-md)', background: 'rgba(255,255,255,0.02)' }}>
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
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, minmax(0,1fr))', gap: '8px 8px', padding: '7px 8px', borderRadius: 'var(--radius-md)', background: 'rgba(255,255,255,0.02)' }}>
        <Metric label="P&L" value="—" big />
        <Metric label="Profit factor" value="—" big />
        <Metric label="Win rate" value="—" big />
        <Metric label="Trades" value="—" />
        <Metric label="Status" value={liveActive ? 'Active' : '—'} color={liveActive ? 'var(--pnl-pos)' : 'var(--text-muted)'} />
        <Metric label="Conviction" value={conviction != null ? Number(conviction).toFixed(1) : '—'} />
      </div>
    );
  }

  // Sim (backtest/OOS) block. returns_oos semantics differ per strategy (CAGR
  // on some runs, total return on others) and win-rate / trade-count bases
  // differ per strategy too (per month/day vs per leg/rebalance event) —
  // disclose both on tooltips instead of letting the numbers read as
  // directly comparable. Unit normalization is tracked upstream (qr_etl
  // t_fcfe5f4f); nothing is re-derived or estimated here.
  const oosStart = s._api?.oos_start || null;
  const oosEnd = s._api?.oos_end || null;
  const oosWinShort = oosStart && oosEnd ? `${oosStart.slice(0, 7)}→${oosEnd.slice(0, 7)}` : null;
  const oosTrades = s._api?.trade_count_oos;
  const btWRn = s.btWR != null ? Number(s.btWR) : null;
  // Non-integer WR×trades proves the WR base is not this trade count.
  const wrMixedBase = btWRn != null && oosTrades > 0
    && Math.abs((btWRn / 100) * oosTrades - Math.round((btWRn / 100) * oosTrades)) > 0.15;
  const returnTip = `Stored OOS return of the latest backtest run${oosStart && oosEnd ? `, window ${oosStart} → ${oosEnd}` : ''}. Annualization basis differs per strategy (CAGR on some, total return on others) — unit normalization tracked in qr_etl t_fcfe5f4f; compare strategies via the annual bars, not this number alone.`;
  const wrTip = `Win rate over this strategy's own OOS base (per trade / month / day — set by each run's convention).${wrMixedBase ? ' For this strategy the base is NOT the trade count shown, so WR × trades is not an integer.' : ''} Not directly comparable across strategies.`;
  const tradesTip = 'OOS trade/event count from the latest backtest run; counting convention (legs vs rebalance events) differs per strategy.';
  return (
    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, minmax(0,1fr))', gap: '8px 8px', padding: '7px 8px', borderRadius: 'var(--radius-md)', background: 'rgba(255,255,255,0.02)' }}>
      <Metric label="Return (BT)" value={s.returns != null ? `${s.returns >= 0 ? '+' : ''}${s.returns}%` : '—'} color={s.returns == null ? undefined : s.returns >= 0 ? 'var(--pnl-pos)' : 'var(--pnl-neg)'} big tip={returnTip} sub={oosWinShort ? `OOS ${oosWinShort}` : null} />
      <Metric label="Sharpe" value={s.sharpe ? s.sharpe.toFixed(2) : '—'} big />
      <Metric label="Win rate" value={s.btWR != null ? `${s.btWR}%` : '—'} color={s.btWR == null ? undefined : s.btWR >= 50 ? 'var(--pnl-pos)' : 'var(--pnl-neg)'} big tip={wrTip} />
      <Metric label="Max DD" value={s.dd != null ? `${s.dd}%` : '—'} color="var(--pnl-neg)" />
      <Metric label="Trades (OOS)" value={s._api?.trade_count_oos ?? '—'} tip={tradesTip} />
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
  // CLEANSE-1 (t_070590de): halted books (registry paused/retired; PENDING is
  // stored as paused + 'PENDING —' reason prefix) render their status label +
  // operator reason on the card and get no ladder CTAs — never implied live.
  const halted = haltedLabel(s._api?.registry_status || s._api?.status, s._api?.retirement_reason);
  const NEXT_CTA = { PAPER_TRADING: 'Promote to Paper →', UAT: 'Promote to UAT →', LIVE_TRADING: 'Deploy Live →' };
  const oosStart = s._api?.oos_start || null;
  const oosEnd = s._api?.oos_end || null;
  const barsLabel = viewMode === 'paper' ? 'Paper returns · % of assigned capital (solid realized · outline open book)'
    : viewMode === 'live' ? 'Live returns'
    : viewMode === 'uat' ? 'Broker rehearsal — fills-based metrics pending qr_etl mirror'
    : (oosStart && oosEnd ? `Annual returns · OOS ${oosStart.slice(0, 7)}→${oosEnd.slice(0, 7)}` : 'Annual backtest returns');
  // Bars honesty legend (sim): hatched = in-sample year (before OOS start),
  // YTD = partial year through the window end, and OOS years with no stored
  // annual return stay absent rather than estimated (book-level annual
  // recompute tracked in qr_etl t_fcfe5f4f).
  const barsTip = viewMode === 'sim'
    ? 'Calendar-year returns of the latest backtest run. Hatched bar (·IS) = in-sample year before the OOS window. YTD = partial year through the window end. OOS years with no bar have no stored annual return — recompute in progress (qr_etl t_fcfe5f4f), never estimated.'
    : undefined;
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
            <Chip color={STAGE_CHIP[s.stage]}>{halted ? halted.k : s.stage.replace('_', ' ')}</Chip>
            <span style={{ fontSize: 9, color: 'var(--text-muted)' }}>{s.asset}</span>
          </div>
          {halted && halted.reason && (
            <div style={{ fontSize: 8, color: 'var(--text-muted)', lineHeight: 1.35, marginTop: 3, display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical', overflow: 'hidden' }} title={halted.reason}>
              {halted.reason}
            </div>
          )}
        </div>
        <ModeBadge mode={s.mode} />
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
        <Chip color={hz.color}>{hz.label}</Chip>
        <Chip color={s.tier === 'T1' ? 'emerald' : s.tier === 'T2' ? 'amber' : 'slate'}>{s.tier}</Chip>
        {viewMode === 'paper' && s._api?.paper_tier && (
          <span title={s._api.paper_tier_blocker || undefined} style={{ cursor: 'help' }}>
            <Chip color={s._api.paper_tier === 'CORE_PAPER' ? 'emerald' : 'slate'}>{s._api.paper_tier === 'CORE_PAPER' ? 'CORE' : 'WATCH'}</Chip>
          </span>
        )}
        {live && s.trades > 0 && <span style={{ marginLeft: 'auto', fontFamily: 'var(--font-mono)', fontSize: 9, color: 'var(--pnl-pos)' }}>{s.trades} live trades</span>}
      </div>

      <RealMetrics s={s} mode={viewMode} />

      <div style={{ padding: '7px 8px', borderRadius: 'var(--radius-md)', background: 'rgba(255,255,255,0.02)', display: 'flex', flexDirection: 'column', gap: 6 }}>
        <span style={{ fontSize: 8, textTransform: 'uppercase', letterSpacing: '0.06em', color: 'var(--text-muted)' }} title={barsTip}>{barsLabel}</span>
        <YearlyBars yearly={barsData} normalize={barsNormalize} openBar={openBar} oosStart={viewMode === 'sim' ? oosStart : null} oosEnd={viewMode === 'sim' ? oosEnd : null} emptyLabel={viewMode === 'paper' ? 'No closed paper trades yet' : viewMode === 'live' ? 'No live returns yet' : viewMode === 'uat' ? 'Book lives at the IBKR UAT session — see Execution → UAT' : undefined} />
      </div>

      {showLadder && !halted && (
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
  // Archive registry (PORTFOLIO-PRUNE-1): drives the Archive tab and the
  // Archived count on the summary strip.
  const [archive, setArchive] = useState(null);
  const [archiveError, setArchiveError] = useState(false);
  const loadArchive = useCallback(async () => {
    const r = await api.get('/api/strategies/archive');
    if (r == null) { setArchiveError(true); return; }
    setArchiveError(false);
    setArchive(r);
  }, []);
  usePoll(loadArchive, 60000);
  if (!book) return <Placeholder label={error ? 'Could not load strategies — backend unreachable.' : 'Loading strategies…'} />;

  // Counts and asset options reflect ACTIVE books only — archived/halted rows
  // are excluded from active strategy counts (their home is the Archive tab).
  const activeBook = book.filter((s) => s.stage !== 'halted');
  const counts = { all: activeBook.length, day: 0, swing: 0, position: 0 };
  activeBook.forEach((s) => { counts[s.horizon] = (counts[s.horizon] || 0) + 1; });
  // Mode ladder (cumulative): Sim shows every ACTIVE strategy, Paper shows
  // paper/uat/live deployments, UAT shows rehearsal + live, Live shows live
  // capital only. Halted rows (registry paused/retired, incl. archived books)
  // are excluded from every active view and every ranking — their home is the
  // Archive tab.
  const ACTIVE_ONLY = (s) => s.stage !== 'halted';
  const MODE_FILTER = {
    sim: ACTIVE_ONLY,
    paper: (s) => ACTIVE_ONLY(s) && (s.mode === 'PAPER_TRADING' || s.mode === 'UAT' || s.mode === 'LIVE_TRADING'),
    uat: (s) => ACTIVE_ONLY(s) && (s.mode === 'UAT' || s.mode === 'LIVE_TRADING'),
    live: (s) => s.mode === 'LIVE_TRADING',
  };

  // Asset-class options from the classes actually present in the active book.
  const assetCounts = { all: activeBook.length };
  activeBook.forEach((s) => { const k = s.assetClass || 'EQUITY'; assetCounts[k] = (assetCounts[k] || 0) + 1; });
  const assetOpts = ['all', ...Object.keys(assetCounts).filter((k) => k !== 'all').sort()];

  const src = book
    .filter((s) => hzn === 'all' || s.horizon === hzn)
    .filter(MODE_FILTER[perfMode] || (() => true))
    .filter((s) => assetFilter === 'all' || (s.assetClass || 'EQUITY') === assetFilter);

  const SORTS = {
    sim: [{ k: 'returns', l: 'Return' }, { k: 'sharpe', l: 'Sharpe' }, { k: 'btWR', l: 'Win rate' }, { k: 'trades', l: 'Trades' }],
    paper: [{ k: 'paperRealized', l: 'Closed P&L' }, { k: 'paperPF', l: 'Profit factor' }, { k: 'paperWR', l: 'Win rate' }, { k: 'paperTrades', l: 'Trades' }],
    uat: [{ k: 'returns', l: 'Return' }, { k: 'btWR', l: 'Win rate' }, { k: 'trades', l: 'Trades' }],
    live: [{ k: 'returns', l: 'Return' }, { k: 'btWR', l: 'Win rate' }, { k: 'trades', l: 'Trades' }],
  };

  // keep sort key valid across mode switches
  const currentSorts = SORTS[perfMode] || SORTS.sim;
  const effectiveSort = currentSorts.find((o) => o.k === sortKey) ? sortKey : currentSorts[0].k;
  const sortVal = (s, k) => (k === 'paperRealized' ? (s._api?.paper_pnl_realized ?? null) : s[k]);

  const sorted = [...src].sort((a, b) => (sortVal(b, effectiveSort) ?? -Infinity) - (sortVal(a, effectiveSort) ?? -Infinity));
  const liveN = book.filter((s) => s.mode === 'LIVE_TRADING' && s.stage !== 'halted').length;

  // Summary strip (PORTFOLIO-PRUNE-1): active potential vs archived history.
  // Counts come from the active book tiers, not average win rates over tiny
  // samples. Archived = archive registry size.
  const activePaper = book.filter((s) => s.stage !== 'halted' && (s.mode === 'PAPER_TRADING' || s.mode === 'UAT' || s.mode === 'LIVE_TRADING'));
  const coreN = activePaper.filter((s) => s._api?.paper_tier === 'CORE_PAPER').length;
  const watchN = activePaper.filter((s) => s._api?.paper_tier === 'WATCH_PAPER').length;
  const archivedN = archive?.count ?? null;

  // Headline rankings — evidence-first (2026-11-02):
  //  - Sim: best OOS return among ACTIVE, non-halted books only (archived and
  //    PENDING/DATA_BLOCKED books never headline, even when their stored
  //    backtest return is the biggest number on the page).
  //  - Paper: "Best validated book" — eligible only for CORE_PAPER with >=20
  //    closed cost-true trades; ranked on closed net (realized) P&L. Open
  //    (unrealized) gains never win a headline. "—" when nothing qualifies.
  const simBest = perfMode === 'sim'
    ? [...src].filter((s) => s.returns != null).sort((a, b) => b.returns - a.returns)[0]
    : null;
  const validated = [...src].filter((s) => s._api?.paper_tier === 'CORE_PAPER' && (s.paperTrades ?? 0) >= 20 && s._api?.paper_pnl_realized != null)
    .sort((a, b) => Number(b._api.paper_pnl_realized) - Number(a._api.paper_pnl_realized));
  const bestValidated = perfMode === 'paper' ? (validated[0] || null) : null;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
      <div style={{ display: 'flex', alignItems: 'flex-end', justifyContent: 'space-between', flexWrap: 'wrap', gap: 8 }}>
        <div>
          <h2 style={{ margin: 0, fontSize: 14, fontWeight: 700, color: 'var(--text-strong)' }}>Performance</h2>
          <p style={{ margin: '2px 0 0', fontSize: 10, color: 'var(--text-muted)' }}>Backtest, paper &amp; live metrics from the strategy registry · click a card for full detail</p>
        </div>
        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
          <ModeSeg mode={perfMode} setMode={setPerfMode} />
          {perfMode !== 'archive' && (
            <>
              <AssetSeg asset={assetFilter} setAsset={setAssetFilter} opts={assetOpts} counts={assetCounts} />
              <HorizonSeg hzn={hzn} setHzn={setHzn} counts={counts} />
            </>
          )}
        </div>
      </div>

      <div className="strat-kpi-grid">
        <KpiTile label="Active Core" value={coreN} sub="CORE_PAPER · probation binding" />
        <KpiTile label="Watch" value={watchN} sub="WATCH_PAPER · blocker open" />
        <KpiTile label="Archived" value={archivedN ?? '—'} sub="evidence record · excluded from rankings" />
        <KpiTile label="Live" value={liveN} pos={liveN > 0} />
      </div>

      {perfMode === 'archive' ? (
        <ArchivePanel data={archive} error={archiveError} onOpen={onOpen} />
      ) : (
        <>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 6, flexWrap: 'wrap' }}>
            <span style={{ fontSize: 9, color: 'var(--text-faint)' }}>
              {perfMode === 'sim' && (simBest
                ? <>Best OOS return (active only): <b style={{ color: 'var(--text-secondary)' }}>{simBest.name} <span style={{ fontFamily: 'var(--font-mono)' }}>{fmtPct(simBest.returns)}</span></b></>
                : 'Best OOS return: —')}
              {perfMode === 'paper' && (bestValidated
                ? <>Best validated book: <b style={{ color: 'var(--text-secondary)' }}>{bestValidated.name} <span style={{ fontFamily: 'var(--font-mono)' }}>{fmtK(Number(bestValidated._api.paper_pnl_realized))} closed net</span></b></>
                : 'Best validated book: — (no CORE_PAPER book with ≥20 closed cost-true trades)')}
              {(perfMode === 'uat' || perfMode === 'live') && 'Headline rankings populate when the book has realized history.'}
            </span>
            <span style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              <span style={{ fontSize: 9, color: 'var(--text-faint)' }}>Sort</span>
              <div className="strat-seg" style={{ display: 'flex', gap: 2, padding: 3, borderRadius: 'var(--radius-md)', background: 'rgba(15,23,42,0.5)', border: '1px solid var(--border-glass)' }}>
                {currentSorts.map((o) => (
                  <button key={o.k} onClick={() => setSortKey(o.k)} style={{ padding: '4px 9px', borderRadius: 'var(--radius-sm)', border: 'none', cursor: 'pointer', fontSize: 10, fontWeight: 700, background: sortKey === o.k ? 'var(--primary)' : 'transparent', color: sortKey === o.k ? '#fff' : 'var(--text-secondary)' }}>{o.l}</button>
                ))}
              </div>
            </span>
          </div>

          {sorted.length === 0
            ? <Placeholder label="No strategies match these filters." hint="Try another mode, asset class, or horizon — or deploy strategies from the Lab." />
            : <div className="strat-card-grid">
                {sorted.map((s) => <StrategyCard key={s.id} s={s} onOpen={onOpen} onAction={onAction} showLadder={false} viewMode={perfMode} />)}
              </div>}
        </>
      )}
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

      <div className="strat-pipeline-grid">
        {LADDER.map((st) => {
          // Halted books (registry paused/retired) never sit in a live lane —
          // they render in the Halted lane below with their reason.
          const items = view.filter((s) => s.mode === st.mode && s.stage !== 'halted');
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
        {(() => {
          const haltedItems = view.filter((s) => s.stage === 'halted');
          if (!haltedItems.length) return null;
          return (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '6px 4px' }}>
                <span style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                  <Chip color="rose">Halted</Chip>
                  <span style={{ fontSize: 9, color: 'var(--text-faint)' }}>registry paused / pending / retired — not trading</span>
                </span>
                <span style={{ fontFamily: 'var(--font-mono)', fontSize: 12, fontWeight: 700, color: 'var(--text-secondary)' }}>{haltedItems.length}</span>
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 8, minHeight: 60, padding: 6, borderRadius: 'var(--radius-lg)', background: 'rgba(255,255,255,0.012)', border: '1px solid var(--border-glass)' }}>
                {haltedItems.map((s) => <StrategyCard key={s.id} s={s} onOpen={onOpen} onAction={onAction} showLadder={false} viewMode="paper" />)}
              </div>
            </div>
          );
        })()}
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
