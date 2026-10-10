import React, { useMemo, useState, useEffect, useRef } from 'react';
import { api, usePoll, fmtK, fmtKCcy, fmtCcy, fmtPct, fmtAge, pnlCl, marketClock, marketStatus } from '../utils';
import { FR, FR_NAME, PANEL_SOURCES, panelFreshness, useFreshness, fmtAgeSec } from '../freshness';

// Command home — 2026-09-18 redesign (v2). Layout top-to-bottom:
//   1) Market status strip (slim: indices + sparklines, VIX, US/HK F&G)
//   2) Environment cards SIM / PAPER / UAT / LIVE (clickable book selectors)
//   3) Selected book: full-width cumulative realized P&L chart + KPI row
//      (win rate, open positions, today, cumulative P&L) under it
//   4) Regime Forecast + Top Opportunities (side by side)
//   5) Order Book
// The Action Center moved to Settings ▸ Alerts (components/ActionCenter.jsx);
// a severity-colored alert badge in the global header links to it.
//
// Restrained palette: colour carries meaning only.
//   rose  = critical severity   emerald/rose text = signed P&L (via pnlCl)
//   blue  = interactive links   everything else = neutral slate/white

// Cumulative P&L chart. Width tracks the container via ResizeObserver so the
// chart truly spans the full page width (a fixed viewBox + preserveAspectRatio
// would letterbox); height stays fixed.
function EquityCurve({ data, color, emptyLabel = 'No equity history yet' }) {
  const ref = useRef(null);
  const [width, setWidth] = useState(600);
  useEffect(() => {
    if (!ref.current) return undefined;
    const ro = new ResizeObserver((entries) => {
      setWidth(Math.max(320, Math.round(entries[0].contentRect.width)));
    });
    ro.observe(ref.current);
    return () => ro.disconnect();
  }, []);

  if (!data || data.length < 2) {
    return <div className="h-32 flex items-center justify-center text-[11px] text-slate-600">{emptyLabel}</div>;
  }
  const margin = { left: 46, right: 10, top: 8, bottom: 22 };
  const values = data.map(d => d.equity);
  const min = Math.min(...values), max = Math.max(...values), range = (max - min) || 1;
  const w = width, h = 190;
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
    <div ref={ref}>
      <svg viewBox={`0 0 ${w} ${h}`} className="w-full block" style={{ height: h }}>
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
          <text key={i} x={margin.left - 5} y={y(v) + 3} textAnchor="end" fill="rgba(148,163,184,0.8)" fontSize="9" fontFamily="ui-monospace, SFMono-Regular, Menlo, monospace">
            {fmtK(v)}
          </text>
        ))}
        {monthTicks.map((t, i) => (
          <text key={i} x={x(t.i)} y={h - 6} textAnchor="middle" fill="rgba(148,163,184,0.8)" fontSize="9" fontFamily="ui-monospace, SFMono-Regular, Menlo, monospace">
            {t.date.toLocaleDateString('en-US', { month: 'short' })}
          </text>
        ))}
      </svg>
    </div>
  );
}

