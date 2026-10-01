// Shared primitives for the Derivatives vertical.
// Containment contract: this folder is the ONLY place derivatives UI lives.
// It must not import from other tabs' components and other tabs must not
// import from here. Data comes exclusively from /api/derivatives/* (Phase 2);
// until those endpoints serve real rows every panel renders an honest
// PENDING state — never synthetic data.

export function DerivPendingBadge({ endpoint }) {
  return (
    <span
      className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[9px] font-bold uppercase tracking-wider text-slate-500 bg-white/[0.05]"
      title={`Awaiting backend: ${endpoint} (Phase 2 — /api/derivatives/* router). Data feeds are qr_etl-owned; no synthetic rows are shown.`}
    >
      Pending
    </span>
  );
}

export function DerivPanel({ title, endpoint, note, children }) {
  return (
    <div className="qr-surface p-3">
      <div className="flex items-center justify-between gap-2 mb-2">
        <div className="flex items-center gap-2 min-w-0">
          <span className="text-[11px] font-bold uppercase tracking-wider text-slate-300 truncate">{title}</span>
          <DerivPendingBadge endpoint={endpoint} />
        </div>
      </div>
      {note && <div className="text-[10px] text-slate-500 mb-2">{note}</div>}
      {children}
    </div>
  );
}

export function DerivEmptyState({ line }) {
  return (
    <div className="rounded border border-dashed border-white/[0.08] px-3 py-6 text-center text-[11px] text-slate-500">
      {line}
    </div>
  );
}
