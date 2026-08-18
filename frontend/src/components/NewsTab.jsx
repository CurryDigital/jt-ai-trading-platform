import React, { useEffect, useRef, useState } from 'react';
import { api, usePoll, fmtAge, fmtK } from '../utils';

// Research > News — story-CLUSTER feed (refactor 2026-08-12).
// Display unit = one row per cluster, NOT per headline. Primary source:
// GET /api/news/clusters (consumption.news_clusters, embedding clustering,
// qr_etl kanban t_d492325f). Until that table/endpoint lands, the feed is
// derived from GET /api/news/digest (token-Jaccard clusters over
// silver.historical_news) mapped onto the same contract — expansion then shows
// outlets only (no per-member links/timestamps yet).
// The old cross-category top-stories strip and the per-asset-class cards are
// gone: the feed itself, sorted by impact_score with no asset filter,
// replaces them (they would duplicate headline text).
// Acceptance invariant: no headline text renders twice on the page. Enforced
// client-side by normalizing ('(copy)' suffix stripped, case/whitespace
// folded) and keeping first occurrence; member headlines identical to the
// canonical headline are not re-printed inside the expansion.
// Colour carries meaning only: rose/emerald = signed direction/tone,
// blue = links only, everything else neutral slate/white.

const STALE_HOURS = 72;
// Default feed cap — rendering everything is why nothing stands out.
const FEED_CAP = 12;

// User reads English & Chinese only (persisted toggle). Server-side
// ?langs=en,zh is passed to both endpoints (silver.historical_news.lang);
// this regex is the client-side safety net. Durable ingest-side tagging is
// qr_etl t_69e09f53 (delivered: lang column + langs param).
// Outlook key space (t_3bfe7f78, after qr_research t_1f95572e): /api/news/outlook
// cluster keys are now EMBEDDING cluster_ids (news_clusters.cluster_id), not the
// digest token-Jaccard cluster_key. Badging is therefore exact cluster_id
// matching on the /api/news/clusters view: server-stamped llm_* columns win
// (qr_etl t_9a746bb9), with an exact (asset_class, cluster_id) join against the
// outlook map as fill-in for rows the stamp hasn't reached yet. The digest
// fallback keeps only a verbatim-headline join (no token-key join — the key
// spaces no longer intersect). Outlook is fetched UNFILTERED: the
// category-level strip is filter-independent.
const UNREADABLE_RE = /[Ͱ-ϿЀ-ӿ֐-׿؀-ۿݐ-ݿࢠ-ࣿऀ-ॿঀ-৿਀-੿઀-૿଀-୿ஂ-௿ఀ-౿ಀ-೿ഀ-ൿก-๿က-ၟႠ-ჿᄀ-ᄿፀ-፟ក-៿぀-ヿ가-힯ﭐ-﷿ﹰ-﻿]/;
const isReadable = (text) => !text || !UNREADABLE_RE.test(text);

// Normalize a headline for dedup: fold case/whitespace, strip trailing
// '(copy)' wire-dup marker. Used for the no-headline-twice invariant.
const normH = (h) =>
  (h || '').toLowerCase().replace(/\s*\(copy\)\s*$/, '').replace(/\s+/g, ' ').trim();

// HH:MM straight from the ISO string (timestamps are naive UTC — do NOT
// round-trip through Date, which would shift them into local time).
const fmtHHMM = (iso) => {
  if (!iso) return '—';
  const m = String(iso).match(/T?(\d{2}:\d{2})/);
  return m ? m[1] : '—';
};

const signedCl = (v) => (v > 0 ? 'text-emerald-400' : v < 0 ? 'text-rose-400' : 'text-slate-500');

const dirCl = (d) =>
  d === 'bullish' || d === 'bull' ? 'text-emerald-400'
    : d === 'bearish' || d === 'bear' ? 'text-rose-400'
    : 'text-slate-500';

const Chip = ({ label }) => (
  <span className="rounded bg-white/[0.05] px-1.5 py-px text-[8px] font-mono text-slate-400 whitespace-nowrap">
    {label}
  </span>
);

const AssetBadge = ({ cat, labels }) =>
  !cat ? null : (
    <span className="rounded border border-white/10 px-1.5 py-px text-[8px] font-mono text-slate-300 whitespace-nowrap">
      {labels?.[cat] || cat}
    </span>
  );

// t_9f70a327: serve-time macro-event grouping (GET /api/news/clusters,
// dedupe_events=true by default). Angle-split clusters of the same calendar
// event collapse into the highest-impact row, which carries an additive
// event_group annotation {event, event_date, anchor, related_count,
// related[]}. The chip names the event + collapsed-angle count; the
// expansion lists the angles for drill-down. Nothing is deleted — the raw
// list stays available via dedupe_events=false.
const EventGroupChip = ({ eg }) =>
  !eg ? null : (
    <span
      className="rounded bg-white/[0.05] px-1.5 py-px text-[8px] font-mono text-slate-400 whitespace-nowrap"
      title={`Macro event group · ${eg.event} (${eg.event_date}) · anchor: ${eg.anchor}\nCollapsed angles: ${(eg.related || []).map((r) => r.canonical_headline).join(' | ')}`}
    >
      ⧉ {eg.related_count} angle{eg.related_count === 1 ? '' : 's'} · {eg.event}
    </span>
  );

// Impact-tiered visual hierarchy — DISTRIBUTION-RELATIVE since 2026-08-12.
// Absolute thresholds (65/40) collapsed when scores compressed into the 40s,
// so tiers are now assigned by rank within the currently filtered feed
// window: top 10% HIGH, next 30% MEDIUM, remainder LOW — with a floor of
// 3 and a cap of 6 HIGH rows so the "top 3 at a glance" property survives
// any score distribution. The absolute score stays visible and unchanged;
// only the visual tier is relative.
//   HIGH:   15px/500 headline, full opacity, 3px left border by direction
//           (bearish=coral, bullish=teal, neutral=gray). Full meta + tickers.
//   MEDIUM: 13px/400 text-primary, 3px gray left border. Tickers on hover.
//   LOW:    13px/400 text-secondary, no border, collapsed meta.
// Single-sided borders are never rounded (rounded-none is explicit).
const TIER_BORDER = {
  HIGH: { bullish: 'border-teal-400', bearish: 'border-rose-400', neutral: 'border-slate-500' },
  MEDIUM: { bullish: 'border-slate-600', bearish: 'border-slate-600', neutral: 'border-slate-600' },
  LOW: null,
};
const TIER_SCORE_CL = { HIGH: 'text-white', MEDIUM: 'text-slate-400', LOW: 'text-slate-600' };
const TIER_HEAD_CL = {
  HIGH: 'text-[15px] font-medium text-white',
  MEDIUM: 'text-[13px] font-normal text-slate-200',
  LOW: 'text-[13px] font-normal text-slate-500',
};
const dirKeyOf = (d) => {
  const v = (d || '').toLowerCase();
  return v.startsWith('bull') ? 'bullish' : v.startsWith('bear') ? 'bearish' : 'neutral';
};

// --- Reference frames for every numeric display (2026-08-12) --------------
// Rule: no bare number without a scale, unit, or tooltip.

// Server timestamps are naive UTC ('2026-08-10T08:45:00') — append Z before
// epoch math, otherwise Date parses them as local time.
const parseUtc = (ts) => {
  if (!ts) return null;
  let s = String(ts);
  if (!/[zZ]|[+-]\d{2}:?\d{2}$/.test(s)) s += 'Z';
  const t = new Date(s).getTime();
  return Number.isNaN(t) ? null : t;
};
const ageHours = (ts) => {
  const t = parseUtc(ts);
  return t == null ? null : (Date.now() - t) / 3600000;
};
const exactUtc = (ts) => (ts ? `${String(ts).replace('T', ' ').slice(0, 16)} UTC` : '—');

// Freshness: colour-coded age dot, exact timestamp on hover.
// <1h live/pulsing · <6h fresh · <24h normal · >24h muted.
const AgeDot = ({ ts }) => {
  const h = ageHours(ts);
  if (h == null) return null;
  const [cls, band] = h < 1 ? ['bg-emerald-400 animate-pulse', 'live · <1h']
    : h < 6 ? ['bg-teal-400', 'fresh · <6h']
    : h < 24 ? ['bg-slate-400', 'normal · <24h']
    : ['bg-slate-600', 'muted · >24h'];
  return (
    <span
      className={`inline-block w-[7px] h-[7px] rounded-full shrink-0 ${cls}`}
      title={`${band} · ${exactUtc(ts)}`}
    />
  );
};

// >48h => explicit stale pill (rose = critical severity).
const StalePill = ({ ts }) => {
  const h = ageHours(ts);
  if (h == null || h <= 48) return null;
  return (
    <span
      className="rounded border border-rose-400/30 bg-rose-400/[0.06] px-1 py-px text-[8px] font-mono text-rose-400"
      title={`last seen ${exactUtc(ts)} (${Math.round(h)}h ago)`}
    >
      stale
    </span>
  );
};

