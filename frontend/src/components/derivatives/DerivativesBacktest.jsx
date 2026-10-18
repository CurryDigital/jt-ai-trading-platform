import { useEffect, useMemo, useState } from 'react';
import { api, fmtK, fmtNum, fmtTime, pnlCl } from '../../utils.js';
import {
  DerivPanel, DerivEmptyState, DerivKpiStrip, DerivTable, DerivChipFilter,
  DerivResearchOnlyChip,
  TASK_DERIV_LEDGERS,
} from './shared.jsx';
import { fpct, fpctBare, fmdd, variantLabel, oosCoversNamedStress } from './format.js';

// Derivatives ▸ Backtest — backtest runs for derivative strategies.
// Phase 2 (2026-10-02, t_d67907e4): LIVE on GET /api/derivatives/backtests
// (gold.derivatives_backtest_runs, qr_etl t_15d7e66a).
// derivatives_page_alignment_v1 (2026-10-17): platform-aligned look —
// data-derived tile subtitles, Variant column from run params, percent
// formatting (stored units are fractions), IS+OOS windows, and a basis
// toggle (total / option-only, default option-only) because the stored
// headline sharpe/returns/mdd are TOTAL-BASIS (rf=0, T-bill cash carry
// included) while parameters_used.option_only carries the carry-free
// option-leg figures — every metric column is labelled with its basis.
// Run Detail renders the equity curve + trade ledger strictly from
// gold.derivatives_backtest_trades; that table is EMPTY as of 2026-10-17
// (runs landed aggregate-only), so the drill-down shows the honest empty
// state (kanban filed to qr_research).

const TRADE_COLS = [
  { label: 'Window', tip: 'IS (in-sample) / OOS (out-of-sample) by entry date vs the run windows',
    render: r => r.window || null,
    cl: r => r.window === 'OOS' ? 'text-slate-200 font-mono' : 'text-slate-500 font-mono', width: 52 },
  { label: 'Contract', tip: 'Full contract id', key: 'contract', cl: 'text-slate-200 font-mono' },
  { label: 'Side', tip: 'BUY / SELL', key: 'side',
    cl: r => r.side === 'BUY' ? 'text-emerald-400' : r.side === 'SELL' ? 'text-rose-400' : 'text-slate-300' },
  { label: 'Qty', tip: 'Contracts', render: r => fmtNum(r.qty, 0), cl: 'text-slate-300 font-mono', num: true },
  { label: 'Entry', tip: 'Entry date · price', render: r => `${r.entry_date || '—'} @ ${fmtNum(r.entry_price)}`, cl: 'text-slate-300 font-mono' },
  { label: 'Exit', tip: 'Exit date · price', render: r => r.exit_date ? `${r.exit_date} @ ${fmtNum(r.exit_price)}` : null, cl: 'text-slate-300 font-mono' },
  { label: 'P&L', tip: 'Realized P&L ($, net of recorded fees)', render: r => r.pnl == null ? null : fmtK(r.pnl),
    cl: r => pnlCl(r.pnl) + ' font-mono', num: true },
  { label: 'P&L %', tip: 'P&L % as recorded — unit contract pins with the first ledger rows', render: r => fmtNum(r.pnl_pct), cl: 'text-slate-300 font-mono', num: true },
  { label: 'Status', tip: 'Trade status', key: 'status' },
];

// Option-only money (parameters_used.option_only.*.pnl_usd) — signed dollars.
const money = (v) => v == null ? null : `${Number(v) >= 0 ? '+' : '−'}$${Math.abs(Number(v)).toLocaleString('en-US', { maximumFractionDigits: 0 })}`;

