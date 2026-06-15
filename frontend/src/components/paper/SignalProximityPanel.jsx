import React from 'react';

const REGIME_COLORS = {
  MEAN_REV: 'bg-amber-500/20 text-amber-400 border-amber-500/30',
  TREND:    'bg-emerald-500/20 text-emerald-400 border-emerald-500/30',
  CARRY:    'bg-purple-500/20 text-purple-400 border-purple-500/30',
  ANY:      'bg-slate-500/20 text-slate-400 border-slate-500/30',
};

function humanReadableCondition(signal) {
  const { signal_type, current_value, threshold } = signal;
  const cv = typeof current_value === 'number' ? current_value.toFixed(2) : current_value;
  const th = typeof threshold === 'number' ? threshold.toFixed(2) : threshold;

  switch (signal_type) {
    case 'earnings':
      return `EPS surprise > ${th}%`;
    case 'regime':
      return `Regime score > ${th}`;
    case 'regime_transition':
      return `Regime transition triggered`;
    case 'volatility':
      return `rv_iv_ratio < ${th}`;
    case 'sentiment':
      return `COT z > ${th}`;
    case 'calendar':
      return `Seasonal window open`;
    case 'carry':
      return `Carry signal > ${th}`;
    default:
      return `${signal_type}: ${cv} → ${th}`;
  }
}

function valueVsThreshold(signal) {
  const { signal_type, current_value, threshold } = signal;
  const cv = typeof current_value === 'number' ? current_value.toFixed(2) : current_value;
  const th = typeof threshold === 'number' ? threshold.toFixed(2) : threshold;

  switch (signal_type) {
    case 'earnings':
      return `surprise: ${cv} → ${th}`;
    case 'regime':
      return `score: ${cv} → ${th}`;
    case 'volatility':
      return `rv_iv: ${cv} → ${th}`;
    case 'sentiment':
      return `COT z: ${cv} → ${th}`;
    case 'carry':
      return `carry: ${cv} → ${th}`;
    default:
      return `${signal_type}: ${cv} → ${th}`;
  }
}

function progressBarColor(signal) {
  if (signal.signal_active) return 'bg-emerald-500';
  if (signal.distance_pct > 75) return 'bg-amber-500';
  return 'bg-slate-500';
}

export default function SignalProximityPanel({ data }) {
  const signals = data?.signals || [];

  // Group by strategy_id, take top 5 per strategy by distance_pct DESC
  const grouped = {};
  signals.forEach((s) => {
    if (!grouped[s.strategy_id]) grouped[s.strategy_id] = [];
    grouped[s.strategy_id].push(s);
  });
  Object.keys(grouped).forEach((k) => {
    grouped[k].sort((a, b) => (b.distance_pct || 0) - (a.distance_pct || 0));
    grouped[k] = grouped[k].slice(0, 5);
  });
  const strategyKeys = Object.keys(grouped);

  if (!signals.length) {
    return (
      <div className="rounded-lg bg-slate-800/50 border border-slate-700/50 p-4 mb-6">
        <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">
          Signal watchlist — closest to firing
        </h3>
        <p className="text-sm text-slate-500">No active strategies watching</p>
      </div>
    );
  }

  return (
    <div className="rounded-lg bg-slate-800/50 border border-slate-700/50 p-4 mb-6">
      <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-3">
        Signal watchlist — closest to firing ({signals.length})
      </h3>
      <div className="space-y-4">
        {strategyKeys.map((strategyId) => (
          <div key={strategyId}>
            <div className="text-[10px] font-bold uppercase tracking-wider text-slate-500 mb-1.5">
              {strategyId}
            </div>
            <div className="space-y-1.5">
              {grouped[strategyId].map((s, idx) => {
                const regime = s.regime || 'ANY';
                const regimeClass = REGIME_COLORS[regime] || REGIME_COLORS.ANY;
                const barColor = progressBarColor(s);
                const isFiring = s.signal_active;
                return (
                  <div
                    key={`${s.strategy_id}-${s.instrument_or_ticker}-${idx}`}
                    className={`flex items-center gap-3 rounded border px-2.5 py-2 ${
                      isFiring
                        ? 'border-l-4 border-l-emerald-500 border-slate-700/50 bg-emerald-500/5'
                        : 'border-slate-700/50 hover:bg-slate-800/30'
                    }`}
                  >
                    {/* Strategy pill */}
                    <span className={`text-[10px] px-1.5 py-0.5 rounded border shrink-0 ${regimeClass}`}>
                      {regime}
                    </span>

                    {/* Ticker */}
                    <span className="text-[11px] font-mono text-slate-300 w-16 shrink-0 truncate">
                      {s.instrument_or_ticker}
                    </span>

                    {/* Condition */}
                    <span className="text-[11px] text-slate-400 flex-1 truncate">
                      {humanReadableCondition(s)}
                    </span>

                    {/* Progress bar */}
                    <div className="w-20 shrink-0">
                      <div className="h-1.5 bg-slate-700 rounded-full overflow-hidden">
                        <div
                          className={`h-full ${barColor} transition-all duration-500`}
                          style={{ width: `${Math.min(100, Math.max(0, s.distance_pct || 0))}%` }}
                        />
                      </div>
                      <div className="text-[9px] text-slate-500 text-right mt-0.5">
                        {s.distance_pct?.toFixed(0) || 0}%
                      </div>
                    </div>

                    {/* Value vs threshold */}
                    <span className="text-[10px] font-mono text-slate-400 w-24 text-right shrink-0 truncate">
                      {valueVsThreshold(s)}
                    </span>

                    {/* Days until relevant */}
                    {s.days_until_relevant > 0 && (
                      <span className="text-[10px] text-slate-500 w-12 text-right shrink-0">
                        {s.days_until_relevant}d
                      </span>
                    )}

                    {/* FIRING badge */}
                    {isFiring && (
                      <span className="text-[9px] font-bold px-1.5 py-0.5 rounded bg-emerald-500/20 text-emerald-400 shrink-0">
                        FIRING
                      </span>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
