import React, { useState, useEffect } from 'react';
import { api } from '../utils';

const BUCKET_ORDER = ['HK', 'FX', 'METAL', 'CRYPTO', 'US'];

const bucketMeta = {
  US: { title: 'US Equities', icon: '📊', color: '#3b82f6', subtitle: 'Stocks' },
  HK: { title: 'HK Crypto', icon: '🏙', color: '#f97316', subtitle: 'Hong Kong' },
  METAL: { title: 'XAU / Metal', icon: '🥇', color: '#eab308', subtitle: 'Gold & silver' },
  CRYPTO: { title: 'Crypto', icon: '₿', color: '#14b8a6', subtitle: 'Digital assets' },
  FX: { title: 'FX', icon: '💱', color: '#0ea5e9', subtitle: 'Currency pairs' },
};

const fmt = (n, d = 2) => {
  if (n == null || n === '' || Number.isNaN(Number(n))) return '—';
  return Number(n).toFixed(d);
};

const pnlCl = (v) => (v == null ? 'text-slate-500' : Number(v) >= 0 ? 'text-emerald-400' : 'text-rose-400');

const normalizeRegime = (raw) => {
  if (!raw || typeof raw !== 'object') return null;
  const r = raw;
  const riskOn = Number.isFinite(Number(r.risk_on_pct)) ? Number(r.risk_on_pct) : null;
  const riskOff = Number.isFinite(Number(r.risk_off_pct)) ? Number(r.risk_off_pct) : null;
  const neutral = Number.isFinite(Number(r.neutral_pct)) ? Number(r.neutral_pct) : null;
  const confidence = Number.isFinite(Number(r.regime_confidence)) ? Number(r.regime_confidence) : null;
  const allFifty = [riskOn, riskOff, neutral].every(n => n === 50);
  const stale = Boolean(r.stale) || allFifty;
  const dominant = r.dominant_regime || (allFifty ? 'NO DATA' : 'NEUTRAL');
  return { riskOn, riskOff, neutral, dominant, confidence, stale, allFifty };
};

