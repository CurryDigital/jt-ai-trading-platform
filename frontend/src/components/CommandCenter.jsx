import React, { useMemo, useState, useEffect } from 'react';
import { api, usePoll, fmtK, fmtKCcy, fmtPct, fmtAge, pnlCl, marketClock, marketStatus } from '../utils';

// Command home — UAT trading command center (redesign 2026-11-03, v3).
// EVERY figure on this page is UAT-sourced. Lineage:
//   UAT session / heartbeat  — GET /api/ib/tws/uat/status
//   Account equity / buying power — GET /api/ib/tws/uat/account (live gateway)
//   Open positions           — GET /api/ib/tws/uat/positions (IBKR portfolio,
//                              never the DB book; connected=false => PENDING)
//   Working orders           — GET /api/ib/tws/uat/open-orders (ib.openTrades)
//   Recent fills             — GET /api/execution/trades?book=uat
//                              (gold.manual_orders DB blotter, book=uat)
//   Fill totals / last fill  — GET /api/command/pnl-by-mode modes.uat
//                              (gold.paper_uat_fills — fills ledger)
//   HALT state               — GET /api/execution/limits (gold.risk_limits)
//
// KNOWN CONTRACT GAPS (documented, never fabricated):
//   * No UAT round-trip P&L ledger exists (gold.paper_uat_fills is fills-only)
//     => NO P&L chart and no realized-P&L KPIs on this page (qr_etl's domain).
//   * The IBKR portfolio payload has NO entry date, strategy attribution, or
//     days-held per position => those columns render '—' with a tooltip.
//   * The signal universe has no UAT attribution => no opportunities section.
//
// Restrained palette: colour carries meaning only.
//   rose  = critical severity   emerald/rose text = signed P&L (via pnlCl)
//   blue  = interactive links   everything else = neutral slate/white

// ---------------------------------------------------------------------------
// Shared bits
// ---------------------------------------------------------------------------
const LinkBtn = ({ children, onClick }) => (
  <button onClick={onClick} className="text-[10px] font-semibold text-blue-400 hover:text-blue-300">{children}</button>
);

const Panel = ({ title, action, children, className = '' }) => (
  <div className={`qr-surface overflow-hidden ${className}`}>
    <div className="flex items-center justify-between px-3 py-1.5 border-b border-white/[0.05]">
      <span className="qr-label flex items-center gap-2">{title}</span>
      {action}
    </div>
    {children}
  </div>
);

// Small as-of tag sourced from the payload's own timestamp (these UAT panels
// read live gateway state, so the payload as_of IS the freshness truth).
const AsOf = ({ ts }) => {
  if (!ts) return null;
  return <span className="font-mono text-[9px] text-slate-600 normal-case tracking-normal" title={`Payload as_of ${ts}`}>upd {fmtAge(ts)}</span>;
};

// ---------------------------------------------------------------------------
// Header — "Command · UAT" + HALT / UAT session. One line on desktop, wraps
// on mobile.
// ---------------------------------------------------------------------------
const StatusItem = ({ label, children, tip }) => (
  <span className="flex items-center gap-1.5 flex-none" title={tip}>
    <span className="text-[9px] uppercase tracking-wide text-slate-500">{label}</span>
    {children}
  </span>
);

const CommandHeader = ({ limits, uatStatus }) => {
  const halted = !!limits?.global_halt;
  const connected = uatStatus?.is_connected === true;
  const acct = uatStatus?.account;
  return (
    <div className="qr-surface px-3 py-2">
      <div className="flex items-center gap-x-4 gap-y-1 flex-wrap">
        <span className="flex items-baseline gap-2 flex-none">
          <h1 className="text-sm font-bold text-white">Command · UAT</h1>
          <span className="qr-chip qr-chip-slate"
            title={`IBKR paper (UAT) session${acct ? ` · account ${acct}` : ''} — /api/ib/tws/uat/status`}>
            UAT{acct ? ` · ${acct}` : ''}
          </span>
        </span>
        <StatusItem label="HALT" tip={halted ? 'Global halt is ACTIVE — gold.risk_limits.global_halt' : 'No global halt — gold.risk_limits.global_halt = false'}>
          <span className={`font-mono text-[10px] font-bold ${halted ? 'text-rose-300' : 'text-slate-300'}`}>
            {limits == null ? '—' : halted ? 'HALTED' : 'off'}
          </span>
        </StatusItem>
        <StatusItem label="Session" tip={uatStatus ? `${uatStatus.message || ''} · ${uatStatus.host || ''}:${uatStatus.port || ''} client ${uatStatus.client_id ?? '—'}` : 'UAT session status unavailable'}>
          <span className={`w-1.5 h-1.5 rounded-full ${uatStatus == null ? 'bg-slate-600' : connected ? 'bg-emerald-400' : 'bg-rose-400'}`} />
          <span className="font-mono text-[10px] text-slate-300">{uatStatus == null ? '—' : connected ? 'connected' : 'down'}</span>
        </StatusItem>
      </div>
    </div>
  );
};

