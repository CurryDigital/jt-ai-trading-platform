import React, { useState, useRef, useEffect } from 'react';
import { api, usePoll, pnlCl } from '../../utils';

// Shared per-book performance overview for ALL Execution subtabs (SIM / PAPER /
// UAT / LIVE) — mounted in ExecScaffold's full-width overview slot so the YTD
// chart spans the page. One endpoint — GET /api/execution/book-overview?book=
// — serves sim/paper/uat. UAT is fills-only (no round-trip P&L in
// gold.paper_uat_fills): its P&L fields arrive null and render as PENDING,
// never a fake $0. The endpoint does not serve the live book — LIVE renders
// the same three sections in an explicit PENDING state, no request fired.

const SUPPORTED_BOOKS = new Set(['sim', 'paper', 'uat']);

const fmtUsd = (n) => n == null ? '—'
  : `${n < 0 ? '-' : '+'}$${Math.abs(n).toLocaleString(undefined, { maximumFractionDigits: 0 })}`;
const fmtAxis = (n) => {
  const s = Math.abs(n) >= 1e6 ? `$${(Math.abs(n) / 1e6).toFixed(1)}M`
    : Math.abs(n) >= 1e3 ? `$${(Math.abs(n) / 1e3).toFixed(0)}K` : `$${Math.abs(n).toFixed(0)}`;
  return n < 0 ? `-${s}` : s;
};

const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

// YTD cumulative realized P&L, dollars. SVG area chart. X axis spans the full
// calendar year (Jan–Dec) with month labels at month starts; the curve draws
// up to today and the rest of the year stays empty. Y axis is symmetric with
// $0 pinned at the vertical center so gains and losses read at the same scale.
// Width tracks the container via ResizeObserver so the chart truly spans the
// full page width (a fixed viewBox + preserveAspectRatio would letterbox).
const YtdChart = ({ curve }) => {
  const ref = useRef(null);
  const [width, setWidth] = useState(600);
  useEffect(() => {
    if (!ref.current) return undefined;
    const ro = new ResizeObserver((entries) => {
      setWidth(Math.max(320, Math.round(entries[0].contentRect.width)));
    });
    ro.observe(ref.current);
    return () => ro.disconnect();
  }, []);

  if (!curve || curve.length < 2) return null;
  const W = width, H = 150, ml = 46, mr = 8, mt = 10, mb = 20;
  const pw = W - ml - mr, ph = H - mt - mb;
  const year = Number(curve[0].d.slice(0, 4));
  const isLeap = (year % 4 === 0 && year % 100 !== 0) || year % 400 === 0;
  const daysInYear = isLeap ? 366 : 365;
  const jan1 = Date.UTC(year, 0, 1);
  const dayIdx = (d) => Math.round((Date.UTC(Number(d.slice(0, 4)), Number(d.slice(5, 7)) - 1, Number(d.slice(8, 10))) - jan1) / 86400000);
  const x = (i) => ml + (i / (daysInYear - 1)) * pw;
  // Symmetric range: $0 at the vertical center.
  const maxAbs = Math.max(...curve.map(p => Math.abs(p.cum)), 1);
  const y = (v) => mt + ph / 2 - (v / maxAbs) * (ph / 2);
  const pts = curve.map((p) => `${x(dayIdx(p.d)).toFixed(1)},${y(p.cum).toFixed(1)}`);
  const zeroY = y(0);
  const area = `${pts[0].split(',')[0]},${zeroY.toFixed(1)} ${pts.join(' ')} ${pts[pts.length - 1].split(',')[0]},${zeroY.toFixed(1)}`;
  const last = curve[curve.length - 1].cum;
  const stroke = last >= 0 ? '#34d399' : '#fb7185';
  // Month labels at each month start across the full year.
  const labels = MONTHS.map((m, i) => ({ m, i, x: x(dayIdx(`${year}-${String(i + 1).padStart(2, '0')}-01`)) }));
  const ticks = [-maxAbs, 0, maxAbs];
  return (
    <div ref={ref}>
      <svg viewBox={`0 0 ${W} ${H}`} className="w-full h-[150px] block">
        {ticks.map((t, i) => (
          <g key={i}>
            <line x1={ml} x2={W - mr} y1={y(t)} y2={y(t)}
              stroke={t === 0 ? 'rgba(255,255,255,0.16)' : 'rgba(255,255,255,0.07)'} strokeWidth="1" />
            <text x={ml - 5} y={y(t) + 3} textAnchor="end" fontSize="8" fill="#94a3b8" opacity="0.8"
              fontFamily="ui-monospace, SFMono-Regular, Menlo, monospace">{fmtAxis(t)}</text>
          </g>
        ))}
        <polygon points={area} fill={stroke} opacity="0.10" />
        <polyline points={pts.join(' ')} fill="none" stroke={stroke} strokeWidth="1.5" strokeLinejoin="round" strokeLinecap="round" />
        {labels.map(({ m, i, x: lx }) => (
          <text key={m} x={lx} y={H - 6} textAnchor={i === 0 ? 'start' : i === 11 ? 'end' : 'middle'}
            fontSize="8" fill="#94a3b8" opacity="0.7"
            fontFamily="ui-monospace, SFMono-Regular, Menlo, monospace">{m}</text>
        ))}
      </svg>
    </div>
  );
};

