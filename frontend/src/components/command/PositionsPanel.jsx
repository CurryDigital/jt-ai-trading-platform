// Command center — ROW 3 INVESTIGATION. Full-width Open Positions: ENTRY
// DATE leftmost, strategy filter, sort control, 16-row real pagination,
// strategy grouping (collapsed subtotal headers; expand a group to see its
// rows). Totals footer sums per currency — never across currencies.

import React, { useMemo, useState } from 'react';
import { fmtK, fmtKCcy, pnlCl } from '../../utils';
import { Panel, EnvChip, NoData, AsOf, PageBtn, LinkBtn, selectCl } from './shared';
import { sK, sCcy } from './format';
import { POSITIONS_PAGE, POSITIONS_HEAD, SORTS } from './meta';
import { sumByCcy } from './aggregate';

const PositionsTotals = ({ rows, defCcy }) => {
  const unreal = sumByCcy(rows, 'unreal', defCcy);
  const mv = sumByCcy(rows, 'mv', defCcy);
  if (unreal.sums.length === 0 && mv.sums.length === 0) return null;
  return (
    <div className="flex items-center gap-x-5 gap-y-1 flex-wrap px-4 py-2.5 border-t border-white/[0.06] bg-white/[0.02] text-[12px]">
      <span className="text-slate-400">{rows.length} open</span>
      {unreal.sums.length > 0 && (
        <span className="flex items-center gap-1.5" title={unreal.skipped > 0 ? `${unreal.skipped} position(s) without a mark excluded` : 'Sum of unrealized P&L over open positions — per currency, never netted across currencies'}>
          <span className="text-slate-400 uppercase tracking-wider text-[11px]">Unrealized Σ</span>
          {unreal.sums.map(([c, v]) => (
            <span key={c} className={`font-mono font-bold ${pnlCl(v)}`}>{sCcy(v, c)}</span>
          ))}
        </span>
      )}
      {mv.sums.length > 0 && (
        <span className="flex items-center gap-1.5" title={mv.skipped > 0 ? `${mv.skipped} position(s) without a market value excluded` : 'Sum of market value over open positions — per currency, never netted across currencies'}>
          <span className="text-slate-400 uppercase tracking-wider text-[11px]">Market value Σ</span>
          {mv.sums.map(([c, v]) => (
            <span key={c} className="font-mono text-slate-200">{fmtKCcy(v, c)}</span>
          ))}
        </span>
      )}
    </div>
  );
};

const PositionRow = ({ p }) => (
  <tr className="border-t border-white/[0.05] text-[13px] leading-5 hover:bg-white/[0.02]">
    <td className="px-4 py-2 font-mono text-slate-300 whitespace-nowrap" title={p.entryTip || undefined}>
      {p.entryDate ?? '—'}
    </td>
    <td className="px-3 py-2 font-mono font-bold text-white whitespace-nowrap">
      {p.symbol}
      {p.ccy && <span className="text-[11px] font-normal text-slate-500 ml-1.5">{p.ccy}</span>}
    </td>
    <td className="px-3 py-2 text-[12px] text-slate-400 max-w-[260px] truncate" title={p.strategyTip || p.strategy || undefined}>
      {p.strategy ?? '—'}
    </td>
    <td className="px-3 py-2 font-mono font-bold text-slate-300">{p.side ?? '—'}</td>
    <td className="px-3 py-2 text-right font-mono text-slate-200" style={{ fontVariantNumeric: 'tabular-nums' }}>{p.qty != null ? Math.abs(p.qty).toLocaleString() : '—'}</td>
    <td className="px-3 py-2 text-right font-mono text-slate-300" style={{ fontVariantNumeric: 'tabular-nums' }}>{p.entryPx != null ? p.entryPx.toLocaleString(undefined, { maximumFractionDigits: 2 }) : '—'}</td>
    <td className="px-3 py-2 text-right font-mono text-slate-300" style={{ fontVariantNumeric: 'tabular-nums' }} title={p.curTip || undefined}>
      {p.curPx != null ? p.curPx.toLocaleString(undefined, { maximumFractionDigits: 2 }) : '—'}
    </td>
    <td className={`px-3 py-2 text-right font-mono font-bold whitespace-nowrap ${p.unreal != null ? pnlCl(p.unreal) : 'text-slate-600'}`} style={{ fontVariantNumeric: 'tabular-nums' }}>
      {p.unreal != null ? sK(p.unreal) : '—'}
    </td>
    <td className="px-3 py-2 text-right font-mono text-slate-300" style={{ fontVariantNumeric: 'tabular-nums' }}>{p.mv != null ? fmtK(p.mv) : '—'}</td>
    <td className="px-3 pr-4 py-2 text-right font-mono text-[12px] text-slate-400" title={p.entryTip || undefined}>
      {p.days != null ? p.days : '—'}
    </td>
  </tr>
);

