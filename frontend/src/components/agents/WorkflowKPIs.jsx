import React from 'react';

const KPI_CONFIG = [
  { key: 'total', label: 'Total', color: 'text-white' },
  { key: 'backtesting', label: 'Backtesting', color: 'text-blue-400' },
  { key: 'risk_review', label: 'Risk Review', color: 'text-amber-400' },
  { key: 'qa_review', label: 'QA Review', color: 'text-violet-400' },
  { key: 'approved', label: 'Approved', color: 'text-emerald-400' },
  { key: 'deployed', label: 'Deployed', color: 'text-emerald-300' },
  { key: 'rejected', label: 'Rejected', color: 'text-rose-400' },
  { key: 'golden', label: 'Golden', color: 'text-amber-400' },
];

export function WorkflowKPIs({ summary, pendingCount }) {
  if (!summary) return null;

  return (
    <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-5 gap-2">
      {KPI_CONFIG.map(kpi => (
        <div key={kpi.key} className="px-3 py-2.5 bg-slate-900/60 rounded-xl border border-white/[0.06]">
          <div className="text-[9px] text-slate-500 uppercase tracking-wider">{kpi.label}</div>
          <div className={`text-lg font-bold font-mono ${kpi.color}`}>{summary[kpi.key] ?? 0}</div>
        </div>
      ))}
      <div className="px-3 py-2.5 bg-slate-900/60 rounded-xl border border-white/[0.06]">
        <div className="text-[9px] text-slate-500 uppercase tracking-wider">Pending Work</div>
        <div className="text-lg font-bold font-mono text-blue-400">{pendingCount ?? 0}</div>
      </div>
    </div>
  );
}
