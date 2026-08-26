"""Market data endpoints — movers, sectors, volume leaders, global indices, breadth, sentiment."""
import re
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.dependencies import get_db, logger

router = APIRouter(prefix="/api/market", tags=["market"])


@router.get("/indices")
def get_market_indices(timeframe: str = "1D", db: Session = Depends(get_db)):
    """Get major market indices from consumption view (INDEX market entries)."""
    try:
        rows = db.execute(text("""
            SELECT ticker, name, price, change_pct
            FROM consumption.markets_stocks_overview
            WHERE (market = 'INDEX' OR ticker = '^VIX')
              AND ticker IN ('^GSPC', '^IXIC', '^DJI', '^VIX', '^FTSE', '^GDAXI', '^N225', '^HSI', '000001.SS', '^AXJO')
              AND price > 0
        """)).fetchall()

        index_map = {
            "^GSPC": {"name": "S&P 500", "symbol": "SPX"},
            "^IXIC": {"name": "Nasdaq", "symbol": "COMP"},
            "^DJI": {"name": "Dow Jones", "symbol": "DJI"},
            "^VIX": {"name": "VIX", "symbol": "VIX"},
            "^FTSE": {"name": "FTSE 100", "symbol": "UKX"},
            "^GDAXI": {"name": "DAX", "symbol": "DAX"},
            "^N225": {"name": "Nikkei 225", "symbol": "N225"},
            "^HSI": {"name": "Hang Seng", "symbol": "HSI"},
            "000001.SS": {"name": "Shanghai", "symbol": "SHCOMP"},
            "^AXJO": {"name": "ASX 200", "symbol": "ASX"},
        }

        indices = []
        for row in rows:
            if row.ticker in index_map:
                info = index_map[row.ticker]
                indices.append({
                    **info,
                    "price": float(row.price),
                    "change_percent": round(float(row.change_pct or 0), 2),
                    "value": float(row.price),
                    "change": round(float(row.price) * float(row.change_pct or 0) / 100, 2),
                })

        if indices:
            return {"data": indices}
    except Exception as e:
        logger.error(f"Error in indices: {e}")

    return {"data": []}


@router.get("/movers")
def get_market_movers(timeframe: str = "1D", market: str = None, db: Session = Depends(get_db)):
    """Get top gainers and losers from consumption view. Optional market filter: US, HK, CN, SG."""
    try:
        # Build query with optional market filter
        market_val = market.upper() if market else None
        if market_val and market_val in ("US", "HK", "CN", "SG"):
            rows = db.execute(text("""
                SELECT ticker, name, price, change_pct, volume, sector
                FROM consumption.markets_stocks_overview
                WHERE change_pct IS NOT NULL AND price > 0 AND market = :market
                ORDER BY change_pct DESC
            """), {"market": market_val}).fetchall()
        else:
            rows = db.execute(text("""
                SELECT ticker, name, price, change_pct, volume, sector
                FROM consumption.markets_stocks_overview
                WHERE change_pct IS NOT NULL AND price > 0
                ORDER BY change_pct DESC
            """)).fetchall()

        if rows:
            # Separate gainers (positive) from losers (negative)
            gainers = [{"ticker": r.ticker, "name": r.name or r.ticker, "price": float(r.price or 0),
                        "change_percent": round(float(r.change_pct), 2),
                        "volume": r.volume} for r in rows if r.change_pct > 0][:10]

            # rows is sorted DESC, so negatives are at the end. Take the last 10 negatives (biggest drops)
            negative_rows = [r for r in rows if r.change_pct < 0]
            losers = [{"ticker": r.ticker, "name": r.name or r.ticker, "price": float(r.price or 0),
                       "change_percent": round(float(r.change_pct), 2),
                       "volume": r.volume} for r in negative_rows[-10:]][::-1]

            # If no losers with negative change, get biggest drops (closest to zero from negative side)
            if not losers:
                losers = [{"ticker": r.ticker, "name": r.name or r.ticker, "price": float(r.price or 0),
                           "change_percent": round(float(r.change_pct), 2),
                           "volume": r.volume} for r in rows if r.change_pct <= 0][:10]

            return {"gainers": gainers, "losers": losers, "source": "consumption", "count": len(rows), "market": market}
    except Exception as e:
        logger.warning(f"Consumption movers failed: {e}")

    return {"gainers": [], "losers": [], "source": "fallback", "message": "No market data available", "market": market}


