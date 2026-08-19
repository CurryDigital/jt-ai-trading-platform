import React, { useMemo, useState, useEffect } from 'react';
import { api, usePoll, fmtK, fmtPct, fmtAge, pnlCl } from '../utils';
import { FR, FR_NAME, PANEL_SOURCES, panelFreshness, useFreshness, fmtAgeSec } from '../freshness';

// Re-zoned Command Center — JTCML workspace redesign:
//   1) Market Status band (US · HK)   2) My Book (equity curve + KPIs)
//   3) Pipeline + Deployed Health     4) Action Center (Needs Attention)

// Restrained palette: colour carries meaning only.
//   rose  = critical severity   emerald/rose text = signed P&L (via pnlCl)
//   blue  = interactive links   everything else = neutral slate/white
const SEV_STYLE = {
  critical: { border: 'border-l-rose-500', bg: 'bg-rose-500/[0.06]', tag: 'text-rose-300 bg-rose-500/15' },
  warning:  { border: 'border-l-slate-500', bg: '', tag: 'text-slate-300 bg-white/[0.07]' },
  info:     { border: 'border-l-slate-700', bg: '', tag: 'text-slate-400 bg-white/[0.05]' },
};
const SEV_RANK = { critical: 0, warning: 1, info: 2 };

function EquityCurve({ data, color }) {
  if (!data || data.length < 2) {
    return <div className="h-32 flex items-center justify-center text-[11px] text-slate-600">No equity history yet</div>;
  }
  const margin = { left: 42, right: 8, top: 8, bottom: 22 };
  const values = data.map(d => d.equity);
  const min = Math.min(...values), max = Math.max(...values), range = (max - min) || 1;
  const w = 600, h = 172;
  const plotW = w - margin.left - margin.right;
  const plotH = h - margin.top - margin.bottom;
  const x = (i) => margin.left + (i / (values.length - 1)) * plotW;
  const y = (v) => margin.top + plotH - ((v - min) / range) * plotH;
  const line = values.map((v, i) => `${x(i)},${y(v)}`).join(' ');
  const area = `${margin.left},${margin.top + plotH} ${line} ${margin.left + plotW},${margin.top + plotH}`;
  const id = 'jt-eq-grad';
  const yTicks = [min, (min + max) / 2, max];
  const monthTicks = data.map((d, i) => ({ i, label: d.d, date: new Date(d.d + 'T00:00:00') })).filter((d, i, arr) => {
    if (i === 0) return true;
    const prev = arr[i - 1].date;
    return d.date.getMonth() !== prev.getMonth() || d.date.getFullYear() !== prev.getFullYear();
  });
  return (
    <svg viewBox={`0 0 ${w} ${h}`} preserveAspectRatio="xMidYMid meet" className="w-full block" style={{ height: h }}>
      <defs>
        <linearGradient id={id} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor={color} stopOpacity="0.28" />
          <stop offset="100%" stopColor={color} stopOpacity="0" />
        </linearGradient>
      </defs>
      {[0, 0.5, 1].map(f => {
        const gy = margin.top + plotH * f;
        return <line key={f} x1={margin.left} y1={gy} x2={margin.left + plotW} y2={gy} stroke="rgba(255,255,255,0.08)" strokeWidth="1" vectorEffect="non-scaling-stroke" />;
      })}
      <polygon points={area} fill={`url(#${id})`} />
      <polyline points={line} fill="none" stroke={color} strokeWidth="2" strokeLinejoin="round" strokeLinecap="round" vectorEffect="non-scaling-stroke" />
      <line x1={margin.left} y1={margin.top} x2={margin.left} y2={margin.top + plotH} stroke="rgba(255,255,255,0.15)" strokeWidth="1" vectorEffect="non-scaling-stroke" />
      <line x1={margin.left} y1={margin.top + plotH} x2={margin.left + plotW} y2={margin.top + plotH} stroke="rgba(255,255,255,0.15)" strokeWidth="1" vectorEffect="non-scaling-stroke" />
      {yTicks.map((v, i) => (
        <text key={i} x={margin.left - 5} y={y(v) + 3} textAnchor="end" fill="rgba(148,163,184,0.7)" fontSize="8" fontFamily="ui-monospace, SFMono-Regular, Menlo, monospace">
          {fmtK(v)}
        </text>
      ))}
      {monthTicks.map((t, i) => (
        <text key={i} x={x(t.i)} y={h - 6} textAnchor="middle" fill="rgba(148,163,184,0.7)" fontSize="8" fontFamily="ui-monospace, SFMono-Regular, Menlo, monospace">
          {t.date.toLocaleDateString('en-US', { month: 'short' })}
        </text>
      ))}
    </svg>
  );
}