// Minimal cumulative-P&L sparkline (no axes — trend shape only).
function Sparkline({ data, height = 36 }) {
  if (!data || data.length < 2) {
    return <div className="flex items-center justify-center text-[9px] text-slate-700" style={{ height }}>no history</div>;
  }
  const values = data.map(d => d.cum);
  const min = Math.min(...values), max = Math.max(...values), range = (max - min) || 1;
  const w = 200, h = height;
  const x = (i) => (i / (values.length - 1)) * w;
  const y = (v) => h - 2 - ((v - min) / range) * (h - 4);
  const line = values.map((v, i) => `${x(i).toFixed(1)},${y(v).toFixed(1)}`).join(' ');
  const up = values[values.length - 1] >= values[0];
  const color = up ? '#34d399' : '#fb7185';
  return (
    <svg viewBox={`0 0 ${w} ${h}`} preserveAspectRatio="none" className="w-full block" style={{ height }}
      title={`30d cumulative realized P&L: ${fmtK(values[0])} → ${fmtK(values[values.length - 1])}`}>
      <polyline points={line} fill="none" stroke={color} strokeWidth="1.5" strokeLinejoin="round" strokeLinecap="round" vectorEffect="non-scaling-stroke" />
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

// Compact KPI tile used by the mode-scoped book grid (Zone 2).
const KpiTile = ({ label, value, valueCl = 'text-white', sub, tip }) => (
  <div className="qr-surface p-2.5 flex flex-col justify-center" title={tip}>
    <div className="qr-label">{label}</div>
    <div className={`font-mono text-lg font-bold mt-0.5 ${valueCl}`}>{value}</div>
    {sub != null && <div className="text-[9px] text-slate-500 mt-0.5">{sub}</div>}
  </div>
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

// ---------------------------------------------------------------------------
// ZONE 1 — P&L by Mode (4 clickable book selectors: the card you click
// drives every figure in the zone below it)
// ---------------------------------------------------------------------------
const MODE_DEFS = [
  { key: 'sim', label: 'Sim', title: 'Simulation' },
  { key: 'paper', label: 'Paper', title: 'Paper' },
  { key: 'uat', label: 'UAT', title: 'UAT' },
  { key: 'live', label: 'Live', title: 'Live' },
];

const ModePanel = ({ label, modeKey, m, fresh, selected, onSelect }) => {
  const isUat = modeKey === 'uat';
  const empty = m == null || (isUat ? !m.fills : (m.closed_trades === 0 && m.open_trades === 0 && m.cum_pnl == null));
  return (
    <div role="button" tabIndex={0} onClick={onSelect}
      onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); onSelect(); } }}
      className={`rounded-lg cursor-pointer transition-shadow ${selected ? 'ring-1 ring-slate-300/50 shadow-[0_0_0_1px_rgba(255,255,255,0.06)]' : 'ring-1 ring-transparent hover:ring-white/[0.15]'}`}
      title={selected ? `${label} book selected — the figures below follow this mode` : `Show the ${label} book below`}>
    <Panel title={label} fresh={fresh} action={
      isUat
        ? <span className="text-[8px] font-bold uppercase tracking-wide text-slate-500" title="gold.paper_uat_fills is a fills ledger — round-trip P&L / win rate stay pending until qr_etl builds the UAT round-trip ledger">fills only</span>
        : m?.win_rate != null
          ? <span className="font-mono text-[10px] text-slate-400" title="Win rate over closed trades">WR {m.win_rate}%</span>
          : null
    }>
      {isUat ? (
        <div className="px-3 pt-2.5 pb-2">
          <div className="flex items-end justify-between">
            <div>
              <div className="font-mono text-[22px] font-black leading-none text-slate-600">—</div>
              <div className="text-[9px] text-slate-500 mt-1">round-trip P&amp;L pending</div>
            </div>
            <div className="text-right">
              <div className="text-[9px] uppercase tracking-wide text-slate-500">Fills today</div>
              <div className="font-mono text-[13px] font-bold text-slate-200">{m?.fills_today ?? 0}</div>
            </div>
          </div>
          <div className="flex items-center gap-3 mt-2 text-[10px] font-mono text-slate-400">
            <span title="Broker-rehearsal fills (gold.paper_uat_fills)">{m?.fills ?? 0} fills</span>
            <span title="Distinct strategies with fills">{m?.strategies_active ?? 0} strateg{(m?.strategies_active ?? 0) === 1 ? 'y' : 'ies'}</span>
            {m?.last_fill_at && <span title={`Last fill ${m.last_fill_at}`}>last {fmtAge(m.last_fill_at)}</span>}
          </div>
          <div className="mt-1.5 h-[36px] flex items-center justify-center text-[9px] text-slate-700">no round-trip history — fills only</div>
        </div>
      ) : (
      <div className="px-3 pt-2.5 pb-2">
        <div className="flex items-end justify-between">
          <div>
            <div className={`font-mono text-[22px] font-black leading-none ${m?.cum_pnl != null ? pnlCl(m.cum_pnl) : 'text-slate-600'}`}>
              {m?.cum_pnl != null ? `${m.cum_pnl >= 0 ? '+' : ''}${fmtK(m.cum_pnl)}` : '—'}
            </div>
            <div className="text-[9px] text-slate-500 mt-1">cumulative realized P&amp;L</div>
          </div>
          <div className="text-right">
            <div className="text-[9px] uppercase tracking-wide text-slate-500">Today</div>
            <div className={`font-mono text-[13px] font-bold ${m?.today ? pnlCl(m.today.pnl) : 'text-slate-600'}`}
              title={m?.today ? `${m.today.trades} closed trade${m.today.trades === 1 ? '' : 's'} today` : 'no exits today'}>
              {m?.today ? `${m.today.pnl >= 0 ? '+' : ''}${fmtK(m.today.pnl)}` : '—'}
            </div>
          </div>
        </div>

        <div className="flex items-center gap-3 mt-2 text-[10px] font-mono text-slate-400">
          <span title="Closed trades (all time)">{m?.closed_trades ?? 0} closed</span>
          <span title="Open positions">{m?.open_trades ?? 0} open</span>
        </div>

        <div className="text-[9px] text-slate-600 mt-2 h-[18px] flex items-center">
          {empty ? 'no trades in this mode yet' : (m?.open_trades ? '' : 'no open positions')}
        </div>

        <div className="mt-1.5">
          <Sparkline data={m?.spark} />
        </div>
      </div>
      )}
    </Panel>
    </div>
  );
};

// ---------------------------------------------------------------------------
// ZONE 3a — Regime Forecast (redesign 2026-09-18).
// Data truth (traced, not assumed):
//   current regime label  — consumption.market_sentiment (canonical, US + HK)
//   probability           — HMM posterior, gold.regime_label (US scope only,
//                           SPY/VIX features; labels in the data: TREND,
//                           MEAN_REV, CARRY, EVENT, FLAT — HK has no posterior)
//   change vs yesterday   — /api/command/regime-change (US HMM daily history;
//                           HK market_sentiment is latest-only → honest note)
//   7-day strip           — consumption.macro_regime_7d, method=momentum_nowcast
//                           (risk-on % per calendar day; HK currently emits a
//                           flat carry-forward — flagged in the cell tooltip)
// Only real labels are rendered; every panel names its model source in a
// tooltip.
// ---------------------------------------------------------------------------
const REGIME_MEANING = {
  TREND: 'Trending tape — momentum and trend-following books should keep working; fade entries get run over.',
  MEAN_REV: 'Mean-reverting tape — moves fade; breakout entries underperform.',
  CARRY: 'Carry / range tape — low-vol grind; income-style books favoured over breakouts.',
  EVENT: 'Event-driven stress — expect gaps and vol spikes; gross exposure earns less.',
  FLAT: 'No dominant regime — weak signal environment; neutral sizing.',
};

const RISK_CELL = (v) => v == null ? 'bg-white/[0.04] text-slate-600'
  : v >= 60 ? 'bg-emerald-500/15 text-emerald-300'
  : v <= 40 ? 'bg-rose-500/15 text-rose-300'
  : 'bg-white/[0.06] text-slate-300';

const fmtConf = (c) => c == null ? '—' : c >= 0.99995 ? '>99.99%' : `${(c * 100).toFixed(1)}%`;