// Tone: horizontal diverging bar on a FIXED -100..+100 axis
// (coral → gray → teal), marker at the current value, endpoints labelled.
const ToneBar = ({ value }) => {
  if (value == null) return null;
  const v = Math.max(-100, Math.min(100, Number(value) || 0));
  const pct = (v + 100) / 2;
  return (
    <span
      className="inline-flex items-center gap-1"
      title={`tone balance ${v > 0 ? '+' : ''}${v} on a −100…+100 scale (net bull vs bear share of clusters, %)`}
    >
      <span className="text-[7px] font-mono text-slate-600">tone</span>
      <span className="text-[7px] font-mono text-rose-400/80">−100</span>
      <span className="relative w-16 h-1.5 rounded-full bg-gradient-to-r from-rose-400/60 via-slate-500/40 to-teal-400/60">
        <span
          className="absolute top-1/2 -translate-y-1/2 w-[3px] h-[9px] rounded-none bg-white"
          style={{ left: `calc(${pct}% - 1px)` }}
        />
      </span>
      <span className="text-[7px] font-mono text-teal-400/80">+100</span>
    </span>
  );
};

// Confidence: 5-segment pip meter, exact % on hover (never "conf 60%").
const ConfPips = ({ conf }) => {
  if (conf == null) return null;
  const frac = conf > 1 ? conf / 100 : conf;
  const pct = Math.round(frac * 100);
  const filled = Math.max(0, Math.min(5, Math.round(frac * 5)));
  return (
    <span className="inline-flex items-center gap-[2px]" title={`LLM confidence ${pct}% (${filled} of 5 pips)`}>
      {[0, 1, 2, 3, 4].map((i) => (
        <span key={i} className={`w-1.5 h-[7px] rounded-none ${i < filled ? 'bg-slate-300' : 'bg-white/[0.08]'}`} />
      ))}
    </span>
  );
};

// 24h attention micro-chart: story count per hour from REAL member
// timestamps. User rule: if it can't be populated with real data, render
// nothing — an undecodable chart is worse than none. The digest fallback
// gives every member the same timestamp, so this stays null until
// news_clusters lands (qr_etl t_d492325f).
const AttentionChart = ({ members }) => {
  const buckets = new Array(24).fill(0);
  const now = Date.now();
  let n = 0;
  for (const m of members || []) {
    const t = parseUtc(m.published_at);
    if (t == null) continue;
    const ageH = (now - t) / 3600000;
    if (ageH >= 0 && ageH < 24) { buckets[23 - Math.floor(ageH)]++; n++; }
  }
  const peak = Math.max(...buckets);
  if (n < 2 || buckets.filter((b) => b > 0).length < 2) return null;
  const H = 18;
  const hourLabel = (i) => {
    const d = new Date(now - (23 - i) * 3600000);
    return `${String(d.getUTCHours()).padStart(2, '0')}:00`;
  };
  const peakLabel = hourLabel(buckets.indexOf(peak));
  return (
    <span
      className="inline-flex items-end gap-px shrink-0"
      title={`24h attention (stories per hour) · peak ${peakLabel} UTC with ${peak} ${peak === 1 ? 'story' : 'stories'}`}
    >
      {buckets.map((b, i) => (
        <svg key={i} width="2" height={H}>
          <rect
            x="0" y={H - (b / peak) * H} width="2" height={Math.max((b / peak) * H, b > 0 ? 1 : 0)}
            className={b === peak ? 'fill-slate-300' : 'fill-slate-600'}
          >
            <title>{`${hourLabel(i)} UTC · ${b} ${b === 1 ? 'story' : 'stories'}`}</title>
          </rect>
        </svg>
      ))}
    </span>
  );
};

// Impact score tooltip: formula + this cluster's component contributions.
// Prefers server-provided impact_components (news_clusters, qr_etl
// t_1f96bc9b); falls back to deriving coverage/recency from the documented
// digest formula and keyword impact as the arithmetic residual (marked ≈).
const impactTitle = (c) => {
  const s = c.impact_score;
  if (s == null) return 'impact score: n/a';
  const comp = c.impact_components;
  if (comp) {
    return `impact ${s}/100 = attention ${comp.attention ?? '—'} + coverage ${comp.coverage ?? '—'} + recency ${comp.recency ?? '—'} + LLM impact ${comp.llm_impact ?? '—'}`;
  }
  // digest formula (backend/app/routes/macro.py):
  // score = round(100 * (0.45*min(coverage/6,1) + 0.35*recency + 0.20*min(keywords/6,1)))
  const covPts = Math.round(45 * Math.min((c.story_count ?? 0) / 6, 1));
  const ageH = ageHours(c.last_seen_utc || c.first_seen_utc);
  const recPts = ageH == null ? 0 : Math.round(35 * Math.max(0, 1 - ageH / 72));
  const kwPts = s - covPts - recPts; // residual incl. rounding/time drift
  return `impact ${s}/100 ≈ coverage ${covPts} + recency ${recPts} + keywords ≈${kwPts} · formula 0.45·coverage + 0.35·recency + 0.20·keyword-impact (exact per-cluster components land with news_clusters)`;
};

// --- Portfolio-awareness layer (2026-08-12) --------------------------------
// "Does this matter to me": join cluster.tickers[] against current positions
// (/api/portfolio/positions, ACTIVE rows netted per ticker) and the watchlist
// (/api/watchlist — endpoint pending qr_etl t_03bdbbfa; degrades to
// positions-only). Per-ticker delta since the story broke comes from
// /api/market/delta-since (same task); chips render delta-less until then.
// NOTE: news_clusters tickers[] is currently phrase-junk upstream ('US
// stocks', 'Wall Street') — being fixed in t_03bdbbfa; until then the join
// legitimately finds few hits. No mapping is invented client-side.

const buildBook = (positions) => {
  const book = {};
  for (const r of positions || []) {
    if (r.status !== 'ACTIVE' || !r.ticker) continue;
    const q = (r.side === 'SHORT' ? -1 : 1) * (r.quantity ?? 0);
    const b = (book[r.ticker] = book[r.ticker] || { qty: 0, mv: 0 });
    b.qty += q;
    b.mv += r.market_value ?? 0;
  }
  for (const b of Object.values(book)) {
    b.side = b.qty > 0 ? 'LONG' : b.qty < 0 ? 'SHORT' : 'FLAT';
    b.qty = Math.abs(b.qty);
  }
  return book;
};

// Clusters ∩ (positions ∪ watchlist); held positions carry size+direction.
const bookHits = (c, book, watch) => {
  const hits = [];
  for (const t of c.tickers || []) {
    if (book[t] && book[t].side !== 'FLAT') hits.push({ ticker: t, ...book[t], held: true });
    else if (watch.has(t)) hits.push({ ticker: t, held: false });
  }
  return hits;
};

// Delta cache key: ticker + the hour the story broke (first_seen_utc).
const deltaKey = (t, firstSeen) => `${t}|${(firstSeen || '').slice(0, 13)}`;

const HeldChip = ({ h }) => (
  <span
    className="rounded border border-white/15 bg-white/[0.04] px-1.5 py-px text-[8px] font-mono text-slate-200 whitespace-nowrap"
    title={h.held ? `held position · net ${h.side} ${h.qty} shares · ${fmtK(h.mv)} market value` : 'on watchlist (no position)'}
  >
    {h.held ? `held ${h.ticker} ${h.side} ${h.qty}sh · ${fmtK(h.mv)}` : `watch ${h.ticker}`}
  </span>
);

// Ticker chip with price delta since cluster first_seen_utc, coloured by
// sign (emerald/rose signed values). No delta endpoint yet → plain chip.
const TickerChip = ({ t, delta }) => {
  if (delta && delta.pct != null) {
    const p = Number(delta.pct);
    return (
      <span
        className={`rounded bg-white/[0.05] px-1.5 py-px text-[8px] font-mono whitespace-nowrap ${signedCl(p)}`}
        title={`${t} ${p >= 0 ? '+' : ''}${p.toFixed(1)}% since story broke · ${delta.source === 'daily' ? 'daily-close fallback (intraday bars stale)' : 'intraday bars'} · ref ${delta.ref_px} @ ${String(delta.ref_ts || '').slice(0, 16)} → last ${delta.last_px} @ ${String(delta.last_ts || '').slice(0, 16)}`}
      >
        {t} {p >= 0 ? '+' : ''}{p.toFixed(1)}%
      </span>
    );
  }
  return (
    <span title={`${t} — no delta for this story window (ticker unresolved or no bars at/after first_seen)`}>
      <Chip label={t} />
    </span>
  );
};