// ---------------------------------------------------------------------------
// Slim market ticker — visually subordinate context strip.
// ---------------------------------------------------------------------------
const StripSpark = ({ values }) => {
  if (!values || values.length < 2) return null;
  const min = Math.min(...values), max = Math.max(...values), range = (max - min) || 1;
  const w = 40, h = 12;
  const line = values.map((v, i) => `${((i / (values.length - 1)) * w).toFixed(1)},${(h - 1 - ((v - min) / range) * (h - 2)).toFixed(1)}`).join(' ');
  return (
    <svg viewBox={`0 0 ${w} ${h}`} className="block opacity-70" style={{ width: w, height: h }}>
      <polyline points={line} fill="none" stroke="rgba(148,163,184,0.8)" strokeWidth="1" vectorEffect="non-scaling-stroke" />
    </svg>
  );
};

const Clocks = () => {
  const [, setTick] = useState(0);
  useEffect(() => {
    const id = setInterval(() => setTick(t => t + 1), 1000);
    return () => clearInterval(id);
  }, []);
  const c = marketClock();
  const s = marketStatus();
  const Clock = ({ label, t, open }) => (
    <span className="flex items-center gap-1" title={open ? 'session open' : 'session closed'}>
      <span className={`w-1 h-1 rounded-full ${open ? 'bg-emerald-400' : 'bg-slate-600'}`} />
      <span className="text-slate-500">{label}</span>
      <span className="font-mono text-slate-300">{t}</span>
    </span>
  );
  return (
    <span className="flex items-center gap-2.5 text-[9px] flex-none">
      <Clock label="HKT" t={c.hkt} open={s.hk} />
      <Clock label="LON" t={c.lon} open={s.lon} />
      <Clock label="NYC" t={c.nyc} open={s.nyc} />
    </span>
  );
};

function MarketTicker() {
  const [ov, setOv] = useState(null);
  const load = async () => {
    const res = await api.get('/api/markets/overview?regions=US,HK');
    if (res) setOv(res);
  };
  useEffect(() => { load(); }, []);
  usePoll(load, 30000, 800);

  const rawIdx = ov?.indices?.data || ov?.indices;
  const indices = Array.isArray(rawIdx) ? rawIdx : [];
  const us = indices.filter(i => i.region === 'US').slice(0, 3);
  const hk = indices.filter(i => i.region === 'HK').slice(0, 2);
  const sentiment = ov?.sentiment || {};
  const usS = sentiment?.us || sentiment;
  const hkS = sentiment?.hk;

  return (
    <div className="flex items-center gap-3 px-1 overflow-x-auto text-[10px] text-slate-500">
      <Clocks />
      <span className="w-px self-stretch bg-white/[0.07] flex-none" />
      {[...us, ...hk].map(i => (
        <span key={i.sym} className="flex items-center gap-1.5 flex-none" title={i.name}>
          <span className="font-bold text-slate-300">{i.sym}</span>
          <span className="font-mono text-slate-300">{i.last != null ? i.last.toLocaleString(undefined, { maximumFractionDigits: 1 }) : '—'}</span>
          <span className={`font-mono ${pnlCl(i.change_pct ?? i.change_1d)}`}>{fmtPct(i.change_pct ?? i.change_1d)}</span>
          <StripSpark values={i.spark} />
        </span>
      ))}
      <span className="w-px self-stretch bg-white/[0.07] flex-none" />
      <span className="flex items-center gap-1 flex-none" title="CNN Fear & Greed (US)">
        <span>US F&amp;G</span><span className="font-mono text-slate-300">{usS?.fear_greed ?? '—'}</span>
      </span>
      <span className="flex items-center gap-1 flex-none" title="Fear & Greed (HK)">
        <span>HK F&amp;G</span><span className="font-mono text-slate-300">{hkS?.fear_greed ?? '—'}</span>
      </span>
      <span className="flex items-center gap-1 flex-none" title="CBOE VIX (US)">
        <span>VIX</span><span className="font-mono text-slate-300">{usS?.vix ?? '—'}</span>
      </span>
    </div>
  );
}

