// Command center — EnvBook: the whole analytical workspace, scoped to ONE
// environment. Mounted with key={env}: switching remounts so no stale figure
// lingers.
//
// Per-environment lineage:
//   SIM   — positions /api/portfolio/positions (consumption.portfolio_positions_current)
//           stats+curve /api/execution/book-overview?book=sim
//           strategy realized /api/execution/strategy-pnl?book=sim (FULL
//           closed-ledger aggregate — no row cap) · fills
//           /api/execution/trades?book=sim · NO working-order book, NO equity
//   PAPER — positions /api/agents/paper/open-positions · stats+curve
//           book-overview?book=paper · strategy realized
//           strategy-pnl?book=paper · orders /api/command/order-book
//           (source=paper) · fills /api/execution/trades?book=paper ·
//           account /api/command/overview account.books.paper
//   UAT   — session/account/positions/orders /api/ib/tws/uat/* (live gateway)
//           fills /api/execution/trades?book=uat (gold.manual_orders blotter)
//           fill totals /api/command/pnl-by-mode modes.uat · NO round-trip
//           P&L ledger (fills-only) => curve/realized are honest no-data
//   LIVE  — positions /api/positions/live (ibkr_snapshot) · account
//           /api/command/overview account.books.live · equity curve
//           (last 30 sessions, HKD) · orders /api/command/order-book
//           (source=live) · fills /api/execution/trades?book=live

import React, { useMemo, useState } from 'react';
import { api, usePoll, fmtK, fmtKCcy, fmtPct, pnlCl } from '../../utils';
import { sK, sCcy, tsTip } from './format';
import { ENV_META } from './meta';
import { Panel, NoData, AsOf, LinkBtn, HBar } from './shared';
import { PerfPanel } from './PerfPanel';
import { ExposurePanel, AllocBars } from './ExposurePanel';
import { ActionsPanel } from './ActionsPanel';
import { StrategyPanel } from './StrategyPanel';
import { DriversPanel } from './DriversPanel';
import { PositionsPanel } from './PositionsPanel';
import { ActivityDock, OrdersTable, FillsTable } from './ActivityDock';
import { Opportunities } from './Opportunities';
import { MarketContext } from './MarketContext';
import {
  maxDrawdown, bookGrossStats, perCcyUnrealized, buildActionItems,
  normPositions, normFills, normOrders, fetchOpportunities,
} from './aggregate';

