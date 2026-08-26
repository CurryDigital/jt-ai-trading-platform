import React, { useState } from 'react';
import { api, usePoll, fmt, fmtK, fmtAge, pnlCl } from '../utils';
import { ExecScaffold, ExecStat, ExecTabs, CloseButton } from './execution/ExecScaffold';

// Fire a real opposite-side IBKR market order to close one position row.
// LONG -> SELL, SHORT -> BUY, qty = full position quantity.
const fireCloseOrder = async (p) => {
  const action = p.side === 'LONG' ? 'SELL' : 'BUY';
  const res = await fetch('/api/ib/place-order', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ symbol: p.ticker, action, quantity: Number(p.quantity), order_type: 'MKT' }),
  });
  const body = await res.json().catch(() => ({}));
  if (res.ok && body.success) return { ok: true, text: body.message || `${action} ${p.quantity} ${p.ticker} sent` };
  return { ok: false, text: body.detail || body.message || 'Order failed' };
};

// Live positions table fed by GET /api/positions/live (gold.ibkr_positions_live
// primary, netted gold.trade_executions LIVE_TRADING fills as per-ticker fallback).
// Per-row Close fires a REAL opposite-side IBKR market order — the live book
// always fires live (per-book guard, no global mode); window.confirm gates it.
// stale=true (as_of > 24h) surfaces a STALE badge.
const LivePositionsPanel = ({ data, onRefresh }) => {
  const [closeState, setCloseState] = useState(null); // {id, busy, msg}
  const canClose = true;

  const closeOne = async (p) => {
    const action = p.side === 'LONG' ? 'SELL' : 'BUY';
    if (!window.confirm(`Fire real IBKR ${action} ${p.quantity} ${p.ticker} (MKT) to close this ${p.side} position?`)) return;
    setCloseState({ id: p.id, busy: true, msg: null });
    try {
      const r = await fireCloseOrder(p);
      setCloseState({ id: p.id, busy: false, msg: { type: r.ok ? 'success' : 'error', text: r.text } });
      if (r.ok) onRefresh?.();
    } catch (e) {
      setCloseState({ id: p.id, busy: false, msg: { type: 'error', text: e.message || 'Network error' } });
    }
  };

  if (!data) {
    return <div className="py-6 text-center text-slate-600 text-[11px]">Loading live positions…</div>;
  }
  const positions = data.positions || [];
  return (
    <div className="qr-surface overflow-hidden">
      <div className="px-3 py-2 border-b border-white/[0.05] flex items-center justify-between flex-wrap gap-2">
        <span className="flex items-center gap-2">
          <span className="qr-label">Live Positions{positions.length ? ` (${positions.length})` : ''}</span>
          {data.stale && (
            <span className="qr-chip qr-chip-rose" title={`Broker snapshot is >24h old (as_of ${data.as_of || '—'}) — sync pipeline has not refreshed`}>STALE</span>
          )}
        </span>
        <span className="text-[9px] text-slate-500" title="Primary: gold.ibkr_positions_live broker snapshot. Fallback: netted LIVE_TRADING fills from gold.trade_executions.">
          src {data.source || '—'} · upd {data.as_of ? fmtAge(data.as_of) + ' ago' : '—'}
        </span>
      </div>
      {!positions.length ? (
        <div className="py-6 text-center text-slate-600 text-[11px]">
          No live positions{data.source === 'none' ? ' · no broker snapshot and no ledger fills' : ''}
        </div>
      ) : (
        <div className="overflow-x-auto max-h-72 overflow-y-auto">
          <table className="w-full">
            <thead className="qr-th-sticky">
              <tr className="border-b border-white/[0.06]">
                <th className="qr-label text-left  py-1 px-2">Ticker</th>
                <th className="qr-label text-right py-1 px-2">Side</th>
                <th className="qr-label text-right py-1 px-2">Qty</th>
                <th className="qr-label text-right py-1 px-2">Avg Entry</th>
                <th className="qr-label text-right py-1 px-2">Current</th>
                <th className="qr-label text-right py-1 px-2">Unreal P&L</th>
                <th className="qr-label text-right py-1 px-2">Src</th>
                <th className="qr-label text-right py-1 px-2"></th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/[0.04]">
              {positions.map((p, i) => (
                <tr key={`${p.ticker}-${p.id ?? i}`} className="qr-tr-hover">
                  <td className="py-1 px-2 text-[11px] font-mono text-white">{p.ticker}</td>
                  <td className="py-1 px-2 text-right">
                    <span className={`qr-chip ${SIDE_STYLE[p.side] || 'qr-chip-slate'}`}>{p.side}</span>
                  </td>
                  <td className="py-1 px-2 qr-num text-slate-300 text-right">{fmt(p.quantity, 0)}</td>
                  <td className="py-1 px-2 qr-num text-slate-400 text-right">{fmt(p.avg_entry)}</td>
                  <td className="py-1 px-2 qr-num text-slate-300 text-right">{fmt(p.current_price)}</td>
                  <td className={`py-1 px-2 qr-num font-bold text-right ${pnlCl(p.unrealized_pnl)}`}>{p.unrealized_pnl == null ? '—' : fmt(p.unrealized_pnl)}</td>
                  <td className="py-1 px-2 qr-num text-[9px] text-slate-500 text-right">{(p.source || '').replace('ibkr_snapshot', 'ibkr')}</td>
                  <td className="py-1 px-2 text-right whitespace-nowrap">
                    <CloseButton
                      busy={closeState?.id === p.id && closeState.busy}
                      disabled={!canClose}
                      title={`Fire real IBKR ${p.side === 'LONG' ? 'SELL' : 'BUY'} ${p.quantity} ${p.ticker} (MKT) to close`}
                      onClick={() => closeOne(p)}
                    />
                    {closeState?.id === p.id && closeState.msg && (
                      <div className={`text-[9px] mt-0.5 ${closeState.msg.type === 'success' ? 'text-emerald-400' : 'text-rose-400'}`}>
                        {closeState.msg.text}
                      </div>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      {!canClose && positions.length > 0 && (
        <div className="px-3 py-1.5 border-t border-white/[0.05] text-[9px] text-slate-500">
          Close buttons arm only when the global mode is LIVE.
        </div>
      )}
    </div>
  );
};

// Manual close form — collapsed fallback for tickers not in the positions list.
// Fires a REAL opposite-side market order to the connected IBKR session (works in
// PAPER_TRADING/LIVE_TRADING; SIMULATION returns a simulated acknowledgement).
const LiveFlattenCard = () => {
  const [open, setOpen] = useState(false);
  const [f, setF] = useState({ ticker: '', side: 'LONG', qty: '' });
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState(null);
  const up = (k) => (e) => setF(s => ({ ...s, [k]: e.target.value }));
  const valid = f.ticker.trim() && Number(f.qty) > 0;

  const submit = async () => {
    if (!valid) return;
    const action = f.side === 'LONG' ? 'SELL' : 'BUY';
    const sym = f.ticker.trim().toUpperCase();
    if (!window.confirm(`Fire real IBKR ${action} ${f.qty} ${sym} (MKT) to close this ${f.side} position?`)) return;
    setBusy(true);
    setMsg(null);
    try {
      const res = await fetch('/api/ib/place-order', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ symbol: sym, action, quantity: Number(f.qty), order_type: 'MKT' }),
      });
      const body = await res.json().catch(() => ({}));
      if (res.ok && body.success) {
        setMsg({ type: 'success', text: body.message || `${action} ${f.qty} ${sym} sent` });
        setF({ ticker: '', side: 'LONG', qty: '' });
      } else {
        setMsg({ type: 'error', text: body.detail || body.message || 'Order failed' });
      }
    } catch (e) {
      setMsg({ type: 'error', text: e.message || 'Network error' });
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="qr-surface overflow-hidden">
      <button onClick={() => setOpen(o => !o)} className="w-full px-3 py-2 border-b border-white/[0.05] flex items-center justify-between">
        <span className="text-[12px] font-bold text-white">Manual Close</span>
        <span className="text-[9px] text-slate-500" title="Fires a real opposite-side market order to the connected IBKR session. Fallback for tickers not in the Live Positions table.">
          IBKR market · {open ? 'hide ▴' : 'show ▾'}
        </span>
      </button>
      {open && <div className="p-3 flex flex-col gap-2.5">
        <div>
          <label className="qr-label block mb-1">Symbol</label>
          <input value={f.ticker} onChange={up('ticker')} placeholder="AAPL" className="w-full box-border px-2 py-1.5 text-[11px] font-mono text-white bg-slate-900/50 border border-white/10 rounded outline-none" />
        </div>
        <div>
          <label className="qr-label block mb-1">Position Side</label>
          <div className="flex gap-0.5 p-0.5 rounded-md bg-slate-900/50 border border-white/10">
            {[['LONG', 'bg-emerald-600'], ['SHORT', 'bg-rose-600']].map(([k, bg]) => (
              <button key={k} onClick={() => setF(s => ({ ...s, side: k }))} className={`flex-1 py-1 rounded text-[10px] font-bold ${f.side === k ? `${bg} text-white` : 'text-slate-400'}`}>{k}</button>
            ))}
          </div>
        </div>
        <div>
          <label className="qr-label block mb-1">Qty</label>
          <input value={f.qty} onChange={up('qty')} inputMode="decimal" placeholder="100" className="w-full box-border px-2 py-1.5 text-[11px] font-mono text-white bg-slate-900/50 border border-white/10 rounded outline-none" />
        </div>
        <button onClick={submit} disabled={!valid || busy} className="qr-btn-primary justify-center disabled:opacity-40">
          {busy ? 'Firing…' : 'Fire Closing Order'}
        </button>
        {msg && <div className={`text-[10px] ${msg.type === 'success' ? 'text-emerald-400' : 'text-rose-400'}`}>{msg.text}</div>}
        <div className="text-[9px] text-slate-500 leading-relaxed">Closes by firing the opposite side at market on the connected IBKR session. Fallback for tickers not in the Live Positions table.</div>
      </div>}
    </div>
  );
};

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
  usePoll(async () => { const r = await api.get('/api/execution/gateway'); if (r) setGw(r); }, 15000);
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
  usePoll(async () => { const r = await api.get('/api/execution/limits'); if (r) setLimits(r); }, 15000);
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
  const [livePos, setLivePos] = useState(null);

  usePoll(async () => {
    const res = await api.get('/api/operations/live');
    if (res) setData(res);
    setRefreshedAt(new Date().toISOString());
  }, 10000); // 10s — this is the "now" surface

  const fetchLivePos = async () => {
    const r = await api.get('/api/positions/live');
    if (r) setLivePos(r);
  };
  usePoll(fetchLivePos, 10000);

  if (!data) {
    return (
      <div className="qr-surface px-3 py-6 flex items-center justify-center gap-2 text-[11px] text-slate-500">
        <div className="w-3 h-3 border-2 border-slate-700 border-t-blue-500 rounded-full animate-spin" />
        Loading live operations…
      </div>
    );
  }

  const s = data.summary;

  // Data-honesty guard: when the backend falls back to its generic
  // data_not_available shape (e.g. missing column in the signals view),
  // render an explicit PENDING state instead of crashing the whole app.
  // The rail (manual ticket + close) stays usable in this state.
  if (!s) {
    return (
      <ExecScaffold mode="live" book="live" railExtra={<LiveFlattenCard />}>
        <div className="qr-surface px-4 py-8 text-center">
          <span className="qr-chip qr-chip-rose">PENDING</span>
          <div className="mt-2 text-[12px] font-semibold text-slate-300">Live operations data not available yet</div>
          <div className="mt-1 text-[10px] text-slate-500">
            Source: GET /api/operations/live (gold.trade_executions · consumption.Strategies_Signals_Current)
            — blocked on qr_etl: signals view is missing the generated_at column
          </div>
          {data.message && <div className="mt-1 text-[10px] text-slate-600">{data.message}</div>}
          <div className="mt-2 qr-num text-[9px] text-slate-600">auto-retrying every 10s · upd {fmtAge(refreshedAt)}</div>
        </div>
      </ExecScaffold>
    );
  }

  const activeOrders = data.active_orders || [];
  const todaysFills = data.todays_fills || [];
  const activeSignals = data.signals || [];
  const tabs = [
    { id: 'orders',  label: `Orders (${s.active_order_count})` },
    { id: 'positions', label: `Positions (${livePos?.count ?? livePos?.positions?.length ?? '…'})` },
    { id: 'fills',   label: `Today (${s.todays_fill_count})` },
    { id: 'signals', label: `Signals (${s.active_signal_count})` },
    { id: 'gateway', label: 'Gateway' },
    { id: 'kill_switch', label: 'Kill Switch' },
  ];

  return (
    <ExecScaffold
      mode="live"
      book="live"
      stats={<>
        <ExecStat l="Today" v={fmtK(s.today_pnl)} tone={pnlCl(s.today_pnl)} />
        <ExecStat l="W / L" v={`${s.today_winners} / ${s.today_losers}`} tone="text-slate-400" />
        <ExecStat l="Updated" v={fmtAge(refreshedAt)} tone="text-slate-500" />
      </>}
      railExtra={<LiveFlattenCard />}
    >
    <div className="qr-surface overflow-hidden">
      <ExecTabs tabs={tabs} active={tab} onChange={setTab} />

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
              {activeOrders.map(o => (
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
              {!activeOrders.length && (
                <tr><td colSpan={9} className="py-6 text-center text-slate-600 text-[11px]">No active orders · all clear</td></tr>
              )}
            </tbody>
          </table>
        </div>
      )}

      {/* Live Positions (broker snapshot + ledger fallback) */}
      {tab === 'positions' && (
        <LivePositionsPanel data={livePos} onRefresh={fetchLivePos} />
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
              {todaysFills.map(f => (
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
              {!todaysFills.length && (
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
              {activeSignals.map((sig, i) => (
                <tr key={`${sig.strategy_id}-${sig.ticker}-${i}`} className="qr-tr-hover">
                  <td className="py-1 px-2 text-[10px] font-mono text-slate-300 truncate max-w-[120px]">
                    <button onClick={() => onSelectStrategy?.(sig.strategy_id)} className="hover:text-blue-300">{sig.strategy_id}</button>
                  </td>
                  <td className="py-1 px-2 text-[11px] font-mono text-white">{sig.ticker}</td>
                  <td className="py-1 px-2 text-right">
                    <span className={`qr-chip ${SIDE_STYLE[sig.signal] || 'qr-chip-slate'}`}>{sig.signal}</span>
                  </td>
                  <td className="py-1 px-2 qr-num text-slate-300">{sig.strength != null ? `${(sig.strength * 100).toFixed(0)}%` : '—'}</td>
                  <td className="py-1 px-2 qr-num text-slate-300">{sig.confidence != null ? `${(sig.confidence * 100).toFixed(0)}%` : '—'}</td>
                  <td className="py-1 px-2 qr-num text-slate-300">{fmt(sig.price)}</td>
                  <td className="py-1 px-2 qr-num text-[10px] text-slate-500 text-right">{sig.ts ? fmtAge(sig.ts) : '—'}</td>
                </tr>
              ))}
              {!activeSignals.length && (
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
    </ExecScaffold>
  );
};

export default LiveOpsPanel;
