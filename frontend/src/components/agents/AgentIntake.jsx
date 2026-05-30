import React, { useState } from 'react';
import { PendingWork } from './PendingWork';
import { CompletedWork } from './CompletedWork';
import { resolveAgent } from './utils';

export function AgentIntake({ agentId, agents, pendingWork, completedWork, onSelectStrategy }) {
  const [activeTab, setActiveTab] = useState('pending');
  const registry = Object.fromEntries((agents || []).map(a => [a.agent_id, a]));
  const agentInfo = resolveAgent(agentId, registry);

  const agentPending = (pendingWork.work_items || []).filter(w => w.target_agent === agentId);
  const agentCompleted = (completedWork.completed_items || []).filter(c => c.processed_by === agentId);

  // Auto-switch to completed if no pending
  React.useEffect(() => {
    if (agentPending.length === 0 && agentCompleted.length > 0 && activeTab === 'pending') {
      setActiveTab('completed');
    }
  }, [agentPending.length, agentCompleted.length]);

  return (
    <div className="space-y-4">
      {/* Agent Header */}
      <div className="flex items-center gap-3 p-3 bg-blue-500/5 rounded-xl border border-blue-500/20">
        <span className="text-2xl">{agentInfo.icon}</span>
        <div className="flex-1">
          <div className="text-sm font-bold text-white">
            {agentInfo.name} <span className="text-[10px] text-slate-500 font-normal font-mono">({agentId})</span>
          </div>
          <p className="text-[11px] text-slate-400">{agentInfo.role || 'Agent in research pipeline'}</p>
        </div>
        <div className="flex items-center gap-2">
          <span className="px-2 py-1 rounded-lg bg-blue-500/20 text-blue-400 text-xs font-bold">
            {agentPending.length} pending
          </span>
          <span className="px-2 py-1 rounded-lg bg-emerald-500/20 text-emerald-400 text-xs font-bold">
            {agentCompleted.length} completed
          </span>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex items-center gap-1 p-1 rounded-lg bg-slate-900/50 border border-white/[0.06]">
        <button
          onClick={() => setActiveTab('pending')}
          className={`flex-1 px-3 py-1.5 rounded-md text-[10px] font-bold transition-colors ${
            activeTab === 'pending' ? 'bg-blue-500 text-white shadow-sm' : 'text-slate-400 hover:text-white'
          }`}
        >
          Pending ({agentPending.length})
        </button>
        <button
          onClick={() => setActiveTab('completed')}
          className={`flex-1 px-3 py-1.5 rounded-md text-[10px] font-bold transition-colors ${
            activeTab === 'completed' ? 'bg-emerald-500 text-white shadow-sm' : 'text-slate-400 hover:text-white'
          }`}
        >
          Completed ({agentCompleted.length})
        </button>
      </div>

      {/* Content */}
      <div className="bg-slate-900/40 rounded-xl border border-white/[0.06] overflow-hidden">
        {activeTab === 'pending' && (
          <PendingWork
            workItems={agentPending}
            agents={agents}
            selectedAgent={null}
            onSelectStrategy={onSelectStrategy}
          />
        )}
        {activeTab === 'completed' && (
          <CompletedWork
            completedItems={agentCompleted}
            agents={agents}
            loading={false}
          />
        )}
      </div>
    </div>
  );
}
