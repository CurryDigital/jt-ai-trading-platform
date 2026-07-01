"""Market Status band endpoints for the redesigned Command Center (US + HK only).

Separate namespace (/api/markets/*) from the legacy /api/market/* routes used
by the old world-index framing — see design-bundle handoff/API_SPEC_v2.md §1.2.
"""
from fastapi import APIRouter, Depends
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.db.safe_query import safe_query

router = APIRouter(prefix="/api/markets", tags=["markets_v2"])


def _now_iso():
    return datetime.now(timezone.utc).isoformat()


@router.get("/indices")
def get_dashboard_indices(regions: str = "US,HK", db: Session = Depends(get_db)):
    region_list = [r.strip() for r in regions.split(",") if r.strip()]
    rows = safe_query(db, """
        SELECT sym, name, region, last, change_pct, spark
        FROM consumption.dashboard_indices
        WHERE region = ANY(:regions) ORDER BY region, sym
    """, {"regions": region_list}, label="markets_indices")
    data = [{
        "sym": r.sym, "name": r.name, "region": r.region,
        "last": float(r.last) if r.last is not None else None,
        "change_pct": float(r.change_pct) if r.change_pct is not None else None,
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
def get_market_sentiment_v2(db: Session = Depends(get_db)):
    row_list = safe_query(db, """
        SELECT fear_greed, fear_greed_label, vix, vix_change_pct, put_call
        FROM consumption.market_sentiment LIMIT 1
    """, label="markets_sentiment")
    if not row_list:
        return {"fear_greed": None, "fear_greed_label": None, "vix": None, "vix_change_pct": None, "put_call": None}
    r = row_list[0]
    return {
        "fear_greed": r.fear_greed, "fear_greed_label": r.fear_greed_label,
        "vix": float(r.vix) if r.vix is not None else None,
        "vix_change_pct": float(r.vix_change_pct) if r.vix_change_pct is not None else None,
        "put_call": float(r.put_call) if r.put_call is not None else None,
    }


@router.get("/movers")
def get_market_movers_v2(db: Session = Depends(get_db)):
    rows = safe_query(db, """
        SELECT direction, ticker, change_pct FROM consumption.market_movers
        ORDER BY direction, rank
    """, label="markets_movers")
    gainers = [{"ticker": r.ticker, "change_pct": float(r.change_pct)} for r in rows if r.direction == "gainer"]
    losers = [{"ticker": r.ticker, "change_pct": float(r.change_pct)} for r in rows if r.direction == "loser"]
    return {"gainers": gainers, "losers": losers}