const RegimeRegion = ({ region, fc, chg }) => {
  const days = fc?.days || [];
  const regime = chg?.regime ?? null;
  const allSame = days.length > 1 && days.every(d => d.risk_on === days[0].risk_on);
  // What changed vs yesterday: run length 1 = changed today, 2 = changed
  // yesterday, longer = unchanged. No history → honest note.
  let changeLine = null;
  if (chg) {
    if (!chg.history) {
      changeLine = 'no daily history — latest snapshot only';
    } else if (chg.prev_regime == null) {
      changeLine = `${regime} for ${chg.days_in_regime ?? '—'}+ days (120d window)`;
    } else if (chg.days_in_regime === 1) {
      changeLine = `changed today: ${chg.prev_regime} → ${regime}`;
    } else {
      changeLine = `${chg.prev_regime} → ${regime} on ${chg.changed_on} · ${chg.days_in_regime}d in regime`;
    }
  }
  return (
    <div className="px-3 py-2.5">
      <div className="flex items-baseline justify-between flex-wrap gap-1">
        <span className="flex items-baseline gap-2">
          <span className="font-mono text-[11px] font-black text-white">{region}</span>
          <span className="text-[13px] font-bold text-slate-100" title={chg?.source || ''}>
            {regime ?? '—'}
          </span>
        </span>
        <span className="font-mono text-[10px] text-slate-400"
          title={region === 'US' ? 'HMM posterior probability of the current regime (gold.regime_label)' : 'No regime posterior for HK — the HMM is US-scope (SPY/VIX features)'}>
          P {fmtConf(chg?.confidence)}
        </span>
      </div>
      <div className="text-[10px] text-slate-400 mt-1 leading-snug">
        {regime ? REGIME_MEANING[regime] || 'Regime label without a glossary entry.' : '—'}
      </div>
      <div className="text-[9px] font-mono text-slate-500 mt-1" title={chg?.source || ''}>
        {changeLine ?? '—'}
      </div>
      {days.length > 0 ? (
        <div className="mt-2">
          <div className="grid grid-cols-7 gap-1">
            {days.map((d, i) => (
              <div key={d.date || i}
                className={`rounded px-0.5 py-1 text-center ${RISK_CELL(d.risk_on)}`}
                title={`${d.date ?? ''} · ${d.risk_on != null ? `${d.risk_on.toFixed(1)}%` : '—'} risk-on — momentum_nowcast (consumption.macro_regime_7d)${allSame ? ' · flat carry-forward nowcast' : ''}`}>
                <div className="text-[8px] font-mono opacity-80">
                  {d.date ? new Date(d.date + 'T00:00:00').toLocaleDateString('en-US', { weekday: 'short' }) : '·'}
                </div>
                <div className="text-[8px] font-mono opacity-60">
                  {d.date ? new Date(d.date + 'T00:00:00').toLocaleDateString('en-US', { month: 'numeric', day: 'numeric' }) : ''}
                </div>
                <div className="text-[10px] font-mono font-bold mt-0.5">
                  {d.risk_on != null ? `${d.risk_on.toFixed(0)}%` : '—'}
                </div>
              </div>
            ))}
          </div>
        </div>
      ) : (
        <div className="h-[52px] flex items-center justify-center text-[10px] text-slate-600">no forecast</div>
      )}
    </div>
  );
};

const RegimePanel = ({ fc, chg, fresh }) => (
  <Panel title="Regime Forecast" fresh={fresh} action={
    <span className="text-[9px] text-slate-600"
      title="Current regime: consumption.market_sentiment (canonical) + HMM posterior from gold.regime_label (US, SPY/VIX features). 7-day strip: momentum_nowcast (consumption.macro_regime_7d). Legend: ≥60% risk-on = emerald · ≤40% = rose · else neutral.">
      HMM daily + 7d nowcast · ≥60% on / ≤40% off
    </span>
  }>
    <div className="grid grid-cols-1 sm:grid-cols-2 divide-y sm:divide-y-0 sm:divide-x divide-white/[0.05]">
      <RegimeRegion region="US" fc={fc?.US} chg={chg?.US} />
      <RegimeRegion region="HK" fc={fc?.HK} chg={chg?.HK} />
    </div>
  </Panel>
);

// ---------------------------------------------------------------------------
// ZONE 3b — Top Opportunities (redesign 2026-09-18).
// Score honesty: the displayed score is the signal engine's raw 'potential'
// field (consumption.signal_setups, 0–100). The pipeline publishes NO formula
// or component breakdown for it (the note column is empty engine-side), so the
// UI shows the raw context fields and says what the score is — a heuristic
// ranking — instead of inventing a decomposition.
// Held / pending-order flags are a client-side join against the sim book
// positions (data prop) and the Command order book — no new backend state.
// ---------------------------------------------------------------------------
const MARKET_LABEL = { US: 'US Equity', HK: 'HK Equity', CRYPTO: 'Crypto', FX: 'FX', METAL: 'Metals' };

const SCORE_TIP = 'Engine conviction score (consumption.signal_setups.potential, 0–100). '
  + 'The signal pipeline publishes no formula or component breakdown for this field — '
  + 'treat it as a heuristic ranking, not a decomposable model output.';

const Opportunities = ({ picks, positions, orders, navigateToTab, fresh }) => {
  const [open, setOpen] = useState(null);
  const held = useMemo(() => new Set((positions || []).map(p => p.ticker)), [positions]);
  const pending = useMemo(() => new Set((orders || []).map(o => o.ticker)), [orders]);
  return (
    <Panel title="Top Opportunities" fresh={fresh} action={
      <span className="flex items-center gap-2">
        <span className="text-[9px] text-slate-600" title={SCORE_TIP}>best per class · heuristic score ⓘ</span>
        <LinkBtn onClick={() => navigateToTab('research')}>Signals →</LinkBtn>
      </span>
    }>
      <div className="divide-y divide-white/[0.05]">
        {picks.map((p, i) => {
          const isOpen = open === p.ticker;
          const isHeld = held.has(p.ticker);
          const hasPending = pending.has(p.ticker);
          return (
            <div key={`${p.market}-${p.ticker}`}>
              <button onClick={() => setOpen(isOpen ? null : p.ticker)}
                className="w-full flex items-center gap-3 px-3 py-2.5 hover:bg-white/[0.03] text-left"
                title={isOpen ? 'Collapse detail' : 'Expand score context'}>
                <span className="font-mono text-[10px] text-slate-600 w-4 flex-none">#{i + 1}</span>
                <div className="flex-none w-[110px] min-w-0">
                  <div className="font-mono text-[13px] font-black text-white leading-tight">{p.ticker}</div>
                  <div className="text-[9px] text-slate-500 truncate" title={p.name || ''}>{p.name || MARKET_LABEL[p.market] || p.market}</div>
                </div>
                <div className="flex-none w-[86px]">
                  <div className="flex items-baseline gap-1" title={SCORE_TIP}>
                    <span className="font-mono text-[13px] font-bold text-slate-100">{p.potential != null ? p.potential.toFixed(0) : '—'}</span>
                    <span className="text-[8px] text-slate-500">/ 100</span>
                  </div>
                  <div className="h-1 mt-0.5 rounded bg-white/[0.06] overflow-hidden">
                    <div className="h-full bg-slate-300" style={{ width: `${Math.max(0, Math.min(100, p.potential ?? 0))}%` }} />
                  </div>
                </div>
                <div className="flex-1 min-w-0">
                  <div className="text-[10px] font-bold text-slate-200 truncate">{p.strategyName || '—'}</div>
                  <div className="text-[9px] text-slate-500 truncate">{p.reason}</div>
                </div>
                <span className="flex-none flex items-center gap-1">
                  {isHeld && <span className="qr-chip qr-chip-slate" title="Already held in the sim book">held</span>}
                  {hasPending && <span className="qr-chip qr-chip-slate" title="A working order for this ticker is in the order book">order pending</span>}
                  <span className="text-slate-600 text-[10px]">{isOpen ? '▾' : '▸'}</span>
                </span>
              </button>
              {isOpen && (
                <div className="px-3 pb-2.5 pt-0.5 pl-9">
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-1 rounded overflow-hidden bg-white/[0.05]">
                    {[
                      ['Direction', p.direction || '—'],
                      ['Signal date', p.signalDate ? `${p.signalDate.slice(0, 10)} ${p.signalDate.slice(11, 16)}Z` : '—'],
                      ['Price', p.price != null ? `${fmtK(p.price)}` : '—'],
                      ['1d change', p.changePct != null ? fmtPct(p.changePct) : '—'],
                    ].map(([l, v]) => (
                      <div key={l} className="px-2.5 py-1.5 bg-[#10141f]">
                        <div className="text-[8px] uppercase tracking-wide text-slate-500">{l}</div>
                        <div className="font-mono text-[11px] font-bold text-white mt-0.5 truncate">{v}</div>
                      </div>
                    ))}
                  </div>
                  <div className="text-[9px] text-slate-500 mt-1.5 leading-snug">
                    <span className="font-bold text-slate-400">Score:</span> {SCORE_TIP}
                  </div>
                </div>
              )}
            </div>
          );
        })}
        {picks.length === 0 && (
          <div className="py-6 text-center text-[11px] text-slate-600">No active BUY candidates across asset classes</div>
        )}
      </div>
    </Panel>
  );
};

