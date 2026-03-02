"""Market data endpoints — movers, sectors, volume leaders, global indices, breadth, sentiment."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.dependencies import get_db, logger

router = APIRouter(prefix="/api/market", tags=["market"])


@router.get("/movers")
def get_market_movers(timeframe: str = "1D", db: Session = Depends(get_db)):
    """Get top gainers and losers from DB."""
    try:
        rows = db.execute(text("""
            WITH price_changes AS (
                SELECT 
                    ticker, close, date,
                    LAG(close) OVER (PARTITION BY ticker ORDER BY date DESC) as prev_close,
                    ROW_NUMBER() OVER (PARTITION BY ticker ORDER BY date DESC) as rn
                FROM silver.unified_prices
                WHERE date >= CURRENT_DATE - INTERVAL '5 days'
            )
            SELECT ticker, close, prev_close,
                   CASE WHEN prev_close > 0 AND prev_close IS NOT NULL 
                        THEN ((close - prev_close) / prev_close * 100) 
                        ELSE 0 
                   END as change_pct
            FROM price_changes
            WHERE rn = 1 AND prev_close IS NOT NULL
            ORDER BY change_pct DESC
        """)).fetchall()

        if not rows:
            return {"gainers": [], "losers": [], "source": "database", "message": "No recent price data"}

        ticker_changes = {}
        for row in rows:
            if row.ticker not in ticker_changes and row.change_pct is not None:
                ticker_changes[row.ticker] = {
                    "ticker": row.ticker,
                    "price": float(row.close),
                    "change_percent": float(row.change_pct),
                    "name": row.ticker,
                }

        sorted_stocks = sorted(ticker_changes.values(), key=lambda x: x["change_percent"], reverse=True)
        return {"gainers": sorted_stocks[:10], "losers": sorted_stocks[-10:][::-1], "source": "database"}
    except Exception as e:
        logger.error(f"Error in market movers: {e}")
        return {"gainers": [], "losers": [], "error": str(e)}


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
    """Get stocks with unusual volume."""
    try:
        rows = db.execute(text("""
            SELECT ticker, close as price, volume,
                   AVG(volume) OVER (PARTITION BY ticker ORDER BY date ROWS BETWEEN 20 PRECEDING AND 1 PRECEDING) as avg_volume
            FROM silver.unified_prices
            WHERE date >= CURRENT_DATE - INTERVAL '1 day'
            ORDER BY date DESC
            LIMIT 50
        """)).fetchall()

        leaders = []
        seen = set()
        for row in rows:
            if row.ticker not in seen and row.avg_volume and row.avg_volume > 0:
                volume_ratio = row.volume / row.avg_volume
                if volume_ratio > 1.5:
                    leaders.append({
                        "ticker": row.ticker,
                        "name": row.ticker,
                        "price": float(row.price),
                        "volume_ratio": float(volume_ratio),
                        "change_percent": 0.0,
                    })
                    seen.add(row.ticker)

        return {"data": leaders[:12]}
    except Exception as e:
        logger.error(f"Error in volume leaders: {e}")
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
    """Get market breadth indicators."""
    try:
        rows = db.execute(text("""
            WITH latest_changes AS (
                SELECT ticker, close,
                       LAG(close) OVER (PARTITION BY ticker ORDER BY date) as prev_close
                FROM silver.unified_prices
                WHERE date >= CURRENT_DATE - INTERVAL '1 day'
            )
            SELECT 
                SUM(CASE WHEN close > prev_close THEN 1 ELSE 0 END) as advancing,
                SUM(CASE WHEN close < prev_close THEN 1 ELSE 0 END) as declining,
                SUM(CASE WHEN close = prev_close THEN 1 ELSE 0 END) as unchanged
            FROM latest_changes
            WHERE prev_close IS NOT NULL
        """)).fetchone()

        return {
            "advancing": rows.advancing or 0,
            "declining": rows.declining or 0,
            "unchanged": rows.unchanged or 0,
            "newHighs": 0, "newLows": 0,
            "above50MA": None, "above200MA": None,
            "overbought": None, "oversold": None,
        }
    except Exception as e:
        logger.error(f"Error in market breadth: {e}")
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
