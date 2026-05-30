"""Market data endpoints — movers, sectors, volume leaders, global indices, breadth, sentiment."""
from fastapi import APIRouter, Depends
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