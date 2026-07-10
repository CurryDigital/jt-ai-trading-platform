import React, { useState } from 'react';
import { api, usePoll } from '../utils';

// Research > Analytics — signal performance, proximity-to-trigger, live feed. Per market.
const MARKET_META = {
  US:     { label: 'United States', sym: 'US',  hex: '#3b82f6' },
  HK:     { label: 'Hong Kong',     sym: 'HK',  hex: '#f43f5e' },
  CRYPTO: { label: 'Crypto',        sym: 'CR',  hex: '#14b8a6' },
  FX:     { label: 'Forex',         sym: 'FX',  hex: '#0ea5e9' },
  METAL:  { label: 'Metals',        sym: 'XAU', hex: '#eab308' },
};
const MARKETS = Object.keys(MARKET_META);

// Defensive scale guards — the ETL has shipped both fractions (0.62) and
// percents (62) for these fields; render the same either way.
const asPct = (v) => (v == null ? null : (v <= 1.5 && v >= -1.5 ? v * 100 : v));
const asFrac = (v) => (v == null ? null : (v > 1 ? v / 100 : v));

const Sec = ({ label, hint, children }) => (
  <div className="border-t border-white/[0.05]">
    <div className="px-3.5 pt-2.5 pb-1.5">
      <div className="text-[9px] uppercase tracking-wide text-slate-500">{label}</div>
      {hint && <div className="text-[9px] text-slate-600 normal-case tracking-normal mt-0.5">{hint}</div>}
    </div>
    {children}
  </div>
);

