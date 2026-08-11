import React, { useState } from 'react';
import { api, usePoll, fmtAge } from '../utils';

// Research > News — analytics digest over silver.historical_news (GDELT).
// Server-side (/api/news/digest): wire-copy dedup clustering, attention score
// (coverage × recency × impact keywords), driver tags, tone heuristic, and
// forward-event watch extraction. LLM layer (/api/news/outlook, table
// consumption.news_outlook, qr_research cron news-outlook-daily): per-category
// daily outlooks + per-story impact assessments joined by cluster_key.
// Colour carries meaning only:
//   rose   = critical (stale feed > 72h, STALE FEED / DATA GAP warnings) or bearish bias/tone (signed)
//   emerald = bullish bias/tone / positive tone balance (signed)
//   blue   = links only (none here)
//   everything else = neutral slate/white.

const ASSET_ORDER = ['US', 'HK', 'CRYPTO', 'FX', 'METAL'];
const STALE_HOURS = 72;

const staleHours = (iso) => {
  if (!iso) return Infinity;
  return (Date.now() - new Date(iso).getTime()) / 3600000;
};

const toneCl = (tone) =>
  tone === 'bull' ? 'text-emerald-400' : tone === 'bear' ? 'text-rose-400' : 'text-slate-500';

const signedCl = (v) => (v > 0 ? 'text-emerald-400' : v < 0 ? 'text-rose-400' : 'text-slate-500');

// bias is a signed LLM assessment: bullish=emerald, bearish=rose, else neutral slate
const biasCl = (b) =>
  b === 'bullish' ? 'text-emerald-400 border-emerald-400/25 bg-emerald-400/[0.06]'
    : b === 'bearish' ? 'text-rose-400 border-rose-400/25 bg-rose-400/[0.06]'
    : 'text-slate-300 border-white/10 bg-white/[0.03]';

const BiasBadge = ({ bias }) =>
  !bias ? null : (
    <span className={`rounded border px-1.5 py-px text-[8px] font-mono uppercase ${biasCl(bias)}`}>
      {bias}
    </span>
  );

// Split a leading warning sentence ("DATA GAP WARNING: …" / "STALE FEED: …")
// out of verbatim text so it renders rose (critical severity) while the rest
// stays neutral. Text is never altered — only split for colouring.
const splitWarning = (text) => {
  if (!text) return { warn: null, rest: '' };
  const m = text.match(/^((?:DATA GAP WARNING|STALE FEED)[:\s][^.]*\.)\s*(.*)$/s);
  if (m) return { warn: m[1], rest: m[2] };
  if (/^(DATA GAP WARNING|STALE FEED)[:\s]/.test(text)) return { warn: text, rest: '' };
  return { warn: null, rest: text };
};

const DriverChip = ({ label }) => (
  <span className="rounded bg-white/[0.05] px-1.5 py-px text-[8px] font-mono text-slate-400 whitespace-nowrap">
    {label}
  </span>
);

const ToneTag = ({ tone }) =>
  tone === 'neu' ? null : (
    <span className={`text-[8px] font-mono uppercase ${toneCl(tone)}`}>{tone}</span>
  );

const ScoreBar = ({ score }) => (
  <div className="flex items-center gap-1.5 shrink-0">
    <div className="w-10 h-1 rounded bg-white/[0.06] overflow-hidden">
      <div className="h-full bg-slate-300/70" style={{ width: `${Math.min(score, 100)}%` }} />
    </div>
    <span className="text-[9px] font-mono text-slate-400 w-5 text-right">{score}</span>
  </div>
);

// Per-story LLM impact badges (bias + confidence + horizon + affected assets),
// matched from /api/news/outlook cluster rows by cluster_key/headline.
const LlmBadges = ({ llm }) => {
  if (!llm) return null;
  const conf = llm.confidence != null ? Math.round(llm.confidence * 100) : null;
  const assets = (llm.affected_assets || []).slice(0, 4);
  return (
    <div className="flex flex-wrap items-center gap-1 mt-1" title={llm.rationale || undefined}>
      <span className="text-[8px] font-mono text-slate-500 uppercase">LLM</span>
      <BiasBadge bias={llm.bias} />
      {conf != null && <span className="text-[8px] font-mono text-slate-400">conf {conf}%</span>}
      {llm.horizon && <span className="text-[8px] font-mono text-slate-500">· {llm.horizon}</span>}
      {assets.map(a => <DriverChip key={a} label={a} />)}
    </div>
  );
};

