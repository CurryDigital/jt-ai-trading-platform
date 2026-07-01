import React, { useEffect, useMemo, useState } from 'react';
import { api, fmtK, fmtPct, fmtAge, pnlCl } from '../utils';

// Re-zoned Command Center — JTCML workspace redesign:
//   1) Market Status band (US · HK)   2) My Book (equity curve + KPIs)
//   3) Pipeline + Deployed Health     4) Action Center (Needs Attention)

const SEV_STYLE = {
  critical: { border: 'border-l-rose-500', bg: 'bg-rose-500/[0.07]', tag: 'text-rose-400 bg-rose-500/20' },
  warning:  { border: 'border-l-amber-500', bg: 'bg-amber-500/[0.05]', tag: 'text-amber-400 bg-amber-500/20' },
  info:     { border: 'border-l-blue-500', bg: '', tag: 'text-blue-400 bg-blue-500/20' },
};
const SEV_RANK = { critical: 0, warning: 1, info: 2 };

function EquityCurve({ data, color }) {
  if (!data || data.length < 2) {
    return <div className="h-32 flex items-center justify-center text-[11px] text-slate-600">No equity history yet</div>;
  }
  const values = data.map(d => d.equity);
  const min = Math.min(...values), max = Math.max(...values), range = (max - min) || 1;
  const w = 600, h = 128;
  const x = (i) => (i / (values.length - 1)) * w;
  const y = (v) => h - 8 - ((v - min) / range) * (h - 22);
  const line = values.map((v, i) => `${x(i)},${y(v)}`).join(' ');
  const area = `0,${h} ${line} ${w},${h}`;
  const id = 'jt-eq-grad';
  return (
    <svg viewBox={`0 0 ${w} ${h}`} preserveAspectRatio="none" className="w-full block" style={{ height: h }}>
      <defs>
        <linearGradient id={id} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor={color} stopOpacity="0.28" />
          <stop offset="100%" stopColor={color} stopOpacity="0" />
        </linearGradient>
      </defs>
      {[0.25, 0.5, 0.75].map(f => (
        <line key={f} x1="0" y1={h * f} x2={w} y2={h * f} stroke="rgba(255,255,255,0.05)" strokeWidth="1" vectorEffect="non-scaling-stroke" />
      ))}
      <polygon points={area} fill={`url(#${id})`} />
      <polyline points={line} fill="none" stroke={color} strokeWidth="2" strokeLinejoin="round" strokeLinecap="round" vectorEffect="non-scaling-stroke" />
    </svg>
  );
}

function Sparkline({ data, color }) {
  if (!data || !data.length) return <div className="w-[70px] h-[22px]" />;
  const w = 70, h = 22;
  const min = Math.min(...data), max = Math.max(...data), range = (max - min) || 1;
  const pts = data.map((v, i) => `${(i / (data.length - 1)) * w},${h - 2 - ((v - min) / range) * (h - 4)}`);
  return (
    <svg width={w} height={h} className="block">
      <polyline points={pts.join(' ')} fill="none" stroke={color} strokeWidth="1.5" strokeLinejoin="round" strokeLinecap="round" />
    </svg>
  );
}

const Panel = ({ title, action, children, className = '' }) => (
  <div className={`qr-surface overflow-hidden ${className}`}>
    <div className="flex items-center justify-between px-3 py-1.5 border-b border-white/[0.05]">
      <span className="qr-label">{title}</span>
      {action}
    </div>
    {children}
  </div>
);

const LinkBtn = ({ children, onClick }) => (
  <button onClick={onClick} className="text-[10px] font-semibold text-blue-400 hover:text-blue-300">{children}</button>
);

const BreadthBar = ({ label, bd, accent }) => {
  const total = bd ? (bd.advancing || 0) + (bd.declining || 0) + (bd.unchanged || 0) : 0;
  return (
    <div>
      <div className="flex justify-between mb-1">
        <span className={`qr-label ${accent}`}>{label}</span>
        <span className="text-[10px] font-mono text-slate-300">{bd ? `${bd.advancing || 0}/${bd.declining || 0}` : '—'}</span>
      </div>
      <div className="flex h-1.5 rounded overflow-hidden bg-white/5">
        {total > 0 ? (
          <>
            <div className="bg-emerald-500" style={{ width: `${(bd.advancing / total) * 100}%` }} />
            <div className="bg-slate-500" style={{ width: `${(bd.unchanged / total) * 100}%` }} />
            <div className="bg-rose-500" style={{ width: `${(bd.declining / total) * 100}%` }} />
          </>
        ) : <div className="w-full bg-slate-800" />}
      </div>
    </div>
  );
};

