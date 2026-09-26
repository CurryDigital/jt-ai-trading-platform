import React, { useState } from 'react';
import { ExecScaffold, ExecStat, ExecTabs, CloseButton } from './ExecScaffold';
import { PositionsByReturn, normManualPosition } from './BookPositions';
import { fmt, fmtK, pnlCl, api, usePoll, fetchWithTimeout } from '../../utils';

// Execution > Manual book (2026-09-25 goal): discretionary positions entered
// by hand — no strategy attribution, no IBKR routing anywhere. Data model is
// gold.manual_positions via /api/execution/manual/positions; open rows are
// marked with the same quote source as the Paper book (silver.unified_prices
// → gold.daily_ohlcv fallback), computed server-side. Siloed by design: the
// manual book does NOT feed Command aggregates or NAV.
//
// 2026-09-25 pm: split into per-market books (US / HK / CN side by side,
// stacked on narrow screens) so per-region performance evaluates separately —
// each panel carries its own summary strip in its NATIVE currency
// (USD / HKD / CNY); the HK book marks in HKD, the CN book in CNY, the US
// book in USD, and a combined total would mix FX silently. All three region
// panels render always (empty regions show an honest empty state) so the
// per-region structure is visible before the first HK/CN entry.

const TODAY = new Date().toISOString().slice(0, 10);

const CCY = {
  US: { sign: '$', code: 'USD', title: 'US Stocks' },
  HK: { sign: 'HK$', code: 'HKD', title: 'HK Stocks' },
  CN: { sign: 'CN¥', code: 'CNY', title: 'CN Stocks' },
};
const MARKETS = ['US', 'HK', 'CN'];

// Symbol suffix implies the market: .HK → HK, .SS/.SZ (Shanghai/Shenzhen) → CN.
const marketForSymbol = (sym) => {
  const s = (sym || '').trim().toUpperCase();
  if (/\.HK$/.test(s)) return 'HK';
  if (/\.(SS|SZ)$/.test(s)) return 'CN';
  return null;
};

const fmtCcy = (n, sign) => n == null ? '—'
  : `${n < 0 ? '-' : '+'}${sign}${Math.abs(n).toLocaleString(undefined, { maximumFractionDigits: 0 })}`;

const inputCls = 'w-full bg-slate-900/70 border border-white/[0.08] rounded px-2 py-1 text-[11px] text-white placeholder-slate-600 focus:outline-none focus:border-white/[0.2]';
const labelCls = 'qr-label block mb-0.5';

