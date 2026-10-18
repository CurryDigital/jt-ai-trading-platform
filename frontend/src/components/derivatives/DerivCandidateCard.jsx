import { Chip, Button, pnlColor } from '../jtkit';
import { Metric } from '../StrategiesWorkspace';
import { DerivTable, DerivResearchOnlyChip, DerivThinSampleChip } from './shared.jsx';
import { fpct, fpctBare, fmdd, variantLabel, oosCoversNamedStress, PUBLISHABLE_MIN_TRADES } from './format.js';

// DerivCandidateCard — a derivatives research candidate WITH backtest runs,
// rendered with the same anatomy as the HK IPO STRATEGIES card
// (IpoTab.IpoStrategyCard): header + chips, six-metric grid, variants
// mini-table, SIM/PAPER/UAT/LIVE ladder, verbatim rules, ledger line,
// "View detail" only (no allocation/pause/enrol — derivatives has no capital
// and no order route; stage tabs beyond SIM stay inert by design).
//
// NEW component, one-line justification: IpoStrategyCard itself is wired to
// equity-registry props (evaluation endpoint, mirror cohort, capital fields)
// and cannot render a derivatives run set; this card reuses its exact
// building blocks (jtkit Chip/Button, Metric from StrategiesWorkspace,
// DerivTable) instead of copying markup.
//
// Basis honesty: stored headline metrics are TOTAL-basis (rf=0, T-bill cash
// carry included — parameters_used.basis_label); option-only figures come
// from parameters_used.option_only and are shown per-variant so the
// carry-free read is one glance away. Per-year bars are intentionally
// absent: annual returns derive from gold.derivatives_backtest_trades, which
// is empty (aggregate-only runs) — bars mount once real per-year data exists.

// Headline run = the V1 variant (candidate under evaluation). The twin is the
// baseline — it stays in the variants table, never the headline (2026-10-18,
// operator). Falls back to lowest run_number when no V1 exists.
const headlineRun = (r) =>
  (r.runs || []).find(v => (v.variant || '').toLowerCase() === 'v1') || (r.runs || [])[0] || null;

const money = (v) => v == null ? '—' : `${Number(v) >= 0 ? '+' : '−'}$${Math.abs(Number(v)).toLocaleString('en-US', { maximumFractionDigits: 0 })}`;

// IPO-card thresholds: Win green >= 50%, returns/MDD signed colours, Sharpe
// neutral, and nothing green while PF < 1.
const VARIANT_COLS = [
  { label: 'Variant', tip: 'parameters_used.variant — variants of the one run of record. A "thin" tag marks a variant under the 30-episode publishable gate.',
    render: r => (
      <span style={{ display: 'inline-flex', alignItems: 'center', gap: 4 }}>
        {variantLabel(r.variant)}
        {r.episodes_oos != null && r.episodes_oos < PUBLISHABLE_MIN_TRADES && (
          <span className="qr-chip qr-chip-slate" title={`Thin sample: ${r.episodes_oos} independent OOS episodes < ${PUBLISHABLE_MIN_TRADES} (publishable gate threshold applied to episodes)`}>thin</span>
        )}
      </span>
    ), cl: 'text-slate-200 font-mono', width: 58 },
  { label: 'Sharpe · tot', tip: 'OOS Sharpe, TOTAL basis (carry-inclusive)', render: r => r.sharpe_oos != null ? Number(r.sharpe_oos).toFixed(2) : null, cl: 'text-slate-300 font-mono', num: true },
  { label: 'Sharpe · opt', tip: 'OOS Sharpe, OPTION-ONLY basis (no cash carry) — parameters_used.option_only.OOS.sharpe', render: r => r.option_only?.OOS?.sharpe != null ? Number(r.option_only.OOS.sharpe).toFixed(2) : null, cl: 'text-slate-300 font-mono', num: true },
  { label: 'PF', tip: 'OOS profit factor as stored (total-basis run metric). Never green below 1.0.',
    render: r => r.profit_factor_oos != null ? Number(r.profit_factor_oos).toFixed(2) : null,
    cl: r => (r.profit_factor_oos != null && r.profit_factor_oos >= 1 ? 'text-emerald-400' : 'text-slate-300') + ' font-mono', num: true },
  { label: 'MDD · tot', tip: 'OOS max drawdown, TOTAL basis (fraction → %)', render: r => fmdd(r.max_drawdown_oos, 2), cl: 'text-rose-400 font-mono', num: true },
  { label: 'MDD · opt', tip: 'OOS max drawdown, OPTION-ONLY basis, % of NAV', render: r => fmdd(r.option_only?.OOS?.maxdd_pct_nav, 2), cl: 'text-rose-400 font-mono', num: true },
  { label: 'Trades', tip: 'OOS trade count', key: 'trade_count_oos', cl: 'text-slate-300 font-mono', num: true },
  { label: 'Episodes', tip: 'Independent (non-overlapping) OOS episodes from the trade ledger — pending while gold.derivatives_backtest_trades is empty',
    render: r => r.episodes_oos ?? 'pending', cl: r => r.episodes_oos == null ? 'text-slate-500 font-mono' : 'text-slate-300 font-mono', num: true },
];

