import React, { useMemo, useState } from 'react';
import { api, usePoll, pnlCl, fmtPct, fmtNum } from '../utils';

// Research > Signals — multi-family setups across US · HK · ETF · Crypto · FX · Metals.
// Signal families ARE the deployed strategies (shared vocabulary with Strategies).
// Click a row to open the signal detail drawer (with strategy click-through when deployed).

const MARKET_META = {
  US:     { label: 'United States', sub: 'US equities',    sym: 'US',  hex: '#3b82f6' },
  HK:     { label: 'Hong Kong',     sub: 'HK equities',    sym: 'HK',  hex: '#f43f5e' },
  ETF:    { label: 'ETF',           sub: 'Exchange traded funds', sym: 'ETF', hex: '#8b5cf6' },
  CRYPTO: { label: 'Crypto',        sub: 'Digital assets', sym: 'CR',  hex: '#14b8a6' },
  FX:     { label: 'Forex',         sub: 'Currency pairs', sym: 'FX',  hex: '#0ea5e9' },
  METAL:  { label: 'Metals',        sub: 'Gold & silver',  sym: 'XAU', hex: '#eab308' },
};
const MARKETS = Object.keys(MARKET_META);
const ROWS = [['US', 'HK'], ['ETF', 'METAL'], ['CRYPTO', 'FX']];
const LOW_SCORE = 40; // below this, a setup is "lower conviction" and de-emphasized

const HORIZONS = [
  { key: 'fwd_5d',  label: '5D' },
  { key: 'fwd_20d', label: '20D' },
  { key: 'fwd_1q',  label: '1Q' },
];

const signedPct = (v) => (v == null ? '—' : `${v >= 0 ? '+' : ''}${Number(v).toFixed(2)}%`);

const HorizonChips = ({ s }) => {
  const present = HORIZONS.filter(h => s[h.key] != null);
  if (!present.length) return null;
  return (
    <span className="font-mono text-[9px] text-slate-400 flex-none">
      {present.map(h => `${h.label} ${signedPct(s[h.key])}`).join(' · ')}
    </span>
  );
};

function SignalRow({ s, rank, familyByKey, dim, onClick }) {
  const fam = familyByKey[s.families?.[0]];
  const color = fam?.color || '#3b82f6';
  const multi = (s.families || []).length > 1;
  return (
    <div
      onClick={onClick}
      className={`flex items-center gap-3 px-3.5 py-2 cursor-pointer hover:bg-white/[0.03] border-t border-white/[0.04] ${dim ? 'opacity-55' : ''}`}
    >
      <span className="font-mono text-[13px] font-black w-4 flex-none" style={{ color: rank === 1 && !dim ? color : '#64748b' }}>{rank}</span>
      <div className="min-w-[76px] flex-none">
        <div className="flex items-center gap-1.5">
          <span className="text-[12px] font-bold text-white">{s.ticker}</span>
          <span className={`qr-chip ${s.direction === 'BUY' ? 'qr-chip-emerald' : 'qr-chip-rose'}`}>{s.direction}</span>
        </div>
        <div className="text-[9px] text-slate-500">{s.name}</div>
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-1.5">
          <span className="text-[10px] text-slate-300 truncate" title={s.note || ''}>{s.note}</span>
          {multi && <span className="text-[8px] font-black px-1 py-0.5 rounded bg-amber-500/15 text-amber-400 flex-none" title={`${s.families.length} signal families agree`}>★ {s.families.length}</span>}
        </div>
        <div className="flex items-center gap-1.5 mt-0.5 flex-wrap">
          {(s.families || []).map(fk => {
            const f = familyByKey[fk];
            return (
              <span key={fk} className="text-[8px] font-bold px-1.5 py-0.5 rounded" style={{ background: `${f?.color || '#3b82f6'}22`, color: f?.color || '#3b82f6', opacity: f?.deployed === false ? 0.7 : 1 }}>
                {f?.label || fk}{f?.deployed === false && ' · candidate'}
              </span>
            );
          })}
          {s.change_pct != null && <span className={`font-mono text-[9px] ${pnlCl(s.change_pct)}`}>{fmtPct(s.change_pct)}</span>}
          <HorizonChips s={s} />
        </div>
      </div>
      <div className="w-14 text-right flex-none">
        <div className="font-mono text-[13px] font-bold text-white">{fmtNum(s.potential) ?? '—'}</div>
        {s.potential != null && (
          <div className="h-1 rounded bg-white/10 overflow-hidden mt-1">
            <div className="h-full" style={{ width: `${Math.min(s.potential || 0, 100)}%`, background: color }} />
          </div>
        )}
      </div>
    </div>
  );
}