function MarketBand({ navigateToTab }) {
  const [indices, setIndices] = useState([]);
  const [breadth, setBreadth] = useState({ us: null, hk: null });
  const [sentiment, setSentiment] = useState(null);
  const [movers, setMovers] = useState({ gainers: [], losers: [] });

  useEffect(() => {
    let alive = true;
    const load = async () => {
      const [idx, brd, sent, mov] = await Promise.all([
        api.get('/api/markets/indices?regions=US,HK'),
        api.get('/api/markets/breadth?regions=US,HK'),
        api.get('/api/markets/sentiment'),
        api.get('/api/markets/movers'),
      ]);
      if (!alive) return;
      setIndices(idx?.data || []);
      setBreadth(brd || { us: null, hk: null });
      setSentiment(sent || null);
      setMovers(mov || { gainers: [], losers: [] });
    };
    load();
    const id = setInterval(load, 15000);
    return () => { alive = false; clearInterval(id); };
  }, []);

  const fg = sentiment?.fear_greed;
  const fgColor = fg == null ? 'text-slate-400' : fg >= 55 ? 'text-emerald-400' : fg >= 45 ? 'text-blue-400' : 'text-rose-400';

  return (
    <Panel title="Market Status" action={
      <span className="flex items-center gap-2">
        <span className="text-[9px] text-slate-600">live · 15s</span>
        <LinkBtn onClick={() => navigateToTab('research')}>Markets →</LinkBtn>
      </span>
    }>
      <div className="grid grid-cols-1 md:grid-cols-2 divide-y md:divide-y-0 md:divide-x divide-white/[0.05]">
        {[['US', 'text-blue-400'], ['HK', 'text-rose-400']].map(([reg, accent]) => (
          <div key={reg} className="p-2.5 flex items-center gap-3">
            <span className={`font-mono text-lg font-black tracking-wide ${accent}`}>{reg}</span>
            <div className="flex-1 grid grid-cols-2 gap-1">
              {indices.filter(i => i.region === reg).map(i => (
                <div key={i.sym} className="flex items-center justify-between gap-2 px-1">
                  <div>
                    <div className="text-[11px] font-bold text-white">{i.sym}</div>
                    <div className="text-[10px] font-mono text-slate-400">{i.last != null ? i.last.toLocaleString() : '—'}</div>
                    <div className={`text-[9px] font-mono ${pnlCl(i.change_pct)}`}>{i.change_pct != null ? fmtPct(i.change_pct) : '—'}</div>
                  </div>
                  <Sparkline data={i.spark} color={(i.change_pct || 0) >= 0 ? '#34d399' : '#fb7185'} />
                </div>
              ))}
              {indices.filter(i => i.region === reg).length === 0 && (
                <div className="col-span-2 text-[10px] text-slate-600">No index data yet</div>
              )}
            </div>
          </div>
        ))}
      </div>
      <div className="p-2.5 grid grid-cols-1 md:grid-cols-4 gap-3 border-t border-white/[0.05]">
        <BreadthBar label="US Breadth" bd={breadth.us} accent="text-blue-400" />
        <BreadthBar label="HK Breadth" bd={breadth.hk} accent="text-rose-400" />
        <div className="rounded bg-white/[0.03] px-2 py-1">
          <div className="qr-label">Fear / Greed</div>
          <div className={`font-mono text-base font-bold ${fgColor}`}>{fg ?? '—'}<span className="text-[9px] ml-1 text-slate-500">{sentiment?.fear_greed_label || ''}</span></div>
        </div>
        <div className="rounded bg-white/[0.03] px-2 py-1">
          <div className="qr-label">VIX</div>
          <div className="font-mono text-base font-bold text-white">{sentiment?.vix ?? '—'}</div>
        </div>
      </div>
      {(movers.gainers.length > 0 || movers.losers.length > 0) && (
        <div className="flex items-center gap-3 px-3 py-1.5 border-t border-white/[0.05] overflow-x-auto">
          <span className="qr-label flex-none">Movers</span>
          {[...movers.gainers, ...movers.losers].map(m => (
            <span key={m.ticker} className="flex items-baseline gap-1 flex-none">
              <span className="text-[11px] font-bold text-white">{m.ticker}</span>
              <span className={`text-[10px] font-mono ${pnlCl(m.change_pct)}`}>{fmtPct(m.change_pct)}</span>
            </span>
          ))}
        </div>
      )}
    </Panel>
  );
}