const AddPositionForm = ({ onAdded }) => {
  const [form, setForm] = useState({
    symbol: '', market: 'US', side: 'LONG', qty: '', entry_price: '', entry_date: TODAY, notes: '',
  });
  const [state, setState] = useState(null); // { busy, msg: { type, text } }
  const set = (k) => (e) => {
    const v = e.target.value;
    setForm((f) => ({
      ...f, [k]: v,
      // Symbol suffix implies the market — .HK → HK, .SS/.SZ → CN.
      ...(k === 'symbol' && marketForSymbol(v) ? { market: marketForSymbol(v) } : {}),
    }));
  };

  const submit = async () => {
    setState({ busy: true, msg: null });
    try {
      const res = await fetchWithTimeout('/api/execution/manual/positions', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          symbol: form.symbol.trim(),
          market: form.market,
          asset_type: 'STOCK',
          side: form.side,
          qty: Number(form.qty),
          entry_price: Number(form.entry_price),
          entry_date: form.entry_date,
          notes: form.notes.trim() || null,
        }),
      }, 20000);
      const body = await res.json().catch(() => ({}));
      if (res.ok) {
        setState({ busy: false, msg: { type: 'success', text: `Added ${body.symbol || form.symbol.toUpperCase()} — row #${body.id}` } });
        setForm({ symbol: '', market: form.market, side: form.side, qty: '', entry_price: '', entry_date: TODAY, notes: '' });
        onAdded?.();
      } else {
        setState({ busy: false, msg: { type: 'error', text: body.detail || `Add failed (${res.status})` } });
      }
    } catch (e) {
      setState({ busy: false, msg: { type: 'error', text: e.message || 'Network error' } });
    }
  };

  const ready = form.symbol.trim() && Number(form.qty) > 0 && Number(form.entry_price) > 0 && form.entry_date;
  return (
    <div className="qr-surface overflow-hidden">
      <div className="px-3 py-2 border-b border-white/[0.05] flex items-center justify-between">
        <span className="qr-label">Add Position</span>
        <span className="text-[9px] text-slate-600">ledger write only · no IBKR</span>
      </div>
      <div className="p-3 space-y-2">
        <div>
          <label className={labelCls}>Symbol</label>
          <input className={inputCls} placeholder="AAPL · 0700.HK · 600519.SS" value={form.symbol} onChange={set('symbol')} />
        </div>
        <div className="grid grid-cols-2 gap-2">
          <div>
            <label className={labelCls}>Market</label>
            <select className={inputCls} value={form.market} onChange={set('market')}>
              {MARKETS.map(mk => <option key={mk} value={mk}>{mk}</option>)}
            </select>
          </div>
          <div>
            <label className={labelCls}>Side</label>
            <select className={inputCls} value={form.side} onChange={set('side')}>
              <option value="LONG">LONG</option>
              <option value="SHORT">SHORT</option>
            </select>
          </div>
        </div>
        <div className="grid grid-cols-2 gap-2">
          <div>
            <label className={labelCls}>Qty</label>
            <input className={inputCls} type="number" min="0" step="any" placeholder="100" value={form.qty} onChange={set('qty')} />
          </div>
          <div>
            <label className={labelCls}>Entry Price</label>
            <input className={inputCls} type="number" min="0" step="any" placeholder="0.00" value={form.entry_price} onChange={set('entry_price')} />
          </div>
        </div>
        <div>
          <label className={labelCls}>Entry Date</label>
          <input className={inputCls} type="date" max={TODAY} value={form.entry_date} onChange={set('entry_date')} />
        </div>
        <div>
          <label className={labelCls}>Notes</label>
          <input className={inputCls} placeholder="optional — thesis, source, reminder" value={form.notes} onChange={set('notes')} />
        </div>
        <button
          onClick={submit}
          disabled={!ready || state?.busy}
          className="w-full px-2 py-1.5 rounded text-[11px] font-bold bg-slate-700/80 text-slate-100 hover:bg-slate-600 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
        >
          {state?.busy ? 'Adding…' : 'Add Position'}
        </button>
        {state?.msg && (
          <div className={`text-[10px] ${state.msg.type === 'success' ? 'text-emerald-400' : 'text-rose-400'}`}>
            {state.msg.text}
          </div>
        )}
      </div>
    </div>
  );
};

// Small exit-legs form — opens from a row's Close button. Prefills the exit
// price with the latest mark; submit writes exit legs and realized P&L
// server-side. No order routing.
const CloseForm = ({ row, onDone, onCancel }) => {
  const p = row.raw;
  const meta = CCY[p.market] || CCY.US;
  const [exitPrice, setExitPrice] = useState(p.current_price != null ? String(p.current_price) : '');
  const [exitDate, setExitDate] = useState(TODAY);
  const [state, setState] = useState(null);

  const submit = async () => {
    setState({ busy: true, msg: null });
    try {
      const res = await fetchWithTimeout(`/api/execution/manual/positions/${p.id}/close`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ exit_price: Number(exitPrice), exit_date: exitDate }),
      }, 20000);
      const body = await res.json().catch(() => ({}));
      if (res.ok) {
        onDone?.(`Closed ${p.symbol} · realized ${fmtCcy(body.realized_pnl, meta.sign)}`);
      } else {
        setState({ busy: false, msg: body.detail || `Close failed (${res.status})` });
      }
    } catch (e) {
      setState({ busy: false, msg: e.message || 'Network error' });
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60" onClick={onCancel}>
      <div className="qr-surface w-72 p-3 space-y-2" onClick={(e) => e.stopPropagation()}>
        <div className="flex items-center justify-between">
          <span className="qr-label">Close Position</span>
          <button onClick={onCancel} className="text-slate-500 hover:text-slate-300 text-[11px] px-1">✕</button>
        </div>
        <div className="text-[11px] text-white font-mono">{p.symbol}
          <span className="ml-2 text-[9px] text-slate-500">{p.side} {fmt(p.qty, 0)} @ {meta.sign}{fmt(p.entry_price)} · {p.entry_date}</span>
        </div>
        <div>
          <label className={labelCls}>Exit Price ({meta.code})</label>
          <input className={inputCls} type="number" min="0" step="any" value={exitPrice} onChange={(e) => setExitPrice(e.target.value)} />
        </div>
        <div>
          <label className={labelCls}>Exit Date</label>
          <input className={inputCls} type="date" min={p.entry_date} max={TODAY} value={exitDate} onChange={(e) => setExitDate(e.target.value)} />
        </div>
        <button
          onClick={submit}
          disabled={!(Number(exitPrice) > 0) || !exitDate || state?.busy}
          className="w-full px-2 py-1.5 rounded text-[11px] font-bold bg-slate-700/80 text-slate-100 hover:bg-slate-600 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
        >
          {state?.busy ? 'Closing…' : 'Close Position'}
        </button>
        {state?.msg && <div className="text-[10px] text-rose-400">{state.msg}</div>}
      </div>
    </div>
  );
};

