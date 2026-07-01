import React, { useState } from 'react';

const ASSETS = ['STOCK', 'CRYPTO', 'FX'];
const MARKETS = ['US', 'HK'];

// Manual order ticket — posts to /api/execution/manual-order (gold.manual_orders).
// Shared by the Live and Paper books; `book` decides which blotter the fill lands in.
export const ManualTicket = ({ book, globalMode, prefill, onFilled }) => {
  const blank = { ticker: '', asset: 'STOCK', market: 'US', side: 'LONG', qty: '', entry: '' };
  const [f, setF] = useState(() => ({ ...blank, ...prefill }));
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState(null);

  const up = (k) => (e) => setF(s => ({ ...s, [k]: e.target.value }));
  const valid = f.ticker.trim() && Number(f.qty) > 0 && Number(f.entry) > 0;

  const modeLabel = globalMode === 'LIVE_TRADING' ? 'LIVE' : globalMode === 'PAPER_TRADING' ? 'PAPER' : 'SIM';
  const routesHere = book === 'live' ? modeLabel === 'LIVE' : modeLabel !== 'LIVE';

  const submit = async () => {
    if (!valid) return;
    setBusy(true);
    setMsg(null);
    try {
      const res = await fetch('/api/execution/manual-order', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          book, ticker: f.ticker.trim().toUpperCase(), market: f.market, asset: f.asset,
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
    } catch (e) {
      setMsg({ type: 'error', text: e.message || 'Network error' });
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="qr-surface overflow-hidden">
      <div className="px-3 py-2 border-b border-white/[0.05] flex items-center justify-between">
        <span className="text-[12px] font-bold text-white">Manual Ticket</span>
        <span title="The global MODE (top ribbon) decides where new algo orders route. This ticket always books to this tab's book."
          className="flex items-center gap-1.5 text-[9px] text-slate-500">
          <span className={`w-1.5 h-1.5 rounded-full ${routesHere ? 'bg-emerald-400' : 'bg-slate-600'}`} />
          Mode <b className="text-slate-300">{modeLabel}</b>
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
            <select value={f.market} onChange={up('market')} className="w-full box-border px-2 py-1.5 text-[11px] font-mono text-white bg-slate-900/50 border border-white/10 rounded outline-none">
              {MARKETS.map(m => <option key={m} value={m}>{m}</option>)}
            </select>
          </div>
        </div>
        <div>
          <label className="qr-label block mb-1">Asset</label>
          <select value={f.asset} onChange={up('asset')} className="w-full box-border px-2 py-1.5 text-[11px] font-mono text-white bg-slate-900/50 border border-white/10 rounded outline-none">
            {ASSETS.map(a => <option key={a} value={a}>{a}</option>)}
          </select>
        </div>
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
          <div>
            <label className="qr-label block mb-1">Entry</label>
            <input value={f.entry} onChange={up('entry')} inputMode="decimal" placeholder="0.00" className="w-full box-border px-2 py-1.5 text-[11px] font-mono text-white bg-slate-900/50 border border-white/10 rounded outline-none" />
          </div>
        </div>
        <button onClick={submit} disabled={!valid || busy} className="qr-btn-primary justify-center disabled:opacity-40">
          {busy ? 'Adding…' : 'Add to Book'}
        </button>
        {msg && <div className={`text-[10px] ${msg.type === 'success' ? 'text-emerald-400' : 'text-rose-400'}`}>{msg.text}</div>}
        <div className="text-[9px] text-slate-500 leading-relaxed">Manual fills roll straight into the blotter and Open P&L.</div>
      </div>
    </div>
  );
};

export default ManualTicket;
