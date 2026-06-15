import React, { useState } from 'react';

const STATUS_CONFIG = {
  approved:    { dot: 'bg-emerald-400', label: 'LIVE',       cls: 'border-emerald-500/20' },
  backtesting: { dot: 'bg-blue-400',    label: 'TESTING',    cls: 'border-blue-500/20' },
  rejected:    { dot: 'bg-rose-400',    label: 'REJECTED',   cls: 'border-rose-500/20' },
  pending:     { dot: 'bg-slate-400',   label: 'PENDING',    cls: 'border-slate-500/20' },
};

const REGIME_COLORS = {
  TREND:     'text-emerald-400',
  MEAN_REV:  'text-blue-400',
  VOLATILE:  'text-rose-400',
  CARRY:     'text-amber-400',
  ANY:       'text-slate-400',
};

function ICBar({ value }) {
  if (value == null) return <span className="text-slate-600">—</span>;
  const pct = Math.min(Math.max((value / 0.30) * 100, 0), 100);
  const color = value > 0.05 ? 'bg-emerald-400' : value >= 0.03 ? 'bg-amber-400' : 'bg-rose-400';
  return (
    <div className="flex items-center gap-1.5">
      <span className="font-mono text-[11px] text-slate-300 w-10 text-right">{value.toFixed(3)}</span>
      <div className="w-16 h-1 bg-slate-700 rounded-full overflow-hidden">
        <div className={`h-full ${color} rounded-full`} style={{ width: `${pct}%` }} />
      </div>
    </div>
  );
}

export default function StrategyRow({ strategy, isArchived }) {
  const [expanded, setExpanded] = useState(false);
  const cfg = STATUS_CONFIG[strategy.status] || STATUS_CONFIG.pending;

  const directionArrow =
    strategy.last_direction === 'long' ? '↑' :
    strategy.last_direction === 'short' ? '↓' : '—';

  const directionColor =
    strategy.last_direction === 'long' ? 'text-emerald-400' :
    strategy.last_direction === 'short' ? 'text-rose-400' : 'text-slate-500';

  const isActive = strategy.status === 'approved';

  // Fix 4: cap Sharpe at 10
  const sharpeDisplay = (() => {
    if (strategy.sharpe_ratio == null) return '—';
    if (strategy.sharpe_ratio > 10) return '10+';
    return strategy.sharpe_ratio.toFixed(2);
  })();

  const PAPER_NAV_USD = 32000;

  // NAV tradeability vs $32k paper account
  const navStatus = (() => {
    if (strategy.min_nav_usd == null) return null;
    if (strategy.min_nav_usd <= PAPER_NAV_USD) {
      return { text: '✓ tradeable', color: 'text-emerald-400' };
    }
    return { text: '✗ underfunded', color: 'text-rose-400/70' };
  })();

  return (
    <div className={`rounded-lg border bg-slate-800/30 ${cfg.cls} ${isActive ? 'border-l-2 border-l-emerald-400' : ''}`}>
      <div
        className="flex items-center gap-3 px-3 py-2 cursor-pointer hover:bg-slate-800/50 transition-colors"
        onClick={() => setExpanded(!expanded)}
      >
        {/* Status dot */}
        <div className={`w-2 h-2 rounded-full ${cfg.dot} ${isActive ? 'animate-pulse' : ''} flex-shrink-0`} />

        {/* Name */}
        <div className="flex-1 min-w-0">
          <div className="text-[11px] font-bold text-slate-200 truncate">{strategy.display_name || strategy.name}</div>
        </div>

        {/* Fix 3: hide instrument, regime, direction, NAV for archived */}
        {!isArchived && (
          <>
            {/* Instrument */}
            <div className="text-[10px] font-mono text-slate-400 w-10 text-center flex-shrink-0">{strategy.instrument || '—'}</div>

            {/* Regime scope */}
            <div className={`text-[10px] font-mono w-16 text-center flex-shrink-0 ${REGIME_COLORS[strategy.regime_scope] || 'text-slate-400'}`}>
              {strategy.regime_scope}
            </div>

            {/* Sharpe */}
            <div className="text-[11px] font-mono text-slate-300 w-12 text-right flex-shrink-0">
              {sharpeDisplay}
            </div>

            {/* Direction */}
            <div className={`text-[12px] font-bold w-6 text-center flex-shrink-0 ${directionColor}`}>
              {directionArrow}
            </div>
          </>
        )}

        {/* Status badge */}
        <div className={`text-[9px] px-1.5 py-0.5 rounded font-bold flex-shrink-0 ${
          strategy.status === 'approved' ? 'bg-emerald-500/20 text-emerald-400' :
          strategy.status === 'backtesting' ? 'bg-blue-500/20 text-blue-400' :
          'bg-slate-600/20 text-slate-400'
        }`}>
          {cfg.label}
        </div>

        {/* NAV tradeability badge */}
        {navStatus && (
          <div className={`text-[9px] flex-shrink-0 ${navStatus.color}`}>
            {navStatus.text}
          </div>
        )}
      </div>

      {/* Expanded detail */}
      {expanded && (
        <div className="px-3 pb-3 pt-1 border-t border-slate-700/30 space-y-1.5">
          {/* Fix 1: show strategy_id in expanded detail only */}
          <div style={{color:'#555',fontFamily:'monospace',fontSize:'10px'}}>
            id: {strategy.strategy_id}
          </div>
          {strategy.entry_logic && (
            <div className="text-[10px] text-slate-400">
              <span className="text-slate-500">Entry:</span> {strategy.entry_logic}
            </div>
          )}
          {strategy.exit_logic && (
            <div className="text-[10px] text-slate-400">
              <span className="text-slate-500">Exit:</span> {strategy.exit_logic}
            </div>
          )}
          <div className="flex gap-4 text-[10px] text-slate-500">
            {strategy.asset_class && <span>Asset: <span className="text-slate-400">{strategy.asset_class}</span></span>}
            {strategy.last_traded_at && (
              <span>Last trade: <span className="text-slate-400">{new Date(strategy.last_traded_at).toLocaleDateString()}</span></span>
            )}
            {strategy.backtest_date && (
              <span>Backtest: <span className="text-slate-400">{new Date(strategy.backtest_date).toLocaleDateString()}</span></span>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
