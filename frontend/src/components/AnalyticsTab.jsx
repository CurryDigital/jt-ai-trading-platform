import React, { useEffect, useState } from 'react';
import { api } from '../utils';

// Research > Analytics — signal performance, proximity-to-trigger, live feed. Per market.
const MARKET_META = {
  US:     { label: 'United States', sym: 'US',  hex: '#3b82f6' },
  HK:     { label: 'Hong Kong',     sym: 'HK',  hex: '#f43f5e' },
  CRYPTO: { label: 'Crypto',        sym: 'CR',  hex: '#14b8a6' },
  FX:     { label: 'Forex',         sym: 'FX',  hex: '#0ea5e9' },
  METAL:  { label: 'Metals',        sym: 'XAU', hex: '#eab308' },
};
const MARKETS = Object.keys(MARKET_META);
const ROWS = [['US', 'HK'], ['CRYPTO', 'FX', 'METAL']];

const Sec = ({ label, children }) => (
  <div className="border-t border-white/[0.05]">
    <div className="text-[9px] uppercase tracking-wide text-slate-500 px-3.5 pt-2.5 pb-1.5">{label}</div>
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

      <Sec label="Signal Performance · hit-rate &amp; 5-day fwd">
        {(perf && perf.length ? perf : [{ family: 'No performance data yet' }]).map((s, i) => (
          <div key={s.family + i} className={`flex items-center gap-2.5 px-3.5 py-2 ${i ? 'border-t border-white/[0.04]' : ''}`}>
            <div className="flex-1 min-w-0">
              <div className="text-[12px] font-semibold text-white truncate">{s.family}</div>
              {s.n_trades != null && <div className="text-[9px] text-slate-500">{s.n_trades} trades</div>}
            </div>
            {s.hit_rate != null && (
              <div className="text-right w-24">
                <div className="flex items-baseline gap-1.5 justify-end">
                  <span className="font-mono text-[13px] font-bold text-white">{s.hit_rate}%</span>
                  {s.fwd_return_5d != null && <span className="font-mono text-[9px] text-emerald-400">+{s.fwd_return_5d}% fwd</span>}
                </div>
                <div className="h-1 rounded bg-white/[0.08] overflow-hidden mt-1">
                  <div className={`h-full ${s.hit_rate >= 55 ? 'bg-emerald-500' : 'bg-amber-500'}`} style={{ width: `${s.hit_rate}%` }} />
                </div>
              </div>
            )}
          </div>
        ))}
      </Sec>

      <Sec label="Signal Proximity · distance to trigger">
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

      <Sec label="Live Signal Feed">
        {(feed && feed.length ? feed : [{ ticker: 'No signals yet' }]).map((s, i) => (
          <div key={i} className={`flex items-center gap-2.5 px-3.5 py-2 ${i ? 'border-t border-white/[0.04]' : ''}`}>
            {s.ts && <span className="font-mono text-[10px] text-slate-500">{s.ts}</span>}
            {s.signal && <span className={`qr-chip ${s.signal === 'BUY' ? 'qr-chip-emerald' : 'qr-chip-rose'}`}>{s.signal}</span>}
            <span className="text-[12px] font-bold text-white">{s.ticker}</span>
            {s.strategy && <span className="text-[9px] text-slate-500 ml-1">{s.strategy}</span>}
            {s.confidence != null && (
              <div className="ml-auto flex items-center gap-1.5">
                <div className="w-10 h-1 rounded bg-white/[0.08] overflow-hidden"><div className="h-full bg-blue-500" style={{ width: `${s.confidence * 100}%` }} /></div>
                <span className="font-mono text-[10px] text-slate-400">{s.confidence.toFixed(2)}</span>
              </div>
            )}
          </div>
        ))}
      </Sec>
    </div>
  );
}

export const AnalyticsTab = () => {
  const [perf, setPerf] = useState({});
  const [prox, setProx] = useState({});
  const [feed, setFeed] = useState({});
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let alive = true;
    const load = async () => {
      const q = `markets=${MARKETS.join(',')}`;
      const [p, x, f] = await Promise.all([
        api.get(`/api/signals/performance?${q}`),
        api.get(`/api/signals/proximity?${q}`),
        api.get(`/api/signals/feed?${q}&limit=4`),
      ]);
      if (!alive) return;
      setPerf(p?.data || {});
      setProx(x?.data || {});
      setFeed(f?.data || {});
      setLoading(false);
    };
    load();
    const id = setInterval(load, 300000); // 5 min
    return () => { alive = false; clearInterval(id); };
  }, []);

  return (
    <div className="space-y-3">
      <div>
        <h2 className="text-sm font-bold text-white">Analytics</h2>
        <p className="text-[10px] text-slate-500">Signal performance, proximity &amp; live feed — US · HK · Crypto · FX · Metals</p>
      </div>
      {loading ? (
        <div className="qr-surface px-3 py-6 flex items-center justify-center gap-2 text-[11px] text-slate-500">
          <div className="w-3 h-3 border-2 border-slate-700 border-t-blue-500 rounded-full animate-spin" />
          Loading analytics…
        </div>
      ) : (
        ROWS.map((row, i) => (
          <div key={i} className={`grid grid-cols-1 ${row.length === 2 ? 'lg:grid-cols-2' : 'lg:grid-cols-3'} gap-3`}>
            {row.map(m => <AnalyticsColumn key={m} market={m} perf={perf[m]} prox={prox[m]} feed={feed[m]} />)}
          </div>
        ))
      )}
    </div>
  );
};

export default AnalyticsTab;
