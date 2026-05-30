import React, { useState } from 'react';
import { WORK_TYPE_COLORS, formatTimeAgo, resolveAgent } from './utils';

export function CompletedWork({ completedItems, agents, loading }) {
  const [dateFilter, setDateFilter] = useState('');

  if (loading) {
    return (
      <div className="text-center p-8 text-slate-500">
        <div className="w-6 h-6 border-2 border-slate-600 border-t-emerald-500 rounded-full animate-spin mx-auto mb-2" />
        <p className="text-xs">Loading completed work...</p>
      </div>
    );
  }

  const registry = Object.fromEntries((agents || []).map(a => [a.agent_id, a]));

  const filtered = (() => {
    if (!dateFilter) return completedItems;
    const today = new Date().toISOString().split('T')[0];
    if (dateFilter === 'today') {
      return completedItems.filter(item => item.processed_at?.startsWith(today));
    }
    if (dateFilter === 'week') {
      const weekAgo = new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString();
      return completedItems.filter(item => item.processed_at >= weekAgo);
    }
    if (dateFilter === 'month') {
      const monthAgo = new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString();
      return completedItems.filter(item => item.processed_at >= monthAgo);
    }
    return completedItems;
  })();

  if (!filtered || filtered.length === 0) {
    return (
      <div className="text-center p-8 text-slate-500">
        <div className="text-3xl mb-3">📭</div>
        <p className="text-sm font-medium text-slate-400">No completed work</p>
        <p className="text-[11px] text-slate-600 mt-1">No processed work found for the selected filter.</p>
      </div>
    );
  }

  return (
    <div>
      <div className="px-4 py-2.5 border-b border-white/[0.06] flex items-center justify-between">
        <span className="text-[10px] text-slate-500 uppercase font-bold tracking-wider">Completed History</span>
        <div className="flex items-center gap-2">
          <select
            value={dateFilter}
            onChange={(e) => setDateFilter(e.target.value)}
            className="bg-slate-800/80 border border-white/10 rounded px-2 py-1 text-[10px] text-slate-300 outline-none"
          >
            <option value="">All time</option>
            <option value="today">Today</option>
            <option value="week">Last 7 days</option>
            <option value="month">Last 30 days</option>
          </select>
          <span className="text-[10px] text-slate-600">{filtered.length} items</span>
        </div>
      </div>
      <div className="divide-y divide-white/5 max-h-[500px] overflow-y-auto">
        {filtered.map(c => {
          const agentInfo = resolveAgent(c.processed_by, registry);
          const typeClass = WORK_TYPE_COLORS[c.work_type] || 'bg-slate-700/50 text-slate-400';
          return (
            <div key={`${c.strategy_id}-${c.processed_at}`} className="flex items-center gap-3 p-3 hover:bg-white/[0.02] transition-colors">
              <div className="flex-shrink-0 w-8 h-8 rounded-lg bg-emerald-500/10 flex items-center justify-center text-sm">
                ✅
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1 flex-wrap">
                  <span className={`text-[9px] px-1.5 py-0.5 rounded font-bold ${typeClass}`}>
                    {c.work_type}
                  </span>
                  {c.strategy_id && (
                    <span className="text-[9px] text-amber-400 font-mono">{c.strategy_id}</span>
                  )}
                </div>
                <div className="flex items-center gap-2 text-[9px] text-slate-500">
                  <span>By: <span className="text-emerald-400">{agentInfo.name}</span></span>
                  <span>Status: <span className={c.processing_status === 'APPROVED' ? 'text-emerald-400' : 'text-rose-400'}>{c.processing_status}</span></span>
                  {c.conviction_score != null && (
                    <span>Conviction: <span className="text-white font-mono">{c.conviction_score.toFixed(1)}</span></span>
                  )}
                </div>
              </div>
              <div className="flex flex-col items-end flex-shrink-0">
                <span className="text-[10px] text-slate-600">{formatTimeAgo(c.processed_at)}</span>
                <span className="text-[8px] text-slate-700">{c.processed_at?.slice(0, 10)}</span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
