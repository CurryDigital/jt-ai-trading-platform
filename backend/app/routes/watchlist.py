"""Watchlist endpoint — News portfolio layer (kanban t_03bdbbfa).

Serves consumption.watchlist, refreshed every 2h by qr_etl cron
'news_clusters_refresh' (build_watchlist.py): active-strategy holdings
(source='positions') + curated macro instruments (source='core') + any
manually-added rows (source='manual').
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.db.safe_query import safe_query

router = APIRouter(prefix="/api", tags=["watchlist"])


@router.get("/watchlist")
def get_watchlist(db: Session = Depends(get_db)):
    """News > portfolio layer: tickers the desk watches.

    Returns {tickers: [...], by_source: {...}, as_of}. Empty list on missing
    table (graceful degradation — UI falls back to positions-only join).
    """
    rows = safe_query(db, """
        SELECT ticker, source, updated_at
        FROM consumption.watchlist
        ORDER BY ticker
    """, label="watchlist")

    tickers = [r.ticker for r in rows]
    by_source = {}
    as_of = None
    for r in rows:
        by_source.setdefault(r.source, []).append(r.ticker)
        ts = r.updated_at.isoformat() if r.updated_at else None
        if ts and (as_of is None or ts > as_of):
            as_of = ts

    return {"tickers": tickers, "by_source": by_source, "as_of": as_of,
            "source": "watchlist"}