// Cumulative realized P&L curve — derived_from_trades (labeled server-side).
function DerivCurve({ points }) {
  const clean = (points || []).filter(p => p.cum_pnl != null);
  if (clean.length < 2) {
    return <DerivEmptyState line="Not enough closed trades to draw a curve." sub="Curve derives from gold.derivatives_backtest_trades exit dates." />;
  }
  const w = 600, h = 140, padL = 48, padB = 18, padT = 8, padR = 8;
  const vals = clean.map(p => p.cum_pnl);
  const min = Math.min(...vals), max = Math.max(...vals), range = (max - min) || 1;
  const x = i => padL + (i / (clean.length - 1)) * (w - padL - padR);
  const y = v => padT + (1 - (v - min) / range) * (h - padT - padB);
  const pts = clean.map((p, i) => `${x(i)},${y(p.cum_pnl)}`).join(' ');
  const last = vals[vals.length - 1];
  const stroke = last >= 0 ? '#34d399' : '#fb7185';
  return (
    <svg viewBox={`0 0 ${w} ${h}`} className="w-full block" preserveAspectRatio="none" style={{ height: 140 }}>
      {[min, (min + max) / 2, max].map((v, i) => (
        <g key={i}>
          <line x1={padL} y1={y(v)} x2={w - padR} y2={y(v)} stroke="rgba(255,255,255,0.08)" strokeWidth="1" />
          <text x={4} y={y(v) + 3} fontSize="8" fontFamily="ui-monospace, monospace" fill="#94a3b8" opacity="0.8">{fmtK(v)}</text>
        </g>
      ))}
      <polyline points={pts} fill="none" stroke={stroke} strokeWidth="1.5" strokeLinejoin="round" strokeLinecap="round" />
      <text x={padL} y={h - 4} fontSize="8" fontFamily="ui-monospace, monospace" fill="#64748b">{clean[0].d}</text>
      <text x={w - padR} y={h - 4} fontSize="8" fontFamily="ui-monospace, monospace" fill="#64748b" textAnchor="end">{clean[clean.length - 1].d}</text>
    </svg>
  );
}

// Basis toggle options — default option-only (goal: the carry-inclusive
// total basis flatters every variant; the option legs alone are negative).
const BASIS_OPTS = [
  { label: 'Option-only', value: 'opt' },
  { label: 'Total (carry-incl)', value: 'total' },
];

// IS-window hold (user directive 2026-10-17): the twin variant's in-sample
// figures (stored: 134 trades / IS net P&L −$2,766) are under qr_research
// reconciliation against the audited Run-0 twin (62 trades, sharpe_is 0.9941
// per parameters_used.twin_definition_note). Display "under reconciliation"
// for the IS window ONLY — OOS figures are unaffected and stay live.
// REMOVE THIS HOLD when the user says the reconciliation is done.
const IS_RECONCILING = { strategy_id: 'deriv_putwrite_regime_v1', variant: 'twin', run_id: '98cf94f6-b93e-450b-bc6e-edf03d4b9545' };
const isReconcilingIS = (r) => !!r && r.strategy_id === IS_RECONCILING.strategy_id
  && ((r.variant || '').toLowerCase() === IS_RECONCILING.variant || r.run_id === IS_RECONCILING.run_id);

function windowCell(r) {
  const oos = r.oos_start && r.oos_end
    ? `OOS ${String(r.oos_start).slice(0, 7)}→${String(r.oos_end).slice(0, 7)}` : null;
  if (isReconcilingIS(r)) {
    return oos ? `IS under reconciliation · ${oos}` : 'IS under reconciliation';
  }
  if (r.is_start && r.oos_start) {
    return `IS ${String(r.is_start).slice(0, 7)}→${String(r.is_end).slice(0, 7)} · ${oos}`;
  }
  return oos;
}

