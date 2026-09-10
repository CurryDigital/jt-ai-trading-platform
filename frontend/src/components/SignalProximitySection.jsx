import React, { useEffect, useMemo, useState } from 'react';
import { fetchWithTimeout } from '../utils';

const REGIME_COLORS = {
  MEAN_REV: 'bg-amber-500/15 text-amber-400 border-amber-500/20',
  TREND:    'bg-emerald-500/15 text-emerald-400 border-emerald-500/20',
  CARRY:    'bg-purple-500/15 text-purple-400 border-purple-500/20',
  VOLATILE: 'bg-rose-500/15 text-rose-400 border-rose-500/20',
  ANY:      'bg-slate-500/15 text-slate-400 border-slate-500/20',
};

const SIGNAL_TYPE_LABELS = {
  earnings:          'EPS surprise',
  regime:            'Regime score',
  regime_transition: 'Regime transition',
  volatility:        'RV/IV ratio',
  sentiment:         'COT z-score',
  calendar:          'Seasonal window',
  carry:             'Carry signal',
  momentum:          'Momentum',
  breakout:          'Breakout',
  mean_reversion:    'Mean reversion',
  trend:             'Trend',
  default:           'Signal',
};

function humanReadableCondition(signal) {
  const { signal_type, threshold } = signal;
  const label = SIGNAL_TYPE_LABELS[signal_type] || SIGNAL_TYPE_LABELS.default;
  const th = typeof threshold === 'number' ? threshold.toFixed(2) : threshold;
  return `${label} > ${th}`;
}

function valueVsThreshold(signal) {
  const { signal_type, current_value, threshold } = signal;
  const cv = typeof current_value === 'number' ? current_value.toFixed(2) : current_value;
  const th = typeof threshold === 'number' ? threshold.toFixed(2) : threshold;
  const label = SIGNAL_TYPE_LABELS[signal_type] || SIGNAL_TYPE_LABELS.default;
  return `${label}: ${cv} → ${th}`;
}

function fmtPct(v) {
  if (v == null) return '—';
  const s = v >= 0 ? '+' : '';
  return `${s}${v.toFixed(1)}%`;
}

function progressBarColor(signal) {
  if (signal.signal_active) return 'bg-emerald-500';
  if (signal.distance_pct > 75) return 'bg-amber-500';
  return 'bg-slate-500';
}

function usePoll(endpoint, intervalMs = 60000) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let cancelled = false;
    const fetchData = async () => {
      try {
        setLoading(true);
        const res = await fetchWithTimeout(endpoint, {}, 12000);
        if (!res.ok) throw new Error(`${res.status}`);
        const json = await res.json();
        if (!cancelled) {
          setData(json);
          setError(null);
        }
      } catch (e) {
        if (!cancelled) setError(e.message);
      } finally {
        if (!cancelled) setLoading(false);
      }
    };
    fetchData();
    const id = setInterval(fetchData, intervalMs);
    return () => { cancelled = true; clearInterval(id); };
  }, [endpoint, intervalMs]);

  return { data, loading, error };
}

/* ─── Skeleton ─── */
function SkeletonRow() {
  return (
    <div className="flex items-center gap-3 rounded border border-slate-700/50 px-2.5 py-2 animate-pulse">
      <span className="w-12 h-3 rounded bg-slate-700/60" />
      <span className="w-16 h-3 rounded bg-slate-700/60" />
      <span className="flex-1 h-3 rounded bg-slate-700/60" />
      <span className="w-20 h-3 rounded bg-slate-700/60" />
      <span className="w-16 h-3 rounded bg-slate-700/60" />
    </div>
  );
}

function SkeletonBlock({ count = 3 }) {
  return (
    <div className="space-y-1.5">
      <div className="w-24 h-3 rounded bg-slate-700/60 mb-2" />
      {Array.from({ length: count }).map((_, i) => <SkeletonRow key={i} />)}
    </div>
  );
}

