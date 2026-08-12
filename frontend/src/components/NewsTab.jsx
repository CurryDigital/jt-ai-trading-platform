import React, { useEffect, useRef, useState } from 'react';
import { api, usePoll, fmtAge } from '../utils';

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
// Outlook caveat (t_940dd051): /api/news/outlook joins digest stories on
// (category, cluster_key) and clustering shifts under ?langs=. Decision:
// fetch outlook UNFILTERED (category-level strip is filter-independent) and
// accept degraded per-cluster badge coverage on the filtered view, mitigated
// by the verbatim-headline fallback join in the digest path below.
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

// Impact-tiered visual hierarchy (2026-08-12): the score drives presentation
// so the top stories are identifiable at a 2-second glance without reading
// any number.
//   HIGH   (>=65): 15px/500 headline, full opacity, 3px left border coloured
//                  by direction (bearish=coral/rose-400, bullish=teal-400,
//                  neutral=gray). Full metadata + ticker chips.
//   MEDIUM (40-64): 13px/400 headline in text-primary, 3px gray left border.
//                  Ticker chips hidden until hover/expand.
//   LOW    (<40):  13px/400 headline in text-secondary, no border, metadata
//                  collapsed to "N stories · time ago".
// Single-sided borders are never rounded (rounded-none is explicit).
const tierOf = (score) => ((score ?? 0) >= 65 ? 'HIGH' : (score ?? 0) >= 40 ? 'MEDIUM' : 'LOW');
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

// Map a /api/news/digest story onto the cluster contract (fallback path).
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
                    <span className="font-mono">{m.published_at ? `${fmtAge(m.published_at)} ago` : '—'}</span>
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

