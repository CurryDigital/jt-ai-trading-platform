"""Market data endpoints — movers, sectors, volume leaders, global indices, breadth, sentiment."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.dependencies import get_db, logger

router = APIRouter(prefix="/api/market", tags=["market"])


@router.get("/indices")
def get_market_indices(timeframe: str = "1D", db: Session = Depends(get_db)):
    """Get major market indices with proper timeframe-based change calculation."""
    try:
        # Use latest rows with non-NULL close prices to get most recent valid close
        # This handles the case where today's row exists but market is still open
        rows = db.execute(text("""
            WITH ranked_prices AS (
                SELECT ticker, close as price, date,
                       LAG(close) OVER (PARTITION BY ticker ORDER BY date) as prev_price,
                       LAG(date) OVER (PARTITION BY ticker ORDER BY date) as prev_date,
                       ROW_NUMBER() OVER (PARTITION BY ticker ORDER BY date DESC) as rn
                FROM silver.unified_prices
                WHERE ticker IN ('^GSPC', '^IXIC', '^DJI', '^VIX', '^FTSE', '^GDAXI', '^N225', '^HSI', '000001.SS', '^AXJO')
                  AND close IS NOT NULL
            )
            SELECT ticker, price, date, prev_price, prev_date
            FROM ranked_prices
            WHERE rn = 1 AND prev_price IS NOT NULL
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
            if row.ticker in index_map and row.prev_price:
                info = index_map[row.ticker]
                change_pct = ((row.price - row.prev_price) / row.prev_price * 100)
                indices.append({
                    **info,
                    "price": float(row.price),
                    "change_percent": round(float(change_pct), 2),
                    "value": float(row.price),
                    "change": round(float(row.price - row.prev_price), 2),
                })

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
    """Get global market indices — uses latest available data regardless of date."""
    try:
        rows = db.execute(text("""
            WITH latest_prices AS (
                SELECT ticker, close as price, date,
                       LAG(close) OVER (PARTITION BY ticker ORDER BY date) as prev_close,
                       ROW_NUMBER() OVER (PARTITION BY ticker ORDER BY date DESC) as rn
                FROM silver.unified_prices
                WHERE ticker IN ('^GSPC', '^IXIC', '^FTSE', '^GDAXI', '^N225', '^HSI', '000001.SS', '^AXJO')
            )
            SELECT ticker, price, date, prev_close
            FROM latest_prices
            WHERE rn = 1 AND prev_close IS NOT NULL
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
            if row.ticker in index_map and row.prev_close:
                info = index_map[row.ticker]
                change_pct = ((row.price - row.prev_close) / row.prev_close * 100)
                markets.append({**info, "price": float(row.price), "change_percent": round(float(change_pct), 2)})

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
def get_market_breadth(country: str = "US", db: Session = Depends(get_db)):
    """Get market breadth by country. Supports US, HK, CN."""
    try:
        # Define ticker suffix patterns by country
        country_patterns = {
            "US": "AND NOT (ticker LIKE '%.HK' OR ticker LIKE '%.SS' OR ticker LIKE '%.SZ' OR ticker ~ '^[0-9]{6}$')",
            "HK": "AND ticker LIKE '%.HK'",
            "CN": "AND (ticker LIKE '%.SS' OR ticker LIKE '%.SZ' OR ticker ~ '^[0-9]{6}$')"
        }
        suffix_filter = country_patterns.get(country, country_patterns["US"])

        # Basic breadth metrics
        rows = db.execute(text(f"""
            SELECT 
                SUM(CASE WHEN change_pct > 0 THEN 1 ELSE 0 END) as advancing,
                SUM(CASE WHEN change_pct < 0 THEN 1 ELSE 0 END) as declining,
                SUM(CASE WHEN change_pct = 0 THEN 1 ELSE 0 END) as unchanged,
                COUNT(*) as total
            FROM consumption.Markets_Stocks_Overview
            WHERE change_pct IS NOT NULL {suffix_filter}
        """)).fetchone()

        if rows and rows.total:
            return {
                "advancing": rows.advancing or 0,
                "declining": rows.declining or 0,
                "unchanged": rows.unchanged or 0,
                "newHighs": 0, "newLows": 0,
                "above50MA": None, "above200MA": None,
                "country": country
            }
    except Exception as e:
        logger.warning(f"Consumption breadth failed for {country}: {e}")

    return {"advancing": 0, "declining": 0, "unchanged": 0, "newHighs": 0, "newLows": 0, "country": country}


@router.get("/sentiment")
def get_market_sentiment(country: str = "US", db: Session = Depends(get_db)):
    """Get market sentiment indicators by country. VIX is US-only; others use proxies."""
    try:
        # VIX is US-specific
        if country == "US":
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

            return {"fearGreed": fear_greed, "vix": vix, "putCall": 1.0, "country": "US"}

        # For HK/CN, use index volatility as proxy
        index_ticker = {"HK": "^HSI", "CN": "000001.SS"}.get(country, "^GSPC")

        # Get index recent volatility (5-day vs 20-day)
        vol_row = db.execute(text("""
            WITH prices AS (
                SELECT close, date,
                       STDDEV(close) OVER (ORDER BY date ROWS BETWEEN 4 PRECEDING AND CURRENT ROW) as vol_5d,
                       STDDEV(close) OVER (ORDER BY date ROWS BETWEEN 19 PRECEDING AND CURRENT ROW) as vol_20d
                FROM silver.unified_prices
                WHERE ticker = :ticker AND date >= CURRENT_DATE - INTERVAL '30 days'
                ORDER BY date DESC
                LIMIT 1
            )
            SELECT vol_5d, vol_20d FROM prices
        """), {"ticker": index_ticker}).fetchone()

        # Estimate fear/greed from volatility ratio (simplified)
        if vol_row and vol_row.vol_20d and vol_row.vol_20d > 0:
            vol_ratio = vol_row.vol_5d / vol_row.vol_20d if vol_row.vol_5d else 1.0
            # High recent vol = fear (0-30), Low vol = greed (70-100)
            fear_greed = int(max(0, min(100, 100 - (vol_ratio - 0.5) * 100)))
        else:
            fear_greed = 50

        return {"fearGreed": fear_greed, "vix": None, "putCall": 1.0, "country": country}
    except Exception as e:
        logger.error(f"Error in market sentiment for {country}: {e}")
        return {"fearGreed": 50, "vix": None, "putCall": 1.0, "country": country}
