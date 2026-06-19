import { useState, useEffect, useCallback, useRef } from 'react';

const API_BASE = import.meta.env.VITE_API_URL || '';

// Exponential backoff for 503 responses: 30s -> 60s -> 120s (cap)
function nextBackoff(attempt) {
  const base = 30000; // 30s
  const max = 120000; // 120s
  return Math.min(base * Math.pow(2, attempt), max);
}

function usePoll(endpoint, intervalMs = 60000) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [degraded, setDegraded] = useState(false);
  const backoffAttemptRef = useRef(0);
  const timeoutRef = useRef(null);

  const fetchData = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}${endpoint}`);
      if (res.status === 503) {
        // DB unavailable — enter degraded mode with backoff
        const retryAfter = nextBackoff(backoffAttemptRef.current);
        backoffAttemptRef.current += 1;
        setDegraded(true);
        setError({ code: 503, retryAfter });
        setLoading(false);
        // Schedule next retry with backoff
        if (timeoutRef.current) clearTimeout(timeoutRef.current);
        timeoutRef.current = setTimeout(fetchData, retryAfter);
        return;
      }
      if (!res.ok) throw new Error(`${res.status}`);
      const json = await res.json();
      setData(json);
      setError(null);
      setDegraded(false);
      backoffAttemptRef.current = 0; // reset on success
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }, [endpoint]);

  useEffect(() => {
    fetchData();
    const id = setInterval(() => {
      // Only poll on interval if not in degraded backoff mode
      if (backoffAttemptRef.current === 0) {
        fetchData();
      }
    }, intervalMs);
    return () => {
      clearInterval(id);
      if (timeoutRef.current) clearTimeout(timeoutRef.current);
    };
  }, [fetchData, intervalMs]);

  return { data, loading, error, degraded, refetch: fetchData };
}

export function usePaperSystemStatus() {
  return usePoll('/api/agents/paper/system-status', 60000);
}

export function usePaperOpenPositions() {
  return usePoll('/api/agents/paper/open-positions', 60000);
}

export function usePaperDailyRuns() {
  return usePoll('/api/agents/paper/daily-runs', 60000);
}

export function usePaperTradeHistory() {
  return usePoll('/api/agents/paper/trade-history', 60000);
}

export function usePaperTradeSummary() {
  return usePoll('/api/agents/paper/trade-summary', 60000);
}

export function usePaperStrategyBook() {
  return usePoll('/api/agents/paper/strategy-book', 300000);
}

export function usePaperStrategyBookExtended() {
  return usePoll('/api/agents/paper/strategy-book-extended', 60000);
}

export function usePaperAgentActivity() {
  return usePoll('/api/agents/paper/agent-activity', 30000);
}

export function usePaperUpcomingEvents() {
  return usePoll('/api/agents/paper/upcoming-events', 300000);
}

export function usePaperGatewayStatus() {
  return usePoll('/api/agents/paper/gateway-status', 30000);
}

export function usePaperCronStatus() {
  return usePoll('/api/agents/paper/cron-status', 30000);
}

export function usePaperSignalProximity() {
  return usePoll('/api/agents/paper/signal-proximity', 300000);
}

export function usePaperOpenPositionsPnl() {
  return usePoll('/api/agents/paper/open-positions-pnl', 60000);
}
