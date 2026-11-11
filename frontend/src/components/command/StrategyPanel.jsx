// Command center — ROW 2A STRATEGY PERFORMANCE. One compact row per
// strategy, split ACTIVE (open holdings) vs HISTORICAL (closed ledger only).
// Realized P&L comes from the authoritative full-ledger aggregate
// (/api/execution/strategy-pnl) — never from a truncated trades page.
// Contribution is a percentage ONLY when the book unrealized total is a
// meaningful positive base; otherwise the signed currency contribution shows.

import React, { useMemo } from 'react';
import { fmtKCcy, pnlCl } from '../../utils';
import { Panel, EnvChip, NoData, HBar, LinkBtn } from './shared';
import { sK, sCcy } from './format';
import { SEV_TAG } from './meta';
import { buildStrategyRows, contribution, reconcileRealized } from './aggregate';

const StratRow = ({ g, defCcy, totalUn, onSelectStrategy }) => {
  const contrib = g.unN > 0 ? contribution(g.unreal, totalUn) : { mode: 'none' };
  return (
    <tr className="border-t border-white/[0.05] text-[13px] leading-5 hover:bg-white/[0.02]">
      <td className="px-4 py-1.5 max-w-[220px] truncate" title={g.name ? `${g.name} — open strategy detail` : 'No strategy attribution for these rows'}>
        {g.id ? (
          <button onClick={() => onSelectStrategy?.(g.id)}
            className="text-[12px] font-bold text-blue-400 hover:text-blue-300 truncate max-w-full" title={`${g.name} — open strategy detail`}>
            {g.name}
          </button>
        ) : (
          <span className="text-[12px] font-bold text-slate-200">{g.name || 'Unattributed'}</span>
        )}
      </td>
      <td className="px-3 py-1.5 text-right font-mono text-slate-300">{g.open}</td>
      <td className="px-3 py-1.5 text-right font-mono text-slate-300">{g.mvN > 0 ? fmtKCcy(g.mv, defCcy) : '—'}</td>
      <td className={`px-3 py-1.5 text-right font-mono font-bold ${g.unN > 0 ? pnlCl(g.unreal) : 'text-slate-600'}`}>{g.unN > 0 ? sK(g.unreal) : '—'}</td>
      <td className={`px-3 py-1.5 text-right font-mono ${g.realized != null ? pnlCl(g.realized) : 'text-slate-600'}`}
        title={g.closed != null ? `${g.closed} closed trades · all-time realized (full-ledger aggregate)${g.ytdRealized != null ? ` · YTD ${sK(g.ytdRealized)}` : ''}` : 'No closed trades for this strategy in the ledger'}>
        {g.realized != null ? sK(g.realized) : '—'}
      </td>
      <td className="px-3 py-1.5 w-[110px]">
        {contrib.mode === 'pct' ? (
          <span className="flex items-center gap-1.5" title="Unrealized contribution: strategy unrealized ÷ book unrealized (open positions)">
            <span className="w-[56px]"><HBar pct={Math.abs(contrib.pct)} /></span>
            <span className={`font-mono text-[11px] ${pnlCl(contrib.pct)}`}>{contrib.pct >= 0 ? '+' : ''}{contrib.pct.toFixed(0)}%</span>
          </span>
        ) : contrib.mode === 'amount' ? (
          <span className={`font-mono text-[11px] ${pnlCl(contrib.amount)}`}
            title="Book unrealized total is zero, negative, or near zero — a percentage would mislead; showing the signed currency contribution instead">
            {sCcy(contrib.amount, defCcy)}
          </span>
        ) : <span className="text-slate-600">—</span>}
      </td>
      <td className="px-4 py-1.5">
        {g.risk
          ? <span className={`text-[10px] px-1.5 py-0.5 rounded border ${SEV_TAG[g.risk.sev] || SEV_TAG.warning}`} title={g.risk.tip}>{g.risk.label}</span>
          : <span className="text-[11px] text-slate-600">—</span>}
      </td>
    </tr>
  );
};

const SectionHead = ({ label, count }) => (
  <tr className="bg-white/[0.02]">
    <td colSpan={7} className="px-4 py-1 text-[10px] font-bold uppercase tracking-wider text-slate-500">
      {label} <span className="font-mono font-normal">{count}</span>
    </td>
  </tr>
);