const PositionsHead = () => (
  <thead className="sticky top-0 z-10">
    <tr className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
      {POSITIONS_HEAD.map(h => (
        <th key={h.k} className={`bg-[#0a0d12] ${h.align === 'right' ? 'text-right' : 'text-left'} ${h.k === 'entry' ? 'px-4' : 'px-3'} py-2 ${h.k === 'days' ? 'pr-4' : ''}`}
          title={h.k === 'entry' || h.k === 'days' ? 'Absolute entry date (YYYY-MM-DD), newest first where the environment serves entry dates' : undefined}>
          {h.label}
        </th>
      ))}
    </tr>
  </thead>
);

export const PositionsPanel = ({ env, rows, count, asOf, headTip, note, emptyText, defCcy, navigateToTab }) => {
  const [page, setPage] = useState(0);
  const [strat, setStrat] = useState('all');
  const [sortK, setSortK] = useState('entry');
  const [grouped, setGrouped] = useState(false);
  const [openGroups, setOpenGroups] = useState(() => new Set());

  const strategies = useMemo(() => {
    if (!rows) return [];
    return [...new Set(rows.map(p => p.strategy).filter(Boolean))].sort();
  }, [rows]);

  const filtered = useMemo(() => {
    if (!rows) return null;
    const f = strat === 'all' ? rows : rows.filter(p => (p.strategy || '') === strat);
    return [...f].sort(SORTS[sortK].fn);
  }, [rows, strat, sortK]);

  const nPages = filtered && filtered.length > 0 ? Math.ceil(filtered.length / POSITIONS_PAGE) : 1;
  const cur = Math.min(page, nPages - 1);
  const visible = filtered == null ? null : filtered.slice(cur * POSITIONS_PAGE, (cur + 1) * POSITIONS_PAGE);
  const from = filtered && filtered.length > 0 ? cur * POSITIONS_PAGE + 1 : 0;
  const to = filtered && filtered.length > 0 ? Math.min(filtered.length, (cur + 1) * POSITIONS_PAGE) : 0;

  // Grouped view: per-strategy subtotal headers, collapsed by default.
  const groups = useMemo(() => {
    if (!grouped || !filtered) return null;
    const m = new Map();
    for (const p of filtered) {
      const k = p.strategy || 'Unattributed';
      if (!m.has(k)) m.set(k, { name: k, rows: [], mv: 0, mvN: 0, unreal: 0, unN: 0 });
      const g = m.get(k);
      g.rows.push(p);
      if (p.mv != null && !isNaN(p.mv)) { g.mv += p.mv; g.mvN += 1; }
      if (p.unreal != null && !isNaN(p.unreal)) { g.unreal += p.unreal; g.unN += 1; }
    }
    return [...m.values()].sort((a, b) => Math.abs(b.unreal) - Math.abs(a.unreal));
  }, [grouped, filtered]);

  const toggleGroup = (name) => {
    setOpenGroups(prev => {
      const next = new Set(prev);
      if (next.has(name)) next.delete(name); else next.add(name);
      return next;
    });
  };

  const pager = nPages > 1 && !grouped ? (
    <span className="flex items-center gap-2 flex-none">
      <PageBtn disabled={cur === 0} onClick={() => setPage(cur - 1)}>‹ Prev</PageBtn>
      <span className="font-mono text-[11px] text-slate-400 whitespace-nowrap" title={`Page ${cur + 1} of ${nPages} · ${POSITIONS_PAGE} rows per page`}>
        {from}–{to} of {filtered.length}
      </span>
      <PageBtn disabled={cur >= nPages - 1} onClick={() => setPage(cur + 1)}>Next ›</PageBtn>
    </span>
  ) : null;

  return (
    <Panel title={<>Open Positions <EnvChip env={env} /></>} action={
      <span className="flex items-center gap-3 flex-wrap justify-end">
        <span className="text-[11px] text-slate-400" title={headTip}>{count != null ? `${count} open` : ''}{note ? ` · ${note}` : ''}</span>
        <AsOf ts={asOf} />
        {strategies.length > 1 && (
          <select className={selectCl} value={strat} onChange={e => { setStrat(e.target.value); setPage(0); }} title="Filter by strategy">
            <option value="all">All strategies</option>
            {strategies.map(s => <option key={s} value={s}>{s}</option>)}
          </select>
        )}
        <select className={selectCl} value={sortK} onChange={e => { setSortK(e.target.value); setPage(0); }} title="Sort rows">
          {Object.entries(SORTS).map(([k, s]) => <option key={k} value={k}>{s.label}</option>)}
        </select>
        {strategies.length > 1 && (
          <button onClick={() => setGrouped(g => !g)}
            className={`px-2.5 py-1 text-[12px] font-semibold rounded border ${grouped ? 'border-white/[0.25] text-white bg-white/[0.08]' : 'border-white/[0.10] text-slate-300 hover:bg-white/[0.06]'}`}
            title="Group rows by strategy — collapsed subtotal headers; expand a group to see its rows">
            Group: strategy
          </button>
        )}
        {pager}
        <LinkBtn onClick={() => navigateToTab('execution')}>Execution →</LinkBtn>
      </span>
    }>
      {rows == null ? (
        <NoData>Loading…</NoData>
      ) : rows.length > 0 ? (
        <div className="overflow-x-auto">
          <table className="w-full min-w-[980px]">
            <PositionsHead />
            {grouped && groups ? (
              <tbody>
                {groups.map(g => {
                  const open = openGroups.has(g.name);
                  return (
                    <React.Fragment key={g.name}>
                      <tr className="border-t border-white/[0.08] bg-white/[0.03] hover:bg-white/[0.05] cursor-pointer" onClick={() => toggleGroup(g.name)}
                        title={`${g.rows.length} open · click to ${open ? 'collapse' : 'expand'}`}>
                        <td className="px-4 py-2 text-[12px] font-bold text-slate-100" colSpan={3}>
                          <span className="font-mono text-slate-500 mr-2">{open ? '▾' : '▸'}</span>
                          {g.name}
                          <span className="ml-2 font-mono text-[11px] font-normal text-slate-500">{g.rows.length} open</span>
                        </td>
                        <td colSpan={4} />
                        <td className={`px-3 py-2 text-right font-mono font-bold text-[12px] ${g.unN > 0 ? pnlCl(g.unreal) : 'text-slate-600'}`}>{g.unN > 0 ? sK(g.unreal) : '—'}</td>
                        <td className="px-3 py-2 text-right font-mono text-[12px] text-slate-300">{g.mvN > 0 ? fmtK(g.mv) : '—'}</td>
                        <td className="pr-4" />
                      </tr>
                      {open && g.rows.map((p, i) => <PositionRow key={p.key || `${p.symbol}-${i}`} p={p} />)}
                    </React.Fragment>
                  );
                })}
              </tbody>
            ) : (
              <tbody>
                {(visible || []).map((p, i) => <PositionRow key={p.key || `${p.symbol}-${i}`} p={p} />)}
              </tbody>
            )}
          </table>
          <PositionsTotals rows={filtered || []} defCcy={defCcy} />
          {nPages > 1 && !grouped && (
            <div className="flex items-center justify-center gap-3 px-4 py-2.5 border-t border-white/[0.05]">
              {pager}
            </div>
          )}
        </div>
      ) : (
        <NoData>{emptyText}</NoData>
      )}
    </Panel>
  );
};
