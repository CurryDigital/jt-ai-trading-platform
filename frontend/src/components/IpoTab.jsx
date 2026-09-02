import React, { useState, useMemo, useCallback } from 'react';
import { fmtPct, api, usePoll, compact } from '../utils';

// =================================================================
// IPO subtab (Strategies > IPO) — HK IPO only, redesign 2026-09-02
//
// Data sources:
//   GET /api/hkex/ipos?limit=400      enriched list: calendar + details + performance
//                                     + price range/lot/grey (silver) + day-20 (lateral
//                                     silver.unified_prices until gold.return_day20_pct
//                                     is backfilled — qr_etl t_e71cffde)
//   GET /api/hkex/ipos/subscription   open/upcoming subscription windows
//                                     (feed incomplete — qr_etl t_e71cffde)
//   GET /api/hkex/ipos/book           active paper-book positions in IPO names
//   GET /api/hkex/ipos/sectors        2y sector aggregates
//   GET /api/strategies/researcher    strategy book, filtered to HK IPO strategies
//
// Chinese names: gold.hk_ipo_calendar.stock_name_zh — column does not exist yet
// (qr_etl t_437922f4). API self-adapts once it lands; until then zh is null and
// the UI falls back to the English name (flagged, not hidden).
// =================================================================

const CSS = `
.ipo-panel{background:#10141c;border:1px solid #161b25;border-radius:8px;}
.ipo-head{display:flex;align-items:center;justify-content:space-between;padding:13px 16px;border-bottom:1px solid #161b25;}
.ipo-title{font-size:11px;color:#8b93a3;letter-spacing:.5px;font-weight:600;display:flex;align-items:center;gap:8px;}
.ipo-tag{font-size:9px;font-weight:700;letter-spacing:.4px;padding:2px 7px;border-radius:4px;}
.ipo-tag-live{background:#0e3630;color:#2dd4bf;}
.ipo-tag-pending{background:#332a0e;color:#fbbf24;}
.ipo-tag-paper{background:#1b2230;color:#8b93a3;}
.ipo-tag-exp{background:#241f38;color:#a78bfa;}
.ipo-tag-watch{background:#0e3630;color:#2dd4bf;}
.ipo-stat{background:#10141c;border:1px solid #161b25;border-radius:8px;padding:12px 14px;}
.ipo-tbl{width:100%;border-collapse:collapse;}
.ipo-tbl th{text-align:left;font-size:10px;color:#565e6c;letter-spacing:.3px;font-weight:600;padding:8px 10px;border-bottom:1px solid #161b25;white-space:nowrap;}
.ipo-tbl td{padding:10px;border-bottom:1px solid #161b25;font-size:12px;vertical-align:middle;white-space:nowrap;}
.ipo-tbl tr:last-child td{border-bottom:none;}
.ipo-tbl tbody tr:hover td{background:#12161f;}
.ipo-tbl th.num,.ipo-tbl td.num{text-align:right;font-family:ui-monospace,'JetBrains Mono',monospace;font-variant-numeric:tabular-nums;}
.ipo-tbl th.sortable{cursor:pointer;user-select:none;}
.ipo-tbl th.sortable:hover{color:#8b93a3;}
.ipo-ticker{color:#2dd4bf;font-family:ui-monospace,'JetBrains Mono',monospace;font-weight:600;}
.ipo-name{color:#e6e8eb;font-size:12px;}
.ipo-name-en{color:#565e6c;font-size:10px;}
.ipo-co{color:#8b93a3;font-size:11px;}
.ipo-green{color:#34d399;} .ipo-red{color:#f87171;} .ipo-faint{color:#565e6c;}
.ipo-pill{font-size:9px;font-weight:700;padding:3px 8px;border-radius:4px;letter-spacing:.3px;white-space:nowrap;}
.ipo-st-book{background:#332a0e;color:#fbbf24;}
.ipo-st-listing{background:#0e3630;color:#2dd4bf;}
.ipo-st-hold{background:#152233;color:#60a5fa;}
.ipo-st-exit{background:#332a0e;color:#fbbf24;}
.ipo-st-urgent{background:#331717;color:#f87171;}
.ipo-st-open{background:#152233;color:#60a5fa;}
.ipo-btn{font-size:11px;font-weight:600;padding:6px 12px;border-radius:6px;border:1px solid #1d2430;background:transparent;color:#8b93a3;cursor:pointer;}
.ipo-btn:hover{border-color:#565e6c;color:#e6e8eb;}
.ipo-btn:disabled{opacity:.4;cursor:not-allowed;}
.ipo-btn:disabled:hover{border-color:#1d2430;color:#8b93a3;}
.ipo-btn-primary{background:#2dd4bf;color:#04211c;border-color:#2dd4bf;}
.ipo-btn-danger{border-color:#4a2323;color:#f87171;}
.ipo-btn-amber{background:#fbbf24;color:#332a05;border-color:#fbbf24;}
.ipo-yr{font-size:11px;padding:4px 10px;border-radius:5px;border:1px solid #1d2430;color:#565e6c;cursor:pointer;background:transparent;}
.ipo-yr.active{background:#12161f;color:#e6e8eb;border-color:#565e6c;}
.ipo-note{font-size:11px;color:#565e6c;line-height:1.6;padding:12px 16px;border-top:1px solid #161b25;}
.ipo-note code{font-family:ui-monospace,monospace;color:#8b93a3;background:#12161f;padding:1px 5px;border-radius:3px;}
.ipo-sector-row{display:flex;justify-content:space-between;padding:7px 0;border-bottom:1px solid #161b25;font-size:11px;}
.ipo-sector-row:last-child{border-bottom:none;}
`;