function Ladder({ hasRuns }) {
  const cells = [
    { k: 'sim', label: 'SIM', value: hasRuns ? 'Backtest' : '—',
      sub: hasRuns ? 'research-only · forward SIM: not enabled' : 'no run yet' },
    { k: 'paper', label: 'PAPER', value: '—', sub: 'not reached' },
    { k: 'uat', label: 'UAT', value: '—', sub: 'not reached' },
    { k: 'live', label: 'LIVE', value: '—', sub: 'not reached' },
  ];
  return (
    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4,minmax(0,1fr))', gap: 4 }}>
      {cells.map(c => (
        <div key={c.k} style={{ padding: '5px 7px', borderRadius: 'var(--radius-md)', background: 'rgba(255,255,255,0.02)', boxShadow: c.k === 'sim' ? 'inset 0 0 0 1px var(--border-strong)' : 'none' }}
          title={c.k === 'sim'
            ? 'Research backtest only — no forward simulation is enabled for derivatives, and there is no capital, no enrolment, and no order route.'
            : 'Stage not reached — derivatives stages beyond SIM stay inert.'}>
          <div style={{ fontSize: 8, textTransform: 'uppercase', letterSpacing: '0.06em', color: 'var(--text-muted)', display: 'flex', justifyContent: 'space-between', gap: 4 }}>
            <span>{c.label}</span>{c.k === 'sim' && hasRuns && <span style={{ color: 'var(--text-secondary)' }}>ACTIVE</span>}
          </div>
          <div style={{ fontFamily: 'var(--font-mono)', fontSize: 11, fontWeight: 700, color: 'var(--text-secondary)', marginTop: 2 }}>{c.value}</div>
          <div style={{ fontSize: 8, color: 'var(--text-faint)', marginTop: 1 }}>{c.sub}</div>
        </div>
      ))}
    </div>
  );
}

