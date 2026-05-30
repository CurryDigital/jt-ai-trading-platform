import React, { useState } from 'react';
import {
  AgentPipeline,
  WorkflowKPIs,
  StrategyWorkflows,
  PendingWork,
  CompletedWork,
  StrategyDetail,
  AgentIntake,
  GoldLayerStatus,
  useAgentData,
} from './agents';

const TABS = [
  { id: 'workflows', label: 'Workflows' },
  { id: 'pending', label: 'Pending' },
  { id: 'intake', label: 'Intake' },
];

export const AgenticResearch = () => {
  const {
    agents,
    workflowSummary,
    workflows,
    pendingWork,
    completedWork,
    goldStatus,
    loading,
    error,
  } = useAgentData();

  const [activeView, setActiveView] = useState('workflows');
  const [selectedAgent, setSelectedAgent] = useState(null);
  const [selectedStrategy, setSelectedStrategy] = useState(null);

  const handleSelectAgent = (agentId) => {
    setSelectedAgent(agentId);
    if (agentId) {
      setActiveView('intake');
    }
  };

  if (loading && !agents.length) {
    return (
      <div className="p-12 text-center text-slate-500">
        <div className="w-8 h-8 border-2 border-slate-600 border-t-blue-500 rounded-full animate-spin mx-auto mb-4" />
        Loading agent research pipeline...
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-12 text-center text-rose-400">
        <div className="text-3xl mb-3">⚠️</div>
        <p className="text-sm font-medium">Failed to load agent data</p>
        <p className="text-[11px] text-slate-500 mt-1">{error}</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-bold text-white">Agentic Research</h2>
          <p className="text-xs text-slate-500 mt-0.5">
            {agents.length} Hermes agents · {workflows.length} strategies in pipeline
          </p>
        </div>
        <div className="flex items-center gap-1 p-1 rounded-lg bg-slate-900/50 border border-white/[0.06]">
          {TABS.map(tab => (
            <button
              key={tab.id}
              onClick={() => {
                setActiveView(tab.id);
                setSelectedStrategy(null);
                if (tab.id !== 'intake') setSelectedAgent(null);
              }}
              className={`px-3 py-1.5 rounded-md text-[10px] font-bold transition-colors ${
                activeView === tab.id ? 'bg-blue-500 text-white shadow-sm' : 'text-slate-400 hover:text-white'
              }`}
            >
              {tab.id === 'pending' ? `Pending (${pendingWork.count || 0})` : tab.label}
            </button>
          ))}
        </div>
      </div>

      {/* KPIs + Gold Status */}
      <WorkflowKPIs summary={workflowSummary} pendingCount={pendingWork.count} />
      <GoldLayerStatus status={goldStatus} />

      {/* Agent Pipeline */}
      <div className="bg-slate-900/40 rounded-xl border border-white/[0.06] overflow-hidden">
        <div className="px-4 py-2.5 border-b border-white/[0.06] flex items-center gap-2">
          <span className="text-[10px] text-slate-500 uppercase font-bold tracking-wider">Agent Pipeline</span>
          {selectedAgent && (
            <button
              onClick={() => { setSelectedAgent(null); setActiveView('workflows'); }}
              className="text-[10px] text-blue-400 hover:text-blue-300"
            >
              Clear filter
            </button>
          )}
        </div>
        <AgentPipeline
          agents={agents}
          pendingByAgent={pendingWork.by_agent || {}}
          selectedAgent={selectedAgent}
          onSelectAgent={handleSelectAgent}
        />
      </div>

      {/* Strategy Detail Overlay */}
      {selectedStrategy && (
        <div className="bg-slate-900/60 rounded-xl border border-blue-500/20 p-4">
          <StrategyDetail strategyId={selectedStrategy} onClose={() => setSelectedStrategy(null)} />
        </div>
      )}

      {/* Main Content */}
      <div className="bg-slate-900/40 rounded-xl border border-white/[0.06] overflow-hidden">
        {activeView === 'workflows' && (
          <>
            <div className="px-4 py-2.5 border-b border-white/[0.06] flex items-center justify-between">
              <span className="text-[10px] text-slate-500 uppercase font-bold tracking-wider">Strategy Workflows</span>
              <span className="text-[10px] text-slate-600">{workflows.length} strategies</span>
            </div>
            <StrategyWorkflows workflows={workflows} onSelectStrategy={setSelectedStrategy} />
          </>
        )}

        {activeView === 'pending' && (
          <>
            <div className="px-4 py-2.5 border-b border-white/[0.06] flex items-center justify-between">
              <span className="text-[10px] text-slate-500 uppercase font-bold tracking-wider">Pending Work</span>
              <span className="text-[10px] text-slate-600">{pendingWork.count || 0} items</span>
            </div>
            <PendingWork
              workItems={pendingWork.work_items || []}
              agents={agents}
              selectedAgent={selectedAgent}
              onSelectStrategy={setSelectedStrategy}
            />
          </>
        )}

        {activeView === 'intake' && selectedAgent && (
          <>
            <div className="px-4 py-2.5 border-b border-white/[0.06]">
              <span className="text-[10px] text-slate-500 uppercase font-bold tracking-wider">Agent Intake</span>
            </div>
            <div className="p-4">
              <AgentIntake
                agentId={selectedAgent}
                agents={agents}
                pendingWork={pendingWork}
                completedWork={completedWork}
                onSelectStrategy={setSelectedStrategy}
              />
            </div>
          </>
        )}

        {activeView === 'intake' && !selectedAgent && (
          <div className="text-center p-12 text-slate-500">
            <div className="text-3xl mb-3">👆</div>
            <p className="text-sm font-medium text-slate-400">Select an agent from the pipeline</p>
            <p className="text-[11px] text-slate-600 mt-1">Click on any agent to see their pending and completed work</p>
          </div>
        )}
      </div>

      {/* All Agents Grid */}
      {!selectedAgent && !selectedStrategy && (
        <div className="bg-slate-900/40 rounded-xl border border-white/[0.06] overflow-hidden">
          <div className="px-4 py-2.5 border-b border-white/[0.06]">
            <span className="text-[10px] text-slate-500 uppercase font-bold tracking-wider">All Agents</span>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-px bg-white/5">
            {agents.map(agent => {
              const agentPending = pendingWork.by_agent?.[agent.agent_id] || 0;
              return (
                <button
                  key={agent.agent_id}
                  onClick={() => handleSelectAgent(agent.agent_id)}
                  className="relative p-3 bg-[#05070a] hover:bg-white/[0.02] transition-colors text-left"
                >
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-lg">{agent.icon}</span>
                    <span className="text-xs font-bold text-white">{agent.name}</span>
                    {agentPending > 0 && (
                      <span className="ml-auto text-[9px] px-1.5 py-0.5 rounded bg-blue-500/20 text-blue-400 font-bold">
                        {agentPending}
                      </span>
                    )}
                  </div>
                  <p className="text-[10px] text-slate-500 line-clamp-2">{agent.role}</p>
                </button>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
};

export default AgenticResearch;
