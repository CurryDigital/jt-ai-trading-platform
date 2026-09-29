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
// 2026-09-25 pm: split into per-market books (US / HK side by side, stacked
// on narrow screens) so per-region performance evaluates separately — each
// panel carries its own summary strip in its NATIVE currency (USD / HKD);
// a combined total would mix FX silently. Both region panels render always
// (empty regions show an honest empty state).
//
// 2026-09-26: CN support exists in the BACKEND (market=CN validates; .SS/.SZ
// tickers mark fine) but the UI shows US + HK only, per user. Any unexpected
// market value in the ledger still gets a defensive extra panel — a position
// must never vanish. Each book also carries a monthly realized-P&L heatmap
// (backend monthly_by_market, realized by exit month, native currency).

const TODAY = new Date().toISOString().slice(0, 10);

const CCY = {
  US: { sign: '$', code: 'USD', title: 'US Stocks' },
  HK: { sign: 'HK$', code: 'HKD', title: 'HK Stocks' },
  CN: { sign: 'CN¥', code: 'CNY', title: 'CN Stocks' },
};
const MARKETS = ['US', 'HK'];

// Symbol suffix implies the market: .HK → HK.
const marketForSymbol = (sym) => {
  const s = (sym || '').trim().toUpperCase();
  if (/\.HK$/.test(s)) return 'HK';
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
      // Symbol suffix implies the market — .HK → HK.
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
          <input className={inputCls} placeholder="AAPL · 0700.HK" value={form.symbol} onChange={set('symbol')} />
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

  // Purge (2026-09-29, per user): delete the ledger row entirely so it is
  // never recognized as a closed trade — for testing tickers. Hard delete,
  // confirm-gated; no order routing.
  const purge = async () => {
    if (!window.confirm(`Purge ${p.symbol} #${p.id}? The ledger row is deleted entirely — it will NOT be recorded as a closed trade.`)) return;
    setState({ busy: true, msg: null });
    try {
      const res = await fetchWithTimeout(`/api/execution/manual/positions/${p.id}`, { method: 'DELETE' }, 20000);
      const body = await res.json().catch(() => ({}));
      if (res.ok) {
        onDone?.(`Purged ${p.symbol} — ledger row deleted, not recorded as closed`);
      } else {
        setState({ busy: false, msg: body.detail || `Purge failed (${res.status})` });
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
        <button
          onClick={purge}
          disabled={state?.busy}
          className="w-full text-center text-[10px] text-rose-400/80 hover:text-rose-300 disabled:opacity-40 transition-colors"
          title="Delete this ledger row entirely — it will NOT be recorded as a closed trade. For testing tickers."
        >
          Purge record — delete, no closed entry kept
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

// Monthly realized-P&L heatmap (2026-09-26, per user) — years × months grid
// with a YTD column, realized P&L by EXIT month in the book's native
// currency (backend monthly_by_market). '·' = no closed trades that month
// (never a fake $0); unrealized is never mixed in. Cells are signed text
// (emerald/rose via pnlCl) on neutral slate — heat comes from sign, not hue.
const MONTH_LETTERS = ['J', 'F', 'M', 'A', 'M', 'J', 'J', 'A', 'S', 'O', 'N', 'D'];
const MONTH_NAMES = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

const fmtCell = (v) => v == null ? '·'
  : `${v < 0 ? '-' : '+'}${Math.abs(v) >= 1e6 ? `${(Math.abs(v) / 1e6).toFixed(1)}M`
    : Math.abs(v) >= 1e3 ? `${(Math.abs(v) / 1e3).toFixed(1)}K`
    : Math.abs(v).toFixed(0)}`;

const MonthlyHeatmap = ({ data, sign, code }) => {
  const cells = data || {};
  const thisYear = new Date().getFullYear();
  const years = [...new Set([thisYear, ...Object.keys(cells).map(k => +k.slice(0, 4))])].sort((a, b) => b - a);
  const hasAny = Object.values(cells).some(c => c && c.pnl != null);
  return (
    <div className="px-2 pt-2">
      <div className="flex items-center justify-between pb-1">
        <span className="qr-label">Monthly Realized P&amp;L</span>
        <span className="text-[9px] text-slate-600" title={`Realized P&L grouped by exit month, in ${code}. Unrealized P&L on open positions is never mixed in; '·' means no closed trades that month.`}>
          {hasAny ? `by exit month · ${code}` : `no closed trades yet · ${code}`}
        </span>
      </div>
      <table className="w-full table-fixed">
        <thead>
          <tr className="border-b border-white/[0.06]">
            <th className="qr-label text-left py-0.5 pr-1 w-8">YR</th>
            {MONTH_LETTERS.map((m, i) => <th key={`${m}-${i}`} className="qr-label text-right py-0.5 px-0.5">{m}</th>)}
            <th className="qr-label text-right py-0.5 pl-1 w-10">YTD</th>
          </tr>
        </thead>
        <tbody>
          {years.map((y) => {
            const months = MONTH_LETTERS.map((_, i) => cells[`${y}-${String(i + 1).padStart(2, '0')}`] || null);
            const ytd = months.reduce((s, c) => s + (c && c.pnl != null ? c.pnl : 0), 0);
            const ytdAny = months.some(c => c && c.pnl != null);
            return (
              <tr key={y} className="border-b border-white/[0.03] last:border-0">
                <td className="py-0.5 pr-1 font-mono text-[10px] text-slate-400">{y}</td>
                {months.map((c, i) => (
                  <td key={i}
                    className={`py-0.5 px-0.5 text-right font-mono text-[10px] ${c && c.pnl != null ? pnlCl(c.pnl) : 'text-slate-700'}`}
                    title={c ? `${MONTH_NAMES[i]} ${y} · ${c.n} exit${c.n === 1 ? '' : 's'} · ${c.pnl != null ? fmtCcy(c.pnl, sign) : '—'}` : `${MONTH_NAMES[i]} ${y} · no closed trades`}>
                    {c && c.pnl != null ? fmtCell(c.pnl) : '·'}
                  </td>
                ))}
                <td className={`py-0.5 pl-1 text-right font-mono text-[10px] font-bold ${ytdAny ? pnlCl(ytd) : 'text-slate-700'}`}
                  title={ytdAny ? `${y} realized P&L · ${fmtCcy(ytd, sign)}` : `${y} · no closed trades`}>
                  {ytdAny ? fmtCell(ytd) : '·'}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
};

// Unrealized P&L by month-end mark (2026-09-26, per user) — one bar per
// calendar month from the oldest open position's entry month to now; the
// current month marks at the latest close, past months at month-end close
// (same quote source as the live marks). Open book only, native currency.
// Bars are emerald/rose by SIGN (signed-value convention); height is
// relative to the max |month| in the visible series, exact value on hover.
const UnrealizedMonthlyChart = ({ data, sign, code }) => {
  const cells = data || {};
  const keys = Object.keys(cells).sort();
  if (!keys.length) return null;
  const now = new Date();
  const curYm = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`;
  const seq = [];
  {
    let [y, m] = keys[0].split('-').map(Number);
    while (`${y}-${String(m).padStart(2, '0')}` <= curYm && seq.length < 240) {
      seq.push(`${y}-${String(m).padStart(2, '0')}`);
      m += 1; if (m === 13) { y += 1; m = 1; }
    }
  }
  const maxAbs = Math.max(...seq.map(k => Math.abs(cells[k] ?? 0)), 1e-9);
  const cur = cells[curYm];
  return (
    <div className="px-2 pt-2">
      <div className="flex items-center justify-between pb-1">
        <span className="qr-label">Unrealized P&amp;L · Monthly</span>
        <span className={`text-[9px] font-mono ${cur != null ? pnlCl(cur) : 'text-slate-600'}`}
          title={`Open book marked at each month-end close (current month = latest close), in ${code}. Reconstructed from daily closes — same quote source as the live marks.`}>
          {cur != null ? `now ${fmtCcy(cur, sign)}` : `month-end marks · ${code}`}
        </span>
      </div>
      <div className="flex items-stretch gap-px h-14">
        {seq.map((k) => {
          const v = cells[k];
          const h = v != null ? Math.max(Math.abs(v) / maxAbs * 50, 2) : 0;
          const [y, m] = k.split('-').map(Number);
          return (
            <div key={k} className="relative flex-1 min-w-0"
              title={v != null ? `${MONTH_NAMES[m - 1]} ${y} · ${fmtCcy(v, sign)}` : `${MONTH_NAMES[m - 1]} ${y} · no mark`}>
              <div className="absolute left-0 right-0 top-1/2 border-t border-white/[0.08]" />
              {v != null && (
                <div className={`absolute left-0 right-0 mx-px ${v >= 0 ? 'bottom-1/2 bg-emerald-500/40' : 'top-1/2 bg-rose-500/40'}`}
                  style={{ height: `${h}%` }} />
              )}
            </div>
          );
        })}
      </div>
      <div className="flex gap-px">
        {seq.map((k) => {
          const [y, m] = k.split('-').map(Number);
          return (
            <div key={k} className="flex-1 min-w-0 text-center font-mono text-[8px] text-slate-600">
              {MONTH_LETTERS[m - 1]}{m === 1 || k === seq[0] ? <span className="text-slate-700">{`'${String(y).slice(2)}`}</span> : null}
            </div>
          );
        })}
      </div>
    </div>
  );
};

const ClosedTable = ({ rows, sign }) => (
  <div className="max-h-96 overflow-y-auto">
    <table className="w-full">
      <thead className="qr-th-sticky">
        <tr className="border-b border-white/[0.06]">
          {['Symbol', 'Side', 'Qty', 'Entry', 'Exit', 'Entry Date', 'Exit Date', 'Days', 'Realized P&L'].map(h =>
            <th key={h} className="qr-label text-right py-1 px-1 first:text-left">{h}</th>)}
        </tr>
      </thead>
      <tbody className="divide-y divide-white/[0.04]">
        {rows.map((p) => (
          <tr key={p.id} className="qr-tr-hover">
            <td className="py-1 px-1">
              <span className="text-[11px] font-mono text-white">{p.symbol}</span>
              {p.notes && <span className="block text-[9px] text-slate-500 leading-tight truncate max-w-[110px]" title={p.notes}>{p.notes}</span>}
            </td>
            <td className="py-1 px-1 text-right">
              <span className={`qr-chip ${p.side === 'SHORT' ? 'qr-chip-rose' : 'qr-chip-emerald'}`}>{p.side}</span>
            </td>
            <td className="py-1 px-1 qr-num text-slate-300">{fmt(p.qty, 0)}</td>
            <td className="py-1 px-1 qr-num text-slate-400">{fmt(p.entry_price)}</td>
            <td className="py-1 px-1 qr-num text-slate-300">{p.exit_price != null ? fmt(p.exit_price) : '—'}</td>
            <td className="py-1 px-1 qr-num text-slate-400 text-[10px] whitespace-nowrap">{p.entry_date}</td>
            <td className="py-1 px-1 qr-num text-slate-400 text-[10px] whitespace-nowrap">{p.exit_date}</td>
            <td className="py-1 px-1 qr-num text-slate-400">{p.held_days != null ? `${p.held_days}d` : '—'}</td>
            <td className={`py-1 px-1 qr-num font-bold whitespace-nowrap ${pnlCl(p.realized_pnl)}`}>{p.realized_pnl != null ? fmtCcy(p.realized_pnl, sign) : '—'}</td>
          </tr>
        ))}
      </tbody>
    </table>
  </div>
);

// One market book: summary strip + monthly realized heatmap + unrealized
// monthly chart in native currency + Positions / Closed tabs.
const MarketBook = ({ market, open, closed, summary, monthly, unrealMonthly, onCloseRow }) => {
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
      <MonthlyHeatmap data={monthly} sign={meta.sign} code={meta.code} />
      <UnrealizedMonthlyChart data={unrealMonthly} sign={meta.sign} code={meta.code} />
      <ExecTabs tabs={tabs} active={tab} onChange={setTab} />
      {tab === 'open' ? (
        open.length === 0 ? (
          <div className="py-6 text-center text-slate-600 text-[11px]">No open {market} positions</div>
        ) : (
          <div className="p-2 space-y-2">
            <PositionsByReturn
              rows={rows}
              dense
              sign={meta.sign}
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
  const monthlyByMarket = data?.monthly_by_market || {};
  const unrealMonthlyByMarket = data?.unrealized_monthly_by_market || {};
  // Render the US + HK region books always (empty regions show an honest
  // empty state) — plus any unexpected legacy market value defensively
  // appended so a ledger row can never vanish from view.
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
          <span className="text-[9px] text-slate-600">marked to latest close · same quote source as Paper · per-market summaries in native currency (US = USD · HK = HKD) · siloed — not in Command totals</span>
        </div>
        {!data ? (
          <div className="qr-surface py-6 text-center text-slate-600 text-[11px]">Loading…</div>
        ) : (
          <div className={`grid grid-cols-1 gap-3 ${markets.length > 1 ? 'xl:grid-cols-2' : ''} items-start`}>
            {markets.map((mk) => (
              <MarketBook
                key={mk}
                market={mk}
                open={open.filter(p => p.market === mk)}
                closed={closed.filter(p => p.market === mk)}
                summary={byMarket[mk]}
                monthly={monthlyByMarket[mk]}
                unrealMonthly={unrealMonthlyByMarket[mk]}
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
