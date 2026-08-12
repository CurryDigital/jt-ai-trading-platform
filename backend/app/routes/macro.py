"""Research > Macro endpoints — regime forecast, KPIs, sectors, calendar, news.

See design-bundle handoff/API_SPEC_v2.md §2 and DB_CHANGES_v2.md §3.
"""
import re
import hashlib
from collections import Counter
from fastapi import APIRouter, Depends
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.db.safe_query import safe_query

router = APIRouter(prefix="/api", tags=["macro"])

REGION_META = {
    "US": {"index_sym": "SPX", "index_name": "S&P 500"},
    "HK": {"index_sym": "HSI", "index_name": "Hang Seng"},
}
GLOBAL_SCOPES = ["CRYPTO", "FX", "METAL"]


def _now_iso():
    return datetime.now(timezone.utc).isoformat()


def _regime_by_scope(db, scopes):
    rows = safe_query(db, """
        SELECT scope, day_offset, risk_on_pct FROM consumption.macro_regime_7d
        WHERE scope = ANY(:scopes) ORDER BY scope, day_offset
    """, {"scopes": scopes}, label="macro_regime_7d")
    out = {}
    for r in rows:
        out.setdefault(r.scope, [None] * 7)
        if 0 <= r.day_offset < 7:
            out[r.scope][r.day_offset] = float(r.risk_on_pct)
    return out


def _kpis_by_scope(db, scopes):
    rows = safe_query(db, """
        SELECT scope, label, value FROM consumption.macro_kpis
        WHERE scope = ANY(:scopes) ORDER BY scope, ord
    """, {"scopes": scopes}, label="macro_kpis")
    out = {}
    for r in rows:
        out.setdefault(r.scope, []).append([r.label, r.value])
    return out


@router.get("/macro/regions")
def get_macro_regions(db: Session = Depends(get_db)):
    scopes = list(REGION_META.keys())
    regimes = _regime_by_scope(db, scopes)
    kpis = _kpis_by_scope(db, scopes)

    events_rows = safe_query(db, """
        SELECT region, event, event_date, importance FROM consumption.macro_events
        WHERE region = ANY(:scopes) ORDER BY region, event_date
    """, {"scopes": scopes}, label="macro_events")
    events = {}
    for r in events_rows:
        events.setdefault(r.region, []).append({"event": r.event, "date": r.event_date, "importance": r.importance})

    sectors_rows = safe_query(db, """
        SELECT region, sector, perf_pct FROM consumption.macro_sectors
        WHERE region = ANY(:scopes) ORDER BY region, ord
    """, {"scopes": scopes}, label="macro_sectors")
    sectors = {}
    for r in sectors_rows:
        sectors.setdefault(r.region, []).append({"sector": r.sector, "perf_pct": float(r.perf_pct)})

    idx_rows = safe_query(db, """
        SELECT sym, region, last, change_pct FROM consumption.dashboard_indices
        WHERE region = ANY(:scopes)
    """, {"scopes": scopes}, label="macro_index_lookup")
    idx_by_region = {r.region: r for r in idx_rows}

    data = []
    for key, meta in REGION_META.items():
        idx = idx_by_region.get(key)
        data.append({
            "key": key, "index_sym": meta["index_sym"], "index_name": meta["index_name"],
            "last": float(idx.last) if idx is not None and idx.last is not None else None,
            "change_pct": float(idx.change_pct) if idx is not None and idx.change_pct is not None else None,
            "session": None,
            "regime_7d": regimes.get(key, [None] * 7),
            "kpis": kpis.get(key, []),
            "events": events.get(key, []),
            "sectors": sectors.get(key, []),
        })
    return {"data": data, "as_of": _now_iso()}


@router.get("/macro/global")
def get_macro_global(db: Session = Depends(get_db)):
    regimes = _regime_by_scope(db, GLOBAL_SCOPES)
    kpis = _kpis_by_scope(db, GLOBAL_SCOPES)

    news_rows = safe_query(db, """
        SELECT DISTINCT ON (market) market, headline, tone FROM consumption.market_news
        WHERE market = ANY(:scopes) ORDER BY market, published_at DESC
    """, {"scopes": GLOBAL_SCOPES}, label="macro_global_news")
    news_by_scope = {r.market: {"headline": r.headline, "tone": r.tone} for r in news_rows}

    data = [{
        "key": key,
        "regime_7d": regimes.get(key, [None] * 7),
        "kpis": kpis.get(key, []),
        "news": news_by_scope.get(key),
    } for key in GLOBAL_SCOPES]
    return {"data": data, "as_of": _now_iso()}


