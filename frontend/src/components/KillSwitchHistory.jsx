import React, { useState, useEffect } from 'react';
import { api, fmtAge } from '../utils';

export const KillSwitchHistory = ({ onClose }) => {
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      const res = await api.get('/api/audit/events?event_type=kill_switch.fire&limit=20');
      if (res?.events) setEvents(res.events);
      setLoading(false);
    })();
  }, []);

  return (
    <div className="absolute right-0 top-full mt-1 z-50 w-72 bg-[#0e111a] border border-white/[0.08] rounded-lg shadow-xl overflow-hidden">
      <div className="px-3 py-2 border-b border-white/[0.06] flex items-center justify-between">
        <span className="text-[11px] font-bold text-rose-300">Kill Switch History</span>
        <button onClick={onClose} className="text-[10px] text-slate-500 hover:text-white">×</button>
      </div>

      {loading ? (
        <div className="px-3 py-4 text-center text-[10px] text-slate-500">Loading…</div>
      ) : !events.length ? (
        <div className="px-3 py-4 text-center text-[10px] text-slate-600">No kill switch events recorded</div>
      ) : (
        <div className="max-h-64 overflow-y-auto divide-y divide-white/[0.04]">
          {events.map(e => {
            const payload = e.payload || {};
            return (
              <div key={e.id} className="px-3 py-2">
                <div className="flex items-center justify-between">
                  <span className="text-[10px] font-bold text-rose-300">HALT FIRED</span>
                  <span className="text-[9px] text-slate-500">{fmtAge(e.created_at)}</span>
                </div>
                <div className="text-[10px] text-slate-400 mt-0.5">
                  {payload.count || 0} strategies demoted to PAPER
                </div>
                {payload.affected_strategies?.length > 0 && (
                  <div className="flex flex-wrap gap-1 mt-1">
                    {payload.affected_strategies.slice(0, 5).map(id => (
                      <span key={id} className="px-1 py-0.5 rounded bg-rose-500/10 text-[8px] font-mono text-rose-400">{id}</span>
                    ))}
                    {payload.affected_strategies.length > 5 && (
                      <span className="text-[8px] text-slate-600">+{payload.affected_strategies.length - 5} more</span>
                    )}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};

export default KillSwitchHistory;
