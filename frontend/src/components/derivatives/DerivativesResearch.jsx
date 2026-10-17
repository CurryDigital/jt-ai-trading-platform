import { useEffect, useMemo, useState } from 'react';
import { api } from '../../utils.js';
import {
  DerivPanel, DerivKpiStrip, DerivTable, DerivChipFilter, DerivResearchOnlyChip,
  fmdd,
  TASK_RESEARCH_REGISTRY,
} from './shared.jsx';
import { DerivCandidateCard } from './DerivCandidateCard.jsx';

// Derivatives ▸ Research — rank-ordered research queue for derivative
// strategy candidates.
// Phase 2 (2026-10-02, t_d67907e4): LIVE on GET /api/derivatives/strategies
// (gold.derivatives_strategies, qr_research t_736850c6).
//
// derivatives_page_alignment_v1 (2026-10-17): platform-aligned look.
// - Queue table fits 1280px: 'Must beat' moved out of the row (it stays in
//   the expanded card), 'Blocked on' is a fixed truncated width, and
//   Sharpe/PF/MDD/Trades are sortable columns off the headline run
//   (lowest run_number = the twin variant; both bases live on the card).
//   Default sort = research rank.
// - The rank-1 blocking-decision banner and the live KAT chip row render
//   ALWAYS. (They used to be gated on zero backtested candidates, so they
//   vanished the moment the first runs landed on 2026-10-17 — an emergent
//   condition of the 2026-10-09 design, not a deliberate removal.)
// - A candidate with runs expands into DerivCandidateCard (IPO-card anatomy:
//   six metrics + episodes, variants mini-table with both bases, SIM/PAPER/
//   UAT/LIVE ladder, verbatim rules, next-gate line, View detail only).
//   Candidates without runs keep the verbatim prose ResearchCard.

// Render a timestamp unambiguously: full ISO-8601 seconds + explicit UTC
// marker ('2026-10-15T05:15:50Z'). Accepts 'T' or space separators and a
// missing zone (assumed UTC); unparseable input is shown verbatim, never
// silently truncated (the old slice(0,16)+'Z' read as '05:15Z' ~ '05:152').
function fmtIsoUtc(s) {
  if (!s) return '—';
  let iso = String(s).trim();
  if (/^\d{4}-\d{2}-\d{2} \d{2}:\d{2}/.test(iso)) iso = iso.replace(' ', 'T');
  if (/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}(:\d{2}(\.\d+)?)?$/.test(iso)) iso += 'Z';
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return String(s);
  return d.toISOString().slice(0, 19) + 'Z';
}

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
          title="KAT status only: PASS when the latest deriv.kat_runs run per (index, fill_frac) is verdict PASS for both BXM and PUT; otherwise FAIL. Other gates (regime wf_v2, sleeve evidence, promotion) remain open — KAT: PASS is not a go."
        >
          KAT: {gateOpen ? 'PASS' : 'FAIL'}
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
          live · deriv.kat_runs · latest {fmtIsoUtc(latestAt)}
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
                  <span>{fmtIsoUtc(r.created_at)}</span>
                  {r.symbol && <span>{r.symbol}</span>}
                  {r.bug_fix && <span className="text-slate-600">{r.bug_fix}</span>}
                  {r.gold_data_tag && <span className="text-slate-600" title="Gold data snapshot tag this run validated against">gold: {r.gold_data_tag}</span>}
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

// Full verbatim research card for candidates WITHOUT runs (thesis / entry /
// exit / kill conditions / provenance). Candidates with runs expand into
// DerivCandidateCard instead (IPO-card anatomy).
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
      {r.data_blocker && <ProseBlock label="Next gate (display only)" text={r.data_blocker} />}
      <div className="text-[9px] text-slate-600 font-mono">
        {[
          r.source_doc,
          r.nav_basis ? `NAV basis ${r.nav_basis}` : null,
          r.updated_at ? `updated ${String(r.updated_at).slice(0, 10)}` : null,
          'no backtest run yet',
        ].filter(Boolean).join(' · ')}
      </div>
    </div>
  );
}

// Headline run per candidate (backend orders runs by run_number ASC — the
// twin/structure-consistent variant leads). Queue metric columns read from it.
const headlineOf = (r) => (r.runs && r.runs.length ? r.runs[0] : null);

const SORTERS = {
  rank:   { get: r => r.research_rank ?? 999, dir: 'asc' },
  sharpe: { get: r => headlineOf(r)?.sharpe_oos ?? null, dir: 'desc' },
  pf:     { get: r => headlineOf(r)?.profit_factor_oos ?? null, dir: 'desc' },
  mdd:    { get: r => headlineOf(r)?.max_drawdown_oos ?? null, dir: 'asc' },
  trades: { get: r => headlineOf(r)?.trade_count_oos ?? null, dir: 'desc' },
};