function MarketColumn({ market, list, familyByKey, onSelect }) {
  const meta = MARKET_META[market];
  const [showWeak, setShowWeak] = useState(false);
  const sorted = useMemo(
    () => [...list].sort((a, b) => (b.potential || 0) - (a.potential || 0)),
    [list],
  );
  const strong = sorted.filter(s => (s.potential || 0) >= LOW_SCORE);
  const weak = sorted.filter(s => (s.potential || 0) < LOW_SCORE);
  const weakVisible = showWeak || strong.length === 0;
  return (
    <div className="jt-surface-strong overflow-hidden" style={{ border: `1px solid ${meta.hex}44`, borderTop: `3px solid ${meta.hex}` }}>
      <div className="flex items-center gap-3 px-3.5 py-2.5" style={{ background: `${meta.hex}24` }}>
        <span className="font-mono text-xl font-black tracking-wide" style={{ color: meta.hex }}>{meta.sym}</span>
        <div className="flex-1">
          <div className="text-[13px] font-bold text-white">{meta.label}</div>
          <div className="text-[9px] text-slate-500">{meta.sub}</div>
        </div>
        <span className="text-[9px] font-bold text-slate-400 bg-white/[0.06] rounded px-2 py-0.5">{sorted.length} setup{sorted.length === 1 ? '' : 's'}</span>
      </div>
      <div className="px-3.5 py-1.5 border-t border-white/[0.05] flex items-center justify-between">
        <span className="text-[9px] uppercase tracking-wide text-slate-500">Top Opportunities · by signal score</span>
        <span className="text-[8px] text-slate-600" title="Score = signal strength 0–100 from the signal engine — NOT a forecast return">score 0–100 ⓘ</span>
      </div>
      {strong.map((s, i) => (
        <SignalRow key={s.ticker} s={s} rank={i + 1} familyByKey={familyByKey} onClick={() => onSelect({ ...s, market })} />
      ))}
      {weak.length > 0 && strong.length > 0 && (
        <button
          onClick={() => setShowWeak(v => !v)}
          className="w-full text-left px-3.5 py-1.5 border-t border-white/[0.04] text-[9px] text-slate-500 hover:text-slate-300 hover:bg-white/[0.02]"
        >
          {showWeak ? '▾ Hide' : '▸ Show'} {weak.length} lower-conviction setup{weak.length === 1 ? '' : 's'} (score &lt; {LOW_SCORE})
        </button>
      )}
      {weakVisible && weak.map((s, i) => (
        <SignalRow key={s.ticker} s={s} rank={strong.length + i + 1} familyByKey={familyByKey} dim onClick={() => onSelect({ ...s, market })} />
      ))}
      {sorted.length === 0 && (
        <div className="py-8 text-center text-[11px] text-slate-600">No setups yet — signal_setups is not populated</div>
      )}
    </div>
  );
}