@router.get("/sectors")
def get_market_sectors(db: Session = Depends(get_db)):
    """Get sector performance."""
    try:
        rows = db.execute(text("""
            SELECT sector,
                   AVG(change_pct) as avg_change,
                   COUNT(*) as stock_count
            FROM consumption.Markets_Stocks_Overview
            WHERE sector IS NOT NULL
            GROUP BY sector
            ORDER BY avg_change DESC
        """)).fetchall()

        if rows:
            return {"data": [{
                "name": r.sector,
                "change_percent": round(float(r.avg_change or 0), 2),
                "stock_count": r.stock_count,
            } for r in rows]}
    except Exception:
        pass

    # Fallback: static structure (DE will populate consumption views)
    sectors = [
        {"name": "Technology", "change_percent": 0, "icon": "💻"},
        {"name": "Healthcare", "change_percent": 0, "icon": "🏥"},
        {"name": "Finance", "change_percent": 0, "icon": "🏦"},
        {"name": "Energy", "change_percent": 0, "icon": "⛽"},
        {"name": "Consumer", "change_percent": 0, "icon": "🛒"},
        {"name": "Industrial", "change_percent": 0, "icon": "🏭"},
        {"name": "Materials", "change_percent": 0, "icon": "🏗️"},
        {"name": "Utilities", "change_percent": 0, "icon": "💡"},
    ]
    return {"data": sectors}


@router.get("/volume-leaders")
def get_volume_leaders(db: Session = Depends(get_db)):
    """Get stocks with highest volume from consumption view."""
    try:
        rows = db.execute(text("""
            SELECT ticker, name, price, volume, change_pct
            FROM consumption.Markets_Stocks_Overview
            WHERE volume IS NOT NULL
            ORDER BY volume DESC
            LIMIT 20
        """)).fetchall()

        if rows:
            return {"data": [{"ticker": r.ticker, "name": r.name or r.ticker, 
                    "price": float(r.price or 0), "volume": r.volume,
                    "change_percent": round(float(r.change_pct or 0), 2)} for r in rows]}
    except Exception as e:
        logger.warning(f"Consumption volume failed: {e}")

    # Fallback
    return {"data": []}


@router.get("/global")
def get_global_markets(db: Session = Depends(get_db)):
    """Get global market indices from consumption view (INDEX market entries)."""
    try:
        rows = db.execute(text("""
            SELECT ticker, name, price, change_pct
            FROM consumption.markets_stocks_overview
            WHERE market = 'INDEX'
              AND ticker IN ('^GSPC', '^IXIC', '^FTSE', '^GDAXI', '^N225', '^HSI', '000001.SS', '^AXJO')
              AND price > 0
        """)).fetchall()

        index_map = {
            "^GSPC": {"name": "S&P 500", "region": "US", "flag": "🇺🇸"},
            "^IXIC": {"name": "Nasdaq", "region": "US", "flag": "🇺🇸"},
            "^FTSE": {"name": "FTSE 100", "region": "Europe", "flag": "🇬🇧"},
            "^GDAXI": {"name": "DAX", "region": "Europe", "flag": "🇩🇪"},
            "^N225": {"name": "Nikkei 225", "region": "Asia", "flag": "🇯🇵"},
            "^HSI": {"name": "Hang Seng", "region": "Asia", "flag": "🇭🇰"},
            "000001.SS": {"name": "Shanghai", "region": "Asia", "flag": "🇨🇳"},
            "^AXJO": {"name": "ASX 200", "region": "Asia", "flag": "🇦🇺"},
        }

        markets = []
        for row in rows:
            if row.ticker in index_map:
                info = index_map[row.ticker]
                markets.append({
                    **info,
                    "price": float(row.price),
                    "change_percent": round(float(row.change_pct or 0), 2)
                })

        if markets:
            return {"data": markets}
    except Exception:
        pass

    return {"data": []}


