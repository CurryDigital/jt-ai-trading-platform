import React, { useState, useEffect, useMemo } from 'react';

// Strategy-Specific Signal Metrics Display
const StrategySignalMetrics = ({ signal, strategyId, isActive }) => {
  if (!signal || !signal.metrics) return null;

  const m = signal.metrics;
  const isSell = isActive;
  const strength = signal.signal_strength || 0;
  const pnlPct = m.pnl_pct;

  // Check for take profit / stop loss signals
  const isTakeProfit = signal.message?.includes('TAKE PROFIT');
  const isStopLoss = signal.message?.includes('STOP LOSS');
  const isProfitable = pnlPct > 0;

  // Override colors for take profit / stop loss
  let strengthColor, barColor, borderColor, labelText;

  if (isTakeProfit) {
    strengthColor = 'text-emerald-400';
    barColor = 'bg-emerald-500';
    borderColor = 'border-emerald-500/50 bg-emerald-500/20';
    labelText = '🎯 TAKE PROFIT TRIGGERED';
  } else if (isStopLoss) {
    strengthColor = 'text-rose-400';
    barColor = 'bg-rose-500';
    borderColor = 'border-rose-500/50 bg-rose-500/20';
    labelText = '🛑 STOP LOSS TRIGGERED';
  } else if (isProfitable) {
    strengthColor = 'text-emerald-400';
    barColor = 'bg-emerald-500';
    borderColor = 'border-emerald-500/30 bg-emerald-500/10';
    labelText = isSell ? '📈 Approaching Take Profit (+5%)' : '📈 Buy Signal';
  } else {
    strengthColor = 'text-rose-400';
    barColor = 'bg-rose-500';
    borderColor = 'border-rose-500/30 bg-rose-500/10';
    labelText = isSell ? '📉 Approaching Stop Loss (-5%)' : '📉 Buy Signal';
  }

  // Show P&L progress bar toward targets
  let progressText = '';
  if (pnlPct !== undefined) {
    if (isProfitable) {
      progressText = `+${pnlPct.toFixed(2)}% toward +5% target`;
    } else {
      progressText = `${pnlPct.toFixed(2)}% toward -5% limit`;
    }
  }

  // Determine strategy type for additional metrics
  const isRSI = strategyId?.toLowerCase().includes('rsi');
  const is3Day = strategyId?.toLowerCase().includes('3day') || strategyId?.toLowerCase().includes('three_day');
  const isGap = strategyId?.toLowerCase().includes('gap');
  const isMomentum = strategyId?.toLowerCase().includes('momentum');
  const isMACD = strategyId?.toLowerCase().includes('macd');

  // Strategy-specific additional metrics
  let additionalMetrics = null;

  if (isRSI) {
    additionalMetrics = (
      <div className="flex justify-between text-[9px] text-slate-500 mt-1">
        <span>RSI: {m.rsi?.toFixed(1) || '--'}</span>
        <span>Vol: {m.volume_spike?.toFixed(1) || '--'}x</span>
      </div>
    );
  } else if (is3Day) {
    additionalMetrics = (
      <div className="flex justify-between text-[9px] text-slate-500 mt-1">
        <span>3D Decline: {m.total_decline_pct?.toFixed(1) || '--'}%</span>
        <span>Vol: {m.volume_spike?.toFixed(1) || '--'}x</span>
      </div>
    );
  } else if (isGap) {
    additionalMetrics = (
      <div className="flex justify-between text-[9px] text-slate-500 mt-1">
        <span>Gap: {m.gap_pct?.toFixed(2) || '--'}%</span>
        <span>Prev: ${m.prev_close?.toFixed(2) || '--'}</span>
      </div>
    );
  } else if (isMomentum) {
    additionalMetrics = (
      <div className="flex justify-between text-[9px] text-slate-500 mt-1">
        <span>Momentum: {m.momentum_20d?.toFixed(1) || '--'}%</span>
        <span>Entry: ${m.price_20d_ago?.toFixed(2) || '--'}</span>
      </div>
    );
  }

  // Calculate bidirectional bar widths from center (0)
  // Left bar (rose) grows as we approach -5% stop loss
  // Right bar (emerald) grows as we approach +5% take profit
  let leftBarWidth = 0;
  let rightBarWidth = 0;
  
  if (pnlPct !== undefined) {
    const maxPnL = 5; // ±5% target/stop
    const clampedPnL = Math.max(-maxPnL, Math.min(maxPnL, pnlPct));
    
    if (clampedPnL < 0) {
      // Negative: left bar grows
      leftBarWidth = (Math.abs(clampedPnL) / maxPnL) * 50;
    } else if (clampedPnL > 0) {
      // Positive: right bar grows
      rightBarWidth = (clampedPnL / maxPnL) * 50;
    }
  }
  
  // Show current PnL value
  const pnlDisplay = pnlPct !== undefined ? `${pnlPct >= 0 ? '+' : ''}${pnlPct.toFixed(2)}%` : '0.00%';

  return (
    <div className={`mt-3 p-3 rounded-lg border ${borderColor}`}>
      <div className="flex items-center justify-between mb-2">
        <span className={`text-xs font-bold ${strengthColor}`}>{labelText}</span>
        <span className={`text-sm font-bold ${strengthColor}`}>{strength.toFixed(0)}%</span>
      </div>

      {/* Bidirectional Performance Bar - Axis at 0 */}
      <div className="relative mt-2">
        {/* Track background */}
        <div className="h-4 rounded-full bg-slate-700/50 flex items-center relative overflow-hidden">
          {/* Left side (Stop Loss) - grows from center to left */}
          <div className="absolute right-1/2 top-0.5 bottom-0.5 flex justify-end" style={{ width: '50%' }}>
            <div 
              className={`h-full rounded-l-full bg-rose-500 transition-all duration-300 ${leftBarWidth > 0 ? 'shadow-[0_0_10px_rgba(244,63,94,0.6)]' : ''}`}
              style={{ width: `${leftBarWidth}%` }}
            />
          </div>
          
          {/* Right side (Take Profit) - grows from center to right */}
          <div className="absolute left-1/2 top-0.5 bottom-0.5" style={{ width: '50%' }}>
            <div 
              className={`h-full rounded-r-full bg-emerald-500 transition-all duration-300 ${rightBarWidth > 0 ? 'shadow-[0_0_10px_rgba(16,185,129,0.6)]' : ''}`}
              style={{ width: `${rightBarWidth}%` }}
            />
          </div>
          
          {/* Center axis marker */}
          <div className="absolute left-1/2 top-0 bottom-0 w-0.5 bg-white/80 transform -translate-x-1/2 z-10" />
        </div>
        
        {/* PnL value below center */}
        <div className="flex justify-center mt-1">
          <span className={`text-xs font-bold ${pnlPct > 0 ? 'text-emerald-400' : pnlPct < 0 ? 'text-rose-400' : 'text-slate-400'}`}>
            {pnlDisplay}
          </span>
        </div>
      </div>
      
      {/* Labels below bar */}
      <div className="flex justify-between text-[9px] mt-1 text-slate-500">
        <span className="text-rose-400 font-bold">-5% Stop Loss</span>
        <span className="text-slate-400">Entry (0%)</span>
        <span className="text-emerald-400 font-bold">+5% Take Profit</span>
      </div>

      {progressText && (
        <div className="flex justify-between text-[10px] mt-2">
          <span className="text-slate-400">Entry: ${m.entry_price?.toFixed(2) || '--'}</span>
          <span className={isProfitable ? 'text-emerald-400' : 'text-rose-400'}>{progressText}</span>
        </div>
      )}

      {(m.take_profit_target || m.stop_loss_limit) && (
        <div className="flex justify-between text-[9px] mt-1">
          <span className="text-emerald-400">Target: ${m.take_profit_target?.toFixed(2) || '--'}</span>
          <span className="text-rose-400">Stop: ${m.stop_loss_limit?.toFixed(2) || '--'}</span>
        </div>
      )}

      {additionalMetrics}
    </div>
  );
};

