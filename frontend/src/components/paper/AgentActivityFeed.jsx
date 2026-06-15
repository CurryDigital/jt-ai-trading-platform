import React from 'react';

const AGENT_CONFIG = {
  qr_research:   { label: 'RESEARCH', color: 'bg-blue-500/20 text-blue-400' },
  qr_risk:       { label: 'RISK',     color: 'bg-emerald-500/20 text-emerald-400' },
  qr_etl:        { label: 'ETL',      color: 'bg-amber-500/20 text-amber-400' },
  qr_qa:         { label: 'QA',       color: 'bg-violet-500/20 text-violet-400' },
  scrum_master:  { label: 'OPS',      color: 'bg-slate-600/20 text-slate-400' },
};

function formatTimeAgo(ts) {
  if (!ts) return '';
  const diff = Date.now() - new Date(ts).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return 'just now';
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  const days = Math.floor(hrs / 24);
  return `${days}d ago`;
}

export default function AgentActivityFeed({ data }) {
  const events = data?.events || [];

  return (
    <div className="rounded-lg bg-slate-800/50 border border-slate-700/50 p-3 h-full flex flex-col">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider">
          Agent Activity
        </h3>
        <div className="flex items-center gap-1.5">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
          <span className="text-[9px] text-slate-500">LIVE</span>
        </div>
      </div>

      {events.length === 0 ? (
        <div className="flex-1 flex flex-col items-center justify-center text-center py-8">
          <span className="text-2xl mb-2">🤖</span>
          <p className="text-sm text-slate-500">No agent activity yet</p>
          <p className="text-[10px] text-slate-600 mt-1 max-w-[200px]">
            Agents will log here as strategies are promoted, orders are placed, and regime changes occur.
          </p>
        </div>
      ) : (
        <div className="space-y-2 overflow-y-auto flex-1 max-h-[600px]">
          {events.map((ev, i) => {
            const cfg = AGENT_CONFIG[ev.agent_name] || { label: ev.agent_name?.toUpperCase(), color: 'bg-slate-600/20 text-slate-400' };
            return (
              <div key={i} className="flex items-start gap-2 p-2 rounded bg-slate-800/30 hover:bg-slate-800/50 transition-colors">
                <span className={`text-[9px] px-1.5 py-0.5 rounded font-bold flex-shrink-0 ${cfg.color}`}>
                  {cfg.label}
                </span>
                <div className="flex-1 min-w-0">
                  <div className="text-[11px] font-bold text-slate-300">{ev.event_type}</div>
                  {ev.detail && (
                    <div className="text-[10px] text-slate-400 truncate" title={ev.detail}>{ev.detail}</div>
                  )}
                  {ev.strategy_id && (
                    <div className="text-[10px] text-slate-500">Strategy: {ev.strategy_id}</div>
                  )}
                </div>
                <span className="text-[9px] text-slate-600 whitespace-nowrap">{formatTimeAgo(ev.ts)}</span>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
