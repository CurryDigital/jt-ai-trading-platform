import React, { useMemo, useState } from 'react';
import { api, usePoll, pnlCl, fmtPct, fmtNum } from '../utils';

// Research > Signals — multi-family setups across US · HK · Crypto · FX · Metals.
// Signal families ARE the deployed strategies (shared vocabulary with Strategies).
// Click a row to open Strategy Detail (if the family is deployed).

const MARKET_META = {
  US:     { label: 'United States', sub: 'US equities',    sym: 'US',  hex: '#3b82f6' },
  HK:     { label: 'Hong Kong',     sub: 'HK equities',    sym: 'HK',  hex: '#f43f5e' },
  CRYPTO: { label: 'Crypto',        sub: 'Digital assets', sym: 'CR',  hex: '#14b8a6' },
  FX:     { label: 'Forex',         sub: 'Currency pairs', sym: 'FX',  hex: '#0ea5e9' },
  METAL:  { label: 'Metals',        sub: 'Gold & silver',  sym: 'XAU', hex: '#eab308' },
};
const MARKETS = Object.keys(MARKET_META);
const ROWS = [['US', 'HK'], ['CRYPTO', 'FX', 'METAL']];

export const SignalsTab = ({ onOpenStrategy }) => {
  const [universe, setUniverse] = useState({});
  const [families, setFamilies] = useState([]);
  const [asOf, setAsOf] = useState(null);
  const [loading, setLoading] = useState(true);

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

  const Column = ({ market }) => {
    const meta = MARKET_META[market];
    const list = [...(universe[market] || [])].sort((a, b) => (b.potential || 0) - (a.potential || 0));
    return (
      <div className="jt-surface-strong overflow-hidden" style={{ border: `1px solid ${meta.hex}44`, borderTop: `3px solid ${meta.hex}` }}>
        <div className="flex items-center gap-3 px-3.5 py-2.5" style={{ background: `${meta.hex}24` }}>
          <span className="font-mono text-xl font-black tracking-wide" style={{ color: meta.hex }}>{meta.sym}</span>
          <div className="flex-1">
            <div className="text-[13px] font-bold text-white">{meta.label}</div>
            <div className="text-[9px] text-slate-500">{meta.sub}</div>
          </div>
          <span className="text-[9px] font-bold text-slate-400 bg-white/[0.06] rounded px-2 py-0.5">{list.length} setups</span>
        </div>
        <div className="px-3.5 py-1.5 border-t border-white/[0.05] text-[9px] uppercase tracking-wide text-slate-500">Top Opportunities · ranked by potential</div>
        {list.map((s, i) => {
          const fam = familyByKey[s.families?.[0]];
          const color = fam?.color || '#3b82f6';
          const multi = (s.families || []).length > 1;
          return (
            <div
              key={s.ticker}
              onClick={() => {
                const f = familyByKey[s.families?.[0]];
                if (f?.strategy_id) onOpenStrategy?.(f.strategy_id);
              }}
              className={`flex items-center gap-3 px-3.5 py-2 cursor-pointer hover:bg-white/[0.03] ${i > 0 ? 'border-t border-white/[0.04]' : ''}`}
            >
              <span className="font-mono text-[13px] font-black w-4 flex-none" style={{ color: i === 0 ? color : '#64748b' }}>{i + 1}</span>
              <div className="min-w-[76px] flex-none">
                <div className="flex items-center gap-1.5">
                  <span className="text-[12px] font-bold text-white">{s.ticker}</span>
                  <span className={`qr-chip ${s.direction === 'BUY' ? 'qr-chip-emerald' : 'qr-chip-rose'}`}>{s.direction}</span>
                </div>
                <div className="text-[9px] text-slate-500">{s.name}</div>
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-1.5">
                  <span className="text-[10px] text-slate-300 truncate">{s.note}</span>
                  {multi && <span className="text-[8px] font-black px-1 py-0.5 rounded bg-amber-500/15 text-amber-400 flex-none">★ {s.families.length}</span>}
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
                </div>
              </div>
              <div className="w-14 text-right flex-none">
                <div className="font-mono text-[13px] font-bold text-white">{fmtNum(s.potential) ?? '—'}</div>
                <div className="h-1 rounded bg-white/10 overflow-hidden mt-1">
                  <div className="h-full" style={{ width: `${Math.min(s.potential || 0, 100)}%`, background: color }} />
                </div>
              </div>
            </div>
          );
        })}
        {list.length === 0 && (
          <div className="py-8 text-center text-[11px] text-slate-600">No setups yet — signal_setups is not populated</div>
        )}
      </div>
    );
  };

  return (
    <div className="space-y-3">
      <div className="flex items-end justify-between">
        <div>
          <h2 className="text-sm font-bold text-white">Signals</h2>
          <p className="text-[10px] text-slate-500">Stock-level analysis — US · HK · Crypto · FX · Metals · click a row to open its strategy</p>
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
          <div key={i} className={`grid grid-cols-1 ${row.length === 2 ? 'lg:grid-cols-2' : 'lg:grid-cols-3'} gap-3`}>
            {row.map(market => <Column key={market} market={market} />)}
          </div>
        ))
      )}
    </div>
  );
};

export default SignalsTab;
