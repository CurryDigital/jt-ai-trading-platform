import React, { useState, useEffect, useMemo } from 'react';

// Visual Entry Signal Gauge - Shows why we bought/sold and current status
const EntrySignalGauge = ({ position, strategyId }) => {
  // Parse strategy name to determine signal type
  const strategyLower = strategyId?.toLowerCase() || '';
  const ticker = position?.ticker || '';
  
  // Determine strategy type and signal logic
  const getSignalConfig = () => {
    if (strategyLower.includes('rsi')) {
      return {
        type: 'RSI',
        indicator: 'RSI (14)',
        threshold: 30,
        operator: '<',
        description: 'Oversold bounce',
        min: 0,
        max: 100,
        buyZone: [0, 30],
        sellZone: [70, 100],
        current: position?.signal_metrics?.rsi || 45, // Mock current value
      };
    }
    if (strategyLower.includes('gap')) {
      return {
        type: 'GAP',
        indicator: 'Gap %',
        threshold: -2,
        operator: '<',
        description: 'Gap fade entry',
        min: -5,
        max: 5,
        buyZone: [-5, -2],
        sellZone: [2, 5],
        current: position?.signal_metrics?.gap_pct || -1.5,
      };
    }
    if (strategyLower.includes('momentum') || strategyLower.includes('breakout')) {
      return {
        type: 'MOMENTUM',
        indicator: 'Price vs 20D MA',
        threshold: 5,
        operator: '>',
        description: 'Momentum breakout',
        min: -10,
        max: 15,
        buyZone: [5, 15],
        sellZone: [-10, -5],
        current: position?.signal_metrics?.momentum_20d || 3.2,
      };
    }
    if (strategyLower.includes('mean_rev') || strategyLower.includes('meanrev')) {
      return {
        type: 'BB',
        indicator: 'Bollinger Position',
        threshold: -2,
        operator: '<',
        description: 'Mean reversion from lower band',
        min: -3,
        max: 3,
        buyZone: [-3, -2],
        sellZone: [2, 3],
        current: position?.signal_metrics?.bb_position || -1.8,
      };
    }
    if (strategyLower.includes('macd')) {
      return {
        type: 'MACD',
        indicator: 'MACD Histogram',
        threshold: 0,
        operator: '>',
        description: 'MACD bullish crossover',
        min: -2,
        max: 2,
        buyZone: [0, 2],
        sellZone: [-2, 0],
        current: position?.signal_metrics?.macd_hist || 0.3,
      };
    }
    // Default/generic signal
    return {
      type: 'SIGNAL',
      indicator: 'Signal Strength',
      threshold: 60,
      operator: '>',
      description: 'AI confidence threshold',
      min: 0,
      max: 100,
      buyZone: [60, 100],
      sellZone: [0, 40],
      current: position?.signal_strength || 55,
    };
  };

  const config = getSignalConfig();
  const { min, max, current, threshold, operator, buyZone, sellZone, indicator, description } = config;
  
  // Calculate position on gauge (0-100%)
  const gaugePercent = Math.max(0, Math.min(100, ((current - min) / (max - min)) * 100));
  const thresholdPercent = Math.max(0, Math.min(100, ((threshold - min) / (max - min)) * 100));
  
  // Determine status
  const inBuyZone = current >= buyZone[0] && current <= buyZone[1];
  const inSellZone = current >= sellZone[0] && current <= sellZone[1];
  const approachingBuy = operator === '<' ? current > threshold : current < threshold;
  
  // Color based on status
  let statusColor = 'text-slate-400';
  let statusBg = 'bg-slate-500';
  let statusText = 'Monitoring';
  
  if (inBuyZone) {
    statusColor = 'text-emerald-400';
    statusBg = 'bg-emerald-500';
    statusText = '✅ BUY SIGNAL ACTIVE';
  } else if (inSellZone) {
    statusColor = 'text-rose-400';
    statusBg = 'bg-rose-500';
    statusText = '⚠️ SELL SIGNAL ACTIVE';
  } else if (approachingBuy) {
    statusColor = 'text-amber-400';
    statusBg = 'bg-amber-500';
    statusText = '📊 Approaching Entry';
  }

  // Format value
  const formatValue = (val) => {
    if (Math.abs(val) >= 100) return val.toFixed(0);
    if (Math.abs(val) >= 10) return val.toFixed(1);
    return val.toFixed(2);
  };

  return (
    <div className="bg-slate-800/50 rounded-lg p-3 border border-white/10">
      {/* Header */}
      <div className="flex items-center justify-between mb-2">
        <div>
          <span className="text-[10px] text-slate-500 uppercase">{indicator}</span>
          <p className="text-xs text-slate-400">{description}</p>
        </div>
        <div className={`text-[10px] px-2 py-1 rounded font-bold ${statusBg}/20 ${statusColor}`}>
          {statusText}
        </div>
      </div>

      {/* Current Value Large */}
      <div className="flex items-baseline gap-2 mb-3">
        <span className="text-2xl font-bold text-white">{formatValue(current)}</span>
        <span className="text-xs text-slate-500">
          {operator} {formatValue(threshold)} to trigger
        </span>
      </div>

      {/* Visual Gauge */}
      <div className="relative">
        {/* Gauge Background */}
        <div className="h-3 bg-slate-700 rounded-full overflow-hidden relative">
          {/* Buy Zone */}
          <div 
            className="absolute h-full bg-emerald-500/30"
            style={{
              left: `${Math.max(0, ((buyZone[0] - min) / (max - min)) * 100)}%`,
              width: `${((buyZone[1] - buyZone[0]) / (max - min)) * 100}%`
            }}
          />
          {/* Sell Zone */}
          <div 
            className="absolute h-full bg-rose-500/30"
            style={{
              left: `${Math.max(0, ((sellZone[0] - min) / (max - min)) * 100)}%`,
              width: `${((sellZone[1] - sellZone[0]) / (max - min)) * 100}%`
            }}
          />
        </div>

        {/* Threshold Marker */}
        <div 
          className="absolute top-0 w-0.5 h-3 bg-white"
          style={{ left: `${thresholdPercent}%`, transform: 'translateX(-50%)' }}
        >
          <div className="absolute -top-4 left-1/2 transform -translate-x-1/2 text-[9px] text-white font-bold whitespace-nowrap">
            {formatValue(threshold)}
          </div>
        </div>

        {/* Current Value Marker */}
        <div 
          className={`absolute -top-1 w-3 h-5 ${statusBg} rounded-full border-2 border-slate-900 shadow-lg`}
          style={{ left: `${gaugePercent}%`, transform: 'translateX(-50%)' }}
        >
          <div className={`absolute -bottom-5 left-1/2 transform -translate-x-1/2 text-[10px] font-bold ${statusColor} whitespace-nowrap`}>
            Current
          </div>
        </div>
      </div>

      {/* Zone Labels */}
      <div className="flex justify-between text-[9px] text-slate-500 mt-6">
        <span className="text-emerald-400">{config.type === 'RSI' ? 'Oversold' : 'Buy Zone'}</span>
        <span className="text-slate-400">Neutral</span>
        <span className="text-rose-400">{config.type === 'RSI' ? 'Overbought' : 'Sell Zone'}</span>
      </div>

      {/* Distance to Signal */}
      {!inBuyZone && !inSellZone && (
        <div className="mt-3 p-2 bg-slate-900/50 rounded text-center">
          <span className="text-[10px] text-slate-500">
            {approachingBuy 
              ? `📉 ${formatValue(Math.abs(current - threshold))} points to BUY signal`
              : `📈 ${formatValue(Math.abs(current - threshold))} points to SELL signal`
            }
          </span>
        </div>
      )}
    </div>
  );
};