function SignalDetailModal({ signal, familyByKey, onOpenStrategy, onClose }) {
  if (!signal) return null;
  const meta = MARKET_META[signal.market] || {};
  const fams = (signal.families || []).map(fk => ({ key: fk, ...(familyByKey[fk] || {}) }));
  const anyHorizon = HORIZONS.some(h => signal[h.key] != null);
  return (
    <div className="fixed inset-0 z-50 bg-black/60 flex items-center justify-center p-4" onClick={e => e.target === e.currentTarget && onClose()}>
      <div className="jt-surface-strong w-full max-w-md overflow-hidden" style={{ border: `1px solid ${meta.hex || '#3b82f6'}55`, borderTop: `3px solid ${meta.hex || '#3b82f6'}` }}>
        <div className="flex items-center gap-3 px-4 py-3" style={{ background: `${meta.hex || '#3b82f6'}20` }}>
          <div className="flex-1">
            <div className="flex items-center gap-2">
              <span className="text-[15px] font-black text-white">{signal.ticker}</span>
              <span className={`qr-chip ${signal.direction === 'BUY' ? 'qr-chip-emerald' : 'qr-chip-rose'}`}>{signal.direction}</span>
              <span className="text-[9px] font-bold px-1.5 py-0.5 rounded" style={{ background: `${meta.hex}22`, color: meta.hex }}>{meta.label || signal.market}</span>
            </div>
            <div className="text-[10px] text-slate-400 mt-0.5">{signal.name}</div>
          </div>
          <button onClick={onClose} className="text-slate-400 hover:text-white text-lg leading-none px-1">✕</button>
        </div>

        <div className="px-4 py-3 border-t border-white/[0.05]">
          <div className="flex items-baseline justify-between">
            <span className="text-[9px] uppercase tracking-wide text-slate-500">Signal score</span>
            <span className="font-mono text-xl font-black text-white">{fmtNum(signal.potential) ?? '—'}</span>
          </div>
          {signal.potential != null && (
            <div className="h-1.5 rounded bg-white/[0.08] overflow-hidden mt-1.5">
              <div className="h-full" style={{ width: `${Math.min(signal.potential, 100)}%`, background: meta.hex || '#3b82f6' }} />
            </div>
          )}
          <p className="text-[9px] text-slate-500 mt-1.5">
            Signal strength 0–100 (composite weight/confidence from the signal engine) — not a forecast return.
            {signal.potential != null && signal.potential < LOW_SCORE && ' Below 40 = lower conviction; treat as watchlist, not a trade trigger.'}
          </p>
        </div>

        <div className="px-4 py-3 border-t border-white/[0.05]">
          <div className="text-[9px] uppercase tracking-wide text-slate-500 mb-1.5">Forecast horizons</div>
          <div className="grid grid-cols-4 gap-2">
            <div className="text-center rounded bg-white/[0.04] py-2">
              <div className="text-[8px] text-slate-500 uppercase">Today</div>
              <div className={`font-mono text-[12px] font-bold ${signal.change_pct != null ? pnlCl(signal.change_pct) : 'text-slate-600'}`}>{signedPct(signal.change_pct)}</div>
            </div>
            {HORIZONS.map(h => (
              <div key={h.key} className="text-center rounded bg-white/[0.04] py-2">
                <div className="text-[8px] text-slate-500 uppercase">{h.label}</div>
                <div className={`font-mono text-[12px] font-bold ${signal[h.key] != null ? pnlCl(signal[h.key]) : 'text-slate-600'}`}>{signedPct(signal[h.key])}</div>
              </div>
            ))}
          </div>
          {!anyHorizon && (
            <p className="text-[9px] text-slate-600 mt-1.5">5D / 20D / 1Q forecasts pending qr_etl backfill (`fwd_5d`, `fwd_20d`, `fwd_1q` on signal_setups).</p>
          )}
        </div>

        {signal.note && (
          <div className="px-4 py-3 border-t border-white/[0.05]">
            <div className="text-[9px] uppercase tracking-wide text-slate-500 mb-1">Why this signal</div>
            <p className="text-[11px] text-slate-300 leading-relaxed break-words">{signal.note}</p>
          </div>
        )}

        <div className="px-4 py-3 border-t border-white/[0.05]">
          <div className="text-[9px] uppercase tracking-wide text-slate-500 mb-1.5">Signal families</div>
          {fams.length === 0 && <p className="text-[10px] text-slate-600">No family tags on this setup.</p>}
          <div className="flex flex-col gap-1.5">
            {fams.map(f => (
              <div key={f.key} className="flex items-center gap-2">
                <span className="text-[9px] font-bold px-1.5 py-0.5 rounded flex-none" style={{ background: `${f.color || '#3b82f6'}22`, color: f.color || '#3b82f6' }}>
                  {f.label || f.key}
                </span>
                <span className="text-[9px] text-slate-500 flex-1">{f.strategy_id ? (f.deployed ? 'deployed strategy' : 'strategy (not deployed)') : 'candidate pattern — no strategy yet'}</span>
                {f.strategy_id && (
                  <button
                    onClick={() => { onClose(); onOpenStrategy?.(f.strategy_id); }}
                    className="text-[10px] font-bold text-blue-400 hover:text-blue-300 flex-none"
                  >
                    Open strategy →
                  </button>
                )}
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

export const SignalsTab = ({ onOpenStrategy }) => {
  const [universe, setUniverse] = useState({});
  const [families, setFamilies] = useState([]);
  const [asOf, setAsOf] = useState(null);
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState(null);

  usePoll(async () => {
    const [uni, fam] = await Promise.all([
      api.get(`/api/signals/universe?markets=${MARKETS.join(',')}&limit=8`),
      api.get('/api/signals/families'),
    ]);
    setUniverse(uni?.data || {});
    setAsOf(uni?.as_of || null);
    setFamilies(fam?.data || []);
    setLoading(false);
  }, 300000); // 5 min — matches signal_setups DE refresh cadence

  const familyByKey = useMemo(() => {
    const m = {};
    families.forEach(f => { m[f.key] = f; });
    return m;
  }, [families]);

  return (
    <div className="space-y-3">
      <div className="flex items-end justify-between">
        <div>
          <h2 className="text-sm font-bold text-white">Signals</h2>
          <p className="text-[10px] text-slate-500">Stock-level setups ranked by signal score (0–100 strength, not a return) — click a row for details</p>
        </div>
        {asOf && <span className="text-[9px] text-slate-600">as of {new Date(asOf).toLocaleTimeString()}</span>}
      </div>
      {loading ? (
        <div className="qr-surface px-3 py-6 flex items-center justify-center gap-2 text-[11px] text-slate-500">
          <div className="w-3 h-3 border-2 border-slate-700 border-t-blue-500 rounded-full animate-spin" />
          Loading signal universe…
        </div>
      ) : (
        ROWS.map((row, i) => (
          <div key={i} className="grid grid-cols-1 lg:grid-cols-2 gap-3">
            {row.map(market => (
              <MarketColumn
                key={market}
                market={market}
                list={universe[market] || []}
                familyByKey={familyByKey}
                onSelect={setSelected}
              />
            ))}
          </div>
        ))
      )}
      <SignalDetailModal signal={selected} familyByKey={familyByKey} onOpenStrategy={onOpenStrategy} onClose={() => setSelected(null)} />
    </div>
  );
};

export default SignalsTab;