const num = (v, d = 2) => v == null || isNaN(v) ? '—' : Number(v).toLocaleString(undefined, { minimumFractionDigits: d, maximumFractionDigits: d });
const signed = (v, d = 1) => v == null ? '—' : `${v >= 0 ? '+' : ''}${Number(v).toFixed(d)}%`;
const sgnCl = (v) => v == null ? 'ipo-faint' : v >= 0 ? 'ipo-green' : 'ipo-red';
const pctOrRatio = (v, d = 1) => {
  if (v == null || isNaN(v)) return null;
  const n = Number(v);
  return Math.abs(n) > 1 ? +n.toFixed(d) : +(n * 100).toFixed(d);
};
const median = (arr) => {
  if (!arr.length) return null;
  const s = [...arr].sort((a, b) => a - b);
  const m = s.length >> 1;
  return s.length % 2 ? s[m] : (s[m - 1] + s[m]) / 2;
};
const daysSince = (dateStr) => {
  if (!dateStr) return null;
  return Math.floor((Date.now() - new Date(dateStr + 'T00:00:00Z').getTime()) / 86400000);
};

const Panel = ({ title, tag, right, note, children, scroll }) => (
  <div className="ipo-panel">
    <div className="ipo-head">
      <div className="ipo-title">{title}{tag}</div>
      {right && <div style={{ fontSize: 10, color: '#565e6c' }}>{right}</div>}
    </div>
    {scroll ? <div style={{ overflowX: 'auto' }}>{children}</div> : children}
    {note && <div className="ipo-note">{note}</div>}
  </div>
);

const Tag = ({ kind, children }) => <span className={`ipo-tag ipo-tag-${kind}`}>{children}</span>;

const Stat = ({ label, value, sub, green }) => (
  <div className="ipo-stat">
    <div style={{ fontSize: 10, color: '#565e6c', letterSpacing: '.4px', marginBottom: 8 }}>{label}</div>
    <div className={green ? 'ipo-green' : ''} style={{ fontSize: 20, fontWeight: 600, fontFamily: 'ui-monospace,monospace' }}>{value}</div>
    <div style={{ fontSize: 10, color: '#565e6c', marginTop: 4 }}>{sub || ' '}</div>
  </div>
);

const NameCell = ({ zh, en, pending }) => (
  <td>
    <div className={zh ? 'ipo-name' : 'ipo-co'}>{zh || en || '—'}</div>
    {zh && en && <div className="ipo-name-en">{en}</div>}
    {!zh && pending && <div className="ipo-name-en">zh pending · t_437922f4</div>}
  </td>
);

// Min investment for one board lot at top of range, incl. ~0.77% brokerage/levies estimate
const minInvestment = (r) => {
  const px = r.fixed_price ? r.offer_price : (r.offer_price_high ?? r.offer_price);
  if (px == null || !r.lot_size) return null;
  return Math.round(px * r.lot_size * 1.0077);
};

