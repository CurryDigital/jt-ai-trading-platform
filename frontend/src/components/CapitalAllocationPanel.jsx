import React, { useEffect, useState } from 'react';
import { api, fmtK } from '../utils';

const PRESETS = [25_000, 50_000, 100_000, 250_000, 500_000, 1_000_000];

export const CapitalAllocationPanel = ({ strategyId, executionMode, activeSignalCount }) => {
  const [pool, setPool] = useState(null);
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState(0);
  const [busy, setBusy] = useState(false);
  const [feedback, setFeedback] = useState(null);

  const load = async () => {
    const data = await api.get(`/api/strategies/${encodeURIComponent(strategyId)}/capital-pool`);
    if (data) {
      setPool(data);
      setDraft(data.total_assigned);
    }
  };

  useEffect(() => {
    load();
    const id = setInterval(load, 30000);
    return () => clearInterval(id);
  }, [strategyId]);

  const save = async () => {
    setBusy(true);
    setFeedback(null);
    const res = await api.post(`/api/strategies/${encodeURIComponent(strategyId)}/capital-pool`, {
      total_assigned: Number(draft),
    });
    setBusy(false);
    if (res?.success) {
      setFeedback({ ok: true, msg: 'Capital updated' });
      setEditing(false);
      load();
      setTimeout(() => setFeedback(null), 2500);
    } else {
      setFeedback({ ok: false, msg: 'Update failed' });
    }
  };

  if (!pool) {
    return (
      <div className="qr-surface px-3 py-2.5 flex items-center gap-2 text-[11px] text-slate-500">
        <div className="w-3 h-3 border-2 border-slate-700 border-t-blue-500 rounded-full animate-spin" />
        Loading capital pool…
      </div>
    );
  }

  const usagePct = pool.usage_pct || 0;
  const usageColor = usagePct > 90 ? 'bg-rose-500' : usagePct > 70 ? 'bg-amber-500' : 'bg-emerald-500';

  // The backend pool counts cash-booking slots; the allocation tab counts actual
  // active BUY signals. Prefer the live signal count so the two panels agree.
  const activePositions = activeSignalCount != null ? activeSignalCount : pool.active_positions;
  const maxPositions = activeSignalCount != null
    ? Math.max(activeSignalCount, pool.max_positions)
    : pool.max_positions;

  return (
    <div className="qr-surface overflow-hidden">
      <div className="px-3 py-2 border-b border-white/[0.05] flex items-center justify-between flex-wrap gap-2">
        <div className="flex items-center gap-2">
          <span className="qr-label">Capital Allocation</span>
          {executionMode && (
            <span className={`qr-chip ${
              executionMode === 'LIVE_TRADING' ? 'qr-chip-rose' :
              executionMode === 'PAPER_TRADING' ? 'qr-chip-amber' : 'qr-chip-blue'
            }`}>
              {executionMode === 'LIVE_TRADING' ? 'LIVE' : executionMode === 'PAPER_TRADING' ? 'PAPER' : 'SIM'}
            </span>
          )}
        </div>
        <div className="flex items-center gap-2">
          {feedback && (
            <span className={`text-[10px] font-semibold ${feedback.ok ? 'text-emerald-300' : 'text-rose-300'}`}>{feedback.msg}</span>
          )}
          {!editing ? (
            <button onClick={() => setEditing(true)} className="qr-btn-ghost">Edit</button>
          ) : (
            <>
              <button
                onClick={save}
                disabled={busy || draft === pool.total_assigned}
                className={`qr-btn-primary ${busy || draft === pool.total_assigned ? 'opacity-50 cursor-not-allowed' : ''}`}
              >{busy ? 'Saving…' : 'Save'}</button>
              <button onClick={() => { setEditing(false); setDraft(pool.total_assigned); }} className="qr-btn-ghost">Cancel</button>
            </>
          )}
        </div>
      </div>

      <div className="p-3 space-y-3">
        {/* Metrics row */}
        <div className="grid grid-cols-2 md:grid-cols-5 gap-2">
          <Metric label="Pool Size" value={fmtK(pool.total_assigned)} sub="assigned" />
          <Metric label="Used"      value={fmtK(pool.used)}           sub={`${usagePct.toFixed(1)}%`} valClass={usagePct > 90 ? 'qr-pnl-neg' : 'text-slate-200'} />
          <Metric label="Available" value={fmtK(pool.available)}      sub={pool.can_trade ? 'can trade' : 'below 1 slot'} valClass={pool.can_trade ? 'qr-pnl-pos' : 'qr-pnl-neg'} />
          <Metric label="Slot Capital" value={fmtK(pool.trade_size)}  sub={pool.slot_pct != null ? `${(pool.slot_pct * 100).toFixed(0)}% of pool · 1/${pool.max_positions} slots` : 'per position'} />
          <Metric label="Positions" value={`${activePositions}/${maxPositions}`} sub="active" />
        </div>

        {/* Usage bar */}
        <div>
          <div className="h-1.5 bg-slate-800/60 rounded-full overflow-hidden">
            <div
              className={`h-full transition-all duration-500 ${usageColor}`}
              style={{ width: `${Math.min(100, usagePct)}%` }}
            />
          </div>
        </div>

        {/* Edit panel */}
        {editing && (
          <div className="border-t border-white/[0.05] pt-3 space-y-2">
            <div className="flex items-center gap-2">
              <input
                type="number"
                value={draft}
                onChange={(e) => setDraft(Number(e.target.value))}
                step="1000"
                min="0"
                className="px-2 py-1 bg-slate-900/60 border border-white/[0.08] rounded-md text-[12px] text-white w-32 focus:outline-none focus:border-blue-500/50 font-mono"
              />
              <span className="text-[10px] text-slate-500">USD</span>
              <span className="text-[10px] text-slate-600 ml-2">→ {fmtK(draft / Math.max(1, maxPositions))} per slot × {maxPositions} slots</span>
            </div>
            <div className="flex flex-wrap gap-1">
              {PRESETS.map(p => (
                <button
                  key={p}
                  onClick={() => setDraft(p)}
                  className={`px-2 py-0.5 rounded text-[10px] font-bold transition-colors ${
                    draft === p ? 'bg-blue-500 text-white' : 'bg-slate-800 text-slate-400 hover:text-white hover:bg-slate-700'
                  }`}
                >
                  {fmtK(p)}
                </button>
              ))}
            </div>
            {executionMode === 'LIVE_TRADING' && (
              <p className="text-[10px] text-amber-300/80">⚠ Changes apply to LIVE capital — affects real-money sizing</p>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

const Metric = ({ label, value, sub, valClass = 'text-white' }) => (
  <div className="px-2 py-1.5 bg-slate-900/40 rounded-md">
    <div className="qr-label">{label}</div>
    <div className={`qr-num text-[13px] font-bold leading-tight mt-0.5 ${valClass}`}>{value}</div>
    {sub && <div className="qr-num text-[9px] text-slate-500 mt-0.5">{sub}</div>}
  </div>
);

export default CapitalAllocationPanel;
