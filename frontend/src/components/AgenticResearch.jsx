import React, { useState, useEffect } from 'react';

// Agent pipeline flow order
const PIPELINE_STAGES = [
  { id: 'qr_idea_intake', stage: 'Intake' },
  { id: 'qr_hub', stage: 'Orchestration' },
  { id: 'qr_researcher', stage: 'Research' },
  { id: 'qr_macro_sentinel', stage: 'Macro Analysis' },
  { id: 'qr_data_validator', stage: 'Data Validation' },
  { id: 'qr_etl_manager', stage: 'Data Pipeline' },
  { id: 'qr_algo', stage: 'Algorithm Design' },
  { id: 'qr_exp_manager', stage: 'Backtesting' },
  { id: 'qr_risk', stage: 'Risk Assessment' },
  { id: 'qr_qa', stage: 'Quality Assurance' },
  { id: 'qr_debate', stage: 'Debate' },
  { id: 'qr_architect', stage: 'Architecture' },
  { id: 'qr_monitor', stage: 'Monitoring' },
  { id: 'qr_frontend', stage: 'Reporting' },
];

const ACTION_COLORS = {
  REVIEW: 'bg-blue-500/20 text-blue-400',
  APPROVE: 'bg-emerald-500/20 text-emerald-400',
  REJECT: 'bg-rose-500/20 text-rose-400',
  COMMENT: 'bg-slate-600/20 text-slate-300',
  SIGNAL: 'bg-amber-500/20 text-amber-400',
  VALIDATE: 'bg-violet-500/20 text-violet-400',
  BACKTEST: 'bg-cyan-500/20 text-cyan-400',
  ALERT: 'bg-rose-500/20 text-rose-400',
  RESEARCH: 'bg-indigo-500/20 text-indigo-400',
};

// Pipeline Flow Visualization
const PipelineFlow = ({ agents, selectedAgent, onSelectAgent }) => {
  return (
    <div className="overflow-x-auto no-scrollbar">
      <div className="flex items-center gap-1 min-w-max p-3">
        {PIPELINE_STAGES.map((stage, i) => {
          const agent = agents.find(a => a.agent_id === stage.id);
          const isSelected = selectedAgent === stage.id;
          return (
            <React.Fragment key={stage.id}>
              {i > 0 && (
                <div className="flex-shrink-0 w-6 flex items-center justify-center">
                  <svg className="w-4 h-3 text-slate-700" viewBox="0 0 16 12" fill="none">
                    <path d="M1 6h14M11 1l4 5-4 5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
                  </svg>
                </div>
              )}
              <button
                onClick={() => onSelectAgent(isSelected ? null : stage.id)}
                className={`flex-shrink-0 flex flex-col items-center gap-1 px-3 py-2 rounded-xl transition-all ${
                  isSelected
                    ? 'bg-blue-500/20 border border-blue-500/40 ring-1 ring-blue-500/20'
                    : 'bg-slate-900/50 border border-white/5 hover:border-white/10'
                }`}
              >
                <span className="text-lg">{agent?.icon || '🤖'}</span>
                <span className="text-[9px] text-slate-400 uppercase tracking-wider font-medium whitespace-nowrap">{agent?.name || stage.stage}</span>
              </button>
            </React.Fragment>
          );
        })}
      </div>
    </div>
  );
};