// --- Filter panels (2026-08-12): attention timeline + driver×asset matrix --
// Both panels are FILTER CONTROLS over the feed, not decoration. They consume
// the language-filtered, deduped feed so panel distributions always match
// what the feed can show. Mean tone is derived per cluster from
// llm_direction (bullish=+1, bearish=-1, else 0) — no numeric tone field
// exists on news_clusters; missing direction counts as neutral.
const DRIVERS = ['Oil & Energy', 'Fed & Rates', 'Inflation & CPI', 'China & HK', 'Earnings', 'FX & Currency'];
const MATRIX_ASSETS = ['US', 'HK', 'CRYPTO', 'FX', 'METAL'];

const toneOf = (c) => {
  const d = (c.llm_direction || '').toLowerCase();
  return d.startsWith('bull') ? 1 : d.startsWith('bear') ? -1 : 0;
};

// Cell/bar fill: teal (bullish) / coral-rose (bearish), alpha scaled by
// |mean tone|; zero-count buckets render NEUTRAL (visible slate), never blank.
const toneStyle = (mean, n) => {
  if (!n) return { backgroundColor: 'rgba(100,116,139,0.10)' };
  const a = 0.12 + 0.5 * Math.min(Math.abs(mean), 1);
  if (mean > 0.05) return { backgroundColor: `rgba(45,212,191,${a})` };
  if (mean < -0.05) return { backgroundColor: `rgba(251,113,133,${a})` };
  return { backgroundColor: 'rgba(100,116,139,0.22)' };
};

const MONTH_IDX = { jan: 0, feb: 1, mar: 2, apr: 3, may: 4, jun: 5, jul: 6, aug: 7, sep: 8, oct: 9, nov: 10, dec: 11 };
const MONTH_SHORT = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
// Catalyst dates: ISO when the calendar endpoint lands; the existing
// macro/regions events use year-less 'Aug 14' — infer the nearest year
// (±200d rollover) so real rows still render.
const parseEventDate = (s) => {
  if (!s) return null;
  if (/^\d{4}-\d{2}-\d{2}/.test(s)) return parseUtc(s);
  const m = String(s).match(/([A-Za-z]{3})\w*\s+(\d{1,2})/);
  if (!m) return null;
  const mo = MONTH_IDX[m[1].slice(0, 3).toLowerCase()];
  if (mo == null) return null;
  const now = Date.now();
  let t = Date.UTC(new Date(now).getUTCFullYear(), mo, +m[2]);
  if (t < now - 200 * 86400000) t = Date.UTC(new Date(now).getUTCFullYear() + 1, mo, +m[2]);
  else if (t > now + 200 * 86400000) t = Date.UTC(new Date(now).getUTCFullYear() - 1, mo, +m[2]);
  return t;
};
const dayLabel = (t) => `${MONTH_SHORT[new Date(t).getUTCMonth()]} ${new Date(t).getUTCDate()}`;
const fmtTone = (m) => `${m > 0 ? '+' : ''}${m.toFixed(2)}`;

// --- Absent-data vs measured-neutral (2026-08-12) ---------------------------
// No panel may render a data gap as a meaningful zero. UNSCORED/NO DATA get
// a diagonal hatch (or outline), MEASURED NEUTRAL keeps the solid slate fill.
const HATCH = { backgroundImage: 'repeating-linear-gradient(45deg, rgba(100,116,139,0.18) 0 2px, transparent 2px 5px)' };
const hasDirection = (c) => !!(c.llm_direction || '').trim();

// Provenance badge: which parts of the page can be trusted at a glance.
// LIVE = serving from the purpose-built table/endpoint · FALLBACK = derived
// from the legacy digest · PENDING = upstream task outstanding (named in tip).
const ProvBadge = ({ state, tip }) => {
  const cl = state === 'LIVE'
    ? 'text-teal-400 border-teal-400/30'
    : state === 'PENDING'
    ? 'text-rose-400 border-rose-400/30'
    : 'text-slate-500 border-white/10';
  return (
    <span className={`rounded border px-1 py-px text-[7px] font-mono ${cl}`} title={tip}>
      {state}
    </span>
  );
};

// Panel A — attention timeline. 7D view: 7 daily buckets spanning D-4..D+2
// (today at index 4) so scheduled catalysts sit on the FORWARD portion of
// the axis with days-until labels; past catalysts stay on their day so the
// attention spike they caused is visible. 24H view: 4h buckets, same idea.
// Click a bar to filter the feed to stories that broke in that bucket.
const AttentionTimeline = ({ feed, catalysts, mode, onMode, active, onSelect, live }) => {
  const now = Date.now();
  const is7d = mode === '7d';
  const DAY = 86400000;
  // Real coverage start: buckets entirely before the earliest news_clusters
  // row are NO DATA (hatched, zero height) — never a zero-volume bar.
  const earliest = feed.reduce((m, c) => {
    const t = parseUtc(c.first_seen_utc);
    return t != null && (m == null || t < m) ? t : m;
  }, null);
  const buckets = [];
  if (is7d) {
    const today0 = Date.UTC(new Date(now).getUTCFullYear(), new Date(now).getUTCMonth(), new Date(now).getUTCDate());
    for (let i = -4; i <= 2; i++) buckets.push({ start: today0 + i * DAY, end: today0 + (i + 1) * DAY, label: dayLabel(today0 + i * DAY) });
  } else {
    const q = 4 * 3600000;
    const cur0 = Math.floor(now / q) * q;
    for (let i = -5; i <= 0; i++) buckets.push({ start: cur0 + i * q, end: cur0 + (i + 1) * q, label: `${String(new Date(cur0 + i * q).getUTCHours()).padStart(2, '0')}h` });
    buckets.push({ start: cur0 + q, end: cur0 + 2 * q, label: `${String(new Date(cur0 + q).getUTCHours()).padStart(2, '0')}h` });
  }
  const stats = buckets.map((b) => {
    const inB = feed.filter((c) => { const t = parseUtc(c.first_seen_utc); return t != null && t >= b.start && t < b.end; });
    const scored = inB.filter(hasDirection);
    const stories = inB.reduce((s, c) => s + (c.story_count ?? 1), 0);
    // Mean tone over SCORED clusters only; unscored ones are not neutral votes.
    const mean = scored.length ? scored.reduce((s, c) => s + toneOf(c), 0) / scored.length : 0;
    const noData = earliest != null && b.end <= earliest;
    return { ...b, n: inB.length, scored: scored.length, stories, mean, noData };
  });
  const maxN = Math.max(...stats.map((s) => s.n), 1);
  const cats = (catalysts || [])
    .map((e) => ({ ...e, ts: parseEventDate(e.date) }))
    .filter((e) => e.ts != null)
    .sort((a, b) => a.ts - b.ts);
  const inWindow = (b, ts) => ts >= b.start && ts < b.end;
  const upcoming = cats.filter((e) => e.ts >= now).slice(0, 3);
  const isActive = (b) => active?.type === 'time' && active.start === b.start;
  return (
    <div className="qr-surface px-3 py-2">
      <div className="flex items-baseline justify-between mb-1">
        <div className="qr-label flex items-center gap-1.5">
          Attention · {is7d ? '7 days' : '24 hours'}
          <ProvBadge state={live ? 'LIVE' : 'FALLBACK'} tip={live ? 'consumption.news_clusters via /api/news/clusters' : 'silver.historical_news via /api/news/digest (token-Jaccard fallback)'} />
        </div>
        <div className="flex items-center gap-1">
          {[['7d', '7D'], ['24h', '24H']].map(([v, lbl]) => (
            <button
              key={v}
              onClick={() => onMode(v)}
              className={`rounded border px-1.5 py-px text-[8px] font-mono ${mode === v ? 'border-white/25 bg-white/[0.06] text-white' : 'border-white/10 text-slate-500 hover:text-slate-300'}`}
            >
              {lbl}
            </button>
          ))}
        </div>
      </div>
      <div className="flex items-end gap-1 h-11">
        {stats.map((b) => {
          const bCats = cats.filter((e) => inWindow(b, e.ts));
          if (b.noData) {
            return (
              <div
                key={b.start}
                className="flex-1 flex flex-col items-center justify-end gap-px cursor-not-allowed"
                title={`${b.label} · NO DATA — news_clusters coverage begins ${earliest ? dayLabel(earliest) : '—'}; a gap, not zero volume`}
              >
                <span className="h-2" />
                <span className="w-full rounded-none" style={{ height: '3px', ...HATCH }} />
                <span className="text-[7px] font-mono text-slate-700">{b.label}</span>
              </div>
            );
          }
          return (
            <button
              key={b.start}
              onClick={() => onSelect(isActive(b) ? null : { type: 'time', start: b.start, end: b.end, label: b.label, n: b.n })}
              className={`flex-1 flex flex-col items-center justify-end gap-px group/bar ${isActive(b) ? 'outline outline-1 outline-white/30 rounded-sm' : ''}`}
              title={`${b.label} · ${b.n} clusters, ${b.scored} scored · ${b.stories} stories · mean tone ${fmtTone(b.mean)} over scored only${b.n ? ' · click to filter feed' : ' · no clusters this bucket (measured)'}`}
            >
              <span className="flex gap-px h-2 items-center">
                {bCats.map((e, i) => (
                  <span
                    key={i}
                    className={`text-[8px] leading-none ${e.ts >= now ? 'text-white' : 'text-slate-500'}`}
                    title={`${e.event} · ${dayLabel(e.ts)}${e.ts >= now ? ` · in ${Math.ceil((e.ts - now) / DAY)}d` : ' · past'}${e.importance ? ` · ${e.importance}` : ''}${e.region ? ` · ${e.region}` : ''}`}
                  >
                    ◆{e.ts >= now && <span className="text-[7px] text-slate-400">{Math.ceil((e.ts - now) / DAY)}d</span>}
                  </span>
                ))}
              </span>
              <span
                className="w-full rounded-none"
                style={{ height: `${Math.max((b.n / maxN) * 28, b.n ? 2 : 1)}px`, ...toneStyle(b.mean, b.scored) }}
              />
              <span className={`text-[7px] font-mono ${b.start <= now && now < b.end ? 'text-slate-300' : 'text-slate-600'}`}>
                {b.label}{b.start <= now && now < b.end ? '·now' : ''}
              </span>
            </button>
          );
        })}
      </div>
      <div className="text-[7px] font-mono text-slate-600 mt-0.5 truncate" title={upcoming.map((e) => `${e.event} ${dayLabel(e.ts)}`).join(' · ')}>
        {earliest != null && <span className="text-slate-500">coverage begins {dayLabel(earliest)} · </span>}
        {upcoming.length
          ? `next: ${upcoming.map((e) => `${e.event} in ${Math.max(Math.ceil((e.ts - now) / DAY), 0)}d (${dayLabel(e.ts)})`).join(' · ')}`
          : 'no scheduled catalysts on file — global calendar pending qr_etl t_7a646947'}
      </div>
    </div>
  );
};