export const EnvBook = ({ env, limits, stratNames, onDataAsOf, regimeFc, regimeChg, navigateToTab, onSelectStrategy }) => {
  const [bookOv, setBookOv] = useState(null);       // sim/paper
  const [positions, setPositions] = useState(null); // raw payload per env
  const [orders, setOrders] = useState(null);
  const [fills, setFills] = useState(null);
  const [stratPnl, setStratPnl] = useState(null);   // sim/paper authoritative aggregate
  const [overview, setOverview] = useState(null);   // paper/live
  const [pnlMode, setPnlMode] = useState(null);
  const [uatAcct, setUatAcct] = useState(null);     // uat
  const [oppPicks, setOppPicks] = useState([]);
  const [dockTab, setDockTab] = useState(null);     // null => auto default

  const isSim = env === 'sim', isPaper = env === 'paper', isUat = env === 'uat', isLive = env === 'live';

  // Wave 1: positions — feeds every analytical panel + the freshness readout.
  usePoll(async () => {
    let res = null;
    if (isSim) res = await api.get('/api/portfolio/positions');
    else if (isPaper) res = await api.get('/api/agents/paper/open-positions');
    else if (isUat) res = await api.get('/api/ib/tws/uat/positions');
    else res = await api.get('/api/positions/live');
    if (res) {
      setPositions(res);
      const ts = res.as_of || new Date().toISOString();
      const t = new Date(String(ts).includes('T') ? String(ts) : `${String(ts).replace(' ', 'T')}Z`);
      onDataAsOf?.({ ts, stale: isNaN(t) ? false : (Date.now() - t.getTime()) > 3600000 });
    }
  }, 30000);

  // Wave 2: stats + curve (sim/paper), account (uat), overview (paper/live).
  usePoll(async () => {
    if (!isSim && !isPaper) return;
    const res = await api.get(`/api/execution/book-overview?book=${env}`);
    if (res) setBookOv(res);
  }, 60000, 1200);

  usePoll(async () => {
    if (!isUat) return;
    const res = await api.get('/api/ib/tws/uat/account');
    if (res) setUatAcct(res);
  }, 60000, 1200);

  usePoll(async () => {
    if (!isPaper && !isLive) return;
    const res = await api.get('/api/command/overview');
    if (res) setOverview(res);
  }, 60000, 1400);

  // Wave 3: orders + fills + mode P&L + per-strategy realized aggregate.
  usePoll(async () => {
    if (isSim) { setOrders({ unsupported: true }); return; }
    let res = null;
    if (isUat) res = await api.get('/api/ib/tws/uat/open-orders');
    else res = await api.get('/api/command/order-book');
    if (res) setOrders(res);
  }, 30000, 2600);

  usePoll(async () => {
    const res = await api.get(`/api/execution/trades?book=${env}&limit=15`);
    if (res) setFills(res);
  }, 60000, 2800);

  // Authoritative per-strategy realized P&L over the FULL closed ledger —
  // SQL aggregate, no row cap (replaces the old /trades?limit=500 page
  // aggregation, which silently under-reported books over 500 trades).
  // uat/live fills carry no per-fill P&L, so there is nothing to aggregate.
  usePoll(async () => {
    if (!isSim && !isPaper) return;
    const res = await api.get(`/api/execution/strategy-pnl?book=${env}`);
    if (res) setStratPnl(res);
  }, 60000, 3200);

  usePoll(async () => {
    const res = await api.get('/api/command/pnl-by-mode');
    if (res) setPnlMode(res?.modes?.[env] || null);
  }, 60000, 3000);

  // Opportunities (SIM/PAPER books are signal-driven).
  usePoll(async () => {
    if (!isSim && !isPaper) return;
    const picks = await fetchOpportunities();
    if (picks) setOppPicks(picks);
  }, 120000, 8000);

  // ----- normalized, environment-scoped rows -----
  const posRaw = isSim || isLive ? positions?.positions
    : isPaper ? positions?.positions
    : positions?.data;
  const posRows = useMemo(() => {
    if (posRaw == null) return null;
    const rows = normPositions(env, posRaw, stratNames);
    if (isSim || isPaper) rows.sort((a, b) => (b.entryDate || '').localeCompare(a.entryDate || ''));
    return rows;
  }, [posRaw, env, stratNames, isSim, isPaper]);

  const orderRows = useMemo(() => {
    if (orders == null || orders.unsupported) return orders;
    const raw = isUat ? orders.data : (orders.orders || []).filter(o => o.source === env);
    return normOrders(env, raw, stratNames)
      .sort((a, b) => (b.orderTs || '').localeCompare(a.orderTs || ''));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [orders, env, stratNames]);

  const fillRows = useMemo(() => {
    if (fills == null) return null;
    return normFills(env, fills.data || [], stratNames)
      .sort((a, b) => (b.fillTs || '').localeCompare(a.fillTs || ''));
  }, [fills, env, stratNames]);

  // Per-strategy risk/status (PAPER strategy_risks, LIVE deployed_health).
  const riskBy = useMemo(() => {
    const m = {};
    if (isPaper) {
      for (const r of (overview?.strategy_risks || [])) {
        const name = stratNames[r.strategy_id] || r.name || r.strategy_id;
        m[name] = { sev: r.sev || 'warning', label: r.sev === 'critical' ? 'critical' : 'risk', tip: (r.triggers || []).join(' · ') };
      }
    }
    if (isLive) {
      for (const h of (Array.isArray(overview?.deployed_health) ? overview.deployed_health : [])) {
        const name = stratNames[h.strategy_id] || h.name || h.strategy_id;
        m[name] = { sev: h.sev || 'warning', label: h.sev === 'critical' ? 'critical' : 'health', tip: h.impact || h.title || '' };
      }
    }
    return m;
  }, [overview, stratNames, isPaper, isLive]);

  // ----- environment-scoped action items (critical -> issues -> info) -----
  const actionItems = useMemo(
    () => buildActionItems({ env, limits, overview, positions }),
    [env, limits, overview, positions],
  );

  // ----- derived book facts -----
  const st = bookOv?.stats;
  const paperAcct = overview?.account?.books?.paper;
  const liveAcct = overview?.account?.books?.live;
  const a = uatAcct?.data;

  const simUnreal = useMemo(() => {
    if (!isSim || !posRows) return null;
    let sum = 0, n = 0;
    for (const p of posRows) if (p.unreal != null && !isNaN(p.unreal)) { sum += p.unreal; n += 1; }
    return n > 0 ? sum : null;
  }, [isSim, posRows]);

  // UAT unrealized: per-currency segments, never netted (no cross-currency
  // sum anywhere — not even for colour).
  const uatUnreal = useMemo(() => (isUat ? perCcyUnrealized(posRows, 'USD') : null), [isUat, posRows]);

  // Gross open market value + concentration + allocation (per book; UAT is
  // segmented per currency downstream where needed — never netted).
  const bookGross = useMemo(() => bookGrossStats(posRows, 'USD'), [posRows]);
  // Curves per environment + drawdown of the shown curve.
  const simCurve = useMemo(() => (bookOv?.ytd_curve || []).map(p => ({ d: p.d, equity: p.cum })), [bookOv]);
  const liveCurve = useMemo(() => (overview?.equity_curve || []).map(p => ({ d: p.d, equity: p.equity })), [overview]);
  const curve = isSim || isPaper ? simCurve : isLive ? liveCurve : null;
  const dd = useMemo(() => maxDrawdown(curve), [curve]);

  // Drawdown label is basis-honest (v7.1): a drawdown of the cumulative
  // REALIZED P&L curve is NOT portfolio max drawdown (no SIM/PAPER NAV/equity
  // history is served); only LIVE has a genuine equity series.
  const ddMeta = useMemo(() => {
    if (dd == null) return null;
    if (isSim || isPaper) {
      return {
        label: 'Realized P&L drawdown',
        value: fmtK(dd),
        sub: 'YTD · realized curve',
        tip: `Peak-to-trough of the cumulative REALIZED P&L curve shown in Performance (year to date, USD, frontend-derived from the displayed series). This is NOT portfolio max drawdown — no ${ENV_META[env].badge} NAV/equity history is served.`,
      };
    }
    if (isLive) {
      return {
        label: 'Max drawdown',
        value: fmtKCcy(dd, overview?.equity_curve_currency || 'HKD'),
        sub: 'equity · last 30 sessions',
        tip: 'Peak-to-trough of the live account equity curve (consumption.account_equity_curve, last 30 sessions) — a genuine equity series, frontend-derived from the displayed window.',
      };
    }
    return null;
  }, [dd, isSim, isPaper, isLive, overview, env]);

  // Risk utilization: per-strategy capital caps where actually set.
  const util = useMemo(() => {
    const rows = (limits?.per_strategy || []).filter(u => u.capital_cap_pct != null);
    return rows.map(u => ({ ...u, name: stratNames[u.strategy_id] || u.strategy_id }));
  }, [limits, stratNames]);

  // ----- ROW 1A Performance props per env -----
  const perfProps = (() => {
    if (isSim || isPaper) {
      const acct = isPaper ? paperAcct : null;
      const unreal = isPaper ? acct?.open_pnl : simUnreal;
      return {
        footnote: `Cumulative realized P&L, ${ENV_META[env].badge} book ledger (USD) — /api/execution/book-overview. Curve: daily cumulative realized, year to date.`,
        curve, curveNote: 'YTD · realized · USD',
        curveEmpty: bookOv == null ? 'Loading book…' : `No realized P&L this year in the ${ENV_META[env].badge} book`,
        focal: {
          label: 'Cumulative · realized · all time · USD',
          tip: `All-time cumulative realized P&L, ${ENV_META[env].badge} book (USD)`,
          value: st?.cum_pnl != null ? sK(st.cum_pnl) : '—',
        },
        focalCl: st?.cum_pnl != null ? pnlCl(st.cum_pnl) : 'text-slate-600',
        focalSub: st ? `YTD ${st.ytd_pnl != null ? sK(st.ytd_pnl) : '—'} · ${st.closed_trades ?? 0} closed · WR ${st.win_rate ?? '—'}%` : null,
        secondaries: [
          { label: 'Today · realized · USD', tip: "Realized P&L from today's exits (USD)", value: st?.today ? sK(st.today.pnl) : '—', valueCl: st?.today ? pnlCl(st.today.pnl) : 'text-slate-600', sub: st?.today ? `${st.today.trades} exit${st.today.trades === 1 ? '' : 's'}` : 'no exits today' },
          { label: 'Unrealized · open · USD', tip: isPaper ? 'Open P&L, paper book (consumption.account_summary)' : 'Sum of unrealized P&L over open SIM positions (USD)', value: unreal != null ? sK(unreal) : '—', valueCl: unreal != null ? pnlCl(unreal) : 'text-slate-600', sub: posRows ? `over ${posRows.length} open` : null },
          { label: 'Open positions', tip: `Open positions in the ${ENV_META[env].badge} book`, value: posRows ? posRows.length : '—', sub: `${ENV_META[env].badge} book` },
        ],
      };
    }
    if (isUat) {
      const ccy = a?.net_liquidation_currency || a?.currency;
      return {
        footnote: 'UAT paper account — /api/ib/tws/uat/account (live gateway). No UAT round-trip P&L ledger exists (gold.paper_uat_fills is fills-only), so there is no honest curve or realized figure.',
        curve: null, curveNote: 'account snapshot',
        curveEmpty: 'No UAT round-trip P&L ledger exists — fills-only blotter; no honest curve to draw (backend/ETL gap, not hidden data).',
        focal: {
          label: `Net liquidation${ccy ? ` · ${ccy}` : ''}`,
          tip: 'UAT paper account net liquidation (live gateway)',
          value: a?.net_liquidation != null ? fmtKCcy(a.net_liquidation, ccy) : '—',
        },
        focalCl: a?.net_liquidation != null ? 'text-white' : 'text-slate-600',
        focalSub: a?.net_liquidation_usd != null ? `≈ ${fmtKCcy(a.net_liquidation_usd, 'USD')} (authoritative gateway conversion)` : null,
        secondaries: [
          { label: 'Buying power', value: a?.buying_power != null ? fmtKCcy(a.buying_power, a.buying_power_currency || ccy) : '—', sub: a?.available_funds != null ? `avail ${fmtKCcy(a.available_funds, a.available_funds_currency || ccy)}` : null },
          { label: 'Unrealized · open', tip: 'Unrealized P&L over the UAT gateway portfolio — per-currency segments, never netted across currencies', valueCl: 'text-slate-100', value: uatUnreal
              ? <span className="inline-flex gap-2 flex-wrap">{uatUnreal.map(([c, v]) => <span key={c} className={pnlCl(v)}>{sCcy(v, c)}</span>)}</span>
              : '—' },
          { label: 'Open positions', value: posRows ? posRows.length : '—', sub: 'gateway portfolio' },
        ],
      };
    }
    // live
    return {
      footnote: 'Live account — /api/command/overview account.books.live. Curve: account equity, last 30 sessions (consumption.account_equity_curve, HKD).',
      curve, curveNote: `30 sessions · equity${overview?.equity_curve_currency ? ` · ${overview.equity_curve_currency}` : ''}`,
      curveEmpty: overview == null ? 'Loading account…' : 'No live equity history served',
      focal: {
        label: `Equity · net liquidation${liveAcct?.native_currency ? ` · ${liveAcct.native_currency}` : ''}`,
        tip: 'Live account net liquidation (account.books.live)',
        value: liveAcct?.equity_native != null ? fmtKCcy(liveAcct.equity_native, liveAcct.native_currency) : '—',
      },
      focalCl: liveAcct?.equity_native != null ? 'text-white' : 'text-slate-600',
      focalSub: liveAcct?.equity_usd != null ? `≈ ${fmtKCcy(liveAcct.equity_usd, 'USD')}` : null,
      secondaries: [
        { label: 'Today · day P&L', value: liveAcct?.day_pnl != null ? sK(liveAcct.day_pnl) : '—', valueCl: liveAcct?.day_pnl != null ? pnlCl(liveAcct.day_pnl) : 'text-slate-600', sub: liveAcct?.day_pnl_pct != null ? fmtPct(liveAcct.day_pnl_pct) : null },
        { label: 'Unrealized · open', value: liveAcct?.open_pnl != null ? sK(liveAcct.open_pnl) : '—', valueCl: liveAcct?.open_pnl != null ? pnlCl(liveAcct.open_pnl) : 'text-slate-600' },
        { label: 'Open positions', value: posRows ? posRows.length : '—', sub: 'ibkr snapshot' },
      ],
    };
  })();

  // ----- ROW 1B Exposure & Risk props per env -----
  const exposureStats = (() => {
    if (isSim) {
      return [
        { label: 'Gross open MV · USD', tip: 'Gross open market value — Σ|market value| over open SIM positions (USD book)', value: bookGross && !bookGross.mixed && bookGross.gross ? fmtK(bookGross.gross) : '—', sub: 'USD book' },
        { label: 'Exposure %', tip: 'No SIM equity figure is served, so exposure as % of equity cannot be computed honestly', value: 'n/a', valueCl: 'text-slate-600', sub: 'no SIM equity served' },
        { label: 'Cash', tip: 'No SIM cash ledger is served', value: 'n/a', valueCl: 'text-slate-600' },
      ];
    }
    if (isPaper) {
      const cash = paperAcct?.equity != null && paperAcct?.cash_pct != null ? paperAcct.equity * paperAcct.cash_pct / 100 : null;
      return [
        { label: 'Gross exposure', tip: 'Gross exposure as % of paper-book equity (consumption.account_summary)', value: paperAcct?.gross_exp_pct != null ? `${paperAcct.gross_exp_pct.toFixed(1)}%` : '—', sub: paperAcct?.net_exp_pct != null ? `net ${paperAcct.net_exp_pct.toFixed(1)}%` : null },
        { label: 'Equity · USD', value: paperAcct?.equity != null ? fmtKCcy(paperAcct.equity, paperAcct.currency || 'USD') : '—', sub: 'paper book' },
        { label: 'Estimated cash · USD', tip: 'ESTIMATE — derived as equity × cash_pct (consumption.account_summary fields); no separate paper cash ledger is served', value: cash != null ? fmtK(cash) : '—', sub: paperAcct?.cash_pct != null ? `${paperAcct.cash_pct.toFixed(1)}% of equity` : null },
      ];
    }
    if (isUat) {
      const ccy = a?.net_liquidation_currency || a?.currency;
      return [
        { label: `Net liquidation${ccy ? ` · ${ccy}` : ''}`, value: a?.net_liquidation != null ? fmtKCcy(a.net_liquidation, ccy) : '—', sub: a?.net_liquidation_usd != null ? `≈ ${fmtKCcy(a.net_liquidation_usd, 'USD')}` : null },
        { label: 'Available funds', value: a?.available_funds != null ? fmtKCcy(a.available_funds, a.available_funds_currency || ccy) : '—' },
        { label: 'Exposure %', tip: 'UAT positions are multi-currency and per-position base conversion is not served — an exposure % would require netting mixed currencies, which this page never does', value: 'n/a', valueCl: 'text-slate-600', sub: 'mixed ccy — see segments' },
      ];
    }
    // live
    return [
      { label: 'Gross exposure', tip: 'Gross exposure as % of live equity (backend field; see qr_etl ticket for the gross-vs-attention inconsistency)', value: liveAcct?.gross_exp_pct != null ? `${liveAcct.gross_exp_pct.toFixed(1)}%` : '—', sub: liveAcct?.net_exp_pct != null ? `net ${liveAcct.net_exp_pct.toFixed(1)}%` : null },
      { label: 'Cash · HKD', tip: 'Live account cash, HKD leg (never summed with the USD leg)', value: liveAcct?.cash_hkd != null ? fmtKCcy(liveAcct.cash_hkd, 'HKD') : '—' },
      { label: 'Cash · USD', tip: 'Live account cash, USD leg', value: liveAcct?.cash_usd != null ? fmtKCcy(liveAcct.cash_usd, 'USD') : '—', sub: liveAcct?.cash_pct != null ? `cash ${liveAcct.cash_pct.toFixed(1)}% of equity` : null },
    ];
  })();

  const allocNode = (() => {
    if (isUat) {
      if (!posRows) return <span className="text-[12px] text-slate-500">Loading…</span>;
      const acc = new Map();
      for (const p of posRows) {
        if (p.mv == null || isNaN(p.mv)) continue;
        const c = p.ccy || 'USD';
        acc.set(c, (acc.get(c) || 0) + Math.abs(p.mv));
      }
      if (acc.size === 0) return <span className="text-[12px] text-slate-500">Book flat — no open market value.</span>;
      const total = [...acc.values()].reduce((s, v) => s + v, 0);
      return (
        <div className="space-y-1.5">
          {[...acc.entries()].sort((x, y) => y[1] - x[1]).map(([c, v]) => (
            <div key={c} className="flex items-center gap-2" title="Per-currency gross open market value — currencies are never netted">
              <span className="w-[120px] flex-none text-[12px] font-mono text-slate-300">{c}</span>
              <span className="flex-1"><HBar pct={total > 0 ? v / total * 100 : 0} /></span>
              <span className="flex-none font-mono text-[11px] text-slate-300">{fmtKCcy(v, c)}</span>
            </div>
          ))}
          <div className="text-[11px] text-slate-500">gross open market value per currency — never netted across currencies</div>
        </div>
      );
    }
    if (!bookGross) return <span className="text-[12px] text-slate-500">Loading…</span>;
    if (bookGross.mixed) return <span className="text-[12px] text-slate-500">Mixed-currency book — allocation withheld; currencies are never netted.</span>;
    if (!bookGross.gross) return <span className="text-[12px] text-slate-500">Book flat — no open market value.</span>;
    return <AllocBars rows={bookGross.alloc} total={bookGross.gross} defCcy={bookGross.ccy} />;
  })();

  // ----- ROW 1C Actions facts — ordered: working orders, then recent
  // activity. Monitoring issues live in the alert items above, not here.
  const facts = (() => {
    const f = [];
    f.push({
      label: 'Working orders',
      value: orders?.unsupported ? 'n/a' : (Array.isArray(orderRows) ? `${orderRows.length}${orderRows[0]?.orderDate ? ` · latest ${orderRows[0].orderDate}` : ''}` : '—'),
      valueCl: Array.isArray(orderRows) && orderRows.length > 0 ? 'text-white font-bold' : undefined,
      tip: orders?.unsupported ? 'The SIM book has no working-order book — synthetic fills execute at signal' : `Pending orders in the ${ENV_META[env].badge} order book (latest order date shown)`,
      target: orders?.unsupported ? null : 'execution',
    });
    f.push({
      label: 'Recent fills',
      value: Array.isArray(fillRows) ? `${fillRows.length}${fillRows[0]?.fillDate ? ` · latest ${fillRows[0].fillDate}` : ''}` : '—',
      tip: `Closed-trade blotter, ${ENV_META[env].badge} book (latest 15 served, absolute fill dates)`,
      target: 'execution',
    });
    if ((isSim || isPaper) && st) {
      f.push({
        label: 'Exits today',
        value: st.today ? `${st.today.trades} · ${sK(st.today.pnl)}` : '0',
        tip: `Closed exits today (UTC) in the ${ENV_META[env].badge} ledger`,
        target: 'execution',
      });
    }
    if (isUat && pnlMode) {
      f.push({
        label: 'Blotter fills',
        value: `${pnlMode.fills ?? 0} · today ${pnlMode.fills_today ?? 0}`,
        tip: 'UAT fills blotter totals (/api/command/pnl-by-mode) — fills, not round-trips',
        target: 'execution',
      });
    }
    return f;
  })();

  // ----- ROW 2 honest no-data states -----
  const stratNoData = isUat
    ? 'No strategy attribution exists for the UAT book — the IBKR portfolio payload carries no strategy field and the fills ledger is per-fill. Rows are never fabricated into strategies.'
    : null;
  const driversNoData = isUat
    ? 'UAT gateway positions carry no unrealized marks — nothing to rank honestly.'
    : null;

  // ----- ROW 4 dock panes -----
  const ordersUnsupported = orders?.unsupported
    ? 'Not supported for SIM — synthetic fills execute at signal; the SIM ledger records closed trades only.'
    : null;
  const ordersPane = (() => {
    if (ordersUnsupported) return <NoData>{ordersUnsupported}</NoData>;
    if (orderRows == null) return <NoData>Loading…</NoData>;
    if (!Array.isArray(orderRows) || orderRows.length === 0) return <NoData>No working orders in the {ENV_META[env].badge} book.</NoData>;
    return (
      <div>
        <div className="flex items-center justify-end gap-3 px-4 pt-2">
          <AsOf ts={orders?.as_of} />
          <LinkBtn onClick={() => navigateToTab('execution')}>Orders →</LinkBtn>
        </div>
        <OrdersTable rows={orderRows} />
      </div>
    );
  })();

  const fillsPane = (() => {
    if (fillRows == null) return <NoData>Loading…</NoData>;
    if (fillRows.length === 0) return <NoData>No fills in the {ENV_META[env].badge} book.</NoData>;
    return (
      <div>
        <div className="flex items-center justify-end gap-3 px-4 pt-2">
          <AsOf ts={fills?.as_of} />
        </div>
        <FillsTable rows={fillRows} />
      </div>
    );
  })();

  const signalsPane = (
    <Opportunities env={env} picks={oppPicks} positions={posRows || []} orders={Array.isArray(orderRows) ? orderRows : []} navigateToTab={navigateToTab} />
  );
  const contextPane = <MarketContext fc={regimeFc} chg={regimeChg} />;

  const hasOrders = Array.isArray(orderRows) && orderRows.length > 0;
  const hasFills = Array.isArray(fillRows) && fillRows.length > 0;
  const orderCount = ordersUnsupported ? null : (Array.isArray(orderRows) ? orderRows.length : null);
  const tab = dockTab ?? (hasOrders ? 'orders' : hasFills ? 'fills' : 'signals');
  const dockTabs = [
    { k: 'orders', label: 'Orders', count: orderCount },
    { k: 'fills', label: 'Fills', count: Array.isArray(fillRows) ? fillRows.length : null },
    { k: 'signals', label: 'Signals', count: null },
    { k: 'context', label: 'Context', count: null },
  ];

  return (
    <>
      {/* ROW 1 — BOOK OVERVIEW (5/4/3) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4 items-start">
        <div className="lg:col-span-5 min-w-0"><PerfPanel env={env} {...perfProps} /></div>
        <div className="lg:col-span-4 min-w-0">
          <ExposurePanel env={env} stats={exposureStats} alloc={allocNode}
            dd={ddMeta}
            util={util}
            conc={bookGross && !bookGross.mixed && bookGross.gross ? { top1: bookGross.top1, top3: bookGross.top3, top1Name: bookGross.top1Name } : null} />
        </div>
        <div className="lg:col-span-3 min-w-0">
          <ActionsPanel env={env} items={actionItems} facts={facts}
            latestFills={Array.isArray(fillRows) ? fillRows.slice(0, 8) : []}
            navigateToTab={navigateToTab} />
        </div>
      </div>

      {/* ROW 2 — EXPLANATION: strategy performance (wide) + P&L drivers */}
      <div className="grid grid-cols-1 lg:grid-cols-[minmax(0,7fr)_minmax(0,5fr)] gap-4 items-start">
        <div className="min-w-0">
          <StrategyPanel env={env} rows={posRows} stratPnl={stratPnl} bookCumPnl={st?.cum_pnl ?? null}
            riskBy={riskBy} defCcy={'USD'}
            navigateToTab={navigateToTab} onSelectStrategy={onSelectStrategy} noDataText={stratNoData} />
        </div>
        <div className="min-w-0">
          <DriversPanel env={env} rows={posRows} defCcy={'USD'} noDataText={driversNoData} />
        </div>
      </div>

      {/* ROW 3 — INVESTIGATION: full-width positions */}
      <PositionsPanel env={env} rows={posRows}
        count={posRows ? posRows.length : null}
        asOf={positions?.as_of}
        headTip={
          isSim ? 'SIM book — consumption.portfolio_positions_current. Entry date leftmost (YYYY-MM-DD), newest first.'
          : isPaper ? 'Paper book — /api/agents/paper/open-positions. Entry date leftmost (YYYY-MM-DD), newest first. Market value = qty × last px (native ccy).'
          : isUat ? 'Live IBKR UAT paper-account portfolio (ib.portfolio()). Entry price = IBKR average cost. No entry dates served — rows keep gateway order.'
          : 'Live book — /api/positions/live (ibkr_snapshot). Entry = earliest FIFO open lot from the DUP825942 fills ledger (gold.paper_uat_fills), as-of the snapshot row.'
        }
        note={isUat ? 'no entry dates served' : null}
        emptyText={
          isSim ? 'SIM book flat — 0 open positions'
          : isPaper ? 'No open positions in the paper book'
          : isUat ? (positions && positions.connected === false
              ? 'UAT session disconnected — positions unavailable (PENDING). Reconnect from Execution ▸ UAT.'
              : `UAT book flat — 0 open positions at the gateway${positions?.as_of ? ` (as of ${tsTip(positions.as_of)})` : ''}`)
          : 'Live book flat — 0 open positions in the snapshot'
        }
        defCcy={'USD'}
        navigateToTab={navigateToTab} />

      {/* ROW 4 — ACTIVITY (secondary): Orders | Fills | Signals | Context */}
      <ActivityDock tab={tab} onTab={setDockTab} tabs={dockTabs}>
        {tab === 'orders' ? ordersPane : tab === 'fills' ? fillsPane : tab === 'signals' ? signalsPane : contextPane}
      </ActivityDock>
    </>
  );
};

// Default display currency is USD: SIM/PAPER books are USD; LIVE position P&L
// is reported in instrument currency (US instruments => USD, matching the
// account open_pnl sum); UAT rows carry their own per-row currency and are
// always segmented, never netted.
