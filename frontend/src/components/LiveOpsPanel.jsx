import React, { useEffect, useState } from 'react';
import { api, fmt, fmtK, fmtAge, pnlCl } from '../utils';

const STATUS_STYLE = {
  PENDING:   'qr-chip-amber',
  WORKING:   'qr-chip-blue',
  SUBMITTED: 'qr-chip-blue',
  PARTIAL:   'qr-chip-violet',
  FILLED:    'qr-chip-emerald',
  CANCELLED: 'qr-chip-slate',
  REJECTED:  'qr-chip-rose',
};

const SIDE_STYLE = {
  BUY:  'qr-chip-emerald',
  SELL: 'qr-chip-rose',
  LONG: 'qr-chip-emerald',
  SHORT:'qr-chip-rose',
};

const fmtTimeShort = (iso) => {
  if (!iso) return '—';
  return new Date(iso).toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
};

const GatewayPanel = () => {
  const [gw, setGw] = useState(null);
  useEffect(() => {
    let alive = true;
    const load = async () => { const r = await api.get('/api/execution/gateway'); if (alive) setGw(r); };
    load();
    const id = setInterval(load, 15000);
    return () => { alive = false; clearInterval(id); };
  }, []);
  if (!gw) return <div className="py-6 text-center text-[11px] text-slate-600">Loading gateway status…</div>;
  return (
    <div className="p-3.5 flex flex-col gap-3">
      <div className="grid grid-cols-3 gap-2">
        {[
          ['Connected', gw.connected == null ? '—' : gw.connected ? 'Yes' : 'No', gw.connected ? 'text-emerald-400' : 'text-rose-400'],
          ['Latency', gw.latency_ms != null ? `${gw.latency_ms} ms` : '—', 'text-white'],
          ['Global Mode', (gw.global_mode || '').replace('_TRADING', '').replace('SIMULATION', 'SIM'), 'text-blue-400'],
        ].map(([l, v, c]) => (
          <div key={l} className="p-2 rounded bg-white/[0.03] border border-white/[0.05]">
            <div className="text-[8px] uppercase tracking-wide text-slate-500">{l}</div>
            <div className={`font-mono text-[14px] font-bold mt-0.5 ${c}`}>{v}</div>
          </div>
        ))}
      </div>
      <div className="grid grid-cols-2 gap-1 rounded overflow-hidden bg-white/[0.05]">
        {[['Host', gw.host || '—'], ['Port', gw.port || '—'], ['Account', gw.account || '—'],
          ['Last Heartbeat', gw.last_heartbeat ? fmtAge(gw.last_heartbeat) + ' ago' : '—']].map(([l, v]) => (
          <div key={l} className="px-3 py-1.5 bg-[#10141f] flex justify-between items-center">
            <span className="text-[10px] text-slate-500">{l}</span>
            <span className="font-mono text-[11px] font-bold text-white">{v}</span>
          </div>
        ))}
      </div>
    </div>
  );
};