const StatTile = ({ label, value, tone, title }) => (
  <div className="rounded bg-white/[0.03] px-2 py-1.5 min-w-0" title={title}>
    <div className="qr-label">{label}</div>
    <div className={`font-mono text-[13px] font-bold leading-tight truncate ${tone || 'text-white'}`}>{value}</div>
  </div>
);

const PendingBody = ({ text, tip }) => (
  <div className="py-6 text-center text-[11px] text-slate-500" title={tip}>
    <span className="qr-chip qr-chip-rose mr-2">PENDING</span>
    {text}
  </div>
);

// One strategy-performance card. rows arrive pre-sorted; pendingText short-
// circuits the table with an honest pending state (no fake data).
const StrategyPerfCard = ({ title, sub, rows, isFills, loading, pendingText, pendingTip, emptyText }) => (
  <div className="qr-surface overflow-hidden">
    <div className="px-3 py-2 border-b border-white/[0.05] flex items-center justify-between">
      <span className="qr-label">{title}</span>
      <span className="text-[9px] text-slate-600">{sub}</span>
    </div>
    {pendingText ? (
      <PendingBody text={pendingText} tip={pendingTip} />
    ) : loading ? (
      <div className="py-5 text-center text-slate-600 text-[11px]">Loading…</div>
    ) : rows.length === 0 ? (
      <div className="py-5 text-center text-slate-600 text-[11px]">{emptyText}</div>
    ) : (
      <table className="w-full">
        <thead>
          <tr className="border-b border-white/[0.06]">
            <th className="qr-label text-left py-1 px-2">#</th>
            <th className="qr-label text-left py-1 px-2">Strategy</th>
            {isFills ? (
              <>
                <th className="qr-label text-right py-1 px-2">Fills</th>
                <th className="qr-label text-right py-1 px-2">Symbols</th>
                <th className="qr-label text-right py-1 px-2">Last Fill</th>
              </>
            ) : (
              <>
                <th className="qr-label text-right py-1 px-2">Closed</th>
                <th className="qr-label text-right py-1 px-2">Win %</th>
                <th className="qr-label text-right py-1 px-2">YTD P&L</th>
                <th className="qr-label text-right py-1 px-2">Cum P&L</th>
              </>
            )}
          </tr>
        </thead>
        <tbody className="divide-y divide-white/[0.04]">
          {rows.map((s, i) => (
            <tr key={`${s.strategy_id}-${i}`} className="qr-tr-hover">
              <td className="py-1 px-2 text-[10px] text-slate-500 w-6">{i + 1}</td>
              <td className="py-1 px-2 text-[11px] text-white max-w-[220px] truncate" title={s.strategy_id}>
                {s.name || (s.strategy_id ? s.strategy_id : 'Manual / unattributed')}
              </td>
              {isFills ? (
                <>
                  <td className="py-1 px-2 qr-num text-slate-300">{s.fills}</td>
                  <td className="py-1 px-2 qr-num text-slate-300">{s.symbols}</td>
                  <td className="py-1 px-2 qr-num text-[10px] text-slate-400">
                    {s.last_fill_at ? s.last_fill_at.slice(0, 10) : '—'}
                  </td>
                </>
              ) : (
                <>
                  <td className="py-1 px-2 qr-num text-slate-300">{s.closed_trades}</td>
                  <td className="py-1 px-2 qr-num text-slate-400">{s.win_rate != null ? `${s.win_rate}%` : '—'}</td>
                  <td className={`py-1 px-2 qr-num ${pnlCl(s.ytd_pnl)}`}>{s.ytd_pnl != null ? fmtUsd(s.ytd_pnl) : '—'}</td>
                  <td className={`py-1 px-2 qr-num font-bold ${pnlCl(s.cum_pnl)}`}>{s.cum_pnl != null ? fmtUsd(s.cum_pnl) : '—'}</td>
                </>
              )}
            </tr>
          ))}
        </tbody>
      </table>
    )}
  </div>
);

