import React, { useState } from 'react';
import { ExecScaffold, ExecStat, ExecTabs, CloseButton } from './ExecScaffold';
import { api, usePoll, fmt, fmtSigned, pnlCl } from '../../utils';

// Paper UAT — IBKR paper account book: real gateway, real order firing, paper money.
// Backend landed in qr_etl t_8d32721e (verified t_1fbd9d7c): PAPER_UAT mode +
// dedicated UAT session (separate client id, never falls back to primary/live).
// Unified anatomy (2026-08-26): same tabbed surface as the Live book —
// Positions / Working / Fills / Session. The old always-open "UAT Blotter"
// card is now the Fills tab; the session card is the Session tab.

const fmtAge = (iso) => {
  if (!iso) return '—';
  const t = new Date(iso.endsWith('Z') || iso.includes('+') ? iso : iso + 'Z');
  const s = Math.max(0, Math.round((Date.now() - t.getTime()) / 1000));
  if (s < 60) return `${s}s`;
  if (s < 3600) return `${Math.floor(s / 60)}m`;
  return `${Math.floor(s / 3600)}h`;
};

const fmtTime = (iso) => {
  if (!iso) return '—';
  const t = new Date(iso.endsWith('Z') || iso.includes('+') ? iso : iso + 'Z');
  return t.toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
};

// One IBKR gateway session row (primary or uat) with its own connect action.
const SessionRow = ({ name, title, note, sess, liveConnected, connectPath, onConnected }) => {
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState(null);
  const connected = liveConnected ?? sess?.connected ?? null;

  const connect = async () => {
    setBusy(true); setMsg(null);
    const res = await api.post(connectPath, {});
    if (res && (res.status === 'Connected' || res.is_connected)) {
      setMsg({ type: 'ok', text: `Connected — ${res.host || sess?.host || ''}:${res.port || sess?.port || ''} client ${res.client_id ?? sess?.live?.client_id ?? '?'}${res.account ? ` · ${res.account}` : ''}` });
    } else {
      setMsg({ type: 'err', text: res?.reason || res?.message || 'Connect failed — is the IBKR gateway reachable?' });
    }
    setBusy(false);
    if (onConnected) onConnected();
  };

  return (
    <div className="rounded bg-white/[0.03] border border-white/[0.05] px-3 py-2.5">
      <div className="flex items-center justify-between gap-2 flex-wrap">
        <div className="min-w-0">
          <div className="flex items-center gap-2">
            <span className="text-[11px] font-bold text-white">{title}</span>
            <span className={`qr-chip ${connected == null ? 'qr-chip-slate' : connected ? 'qr-chip-emerald' : 'qr-chip-rose'}`}>
              {connected == null ? 'UNKNOWN' : connected ? 'CONNECTED' : 'DISCONNECTED'}
            </span>
          </div>
          <div className="text-[9px] text-slate-500 mt-0.5">{note}</div>
        </div>
        <button
          onClick={connect}
          disabled={busy || connected === true}
          title={connected ? 'Session is connected' : `Start the ${name} session`}
          className="px-2.5 py-1 rounded text-[9px] font-bold uppercase tracking-wide bg-slate-700/80 text-slate-200 hover:bg-slate-600 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
        >
          {busy ? 'Connecting…' : connected ? 'Connected' : 'Connect'}
        </button>
      </div>
      <div className="mt-2 grid grid-cols-2 sm:grid-cols-4 gap-1 rounded overflow-hidden bg-white/[0.05]">
        {[
          ['Endpoint', sess ? `${sess.host || '—'}:${sess.port || '—'}` : '—'],
          ['Client ID', sess?.live?.client_id ?? '—'],
          // Real account id comes from the live session (managedAccounts at
          // connect time); the DB heartbeat account is only a fallback and is
          // hidden when disconnected so a stale row never reads as truth.
          ['Account', connected ? (sess?.live?.account || sess?.account || '—') : '—'],
          ['Heartbeat', sess?.last_heartbeat ? `${fmtAge(sess.last_heartbeat)} ago` : '—'],
        ].map(([l, v]) => (
          <div key={l} className="px-2.5 py-1.5 bg-[#10141f]">
            <div className="text-[8px] uppercase tracking-wide text-slate-500">{l}</div>
            <div className="font-mono text-[11px] font-bold text-white mt-0.5 truncate">{v}</div>
          </div>
        ))}
      </div>
      {msg && <div className={`mt-1.5 text-[10px] ${msg.type === 'ok' ? 'text-emerald-400' : 'text-rose-400'}`}>{msg.text}</div>}
    </div>
  );
};