// ---------------------------------------------------------------------------
// ZONE 4 — Order Book
// ---------------------------------------------------------------------------
const OrderBook = ({ orders, fresh }) => (
  <Panel title="Order Book" fresh={fresh} action={
    <span className="text-[9px] text-slate-600" title="Working orders across live (IBKR) and paper books. Est gain = limit vs latest daily close; blank for market orders.">
      {orders.length} working · est gain = limit vs last close
    </span>
  }>
    {orders.length > 0 ? (
      <table className="w-full">
        <thead>
          <tr className="text-[8px] font-semibold text-slate-500 uppercase tracking-wide">
            <th className="text-left px-3 py-1">Ticker</th>
            <th className="text-left px-2 py-1">Side</th>
            <th className="text-right px-2 py-1">Qty</th>
            <th className="text-right px-2 py-1">Limit</th>
            <th className="text-right px-2 py-1">Last</th>
            <th className="text-right px-2 py-1">Est Gain</th>
            <th className="text-left px-2 py-1">Status</th>
            <th className="text-left px-2 py-1">Book</th>
            <th className="text-right px-3 py-1">Age</th>
          </tr>
        </thead>
        <tbody>
          {orders.map((o, i) => (
            <tr key={`${o.source}-${o.ticker}-${i}`} className="border-t border-white/[0.05] text-[11px]">
              <td className="px-3 py-1.5 font-mono font-bold text-white">{o.ticker}</td>
              <td className={`px-2 py-1.5 font-mono font-bold ${o.side === 'BUY' ? 'text-emerald-400' : o.side === 'SELL' ? 'text-rose-400' : 'text-slate-400'}`}>{o.side ?? '—'}</td>
              <td className="px-2 py-1.5 text-right font-mono text-slate-200">{o.qty != null ? o.qty.toLocaleString() : '—'}</td>
              <td className="px-2 py-1.5 text-right font-mono text-slate-300">{o.limit_price != null ? o.limit_price.toLocaleString() : 'MKT'}</td>
              <td className="px-2 py-1.5 text-right font-mono text-slate-300" title={o.last_price_as_of ? `daily close as of ${o.last_price_as_of}` : 'no daily close for this ticker'}>
                {o.last_price != null ? o.last_price.toLocaleString(undefined, { maximumFractionDigits: 2 }) : '—'}
              </td>
              <td className={`px-2 py-1.5 text-right font-mono font-bold ${o.est_gain != null ? pnlCl(o.est_gain) : 'text-slate-600'}`}>
                {o.est_gain != null ? `${o.est_gain >= 0 ? '+' : ''}${fmtK(o.est_gain)}` : '—'}
              </td>
              <td className="px-2 py-1.5">
                <span className="text-[9px] px-1.5 py-0.5 rounded bg-white/[0.06] text-slate-300">{o.status}</span>
              </td>
              <td className="px-2 py-1.5 text-[10px] text-slate-400 max-w-[160px] truncate" title={o.strategy_name || o.venue}>
                {o.strategy_name || o.venue}
              </td>
              <td className="px-3 py-1.5 text-right font-mono text-[10px] text-slate-500">{o.submitted_at ? fmtAge(o.submitted_at) : '—'}</td>
            </tr>
          ))}
        </tbody>
      </table>
    ) : (
      <div className="py-6 text-center text-[11px] text-slate-600">No working orders</div>
    )}
  </Panel>
);

// ---------------------------------------------------------------------------
// ZONE 1 — Market Status strip (slim, top of page): clocks · indices with
// sparklines · VIX · US + HK Fear & Greed. Breadth detail lives on
// Research ▸ Macro.
// ---------------------------------------------------------------------------
const StripSpark = ({ values }) => {
  if (!values || values.length < 2) return null;
  const min = Math.min(...values), max = Math.max(...values), range = (max - min) || 1;
  const w = 48, h = 14;
  const line = values.map((v, i) => `${((i / (values.length - 1)) * w).toFixed(1)},${(h - 1 - ((v - min) / range) * (h - 2)).toFixed(1)}`).join(' ');
  return (
    <svg viewBox={`0 0 ${w} ${h}`} className="block" style={{ width: w, height: h }}>
      <polyline points={line} fill="none" stroke="rgba(148,163,184,0.8)" strokeWidth="1" vectorEffect="non-scaling-stroke" />
    </svg>
  );
};