// Price display with color-coded change
const PriceDisplay = ({ price, change, changePercent }) => {
  const isPositive = change >= 0;
  
  return (
    <div className="text-right">
      <div className="text-lg font-bold text-white">${price.toFixed(2)}</div>
      <div className={`text-xs font-bold flex items-center justify-end gap-1 ${
        isPositive ? 'text-emerald-400' : 'text-rose-400'
      }`}>
        {isPositive ? '▲' : '▼'}
        {Math.abs(change).toFixed(2)} ({Math.abs(changePercent).toFixed(2)}%)
      </div>
    </div>
  );
};

// Detailed Position KPIs Panel
const PositionKPIDetail = ({ position, priceData, onClose }) => {
  const tickerPrice = priceData?.[position.ticker];
  const currentPrice = tickerPrice?.price || 0;
  const hasTrades = position.trades_count > 0;
  
  // Calculate KPIs
  const investedPct = position.capital > 0 ? (position.invested_capital / position.capital) * 100 : 0;
  const remainingPct = 100 - investedPct;
  
  const totalPnL = position.realized_pnl + position.unrealized_pnl;
  const winRate = position.wins && position.trades_count > 0 
    ? (position.wins / position.trades_count) * 100 
    : 0;
  
  const avgWin = position.avg_win || 0;
  const avgLoss = position.avg_loss || 0;
  const profitFactor = avgLoss !== 0 ? Math.abs(avgWin / avgLoss) : 0;
  
  // Current position value
  let currentValue = position.invested_capital;
  let unrealizedPct = 0;
  if (position.entry_price && currentPrice > 0 && hasTrades) {
    const shares = position.invested_capital / position.entry_price;
    currentValue = shares * currentPrice;
    unrealizedPct = ((currentPrice - position.entry_price) / position.entry_price) * 100;
  }
  
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm"
         onClick={(e) => e.target === e.currentTarget && onClose()}>
      <div className="bg-slate-900 border border-white/10 rounded-2xl max-w-lg w-full max-h-[80vh] overflow-y-auto shadow-2xl">
        {/* Header */}
        <div className="p-6 border-b border-white/10">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <span className="text-3xl font-black text-white">{position.ticker}</span>
              <span className={`text-[10px] px-2 py-1 rounded font-bold ${
                hasTrades ? 'bg-emerald-500/20 text-emerald-400' : 'bg-amber-500/20 text-amber-400'
              }`}>
                {hasTrades ? '🟢 ACTIVE' : '⏳ PENDING'}
              </span>
            </div>
            <button onClick={onClose} className="text-slate-400 hover:text-white text-xl">✕</button>
          </div>
          <p className="text-sm text-slate-400 mt-1">{position.strategy_name}</p>
        </div>
        
        <div className="p-6 space-y-6">
          {/* Live Price Section */}
          {currentPrice > 0 && (
            <div className="bg-slate-800/50 rounded-xl p-4">
              <div className="flex items-center justify-between">
                <div>
                  <span className="text-xs text-slate-500 uppercase">Current Price</span>
                  <div className="text-2xl font-bold text-white">${currentPrice.toFixed(2)}</div>
                </div>
                <div className="text-right">
                  <span className="text-xs text-slate-500 uppercase">Daily Change</span>
                  <div className={`text-lg font-bold ${tickerPrice?.change >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                    {tickerPrice?.change >= 0 ? '+' : ''}{tickerPrice?.change?.toFixed(2)} ({tickerPrice?.changePercent?.toFixed(2)}%)
                  </div>
                </div>
              </div>
            </div>
          )}
          
          {/* Capital Allocation */}
          <div>
            <h3 className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-3">Capital Allocation</h3>
            <div className="bg-slate-800/50 rounded-xl p-4 space-y-3">
              <div>
                <div className="flex justify-between text-xs mb-1">
                  <span className="text-slate-400">Invested: {investedPct.toFixed(1)}%</span>
                  <span className="text-slate-400">Available: {remainingPct.toFixed(1)}%</span>
                </div>
                <div className="h-3 rounded-full bg-slate-700 overflow-hidden">
                  <div className="h-full bg-emerald-500 rounded-full" style={{ width: `${investedPct}%` }} />
                </div>
              </div>
              
              <div className="grid grid-cols-3 gap-3">
                <div className="text-center p-2 bg-slate-900/50 rounded">
                  <span className="text-[10px] text-slate-500 block">Total Pool</span>
                  <span className="text-sm font-bold text-white">${position.capital?.toLocaleString()}</span>
                </div>
                <div className="text-center p-2 bg-slate-900/50 rounded">
                  <span className="text-[10px] text-slate-500 block">Invested</span>
                  <span className="text-sm font-bold text-emerald-400">${position.invested_capital?.toLocaleString()}</span>
                </div>
                <div className="text-center p-2 bg-slate-900/50 rounded">
                  <span className="text-[10px] text-slate-500 block">Available</span>
                  <span className="text-sm font-bold text-blue-400">${(position.capital - position.invested_capital)?.toLocaleString()}</span>
                </div>
              </div>
            </div>
          </div>
          
          {/* Performance KPIs */}
          {hasTrades && (
            <div>
              <h3 className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-3">Performance KPIs</h3>
              <div className="grid grid-cols-2 gap-3">
                <div className="bg-slate-800/50 rounded-xl p-3">
                  <span className="text-[10px] text-slate-500 uppercase block">Total Trades</span>
                  <span className="text-xl font-bold text-white">{position.trades_count}</span>
                </div>
                
                <div className="bg-slate-800/50 rounded-xl p-3">
                  <span className="text-[10px] text-slate-500 uppercase block">Win Rate</span>
                  <span className={`text-xl font-bold ${winRate >= 50 ? 'text-emerald-400' : 'text-rose-400'}`}>
                    {winRate.toFixed(1)}%
                  </span>
                </div>
                
                <div className="bg-slate-800/50 rounded-xl p-3">
                  <span className="text-[10px] text-slate-500 uppercase block">Realized P&L</span>
                  <span className={`text-xl font-bold ${position.realized_pnl >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                    {position.realized_pnl >= 0 ? '+' : ''}${position.realized_pnl?.toLocaleString()}
                  </span>
                </div>
                
                <div className="bg-slate-800/50 rounded-xl p-3">
                  <span className="text-[10px] text-slate-500 uppercase block">Unrealized P&L</span>
                  <span className={`text-xl font-bold ${position.unrealized_pnl >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                    {position.unrealized_pnl >= 0 ? '+' : ''}${position.unrealized_pnl?.toLocaleString()}
                  </span>
                  {unrealizedPct !== 0 && (
                    <span className={`text-xs ${unrealizedPct >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                      ({unrealizedPct >= 0 ? '+' : ''}{unrealizedPct.toFixed(2)}%)
                    </span>
                  )}
                </div>
                
                {avgWin > 0 && (
                  <div className="bg-slate-800/50 rounded-xl p-3">
                    <span className="text-[10px] text-slate-500 uppercase block">Avg Win</span>
                    <span className="text-lg font-bold text-emerald-400">+${avgWin.toLocaleString()}</span>
                  </div>
                )}
                
                {avgLoss < 0 && (
                  <div className="bg-slate-800/50 rounded-xl p-3">
                    <span className="text-[10px] text-slate-500 uppercase block">Avg Loss</span>
                    <span className="text-lg font-bold text-rose-400">${avgLoss.toLocaleString()}</span>
                  </div>
                )}
                
                {profitFactor > 0 && (
                  <div className="bg-slate-800/50 rounded-xl p-3 col-span-2">
                    <span className="text-[10px] text-slate-500 uppercase block">Profit Factor</span>
                    <span className={`text-xl font-bold ${profitFactor >= 1 ? 'text-emerald-400' : 'text-rose-400'}`}>
                      {profitFactor.toFixed(2)}
                    </span>
                    <span className="text-xs text-slate-500 ml-2">
                      {profitFactor >= 2 ? 'Excellent' : profitFactor >= 1.5 ? 'Good' : profitFactor >= 1 ? 'Break Even' : 'Poor'}
                    </span>
                  </div>
                )}
              </div>
            </div>
          )}
          
          {/* Position Details */}
          {hasTrades && position.entry_price && (
            <div>
              <h3 className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-3">Position Details</h3>
              <div className="bg-slate-800/50 rounded-xl p-4 space-y-2">
                <div className="flex justify-between">
                  <span className="text-sm text-slate-400">Entry Price</span>
                  <span className="text-sm font-bold text-white">${position.entry_price.toFixed(2)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-slate-400">Current Price</span>
                  <span className="text-sm font-bold text-white">${currentPrice > 0 ? currentPrice.toFixed(2) : '--'}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-slate-400">Shares/Contracts</span>
                  <span className="text-sm font-bold text-white">
                    {position.invested_capital > 0 && position.entry_price > 0 
                      ? Math.floor(position.invested_capital / position.entry_price).toLocaleString()
                      : '--'}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-slate-400">Current Value</span>
                  <span className="text-sm font-bold text-white">${currentValue.toLocaleString()}</span>
                </div>
              </div>
            </div>
          )}
          
          {!hasTrades && (
            <div className="p-4 bg-amber-500/10 border border-amber-500/30 rounded-xl text-center">
              <span className="text-2xl mb-2 block">⏳</span>
              <p className="text-sm text-amber-400">No trades executed yet</p>
              <p className="text-xs text-slate-500 mt-1">Position is monitoring for entry signals</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

// Strategy Positions Detail Modal
const StrategyPositionsDetail = ({ strategy, positions, priceData, signalData, onClose }) => {
  // Defensive coding - ensure all props are valid
  if (!strategy || !positions) {
    return (
      <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm"
           onClick={(e) => e.target === e.currentTarget && onClose()}>
        <div className="bg-slate-900 border border-white/10 rounded-2xl p-8 shadow-2xl">
          <p className="text-slate-400">Loading strategy details...</p>
          <button onClick={onClose} className="mt-4 px-4 py-2 bg-blue-500 rounded-lg text-white">Close</button>
        </div>
      </div>
    );
  }

  const totalCapital = positions.reduce((sum, p) => sum + (p.capital || 0), 0);
  const totalInvested = positions.reduce((sum, p) => sum + (p.invested_capital || 0), 0);
  const totalTrades = positions.reduce((sum, p) => sum + (p.trades_count || 0), 0);
  const activePositions = positions.filter(p => p.trades_count > 0);
  const pendingPositions = positions.filter(p => p.trades_count === 0);
  
  // Calculate strategy-level signal status
  const positionsWithSignals = positions.filter(p => signalData && signalData[p.id]);
  const avgSignalStrength = positionsWithSignals.length > 0 
    ? positionsWithSignals.reduce((sum, p) => sum + ((signalData[p.id] && signalData[p.id].signal_strength) || 0), 0) / positionsWithSignals.length 
    : 0;
  const nearTriggerCount = positions.filter(p => {
    const sig = signalData && signalData[p.id];
    return sig && sig.signal_strength > 50;
  }).length;
  
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm"
         onClick={(e) => e.target === e.currentTarget && onClose()}>
      <div className="bg-slate-900 border border-white/10 rounded-2xl max-w-4xl w-full max-h-[85vh] overflow-y-auto shadow-2xl">
        {/* Header */}
        <div className="p-6 border-b border-white/10 sticky top-0 bg-slate-900 z-10">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-xl font-black text-white">{strategy?.strategy_name || 'Strategy'}</h2>
              <p className="text-sm text-slate-400 mt-1">
                {positions?.length || 0} positions • {activePositions?.length || 0} active • {pendingPositions?.length || 0} pending
              </p>
            </div>
            <button onClick={onClose} className="text-slate-400 hover:text-white text-2xl">✕</button>
          </div>
          
          {/* Signal Status Banner */}
          <div className={`mt-4 p-3 rounded-lg border ${avgSignalStrength > 50 ? 'bg-blue-500/10 border-blue-500/30' : 'bg-slate-800/50 border-white/10'}`}>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <span className="text-2xl">{avgSignalStrength > 50 ? '🔵' : '⚪'}</span>
                <div>
                  <span className="text-sm font-bold text-white">
                    {avgSignalStrength > 50 ? 'Signals Near Trigger' : 'Signals Monitoring'}
                  </span>
                  <span className="text-xs text-slate-400 block">
                    {nearTriggerCount} of {pendingPositions.length} pending positions close to entry
                  </span>
                </div>
              </div>
              <div className="text-right">
                <span className="text-xs text-slate-400 block">Avg Signal Strength</span>
                <span className={`text-lg font-bold ${avgSignalStrength > 50 ? 'text-blue-400' : 'text-slate-400'}`}>
                  {avgSignalStrength.toFixed(0)}%
                </span>
              </div>
            </div>
          </div>
          
          {/* Summary Stats */}
          <div className="grid grid-cols-4 gap-4 mt-4">
            <div className="bg-slate-800/50 rounded-lg p-3 text-center">
              <span className="text-[10px] text-slate-500 uppercase block">Total Capital</span>
              <span className="text-lg font-bold text-white">${totalCapital.toLocaleString()}</span>
            </div>
            <div className="bg-slate-800/50 rounded-lg p-3 text-center">
              <span className="text-[10px] text-slate-500 uppercase block">Invested</span>
              <span className="text-lg font-bold text-emerald-400">${totalInvested.toLocaleString()}</span>
            </div>
            <div className="bg-slate-800/50 rounded-lg p-3 text-center">
              <span className="text-[10px] text-slate-500 uppercase block">Total Trades</span>
              <span className="text-lg font-bold text-blue-400">{totalTrades}</span>
            </div>
            <div className="bg-slate-800/50 rounded-lg p-3 text-center">
              <span className="text-[10px] text-slate-500 uppercase block">Invested %</span>
              <span className="text-lg font-bold text-purple-400">
                {totalCapital > 0 ? ((totalInvested / totalCapital) * 100).toFixed(1) : 0}%
              </span>
            </div>
          </div>
        </div>
        
        <div className="p-6 space-y-6">
          {/* Active Positions with Sell Signals */}
          {activePositions.length > 0 && (
            <div>
              <h3 className="text-sm font-black text-emerald-400 uppercase tracking-wider mb-3 flex items-center gap-2">
                🟢 Active Positions ({activePositions.length}) - Watching Sell Signals
              </h3>
              <div className="space-y-3">
                {activePositions.map(pos => {
                  const tickerPrice = priceData?.[pos.ticker];
                  const currentPrice = tickerPrice?.price || 0;
                  const entryPrice = pos.entry_price;
                  const pnl = entryPrice && currentPrice > 0 
                    ? ((currentPrice - entryPrice) / entryPrice) * 100 
                    : 0;
                  const shares = entryPrice > 0 ? Math.floor(pos.invested_capital / entryPrice) : 0;
                  const currentValue = shares * currentPrice;
                  
                  // Get signal data for this position
                  const signal = signalData?.[pos.id];
                  const hasSellSignal = signal?.metrics?.rsi > 70 || signal?.metrics?.price_change_3d > 5;
                  const sellSignalStrength = signal?.signal_strength || 0;
                  
                  return (
                    <div key={pos.id} className="bg-emerald-500/5 border border-emerald-500/20 rounded-xl p-4">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          <span className="text-lg font-bold text-white">{pos.ticker}</span>
                          <span className="text-xs text-slate-400">{pos.strategy_name}</span>
                          {hasSellSignal && (
                            <span className="text-[10px] px-2 py-0.5 rounded bg-rose-500/20 text-rose-400 font-bold">
                              🔴 SELL SIGNAL
                            </span>
                          )}
                        </div>
                        <div className="text-right">
                          <div className="text-sm font-bold text-white">${currentPrice > 0 ? currentPrice.toFixed(2) : '--'}</div>
                          {tickerPrice && (
                            <div className={`text-xs ${tickerPrice.change >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                              {tickerPrice.change >= 0 ? '+' : ''}{tickerPrice.change?.toFixed(2)} ({tickerPrice.changePercent?.toFixed(2)}%)
                            </div>
                          )}
                        </div>
                      </div>
                      
                      {/* Strategy-Specific Metrics Display */}
                      {signal && (
                        <StrategySignalMetrics signal={signal} strategyId={pos.strategy_id} isActive={true} />
                      )}
                      
                      <div className="grid grid-cols-4 gap-4 mt-3 pt-3 border-t border-white/5">
                        <div>
                          <span className="text-[10px] text-slate-500 block">Entry Price</span>
                          <span className="text-sm font-bold text-white">${entryPrice?.toFixed(2)}</span>
                        </div>
                        <div>
                          <span className="text-[10px] text-slate-500 block">Shares</span>
                          <span className="text-sm font-bold text-white">{shares.toLocaleString()}</span>
                        </div>
                        <div>
                          <span className="text-[10px] text-slate-500 block">Invested</span>
                          <span className="text-sm font-bold text-emerald-400">${pos.invested_capital?.toLocaleString()}</span>
                        </div>
                        <div>
                          <span className="text-[10px] text-slate-500 block">Unrealized P&L</span>
                          <span className={`text-sm font-bold ${pnl >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                            {pnl >= 0 ? '+' : ''}{pnl.toFixed(2)}%
                          </span>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}
          
          {/* Pending Positions with Buy Signals */}
          {pendingPositions.length > 0 && (
            <div>
              <h3 className="text-sm font-black text-amber-400 uppercase tracking-wider mb-3 flex items-center gap-2">
                ⏳ Pending Positions ({pendingPositions.length}) - Waiting Buy Signals
              </h3>
              <div className="space-y-3">
                {pendingPositions.map(pos => {
                  const tickerPrice = priceData?.[pos.ticker];
                  const currentPrice = tickerPrice?.price || 0;
                  
                  // Get signal data for this position
                  const signal = signalData?.[pos.id];
                  const hasBuySignal = signal?.metrics?.rsi < 30 || signal?.metrics?.price_change_3d < -5;
                  const buySignalStrength = signal?.signal_strength || 0;
                  const isNearTrigger = buySignalStrength > 50;
                  
                  return (
                    <div key={pos.id} className={`border rounded-xl p-4 ${isNearTrigger ? 'bg-blue-500/5 border-blue-500/40 ring-1 ring-blue-500/20' : 'bg-amber-500/5 border-amber-500/20'}`}>
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          <span className="text-lg font-bold text-white">{pos.ticker}</span>
                          <span className="text-xs text-slate-400">{pos.strategy_name}</span>
                          {hasBuySignal && (
                            <span className="text-[10px] px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-400 font-bold">
                              🟢 BUY SIGNAL
                            </span>
                          )}
                          {isNearTrigger && !hasBuySignal && (
                            <span className="text-[10px] px-2 py-0.5 rounded bg-blue-500/20 text-blue-400 font-bold">
                              🔵 NEAR TRIGGER
                            </span>
                          )}
                        </div>
                        <div className="text-right">
                          <div className="text-sm font-bold text-white">${currentPrice > 0 ? currentPrice.toFixed(2) : '--'}</div>
                          {tickerPrice && (
                            <div className={`text-xs ${tickerPrice.change >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                              {tickerPrice.change >= 0 ? '+' : ''}{tickerPrice.change?.toFixed(2)} ({tickerPrice.changePercent?.toFixed(2)}%)
                            </div>
                          )}
                        </div>
                      </div>
                      
                      {/* Strategy-Specific Metrics Display */}
                      {signal ? (
                        <StrategySignalMetrics signal={signal} strategyId={pos.strategy_id} isActive={false} />
                      ) : (
                        <div className="mt-3 p-2 rounded-lg bg-slate-800/30 border border-white/5 text-center">
                          <span className="text-xs text-slate-500">No signal data available</span>
                        </div>
                      )}
                      
                      <div className="grid grid-cols-3 gap-4 mt-3 pt-3 border-t border-white/5">
                        <div>
                          <span className="text-[10px] text-slate-500 block">Capital Allocated</span>
                          <span className="text-sm font-bold text-amber-400">${pos.capital?.toLocaleString()}</span>
                        </div>
                        <div>
                          <span className="text-[10px] text-slate-500 block">Status</span>
                          <span className={`text-sm font-bold ${isNearTrigger ? 'text-blue-400' : 'text-slate-400'}`}>
                            {isNearTrigger ? '🔵 Near Trigger' : '⏳ Awaiting Signal'}
                          </span>
                        </div>
                        <div>
                          <span className="text-[10px] text-slate-500 block">Daily Change</span>
                          <span className={`text-sm font-bold ${tickerPrice?.change >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                            {tickerPrice?.change >= 0 ? '+' : ''}{tickerPrice?.changePercent?.toFixed(2)}%
                          </span>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

// Position Status Card with Click and Signal Status
const PositionCard = ({ position, priceData, signalData, onClick }) => {
  const hasTrades = position.trades_count > 0;
  const totalPnL = position.realized_pnl + position.unrealized_pnl;
  
  const tickerPrice = priceData?.[position.ticker];
  const currentPrice = tickerPrice?.price || 0;
  
  const investedPct = position.capital > 0 ? (position.invested_capital / position.capital) * 100 : 0;
  
  // Get signal data for this position
  const signal = signalData?.[position.id];
  const signalStrength = signal?.signal_strength || 0;
  const isNearTrigger = signalStrength > 50;
  
  return (
    <button 
      onClick={onClick}
      className={`w-full text-left p-4 rounded-xl border transition-all hover:scale-[1.02] ${
        hasTrades 
          ? 'bg-emerald-500/5 border-emerald-500/20 hover:border-emerald-500/40' 
          : isNearTrigger
            ? 'bg-blue-500/5 border-blue-500/40 hover:border-blue-500/60 ring-1 ring-blue-500/20'
            : 'bg-amber-500/5 border-amber-500/20 hover:border-amber-500/40'
      }`}
    >
      <div className="flex items-start justify-between mb-3">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-xl font-black text-white">{position.ticker}</span>
            <span className={`text-[10px] px-2 py-0.5 rounded font-bold ${
              hasTrades ? 'bg-emerald-500/20 text-emerald-400' : 
              isNearTrigger ? 'bg-blue-500/20 text-blue-400' :
              'bg-amber-500/20 text-amber-400'
            }`}>
              {hasTrades ? '🟢 ACTIVE' : 
               isNearTrigger ? '🔵 NEAR TRIGGER' :
               '⏳ PENDING'}
            </span>
          </div>
          <p className="text-xs text-slate-400">{position.strategy_name}</p>
        </div>
        
        {currentPrice > 0 ? (
          <PriceDisplay price={currentPrice} change={tickerPrice?.change || 0} changePercent={tickerPrice?.changePercent || 0} />
        ) : (
          <div className="text-right">
            <div className="text-lg font-bold text-slate-500">--</div>
          </div>
        )}
      </div>

      {/* Signal Status Bar for Pending Positions */}
      {!hasTrades && signal && (
        <div className="mb-3 p-2 bg-slate-800/50 rounded-lg">
          <div className="flex items-center justify-between mb-1">
            <span className="text-[10px] text-slate-400">Signal Strength</span>
            <span className={`text-[10px] font-bold ${
              signalStrength > 75 ? 'text-emerald-400' :
              signalStrength > 50 ? 'text-blue-400' :
              'text-slate-400'
            }`}>
              {signalStrength.toFixed(0)}%
            </span>
          </div>
          <div className="h-2 bg-slate-700 rounded-full overflow-hidden">
            <div 
              className={`h-full rounded-full transition-all ${
                signalStrength > 75 ? 'bg-emerald-500' :
                signalStrength > 50 ? 'bg-blue-500' :
                'bg-slate-500'
              }`}
              style={{ width: `${signalStrength}%` }}
            />
          </div>
          <p className="text-[10px] text-slate-500 mt-1 truncate">{signal.message}</p>
        </div>
      )}

      <div className="grid grid-cols-3 gap-2">
        <div className="bg-slate-800/50 rounded p-2 text-center">
          <span className="text-[10px] text-slate-500 block">Invested %</span>
          <span className="text-sm font-bold text-emerald-400">{investedPct.toFixed(1)}%</span>
        </div>
        
        <div className="bg-slate-800/50 rounded p-2 text-center">
          <span className="text-[10px] text-slate-500 block">Trades</span>
          <span className={`text-sm font-bold ${hasTrades ? 'text-emerald-400' : 'text-slate-400'}`}>
            {position.trades_count}
          </span>
        </div>
        
        <div className="bg-slate-800/50 rounded p-2 text-center">
          <span className="text-[10px] text-slate-500 block">P&L</span>
          <span className={`text-sm font-bold ${totalPnL >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
            {totalPnL >= 0 ? '+' : ''}${totalPnL.toLocaleString()}
          </span>
        </div>
      </div>
      
      <div className="mt-2 text-center">
        <span className="text-[10px] text-slate-500">Click for details →</span>
      </div>
    </button>
  );
};

// Strategy Summary Card - Enhanced with P&L and Win Rate
const StrategySummary = ({ strategy, positions, priceData, onClick }) => {
  const totalCapital = positions.reduce((sum, p) => sum + p.capital, 0);
  const totalInvested = positions.reduce((sum, p) => sum + (p.invested_capital || 0), 0);
  const totalTrades = positions.reduce((sum, p) => sum + p.trades_count, 0);
  const activePositions = positions.filter(p => p.trades_count > 0);
  const pendingPositions = positions.filter(p => p.trades_count === 0);
  
  // Calculate P&L for active positions using current prices
  let totalUnrealizedPnL = 0;
  activePositions.forEach(pos => {
    const tickerPrice = priceData?.[pos.ticker];
    if (tickerPrice?.price && pos.entry_price && pos.invested_capital > 0) {
      const shares = pos.invested_capital / pos.entry_price;
      const currentValue = shares * tickerPrice.price;
      totalUnrealizedPnL += (currentValue - pos.invested_capital);
    }
  });
  
  // Total P&L = realized + unrealized
  const totalRealizedPnL = positions.reduce((sum, p) => sum + (p.realized_pnl || 0), 0);
  const totalUnrealizedFromDb = positions.reduce((sum, p) => sum + (p.unrealized_pnl || 0), 0);
  const totalPnL = totalRealizedPnL + totalUnrealizedPnL;
  
  // Calculate win rate based on positions with positive P&L
  const positionsWithPnL = positions.filter(p => p.trades_count > 0);
  const winningPositions = positionsWithPnL.filter(p => {
    const pnl = (p.realized_pnl || 0) + (p.unrealized_pnl || 0);
    return pnl > 0;
  }).length;
  const strategyWinRate = positionsWithPnL.length > 0 ? (winningPositions / positionsWithPnL.length) * 100 : 0;
  
  // Buy Win Rate: Active positions with positive unrealized P&L (entry was good)
  const buyWinners = activePositions.filter(p => {
    const tickerPrice = priceData?.[p.ticker];
    if (!tickerPrice?.price || !p.entry_price) return false;
    return tickerPrice.price > p.entry_price;
  }).length;
  const buyWinRate = activePositions.length > 0 ? (buyWinners / activePositions.length) * 100 : 0;
  
  // Sell Win Rate: Positions with positive realized P&L (exit was good)
  const sellTrades = positions.filter(p => p.realized_pnl !== 0);
  const sellWinners = sellTrades.filter(p => p.realized_pnl > 0).length;
  const sellWinRate = sellTrades.length > 0 ? (sellWinners / sellTrades.length) * 100 : 0;

  return (
    <button 
      onClick={onClick}
      className="w-full text-left bg-slate-900/50 border border-white/10 rounded-xl p-4 hover:border-blue-500/50 hover:bg-slate-800/50 transition-all"
    >
      <div className="flex items-center justify-between mb-3">
        <div>
          <h3 className="text-sm font-bold text-white">{strategy.strategy_name}</h3>
          <p className="text-xs text-slate-400">{positions.length} positions • {activePositions.length} active • {pendingPositions.length} pending</p>
        </div>
        <div className={`text-right ${totalPnL >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
          <span className="text-lg font-bold">{totalPnL >= 0 ? '+' : ''}${Math.abs(totalPnL).toLocaleString(undefined, {maximumFractionDigits: 0})}</span>
          <p className="text-[10px] text-slate-500">Total P&L</p>
        </div>
      </div>

      <div className="grid grid-cols-4 gap-3 mb-3">
        <div className="bg-slate-800/50 rounded p-2 text-center">
          <span className="text-[10px] text-slate-500 block">Allocated</span>
          <span className="text-sm font-bold text-white">${totalCapital.toLocaleString(undefined, {maximumFractionDigits: 0})}</span>
        </div>
        <div className="bg-slate-800/50 rounded p-2 text-center">
          <span className="text-[10px] text-slate-500 block">Deployed</span>
          <span className="text-sm font-bold text-blue-400">${totalInvested.toLocaleString(undefined, {maximumFractionDigits: 0})}</span>
        </div>
        <div className="bg-slate-800/50 rounded p-2 text-center">
          <span className="text-[10px] text-slate-500 block">Buy Win Rate</span>
          <span className={`text-sm font-bold ${buyWinRate >= 50 ? 'text-emerald-400' : buyWinRate > 0 ? 'text-amber-400' : 'text-slate-400'}`}>
            {buyWinRate.toFixed(0)}%
          </span>
          <span className="text-[9px] text-slate-500 block">{buyWinners}/{activePositions.length}</span>
        </div>
        <div className="bg-slate-800/50 rounded p-2 text-center">
          <span className="text-[10px] text-slate-500 block">Sell Win Rate</span>
          <span className={`text-sm font-bold ${sellWinRate >= 50 ? 'text-emerald-400' : sellWinRate > 0 ? 'text-amber-400' : 'text-slate-400'}`}>
            {sellWinRate.toFixed(0)}%
          </span>
          <span className="text-[9px] text-slate-500 block">{sellWinners}/{sellTrades.length}</span>
        </div>
      </div>

      {/* P&L Breakdown - Enhanced */}
      <div className="grid grid-cols-2 gap-2 mb-3">
        <div className={`rounded p-2 text-center border ${totalRealizedPnL >= 0 ? 'bg-emerald-500/10 border-emerald-500/30' : 'bg-rose-500/10 border-rose-500/30'}`}>
          <span className="text-[10px] text-slate-400 block mb-1">Realized P&L</span>
          <span className={`text-lg font-bold ${totalRealizedPnL >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
            {totalRealizedPnL >= 0 ? '+' : ''}${totalRealizedPnL.toLocaleString(undefined, {maximumFractionDigits: 0})}
          </span>
          <p className="text-[9px] text-slate-500 mt-1">Closed trades</p>
        </div>
        <div className={`rounded p-2 text-center border ${totalUnrealizedPnL >= 0 ? 'bg-blue-500/10 border-blue-500/30' : 'bg-rose-500/10 border-rose-500/30'}`}>
          <span className="text-[10px] text-slate-400 block mb-1">Unrealized P&L</span>
          <span className={`text-lg font-bold ${totalUnrealizedPnL >= 0 ? 'text-blue-400' : 'text-rose-400'}`}>
            {totalUnrealizedPnL >= 0 ? '+' : ''}${totalUnrealizedPnL.toLocaleString(undefined, {maximumFractionDigits: 0})}
          </span>
          <p className="text-[9px] text-slate-500 mt-1">Open positions</p>
        </div>
      </div>

      {/* Return Metrics */}
      <div className="grid grid-cols-2 gap-2 mb-3">
        <div className="bg-slate-800/30 rounded p-2 text-center">
          <span className="text-[10px] text-slate-500 block">Return on Deployed</span>
          <span className={`text-sm font-bold ${totalInvested > 0 ? (totalPnL / totalInvested * 100 >= 0 ? 'text-emerald-400' : 'text-rose-400') : 'text-slate-400'}`}>
            {totalInvested > 0 ? (totalPnL / totalInvested * 100).toFixed(2) : '0.00'}%
          </span>
        </div>
        <div className="bg-slate-800/30 rounded p-2 text-center">
          <span className="text-[10px] text-slate-500 block">Winning Positions</span>
          <span className="text-sm font-bold text-emerald-400">
            {winningPositions}/{positionsWithPnL.length}
          </span>
        </div>
      </div>

      {/* Progress Bar */}
      <div>
        <div className="h-2 rounded-full bg-slate-700 overflow-hidden">
          <div className="h-full rounded-full bg-blue-500 transition-all"
            style={{ width: `${totalCapital > 0 ? (totalInvested / totalCapital) * 100 : 0}%` }} />
        </div>
        <p className="text-[10px] text-slate-500 mt-1 text-center">
          {totalInvested > 0 ? `${((totalInvested / totalCapital) * 100).toFixed(1)}% deployed` : 'No trades yet'}
        </p>
      </div>
      
      <div className="mt-2 text-center">
        <span className="text-[10px] text-slate-500">Click to see all positions →</span>
      </div>
    </button>
  );
};

// Main Performance Component
export const StrategyPerformance = () => {
  const [paperStrategies, setPaperStrategies] = useState([]);
  const [priceData, setPriceData] = useState({});
  const [signalData, setSignalData] = useState({});
  const [loading, setLoading] = useState(true);
  const [activeView, setActiveView] = useState('overview');
  const [selectedPosition, setSelectedPosition] = useState(null);
  const [selectedStrategy, setSelectedStrategy] = useState(null);
  const [lastPriceUpdate, setLastPriceUpdate] = useState(null);
  const [executionMode, setExecutionMode] = useState('SIMULATION');

  useEffect(() => {
    fetchData();
    fetchGlobalMode();
    const interval = setInterval(fetchData, 30000);
    const modeInterval = setInterval(fetchGlobalMode, 60000);
    return () => {
      clearInterval(interval);
      clearInterval(modeInterval);
    };
  }, []);

  const fetchGlobalMode = async () => {
    try {
      const res = await fetch('/api/execution/global-mode');
      if (res.ok) {
        const data = await res.json();
        setExecutionMode(data.execution_mode);
      }
    } catch (e) { console.error('Failed to fetch mode:', e); }
  };

  const fetchSignals = async () => {
    try {
      const res = await fetch('/api/positions/signals');
      if (res.ok) {
        const data = await res.json();
        const signalMap = {};
        data.signals?.forEach(sig => {
          signalMap[sig.position_id] = sig;
        });
        setSignalData(signalMap);
      }
    } catch (e) { console.error('Failed to fetch signals:', e); }
  };

  useEffect(() => {
    if (paperStrategies.length > 0) {
      fetchPrices();
      fetchSignals();
      const priceInterval = setInterval(fetchPrices, 15000);
      const signalInterval = setInterval(fetchSignals, 30000);
      return () => {
        clearInterval(priceInterval);
        clearInterval(signalInterval);
      };
    }
  }, [paperStrategies]);

  const fetchData = async () => {
    try {
      const res = await fetch('/api/paper-strategies');
      if (res.ok) {
        const data = await res.json();
        setPaperStrategies(data.strategies || []);
      }
    } catch (e) { console.error('Failed to fetch:', e); }
    finally { setLoading(false); }
  };

  const fetchPrices = async () => {
    const uniqueTickers = [...new Set(paperStrategies.map(p => p.ticker))];
    if (uniqueTickers.length === 0) return;

    try {
      const res = await fetch(`/api/market-data?tickers=${uniqueTickers.join(',')}`);
      if (res.ok) {
        const data = await res.json();
        const prices = {};
        data.data?.forEach(item => { prices[item.ticker] = item; });
        setPriceData(prices);
        setLastPriceUpdate(new Date());
      }
    } catch (e) { console.error('Failed to fetch prices:', e); }
  };

  // Group strategies for the stats calculation
  const groupedByStrategy = useMemo(() => {
    return paperStrategies.reduce((acc, ps) => {
      if (!acc[ps.strategy_id]) acc[ps.strategy_id] = { 
        strategy_id: ps.strategy_id, 
        strategy_name: ps.strategy_name, 
        positions: [] 
      };
      acc[ps.strategy_id].positions.push(ps);
      return acc;
    }, {});
  }, [paperStrategies]);

  // Calculate comprehensive stats
  const stats = useMemo(() => {
    const totalPositions = paperStrategies.length;
    const activePositions = paperStrategies.filter(p => p.trades_count > 0);
    const pendingPositions = paperStrategies.filter(p => p.trades_count === 0);
    
    const totalAllocated = paperStrategies.reduce((sum, p) => sum + p.capital, 0);
    const totalInvested = paperStrategies.reduce((sum, p) => sum + (p.invested_capital || 0), 0);
    const totalPending = totalAllocated - totalInvested;
    
    const totalRealizedPnL = paperStrategies.reduce((sum, p) => sum + (p.realized_pnl || 0), 0);
    
    // Calculate unrealized P&L for active positions using current prices
    let totalUnrealizedPnL = 0;
    activePositions.forEach(pos => {
      const tickerPrice = priceData?.[pos.ticker];
      if (tickerPrice?.price && pos.entry_price && pos.invested_capital > 0) {
        const shares = pos.invested_capital / pos.entry_price;
        const currentValue = shares * tickerPrice.price;
        totalUnrealizedPnL += (currentValue - pos.invested_capital);
      } else {
        totalUnrealizedPnL += (pos.unrealized_pnl || 0);
      }
    });
    
    const totalPnL = totalRealizedPnL + totalUnrealizedPnL;
    const totalTrades = paperStrategies.reduce((sum, p) => sum + p.trades_count, 0);
    
    // Calculate strategy-level win rate
    const strategiesWithPositions = Object.entries(groupedByStrategy);
    const activeStrategies = strategiesWithPositions.filter(([_, data]) => 
      data.positions.some(p => p.trades_count > 0)
    );
    
    const winningStrategies = activeStrategies.filter(([_, data]) => {
      const strategyPnL = data.positions.reduce((sum, p) => {
        const pnl = (p.realized_pnl || 0) + (p.unrealized_pnl || 0);
        return sum + pnl;
      }, 0);
      return strategyPnL > 0;
    });
    
    const overallWinRate = activeStrategies.length > 0 
      ? (winningStrategies.length / activeStrategies.length) * 100 
      : 0;
    
    const deploymentRate = totalAllocated > 0 ? ((totalInvested / totalAllocated) * 100).toFixed(1) : 0;
    
    return {
      totalPositions,
      activePositions: activePositions.length,
      pendingPositions: pendingPositions.length,
      totalAllocated,
      totalInvested,
      totalPending,
      totalRealizedPnL,
      totalUnrealizedPnL,
      totalPnL,
      totalTrades,
      overallWinRate,
      winningStrategies: winningStrategies.length,
      activeStrategies: activeStrategies.length,
      deploymentRate
    };
  }, [paperStrategies, priceData, groupedByStrategy]);

  if (loading) {
    return (
      <div className="p-12 text-center text-slate-500">
        <div className="w-8 h-8 border-2 border-slate-600 border-t-blue-500 rounded-full animate-spin mx-auto mb-4" />
        Loading Performance Data...
      </div>
    );
  }

  return (
    <div className="strategy-performance space-y-6 p-4">
      {/* KPI Detail Modal */}
      {selectedPosition && (
        <PositionKPIDetail 
          position={selectedPosition} 
          priceData={priceData}
          onClose={() => setSelectedPosition(null)}
        />
      )}
      
      {/* Strategy Positions Detail Modal */}
      {selectedStrategy && (
        <StrategyPositionsDetail
          strategy={selectedStrategy}
          positions={selectedStrategy.positions || []}
          priceData={priceData}
          signalData={signalData}
          onClose={() => setSelectedStrategy(null)}
        />
      )}

      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <div className="flex items-center gap-3">
            <h2 className="text-xl font-black text-white flex items-center gap-2">
              <span className="text-2xl">📊</span>
              Trading Performance
            </h2>
            <span className={`text-[10px] px-2 py-1 rounded font-bold ${
              executionMode === 'SIMULATION' ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30' :
              executionMode === 'PAPER_TRADING' ? 'bg-amber-500/20 text-amber-400 border border-amber-500/30' :
              'bg-rose-500/20 text-rose-400 border border-rose-500/30'
            }`}>
              {executionMode === 'SIMULATION' ? '🧪 SIMULATION' :
               executionMode === 'PAPER_TRADING' ? '📝 PAPER TRADING' :
               '💰 LIVE TRADING'}
            </span>
          </div>
          <p className="text-sm text-slate-400 mt-1">
            {executionMode === 'SIMULATION' 
              ? 'Trades are simulated (database only)'
              : executionMode === 'PAPER_TRADING'
              ? 'Trades execute in IBKR Paper Account'
              : '⚠️ Trades execute with REAL MONEY'}
          </p>
        </div>

        <div className="flex items-center gap-3">
          {lastPriceUpdate && (
            <span className="text-[10px] text-slate-500">
              Prices: {lastPriceUpdate.toLocaleTimeString()}
            </span>
          )}
          <div className="flex items-center gap-2">
            {['overview', 'positions'].map((view) => (
              <button key={view} onClick={() => setActiveView(view)}
                className={`px-4 py-2 rounded-lg text-xs font-bold capitalize transition-all ${
                  activeView === view ? 'bg-blue-500 text-white' : 'bg-slate-800 text-slate-400 hover:bg-slate-700'
                }`}
              >
                {view}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Overview Stats - Clean Layout */}
      {activeView === 'overview' && (
        <>
          {/* Top Stats Row */}
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
            <div className="bg-slate-900/50 border border-white/10 rounded-xl p-4">
              <span className="text-xs text-slate-500 uppercase">Total Positions</span>
              <p className="text-2xl font-bold text-white mt-1">{stats.totalPositions}</p>
              <p className="text-xs text-emerald-400 mt-1">{stats.activePositions} active • {stats.pendingPositions} pending</p>
            </div>

            <div className="bg-slate-900/50 border border-white/10 rounded-xl p-4">
              <span className="text-xs text-slate-500 uppercase">Total Trades</span>
              <p className="text-2xl font-bold text-white mt-1">{stats.totalTrades}</p>
              <p className="text-xs text-slate-500 mt-1">Across all strategies</p>
            </div>

            <div className="bg-slate-900/50 border border-white/10 rounded-xl p-4">
              <span className="text-xs text-slate-500 uppercase">Total P&L</span>
              <p className={`text-2xl font-bold mt-1 ${stats.totalPnL >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                {stats.totalPnL >= 0 ? '+' : ''}${stats.totalPnL.toLocaleString(undefined, {maximumFractionDigits: 0})}
              </p>
              <p className="text-xs text-slate-500 mt-1">Realized + Unrealized</p>
            </div>

            <div className="bg-slate-900/50 border border-white/10 rounded-xl p-4">
              <span className="text-xs text-slate-500 uppercase">Unrealized P&L</span>
              <p className={`text-2xl font-bold mt-1 ${stats.totalUnrealizedPnL >= 0 ? 'text-blue-400' : 'text-rose-400'}`}>
                {stats.totalUnrealizedPnL >= 0 ? '+' : ''}${stats.totalUnrealizedPnL.toLocaleString(undefined, {maximumFractionDigits: 0})}
              </p>
              <p className="text-xs text-slate-500 mt-1">Open positions</p>
            </div>

            <div className="bg-slate-900/50 border border-white/10 rounded-xl p-4">
              <span className="text-xs text-slate-500 uppercase">Strategy Win Rate</span>
              <p className={`text-2xl font-bold mt-1 ${stats.overallWinRate >= 50 ? 'text-emerald-400' : 'text-amber-400'}`}>
                {stats.overallWinRate.toFixed(0)}%
              </p>
              <p className="text-xs text-slate-500 mt-1">{stats.winningStrategies}/{stats.activeStrategies} strategies profitable</p>
            </div>
          </div>

          {/* Capital Deployment Status */}
          <div className="bg-slate-900/50 border border-white/10 rounded-xl p-4">
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-xs font-bold text-slate-500 uppercase">Capital Deployment</h3>
              <span className={`text-[10px] px-2 py-1 rounded ${
                executionMode === 'SIMULATION' ? 'bg-emerald-500/20 text-emerald-400' :
                executionMode === 'PAPER_TRADING' ? 'bg-amber-500/20 text-amber-400' :
                'bg-rose-500/20 text-rose-400'
              }`}>
                {executionMode === 'SIMULATION' ? '🧪 SIMULATION' :
                 executionMode === 'PAPER_TRADING' ? '📝 PAPER TRADING' :
                 '💰 LIVE TRADING'}
              </span>
            </div>
            
            <div className="grid grid-cols-3 gap-4">
              <div className="text-center p-3 bg-slate-800/50 rounded-lg">
                <span className="text-[10px] text-slate-500 uppercase block">Total Allocated</span>
                <span className="text-xl font-bold text-white">${stats.totalAllocated.toLocaleString(undefined, {maximumFractionDigits: 0})}</span>
                <span className="text-[10px] text-slate-500 block">Reserved capital</span>
              </div>
              <div className="text-center p-3 bg-emerald-500/10 rounded-lg border border-emerald-500/20">
                <span className="text-[10px] text-emerald-400 uppercase block">Deployed</span>
                <span className="text-xl font-bold text-emerald-400">${stats.totalInvested.toLocaleString(undefined, {maximumFractionDigits: 0})}</span>
                <span className="text-[10px] text-slate-500 block">{stats.deploymentRate}% of allocated</span>
              </div>
              <div className="text-center p-3 bg-amber-500/10 rounded-lg border border-amber-500/20">
                <span className="text-[10px] text-amber-400 uppercase block">Available</span>
                <span className="text-xl font-bold text-amber-400">${(stats.totalAllocated - stats.totalInvested).toLocaleString(undefined, {maximumFractionDigits: 0})}</span>
                <span className="text-[10px] text-slate-500 block">Waiting for signals</span>
              </div>
            </div>
            
            <div className="mt-4">
              <div className="h-4 rounded-full bg-slate-700 overflow-hidden">
                <div 
                  className="h-full bg-gradient-to-r from-emerald-500 to-emerald-400 rounded-full transition-all"
                  style={{ width: `${stats.deploymentRate}%` }} 
                />
              </div>
              <div className="flex justify-between text-[10px] mt-2">
                <span className="text-emerald-400 font-bold">{stats.deploymentRate}% Deployed</span>
                <span className="text-slate-500">${stats.totalInvested.toLocaleString(undefined, {maximumFractionDigits: 0})} / ${stats.totalAllocated.toLocaleString(undefined, {maximumFractionDigits: 0})}</span>
              </div>
            </div>
          </div>

          <div className="space-y-4">
            <h3 className="text-sm font-black text-white uppercase tracking-wider">Strategy Performance (Click for Details)</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {Object.entries(groupedByStrategy).map(([strategyId, data]) => (
                <StrategySummary 
                  key={strategyId} 
                  strategy={data} 
                  positions={data.positions} 
                  priceData={priceData}
                  onClick={() => setSelectedStrategy(data)}
                />
              ))}
            </div>
          </div>
        </>
      )}

      {/* Positions View */}
      {activeView === 'positions' && (
        <div className="space-y-4">
          <h3 className="text-sm font-black text-white uppercase tracking-wider">All Positions (Click for Details)</h3>
          
          {paperStrategies.length === 0 ? (
            <div className="text-center py-12 text-slate-500">
              <div className="text-4xl mb-2">📭</div>
              <p>No positions deployed</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {paperStrategies.map((position) => (
                <PositionCard 
                  key={position.id} 
                  position={position} 
                  priceData={priceData}
                  signalData={signalData}
                  onClick={() => setSelectedPosition(position)}
                />
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default StrategyPerformance;
