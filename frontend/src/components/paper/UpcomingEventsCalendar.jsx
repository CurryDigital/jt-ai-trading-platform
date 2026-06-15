import React from 'react';

const CATEGORY_CONFIG = {
  earnings:  { icon: '📈', color: 'text-emerald-400',  bg: 'bg-emerald-500/10', border: 'border-emerald-500/20' },
  macro:     { icon: '📊', color: 'text-amber-400',    bg: 'bg-amber-500/10',   border: 'border-amber-500/20' },
  roll:      { icon: '🔄', color: 'text-blue-400',     bg: 'bg-blue-500/10',    border: 'border-blue-500/20' },
  review:    { icon: '📋', color: 'text-violet-400',   bg: 'bg-violet-500/10',  border: 'border-violet-500/20' },
  seasonal:  { icon: '🌿', color: 'text-teal-400',     bg: 'bg-teal-500/10',    border: 'border-teal-500/20' },
};

export default function UpcomingEventsCalendar({ data }) {
  const events = data?.events || [];

  if (!events.length) {
    return (
      <div className="rounded-lg bg-slate-800/50 border border-slate-700/50 p-4">
        <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">Upcoming Events</h3>
        <p className="text-sm text-slate-500">No events in next 14 days</p>
      </div>
    );
  }

  return (
    <div className="rounded-lg bg-slate-800/50 border border-slate-700/50 p-3">
      <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-3">
        Upcoming Events ({events.length})
      </h3>

      {/* Timeline bar */}
      <div className="relative mb-4">
        <div className="h-0.5 bg-slate-700 rounded-full" />
        <div className="flex justify-between mt-1">
          {['Today', '+3d', '+7d', '+10d', '+14d'].map((label, i) => (
            <span key={i} className="text-[9px] text-slate-600">{label}</span>
          ))}
        </div>
      </div>

      {/* Event cards */}
      <div className="flex gap-2 overflow-x-auto pb-2 no-scrollbar">
        {events.slice(0, 10).map((ev, i) => {
          const cfg = CATEGORY_CONFIG[ev.event_category] || CATEGORY_CONFIG.macro;
          const urgencyColor = ev.days_away <= 1 ? 'text-rose-400' : ev.days_away <= 3 ? 'text-amber-400' : 'text-slate-500';

          return (
            <div
              key={i}
              className={`flex-shrink-0 w-32 rounded-lg border p-2 ${cfg.border} ${cfg.bg} hover:border-slate-500/30 transition-colors`}
            >
              <div className="flex items-center gap-1 mb-1">
                <span className="text-xs">{cfg.icon}</span>
                <span className={`text-[9px] font-bold uppercase ${cfg.color}`}>{ev.event_category}</span>
              </div>
              <div className="text-[11px] font-bold text-slate-200 truncate" title={ev.event_label}>
                {ev.event_label}
              </div>
              <div className="text-[9px] text-slate-400 mt-0.5">{ev.event_date}</div>
              <div className="text-[9px] text-slate-500 truncate" title={ev.description}>
                {ev.description}
              </div>
              <div className={`text-[9px] font-bold mt-1 ${urgencyColor}`}>
                {ev.days_away === 0 ? 'TODAY' : `${ev.days_away}d away`}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