NEWS_ASSET_ORDER = ["US", "HK", "CRYPTO", "FX", "METAL"]

NEWS_ASSET_LABELS = {
    "US": "US Equities",
    "HK": "HK Equities",
    "CRYPTO": "Crypto",
    "FX": "FX",
    "METAL": "Metals",
}


@router.get("/news/by-asset")
def get_news_by_asset(per_group: int = 15, db: Session = Depends(get_db)):
    """Research > News subtab — latest silver.historical_news headlines split
    by asset class (category). Junk categories ('market', 'person') are
    excluded. last_updated exposes per-category freshness so the UI can flag
    stale feeds (ETL cadence differs per category)."""
    per_group = max(1, min(per_group, 50))
    rows = safe_query(db, """
        SELECT category, date, entity_name, headline, source FROM (
            SELECT category, date, entity_name, headline, source,
                   ROW_NUMBER() OVER (PARTITION BY category ORDER BY date DESC, id DESC) AS rn
            FROM silver.historical_news
            WHERE category = ANY(:cats)
        ) t WHERE rn <= :per_group
        ORDER BY category, date DESC
    """, {"cats": NEWS_ASSET_ORDER, "per_group": per_group}, label="news_by_asset")
    data = {c: [] for c in NEWS_ASSET_ORDER}
    last_updated = {}
    for r in rows:
        if r.category not in data:
            continue
        data[r.category].append({
            "headline": r.headline,
            "source": (r.source or "").replace("gdelt:", "") or None,
            "entity": r.entity_name or None,
            "published_at": r.date.isoformat() if r.date else None,
        })
        if r.category not in last_updated and r.date:
            last_updated[r.category] = r.date.isoformat()
    return {
        "data": data,
        "labels": NEWS_ASSET_LABELS,
        "last_updated": last_updated,
        "as_of": _now_iso(),
    }


@router.get("/news")
def get_market_news(markets: str = "US,HK", db: Session = Depends(get_db)):
    market_list = [m.strip() for m in markets.split(",") if m.strip()]
    rows = safe_query(db, """
        SELECT market, headline, source, tone, impact, tags, published_at
        FROM consumption.market_news WHERE market = ANY(:markets)
        ORDER BY market, published_at DESC LIMIT 40
    """, {"markets": market_list}, label="market_news")
    data = {}
    for r in rows:
        data.setdefault(r.market, []).append({
            "headline": r.headline, "source": r.source,
            "age": None, "tone": r.tone, "impact": r.impact,
            "tags": list(r.tags) if r.tags is not None else [],
            "published_at": r.published_at.isoformat() if r.published_at else None,
        })
    return {"data": data, "as_of": _now_iso() if rows else None}


# ---------------------------------------------------------------------------
# News digest - dedup clustering, attention scoring, driver tags, tone,
# forward-event extraction. All computed deterministically from real
# silver.historical_news headlines (no fabricated predictions).
# ---------------------------------------------------------------------------

_NEWS_STOPWORDS = {
    "the", "a", "an", "and", "or", "of", "to", "in", "on", "as", "at", "for",
    "with", "by", "from", "is", "are", "was", "were", "after", "amid", "over",
    "its", "it", "this", "that", "says", "say", "new", "video", "watch",
    "market", "markets", "stocks", "stock", "shares", "prices", "price",
    "today", "week", "day", "ago", "vs", "per", "cent",
}

_NEWS_TOKEN_RE = re.compile(r"[a-z0-9]+")
_NEWS_CJK_RE = re.compile(r"[\u4e00-\u9fff]")