export const PaperUatPanel = () => {
  const [tab, setTab] = useState('positions');
  const [gw, setGw] = useState(null);
  const [uat, setUat] = useState(null);
  const [acct, setAcct] = useState(null);
  const [blotter, setBlotter] = useState(null);
  const [positions, setPositions] = useState(null);
  const [openOrders, setOpenOrders] = useState(null);
  const [sessionFills, setSessionFills] = useState(null);
  const [closing, setClosing] = useState(null);   // symbol currently being closed
  const [cancelling, setCancelling] = useState(null); // order_id currently being cancelled
  const [closeMsg, setCloseMsg] = useState(null); // {type:'ok'|'info'|'err', text}
  const [refreshing, setRefreshing] = useState(false);
  const [lastRefresh, setLastRefresh] = useState(null);

  const poll = async () => {
    const [g, u, a, b, p, oo, sf] = await Promise.all([
      api.get('/api/execution/gateway'),
      api.get('/api/ib/tws/uat/status'),
      api.get('/api/ib/tws/uat/account'),
      api.get('/api/execution/trades?book=paper_uat&limit=50'),
      api.get('/api/ib/tws/uat/positions'),
      api.get('/api/ib/tws/uat/open-orders'),
      api.get('/api/ib/tws/uat/fills'),
    ]);
    if (g) setGw(g);
    if (u) setUat(u);
    if (a) setAcct(a);
    if (b) setBlotter(b);
    if (p) setPositions(p);
    if (oo) setOpenOrders(oo);
    if (sf) setSessionFills(sf);
    setLastRefresh(new Date());
  };
  usePoll(poll, 15000);

  // On-demand refresh — user-triggered latest status without waiting for the 15s poll.
  const refresh = async () => {
    setRefreshing(true);
    try { await poll(); } finally { setRefreshing(false); }
  };

  // Close one IBKR paper-account position: real opposite-side MKT on the UAT
  // session (backend resolves qty from the live portfolio, never the client).
  // Raw fetch with a 45s budget: the backend waits up to 30s for the fill, and
  // error bodies carry the real reason (api.post would swallow them as null).
  const closePosition = async (p) => {
    const side = p.qty > 0 ? 'SELL' : 'BUY';
    if (!window.confirm(`Close ${Math.abs(p.qty)} ${p.ticker} on UAT paper account ${positions?.account}?
${side} ${Math.abs(p.qty)} @ MKT — real order, paper money.`)) return;
    setClosing(p.symbol); setCloseMsg(null);
    let res = null;
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 45000);
      const r = await fetch('/api/ib/tws/uat/close-position', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ symbol: p.symbol }),
        signal: controller.signal,
      });
      clearTimeout(timeoutId);
      res = r.ok
        ? await r.json().catch(() => ({}))
        : { success: false, ...(await r.json().catch(() => ({}))) };
    } catch {
      res = { success: false, error: 'Request timed out or network error — check the session status before retrying' };
    }
    if (res && res.success) {
      const working = res.already_working || res.filled === false;
      setCloseMsg({
        type: working ? 'info' : 'ok',
        text: `${res.message}${res.fill_price ? ` · filled ${res.fill_price}` : ''} · order ${res.order_id}`,
      });
      // Let the gateway portfolio settle, then pull the latest state.
      setTimeout(poll, 1500);
    } else {
      setCloseMsg({ type: 'err', text: res?.detail || res?.error || res?.message || 'Close failed' });
    }
    setClosing(null);
    poll();
  };

  // Cancel a working (pending-execution) order on the UAT session.
  const cancelOrder = async (o) => {
    if (!window.confirm(`Cancel order ${o.order_id} — ${o.action} ${o.qty} ${o.symbol} (${o.status})?`)) return;
    setCancelling(o.order_id); setCloseMsg(null);
    let res = null;
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 25000);
      const r = await fetch('/api/ib/tws/uat/cancel-order', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ order_id: o.order_id }),
        signal: controller.signal,
      });
      clearTimeout(timeoutId);
      res = r.ok
        ? await r.json().catch(() => ({}))
        : { success: false, ...(await r.json().catch(() => ({}))) };
    } catch {
      res = { success: false, error: 'Request timed out or network error' };
    }
    if (res && res.success) {
      setCloseMsg({ type: 'info', text: res.message });
    } else {
      setCloseMsg({ type: 'err', text: res?.detail || res?.error || 'Cancel failed' });
    }
    setCancelling(null);
    poll();
  };

  const uatSess = gw?.sessions?.uat;
  const uatLive = uat?.is_connected ?? uatSess?.live?.connected ?? null;
  // Per-book equity: NetLiquidation straight from the UAT paper session.
  // connected=false + data=null → render '—', never a fake $0.
  const netLiq = acct?.connected && acct?.data?.net_liquidation != null ? acct.data.net_liquidation : null;

  // Blotter = REAL session fills (ib.fills()) merged with DB rows (manual
  // ticket / endpoint-booked closes). Session fills win on (ticker|side|qty)
  // so an endpoint-booked close never prints twice.
  const dbFills = Array.isArray(blotter?.data) ? blotter.data : (Array.isArray(blotter) ? blotter : []);
  const ibFills = (sessionFills?.data || []).map(f => ({
    t: f.time, side: f.side, ticker: f.symbol, qty: f.qty, price: f.price, source: 'ibkr',
  }));
  const ibSeen = new Set(ibFills.map(f => `${f.ticker}|${(f.side || '').toUpperCase()}|${f.qty}`));
  const mergedDb = dbFills.filter(r => !ibSeen.has(`${r.ticker}|${(r.side || '').toUpperCase()}|${r.qty}`));
  const epochOf = (r) => {
    const iso = r.t || r.ts;
    if (!iso) return 0;
    return new Date(iso.endsWith('Z') || iso.includes('+') ? iso : iso + 'Z').getTime() || 0;
  };
  const fills = [...ibFills, ...mergedDb].sort((a, b) => epochOf(b) - epochOf(a));
  const working = openOrders?.data || [];
  const posRows = positions?.data || [];

  const tabs = [
    { id: 'positions', label: `Positions (${posRows.length})`, badge: positions && !positions.connected ? 'qr-chip-rose' : null, badgeText: 'PENDING' },
    { id: 'working',   label: `Working (${working.length})` },
    { id: 'fills',     label: `Fills (${fills.length})` },
    { id: 'session',   label: 'Session', badge: uatLive === false ? 'qr-chip-rose' : null, badgeText: 'DOWN' },
  ];

  return (
    <ExecScaffold
      mode="uat"
      book="paper_uat"
      stats={<>
        <ExecStat
          l="UAT Session"
          v={uatLive == null ? '…' : uatLive ? 'Connected' : 'Disconnected'}
          tone={uatLive == null ? 'text-slate-500' : uatLive ? 'text-emerald-400' : 'text-rose-400'}
        />
        <ExecStat l="Endpoint" v={uat ? `${uat.host}:${uat.port} · c${uat.client_id}` : '—'} tone="text-slate-400" />
        <ExecStat l="Account" v={uatLive ? (uat?.account || uatSess?.live?.account || '…') : '—'} tone="text-slate-400" />
        <ExecStat l="Net Liq" v={netLiq != null ? `$${Number(netLiq).toLocaleString(undefined, { maximumFractionDigits: 0 })}` : '—'} tone="text-slate-200" />
      </>}
    >
      <div className="qr-surface overflow-hidden">
        <ExecTabs
          tabs={tabs}
          active={tab}
          onChange={setTab}
          right={<>
            {lastRefresh && (
              <span className="text-[8px] text-slate-600 font-mono" title="Last status refresh (auto-polls every 15s)">
                updated {lastRefresh.toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
              </span>
            )}
            <button
              onClick={refresh}
              disabled={refreshing}
              title="Fetch the latest session status now (auto-polls every 15s)"
              className="px-2 py-0.5 rounded text-[9px] font-bold uppercase tracking-wide bg-slate-700/80 text-slate-200 hover:bg-slate-600 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
            >
              {refreshing ? 'Refreshing…' : '↻ Refresh'}
            </button>
            <span
              className={`qr-chip ${uatLive ? 'qr-chip-emerald' : 'qr-chip-rose'}`}
              title="Source: /api/execution/gateway + /api/ib/tws/uat/status + /api/ib/tws/uat/positions"
            >
              {uatLive ? 'LIVE' : 'PENDING'}
            </span>
          </>}
        />

        {/* Positions — real IBKR paper-account positions from the gateway
            session, never the DB book. PENDING when the session is down so an
            unreachable gateway never reads as a flat account. */}
        {tab === 'positions' && (
          !positions ? (
            <div className="py-6 text-center text-slate-600 text-[11px]">Loading UAT positions…</div>
          ) : !positions.connected ? (
            <div className="py-6 text-center text-[11px] text-slate-500">
              <span className="qr-chip qr-chip-rose mr-2">PENDING</span>
              Positions unavailable — UAT session disconnected. Connect on the Session tab, then ↻ Refresh.
            </div>
          ) : posRows.length === 0 ? (
            <div className="py-6 text-center text-slate-600 text-[11px]">
              Paper account {positions?.account || ''} is flat — no open positions at IBKR
            </div>
          ) : (
            <div className="overflow-x-auto max-h-72 overflow-y-auto">
              <table className="w-full">
                <thead className="qr-th-sticky">
                  <tr className="border-b border-white/[0.06]">
                    <th className="qr-label text-left  py-1 px-2">Ticker</th>
                    <th className="qr-label text-right py-1 px-2">Qty</th>
                    <th className="qr-label text-right py-1 px-2">Avg Cost</th>
                    <th className="qr-label text-right py-1 px-2">Mkt Price</th>
                    <th className="qr-label text-right py-1 px-2">Mkt Value</th>
                    <th className="qr-label text-right py-1 px-2">Unrl P&L</th>
                    <th className="qr-label text-right py-1 px-2"></th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/[0.04]">
                  {posRows.map((p, i) => (
                    <tr key={`${p.symbol}-${i}`} className="qr-tr-hover">
                      <td className="py-1 px-2">
                        <span className="text-[11px] font-mono text-white">{p.ticker}</span>
                        <span className="ml-1.5 text-[9px] text-slate-500">{p.exchange} · {p.currency}</span>
                      </td>
                      <td className="py-1 px-2 qr-num text-slate-300">{fmt(p.qty, 0)}</td>
                      <td className="py-1 px-2 qr-num text-slate-400">{fmt(p.avg_cost)}</td>
                      <td className="py-1 px-2 qr-num text-slate-300">{fmt(p.market_price)}</td>
                      <td className="py-1 px-2 qr-num text-slate-300">{fmt(p.market_value, 0)}</td>
                      <td className={`py-1 px-2 qr-num font-bold ${pnlCl(p.unrealized_pnl)}`}>{fmtSigned(p.unrealized_pnl)}</td>
                      <td className="py-1 px-2 text-right whitespace-nowrap">
                        <CloseButton
                          busy={closing === p.symbol}
                          disabled={closing != null}
                          title={`${p.qty > 0 ? 'SELL' : 'BUY'} ${Math.abs(p.qty)} ${p.ticker} @ MKT on the UAT session — flattens this position (real order, paper money)`}
                          onClick={() => closePosition(p)}
                        />
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {closeMsg && (
                <div className={`px-3 py-2 border-t border-white/[0.05] text-[10px] ${closeMsg.type === 'ok' ? 'text-emerald-400' : closeMsg.type === 'info' ? 'text-slate-300' : 'text-rose-400'}`}>
                  {closeMsg.text}
                </div>
              )}
            </div>
          )
        )}

        {/* Working — orders accepted at IBKR, pending execution, cancellable */}
        {tab === 'working' && (
          working.length === 0 ? (
            <div className="py-6 text-center text-slate-600 text-[11px]">No working orders · all clear</div>
          ) : (
            <div className="overflow-x-auto max-h-72 overflow-y-auto">
              <table className="w-full">
                <thead className="qr-th-sticky">
                  <tr className="border-b border-white/[0.06]">
                    <th className="qr-label text-left  py-1 px-2">Status</th>
                    <th className="qr-label text-right py-1 px-2">Side</th>
                    <th className="qr-label text-left  py-1 px-2">Ticker</th>
                    <th className="qr-label text-right py-1 px-2">Qty</th>
                    <th className="qr-label text-right py-1 px-2">Type · Order</th>
                    <th className="qr-label text-right py-1 px-2"></th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/[0.04]">
                  {working.map((o, i) => (
                    <tr key={`${o.order_id}-${i}`} className="qr-tr-hover">
                      <td className="py-1 px-2">
                        <span className="qr-chip qr-chip-slate" title="Order accepted at IBKR, waiting to execute (e.g. market closed)">
                          {o.status || 'WORKING'}
                        </span>
                      </td>
                      <td className="py-1 px-2 text-right">
                        <span className={`qr-chip ${o.action === 'BUY' ? 'qr-chip-emerald' : 'qr-chip-rose'}`}>{o.action}</span>
                      </td>
                      <td className="py-1 px-2 text-[11px] font-mono text-white">{o.symbol}</td>
                      <td className="py-1 px-2 qr-num text-slate-300">{o.qty}</td>
                      <td className="py-1 px-2 qr-num text-[10px] text-slate-400">{o.order_type} · #{o.order_id}</td>
                      <td className="py-1 px-2 text-right whitespace-nowrap">
                        <button
                          onClick={() => cancelOrder(o)}
                          disabled={cancelling != null}
                          title={`Cancel order ${o.order_id} on the UAT session (real cancel, paper money)`}
                          className="px-2 py-0.5 rounded text-[9px] font-bold uppercase tracking-wide bg-slate-700/80 text-slate-200 hover:bg-slate-600 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
                        >
                          {cancelling === o.order_id ? 'Cancelling…' : 'Cancel'}
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {closeMsg && (
                <div className={`px-3 py-2 border-t border-white/[0.05] text-[10px] ${closeMsg.type === 'ok' ? 'text-emerald-400' : closeMsg.type === 'info' ? 'text-slate-300' : 'text-rose-400'}`}>
                  {closeMsg.text}
                </div>
              )}
            </div>
          )
        )}

        {/* Fills — merged real session fills (ib.fills(), canonical) + DB
            blotter rows (manual ticket / endpoint-booked closes). */}
        {tab === 'fills' && (
          fills.length === 0 ? (
            <div className="py-6 text-center text-slate-600 text-[11px]">
              No UAT fills yet — fire one from the ticket on the right; it routes to the IBKR paper session and the fill appears here (source: ibkr)
            </div>
          ) : (
            <div className="overflow-x-auto max-h-72 overflow-y-auto">
              <table className="w-full">
                <thead className="qr-th-sticky">
                  <tr className="border-b border-white/[0.06]">
                    <th className="qr-label text-left  py-1 px-2">Time</th>
                    <th className="qr-label text-right py-1 px-2">Side</th>
                    <th className="qr-label text-left  py-1 px-2">Ticker</th>
                    <th className="qr-label text-right py-1 px-2">Qty</th>
                    <th className="qr-label text-right py-1 px-2">Price</th>
                    <th className="qr-label text-right py-1 px-2">Source</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/[0.04]">
                  {fills.map((r, i) => (
                    <tr key={`${r.t || r.ts}-${r.ticker}-${i}`} className="qr-tr-hover">
                      <td className="py-1 px-2 qr-num text-[10px] text-slate-400">{fmtTime(r.t || r.ts)}</td>
                      <td className="py-1 px-2 text-right">
                        <span className={`qr-chip ${(r.side || '').toUpperCase() === 'BUY' ? 'qr-chip-emerald' : 'qr-chip-rose'}`}>{r.side || '—'}</span>
                      </td>
                      <td className="py-1 px-2 text-[11px] font-mono text-white">{r.ticker || '—'}</td>
                      <td className="py-1 px-2 qr-num text-slate-300">{r.qty ?? '—'}</td>
                      <td className="py-1 px-2 qr-num text-slate-300">{r.price ?? '—'}</td>
                      <td className="py-1 px-2 qr-num text-[9px] text-slate-500">{r.source || '—'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )
        )}

        {/* Session — the UAT paper session is the ONLY session this book talks
            to. The primary/live session exists backend-side for the LIVE book
            but is not shown here: UAT orders never fall back to it. */}
        {tab === 'session' && (
          <div className="p-3.5 flex flex-col gap-2.5">
            <SessionRow
              name="uat"
              title="UAT Paper Session"
              note="IBKR paper account · real order routing, paper money · this book always fires here (book=paper_uat) · never falls back to the primary/live session"
              sess={uatSess ? { ...uatSess, host: uat?.host ?? uatSess.host, port: uat?.port ?? uatSess.port } : (uat ? { host: uat.host, port: uat.port, live: { client_id: uat.client_id } } : null)}
              liveConnected={uatLive}
              connectPath="/api/ib/tws/uat/connect"
              onConnected={poll}
            />
            {uatLive === false && (
              <div className="text-[9px] text-rose-400/90 leading-relaxed">
                UAT session disconnected — the manual ticket hard-fails (503) until it connects; orders never fall back to the primary/live session.
              </div>
            )}
          </div>
        )}
      </div>
    </ExecScaffold>
  );
};

export default PaperUatPanel;