// Runs-table columns, rebuilt when the basis flips. Every performance column
// is labelled with its basis; PF/trades/win are basis-invariant as stored.
function runCols(basis) {
  const opt = basis === 'opt';
  return [
    { label: 'Run date', tip: 'Backtest run timestamp (UTC)',
      render: r => r.created_at ? `${String(r.created_at).slice(0, 10)} ${fmtTime(r.created_at)}` : null,
      cl: 'text-slate-400 font-mono', width: 110 },
    { label: 'Strategy', tip: 'Derivative strategy id', key: 'strategy_id',
      cl: 'text-slate-200 font-mono', width: 190, cellTip: r => r.strategy_id },
    { label: 'Variant', tip: 'Run variant from parameters_used.variant (twin / V1 / V2 — variants of one run of record)',
      render: r => variantLabel(r.variant), cl: 'text-slate-300 font-mono', width: 62 },
    { label: 'Window', tip: 'In-sample and out-of-sample spans (both stored). The twin variant\'s IS window is under qr_research reconciliation (stored 134 trades vs audited 62) — marked, not hidden.',
      render: r => windowCell(r),
      cl: r => isReconcilingIS(r) ? 'text-slate-500 font-mono' : 'text-slate-400 font-mono', width: 250 },
    opt
      ? { label: 'Sharpe · opt', tip: 'OPTION-ONLY basis: option legs alone, no T-bill cash carry (parameters_used.option_only.OOS.sharpe)',
          render: r => fmtNum(r.option_only?.OOS?.sharpe), cl: 'text-slate-300 font-mono', num: true }
      : { label: 'Sharpe · tot', tip: 'TOTAL basis (rf=0, carry-inclusive: DTB3 on cash) — stored headline sharpe_oos',
          render: r => fmtNum(r.sharpe_oos), cl: 'text-slate-300 font-mono', num: true },
    opt
      ? { label: 'Opt P&L', tip: 'OPTION-ONLY basis: option-leg P&L in $ (parameters_used.option_only.OOS.pnl_usd) — no return fraction is stored for this basis',
          render: r => money(r.option_only?.OOS?.pnl_usd), cl: r => pnlCl(r.option_only?.OOS?.pnl_usd) + ' font-mono', num: true }
      : { label: 'Return · tot', tip: 'TOTAL basis OOS return (carry-inclusive), stored as a fraction → %',
          render: r => fpct(r.returns_oos, 2), cl: r => pnlCl(r.returns_oos) + ' font-mono', num: true },
    { label: 'Win', tip: 'OOS win rate (basis-invariant), stored as a fraction → %',
      render: r => fpctBare(r.win_rate_oos, 1),
      cl: r => (r.win_rate_oos == null ? 'text-slate-400' : r.win_rate_oos >= 0.5 ? 'text-emerald-400' : 'text-rose-400') + ' font-mono', num: true },
    opt
      ? { label: 'MDD · opt', tip: 'OPTION-ONLY basis: max drawdown as % of NAV (parameters_used.option_only.OOS.maxdd_pct_nav, stored as a fraction)',
          render: r => fmdd(r.option_only?.OOS?.maxdd_pct_nav, 2), cl: r => pnlCl(-(r.option_only?.OOS?.maxdd_pct_nav ?? 0)) + ' font-mono', num: true }
      : { label: 'MDD · tot', tip: 'TOTAL basis OOS max drawdown (stored as a fraction → %)',
          render: r => fmdd(r.max_drawdown_oos, 2), cl: r => pnlCl(-(r.max_drawdown_oos ?? 0)) + ' font-mono', num: true },
    { label: 'PF', tip: 'OOS profit factor as stored (total-basis run metric — no option-only split is stored). Never green below 1.0.',
      render: r => fmtNum(r.profit_factor_oos),
      cl: r => (r.profit_factor_oos != null && r.profit_factor_oos >= 1 ? 'text-emerald-400' : 'text-slate-300') + ' font-mono', num: true },
    { label: 'Trades', tip: 'OOS trade count', key: 'trade_count_oos', cl: 'text-slate-300 font-mono', num: true },
    { label: 'Episodes', tip: 'Independent (non-overlapping) OOS episodes, computed from gold.derivatives_backtest_trades — pending while that ledger is empty',
      render: r => r.episodes_oos ?? 'pending', cl: r => r.episodes_oos == null ? 'text-slate-500 font-mono' : 'text-slate-300 font-mono', num: true },
  ];
}