_NEWS_DRIVERS = [
    ("Oil & Energy", ["oil", "crude", "brent", "wti", "opec", "hormuz"]),
    ("Fed & Rates", ["fed ", "fomc", "powell", "rate hike", "rate cut", "repricing",
                      "yields", "treasury", "bessent", "monetary policy"]),
    ("Inflation & CPI", ["cpi", "inflation", "pce", "payrolls", "jobs report"]),
    ("Geopolitics", ["iran", "russia", "ukraine", "sanction", "irgc", "geopolitic",
                      "putin", "middle east", "tariff", "trade war"]),
    ("Earnings", ["earnings", "eps", "profit", "revenue", "wall street earnings"]),
    ("AI & Tech", [" ai ", "artificial intelligence", "nvidia", "chip", "semiconductor",
                    "data center", "datacenter"]),
    ("Crypto Policy", ["bitcoin", "crypto", "usdc", "stablecoin", "xrp", "defi"]),
    ("China & HK", ["hang seng", "\u6052\u6307", "\u6e2f\u80a1", "\u5317\u6c34", "\u79d1\u6307",
                     "china", "pboc", "yuan", "stimulus", "property",
                     "\u6a13", "\u5546\u5ec8", "\u9999\u6e2f"]),
    ("FX & Currency", ["yen", "dollar", "euro", "ringgit", "intervention", "currency",
                        "currencies", "\uc5d4\ud654"]),
    ("Metals", ["gold", "silver", "bullion", "\u9ec4\u91d1", "precious metal"]),
]

_NEWS_BULL = ["surge", "rally", "soar", "jump", "gain", "rise", "rises", "record high",
              "all-time high", "all - time high", "beat", "beats", "beating", "rebound",
              "higher", "inflows", "paying off", "hikes s & p", "extends", "breakout",
              "\u6da8", "\u63da", "\u98c6", "\u65b0\u9ad8", "\u6383\u8ca8"]
_NEWS_BEAR = ["slip", "fall", "fell", "drop", "plunge", "slump", "slide", "lower",
              "down", "miss", "fear", "crisis", "crash", "outflow", "retreat",
              "fade", "fades", "weigh", "loss", "schock", "horror", "selloff",
              "\u8dcc", "\u56de\u8c03", "\u6cbd"]

_NEWS_WATCH = [
    ("cpi", "US CPI"), ("fomc", "FOMC"), ("rba", "RBA decision"),
    ("payrolls", "Payrolls"), ("nonfarm", "Payrolls"), ("opec", "OPEC"),
    ("boj", "BoJ"), ("ecb", "ECB"), ("fed decision", "Fed decision"),
]


def _news_tokens(headline):
    h = (headline or "").lower()
    toks = {t for t in _NEWS_TOKEN_RE.findall(h) if t not in _NEWS_STOPWORDS and len(t) > 1}
    cjk = _NEWS_CJK_RE.findall(h)
    for i in range(0, max(0, len(cjk) - 1)):
        toks.add("".join(cjk[i:i + 2]))
    return toks


def _news_cluster_key(headline):
    """Stable key joining a digest cluster to consumption.news_outlook rows.

    Must match qr_research extract_clusters.cluster_key exactly:
    sha1-16 of the sorted, space-joined token set (truncated to 48 chars).
    """
    norm = " ".join(sorted(_news_tokens(headline)))[:48]
    return hashlib.sha1(norm.encode()).hexdigest()[:16]


def _news_tone(text):
    h = " " + (text or "").lower() + " "
    bull = sum(1 for k in _NEWS_BULL if k in h)
    bear = sum(1 for k in _NEWS_BEAR if k in h)
    if bull > bear:
        return "bull"
    if bear > bull:
        return "bear"
    return "neu"


def _news_drivers(text, limit=3):
    h = " " + (text or "").lower() + " "
    hits = [label for label, kws in _NEWS_DRIVERS if any(k in h for k in kws)]
    return hits[:limit]


def _news_watch(text):
    h = (text or "").lower()
    forward = any(p in h for p in ("ahead of", "this week", "upcoming", "next week",
                                   "set to", "bets", "expectation", "forecast", "outlook"))
    labels = [lbl for kw, lbl in _NEWS_WATCH if kw in h]
    if labels:
        return labels[0]
    return "Watch" if forward else None


