import React, { useState } from 'react';
import { api, usePoll, pnlCl, fmtPct } from '../utils';

// Research > Macro — US & HK equities + Crypto/FX/Metals + ETF strategy book summary.
const ETF_META = { hex: '#8b5cf6' };
const REGION_META = {
  US: { hex: '#3b82f6' },
  HK: { hex: '#f43f5e' },
};
const GLOBAL_META = {
  CRYPTO: { label: 'Crypto', sub: 'Digital assets', sym: 'CR',  hex: '#14b8a6' },
  FX:     { label: 'Forex',  sub: 'Currency pairs', sym: 'FX',  hex: '#0ea5e9' },
  METAL:  { label: 'Metals', sub: 'Gold & silver',  sym: 'XAU', hex: '#eab308' },
};
const DAY2 = ['Mo', 'Tu', 'We', 'Th', 'Fr', 'Sa', 'Su'];

// Thresholds match the backend regime model (research.py): ≥55 RISK_ON, ≤45 RISK_OFF.
function regimeOf(avg) {
  if (avg == null) return { label: '—', cls: 'text-slate-500' };
  if (avg >= 55) return { label: 'Risk-On', cls: 'text-emerald-400' };
  if (avg > 45) return { label: 'Neutral', cls: 'text-amber-400' };
  return { label: 'Risk-Off', cls: 'text-rose-400' };
}
function avgOf(arr) {
  const vals = (arr || []).filter(v => v != null);
  return vals.length ? Math.round(vals.reduce((a, b) => a + b, 0) / vals.length) : null;
}

// Turns the 7-day forecast series into a one-line trading instruction.
function regimeReading(regime7) {
  const vals = (regime7 || []).filter(v => v != null);
  if (vals.length < 2) return null;
  const avg = Math.round(vals.reduce((a, b) => a + b, 0) / vals.length);
  const delta = vals[vals.length - 1] - vals[0];
  const trend = delta >= 2 ? { arrow: '↗', word: 'strengthening', cls: 'text-emerald-400' }
    : delta <= -2 ? { arrow: '↘', word: 'fading', cls: 'text-rose-400' }
    : { arrow: '→', word: 'steady', cls: 'text-slate-400' };
  const bias = avg >= 55
    ? 'risk-on bias — long setups favored; adds OK'
    : avg > 45
      ? 'no regime edge — trade individual setups, keep sizing normal'
      : 'risk-off bias — reduce exposure, tighten stops, favor defensive';
  return { avg, trend, bias };
}

const RegimeReading = ({ regime7 }) => {
  const r = regimeReading(regime7);
  if (!r) return null;
  return (
    <div className="mt-2 pt-2 border-t border-white/[0.04] text-[9px] leading-relaxed">
      <span className={`font-mono font-bold ${r.trend.cls}`}>{r.trend.arrow} {r.trend.word}</span>
      <span className="text-slate-400"> · {r.bias}</span>
    </div>
  );
};
function heatBg(v) {
  if (v == null) return 'bg-white/[0.03]';
  const a = Math.min(1, Math.abs(v) / 1.5);
  return v >= 0 ? `rgba(52,211,153,${0.1 + a * 0.4})` : `rgba(244,63,94,${0.1 + a * 0.4})`;
}

const Regime7Bar = ({ regime7 }) => (
  <div className="flex items-end justify-between gap-1">
    {(regime7 || Array(7).fill(null)).map((on, i) => (
      <div key={i} className="flex-1 flex flex-col items-center gap-1">
        <span className={`font-mono text-[9px] font-bold ${on == null ? 'text-slate-600' : on >= 55 ? 'text-emerald-400' : on > 45 ? 'text-amber-400' : 'text-rose-400'}`}>{on != null ? Math.round(on) : '—'}</span>
        <div className="relative w-[60%] h-11 rounded bg-white/[0.05] flex flex-col justify-end overflow-hidden">
          <div className="absolute left-0 right-0 top-1/2 border-t border-dashed border-white/20 pointer-events-none" />
          {on != null && <div className={`${on >= 55 ? 'bg-emerald-500' : on > 45 ? 'bg-amber-500' : 'bg-rose-500'}`} style={{ height: `${on}%` }} />}
        </div>
        <span className="text-[8px] text-slate-600">{DAY2[i]}</span>
      </div>
    ))}
  </div>
);

