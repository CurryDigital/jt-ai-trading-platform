import React, { useState } from 'react';
import { fetchWithTimeout } from '../utils';

const ASSETS = ['STOCK', 'CRYPTO', 'FX'];
const MARKETS = ['US', 'HK'];

// Manual order ticket.
//  - sim / paper     -> POST /api/execution/manual-order (virtual books, DB ledger only)
//  - uat             -> POST /api/ib/place-order {book:'uat'} — REAL order on the
//                       dedicated IBKR paper session (paper money, hard 503 when down,
//                       never falls back to primary/live). Nothing is written to the
//                       blotter client-side; fills appear from ib.fills() (source: ibkr).
//  - live            -> POST /api/ib/place-order {book:'live'} — REAL order on the
//                       primary session (real money), confirm-gated.
export const ManualTicket = ({ book, prefill, onFilled }) => {
  const blank = { ticker: '', asset: 'STOCK', market: 'US', side: 'LONG', qty: '', entry: '' };
  const [f, setF] = useState(() => ({ ...blank, ...prefill }));
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState(null);

  const up = (k) => (e) => setF(s => ({ ...s, [k]: e.target.value }));

  const BOOK_LABEL = { sim: 'SIM', paper: 'PAPER', uat: 'UAT', paper_uat: 'UAT', live: 'LIVE' };
  const bookLabel = BOOK_LABEL[book] || (book || '').toUpperCase();
  const isReal = book === 'uat' || book === 'paper_uat' || book === 'live';
  const realMoney = book === 'live';

  const valid = f.ticker.trim() && Number(f.qty) > 0 && (isReal || Number(f.entry) > 0);

  const submit = async () => {
    if (!valid) return;
    const action = f.side === 'SHORT' ? 'SELL' : 'BUY';
    const symbol = f.ticker.trim().toUpperCase();

    if (isReal) {
      const ok = window.confirm(
        `Fire a REAL order on the ${realMoney ? 'LIVE account — REAL MONEY' : 'IBKR UAT paper account (paper money)'}?\n\n` +
        `${action} ${f.qty} ${symbol} @ MKT\n` +
        (realMoney
          ? `Routes to the primary session. This cannot be undone once filled.`
          : `Routes to the dedicated UAT session (book=uat) — never falls back to live.`)
      );
      if (!ok) return;
    }

    setBusy(true);
    setMsg(null);
    try {
      if (isReal) {
        // Raw fetch with a 45s budget: the backend waits up to ~30s for the fill
        // inside the IB thread, and error bodies carry the real reason.
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 45000);
        const res = await fetch('/api/ib/place-order', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ symbol, action, quantity: Number(f.qty), order_type: 'MKT', book }),
          signal: controller.signal,
        });
        clearTimeout(timeoutId);
        const body = await res.json().catch(() => ({}));
        if (res.ok && body.success) {
          const st = body.status || 'Submitted';
          setMsg({
            type: 'success',
            text: st === 'Filled'
              ? `FILLED — ${action} ${body.quantity} ${body.symbol} · order ${body.order_id} (${body.session} session)`
              : `${st} — ${action} ${body.quantity} ${body.symbol} · order ${body.order_id} working at IBKR (fills when the market opens; see Working orders)`,
          });
          setF(blank);
          onFilled?.(body);
        } else {
          setMsg({ type: 'error', text: body.detail || body.error || `Order failed (HTTP ${res.status})` });
        }
      } else {
        const res = await fetchWithTimeout('/api/execution/manual-order', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            book, ticker: symbol, market: f.market, asset: f.asset,
            side: f.side, qty: Number(f.qty), entry: Number(f.entry),
          }),
        });
        const body = await res.json().catch(() => ({}));
        if (res.ok) {
          setMsg({ type: 'success', text: `${body.status === 'accepted' ? 'Added' : body.status} — ${body.ticker} ${body.filled_qty} @ ${body.avg_price}` });
          setF(blank);
          onFilled?.(body);
        } else {
          setMsg({ type: 'error', text: body.detail?.error || body.detail || 'Manual order failed' });
        }
      }
    } catch (e) {
      setMsg({ type: 'error', text: e.name === 'AbortError' ? 'Timed out waiting for IBKR — check the session status before retrying' : (e.message || 'Network error') });
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="qr-surface overflow-hidden">
      <div className="px-3 py-2 border-b border-white/[0.05] flex items-center justify-between">
        <span className="text-[12px] font-bold text-white">Manual Ticket</span>
        <span title="This ticket always books to this tab's book — there is no global mode switch."
          className="flex items-center gap-1.5 text-[9px] text-slate-500">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
          Book <b className="text-slate-300">{bookLabel}</b>
        </span>
      </div>
      <div className="p-3 flex flex-col gap-2.5">
        <div className="grid grid-cols-[1.4fr_1fr] gap-2">
          <div>
            <label className="qr-label block mb-1">Symbol</label>
            <input value={f.ticker} onChange={up('ticker')} placeholder="AAPL" className="w-full box-border px-2 py-1.5 text-[11px] font-mono text-white bg-slate-900/50 border border-white/10 rounded outline-none" />
          </div>
          <div>
            <label className="qr-label block mb-1">Market</label>
            <select value={f.market} onChange={up('market')} disabled={isReal} className="w-full box-border px-2 py-1.5 text-[11px] font-mono text-white bg-slate-900/50 border border-white/10 rounded outline-none disabled:opacity-40">
              {MARKETS.map(m => <option key={m} value={m}>{m}</option>)}
            </select>
          </div>
        </div>
        {!isReal && (
          <div>
            <label className="qr-label block mb-1">Asset</label>
            <select value={f.asset} onChange={up('asset')} className="w-full box-border px-2 py-1.5 text-[11px] font-mono text-white bg-slate-900/50 border border-white/10 rounded outline-none">
              {ASSETS.map(a => <option key={a} value={a}>{a}</option>)}
            </select>
          </div>
        )}
        <div>
          <label className="qr-label block mb-1">Side</label>
          <div className="flex gap-0.5 p-0.5 rounded-md bg-slate-900/50 border border-white/10">
            {[['LONG', 'BUY', 'bg-emerald-600'], ['SHORT', 'SELL', 'bg-rose-600']].map(([k, l, bg]) => (
              <button key={k} onClick={() => setF(s => ({ ...s, side: k }))} className={`flex-1 py-1 rounded text-[10px] font-bold ${f.side === k ? `${bg} text-white` : 'text-slate-400'}`}>{l}</button>
            ))}
          </div>
        </div>
        <div className="grid grid-cols-2 gap-2">
          <div>
            <label className="qr-label block mb-1">Qty</label>
            <input value={f.qty} onChange={up('qty')} inputMode="decimal" placeholder="100" className="w-full box-border px-2 py-1.5 text-[11px] font-mono text-white bg-slate-900/50 border border-white/10 rounded outline-none" />
          </div>
          {!isReal && (
            <div>
              <label className="qr-label block mb-1">Entry</label>
              <input value={f.entry} onChange={up('entry')} inputMode="decimal" placeholder="0.00" className="w-full box-border px-2 py-1.5 text-[11px] font-mono text-white bg-slate-900/50 border border-white/10 rounded outline-none" />
            </div>
          )}
        </div>
        <button onClick={submit} disabled={!valid || busy} className="qr-btn-primary justify-center disabled:opacity-40">
          {busy ? (isReal ? 'Firing…' : 'Adding…') : isReal ? 'Fire Order @ MKT' : 'Add to Book'}
        </button>
        {msg && <div className={`text-[10px] ${msg.type === 'success' ? 'text-emerald-400' : 'text-rose-400'}`}>{msg.text}</div>}
        <div className="text-[9px] text-slate-500 leading-relaxed">
          {isReal
            ? (realMoney
              ? 'REAL order on the primary session — confirm-gated. Fills come back from IBKR, nothing is bookkept client-side.'
              : 'Real order routing to the IBKR paper session — confirm-gated. Fills appear from the broker (source: ibkr); nothing is written to the blotter until IBKR reports it.')
            : 'Manual fills roll straight into the blotter and Open P&L.'}
        </div>
      </div>
    </div>
  );
};

export default ManualTicket;
