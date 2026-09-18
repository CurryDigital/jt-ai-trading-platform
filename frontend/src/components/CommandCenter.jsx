import React, { useMemo, useState, useEffect } from 'react';
import { api, usePoll, fmtK, fmtPct, fmtAge, pnlCl, marketClock, marketStatus } from '../utils';
import { FR, FR_NAME, PANEL_SOURCES, panelFreshness, useFreshness, fmtAgeSec, useBarQuality, barQualityView } from '../freshness';

// Command home — 2026-08-20 redesign. Priority: what am I making/losing,
// where's my cash, what's working, what to buy next.
//   1) P&L by Mode (hero; 4 clickable book selectors SIM/PAPER/UAT/LIVE)
//   2) Selected Book (per-mode stats + curve, follows the card clicked above)
//   3) Regime Forecast + Top Opportunities
//   4) Order Book                  5) Market Status (compact strip)
//   6) Action Center (attention queue)
// Cut vs. previous layout: Strategy Pipeline funnel + Deployed Health table
// (redundant with P&L by Mode; they live on the Strategies tab), the monthly
// P&L panel, and the paper-book-by-asset strip. 2026-09-18: strategy-name
// chips removed from the mode cards (front-page clutter).

// Restrained palette: colour carries meaning only.
//   rose  = critical severity   emerald/rose text = signed P&L (via pnlCl)
//   blue  = interactive links   everything else = neutral slate/white
const SEV_STYLE = {
  critical: { border: 'border-l-rose-500', bg: 'bg-rose-500/[0.06]', tag: 'text-rose-300 bg-rose-500/15' },
  warning:  { border: 'border-l-slate-500', bg: '', tag: 'text-slate-300 bg-white/[0.07]' },
  info:     { border: 'border-l-slate-700', bg: '', tag: 'text-slate-400 bg-white/[0.05]' },
};
const SEV_RANK = { critical: 0, warning: 1, info: 2 };