export function DerivativesBacktest({ focusStrategy = null, onFocusConsumed }) {
  const [data, setData] = useState(null);
  const [loaded, setLoaded] = useState(false);
  const [selRun, setSelRun] = useState(null);
  const [detail, setDetail] = useState(null);
  const [detailFailed, setDetailFailed] = useState(false);
  const [basis, setBasis] = useState('opt');

  useEffect(() => {
    let dead = false;
    api.get('/api/derivatives/backtests').then(d => {
      if (dead) return;
      setData(d && Array.isArray(d.runs) ? d : null);
      setLoaded(true);
    });
    return () => { dead = true; };
  }, []);

  // Focus handoff from the Research tab's "View detail" — select the
  // strategy's headline run (lowest run_number = twin when present).
  // setState deferred via timeout: the lint rule forbids synchronous setState
  // in an effect body (cascading renders).
  useEffect(() => {
    if (!focusStrategy || !data) return;
    const t = setTimeout(() => {
      const runs = (data.runs || []).filter(r => r.strategy_id === focusStrategy);
      if (runs.length) {
        const headline = [...runs].sort((a, b) => (a.run_number ?? 99) - (b.run_number ?? 99))[0];
        setSelRun(headline.run_id);
      }
      onFocusConsumed && onFocusConsumed();
    }, 0);
    return () => clearTimeout(t);
  }, [focusStrategy, data, onFocusConsumed]);

  useEffect(() => {
    if (!selRun) { setDetail(null); return; }
    let dead = false;
    setDetail(null);
    setDetailFailed(false);
    api.get(`/api/derivatives/backtests/${selRun}`).then(d => {
      if (dead) return;
      if (d && d.run && Array.isArray(d.trades)) setDetail(d);
      else setDetailFailed(true);
    });
    return () => { dead = true; };
  }, [selRun]);

  const sum = data?.summary || {};
  const failed = loaded && !data;
  const runs = data?.runs || [];
  const latest = runs[0] || null;

  // Stress-window honesty: no run's OOS may silently imply stress evidence.
  const noStress = runs.length > 0 && runs.every(r => !oosCoversNamedStress(r.oos_start, r.oos_end));
  const oosSpan = latest ? `${latest.oos_start}→${latest.oos_end}` : null;

  const cols = useMemo(() => runCols(basis), [basis]);

  return (
    <div className="space-y-3">
      <DerivKpiStrip
        tiles={[
          { label: 'Runs', tip: 'Derivative backtest runs in gold.derivatives_backtest_runs (variant rows of a run of record count individually)',
            value: data ? sum.runs ?? null : null,
            sub: data ? `${sum.strategies ?? 0} strateg${sum.strategies === 1 ? 'y' : 'ies'} · latest ${latest ? String(latest.created_at).slice(0, 10) : '—'}` : 'loading' },
          { label: 'Variants', tip: 'Distinct variants across runs (parameters_used.variant)',
            value: data ? new Set(runs.map(r => r.variant).filter(Boolean)).size : null,
            sub: data ? [...new Set(runs.map(r => variantLabel(r.variant)))].join(' · ') : 'loading' },
          { label: 'Latest run', tip: 'Most recent run (variant rows share the run timestamp)',
            value: latest ? String(latest.created_at).slice(0, 10) : null,
            sub: latest ? `${latest.run_label || 'run'} · ${runs.length} variant rows` : 'no runs yet' },
          { label: (
              <span className="flex items-center gap-1">Best PF (OOS) <DerivResearchOnlyChip /></span>
            ),
            tip: 'Best out-of-sample profit factor across all variant rows (as stored, total-basis). RESEARCH-ONLY evidence class.',
            value: data ? (sum.best_pf_oos != null ? fmtNum(sum.best_pf_oos) : null) : null,
            cl: sum.best_pf_oos != null && sum.best_pf_oos >= 1 ? 'text-emerald-400' : undefined,
            sub: data ? (sum.pf_ge_1 === 0 ? `none above 1.0 (${runs.length} variant${runs.length === 1 ? '' : 's'})` : `${sum.pf_ge_1} of ${runs.length} above 1.0`) : 'loading' },
        ]}
      />

      <DerivChipFilter
        groups={[
          { label: 'Basis', value: basis, onChange: setBasis, options: BASIS_OPTS },
        ]}
      />

      <DerivPanel
        title="Backtest Runs"
        endpoint="GET /api/derivatives/backtests"
        task={TASK_DERIV_LEDGERS}
        live={!!data}
        failed={failed}
        note="Variant rows of each run of record, from gold.derivatives_backtest_runs — separate tables from equity strategy backtests, so existing performance views are unaffected. Stored headline metrics are TOTAL-basis (rf=0, T-bill cash carry included); the basis toggle switches Sharpe / Return / MDD to the carry-free option-only figures stored in run params. Click a run for drill-down."
        right={<DerivResearchOnlyChip />}
      >
        {noStress && oosSpan && (
          <div className="mb-2 text-[10px] text-slate-500">
            OOS window {oosSpan} contains no named stress episode (no COVID-2020 / 2022 bear) — stress evidence accrues forward only.
          </div>
        )}
        <DerivTable
          cols={cols}
          rows={runs}
          rowKey={r => r.run_id}
          onRowClick={r => setSelRun(r.run_id)}
          selectedId={selRun}
          empty={failed ? 'Feed unavailable — see badge tooltip.' : 'No backtest runs yet — the ledger is live and empty.'}
          sub="Runs appear here when qr_research executes a derivatives backtest into gold.derivatives_backtest_runs."
        />
      </DerivPanel>

      <DerivPanel
        title="Run Detail"
        endpoint="GET /api/derivatives/backtests/{run_id}"
        task={TASK_DERIV_LEDGERS}
        live={!!detail}
        failed={detailFailed}
        note={detail
          ? `${detail.run.strategy_id} · variant ${variantLabel(detail.run.variant)} · ${isReconcilingIS(detail.run) ? 'IS under reconciliation' : `IS ${detail.run.is_start || '—'}→${detail.run.is_end || '—'}`} · OOS ${detail.run.oos_start || '—'}→${detail.run.oos_end || '—'} · ${detail.oos_rows ?? '—'} OOS · ${detail.is_rows ?? '—'} IS trades · ${detail.run.episodes_oos ?? 'pending'} episodes · risk gates ${detail.run.all_risk_gates_passed == null ? '—' : detail.run.all_risk_gates_passed ? 'PASSED' : 'FAILED'}`
          : 'Per-run drill-down — activates when a run is selected above.'}
        right={detail ? <DerivResearchOnlyChip /> : undefined}
      >
        {!detail ? (
          <div className="grid grid-cols-1 xl:grid-cols-2 gap-3">
            <DerivEmptyState
              line={detailFailed ? 'Detail feed unavailable — see badge tooltip.' : 'Equity curve renders here once a run is selected.'}
              sub="Cumulative realized P&L curve derived from gold.derivatives_backtest_trades (labelled derived_from_trades)."
            />
            <DerivEmptyState
              line={detailFailed ? 'Detail feed unavailable — see badge tooltip.' : 'Annual returns + trade ledger render here.'}
              sub="Per-year sums and round-trip ledger from gold.derivatives_backtest_trades."
            />
          </div>
        ) : (
          <div className="space-y-3">
            {isReconcilingIS(detail.run) && (
              <div className="text-[10px] text-slate-500">
                IS window under reconciliation — qr_research is reconciling the twin variant's stored in-sample figures (134 trades / IS net P&L) against the audited Run-0 twin (62 trades). OOS figures below are unaffected. (Hold per operator, 2026-10-17.)
              </div>
            )}
            {detail.run.episodes_oos == null && detail.trade_count === 0 && (
              <div className="text-[10px] text-slate-500">
                gold.derivatives_backtest_trades holds no rows for this run — aggregate metrics only. Curve, annual bars, ledger and the episode count activate when the trade-level rows land (requested from qr_research).
              </div>
            )}
            {detailMismatch(detail).length > 0 ? (
              <DerivEmptyState
                line="Data mismatch — ledger does not tie to the run's stored totals. Charts withheld."
                sub={detailMismatch(detail).join(' · ')}
              />
            ) : (
            <>
            <div className="grid grid-cols-1 xl:grid-cols-2 gap-3">
              <div>
                <div className="qr-label mb-1">Cumulative realized P&amp;L · OOS window · derived from trades</div>
                <DerivCurve points={detail.curve?.points} />
              </div>
              <div>
                <div className="qr-label mb-1">Annual P&amp;L · OOS window · derived from trades</div>
                {(detail.annual?.years || []).length === 0 ? (
                  <DerivEmptyState line="No closed-trade years yet." />
                ) : (
                  <div className="space-y-1">
                    {detail.annual.years.map(y => (
                      <div key={y.year} className="flex items-center gap-2 text-[11px]">
                        <span className="w-10 font-mono text-slate-400">{y.year}</span>
                        <span className={`font-mono font-bold ${pnlCl(y.pnl)}`}>{fmtK(y.pnl)}</span>
                        <span className="text-[9px] text-slate-500">{y.trades} trades</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
            <DerivTable
              cols={TRADE_COLS}
              rows={detail.trades}
              rowKey={r => r.id}
              empty="No trade rows recorded for this run."
            />
            </>
            )}
          </div>
        )}
      </DerivPanel>
    </div>
  );
}

// Tie-out (follow-up 2026-10-17, item 3): the derived views must reconcile
// with the run's stored totals — any mismatch renders a notice INSTEAD of
// the charts, never a chart that disagrees with stored metrics. The ledger
// carries IS+OOS rows, so counts tie per window and P&L ties against the
// run's stored net_at_f1.0 per window. An empty ledger is the known pending
// state (qr_research t_84d15809), not a mismatch.
function detailMismatch(detail) {
  if (!detail || !detail.trade_count) return [];
  const out = [];
  const run = detail.run || {};
  if (detail.oos_rows != null && run.trade_count_oos != null && detail.oos_rows !== run.trade_count_oos) {
    out.push(`OOS ledger rows ${detail.oos_rows} ≠ stored OOS trade count ${run.trade_count_oos}`);
  }
  if (detail.is_rows != null && run.trade_count_is != null && detail.is_rows !== run.trade_count_is) {
    out.push(`IS ledger rows ${detail.is_rows} ≠ stored IS trade count ${run.trade_count_is}`);
  }
  const pts = detail.curve?.points || [];
  const curveTotal = pts.length ? pts[pts.length - 1].cum_pnl : 0;
  const annualTotal = (detail.annual?.years || []).reduce((a, y) => a + (y.pnl || 0), 0);
  if (pts.length > 0 && Math.abs(curveTotal - annualTotal) > 0.01) {
    out.push(`curve total $${curveTotal} ≠ annual sum $${annualTotal}`);
  }
  if (pts.length > 0 && run.net_pnl_oos != null && Math.abs(curveTotal - run.net_pnl_oos) > 0.01) {
    out.push(`OOS curve total $${curveTotal} ≠ stored net P&L $${run.net_pnl_oos} (net_at_f1.0)`);
  }
  return out;
}