// Strategy-Specific Signal Metrics Display
const StrategySignalMetrics = ({ signal, strategyId, isActive }) => {
  if (!signal || !signal.metrics) return null;

  const m = signal.metrics;
  const isSell = isActive;
  const strength = signal.signal_strength || 0;
  let pnlPct = m.pnl_pct;

  // Validate pnlPct - cap at reasonable values to prevent display errors
  // Crypto micro-units can cause crazy P&L calculations
  if (pnlPct !== undefined && pnlPct !== null) {
    if (pnlPct > 1000) {
      console.warn(`Capping crazy P&L: ${pnlPct}% -> 100%`);
      pnlPct = 100; // Cap at 100%
    } else if (pnlPct < -100) {
      pnlPct = -100; // Cap at -100%
    }
  } else {
    pnlPct = 0;
  }

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
          
          {/* Entry Signal Gauge for Pending Positions */}
          {!hasTrades && (
            <div>
              <h3 className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-3">Entry Signal</h3>
              <EntrySignalGauge position={position} strategyId={position.strategy_id} />
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
                {activePositions.map((pos, idx) => {
                  const tickerPrice = priceData?.[pos.ticker];
                  const currentPrice = tickerPrice?.price || 0;
                  const entryPrice = pos.entry_price || 0;
                  const investedCapital = pos.invested_capital || 0;
                  
                  // Calculate P&L only if we have valid data
                  let pnl = 0;
                  let shares = 0;
                  if (entryPrice > 0 && currentPrice > 0 && investedCapital > 0) {
                    shares = Math.floor(investedCapital / entryPrice);
                    pnl = ((currentPrice - entryPrice) / entryPrice) * 100;
                  }
                  
                  // Get signal data for this position
                  const signal = signalData?.[pos.id];
                  const hasSellSignal = signal?.metrics?.rsi > 70 || signal?.metrics?.price_change_3d > 5;
                  
                  return (
                    <div key={`active-${pos.id}-${idx}`} className="bg-emerald-500/5 border border-emerald-500/20 rounded-xl p-4">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          <span className="text-lg font-bold text-white">{pos.ticker}</span>
                          <span className="text-[10px] text-slate-500">ID: {pos.id}</span>
                          {hasSellSignal && (
                            <span className="text-[10px] px-2 py-0.5 rounded bg-rose-500/20 text-rose-400 font-bold">
                              🔴 SELL SIGNAL
                            </span>
                          )}
                        </div>
                        <div className="text-right">
                          <div className="text-sm font-bold text-white">
                            ${currentPrice > 0 ? currentPrice.toFixed(2) : '--'}
                          </div>
                          {tickerPrice && (
                            <div className={`text-xs ${tickerPrice.change >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                              {tickerPrice.change >= 0 ? '+' : ''}{tickerPrice.change?.toFixed(2)} ({tickerPrice.changePercent?.toFixed(2)}%)
                            </div>
                          )}
                        </div>
                      </div>
                      
                      <div className="grid grid-cols-4 gap-4 mt-3 pt-3 border-t border-white/5">
                        <div>
                          <span className="text-[10px] text-slate-500 block">Entry Price</span>
                          <span className="text-sm font-bold text-white">
                            {entryPrice > 0 ? `$${entryPrice.toFixed(2)}` : '--'}
                          </span>
                        </div>
                        <div>
                          <span className="text-[10px] text-slate-500 block">Shares</span>
                          <span className="text-sm font-bold text-white">{shares > 0 ? shares.toLocaleString() : '--'}</span>
                        </div>
                        <div>
                          <span className="text-[10px] text-slate-500 block">Invested</span>
                          <span className={`text-sm font-bold ${investedCapital > 0 ? 'text-emerald-400' : 'text-amber-400'}`}>
                            ${investedCapital > 0 ? investedCapital.toLocaleString() : 'Pending'}
                          </span>
                        </div>
                        <div>
                          <span className="text-[10px] text-slate-500 block">Unrealized P&L</span>
                          <span className={`text-sm font-bold ${pnl >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                            {pnl !== 0 ? `${pnl >= 0 ? '+' : ''}${pnl.toFixed(2)}%` : '--'}
                          </span>
                        </div>
                      </div>                      
                      
                      {/* Show warning if invested amount seems wrong */}
                      {pos.trades_count > 0 && investedCapital === 0 && (
                        <div className="mt-3 p-2 bg-amber-500/10 border border-amber-500/30 rounded text-center">
                          <span className="text-[10px] text-amber-400">
                            ⚠️ Data inconsistency: {pos.trades_count} trades recorded but $0 invested
                          </span>
                        </div>
                      )}
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
                {pendingPositions.map((pos, idx) => {
                  const tickerPrice = priceData?.[pos.ticker];
                  const currentPrice = tickerPrice?.price || 0;
                  const capital = pos.capital || 0;
                  
                  // Get signal data for this position
                  const signal = signalData?.[pos.id];
                  const hasBuySignal = signal?.metrics?.rsi < 30 || signal?.metrics?.price_change_3d < -5;
                  const buySignalStrength = signal?.signal_strength || 0;
                  const isNearTrigger = buySignalStrength > 50;
                  
                  return (
                    <div key={`pending-${pos.id}-${idx}`} className={`border rounded-xl p-4 ${isNearTrigger ? 'bg-blue-500/5 border-blue-500/40 ring-1 ring-blue-500/20' : 'bg-amber-500/5 border-amber-500/20'}`}>
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          <span className="text-lg font-bold text-white">{pos.ticker}</span>
                          <span className="text-[10px] text-slate-500">ID: {pos.id}</span>
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
                      
                      {/* Entry Signal Gauge for Pending Positions */}
                      {!pos.trades_count && (
                        <div className="mt-3">
                          <EntrySignalGauge position={pos} strategyId={pos.strategy_id} />
                        </div>
                      )}
                      
                      <div className="grid grid-cols-3 gap-4 mt-3 pt-3 border-t border-white/5">
                        <div>
                          <span className="text-[10px] text-slate-500 block">Capital Allocated</span>
                          <span className="text-sm font-bold text-amber-400">${capital > 0 ? capital.toLocaleString() : '0'}</span>
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
                            {tickerPrice?.change >= 0 ? '+' : ''}{tickerPrice?.changePercent?.toFixed(2) || '0.00'}%
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
  
  // Check if price data is stale (older than 5 minutes)
  const priceFetchedAt = tickerPrice?.fetchedAt;
  const isStale = priceFetchedAt && (Date.now() - new Date(priceFetchedAt).getTime() > 5 * 60 * 1000);
  
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
          <div className="text-right">
            <PriceDisplay price={currentPrice} change={tickerPrice?.change || 0} changePercent={tickerPrice?.changePercent || 0} />
            {isStale && (
              <span className="text-[9px] text-amber-400 block mt-1">⚠️ Stale data</span>
            )}
          </div>
        ) : (
          <div className="text-right">
            <div className="text-lg font-bold text-slate-500">--</div>
          </div>
        )}
      </div>

      {/* Entry Signal Gauge for Pending Positions */}
      {!hasTrades && (
        <div className="mb-3">
          <EntrySignalGauge position={position} strategyId={position.strategy_id} />
        </div>
      )}

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
  const [simBalance, setSimBalance] = useState({ total: 100000, used: 0, available: 100000 });
  const [strategyHealth, setStrategyHealth] = useState({});
  const [pausedStrategies, setPausedStrategies] = useState(new Set());
  const [showStrategyDetail, setShowStrategyDetail] = useState(null);
  const [timePeriod, setTimePeriod] = useState('1M'); // 1W, 1M, 3M, YTD, ALL
  const [dailyPnL, setDailyPnL] = useState([]);
  const [allTrades, setAllTrades] = useState([]);
  const [maxDrawdown, setMaxDrawdown] = useState(0);

  useEffect(() => {
    fetchData();
    fetchGlobalMode();
    const interval = setInterval(fetchData, 60000);
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
        // Track simulation balance
        setSimBalance({
          total: data.simulation_capital || 100000,
          used: data.simulation_used || 0,
          available: data.simulation_available || (data.simulation_capital || 100000)
        });
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
      const priceInterval = setInterval(fetchPrices, 60000);
      const signalInterval = setInterval(fetchSignals, 60000);
      return () => {
        clearInterval(priceInterval);
        clearInterval(signalInterval);
      };
    }
  }, [paperStrategies]);

  const fetchData = async () => {
    try {
      const [paperRes, pnlRes, tradesRes] = await Promise.all([
        fetch('/api/paper-strategies').then(r => r.json()).catch(() => null),
        fetch('/api/performance/daily-pnl').then(r => r.json()).catch(() => null),
        fetch('/api/velocity/trades').then(r => r.json()).catch(() => null)
      ]);
      
      if (paperRes) setPaperStrategies(paperRes.strategies || []);
      if (pnlRes) {
        setDailyPnL(pnlRes.daily || []);
        setMaxDrawdown(pnlRes.summary?.max_drawdown || 0);
      }
      if (tradesRes) setAllTrades(tradesRes.slice(-50).reverse()); // Last 50 trades
    } catch (e) { console.error('Failed to fetch:', e); }
    finally { setLoading(false); }
  };

  const fetchPrices = async () => {
    const uniqueTickers = [...new Set(paperStrategies.map(p => p.ticker))];
    if (uniqueTickers.length === 0) return;

    try {
      // Add cache-busting timestamp to get fresh data
      const timestamp = Date.now();
      const res = await fetch(`/api/market-data?tickers=${uniqueTickers.join(',')}&t=${timestamp}`);
      if (res.ok) {
        const data = await res.json();
        const prices = {};
        data.data?.forEach(item => { 
          prices[item.ticker] = {
            ...item,
            fetchedAt: new Date()
          }; 
        });
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

  // Debug: Log positions for crypto funding strategy
  useEffect(() => {
    const cryptoStrategy = groupedByStrategy['crypto_funding_rate_arbitrage'];
    if (cryptoStrategy) {
      console.log('Crypto Funding Strategy:', {
        positionCount: cryptoStrategy.positions.length,
        positions: cryptoStrategy.positions.map(p => ({ id: p.id, ticker: p.ticker, trades: p.trades_count, invested: p.invested_capital }))
      });
    }
  }, [groupedByStrategy]);

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
    
    // Calculate current portfolio value (invested + unrealized P&L)
    const portfolioValue = totalInvested + totalUnrealizedPnL;
    
    // Cash position = Simulation available (for SIM mode) or IBKR cash
    const cashPosition = executionMode === 'SIMULATION' 
      ? simBalance.available 
      : 0; // TODO: Get from IBKR for paper/live modes
    
    // Total account value = Cash + Portfolio Value
    const totalAccountValue = cashPosition + portfolioValue;
    
    // Calculate strategy-level win rate
    const strategiesWithPositions = Object.entries(groupedByStrategy);
    const activeStrategies = strategiesWithPositions.filter(([_, data]) => 
      data.positions.some(p => p.trades_count > 0)
    );
    
    // Strategy attribution (PnL contribution by strategy)
    const strategyAttribution = activeStrategies.map(([strategyId, data]) => {
      const strategyPnL = data.positions.reduce((sum, p) => {
        const pnl = (p.realized_pnl || 0) + (p.unrealized_pnl || 0);
        return sum + pnl;
      }, 0);
      const winningPositions = data.positions.filter(p => (p.realized_pnl || 0) + (p.unrealized_pnl || 0) > 0).length;
      const losingPositions = data.positions.filter(p => (p.realized_pnl || 0) + (p.unrealized_pnl || 0) < 0).length;
      const totalPositions = data.positions.filter(p => p.trades_count > 0).length;
      
      return {
        strategyId,
        strategyName: data.strategy_name,
        pnl: strategyPnL,
        contribution: totalPnL !== 0 ? (strategyPnL / Math.abs(totalPnL)) * 100 : 0,
        winningPositions,
        losingPositions,
        totalPositions,
        winRate: totalPositions > 0 ? (winningPositions / totalPositions) * 100 : 0,
        avgWin: winningPositions > 0 ? strategyPnL / winningPositions : 0,
        avgLoss: losingPositions > 0 ? strategyPnL / losingPositions : 0
      };
    }).sort((a, b) => b.pnl - a.pnl);
    
    // Asset class distribution (inferred from ticker patterns)
    const assetDistribution = {
      stocks: { value: 0, positions: 0, label: 'Stocks' },
      fx: { value: 0, positions: 0, label: 'FX' },
      crypto: { value: 0, positions: 0, label: 'Crypto' },
      commodities: { value: 0, positions: 0, label: 'Commodities' }
    };
    
    activePositions.forEach(pos => {
      const ticker = pos.ticker?.toUpperCase() || '';
      const value = pos.invested_capital || 0;
      
      // Determine asset class from ticker
      if (ticker.includes('/') || ['EUR', 'GBP', 'JPY', 'AUD', 'CAD', 'CHF', 'NZD', 'CNH', 'MXN', 'NOK', 'SEK'].some(c => ticker.startsWith(c))) {
        assetDistribution.fx.value += value;
        assetDistribution.fx.positions++;
      } else if (['BTC', 'ETH', 'SOL', 'XRP', 'ADA', 'DOT', 'LINK'].includes(ticker)) {
        assetDistribution.crypto.value += value;
        assetDistribution.crypto.positions++;
      } else if (['GLD', 'SLV', 'USO', 'UNG', 'DBA', 'DBB', 'GC', 'SI', 'CL', 'NG'].includes(ticker) || ticker.includes('=')) {
        assetDistribution.commodities.value += value;
        assetDistribution.commodities.positions++;
      } else {
        assetDistribution.stocks.value += value;
        assetDistribution.stocks.positions++;
      }
    });
    
    // Convert to array and calculate percentages
    const assetDistributionArray = Object.entries(assetDistribution)
      .filter(([_, data]) => data.value > 0)
      .map(([key, data]) => ({
        key,
        ...data,
        percentage: totalInvested > 0 ? (data.value / totalInvested) * 100 : 0
      }))
      .sort((a, b) => b.value - a.value);
    
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
      deploymentRate,
      // New: Cash and Portfolio breakdown
      cashPosition,
      portfolioValue,
      totalAccountValue,
      // New: Strategy attribution and asset distribution
      strategyAttribution,
      assetDistribution: assetDistributionArray
    };
  }, [paperStrategies, priceData, groupedByStrategy, executionMode, simBalance]);

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
          <div className="flex items-center gap-2.5">
            <h2 className="text-sm font-bold text-white">Performance</h2>
            <span className={`qr-chip ${
              executionMode === 'SIMULATION' ? 'qr-chip-slate' :
              executionMode === 'PAPER_TRADING' ? 'qr-chip-amber' :
              'qr-chip-rose'
            }`}>
              {executionMode === 'SIMULATION' ? 'SIMULATION' :
               executionMode === 'PAPER_TRADING' ? 'PAPER TRADING' :
               'LIVE TRADING'}
            </span>
          </div>
          <p className="text-[10px] text-slate-500 mt-1">
            {executionMode === 'SIMULATION'
              ? 'Trades are simulated (database only)'
              : executionMode === 'PAPER_TRADING'
              ? 'Trades execute in IBKR Paper Account'
              : 'Trades execute with real money'}
          </p>
        </div>

        <div className="flex items-center gap-3">
          {lastPriceUpdate && (
            <span className="text-[10px] text-slate-500">
              Prices: {lastPriceUpdate.toLocaleTimeString()}
            </span>
          )}

          {/* Manual Refresh Button */}
          <button
            onClick={fetchPrices}
            className="qr-btn-ghost"
            title="Refresh prices now"
          >
            Refresh
          </button>

          {/* Time Period Selector */}
          <div className="flex items-center gap-1 bg-slate-800 rounded-lg p-1">
            {['1W', '1M', '3M', 'YTD', 'ALL'].map((period) => (
              <button
                key={period}
                onClick={() => setTimePeriod(period)}
                className={`px-3 py-1.5 rounded text-[10px] font-bold transition-all ${
                  timePeriod === period ? 'bg-blue-500 text-white' : 'text-slate-400 hover:text-white'
                }`}
              >
                {period}
              </button>
            ))}
          </div>
          
          <div className="flex items-center gap-2">
            {['overview', 'trades', 'positions'].map((view) => (
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

          {/* Account Summary - Cash + Portfolio Value */}
          <div className="bg-slate-900/50 border border-white/10 rounded-xl p-4">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-xs font-bold text-slate-500 uppercase">Account Summary</h3>
              <span className="text-[10px] text-slate-500">
                Total Value: ${stats.totalAccountValue.toLocaleString(undefined, {maximumFractionDigits: 0})}
              </span>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {/* Cash Position */}
              <div className="text-center p-4 bg-slate-800/50 rounded-lg border border-white/5">
                <span className="text-[10px] text-slate-500 uppercase block mb-1">💵 Cash Position</span>
                <span className="text-2xl font-bold text-emerald-400">${stats.cashPosition.toLocaleString(undefined, {maximumFractionDigits: 0})}</span>
                <span className="text-[10px] text-slate-500 block mt-1">
                  {executionMode === 'SIMULATION' ? 'Available to trade' : 'IBKR Account Cash'}
                </span>
              </div>
              
              {/* Portfolio Value */}
              <div className="text-center p-4 bg-slate-800/50 rounded-lg border border-white/5">
                <span className="text-[10px] text-slate-500 uppercase block mb-1">📈 Portfolio Value</span>
                <span className="text-2xl font-bold text-blue-400">${stats.portfolioValue.toLocaleString(undefined, {maximumFractionDigits: 0})}</span>
                <span className="text-[10px] text-slate-500 block mt-1">
                  Invested + Unrealized P&L
                </span>
              </div>
              
              {/* Allocation Breakdown */}
              <div className="p-4 bg-slate-800/50 rounded-lg border border-white/5">
                <span className="text-[10px] text-slate-500 uppercase block mb-2">Allocation</span>
                <div className="space-y-2">
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-slate-400">Cash</span>
                    <span className="text-emerald-400 font-bold">
                      {stats.totalAccountValue > 0 ? ((stats.cashPosition / stats.totalAccountValue) * 100).toFixed(1) : 0}%
                    </span>
                  </div>
                  <div className="w-full h-2 bg-slate-700 rounded-full overflow-hidden">
                    <div 
                      className="h-full bg-emerald-500 rounded-full"
                      style={{ width: `${stats.totalAccountValue > 0 ? (stats.cashPosition / stats.totalAccountValue) * 100 : 0}%` }}
                    />
                  </div>
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-slate-400">Invested</span>
                    <span className="text-blue-400 font-bold">
                      {stats.totalAccountValue > 0 ? ((stats.portfolioValue / stats.totalAccountValue) * 100).toFixed(1) : 0}%
                    </span>
                  </div>
                  <div className="w-full h-2 bg-slate-700 rounded-full overflow-hidden">
                    <div 
                      className="h-full bg-blue-500 rounded-full"
                      style={{ width: `${stats.totalAccountValue > 0 ? (stats.portfolioValue / stats.totalAccountValue) * 100 : 0}%` }}
                    />
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Daily P&L Chart & Risk Metrics */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
            {/* Daily P&L Chart */}
            <div className="lg:col-span-2 bg-slate-900/50 border border-white/10 rounded-xl p-4">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-xs font-bold text-slate-500 uppercase">Daily P&L</h3>
                <span className="text-[10px] text-slate-500">{dailyPnL.length} days</span>
              </div>
              
              {dailyPnL.length > 0 ? (
                <div className="space-y-3">
                  {dailyPnL.map((day, idx) => {
                    const maxVal = Math.max(...dailyPnL.map(d => Math.abs(d.pnl)), 100);
                    const width = Math.max(10, (Math.abs(day.pnl) / maxVal) * 100);
                    return (
                      <div key={idx} className="flex items-center gap-3">
                        <span className="text-[10px] text-slate-500 w-16">{day.date}</span>
                        <div className="flex-1 h-6 bg-slate-800 rounded-full overflow-hidden relative">
                          <div 
                            className={`h-full ${day.pnl >= 0 ? 'bg-emerald-500' : 'bg-rose-500'}`}
                            style={{ width: `${width}%`, marginLeft: day.pnl < 0 ? 'auto' : 0 }}
                          />
                        </div>
                        <span className={`text-xs font-bold w-16 text-right ${day.pnl >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                          {day.pnl >= 0 ? '+' : ''}${day.pnl.toFixed(0)}
                        </span>
                      </div>
                    );
                  })}
                </div>
              ) : (
                <div className="h-40 flex items-center justify-center text-slate-500 text-sm">
                  No daily P&L data available yet
                </div>
              )}
            </div>
            
            {/* Risk Metrics */}
            <div className="bg-slate-900/50 border border-white/10 rounded-xl p-4 space-y-4">
              <h3 className="text-xs font-bold text-slate-500 uppercase">Risk Metrics</h3>
              
              {/* Drawdown Gauge */}
              <div className="p-3 bg-slate-800/50 rounded-lg">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-[10px] text-slate-500 uppercase">Current Drawdown</span>
                  <span className={`text-xl font-bold ${maxDrawdown <= -5 ? 'text-rose-400' : maxDrawdown <= -2 ? 'text-amber-400' : 'text-emerald-400'}`}>
                    {maxDrawdown.toFixed(2)}%
                  </span>
                </div>
                <div className="relative h-4 bg-slate-700 rounded-full overflow-hidden">
                  {/* Background zones */}
                  <div className="absolute inset-0 flex">
                    <div className="flex-1 bg-emerald-500/20" />{/* 0 to -2% */}
                    <div className="flex-1 bg-amber-500/20" />{/* -2% to -5% */}
                    <div className="flex-1 bg-rose-500/20" />{/* -5%+ */}
                  </div>
                  {/* Drawdown indicator */}
                  <div 
                    className="absolute top-0 bottom-0 w-1 bg-white shadow-lg transition-all"
                    style={{ left: `${Math.min(Math.abs(maxDrawdown) / 10 * 100, 100)}%` }}
                  />
                </div>
                <div className="flex justify-between text-[10px] text-slate-500 mt-1">
                  <span>0%</span>
                  <span className={maxDrawdown <= -5 ? 'text-rose-400 font-bold' : ''}>-5% High Risk</span>
                  <span>-10%+</span>
                </div>
              </div>
              
              <div className="p-3 bg-slate-800/50 rounded-lg">
                <span className="text-[10px] text-slate-500 uppercase block">Best Day</span>
                <span className="text-xl font-bold text-emerald-400">
                  +${Math.max(...dailyPnL.map(d => d.pnl), 0).toFixed(0)}
                </span>
              </div>
              
              <div className="p-3 bg-slate-800/50 rounded-lg">
                <span className="text-[10px] text-slate-500 uppercase block">Worst Day</span>
                <span className="text-xl font-bold text-rose-400">
                  ${Math.min(...dailyPnL.map(d => d.pnl), 0).toFixed(0)}
                </span>
              </div>
              
              <div className="p-3 bg-slate-800/50 rounded-lg">
                <span className="text-[10px] text-slate-500 uppercase block">Avg Daily P&L</span>
                <span className="text-xl font-bold text-white">
                  ${dailyPnL.length > 0 ? (dailyPnL.reduce((a, b) => a + b.pnl, 0) / dailyPnL.length).toFixed(0) : '0'}
                </span>
              </div>
            </div>
          </div>

          {/* NEW: Strategy Attribution & Analytics */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {/* Strategy Attribution Pie Chart */}
            <div className="bg-slate-900/50 border border-white/10 rounded-xl p-4">
              <h3 className="text-xs font-bold text-slate-500 uppercase mb-4">Strategy P&L Attribution</h3>
              {stats.strategyAttribution.length > 0 ? (
                <div className="space-y-3">
                  {stats.strategyAttribution.map((strategy, idx) => (
                    <div key={strategy.strategyId} className="space-y-1">
                      <div className="flex items-center justify-between text-xs">
                        <span className="text-slate-300 truncate flex-1" title={strategy.strategyName}>
                          {idx + 1}. {strategy.strategyName.slice(0, 25)}{strategy.strategyName.length > 25 ? '...' : ''}
                        </span>
                        <span className={`font-bold ml-2 ${strategy.pnl >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                          {strategy.pnl >= 0 ? '+' : ''}${Math.abs(strategy.pnl).toLocaleString(undefined, {maximumFractionDigits: 0})}
                        </span>
                      </div>
                      <div className="flex items-center gap-2">
                        <div className="flex-1 h-2 bg-slate-800 rounded-full overflow-hidden">
                          <div 
                            className={`h-full rounded-full ${strategy.pnl >= 0 ? 'bg-emerald-500' : 'bg-rose-500'}`}
                            style={{ width: `${Math.min(Math.abs(strategy.contribution), 100)}%` }}
                          />
                        </div>
                        <span className="text-[10px] text-slate-500 w-10 text-right">
                          {Math.abs(strategy.contribution).toFixed(1)}%
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="h-32 flex items-center justify-center text-slate-500 text-sm">
                  No strategy data available
                </div>
              )}
            </div>

            {/* Trade Distribution by Asset Class */}
            <div className="bg-slate-900/50 border border-white/10 rounded-xl p-4">
              <h3 className="text-xs font-bold text-slate-500 uppercase mb-4">Portfolio by Asset Class</h3>
              {stats.assetDistribution.length > 0 ? (
                <div className="space-y-4">
                  {stats.assetDistribution.map((asset) => (
                    <div key={asset.key} className="flex items-center gap-4">
                      <div className="w-10 h-10 rounded-lg bg-slate-800 flex items-center justify-center text-lg">
                        {asset.key === 'stocks' && '📈'}
                        {asset.key === 'fx' && '💱'}
                        {asset.key === 'crypto' && '₿'}
                        {asset.key === 'commodities' && '🥇'}
                      </div>
                      <div className="flex-1">
                        <div className="flex items-center justify-between mb-1">
                          <span className="text-sm font-medium text-white">{asset.label}</span>
                          <span className="text-xs font-bold text-slate-400">
                            {asset.percentage.toFixed(1)}%
                          </span>
                        </div>
                        <div className="h-3 bg-slate-800 rounded-full overflow-hidden">
                          <div 
                            className={`h-full rounded-full ${
                              asset.key === 'stocks' ? 'bg-blue-500' :
                              asset.key === 'fx' ? 'bg-purple-500' :
                              asset.key === 'crypto' ? 'bg-orange-500' :
                              'bg-yellow-500'
                            }`}
                            style={{ width: `${asset.percentage}%` }}
                          />
                        </div>
                        <div className="flex justify-between mt-1">
                          <span className="text-[10px] text-slate-500">
                            ${asset.value.toLocaleString(undefined, {maximumFractionDigits: 0})}
                          </span>
                          <span className="text-[10px] text-slate-500">
                            {asset.positions} position{asset.positions !== 1 ? 's' : ''}
                          </span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="h-32 flex items-center justify-center text-slate-500 text-sm">
                  No active positions
                </div>
              )}
            </div>
          </div>

          {/* NEW: Win/Loss Table by Strategy */}
          <div className="bg-slate-900/50 border border-white/10 rounded-xl p-4">
            <h3 className="text-xs font-bold text-slate-500 uppercase mb-4">Win/Loss by Strategy</h3>
            {stats.strategyAttribution.filter(s => s.totalPositions > 0).length > 0 ? (
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="text-[10px] text-slate-500 uppercase border-b border-white/10">
                      <th className="text-left py-2">Strategy</th>
                      <th className="text-center py-2">Wins</th>
                      <th className="text-center py-2">Losses</th>
                      <th className="text-center py-2">Win Rate</th>
                      <th className="text-right py-2">Total P&L</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-white/5">
                    {stats.strategyAttribution
                      .filter(s => s.totalPositions > 0)
                      .map(strategy => (
                        <tr key={strategy.strategyId} className="text-xs">
                          <td className="py-3 text-slate-300">
                            {strategy.strategyName.slice(0, 30)}{strategy.strategyName.length > 30 ? '...' : ''}
                          </td>
                          <td className="py-3 text-center text-emerald-400 font-bold">{strategy.winningPositions}</td>
                          <td className="py-3 text-center text-rose-400 font-bold">{strategy.losingPositions}</td>
                          <td className="py-3 text-center">
                            <span className={`font-bold ${strategy.winRate >= 50 ? 'text-emerald-400' : 'text-amber-400'}`}>
                              {strategy.winRate.toFixed(0)}%
                            </span>
                          </td>
                          <td className={`py-3 text-right font-bold ${strategy.pnl >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                            {strategy.pnl >= 0 ? '+' : ''}${strategy.pnl.toLocaleString(undefined, {maximumFractionDigits: 0})}
                          </td>
                        </tr>
                      ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="h-24 flex items-center justify-center text-slate-500 text-sm">
                No trades completed yet
              </div>
            )}
          </div>

          {/* NEW: Recent Activity Feed */}
          <div className="bg-slate-900/50 border border-white/10 rounded-xl p-4">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-xs font-bold text-slate-500 uppercase">Recent Activity</h3>
              <span className="text-[10px] text-slate-500">Last {Math.min(allTrades.length, 10)} trades</span>
            </div>
            {allTrades.length > 0 ? (
              <div className="space-y-2">
                {allTrades.slice(0, 10).map((trade, idx) => (
                  <div key={idx} className="flex items-center gap-3 p-2 bg-slate-800/30 rounded-lg">
                    <div className={`w-2 h-2 rounded-full ${trade.pnl >= 0 ? 'bg-emerald-500' : 'bg-rose-500'}`} />
                    <span className="text-xs text-slate-500 w-16">
                      {new Date(trade.entry_date || Date.now()).toLocaleDateString()}
                    </span>
                    <span className="text-sm font-bold text-white w-12">{trade.ticker}</span>
                    <span className={`text-[10px] px-2 py-0.5 rounded ${trade.side === 'BUY' ? 'bg-emerald-500/20 text-emerald-400' : 'bg-rose-500/20 text-rose-400'}`}>
                      {trade.side}
                    </span>
                    <span className={`text-xs font-bold ml-auto ${trade.pnl >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                      {trade.pnl >= 0 ? '+' : ''}${trade.pnl?.toFixed(0)}
                    </span>
                  </div>
                ))}
              </div>
            ) : (
              <div className="h-24 flex items-center justify-center text-slate-500 text-sm">
                No recent activity
              </div>
            )}
          </div>

          {/* NEW: Strategy Scorecard - Primary Focus */}
          <div className="bg-slate-900/50 border border-white/10 rounded-xl p-4">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h3 className="text-sm font-black text-white uppercase tracking-wider">🎯 Strategy Scorecard</h3>
                <p className="text-xs text-slate-400 mt-1">Performance metrics to decide: PAUSE / REFINE / CONTINUE</p>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-[10px] text-slate-500">
                  {stats.strategyAttribution.filter(s => s.totalPositions > 0).length} Active Strategies
                </span>
              </div>
            </div>

            {stats.strategyAttribution.filter(s => s.totalPositions > 0).length > 0 ? (
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="text-[10px] text-slate-500 uppercase border-b border-white/10">
                      <th className="text-left py-2 px-2">Strategy</th>
                      <th className="text-center py-2 px-2">Health</th>
                      <th className="text-center py-2 px-2">W/L</th>
                      <th className="text-center py-2 px-2">Win Rate</th>
                      <th className="text-right py-2 px-2">Total P&L</th>
                      <th className="text-center py-2 px-2">Positions</th>
                      <th className="text-center py-2 px-2">Action</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-white/5">
                    {stats.strategyAttribution
                      .filter(s => s.totalPositions > 0)
                      .map(strategy => {
                        // Determine strategy health
                        let health = 'good';
                        let healthIcon = '🟢';
                        let healthText = 'Good';
                        
                        if (strategy.winRate < 40 || strategy.pnl < -1000) {
                          health = 'poor';
                          healthIcon = '🔴';
                          healthText = 'Review';
                        } else if (strategy.winRate < 50 || strategy.pnl < 0) {
                          health = 'warning';
                          healthIcon = '🟡';
                          healthText = 'Watch';
                        }
                        
                        const isPaused = pausedStrategies.has(strategy.strategyId);
                        
                        return (
                          <tr key={strategy.strategyId} className={`text-xs hover:bg-white/5 transition-colors ${isPaused ? 'opacity-50' : ''}`}>
                            <td className="py-3 px-2">
                              <div className="flex items-center gap-2">
                                <span className="font-bold text-white">{strategy.strategyName}</span>
                                {isPaused && (
                                  <span className="text-[10px] px-1.5 py-0.5 bg-amber-500/20 text-amber-400 rounded">PAUSED</span>
                                )}
                              </div>
                            </td>
                            <td className="py-3 px-2 text-center">
                              <span className={`text-[10px] px-2 py-1 rounded font-bold ${
                                health === 'good' ? 'bg-emerald-500/20 text-emerald-400' :
                                health === 'warning' ? 'bg-amber-500/20 text-amber-400' :
                                'bg-rose-500/20 text-rose-400'
                              }`}>
                                {healthIcon} {healthText}
                              </span>
                            </td>
                            <td className="py-3 px-2 text-center">
                              <span className="text-emerald-400">{strategy.winningPositions}</span>
                              <span className="text-slate-500 mx-1">/</span>
                              <span className="text-rose-400">{strategy.losingPositions}</span>
                            </td>
                            <td className="py-3 px-2 text-center">
                              <span className={`font-bold ${strategy.winRate >= 55 ? 'text-emerald-400' : strategy.winRate >= 45 ? 'text-amber-400' : 'text-rose-400'}`}>
                                {strategy.winRate.toFixed(0)}%
                              </span>
                            </td>
                            <td className={`py-3 px-2 text-right font-bold ${strategy.pnl >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                              {strategy.pnl >= 0 ? '+' : ''}${strategy.pnl.toLocaleString(undefined, {maximumFractionDigits: 0})}
                            </td>
                            <td className="py-3 px-2 text-center text-slate-400">
                              {strategy.totalPositions}
                            </td>
                            <td className="py-3 px-2 text-center">
                              <div className="flex items-center justify-center gap-1">
                                <button
                                  onClick={() => setShowStrategyDetail(strategy)}
                                  className="px-2 py-1 bg-blue-500/20 text-blue-400 hover:bg-blue-500/30 rounded text-[10px] font-bold"
                                  title="View Details"
                                >
                                  👁️
                                </button>
                                <button
                                  onClick={() => {
                                    const newPaused = new Set(pausedStrategies);
                                    if (newPaused.has(strategy.strategyId)) {
                                      newPaused.delete(strategy.strategyId);
                                    } else {
                                      newPaused.add(strategy.strategyId);
                                    }
                                    setPausedStrategies(newPaused);
                                  }}
                                  className={`px-2 py-1 rounded text-[10px] font-bold ${
                                    isPaused 
                                      ? 'bg-emerald-500/20 text-emerald-400 hover:bg-emerald-500/30' 
                                      : 'bg-amber-500/20 text-amber-400 hover:bg-amber-500/30'
                                  }`}
                                  title={isPaused ? 'Resume Strategy' : 'Pause Strategy'}
                                >
                                  {isPaused ? '▶️' : '⏸️'}
                                </button>
                              </div>
                            </td>
                          </tr>
                        );
                      })}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="h-32 flex items-center justify-center text-slate-500 text-sm">
                No active strategies with trades yet
              </div>
            )}

            {/* Strategy Health Legend */}
            <div className="mt-4 pt-4 border-t border-white/10 flex items-center gap-6 text-[10px] text-slate-400">
              <span className="flex items-center gap-1">
                <span className="w-2 h-2 rounded-full bg-emerald-500"></span>
                Good (Win Rate ≥55%)
              </span>
              <span className="flex items-center gap-1">
                <span className="w-2 h-2 rounded-full bg-amber-500"></span>
                Watch (Win Rate 45-54%)
              </span>
              <span className="flex items-center gap-1">
                <span className="w-2 h-2 rounded-full bg-rose-500"></span>
                Review (Win Rate &lt;45% or P&L &lt;-$1k)
              </span>
            </div>
          </div>

          {/* NEW: Underperforming Strategies Alert */}
          {(() => {
            const underperforming = stats.strategyAttribution.filter(s => 
              s.totalPositions > 0 && (s.winRate < 40 || s.pnl < -1000)
            );
            
            if (underperforming.length > 0) {
              return (
                <div className="bg-rose-900/20 border border-rose-500/30 rounded-xl p-4">
                  <div className="flex items-center gap-3 mb-3">
                    <span className="text-2xl">⚠️</span>
                    <div>
                      <h3 className="text-sm font-black text-rose-400">Underperforming Strategies Detected</h3>
                      <p className="text-xs text-slate-400">{underperforming.length} strategy{underperforming.length > 1 ? 'ies' : 'y'} need attention</p>
                    </div>
                  </div>
                  <div className="space-y-2">
                    {underperforming.map(strategy => (
                      <div key={strategy.strategyId} className="flex items-center justify-between p-2 bg-rose-500/10 rounded-lg">
                        <span className="text-sm font-bold text-white">{strategy.strategyName}</span>
                        <div className="flex items-center gap-3">
                          <span className="text-xs text-rose-400">
                            Win Rate: {strategy.winRate.toFixed(0)}% | P&L: ${strategy.pnl.toFixed(0)}
                          </span>
                          <button
                            onClick={() => {
                              const newPaused = new Set(pausedStrategies);
                              newPaused.add(strategy.strategyId);
                              setPausedStrategies(newPaused);
                            }}
                            className="px-3 py-1 bg-rose-500/30 text-rose-400 hover:bg-rose-500/40 rounded text-xs font-bold"
                          >
                            ⏸️ Pause Now
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              );
            }
            return null;
          })()}

          {/* NEW: Strategy Detail Modal */}
          {showStrategyDetail && (
            <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm"
                 onClick={(e) => e.target === e.currentTarget && setShowStrategyDetail(null)}>
              <div className="bg-slate-900 border border-white/10 rounded-2xl max-w-2xl w-full max-h-[80vh] overflow-y-auto shadow-2xl">
                <div className="p-6 border-b border-white/10">
                  <div className="flex items-center justify-between">
                    <div>
                      <h3 className="text-lg font-black text-white">{showStrategyDetail.strategyName}</h3>
                      <p className="text-xs text-slate-400">Strategy Performance Analysis</p>
                    </div>
                    <button onClick={() => setShowStrategyDetail(null)} className="text-slate-400 hover:text-white text-xl">✕</button>
                  </div>
                </div>
                
                <div className="p-6 space-y-6">
                  {/* Key Metrics */}
                  <div className="grid grid-cols-3 gap-4">
                    <div className="text-center p-4 bg-slate-800/50 rounded-lg">
                      <span className="text-[10px] text-slate-500 uppercase block">Total P&L</span>
                      <span className={`text-xl font-bold ${showStrategyDetail.pnl >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                        {showStrategyDetail.pnl >= 0 ? '+' : ''}${showStrategyDetail.pnl.toLocaleString(undefined, {maximumFractionDigits: 0})}
                      </span>
                    </div>
                    <div className="text-center p-4 bg-slate-800/50 rounded-lg">
                      <span className="text-[10px] text-slate-500 uppercase block">Win Rate</span>
                      <span className={`text-xl font-bold ${showStrategyDetail.winRate >= 50 ? 'text-emerald-400' : 'text-amber-400'}`}>
                        {showStrategyDetail.winRate.toFixed(0)}%
                      </span>
                    </div>
                    <div className="text-center p-4 bg-slate-800/50 rounded-lg">
                      <span className="text-[10px] text-slate-500 uppercase block">Total Trades</span>
                      <span className="text-xl font-bold text-white">
                        {showStrategyDetail.totalPositions}
                      </span>
                    </div>
                  </div>

                  {/* Win/Loss Breakdown */}
                  <div>
                    <h4 className="text-xs font-bold text-slate-500 uppercase mb-3">Win/Loss Breakdown</h4>
                    <div className="flex items-center gap-4">
                      <div className="flex-1">
                        <div className="flex justify-between text-xs mb-1">
                          <span className="text-emerald-400">Wins: {showStrategyDetail.winningPositions}</span>
                          <span className="text-rose-400">Losses: {showStrategyDetail.losingPositions}</span>
                        </div>
                        <div className="h-4 bg-slate-800 rounded-full overflow-hidden flex">
                          <div 
                            className="h-full bg-emerald-500"
                            style={{ width: `${showStrategyDetail.totalPositions > 0 ? (showStrategyDetail.winningPositions / showStrategyDetail.totalPositions) * 100 : 0}%` }}
                          />
                          <div 
                            className="h-full bg-rose-500"
                            style={{ width: `${showStrategyDetail.totalPositions > 0 ? (showStrategyDetail.losingPositions / showStrategyDetail.totalPositions) * 100 : 0}%` }}
                          />
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Recommendations */}
                  <div className="p-4 bg-slate-800/30 rounded-lg border border-white/5">
                    <h4 className="text-xs font-bold text-slate-500 uppercase mb-3">💡 Recommendations</h4>
                    <div className="space-y-2 text-sm">
                      {showStrategyDetail.winRate < 45 && (
                        <p className="text-rose-400">⚠️ Win rate below 45%. Consider reviewing entry signals or reducing position size.</p>
                      )}
                      {showStrategyDetail.winRate >= 55 && showStrategyDetail.pnl > 0 && (
                        <p className="text-emerald-400">✅ Strategy performing well. Consider increasing allocation.</p>
                      )}
                      {showStrategyDetail.pnl < -1000 && (
                        <p className="text-rose-400">⚠️ Significant losses. Recommend pausing and backtesting new parameters.</p>
                      )}
                      {showStrategyDetail.totalPositions < 5 && (
                        <p className="text-amber-400">⏳ Insufficient data. Need more trades for reliable analysis.</p>
                      )}
                    </div>
                  </div>

                  {/* Actions */}
                  <div className="flex gap-3">
                    <button
                      onClick={() => {
                        const newPaused = new Set(pausedStrategies);
                        if (newPaused.has(showStrategyDetail.strategyId)) {
                          newPaused.delete(showStrategyDetail.strategyId);
                        } else {
                          newPaused.add(showStrategyDetail.strategyId);
                        }
                        setPausedStrategies(newPaused);
                        setShowStrategyDetail(null);
                      }}
                      className={`flex-1 py-3 rounded-lg text-sm font-bold ${
                        pausedStrategies.has(showStrategyDetail.strategyId)
                          ? 'bg-emerald-500 hover:bg-emerald-400 text-white'
                          : 'bg-amber-500 hover:bg-amber-400 text-white'
                      }`}
                    >
                      {pausedStrategies.has(showStrategyDetail.strategyId) ? '▶️ Resume Strategy' : '⏸️ Pause Strategy'}
                    </button>
                    <button
                      onClick={() => setShowStrategyDetail(null)}
                      className="flex-1 py-3 bg-slate-700 hover:bg-slate-600 text-white rounded-lg text-sm font-bold"
                    >
                      Close
                    </button>
                  </div>
                </div>
              </div>
            </div>
          )}

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

      {/* Trades View */}
      {activeView === 'trades' && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-black text-white uppercase tracking-wider">Trade History</h3>
            <span className="text-xs text-slate-500">Last {allTrades.length} trades</span>
          </div>
          
          {allTrades.length === 0 ? (
            <div className="text-center py-12 text-slate-500">
              <div className="text-4xl mb-2">📊</div>
              <p>No trades yet</p>
            </div>
          ) : (
            <div className="rounded-xl border border-white/10 overflow-hidden">
              <table className="w-full">
                <thead className="bg-slate-900/50">
                  <tr className="text-[10px] font-black text-slate-500 uppercase tracking-wider">
                    <th className="text-left p-3">Trade ID</th>
                    <th className="text-left p-3">Ticker</th>
                    <th className="text-center p-3">Side</th>
                    <th className="text-right p-3">Entry Price</th>
                    <th className="text-right p-3">P&L</th>
                    <th className="text-left p-3">Strategy</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/5">
                  {allTrades.map((trade, idx) => (
                    <tr key={idx} className="hover:bg-white/5 transition-colors">
                      <td className="p-3">
                        <span className="text-xs font-mono text-slate-400">{trade.id}</span>
                      </td>
                      <td className="p-3">
                        <span className="text-sm font-bold text-white">{trade.ticker}</span>
                      </td>
                      <td className="p-3 text-center">
                        <span className={`text-[10px] px-2 py-1 rounded font-bold ${
                          trade.side === 'BUY' ? 'bg-emerald-500/20 text-emerald-400' : 'bg-rose-500/20 text-rose-400'
                        }`}>
                          {trade.side}
                        </span>
                      </td>
                      <td className="p-3 text-right">
                        <span className="text-sm font-mono text-white">${trade.entry_price?.toFixed(2)}</span>
                      </td>
                      <td className="p-3 text-right">
                        <span className={`text-sm font-bold ${trade.pnl >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                          {trade.pnl >= 0 ? '+' : ''}${trade.pnl?.toFixed(2)}
                        </span>
                      </td>
                      <td className="p-3">
                        <span className="text-xs text-slate-500">{trade.strategy?.slice(0, 20)}...</span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default StrategyPerformance;
