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
                    db: Session = Depends(get_db)):
    """Research > News - analytics digest over silver.historical_news.

    Dedups wire-copy repetition (same story from N outlets -> one cluster with
    source count), scores attention (coverage x recency x impact keywords),
    tags market drivers, derives a directional tone heuristic, and extracts
    forward-looking events into a watch list. Everything is computed from real
    headlines; no predictions are fabricated.
    """
    per_group = max(10, min(per_group, 300))
    key_limit = max(1, min(key_limit, 20))
    hours = max(24, min(hours, 24 * 30))
    rows = safe_query(db, """
        SELECT category, date, entity_name, headline, source FROM (
            SELECT category, date, entity_name, headline, source,
                   ROW_NUMBER() OVER (PARTITION BY category ORDER BY date DESC, id DESC) AS rn
            FROM silver.historical_news
            WHERE category = ANY(:cats)
              AND date >= NOW() - INTERVAL '1 hour' * :hours
        ) t WHERE rn <= :per_group
        ORDER BY category, date DESC
    """, {"cats": NEWS_ASSET_ORDER, "per_group": per_group, "hours": hours},
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
        "last_updated": last_updated,
        "as_of": _now_iso(),
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