const Clocks = () => {
  const [, setTick] = useState(0);
  useEffect(() => {
    const id = setInterval(() => setTick(t => t + 1), 1000);
    return () => clearInterval(id);
  }, []);
  const c = marketClock();
  const s = marketStatus();
  const Clock = ({ label, t, open }) => (
    <span className="flex items-center gap-1" title={open ? 'session open' : 'session closed'}>
      <span className={`w-1.5 h-1.5 rounded-full ${open ? 'bg-emerald-400' : 'bg-slate-600'}`} />
      <span className="text-slate-500">{label}</span>
      <span className="font-mono text-slate-200">{t}</span>
    </span>
  );
  return (
    <span className="flex items-center gap-3 text-[10px] flex-none">
      <Clock label="HKT" t={c.hkt} open={s.hk} />
      <Clock label="LON" t={c.lon} open={s.lon} />
      <Clock label="NYC" t={c.nyc} open={s.nyc} />
    </span>
  );
};

function MarketStrip({ navigateToTab, fresh }) {
  const [ov, setOv] = useState(null);

  const load = async () => {
    const res = await api.get('/api/markets/overview?regions=US,HK');
    if (res) setOv(res);
  };
  useEffect(() => { load(); }, []);
  usePoll(load, 30000);

  const rawIdx = ov?.indices?.data || ov?.indices;
  const indices = Array.isArray(rawIdx) ? rawIdx : [];
  const us = indices.filter(i => i.region === 'US').slice(0, 3);
  const hk = indices.filter(i => i.region === 'HK').slice(0, 2);
  const sentiment = ov?.sentiment || {};
  const usS = sentiment?.us || sentiment;
  const hkS = sentiment?.hk;

  const Divider = () => <span className="w-px self-stretch bg-white/[0.07] flex-none" />;

  return (
    <Panel title="Market Status" fresh={fresh} action={<LinkBtn onClick={() => navigateToTab('research')}>Markets →</LinkBtn>}>
      <div className="flex items-center gap-4 px-3 py-1.5 overflow-x-auto text-[10px]">
        <Clocks />
        <Divider />
        {[...us, ...hk].map(i => (
          <span key={i.sym} className="flex items-center gap-1.5 flex-none" title={i.name}>
            <span className="font-bold text-slate-200">{i.sym}</span>
            <span className="font-mono text-slate-200">{i.last != null ? i.last.toLocaleString(undefined, { maximumFractionDigits: 1 }) : '—'}</span>
            <span className={`font-mono ${pnlCl(i.change_pct ?? i.change_1d)}`}>{fmtPct(i.change_pct ?? i.change_1d)}</span>
            <StripSpark values={i.spark} />
          </span>
        ))}
        <Divider />
        <span className="flex items-center gap-1.5 flex-none" title="CNN Fear & Greed (US)">
          <span className="text-slate-400">US F&amp;G</span>
          <span className="font-mono text-slate-200">{usS?.fear_greed ?? '—'}</span>
          <span className="text-slate-500">{usS?.fear_greed_label || ''}</span>
        </span>
        <span className="flex items-center gap-1.5 flex-none" title="Fear & Greed (HK)">
          <span className="text-slate-400">HK F&amp;G</span>
          <span className="font-mono text-slate-200">{hkS?.fear_greed ?? '—'}</span>
          <span className="text-slate-500">{hkS?.fear_greed_label || ''}</span>
        </span>
        <span className="flex items-center gap-1.5 flex-none" title="CBOE VIX (US)">
          <span className="text-slate-400">VIX</span>
          <span className="font-mono text-slate-200">{usS?.vix ?? '—'}</span>
        </span>
      </div>
    </Panel>
  );
}

