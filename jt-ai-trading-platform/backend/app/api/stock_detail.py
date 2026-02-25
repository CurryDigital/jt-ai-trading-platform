"""
Stock Detail API Endpoint
Returns historical data + metrics for a specific ticker
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from pydantic import BaseModel
from typing import List
from app.db.session import SessionLocal
from sqlalchemy import text

router = APIRouter()

class StockDataPoint(BaseModel):
    date: str
    open: float
    high: float
    low: float
    close: float
    volume: float
    returns: Optional[float]

class StockDetailResponse(BaseModel):
    ticker: str
    total_rows: int
    date_range: dict
    data: List[StockDataPoint]
    summary: dict

@router.get("/api/stock/detail")
async def get_stock_detail(
    ticker: str = Query(..., description="Stock ticker symbol"),
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    limit: int = Query(5000, description="Max rows to return")
):
    """
    Get historical OHLCV data for a specific ticker from silver layer.
    """
    db = SessionLocal()
    
    try:
        # Build query
        query = """
            SELECT 
                date,
                open,
                high,
                low,
                close,
                volume,
                returns
            FROM silver.historical_stock_data
            WHERE ticker = :ticker
        """
        
        params = {"ticker": ticker.upper()}
        
        if start_date:
            query += " AND date >= :start_date"
            params["start_date"] = start_date
        
        if end_date:
            query += " AND date <= :end_date"
            params["end_date"] = end_date
        
        query += " ORDER BY date ASC LIMIT :limit"
        params["limit"] = limit
        
        # Fetch data
        result = db.execute(text(query), params)
        rows = result.fetchall()
        
        if not rows:
            raise HTTPException(status_code=404, detail=f"No data found for ticker: {ticker}")
        
        # Get summary stats
        summary_query = """
            SELECT 
                COUNT(*) as total,
                MIN(date) as earliest,
                MAX(date) as latest,
                MIN(close) as min_price,
                MAX(close) as max_price,
                AVG(close) as avg_price,
                AVG(volume) as avg_volume
            FROM silver.historical_stock_data
            WHERE ticker = :ticker
        """
        
        summary = db.execute(text(summary_query), {"ticker": ticker.upper()}).fetchone()
        
        # Format response
        data_points = [
            StockDataPoint(
                date=str(row.date),
                open=round(row.open, 2) if row.open else None,
                high=round(row.high, 2) if row.high else None,
                low=round(row.low, 2) if row.low else None,
                close=round(row.close, 2) if row.close else None,
                volume=round(row.volume, 0) if row.volume else None,
                returns=round(row.returns, 4) if row.returns else None
            )
            for row in rows
        ]
        
        return StockDetailResponse(
            ticker=ticker.upper(),
            total_rows=len(data_points),
            date_range={
                "start": str(summary.earliest),
                "end": str(summary.latest)
            },
            data=data_points,
            summary={
                "min_price": round(summary.min_price, 2),
                "max_price": round(summary.max_price, 2),
                "avg_price": round(summary.avg_price, 2),
                "avg_volume": round(summary.avg_volume, 0),
                "total_days": summary.total
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

@router.get("/api/stock/list")
async def get_stock_list():
    """
    Get list of all available tickers in silver layer.
    """
    db = SessionLocal()
    
    try:
        result = db.execute(text("""
            SELECT 
                ticker,
                COUNT(*) as days,
                MIN(date) as earliest,
                MAX(date) as latest
            FROM silver.historical_stock_data
            GROUP BY ticker
            ORDER BY ticker
        """))
        
        tickers = [
            {
                "ticker": row.ticker,
                "days": row.days,
                "earliest": str(row.earliest),
                "latest": str(row.latest)
            }
            for row in result.fetchall()
        ]
        
        return {
            "total": len(tickers),
            "tickers": tickers
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()