export const StrategyPanel = ({ env, rows, stratPnl, bookCumPnl, riskBy, defCcy, navigateToTab, onSelectStrategy, noDataText }) => {
  const groups = useMemo(() => {
    if (!rows && !stratPnl) return null;
    return buildStrategyRows({ posRows: rows || [], stratPnl, riskBy });
  }, [rows, stratPnl, riskBy]);

  // Reconciliation: Σ per-strategy realized (full-ledger aggregate) must tie
  // to the book-level cumulative realized P&L from book-overview.
  const recon = useMemo(() => reconcileRealized(stratPnl?.total_cum_pnl, bookCumPnl), [stratPnl, bookCumPnl]);

  if (noDataText) return <Panel title={<>Strategy Performance <EnvChip env={env} /></>}><NoData>{noDataText}</NoData></Panel>;
  if (!groups) return <Panel title={<>Strategy Performance <EnvChip env={env} /></>}><NoData>Loading…</NoData></Panel>;

  const ACTIVE_CAP = 10, HIST_CAP = 5;
  const active = groups.active.slice(0, ACTIVE_CAP);
  const hist = groups.historical.slice(0, HIST_CAP);
  const restActive = groups.active.length - active.length;
  const restHist = groups.historical.length - hist.length;
  const restRows = [...groups.active.slice(ACTIVE_CAP), ...groups.historical.slice(HIST_CAP)];
  const restUn = restRows.reduce((s, g) => s + g.unreal, 0);
  const restRe = restRows.reduce((s, g) => s + (g.realized ?? 0), 0);
  const restN = restActive + restHist;

  return (
    <Panel title={<>Strategy Performance <EnvChip env={env} /></>} action={
      <span className="flex items-center gap-3">
        {recon && (
          <span className={`text-[11px] ${recon.ok ? 'text-slate-500' : 'text-rose-300 font-bold'}`}
            title={recon.ok
              ? 'Σ per-strategy realized (full-ledger aggregate) reconciles exactly with the book cumulative realized P&L'
              : `Σ per-strategy realized differs from book cumulative realized P&L by ${recon.delta} — investigate`}>
            {recon.ok ? 'ledger ✓ reconciled' : `recon Δ ${recon.delta}`}
          </span>
        )}
        <span className="text-[11px] text-slate-500" title={stratPnl != null
          ? "Open count / market value / unrealized: aggregated from the open positions below. Realized: authoritative per-strategy aggregate over the FULL closed ledger (/api/execution/strategy-pnl — no row cap). Contribution: strategy unrealized ÷ book unrealized (percentage only when the book total is a meaningful positive base)."
          : "Open count / market value / unrealized: aggregated from the open positions below. Contribution: strategy unrealized ÷ book unrealized (percentage only when the book total is a meaningful positive base)."}>open rows ⓘ</span>
        <LinkBtn onClick={() => navigateToTab('strategies')}>Strategies →</LinkBtn>
      </span>
    }>
      {groups.active.length === 0 && groups.historical.length === 0 ? (
        <NoData>Book flat — no open positions to attribute.</NoData>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full min-w-[760px]">
            <thead>
              <tr className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider bg-white/[0.02]">
                <th className="text-left px-4 py-1.5">Strategy</th>
                <th className="text-right px-3 py-1.5">Open</th>
                <th className="text-right px-3 py-1.5" title="Sum of market value over the strategy's open positions">Mkt value</th>
                <th className="text-right px-3 py-1.5" title="Sum of unrealized P&L over open positions">Unrealized</th>
                <th className="text-right px-3 py-1.5" title="Cumulative realized P&L — full closed-ledger aggregate per strategy">Realized · cum</th>
                <th className="text-left px-3 py-1.5" title="Strategy share of book unrealized P&L — percentage only when the book total is a meaningful positive base; signed currency amount otherwise">Contrib</th>
                <th className="text-left px-4 py-1.5">Risk</th>
              </tr>
            </thead>
            <tbody>
              {active.length > 0 && <SectionHead label="Active — open holdings" count={groups.active.length} />}
              {active.map(g => <StratRow key={g.key} g={g} defCcy={defCcy} totalUn={groups.totalUn} onSelectStrategy={onSelectStrategy} />)}
              {hist.length > 0 && <SectionHead label="Historical — closed ledger" count={groups.historical.length} />}
              {hist.map(g => <StratRow key={g.key} g={g} defCcy={defCcy} totalUn={groups.totalUn} onSelectStrategy={onSelectStrategy} />)}
            </tbody>
          </table>
          {restN > 0 && (
            <div className="px-4 py-2 border-t border-white/[0.05] text-[11px] text-slate-500">
              +{restN} more strateg{restN === 1 ? 'y' : 'ies'} · unrealized Σ <span className={`font-mono ${pnlCl(restUn)}`}>{sK(restUn)}</span> · realized Σ <span className={`font-mono ${pnlCl(restRe)}`}>{sK(restRe)}</span>
            </div>
          )}
        </div>
      )}
    </Panel>
  );
};