function AnalyticsColumn({ market, perf, prox, feed }) {
  const meta = MARKET_META[market];
  return (
    <div className="jt-surface-strong overflow-hidden" style={{ border: `1px solid ${meta.hex}44`, borderTop: `3px solid ${meta.hex}` }}>
      <div className="flex items-center gap-3 px-3.5 py-2.5" style={{ background: `${meta.hex}24` }}>
        <span className="font-mono text-lg font-black" style={{ color: meta.hex }}>{meta.sym}</span>
        <div className="text-[13px] font-bold text-white flex-1">{meta.label}</div>
        <span className="text-[9px] font-bold text-slate-400 bg-white/[0.06] rounded px-2 py-0.5">{(feed || []).length} live</span>
      </div>

      <Sec label="Signal Performance" hint="Track record per signal family — % of past signals that were winners, and the avg move 5 days after firing">
        {(perf && perf.length ? perf : [{ family: 'No performance data yet' }]).map((s, i) => {
          const hr = asPct(s.hit_rate);
          const fwd = s.fwd_return_5d;
          return (
            <div key={s.family + i} className={`flex items-center gap-2.5 px-3.5 py-2 ${i ? 'border-t border-white/[0.04]' : ''}`}>
              <div className="flex-1 min-w-0">
                <div className="text-[12px] font-semibold text-white truncate">{s.family}</div>
                {s.n_trades != null && <div className="text-[9px] text-slate-500">{s.n_trades} trades</div>}
              </div>
              {hr != null && (
                <div className="text-right w-28">
                  <div className="flex items-baseline gap-1.5 justify-end">
                    <span className="font-mono text-[13px] font-bold text-white">{hr.toFixed(0)}% win</span>
                    {fwd != null && (
                      <span className={`font-mono text-[9px] ${fwd >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                        {fwd >= 0 ? '+' : ''}{fwd}% fwd
                      </span>
                    )}
                  </div>
                  <div className="h-1 rounded bg-white/[0.08] overflow-hidden mt-1">
                    <div className={`h-full ${hr >= 55 ? 'bg-emerald-500' : 'bg-amber-500'}`} style={{ width: `${Math.min(hr, 100)}%` }} />
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </Sec>

      <Sec label="Signal Proximity" hint="Watchlist — setups that have NOT fired yet; % is how far price is from the trigger level (amber = close)">
        <div className="px-3.5 pb-3 flex flex-col gap-2.5">
          {(prox && prox.length ? prox : [{ ticker: 'No proximity data yet' }]).map((p, i) => (
            <div key={p.ticker + i}>
              <div className="flex justify-between items-center mb-1">
                <div className="flex items-center gap-1.5">
                  <span className="text-[12px] font-bold text-white">{p.ticker}</span>
                  {p.direction && <span className={`qr-chip ${p.direction === 'BUY' ? 'qr-chip-emerald' : 'qr-chip-rose'}`}>{p.direction}</span>}
                  {p.family && <span className="text-[9px] text-slate-500">{p.family}</span>}
                </div>
                {p.distance_pct != null && <span className={`font-mono text-[10px] ${p.distance_pct < 15 ? 'text-amber-400' : 'text-slate-500'}`}>{p.distance_pct}% away</span>}
              </div>
              {p.distance_pct != null && (
                <div className="h-1.5 rounded bg-white/[0.06] overflow-hidden">
                  <div className={p.distance_pct < 15 ? 'bg-amber-500 h-full' : 'bg-blue-500 h-full'} style={{ width: `${100 - p.distance_pct}%` }} />
                </div>
              )}
            </div>
          ))}
        </div>
      </Sec>

      <Sec label="Live Signal Feed" hint="Signals that already FIRED — actual BUY/SELL calls with model confidence, newest first">
        {(feed && feed.length ? feed : [{ ticker: 'No signals yet' }]).map((s, i) => {
          const c = asFrac(s.confidence);
          return (
            <div key={i} className={`flex items-center gap-2.5 px-3.5 py-2 ${i ? 'border-t border-white/[0.04]' : ''}`}>
              {s.ts && <span className="font-mono text-[10px] text-slate-500">{s.ts}</span>}
              {s.signal && <span className={`qr-chip ${s.signal === 'BUY' ? 'qr-chip-emerald' : 'qr-chip-rose'}`}>{s.signal}</span>}
              <span className="text-[12px] font-bold text-white">{s.ticker}</span>
              {s.strategy && <span className="text-[9px] text-slate-500 ml-1">{s.strategy}</span>}
              {c != null && (
                <div className="ml-auto flex items-center gap-1.5" title="Model confidence (0–100%)">
                  <div className="w-10 h-1 rounded bg-white/[0.08] overflow-hidden"><div className="h-full bg-blue-500" style={{ width: `${Math.min(c * 100, 100)}%` }} /></div>
                  <span className="font-mono text-[10px] text-slate-400">{(c * 100).toFixed(0)}%</span>
                </div>
              )}
            </div>
          );
        })}
      </Sec>
    </div>
  );
}

export const AnalyticsTab = () => {
  const [perf, setPerf] = useState({});
  const [prox, setProx] = useState({});
  const [feed, setFeed] = useState({});
  const [loading, setLoading] = useState(true);

  usePoll(async () => {
    const q = `markets=${MARKETS.join(',')}`;
    const [p, x, f] = await Promise.all([
      api.get(`/api/signals/performance?${q}`),
      api.get(`/api/signals/proximity?${q}`),
      api.get(`/api/signals/feed?${q}&limit=4`),
    ]);
    setPerf(p?.data || {});
    setProx(x?.data || {});
    setFeed(f?.data || {});
    setLoading(false);
  }, 300000); // 5 min

  return (
    <div className="space-y-3">
      <div>
        <h2 className="text-sm font-bold text-white">Analytics</h2>
        <p className="text-[10px] text-slate-500">
          Per market: Performance = past signal quality · Proximity = setups about to fire · Feed = signals already fired
        </p>
      </div>
      {loading ? (
        <div className="qr-surface px-3 py-6 flex items-center justify-center gap-2 text-[11px] text-slate-500">
          <div className="w-3 h-3 border-2 border-slate-700 border-t-blue-500 rounded-full animate-spin" />
          Loading analytics…
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-3">
          {MARKETS.map(m => <AnalyticsColumn key={m} market={m} perf={perf[m]} prox={prox[m]} feed={feed[m]} />)}
        </div>
      )}
    </div>
  );
};

export default AnalyticsTab;