// Freshness tag colors — palette rule: rose = bad states, teal = aging,
// everything else neutral slate. No amber/violet.
const FR_TAG_CL = {
  [FR.FRESH]: 'text-slate-600',
  [FR.LAGGING]: 'text-teal-300',
  [FR.UNKNOWN]: 'text-slate-600',
  [FR.STALE]: 'text-rose-400',
  [FR.DISCONNECTED]: 'text-rose-300',
};

// Per-panel as-of tag. Tooltip names the culprit source and its configured
// staleness budget so a stale panel explains itself.
const FreshTag = ({ fresh }) => {
  if (!fresh) return null;
  const { state, asOfSec, culprit } = fresh;
  const tip = culprit
    ? `${FR_NAME[state]} — source ${culprit.name}${culprit.budgetH != null ? ` (budget ${culprit.budgetH}h)` : ''}`
    : FR_NAME[state];
  const text = state === FR.UNKNOWN ? 'upd ?'
    : state === FR.DISCONNECTED ? 'no feed'
    : `upd ${fmtAgeSec(asOfSec)}`;
  return <span className={`font-mono text-[9px] normal-case tracking-normal ${FR_TAG_CL[state]}`} title={tip}>{text}</span>;
};

// Panel: when DISCONNECTED the numbers are masked ('--') and the muted
// footer keeps the last-known value visible; when STALE the body desaturates
// and gets a diagonal hatch so no figure reads as live.
const Panel = ({ title, action, children, className = '', fresh }) => {
  const stale = fresh?.state === FR.STALE;
  const disc = fresh?.state === FR.DISCONNECTED;
  return (
    <div className={`qr-surface overflow-hidden ${className}`}>
      <div className="flex items-center justify-between px-3 py-1.5 border-b border-white/[0.05]">
        <span className="qr-label flex items-center gap-2">{title}{fresh && <FreshTag fresh={fresh} />}</span>
        {action}
      </div>
      {disc ? (
        <div className="px-3 py-4">
          <div className="font-mono text-lg text-slate-600">--</div>
          <div className="text-[9px] text-slate-600 mt-1">
            feed disconnected · last known {fresh.lastKnown ?? '—'}{fresh.culprit ? ` · ${fresh.culprit.name}` : ''}
          </div>
        </div>
      ) : (
        <div className={`relative ${stale ? 'qr-fresh-desat' : ''}`}>
          {children}
          {stale && <div className="qr-hatch absolute inset-0 pointer-events-none" />}
        </div>
      )}
    </div>
  );
};

const LinkBtn = ({ children, onClick }) => (
  <button onClick={onClick} className="text-[10px] font-semibold text-blue-400 hover:text-blue-300">{children}</button>
);

// Freshness wrapper for surfaces that are not Panel components (KPI grids,
// asset-class boxes). Same contract: STALE = desaturate + hatch,
// DISCONNECTED = masked numbers + muted last-known footer.
const FreshWrap = ({ fresh, lastKnown, className = '', children }) => {
  if (fresh?.state === FR.DISCONNECTED) {
    return (
      <div className={`qr-surface px-3 py-4 ${className}`}>
        <div className="font-mono text-lg text-slate-600">--</div>
        <div className="text-[9px] text-slate-600 mt-1">
          feed disconnected · last known {lastKnown ?? '—'}{fresh.culprit ? ` · ${fresh.culprit.name}` : ''}
        </div>
      </div>
    );
  }
  const stale = fresh?.state === FR.STALE;
  return (
    <div className={`relative ${stale ? 'qr-fresh-desat' : ''} ${className}`}>
      {children}
      {stale && <div className="qr-hatch absolute inset-0 pointer-events-none rounded-lg" />}
    </div>
  );
};