const KillSwitchPanel = () => {
  const [limits, setLimits] = useState(null);
  const [phrase, setPhrase] = useState('');
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState(null);
  useEffect(() => {
    let alive = true;
    const load = async () => { const r = await api.get('/api/execution/limits'); if (alive) setLimits(r); };
    load();
    const id = setInterval(load, 15000);
    return () => { alive = false; clearInterval(id); };
  }, []);
  const haltReady = phrase.trim().toUpperCase() === 'HALT ALL';
  const fire = async () => {
    setBusy(true); setMsg(null);
    const res = await api.post('/api/execution/kill-switch', { phrase });
    setMsg(res ? { type: 'success', text: `Status: ${res.status}` } : { type: 'error', text: 'Kill switch request failed' });
    setBusy(false);
    setPhrase('');
  };
  if (!limits) return <div className="py-6 text-center text-[11px] text-slate-600">Loading limits…</div>;
  return (
    <div className="p-3.5 flex flex-col gap-3.5">
      <div className={`p-3 rounded-lg border ${limits.global_halt ? 'border-rose-500/40 bg-rose-500/10' : 'border-rose-500/25 bg-rose-500/5'}`}>
        <div className="text-[10px] font-bold text-rose-400 mb-1.5">GLOBAL KILL SWITCH {limits.global_halt ? '· HALTED' : ''}</div>
        <div className="text-[9px] text-slate-500 mb-2">Type <span className="font-mono text-slate-300">HALT ALL</span> to cancel every working order and flatten the book.</div>
        <div className="flex gap-2">
          <input value={phrase} onChange={e => setPhrase(e.target.value)} placeholder="confirmation phrase"
            className="flex-1 box-border px-2.5 py-1.5 text-[11px] font-mono text-white bg-slate-900/60 border border-white/10 rounded outline-none" />
          <button onClick={fire} disabled={!haltReady || busy} className="px-3 py-1.5 rounded text-[10px] font-bold uppercase bg-rose-600 hover:bg-rose-500 disabled:bg-slate-700 text-white">
            {busy ? '...' : 'HALT'}
          </button>
        </div>
        {msg && <div className={`mt-2 text-[10px] ${msg.type === 'success' ? 'text-emerald-400' : 'text-rose-400'}`}>{msg.text}</div>}
      </div>
      <div className="flex flex-col gap-2">
        <div className="text-[9px] uppercase tracking-wide text-slate-500 font-semibold">Per-Strategy Capital Caps</div>
        {(limits.per_strategy || []).map(s => {
          const pct = s.capital_cap_pct ? Math.round((s.used_pct / s.capital_cap_pct) * 100) : 0;
          const hot = pct >= 90;
          return (
            <div key={s.strategy_id}>
              <div className="flex justify-between text-[10px] mb-1">
                <span className="text-slate-300">{s.strategy_id}</span>
                <span className={`font-mono ${hot ? 'text-rose-400' : 'text-slate-500'}`}>{s.used_pct ?? '—'}% / {s.capital_cap_pct ?? '—'}%</span>
              </div>
              <div className="h-1 rounded bg-white/[0.06] overflow-hidden">
                <div className={`h-full ${hot ? 'bg-rose-500' : 'bg-blue-500'}`} style={{ width: `${Math.min(100, pct)}%` }} />
              </div>
            </div>
          );
        })}
        {(limits.per_strategy || []).length === 0 && <div className="text-[10px] text-slate-600">No per-strategy caps configured yet</div>}
      </div>
    </div>
  );
};