// ---------------------------------------------------------------------------
// UAT KPI row — compact tiles, UAT-sourced only. No realized/unrealized book
// P&L tiles: the UAT round-trip ledger does not exist (fills-only).
// ---------------------------------------------------------------------------
const Kpi = ({ label, value, valueCl = 'text-white', sub, tip }) => (
  <div className="qr-surface px-2.5 py-2 flex flex-col justify-center min-w-0" title={tip}>
    <div className="qr-label truncate">{label}</div>
    <div className={`font-mono text-[15px] font-bold leading-tight mt-0.5 truncate ${valueCl}`}>{value}</div>
    {sub != null && <div className="text-[9px] text-slate-500 leading-tight mt-0.5 truncate">{sub}</div>}
  </div>
);

const KpiRow = ({ acct, posCount, orderCount, fills, limits, uatStatus }) => {
  const a = acct?.data;
  const ccy = a?.net_liquidation_currency || a?.currency;
  const halted = !!limits?.global_halt;
  const connected = uatStatus?.is_connected === true;
  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-2">
      <Kpi label="Net liquidation" tip="UAT paper account net liquidation — /api/ib/tws/uat/account (live gateway)"
        value={a?.net_liquidation != null ? fmtKCcy(a.net_liquidation, ccy) : '—'}
        sub={a?.net_liquidation_usd != null ? `≈ ${fmtKCcy(a.net_liquidation_usd, 'USD')}` : null} />
      <Kpi label="Buying power" tip="UAT paper account buying power — /api/ib/tws/uat/account"
        value={a?.buying_power != null ? fmtKCcy(a.buying_power, a.buying_power_currency || ccy) : '—'}
        sub={a?.available_funds != null ? `avail ${fmtKCcy(a.available_funds, a.available_funds_currency || ccy)}` : null} />
      <Kpi label="Open positions" tip="UAT gateway portfolio — /api/ib/tws/uat/positions"
        value={posCount ?? '—'} />
      <Kpi label="Working orders" tip="Unfilled orders on the UAT session — /api/ib/tws/uat/open-orders"
        value={orderCount ?? '—'} />
      <Kpi label="Fills" tip="Broker-rehearsal fills ledger (gold.paper_uat_fills) — fills, not round-trips; no per-fill P&L exists"
        value={fills?.fills ?? '—'}
        sub={fills ? `today ${fills.fills_today ?? 0} · last ${fills.last_fill_at ? fmtAge(fills.last_fill_at) : '—'}` : null} />
      <Kpi label="Risk status" tip="Global halt (gold.risk_limits) + UAT session state"
        value={halted ? 'HALTED' : (uatStatus != null && !connected) ? 'SESSION DOWN' : 'OK'}
        valueCl={halted || (uatStatus != null && !connected) ? 'text-rose-300' : 'text-white'}
        sub={halted ? 'global halt active' : 'halt clear'} />
    </div>
  );
};

// ---------------------------------------------------------------------------
// Open Positions · UAT — the primary section. Full-width compact table, all
// rows, internal scroll. ENTRY DATE leftmost per spec.
//
// IBKR portfolio payload fields: ticker, symbol, sec_type, exchange, currency,
// qty, avg_cost, market_price, market_value, unrealized_pnl, realized_pnl.
// It carries NO entry timestamp and NO strategy attribution, so ENTRY DATE /
// STRATEGY / DAYS HELD render '—' with an explanatory tooltip rather than a
// fabricated value. Default sort by entry date is unsupported for the same
// reason (rows keep gateway order).
// ---------------------------------------------------------------------------
const NO_ENTRY_TIP = 'Not served: the IBKR portfolio payload (/api/ib/tws/uat/positions) has no entry timestamp — a UAT positions ledger with entry dates is a backend/ETL gap.';
const NO_STRAT_TIP = 'Not served: the IBKR portfolio payload has no strategy attribution — the UAT fills ledger (gold.paper_uat_fills.strategy_id) is per-fill and cannot be uniquely mapped to an aggregated position.';