@router.get("/breadth")
def get_market_breadth(country: str = "US", db: Session = Depends(get_db)):
    """Get market breadth by country. Supports US, HK, CN.
    
    Calculates 52-week highs from distance_to_52w_high_pct (stocks within 0.5% of their 52w high).
    52-week lows and MA percentages are returned as None when underlying data is unavailable.
    """
    try:
        # Define market filter by country
        market_filter = {"US": "market = 'US'", "HK": "market = 'HK'", "CN": "market = 'CN'"}.get(country, "market = 'US'")

        # Basic breadth metrics + 52w highs from consumption view
        rows = db.execute(text(f"""
            SELECT 
                SUM(CASE WHEN change_pct > 0 THEN 1 ELSE 0 END) as advancing,
                SUM(CASE WHEN change_pct < 0 THEN 1 ELSE 0 END) as declining,
                SUM(CASE WHEN change_pct = 0 THEN 1 ELSE 0 END) as unchanged,
                COUNT(*) as total,
                SUM(CASE WHEN distance_to_52w_high_pct IS NOT NULL 
                          AND distance_to_52w_high_pct >= -0.5 THEN 1 ELSE 0 END) as new_highs
            FROM consumption.markets_stocks_overview
            WHERE change_pct IS NOT NULL AND {market_filter}
        """)).fetchone()

        result = {
            "advancing": rows.advancing or 0,
            "declining": rows.declining or 0,
            "unchanged": rows.unchanged or 0,
            "newHighs": rows.new_highs or 0,
            "newLows": None,       # Data unavailable: distance_to_52w_low_pct is NULL for all rows
            "above50MA": None,     # Data unavailable: no MA data in consumption view or historical table
            "above200MA": None,    # Data unavailable: no MA data in consumption view or historical table
            "country": country
        }
        return result

    except Exception as e:
        logger.warning(f"Consumption breadth failed for {country}: {e}")

    return {"advancing": 0, "declining": 0, "unchanged": 0, "newHighs": 0, "newLows": None, "above50MA": None, "above200MA": None, "country": country}


# ---------------------------------------------------------------------------
# News portfolio layer (kanban t_03bdbbfa): price move since a story broke.
# ---------------------------------------------------------------------------
_DELTA_TICKER_RE = re.compile(r"^[A-Z0-9][A-Z0-9.=-]{0,11}$")
_INTRADAY_FRESH_H = 36  # intraday bars older than this are treated as stale