const StoryRow = ({ s, showCat, labels, llm }) => (
  <div className="py-1.5">
    <div className="flex items-start gap-2">
      <div className="flex-1 min-w-0">
        <div className="text-[11px] text-slate-200 leading-snug">{s.headline}</div>
        <div className="text-[9px] text-slate-500 mt-0.5 flex flex-wrap items-center gap-x-2 gap-y-0.5">
          {showCat && <span className="font-mono text-slate-400">{labels?.[s.cat] || s.cat}</span>}
          {s.published_at && <span className="font-mono">{fmtAge(s.published_at)} ago</span>}
          {s.n_sources > 1 && (
            <span className="font-mono text-slate-400" title={s.sources?.join(', ')}>
              ×{s.n_sources} sources
            </span>
          )}
          {s.entity && <span className="truncate">{s.entity}</span>}
          <ToneTag tone={s.tone} />
        </div>
        {(s.drivers || []).length > 0 && (
          <div className="flex flex-wrap gap-1 mt-1">
            {s.drivers.map(d => <DriverChip key={d} label={d} />)}
            {s.watch && s.watch !== 'Watch' && (
              <span className="rounded border border-white/10 px-1.5 py-px text-[8px] font-mono text-slate-300 whitespace-nowrap">
                ⏱ {s.watch}
              </span>
            )}
          </div>
        )}
        <LlmBadges llm={llm} />
      </div>
      <ScoreBar score={s.score} />
    </div>
  </div>
);

// Daily LLM outlook card for one asset class. Renders STALE FEED / DATA GAP
// warnings verbatim (rose = critical severity). Degrades to null when the
// category has no outlook row for the latest run_date.
const OutlookBlock = ({ outlook, runDate }) => {
  if (!outlook) return null;
  const conf = outlook.confidence != null ? Math.round(outlook.confidence * 100) : null;
  const head = splitWarning(outlook.headline);
  const body = splitWarning(outlook.rationale);
  return (
    <div className="mb-2 rounded border border-white/10 bg-white/[0.02] px-2 py-1.5">
      <div className="flex flex-wrap items-center gap-x-1.5 gap-y-0.5">
        <span className="text-[8px] font-mono text-slate-500 uppercase">LLM outlook{runDate ? ` · ${runDate}` : ''}</span>
        <BiasBadge bias={outlook.bias} />
        {outlook.horizon && <span className="text-[8px] font-mono text-slate-400">{outlook.horizon}</span>}
        {conf != null && <span className="text-[8px] font-mono text-slate-400">conf {conf}%</span>}
      </div>
      {outlook.headline && (
        <div className={`text-[10px] font-semibold mt-1 leading-snug ${head.warn ? 'text-rose-400' : 'text-slate-200'}`}>
          {head.warn || head.rest}
        </div>
      )}
      {outlook.rationale && (
        <div className="text-[9px] mt-0.5 leading-snug">
          {body.warn && <span className="text-rose-400">{body.warn} </span>}
          <span className="text-slate-400">{body.rest}</span>
        </div>
      )}
      {(outlook.affected_assets || []).length > 0 && (
        <div className="flex flex-wrap gap-1 mt-1">
          {outlook.affected_assets.slice(0, 6).map(a => <DriverChip key={a} label={a} />)}
        </div>
      )}
    </div>
  );
};