export function DerivCandidateCard({ r, onViewRuns, basis = 'opt' }) {
  const h = headlineRun(r);
  const kills = Array.isArray(r.kill_conditions) ? r.kill_conditions : [];
  const optOos = h?.option_only?.OOS || {};
  const opt = basis === 'opt';
  const noStress = h ? !oosCoversNamedStress(h.oos_start, h.oos_end) : false;
  // Thin-sample keying: the MINIMUM episode count across variants decides
  // (weakest variant, not the headline twin). Null when no run has episodes.
  const epValues = (r.runs || []).map(v => v.episodes_oos).filter(v => v != null);
  const minEp = epValues.length ? Math.min(...epValues) : null;
  const minEpVariant = minEp != null
    ? (r.runs.find(v => v.episodes_oos === minEp)?.variant) : null;

  return (
    <div className="jt-surface" style={{ padding: 12, display: 'flex', flexDirection: 'column', gap: 9, marginTop: 8 }}>
      {/* header — name + chips (IPO card layout) */}
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 8 }}>
        <div style={{ minWidth: 0 }}>
          <div style={{ fontSize: 12, fontWeight: 700, color: 'var(--text-strong)' }}>{r.name || r.strategy_id}</div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginTop: 4, flexWrap: 'wrap' }}>
            <Chip color="slate">{String(r.status || '—').toUpperCase()}</Chip>
            {r.phase && r.phase !== r.status && <Chip color="slate">{r.phase}</Chip>}
            <Chip color="slate">{r.instrument || '—'}</Chip>
            {r.evidence_class && <Chip color="slate">{r.evidence_class}</Chip>}
            <DerivResearchOnlyChip />
            {h && <DerivThinSampleChip episodes={minEp} variant={minEpVariant ? variantLabel(minEpVariant) : undefined} />}
          </div>
        </div>
        <span style={{ fontFamily: 'var(--font-mono)', fontSize: 9, color: 'var(--text-faint)' }}>{r.strategy_id}</span>
      </div>

      {/* six-metric grid + episodes — V1 headline on the shared basis toggle;
          win rate neutral (2026-10-18: 53-58% win with negative option-only
          P&L must not read green — colour lives on PF and P&L) */}
      {h && (
        <div style={{ padding: '7px 8px', borderRadius: 'var(--radius-md)', background: 'rgba(255,255,255,0.02)' }}>
          <div style={{ fontSize: 8, textTransform: 'uppercase', letterSpacing: '0.06em', color: 'var(--text-faint)', marginBottom: 5 }}
            title={`Headline = ${variantLabel(h.variant)} variant — the candidate under evaluation (run ${h.run_label || h.run_id.slice(0, 8)}); the twin is the baseline, in the variants table. Basis = ${opt ? 'OPTION-ONLY (no cash carry)' : `TOTAL (rf=0, T-bill cash carry included — ${h.basis_label || 'see run params'})`} from the shared toggle. RESEARCH-ONLY evidence class — no capital, no forward SIM.`}>
            Backtest · OOS {String(h.oos_start || '—').slice(0, 7)}→{String(h.oos_end || '—').slice(0, 7)} · {variantLabel(h.variant)} · {opt ? 'option-only' : 'total-basis (carry-incl)'} · research-only
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, minmax(0,1fr))', gap: '8px 8px' }}>
            {opt ? (
              <Metric label="Sharpe · opt" value={optOos.sharpe != null ? Number(optOos.sharpe).toFixed(2) : '—'} big
                tip="OPTION-ONLY basis: option legs alone, no T-bill carry." sub={h.sharpe_oos != null ? `tot ${Number(h.sharpe_oos).toFixed(2)}` : undefined} />
            ) : (
              <Metric label="Sharpe · tot" value={h.sharpe_oos != null ? Number(h.sharpe_oos).toFixed(2) : '—'} big
                tip="TOTAL basis (carry-inclusive). Option-only: see variants table." sub={optOos.sharpe != null ? `opt ${Number(optOos.sharpe).toFixed(2)}` : undefined} />
            )}
            {opt ? (
              <Metric label="Opt P&L" value={money(optOos.pnl_usd)} color={optOos.pnl_usd == null ? undefined : pnlColor(optOos.pnl_usd)} big
                tip="OPTION-ONLY basis: option-leg P&L in $ (no return fraction stored for this basis)." sub={h.returns_oos != null ? `tot ${fpct(h.returns_oos, 2)}` : undefined} />
            ) : (
              <Metric label="OOS ret · tot" value={fpct(h.returns_oos, 2) ?? '—'} color={h.returns_oos == null ? undefined : pnlColor(h.returns_oos)} big
                tip="TOTAL basis OOS return (fraction → %). Option-only stores P&L $, not a return fraction." sub={optOos.pnl_usd != null ? `opt ${money(optOos.pnl_usd)}` : undefined} />
            )}
            <Metric label="Win" value={fpctBare(h.win_rate_oos, 1) ?? '—'} big
              tip="OOS win rate (basis-invariant). Neutral colour — a 53-58% win rate with negative option-only P&L is not green (2026-10-18). Colour lives on PF and P&L." />
            {opt ? (
              <Metric label="MDD · opt" value={optOos.maxdd_pct_nav != null ? fmdd(optOos.maxdd_pct_nav, 2) : '—'} color="var(--pnl-neg)" big
                tip="OPTION-ONLY basis OOS max drawdown, % of NAV" sub={h.max_drawdown_oos != null ? `tot ${fmdd(h.max_drawdown_oos, 2)}` : undefined} />
            ) : (
              <Metric label="MDD · tot" value={fmdd(h.max_drawdown_oos, 2) ?? '—'} color="var(--pnl-neg)" big
                tip="TOTAL basis OOS max drawdown" sub={optOos.maxdd_pct_nav != null ? `opt ${fmdd(optOos.maxdd_pct_nav, 2)} NAV` : undefined} />
            )}
            <Metric label="Profit factor" value={h.profit_factor_oos != null ? Number(h.profit_factor_oos).toFixed(2) : '—'}
              color={h.profit_factor_oos != null && h.profit_factor_oos >= 1 ? 'var(--pnl-pos)' : undefined}
              tip="OOS profit factor as stored (total-basis run metric — no option-only split stored). Never green below 1.0." />
            <Metric label="OOS trades" value={h.trade_count_oos ?? '—'} tip="OOS trade count" />
            <Metric label="Episodes" value={h.episodes_oos ?? 'pending'}
              tip="Independent (non-overlapping) OOS episodes — computed from gold.derivatives_backtest_trades, which is empty (aggregate-only runs, qr_research t_84d15809). Pending, never a fabricated 0. Thin-sample gating keys on this count (threshold 30, the publishable gate)." />
          </div>
          {noStress && (
            <div style={{ fontSize: 9, color: 'var(--text-faint)', marginTop: 5 }}>
              OOS window {h.oos_start}→{h.oos_end} contains no named stress episode (no COVID-2020 / 2022 bear) — stress evidence accrues forward only.
            </div>
          )}
        </div>
      )}

      {/* variants mini-table — both bases, PF comparable at a glance */}
      {(r.runs || []).length > 1 && (
        <div style={{ padding: '7px 8px', borderRadius: 'var(--radius-md)', background: 'rgba(255,255,255,0.02)' }}>
          <div style={{ fontSize: 8, textTransform: 'uppercase', letterSpacing: '0.06em', color: 'var(--text-faint)', marginBottom: 5 }}
            title="Every variant of the run of record, both bases side by side: tot = carry-inclusive headline; opt = option legs only (no T-bill carry).">
            Variants · {r.runs.length} · both bases
          </div>
          <DerivTable cols={VARIANT_COLS} rows={r.runs} rowKey={v => v.run_id} empty="No variant rows." />
        </div>
      )}

      {/* SIM/PAPER/UAT/LIVE ladder — IPO card pattern, stages beyond SIM inert */}
      <Ladder hasRuns={!!h} />

      {/* rules — verbatim from the research-owned registry fields */}
      {(r.entry_logic || r.exit_logic) && (
        <div style={{ padding: '7px 8px', borderRadius: 'var(--radius-md)', background: 'rgba(255,255,255,0.02)', fontSize: 9, color: 'var(--text-muted)', lineHeight: 1.55 }}>
          {r.entry_logic && (
            <div title={r.entry_logic}>
              <span style={{ fontSize: 8, textTransform: 'uppercase', letterSpacing: '0.06em', color: 'var(--text-faint)' }}>Buy — </span>
              {r.entry_logic}
            </div>
          )}
          {r.exit_logic && (
            <div style={{ marginTop: 3 }} title={r.exit_logic}>
              <span style={{ fontSize: 8, textTransform: 'uppercase', letterSpacing: '0.06em', color: 'var(--text-faint)' }}>Sell — </span>
              {r.exit_logic}
            </div>
          )}
          {kills.length > 0 && (
            <div style={{ marginTop: 3 }} title={kills.join('\n')}>
              <span style={{ fontSize: 8, textTransform: 'uppercase', letterSpacing: '0.06em', color: 'var(--text-faint)' }}>Kill — </span>
              {kills.join(' · ')}
            </div>
          )}
        </div>
      )}

      {/* next gate — display only, verbatim from data_blocker (research-owned) */}
      {r.data_blocker && (
        <div style={{ fontSize: 9, color: 'var(--text-muted)', lineHeight: 1.5 }} title={r.data_blocker}>
          <span style={{ fontSize: 8, textTransform: 'uppercase', letterSpacing: '0.06em', color: 'var(--text-faint)' }}>Next gate — </span>
          {r.data_blocker}
        </div>
      )}

      {/* ledger line — same one-liner pattern as the IPO card */}
      <div style={{ fontSize: 9, color: 'var(--text-muted)', lineHeight: 1.5 }}>
        Ledger: {(r.runs || []).length} run{(r.runs || []).length === 1 ? '' : 's'} · trade-level rows pending (gold.derivatives_backtest_trades empty) — annual bars mount when per-year data exists.
      </div>

      {/* View detail ONLY — no Adjust allocation / Pause / Enrol / order action */}
      <div style={{ display: 'flex', gap: 6 }}>
        <Button variant="primary" size="sm" style={{ flex: 1 }} onClick={() => onViewRuns && onViewRuns(r)}
          title="Open this strategy's backtest runs (Derivatives ▸ Backtest)">
          View detail ↗
        </Button>
      </div>
    </div>
  );
}