def _cluster_news(items, threshold=0.42):
    """Greedy clustering by token Jaccard similarity; items carry '_tok' sets
    and must be pre-sorted newest first."""
    clusters = []
    for it in items:
        placed = False
        for cl in clusters:
            rep = cl[0]["_tok"]
            tok = it["_tok"]
            if not rep or not tok:
                continue
            j = len(rep & tok) / len(rep | tok)
            if j >= threshold:
                cl.append(it)
                placed = True
                break
        if not placed:
            clusters.append([it])
    return clusters


@router.get("/news/digest")
def get_news_digest(hours: int = 240, per_group: int = 120, key_limit: int = 8,
                    langs: str | None = None, db: Session = Depends(get_db)):
    """Research > News - analytics digest over silver.historical_news.

    Dedups wire-copy repetition (same story from N outlets -> one cluster with
    source count), scores attention (coverage x recency x impact keywords),
    tags market drivers, derives a directional tone heuristic, and extracts
    forward-looking events into a watch list. Everything is computed from real
    headlines; no predictions are fabricated.

    ?langs=en,zh filters by silver.historical_news.lang (ISO 639-1) BEFORE
    clustering/scoring, so all analytics reflect the filtered subset.
    """
    per_group = max(10, min(per_group, 300))
    key_limit = max(1, min(key_limit, 20))
    hours = max(24, min(hours, 24 * 30))
    lang_filter = None
    if langs:
        lang_filter = [l.strip().lower() for l in langs.split(",")
                       if re.fullmatch(r"[a-z]{2,3}", l.strip().lower())]
        if not lang_filter:
            lang_filter = None
    lang_clause = "AND lang = ANY(:langs)" if lang_filter else ""
    rows = safe_query(db, f"""
        SELECT category, date, entity_name, headline, source, lang FROM (
            SELECT category, date, entity_name, headline, source, lang,
                   ROW_NUMBER() OVER (PARTITION BY category ORDER BY date DESC, id DESC) AS rn
            FROM silver.historical_news
            WHERE category = ANY(:cats)
              AND date >= NOW() - INTERVAL '1 hour' * :hours
              {lang_clause}
        ) t WHERE rn <= :per_group
        ORDER BY category, date DESC
    """, {"cats": NEWS_ASSET_ORDER, "per_group": per_group, "hours": hours,
          "langs": lang_filter},
        label="news_digest")

    by_cat = {c: [] for c in NEWS_ASSET_ORDER}
    last_updated = {}
    for r in rows:
        if r.category not in by_cat:
            continue
        src = (r.source or "").replace("gdelt:", "") or None
        item = {
            "headline": r.headline,
            "source": src,
            "entity": r.entity_name or None,
            "lang": r.lang or None,
            "published_at": r.date.isoformat() if r.date else None,
            "_dt": r.date,
            "_tok": _news_tokens(r.headline),
        }
        by_cat[r.category].append(item)
        if r.category not in last_updated and r.date:
            last_updated[r.category] = r.date.isoformat()

    now = datetime.now()
    categories = {}
    all_clusters = []
    for cat in NEWS_ASSET_ORDER:
        items = by_cat[cat]
        clusters = _cluster_news(items)
        stories = []
        for cl in clusters:
            rep = cl[0]
            newest = max((i["_dt"] for i in cl if i["_dt"]), default=None)
            sources = sorted({i["source"] for i in cl if i["source"]})
            text = " ".join(i["headline"] or "" for i in cl)
            tone = _news_tone(text)
            drivers = _news_drivers(text)
            watch = _news_watch(text)
            age_h = ((now - newest).total_seconds() / 3600.0) if newest else 999.0
            coverage = len(cl)
            low = " " + text.lower() + " "
            impact = sum(1 for kws in (_NEWS_BULL, _NEWS_BEAR) for k in kws if k in low)
            impact_norm = min(impact / 6.0, 1.0)
            coverage_norm = min(coverage / 6.0, 1.0)
            recency = max(0.0, 1.0 - age_h / 72.0)
            score = round(100 * (0.45 * coverage_norm + 0.35 * recency + 0.20 * impact_norm))
            story = {
                "headline": rep["headline"],
                "cluster_key": _news_cluster_key(rep["headline"]),
                "entity": rep["entity"],
                "lang": rep["lang"],
                "published_at": newest.isoformat() if newest else None,
                "sources": sources,
                "n_sources": coverage,
                "score": score,
                "tone": tone,
                "drivers": drivers,
                "watch": watch,
            }
            stories.append(story)
            all_clusters.append({"cat": cat, **story})
        stories.sort(key=lambda s: s["score"], reverse=True)

        tones = Counter(s["tone"] for s in stories)
        driver_counts = Counter(d for s in stories for d in s["drivers"])
        total_tone = max(sum(tones.values()), 1)
        categories[cat] = {
            "analytics": {
                "headlines": len(items),
                "unique_stories": len(stories),
                "sources": len({i["source"] for i in items if i["source"]}),
                "top_drivers": [d for d, _ in driver_counts.most_common(3)],
                "tone_balance": round(100 * (tones.get("bull", 0) - tones.get("bear", 0)) / total_tone),
            },
            "stories": stories,
        }

    all_clusters.sort(key=lambda s: s["score"], reverse=True)
    key = all_clusters[:key_limit]
    watch_list = []
    seen_watch = set()
    for s in all_clusters:
        if s["watch"] and s["watch"] not in seen_watch and s["watch"] != "Watch":
            seen_watch.add(s["watch"])
            watch_list.append({"event": s["watch"], "cat": s["cat"],
                               "headline": s["headline"],
                               "published_at": s["published_at"]})
        if len(watch_list) >= 6:
            break

    return {
        "key": key,
        "watch": watch_list,
        "categories": categories,
        "labels": NEWS_ASSET_LABELS,
        "langs": lang_filter,
        "last_updated": last_updated,
        "as_of": _now_iso(),
    }


