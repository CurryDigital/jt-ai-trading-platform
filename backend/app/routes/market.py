"""Market data endpoints — movers, sectors, volume leaders, global indices, breadth, sentiment."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.dependencies import get_db, logger

router = APIRouter(prefix="/api/market", tags=["market"])


@router.get("/indices")
def get_market_indices(timeframe: str = "1D", db: Session = Depends(get_db)):
    """Get major market indices — same as global but structured for MarketsTab."""
    try:
        rows = db.execute(text("""
            SELECT ticker, close as price, date,
                   LAG(close) OVER (PARTITION BY ticker ORDER BY date) as prev_close
            FROM silver.unified_prices
            WHERE ticker IN ('^GSPC', '^IXIC', '^DJI', '^VIX', '^FTSE', '^GDAXI', '^N225', '^HSI', '000001.SS', '^AXJO')
            AND date >= CURRENT_DATE - INTERVAL '5 days'
            ORDER BY date DESC
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

        seen = set()
        indices = []
        for row in rows:
            if row.ticker not in seen and row.ticker in index_map and row.prev_close:
                info = index_map[row.ticker]
                change_pct = ((row.price - row.prev_close) / row.prev_close * 100)
                indices.append({
                    **info,
                    "price": float(row.price),
                    "change_percent": round(float(change_pct), 2),
                    "value": float(row.price),
                    "change": round(float(row.price - row.prev_close), 2),
                })
                seen.add(row.ticker)

        if indices:
            return {"data": indices}
    except Exception as e:
        logger.error(f"Error in indices: {e}")

    # Fallback skeleton
    return {"data": [
        {"name": "S&P 500", "symbol": "SPX", "price": 0, "change_percent": 0, "value": 0, "change": 0},
        {"name": "Nasdaq", "symbol": "COMP", "price": 0, "change_percent": 0, "value": 0, "change": 0},
        {"name": "Dow Jones", "symbol": "DJI", "price": 0, "change_percent": 0, "value": 0, "change": 0},
    ]}


@router.get("/movers")
def get_market_movers(timeframe: str = "1D", db: Session = Depends(get_db)):
    """Get top gainers and losers from consumption view."""
    try:
        # Get stocks with non-zero change, properly separated
        rows = db.execute(text("""
            SELECT ticker, name, price, change_pct, volume, sector
            FROM consumption.Markets_Stocks_Overview
            WHERE change_pct IS NOT NULL AND change_pct != 0 AND price > 0
            ORDER BY change_pct DESC
        """)).fetchall()

        if rows:
            # Properly separate gainers (positive) from losers (negative)
            gainers = [{"ticker": r.ticker, "name": r.name or r.ticker, "price": float(r.price or 0), 
                        "change_percent": round(float(r.change_pct), 2),
                        "volume": r.volume} for r in rows if r.change_pct > 0][:10]
            
            losers = [{"ticker": r.ticker, "name": r.name or r.ticker, "price": float(r.price or 0),
                       "change_percent": round(float(r.change_pct), 2),
                       "volume": r.volume} for r in rows if r.change_pct < 0][:10]
            
            return {"gainers": gainers, "losers": losers, "source": "consumption", "count": len(rows)}
    except Exception as e:
        logger.warning(f"Consumption movers failed: {e}")

    return {"gainers": [], "losers": [], "source": "fallback", "message": "No market data available"}


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
    """Get global market indices from DB."""
    try:
        rows = db.execute(text("""
            SELECT ticker, close as price, 
                   LAG(close) OVER (PARTITION BY ticker ORDER BY date) as prev_close
            FROM silver.unified_prices
            WHERE ticker IN ('^GSPC', '^IXIC', '^FTSE', '^GDAXI', '^N225', '^HSI', '000001.SS', '^AXJO')
            AND date >= CURRENT_DATE - INTERVAL '5 days'
            ORDER BY date DESC
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

        seen = set()
        markets = []
        for row in rows:
            if row.ticker not in seen and row.ticker in index_map and row.prev_close:
                info = index_map[row.ticker]
                change_pct = ((row.price - row.prev_close) / row.prev_close * 100)
                markets.append({**info, "price": float(row.price), "change_percent": round(float(change_pct), 2)})
                seen.add(row.ticker)

        if markets:
            return {"data": markets}
    except Exception:
        pass

    # Fallback skeleton
    return {"data": [
        {"name": "S&P 500", "region": "US", "flag": "🇺🇸", "price": 0, "change_percent": 0},
        {"name": "Hang Seng", "region": "Asia", "flag": "🇭🇰", "price": 0, "change_percent": 0},
    ]}


@router.get("/breadth")
def get_market_breadth(db: Session = Depends(get_db)):
    """Get market breadth from consumption view."""
    try:
        # Try consumption view
        rows = db.execute(text("""
            SELECT 
                SUM(CASE WHEN change_pct > 0 THEN 1 ELSE 0 END) as advancing,
                SUM(CASE WHEN change_pct < 0 THEN 1 ELSE 0 END) as declining,
                SUM(CASE WHEN change_pct = 0 THEN 1 ELSE 0 END) as unchanged,
                COUNT(*) as total
            FROM consumption.Markets_Stocks_Overview
            WHERE change_pct IS NOT NULL
        """)).fetchone()

        if rows and rows.total:
            return {
                "advancing": rows.advancing or 0,
                "declining": rows.declining or 0,
                "unchanged": rows.unchanged or 0,
                "newHighs": 0, "newLows": 0,
                "above50MA": None, "above200MA": None,
                "overbought": None, "oversold": None,
            }
    except Exception as e:
        logger.warning(f"Consumption breadth failed: {e}")

    return {"advancing": 0, "declining": 0, "unchanged": 0, "newHighs": 0, "newLows": 0}


@router.get("/sentiment")
def get_market_sentiment(db: Session = Depends(get_db)):
    """Get market sentiment indicators from DB."""
    try:
        vix_row = db.execute(text("""
            SELECT close FROM silver.unified_prices
            WHERE ticker = '^VIX' ORDER BY date DESC LIMIT 1
        """)).fetchone()

        vix = float(vix_row.close) if vix_row and vix_row.close else 20.0

        if vix < 15:
            fear_greed = 75
        elif vix < 20:
            fear_greed = 55
        elif vix < 25:
            fear_greed = 50
        elif vix < 30:
            fear_greed = 35
        else:
            fear_greed = 20

        return {"fearGreed": fear_greed, "vix": vix, "putCall": 1.0}
    except Exception as e:
        logger.error(f"Error in market sentiment: {e}")
        return {"fearGreed": 50, "vix": 20.0, "putCall": 1.0}
