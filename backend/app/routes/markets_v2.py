"""Market Status band endpoints for the redesigned Command Center (US + HK only).

Separate namespace (/api/markets/*) from the legacy /api/market/* routes used
by the old world-index framing — see design-bundle handoff/API_SPEC_v2.md §1.2.
"""
import time
from fastapi import APIRouter, Depends
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.db.safe_query import safe_query

router = APIRouter(prefix="/api/markets", tags=["markets_v2"])

# The Command Center ribbon polls the market band every 15s from every open
# browser tab. A short in-process cache keeps that from turning into 4 DB
# queries per tab per tick (this RDS has a history of pool exhaustion).
_OVERVIEW_TTL_S = 12
_overview_cache = {}  # regions key -> (monotonic_ts, payload)


def _now_iso():
    return datetime.now(timezone.utc).isoformat()


@router.get("/indices")
def get_dashboard_indices(regions: str = "US,HK", db: Session = Depends(get_db)):
    region_list = [r.strip() for r in regions.split(",") if r.strip()]
    rows = safe_query(db, """
        SELECT sym, name, region, last, change_pct,
               change_1d, change_1w, change_1m, change_ytd,
               est_1d, est_1w, est_1m, spark
        FROM consumption.dashboard_indices
        WHERE region = ANY(:regions) ORDER BY region, sym
    """, {"regions": region_list}, label="markets_indices")
    data = [{
        "sym": r.sym, "name": r.name, "region": r.region,
        "last": float(r.last) if r.last is not None else None,
        "change_pct": float(r.change_pct) if r.change_pct is not None else None,
        "change_1d": float(r.change_1d) if r.change_1d is not None else None,
        "change_1w": float(r.change_1w) if r.change_1w is not None else None,
        "change_1m": float(r.change_1m) if r.change_1m is not None else None,
        "change_ytd": float(r.change_ytd) if r.change_ytd is not None else None,
        "est_1d": r.est_1d,
        "est_1w": r.est_1w,
        "est_1m": r.est_1m,
        "spark": list(r.spark) if r.spark is not None else [],
    } for r in rows]
    return {"data": data, "as_of": _now_iso() if data else None}


@router.get("/breadth")
def get_market_breadth_v2(regions: str = "US,HK", db: Session = Depends(get_db)):
    region_list = [r.strip() for r in regions.split(",") if r.strip()]
    rows = safe_query(db, """
        SELECT region, advancing, declining, unchanged, new_highs, new_lows
        FROM consumption.market_breadth WHERE region = ANY(:regions)
    """, {"regions": region_list}, label="markets_breadth")
    data = {r.region.lower(): {
        "advancing": r.advancing, "declining": r.declining, "unchanged": r.unchanged,
        "new_highs": r.new_highs, "new_lows": r.new_lows,
    } for r in rows}
    return data


@router.get("/sentiment")
def get_market_sentiment_v2(regions: str = "US,HK", db: Session = Depends(get_db)):
    region_list = [r.strip().upper() for r in regions.split(",") if r.strip()]

    # qr_etl added region + regime columns to consumption.market_sentiment.
    # Query per-region; HK VIX/put_call are NULL because no dedicated HK feed is wired.
    rows = safe_query(db, """
        SELECT region, fear_greed, fear_greed_label, vix, vix_change_pct, put_call, regime
        FROM consumption.market_sentiment
        WHERE region = ANY(:regions)
        ORDER BY region
    """, {"regions": region_list}, label="markets_sentiment")
    data = {}
    for r in rows:
        data[r.region.lower()] = {
            "fear_greed": r.fear_greed,
            "fear_greed_label": r.fear_greed_label,
            "vix": float(r.vix) if r.vix is not None else None,
            "vix_change_pct": float(r.vix_change_pct) if r.vix_change_pct is not None else None,
            "put_call": float(r.put_call) if r.put_call is not None else None,
            "regime": r.regime,
        }

    # Fallback: legacy flat source for US when the DE view is empty.
    if "us" not in data:
        try:
            from app.main import get_market_sentiment
            us = get_market_sentiment(country="US", db=db)
            data["us"] = {
                "fear_greed": us.get("fearGreed"),
                "fear_greed_label": us.get("fearGreedLabel"),
                "vix": us.get("vix"),
                "vix_change_pct": None,
                "put_call": None,
                "regime": None,
            }
        except Exception:
            pass

    # Ensure requested regions always have a key (nulls render as "—" in the UI).
    for reg in region_list:
        reg_key = reg.lower()
        if reg_key not in data:
            data[reg_key] = {
                "fear_greed": None, "fear_greed_label": None,
                "vix": None, "vix_change_pct": None,
                "put_call": None, "regime": None,
            }

    # Fallback: keep legacy flat keys for backwards compatibility if only one region present.
    if len(data) == 1:
        return next(iter(data.values()))
    return data


@router.get("/movers")
def get_market_movers_v2(db: Session = Depends(get_db)):
    rows = safe_query(db, """
        SELECT direction, ticker, change_pct FROM consumption.market_movers
        ORDER BY direction, rank
    """, label="markets_movers")
    gainers = [{"ticker": r.ticker, "change_pct": float(r.change_pct)} for r in rows if r.direction == "gainer"]
    losers = [{"ticker": r.ticker, "change_pct": float(r.change_pct)} for r in rows if r.direction == "loser"]
    return {"gainers": gainers, "losers": losers}


@router.get("/overview")
def get_markets_overview(regions: str = "US,HK", db: Session = Depends(get_db)):
    """Single-call aggregate of indices + breadth + sentiment + movers.

    The Command Center's Market Status band previously made 4 HTTP requests
    per 15s poll tick; this collapses them to one, and the in-process cache
    means concurrent tabs / rapid polls share one set of DB queries.
    """
    key = ",".join(sorted(r.strip().upper() for r in regions.split(",") if r.strip()))
    cached = _overview_cache.get(key)
    if cached and (time.monotonic() - cached[0]) < _OVERVIEW_TTL_S:
        return cached[1]

    payload = {
        "indices": get_dashboard_indices(regions=regions, db=db),
        "breadth": get_market_breadth_v2(regions=regions, db=db),
        "sentiment": get_market_sentiment_v2(regions=regions, db=db),
        "movers": get_market_movers_v2(db=db),
        "as_of": _now_iso(),
    }
    _overview_cache[key] = (time.monotonic(), payload)
    return payload