const NewsAssetCard = ({ cat, label, catData, lastUpdated, outlook, runDate, llmFor }) => {
  const stale = staleHours(lastUpdated) > STALE_HOURS;
  const analytics = catData?.analytics || {};
  const stories = catData?.stories || [];
  return (
    <div className="qr-surface px-3 py-2.5">
      <div className="flex items-baseline justify-between mb-1">
        <div className="qr-label">{label || cat}</div>
        <div className={`text-[9px] font-mono ${stale ? 'text-rose-400' : 'text-slate-500'}`}>
          {lastUpdated ? `${fmtAge(lastUpdated)} ago${stale ? ' · stale feed' : ''}` : 'no data'}
        </div>
      </div>
      {stories.length > 0 && (
        <div className="text-[9px] font-mono text-slate-500 mb-1.5 flex flex-wrap items-center gap-x-2">
          <span>{analytics.headlines} headlines → <span className="text-slate-300">{analytics.unique_stories} stories</span></span>
          <span>{analytics.sources} outlets</span>
          <span>tone <span className={signedCl(analytics.tone_balance)}>{analytics.tone_balance > 0 ? '+' : ''}{analytics.tone_balance}</span></span>
        </div>
      )}
      <OutlookBlock outlook={outlook} runDate={runDate} />
      {(analytics.top_drivers || []).length > 0 && (
        <div className="flex flex-wrap gap-1 mb-1.5">
          {analytics.top_drivers.map(d => <DriverChip key={d} label={d} />)}
        </div>
      )}
      {stories.length === 0 ? (
        <div className="text-[10px] text-slate-600 py-2">No headlines for this asset class yet.</div>
      ) : (
        <div className="divide-y divide-white/[0.04]">
          {stories.slice(0, 10).map((s, i) => <StoryRow key={i} s={s} llm={llmFor?.(cat, s)} />)}
        </div>
      )}
    </div>
  );
};

export const NewsTab = () => {
  const [digest, setDigest] = useState(null);
  const [outlookData, setOutlookData] = useState(null);
  const [loading, setLoading] = useState(true);

  usePoll(async () => {
    const [res, out] = await Promise.all([
      api.get('/api/news/digest?per_group=120&key_limit=8'),
      api.get('/api/news/outlook'),
    ]);
    if (res && res.categories) setDigest(res);
    if (out && out.data) setOutlookData(out.data);
    setLoading(false);
  }, 300000); // 5 min — GDELT ingestion cadence is hourly-ish

  const labels = digest?.labels || {};
  const lastUpdated = digest?.last_updated || {};
  const keyStories = digest?.key || [];
  const watch = digest?.watch || [];

  const outlooks = outlookData?.outlooks || {};
  const llmClusters = outlookData?.clusters || {};
  const runDate = outlookData?.run_date || null;

  // Join a digest story onto its LLM assessment: cluster_key first (exact),
  // fall back to verbatim headline match (stale-feed windows can shift the
  // cluster representative so the key differs while the story is the same).
  const llmFor = (cat, story) => {
    const byKey = llmClusters?.[cat] || {};
    if (story?.cluster_key && byKey[story.cluster_key]) return byKey[story.cluster_key];
    const hit = Object.values(byKey).find(v => v.headline && v.headline === story?.headline);
    return hit || null;
  };

  return (
    <div className="space-y-3">
      <div className="flex items-end justify-between">
        <div>
          <h2 className="text-sm font-bold text-white">News</h2>
          <p className="text-[10px] text-slate-500">
            Deduped & attention-ranked · driver tags · tone heuristic · GDELT · silver.historical_news · LLM impact layer (consumption.news_outlook)
          </p>
        </div>
      </div>

      {loading ? (
        <div className="qr-surface px-3 py-6 flex items-center justify-center gap-2 text-[11px] text-slate-500">
          <div className="w-3 h-3 border-2 border-slate-700 border-t-blue-500 rounded-full animate-spin" />
          Loading news…
        </div>
      ) : !digest ? (
        <div className="qr-surface px-3 py-6 text-center text-[11px] text-slate-500">
          News digest unavailable.
        </div>
      ) : (
        <>
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

          {keyStories.length > 0 && (
            <div className="qr-surface px-3 py-2.5">
              <div className="qr-label mb-1">Key Developments</div>
              <div className="text-[9px] text-slate-500 mb-1.5 font-mono">
                Highest-attention stories across all asset classes · score = coverage × recency × impact
              </div>
              <div className="divide-y divide-white/[0.04]">
                {keyStories.map((s, i) => <StoryRow key={i} s={s} showCat labels={labels} llm={llmFor(s.cat, s)} />)}
              </div>
            </div>
          )}

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-3.5 items-start">
            {ASSET_ORDER.map(cat => (
              <NewsAssetCard
                key={cat}
                cat={cat}
                label={labels[cat]}
                catData={digest.categories?.[cat]}
                lastUpdated={lastUpdated[cat]}
                outlook={outlooks[cat]}
                runDate={runDate}
                llmFor={llmFor}
              />
            ))}
          </div>
        </>
      )}
    </div>
  );
};

export default NewsTab;