const BreadthBar = ({ label, bd }) => {
  const total = bd ? (bd.advancing || 0) + (bd.declining || 0) + (bd.unchanged || 0) : 0;
  return (
    <div>
      <div className="flex justify-between mb-1">
        <span className="qr-label">{label}</span>
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

function MarketBand({ navigateToTab, fresh }) {
  const [indices, setIndices] = useState([]);
  const [breadth, setBreadth] = useState({ us: null, hk: null });
  const [sentiment, setSentiment] = useState(null);
  const [movers, setMovers] = useState({ gainers: [], losers: [] });

  const loadMarketData = async () => {
    const ov = await api.get('/api/markets/overview?regions=US,HK');
    if (!ov) return;
    const rawIdx = ov.indices?.data || ov.indices;
    setIndices(Array.isArray(rawIdx) ? rawIdx : []);
    setBreadth(ov.breadth || { us: null, hk: null });
    setSentiment(ov.sentiment || null);
    setMovers(ov.movers || { gainers: [], losers: [] });
  };

  // Initial load on mount, then visibility-aware polling every 15s.
  useEffect(() => { loadMarketData(); }, []);
  usePoll(loadMarketData, 15000);

  const us = sentiment?.us || sentiment;
  const hk = sentiment?.hk;
  const usFg = us?.fear_greed;
  const hkFg = hk?.fear_greed;

  const isHK = (ticker) => ticker != null && ticker.endsWith('.HK');
  const regionMovers = (reg) => {
    const gain = movers.gainers.filter(m => isHK(m.ticker) === (reg === 'HK')).slice(0, 3);
    const lose = movers.losers.filter(m => isHK(m.ticker) === (reg === 'HK')).slice(0, 3);
    return { gain, lose };
  };

  return (
    <Panel title="Market Status" fresh={fresh} action={
      <span className="flex items-center gap-2">
        <span className="text-[9px] text-slate-600">poll 15s</span>
        <LinkBtn onClick={() => navigateToTab('research')}>Markets →</LinkBtn>
      </span>
    }>
      <div className="grid grid-cols-1 divide-y divide-white/[0.05]">
        {['US', 'HK'].map((reg) => {
          const bd = breadth[reg.toLowerCase()];
          const { gain, lose } = regionMovers(reg);
          const fg = reg === 'US' ? usFg : hkFg;
          const sent = reg === 'US' ? us : hk;
          return (
            <div key={reg} className="p-2.5">
              <div className="flex items-center gap-2 mb-2">
                <span className="font-mono text-sm font-black tracking-wide text-white">{reg}</span>
                <span className="qr-label">{reg === 'US' ? 'US Markets' : 'HK Markets'}</span>
              </div>

              {(() => {
                const regionIdx = indices.filter(i => i.region === reg).slice(0, 4);
                const emptySlots = Math.max(0, 4 - regionIdx.length);
                return (
                  <div className="mb-2.5 h-[172px] flex flex-col justify-between overflow-x-auto">
                    {(() => {
                      const cols = [
                        { key: 'change_1d', label: '1D', est: false },
                        { key: 'change_1w', label: '1W', est: false },
                        { key: 'change_1m', label: '1M', est: false },
                        { key: 'change_ytd', label: 'YTD', est: false },
                        { key: 'est_1d', label: 'Est 1D', est: true },
                        { key: 'est_1w', label: 'Est 1W', est: true },
                        { key: 'est_1m', label: 'Est 1M', est: true },
                      ];
                      const showEst = regionIdx.some(i => cols.some(c => c.est && i[c.key] != null));
                      const visibleCols = cols.filter(c => !c.est || showEst);
                      const gridCols = `70px 64px repeat(${visibleCols.length}, minmax(44px, 1fr))`;
                      return (
                        <div className="min-w-[620px]">
                          <div className="grid gap-x-0.5 px-0.5 text-[9px] font-semibold text-slate-500 uppercase tracking-wide whitespace-nowrap" style={{ gridTemplateColumns: gridCols }}>
                            <span className="whitespace-nowrap">Index</span>
                            <span className="text-right whitespace-nowrap">Last</span>
                            {visibleCols.map(c => (
                              <span key={c.key} className={`text-right whitespace-nowrap ${c.est ? 'text-slate-600' : ''}`}>{c.label}</span>
                            ))}
                          </div>
                          {regionIdx.map(i => (
                            <div key={i.sym} className="grid gap-x-0.5 px-0.5 h-[36px] items-center text-[11px] border-b border-white/[0.03] last:border-0 whitespace-nowrap" style={{ gridTemplateColumns: gridCols }}>
                              <div className="font-bold text-white truncate">{i.sym}</div>
                              <div className="font-mono text-right text-slate-200 truncate">{i.last != null ? i.last.toLocaleString() : '—'}</div>
                              {visibleCols.map(c => {
                                const val = c.key === 'change_1d' && i.change_1d == null ? i.change_pct : i[c.key];
                                const isNum = typeof val === 'number' && !isNaN(val);
                                const isStr = typeof val === 'string';
                                return (
                                  <div key={c.key} className={`font-mono text-right whitespace-nowrap ${c.est ? 'text-slate-400' : pnlCl(val)}`}>
                                    {isNum ? fmtPct(val) : isStr ? (
                                      <span className={`inline-block px-1 rounded-[3px] text-[9px] font-bold uppercase ${val === 'BULLISH' ? 'bg-emerald-500/10 text-emerald-300' : val === 'BEARISH' ? 'bg-rose-500/10 text-rose-300' : 'bg-white/[0.05] text-slate-400'}`}>{val}</span>
                                    ) : '—'}
                                  </div>
                                );
                              })}
                            </div>
                          ))}
                          {Array.from({ length: emptySlots }).map((_, idx) => (
                            <div key={`empty-${idx}`} className="grid gap-x-0.5 px-0.5 h-[36px] items-center border-b border-white/[0.03] last:border-0" style={{ gridTemplateColumns: gridCols }}>
                              <span className="text-slate-700">—</span>
                            </div>
                          ))}
                        </div>
                      );
                    })()}
                  </div>
                );
              })()}

              <div className="h-[34px]">
                <BreadthBar label="Adv/Dec" bd={bd} />
              </div>

              <div className="mt-2.5 grid grid-cols-2 gap-2">
                <div className="rounded bg-white/[0.03] px-2 h-[58px] flex flex-col justify-center">
                  <div className="qr-label">Fear / Greed</div>
                  <div className="font-mono text-base font-bold leading-tight text-white">{fg ?? '—'}</div>
                  <div className="text-[9px] text-slate-500 truncate h-[12px]">
                    {sent?.fear_greed_label || ' '}
                  </div>
                </div>
                <div className={`rounded px-2 h-[58px] flex flex-col justify-center ${reg === 'US' ? 'bg-white/[0.03]' : 'bg-white/[0.02]'}`}>
                  <div className="qr-label">VIX</div>
                  <div className="font-mono text-base font-bold leading-tight text-white">
                    {reg === 'US' ? (us?.vix ?? '—') : 'N/A'}
                  </div>
                  <div className="text-[9px] text-slate-500 truncate h-[12px]">{reg === 'US' ? 'CBOE' : ' '}</div>
                </div>
              </div>

              <div className="mt-2.5 space-y-1 min-h-[44px]">
                {[
                  { label: 'Gainers', list: gain },
                  { label: 'Losers', list: lose }
                ].map(({ label, list }) => (
                  <div key={label} className="flex items-center gap-2 h-[22px]">
                    <span className="qr-label flex-none w-[52px]">{label}</span>
                    <div className="flex-1 grid grid-cols-3 gap-1.5">
                      {[0, 1, 2].map(i => {
                        const m = list[i];
                        return m ? (
                          <span key={m.ticker} className="inline-flex items-center justify-between gap-1.5 px-1.5 py-0.5 rounded bg-white/[0.04] border border-white/[0.06] min-w-0">
                            <span className="text-[10px] font-bold text-slate-200 truncate">{m.ticker}</span>
                            <span className={`text-[10px] font-mono flex-none ${pnlCl(m.change_pct)}`}>{fmtPct(m.change_pct)}</span>
                          </span>
                        ) : <span key={`slot-${i}`} className="rounded bg-white/[0.02]" />;
                      })}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          );
        })}
      </div>
    </Panel>
  );
}

// Regime + Alignment (P0-2): one row per market — regime label, days in the
// current regime, HMM posterior confidence, and active-strategy fit counts
// (declared regime_scope vs current regime; ANY = agnostic, never conflict).
// HK has no HMM series — confidence/days render '—' (no-data), never zero.
const RegimeRow = ({ region, r }) => {
  const fit = r?.fit;
  return (
    <div className="flex items-center gap-3 px-3 py-2">
      <span className="font-mono text-[11px] font-black text-white w-[26px] flex-none">{region}</span>
      <span className="font-mono text-[13px] font-bold text-slate-100 w-[88px] flex-none truncate" title={r?.as_of ? `label as of ${r.as_of}` : undefined}>
        {r?.regime ?? '—'}
      </span>
      <span className="text-[10px] text-slate-400 w-[86px] flex-none" title="Consecutive sessions in current regime (gold.regime_label)">
        {r?.days_in_regime != null ? `${r.days_in_regime}d in regime` : '— in regime'}
      </span>
      <span className="text-[10px] text-slate-400 w-[76px] flex-none" title="HMM posterior confidence (gold.regime_label)">
        {r?.confidence != null ? `conf ${(r.confidence * 100).toFixed(2)}%` : 'conf —'}
      </span>
      {fit ? (
        <span className="flex items-center gap-2 text-[10px] font-mono min-w-0" title="Active strategies (paper/live) whose declared regime-fit matches vs conflicts with the current regime; ANY scope is agnostic">
          <span className="text-slate-300">{fit.matched} match</span>
          <span className={fit.conflicted > 0 ? 'text-rose-400 font-bold' : 'text-slate-500'}>{fit.conflicted} conflict</span>
          <span className="text-slate-600 truncate">{fit.agnostic} agnostic / {fit.active} active</span>
        </span>
      ) : <span className="text-[10px] text-slate-600">fit —</span>}
      {r?.staleness_days > 1 && (
        <span className="ml-auto flex-none text-[9px] font-mono text-slate-600" title="gold.regime_label is behind the calendar">
          label {r.staleness_days}d old
        </span>
      )}
    </div>
  );
};

export const CommandCenter = ({ data, navigateToTab, onSelectStrategy }) => {
  const [overview, setOverview] = useState(null);
  const registry = useFreshness();

  usePoll(async () => {
    const res = await api.get('/api/command/overview');
    if (res) setOverview(res);
  }, 60000);

  const positions = data?.positions || [];
  const longMV = positions.filter(p => p.side === 'LONG').reduce((s, p) => s + (p.market_value || 0), 0);
  const shortMV = positions.filter(p => p.side === 'SHORT').reduce((s, p) => s + (p.market_value || 0), 0);
  const openPnl = positions.reduce((s, p) => s + (p.unrealized_pnl || p.pnl || 0), 0);

  const account = overview?.account;
  const equity = account?.equity;
  const eqCurve = overview?.equity_curve || [];
  const ret30 = eqCurve.length > 1 ? ((eqCurve[eqCurve.length - 1].equity - eqCurve[0].equity) / eqCurve[0].equity) * 100 : null;
  const gross = account?.gross_exp_pct;
  const net = account?.net_exp_pct;

  const monthlyPnl = overview?.monthly_pnl || {};
  const assetBreakdown = overview?.asset_breakdown || [];
  const paperBook = overview?.paper_book_month || { leaders: [], laggards: [] };
  const deployedHealth = overview?.deployed_health || [];
  const strategyRisks = useMemo(() => overview?.strategy_risks || [], [overview]);
  const monitoringGap = overview?.monitoring_gap || 0;
  const regime = overview?.regime_alignment || {};

  // Merged attention queue (P0-2): strategy risks + monitoring gap + platform
  // items in ONE panel, sorted by severity then recency (risks carry no
  // timestamp — nulls sort last within a severity tier).
  const attentionItems = useMemo(() => {
    const items = [];
    for (const s of strategyRisks) items.push({
      kind: 'risk', sev: s.sev, tag: 'RISK', title: s.name,
      impact: `PF ${s.paper_pf != null ? s.paper_pf.toFixed(2) : '—'} · P&L ${s.paper_pnl >= 0 ? '+' : ''}${fmtK(s.paper_pnl)} · WR ${s.paper_wr}% · ${s.closed_trades} closed`,
      ts: null, age: null, strategyId: s.strategy_id, action: 'Review',
      key: `risk-${s.strategy_id}`,
    });
    if (monitoringGap > 0) items.push({
      kind: 'gap', sev: 'info', tag: 'GAPS',
      title: `${monitoringGap} paper strateg${monitoringGap === 1 ? 'y' : 'ies'} not actively monitored`,
      impact: 'Registry says PAPER but no ACTIVE paper deployment — no live signal tracking running.',
      ts: null, age: null, target: 'strategies', action: 'Review', key: 'gap',
    });
    for (const a of (overview?.attention || [])) {
      const raw = a.created_at;
      const ts = raw ? new Date(/Z|[+-]\d{2}:?\d{2}$/.test(raw) ? raw : raw + 'Z').getTime() : null;
      items.push({
        kind: 'platform', sev: a.sev, tag: a.tag, title: a.title, impact: a.impact,
        ts, age: a.age || fmtAge(a.created_at), target: a.target, action: a.action || 'Review',
        key: `plat-${a.ref_id || a.title}`,
      });
    }
    items.sort((x, y) => (SEV_RANK[x.sev] ?? 9) - (SEV_RANK[y.sev] ?? 9) || (y.ts ?? -1) - (x.ts ?? -1));
    return items;
  }, [overview, strategyRisks, monitoringGap]);

  const sevCounts = attentionItems.reduce((m, a) => ({ ...m, [a.sev]: (m[a.sev] || 0) + 1 }), {});

  // Markets band collapsed by default (P0-2), persisted per user/browser.
  const [marketsOpen, setMarketsOpen] = useState(() => {
    try { return localStorage.getItem('command.marketsOpen') === '1'; } catch { return false; }
  });
  const toggleMarkets = () => setMarketsOpen(o => {
    try { localStorage.setItem('command.marketsOpen', o ? '0' : '1'); } catch { /* private mode */ }
    return !o;
  });

  const monthModes = [
    { key: 'sim', label: 'Simulation' },
    { key: 'paper', label: 'Paper' },
    { key: 'live', label: 'Live' },
  ];

  // Per-panel freshness from the source→panel dependency map (never tagged
  // by hand — panels inherit the worst state of their upstream sources).
  const fMarket = panelFreshness(PANEL_SOURCES.market, registry);
  const fBook = panelFreshness(PANEL_SOURCES.myBook, registry);
  const fAsset = panelFreshness(PANEL_SOURCES.paperBookAsset, registry);
  const fMonth = panelFreshness(PANEL_SOURCES.monthlyPnl, registry);
  const fPaperMonth = panelFreshness(PANEL_SOURCES.paperBookMonth, registry);
  const fAttention = panelFreshness(PANEL_SOURCES.attention, registry);
  const fRegime = panelFreshness(PANEL_SOURCES.regime, registry);

  return (
    <div className="space-y-3">
      <div className="flex items-end justify-between">
        <div>
          <h1 className="text-sm font-bold text-white">Command</h1>
          <p className="text-[10px] text-slate-500">attention · my book · regime alignment</p>
        </div>
      </div>

      {/* ZONE 1 — Attention: merged strategy risks + monitoring gap + platform
          alerts in a single panel, severity then recency (P0-2). The most
          actionable content sits first. */}
      <Panel title="Attention" fresh={fAttention} action={
        <span className="flex items-center gap-2 whitespace-nowrap">
          {sevCounts.critical > 0 && <span className="text-[9px] font-bold text-rose-400">{sevCounts.critical} critical</span>}
          {sevCounts.warning > 0 && <span className="text-[9px] font-bold text-slate-400">{sevCounts.warning} warning</span>}
          {sevCounts.info > 0 && <span className="text-[9px] text-slate-500">{sevCounts.info} info</span>}
          {attentionItems.length === 0 && <span className="text-[9px] text-slate-500">clear</span>}
        </span>
      }>
        {attentionItems.map((a, i) => {
          const sv = SEV_STYLE[a.sev] || SEV_STYLE.info;
          const onAct = () => a.strategyId ? onSelectStrategy?.(a.strategyId) : navigateToTab(a.target || 'command');
          return (
            <div key={a.key} className={`flex items-center gap-3 py-2 px-3 border-l-2 ${sv.border} ${sv.bg} ${i > 0 ? 'border-t border-t-white/[0.05]' : ''}`}>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <span className={`text-[8px] font-black tracking-wide px-1.5 py-0.5 rounded ${sv.tag}`}>{a.tag}</span>
                  <button onClick={onAct} className="text-[12px] font-bold text-white truncate hover:opacity-80 text-left">{a.title}</button>
                </div>
                <div className="text-[10px] text-slate-500 mt-0.5 truncate" title={a.impact}>{a.impact}</div>
              </div>
              <span className="font-mono text-[10px] text-slate-600 flex-none">{a.age || '—'}</span>
              <button onClick={onAct} className="flex-none text-[10px] font-bold px-2.5 py-1 rounded bg-white/[0.06] hover:bg-white/[0.1] text-slate-200">{a.action}</button>
            </div>
          );
        })}
        {attentionItems.length === 0 && (
          <div className="py-6 text-center text-[11px] text-slate-600">Nothing needs attention right now</div>
        )}
      </Panel>

      {/* ZONE 2 — My Book */}
      <div>
        <div className="flex items-center justify-between mb-1.5">
          <span className="qr-label flex items-center gap-2">My Book <FreshTag fresh={fBook} /></span>
          <LinkBtn onClick={() => navigateToTab('execution')}>Portfolio →</LinkBtn>
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-[1.55fr_1fr] gap-3">
          <Panel title="Last 30 Sessions" fresh={{ ...fBook, lastKnown: equity != null ? fmtK(equity) : '—' }} action={
            ret30 != null ? <span className={`qr-num text-[11px] font-bold ${pnlCl(ret30)}`}>{fmtPct(ret30)}</span> : null
          }>
            <div className="px-3.5 pt-2.5 pb-1 flex items-end justify-between">
              <div>
                <div className="font-mono text-2xl font-black text-white leading-none">{equity != null ? fmtK(equity) : '—'}</div>
                <div className="text-[10px] text-slate-500 mt-1">{positions.length} open positions{account?.cash_pct != null ? ` · ${Math.round(account.cash_pct)}% cash` : ''}</div>
              </div>
              <div className="text-right">
                <div className="text-[9px] uppercase tracking-wide text-slate-500">Day P&L</div>
                <div className="flex items-baseline gap-1.5 justify-end">
                  <span className={`font-mono text-[17px] font-black ${pnlCl(account?.day_pnl)}`}>{account?.day_pnl != null ? fmtK(account.day_pnl) : '—'}</span>
                  {account?.day_pnl_pct != null && <span className={`font-mono text-[11px] ${pnlCl(account.day_pnl_pct)}`}>{fmtPct(account.day_pnl_pct)}</span>}
                </div>
              </div>
            </div>
            <EquityCurve data={eqCurve} color="#60a5fa" />
          </Panel>

          <FreshWrap fresh={fBook} lastKnown={account?.open_pnl != null ? fmtK(account.open_pnl) : fmtK(openPnl)} className="grid grid-cols-2 gap-2">
            {[
              { l: 'Open P&L', v: account?.open_pnl != null ? fmtK(account.open_pnl) : fmtK(openPnl), sub: account?.equity ? fmtPct((account.open_pnl ?? openPnl) / account.equity * 100) : null, pos: (account?.open_pnl ?? openPnl) >= 0 },
              { l: 'Buying Power', v: account?.buying_power != null ? fmtK(account.buying_power) : '—', sub: account?.cash_pct != null ? `${Number(account.cash_pct).toFixed(1)}% cash` : null },
              { l: 'Gross Exp', v: gross != null ? `${gross.toFixed(1)}%` : '—', sub: gross != null && Math.abs(gross) > 200 ? 'check backend' : null, pos: gross != null ? gross >= 0 : undefined },
              { l: 'Net Exp', v: net != null ? `${net.toFixed(1)}%` : '—', sub: net != null ? (net >= 0 ? 'net long' : 'net short') : null, pos: net != null ? net >= 0 : undefined },
            ].map(k => (
              <div key={k.l} className="qr-surface p-2.5 flex flex-col justify-center">
                <div className="qr-label">{k.l}</div>
                <div className={`font-mono text-lg font-bold mt-0.5 ${k.pos === undefined ? 'text-white' : pnlCl(k.pos ? 1 : -1)}`}>{k.v}</div>
                {k.sub && <div className="text-[9px] text-slate-500 mt-0.5">{k.sub}</div>}
              </div>
            ))}
          </FreshWrap>
        </div>

        {/* Paper book by asset class — each box: open (mark-to-market,
            theoretical) vs closed YTD (realized, actually banked), with
            trade counts. Same sources as the Strategy Lab Closed/Open P&L
            columns so the numbers reconcile across tabs. */}
        {assetBreakdown.length > 0 && (
          <div className="mt-3">
            <div className="flex items-center justify-between mb-1.5">
              <span className="qr-label flex items-center gap-2">Paper book by asset class <FreshTag fresh={fAsset} /></span>
              <span className="text-[9px] text-slate-600">open = unrealized mark-to-market · closed = realized YTD</span>
            </div>
            <FreshWrap fresh={fAsset} className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-2">
              {assetBreakdown.map(b => (
                <div
                  key={b.asset_class}
                  className="qr-surface p-2.5"
                  title="Open = open paper positions marked to latest signal prices (theoretical) · Closed YTD = realized paper trades (gold.paper_trades_synthetic)"
                >
                  <div className="qr-label">{b.asset_class}</div>
                  <div className="flex items-baseline justify-between mt-1.5">
                    <span className="text-[9px] text-slate-500">Open P&amp;L</span>
                    <span className={`font-mono text-[13px] font-bold ${pnlCl(b.open_pnl)}`}>{b.open_pnl >= 0 ? '+' : ''}{fmtK(b.open_pnl)}</span>
                  </div>
                  <div className="text-[9px] text-slate-500 text-right mt-0.5">
                    {b.open_positions} open trade{b.open_positions === 1 ? '' : 's'}{b.unpriced > 0 ? ` · ${b.unpriced} unpriced` : ''}
                  </div>
                  <div className="flex items-baseline justify-between mt-1.5 pt-1.5 border-t border-white/[0.05]">
                    <span className="text-[9px] text-slate-500">Closed P&amp;L</span>
                    <span className={`font-mono text-[13px] font-bold ${b.closed_trades_ytd ? pnlCl(b.closed_pnl_ytd) : 'text-slate-600'}`}>
                      {b.closed_trades_ytd ? `${b.closed_pnl_ytd >= 0 ? '+' : ''}${fmtK(b.closed_pnl_ytd)}` : '—'}
                    </span>
                  </div>
                  <div className="text-[9px] text-slate-500 text-right mt-0.5">
                    {b.closed_trades_ytd ? `${b.closed_trades_ytd} closed YTD` : 'no closed trades YTD'}
                  </div>
                </div>
              ))}
            </FreshWrap>
          </div>
        )}
      </div>

      {/* ZONE 3 — P&L This Month + Deployed Health */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-3">
        <Panel title="P&L · This Month" fresh={fMonth} action={<span className="text-[9px] text-slate-600">realized · closed trades</span>}>
          <div className="p-3 grid grid-cols-3 gap-2">
            {monthModes.map(m => {
              const b = monthlyPnl[m.key];
              return (
                <div key={m.key} className="rounded bg-white/[0.04] py-2.5 px-2 text-center">
                  <div className="qr-label">{m.label}</div>
                  <div className={`font-mono text-lg font-bold mt-1 ${b ? pnlCl(b.pnl) : 'text-slate-600'}`}>
                    {b ? `${b.pnl >= 0 ? '+' : ''}${fmtK(b.pnl)}` : '—'}
                  </div>
                  <div className="text-[9px] text-slate-500 mt-0.5">
                    {b ? `${b.trades} closed trade${b.trades === 1 ? '' : 's'}` : 'no closed trades'}
                  </div>
                </div>
              );
            })}
          </div>
        </Panel>

        {/* Auto-flip: live deployed health once anything is LIVE; paper book
            attribution (this month) while nothing is deployed. */}
        {deployedHealth.length > 0 ? (
          <Panel title="Deployed Health" fresh={fPaperMonth} action={<LinkBtn onClick={() => navigateToTab('strategies')}>Performance →</LinkBtn>}>
            <table className="w-full">
              <tbody>
                {deployedHealth.map(s => (
                  <tr key={s.strategy_id} className="border-t border-white/[0.05]">
                    <td className="py-1.5 px-3">
                      <button onClick={() => onSelectStrategy?.(s.strategy_id)} className="flex items-center gap-1.5 hover:opacity-80">
                        <span className="w-1.5 h-1.5 rounded-full bg-slate-500" />
                        <span className="text-[11px] font-bold text-white">{s.name}</span>
                      </button>
                      <div className="text-[9px] text-slate-500 ml-3">{s.asset} · {s.live_trades ?? 0} live trades</div>
                    </td>
                    <td className="py-1.5 px-2 text-right font-mono text-[10px] text-slate-400">WR {s.live_win_rate != null ? `${s.live_win_rate}%` : '—'}</td>
                    <td className="py-1.5 px-3 text-right font-mono text-[11px] font-bold text-slate-200" title="Out-of-sample Sharpe ratio">SR {s.sharpe ?? '—'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </Panel>
        ) : (
          <Panel title="Paper Book · This Month" fresh={fPaperMonth} action={<LinkBtn onClick={() => navigateToTab('strategies')}>Performance →</LinkBtn>}>
            <div className="divide-y divide-white/[0.05]">
              {[
                { label: 'Leaders', list: paperBook.leaders },
                { label: 'Laggards', list: paperBook.laggards },
              ].map(({ label, list }) => (
                <div key={label} className="px-3 py-2">
                  <div className="qr-label mb-1">{label}</div>
                  {list.length > 0 ? list.map(s => (
                    <div key={s.strategy_id} className="flex items-center gap-2 h-[22px]">
                      <button onClick={() => onSelectStrategy?.(s.strategy_id)} className="flex-1 min-w-0 text-left text-[11px] font-bold text-slate-200 hover:opacity-80 truncate">{s.name}</button>
                      <span className="text-[9px] text-slate-500 flex-none">{s.closed_trades} tr</span>
                      <span className={`font-mono text-[11px] font-bold flex-none w-[64px] text-right ${pnlCl(s.pnl)}`}>{s.pnl >= 0 ? '+' : ''}{fmtK(s.pnl)}</span>
                    </div>
                  )) : <div className="text-[10px] text-slate-600 py-0.5">—</div>}
                </div>
              ))}
            </div>
          </Panel>
        )}
      </div>

      {/* ZONE 4 — Regime + Alignment (merged from the two per-market Regime
          blocks; US/HK rows: regime, days in regime, HMM confidence, fit) */}
      <Panel title="Regime & Alignment" fresh={fRegime} action={<span className="text-[9px] text-slate-600">declared regime-fit vs current regime</span>}>
        <div className="divide-y divide-white/[0.05]">
          <RegimeRow region="US" r={regime.US} />
          <RegimeRow region="HK" r={regime.HK} />
        </div>
      </Panel>

      {/* ZONE 5 — Markets: collapsed by default, state persisted per user */}
      <div>
        <button onClick={toggleMarkets} className="qr-surface w-full flex items-center justify-between px-3 py-1.5 hover:bg-white/[0.02]">
          <span className="qr-label flex items-center gap-2">Markets <FreshTag fresh={fMarket} /></span>
          <span className="flex items-center gap-2 text-[9px] text-slate-500">
            <span className="font-mono">US {regime.US?.regime ?? '—'} · HK {regime.HK?.regime ?? '—'}</span>
            <span className="text-slate-600">{marketsOpen ? '▾ collapse' : '▸ expand'}</span>
          </span>
        </button>
        {marketsOpen && (
          <div className="mt-2">
            <MarketBand navigateToTab={navigateToTab} fresh={fMarket} />
          </div>
        )}
      </div>
    </div>
  );
};

export default CommandCenter;