export const ResearchTab = ({ onTickerClick }) => {
  const [activeSection, setActiveSection] = useState('signals');
  const [signals, setSignals] = useState([]);
  const [universe, setUniverse] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const markets = 'US,HK,CRYPTO,FX,METAL';

  const [regime, setRegime] = useState({});
  const [regimeLoading, setRegimeLoading] = useState(false);
  const [regimeError, setRegimeError] = useState(null);
  const [regimeLoaded, setRegimeLoaded] = useState(false);

  const refreshSignals = () => {
    setLoading(true);
    setError(null);
    api.get('/api/signals/universe?markets=' + encodeURIComponent(markets))
      .then(res => {
        const data = res?.data || {};
        setUniverse(data);
        const all = [];
        Object.entries(data).forEach(([market, list]) => {
          (list || []).forEach(item => {
            all.push({ ...item, market, category: market.toLowerCase() });
          });
        });
        setSignals(all);
      })
      .catch(e => {
        console.error('ResearchTab fetch error:', e);
        setError(e.message || 'Network error');
      })
      .finally(() => setLoading(false));
  };

  const refreshRegime = () => {
    setRegimeLoading(true);
    setRegimeError(null);
    api.get('/api/research/regime-forecast/all?horizon=7d')
      .then(res => {
        const data = res?.data || {};
        const mapped = {};
        BUCKET_ORDER.forEach(k => { mapped[k] = normalizeRegime(data[k]); });
        setRegime(mapped);
        setRegimeLoaded(true);
      })
      .catch(e => {
        console.error('ResearchTab regime fetch error:', e);
        setRegimeError(e.message || 'Network error');
      })
      .finally(() => setRegimeLoading(false));
  };

  useEffect(() => {
    const init = () => refreshSignals();
    init();
  }, []);

  useEffect(() => {
    if (activeSection !== 'regime' || regimeLoaded) return;
    const init = () => refreshRegime();
    init();
  }, [activeSection, regimeLoaded]);

  const SignalCard = ({ bucketKey }) => {
    const meta = bucketMeta[bucketKey] || { title: bucketKey, icon: '•', color: '#64748b', subtitle: '' };
    const list = universe[bucketKey] || [];
    const top = list.slice(0, 8);
    return (
      <div className="rounded-xl bg-slate-900/50 border border-white/[0.06] overflow-hidden h-full flex flex-col" style={{ border: `1px solid ${meta.color}44`, borderTop: `3px solid ${meta.color}` }}>
        <div className="flex items-center gap-3 px-3.5 py-2.5" style={{ background: `${meta.color}24` }}>
          <span className="text-xl flex-none">{meta.icon}</span>
          <div className="flex-1 min-w-0">
            <div className="text-[13px] font-bold text-white truncate">{meta.title}</div>
            <div className="text-[9px] text-slate-500">{meta.subtitle}</div>
          </div>
          <span className="text-[9px] font-bold text-slate-400 bg-white/[0.06] rounded px-2 py-0.5 flex-none">{list.length} setups</span>
        </div>
        <div className="px-3.5 py-1.5 border-t border-white/[0.05] text-[9px] uppercase tracking-wide text-slate-500">Top Opportunities · ranked by potential</div>
        <div className="flex-1">
          {top.length === 0 ? (
            <div className="py-8 text-center text-[11px] text-slate-600">No signals available</div>
          ) : (
            top.map((sig, i) => (
              <div
                key={`${bucketKey}-${sig.ticker || i}`}
                onClick={() => onTickerClick && onTickerClick(sig.ticker)}
                className={`flex items-center gap-3 px-3.5 py-2 cursor-pointer hover:bg-white/[0.03] ${i > 0 ? 'border-t border-white/[0.04]' : ''}`}
              >
                <span className="font-mono text-[13px] font-black w-4 flex-none" style={{ color: i === 0 ? meta.color : '#64748b' }}>{i + 1}</span>
                <div className="min-w-[76px] flex-none">
                  <div className="flex items-center gap-1.5">
                    <span className="text-[12px] font-bold text-white">{sig.ticker}</span>
                    <span className={`text-[8px] font-bold px-1.5 py-0.5 rounded ${sig.direction === 'BUY' ? 'bg-emerald-500/15 text-emerald-400' : sig.direction === 'SELL' ? 'bg-rose-500/15 text-rose-400' : 'bg-amber-500/15 text-amber-400'}`}>{sig.direction || 'HOLD'}</span>
                  </div>
                  <div className="text-[9px] text-slate-500">{sig.name || sig.market}</div>
                </div>
                <div className="flex-1 min-w-0">
                  <div className="text-[10px] text-slate-300 truncate">{sig.note || '—'}</div>
                  <div className="flex items-center gap-1.5 mt-0.5 flex-wrap">
                    {(sig.families || []).slice(0, 2).map(f => (
                      <span key={f} className="text-[8px] font-bold px-1.5 py-0.5 rounded bg-slate-500/15 text-slate-400">{f}</span>
                    ))}
                    {sig.change_pct != null && <span className={`font-mono text-[9px] ${pnlCl(sig.change_pct)}`}>{sig.change_pct >= 0 ? '+' : ''}{fmt(sig.change_pct)}%</span>}
                  </div>
                </div>
                <div className="w-14 text-right flex-none">
                  <div className="font-mono text-[13px] font-bold text-white">{fmt(sig.potential, 0)}%</div>
                  <div className="h-1 rounded bg-white/10 overflow-hidden mt-1">
                    <div className="h-full" style={{ width: `${Math.min(Math.max((sig.potential || 0), 0), 100)}%`, background: meta.color }} />
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    );
  };

  const RegimeCard = ({ bucketKey }) => {
    const meta = bucketMeta[bucketKey] || { title: bucketKey, icon: '•', color: '#64748b', subtitle: '' };
    const r = regime[bucketKey];
    const hasData = Boolean(r && !r.allFifty && !r.stale);
    const riskOn = r?.riskOn ?? 0;
    const riskOff = r?.riskOff ?? 0;
    const neutral = r?.neutral ?? 0;
    const total = riskOn + riskOff + neutral || 1;
    const onWidth = `${((riskOn / total) * 100).toFixed(1)}%`;
    const offWidth = `${((riskOff / total) * 100).toFixed(1)}%`;
    const neutralWidth = `${((neutral / total) * 100).toFixed(1)}%`;
    const dominant = r?.dominant || '—';
    const confidence = r?.confidence;

    return (
      <div className="rounded-xl bg-slate-900/50 border border-white/[0.06] overflow-hidden h-full flex flex-col" style={{ border: `1px solid ${meta.color}44`, borderTop: `3px solid ${meta.color}` }}>
        <div className="flex items-center gap-3 px-3.5 py-2.5" style={{ background: `${meta.color}24` }}>
          <span className="text-xl flex-none">{meta.icon}</span>
          <div className="flex-1 min-w-0">
            <div className="text-[13px] font-bold text-white truncate">{meta.title}</div>
            <div className="text-[9px] text-slate-500">7-day regime</div>
          </div>
          {r?.stale && <span className="text-[8px] font-bold text-amber-300 bg-amber-500/15 rounded px-1.5 py-0.5 flex-none">STALE</span>}
        </div>
        <div className="px-3.5 py-3 flex-1 space-y-3">
          {!hasData ? (
            <div className="py-6 text-center text-[11px] text-amber-400">No forecast</div>
          ) : (
            <>
              <div className="flex items-center justify-between">
                <span className="text-[10px] font-bold text-slate-300">Dominant</span>
                <span className={`text-[10px] font-bold px-2 py-0.5 rounded ${dominant === 'RISK_ON' ? 'bg-emerald-500/15 text-emerald-400' : dominant === 'RISK_OFF' ? 'bg-rose-500/15 text-rose-400' : 'bg-amber-500/15 text-amber-400'}`}>{dominant.replace(/_/g, ' ')}</span>
              </div>
              <div className="space-y-1">
                <div className="flex items-center justify-between text-[9px] text-slate-400">
                  <span>Risk-on</span>
                  <span>{fmt(riskOn, 0)}%</span>
                </div>
                <div className="h-1.5 rounded bg-white/10 overflow-hidden">
                  <div className="h-full rounded bg-emerald-500" style={{ width: onWidth }} />
                </div>
                <div className="flex items-center justify-between text-[9px] text-slate-400">
                  <span>Neutral</span>
                  <span>{fmt(neutral, 0)}%</span>
                </div>
                <div className="h-1.5 rounded bg-white/10 overflow-hidden">
                  <div className="h-full rounded bg-amber-500" style={{ width: neutralWidth }} />
                </div>
                <div className="flex items-center justify-between text-[9px] text-slate-400">
                  <span>Risk-off</span>
                  <span>{fmt(riskOff, 0)}%</span>
                </div>
                <div className="h-1.5 rounded bg-white/10 overflow-hidden">
                  <div className="h-full rounded bg-rose-500" style={{ width: offWidth }} />
                </div>
              </div>
              <div className="flex items-center justify-between pt-1 border-t border-white/[0.05]">
                <span className="text-[9px] text-slate-500">Confidence</span>
                <span className="text-[10px] font-mono font-bold text-white">{confidence != null ? `${fmt(confidence * 100, 0)}%` : '—'}</span>
              </div>
            </>
          )}
        </div>
      </div>
    );
  };

  return (
    <div className="space-y-4 animate-in fade-in duration-300">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-sm font-bold text-white">Research</h2>
          <p className="text-[10px] text-slate-500">Signals across asset classes</p>
        </div>
        <div className="flex items-center gap-2">
          <div className="flex bg-slate-900/60 rounded-md p-0.5 border border-white/[0.06]">
            <button
              onClick={() => setActiveSection('signals')}
              className={`px-3 py-1 text-[10px] font-bold rounded ${activeSection === 'signals' ? 'bg-blue-500 text-white' : 'text-slate-400 hover:text-white'}`}
            >Signals</button>
            <button
              onClick={() => setActiveSection('regime')}
              className={`px-3 py-1 text-[10px] font-bold rounded ${activeSection === 'regime' ? 'bg-blue-500 text-white' : 'text-slate-400 hover:text-white'}`}
            >Regime</button>
          </div>
          <button onClick={activeSection === 'regime' ? refreshRegime : refreshSignals} className="px-3 py-1 bg-blue-500 hover:bg-blue-400 text-white text-[10px] font-bold rounded-md">🔄 Refresh</button>
        </div>
      </div>

      {error && (
        <div className="p-3 rounded-lg bg-rose-500/10 border border-rose-500/20 text-rose-300 text-xs">
          ⚠️ {error}
          <button onClick={refreshSignals} className="ml-2 underline hover:text-rose-200">Retry</button>
        </div>
      )}

      {regimeError && activeSection === 'regime' && (
        <div className="p-3 rounded-lg bg-rose-500/10 border border-rose-500/20 text-rose-300 text-xs">
          ⚠️ {regimeError}
          <button onClick={refreshRegime} className="ml-2 underline hover:text-rose-200">Retry</button>
        </div>
      )}

      {activeSection === 'signals' && loading && (
        <div className="text-center py-12">
          <div className="w-6 h-6 border-2 border-slate-600 border-t-blue-500 rounded-full animate-spin mx-auto mb-2" />
          <p className="text-xs text-slate-500">Loading signals...</p>
        </div>
      )}

      {activeSection === 'signals' && !loading && (
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-bold text-white">{signals.length} signals from /api/signals/universe</span>
            <span className="text-[10px] text-slate-500">{BUCKET_ORDER.map(k => `${k} ${universe[k]?.length || 0}`).join(' · ')}</span>
          </div>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-3">
            {BUCKET_ORDER.map(key => <SignalCard key={key} bucketKey={key} />)}
          </div>
        </div>
      )}

      {activeSection === 'regime' && regimeLoading && (
        <div className="text-center py-12">
          <div className="w-6 h-6 border-2 border-slate-600 border-t-blue-500 rounded-full animate-spin mx-auto mb-2" />
          <p className="text-xs text-slate-500">Loading regime forecasts...</p>
        </div>
      )}

      {activeSection === 'regime' && !regimeLoading && (
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-bold text-white">7-day regime forecasts</span>
            <span className="text-[10px] text-slate-500">{BUCKET_ORDER.map(k => `${k} ${regime[k] ? 'ready' : '—'}`).join(' · ')}</span>
          </div>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-3">
            {BUCKET_ORDER.map(key => <RegimeCard key={key} bucketKey={key} />)}
          </div>
        </div>
      )}
    </div>
  );
};

export default ResearchTab;