export const LiveOpsPanel = ({ onSelectStrategy }) => {
  const [data, setData] = useState(null);
  const [tab, setTab] = useState('orders');
  const [refreshedAt, setRefreshedAt] = useState(null);

  const load = async () => {
    const res = await api.get('/api/operations/live');
    if (res) setData(res);
    setRefreshedAt(new Date().toISOString());
  };

  useEffect(() => {
    load();
    const id = setInterval(load, 10000);  // 10s — this is the "now" surface
    return () => clearInterval(id);
  }, []);

  if (!data) {
    return (
      <div className="qr-surface px-3 py-6 flex items-center justify-center gap-2 text-[11px] text-slate-500">
        <div className="w-3 h-3 border-2 border-slate-700 border-t-blue-500 rounded-full animate-spin" />
        Loading live operations…
      </div>
    );
  }

  const s = data.summary;
  const tabs = [
    { id: 'orders',  label: `Orders (${s.active_order_count})`,  badge: s.active_order_count > 0 ? 'qr-chip-amber' : null },
    { id: 'fills',   label: `Today (${s.todays_fill_count})` },
    { id: 'signals', label: `Signals (${s.active_signal_count})` },
    { id: 'gateway', label: 'Gateway' },
    { id: 'kill_switch', label: 'Kill Switch' },
  ];

  return (
    <div className="qr-surface overflow-hidden">
      <div className="px-3 py-2 border-b border-white/[0.05] flex items-center justify-between flex-wrap gap-2">
        <div className="flex items-center gap-1">
          {tabs.map(t => (
            <button
              key={t.id}
              onClick={() => setTab(t.id)}
              className={`px-2 py-1 rounded text-[11px] font-semibold transition-colors ${
                tab === t.id ? 'bg-white/[0.08] text-white' : 'text-slate-400 hover:text-slate-200'
              }`}
            >{t.label}</button>
          ))}
        </div>
        <div className="flex items-center gap-3 text-[10px]">
          <div>
            <span className="qr-label">Today</span>
            <span className={`qr-num font-bold ml-1 ${pnlCl(s.today_pnl)}`}>{fmtK(s.today_pnl)}</span>
            <span className="text-slate-600 ml-1">·</span>
            <span className="text-emerald-400 ml-1">{s.today_winners}W</span>
            <span className="text-slate-600">/</span>
            <span className="text-rose-400">{s.today_losers}L</span>
          </div>
          <span className="qr-num text-slate-500">upd {fmtAge(refreshedAt)}</span>
        </div>
      </div>

      {/* Active Orders */}
      {tab === 'orders' && (
        <div className="overflow-x-auto max-h-72 overflow-y-auto">
          <table className="w-full">
            <thead className="qr-th-sticky">
              <tr className="border-b border-white/[0.06]">
                <th className="qr-label text-left  py-1 px-2">Submitted</th>
                <th className="qr-label text-left  py-1 px-2">Strategy</th>
                <th className="qr-label text-left  py-1 px-2">Ticker</th>
                <th className="qr-label text-right py-1 px-2">Side</th>
                <th className="qr-label text-right py-1 px-2">Qty</th>
                <th className="qr-label text-right py-1 px-2">Price</th>
                <th className="qr-label text-right py-1 px-2">Type</th>
                <th className="qr-label text-right py-1 px-2">Status</th>
                <th className="qr-label text-right py-1 px-2">Mode</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/[0.04]">
              {data.active_orders.map(o => (
                <tr key={o.id} className="qr-tr-hover">
                  <td className="py-1 px-2 qr-num text-[10px] text-slate-400">{fmtTimeShort(o.submitted_at)}</td>
                  <td className="py-1 px-2 text-[10px] font-mono text-slate-300 truncate max-w-[120px]">
                    <button onClick={() => onSelectStrategy?.(o.strategy_id)} className="hover:text-blue-300">{o.strategy_id}</button>
                  </td>
                  <td className="py-1 px-2 text-[11px] font-mono text-white">{o.ticker}</td>
                  <td className="py-1 px-2 text-right">
                    <span className={`qr-chip ${SIDE_STYLE[o.side] || 'qr-chip-slate'}`}>{o.side}</span>
                  </td>
                  <td className="py-1 px-2 qr-num text-slate-300">{fmt(o.quantity, 0)}</td>
                  <td className="py-1 px-2 qr-num text-slate-300">{o.price != null ? fmt(o.price) : '—'}</td>
                  <td className="py-1 px-2 qr-num text-[10px] text-slate-400 text-right">{o.order_type || 'MKT'}</td>
                  <td className="py-1 px-2 text-right">
                    <span className={`qr-chip ${STATUS_STYLE[o.status] || 'qr-chip-slate'}`}>{o.status}</span>
                  </td>
                  <td className="py-1 px-2 qr-num text-[9px] text-slate-500 text-right">{(o.execution_mode || '').replace('_TRADING','').replace('SIMULATION','SIM')}</td>
                </tr>
              ))}
              {!data.active_orders.length && (
                <tr><td colSpan={9} className="py-6 text-center text-slate-600 text-[11px]">No active orders · all clear</td></tr>
              )}
            </tbody>
          </table>
        </div>
      )}

      {/* Today's Fills */}
      {tab === 'fills' && (
        <div className="overflow-x-auto max-h-72 overflow-y-auto">
          <table className="w-full">
            <thead className="qr-th-sticky">
              <tr className="border-b border-white/[0.06]">
                <th className="qr-label text-left  py-1 px-2">Filled</th>
                <th className="qr-label text-left  py-1 px-2">Strategy</th>
                <th className="qr-label text-left  py-1 px-2">Ticker</th>
                <th className="qr-label text-right py-1 px-2">Side</th>
                <th className="qr-label text-right py-1 px-2">Qty</th>
                <th className="qr-label text-right py-1 px-2">Price</th>
                <th className="qr-label text-right py-1 px-2">P&L</th>
                <th className="qr-label text-right py-1 px-2">Mode</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/[0.04]">
              {data.todays_fills.map(f => (
                <tr key={f.id} className="qr-tr-hover">
                  <td className="py-1 px-2 qr-num text-[10px] text-slate-400">{fmtTimeShort(f.filled_at)}</td>
                  <td className="py-1 px-2 text-[10px] font-mono text-slate-300 truncate max-w-[120px]">
                    <button onClick={() => onSelectStrategy?.(f.strategy_id)} className="hover:text-blue-300">{f.strategy_id}</button>
                  </td>
                  <td className="py-1 px-2 text-[11px] font-mono text-white">{f.ticker}</td>
                  <td className="py-1 px-2 text-right">
                    <span className={`qr-chip ${SIDE_STYLE[f.side] || 'qr-chip-slate'}`}>{f.side}</span>
                  </td>
                  <td className="py-1 px-2 qr-num text-slate-300">{fmt(f.quantity, 0)}</td>
                  <td className="py-1 px-2 qr-num text-slate-300">{fmt(f.price)}</td>
                  <td className={`py-1 px-2 qr-num font-bold ${pnlCl(f.pnl)}`}>{f.pnl == null ? '—' : fmtK(f.pnl)}</td>
                  <td className="py-1 px-2 qr-num text-[9px] text-slate-500 text-right">{(f.execution_mode || '').replace('_TRADING','').replace('SIMULATION','SIM')}</td>
                </tr>
              ))}
              {!data.todays_fills.length && (
                <tr><td colSpan={8} className="py-6 text-center text-slate-600 text-[11px]">No fills today · waiting for signals</td></tr>
              )}
            </tbody>
          </table>
        </div>
      )}

      {/* Active Signals */}
      {tab === 'signals' && (
        <div className="overflow-x-auto max-h-72 overflow-y-auto">
          <table className="w-full">
            <thead className="qr-th-sticky">
              <tr className="border-b border-white/[0.06]">
                <th className="qr-label text-left  py-1 px-2">Strategy</th>
                <th className="qr-label text-left  py-1 px-2">Ticker</th>
                <th className="qr-label text-right py-1 px-2">Signal</th>
                <th className="qr-label text-right py-1 px-2">Strength</th>
                <th className="qr-label text-right py-1 px-2">Confidence</th>
                <th className="qr-label text-right py-1 px-2">Price</th>
                <th className="qr-label text-right py-1 px-2">Generated</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/[0.04]">
              {data.signals.map((s, i) => (
                <tr key={`${s.strategy_id}-${s.ticker}-${i}`} className="qr-tr-hover">
                  <td className="py-1 px-2 text-[10px] font-mono text-slate-300 truncate max-w-[120px]">
                    <button onClick={() => onSelectStrategy?.(s.strategy_id)} className="hover:text-blue-300">{s.strategy_id}</button>
                  </td>
                  <td className="py-1 px-2 text-[11px] font-mono text-white">{s.ticker}</td>
                  <td className="py-1 px-2 text-right">
                    <span className={`qr-chip ${SIDE_STYLE[s.signal] || 'qr-chip-slate'}`}>{s.signal}</span>
                  </td>
                  <td className="py-1 px-2 qr-num text-slate-300">{s.strength != null ? `${(s.strength * 100).toFixed(0)}%` : '—'}</td>
                  <td className="py-1 px-2 qr-num text-slate-300">{s.confidence != null ? `${(s.confidence * 100).toFixed(0)}%` : '—'}</td>
                  <td className="py-1 px-2 qr-num text-slate-300">{fmt(s.price)}</td>
                  <td className="py-1 px-2 qr-num text-[10px] text-slate-500 text-right">{s.ts ? fmtAge(s.ts) : '—'}</td>
                </tr>
              ))}
              {!data.signals.length && (
                <tr><td colSpan={7} className="py-6 text-center text-slate-600 text-[11px]">No active signals · DE pipeline may not have populated yet</td></tr>
              )}
            </tbody>
          </table>
        </div>
      )}

      {/* IBKR Gateway */}
      {tab === 'gateway' && <GatewayPanel />}

      {/* Kill Switch & Limits */}
      {tab === 'kill_switch' && <KillSwitchPanel />}
    </div>
  );
};

export default LiveOpsPanel;
