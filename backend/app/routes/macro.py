"""Research > Macro endpoints — regime forecast, KPIs, sectors, calendar, news.

See design-bundle handoff/API_SPEC_v2.md §2 and DB_CHANGES_v2.md §3.
"""
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
