import React, { useState, useEffect } from 'react';

const EVENT_TYPE_COLORS = {
  'strategy.created': 'bg-emerald-500/20 text-emerald-400',
  'experiment.started': 'bg-blue-500/20 text-blue-400',
  'dataset.ready': 'bg-cyan-500/20 text-cyan-400',
  'backtest.completed': 'bg-violet-500/20 text-violet-400',
  'risk.evaluated': 'bg-amber-500/20 text-amber-400',
  'debate.completed': 'bg-rose-500/20 text-rose-400',
  'qa.validated': 'bg-emerald-500/20 text-emerald-400',
  'strategy.promoted': 'bg-amber-500/20 text-amber-400',
};

const STATUS_COLORS = {
  pending: 'bg-slate-600/20 text-slate-400',
  assigned_algo: 'bg-blue-500/20 text-blue-400',
  claimed_algo: 'bg-blue-500/30 text-blue-300',
  in_progress_algo: 'bg-blue-500/30 text-blue-300',
  algo_complete: 'bg-violet-500/20 text-violet-400',
  assigned_qa: 'bg-amber-500/20 text-amber-400',
  claimed_qa: 'bg-amber-500/30 text-amber-300',
  qa_approved: 'bg-emerald-500/20 text-emerald-400',
  qa_rejected: 'bg-rose-500/20 text-rose-400',
  golden: 'bg-amber-500/30 text-amber-300',
  rejected: 'bg-rose-500/30 text-rose-400',
};

function formatTimeAgo(timestamp) {
  if (!timestamp) return '';
  const diff = Date.now() - new Date(timestamp).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return 'just now';
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  const days = Math.floor(hrs / 24);
  return `${days}d ago`;
}