const OpenPositionsUat = ({ payload, navigateToTab }) => {
  const rows = payload?.data;
  const connected = payload?.connected !== false;
  return (
    <Panel title="Open Positions · UAT" action={
      <span className="flex items-center gap-2">
        <span className="text-[9px] text-slate-600"
          title="Live IBKR UAT paper-account portfolio (ib.portfolio() on the UAT session). Entry price = IBKR average cost. Rows keep gateway order — entry-date sort unsupported (no entry timestamps served).">
          {connected ? `${rows?.length ?? 0} positions · live gateway portfolio` : 'session down'}
        </span>
        <AsOf ts={payload?.as_of} />
        <LinkBtn onClick={() => navigateToTab('execution')}>Execution →</LinkBtn>
      </span>
    }>
      {!connected ? (
        <div className="px-3 py-2 text-[11px] text-slate-500">
          UAT session disconnected — positions unavailable (PENDING). Reconnect from Execution ▸ UAT.
        </div>
      ) : rows && rows.length > 0 ? (
        <div className="max-h-[420px] overflow-y-auto overflow-x-auto">
          <table className="w-full min-w-[860px]">
            <thead className="sticky top-0 bg-[#10141f]">
              <tr className="text-[8px] font-semibold text-slate-500 uppercase tracking-wide">
                <th className="text-left px-3 py-1" title={NO_ENTRY_TIP}>Entry date</th>
                <th className="text-left px-2 py-1">Symbol</th>
                <th className="text-left px-2 py-1" title={NO_STRAT_TIP}>Strategy</th>
                <th className="text-left px-2 py-1">Side</th>
                <th className="text-right px-2 py-1">Qty</th>
                <th className="text-right px-2 py-1" title="IBKR average cost">Entry price</th>
                <th className="text-right px-2 py-1">Current price</th>
                <th className="text-right px-2 py-1">Unrealized P&L</th>
                <th className="text-right px-2 py-1">Market value</th>
                <th className="text-right px-3 py-1" title={NO_ENTRY_TIP}>Days held</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((p, i) => (
                <tr key={`${p.symbol}-${p.currency}-${i}`} className="border-t border-white/[0.05] text-[11px]">
                  <td className="px-3 py-1.5 font-mono text-slate-600" title={NO_ENTRY_TIP}>—</td>
                  <td className="px-2 py-1.5 font-mono font-bold text-white whitespace-nowrap">
                    {p.ticker || p.symbol}
                    <span className="text-[9px] font-normal text-slate-500 ml-1">{p.currency || ''}</span>
                  </td>
                  <td className="px-2 py-1.5 text-slate-600" title={NO_STRAT_TIP}>—</td>
                  <td className="px-2 py-1.5 font-mono font-bold text-slate-300">{p.qty != null ? (p.qty >= 0 ? 'LONG' : 'SHORT') : '—'}</td>
                  <td className="px-2 py-1.5 text-right font-mono text-slate-200">{p.qty != null ? Math.abs(p.qty).toLocaleString() : '—'}</td>
                  <td className="px-2 py-1.5 text-right font-mono text-slate-300">{p.avg_cost != null ? p.avg_cost.toLocaleString(undefined, { maximumFractionDigits: 2 }) : '—'}</td>
                  <td className="px-2 py-1.5 text-right font-mono text-slate-300" title={p.market_price == null ? 'no mark from gateway' : undefined}>
                    {p.market_price != null ? p.market_price.toLocaleString(undefined, { maximumFractionDigits: 2 }) : '—'}
                  </td>
                  <td className={`px-2 py-1.5 text-right font-mono font-bold whitespace-nowrap ${p.unrealized_pnl != null ? pnlCl(p.unrealized_pnl) : 'text-slate-600'}`}>
                    {p.unrealized_pnl != null ? `${p.unrealized_pnl >= 0 ? '+' : ''}${fmtK(p.unrealized_pnl)}` : '—'}
                  </td>
                  <td className="px-2 py-1.5 text-right font-mono text-slate-300">{p.market_value != null ? fmtK(p.market_value) : '—'}</td>
                  <td className="px-3 py-1.5 text-right font-mono text-slate-600" title={NO_ENTRY_TIP}>—</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full min-w-[860px]">
            <thead className="bg-[#10141f]">
              <tr className="text-[8px] font-semibold text-slate-500 uppercase tracking-wide">
                <th className="text-left px-3 py-1" title={NO_ENTRY_TIP}>Entry date</th>
                <th className="text-left px-2 py-1">Symbol</th>
                <th className="text-left px-2 py-1" title={NO_STRAT_TIP}>Strategy</th>
                <th className="text-left px-2 py-1">Side</th>
                <th className="text-right px-2 py-1">Qty</th>
                <th className="text-right px-2 py-1" title="IBKR average cost">Entry price</th>
                <th className="text-right px-2 py-1">Current price</th>
                <th className="text-right px-2 py-1">Unrealized P&L</th>
                <th className="text-right px-2 py-1">Market value</th>
                <th className="text-right px-3 py-1" title={NO_ENTRY_TIP}>Days held</th>
              </tr>
            </thead>
            <tbody>
              <tr className="border-t border-white/[0.05]">
                <td colSpan={10} className="px-3 py-2 text-[11px] text-slate-600">
                  UAT book flat — 0 open positions at the gateway{payload?.as_of ? ` (as of ${payload.as_of.slice(0, 19)}Z)` : ''}
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      )}
    </Panel>
  );
};

// ---------------------------------------------------------------------------
// Working Orders · UAT — ib.openTrades() on the UAT session. Compact table,
// single-line empty state.
// ---------------------------------------------------------------------------
const WorkingOrdersUat = ({ payload, navigateToTab }) => {
  const rows = payload?.data;
  const connected = payload?.connected !== false;
  return (
    <Panel title="Working Orders · UAT" action={
      <span className="flex items-center gap-2">
        <span className="text-[9px] text-slate-600" title="ib.openTrades() on the UAT session — unfilled/cancellable orders">
          {connected ? `${rows?.length ?? 0} working` : 'session down'}
        </span>
        <AsOf ts={payload?.as_of} />
        <LinkBtn onClick={() => navigateToTab('execution')}>Orders →</LinkBtn>
      </span>
    }>
      {!connected ? (
        <div className="px-3 py-2 text-[11px] text-slate-500">UAT session disconnected — working orders unavailable</div>
      ) : rows && rows.length > 0 ? (
        <div className="max-h-[220px] overflow-y-auto overflow-x-auto">
          <table className="w-full min-w-[520px]">
            <thead className="sticky top-0 bg-[#10141f]">
              <tr className="text-[8px] font-semibold text-slate-500 uppercase tracking-wide">
                <th className="text-left px-3 py-1">Symbol</th>
                <th className="text-left px-2 py-1">Side</th>
                <th className="text-right px-2 py-1">Qty</th>
                <th className="text-right px-2 py-1">Filled</th>
                <th className="text-left px-2 py-1">Type</th>
                <th className="text-left px-3 py-1">Status</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((o, i) => (
                <tr key={`${o.order_id ?? o.perm_id}-${i}`} className="border-t border-white/[0.05] text-[11px]">
                  <td className="px-3 py-1 font-mono font-bold text-white">{o.local_symbol || o.symbol}</td>
                  <td className={`px-2 py-1 font-mono font-bold ${o.action === 'BUY' ? 'text-emerald-400' : o.action === 'SELL' ? 'text-rose-400' : 'text-slate-400'}`}>{o.action ?? '—'}</td>
                  <td className="px-2 py-1 text-right font-mono text-slate-200">{o.qty != null ? o.qty.toLocaleString() : '—'}</td>
                  <td className="px-2 py-1 text-right font-mono text-slate-300" title={o.remaining != null ? `${o.remaining} remaining` : undefined}>{o.filled ?? 0}</td>
                  <td className="px-2 py-1 font-mono text-slate-300">{o.order_type ?? '—'}</td>
                  <td className="px-3 py-1"><span className="text-[9px] px-1.5 py-0.5 rounded bg-white/[0.06] text-slate-300">{o.status ?? '—'}</span></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <div className="px-3 py-2 text-[11px] text-slate-600">No working orders on the UAT session</div>
      )}
    </Panel>
  );
};

// ---------------------------------------------------------------------------
// Recent Fills · UAT — DB blotter (gold.manual_orders, book=uat). Fills are
// not round-trips; no per-fill P&L exists. Single-line empty state.
// ---------------------------------------------------------------------------
const RecentFillsUat = ({ trades, asOf }) => (
  <Panel title="Recent Fills · UAT" action={
    <span className="flex items-center gap-2">
      <span className="text-[9px] text-slate-600" title="UAT blotter — gold.manual_orders book=uat. Fills, not round-trips; per-fill P&L is not served.">
        {trades.length} shown · DB blotter
      </span>
      <AsOf ts={asOf} />
    </span>
  }>
    {trades.length > 0 ? (
      <div className="max-h-[220px] overflow-y-auto overflow-x-auto">
        <table className="w-full min-w-[520px]">
          <thead className="sticky top-0 bg-[#10141f]">
            <tr className="text-[8px] font-semibold text-slate-500 uppercase tracking-wide">
              <th className="text-left px-3 py-1">Time</th>
              <th className="text-left px-2 py-1">Ticker</th>
              <th className="text-left px-2 py-1">Side</th>
              <th className="text-right px-2 py-1">Qty</th>
              <th className="text-right px-3 py-1">Price</th>
            </tr>
          </thead>
          <tbody>
            {trades.map((t, i) => (
              <tr key={`${t.t}-${t.ticker}-${i}`} className="border-t border-white/[0.05] text-[11px]">
                <td className="px-3 py-1 font-mono text-[10px] text-slate-400 whitespace-nowrap" title={t.t}>{t.t ? fmtAge(t.t) : '—'}</td>
                <td className="px-2 py-1 font-mono font-bold text-white">{t.ticker}</td>
                <td className={`px-2 py-1 font-mono font-bold ${t.side === 'BUY' ? 'text-emerald-400' : t.side === 'SELL' ? 'text-rose-400' : 'text-slate-400'}`}>{t.side ?? '—'}</td>
                <td className="px-2 py-1 text-right font-mono text-slate-200">{t.qty != null ? t.qty.toLocaleString() : '—'}</td>
                <td className="px-3 py-1 text-right font-mono text-slate-300">{t.price != null ? t.price.toLocaleString(undefined, { maximumFractionDigits: 2 }) : '—'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    ) : (
      <div className="px-3 py-2 text-[11px] text-slate-600">No fills in the UAT blotter</div>
    )}
  </Panel>
);

// ---------------------------------------------------------------------------
// Action Required · UAT — halt state, UAT session health. Compact; one-line
// empty state. (Strategy-risk and platform attention feeds are paper/live
// scoped and deliberately excluded from this page.)
// ---------------------------------------------------------------------------
const SEV_DOT = { critical: 'bg-rose-400', warning: 'bg-slate-400' };

const ActionRequiredUat = ({ items, navigateToTab }) => (
  <Panel title="Action Required · UAT" action={
    items.length > 0
      ? <span className="text-[9px] text-slate-500">{items.filter(i => i.sev === 'critical').length} critical · {items.filter(i => i.sev === 'warning').length} warning</span>
      : null
  }>
    {items.length === 0 ? (
      <div className="px-3 py-2 text-[11px] text-slate-500">No action required — halt clear, UAT session connected</div>
    ) : (
      <div className="divide-y divide-white/[0.05]">
        {items.map((it, i) => (
          <button key={`${it.id}-${i}`} onClick={() => it.target ? navigateToTab(it.target) : undefined}
            className="w-full flex items-start gap-2 px-3 py-1.5 text-left hover:bg-white/[0.03]"
            title={it.tip || it.impact || it.title}>
            <span className={`w-1.5 h-1.5 rounded-full mt-1 flex-none ${SEV_DOT[it.sev] || SEV_DOT.warning}`} />
            <span className="flex-1 min-w-0">
              <span className="block text-[11px] font-bold text-slate-100 truncate">{it.title}</span>
              {it.impact && <span className="block text-[9px] text-slate-500 truncate">{it.impact}</span>}
            </span>
          </button>
        ))}
      </div>
    )}
  </Panel>
);

// ---------------------------------------------------------------------------
// Market Context — compact regime forecast, deliberately low prominence.
//   current regime label  — consumption.market_sentiment (canonical, US + HK)
//   probability           — HMM posterior, gold.regime_label (US scope only)
//   7-day strip           — consumption.macro_regime_7d, momentum_nowcast
// ---------------------------------------------------------------------------
const RISK_CELL = (v) => v == null ? 'bg-white/[0.04] text-slate-600'
  : v >= 60 ? 'bg-emerald-500/15 text-emerald-300'
  : v <= 40 ? 'bg-rose-500/15 text-rose-300'
  : 'bg-white/[0.06] text-slate-300';

const fmtConf = (c) => c == null ? '—' : c >= 0.99995 ? '>99.99%' : `${(c * 100).toFixed(1)}%`;

const REGIME_MEANING = {
  TREND: 'Trending tape — momentum and trend-following books should keep working; fade entries get run over.',
  MEAN_REV: 'Mean-reverting tape — moves fade; breakout entries underperform.',
  CARRY: 'Carry / range tape — low-vol grind; income-style books favoured over breakouts.',
  EVENT: 'Event-driven stress — expect gaps and vol spikes; gross exposure earns less.',
  FLAT: 'No dominant regime — weak signal environment; neutral sizing.',
};

const RegimeRegion = ({ region, fc, chg }) => {
  const days = fc?.days || [];
  const regime = chg?.regime ?? null;
  const allSame = days.length > 1 && days.every(d => d.risk_on === days[0].risk_on);
  let changeLine = null;
  if (chg) {
    if (!chg.history) {
      changeLine = 'no daily history — latest snapshot only';
    } else if (chg.prev_regime == null) {
      changeLine = `${regime} for ${chg.days_in_regime ?? '—'}+ days`;
    } else if (chg.days_in_regime === 1) {
      changeLine = `changed today: ${chg.prev_regime} → ${regime}`;
    } else {
      changeLine = `${chg.prev_regime} → ${regime} on ${chg.changed_on} · ${chg.days_in_regime}d in regime`;
    }
  }
  return (
    <div className="px-3 py-2">
      <div className="flex items-baseline gap-2 flex-wrap">
        <span className="font-mono text-[10px] font-black text-white flex-none">{region}</span>
        <span className="text-[12px] font-bold text-slate-100" title={`${chg?.source || ''}${regime ? `\n${REGIME_MEANING[regime] || ''}` : ''}`}>
          {regime ?? '—'}
        </span>
        <span className="font-mono text-[9px] text-slate-400"
          title={region === 'US' ? 'HMM posterior probability of the current regime (gold.regime_label)' : 'No regime posterior for HK — the HMM is US-scope (SPY/VIX features)'}>
          P {fmtConf(chg?.confidence)}
        </span>
        <span className="text-[9px] font-mono text-slate-500 truncate" title={chg?.source || ''}>{changeLine ?? '—'}</span>
      </div>
      {days.length > 0 && (
        <div className="grid grid-cols-7 gap-0.5 mt-1.5">
          {days.map((d, i) => (
            <div key={d.date || i}
              className={`rounded px-0.5 py-0.5 text-center ${RISK_CELL(d.risk_on)}`}
              title={`${d.date ?? ''} · ${d.risk_on != null ? `${d.risk_on.toFixed(1)}%` : '—'} risk-on — momentum_nowcast (consumption.macro_regime_7d)${allSame ? ' · flat carry-forward nowcast' : ''}`}>
              <div className="text-[8px] font-mono opacity-80">
                {d.date ? new Date(d.date + 'T00:00:00').toLocaleDateString('en-US', { weekday: 'narrow' }) : '·'}
              </div>
              <div className="text-[9px] font-mono font-bold">
                {d.risk_on != null ? `${d.risk_on.toFixed(0)}%` : '—'}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

const MarketContext = ({ fc, chg }) => (
  <Panel title="Market Context · Regime" action={
    <span className="text-[9px] text-slate-600"
      title="Current regime: consumption.market_sentiment (canonical) + HMM posterior from gold.regime_label (US, SPY/VIX features). 7-day strip: momentum_nowcast (consumption.macro_regime_7d). Legend: ≥60% risk-on = emerald · ≤40% = rose · else neutral.">
      HMM daily + 7d nowcast
    </span>
  }>
    <div className="grid grid-cols-1 sm:grid-cols-2 divide-y sm:divide-y-0 sm:divide-x divide-white/[0.05]">
      <RegimeRegion region="US" fc={fc?.US} chg={chg?.US} />
      <RegimeRegion region="HK" fc={fc?.HK} chg={chg?.HK} />
    </div>
  </Panel>
);

// ---------------------------------------------------------------------------
// Command page — UAT trading command center
// ---------------------------------------------------------------------------
export const CommandCenter = ({ navigateToTab }) => {
  const [uatStatus, setUatStatus] = useState(null);
  const [uatAcct, setUatAcct] = useState(null);
  const [uatPos, setUatPos] = useState(null);
  const [uatOrders, setUatOrders] = useState(null);
  const [uatTrades, setUatTrades] = useState(null);
  const [fills, setFills] = useState(null);
  const [limits, setLimits] = useState(null);
  const [regimeFc, setRegimeFc] = useState(null);
  const [regimeChg, setRegimeChg] = useState(null);

  // Wave 1 (t=0): session status + positions — the primary content.
  usePoll(async () => {
    const res = await api.get('/api/ib/tws/uat/status');
    if (res) setUatStatus(res);
  }, 30000);

  usePoll(async () => {
    const res = await api.get('/api/ib/tws/uat/positions');
    if (res) setUatPos(res);
  }, 30000);

  // Wave 2: account + working orders.
  usePoll(async () => {
    const res = await api.get('/api/ib/tws/uat/account');
    if (res) setUatAcct(res);
  }, 60000, 1200);

  usePoll(async () => {
    const res = await api.get('/api/ib/tws/uat/open-orders');
    if (res) setUatOrders(res);
  }, 30000, 1400);

  // Wave 3: DB-backed fills blotter + fills summary + halt state.
  usePoll(async () => {
    const res = await api.get('/api/execution/trades?book=uat&limit=15');
    if (res) setUatTrades(res);
  }, 60000, 2600);

  usePoll(async () => {
    const res = await api.get('/api/command/pnl-by-mode');
    if (res) setFills(res?.modes?.uat || null);
  }, 60000, 2800);

  usePoll(async () => {
    const res = await api.get('/api/execution/limits');
    if (res) setLimits(res);
  }, 60000, 3000);

  // Wave 4: market context (low prominence, loads last).
  usePoll(async () => {
    const res = await api.get('/api/command/regime-forecast');
    if (res) setRegimeFc(res.markets || {});
  }, 300000, 6000);

  usePoll(async () => {
    const res = await api.get('/api/command/regime-change');
    if (res) setRegimeChg(res.regions || {});
  }, 300000, 6500);

  // UAT-only action items.
  const actionItems = useMemo(() => {
    const items = [];
    if (limits?.global_halt) {
      items.push({ id: 'halt', sev: 'critical', title: 'Global HALT active', impact: 'Order firing halted — gold.risk_limits.global_halt', target: 'settings' });
    }
    if (uatStatus && uatStatus.is_connected === false) {
      items.push({ id: 'uat-down', sev: 'critical', title: 'UAT session disconnected', impact: uatStatus.message || 'No order routing or portfolio feed on the UAT session', target: 'execution' });
    }
    return items;
  }, [limits, uatStatus]);

  const trades = uatTrades?.data || [];

  return (
    <div className="space-y-2.5">
      {/* 1 — Command header (UAT) + slim market ticker */}
      <CommandHeader limits={limits} uatStatus={uatStatus} />
      <MarketTicker />

      {/* 2 — UAT KPI row */}
      <KpiRow acct={uatAcct} posCount={uatPos ? (uatPos.count ?? 0) : null}
        orderCount={uatOrders ? (uatOrders.count ?? 0) : null}
        fills={fills} limits={limits} uatStatus={uatStatus} />

      {/* 3 — Open Positions · UAT: the primary section, directly under KPIs.
              P&L chart intentionally absent: no UAT round-trip P&L ledger
              exists (gold.paper_uat_fills is fills-only), so there is no
              honest curve to draw. */}
      <OpenPositionsUat payload={uatPos} navigateToTab={navigateToTab} />

      {/* 4 — Working orders + recent fills, side by side */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-2.5">
        <WorkingOrdersUat payload={uatOrders} navigateToTab={navigateToTab} />
        <RecentFillsUat trades={trades} asOf={uatTrades?.as_of} />
      </div>

      {/* 5 — Action Required · UAT (compact) */}
      <ActionRequiredUat items={actionItems} navigateToTab={navigateToTab} />

      {/* 6 — Market context (reduced prominence, bottom of page) */}
      <MarketContext fc={regimeFc} chg={regimeChg} />
    </div>
  );
};

export default CommandCenter;