// ---------------------------------------------------------------------------
// Command page
// ---------------------------------------------------------------------------
export const CommandCenter = ({ data, navigateToTab, onSelectStrategy }) => {
  const [overview, setOverview] = useState(null);
  const [pnlMode, setPnlMode] = useState(null);
  const [orders, setOrders] = useState(null);
  const [regimeFc, setRegimeFc] = useState(null);
  const [oppPicks, setOppPicks] = useState([]);
  // Selected book (Zone 1 cards drive Zone 2). Default Paper — the book with
  // live signal flow; Live starts empty and Sim is a pure backtest replay.
  const [selMode, setSelMode] = useState('paper');
  // Per-book overview for the selected mode (sim/paper/uat only — the live
  // book reads from overview.account.books.live instead). Tagged with the
  // book it was fetched for so a stale payload never shows under a new mode.
  const [bookOv, setBookOv] = useState(null);
  const registry = useFreshness();
  const [regimeChg, setRegimeChg] = useState(null);

  usePoll(async () => {
    const res = await api.get('/api/command/overview');
    if (res) setOverview(res);
  }, 60000);

  usePoll(async () => {
    const res = await api.get('/api/command/pnl-by-mode');
    if (res) setPnlMode(res);
  }, 60000);

  useEffect(() => {
    if (selMode === 'live') return;
    let cancelled = false;
    api.get(`/api/execution/book-overview?book=${selMode}`).then(res => {
      if (res && !cancelled) setBookOv({ book: selMode, payload: res });
    });
    return () => { cancelled = true; };
  }, [selMode]);
  usePoll(async () => {
    if (selMode === 'live') return;
    const res = await api.get(`/api/execution/book-overview?book=${selMode}`);
    if (res) setBookOv({ book: selMode, payload: res });
  }, 60000);

  usePoll(async () => {
    const res = await api.get('/api/command/order-book');
    if (res) setOrders(res.orders || []);
  }, 60000);

  usePoll(async () => {
    const res = await api.get('/api/command/regime-forecast');
    if (res) setRegimeFc(res.markets || {});
  }, 300000);

  // Change-vs-yesterday per region (read-only addition, 2026-09-18): US from
  // the HMM daily series, HK honestly reports no daily history.
  usePoll(async () => {
    const res = await api.get('/api/command/regime-change');
    if (res) setRegimeChg(res.regions || {});
  }, 300000);

  usePoll(async () => {
    const [u, fams] = await Promise.all([
      api.get('/api/signals/universe?markets=US,HK,CRYPTO,FX,METAL&limit=10'),
      api.get('/api/signals/families'),
    ]);
    if (!u) return;
    const famMap = {};
    for (const f of (fams?.data || [])) famMap[f.key] = f;
    const data = u.data || u;
    const picks = [];
    for (const [mkt, rows] of Object.entries(data)) {
      if (!Array.isArray(rows)) continue;
      const buys = rows.filter(r => r.direction === 'BUY' && !r.exit_to_cash)
        .sort((a, b) => (b.potential ?? -1) - (a.potential ?? -1));
      const top = buys[0];
      if (!top) continue;
      const fam = (top.families || []).map(k => famMap[k]).find(Boolean);
      const note = top.note && top.note !== '—' ? top.note : null;
      picks.push({
        market: mkt,
        ticker: top.ticker,
        name: top.name || null,
        potential: top.potential ?? null,
        direction: top.direction || null,
        price: top.price ?? null,
        changePct: top.change_pct ?? null,
        strategyName: fam?.strategy_name || null,
        reason: note || (fam ? `${fam.label} family signal` : `${MARKET_LABEL[mkt] || mkt} BUY signal`),
      });
    }
    picks.sort((a, b) => (b.potential ?? -1) - (a.potential ?? -1));
    const top3 = picks.slice(0, 3);
    // Signal dates: the universe endpoint does not project updated_at — the
    // read-only /api/command/signal-freshness lookup serves it per ticker.
    const dates = top3.length
      ? await api.get(`/api/command/signal-freshness?tickers=${top3.map(p => encodeURIComponent(p.ticker)).join(',')}`)
      : null;
    const dateMap = dates?.dates || {};
    setOppPicks(top3.map(p => ({ ...p, signalDate: dateMap[p.ticker.toUpperCase()] || null })));
  }, 120000);

  const positions = data?.positions || [];
  // (longMV/shortMV removed t_22dee93d: `positions` is the all-book list —
  // a live-book L/S ratio from it mixed books and currencies.)
  const openPnl = positions.reduce((s, p) => s + (p.unrealized_pnl || p.pnl || 0), 0);

  const account = overview?.account;
  const eqCurve = overview?.equity_curve || [];
  const ret30 = eqCurve.length > 1 ? ((eqCurve[eqCurve.length - 1].equity - eqCurve[0].equity) / eqCurve[0].equity) * 100 : null;

  // The Action Center (alerts, data quality, approvals/gates) moved to
  // Settings ▸ Alerts — components/ActionCenter.jsx. The global header badge
  // in App.jsx surfaces the live alert count.

  // Per-panel freshness from the source→panel dependency map (never tagged
  // by hand — panels inherit the worst state of their upstream sources).
  const fMarket = panelFreshness(PANEL_SOURCES.market, registry);
  const fBook = panelFreshness(PANEL_SOURCES.myBook, registry);
  const fPnlMode = panelFreshness(PANEL_SOURCES.pnlByMode, registry);
  const fOrders = panelFreshness(PANEL_SOURCES.orderBook, registry);
  const fOpps = panelFreshness(PANEL_SOURCES.opportunities, registry);
  const fRegime = panelFreshness(PANEL_SOURCES.regime, registry);

  return (
    <div className="space-y-3">
      <div className="flex items-end justify-between">
        <div>
          <h1 className="text-sm font-bold text-white">Command</h1>
          <p className="text-[10px] text-slate-500">P&amp;L · book · opportunities · orders</p>
        </div>
      </div>

      {/* ZONE 1 — Market Status strip (slim, always first) */}
      <MarketStrip navigateToTab={navigateToTab} fresh={fMarket} />

      {/* ZONE 2 — Environment cards: the most important information on the page.
          Cards are selectors — clicking one re-scopes the book zone below. */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
        {MODE_DEFS.map(md => (
          <ModePanel key={md.key} label={md.label} modeKey={md.key} m={pnlMode?.modes?.[md.key]}
            fresh={fPnlMode} selected={selMode === md.key} onSelect={() => setSelMode(md.key)} />
        ))}
      </div>

      {/* ZONE 3 — selected Book: full-width chart, KPI row under it.
          Every figure follows the card clicked above. */}
      {(() => {
        const modeTitle = MODE_DEFS.find(md => md.key === selMode)?.title || selMode;
        const isLive = selMode === 'live';
        const isUat = selMode === 'uat';
        // Live book: canonical consumption.account_summary row (verbatim),
        // falling back to the combined aggregate when the live row is absent.
        const acctLive = account?.books?.live || account;
        // Currency-labeled live book (t_22dee93d): equity_native = account
        // base currency (HKD), equity_usd = backend-converted via the stored
        // daily rate (fx_date). The frontend never converts — it only renders
        // backend-labeled values; missing labels render unlabeled-marked,
        // never a bare '$'.
        const liveFx = acctLive?.fx || account?.fx;
        const curveCcy = overview?.equity_curve_currency;
        // Sim/Paper/UAT: per-book overview (stats + YTD realized curve).
        const bo = bookOv && bookOv.book === selMode ? bookOv.payload : null;
        const st = bo?.stats;
        const boCurve = (bo?.ytd_curve || []).map(p => ({ d: p.d, equity: p.cum }));
        return (
      <div>
        <div className="flex items-center justify-between mb-1.5">
          <span className="qr-label flex items-center gap-2">{modeTitle} Book <FreshTag fresh={fBook} /></span>
          <LinkBtn onClick={() => navigateToTab('execution')}>Portfolio →</LinkBtn>
        </div>
        <div className="space-y-2">
          {isLive ? (
          <Panel title={`Last 30 Sessions${curveCcy ? ` · ${curveCcy}` : ''}`} fresh={{ ...fBook, lastKnown: acctLive?.equity != null ? fmtKCcy(acctLive.equity, acctLive.currency) : '—' }} action={
            ret30 != null ? <span className={`qr-num text-[11px] font-bold ${pnlCl(ret30)}`}>{fmtPct(ret30)}</span> : null
          }>
            <div className="px-3.5 pt-2.5 pb-1 flex items-end justify-between">
              <div>
                <div className="font-mono text-2xl font-black text-white leading-none">{acctLive?.equity_native != null ? fmtKCcy(acctLive.equity_native, acctLive.native_currency) : acctLive?.equity != null ? fmtKCcy(acctLive.equity, acctLive.currency) : '—'}</div>
                {acctLive?.equity_usd != null && (
                  <div className="text-[9px] text-slate-500 mt-0.5">≈ {fmtKCcy(acctLive.equity_usd, 'USD')}{liveFx?.base_per_usd ? ` @ ${Number(liveFx.base_per_usd).toFixed(4)} ${liveFx.base_currency}/USD` : ''}{liveFx?.fx_date ? ` · rate ${liveFx.fx_date}` : ''}</div>
                )}
                <div className="text-[10px] text-slate-500 mt-1">{acctLive?.positions ?? positions.length} open positions{acctLive?.cash_pct != null ? ` · ${Math.round(acctLive.cash_pct)}% cash` : ''}</div>
              </div>
              <div className="text-right">
                <div className="text-[9px] uppercase tracking-wide text-slate-500">Day P&L</div>
                <div className="flex items-baseline gap-1.5 justify-end">
                  <span className={`font-mono text-[17px] font-black ${pnlCl(acctLive?.day_pnl)}`}>{acctLive?.day_pnl != null ? fmtK(acctLive.day_pnl) : '—'}</span>
                  {/* bps, not %: 1dp percent is below the resolution of a multi-$M book */}
                  {acctLive?.day_pnl != null && acctLive?.equity ? (
                    <span className={`font-mono text-[11px] ${pnlCl(acctLive.day_pnl)}`} title="Day P&L as basis points of equity">
                      {(acctLive.day_pnl / acctLive.equity * 1e4) >= 0 ? '+' : ''}{(acctLive.day_pnl / acctLive.equity * 1e4).toFixed(1)} bps
                    </span>
                  ) : null}
                </div>
              </div>
            </div>
            <EquityCurve data={eqCurve} color="#60a5fa" />
          </Panel>
          ) : (
          <Panel title={isUat ? 'UAT Fills' : 'Cumulative Realized · YTD'} fresh={fBook} action={
            !isUat && st?.win_rate != null
              ? <span className="font-mono text-[10px] text-slate-400" title="Win rate over closed trades">WR {st.win_rate}%</span>
              : null
          }>
            <div className="px-3.5 pt-2.5 pb-1 flex items-end justify-between">
              <div>
                {isUat ? (
                  <>
                    <div className="font-mono text-2xl font-black text-slate-600 leading-none">—</div>
                    <div className="text-[10px] text-slate-500 mt-1"
                      title="gold.paper_uat_fills is a fills ledger, not round-trips — a per-strategy UAT P&L ledger is qr_etl's domain">
                      fills-only ledger · round-trip P&amp;L pending
                    </div>
                  </>
                ) : (
                  <>
                    <div className={`font-mono text-2xl font-black leading-none ${st?.ytd_pnl != null ? pnlCl(st.ytd_pnl) : 'text-slate-600'}`}>
                      {st?.ytd_pnl != null ? `${st.ytd_pnl >= 0 ? '+' : ''}${fmtK(st.ytd_pnl)}` : '—'}
                    </div>
                    <div className="text-[10px] text-slate-500 mt-1">
                      YTD realized{st?.cum_pnl != null ? ` · all-time ${st.cum_pnl >= 0 ? '+' : ''}${fmtK(st.cum_pnl)}` : ''}
                    </div>
                  </>
                )}
              </div>
              <div className="text-right">
                <div className="text-[9px] uppercase tracking-wide text-slate-500">Today</div>
                {isUat ? (
                  <div className="font-mono text-[17px] font-black text-slate-200" title="Fills today">{st?.today?.trades ?? 0} fills</div>
                ) : (
                  <div className={`font-mono text-[17px] font-black ${st?.today ? pnlCl(st.today.pnl) : 'text-slate-600'}`}
                    title={st?.today ? `${st.today.trades} closed trade${st.today.trades === 1 ? '' : 's'} today` : 'no exits today'}>
                    {st?.today ? `${st.today.pnl >= 0 ? '+' : ''}${fmtK(st.today.pnl)}` : '—'}
                  </div>
                )}
              </div>
            </div>
            <EquityCurve data={boCurve} color="#60a5fa"
              emptyLabel={isUat ? 'no round-trip history — fills only' : bo == null ? 'Loading book…' : 'No realized P&L this year'} />
          </Panel>
          )}

          {isLive ? (
          /* KPI row under the chart: Open P&L · Net Cash Flow · Buying Power · Net Exposure */
          <FreshWrap fresh={fBook} lastKnown={acctLive?.open_pnl != null ? fmtK(acctLive.open_pnl) : fmtK(openPnl)} className="grid grid-cols-2 sm:grid-cols-4 gap-2">
            <div className="qr-surface p-2.5 flex flex-col justify-center">
              <div className="qr-label">Open P&amp;L{acctLive?.open_pnl_currency ? ` · ${acctLive.open_pnl_currency}` : ''}</div>
              <div className={`font-mono text-lg font-bold mt-0.5 ${pnlCl(acctLive?.open_pnl ?? openPnl)}`}>
                {acctLive?.open_pnl != null ? fmtKCcy(acctLive.open_pnl, acctLive.open_pnl_currency || acctLive.currency) : fmtKCcy(openPnl, 'USD')}
              </div>
              {acctLive?.open_pnl_pct_of_equity != null ? (
                <div className="text-[9px] text-slate-500 mt-0.5" title="Open P&L (USD, position-derived) ÷ USD equity — same-unit ratio">{fmtPct(acctLive.open_pnl_pct_of_equity)} of equity</div>
              ) : null}
            </div>

            {/* Net Cash Flow (t_98afd0f5): overview.cash_flow from
                consumption.account_cash_flow_summary. NULL = no data → '—',
                never a coerced 0. Paper book is wired (t_b662b4e9); the live
                book has NO cash-flow source yet (IBKR cash transactions not
                ingested) → distinct 'no live source' treatment. */}
            {(() => {
              const cfL = overview?.cash_flow?.live;
              const liveHasSource = !!(cfL && (cfL.mtd_net != null || cfL.net_all_time != null || cfL.last_flow_date != null));
              const tip = 'Net cash flow (deposits − withdrawals), consumption.account_cash_flow_summary — live book.'
                + (liveHasSource
                    ? ` MTD ${cfL.mtd_net != null ? fmtK(cfL.mtd_net) : '—'} (${cfL.flows_mtd_count} flows, last ${cfL.last_flow_date ?? '—'}).`
                    : ' No cash-flow source yet (IBKR cash transactions not yet ingested).');
              return (
                <div className="qr-surface p-2.5 flex flex-col justify-center" title={tip}>
                  <div className="qr-label flex items-center gap-1.5">Net Cash Flow
                    <span className="text-[8px] uppercase tracking-wide text-slate-500">mtd</span>
                  </div>
                  <div className={`font-mono text-lg font-bold mt-0.5 ${cfL?.mtd_net != null ? pnlCl(cfL.mtd_net) : 'text-slate-600'}`}>
                    {cfL?.mtd_net != null ? `${cfL.mtd_net >= 0 ? '+' : ''}${fmtK(cfL.mtd_net)}` : '—'}
                  </div>
                  <div className="text-[9px] text-slate-500 mt-0.5">
                    today {cfL?.today_net != null ? `${cfL.today_net >= 0 ? '+' : ''}${fmtK(cfL.today_net)}` : '—'}
                    {cfL?.flows_mtd_count ? ` · ${cfL.flows_mtd_count} flows` : ''}
                  </div>
                  {!liveHasSource && (
                    <div className="text-[8px] text-slate-600 mt-0.5">live book: no source</div>
                  )}
                </div>
              );
            })()}

            <div className="qr-surface p-2.5 flex flex-col justify-center">
              <div className="qr-label">Buying Power{acctLive?.currency ? ` · ${acctLive.currency}` : ''}</div>
              <div className="font-mono text-lg font-bold mt-0.5 text-white">
                {acctLive?.buying_power != null ? fmtKCcy(acctLive.buying_power, acctLive.currency) : '—'}
              </div>
              {acctLive?.buying_power_usd != null && acctLive?.currency !== 'USD' && (
                <div className="text-[9px] text-slate-500 mt-0.5">≈ {fmtKCcy(acctLive.buying_power_usd, 'USD')}{liveFx?.fx_date ? ` · rate ${liveFx.fx_date}` : ''}</div>
              )}
              {acctLive?.cash_pct != null && (
                <div className="text-[9px] text-slate-500 mt-0.5">{Number(acctLive.cash_pct).toFixed(1)}% cash</div>
              )}
            </div>

            <div className="qr-surface p-2.5 flex flex-col justify-center"
              title={`Canonical per-book exposures (consumption.account_summary, live book only) · gross ${acctLive?.gross_exp_pct != null ? acctLive.gross_exp_pct.toFixed(1) : '—'}%`}>
              <div className="qr-label">Net Exposure</div>
              <div className={`font-mono text-lg font-bold mt-0.5 ${acctLive?.net_exp_pct != null ? pnlCl(acctLive.net_exp_pct) : 'text-slate-600'}`}>
                {acctLive?.net_exp_pct != null ? `${acctLive.net_exp_pct >= 0 ? '+' : ''}${acctLive.net_exp_pct.toFixed(1)}%` : '—'}
              </div>
              {/* No L/S split here: the positions prop is the ALL-book list
                  (77 paper + 7 live), so a client-side long/short ÷ live
                  equity mixes books AND currencies — the old '88%' was an
                  accident of the combined-equity denominator (t_22dee93d). */}
              <div className="text-[9px] text-slate-500 mt-0.5">
                gross {acctLive?.gross_exp_pct != null ? `${acctLive.gross_exp_pct.toFixed(1)}%` : '—'} · live book only
              </div>
            </div>
          </FreshWrap>
          ) : isUat ? (
          <FreshWrap fresh={fBook} className="grid grid-cols-2 sm:grid-cols-4 gap-2">
            <KpiTile label="Total Fills" value={st?.total_fills ?? '—'} sub={`${st?.ytd_trades ?? 0} this year`}
              tip="Broker-rehearsal fills (gold.paper_uat_fills) — fills, not round-trips" />
            <KpiTile label="Fills Today" value={st?.today?.trades ?? 0} />
            <KpiTile label="Last Fill" value={st?.last_fill_at ? fmtAge(st.last_fill_at) : '—'} sub={st?.last_fill_at || undefined} />
            <KpiTile label="Round-Trip P&L" value="—" valueCl="text-slate-600" sub="ledger pending"
              tip="A per-strategy UAT round-trip P&L ledger is qr_etl's domain — never derived serve-time" />
          </FreshWrap>
          ) : (
          <FreshWrap fresh={fBook} lastKnown={st?.cum_pnl != null ? fmtK(st.cum_pnl) : '—'} className="grid grid-cols-2 sm:grid-cols-4 gap-2">
            <KpiTile label="Win Rate" value={st?.win_rate != null ? `${st.win_rate}%` : '—'}
              valueCl={st?.win_rate != null ? 'text-white' : 'text-slate-600'}
              sub={`${st?.closed_trades ?? 0} closed all-time`} tip="Wins / closed trades" />
            <KpiTile label="Open Positions" value={st?.open_trades ?? '—'} sub="actively monitored" />
            <KpiTile label="Today" value={st?.today ? `${st.today.pnl >= 0 ? '+' : ''}${fmtK(st.today.pnl)}` : '—'}
              valueCl={st?.today ? pnlCl(st.today.pnl) : 'text-slate-600'}
              sub={st?.today ? `${st.today.trades} exits` : 'no exits today'} />
            <KpiTile label="Cum P&L" value={st?.cum_pnl != null ? `${st.cum_pnl >= 0 ? '+' : ''}${fmtK(st.cum_pnl)}` : '—'}
              valueCl={st?.cum_pnl != null ? pnlCl(st.cum_pnl) : 'text-slate-600'} sub="all-time realized" />
          </FreshWrap>
          )}
        </div>
      </div>
        );
      })()}

      {/* ZONE 4 — Regime Forecast + Top Opportunities, side by side */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-3">
        <RegimePanel fc={regimeFc} chg={regimeChg} fresh={fRegime} />
        <Opportunities picks={oppPicks} positions={positions} orders={orders || []} navigateToTab={navigateToTab} fresh={fOpps} />
      </div>

      {/* ZONE 5 — Order Book */}
      <OrderBook orders={orders || []} fresh={fOrders} />

    </div>
  );
};

export default CommandCenter;
