import React, { useEffect, useState } from 'react';
import { api, fmtAge } from '../utils';

const TYPE_STYLE = {
  'strategy.mode_change': 'qr-chip-blue',
  'kill_switch.fire':     'qr-chip-rose',
};

export const AuditLog = () => {
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('');

  const load = async () => {
    const params = new URLSearchParams({ limit: '200' });
    if (filter) params.set('event_type', filter);
    const res = await api.get(`/api/audit/events?${params}`);
    setEvents(res?.events || []);
    setLoading(false);
  };

  useEffect(() => { load(); }, [filter]);

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-[13px] font-bold text-white">Audit Log</h3>
          <p className="text-[10px] text-slate-500">Mode changes, kill switches, overrides</p>
        </div>
        <div className="flex items-center gap-2">
          <select
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
            className="px-2 py-1 bg-slate-900/60 border border-white/[0.08] rounded text-[11px] text-slate-300 focus:outline-none"
          >
            <option value="">All events</option>
            <option value="strategy.mode_change">Mode changes</option>
            <option value="kill_switch.fire">Kill switches</option>
          </select>
          <button onClick={load} className="qr-btn-ghost">↻</button>
        </div>
      </div>

      <div className="qr-surface overflow-hidden">
        {loading ? (
          <div className="py-8 text-center text-[11px] text-slate-500">Loading…</div>
        ) : events.length === 0 ? (
          <div className="py-8 text-center text-[11px] text-slate-600">
            No audit events yet · events appear after mode changes or kill switches
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-white/[0.06]">
                  <th className="qr-label text-left py-1.5 px-2">Time</th>
                  <th className="qr-label text-left py-1.5 px-2">Event</th>
                  <th className="qr-label text-left py-1.5 px-2">Strategy</th>
                  <th className="qr-label text-left py-1.5 px-2">Details</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/[0.04]">
                {events.map(e => {
                  const p = e.payload || {};
                  let detail = '';
                  if (e.event_type === 'strategy.mode_change') {
                    detail = `${p.from || '?'} → ${p.to || '?'}${p.override_gates ? ' (override)' : ''}`;
                  } else if (e.event_type === 'kill_switch.fire') {
                    detail = `${p.count || 0} strategies halted`;
                  } else {
                    detail = JSON.stringify(p).slice(0, 120);
                  }

                  return (
                    <tr key={e.id} className="qr-tr-hover">
                      <td className="py-1.5 px-2 qr-num text-[10px] text-slate-400 whitespace-nowrap">
                        {e.created_at ? new Date(e.created_at).toLocaleString('en-GB', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit', second: '2-digit' }) : '—'}
                        <div className="text-[8px] text-slate-600">{fmtAge(e.created_at)}</div>
                      </td>
                      <td className="py-1.5 px-2">
                        <span className={`qr-chip ${TYPE_STYLE[e.event_type] || 'qr-chip-slate'}`}>{e.event_type}</span>
                      </td>
                      <td className="py-1.5 px-2 text-[11px] text-white font-mono">{e.strategy_id || '—'}</td>
                      <td className="py-1.5 px-2 text-[10px] text-slate-400 max-w-xs truncate" title={JSON.stringify(p)}>{detail}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};

export default AuditLog;
