import React from 'react';

export default function SystemStatusBar({ data }) {
  if (!data || data.state === 'error') {
    return (
      <div className="rounded-lg bg-rose-500/10 border border-rose-500/20 p-4 mb-6">
        <p className="text-rose-400 text-sm">System status unavailable</p>
      </div>
    );
  }

  const {
    regime_label,
    regime_confidence,
    regime_override,
    regime_staleness_days,
    last_run_date,
    last_run_type,
    last_run_status,
    last_orders_placed,
    last_orders_skipped,
    paper_nav_usd,
    paper_nav_hkd,
  } = data;

  const regimeColor =
    regime_label === 'TREND' ? 'text-emerald-400' :
    regime_label === 'MEAN_REV' ? 'text-blue-400' :
    regime_label === 'HIGH_VOL' ? 'text-amber-400' :
    'text-slate-400';

  const regimeBg =
    regime_label === 'TREND' ? 'bg-emerald-500/10 border-emerald-500/20' :
    regime_label === 'MEAN_REV' ? 'bg-blue-500/10 border-blue-500/20' :
    regime_label === 'HIGH_VOL' ? 'bg-amber-500/10 border-amber-500/20' :
    'bg-slate-500/10 border-slate-500/20';

  return (
    <div className={`rounded-lg border p-4 mb-6 ${regimeBg}`}>
      <div className="flex flex-wrap items-center gap-6">
        {/* Regime */}
        <div className="flex items-center gap-2">
          <span className="text-[10px] uppercase tracking-wider text-slate-500">Regime</span>
          <span className={`text-sm font-bold ${regimeColor}`}>
            {regime_label || 'Unknown'}
          </span>
          {regime_override && (
            <span className="text-[10px] bg-amber-500/20 text-amber-400 px-1.5 py-0.5 rounded">
              Override
            </span>
          )}
          <span className="text-[10px] text-slate-500">
            {regime_confidence !== null ? `${(regime_confidence * 100).toFixed(0)}%` : ''}
          </span>
          {regime_staleness_days > 0 && (
            <span className="text-[10px] text-amber-400">
              {regime_staleness_days}d stale
            </span>
          )}
        </div>

        {/* Last Run */}
        <div className="flex items-center gap-2">
          <span className="text-[10px] uppercase tracking-wider text-slate-500">Last Run</span>
          <span className="text-sm text-slate-300">{last_run_type || '—'}</span>
          <span className={`text-[10px] px-1.5 py-0.5 rounded ${
            last_run_status === 'ok' ? 'bg-emerald-500/20 text-emerald-400' :
            'bg-rose-500/20 text-rose-400'
          }`}>
            {last_run_status || '—'}
          </span>
          <span className="text-[10px] text-slate-500">{last_run_date || ''}</span>
        </div>

        {/* Orders */}
        <div className="flex items-center gap-2">
          <span className="text-[10px] uppercase tracking-wider text-slate-500">Orders</span>
          <span className="text-sm text-emerald-400">{last_orders_placed || 0} placed</span>
          {last_orders_skipped > 0 && (
            <span className="text-sm text-amber-400">{last_orders_skipped} skipped</span>
          )}
        </div>

        {/* NAV */}
        <div className="flex items-center gap-2 ml-auto">
          <span className="text-[10px] uppercase tracking-wider text-slate-500">NAV</span>
          <span className="text-sm font-mono text-slate-300">
            ${paper_nav_usd?.toLocaleString() || '—'} USD
          </span>
          <span className="text-sm font-mono text-slate-400">
            ${paper_nav_hkd?.toLocaleString() || '—'} HKD
          </span>
        </div>
      </div>
    </div>
  );
}