// Panel B — driver × asset-class matrix. Three cell states: MEASURED (tone
// fill from scored clusters), MEASURED NEUTRAL (solid slate, scored but
// balanced), UNSCORED (hatched, no fill — >50% of the cell's clusters lack
// llm_direction, or the cell is empty). Mean tone is computed over SCORED
// clusters only; tooltips state coverage explicitly. Click = filter feed.
const DriverMatrix = ({ feed, labels, active, onSelect, live }) => {
  const cell = (driver, asset) => {
    const rows = feed.filter((c) => (c.driver_tags || []).includes(driver) && c.asset_class === asset);
    const scored = rows.filter(hasDirection);
    const mean = scored.length ? scored.reduce((s, c) => s + toneOf(c), 0) / scored.length : 0;
    const unscored = rows.length === 0 || scored.length / rows.length <= 0.5;
    return { n: rows.length, k: scored.length, mean, unscored };
  };
  const isActive = (d, a) => active?.type === 'cell' && active.driver === d && active.asset === a;
  const scoredTotal = feed.filter(hasDirection).length;
  const covPct = feed.length ? Math.round((100 * scoredTotal) / feed.length) : 0;
  return (
    <div className="qr-surface px-3 py-2">
      <div className="qr-label mb-1 flex items-center gap-1.5 flex-wrap">
        Driver × asset
        <ProvBadge state={live ? 'LIVE' : 'FALLBACK'} tip={live ? 'consumption.news_clusters via /api/news/clusters' : 'silver.historical_news via /api/news/digest (token-Jaccard fallback)'} />
        <span
          className="text-[9px] font-mono font-bold text-slate-200 normal-case"
          title="clusters carrying an LLM direction assessment out of all clusters in the window; unscored clusters are excluded from mean tone"
        >
          LLM direction on {scoredTotal} of {feed.length} clusters ({covPct}%)
        </span>
      </div>
      <div className="space-y-px">
        <div className="flex gap-px items-center">
          <span className="w-[86px] shrink-0" />
          {MATRIX_ASSETS.map((a) => (
            <span key={a} className="flex-1 text-center text-[7px] font-mono text-slate-500 truncate">{labels?.[a] || a}</span>
          ))}
        </div>
        {DRIVERS.map((d) => (
          <div key={d} className="flex gap-px items-center">
            <span className="w-[86px] shrink-0 text-[7px] font-mono text-slate-400 truncate">{d}</span>
            {MATRIX_ASSETS.map((a) => {
              const { n, k, mean, unscored } = cell(d, a);
              return (
                <button
                  key={a}
                  onClick={() => onSelect(isActive(d, a) ? null : { type: 'cell', driver: d, asset: a, label: `${d} × ${labels?.[a] || a}`, n })}
                  className={`flex-1 h-[13px] rounded-none text-[7px] font-mono ${n && !unscored ? 'text-white/80' : 'text-slate-600'} ${isActive(d, a) ? 'outline outline-1 outline-white/40' : ''}`}
                  style={unscored ? HATCH : toneStyle(mean, k)}
                  title={n === 0
                    ? `${d} × ${labels?.[a] || a} — no clusters (unscored, not neutral)`
                    : unscored
                    ? `${d} × ${labels?.[a] || a} — ${n} clusters, ${k} scored — UNSCORED (>50% lack LLM direction); tone not measured`
                    : `${d} × ${labels?.[a] || a} — ${n} clusters, ${k} scored, mean tone ${fmtTone(mean)} over scored only · click to filter feed`}
                >
                  {unscored ? (n ? '—' : '') : n || ''}
                </button>
              );
            })}
          </div>
        ))}
      </div>
    </div>
  );
};

// --- LLM signal reliability (2026-08-12) -----------------------------------
// Accountability strip for the LLM impact layer: does llm_direction predict
// forward returns? Data: GET /api/news/signal-performance (table
// consumption.news_signal_performance, job pending qr_etl t_03fc7ddb).
// Any metric with n < MIN_N is greyed out — small samples are noise.
const MIN_N = 30;
// hit_rate may arrive as 0-1 or 0-100 depending on the writer — normalize.
const pctNorm = (v) => (v == null ? null : Number(v) > 1 ? Number(v) : Number(v) * 100);

const MetricTile = ({ label, value, n, title, valueCl }) => {
  const dim = n == null || n < MIN_N;
  return (
    <span
      className="inline-flex items-baseline gap-1"
      title={`${title} · n=${n ?? '—'}${dim ? ' · n<30 — insufficient sample, treat as noise' : ''}`}
    >
      <span className="text-[8px] font-mono text-slate-500 uppercase">{label}</span>
      <span className={`text-[11px] font-mono font-bold ${dim ? 'text-slate-600' : valueCl || 'text-white'}`}>
        {value ?? '—'}
      </span>
    </span>
  );
};