# ---------------------------------------------------------------------------
# News story clusters - Research > News primary feed (kanban t_d492325f).
# Serves consumption.news_clusters, rebuilt every 2h by qr_etl cron
# 'qr_etl.news_clusters_refresh' (multilingual title-embedding clustering,
# cosine >= 0.82, 48h window, scoped by asset_class). /news/digest stays
# unchanged as fallback + watch strip.
# ---------------------------------------------------------------------------
@router.get("/news/clusters")
def get_news_clusters(hours: int = 48, limit: int = 200,
                      langs: str | None = None, db: Session = Depends(get_db)):
    """Research > News - story clusters (display unit = cluster, not headline).

    Reads the latest precomputed batch from consumption.news_clusters. Clusters
    carry canonical_headline (highest-authority member outlet), coverage stats,
    driver tags, tickers, optional LLM outlook (null-safe), impact_score with
    exact impact_components {attention, coverage, recency, keyword_impact,
    llm_impact} (points summing to impact_score; null on pre-t_1f96bc9b rows),
    and members[] with real per-member published_at + source urls.

    ?hours= filters clusters by last_seen_utc (default 48, the build window).
    ?langs=en,zh filters cluster MEMBERS by ISO 639-1 lang (clusters with no
    surviving members are dropped; story/outlet counts reflect the filtered
    members). Note: clustering itself runs over all langs in the ETL build -
    the langs param narrows the served members, it does not re-cluster.
    """
    hours = max(1, min(hours, 24 * 30))
    limit = max(1, min(limit, 500))
    lang_filter = None
    if langs:
        lang_filter = [l.strip().lower() for l in langs.split(",")
                       if re.fullmatch(r"[a-z]{2,3}", l.strip().lower())]
        if not lang_filter:
            lang_filter = None

    rows = safe_query(db, """
        SELECT cluster_id, canonical_headline, story_count, outlet_count,
               first_seen_utc, last_seen_utc, asset_class, driver_tags,
               tickers, llm_direction, llm_confidence, llm_rationale,
               impact_score, impact_components, members, computed_at
        FROM consumption.news_clusters
        WHERE window_hours = 48
          AND computed_at = (SELECT MAX(computed_at)
                             FROM consumption.news_clusters
                             WHERE window_hours = 48)
          AND last_seen_utc >= NOW() - INTERVAL '1 hour' * :hours
        ORDER BY impact_score DESC
    """, {"hours": hours}, label="news_clusters")

    clusters = []
    for r in rows:
        members = r.members or []
        if isinstance(members, str):
            try:
                import json as _json
                members = _json.loads(members)
            except Exception:
                members = []
        if lang_filter:
            members = [m for m in members
                       if (m.get("lang") or "").lower() in lang_filter]
            if not members:
                continue
        # Per-cluster lang (kanban t_32c13d6d): lang of the canonical-headline
        # member (member headlines are the normalized text, so exact match on
        # canonical_headline identifies it); fallback = modal lang across the
        # (filtered) members; null when undetermined. Feeds the frontend
        # per-story lang badge (t_940dd051).
        cluster_lang = None
        canon_lower = (r.canonical_headline or "").lower()
        for m in members:
            if (m.get("headline") or "").lower() == canon_lower and m.get("lang"):
                cluster_lang = m["lang"]
                break
        if cluster_lang is None:
            counts = {}
            for m in members:
                ml = (m.get("lang") or "").lower()
                if ml:
                    counts[ml] = counts.get(ml, 0) + 1
            if counts:
                cluster_lang = max(sorted(counts), key=lambda l: counts[l])
        clusters.append({
            "cluster_id": r.cluster_id,
            "canonical_headline": r.canonical_headline,
            "lang": cluster_lang,
            "story_count": len(members) if lang_filter else r.story_count,
            "outlet_count": (len({m.get("outlet") for m in members if m.get("outlet")})
                             if lang_filter else r.outlet_count),
            "first_seen_utc": r.first_seen_utc.isoformat() if r.first_seen_utc else None,
            "last_seen_utc": r.last_seen_utc.isoformat() if r.last_seen_utc else None,
            "asset_class": r.asset_class,
            "driver_tags": list(r.driver_tags or []),
            "tickers": list(r.tickers or []),
            "llm_direction": r.llm_direction,
            "llm_confidence": float(r.llm_confidence) if r.llm_confidence is not None else None,
            "llm_rationale": r.llm_rationale,
            "impact_score": r.impact_score,
            "impact_components": (r.impact_components
                                  if isinstance(r.impact_components, dict) else None),
            "members": members,
        })

    return {
        "clusters": clusters[:limit],
        "langs": lang_filter,
        "as_of": _now_iso(),
        "source": "news_clusters",
    }


