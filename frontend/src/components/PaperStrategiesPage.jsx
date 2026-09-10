import React, { useState } from 'react';
import {
  usePaperSystemStatus,
  usePaperOpenPositions,
  usePaperDailyRuns,
  usePaperTradeHistory,
  usePaperTradeSummary,
  usePaperSignalProximity,
  usePaperOpenPositionsPnl,
} from './paper/usePaperData';
import {
  OpenPositionsTable,
  OpenPositionsPnlPanel,
  SignalProximityPanel,
  DailyRunCards,
  TradeHistoryTable,
} from './paper';
import { ExecScaffold, ExecStat, ExecTabs } from './execution/ExecScaffold';
import { fmtK, pnlCl, fetchWithTimeout } from '../utils';

// Unified anatomy (2026-08-26): same tabbed surface as the Live book.
// Tab bodies lazy-mount so their hooks only fire when the tab is selected —
// this replaces the old PaperLowerPanels settle-gate (t_87ccf8a4): the mount
// fan-out is now 3 endpoints (status + positions + pnl), the rest on demand.

// Tab bodies are separate components so their data hooks mount with the tab.
const PaperSignalsTab = () => {
  const { data } = usePaperSignalProximity();
  return <SignalProximityPanel data={data} />;
};
const PaperRunsTab = () => {
  const { data } = usePaperDailyRuns();
  return <DailyRunCards data={data} />;
};
const PaperHistoryTab = () => {
  const { data: history } = usePaperTradeHistory();
  const { data: summary } = usePaperTradeSummary();
  return <TradeHistoryTable history={history} summary={summary} />;
};

export default function PaperStrategiesPage() {
  const [tab, setTab] = useState('positions');
  const { data: systemStatus, degraded, error: statusError } = usePaperSystemStatus();
  const { data: openPositions, refetch: refetchPositions, error: posError, loading: posLoading } = usePaperOpenPositions();
  const { data: openPositionsPnl } = usePaperOpenPositionsPnl();

  // Per-row close — DB close on the paper book (no IBKR involved).
  // Endpoint contract filed as qr_etl t_02073f2e; 404 renders an honest pending note.
  const [closeState, setCloseState] = useState(null); // { id, busy, msg }
  const closePosition = async (p) => {
    const size = p.shares ?? p.contracts ?? '?';
    if (!window.confirm(`Close paper position ${p.ticker} (${p.direction} ${size}) at the latest mark?`)) return;
    setCloseState({ id: p.id, busy: true, msg: null });
    try {
      const res = await fetchWithTimeout('/api/agents/paper/close-position', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ position_id: p.id }),
      }, 20000);
      const body = await res.json().catch(() => ({}));
      if (res.ok) {
        setCloseState({ id: p.id, busy: false, msg: { type: 'success', text: `Closed @ ${body.closing_price ?? 'mark'}` } });
        refetchPositions?.();
      } else if (res.status === 404) {
        setCloseState({ id: p.id, busy: false, msg: { type: 'error', text: 'Close API pending · t_02073f2e' } });
      } else {
        setCloseState({ id: p.id, busy: false, msg: { type: 'error', text: body.detail || 'Close failed' } });
      }
    } catch (e) {
      setCloseState({ id: p.id, busy: false, msg: { type: 'error', text: e.message || 'Network error' } });
    }
  };

  const positions = openPositions?.positions || [];
  const totPnl = positions.reduce((a, p) => a + (p.unrealised_pnl || 0), 0);
  const degradedMode = degraded || (systemStatus && systemStatus.db === 'unreachable') || systemStatus?.state === 'error';

  const navUsd = systemStatus?.paper_nav_usd;
  const regime = systemStatus?.regime_label;
  const lastRun = systemStatus?.last_run_type
    ? `${systemStatus.last_run_type} ${systemStatus.last_run_status || ''} ${systemStatus.last_run_date || ''}`.trim()
    : null;

  const tabs = [
    { id: 'positions', label: `Positions (${posLoading && !openPositions ? '…' : positions.length})`, badge: posError ? 'qr-chip-rose' : null, badgeText: 'ERR' },
    { id: 'signals',   label: 'Signals' },
    { id: 'runs',      label: 'Runs' },
    { id: 'history',   label: 'History' },
  ];

  return (
    <ExecScaffold
      mode="paper"
      book="paper"
      stats={<>
        <ExecStat l="Open Positions" v={posLoading && !openPositions ? '…' : positions.length} />
        <ExecStat l="Unrealized P&L" v={`${totPnl >= 0 ? '+' : ''}${fmtK(totPnl)}`} tone={pnlCl(totPnl)} />
        <ExecStat l="NAV (USD)" v={navUsd != null ? fmtK(navUsd) : '—'} tone="text-slate-400" />
        <ExecStat
          l="Regime"
          v={regime || '—'}
          tone={systemStatus?.regime_staleness_days > 0 ? 'text-rose-400' : 'text-slate-400'}
        />
        <ExecStat l="Last Run" v={lastRun || '—'} tone="text-slate-400" />
      </>}
    >
      <div className="qr-surface overflow-hidden">
        <ExecTabs
          tabs={tabs}
          active={tab}
          onChange={setTab}
          right={degradedMode && (
            <span
              className="qr-chip qr-chip-rose"
              title={statusError?.retryAfter ? `Database unreachable — retrying in ${Math.round(statusError.retryAfter / 1000)}s` : 'Paper system status unavailable'}
            >
              DEGRADED
            </span>
          )}
        />
      </div>

      {tab === 'positions' && (
        <>
          <OpenPositionsTable data={openPositions} onClose={closePosition} closeState={closeState} loading={posLoading} error={posError} />
          <OpenPositionsPnlPanel data={openPositionsPnl} />
        </>
      )}
      {tab === 'signals' && <PaperSignalsTab />}
      {tab === 'runs' && <PaperRunsTab />}
      {tab === 'history' && <PaperHistoryTab />}
    </ExecScaffold>
  );
}