// Pipeline Flow — agents in order, with pending work badge
const PipelineFlow = ({ agents, pendingByAgent, selectedAgent, onSelectAgent }) => (
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
              onClick={() => onSelectAgent(isSelected ? null : agent.agent_id)}
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

// Event Feed Item
const EventItem = ({ event }) => {
  const typeClass = EVENT_TYPE_COLORS[event.event_type] || 'bg-slate-600/20 text-slate-300';
  return (
    <div className="flex gap-3 p-3 hover:bg-white/[0.02] transition-colors">
      <div className="flex-shrink-0 w-8 h-8 rounded-lg bg-slate-800/80 flex items-center justify-center text-sm">
        {event.agent_icon}
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 mb-1 flex-wrap">
          <span className="text-xs font-bold text-white">{event.agent_name}</span>
          <span className={`text-[9px] px-1.5 py-0.5 rounded font-bold uppercase tracking-wider ${typeClass}`}>
            {event.event_type}
          </span>
          {event.strategy_id && (
            <span className="text-[9px] px-1.5 py-0.5 rounded bg-amber-500/10 text-amber-400 font-mono">
              {event.strategy_id}
            </span>
          )}
          {event.domain && (
            <span className="text-[9px] px-1.5 py-0.5 rounded bg-slate-700/50 text-slate-400">
              {event.domain}
            </span>
          )}
          <span className="text-[10px] text-slate-600 ml-auto flex-shrink-0">{formatTimeAgo(event.timestamp)}</span>
        </div>
        {event.processed_by && (
          <p className="text-[10px] text-slate-500">Processed by: <span className="text-slate-400">{event.processed_by}</span></p>
        )}
        {event.payload && Object.keys(event.payload).length > 0 && (
          <div className="mt-1.5 flex flex-wrap gap-1">
            {Object.entries(event.payload).slice(0, 6).map(([k, v]) => (
              <span key={k} className="text-[9px] px-1.5 py-0.5 rounded bg-slate-800/80 text-slate-500">
                {k}: <span className="text-slate-300 font-mono">{typeof v === 'number' ? v.toFixed(2) : typeof v === 'object' ? JSON.stringify(v).slice(0, 30) : String(v).slice(0, 30)}</span>
              </span>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

// Strategy Workflow Card
const WorkflowCard = ({ strategy, onSelect }) => {
  const statusClass = STATUS_COLORS[strategy.status] || STATUS_COLORS.pending;
  return (
    <button
      onClick={() => onSelect(strategy.strategy_id)}
      className="p-4 text-left hover:bg-white/[0.02] transition-colors w-full"
    >
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          <span className="text-xs font-bold text-white">{strategy.name || strategy.strategy_id}</span>
          <span className={`text-[9px] px-1.5 py-0.5 rounded font-bold uppercase tracking-wider ${statusClass}`}>
            {strategy.status}
          </span>
        </div>
        <span className="text-[10px] text-slate-600">{formatTimeAgo(strategy.updated_at)}</span>
      </div>
      <div className="flex items-center gap-3 text-[10px] text-slate-500">
        {strategy.assigned_to && (
          <span>Assigned: <span className="text-slate-400">{strategy.assigned_to}</span></span>
        )}
        <span>{strategy.event_count} events</span>
        {strategy.result && (
          <span className={strategy.result === 'golden' ? 'text-amber-400' : strategy.result === 'rejected' ? 'text-rose-400' : 'text-slate-400'}>
            Result: {strategy.result}
          </span>
        )}
      </div>
      {strategy.event_history && strategy.event_history.length > 0 && (
        <div className="mt-2 flex flex-wrap gap-1">
          {strategy.event_history.map((evt, i) => {
            const ec = EVENT_TYPE_COLORS[evt] || 'bg-slate-700/50 text-slate-400';
            return (
              <span key={i} className={`text-[8px] px-1 py-0.5 rounded ${ec}`}>
                {evt.replace('.', '\u00B7')}
              </span>
            );
          })}
        </div>
      )}
    </button>
  );
};

// Strategy Detail Modal
const StrategyDetail = ({ strategyId, onClose }) => {
  const [detail, setDetail] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`/api/agents/strategy/${encodeURIComponent(strategyId)}`)
      .then(r => r.json())
      .then(data => { setDetail(data); setLoading(false); })
      .catch(() => setLoading(false));
  }, [strategyId]);

  if (loading) return (
    <div className="p-6 text-center text-slate-500">
      <div className="w-6 h-6 border-2 border-slate-600 border-t-blue-500 rounded-full animate-spin mx-auto mb-2" />
      Loading...
    </div>
  );

  if (!detail || !detail.workflow) return (
    <div className="p-6 text-center text-slate-500">Strategy not found</div>
  );

  const wf = detail.workflow;
  const statusClass = STATUS_COLORS[wf.status] || STATUS_COLORS.pending;

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-sm font-bold text-white">{wf.name || wf.strategy_id}</h3>
          <p className="text-[10px] text-slate-500 font-mono">{wf.strategy_id}</p>
        </div>
        <div className="flex items-center gap-2">
          <span className={`text-[10px] px-2 py-1 rounded font-bold uppercase ${statusClass}`}>{wf.status}</span>
          <button onClick={onClose} className="text-slate-500 hover:text-white text-sm px-2">✕</button>
        </div>
      </div>

      {wf.description && <p className="text-xs text-slate-400">{wf.description}</p>}

      {/* Progress */}
      {wf.progress_percent > 0 && (
        <div>
          <div className="flex items-center justify-between mb-1">
            <span className="text-[10px] text-slate-500">Progress</span>
            <span className="text-[10px] text-white font-mono">{wf.progress_percent}%</span>
          </div>
          <div className="w-full h-1.5 bg-slate-700 rounded-full overflow-hidden">
            <div className="h-full bg-blue-500 rounded-full transition-all" style={{ width: `${wf.progress_percent}%` }} />
          </div>
          {wf.progress_note && <p className="text-[10px] text-slate-500 mt-1">{wf.progress_note}</p>}
        </div>
      )}

      {/* Risk & Debate */}
      <div className="grid grid-cols-2 gap-3">
        {wf.risk_score != null && (
          <div className="bg-slate-800/50 rounded-lg p-3">
            <div className="text-[9px] text-slate-500 uppercase">Risk Score</div>
            <div className={`text-lg font-bold font-mono ${wf.risk_score > 0.7 ? 'text-rose-400' : wf.risk_score > 0.4 ? 'text-amber-400' : 'text-emerald-400'}`}>
              {wf.risk_score.toFixed(2)}
            </div>
            {wf.risk_flags && <p className="text-[9px] text-slate-500 mt-1">{wf.risk_flags}</p>}
          </div>
        )}
        {wf.conviction_score != null && (
          <div className="bg-slate-800/50 rounded-lg p-3">
            <div className="text-[9px] text-slate-500 uppercase">Conviction</div>
            <div className="text-lg font-bold font-mono text-blue-400">{wf.conviction_score.toFixed(2)}</div>
          </div>
        )}
      </div>

      {wf.debate_summary && (
        <div className="bg-slate-800/50 rounded-lg p-3">
          <div className="text-[9px] text-slate-500 uppercase mb-1">Debate Summary</div>
          <p className="text-xs text-slate-300">{wf.debate_summary}</p>
        </div>
      )}

      {/* Event Timeline */}
      {detail.events && detail.events.length > 0 && (
        <div>
          <div className="text-[10px] text-slate-500 uppercase font-bold mb-2">Event Timeline ({detail.events.length})</div>
          <div className="space-y-1 max-h-[300px] overflow-y-auto">
            {detail.events.map(e => (
              <div key={e.id} className="flex items-center gap-2 py-1.5 px-2 rounded bg-slate-800/30">
                <span className="text-sm">{e.agent_icon}</span>
                <span className="text-[10px] font-bold text-slate-300">{e.agent_name}</span>
                <span className={`text-[8px] px-1 py-0.5 rounded font-bold ${EVENT_TYPE_COLORS[e.event_type] || 'bg-slate-700/50 text-slate-400'}`}>
                  {e.event_type}
                </span>
                <span className="text-[9px] text-slate-600 ml-auto">{formatTimeAgo(e.timestamp)}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Lineage / Backtests */}
      {detail.lineage && detail.lineage.length > 0 && (
        <div>
          <div className="text-[10px] text-slate-500 uppercase font-bold mb-2">Experiment Lineage ({detail.lineage.length})</div>
          <div className="space-y-2">
            {detail.lineage.map((l, i) => (
              <div key={i} className="bg-slate-800/50 rounded-lg p-3 text-xs">
                <div className="flex items-center justify-between mb-1">
                  <span className="text-white font-mono font-bold">{l.experiment_id || `Exp #${i + 1}`}</span>
                  <span className="text-[10px] text-slate-600">{formatTimeAgo(l.created_at)}</span>
                </div>
                <div className="flex gap-3 text-[10px] text-slate-400">
                  {l.sharpe_oos != null && <span>Sharpe OOS: <span className="text-white font-mono">{l.sharpe_oos.toFixed(2)}</span></span>}
                  {l.max_drawdown != null && <span>Max DD: <span className="text-rose-400 font-mono">{l.max_drawdown.toFixed(1)}%</span></span>}
                  {l.trade_count_oos != null && <span>Trades: <span className="text-white font-mono">{l.trade_count_oos}</span></span>}
                </div>
                <div className="text-[9px] text-slate-600 mt-1">
                  Dataset: {l.dataset_version} | Engine: {l.engine_version}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

// Pending Work View — grouped by agent
const PendingWorkView = ({ workItems, agents }) => {
  if (!workItems || workItems.length === 0) {
    return (
      <div className="text-center p-8 text-slate-500">
        <div className="text-3xl mb-3">✅</div>
        <p className="text-sm font-medium text-slate-400">No pending work</p>
        <p className="text-[11px] text-slate-600 mt-1">All events have been processed by their target agents</p>
      </div>
    );
  }

  // Group by target agent
  const grouped = {};
  workItems.forEach(w => {
    if (!grouped[w.target_agent]) grouped[w.target_agent] = [];
    grouped[w.target_agent].push(w);
  });

  return (
    <div className="divide-y divide-white/5">
      {Object.entries(grouped).map(([agentId, items]) => (
        <div key={agentId} className="p-4">
          <div className="flex items-center gap-2 mb-3">
            <span className="text-lg">{items[0].target_agent_icon}</span>
            <span className="text-xs font-bold text-white">{items[0].target_agent_name}</span>
            <span className="text-[9px] px-1.5 py-0.5 rounded bg-blue-500/20 text-blue-400 font-bold">{items.length} pending</span>
          </div>
          <div className="space-y-1">
            {items.map(w => (
              <div key={w.event_id} className="flex items-center gap-2 py-1.5 px-2 rounded bg-slate-800/30">
                <span className={`text-[9px] px-1.5 py-0.5 rounded font-bold ${EVENT_TYPE_COLORS[w.event_type] || 'bg-slate-700/50 text-slate-400'}`}>
                  {w.event_type}
                </span>
                {w.strategy_id && <span className="text-[9px] text-amber-400 font-mono">{w.strategy_id}</span>}
                <span className="text-[9px] text-slate-600">from {w.emitter_icon} {w.emitter_name}</span>
                <span className="text-[9px] text-slate-600 ml-auto">{formatTimeAgo(w.created_at)}</span>
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
};

export const AgenticResearch = () => {
  const [agents, setAgents] = useState([]);
  const [events, setEvents] = useState([]);
  const [workflows, setWorkflows] = useState([]);
  const [pendingWork, setPendingWork] = useState({ work_items: [], by_agent: {} });
  const [workflowSummary, setWorkflowSummary] = useState(null);
  const [selectedAgent, setSelectedAgent] = useState(null);
  const [selectedStrategy, setSelectedStrategy] = useState(null);
  const [activeView, setActiveView] = useState('events'); // 'events', 'workflows', 'pending'
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchAll();
    const interval = setInterval(fetchAll, 30000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    fetchEvents();
  }, [selectedAgent]);

  const fetchAll = () => {
    fetchAgents();
    fetchEvents();
    fetchWorkflows();
    fetchPendingWork();
    fetchWorkflowSummary();
  };

  const fetchAgents = () => {
    fetch('/api/agents')
      .then(r => r.json())
      .then(data => { if (data.agents) setAgents(data.agents); })
      .catch(e => console.error('Failed to fetch agents:', e));
  };

  const fetchEvents = () => {
    const params = new URLSearchParams({ limit: '100' });
    if (selectedAgent) params.set('agent_id', selectedAgent);
    fetch(`/api/agents/events?${params}`)
      .then(r => r.json())
      .then(data => { if (data.events) setEvents(data.events); setLoading(false); })
      .catch(() => setLoading(false));
  };

  const fetchWorkflows = () => {
    fetch('/api/agents/strategy-workflows?limit=50')
      .then(r => r.json())
      .then(data => { if (data.strategies) setWorkflows(data.strategies); })
      .catch(e => console.error('Failed to fetch workflows:', e));
  };

  const fetchPendingWork = () => {
    fetch('/api/agents/pending-work')
      .then(r => r.json())
      .then(data => setPendingWork(data))
      .catch(e => console.error('Failed to fetch pending work:', e));
  };

  const fetchWorkflowSummary = () => {
    fetch('/api/agents/workflow-summary')
      .then(r => r.json())
      .then(data => setWorkflowSummary(data))
      .catch(e => console.error('Failed to fetch summary:', e));
  };

  if (loading) {
    return (
      <div className="p-12 text-center text-slate-500">
        <div className="w-8 h-8 border-2 border-slate-600 border-t-blue-500 rounded-full animate-spin mx-auto mb-4" />
        Loading OpenClaw research pipeline...
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-bold text-white">Agentic Research</h2>
          <p className="text-xs text-slate-500 mt-0.5">{agents.length} OpenClaw agents &middot; {workflows.length} strategies in pipeline</p>
        </div>
        <div className="flex items-center gap-1 p-1 rounded-lg bg-slate-900/50 border border-white/[0.06]">
          {[
            { id: 'events', label: 'Events' },
            { id: 'workflows', label: 'Workflows' },
            { id: 'pending', label: `Pending (${pendingWork.count || 0})` },
          ].map(tab => (
            <button
              key={tab.id}
              onClick={() => { setActiveView(tab.id); setSelectedStrategy(null); }}
              className={`px-3 py-1.5 rounded-md text-[10px] font-bold transition-colors ${
                activeView === tab.id ? 'bg-blue-500 text-white shadow-sm' : 'text-slate-400 hover:text-white'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      {/* Workflow Summary KPIs */}
      {workflowSummary && (
        <div className="grid grid-cols-2 md:grid-cols-5 gap-2">
          {[
            { label: 'Total', value: workflowSummary.total, color: 'text-white' },
            { label: 'Pending', value: workflowSummary.pending_queue, color: 'text-slate-400' },
            { label: 'Golden', value: workflowSummary.golden, color: 'text-amber-400' },
            { label: 'Rejected', value: workflowSummary.rejected, color: 'text-rose-400' },
            { label: 'Pending Events', value: pendingWork.count || 0, color: 'text-blue-400' },
          ].map(kpi => (
            <div key={kpi.label} className="px-3 py-2.5 bg-slate-900/60 rounded-xl border border-white/[0.06]">
              <div className="text-[9px] text-slate-500 uppercase tracking-wider">{kpi.label}</div>
              <div className={`text-lg font-bold font-mono ${kpi.color}`}>{kpi.value ?? 0}</div>
            </div>
          ))}
        </div>
      )}

      {/* Agent Pipeline Flow */}
      <div className="bg-slate-900/40 rounded-xl border border-white/[0.06] overflow-hidden">
        <div className="px-4 py-2.5 border-b border-white/[0.06] flex items-center gap-2">
          <span className="text-[10px] text-slate-500 uppercase font-bold tracking-wider">Agent Pipeline</span>
          {selectedAgent && (
            <button onClick={() => setSelectedAgent(null)} className="text-[10px] text-blue-400 hover:text-blue-300">
              Clear filter
            </button>
          )}
        </div>
        <PipelineFlow
          agents={agents}
          pendingByAgent={pendingWork.by_agent || {}}
          selectedAgent={selectedAgent}
          onSelectAgent={setSelectedAgent}
        />
      </div>

      {/* Agent Info Card */}
      {selectedAgent && (() => {
        const agent = agents.find(a => a.agent_id === selectedAgent);
        if (!agent) return null;
        const agentPending = pendingWork.by_agent?.[selectedAgent] || 0;
        return (
          <div className="flex items-center gap-3 p-3 bg-blue-500/5 rounded-xl border border-blue-500/20">
            <span className="text-2xl">{agent.icon}</span>
            <div className="flex-1">
              <div className="text-sm font-bold text-white">{agent.name} <span className="text-[10px] text-slate-500 font-normal font-mono">({agent.agent_id})</span></div>
              <p className="text-[11px] text-slate-400">{agent.role}</p>
            </div>
            {agentPending > 0 && (
              <span className="px-2 py-1 rounded-lg bg-blue-500/20 text-blue-400 text-xs font-bold">
                {agentPending} pending
              </span>
            )}
          </div>
        );
      })()}

      {/* Strategy Detail Overlay */}
      {selectedStrategy && (
        <div className="bg-slate-900/60 rounded-xl border border-blue-500/20 p-4">
          <StrategyDetail strategyId={selectedStrategy} onClose={() => setSelectedStrategy(null)} />
        </div>
      )}

      {/* Main Content */}
      <div className="bg-slate-900/40 rounded-xl border border-white/[0.06] overflow-hidden">
        {activeView === 'events' && (
          <>
            <div className="px-4 py-2.5 border-b border-white/[0.06] flex items-center justify-between">
              <span className="text-[10px] text-slate-500 uppercase font-bold tracking-wider">
                {selectedAgent ? `${agents.find(a => a.agent_id === selectedAgent)?.name} Events` : 'All Events'}
              </span>
              <span className="text-[10px] text-slate-600">{events.length} events</span>
            </div>
            {events.length > 0 ? (
              <div className="divide-y divide-white/5 max-h-[600px] overflow-y-auto">
                {events.map(e => <EventItem key={e.id} event={e} />)}
              </div>
            ) : (
              <div className="text-center p-12 text-slate-500">
                <div className="text-3xl mb-3">📡</div>
                <p className="text-sm font-medium text-slate-400">No events yet</p>
                <p className="text-[11px] text-slate-600 mt-1">
                  Events are emitted by OpenClaw agents as they process strategies through the pipeline.
                </p>
              </div>
            )}
          </>
        )}

        {activeView === 'workflows' && (
          <>
            <div className="px-4 py-2.5 border-b border-white/[0.06] flex items-center justify-between">
              <span className="text-[10px] text-slate-500 uppercase font-bold tracking-wider">Strategy Workflows</span>
              <span className="text-[10px] text-slate-600">{workflows.length} strategies</span>
            </div>
            {workflows.length > 0 ? (
              <div className="divide-y divide-white/5 max-h-[600px] overflow-y-auto">
                {workflows.map(w => (
                  <WorkflowCard key={w.strategy_id} strategy={w} onSelect={setSelectedStrategy} />
                ))}
              </div>
            ) : (
              <div className="text-center p-12 text-slate-500">
                <div className="text-3xl mb-3">🔗</div>
                <p className="text-sm font-medium text-slate-400">No workflows yet</p>
                <p className="text-[11px] text-slate-600 mt-1">Strategy workflows will appear here as the pipeline processes ideas.</p>
              </div>
            )}
          </>
        )}

        {activeView === 'pending' && (
          <>
            <div className="px-4 py-2.5 border-b border-white/[0.06] flex items-center justify-between">
              <span className="text-[10px] text-slate-500 uppercase font-bold tracking-wider">Pending Work by Agent</span>
              <span className="text-[10px] text-slate-600">{pendingWork.count || 0} items</span>
            </div>
            <PendingWorkView workItems={pendingWork.work_items} agents={agents} />
          </>
        )}
      </div>

      {/* Agent Grid */}
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
                  onClick={() => setSelectedAgent(agent.agent_id)}
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