const ReliabilityPanel = ({ perf }) => {
  const [open, setOpen] = useState(false);
  if (!perf) {
    return (
      <div className="qr-surface px-3 py-2 text-[9px] font-mono text-slate-600 flex items-center gap-x-2">
        <span className="uppercase">LLM signal reliability</span>
        <ProvBadge state="PENDING" tip="consumption.news_signal_performance via /api/news/signal-performance — measurement job outstanding" />
        measurement job pending (qr_etl t_03fc7ddb): forward returns at +1h/+1d/+5d
        joined against llm_direction; hit rate, information coefficient, and ticker coverage land here.
      </div>
    );
  }
  const w30 = perf.windows?.['30d']?.by_horizon?.['1d'];
  const w90 = perf.windows?.['90d']?.by_horizon?.['1d'];
  const cov = perf.windows?.['30d']?.coverage;
  const hr = pctNorm(w30?.hit_rate);
  const ic = w90?.information_coefficient ?? w90?.ic;
  const covPct = pctNorm(cov?.pct);
  const buckets = [...(perf.by_confidence_bucket || [])]
    .filter((b) => b.horizon === '1d' || !b.horizon)
    .sort((a, b) => String(a.bucket).localeCompare(String(b.bucket)));
  return (
    <div className="qr-surface px-3 py-2">
      <div className="flex flex-wrap items-center gap-x-4 gap-y-1">
        <span className="text-[8px] font-mono text-slate-500 uppercase" title={perf.computed_at ? `computed ${perf.computed_at}` : undefined}>
          Signal reliability
        </span>
        <ProvBadge state="LIVE" tip="consumption.news_signal_performance via /api/news/signal-performance" />
        <MetricTile
          label="hit 1d" n={w30?.sample_size ?? w30?.n}
          value={hr != null ? `${hr.toFixed(0)}%` : null}
          valueCl={hr == null ? undefined : signedCl(hr - 50)}
          title="30d window · +1d forward return · hit = sign(fwd return) matches llm_direction · 50% = coin flip"
        />
        <MetricTile
          label="IC 90d" n={w90?.sample_size ?? w90?.n}
          value={ic != null ? `${ic > 0 ? '+' : ''}${Number(ic).toFixed(2)}` : null}
          valueCl={ic == null ? undefined : signedCl(ic)}
          title="90d information coefficient · Spearman corr of signed direction × confidence vs +1d forward return · 0 = no predictive power"
        />
        <MetricTile
          label="coverage" n={cov?.n ?? cov?.sample_size}
          value={covPct != null ? `${covPct.toFixed(0)}%` : null}
          title="30d window · % of clusters with a resolvable primary ticker (exposes ticker-extraction quality, t_03bdbbfa)"
        />
        <button
          onClick={() => setOpen((v) => !v)}
          className="ml-auto rounded border border-white/10 px-1.5 py-px text-[8px] font-mono text-slate-500 hover:text-slate-300"
        >
          {open ? '▾ hide breakdown' : '▸ by confidence'}
        </button>
      </div>
      {open && (
        <div className="mt-1.5 space-y-0.5">
          <div className="text-[8px] font-mono text-slate-600">
            hit rate (30d, +1d fwd) by confidence bucket — if high-conf doesn't beat low-conf, the confidence output needs recalibration. Line marks 50% (coin flip).
          </div>
          {buckets.length === 0 ? (
            <div className="text-[9px] font-mono text-slate-600 py-1">No bucket breakdown in the response yet.</div>
          ) : buckets.map((b) => {
            const n = b.sample_size ?? b.n;
            const pct = pctNorm(b.hit_rate);
            const dim = n == null || n < MIN_N;
            return (
              <div key={b.bucket} className="flex items-center gap-2" title={`conf ${b.bucket} · hit rate ${pct != null ? `${pct.toFixed(1)}%` : '—'} · n=${n ?? '—'}${dim ? ' · n<30 — insufficient sample' : ''}`}>
                <span className="w-14 shrink-0 text-[8px] font-mono text-slate-400 text-right">{b.bucket}</span>
                <div className="relative flex-1 h-2 bg-white/[0.04] rounded-none">
                  <div className="absolute inset-y-0 left-1/2 w-px bg-slate-500/70" />
                  {pct != null && (
                    <div
                      className="h-full rounded-none"
                      style={{ width: `${Math.min(pct, 100)}%`, backgroundColor: dim ? 'rgba(100,116,139,0.25)' : pct >= 50 ? 'rgba(45,212,191,0.45)' : 'rgba(251,113,133,0.45)' }}
                    />
                  )}
                </div>
                <span className={`w-16 shrink-0 text-[8px] font-mono ${dim ? 'text-slate-600' : 'text-slate-300'}`}>
                  {pct != null ? `${pct.toFixed(0)}%` : '—'} · n={n ?? '—'}
                </span>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
// llm = joined /api/news/outlook cluster row (bias/confidence/rationale).
const digestToCluster = (s, cat, llm) => ({
  cluster_id: s.cluster_key || normH(s.headline),
  canonical_headline: s.headline,
  story_count: s.n_sources ?? 1,
  outlet_count: (s.sources || []).length || s.n_sources || 1,
  first_seen_utc: s.published_at,
  last_seen_utc: s.published_at,
  asset_class: cat,
  lang: s.lang || null,
  driver_tags: s.drivers || [],
  tickers: [],
  llm_direction: llm?.bias || null,
  llm_confidence: llm?.confidence ?? null,
  llm_rationale: llm?.rationale || null,
  impact_score: s.score ?? 0,
  members: (s.sources || []).map((o) => ({ outlet: o, published_at: s.published_at, url: null })),
  _fallback: true,
});

// Expanded state: LLM rationale + members grouped by outlet with timestamps
// and links. Member headlines equal to the canonical headline are NOT
// re-printed (no-headline-twice invariant); only outlet/time/link show.
const ClusterExpansion = ({ c }) => {
  const byOutlet = {};
  for (const m of c.members || []) {
    const o = m.outlet || 'unknown outlet';
    (byOutlet[o] = byOutlet[o] || []).push(m);
  }
  const outlets = Object.entries(byOutlet).sort((a, b) => b[1].length - a[1].length);
  const canonical = normH(c.canonical_headline);
  return (
    <div className="mt-1.5 ml-9 border-l rounded-none border-white/[0.06] pl-3 pb-1">
      {c.event_group && (c.event_group.related || []).length > 0 && (
        <div className="mb-1.5">
          <div className="text-[8px] font-mono uppercase text-slate-500 mb-0.5">
            Related angles — {c.event_group.event} ({c.event_group.event_date})
          </div>
          <div className="space-y-0.5">
            {(c.event_group.related || []).map((r) => (
              <div key={r.cluster_id} className="text-[9px] text-slate-500 flex flex-wrap items-center gap-x-2 gap-y-0.5 pl-2">
                <span className="font-mono text-slate-400" title="impact score of the collapsed angle row">{r.impact_score ?? '—'}</span>
                <span className="text-slate-400">{r.canonical_headline}</span>
                <span className="font-mono text-slate-600">{r.story_count ?? '—'} stories</span>
                <AgeDot ts={r.last_seen_utc || r.first_seen_utc} />
              </div>
            ))}
          </div>
        </div>
      )}
      {c.llm_rationale && (
        <div className="text-[9px] text-slate-400 leading-snug mb-1.5">
          <span className="text-slate-500 uppercase font-mono text-[8px]">LLM rationale: </span>
          {c.llm_rationale}
        </div>
      )}
      {outlets.length === 0 ? (
        <div className="text-[9px] text-slate-600">No member detail available.</div>
      ) : (
        <div className="space-y-1">
          {outlets.map(([outlet, ms]) => (
            <div key={outlet}>
              <div className="text-[9px] font-mono text-slate-300">{outlet}</div>
              {ms.map((m, i) => {
                const showHeadline = m.headline && normH(m.headline) !== canonical;
                return (
                  <div key={i} className="text-[9px] text-slate-500 flex flex-wrap items-center gap-x-2 gap-y-0.5 pl-2">
                    {showHeadline && <span className="text-slate-400">{m.headline}</span>}
                    <AgeDot ts={m.published_at} />
                    {m.url ? (
                      <a href={m.url} target="_blank" rel="noreferrer" className="text-blue-400 hover:underline font-mono">
                        link ↗
                      </a>
                    ) : (
                      <span className="font-mono text-slate-600" title="Member links land with the news_clusters table (qr_etl t_d492325f)">no link yet</span>
                    )}
                  </div>
                );
              })}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

const ClusterRow = ({ c, labels, expanded, onToggle, hits = [], deltas = {}, tier = 'LOW', rankTip }) => {
  const border = TIER_BORDER[tier]?.[dirKeyOf(c.llm_direction)] || null;
  const tickers = (c.tickers || []).slice(0, 4);
  const seenTs = c.last_seen_utc || c.first_seen_utc;
  const held = hits.some((h) => h.held);
  return (
    <div
      className={`group py-1.5 cursor-pointer select-none ${border ? `border-l-[3px] rounded-none pl-2.5 ${border}` : ''} ${held ? 'shadow-[inset_0_0_0_1px_rgba(255,255,255,0.10)] bg-white/[0.015]' : ''}`}
      onClick={onToggle}
    >
      <div className="flex items-start gap-2.5">
        <span
          className={`font-mono text-base leading-snug w-7 text-right shrink-0 ${TIER_SCORE_CL[tier]}`}
          title={`${rankTip ? `${rankTip} · ` : ''}${impactTitle(c)}`}
        >
          {c.impact_score ?? '—'}
        </span>
        <div className="flex-1 min-w-0">
          <div className={`${TIER_HEAD_CL[tier]} leading-snug`}>
            {c.canonical_headline}
          </div>
          {tier === 'LOW' ? (
            <div className="text-[9px] text-slate-600 mt-0.5 flex items-center gap-x-2">
              <span className="font-mono inline-flex items-center gap-x-1.5">
                {c.story_count ?? '—'} stories · <AgeDot ts={seenTs} />
              </span>
              {hits.map((h) => <HeldChip key={h.ticker} h={h} />)}
              <EventGroupChip eg={c.event_group} />
              <StalePill ts={seenTs} />
              <span className="font-mono text-slate-700">{expanded ? '▾' : '▸'}</span>
            </div>
          ) : (
            <div className="text-[9px] text-slate-500 mt-0.5 flex flex-wrap items-center gap-x-2 gap-y-0.5">
              <span className="font-mono inline-flex items-center gap-x-1.5">
                <AgeDot ts={c.first_seen_utc} />
                {c.story_count ?? '—'} stories · {c.outlet_count ?? '—'} outlets · first seen {fmtHHMM(c.first_seen_utc)}
              </span>
              <StalePill ts={seenTs} />
              {hits.map((h) => <HeldChip key={h.ticker} h={h} />)}
              {c.llm_direction && (
                <span className={`font-mono uppercase inline-flex items-center gap-x-1 ${dirCl(c.llm_direction)}`}>
                  {c.llm_direction}
                  <ConfPips conf={c.llm_confidence} />
                </span>
              )}
              <AssetBadge cat={c.asset_class} labels={labels} />
              <EventGroupChip eg={c.event_group} />
              {c.lang && c.lang !== 'en' && <Chip label={c.lang.toUpperCase()} />}
              {(c.driver_tags || []).slice(0, 4).map((d) => <Chip key={d} label={d} />)}
              {/* MEDIUM: ticker chips hidden until hover/expand; HIGH: always visible */}
              {tickers.length > 0 && (
                <span className={tier === 'MEDIUM' && !expanded ? 'opacity-0 group-hover:opacity-100 transition-opacity inline-flex gap-1' : 'inline-flex gap-1'}>
                  {tickers.map((t) => <TickerChip key={t} t={t} delta={deltas[deltaKey(t, c.first_seen_utc)]} />)}
                </span>
              )}
              <span className="font-mono text-slate-600">{expanded ? '▾ less' : '▸ more'}</span>
            </div>
          )}
        </div>
        {/* 24h attention micro-chart — renders only with real per-member
            timestamps (news_clusters); null in the digest fallback */}
        <AttentionChart members={c.members} />
      </div>
      {expanded && <ClusterExpansion c={c} />}
    </div>
  );
};

export const NewsTab = () => {
  const [clusters, setClusters] = useState(null);   // null = loading
  const [labels, setLabels] = useState({});
  const [digest, setDigest] = useState(null);
  const [outlookData, setOutlookData] = useState(null);
  const [live, setLive] = useState(false);          // true once /api/news/clusters serves real rows
  const [asOf, setAsOf] = useState(null);
  // t_4b664a1a: top-level llm_coverage block from /api/news/clusters (live
  // path only) — explains the direction-scoring rule next to the feed.
  const [coverage, setCoverage] = useState(null);
  const [loading, setLoading] = useState(true);
  const [expanded, setExpanded] = useState({});     // cluster_id -> bool
  const [showAll, setShowAll] = useState(false);    // feed capped at FEED_CAP rows by default
  const [book, setBook] = useState({});             // ticker -> {side, qty, mv} (netted ACTIVE positions)
  const [watchlist, setWatchlist] = useState(new Set()); // /api/watchlist pending qr_etl t_03bdbbfa
  const [deltas, setDeltas] = useState({});         // deltaKey -> delta payload | null (attempted)
  const deltasRef = useRef({});
  const [myBookOnly, setMyBookOnly] = useState(() => localStorage.getItem('news.myBookOnly') === '1');
  const pickBook = (v) => { setMyBookOnly(v); localStorage.setItem('news.myBookOnly', v ? '1' : '0'); };
  const [catalysts, setCatalysts] = useState([]);   // macro calendar events (HK rows now; global pending t_7a646947)
  const [tlMode, setTlMode] = useState('7d');       // attention timeline granularity
  const [panelFilter, setPanelFilter] = useState(null); // {type:'time'|'cell', ...} | null
  const [perf, setPerf] = useState(null);           // /api/news/signal-performance (pending qr_etl t_03fc7ddb)
  const [readableOnly, setReadableOnly] = useState(() => localStorage.getItem('news.readableOnly') !== '0');
  const pickLang = (v) => { setReadableOnly(v); localStorage.setItem('news.readableOnly', v ? '1' : '0'); };

  // Named so the language toggle can force an immediate server re-query
  // (usePoll alone only re-fires on its interval / visibility change).
  const fetchNews = async () => {
    const langs = readableOnly ? '&langs=en,zh' : '';
    // 168h window: the attention timeline needs 7 days of clusters; the feed
    // is impact-sorted and stale-pilled, so the wider window is safe.
    const [cl, dg, out, pos, wl, cal, regs, sp] = await Promise.all([
      api.get(`/api/news/clusters?hours=168&limit=400${langs}`),
      api.get(`/api/news/digest?per_group=120&key_limit=8${langs}`),
      api.get('/api/news/outlook'),
      api.get('/api/portfolio/positions'),
      api.get('/api/watchlist'),
      api.get('/api/macro/calendar?days_past=90&days_fwd=60'),
      api.get('/api/macro/regions'),
      api.get('/api/news/signal-performance'),
    ]);
    if (dg && dg.categories) { setDigest(dg); setLabels(dg.labels || {}); }
    if (out && out.data) setOutlookData(out.data);
    const posRows = Array.isArray(pos) ? pos : (pos?.positions || pos?.data || []);
    setBook(buildBook(posRows));
    const wlRows = Array.isArray(wl) ? wl : (wl?.tickers || wl?.data || []);
    setWatchlist(new Set(wlRows.map((x) => (typeof x === 'string' ? x : x?.ticker)).filter(Boolean)));
    // Catalysts: prefer the dedicated calendar endpoint (pending qr_etl
    // t_7a646947); fall back to the real HK rows nested in /api/macro/regions.
    const calRows = cal?.events || [];
    if (calRows.length) {
      setCatalysts(calRows);
    } else {
      const regRows = Array.isArray(regs) ? regs : (regs?.data || []);
      setCatalysts(regRows.flatMap((r) => (r.events || []).map((e) => ({ ...e, region: r.key }))));
    }
    // Signal reliability: only accept a payload that actually has windows.
    setPerf(sp && sp.windows ? sp : null);

    if (cl && Array.isArray(cl.clusters) && cl.clusters.length > 0) {
      // t_3bfe7f78: exact (asset_class, cluster_id) join against the outlook
      // cluster map fills llm_* on rows the ETL stamp (qr_etl t_9a746bb9)
      // hasn't reached yet. Server-stamped rows always win; the join never
      // overwrites them. Live fill rate measured 2026-08-12: +5/115 rows.
      const outCls = out?.data?.clusters || {};
      const filled = cl.clusters.map((c) => {
        if ((c.llm_direction || '').trim()) return c;
        const hit = c.cluster_id ? outCls[c.asset_class]?.[c.cluster_id] : null;
        if (!hit) return c;
        return {
          ...c,
          llm_direction: hit.bias || null,
          llm_confidence: hit.confidence ?? null,
          llm_rationale: hit.rationale || null,
        };
      });
      setClusters(filled);
      setLive(true);
      setAsOf(cl.as_of || null);
      setCoverage(cl.llm_coverage || null);
      if (cl.labels) setLabels(cl.labels);
    } else if (dg && dg.categories) {
      // Fallback: derive the cluster feed from the digest. The outlook key
      // space is embedding cluster_id now, so the digest token-Jaccard
      // cluster_key can never join (t_3bfe7f78) — only the verbatim-headline
      // fallback remains on this path.
      const llmClusters = out?.data?.clusters || {};
      const mapped = [];
      for (const [cat, payload] of Object.entries(dg.categories)) {
        const byKey = llmClusters[cat] || {};
        for (const s of payload.stories || []) {
          const llm = Object.values(byKey).find((v) => v.headline && v.headline === s.headline)
            || null;
          mapped.push(digestToCluster(s, cat, llm));
        }
      }
      setClusters(mapped);
      setLive(false);
      setAsOf(dg.as_of || null);
      setCoverage(null); // digest fallback has no llm_coverage block
    }
    setLoading(false);
  };
  usePoll(fetchNews, 300000); // 5 min — GDELT ingestion cadence is hourly-ish

  // Toggling EN/中文 <-> All re-queries the server immediately (acceptance:
  // the rendered story set must match the active ?langs= filter, not a stale
  // client-filtered one). Skip the first run — usePoll already fired on mount.
  const fetchRef = useRef(fetchNews);
  useEffect(() => { fetchRef.current = fetchNews; });
  const skipFirstLangRun = useRef(true);
  useEffect(() => {
    if (skipFirstLangRun.current) { skipFirstLangRun.current = false; return; }
    fetchRef.current();
  }, [readableOnly]);

  // Assemble the feed: language safety net, then the no-headline-twice
  // invariant (normalized canonical dedup, highest impact wins), then sort
  // by impact_score desc with NO asset_class filter — the feed itself is now
  // the cross-category top-stories view.
  const feed = (() => {
    const items = (clusters || []).filter((c) =>
      !readableOnly || (isReadable(c.canonical_headline) &&
        (c.members || []).every((m) => !m.headline || isReadable(m.headline))));
    const seen = new Set();
    const deduped = [];
    for (const c of [...items].sort((a, b) => (b.impact_score ?? 0) - (a.impact_score ?? 0))) {
      const k = normH(c.canonical_headline);
      if (!k || seen.has(k)) continue;
      seen.add(k);
      deduped.push(c);
    }
    return deduped;
  })();

  const outlooks = outlookData?.outlooks || {};
  const runDate = outlookData?.run_date || null;

  // Filter chain: language+dedup (feed) → panel filter (time bucket or
  // driver×asset cell) → My book only. Panels consume `feed` directly so
  // their distributions stay visible while a panel filter is active.
  const passesPanel = (c) => {
    if (!panelFilter) return true;
    if (panelFilter.type === 'time') {
      const t = parseUtc(c.first_seen_utc);
      return t != null && t >= panelFilter.start && t < panelFilter.end;
    }
    return (c.driver_tags || []).includes(panelFilter.driver) && c.asset_class === panelFilter.asset;
  };
  const hitsFor = (c) => bookHits(c, book, watchlist);
  const view = feed.filter(passesPanel).filter((c) => !myBookOnly || hitsFor(c).length > 0);
  const hiddenCount = (clusters || []).length - view.length;

  // Distribution-relative tiers over the CURRENTLY FILTERED window (view is
  // impact-sorted): top 10% HIGH with floor 3 / cap 6, next 30% MEDIUM,
  // remainder LOW. Absolute score display is unchanged — only visual tiering
  // is relative. Rank tooltip: "53 — 4th of 136, top 3%".
  const ordinal = (i) => (i % 100 >= 11 && i % 100 <= 13 ? `${i}th` : `${i}${['th', 'st', 'nd', 'rd'][Math.min(i % 10, 4)] || 'th'}`);
  const tierInfo = (() => {
    const n = view.length;
    const hi = Math.min(n, Math.max(3, Math.min(6, Math.round(n * 0.10))));
    const med = Math.round(n * 0.30);
    const m = {};
    view.forEach((c, i) => {
      const key = c.cluster_id || normH(c.canonical_headline);
      m[key] = {
        tier: i < hi ? 'HIGH' : i < hi + med ? 'MEDIUM' : 'LOW',
        rankTip: `${c.impact_score ?? '—'} — ${ordinal(i + 1)} of ${n}, top ${Math.max(1, Math.round(((i + 1) / n) * 100))}%`,
      };
    });
    return m;
  })();
  // INVARIANT (2026-08-13, do not break): the strip counts over EXACTLY the
  // set the feed renders (view = feed → panel filter → my-book filter) with
  // NO extra wall-clock window. bear.size must always equal the count of
  // distinct held tickers on bearish rows below — checked by ad-hoc
  // verification. The old 24h wall-clock gate let >24h held rows render with
  // chips while the strip excluded them (strip said 0/0 above a BEARISH held
  // row). Window mismatch, not a join-path bug: both read the same filled
  // clusters/llm_direction/bookHits.
  const exposure = (() => {
    const bear = new Set(); const bull = new Set();
    let scored = 0, unscored = 0;
    for (const c of view) {
      const heldHits = hitsFor(c).filter((h) => h.held);
      if (!heldHits.length) continue;
      const d = (c.llm_direction || '').toLowerCase();
      if (!d) { unscored += 1; continue; }
      scored += 1;
      for (const h of heldHits) {
        if (d.startsWith('bear')) bear.add(h.ticker);
        if (d.startsWith('bull')) bull.add(h.ticker);
      }
    }
    return { bear, bull, scored, unscored };
  })();
  // "0 bearish / 0 bullish" is only meaningful when clusters actually carry
  // symbols that join to the book. With junk/empty tickers the strip must say
  // UNAVAILABLE and name the blocker — a gap is not a signal.
  const joinableCount = view.filter((c) =>
    (c.tickers || []).some((t) => book[t] || watchlist.has(t))).length;
  // Third gap class: held clusters render in the feed but NONE carry an LLM
  // direction. A bare 0/0 would read as measured; it is a coverage gap in the
  // direction layer (news_outlook stamp/join), so render unavailable.
  const heldUnscored = exposure.scored === 0 && exposure.unscored > 0;
  // Second gap class: the 24h window is anchored to wall clock, so a stale
  // news_clusters table reads as 0/0. If NO cluster falls in the window,
  // render a stale-data state instead of measured-looking zeros.
  const inWindow24 = (clusters || []).filter((c) => {
    const t = parseUtc(c.last_seen_utc || c.first_seen_utc);
    return t != null && (Date.now() - t) / 3600000 <= 24;
  }).length;
  const newestClusterH = (clusters || []).reduce((m, c) => {
    const h = ageHours(c.last_seen_utc || c.first_seen_utc);
    return h != null && (m == null || h < m) ? h : m;
  }, null);

  // t_4b664a1a: coverage caption — EXPLAIN the scoring rule, not bare counts.
  // llm_coverage.description is the canonical text; live scored/cohort counts
  // are appended. A coverage_pct materially below target_pct is transient
  // scoring lag (stamps land at the next 2h build_news_clusters run) — the
  // phrasing must never read as an error state. last_run may be null (table
  // freshly created): degrade to the description only.
  const covLine = (() => {
    if (!coverage) return null;
    const parts = [coverage.description || 'LLM direction coverage'];
    const { scored, cohort_size, coverage_pct, target_pct } = coverage;
    if (Number.isFinite(scored) && Number.isFinite(cohort_size) && cohort_size > 0) {
      parts.push(`${scored}/${cohort_size} scored`);
    }
    if (Number.isFinite(coverage_pct) && Number.isFinite(target_pct) && coverage_pct < target_pct - 5) {
      parts.push('below target — transient, top-up lands on the next 2h scoring run');
    }
    return parts.join(' · ');
  })();
  const covTip = (() => {
    if (!coverage) return undefined;
    const base = `rule ${coverage.rule || '—'} · target ${coverage.target_pct ?? '—'}% of the visible feed by trust rank`;
    const lr = coverage.last_run;
    if (!lr) return `${base} · no scoring run recorded yet (coverage table freshly created)`;
    const when = lr.scored_at ? `${fmtAge(lr.scored_at)} ago` : '—';
    return `${base} · last run ${when}: attempted ${lr.attempted ?? '—'}, scored ${lr.succeeded ?? '—'}, failed ${lr.failed ?? '—'}${lr.model ? ` · model ${lr.model}` : ''}`;
  })();

  // Fetch price deltas (since each story broke) for tickers on visible rows.
  // /api/market/delta-since is LIVE (daily-close fallback while IBKR intraday
  // bars are stale); failures are cached as null so we don't retry every poll.
  useEffect(() => {
    const want = [];
    for (const c of view.slice(0, showAll ? 40 : FEED_CAP)) {
      for (const t of c.tickers || []) {
        const key = deltaKey(t, c.first_seen_utc);
        if (!(key in deltasRef.current) && want.length < 24) want.push([t, c.first_seen_utc, key]);
      }
    }
    if (!want.length) return;
    let cancelled = false;
    (async () => {
      const out = {};
      for (const [t, since, key] of want) {
        // eslint-disable-next-line no-await-in-loop
        const r = await api.get(`/api/market/delta-since?ticker=${encodeURIComponent(t)}&since=${encodeURIComponent(since || '')}`);
        out[key] = r && r.pct != null ? r : null;
      }
      deltasRef.current = { ...deltasRef.current, ...out };
      if (!cancelled) setDeltas((d) => ({ ...d, ...out }));
    })();
    return () => { cancelled = true; };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [clusters, showAll, myBookOnly]);

  return (
    <div className="space-y-3">
      <div className="flex items-end justify-between">
        <div>
          <h2 className="text-sm font-bold text-white">News</h2>
          <p className="text-[10px] text-slate-500">
            Story clusters · impact-ranked · expandable · GDELT ·{' '}
            {live ? 'news_clusters (embedding)' : 'silver.historical_news digest (fallback — clusters table pending, qr_etl t_d492325f)'}
            {asOf ? ` · as of ${fmtAge(asOf)} ago` : ''}
          </p>
        </div>
        <div className="flex items-center gap-1 shrink-0">
          <button
            onClick={() => pickBook(!myBookOnly)}
            title="Filter the feed to clusters touching your positions or watchlist"
            className={`rounded border px-2 py-0.5 text-[9px] font-mono ${myBookOnly ? 'border-white/25 bg-white/[0.06] text-white' : 'border-white/10 text-slate-500 hover:text-slate-300'}`}
          >
            My book only
          </button>
          <div className="flex items-center gap-1" title="Headline language filter">
            {[[true, 'EN/中文'], [false, 'All']].map(([v, lbl]) => (
              <button
                key={lbl}
                onClick={() => pickLang(v)}
                className={`rounded border px-2 py-0.5 text-[9px] font-mono ${readableOnly === v ? 'border-white/25 bg-white/[0.06] text-white' : 'border-white/10 text-slate-500 hover:text-slate-300'}`}
              >
                {lbl}
              </button>
            ))}
          </div>
        </div>
      </div>

      {loading ? (
        <div className="qr-surface px-3 py-6 flex items-center justify-center gap-2 text-[11px] text-slate-500">
          <div className="w-3 h-3 border-2 border-slate-700 border-t-blue-500 rounded-full animate-spin" />
          Loading news…
        </div>
      ) : !clusters ? (
        <div className="qr-surface px-3 py-6 text-center text-[11px] text-slate-500">
          News feed unavailable.
        </div>
      ) : (
        <>
          {Object.keys(book).length > 0 && (
            joinableCount === 0 ? (
              <div className="qr-surface px-3 py-2 flex flex-wrap items-center gap-x-2 gap-y-1">
                <span className="text-[8px] font-mono text-slate-500 uppercase">Exposure impact</span>
                <ProvBadge state="PENDING" tip="positions: consumption.portfolio_positions_current via /api/portfolio/positions (LIVE) · cluster tickers: news_clusters extraction fix pending" />
                <span className="text-[9px] font-mono text-slate-500">
                  unavailable — 0 of {view.length} clusters in view carry symbols that resolve to your book · ticker extraction pending (qr_etl t_03bdbbfa). This is a data gap, not a neutral reading.
                </span>
              </div>
            ) : inWindow24 === 0 ? (
              <div className="qr-surface px-3 py-2 flex flex-wrap items-center gap-x-2 gap-y-1">
                <span className="text-[8px] font-mono text-slate-500 uppercase">Exposure impact · 7d feed</span>
                <ProvBadge state="PENDING" tip="news_clusters build job stalled — qr_etl t_ffff7242" />
                <span className="text-[9px] font-mono text-slate-500">
                  no clusters in the last 24h — newest is {newestClusterH != null ? `${Math.round(newestClusterH)}h` : '—'} old (feed stale, qr_etl t_ffff7242). Not a measured zero.
                </span>
              </div>
            ) : heldUnscored ? (
              <div className="qr-surface px-3 py-2 flex flex-wrap items-center gap-x-2 gap-y-1">
                <span className="text-[8px] font-mono text-slate-500 uppercase">Exposure impact · 7d feed</span>
                <ProvBadge state="PENDING" tip="llm_direction via news_clusters stamp (qr_etl t_9a746bb9) + /api/news/outlook join (t_3bfe7f78) — held-name coverage gap" />
                <span className="text-[9px] font-mono text-slate-500">
                  unavailable — {exposure.unscored} held cluster{exposure.unscored === 1 ? '' : 's'} in the feed but 0 carry LLM direction · direction-layer coverage gap (news_outlook stamp/join). Not a measured 0/0.
                </span>
              </div>
            ) : (
            <div className="qr-surface px-3 py-2 flex flex-wrap items-center gap-x-2 gap-y-1">
              <span className="text-[8px] font-mono text-slate-500 uppercase">Exposure impact · 7d feed</span>
              <ProvBadge state="LIVE" tip="consumption.portfolio_positions_current via /api/portfolio/positions × news_clusters tickers via /api/news/clusters · counted over exactly the rows rendered below (INVARIANT: strip counts == distinct held tickers on rows)" />
              <span
                className="text-[9px] font-mono"
                title={`held names with ≥1 bearish cluster in the visible feed${exposure.bear.size ? `: ${[...exposure.bear].join(', ')}` : ''}`}
              >
                <span className="text-rose-400">{exposure.bear.size}</span>
                <span className="text-slate-500"> held bearish</span>
              </span>
              <span className="text-[9px] font-mono text-slate-600">vs</span>
              <span
                className="text-[9px] font-mono"
                title={`held names with ≥1 bullish cluster in the visible feed${exposure.bull.size ? `: ${[...exposure.bull].join(', ')}` : ''}`}
              >
                <span className="text-emerald-400">{exposure.bull.size}</span>
                <span className="text-slate-500"> held bullish</span>
              </span>
              <span className="text-[8px] font-mono text-slate-600">
                · {Object.keys(book).length} held{watchlist.size > 0 ? ` · ${watchlist.size} watched` : ''}
              </span>
              {exposure.unscored > 0 && (
                <span
                  className="text-[8px] font-mono text-slate-600"
                  title={`${exposure.unscored} held cluster${exposure.unscored === 1 ? '' : 's'} in the feed carry no LLM direction yet — counts are over the ${exposure.scored} scored held cluster${exposure.scored === 1 ? '' : 's'} only`}
                >
                  · direction on {exposure.scored} of {exposure.scored + exposure.unscored} held
                </span>
              )}
            </div>
            )
          )}

          {Object.keys(outlooks).length > 0 && (
            <div className="qr-surface px-3 py-2 flex flex-wrap items-center gap-x-3 gap-y-1">
              <span className="text-[8px] font-mono text-slate-500 uppercase">LLM outlook{runDate ? ` · ${runDate}` : ''}</span>
              <ProvBadge state="LIVE" tip="consumption.news_outlook via /api/news/outlook (qr_research cron news-outlook-daily)" />
              {Object.entries(outlooks).map(([cat, o]) => (
                <span key={cat} className="text-[9px] font-mono inline-flex items-center gap-x-1.5" title={o.headline || undefined}>
                  <span className="text-slate-400">{labels[cat] || cat}</span>
                  <span className={dirCl(o.bias)}>{o.bias || '—'}</span>
                  <ConfPips conf={o.confidence} />
                  <ToneBar value={digest?.categories?.[cat]?.analytics?.tone_balance} />
                  {o.horizon && <span className="text-slate-500">· {o.horizon}</span>}
                </span>
              ))}
            </div>
          )}

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-3 items-start">
            <AttentionTimeline
              feed={feed}
              catalysts={catalysts}
              mode={tlMode}
              onMode={setTlMode}
              active={panelFilter}
              onSelect={setPanelFilter}
              live={live}
            />
            <DriverMatrix
              feed={feed}
              labels={labels}
              active={panelFilter}
              onSelect={setPanelFilter}
              live={live}
            />
          </div>

          <div className="qr-surface px-3 py-2.5">
            <div className="flex items-baseline justify-between mb-1">
              <div className="qr-label flex items-center gap-2">
                Feed
                <ProvBadge state={live ? 'LIVE' : 'FALLBACK'} tip={live ? 'consumption.news_clusters via /api/news/clusters (embedding clusters)' : 'silver.historical_news via /api/news/digest (token-Jaccard fallback)'} />
                {panelFilter && (
                  <button
                    onClick={() => setPanelFilter(null)}
                    className="rounded border border-white/20 bg-white/[0.05] px-1.5 py-px text-[8px] font-mono text-slate-200 hover:border-white/40 normal-case"
                    title="Clear panel filter"
                  >
                    {panelFilter.label} · {panelFilter.n ?? view.length} clusters ✕
                  </button>
                )}
              </div>
              <div className="text-[9px] font-mono text-slate-500">
                {view.length} clusters{myBookOnly ? ' · my book' : ''} · sorted by impact
                {hiddenCount > 0 && <span> · {hiddenCount} hidden (language/dup/book)</span>}
              </div>
            </div>
            {covLine && (
              <div
                className="text-[9px] font-mono text-slate-500 -mt-0.5 mb-1.5"
                title={covTip}
              >
                {covLine}
              </div>
            )}
            {view.length === 0 ? (
              <div className="text-[10px] text-slate-600 py-2">
                {panelFilter && feed.length > 0
                  ? `No clusters in ${panelFilter.label} — clear the filter above.`
                  : myBookOnly && feed.length > 0
                  ? 'No clusters touch your positions or watchlist right now.'
                  : (clusters || []).length > 0
                  ? 'All clusters hidden by the EN/中文 language filter — switch to All above.'
                  : 'No clusters in the window yet.'}
              </div>
            ) : (
              <>
                <div className="divide-y divide-white/[0.04]">
                  {(showAll ? view : view.slice(0, FEED_CAP)).map((c) => {
                    const ti = tierInfo[c.cluster_id || normH(c.canonical_headline)] || {};
                    return (
                      <ClusterRow
                        key={c.cluster_id || normH(c.canonical_headline)}
                        c={c}
                        labels={labels}
                        expanded={!!expanded[c.cluster_id]}
                        onToggle={() => setExpanded((e) => ({ ...e, [c.cluster_id]: !e[c.cluster_id] }))}
                        hits={hitsFor(c)}
                        deltas={deltas}
                        tier={ti.tier || 'LOW'}
                        rankTip={ti.rankTip}
                      />
                    );
                  })}
                </div>
                {view.length > FEED_CAP && (
                  <button
                    onClick={() => setShowAll((v) => !v)}
                    className="mt-1.5 w-full rounded border border-white/10 bg-white/[0.02] py-1 text-[9px] font-mono text-slate-400 hover:text-slate-200 hover:border-white/20"
                  >
                    {showAll ? `show less` : `show ${view.length - FEED_CAP} more`}
                  </button>
                )}
              </>
            )}
          </div>

          <ReliabilityPanel perf={perf} />
        </>
      )}
    </div>
  );
};

export default NewsTab;