# ---------------------------------------------------------------------------
# News outlook - LLM market-impact layer (consumption.news_outlook).
# Populated twice daily by qr_research cron 'news-outlook-daily'. Cluster rows
# join onto /news/digest stories via (category, cluster_key); outlook rows are
# one per category per run_date. STALE FEED / DATA GAP warnings in
# headline/rationale are intentional honesty markers and must be rendered
# verbatim by the UI.
# ---------------------------------------------------------------------------


def _outlook_row_payload(r):
    return {
        "headline": r.headline,
        "bias": r.bias,
        "affected_assets": list(r.affected_assets) if r.affected_assets else [],
        "confidence": float(r.confidence) if r.confidence is not None else None,
        "horizon": r.horizon,
        "rationale": r.rationale,
        "n_sources": r.n_sources,
        "source_latest": r.source_latest.isoformat() if r.source_latest else None,
        "model": r.model,
    }


@router.get("/news/outlook")
def get_news_outlook(db: Session = Depends(get_db)):
    """Research > News - LLM market-impact layer over the digest.

    Returns the latest run_date's consumption.news_outlook rows:
    - outlooks: one daily outlook per category (bias, horizon, confidence,
      rationale, affected_assets)
    - clusters: per-story assessments keyed category -> cluster_key, so the UI
      can badge /news/digest stories (cluster_key is emitted on digest stories).

    Missing table / empty day degrades to empty maps (HTTP 200).
    """
    rows = safe_query(db, """
        SELECT row_type, category, cluster_key, headline, bias, affected_assets,
               confidence, horizon, rationale, n_sources, source_latest, model,
               run_date, generated_at
        FROM consumption.news_outlook
        WHERE run_date = (SELECT max(run_date) FROM consumption.news_outlook)
        ORDER BY category, row_type, n_sources DESC NULLS LAST
    """, label="news_outlook")

    outlooks = {}
    clusters = {}
    run_date = None
    generated_at = None
    for r in rows:
        if run_date is None and r.run_date:
            run_date = r.run_date.isoformat()
        if r.generated_at and (generated_at is None or r.generated_at.isoformat() > generated_at):
            generated_at = r.generated_at.isoformat()
        payload = _outlook_row_payload(r)
        if r.row_type == "outlook":
            outlooks[r.category] = payload
        elif r.row_type == "cluster" and r.cluster_key:
            clusters.setdefault(r.category, {})[r.cluster_key] = payload

    return {
        "data": {
            "run_date": run_date,
            "generated_at": generated_at,
            "outlooks": outlooks,
            "clusters": clusters,
        },
        "as_of": _now_iso(),
    }


