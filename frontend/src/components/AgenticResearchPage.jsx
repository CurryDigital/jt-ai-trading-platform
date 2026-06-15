import React from 'react';
import {
  usePaperSystemStatus,
  usePaperDailyRuns,
  usePaperStrategyBookExtended,
  usePaperAgentActivity,
  usePaperUpcomingEvents,
} from './paper/usePaperData';
import RegimeSnapshotBar from './paper/RegimeSnapshotBar';
import StrategyBookPanel from './paper/StrategyBookPanel';
import AgentActivityFeed from './paper/AgentActivityFeed';
import UpcomingEventsCalendar from './paper/UpcomingEventsCalendar';

export default function AgenticResearchPage() {
  const status = usePaperSystemStatus();
  const runs = usePaperDailyRuns();
  const book = usePaperStrategyBookExtended();
  const activity = usePaperAgentActivity();
  const events = usePaperUpcomingEvents();

  const isLoading = status.loading || book.loading;

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="w-6 h-6 border-2 border-slate-700 border-t-blue-500 rounded-full animate-spin" />
      </div>
    );
  }

  // If we have data but it's empty/null, still render
  const hasData = status.data || book.data;

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-end justify-between">
        <div>
          <h1 className="text-sm font-bold text-white">Agentic Research</h1>
          <p className="text-[10px] text-slate-500">
            {book.data?.count || 0} strategies · {activity.data?.count || 0} events
          </p>
        </div>
        <div className="text-[10px] text-slate-500">
          regime: {status.data?.regime_label || '—'} · conf: {status.data?.regime_confidence != null ? status.data.regime_confidence.toFixed(2) : '—'}
        </div>
      </div>

      {/* Section A — Regime + Signal Snapshot */}
      <RegimeSnapshotBar
        systemStatus={status.data}
        strategyBook={book.data}
        upcomingEvents={events.data}
        dailyRuns={runs.data}
      />

      {/* Sections B + C — Strategy Book + Agent Activity */}
      <div className="grid grid-cols-1 lg:grid-cols-5 gap-4">
        <div className="lg:col-span-3">
          <StrategyBookPanel data={book.data} />
        </div>
        <div className="lg:col-span-2">
          <AgentActivityFeed data={activity.data} />
        </div>
      </div>

      {/* Section D — Upcoming Events Calendar */}
      <UpcomingEventsCalendar data={events.data} />
    </div>
  );
}