function MacroRegionCard({ m, newsForRegion }) {
  const meta = REGION_META[m.key] || {};
  const avg = avgOf(m.regime_7d);
  const r = regimeOf(avg);
  return (
    <div className="jt-surface-strong overflow-hidden" style={{ border: `1px solid ${meta.hex}44`, borderTop: `3px solid ${meta.hex}` }}>
      <div className="flex items-center gap-3 px-3.5 py-2.5" style={{ background: `${meta.hex}24` }}>
        <span className="font-mono text-xl font-black tracking-wide" style={{ color: meta.hex }}>{m.key}</span>
        <div className="flex-1">
          <div className="text-[13px] font-bold text-white">{m.index_name || m.key}</div>
          <div className="text-[9px] text-slate-500">{m.index_sym}</div>
        </div>
        <div className="text-right">
          <div className="flex items-center gap-2 justify-end">
            <span className="font-mono text-[12px] font-bold text-white">{m.last != null ? m.last.toLocaleString() : '—'}</span>
            <span className={`font-mono text-[11px] font-bold ${pnlCl(m.change_pct)}`}>{m.change_pct != null ? fmtPct(m.change_pct) : '—'}</span>
          </div>
          <div className={`text-[9px] font-bold ${r.cls}`}>{r.label}{avg != null ? ` ${avg}%` : ''}</div>
        </div>
      </div>

      <div className="flex border-t border-white/[0.05]">
        {(m.kpis && m.kpis.length ? m.kpis : [['—', '—']]).map(([l, v], i) => (
          <div key={l + i} className={`flex-1 px-3.5 py-2.5 ${i ? 'border-l border-white/[0.05]' : ''}`}>
            <div className="text-[8px] uppercase tracking-wide text-slate-500">{l}</div>
            <div className="font-mono text-[13px] font-bold text-white mt-0.5">{v}</div>
          </div>
        ))}
      </div>

      <div className="px-3.5 py-3 border-t border-white/[0.05]">
        <div className="flex justify-between text-[9px] uppercase tracking-wide text-slate-500 mb-2">
          <span title="Model-forecast probability that each of the next 7 days favors risk-on positioning">7-Day Regime Forecast · P(risk-on) %</span>
          <span className="normal-case text-slate-600">≥55 risk-on · 45–55 neutral · ≤45 risk-off</span>
        </div>
        <Regime7Bar regime7={m.regime_7d} />
        <RegimeReading regime7={m.regime_7d} />
      </div>

      <div className="px-3.5 py-3 border-t border-white/[0.05]">
        <div className="text-[9px] uppercase tracking-wide text-slate-500 mb-2">Sector Split</div>
        <div className="grid grid-cols-3 gap-1.5">
          {(m.sectors && m.sectors.length ? m.sectors : [{ sector: 'No sector data yet', perf_pct: null }]).map((s, i) => (
            <div key={s.sector + i} className="px-2 py-1.5 rounded" style={{ background: heatBg(s.perf_pct) }}>
              <div className="text-[8px] text-slate-300 truncate">{s.sector}</div>
              <div className={`font-mono text-[11px] font-bold ${s.perf_pct == null ? 'text-slate-600' : s.perf_pct >= 0 ? 'text-emerald-300' : 'text-rose-300'}`}>{s.perf_pct != null ? fmtPct(s.perf_pct) : '—'}</div>
            </div>
          ))}
        </div>
      </div>

      <div className="border-t border-white/[0.05]">
        <div className="text-[9px] uppercase tracking-wide text-slate-500 px-3.5 pt-3">Economic Calendar</div>
        <div className="py-2">
          {(m.events && m.events.length ? m.events : [{ event: 'No events scheduled', date: '', importance: null }]).map((ev, i) => (
            <div key={i} className="flex items-center gap-2.5 px-3.5 py-1.5">
              {ev.date && <span className="font-mono text-[10px] font-bold min-w-[46px]" style={{ color: meta.hex }}>{ev.date}</span>}
              <span className="text-[12px] text-slate-300 flex-1">{ev.event}</span>
              {ev.importance && <span className={`qr-chip ${ev.importance === 'High' ? 'qr-chip-rose' : 'qr-chip-amber'}`}>{ev.importance}</span>}
            </div>
          ))}
        </div>
      </div>

      <div className="border-t border-white/[0.05]">
        <div className="text-[9px] uppercase tracking-wide text-slate-500 px-3.5 pt-3 pb-1">News</div>
        {(newsForRegion && newsForRegion.length ? newsForRegion : [{ headline: 'No news yet', source: '', age: '', tone: 'neu', tags: [] }]).map((n, i) => (
          <div key={i} className={`flex items-start gap-2.5 px-3.5 py-2 ${i ? 'border-t border-white/[0.04]' : ''}`}>
            <span className={`w-1 self-stretch rounded ${n.tone === 'bull' ? 'bg-emerald-400' : n.tone === 'bear' ? 'bg-rose-400' : 'bg-slate-500'} flex-none`} />
            <div className="flex-1 min-w-0">
              <div className="text-[12px] font-semibold text-white leading-snug">{n.headline}</div>
              <div className="flex items-center gap-1.5 mt-1 flex-wrap">
                <span className="text-[9px] text-slate-500">{[n.source, n.age].filter(Boolean).join(' · ')}</span>
                {(n.tags || []).map(t => <span key={t} className="text-[9px] px-1.5 py-0.5 rounded bg-white/[0.06] text-slate-300">{t}</span>)}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function MiniMacroCard({ m }) {
  const meta = GLOBAL_META[m.key] || {};
  const avg = avgOf(m.regime_7d);
  const r = regimeOf(avg);
  return (
    <div className="jt-surface-strong overflow-hidden" style={{ border: `1px solid ${meta.hex}44`, borderTop: `3px solid ${meta.hex}` }}>
      <div className="flex items-center gap-3 px-3.5 py-2.5" style={{ background: `${meta.hex}24` }}>
        <span className="font-mono text-lg font-black tracking-wide" style={{ color: meta.hex }}>{meta.sym}</span>
        <div className="flex-1">
          <div className="text-[13px] font-bold text-white">{meta.label}</div>
          <div className="text-[9px] text-slate-500">{meta.sub}</div>
        </div>
        <span className={`qr-chip ${avg == null ? 'qr-chip-slate' : avg >= 55 ? 'qr-chip-emerald' : avg > 45 ? 'qr-chip-amber' : 'qr-chip-rose'}`}>{r.label}{avg != null ? ` ${avg}%` : ''}</span>
      </div>
      <div className="flex border-t border-white/[0.05]">
        {(m.kpis && m.kpis.length ? m.kpis : [['—', '—']]).map(([l, v], i) => (
          <div key={l + i} className={`flex-1 px-3 py-2 ${i ? 'border-l border-white/[0.05]' : ''}`}>
            <div className="text-[8px] uppercase tracking-wide text-slate-500">{l}</div>
            <div className="font-mono text-[12px] font-bold text-white mt-0.5">{v}</div>
          </div>
        ))}
      </div>
      <div className="px-3.5 py-3 border-t border-white/[0.05]">
        <div className="flex justify-between text-[9px] uppercase tracking-wide text-slate-500 mb-2">
          <span title="Model-forecast probability that each of the next 7 days favors risk-on positioning">7-Day Regime Forecast · P(risk-on) %</span>
          <span className="normal-case text-slate-600">≥55 on · ≤45 off</span>
        </div>
        <Regime7Bar regime7={m.regime_7d} />
        <RegimeReading regime7={m.regime_7d} />
      </div>
      {m.news && (
        <div className="flex items-start gap-2.5 px-3.5 py-2.5 border-t border-white/[0.05]">
          <span className={`w-1 self-stretch rounded ${m.news.tone === 'bull' ? 'bg-emerald-400' : m.news.tone === 'bear' ? 'bg-rose-400' : 'bg-slate-500'} flex-none`} />
          <div className="text-[11px] font-semibold text-white leading-snug">{m.news.headline}</div>
        </div>
      )}
    </div>
  );
}

function ETFMacroCard({ strategies }) {
  const etf = (strategies || []).filter(s => s.asset_class === 'ETF');
  const top = etf.slice(0, 3);
  const meta = ETF_META;
  return (
    <div className="jt-surface-strong overflow-hidden" style={{ border: `1px solid ${meta.hex}44`, borderTop: `3px solid ${meta.hex}` }}>
      <div className="flex items-center gap-3 px-3.5 py-2.5" style={{ background: `${meta.hex}24` }}>
        <span className="font-mono text-lg font-black tracking-wide" style={{ color: meta.hex }}>ETF</span>
        <div className="flex-1">
          <div className="text-[13px] font-bold text-white">ETF Strategies</div>
          <div className="text-[9px] text-slate-500">ETF strategy book</div>
        </div>
        <span className="font-mono text-[20px] font-bold text-white">{etf.length}</span>
      </div>
      <div className="px-3.5 py-3 border-t border-white/[0.05]">
        {etf.length === 0 ? (
          <div className="text-[11px] text-slate-500">No ETF strategies in the book.</div>
        ) : (
          <div className="space-y-1.5">
            {top.map(s => (
              <div key={s.strategy_id} className="flex items-center justify-between text-[11px]">
                <span className="text-slate-300 truncate">{s.display_name || s.name}</span>
                <span className="font-mono text-slate-400">{s.sharpe_ratio != null ? s.sharpe_ratio.toFixed(2) : '—'}</span>
              </div>
            ))}
            {etf.length > 3 && <div className="text-[9px] text-slate-500">+{etf.length - 3} more</div>}
          </div>
        )}
      </div>
    </div>
  );
}

export const MacroTab = () => {
  const [regions, setRegions] = useState([]);
  const [global, setGlobal] = useState([]);
  const [news, setNews] = useState({});
  const [etfStrategies, setEtfStrategies] = useState([]);
  const [loading, setLoading] = useState(true);

  usePoll(async () => {
    const [reg, glob, nws, book] = await Promise.all([
      api.get('/api/macro/regions'),
      api.get('/api/macro/global'),
      api.get('/api/news?markets=US,HK'),
      api.get('/api/agents/paper/strategy-book-extended'),
    ]);
    setRegions(reg?.data || []);
    setGlobal(glob?.data || []);
    setNews(nws?.data || {});
    setEtfStrategies(book?.strategies || []);
    setLoading(false);
  }, 900000); // 15 min — matches macro DE refresh cadence

  return (
    <div className="space-y-3">
      <div className="flex items-end justify-between">
        <div>
          <h2 className="text-sm font-bold text-white">Macro</h2>
          <p className="text-[10px] text-slate-500">US &amp; HK equities · Crypto · FX · Metals · ETF strategies</p>
        </div>
      </div>
      {loading ? (
        <div className="qr-surface px-3 py-6 flex items-center justify-center gap-2 text-[11px] text-slate-500">
          <div className="w-3 h-3 border-2 border-slate-700 border-t-blue-500 rounded-full animate-spin" />
          Loading macro data…
        </div>
      ) : (
        <>
          {/* 2×2×2: [US, HK] · [Crypto, FX] · [Metals, ETF] */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-3.5 items-start">
            {(regions.length ? regions : [{ key: 'US' }, { key: 'HK' }]).map(m => (
              <MacroRegionCard key={m.key} m={m} newsForRegion={news[m.key]} />
            ))}
            {(global.length ? global : [{ key: 'CRYPTO' }, { key: 'FX' }, { key: 'METAL' }]).map(m => (
              <MiniMacroCard key={m.key} m={m} />
            ))}
            <ETFMacroCard strategies={etfStrategies} />
          </div>
        </>
      )}
    </div>
  );
};

export default MacroTab;