const MiniTile = ({ label, value, tone, title }) => (
  <div className="rounded bg-white/[0.03] px-1.5 py-1 min-w-0" title={title}>
    <div className="qr-label">{label}</div>
    <div className={`font-mono text-[11px] font-bold leading-tight truncate ${tone || 'text-white'}`}>{value}</div>
  </div>
);

const ClosedTable = ({ rows, sign }) => (
  <div className="overflow-x-auto max-h-96 overflow-y-auto">
    <table className="w-full">
      <thead className="qr-th-sticky">
        <tr className="border-b border-white/[0.06]">
          {['Symbol', 'Side', 'Qty', 'Entry', 'Exit', 'Entry Date', 'Exit Date', 'Days', 'Realized P&L'].map(h =>
            <th key={h} className="qr-label text-right py-1 px-2 first:text-left">{h}</th>)}
        </tr>
      </thead>
      <tbody className="divide-y divide-white/[0.04]">
        {rows.map((p) => (
          <tr key={p.id} className="qr-tr-hover">
            <td className="py-1 px-2">
              <span className="text-[11px] font-mono text-white">{p.symbol}</span>
              {p.notes && <span className="ml-1.5 text-[9px] text-slate-500">{p.notes}</span>}
            </td>
            <td className="py-1 px-2 text-right">
              <span className={`qr-chip ${p.side === 'SHORT' ? 'qr-chip-rose' : 'qr-chip-emerald'}`}>{p.side}</span>
            </td>
            <td className="py-1 px-2 qr-num text-slate-300">{fmt(p.qty, 0)}</td>
            <td className="py-1 px-2 qr-num text-slate-400">{sign}{fmt(p.entry_price)}</td>
            <td className="py-1 px-2 qr-num text-slate-300">{p.exit_price != null ? `${sign}${fmt(p.exit_price)}` : '—'}</td>
            <td className="py-1 px-2 qr-num text-slate-400 text-[10px]">{p.entry_date}</td>
            <td className="py-1 px-2 qr-num text-slate-400 text-[10px]">{p.exit_date}</td>
            <td className="py-1 px-2 qr-num text-slate-400">{p.held_days != null ? `${p.held_days}d` : '—'}</td>
            <td className={`py-1 px-2 qr-num font-bold ${pnlCl(p.realized_pnl)}`}>{p.realized_pnl != null ? fmtCcy(p.realized_pnl, sign) : '—'}</td>
          </tr>
        ))}
      </tbody>
    </table>
  </div>
);