MIN_SAMPLE_TRUSTWORTHY = 30  # frontend greys out metrics with n below this


@router.get("/news/signal-performance")
def get_news_signal_performance(db: Session = Depends(get_db)):
    """Research > News - LLM signal accountability (kanban t_03fc7ddb).

    Serves consumption.news_signal_performance (built daily by qr_etl
    build_news_signal_performance.py from the persistent ledger
    consumption.news_signal_events): does llm_direction predict forward
    returns of the story's primary ticker?

    Shape:
      windows['30d'|'90d'].by_horizon['1h'|'1d'|'5d'] =
          {hit_rate, mean_return, ic, n} or null when unavailable
          (1h is null while bronze.ibkr_historical_bars is stale)
      windows[w].coverage = {pct, n}   (% clusters with resolvable ticker)
      by_confidence_bucket / by_asset_class = 1d-horizon breakdowns
      status = 'ok' | 'insufficient_data' (30d 1d overall n < 30)

    Every metric carries n; treat n < 30 as untrustworthy (greyed out UI).
    Degrades to status='no_data' + empty maps when the table is absent/empty.
    """
    rows = safe_query(db, """
        SELECT horizon, "window", segment_type, segment_value, hit_rate,
               mean_return, information_coefficient, coverage_pct,
               sample_size, computed_at
        FROM consumption.news_signal_performance
        WHERE computed_at = (SELECT max(computed_at)
                             FROM consumption.news_signal_performance)
    """, label="news_signal_performance")

    def _f(v):
        return float(v) if v is not None else None

    windows = {}
    buckets = []
    assets = []
    computed_at = None
    for r in rows:
        if computed_at is None and r.computed_at:
            computed_at = r.computed_at.isoformat()
        w = windows.setdefault(r.window, {"by_horizon": {}, "coverage": None})
        if r.segment_type == "coverage":
            w["coverage"] = {"pct": _f(r.coverage_pct), "n": r.sample_size}
            continue
        metric = {"hit_rate": _f(r.hit_rate),
                  "mean_return": _f(r.mean_return),
                  "ic": _f(r.information_coefficient),
                  "n": r.sample_size}
        if r.segment_type == "overall":
            w["by_horizon"][r.horizon] = metric
        elif (r.segment_type == "confidence_bucket" and r.horizon == "1d"
                and r.window == "30d"):
            buckets.append({"bucket": r.segment_value, "horizon": "1d",
                            "hit_rate": metric["hit_rate"], "n": r.sample_size})
        elif (r.segment_type == "asset_class" and r.horizon == "1d"
                and r.window == "30d"):
            assets.append({"asset_class": r.segment_value, "horizon": "1d",
                           "hit_rate": metric["hit_rate"], "n": r.sample_size})

    # every horizon key present; null = unavailable (e.g. stale 1h bars)
    for w in windows.values():
        for hz in ("1h", "1d", "5d"):
            w["by_horizon"].setdefault(hz, None)

    if not rows:
        status = "no_data"
    else:
        n_30d_1d = ((windows.get("30d") or {}).get("by_horizon", {})
                    .get("1d") or {}).get("n") or 0
        status = "ok" if n_30d_1d >= MIN_SAMPLE_TRUSTWORTHY else "insufficient_data"

    return {
        "data": {
            "status": status,
            "computed_at": computed_at,
            "min_sample_trustworthy": MIN_SAMPLE_TRUSTWORTHY,
            "windows": windows,
            "by_confidence_bucket": buckets,
            "by_asset_class": assets,
        },
        "as_of": _now_iso(),
    }
