import React, { useState, useEffect, useCallback } from 'react';
import { api } from '../utils';

const PRIORITY_STYLE = {
  GOLDEN: 'qr-chip-amber',
  NEAR_GOLDEN: 'qr-chip-blue',
  EXPERIMENTAL: 'qr-chip-slate',
};

export const StrategyReviewQueue = ({ onSelectStrategy }) => {
  const [queue, setQueue] = useState([]);
  const [loading, setLoading] = useState(true);
  const [acting, setActing] = useState(null);
  const [expanded, setExpanded] = useState(null);

  const load = useCallback(async () => {
    const res = await api.get('/api/strategies/review-queue');
    if (res?.strategies) setQueue(res.strategies);
    setLoading(false);
  }, []);

  useEffect(() => { load(); }, [load]);

  const act = async (id, action) => {
    setActing(`${id}:${action}`);
    const res = await api.post(`/api/strategies/${id}/${action}`);
    if (res?.success) {
      setQueue(q => q.filter(s => s.id !== id));
      setExpanded(null);
    }
    setActing(null);
  };

  if (loading) {
    return (
      <div className="qr-surface px-3 py-4 flex items-center justify-center gap-2 text-[11px] text-slate-500">
        <div className="w-3 h-3 border-2 border-slate-700 border-t-blue-500 rounded-full animate-spin" />
        Loading review queue…
      </div>
    );
  }

  return (
    <div className="qr-surface overflow-hidden">
      <div className="px-3 py-2 border-b border-white/[0.05] flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="qr-label">Strategy Review Queue</span>
          {queue.length > 0 && (
            <span className="qr-chip qr-chip-amber">{queue.length} pending</span>
          )}
        </div>
        <button onClick={load} className="qr-btn-ghost text-[10px]">Refresh</button>
      </div>

      {!queue.length ? (
        <div className="px-3 py-6 text-center text-slate-600 text-[11px]">
          No strategies pending review — all clear
        </div>
      ) : (
        <div className="divide-y divide-white/[0.04]">
          {queue.map(s => {
            const isExpanded = expanded === s.id;
            return (
              <div key={s.id} className="hover:bg-white/[0.02] transition-colors">
                <div className="px-3 py-2.5 flex items-center gap-3">
                  <div className="flex-1 min-w-0 cursor-pointer" onClick={() => setExpanded(isExpanded ? null : s.id)}>
                    <div className="flex items-center gap-2">
                      <span className="text-[12px] font-bold text-white truncate">{s.name || s.id}</span>
                      <span className={`qr-chip ${PRIORITY_STYLE[s.priority] || 'qr-chip-slate'}`}>{s.priority}</span>
                      {s.version && <span className="text-[9px] text-slate-600">v{s.version}</span>}
                    </div>
                    <div className="text-[10px] text-slate-500 mt-0.5">
                      WR {s.win_rate != null ? `${s.win_rate}%` : '—'} · {(s.target_assets || []).length} tickers
                      {s.target_assets?.length > 0 && <span className="ml-1 text-slate-600">({s.target_assets.slice(0, 3).join(', ')}{s.target_assets.length > 3 ? '…' : ''})</span>}
                    </div>
                  </div>
                  <div className="flex items-center gap-1.5 flex-shrink-0">
                    <button
                      onClick={() => act(s.id, 'approve')}
                      disabled={!!acting}
                      className="px-2.5 py-1 rounded bg-emerald-500/20 text-emerald-300 ring-1 ring-emerald-500/30 text-[10px] font-bold hover:bg-emerald-500/30 disabled:opacity-50 transition-colors"
                    >
                      {acting === `${s.id}:approve` ? '…' : 'Approve'}
                    </button>
                    <button
                      onClick={() => act(s.id, 'reject')}
                      disabled={!!acting}
                      className="px-2.5 py-1 rounded bg-rose-500/15 text-rose-300 ring-1 ring-rose-500/20 text-[10px] font-bold hover:bg-rose-500/25 disabled:opacity-50 transition-colors"
                    >
                      {acting === `${s.id}:reject` ? '…' : 'Reject'}
                    </button>
                  </div>
                </div>

                {isExpanded && (
                  <div className="px-3 pb-3 space-y-1.5">
                    {s.entry_logic && (
                      <div className="text-[10px]">
                        <span className="text-slate-500">Entry: </span>
                        <span className="text-slate-300">{s.entry_logic}</span>
                      </div>
                    )}
                    {s.exit_logic && (
                      <div className="text-[10px]">
                        <span className="text-slate-500">Exit: </span>
                        <span className="text-slate-300">{s.exit_logic}</span>
                      </div>
                    )}
                    {s.target_assets?.length > 0 && (
                      <div className="flex flex-wrap gap-1 mt-1">
                        {s.target_assets.map(t => (
                          <span key={t} className="px-1.5 py-0.5 rounded bg-slate-800 text-[9px] font-mono text-slate-400">{t}</span>
                        ))}
                      </div>
                    )}
                    <button
                      onClick={() => onSelectStrategy?.(s.id)}
                      className="text-[10px] text-blue-400 hover:text-blue-300 font-semibold mt-1"
                    >
                      View Details →
                    </button>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};

export default StrategyReviewQueue;