export const CommandCenter = ({ data, navigateToTab, onSelectStrategy }) => {
  const [overview, setOverview] = useState(null);

  useEffect(() => {
    let alive = true;
    const load = async () => {
      const res = await api.get('/api/command/overview');
      if (alive) setOverview(res);
    };
    load();
    const id = setInterval(load, 60000);
    return () => { alive = false; clearInterval(id); };
  }, []);

  const positions = data?.positions || [];
  const longMV = positions.filter(p => p.side === 'LONG').reduce((s, p) => s + (p.market_value || 0), 0);
  const shortMV = positions.filter(p => p.side === 'SHORT').reduce((s, p) => s + (p.market_value || 0), 0);
  const openPnl = positions.reduce((s, p) => s + (p.unrealized_pnl || p.pnl || 0), 0);

  const account = overview?.account;
  const equity = account?.equity;
  const eqCurve = overview?.equity_curve || [];
  const ret30 = eqCurve.length > 1 ? ((eqCurve[eqCurve.length - 1].equity - eqCurve[0].equity) / eqCurve[0].equity) * 100 : null;
  const gross = equity ? ((longMV + shortMV) / equity) * 100 : null;
  const net = equity ? ((longMV - shortMV) / equity) * 100 : null;

  const pipeline = overview?.pipeline;
  const deployedHealth = overview?.deployed_health || [];
  const attention = useMemo(() => [...(overview?.attention || [])].sort((a, b) => (SEV_RANK[a.sev] ?? 9) - (SEV_RANK[b.sev] ?? 9)), [overview]);
  const sevCounts = attention.reduce((m, a) => ({ ...m, [a.sev]: (m[a.sev] || 0) + 1 }), {});

  const stages = [
    { key: 'experimental', label: 'Experimental', bg: 'bg-slate-500/10' },
    { key: 'near_golden', label: 'Near Golden', bg: 'bg-blue-500/10' },
    { key: 'golden', label: 'Golden', bg: 'bg-amber-500/10' },
    { key: 'deployed', label: 'Deployed', bg: 'bg-emerald-500/10' },
  ];

  return (
    <div className="space-y-3">
      <div className="flex items-end justify-between">
        <div>
          <h1 className="text-sm font-bold text-white">Command</h1>
          <p className="text-[10px] text-slate-500">My book · pipeline health · needs attention</p>
        </div>
      </div>

      {/* ZONE 1 — Market Status */}
      <MarketBand navigateToTab={navigateToTab} />

      {/* ZONE 2 — My Book */}
      <div>
        <div className="flex items-center justify-between mb-1.5">
          <span className="qr-label">My Book</span>
          <LinkBtn onClick={() => navigateToTab('execution')}>Portfolio →</LinkBtn>
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-[1.55fr_1fr] gap-3">
          <Panel title="Account Equity · 30 sessions" action={
            ret30 != null ? <span className={`qr-num text-[11px] font-bold ${pnlCl(ret30)}`}>{fmtPct(ret30)}</span> : null
          }>
            <div className="px-3.5 pt-2.5 pb-1 flex items-end justify-between">
              <div>
                <div className="font-mono text-2xl font-black text-white leading-none">{equity != null ? fmtK(equity) : '—'}</div>
                <div className="text-[10px] text-slate-500 mt-1">{positions.length} open positions{account?.cash_pct != null ? ` · ${account.cash_pct}% cash` : ''}</div>
              </div>
              <div className="text-right">
                <div className="text-[9px] uppercase tracking-wide text-slate-500">Day P&L</div>
                <div className="flex items-baseline gap-1.5 justify-end">
                  <span className={`font-mono text-[17px] font-black ${pnlCl(account?.day_pnl)}`}>{account?.day_pnl != null ? fmtK(account.day_pnl) : '—'}</span>
                  {account?.day_pnl_pct != null && <span className={`font-mono text-[11px] ${pnlCl(account.day_pnl_pct)}`}>{fmtPct(account.day_pnl_pct)}</span>}
                </div>
              </div>
            </div>
            <EquityCurve data={eqCurve} color={(ret30 ?? 0) >= 0 ? '#34d399' : '#fb7185'} />
          </Panel>

          <div className="grid grid-cols-2 gap-2">
            {[
              { l: 'Open P&L', v: fmtK(openPnl), sub: (longMV + shortMV) > 0 ? fmtPct(openPnl / (longMV + shortMV) * 100) : null, pos: openPnl >= 0 },
              { l: 'Buying Power', v: account?.buying_power != null ? fmtK(account.buying_power) : '—', sub: account?.cash_pct != null ? `${account.cash_pct}% cash` : null },
              { l: 'Gross Exp', v: gross != null ? `${gross.toFixed(0)}%` : '—', sub: null },
              { l: 'Net Exp', v: net != null ? `${net.toFixed(0)}%` : '—', sub: net >= 0 ? 'net long' : 'net short', pos: net >= 0 },
            ].map(k => (
              <div key={k.l} className="qr-surface p-2.5">
                <div className="qr-label">{k.l}</div>
                <div className={`font-mono text-base font-bold mt-0.5 ${k.pos === undefined ? 'text-white' : pnlCl(k.pos ? 1 : -1)}`}>{k.v}</div>
                {k.sub && <div className="text-[9px] text-slate-500 mt-0.5">{k.sub}</div>}
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* ZONE 3 — Pipeline + Deployed Health */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-3">
        <Panel title="Strategy Pipeline" action={<LinkBtn onClick={() => navigateToTab('strategies')}>Manage →</LinkBtn>}>
          <div className="p-3">
            <div className="flex items-center gap-1.5">
              {stages.map((st, i) => (
                <React.Fragment key={st.key}>
                  {i > 0 && <span className="text-slate-600 text-[11px]">→</span>}
                  <div className={`flex-1 text-center py-2 px-1 rounded ${st.bg}`}>
                    <div className="font-mono text-base font-bold text-white">{pipeline ? (pipeline[st.key] ?? 0) : '—'}</div>
                    <div className="text-[8px] uppercase tracking-wide text-slate-500 mt-0.5">{st.label}</div>
                  </div>
                </React.Fragment>
              ))}
            </div>
            <div className="mt-2 flex justify-between text-[10px] text-slate-500">
              <span>Total: <span className="font-mono text-slate-300">{pipeline?.total ?? '—'}</span></span>
            </div>
          </div>
        </Panel>

        <Panel title="Deployed Health" action={<LinkBtn onClick={() => navigateToTab('strategies')}>Performance →</LinkBtn>}>
          <table className="w-full">
            <tbody>
              {deployedHealth.map(s => (
                <tr key={s.strategy_id} className="border-t border-white/[0.05]">
                  <td className="py-1.5 px-3">
                    <button onClick={() => onSelectStrategy?.(s.strategy_id)} className="flex items-center gap-1.5 hover:opacity-80">
                      <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
                      <span className="text-[11px] font-bold text-white">{s.name}</span>
                    </button>
                    <div className="text-[9px] text-slate-500 ml-3">{s.asset} · {s.live_trades ?? 0} live trades</div>
                  </td>
                  <td className="py-1.5 px-2 text-right font-mono text-[10px] text-slate-400">WR {s.live_win_rate ?? '—'}%</td>
                  <td className={`py-1.5 px-3 text-right font-mono text-[11px] font-bold ${pnlCl(s.return_pct)}`}>{s.return_pct != null ? fmtPct(s.return_pct) : '—'}</td>
                </tr>
              ))}
              {deployedHealth.length === 0 && (
                <tr><td colSpan={3} className="py-6 text-center text-[11px] text-slate-600">No deployed strategies yet</td></tr>
              )}
            </tbody>
          </table>
        </Panel>
      </div>

      {/* ZONE 4 — Action Center */}
      <Panel title="Needs Attention" action={
        <span className="flex items-center gap-2 whitespace-nowrap">
          {sevCounts.critical > 0 && <span className="text-[9px] font-bold text-rose-400">{sevCounts.critical} critical</span>}
          {sevCounts.warning > 0 && <span className="text-[9px] font-bold text-amber-400">{sevCounts.warning} warning</span>}
          {sevCounts.info > 0 && <span className="text-[9px] text-slate-500">{sevCounts.info} info</span>}
        </span>
      }>
        {attention.map((a, i) => {
          const sv = SEV_STYLE[a.sev] || SEV_STYLE.info;
          return (
            <div key={a.ref_id || i} className={`flex items-center gap-3 py-2.5 px-3 border-l-2 ${sv.border} ${sv.bg} ${i > 0 ? 'border-t border-t-white/[0.05]' : ''}`}>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <span className={`text-[8px] font-black tracking-wide px-1.5 py-0.5 rounded ${sv.tag}`}>{a.tag}</span>
                  <span className="text-[12px] font-bold text-white truncate">{a.title}</span>
                </div>
                <div className="text-[10px] text-slate-500 mt-0.5">{a.impact}</div>
              </div>
              <span className="font-mono text-[10px] text-slate-600 flex-none">{a.age || fmtAge(a.created_at)}</span>
              <button
                onClick={() => navigateToTab(a.target || 'command')}
                className={`flex-none text-[10px] font-bold px-2.5 py-1 rounded ${a.sev === 'critical' ? 'bg-rose-600 hover:bg-rose-500 text-white' : 'bg-white/[0.06] hover:bg-white/[0.1] text-slate-200'}`}
              >{a.action || 'Review'}</button>
            </div>
          );
        })}
        {attention.length === 0 && (
          <div className="py-6 text-center text-[11px] text-slate-600">Nothing needs attention right now</div>
        )}
      </Panel>
    </div>
  );
};

export default CommandCenter;
