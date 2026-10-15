import { useEffect, useMemo, useState } from 'react';
import { api, fmtNum } from '../../utils.js';
import {
  DerivPanel, DerivKpiStrip, DerivTable, DerivChipFilter,
  TASK_RESEARCH_REGISTRY,
} from './shared.jsx';

// Derivatives ▸ Research — rank-ordered research queue for derivative
// strategy candidates.
// Phase 2 (2026-10-02, t_d67907e4): LIVE on GET /api/derivatives/strategies
// (gold.derivatives_strategies, qr_research t_736850c6 — 9 rows).
//
// 2026-10-09 rework (user: 'page is useless — all zeros, wall of text'):
// the registry rows are rich (rank / structure / risk budget / baseline /
// kill conditions) but the old layout led with 5 permanently-null OOS
// metric columns plus a second prose-wall panel. Now: one queue table with
// the actionable fields up front; clicking a row opens the full verbatim
// research card below the table. OOS metric columns are added automatically
// once gold.derivatives_backtest_runs has its first row (any latest_run_id
// != null) — until then they are absent, not a wall of dashes.

const TRUNC = { maxWidth: 220, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', display: 'inline-block', verticalAlign: 'bottom' };
const TRUNC_W = { maxWidth: 320, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', display: 'inline-block', verticalAlign: 'bottom' };

// OOS metric columns — only mounted when at least one strategy has a run.
const OOS_COLS = [
  { label: 'Sharpe OOS', tip: 'Out-of-sample Sharpe from gold.derivatives_backtest_runs', render: r => fmtNum(r.sharpe_oos), cl: 'text-slate-400 font-mono' },
  { label: 'Ret OOS', tip: 'Out-of-sample return — per-field unit contract pins with the first run', render: r => fmtNum(r.returns_oos), cl: 'text-slate-400 font-mono' },
  { label: 'Win %', tip: 'Out-of-sample win rate', render: r => fmtNum(r.win_rate_oos), cl: 'text-slate-400 font-mono' },
  { label: 'MDD', tip: 'Out-of-sample max drawdown', render: r => fmtNum(r.max_drawdown_oos), cl: 'text-slate-400 font-mono' },
  { label: 'Trades', tip: 'Out-of-sample trade count', key: 'trade_count_oos', cl: 'text-slate-400 font-mono' },
];

function riskBudget(r) {
  const ml = r.max_loss_per_position_usd, nav = r.max_pct_nav_at_risk;
  if (ml == null && nav == null) return null;
  const parts = [];
  if (ml != null) parts.push(`$${Number(ml).toLocaleString('en-US', { maximumFractionDigits: 0 })}`);
  if (nav != null) parts.push(`${(Number(nav) * 100).toFixed(1)}% NAV`);
  return parts.join(' · ');
}

function ProseBlock({ label, text }) {
  if (!text) return null;
  return (
    <div>
      <div className="qr-label mb-0.5">{label}</div>
      <div className="text-[10px] text-slate-400 leading-relaxed whitespace-pre-wrap">{text}</div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Live KAT status (kanban t_83758f8e) — verdicts render from
// GET /api/derivatives/kat-status (deriv.kat_runs) on every page load, never
// from stored data_blocker text. Empty/missing feed -> "KAT status
// unavailable" badge + the stored blocker text carries the qualitative gate.
// ---------------------------------------------------------------------------

const KAT_INDEXES = ['BXM', 'PUT'];
const katIsPass = v => (v || '').toUpperCase() === 'PASS';

function KatMetric({ label, tip, value, tol, cmp = 'lte', int = false }) {
  const fmt = v => int ? String(Math.round(Number(v))) : Number(v).toFixed(4);
  const known = value != null && tol != null;
  const ok = known && (cmp === 'gte' ? Number(value) >= Number(tol) : Number(value) <= Number(tol));
  return (
    <span className="flex items-baseline gap-1" title={tip}>
      <span className="text-slate-500">{label}</span>
      <span className={`font-mono ${!known ? 'text-slate-500' : ok ? 'text-emerald-400' : 'text-rose-400'}`}>
        {value != null ? fmt(value) : '—'}
      </span>
      <span className="text-slate-600 font-mono">{cmp === 'gte' ? '≥' : '≤'}{tol != null ? fmt(tol) : '—'}</span>
    </span>
  );
}

function KatLiveBlock({ kat, katLoaded }) {
  const [expanded, setExpanded] = useState(false);
  if (!katLoaded) {
    return <div className="mt-1.5"><span className="qr-chip qr-chip-slate">KAT …loading</span></div>;
  }
  const runs = kat?.runs || [];
  if (!runs.length) {
    return (
      <div className="mt-1.5">
        <span className="qr-chip qr-chip-slate" title="GET /api/derivatives/kat-status returned no runs — stored blocker text above is the only gate info available. Never a hardcoded verdict.">
          KAT status unavailable
        </span>
      </div>
    );
  }

  const covered = KAT_INDEXES.every(i => runs.some(r => r.index_name === i));
  // Gate OPEN only when the latest run per (index, fill) is PASS for both indexes.
  const gateOpen = covered && runs.every(r => katIsPass(r.verdict));
  const byIndex = KAT_INDEXES.map(idx => {
    const ir = runs.filter(r => r.index_name === idx);
    if (!ir.length) return { idx, verdict: null };
    const failRun = ir.find(r => !katIsPass(r.verdict));
    return { idx, verdict: failRun ? failRun.verdict : 'PASS' };
  });
  const latestAt = kat.latest_run_at;

  return (
    <div className="mt-1.5">
      <div className="flex items-center gap-2 flex-wrap">
        <span
          className={`qr-chip ${gateOpen ? 'qr-chip-emerald' : 'qr-chip-rose'}`}
          title="OPEN only when the latest deriv.kat_runs run per (index, fill_frac) is verdict PASS for both BXM and PUT; otherwise BLOCKED."
        >
          GATE {gateOpen ? 'OPEN' : 'BLOCKED'}
        </span>
        {byIndex.map(({ idx, verdict }) => (
          <button
            key={idx}
            onClick={() => setExpanded(e => !e)}
            className={`qr-chip cursor-pointer ${verdict == null ? 'qr-chip-slate' : katIsPass(verdict) ? 'qr-chip-emerald' : 'qr-chip-rose'}`}
            title="Latest KAT verdict for this index (live from deriv.kat_runs) — click to expand run detail vs tolerances"
          >
            {idx} KAT: RUN · {verdict || 'NO RUN'}
          </button>
        ))}
        <span className="text-[9px] text-slate-600 font-mono">
          live · deriv.kat_runs · latest {latestAt ? latestAt.slice(0, 16).replace('T', ' ') + 'Z' : '—'}
        </span>
      </div>
      {expanded && (
        <div className="mt-2 space-y-1.5">
          {runs.map(r => {
            const t = r.tolerances || {};
            return (
              <div key={r.run_id} className="rounded border border-white/[0.06] bg-white/[0.02] px-2 py-1.5">
                <div className="flex items-center gap-2 flex-wrap text-[9px] font-mono text-slate-500">
                  <span className={`qr-chip ${katIsPass(r.verdict) ? 'qr-chip-emerald' : 'qr-chip-rose'}`}>{r.verdict || '—'}</span>
                  <span className="text-slate-300">{r.index_name} · fill {r.fill_frac}</span>
                  <span>run {String(r.run_id).slice(0, 8)}</span>
                  <span>{r.created_at ? r.created_at.slice(0, 16).replace('T', ' ') + 'Z' : '—'}</span>
                  {r.symbol && <span>{r.symbol}</span>}
                  {r.bug_fix && <span className="text-slate-600">{r.bug_fix}</span>}
                  {Array.isArray(r.window) && r.window.length === 2 && <span>window {r.window[0]} → {r.window[1]}</span>}
                  {r.n_months != null && <span>{Math.round(r.n_months)} months</span>}
                </div>
                <div className="flex items-center gap-3 flex-wrap mt-1 text-[9px]">
                  <KatMetric label="corr" tip="monthly_corr vs tolerance (min)" value={r.monthly_corr} tol={t.monthly_corr} cmp="gte" />
                  <KatMetric label="cagrΔ" tip="cagr_diff vs tolerance (abs max)" value={r.cagr_diff} tol={t.cagr_abs} />
                  <KatMetric label="maxddΔ" tip="maxdd_diff vs tolerance (abs max)" value={r.maxdd_diff} tol={t.maxdd_abs} />
                  <KatMetric label="mo>band" tip={`months with |monthly diff| over the ${t.month_over_band ?? '—'} band, vs tolerance (max)`} value={r.n_months_over_band} tol={t.n_months_over} int />
                  <KatMetric label="worstΔ" tip="worst_month_diff vs tolerance (max)" value={r.worst_month_diff} tol={t.worst_month} />
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

// Full verbatim research card for the selected candidate (thesis / entry /
// exit / kill conditions / provenance) — replaces the old always-on prose
// wall; content renders on demand, straight from the registry.
function ResearchCard({ r }) {
  const kills = Array.isArray(r.kill_conditions) ? r.kill_conditions : [];
  return (
    <div className="mt-2 rounded border border-white/[0.08] bg-white/[0.02] px-3 py-2.5 space-y-2.5">
      <div className="flex items-center gap-2 flex-wrap">
        <span className="text-[11px] font-semibold text-slate-100">{r.name || r.strategy_id}</span>
        <span className="text-[9px] text-slate-500 font-mono">{r.strategy_id}</span>
        <span className="qr-chip qr-chip-slate">{r.instrument || '—'}</span>
        <span className="qr-chip qr-chip-slate">{r.venue || '—'}</span>
        {r.phase && <span className="qr-chip qr-chip-slate opacity-70">{r.phase}</span>}
      </div>
      <ProseBlock label="Thesis" text={r.thesis} />
      <div className="grid md:grid-cols-2 gap-3">
        <ProseBlock label="Entry" text={r.entry_logic} />
        <ProseBlock label="Exit" text={r.exit_logic} />
      </div>
      {r.baseline_spec && (
        <ProseBlock label="Must beat (baseline)" text={r.baseline_spec} />
      )}
      {kills.length > 0 && (
        <div>
          <div className="qr-label mb-0.5">Kill conditions (pre-declared)</div>
          <ul className="list-disc pl-4 space-y-0.5">
            {kills.map((k, i) => (
              <li key={i} className="text-[10px] text-slate-400 leading-relaxed">{k}</li>
            ))}
          </ul>
        </div>
      )}
      {r.data_blocker && <ProseBlock label="Data blocker" text={r.data_blocker} />}
      <div className="text-[9px] text-slate-600 font-mono">
        {[
          r.source_doc,
          r.nav_basis ? `NAV basis ${r.nav_basis}` : null,
          r.updated_at ? `updated ${String(r.updated_at).slice(0, 10)}` : null,
          r.latest_run_id ? `run ${r.latest_run_id}` : 'no backtest run yet',
        ].filter(Boolean).join(' · ')}
      </div>
    </div>
  );
}

export function DerivativesResearch() {
  const [data, setData] = useState(null);       // null = not loaded / failed
  const [loaded, setLoaded] = useState(false);
  const [fInst, setFInst] = useState('ALL');
  const [fVenue, setFVenue] = useState('ALL');
  const [fStage, setFStage] = useState('ALL');
  const [selectedId, setSelectedId] = useState(null);
  const [kat, setKat] = useState(null);        // null = feed failed/empty
  const [katLoaded, setKatLoaded] = useState(false);

  useEffect(() => {
    let dead = false;
    api.get('/api/derivatives/strategies').then(d => {
      if (dead) return;
      // Defensive shape guard — accept only the documented contract.
      setData(d && Array.isArray(d.strategies) ? d : null);
      setLoaded(true);
    });
    return () => { dead = true; };
  }, []);

  // Live KAT verdicts (t_83758f8e) — refetched with the page, never cached
  // into any static feed; the banner reads deriv.kat_runs via the endpoint.
  useEffect(() => {
    let dead = false;
    api.get('/api/derivatives/kat-status').then(d => {
      if (dead) return;
      setKat(d && Array.isArray(d.runs) ? d : null);
      setKatLoaded(true);
    });
    return () => { dead = true; };
  }, []);

  // Rank-ordered canonical list (research_rank asc, nulls last).
  const all = useMemo(() => [...(data?.strategies || [])].sort((a, b) => {
    const ra = a.research_rank ?? 999, rb = b.research_rank ?? 999;
    return ra - rb;
  }), [data]);

  const rows = useMemo(() => all.filter(r => {
    if (fInst !== 'ALL' && (r.instrument || '').toUpperCase() !== fInst) return false;
    if (fVenue !== 'ALL' && (r.venue || '').toUpperCase() !== fVenue) return false;
    if (fStage === 'BACKTESTED') return r.latest_run_id != null;
    if (fStage === 'RESEARCH') return r.latest_run_id == null;
    return true;
  }), [all, fInst, fVenue, fStage]);

  const hasRuns = all.some(r => r.latest_run_id != null);

  const cols = useMemo(() => [
    { label: '#', tip: 'Research priority rank (qr_research ordering)',
      render: r => r.research_rank ?? '—', cl: 'text-slate-500 font-mono' },
    { label: 'Candidate', tip: 'Registry display name + id (research-owned prose)',
      render: r => (
        <span>
          <span className="text-slate-100 font-semibold">{r.name || r.strategy_id}</span>
          <span className="block text-[9px] text-slate-500 font-mono">{r.strategy_id}</span>
        </span>
      ) },
    { label: 'Structure', tip: 'Expression template (option/future structure)',
      render: r => <span className="font-mono text-[10px]">{r.expression_template || '—'}</span>,
      cl: 'text-slate-400' },
    { label: 'Underlying', tip: 'Underlying universe',
      render: r => (r.underlyings || []).length
        ? <span style={TRUNC} title={(r.underlyings || []).join(', ')}>{(r.underlyings || []).join(', ')}</span>
        : '—' },
    { label: 'Stage', tip: 'Registry status + research phase',
      render: r => (
        <span className="flex items-center gap-1">
          <span className={`qr-chip qr-chip-slate ${r.status === 'parked' ? 'opacity-60' : ''}`}>{r.status || '—'}</span>
          {r.phase && r.phase !== r.status && <span className="text-[9px] text-slate-500">{r.phase}</span>}
        </span>
      ) },
    { label: 'Risk budget', tip: 'Max loss per position and max % of NAV at risk (registry-declared sizing)',
      render: r => riskBudget(r), cl: 'text-slate-300 font-mono' },
    { label: 'Must beat', tip: 'Pre-declared baseline the strategy must outperform to survive',
      render: r => r.baseline_spec
        ? <span style={TRUNC_W} title={r.baseline_spec}>{r.baseline_spec}</span>
        : '—',
      cl: 'text-slate-400' },
    { label: 'Blocked on', tip: 'Data blocker standing between this candidate and its first backtest',
      render: r => r.data_blocker
        ? <span style={TRUNC_W} title={r.data_blocker}>{r.data_blocker}</span>
        : '—',
      cl: 'text-slate-400' },
  ], []);

  const fullCols = useMemo(() => hasRuns ? [...cols, ...OOS_COLS] : cols, [cols, hasRuns]);

  const sum = data?.summary || {};
  const failed = loaded && !data;
  const inResearch = all.filter(r => (r.status || '').toLowerCase() === 'research').length;
  const parked = all.filter(r => (r.status || '').toLowerCase() === 'parked').length;
  const rank1Blocker = all.find(r => r.data_blocker)?.data_blocker;
  const noRuns = (sum.backtested ?? 0) === 0;
  const selected = rows.find(r => r.strategy_id === selectedId) || null;

  return (
    <div className="space-y-3">
      <DerivKpiStrip
        tiles={[
          { label: 'Candidates', tip: 'Registered derivative strategy candidates (gold.derivatives_strategies)', value: sum.total ?? null, sub: 'research registry' },
          { label: 'In research', tip: 'Status = research (actively being worked)', value: data ? inResearch : null, sub: 'queue' },
          { label: 'Parked', tip: 'Status = parked (set aside, reason in the research card)', value: data ? parked : null, sub: 'queue' },
          { label: 'Backtested', tip: 'Candidates with at least one OOS run in gold.derivatives_backtest_runs — 0 until each data blocker clears', value: data ? `${sum.backtested ?? 0} / ${sum.total ?? all.length}` : null, sub: noRuns ? 'blocked on data' : 'runs live' },
        ]}
      />

      {data && noRuns && rank1Blocker && (
        <div className="qr-surface px-3 py-2 border-l-2 border-slate-500">
          <div className="flex items-baseline gap-2">
            <span className="qr-label mr-2 shrink-0">Blocking decision · rank 1</span>
            <span className="text-[10px] text-slate-400">{rank1Blocker}</span>
          </div>
          <KatLiveBlock kat={kat} katLoaded={katLoaded} />
        </div>
      )}

      <DerivChipFilter
        groups={[
          { label: 'Instrument', value: fInst, onChange: setFInst, options: ['ALL', 'OPTION', 'FUTURE'] },
          { label: 'Venue', value: fVenue, onChange: setFVenue, options: ['ALL', 'US', 'HK'] },
          { label: 'Stage', value: fStage, onChange: setFStage, options: ['ALL', 'RESEARCH', 'BACKTESTED'] },
        ]}
      />

      <DerivPanel
        title="Research Queue"
        endpoint="GET /api/derivatives/strategies"
        task={TASK_RESEARCH_REGISTRY}
        live={!!data}
        failed={failed}
        note="Rank-ordered derivative strategy candidates — kept out of the equity strategy universe (Lab / Pipeline / Performance) by design. Click a row for the full research card (thesis / entry / exit / kill conditions, verbatim from the registry). OOS metric columns appear once the first backtest run lands."
      >
        <DerivTable
          cols={fullCols}
          rows={rows}
          rowKey={r => r.strategy_id}
          empty={failed ? 'Feed unavailable — see badge tooltip.' : 'No candidates match the active filters.'}
          sub={data ? `${data.count ?? all.length} registered · ${rows.length} shown` : undefined}
          onRowClick={r => setSelectedId(id => id === r.strategy_id ? null : r.strategy_id)}
          selectedId={selectedId}
        />
        {selected && <ResearchCard r={selected} />}
      </DerivPanel>
    </div>
  );
}