const ClusterRow = ({ c, labels, expanded, onToggle }) => {
  const conf = c.llm_confidence != null
    ? Math.round(c.llm_confidence > 1 ? c.llm_confidence : c.llm_confidence * 100)
    : null;
  const tier = tierOf(c.impact_score);
  const border = TIER_BORDER[tier]?.[dirKeyOf(c.llm_direction)] || null;
  const tickers = (c.tickers || []).slice(0, 4);
  return (
    <div
      className={`group py-1.5 cursor-pointer select-none ${border ? `border-l-[3px] rounded-none pl-2.5 ${border}` : ''}`}
      onClick={onToggle}
    >
      <div className="flex items-start gap-2.5">
        <span className={`font-mono text-base leading-snug w-7 text-right shrink-0 ${TIER_SCORE_CL[tier]}`}>
          {c.impact_score ?? '—'}
        </span>
        <div className="flex-1 min-w-0">
          <div className={`${TIER_HEAD_CL[tier]} leading-snug`}>
            {c.canonical_headline}
          </div>
          {tier === 'LOW' ? (
            <div className="text-[9px] text-slate-600 mt-0.5 flex items-center gap-x-2">
              <span className="font-mono">
                {c.story_count ?? '—'} stories · {fmtAge(c.last_seen_utc || c.first_seen_utc)} ago
              </span>
              <span className="font-mono text-slate-700">{expanded ? '▾' : '▸'}</span>
            </div>
          ) : (
            <div className="text-[9px] text-slate-500 mt-0.5 flex flex-wrap items-center gap-x-2 gap-y-0.5">
              <span className="font-mono">
                {c.story_count ?? '—'} stories · {c.outlet_count ?? '—'} outlets · first seen {fmtHHMM(c.first_seen_utc)}
              </span>
              {c.llm_direction && (
                <span className={`font-mono uppercase ${dirCl(c.llm_direction)}`}>
                  · {c.llm_direction}{conf != null ? ` ${conf}%` : ''}
                </span>
              )}
              <AssetBadge cat={c.asset_class} labels={labels} />
              {c.lang && c.lang !== 'en' && <Chip label={c.lang.toUpperCase()} />}
              {(c.driver_tags || []).slice(0, 4).map((d) => <Chip key={d} label={d} />)}
              {/* MEDIUM: ticker chips hidden until hover/expand; HIGH: always visible */}
              {tickers.length > 0 && (
                <span className={tier === 'MEDIUM' && !expanded ? 'opacity-0 group-hover:opacity-100 transition-opacity inline-flex gap-1' : 'inline-flex gap-1'}>
                  {tickers.map((t) => <Chip key={t} label={t} />)}
                </span>
              )}
              <span className="font-mono text-slate-600">{expanded ? '▾ less' : '▸ more'}</span>
            </div>
          )}
        </div>
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
  const [loading, setLoading] = useState(true);
  const [expanded, setExpanded] = useState({});     // cluster_id -> bool
  const [showAll, setShowAll] = useState(false);    // feed capped at FEED_CAP rows by default
  const [readableOnly, setReadableOnly] = useState(() => localStorage.getItem('news.readableOnly') !== '0');
  const pickLang = (v) => { setReadableOnly(v); localStorage.setItem('news.readableOnly', v ? '1' : '0'); };

  // Named so the language toggle can force an immediate server re-query
  // (usePoll alone only re-fires on its interval / visibility change).
  const fetchNews = async () => {
    const langs = readableOnly ? '&langs=en,zh' : '';
    const [cl, dg, out] = await Promise.all([
      api.get(`/api/news/clusters?hours=48&limit=200${langs}`),
      api.get(`/api/news/digest?per_group=120&key_limit=8${langs}`),
      api.get('/api/news/outlook'),
    ]);
    if (dg && dg.categories) { setDigest(dg); setLabels(dg.labels || {}); }
    if (out && out.data) setOutlookData(out.data);

    if (cl && Array.isArray(cl.clusters) && cl.clusters.length > 0) {
      setClusters(cl.clusters);
      setLive(true);
      setAsOf(cl.as_of || null);
      if (cl.labels) setLabels(cl.labels);
    } else if (dg && dg.categories) {
      // Fallback: derive the cluster feed from the digest. LLM cluster rows
      // join by (cat, cluster_key), verbatim headline as backup.
      const llmClusters = out?.data?.clusters || {};
      const mapped = [];
      for (const [cat, payload] of Object.entries(dg.categories)) {
        const byKey = llmClusters[cat] || {};
        for (const s of payload.stories || []) {
          const llm = (s.cluster_key && byKey[s.cluster_key])
            || Object.values(byKey).find((v) => v.headline && v.headline === s.headline)
            || null;
          mapped.push(digestToCluster(s, cat, llm));
        }
      }
      setClusters(mapped);
      setLive(false);
      setAsOf(dg.as_of || null);
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

  const watch = (digest?.watch || []).filter((w) => !readableOnly || isReadable(w.headline));
  const outlooks = outlookData?.outlooks || {};
  const runDate = outlookData?.run_date || null;
  const hiddenCount = (clusters || []).length - feed.length;

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
        <div className="flex items-center gap-1 shrink-0" title="Headline language filter">
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
          {Object.keys(outlooks).length > 0 && (
            <div className="qr-surface px-3 py-2 flex flex-wrap items-center gap-x-3 gap-y-1">
              <span className="text-[8px] font-mono text-slate-500 uppercase">LLM outlook{runDate ? ` · ${runDate}` : ''}</span>
              {Object.entries(outlooks).map(([cat, o]) => (
                <span key={cat} className="text-[9px] font-mono" title={o.headline || undefined}>
                  <span className="text-slate-400">{labels[cat] || cat}</span>{' '}
                  <span className={dirCl(o.bias)}>{o.bias || '—'}</span>
                  {o.horizon && <span className="text-slate-500"> · {o.horizon}</span>}
                  {o.confidence != null && (
                    <span className="text-slate-500"> · conf {Math.round(o.confidence * 100)}%</span>
                  )}
                </span>
              ))}
            </div>
          )}

          {watch.length > 0 && (
            <div className="qr-surface px-3 py-2.5">
              <div className="qr-label mb-1.5">What to Watch</div>
              <div className="flex flex-wrap gap-1.5">
                {watch.map((w, i) => (
                  <span
                    key={i}
                    title={w.headline}
                    className="rounded border border-white/10 bg-white/[0.03] px-2 py-1 text-[9px] font-mono text-slate-200"
                  >
                    ⏱ {w.event}
                    <span className="text-slate-500"> · {labels[w.cat] || w.cat} · {w.published_at ? `${fmtAge(w.published_at)} ago` : ''}</span>
                  </span>
                ))}
              </div>
            </div>
          )}

          <div className="qr-surface px-3 py-2.5">
            <div className="flex items-baseline justify-between mb-1">
              <div className="qr-label">Feed</div>
              <div className="text-[9px] font-mono text-slate-500">
                {feed.length} clusters · sorted by impact
                {hiddenCount > 0 && <span> · {hiddenCount} hidden (language/dup)</span>}
              </div>
            </div>
            {feed.length === 0 ? (
              <div className="text-[10px] text-slate-600 py-2">
                {(clusters || []).length > 0
                  ? 'All clusters hidden by the EN/中文 language filter — switch to All above.'
                  : 'No clusters in the window yet.'}
              </div>
            ) : (
              <>
                <div className="divide-y divide-white/[0.04]">
                  {(showAll ? feed : feed.slice(0, FEED_CAP)).map((c) => (
                    <ClusterRow
                      key={c.cluster_id || normH(c.canonical_headline)}
                      c={c}
                      labels={labels}
                      expanded={!!expanded[c.cluster_id]}
                      onToggle={() => setExpanded((e) => ({ ...e, [c.cluster_id]: !e[c.cluster_id] }))}
                    />
                  ))}
                </div>
                {feed.length > FEED_CAP && (
                  <button
                    onClick={() => setShowAll((v) => !v)}
                    className="mt-1.5 w-full rounded border border-white/10 bg-white/[0.02] py-1 text-[9px] font-mono text-slate-400 hover:text-slate-200 hover:border-white/20"
                  >
                    {showAll ? `show less` : `show ${feed.length - FEED_CAP} more`}
                  </button>
                )}
              </>
            )}
          </div>
        </>
      )}
    </div>
  );
};

export default NewsTab;