export function IpoTab({ onOpen }) {
  const [ipos, setIpos] = useState(null);
  const [strategies, setStrategies] = useState([]);
  const [sectors, setSectors] = useState([]);
  const [subs, setSubs] = useState(null);
  const [book, setBook] = useState(null);
  const [yearFilter, setYearFilter] = useState('ALL');
  const [sort, setSort] = useState({ key: null, dir: 'desc' });
  const [actionMsg, setActionMsg] = useState(null);

  const load = useCallback(async () => {
    const [lst, strat, sec, sub, bk] = await Promise.all([
      api.get('/api/hkex/ipos?limit=400'),
      api.get('/api/strategies/researcher'),
      api.get('/api/hkex/ipos/sectors'),
      api.get('/api/hkex/ipos/subscription'),
      api.get('/api/hkex/ipos/book'),
    ]);
    setIpos(Array.isArray(lst?.ipos) ? lst.ipos : []);
    const bookRows = Array.isArray(strat?.strategies) ? strat.strategies : (Array.isArray(strat?.data) ? strat.data : []);
    setStrategies(bookRows.filter(s =>
      (s.asset_class || '').toLowerCase().includes('ipo') || (s.id || '').toLowerCase().startsWith('hk_ipo')
    ));
    setSectors(Array.isArray(sec?.sectors) ? sec.sectors : []);
    setSubs(Array.isArray(sub?.ipos) ? sub.ipos : []);
    setBook(Array.isArray(bk?.positions) ? bk.positions : []);
  }, []);

  usePoll(load, 120000);

  const stats = useMemo(() => {
    if (!ipos || !ipos.length) return null;
    const fd = ipos.map(r => r.first_day_return).filter(v => v != null);
    const d30 = ipos.map(r => r.return_day30).filter(v => v != null);
    const dates = ipos.map(r => r.listing_date).sort();
    return {
      n: ipos.length,
      window: `${dates[0]} → ${dates[dates.length - 1]}`,
      fdN: fd.length,
      fdAvg: fd.length ? fd.reduce((a, b) => a + b, 0) / fd.length : null,
      fdMed: median(fd),
      fdWin: fd.length ? (fd.filter(v => v > 0).length / fd.length) * 100 : null,
      d30N: d30.length,
      d30Avg: d30.length ? d30.reduce((a, b) => a + b, 0) / d30.length : null,
    };
  }, [ipos]);

  const years = useMemo(() => {
    if (!ipos) return [];
    return [...new Set(ipos.map(r => (r.listing_date || '').slice(0, 4)).filter(Boolean))].sort().reverse().slice(0, 3);
  }, [ipos]);

  const view = useMemo(() => {
    if (!ipos) return [];
    let rows = ipos.filter(r => yearFilter === 'ALL' || (r.listing_date || '').startsWith(yearFilter));
    if (sort.key) {
      const k = sort.key;
      rows = [...rows].sort((a, b) => {
        const av = a[k], bv = b[k];
        if (av == null && bv == null) return 0;
        if (av == null) return 1;
        if (bv == null) return -1;
        return sort.dir === 'desc' ? bv - av : av - bv;
      });
    }
    return rows;
  }, [ipos, yearFilter, sort]);

  const sectorView = useMemo(() => ({
    named: sectors.filter(s => s.sector).slice(0, 8),
    unclassified: sectors.find(s => !s.sector),
  }), [sectors]);

  const toggleSort = (key) => setSort(s => ({ key, dir: s.key === key && s.dir === 'desc' ? 'asc' : 'desc' }));

  const adjustAllocation = async (s) => {
    const cur = s.assigned_capital != null ? Number(s.assigned_capital) : null;
    const input = window.prompt(`New total assigned capital for ${s.id} (current ${cur != null ? '$' + cur.toLocaleString() : 'unassigned'}):`, cur ?? '');
    if (input == null) return;
    const val = Number(input);
    if (!isFinite(val) || val < 0) { setActionMsg('Invalid amount — allocation unchanged'); return; }
    const res = await api.post(`/api/strategies/${s.id}/capital-pool`, { total_assigned: val });
    setActionMsg(res && (res.success !== false) ? `Allocation updated to $${val.toLocaleString()}` : `Allocation update failed: ${res?.error || 'no response'}`);
    load();
  };

  const pauseStrategy = async (s) => {
    if (!window.confirm(`Pause ${s.id}? This closes the paper book and stops monitoring (same as Stop in the Lab).`)) return;
    const res = await api.post(`/api/strategies/${s.id}/deactivate`, { action: 'close' });
    setActionMsg(res && res.success ? 'Strategy paused' : `Pause failed: ${res?.error || res?.message || 'no response'}`);
    load();
  };

  if (ipos === null) {
    return (
      <div className="ipo-panel" style={{ padding: '32px 16px', textAlign: 'center', fontSize: 11, color: '#565e6c' }}>
        <style>{CSS}</style>Loading HK IPO book…
      </div>
    );
  }

  const body = (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
      <style>{CSS}</style>

      {actionMsg && (
        <div className="ipo-panel" style={{ padding: '8px 16px', fontSize: 11, color: '#8b93a3' }}>
          {actionMsg} <button className="ipo-btn" style={{ marginLeft: 8, padding: '2px 8px' }} onClick={() => setActionMsg(null)}>×</button>
        </div>
      )}

      {/* stats strip */}
      {stats && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(6,1fr)', gap: 12 }}>
          <Stat label="IPOS IN WINDOW" value={stats.n} sub={stats.window} />
          <Stat label="AVG FIRST-DAY" value={stats.fdAvg == null ? '—' : fmtPct(stats.fdAvg)} sub={`measured on ${stats.fdN} of ${stats.n}`} green={stats.fdAvg > 0} />
          <Stat label="MEDIAN FIRST-DAY" value={stats.fdMed == null ? '—' : fmtPct(stats.fdMed)} sub="median, measured rows" green={stats.fdMed > 0} />
          <Stat label="FIRST-DAY WIN RATE" value={stats.fdWin == null ? '—' : `${stats.fdWin.toFixed(0)}%`} sub={`${stats.fdN} priced`} />
          <Stat label="AVG DAY-30" value={stats.d30Avg == null ? '—' : fmtPct(stats.d30Avg)} sub={`measured on ${stats.d30N} of ${stats.n}`} green={stats.d30Avg > 0} />
          <Stat label="UNDER SUBSCRIPTION" value={subs === null ? '—' : subs.length}
                sub={subs && subs.length ? `${subs.length} open` : 'feed pending · t_e71cffde'} />
        </div>
      )}

      {/* strategy book */}
      <Panel title="HK IPO STRATEGIES" tag={<Tag kind="live">LIVE</Tag>}>
        <div style={{ padding: 16 }}>
          {strategies.length === 0 ? (
            <div style={{ fontSize: 11, color: '#565e6c' }}>No HK IPO strategies registered in the strategy book.</div>
          ) : strategies.map(s => {
            const wr = pctOrRatio(s.win_rate);
            const mdd = pctOrRatio(s.max_drawdown);
            const ret = pctOrRatio(s.returns_oos);
            return (
              <div key={s.id}>
                <div style={{ fontSize: 14, fontWeight: 600, marginBottom: 8 }}>{s.name || s.id}</div>
                <div style={{ display: 'flex', gap: 6, marginBottom: 14 }}>
                  {s.status && <Tag kind="paper">{String(s.status).toUpperCase()}</Tag>}
                  {s.priority && <Tag kind="exp">{s.priority}</Tag>}
                  {s.is_paper_monitoring && <Tag kind="watch">PAPER · {String(s.paper_state || 'watching').toUpperCase()}</Tag>}
                </div>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4,1fr)', gap: 18, marginBottom: 14 }}>
                  <div><div style={{ fontSize: 10, color: '#565e6c', marginBottom: 4 }}>SHARPE</div>
                    <div style={{ fontSize: 16, fontWeight: 600, fontFamily: 'ui-monospace,monospace' }}>{s.sharpe_ratio == null ? '—' : Number(s.sharpe_ratio).toFixed(2)}</div></div>
                  <div><div style={{ fontSize: 10, color: '#565e6c', marginBottom: 4 }}>OOS RET</div>
                    <div className={ret == null ? '' : sgnCl(ret)} style={{ fontSize: 16, fontWeight: 600, fontFamily: 'ui-monospace,monospace' }}>{ret == null ? '—' : fmtPct(ret)}</div></div>
                  <div><div style={{ fontSize: 10, color: '#565e6c', marginBottom: 4 }}>WIN</div>
                    <div style={{ fontSize: 16, fontWeight: 600, fontFamily: 'ui-monospace,monospace' }}>{wr == null ? '—' : `${wr.toFixed(0)}%`}</div></div>
                  <div><div style={{ fontSize: 10, color: '#565e6c', marginBottom: 4 }}>MDD</div>
                    <div className={mdd == null ? '' : sgnCl(mdd)} style={{ fontSize: 16, fontWeight: 600, fontFamily: 'ui-monospace,monospace' }}>{mdd == null ? '—' : fmtPct(mdd)}</div></div>
                </div>
                <div style={{ fontSize: 11, color: '#565e6c', marginBottom: 14 }}>
                  {s.backtest_trades ?? s.trade_count_oos ?? '—'} OOS trades · {s.assigned_capital != null ? `$${Number(s.assigned_capital).toLocaleString()} assigned` : 'capital unassigned'}
                </div>
                <div style={{ display: 'flex', gap: 8 }}>
                  <button className="ipo-btn" onClick={() => onOpen && onOpen(s.id)}>View signal log ↗</button>
                  <button className="ipo-btn" onClick={() => adjustAllocation(s)}>Adjust allocation</button>
                  <button className="ipo-btn ipo-btn-danger" onClick={() => pauseStrategy(s)}>Pause strategy</button>
                </div>
              </div>
            );
          })}
        </div>
      </Panel>

      {/* under subscription */}
      <Panel
        title="IPO UNDER SUBSCRIPTION"
        tag={subs && subs.length ? <Tag kind="live">LIVE</Tag> : <Tag kind="pending">PENDING</Tag>}
        right={subs && subs.length ? `${subs.length} open` : 'no tracked windows'}
        scroll
        note={<span>Min. investment is one board lot at the top of the offer range plus a ~0.77% brokerage/levies estimate, HK$. The subscription-window feed is incomplete upstream (application dates unpopulated, no forward calendar rows) — <code>qr_etl t_e71cffde</code>. An empty table means &quot;no tracked windows&quot;, not &quot;no HK IPOs open&quot;.</span>}
      >
        {subs && subs.length > 0 ? (
          <table className="ipo-tbl">
            <thead>
              <tr>
                <th>Ticker</th><th>Name</th><th>Sector</th>
                <th className="num">Price range</th><th className="num">Lot size</th><th className="num">Min. investment</th>
                <th>Subscription period</th><th className="num">Oversub (retail)</th><th className="num">Grey market</th>
                <th className="num">Listing</th><th>Action</th>
              </tr>
            </thead>
            <tbody>
              {subs.map(r => {
                const closesIn = daysSince(r.application_end) != null ? -daysSince(r.application_end) : null;
                const urgent = closesIn != null && closesIn <= 1;
                const greyPct = r.grey_close != null && (r.offer_price_high ?? r.offer_price)
                  ? (r.grey_close / (r.offer_price_high ?? r.offer_price) - 1) * 100 : null;
                return (
                  <tr key={r.ticker}>
                    <td className="ipo-ticker">{r.ticker}</td>
                    <NameCell zh={null} en={r.stock_name} pending />
                    <td className="ipo-co">{r.sector || '—'}</td>
                    <td className="num">{r.fixed_price ? `${num(r.offer_price)} (fixed)` : r.offer_price_low != null ? `${num(r.offer_price_low)}–${num(r.offer_price_high)}` : '—'}</td>
                    <td className="num">{r.lot_size ? `${r.lot_size} sh` : '—'}</td>
                    <td className="num">{minInvestment(r) != null ? minInvestment(r).toLocaleString() : '—'}</td>
                    <td>{r.application_end
                      ? <span className={`ipo-pill ${urgent ? 'ipo-st-urgent' : 'ipo-st-open'}`}>{urgent ? 'CLOSES SOON' : 'OPEN'} · ends {r.application_end}</span>
                      : <span className="ipo-pill ipo-st-book">WINDOW TBC</span>}</td>
                    <td className="num">{r.oversubscription_retail != null ? `${num(r.oversubscription_retail, 1)}x` : '—'}</td>
                    <td className={`num ${sgnCl(greyPct)}`}>{greyPct != null ? signed(greyPct, 0) : '—'}</td>
                    <td className="num">{r.listing_date || '—'}</td>
                    <td><button className="ipo-btn ipo-btn-primary" disabled title="IPO subscription is not wired to a broker route">Apply ↗</button></td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        ) : (
          <div style={{ padding: 16, fontSize: 11, color: '#565e6c' }}>
            No IPOs currently tracked in a subscription window.
          </div>
        )}
      </Panel>

      {/* active IPO book */}
      <Panel
        title="ACTIVE IPO BOOK"
        tag={<Tag kind="live">LIVE</Tag>}
        right={book ? `${book.length} tracked` : ''}
        scroll
        note={<span>Positions from the paper book (<code>consumption.portfolio_positions_current</code>) joined with IPO offer data. Day counts are calendar days; the drift strategy targets a 20-trading-day hold. Order actions are managed from the Execution tab, not this page.</span>}
      >
        {book && book.length > 0 ? (
          <table className="ipo-tbl">
            <thead>
              <tr>
                <th>Ticker</th><th>Name</th><th>Status</th>
                <th className="num">IPO price</th><th className="num">Oversub</th>
                <th className="num">Last / current</th><th className="num">Chg vs IPO</th>
                <th className="num">Volume</th><th>Action</th>
              </tr>
            </thead>
            <tbody>
              {book.map(r => {
                const d = daysSince(r.listing_date);
                const chg = r.current_price != null && r.offer_price ? (r.current_price / r.offer_price - 1) * 100 : null;
                const pill = d === 0
                  ? <span className="ipo-pill ipo-st-listing">LISTING TODAY</span>
                  : d != null && d >= 28
                    ? <span className="ipo-pill ipo-st-exit">HOLD COMPLETE · D+{d}</span>
                    : <span className="ipo-pill ipo-st-hold">HOLDING · D+{d ?? '—'} / 20td target</span>;
                return (
                  <tr key={`${r.strategy_id}-${r.ticker}`}>
                    <td className="ipo-ticker">{r.ticker}</td>
                    <NameCell zh={null} en={r.stock_name} pending />
                    <td>{pill}</td>
                    <td className="num">{num(r.offer_price)}</td>
                    <td className="num">{r.oversubscription_retail != null ? `${num(r.oversubscription_retail, 1)}x` : '—'}</td>
                    <td className="num">{num(r.current_price)}</td>
                    <td className={`num ${sgnCl(chg)}`}>{chg != null ? signed(chg) : <span className="ipo-faint">n/a</span>}</td>
                    <td className="num">{r.last_volume != null ? compact(r.last_volume) : '—'}</td>
                    <td><button className="ipo-btn" disabled title="Manage exits from the Execution tab">Manage ↗</button></td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        ) : (
          <div style={{ padding: 16, fontSize: 11, color: '#565e6c' }}>
            No open IPO positions — the drift book is event-driven and currently flat (paper · watching).
          </div>
        )}
      </Panel>

      {/* recent IPOs performance */}
      <Panel
        title="RECENT IPOS — PERFORMANCE"
        tag={<Tag kind="live">LIVE</Tag>}
        scroll
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: 6, padding: '12px 16px' }}>
          {['ALL', ...years].map(y => (
            <button key={y} className={`ipo-yr ${yearFilter === y ? 'active' : ''}`} onClick={() => setYearFilter(y)}>{y === 'ALL' ? 'All' : y}</button>
          ))}
        </div>
        <table className="ipo-tbl">
          <thead>
            <tr>
              <th>Ticker</th><th>Name</th><th>Sector</th><th>Listed</th>
              <th className="num">IPO price</th>
              <th className="num">Day 1 price</th>
              <th className="num sortable" onClick={() => toggleSort('first_day_return')}>Day 1 %<span style={{ opacity: .4, marginLeft: 2 }}>{sort.key === 'first_day_return' ? (sort.dir === 'desc' ? '↓' : '↑') : '↕'}</span></th>
              <th className="num">Day 20 price</th>
              <th className="num sortable" onClick={() => toggleSort('return_day20')}>Day 20 %<span style={{ opacity: .4, marginLeft: 2 }}>{sort.key === 'return_day20' ? (sort.dir === 'desc' ? '↓' : '↑') : '↕'}</span></th>
              <th className="num">Volume (D1)</th>
              <th className="num">Oversub</th>
            </tr>
          </thead>
          <tbody>
            {view.map(r => (
              <tr key={`${r.ticker}-${r.listing_date}`}>
                <td className="ipo-ticker">{r.ticker}</td>
                <NameCell zh={r.stock_name_zh} en={r.stock_name} pending={!r.stock_name_zh} />
                <td className="ipo-co">{r.sector || '—'}</td>
                <td className="num">{r.listing_date}</td>
                <td className="num">{num(r.offer_price)}</td>
                <td className="num">{num(r.first_day_close)}</td>
                <td className={`num ${sgnCl(r.first_day_return)}`}>{r.first_day_return == null ? '—' : signed(r.first_day_return)}</td>
                <td className="num" title={r.day20_date ? `20th trading day: ${r.day20_date}` : 'fewer than 20 trading days since listing'}>{num(r.day20_price)}</td>
                <td className={`num ${sgnCl(r.return_day20)}`}>{r.return_day20 == null ? '—' : signed(r.return_day20)}</td>
                <td className="num">{r.first_day_volume != null ? compact(r.first_day_volume) : '—'}</td>
                <td className="num">{r.oversubscription_retail != null ? `${num(r.oversubscription_retail, 1)}x` : '—'}</td>
              </tr>
            ))}
          </tbody>
        </table>
        <div className="ipo-note">
          {view.length} rows · Day-20 = 20th trading day close vs offer, computed from <code>silver.unified_prices</code> until <code>gold.hk_ipo_performance.return_day20_pct</code> is backfilled (<code>qr_etl t_e71cffde</code>) · names show English until <code>stock_name_zh</code> lands (<code>qr_etl t_437922f4</code>)
        </div>
      </Panel>

      {/* secondary row */}
      <div style={{ display: 'grid', gridTemplateColumns: '1.4fr 1fr', gap: 16 }}>
        <Panel title="SECTOR BREAKDOWN · 2Y">
          <div style={{ padding: '6px 16px 16px' }}>
            {sectorView.named.length === 0 ? (
              <div style={{ fontSize: 11, color: '#565e6c', paddingTop: 8 }}>No classified sectors returned.</div>
            ) : sectorView.named.map(s => (
              <div key={s.sector} className="ipo-sector-row">
                <span style={{ color: '#8b93a3' }}>{s.sector}</span>
                <span style={{ display: 'flex', gap: 16, fontFamily: 'ui-monospace,monospace' }}>
                  <span style={{ color: '#565e6c', width: 30, textAlign: 'right' }}>{s.ipo_count}</span>
                  <span className={sgnCl(s.avg_first_day_return)} style={{ width: 64, textAlign: 'right' }}>{s.avg_first_day_return == null ? '—' : fmtPct(s.avg_first_day_return)}</span>
                  <span style={{ color: '#565e6c', width: 36, textAlign: 'right' }}>{s.win_rate == null ? '—' : `${s.win_rate.toFixed(0)}%`}</span>
                </span>
              </div>
            ))}
            {sectorView.unclassified && (
              <div style={{ fontSize: 9, color: '#565e6c', marginTop: 8, lineHeight: 1.5 }}>
                {sectorView.unclassified.ipo_count} of the 2y IPOs carry no sector classification upstream
                {sectorView.unclassified.avg_first_day_return != null && <> (measured avg 1D {fmtPct(sectorView.unclassified.avg_first_day_return)}, win {sectorView.unclassified.win_rate?.toFixed(0)}%)</>} — excluded above, not treated as a sector. Coverage fix is on <span style={{ fontFamily: 'ui-monospace,monospace', color: '#8b93a3' }}>qr_etl t_2f98c3be</span>.
              </div>
            )}
          </div>
        </Panel>
        <Panel title="OVERSUBSCRIPTION COHORTS" tag={<Tag kind="pending">PENDING</Tag>}>
          <div style={{ padding: '6px 16px 16px', fontSize: 11, color: '#565e6c', lineHeight: 1.6, paddingTop: 14 }}>
            Per-IPO oversubscription multiples are now live on the list endpoint (t_2f98c3be). The cohort-level
            return backtest (the entry signal behind the drift book — e.g. 100–500x bucket vs day-20 drift) is a
            research deliverable, not a UI computation: it lands when <code>qr_research</code> publishes the cohort
            study from the frozen IPO strategy spec. Until then this panel stays pending rather than implying a
            result from raw multiples.
          </div>
        </Panel>
      </div>
    </div>
  );

  return body;
}

export default IpoTab;