export function DerivativesResearch({ onViewRuns }) {
  const [data, setData] = useState(null);       // null = not loaded / failed
  const [loaded, setLoaded] = useState(false);
  const [fInst, setFInst] = useState('ALL');
  const [fVenue, setFVenue] = useState('ALL');
  const [fStage, setFStage] = useState('ALL');
  const [selectedId, setSelectedId] = useState(null);
  const [kat, setKat] = useState(null);        // null = feed failed/empty
  const [katLoaded, setKatLoaded] = useState(false);
  const [sort, setSort] = useState({ key: 'rank', dir: 'asc' });

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

  const all = useMemo(() => [...(data?.strategies || [])], [data]);

  const rows = useMemo(() => {
    const filtered = all.filter(r => {
      if (fInst !== 'ALL' && (r.instrument || '').toUpperCase() !== fInst) return false;
      if (fVenue !== 'ALL' && (r.venue || '').toUpperCase() !== fVenue) return false;
      if (fStage === 'BACKTESTED') return r.latest_run_id != null;
      if (fStage === 'RESEARCH') return r.latest_run_id == null;
      return true;
    });
    const s = SORTERS[sort.key] || SORTERS.rank;
    const dir = sort.dir === 'asc' ? 1 : -1;
    return [...filtered].sort((a, b) => {
      const va = s.get(a), vb = s.get(b);
      // Nulls always last, whichever direction.
      if (va == null && vb == null) return 0;
      if (va == null) return 1;
      if (vb == null) return -1;
      return va === vb ? 0 : (va < vb ? -1 : 1) * dir;
    });
  }, [all, fInst, fVenue, fStage, sort]);

  const onSort = (key) => setSort(prev =>
    prev.key === key
      ? { key, dir: prev.dir === 'desc' ? 'asc' : 'desc' }
      : { key, dir: (SORTERS[key] || SORTERS.rank).dir });

  const cols = useMemo(() => [
    { label: '#', tip: 'Research priority rank (qr_research ordering) — default sort',
      render: r => r.research_rank ?? '—', cl: 'text-slate-500 font-mono', width: 26, num: true },
    { label: 'Candidate', tip: 'Registry display name + id (research-owned prose)',
      render: r => (
        <span>
          <span className="text-slate-100 font-semibold">{r.name || r.strategy_id}</span>
          <span className="block text-[9px] text-slate-500 font-mono">{r.strategy_id}</span>
        </span>
      ), width: 168 },
    { label: 'Structure', tip: 'Expression template (option/future structure)',
      render: r => <span className="font-mono text-[10px]">{r.expression_template || '—'}</span>,
      cl: 'text-slate-400', width: 96, cellTip: r => r.expression_template },
    { label: 'Underlying', tip: 'Underlying universe',
      render: r => (r.underlyings || []).length
        ? (r.underlyings || []).join(', ')
        : '—', width: 78, cellTip: r => (r.underlyings || []).join(', ') },
    { label: 'Stage', tip: 'Registry status + research phase',
      render: r => (
        <span className="flex items-center gap-1">
          <span className={`qr-chip qr-chip-slate ${r.status === 'parked' ? 'opacity-60' : ''}`}>{r.status || '—'}</span>
          {r.phase && r.phase !== r.status && <span className="text-[9px] text-slate-500">{r.phase}</span>}
        </span>
      ), width: 108 },
    { label: 'Risk budget', tip: 'Max loss per position and max % of NAV at risk (registry-declared sizing)',
      render: r => riskBudget(r), cl: 'text-slate-300 font-mono', width: 92, cellTip: r => riskBudget(r) },
    { label: 'Blocked on', tip: 'Next gate — data blocker standing between this candidate and promotion (display only, research-owned verbatim)',
      render: r => r.data_blocker || null, cl: 'text-slate-400', width: 190, cellTip: r => r.data_blocker },
    { label: 'Sharpe', tip: 'Headline run (twin variant) OOS Sharpe — TOTAL basis (carry-inclusive). Option-only per variant on the card below. RESEARCH-ONLY.',
      sortKey: 'sharpe', num: true, width: 58,
      render: r => headlineOf(r)?.sharpe_oos != null ? Number(headlineOf(r).sharpe_oos).toFixed(2) : null,
      cl: 'text-slate-300 font-mono' },
    { label: 'PF', tip: 'Headline run OOS profit factor (total-basis, as stored). Never green below 1.0. RESEARCH-ONLY.',
      sortKey: 'pf', num: true, width: 50,
      render: r => headlineOf(r)?.profit_factor_oos != null ? Number(headlineOf(r).profit_factor_oos).toFixed(2) : null,
      cl: r => (headlineOf(r)?.profit_factor_oos != null && headlineOf(r).profit_factor_oos >= 1 ? 'text-emerald-400' : 'text-slate-300') + ' font-mono' },
    { label: 'MDD', tip: 'Headline run OOS max drawdown, TOTAL basis (fraction → %). RESEARCH-ONLY.',
      sortKey: 'mdd', num: true, width: 62,
      render: r => fmdd(headlineOf(r)?.max_drawdown_oos, 1),
      cl: 'text-rose-400 font-mono' },
    { label: 'Trades', tip: 'Headline run OOS trade count (publishable gate ≥ 30). Episodes on the card below.',
      sortKey: 'trades', num: true, width: 52,
      render: r => headlineOf(r)?.trade_count_oos ?? null,
      cl: 'text-slate-300 font-mono' },
  ], []);

  const sum = data?.summary || {};
  const failed = loaded && !data;
  const inResearch = all.filter(r => (r.status || '').toLowerCase() === 'research').length;
  const parked = all.filter(r => (r.status || '').toLowerCase() === 'parked').length;
  const runRows = all.reduce((n, r) => n + (r.runs?.length || 0), 0);
  const rank1 = all.find(r => (r.research_rank ?? 999) === Math.min(...all.map(x => x.research_rank ?? 999)));
  const rank1Blocker = rank1?.data_blocker || null;
  const selected = rows.find(r => r.strategy_id === selectedId) || null;
  const selectedHasRuns = (selected?.runs?.length || 0) > 0;

  return (
    <div className="space-y-3">
      <DerivKpiStrip
        tiles={[
          { label: 'Candidates', tip: 'Registered derivative strategy candidates (gold.derivatives_strategies)', value: sum.total ?? null,
            sub: data ? `${sum.options ?? 0} option · ${sum.futures ?? 0} future · ${sum.us ?? 0} US / ${sum.hk ?? 0} HK` : 'loading' },
          { label: 'In research', tip: 'Status = research (actively being worked)', value: data ? inResearch : null,
            sub: data ? `of ${sum.total ?? all.length} registered` : 'loading' },
          { label: 'Parked', tip: 'Status = parked (set aside, reason in the research card)', value: data ? parked : null,
            sub: data ? `of ${sum.total ?? all.length} registered` : 'loading' },
          { label: 'Backtested', tip: 'Candidates with at least one run in gold.derivatives_backtest_runs (variant rows count separately on the card)', value: data ? `${sum.backtested ?? 0} / ${sum.total ?? all.length}` : null,
            sub: data ? (runRows ? `${runRows} variant rows` : 'no runs yet') : 'loading' },
        ]}
      />

      {/* Rank-1 blocking decision + live KAT chips — ALWAYS visible (they were
          previously gated on zero backtested candidates and vanished when the
          first runs landed; that was emergent, not intended). */}
      {data && rank1Blocker && (
        <div className="qr-surface px-3 py-2 border-l-2 border-slate-500">
          <div className="flex items-baseline gap-2">
            <span className="qr-label mr-2 shrink-0">Blocking decision · rank 1</span>
            <span className="text-[10px] text-slate-400 whitespace-pre-wrap">{rank1Blocker}</span>
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
        note="Rank-ordered derivative strategy candidates — kept out of the equity strategy universe (Lab / Pipeline / Performance) by design. Click a row: candidates with runs expand into the strategy card (metrics, variants, ladder, rules); others show the verbatim research card. Metric columns read the headline (twin) run, total basis; click Sharpe / PF / MDD / Trades to sort (default = research rank)."
        right={<DerivResearchOnlyChip />}
      >
        <DerivTable
          cols={cols}
          rows={rows}
          rowKey={r => r.strategy_id}
          empty={failed ? 'Feed unavailable — see badge tooltip.' : 'No candidates match the active filters.'}
          sub={data ? `${data.count ?? all.length} registered · ${rows.length} shown` : undefined}
          onRowClick={r => setSelectedId(id => id === r.strategy_id ? null : r.strategy_id)}
          selectedId={selectedId}
          sort={sort}
          onSort={onSort}
        />
        {selected && (selectedHasRuns
          ? <DerivCandidateCard r={selected} onViewRuns={onViewRuns} />
          : <ResearchCard r={selected} />)}
      </DerivPanel>
    </div>
  );
}
