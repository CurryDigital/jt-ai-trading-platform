import React from 'react';
import { resolveAgent } from './utils';

export function AgentPipeline({ agents, pendingByAgent, selectedAgent, onSelectAgent }) {
  if (!agents.length) return null;

  return (
    <div className="overflow-x-auto no-scrollbar">
      <div className="flex items-center gap-1 min-w-max p-3">
        {agents.map((agent, i) => {
          const isSelected = selectedAgent === agent.agent_id;
          const pendingCount = pendingByAgent[agent.agent_id] || 0;
          return (
            <React.Fragment key={agent.agent_id}>
              {i > 0 && (
                <div className="flex-shrink-0 w-6 flex items-center justify-center">
                  <svg className="w-4 h-3 text-slate-700" viewBox="0 0 16 12" fill="none">
                    <path d="M1 6h14M11 1l4 5-4 5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
                  </svg>
                </div>
              )}
              <button
                onClick={() => onSelectAgent(agent.agent_id)}
                className={`relative flex-shrink-0 flex flex-col items-center gap-1 px-3 py-2 rounded-xl transition-all ${
                  isSelected
                    ? 'bg-blue-500/20 border border-blue-500/40 ring-1 ring-blue-500/20'
                    : 'bg-slate-900/50 border border-white/5 hover:border-white/10'
                }`}
              >
                <span className="text-lg">{agent.icon}</span>
                <span className="text-[9px] text-slate-400 uppercase tracking-wider font-medium whitespace-nowrap">{agent.name}</span>
                {pendingCount > 0 && (
                  <span className="absolute -top-1 -right-1 w-4 h-4 rounded-full bg-blue-500 text-[8px] text-white font-bold flex items-center justify-center">
                    {pendingCount}
                  </span>
                )}
              </button>
            </React.Fragment>
          );
        })}
      </div>
    </div>
  );
}
