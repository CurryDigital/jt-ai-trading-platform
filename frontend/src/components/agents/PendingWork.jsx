import React from 'react';
import { STATUS_COLORS, extractSymbols, formatTimeAgo, resolveAgent } from './utils';

export function PendingWork({ workItems, agents, selectedAgent, onSelectStrategy }) {
  if (!workItems || workItems.length === 0) {
    return (
      <div className="text-center p-8 text-slate-500">
        <div className="text-3xl mb-3">✅</div>
        <p className="text-sm font-medium text-slate-400">No pending work</p>
        <p className="text-[11px] text-slate-600 mt-1">All work has been processed.</p>
      </div>
    );
  }

  const registry = Object.fromEntries((agents || []).map(a => [a.agent_id, a]));

  // Group by target agent
  const grouped = {};
  workItems.forEach(w => {
    if (!grouped[w.target_agent]) grouped[w.target_agent] = [];
    grouped[w.target_agent].push(w);
  });

  const agentsToShow = selectedAgent ? [selectedAgent] : Object.keys(grouped);

  return (
    <div className="divide-y divide-white/5">
      {agentsToShow.map(agentId => {
        const items = grouped[agentId];
        if (!items || items.length === 0) return null;
        const agentInfo = resolveAgent(agentId, registry);
        const allSymbols = new Set();
        items.forEach(w => {
          const syms = extractSymbols(w.strategy_name) || [];
          syms.forEach(s => allSymbols.add(s));
        });
        const symbols = Array.from(allSymbols);

        return (
          <div key={agentId} className="p-4">
            <div className="flex items-center gap-2 mb-3">
              <span className="text-lg">{agentInfo.icon}</span>
              <span className="text-xs font-bold text-white">{agentInfo.name}</span>
              <span className="text-[9px] px-1.5 py-0.5 rounded bg-blue-500/20 text-blue-400 font-bold">{items.length} pending</span>
              {symbols.length > 0 && (
                <div className="flex gap-1 ml-auto">
                  {symbols.slice(0, 5).map(s => (
                    <span key={s} className="text-[8px] px-1.5 py-0.5 rounded bg-amber-500/15 text-amber-400 font-mono font-bold">{s}</span>
                  ))}
                  {symbols.length > 5 && (
                    <span className="text-[8px] px-1.5 py-0.5 rounded bg-slate-700/50 text-slate-500 font-mono">+{symbols.length - 5}</span>
                  )}
                </div>
              )}
            </div>
            <div className="space-y-1">
              {items.map(w => {
                const syms = extractSymbols(w.strategy_name) || [];
                const statusClass = STATUS_COLORS[w.work_status] || STATUS_COLORS.pending;
                return (
                  <div
                    key={`${w.strategy_id}-${w.domain}`}
                    onClick={() => w.strategy_id && onSelectStrategy && onSelectStrategy(w.strategy_id)}
                    className={`flex items-center gap-2 py-1.5 px-2 rounded bg-slate-800/30 ${w.strategy_id && onSelectStrategy ? 'cursor-pointer hover:bg-slate-800/50' : ''}`}
                  >
                    <span className={`text-[9px] px-1.5 py-0.5 rounded font-bold ${statusClass}`}>
                      {w.work_status}
                    </span>
                    {w.strategy_id && (
                      <span className="text-[9px] text-amber-400 font-mono">
                        {w.strategy_id.slice(0, 20)}
                        {syms.length > 0 && (
                          <span className="text-slate-500 ml-1">({syms.join(', ')})</span>
                        )}
                      </span>
                    )}
                    <span className="text-[9px] text-slate-600">{w.domain}</span>
                    <span className="text-[9px] text-slate-600 ml-auto">{formatTimeAgo(w.updated_at)}</span>
                  </div>
                );
              })}
            </div>
          </div>
        );
      })}
    </div>
  );
}
