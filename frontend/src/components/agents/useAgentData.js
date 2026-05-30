import { useState, useEffect, useCallback } from 'react';

const POLL_INTERVAL = 30000;

export function useAgentData() {
  const [agents, setAgents] = useState([]);
  const [workflowSummary, setWorkflowSummary] = useState(null);
  const [workflows, setWorkflows] = useState([]);
  const [pendingWork, setPendingWork] = useState({ work_items: [], by_agent: {} });
  const [completedWork, setCompletedWork] = useState({ completed_items: [], count: 0 });
  const [events, setEvents] = useState([]);
  const [goldStatus, setGoldStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchAll = useCallback(async () => {
    try {
      const [
        agentsRes,
        summaryRes,
        workflowsRes,
        pendingRes,
        completedRes,
        eventsRes,
        goldRes,
      ] = await Promise.all([
        fetch('/api/agents').then(r => r.json()),
        fetch('/api/agents/workflow-summary').then(r => r.json()),
        fetch('/api/agents/strategy-workflows?limit=50').then(r => r.json()),
        fetch('/api/agents/pending-work').then(r => r.json()),
        fetch('/api/agents/completed-work?limit=100').then(r => r.json()),
        fetch('/api/agents/events?limit=100').then(r => r.json()),
        fetch('/api/agents/gold-layer-status').then(r => r.json()),
      ]);

      if (agentsRes.agents) setAgents(agentsRes.agents);
      if (summaryRes.total !== undefined) setWorkflowSummary(summaryRes);
      if (workflowsRes.strategies) setWorkflows(workflowsRes.strategies);
      setPendingWork(pendingRes || { work_items: [], by_agent: {} });
      setCompletedWork(completedRes || { completed_items: [], count: 0 });
      if (eventsRes.events) setEvents(eventsRes.events);
      setGoldStatus(goldRes);
      setError(null);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchAll();
    const id = setInterval(fetchAll, POLL_INTERVAL);
    return () => clearInterval(id);
  }, [fetchAll]);

  return {
    agents,
    workflowSummary,
    workflows,
    pendingWork,
    completedWork,
    events,
    goldStatus,
    loading,
    error,
    refetch: fetchAll,
  };
}

export function useStrategyDetail(strategyId) {
  const [detail, setDetail] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!strategyId) return;
    setLoading(true);
    fetch(`/api/agents/strategy/${encodeURIComponent(strategyId)}`)
      .then(r => r.json())
      .then(data => { setDetail(data); })
      .catch(() => setDetail(null))
      .finally(() => setLoading(false));
  }, [strategyId]);

  return { detail, loading };
}
