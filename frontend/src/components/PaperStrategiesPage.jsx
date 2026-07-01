import React from 'react';
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
  SystemStatusBar,
  OpenPositionsTable,
  OpenPositionsPnlPanel,
  SignalProximityPanel,
  DailyRunCards,
  TradeHistoryTable,
} from './paper';
import { ManualTicket } from './ManualTicket';

export default function PaperStrategiesPage({ globalMode }) {
  const { data: systemStatus } = usePaperSystemStatus();
  const { data: openPositions } = usePaperOpenPositions();
  const { data: openPositionsPnl } = usePaperOpenPositionsPnl();
  const { data: signalProximity } = usePaperSignalProximity();
  const { data: dailyRuns } = usePaperDailyRuns();
  const { data: tradeHistory } = usePaperTradeHistory();
  const { data: tradeSummary } = usePaperTradeSummary();

  return (
    <div className="space-y-4">
      <h2 className="text-lg font-bold text-white mb-4">Paper Trading</h2>
      <div className="grid grid-cols-1 lg:grid-cols-[1fr_300px] gap-3 items-start">
        <div className="space-y-4">
          <SystemStatusBar data={systemStatus} />
          <OpenPositionsTable data={openPositions} />
          <OpenPositionsPnlPanel data={openPositionsPnl} />
          <SignalProximityPanel data={signalProximity} />
          <DailyRunCards data={dailyRuns} />
          <TradeHistoryTable history={tradeHistory} summary={tradeSummary} />
        </div>
        <ManualTicket book="paper" globalMode={globalMode} />
      </div>
    </div>
  );
}