const byCumDesc = (a, b) => (b.cum_pnl ?? -Infinity) - (a.cum_pnl ?? -Infinity);
const byCumAsc = (a, b) => (a.cum_pnl ?? Infinity) - (b.cum_pnl ?? Infinity);

export const BookOverview = ({ book }) => {
  const [data, setData] = useState(null);
  const supported = SUPPORTED_BOOKS.has(book);
  usePoll(async () => {
    if (!supported) return;
    const res = await api.get(`/api/execution/book-overview?book=${book}`);
    if (res) setData(res);
  }, 60000);

  const stats = data?.stats;
  const isFills = data?.strategy_metric === 'fills';
  const best = [...(data?.top_strategies || [])].sort(byCumDesc);
  const worstRaw = data?.worst_strategies; // backend t_5ee7db98 — live on sim/paper books
  const worst = Array.isArray(worstRaw) ? [...worstRaw].sort(byCumAsc) : null;

  const livePending = 'Book overview is not served for the live book';
  const liveTip = 'GET /api/execution/book-overview covers sim / paper / uat; a live-book overview endpoint is pending';

  // Best card state
  const bestPending = !supported ? livePending : null;
  const bestTip = !supported ? liveTip : undefined;
  const bestTitle = isFills ? 'Strategy Activity' : 'Best Performing Strategies';
  const bestSub = isFills
    ? 'ranked by fills · round-trip P&L pending'
    : 'ranked by all-time realized P&L · closed trades only';
  const bestEmpty = isFills ? 'No UAT fills attributed to strategies yet' : 'No closed trades yet';

  // Worst card state
  let worstPending = null, worstTip;
  if (!supported) {
    worstPending = livePending; worstTip = liveTip;
  } else if (isFills) {
    worstPending = 'Worst-performing ranking undefined on a fills-only ledger';
    worstTip = 'UAT fills carry no round-trip P&L — the per-strategy UAT round-trip ledger is qr_etl\'s domain';
  } else if (data && worst == null) {
    worstPending = 'Worst-performer ranking not served yet';
    worstTip = 'Waiting on backend field worst_strategies in /api/execution/book-overview (qr_etl t_5ee7db98)';
  }

  return (
    <div className="space-y-3">
      {/* 1 — Strategy performance, split best / worst */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-3">
        <StrategyPerfCard
          title={bestTitle} sub={bestSub} rows={best} isFills={isFills}
          loading={supported && !data} pendingText={bestPending} pendingTip={bestTip} emptyText={bestEmpty}
        />
        <StrategyPerfCard
          title="Worst Performing Strategies"
          sub="lowest all-time realized P&L · closed trades only"
          rows={worst || []} isFills={false}
          loading={false} pendingText={worstPending} pendingTip={worstTip} emptyText={bestEmpty}
        />
      </div>

      {/* 2 — Stats strip */}
      <div className="grid grid-cols-3 sm:grid-cols-6 gap-1.5">
        {!supported ? (
          <>
            <StatTile label="YTD P&L" value="—" tone="text-slate-500" title={liveTip} />
            <StatTile label="Today" value="—" tone="text-slate-500" title={liveTip} />
            <StatTile label="Win Rate" value="—" tone="text-slate-500" title={liveTip} />
            <StatTile label="Closed" value="—" tone="text-slate-500" title={liveTip} />
            <StatTile label="Open" value="—" tone="text-slate-500" title={liveTip} />
            <StatTile label="Cum P&L" value="—" tone="text-slate-500" title={liveTip} />
          </>
        ) : isFills ? (
          <>
            <StatTile label="Total Fills" value={stats?.total_fills ?? '—'} />
            <StatTile label="Fills YTD" value={stats?.ytd_trades ?? '—'} />
            <StatTile label="Fills Today" value={stats?.today?.trades ?? 0} />
            <StatTile label="Last Fill" value={stats?.last_fill_at ? stats.last_fill_at.slice(5, 10) : '—'} tone="text-slate-400" />
            <StatTile label="YTD P&L" value="—" tone="text-slate-500" title="Round-trip P&L pending — UAT ledger is fills-only" />
            <StatTile label="Win Rate" value="—" tone="text-slate-500" title="Pending — UAT ledger is fills-only" />
          </>
        ) : (
          <>
            <StatTile label="YTD P&L" value={stats ? fmtUsd(stats.ytd_pnl) : '…'} tone={pnlCl(stats?.ytd_pnl)}
              title={`Realized, ${stats?.ytd_trades ?? 0} closed trades since Jan 1`} />
            <StatTile label="Today" value={stats?.today ? fmtUsd(stats.today.pnl) : '—'} tone={pnlCl(stats?.today?.pnl)}
              title={stats?.today ? `${stats.today.trades} exits today` : 'No exits today'} />
            <StatTile label="Win Rate" value={stats?.win_rate != null ? `${stats.win_rate}%` : '—'}
              title="Share of closed trades with positive P&L" />
            <StatTile label="Closed" value={stats?.closed_trades ?? '—'} tone="text-slate-300" />
            <StatTile label="Open" value={stats?.open_trades ?? '—'} tone="text-slate-300" />
            <StatTile label="Cum P&L" value={stats ? fmtUsd(stats.cum_pnl) : '…'} tone={pnlCl(stats?.cum_pnl)}
              title="All-time realized P&L" />
          </>
        )}
      </div>

      {/* 3 — Cumulative returns, YTD in dollars (full page width) */}
      <div className="qr-surface overflow-hidden">
        <div className="px-3 py-2 border-b border-white/[0.05] flex items-center justify-between">
          <span className="qr-label">Cumulative Returns · YTD ($)</span>
          {stats?.ytd_pnl != null && (
            <span className={`qr-num text-[11px] font-bold ${pnlCl(stats.ytd_pnl)}`}>{fmtUsd(stats.ytd_pnl)}</span>
          )}
        </div>
        <div className="px-2 py-1">
          {!supported ? (
            <PendingBody text={livePending} tip={liveTip} />
          ) : !data ? (
            <div className="py-6 text-center text-slate-600 text-[11px]">Loading…</div>
          ) : isFills ? (
            <PendingBody
              text="UAT ledger is fills-only — cumulative P&L curve needs the round-trip ledger"
              tip="Round-trip UAT P&L is qr_etl's domain — never derived serve-time"
            />
          ) : (data.ytd_curve || []).length < 2 ? (
            <div className="py-6 text-center text-slate-600 text-[11px]">No realized P&L this year</div>
          ) : (
            <YtdChart curve={data.ytd_curve} />
          )}
        </div>
      </div>
    </div>
  );
};

export default BookOverview;