/* ─── In the Market ─── */
function InTheMarketBlock({ positions, loading, error }) {
  if (loading) {
    return (
      <div className="rounded-lg bg-slate-800/50 border border-slate-700/50 p-4 mb-4">
        <div className="flex items-center gap-2 mb-3">
          <span className="w-2 h-2 rounded-full bg-slate-700 animate-pulse" />
          <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">In the market</span>
        </div>
        <SkeletonBlock count={2} />
      </div>
    );
  }
  if (error) {
    return (
      <div className="rounded-lg bg-slate-800/50 border border-slate-700/50 p-4 mb-4">
        <div className="flex items-center gap-2 mb-2">
          <span className="w-2 h-2 rounded-full bg-rose-500" />
          <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">In the market</span>
        </div>
        <p className="text-[11px] text-rose-400">Error loading positions: {error}</p>
      </div>
    );
  }
  if (!positions?.length) return null;

  return (
    <div className="rounded-lg bg-slate-800/50 border border-slate-700/50 p-4 mb-4">
      <div className="flex items-center gap-2 mb-3">
        <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse-dot" />
        <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">In the market</span>
        <span className="text-[10px] text-slate-500 ml-auto">{positions.length} open</span>
      </div>
      <div className="space-y-1.5">
        {positions.map((p) => {
          const regime = p.regime || 'ANY';
          const regimeClass = REGIME_COLORS[regime] || REGIME_COLORS.ANY;
          const pnlPos = (p.unrealised_pnl_pct || 0) >= 0;
          return (
            <div
              key={`${p.strategy_id}-${p.ticker}`}
              className="flex items-center gap-3 rounded border border-slate-700/50 px-2.5 py-2 hover:bg-slate-800/30"
            >
              <span className={`text-[10px] px-1.5 py-0.5 rounded border shrink-0 ${regimeClass}`}>
                {regime}
              </span>
              <span className="text-[11px] font-mono text-slate-300 w-16 shrink-0 truncate">
                {p.ticker}
              </span>
              <span className="text-[10px] text-slate-500 w-12 shrink-0">
                {p.direction}
              </span>
              <span className="text-[10px] font-mono text-slate-400 w-20 shrink-0 text-right">
                ${p.entry_price?.toFixed(2) || '—'} → ${p.current_price?.toFixed(2) || '—'}
              </span>
              <span className={`text-[11px] font-mono font-bold w-20 text-right shrink-0 ${pnlPos ? 'text-emerald-400' : 'text-rose-400'}`}>
                {fmtPct(p.unrealised_pnl_pct)}
              </span>
              <span className="text-[10px] font-mono text-slate-400 w-20 text-right shrink-0">
                {p.unrealised_pnl_usd != null ? `$${p.unrealised_pnl_usd.toFixed(0)}` : '—'}
              </span>
              {p.price_source === 'eod_proxy' && (
                <span className="text-[9px] font-bold px-1.5 py-0.5 rounded bg-slate-700/40 text-slate-400 shrink-0">
                  EOD
                </span>
              )}
              <span className="text-[10px] text-slate-500 w-10 text-right shrink-0">
                {p.days_held != null ? `${p.days_held}d` : '—'}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}

/* ─── Signal Watchlist ─── */
function SignalWatchlistBlock({ signals, loading, error }) {
  const grouped = useMemo(() => {
    const g = {};
    (signals || []).forEach((s) => {
      if (!g[s.strategy_id]) g[s.strategy_id] = [];
      g[s.strategy_id].push(s);
    });
    Object.keys(g).forEach((k) => {
      g[k].sort((a, b) => (b.distance_pct || 0) - (a.distance_pct || 0));
      g[k] = g[k].slice(0, 5);
    });
    return g;
  }, [signals]);

  const strategyKeys = Object.keys(grouped);

  if (loading) {
    return (
      <div className="rounded-lg bg-slate-800/50 border border-slate-700/50 p-4">
        <div className="flex items-center gap-2 mb-3">
          <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">Signal watchlist</span>
          <span className="text-[10px] text-slate-500 ml-auto">Loading…</span>
        </div>
        <SkeletonBlock count={5} />
      </div>
    );
  }
  if (error) {
    return (
      <div className="rounded-lg bg-slate-800/50 border border-slate-700/50 p-4">
        <div className="flex items-center gap-2 mb-2">
          <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">Signal watchlist</span>
        </div>
        <p className="text-[11px] text-rose-400">Error loading signals: {error}</p>
      </div>
    );
  }

  if (!strategyKeys.length) {
    return (
      <div className="rounded-lg bg-slate-800/50 border border-slate-700/50 p-4">
        <div className="flex items-center gap-2 mb-2">
          <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">Signal watchlist</span>
        </div>
        <p className="text-sm text-slate-500">No active strategies watching</p>
      </div>
    );
  }

  return (
    <div className="rounded-lg bg-slate-800/50 border border-slate-700/50 p-4">
      <div className="flex items-center gap-2 mb-3">
        <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">Signal watchlist</span>
        <span className="text-[10px] text-slate-500 ml-auto">
          {signals.length} signals · top 5 per strategy
        </span>
      </div>
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
                    <span className={`text-[10px] px-1.5 py-0.5 rounded border shrink-0 ${regimeClass}`}>
                      {regime}
                    </span>
                    <span className="text-[11px] font-mono text-slate-300 w-16 shrink-0 truncate">
                      {s.instrument_or_ticker}
                    </span>
                    <span className="text-[11px] text-slate-400 flex-1 truncate">
                      {humanReadableCondition(s)}
                    </span>
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
                    <span className="text-[10px] font-mono text-slate-400 w-24 text-right shrink-0 truncate">
                      {valueVsThreshold(s)}
                    </span>
                    {s.days_until_relevant > 0 && (
                      <span className="text-[10px] text-slate-500 w-12 text-right shrink-0">
                        in {s.days_until_relevant}d
                      </span>
                    )}
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

/* ─── Main Section ─── */
export default function SignalProximitySection() {
  const {
    data: proximityData,
    loading: proximityLoading,
    error: proximityError,
  } = usePoll('/api/agents/paper/signal-proximity', 300000);

  const {
    data: positionsData,
    loading: positionsLoading,
    error: positionsError,
  } = usePoll('/api/agents/paper/open-positions-pnl', 60000);

  const signals = proximityData?.signals || [];
  const positions = positionsData?.positions || [];

  return (
    <div className="space-y-4">
      <InTheMarketBlock
        positions={positions}
        loading={positionsLoading}
        error={positionsError}
      />
      <SignalWatchlistBlock
        signals={signals}
        loading={proximityLoading}
        error={proximityError}
      />
    </div>
  );
}
