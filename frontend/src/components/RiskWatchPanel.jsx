import React, { useEffect, useState } from 'react';
import { api, fmtAge } from '../utils';

const fmtRule = (id, v) => {
  if (v == null) return '—';
  if (id === 'consecutive_losses') return v;
  if (id === 'min_live_pf') return Number(v).toFixed(2);
  return `${Number(v).toFixed(2)}%`;
};

export const RiskWatchPanel = ({ strategyId, executionMode, onDemoted }) => {
  const [status, setStatus] = useState(null);
  const [error, setError] = useState(false);
  const [refreshedAt, setRefreshedAt] = useState(null);
  const [busy, setBusy] = useState(false);

  const load = async () => {
    setError(false);
    const res = await api.get(`/api/strategies/${encodeURIComponent(strategyId)}/risk-status?t=${Date.now()}`);
    if (res) {
      setStatus(res);
      setError(false);
    } else {
      setError(true);
      setStatus(null);
    }
    setRefreshedAt(new Date().toISOString());
  };

  useEffect(() => {
    load();
    const id = setInterval(load, 30000);
    return () => clearInterval(id);
  }, [strategyId]);

  const forceCheck = async () => {
    setBusy(true);
    setError(false);
    const res = await api.post(`/api/strategies/${encodeURIComponent(strategyId)}/auto-demote-check`, {});
    setBusy(false);
    if (res?.demoted) onDemoted?.();
    if (res) {
      setStatus(res);
      setError(false);
    } else {
      setStatus(null);
      setError(true);
    }
    setRefreshedAt(new Date().toISOString());
  };

  if (error) {
    return (
      <div className="qr-surface px-3 py-2.5">
        <div className="flex items-center justify-between gap-2 flex-wrap">
          <div className="text-[11px] text-rose-300">
            ⚠ Risk status unavailable · endpoint returned an error.
          </div>
          <button onClick={load} className="qr-btn-ghost">↻ Retry</button>
        </div>
      </div>
    );
  }

  if (!status) {
    return (
      <div className="qr-surface px-3 py-2.5 flex items-center gap-2 text-[11px] text-slate-500">
        <div className="w-3 h-3 border-2 border-slate-700 border-t-blue-500 rounded-full animate-spin" />
        Loading risk status…
      </div>
    );
  }

  const breached = status.breaches?.length || 0;
  const eligible = executionMode === 'LIVE_TRADING';

  return (
    <div className="qr-surface overflow-hidden">
      <div className="px-3 py-2 border-b border-white/[0.05] flex items-center justify-between flex-wrap gap-2">
        <div className="flex items-center gap-2">
          <span className="qr-label">Risk Watch</span>
          <span className={`qr-chip ${
            !eligible ? 'qr-chip-slate' :
            breached === 0 ? 'qr-chip-emerald' : 'qr-chip-rose'
          }`}>
            {!eligible ? 'NOT LIVE' : breached === 0 ? 'ALL OK' : `${breached} BREACH${breached > 1 ? 'ES' : ''}`}
          </span>
          {!eligible && <span className="text-[10px] text-slate-500">— rules only enforced in LIVE mode</span>}
        </div>
        <div className="flex items-center gap-2">
          <span className="qr-num text-[10px] text-slate-500">
            {status.trades_analyzed} trades · upd {fmtAge(refreshedAt)}
          </span>
          <button onClick={forceCheck} disabled={busy} className="qr-btn-ghost">
            {busy ? '…' : '↻ Check now'}
          </button>
        </div>
      </div>

      <div className="p-3">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-1">
          {(status.rules || []).map(r => (
            <div
              key={r.id}
              className={`flex items-start gap-2 px-2.5 py-1.5 rounded-md ring-1 ${
                r.breach
                  ? 'bg-rose-500/5 ring-rose-500/20'
                  : 'bg-emerald-500/5 ring-emerald-500/15'
              }`}
            >
              <span className={`mt-0.5 inline-flex items-center justify-center w-4 h-4 rounded-full text-[9px] font-bold ${
                r.breach ? 'bg-rose-500/20 text-rose-300' : 'bg-emerald-500/20 text-emerald-300'
              }`}>
                {r.breach ? '!' : '✓'}
              </span>
              <div className="min-w-0 flex-1">
                <div className="text-[11px] text-white font-semibold">{r.label}</div>
                <div className="qr-num text-[9px] text-slate-500 mt-0.5">
                  actual <span className={r.breach ? 'text-rose-300' : 'text-slate-300'}>{fmtRule(r.id, r.actual)}</span>
                  <span className="text-slate-700 mx-1">·</span>
                  limit <span className="text-slate-300">{fmtRule(r.id, r.threshold)}</span>
                </div>
                {r.breach && r.reason && (
                  <div className="text-[9px] text-rose-300/80 mt-0.5">{r.reason}</div>
                )}
              </div>
            </div>
          ))}
        </div>

        {breached > 0 && eligible && (
          <div className="mt-3 text-[11px] text-rose-200 bg-rose-500/10 ring-1 ring-rose-500/25 rounded px-3 py-2">
            <span className="font-bold">⚠ Auto-demote pending.</span> The background scanner will demote this strategy to PAPER on its next pass (every ~5 min). Click <span className="text-white font-semibold">Check now</span> to demote immediately.
          </div>
        )}
      </div>
    </div>
  );
};

export default RiskWatchPanel;
