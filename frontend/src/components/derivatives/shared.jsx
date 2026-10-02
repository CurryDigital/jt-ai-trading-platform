// Shared primitives for the Derivatives vertical.
// Containment contract: this folder is the ONLY place derivatives UI lives.
// It must not import from other tabs' components and other tabs must not
// import from here. Data comes exclusively from /api/derivatives/* (Phase 2);
// until those endpoints serve real rows every panel renders an honest
// PENDING state — never synthetic data.

// Blocking data tasks (kanban, trading board) — named in tooltips per the
// data-honesty rule, never as inline clutter:
//   t_736850c6 qr_research — derivatives research registry (strategy feed)
//   t_15d7e66a qr_etl      — gold.derivatives_* ledgers (backtests/positions/fills)
//   t_822b6365 qr_etl      — Databento contract-month futures data (blocked)
export const TASK_RESEARCH_REGISTRY = 't_736850c6';
export const TASK_DERIV_LEDGERS = 't_15d7e66a';
export const TASK_FUTURES_DATA = 't_822b6365';

// Scroll cap for table bodies — same rule as IpoTab STAGE_SCROLL: feeds grow
// to hundreds of rows, so bodies never render uncapped.
const DERIV_SCROLL = { maxHeight: 340, overflowY: 'auto' };

// PENDING provenance badge — rose per house convention (NewsTab ProvBadge /
// IPO monthly-heatmap PENDING chips). Tooltip names endpoint + blocking task.
export function DerivPendingBadge({ endpoint, task }) {
  return (
    <span
      className="qr-chip qr-chip-rose"
      title={`Awaiting backend: ${endpoint} (Phase 2 — /api/derivatives/* router). Blocked by ${task}. No synthetic rows are shown.`}
    >
      Pending
    </span>
  );
}

export function DerivPanel({ title, endpoint, task, note, right, children }) {
  return (
    <div className="qr-surface p-3">
      <div className="flex items-center justify-between gap-2 mb-2">
        <div className="flex items-center gap-2 min-w-0">
          <span className="text-[11px] font-bold uppercase tracking-wider text-slate-300 truncate">{title}</span>
          {endpoint && <DerivPendingBadge endpoint={endpoint} task={task} />}
        </div>
        {right && <div className="shrink-0">{right}</div>}
      </div>
      {note && <div className="text-[10px] text-slate-500 mb-2">{note}</div>}
      {children}
    </div>
  );
}

export function DerivEmptyState({ line, sub }) {
  return (
    <div className="rounded border border-dashed border-white/[0.08] px-3 py-6 text-center">
      <div className="text-[11px] text-slate-500">{line}</div>
      {sub && <div className="text-[9px] text-slate-600 mt-1">{sub}</div>}
    </div>
  );
}

// KPI strip placeholder: every tile renders '—' (unscored/no-data), never a
// fabricated zero. Tooltip names the blocking task.
const KPI_COLS = { 1: 'xl:grid-cols-1', 2: 'xl:grid-cols-2', 3: 'xl:grid-cols-3', 4: 'xl:grid-cols-4', 5: 'xl:grid-cols-5', 6: 'xl:grid-cols-6' };
export function DerivKpiStrip({ tiles, task }) {
  return (
    <div className={`grid grid-cols-2 sm:grid-cols-3 ${KPI_COLS[Math.min(tiles.length, 6)]} gap-2`}>
      {tiles.map(t => (
        <div
          key={t.label}
          className="qr-surface px-2.5 py-2"
          title={`${t.tip || t.label} — blocked by ${task}`}
        >
          <div className="qr-label">{t.label}</div>
          <div className="font-mono text-base font-bold leading-tight text-slate-500">—</div>
          <div className="text-[9px] text-slate-600 truncate">{t.sub || 'pending'}</div>
        </div>
      ))}
    </div>
  );
}

// Table wireframe: real header row (the intended column contract) over an
// honest empty body. Scroll-capped so a future feed can't stretch the page.
export function DerivTableShell({ cols, empty, sub }) {
  return (
    <div className="rounded border border-white/[0.06] overflow-hidden">
      <div style={DERIV_SCROLL}>
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="border-b border-white/[0.06]">
              {cols.map(c => (
                <th key={c.label} className="qr-label px-2 py-1.5 whitespace-nowrap" title={c.tip || c.label}>
                  {c.label}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            <tr>
              <td colSpan={cols.length} className="px-2 py-0 border-0">
                <div className="py-4 text-center">
                  <div className="text-[11px] text-slate-500">{empty}</div>
                  {sub && <div className="text-[9px] text-slate-600 mt-1">{sub}</div>}
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  );
}

// Disabled filter-chip skeleton — shows the intended filter dimensions before
// the feed exists. Chips are inert (no state, no fetch) until Phase 2/3.
export function DerivChipSkeleton({ groups }) {
  return (
    <div className="qr-surface px-3 py-2 flex flex-wrap items-center gap-x-5 gap-y-2">
      {groups.map(g => (
        <div key={g.label} className="flex items-center gap-1.5" title={`Filter activates when the feed lands (${g.task})`}>
          <span className="qr-label">{g.label}</span>
          {g.options.map(o => (
            <span
              key={o}
              className={`qr-chip ${o === g.options[0] ? 'qr-chip-slate' : ''} opacity-50 cursor-not-allowed`}
            >
              {o}
            </span>
          ))}
        </div>
      ))}
    </div>
  );
}