@router.get("/delta-since")
def get_delta_since(ticker: str, since: str, db: Session = Depends(get_db)):
    """Price move (%) since a story broke.

    GET /api/market/delta-since?ticker=SPY&since=2026-08-11T14:00:00
      -> {ticker, pct, ref_ts, ref_px, last_ts, last_px, source}

    Source priority:
      1. 'intraday' — bronze.ibkr_historical_bars, only when the contract's
         latest bar is <= 36h old (the IBKR bar ingest is currently STALE,
         max bar_time 2026-07-03, so this path is dormant until it is
         refreshed).
      2. 'daily'    — gold.daily_ohlcv fallback. ref = close of the latest
         daily bar stamped (date 21:00 UTC) at-or-before `since`; if none,
         the earliest bar after `since`. Daily granularity is an
         approximation — `source` lets the UI label it.

    400 on bad ticker/since, 404 when no price data exists for the ticker.
    """
    t = (ticker or "").strip().upper()
    if not _DELTA_TICKER_RE.match(t):
        raise HTTPException(status_code=400,
                            detail=f"invalid ticker '{ticker}'")
    try:
        since_dt = datetime.fromisoformat((since or "").replace("Z", "+00:00"))
    except ValueError:
        raise HTTPException(status_code=400,
                            detail=f"invalid since '{since}' (ISO 8601)")
    if since_dt.tzinfo is None:
        since_dt = since_dt.replace(tzinfo=timezone.utc)
    now = datetime.now(timezone.utc)

    def _payload(ref_ts, ref_px, last_ts, last_px, source):
        ref_px, last_px = float(ref_px), float(last_px)
        pct = round((last_px / ref_px - 1.0) * 100.0, 4) if ref_px else None
        return {"ticker": t, "pct": pct,
                "ref_ts": ref_ts, "ref_px": ref_px,
                "last_ts": last_ts, "last_px": last_px,
                "source": source}

    # 1. intraday (dormant while IBKR ingest is stale)
    sym = re.split(r"[.=-]", t)[0]  # platform -> IBKR contract symbol base
    try:
        fresh = db.execute(text("""
            SELECT max(b.bar_time) AS last_ts
            FROM bronze.ibkr_historical_bars b
            JOIN bronze.ibkr_contracts c ON c.con_id = b.con_id
            WHERE c.symbol = :sym
        """), {"sym": sym}).fetchone()
        if (fresh and fresh.last_ts
                and (now - fresh.last_ts).total_seconds() <= _INTRADAY_FRESH_H * 3600):
            ref = db.execute(text("""
                SELECT b.bar_time, b.close
                FROM bronze.ibkr_historical_bars b
                JOIN bronze.ibkr_contracts c ON c.con_id = b.con_id
                WHERE c.symbol = :sym AND b.bar_time <= :since
                ORDER BY b.bar_time DESC LIMIT 1
            """), {"sym": sym, "since": since_dt}).fetchone()
            last = db.execute(text("""
                SELECT b.bar_time, b.close
                FROM bronze.ibkr_historical_bars b
                JOIN bronze.ibkr_contracts c ON c.con_id = b.con_id
                WHERE c.symbol = :sym
                ORDER BY b.bar_time DESC LIMIT 1
            """), {"sym": sym}).fetchone()
            if ref and last:
                return _payload(ref.bar_time.isoformat(), ref.close,
                                last.bar_time.isoformat(), last.close,
                                "intraday")
    except Exception as e:
        logger.warning(f"delta-since intraday path failed for {t}: {e}")
        db.rollback()

    # 2. daily fallback (gold.daily_ohlcv)
    try:
        ref = db.execute(text("""
            SELECT date, close FROM gold.daily_ohlcv
            WHERE ticker = :t
              AND (date + interval '21 hours') AT TIME ZONE 'UTC' <= :since
            ORDER BY date DESC LIMIT 1
        """), {"t": t, "since": since_dt}).fetchone()
        if not ref:  # story predates coverage — use first bar after it
            ref = db.execute(text("""
                SELECT date, close FROM gold.daily_ohlcv
                WHERE ticker = :t AND date > CAST(:since AS date)
                ORDER BY date ASC LIMIT 1
            """), {"t": t, "since": since_dt}).fetchone()
        last = db.execute(text("""
            SELECT date, close FROM gold.daily_ohlcv
            WHERE ticker = :t
            ORDER BY date DESC LIMIT 1
        """), {"t": t}).fetchone()
    except Exception as e:
        logger.warning(f"delta-since daily path failed for {t}: {e}")
        db.rollback()
        ref = last = None

    if not ref or not last:
        raise HTTPException(status_code=404,
                            detail=f"no price data for ticker '{t}'")
    return _payload(ref.date.isoformat() + "T21:00:00+00:00", ref.close,
                    last.date.isoformat() + "T21:00:00+00:00", last.close,
                    "daily")