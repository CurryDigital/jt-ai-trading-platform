"""Research > Signals & Analytics endpoints — multi-family setups, proximity, feed.

See design-bundle handoff/API_SPEC_v2.md §3-4 and DB_CHANGES_v2.md §4.
"""
from fastapi import APIRouter, Depends
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.db.safe_query import safe_query

router = APIRouter(prefix="/api/signals", tags=["signals"])

MARKETS = ["US", "HK", "CRYPTO", "FX", "METAL"]


def _now_iso():
    return datetime.now(timezone.utc).isoformat()


def _market_list(markets: str):
    return [m.strip() for m in markets.split(",") if m.strip()] or MARKETS


@router.get("/universe")
def get_signal_universe(markets: str = "US,HK,CRYPTO,FX,METAL", limit: int = 8, db: Session = Depends(get_db)):
    market_list = _market_list(markets)
    rows = safe_query(db, """
        SELECT market, ticker, name, families, direction, potential, change_pct, note
        FROM consumption.signal_setups WHERE market = ANY(:markets)
        ORDER BY market, potential DESC
    """, {"markets": market_list}, label="signal_universe")
    data = {}
    for r in rows:
        bucket = data.setdefault(r.market, [])
        if len(bucket) >= limit:
            continue
        bucket.append({
            "ticker": r.ticker, "name": r.name,
            "families": list(r.families) if r.families is not None else [],
            "direction": r.direction, "potential": float(r.potential) if r.potential is not None else None,
            "change_pct": float(r.change_pct) if r.change_pct is not None else None, "note": r.note,
        })
    return {"data": data, "as_of": _now_iso() if rows else None}


@router.get("/families")
def get_signal_families(db: Session = Depends(get_db)):
    rows = safe_query(db, """
        SELECT family_key, label, strategy_id, strategy_name, deployed, color
        FROM gold.signal_families ORDER BY family_key
    """, label="signal_families")
    data = [{
        "key": r.family_key, "label": r.label, "strategy_id": r.strategy_id,
        "strategy_name": r.strategy_name, "deployed": bool(r.deployed), "color": r.color,
    } for r in rows]
    return {"data": data}


@router.get("/performance")
def get_signal_performance(markets: str = "US,HK,CRYPTO,FX,METAL", db: Session = Depends(get_db)):
    market_list = _market_list(markets)
    rows = safe_query(db, """
        SELECT market, family, hit_rate, fwd_return_5d, n_trades
        FROM consumption.signal_performance WHERE market = ANY(:markets)
    """, {"markets": market_list}, label="signal_performance")
    data = {}
    for r in rows:
        data.setdefault(r.market, []).append({
            "family": r.family, "hit_rate": float(r.hit_rate) if r.hit_rate is not None else None,
            "fwd_return_5d": float(r.fwd_return_5d) if r.fwd_return_5d is not None else None,
            "n_trades": r.n_trades,
        })
    return {"data": data}


@router.get("/proximity")
def get_signal_proximity(markets: str = "US,HK,CRYPTO,FX,METAL", db: Session = Depends(get_db)):
    market_list = _market_list(markets)
    rows = safe_query(db, """
        SELECT market, ticker, family, distance_pct, direction
        FROM consumption.signal_proximity WHERE market = ANY(:markets)
        ORDER BY market, distance_pct
    """, {"markets": market_list}, label="signal_proximity")
    data = {}
    for r in rows:
        data.setdefault(r.market, []).append({
            "ticker": r.ticker, "family": r.family,
            "distance_pct": float(r.distance_pct) if r.distance_pct is not None else None,
            "direction": r.direction,
        })
    return {"data": data}


@router.get("/feed")
def get_signal_feed(markets: str = "US,HK,CRYPTO,FX,METAL", limit: int = 4, db: Session = Depends(get_db)):
    market_list = _market_list(markets)
    rows = safe_query(db, """
        SELECT market, fired_at, signal, ticker, strategy, confidence
        FROM consumption.signal_feed WHERE market = ANY(:markets)
        ORDER BY market, fired_at DESC
    """, {"markets": market_list}, label="signal_feed")
    data = {}
    for r in rows:
        bucket = data.setdefault(r.market, [])
        if len(bucket) >= limit:
            continue
        bucket.append({
            "ts": r.fired_at.strftime("%H:%M") if r.fired_at else None,
            "signal": r.signal, "ticker": r.ticker, "strategy": r.strategy,
            "confidence": float(r.confidence) if r.confidence is not None else None,
        })
    return {"data": data}