function EquityCurve({ data, color, emptyLabel = 'No equity history yet' }) {
  if (!data || data.length < 2) {
    return <div className="h-32 flex items-center justify-center text-[11px] text-slate-600">{emptyLabel}</div>;
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
// ZONE 3a — Regime Forecast (7-day risk-on bars per market)
// ---------------------------------------------------------------------------
const REGIME_LABEL_CL = { 'Risk-On': 'text-emerald-400', 'Risk-Off': 'text-rose-400', Neutral: 'text-slate-300' };

const RegimeBars = ({ region, fc }) => {
  const days = fc?.days || [];
  return (
    <div className="px-3 py-2.5">
      <div className="flex items-baseline justify-between mb-1.5">
        <span className="flex items-center gap-2">
          <span className="font-mono text-[11px] font-black text-white">{region}</span>
          <span className={`text-[10px] font-bold ${REGIME_LABEL_CL[fc?.label] || 'text-slate-500'}`}>{fc?.label ?? '—'}</span>
        </span>
        <span className="font-mono text-[10px] text-slate-400" title="Latest 7-day risk-on probability (momentum_nowcast)">
          {fc?.latest != null ? `${fc.latest.toFixed(0)}% risk-on` : '—'}
        </span>
      </div>
      {days.length > 0 ? (
        <div className="relative">
          {/* neutral 50% gridline */}
          <div className="absolute left-0 right-0 border-t border-dashed border-white/[0.15]" style={{ bottom: '50%' }} />
          <div className="flex items-end gap-1 h-[64px]">
            {days.map((d, i) => (
              <div key={d.date || i} className="flex-1 flex flex-col items-center justify-end h-full" title={`${d.date ?? ''} · ${d.risk_on != null ? `${d.risk_on.toFixed(1)}%` : '—'} risk-on`}>
                <div className={`w-full rounded-sm ${i === 0 ? 'bg-slate-200' : 'bg-slate-600'}`}
                  style={{ height: `${Math.max(2, Math.min(100, d.risk_on ?? 0))}%` }} />
              </div>
            ))}
          </div>
          <div className="flex gap-1 mt-1">
            {days.map((d, i) => (
              <div key={d.date || i} className="flex-1 text-center text-[8px] font-mono text-slate-500">
                {d.date ? new Date(d.date + 'T00:00:00').toLocaleDateString('en-US', { weekday: 'narrow' }) : '·'}
              </div>
            ))}
          </div>
        </div>
      ) : (
        <div className="h-[64px] flex items-center justify-center text-[10px] text-slate-600">no forecast</div>
      )}
    </div>
  );
};

// ---------------------------------------------------------------------------
// ZONE 3b — Top Opportunities
// ---------------------------------------------------------------------------
const MARKET_LABEL = { US: 'US Equity', HK: 'HK Equity', CRYPTO: 'Crypto', FX: 'FX', METAL: 'Metals' };

const Opportunities = ({ picks, navigateToTab, fresh }) => (
  <Panel title="Top Opportunities" fresh={fresh} action={
    <span className="flex items-center gap-2">
      <span className="text-[9px] text-slate-600" title="Best BUY candidate per asset class, ranked by conviction score (consumption.signal_setups)">best per class</span>
      <LinkBtn onClick={() => navigateToTab('research')}>Signals →</LinkBtn>
    </span>
  }>
    <div className="divide-y divide-white/[0.05]">
      {picks.map((p, i) => (
        <button key={`${p.market}-${p.ticker}`} onClick={() => navigateToTab('execution')}
          className="w-full flex items-center gap-3 px-3 py-2.5 hover:bg-white/[0.03] text-left"
          title="Jump to Execution">
          <span className="font-mono text-[10px] text-slate-600 w-4 flex-none">#{i + 1}</span>
          <div className="flex-none w-[92px]">
            <div className="font-mono text-[13px] font-black text-white leading-tight">{p.ticker}</div>
            <div className="text-[9px] text-slate-500">{MARKET_LABEL[p.market] || p.market}</div>
          </div>
          <div className="flex-none w-[86px]">
            <div className="flex items-baseline gap-1">
              <span className="font-mono text-[13px] font-bold text-slate-100">{p.potential != null ? p.potential.toFixed(0) : '—'}</span>
              <span className="text-[8px] text-slate-500">/ 100</span>
            </div>
            <div className="h-1 mt-0.5 rounded bg-white/[0.06] overflow-hidden" title="Conviction score (signal_setups.potential)">
              <div className="h-full bg-slate-300" style={{ width: `${Math.max(0, Math.min(100, p.potential ?? 0))}%` }} />
            </div>
          </div>
          <div className="flex-1 min-w-0">
            <div className="text-[10px] font-bold text-slate-200 truncate">{p.strategyName || '—'}</div>
            <div className="text-[9px] text-slate-500 truncate">{p.reason}</div>
          </div>
          <span className="text-slate-600 flex-none text-[10px]">→</span>
        </button>
      ))}
      {picks.length === 0 && (
        <div className="py-6 text-center text-[11px] text-slate-600">No active BUY candidates across asset classes</div>
      )}
    </div>
  </Panel>
);

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
// ZONE 5 — Market Status (compact strip; visually quieter than the zones above)
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
  const breadth = ov?.breadth || {};
  const sentiment = ov?.sentiment || {};
  const usS = sentiment?.us || sentiment;
  const hkS = sentiment?.hk;

  const BreadthMini = ({ label, bd }) => {
    const total = bd ? (bd.advancing || 0) + (bd.declining || 0) + (bd.unchanged || 0) : 0;
    return (
      <span className="flex items-center gap-1.5" title={`${label} breadth: ${bd ? `${bd.advancing || 0} adv / ${bd.declining || 0} dec / ${bd.unchanged || 0} unch` : 'no data'}`}>
        <span className="text-slate-500">{label}</span>
        <span className="flex h-1.5 w-16 rounded overflow-hidden bg-white/5">
          {total > 0 ? (
            <>
              <span className="bg-emerald-500/70" style={{ width: `${(bd.advancing / total) * 100}%` }} />
              <span className="bg-slate-600" style={{ width: `${(bd.unchanged / total) * 100}%` }} />
              <span className="bg-rose-500/70" style={{ width: `${(bd.declining / total) * 100}%` }} />
            </>
          ) : <span className="w-full bg-slate-800" />}
        </span>
        <span className="font-mono text-slate-400">{bd ? `${bd.advancing || 0}/${bd.declining || 0}` : '—'}</span>
      </span>
    );
  };

  const Divider = () => <span className="w-px self-stretch bg-white/[0.07] flex-none" />;

  return (
    <Panel title="Market Status" fresh={fresh} action={<LinkBtn onClick={() => navigateToTab('research')}>Markets →</LinkBtn>}>
      <div className="flex items-center gap-4 px-3 py-2 overflow-x-auto text-[10px]">
        <Clocks />
        <Divider />
        {[...us, ...hk].map(i => (
          <span key={i.sym} className="flex items-center gap-1.5 flex-none" title={i.name}>
            <span className="font-bold text-slate-200">{i.sym}</span>
            <span className="font-mono text-slate-300">{i.last != null ? i.last.toLocaleString(undefined, { maximumFractionDigits: 1 }) : '—'}</span>
            <span className={`font-mono ${pnlCl(i.change_pct ?? i.change_1d)}`}>{fmtPct(i.change_pct ?? i.change_1d)}</span>
            <StripSpark values={i.spark} />
          </span>
        ))}
        <Divider />
        <BreadthMini label="US" bd={breadth.us} />
        <BreadthMini label="HK" bd={breadth.hk} />
        <Divider />
        <span className="flex items-center gap-1.5 flex-none" title="CNN Fear & Greed (US)">
          <span className="text-slate-500">F&amp;G</span>
          <span className="font-mono text-slate-200">{usS?.fear_greed ?? '—'}</span>
          <span className="text-slate-500">{usS?.fear_greed_label || ''}</span>
        </span>
        <span className="flex items-center gap-1.5 flex-none" title="CBOE VIX (US)">
          <span className="text-slate-500">VIX</span>
          <span className="font-mono text-slate-200">{usS?.vix ?? '—'}</span>
        </span>
        {hkS?.fear_greed != null && (
          <span className="flex items-center gap-1.5 flex-none" title="Fear & Greed (HK)">
            <span className="text-slate-500">HK F&amp;G</span>
            <span className="font-mono text-slate-200">{hkS.fear_greed}</span>
          </span>
        )}
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
  const barQ = useBarQuality();
  const bqView = barQualityView(barQ.loaded, barQ.bq);

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
        potential: top.potential ?? null,
        strategyName: fam?.strategy_name || null,
        reason: note || (fam ? `${fam.label} family signal` : `${MARKET_LABEL[mkt] || mkt} BUY signal`),
      });
    }
    picks.sort((a, b) => (b.potential ?? -1) - (a.potential ?? -1));
    setOppPicks(picks.slice(0, 3));
  }, 120000);

  const positions = data?.positions || [];
  const longMV = positions.filter(p => p.side === 'LONG').reduce((s, p) => s + (p.market_value || 0), 0);
  const shortMV = positions.filter(p => p.side === 'SHORT').reduce((s, p) => s + (p.market_value || 0), 0);
  const openPnl = positions.reduce((s, p) => s + (p.unrealized_pnl || p.pnl || 0), 0);

  const account = overview?.account;
  const eqCurve = overview?.equity_curve || [];
  const ret30 = eqCurve.length > 1 ? ((eqCurve[eqCurve.length - 1].equity - eqCurve[0].equity) / eqCurve[0].equity) * 100 : null;

  const strategyRisks = useMemo(() => overview?.strategy_risks || [], [overview]);
  const monitoringGap = overview?.monitoring_gap || 0;

  // Merged attention queue: strategy risks + monitoring gap + platform items
  // in ONE panel, sorted by severity then recency. Every item carries a
  // stable ackKey for server-side ack/snooze, a real action verb, and a
  // dedup class so same-class rows collapse to one.
  const attentionItems = useMemo(() => {
    const items = [];
    for (const s of strategyRisks) items.push({
      kind: 'risk', sev: s.sev, tag: 'RISK', title: s.name,
      triggers: s.triggers || null,
      fullMetrics: `PF ${s.paper_pf != null ? s.paper_pf.toFixed(2) : '—'} · P&L ${s.paper_pnl >= 0 ? '+' : ''}${fmtK(s.paper_pnl)} · WR ${s.paper_wr}% · ${s.closed_trades} closed`,
      impact: `PF ${s.paper_pf != null ? s.paper_pf.toFixed(2) : '—'} · P&L ${s.paper_pnl >= 0 ? '+' : ''}${fmtK(s.paper_pnl)} · WR ${s.paper_wr}% · ${s.closed_trades} closed`,
      ts: null, age: null, strategyId: s.strategy_id, action: 'open',
      key: `risk-${s.strategy_id}`, ackKey: `risk:${s.strategy_id}`,
    });
    if (monitoringGap > 0) items.push({
      kind: 'gap', sev: 'info', tag: 'GAPS',
      title: `${monitoringGap} paper strateg${monitoringGap === 1 ? 'y' : 'ies'} not actively monitored`,
      impact: 'Registry says PAPER but no ACTIVE paper deployment — no live signal tracking running.',
      ts: null, age: null, target: 'strategies', action: 'open', key: 'gap', ackKey: 'gap:monitoring',
    });
    for (const a of (overview?.attention || [])) {
      const raw = a.created_at;
      const ts = raw ? new Date(/Z|[+-]\d{2}:?\d{2}$/.test(raw) ? raw : raw + 'Z').getTime() : null;
      items.push({
        kind: 'platform', sev: a.sev, tag: a.tag, title: a.title, impact: a.impact,
        ts, age: a.age || fmtAge(a.created_at), target: a.target,
        action: a.action || 'open', refId: a.ref_id,
        key: `plat-${a.id || a.ref_id || a.title}`, ackKey: a.id ? String(a.id) : null,
      });
    }
    // Yahoo suspect-bar guard (bar_quality, t_285be732): YELLOW is a SOFT
    // warning — never critical, episodes can self-heal as Yahoo backfills
    // real bars. Client-side item (no ackKey → not dismissible; it clears
    // itself when the 30d window heals). UNKNOWN/null is NOT surfaced here —
    // the Settings badge carries that state; the queue stays for real signal.
    if (bqView.level === 'YELLOW') {
      const bq = barQ.bq || {};
      const tickers = bq.recent_30d_tickers || [];
      items.push({
        kind: 'platform', sev: 'warning', tag: 'DATA',
        title: `Yahoo suspect bars — ${tickers.join(', ') || 'unknown tickers'}`,
        impact: `${bq.recent_30d_rows ?? 0} unresolved synthetic zero-volume flat-bar suspects in 30d (latest ${bq.latest_suspect_date ?? '—'}): ${bq.recent_30d_gold_rows ?? 0} pre-guard gold rows + ${bq.recent_30d_quarantined_rows ?? 0} quarantined post-guard. Soft warning — can self-heal as Yahoo backfills. Source: gold.v_us_equity_bar_quality (qr_etl).`,
        ts: null, age: null, target: 'settings', action: 'open',
        key: 'bar-quality', ackKey: null,
      });
    }
    items.sort((x, y) => (SEV_RANK[x.sev] ?? 9) - (SEV_RANK[y.sev] ?? 9) || (y.ts ?? -1) - (x.ts ?? -1));
    return items;
  }, [overview, strategyRisks, monitoringGap, bqView.level, barQ.bq]);

  // Server-side dismissals filter the payload already; this set is the
  // optimistic local removal after the user acks/snoozes in THIS session.
  const [dismissed, setDismissed] = useState(() => new Set());
  const [actBusy, setActBusy] = useState(null);   // ackKey currently executing
  const [actMsg, setActMsg] = useState(null);     // {ackKey, ok, text}
  const visibleItems = useMemo(
    () => attentionItems.filter(a => !a.ackKey || !dismissed.has(a.ackKey)),
    [attentionItems, dismissed],
  );

  // Dedup by class: '<source> feed is stale' rows collapse into one group row
  // with a disclosure triangle; other classes stay individual.
  const alertClass = (a) =>
    (a.kind === 'platform' && / feed is stale$/i.test(a.title)) ? 'feed-stale' : `solo:${a.key}`;
  const attentionGroups = useMemo(() => {
    const order = [], byClass = new Map();
    for (const a of visibleItems) {
      const k = alertClass(a);
      if (!byClass.has(k)) { byClass.set(k, []); order.push(k); }
      byClass.get(k).push(a);
    }
    return order.map(k => byClass.get(k));
  }, [visibleItems]);
  const [openGroups, setOpenGroups] = useState(() => new Set());
  const toggleGroup = (k) => setOpenGroups(prev => {
    const n = new Set(prev);
    n.has(k) ? n.delete(k) : n.add(k);
    return n;
  });

  const dismissAlert = async (targets, action) => {
    const keys = targets.map(a => a.ackKey).filter(Boolean);
    if (!keys.length) return;
    for (const k of keys) {
      await api.post('/api/command/alerts/ack', { alert_key: k, action, snooze_minutes: 60 });
    }
    setDismissed(prev => new Set([...prev, ...keys]));
  };

  const ACT_LABEL = { reconnect: 'Reconnect', flatten: 'Flatten', open: 'Open' };
  const runAction = async (a) => {
    if (a.action === 'reconnect') {
      setActBusy(a.ackKey || a.key);
      const res = await api.post('/api/ib/tws/connect', {});
      setActBusy(null);
      setActMsg({ key: a.ackKey || a.key, ok: !!(res && res.success !== false), text: res && (res.message || res.status) ? String(res.message || res.status) : (res ? 'connect requested' : 'request failed') });
      return;
    }
    if (a.strategyId) onSelectStrategy?.(a.strategyId);
    else navigateToTab(a.target || 'command');
  };

  const sevCounts = visibleItems.reduce((m, a) => ({ ...m, [a.sev]: (m[a.sev] || 0) + 1 }), {});

  // Per-panel freshness from the source→panel dependency map (never tagged
  // by hand — panels inherit the worst state of their upstream sources).
  const fMarket = panelFreshness(PANEL_SOURCES.market, registry);
  const fBook = panelFreshness(PANEL_SOURCES.myBook, registry);
  const fPnlMode = panelFreshness(PANEL_SOURCES.pnlByMode, registry);
  const fOrders = panelFreshness(PANEL_SOURCES.orderBook, registry);
  const fOpps = panelFreshness(PANEL_SOURCES.opportunities, registry);
  const fAttention = panelFreshness(PANEL_SOURCES.attention, registry);
  const fRegime = panelFreshness(PANEL_SOURCES.regime, registry);

  return (
    <div className="space-y-3">
      <div className="flex items-end justify-between">
        <div>
          <h1 className="text-sm font-bold text-white">Command</h1>
          <p className="text-[10px] text-slate-500">P&amp;L · book · opportunities · orders</p>
        </div>
      </div>

      {/* ZONE 1 — P&L by Mode: the most important information on the page.
          Cards are selectors — clicking one re-scopes the book zone below. */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
        {MODE_DEFS.map(md => (
          <ModePanel key={md.key} label={md.label} modeKey={md.key} m={pnlMode?.modes?.[md.key]}
            fresh={fPnlMode} selected={selMode === md.key} onSelect={() => setSelMode(md.key)} />
        ))}
      </div>

      {/* ZONE 2 — selected Book: every figure follows the card clicked above */}
      {(() => {
        const modeTitle = MODE_DEFS.find(md => md.key === selMode)?.title || selMode;
        const isLive = selMode === 'live';
        const isUat = selMode === 'uat';
        // Live book: canonical consumption.account_summary row (verbatim),
        // falling back to the combined aggregate when the live row is absent.
        const acctLive = account?.books?.live || account;
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
        <div className="grid grid-cols-1 lg:grid-cols-[1.55fr_1fr] gap-3">
          {isLive ? (
          <Panel title="Last 30 Sessions" fresh={{ ...fBook, lastKnown: acctLive?.equity != null ? fmtK(acctLive.equity) : '—' }} action={
            ret30 != null ? <span className={`qr-num text-[11px] font-bold ${pnlCl(ret30)}`}>{fmtPct(ret30)}</span> : null
          }>
            <div className="px-3.5 pt-2.5 pb-1 flex items-end justify-between">
              <div>
                <div className="font-mono text-2xl font-black text-white leading-none">{acctLive?.equity != null ? fmtK(acctLive.equity) : '—'}</div>
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
          /* 2x2 KPI grid: Open P&L · Net Cash Flow · Buying Power · Net Exposure */
          <FreshWrap fresh={fBook} lastKnown={acctLive?.open_pnl != null ? fmtK(acctLive.open_pnl) : fmtK(openPnl)} className="grid grid-cols-2 gap-2">
            <div className="qr-surface p-2.5 flex flex-col justify-center">
              <div className="qr-label">Open P&amp;L</div>
              <div className={`font-mono text-lg font-bold mt-0.5 ${pnlCl(acctLive?.open_pnl ?? openPnl)}`}>
                {acctLive?.open_pnl != null ? fmtK(acctLive.open_pnl) : fmtK(openPnl)}
              </div>
              {acctLive?.equity ? (
                <div className="text-[9px] text-slate-500 mt-0.5">{fmtPct(((acctLive.open_pnl ?? openPnl) / acctLive.equity) * 100)}</div>
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
              <div className="qr-label">Buying Power</div>
              <div className="font-mono text-lg font-bold mt-0.5 text-white">
                {acctLive?.buying_power != null ? fmtK(acctLive.buying_power) : '—'}
              </div>
              {acctLive?.cash_pct != null && (
                <div className="text-[9px] text-slate-500 mt-0.5">{Number(acctLive.cash_pct).toFixed(1)}% cash</div>
              )}
            </div>

            <div className="qr-surface p-2.5 flex flex-col justify-center"
              title={`Long ${acctLive?.equity ? ((longMV / acctLive.equity) * 100).toFixed(1) : '—'}% vs short ${acctLive?.equity ? ((shortMV / acctLive.equity) * 100).toFixed(1) : '—'}% of equity · gross ${acctLive?.gross_exp_pct != null ? acctLive.gross_exp_pct.toFixed(1) : '—'}%`}>
              <div className="qr-label">Net Exposure</div>
              <div className={`font-mono text-lg font-bold mt-0.5 ${acctLive?.net_exp_pct != null ? pnlCl(acctLive.net_exp_pct) : 'text-slate-600'}`}>
                {acctLive?.net_exp_pct != null ? `${acctLive.net_exp_pct >= 0 ? '+' : ''}${acctLive.net_exp_pct.toFixed(1)}%` : '—'}
              </div>
              <div className="text-[9px] text-slate-500 mt-0.5">
                gross {acctLive?.gross_exp_pct != null ? `${acctLive.gross_exp_pct.toFixed(1)}%` : '—'}
                {acctLive?.equity ? ` · L ${((longMV / acctLive.equity) * 100).toFixed(0)}% / S ${((shortMV / acctLive.equity) * 100).toFixed(0)}%` : ''}
              </div>
            </div>
          </FreshWrap>
          ) : isUat ? (
          <FreshWrap fresh={fBook} className="grid grid-cols-2 gap-2">
            <KpiTile label="Total Fills" value={st?.total_fills ?? '—'} sub={`${st?.ytd_trades ?? 0} this year`}
              tip="Broker-rehearsal fills (gold.paper_uat_fills) — fills, not round-trips" />
            <KpiTile label="Fills Today" value={st?.today?.trades ?? 0} />
            <KpiTile label="Last Fill" value={st?.last_fill_at ? fmtAge(st.last_fill_at) : '—'} sub={st?.last_fill_at || undefined} />
            <KpiTile label="Round-Trip P&L" value="—" valueCl="text-slate-600" sub="ledger pending"
              tip="A per-strategy UAT round-trip P&L ledger is qr_etl's domain — never derived serve-time" />
          </FreshWrap>
          ) : (
          <FreshWrap fresh={fBook} lastKnown={st?.cum_pnl != null ? fmtK(st.cum_pnl) : '—'} className="grid grid-cols-2 gap-2">
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

      {/* ZONE 3 — Regime Forecast + Top Opportunities (~45/55) */}
      <div className="grid grid-cols-1 lg:grid-cols-[0.82fr_1fr] gap-3">
        <Panel title="Regime Forecast" fresh={fRegime} action={
          <span className="text-[9px] text-slate-600" title="7-day risk-on probability, momentum_nowcast (consumption.macro_regime_7d). Dashed line = neutral 50%.">7d risk-on · 50% = neutral</span>
        }>
          <div className="grid grid-cols-2 divide-x divide-white/[0.05]">
            <RegimeBars region="US" fc={regimeFc?.US} />
            <RegimeBars region="HK" fc={regimeFc?.HK} />
          </div>
        </Panel>
        <Opportunities picks={oppPicks} navigateToTab={navigateToTab} fresh={fOpps} />
      </div>

      {/* ZONE 4 — Order Book */}
      <OrderBook orders={orders || []} fresh={fOrders} />

      {/* ZONE 5 — Market Status (compact strip) */}
      <MarketStrip navigateToTab={navigateToTab} fresh={fMarket} />

      {/* ZONE 6 — Action Center: merged strategy risks + monitoring gap +
          platform alerts in a single panel, severity then recency. */}
      <Panel title="Action Center" fresh={fAttention} action={
        <span className="flex items-center gap-2 whitespace-nowrap">
          {/* Bar-quality badge (bar_quality from /api/system/freshness).
              Always rendered so UNKNOWN/PENDING are visible — never
              silently treated as GREEN. */}
          <span className={`text-[9px] font-bold ${bqView.badgeCl}`} title={bqView.tip}>
            Bar quality {bqView.label}
          </span>
          {sevCounts.critical > 0 && <span className="text-[9px] font-bold text-rose-400">{sevCounts.critical} critical</span>}
          {sevCounts.warning > 0 && <span className="text-[9px] font-bold text-slate-400">{sevCounts.warning} warning</span>}
          {sevCounts.info > 0 && <span className="text-[9px] text-slate-500">{sevCounts.info} info</span>}
          {visibleItems.length === 0 && <span className="text-[9px] text-slate-500">clear</span>}
        </span>
      }>
        {attentionGroups.map((group, gi) => {
          const lead = group[0];
          const isCrit = lead.sev === 'critical';
          const sv = SEV_STYLE[lead.sev] || SEV_STYLE.info;
          const grouped = group.length > 1;
          const gKey = grouped ? alertClass(lead) : null;
          const expanded = gKey != null && openGroups.has(gKey);
          const leadId = lead.ackKey || lead.key;
          const groupTitle = grouped && gKey === 'feed-stale'
            ? `${group.length} feeds stale — ${group.map(a => a.refId || a.title).join(', ')}`
            : lead.title;
          return (
            <div key={gKey || lead.key} className={gi > 0 ? 'border-t border-t-white/[0.05]' : ''}>
              <div className={`flex items-center gap-3 px-3 ${isCrit ? 'py-3 border-l-4' : 'py-2 border-l-2'} ${sv.border} ${sv.bg}`}>
                {grouped && (
                  <button onClick={() => toggleGroup(gKey)} className="flex-none w-3 text-[10px] text-slate-500 hover:text-slate-300" title="Show individual alerts">{expanded ? '▾' : '▸'}</button>
                )}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className={`text-[8px] font-black tracking-wide px-1.5 py-0.5 rounded ${sv.tag}`}>{lead.tag}</span>
                    <button onClick={() => grouped ? toggleGroup(gKey) : runAction(lead)} className={`${isCrit ? 'text-[13px]' : 'text-[12px]'} font-bold text-white truncate hover:opacity-80 text-left`}>{groupTitle}</button>
                  </div>
                  {lead.kind === 'risk' && lead.triggers && lead.triggers.length > 0 ? (
                    <div className="flex items-center gap-1 mt-1 flex-wrap" title={lead.fullMetrics}>
                      {lead.triggers.map(t => (
                        <span key={t} className="font-mono text-[9px] px-1.5 py-0.5 rounded bg-white/[0.06] text-slate-300">{t}</span>
                      ))}
                    </div>
                  ) : (
                    <div className={`${isCrit ? 'text-[11px]' : 'text-[10px]'} text-slate-500 mt-0.5 truncate`} title={lead.impact}>{lead.impact}</div>
                  )}
                  {actMsg && actMsg.key === leadId && (
                    <div className={`text-[9px] font-mono mt-0.5 ${actMsg.ok ? 'text-teal-400' : 'text-rose-400'}`}>{actMsg.text}</div>
                  )}
                </div>
                <span className="font-mono text-[10px] text-slate-600 flex-none">{lead.age || '—'}</span>
                <div className="flex-none flex items-center gap-1">
                  <button onClick={() => runAction(lead)} disabled={actBusy === leadId}
                    className="text-[10px] font-bold px-2.5 py-1 rounded bg-white/[0.06] hover:bg-white/[0.1] text-slate-200 disabled:opacity-50">
                    {actBusy === leadId ? '…' : (ACT_LABEL[lead.action] || 'Open')}
                  </button>
                  {lead.ackKey && (
                    <>
                      <button onClick={() => dismissAlert(group, 'acknowledge')} title="Acknowledge — persists server-side (actor + timestamp)"
                        className="text-[9px] px-1.5 py-1 rounded text-slate-500 hover:text-slate-300 hover:bg-white/[0.05]">Ack</button>
                      <button onClick={() => dismissAlert(group, 'snooze')} title="Snooze 1h — persists server-side, auto-returns"
                        className="text-[9px] px-1.5 py-1 rounded text-slate-500 hover:text-slate-300 hover:bg-white/[0.05]">Snooze 1h</button>
                    </>
                  )}
                </div>
              </div>
              {grouped && expanded && group.map(m => {
                const mid = m.ackKey || m.key;
                return (
                  <div key={m.key} className="flex items-center gap-3 py-1.5 px-3 pl-8 border-l-2 border-l-white/[0.08]">
                    <div className="flex-1 min-w-0">
                      <div className="text-[11px] font-mono text-slate-300 truncate">{m.title}</div>
                      <div className="text-[9px] text-slate-600 truncate" title={m.impact}>{m.impact}</div>
                    </div>
                    <span className="font-mono text-[9px] text-slate-600 flex-none">{m.age || '—'}</span>
                    <button onClick={() => runAction(m)} className="flex-none text-[9px] font-bold px-2 py-0.5 rounded bg-white/[0.05] hover:bg-white/[0.09] text-slate-300">{ACT_LABEL[m.action] || 'Open'}</button>
                    {m.ackKey && <button onClick={() => dismissAlert([m], 'acknowledge')} className="flex-none text-[9px] px-1.5 py-0.5 rounded text-slate-600 hover:text-slate-300">Ack</button>}
                  </div>
                );
              })}
            </div>
          );
        })}
        {visibleItems.length === 0 && (
          <div className="py-6 text-center text-[11px] text-slate-600">Nothing needs attention right now</div>
        )}
      </Panel>
    </div>
  );
};

export default CommandCenter;
