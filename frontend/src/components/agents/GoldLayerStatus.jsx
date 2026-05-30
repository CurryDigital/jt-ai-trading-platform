import React from 'react';

export function GoldLayerStatus({ status }) {
  if (!status) return null;

  const stateColor = status.state === 'ok' ? 'text-emerald-400' : status.state === 'error' ? 'text-rose-400' : 'text-amber-400';
  const hours = status.hours_since_refresh;
  const stale = hours != null && hours > 24;

  return (
    <div className="flex items-center gap-3 px-3 py-2 bg-slate-900/40 rounded-xl border border-white/[0.06]">
      <div className="flex items-center gap-1.5">
        <span className={`w-2 h-2 rounded-full ${status.state === 'ok' ? 'bg-emerald-500' : 'bg-rose-500'}`} />
        <span className="text-[10px] text-slate-500 uppercase font-bold">Gold Layer</span>
      </div>
      <span className={`text-[11px] font-mono font-bold ${stateColor}`}>{status.state}</span>
      {hours != null && (
        <span className={`text-[10px] ${stale ? 'text-rose-400' : 'text-slate-400'}`}>
          {hours.toFixed(1)}h since refresh
        </span>
      )}
      {status.sources_ok != null && (
        <span className="text-[10px] text-slate-500">
          {status.sources_ok} sources OK
        </span>
      )}
      {status.sources_failed ? (
        <span className="text-[10px] text-rose-400">
          {status.sources_failed} failed
        </span>
      ) : null}
    </div>
  );
}