// One market book: summary strip in native currency + Positions / Closed tabs.
const MarketBook = ({ market, open, closed, summary, onCloseRow }) => {
  const [tab, setTab] = useState('open');
  const meta = CCY[market] || { sign: '$', code: market, title: `${market} Stocks` };
  const s = summary || {};
  const rows = open.map(normManualPosition);
  const tabs = [
    { id: 'open',   label: `Positions (${open.length})` },
    { id: 'closed', label: `Closed (${closed.length})` },
  ];
  return (
    <div className="qr-surface overflow-hidden">
      <div className="px-3 py-2 border-b border-white/[0.05] flex items-center justify-between">
        <span className="qr-label">{meta.title}</span>
        <span className="text-[9px] text-slate-600">values in {meta.code}</span>
      </div>
      <div className="px-2 pt-2 grid grid-cols-4 sm:grid-cols-7 gap-1">
        <MiniTile label="YTD P&L" value={fmtCcy(s.ytd_pnl, meta.sign)} tone={pnlCl(s.ytd_pnl)} title="Realized since Jan 1" />
        <MiniTile label="Today" value={s.today ? fmtCcy(s.today.pnl, meta.sign) : '—'} tone={pnlCl(s.today?.pnl)} title={s.today ? `${s.today.trades} exits today` : 'No exits today'} />
        <MiniTile label="Win Rate" value={s.win_rate != null ? `${s.win_rate}%` : '—'} title="Share of closed trades with positive realized P&L" />
        <MiniTile label="Closed" value={s.closed ?? 0} tone="text-slate-300" />
        <MiniTile label="Open" value={s.open ?? open.length} tone="text-slate-300" />
        <MiniTile label="Cum P&L" value={fmtCcy(s.cum_pnl, meta.sign)} tone={pnlCl(s.cum_pnl)} title="All-time realized P&L" />
        <MiniTile label="Unrealized" value={fmtCcy(s.unrealized_pnl, meta.sign)} tone={pnlCl(s.unrealized_pnl)} title="Open book marked to latest close" />
      </div>
      <ExecTabs tabs={tabs} active={tab} onChange={setTab} />
      {tab === 'open' ? (
        open.length === 0 ? (
          <div className="py-6 text-center text-slate-600 text-[11px]">No open {market} positions</div>
        ) : (
          <div className="p-2 space-y-2">
            <PositionsByReturn
              rows={rows}
              renderAction={(r) => (
                <CloseButton onClick={() => onCloseRow(r)} title="Record exit legs — ledger write only, no order routed" />
              )}
            />
          </div>
        )
      ) : (
        closed.length === 0 ? (
          <div className="py-6 text-center text-slate-600 text-[11px]">No closed {market} trades yet</div>
        ) : (
          <ClosedTable rows={closed} sign={meta.sign} />
        )
      )}
    </div>
  );
};

export const ManualPanel = () => {
  const [data, setData] = useState(null);
  const [closing, setClosing] = useState(null);   // normalized row being closed
  const [notice, setNotice] = useState(null);     // { type, text }

  const load = async () => {
    const res = await api.get('/api/execution/manual/positions');
    if (res) setData(res);
  };
  usePoll(load, 60000);

  const open = data?.open || [];
  const closed = data?.closed || [];
  const summary = data?.summary || {};
  const byMarket = data?.summary_by_market || {};
  // Render all three region books always (empty regions show an honest empty
  // state) — plus any unexpected legacy market value defensively appended.
  const markets = [...new Set([...MARKETS,
    ...open.map(p => p.market), ...closed.map(p => p.market)])];

  return (
    <>
      <ExecScaffold
        mode="manual"
        book="manual"
        hideTicket
        railExtra={<AddPositionForm onAdded={load} />}
        stats={<>
          <ExecStat l="Open" v={summary.open ?? '—'} tone="text-slate-300" />
          <ExecStat l="Closed" v={summary.closed ?? '—'} tone="text-slate-300" />
          <ExecStat l="Win Rate" v={summary.win_rate != null ? `${summary.win_rate}%` : '—'} />
        </>}
      >
        {notice && (
          <div className={`qr-surface px-3 py-1.5 text-[10px] ${notice.type === 'success' ? 'text-emerald-400' : 'text-rose-400'}`}>
            {notice.text}
          </div>
        )}
        <div className="flex items-center justify-end px-1">
          <span className="text-[9px] text-slate-600">marked to latest close · same quote source as Paper · per-market summaries in native currency (US = USD · HK = HKD · CN = CNY) · siloed — not in Command totals</span>
        </div>
        {!data ? (
          <div className="qr-surface py-6 text-center text-slate-600 text-[11px]">Loading…</div>
        ) : (
          <div className={`grid grid-cols-1 gap-3 ${markets.length > 2 ? 'xl:grid-cols-2 2xl:grid-cols-3' : markets.length > 1 ? 'xl:grid-cols-2' : ''} items-start`}>
            {markets.map((mk) => (
              <MarketBook
                key={mk}
                market={mk}
                open={open.filter(p => p.market === mk)}
                closed={closed.filter(p => p.market === mk)}
                summary={byMarket[mk]}
                onCloseRow={setClosing}
              />
            ))}
          </div>
        )}
      </ExecScaffold>
      {closing && (
        <CloseForm
          row={closing}
          onCancel={() => setClosing(null)}
          onDone={(text) => { setClosing(null); setNotice({ type: 'success', text }); load(); }}
        />
      )}
    </>
  );
};

export default ManualPanel;