// Activity Feed Item
const ActivityItem = ({ activity }) => {
  const actionClass = ACTION_COLORS[activity.action] || ACTION_COLORS.COMMENT;
  const timeAgo = activity.timestamp ? formatTimeAgo(activity.timestamp) : '';

  return (
    <div className="flex gap-3 p-3 hover:bg-white/[0.02] transition-colors">
      <div className="flex-shrink-0 w-8 h-8 rounded-lg bg-slate-800/80 flex items-center justify-center text-sm">
        {activity.agent_icon}
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 mb-1">
          <span className="text-xs font-bold text-white">{activity.agent_name}</span>
          <span className={`text-[9px] px-1.5 py-0.5 rounded font-bold uppercase tracking-wider ${actionClass}`}>
            {activity.action}
          </span>
          {activity.strategy_id && (
            <span className="text-[9px] px-1.5 py-0.5 rounded bg-amber-500/10 text-amber-400 font-mono">
              {activity.strategy_id}
            </span>
          )}
          <span className="text-[10px] text-slate-600 ml-auto flex-shrink-0">{timeAgo}</span>
        </div>
        <p className="text-xs text-slate-400 leading-relaxed">{activity.message}</p>
        {activity.metadata && (
          <div className="mt-1.5 flex flex-wrap gap-1">
            {Object.entries(activity.metadata).slice(0, 5).map(([k, v]) => (
              <span key={k} className="text-[9px] px-1.5 py-0.5 rounded bg-slate-800/80 text-slate-500">
                {k}: <span className="text-slate-300 font-mono">{typeof v === 'number' ? v.toFixed(2) : String(v)}</span>
              </span>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

// Strategy Assignments View
const StrategyAssignments = ({ assignments, agents }) => {
  if (!assignments || Object.keys(assignments).length === 0) {
    return (
      <div className="text-center p-8 text-slate-500">
        <div className="text-3xl mb-3">🔗</div>
        <p className="text-sm font-medium text-slate-400">No active assignments</p>
        <p className="text-[11px] text-slate-600 mt-1">Agent-strategy assignments will appear here as the pipeline runs</p>
      </div>
    );
  }

  return (
    <div className="divide-y divide-white/5">
      {Object.entries(assignments).map(([strategyId, agentList]) => (
        <div key={strategyId} className="p-4">
          <div className="flex items-center gap-2 mb-3">
            <span className="text-xs font-bold text-white font-mono">{strategyId}</span>
            <span className="text-[10px] text-slate-500">{agentList.length} agent{agentList.length !== 1 ? 's' : ''} active</span>
          </div>
          <div className="flex flex-wrap gap-2">
            {agentList.map(agent => (
              <div key={agent.agent_id} className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg bg-slate-800/50 border border-white/5">
                <span className="text-sm">{agent.agent_icon}</span>
                <span className="text-[10px] font-bold text-slate-300">{agent.agent_name}</span>
                <span className={`text-[8px] px-1 py-0.5 rounded font-bold uppercase ${ACTION_COLORS[agent.action] || ACTION_COLORS.COMMENT}`}>
                  {agent.action}
                </span>
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
};

function formatTimeAgo(timestamp) {
  const diff = Date.now() - new Date(timestamp).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return 'just now';
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  const days = Math.floor(hrs / 24);
  return `${days}d ago`;
}

export const AgenticResearch = () => {
  const [agents, setAgents] = useState([]);
  const [activities, setActivities] = useState([]);
  const [assignments, setAssignments] = useState({});
  const [selectedAgent, setSelectedAgent] = useState(null);
  const [activeView, setActiveView] = useState('feed'); // 'feed' or 'assignments'
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchAgents();
    fetchActivities();
    fetchAssignments();

    const interval = setInterval(() => {
      fetchActivities();
      fetchAssignments();
    }, 30000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    fetchActivities();
  }, [selectedAgent]);

  const fetchAgents = () => {
    fetch('/api/agents')
      .then(r => r.json())
      .then(data => {
        if (data.agents) setAgents(data.agents);
      })
      .catch(e => console.error('Failed to fetch agents:', e));
  };

  const fetchActivities = () => {
    const params = new URLSearchParams({ limit: '100' });
    if (selectedAgent) params.set('agent_id', selectedAgent);

    fetch(`/api/agents/activity?${params}`)
      .then(r => r.json())
      .then(data => {
        if (data.activities) setActivities(data.activities);
        setLoading(false);
      })
      .catch(e => {
        console.error('Failed to fetch activities:', e);
        setLoading(false);
      });
  };

  const fetchAssignments = () => {
    fetch('/api/agents/strategy-assignments')
      .then(r => r.json())
      .then(data => {
        if (data.assignments) setAssignments(data.assignments);
      })
      .catch(e => console.error('Failed to fetch assignments:', e));
  };

  if (loading) {
    return (
      <div className="p-12 text-center text-slate-500">
        <div className="w-8 h-8 border-2 border-slate-600 border-t-blue-500 rounded-full animate-spin mx-auto mb-4" />
        Loading agent research pipeline...
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-bold text-white flex items-center gap-2">
            Agentic Research
          </h2>
          <p className="text-xs text-slate-500 mt-0.5">{agents.length} OpenClaw agents in the research pipeline</p>
        </div>
        <div className="flex items-center gap-1 p-1 rounded-lg bg-slate-900/50 border border-white/[0.06]">
          <button
            onClick={() => setActiveView('feed')}
            className={`px-3 py-1.5 rounded-md text-[10px] font-bold transition-colors ${
              activeView === 'feed' ? 'bg-blue-500 text-white shadow-sm' : 'text-slate-400 hover:text-white'
            }`}
          >
            Activity Feed
          </button>
          <button
            onClick={() => setActiveView('assignments')}
            className={`px-3 py-1.5 rounded-md text-[10px] font-bold transition-colors ${
              activeView === 'assignments' ? 'bg-blue-500 text-white shadow-sm' : 'text-slate-400 hover:text-white'
            }`}
          >
            Strategy Assignments
          </button>
        </div>
      </div>

      {/* Agent Pipeline Flow */}
      <div className="bg-slate-900/40 rounded-xl border border-white/[0.06] overflow-hidden">
        <div className="px-4 py-2.5 border-b border-white/[0.06]">
          <span className="text-[10px] text-slate-500 uppercase font-bold tracking-wider">Agent Pipeline</span>
          {selectedAgent && (
            <button
              onClick={() => setSelectedAgent(null)}
              className="ml-2 text-[10px] text-blue-400 hover:text-blue-300"
            >
              Clear filter
            </button>
          )}
        </div>
        <PipelineFlow agents={agents} selectedAgent={selectedAgent} onSelectAgent={setSelectedAgent} />
      </div>

      {/* Agent Info Card (when selected) */}
      {selectedAgent && (() => {
        const agent = agents.find(a => a.agent_id === selectedAgent);
        if (!agent) return null;
        return (
          <div className="flex items-center gap-3 p-3 bg-blue-500/5 rounded-xl border border-blue-500/20">
            <span className="text-2xl">{agent.icon}</span>
            <div>
              <div className="text-sm font-bold text-white">{agent.name} <span className="text-[10px] text-slate-500 font-normal font-mono">({agent.agent_id})</span></div>
              <p className="text-[11px] text-slate-400">{agent.role}</p>
            </div>
          </div>
        );
      })()}

      {/* Main Content */}
      <div className="bg-slate-900/40 rounded-xl border border-white/[0.06] overflow-hidden">
        {activeView === 'feed' ? (
          <>
            <div className="px-4 py-2.5 border-b border-white/[0.06] flex items-center justify-between">
              <span className="text-[10px] text-slate-500 uppercase font-bold tracking-wider">
                {selectedAgent ? `${agents.find(a => a.agent_id === selectedAgent)?.name || selectedAgent} Activity` : 'All Activity'}
              </span>
              <span className="text-[10px] text-slate-600">{activities.length} events</span>
            </div>
            {activities.length > 0 ? (
              <div className="divide-y divide-white/5 max-h-[600px] overflow-y-auto">
                {activities.map(a => (
                  <ActivityItem key={a.id} activity={a} />
                ))}
              </div>
            ) : (
              <div className="text-center p-12 text-slate-500">
                <div className="text-3xl mb-3">📡</div>
                <p className="text-sm font-medium text-slate-400">No activity yet</p>
                <p className="text-[11px] text-slate-600 mt-1">
                  Agent activity will appear here as the OpenClaw pipeline processes strategies.
                  <br />
                  Agents log their actions via <span className="font-mono text-slate-500">POST /api/agents/activity</span>
                </p>
              </div>
            )}
          </>
        ) : (
          <>
            <div className="px-4 py-2.5 border-b border-white/[0.06]">
              <span className="text-[10px] text-slate-500 uppercase font-bold tracking-wider">Strategy &harr; Agent Assignments</span>
            </div>
            <StrategyAssignments assignments={assignments} agents={agents} />
          </>
        )}
      </div>

      {/* Agent Grid (all agents overview) */}
      {!selectedAgent && (
        <div className="bg-slate-900/40 rounded-xl border border-white/[0.06] overflow-hidden">
          <div className="px-4 py-2.5 border-b border-white/[0.06]">
            <span className="text-[10px] text-slate-500 uppercase font-bold tracking-wider">All Agents</span>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-px bg-white/5">
            {agents.map(agent => (
              <button
                key={agent.agent_id}
                onClick={() => setSelectedAgent(agent.agent_id)}
                className="p-3 bg-[#05070a] hover:bg-white/[0.02] transition-colors text-left"
              >
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-lg">{agent.icon}</span>
                  <span className="text-xs font-bold text-white">{agent.name}</span>
                </div>
                <p className="text-[10px] text-slate-500 line-clamp-2">{agent.role}</p>
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default AgenticResearch;
