"""HKEX IPO endpoints."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.dependencies import get_db

router = APIRouter(prefix="/api/hkex", tags=["hkex"])


@router.get("/ipos")
def get_hkex_ipos(status: str = None, sector: str = None, year: int = None, limit: int = 50,
                  db: Session = Depends(get_db)):
    query = """
        SELECT c.ticker, c.stock_name, c.listing_date, c.offer_price, c.market_cap_hkd,
               c.sector, c.sub_sector, c.sponsor,
               d.oversubscription_retail, d.oversubscription_institutional, d.cornerstone_total_pct,
               p.first_day_return_pct, p.return_day30_pct, p.performance_tier,
               CASE WHEN c.listing_date > CURRENT_DATE THEN 'Upcoming'
                    WHEN c.listing_date = CURRENT_DATE THEN 'Listing Today' ELSE 'Listed' END as status
        FROM gold.hk_ipo_calendar c
        LEFT JOIN gold.hk_ipo_details d ON c.ticker = d.ticker
        LEFT JOIN gold.hk_ipo_performance p ON c.ticker = p.ticker WHERE 1=1
    """
    params = {}
    if status == "upcoming": query += " AND c.listing_date >= CURRENT_DATE"
    elif status == "listed": query += " AND c.listing_date < CURRENT_DATE"
    if sector: query += " AND c.sector = :sector"; params["sector"] = sector
    if year: query += " AND EXTRACT(YEAR FROM c.listing_date) = :year"; params["year"] = year
    query += " ORDER BY c.listing_date DESC LIMIT :limit"; params["limit"] = limit

    result = db.execute(text(query), params).fetchall()
    return {"ipos": [{
        "ticker": r.ticker, "stock_name": r.stock_name, "listing_date": str(r.listing_date),
        "offer_price": float(r.offer_price) if r.offer_price else None,
        "market_cap_hkd": float(r.market_cap_hkd) if r.market_cap_hkd else None,
        "sector": r.sector, "sponsor": r.sponsor,
        "first_day_return": float(r.first_day_return_pct) if r.first_day_return_pct else None,
        "return_day30": float(r.return_day30_pct) if r.return_day30_pct else None,
        "performance_tier": r.performance_tier, "status": r.status,
    } for r in result], "count": len(result)}


@router.get("/ipos/leaderboard")
def get_hkex_ipo_leaderboard(period: str = "first_day", limit: int = 20, db: Session = Depends(get_db)):
    order_col = {"first_day": "p.first_day_return_pct", "day30": "p.return_day30_pct",
                 "total": "p.total_return_pct"}.get(period, "p.first_day_return_pct")
    result = db.execute(text(f"""
        SELECT c.ticker, c.stock_name, c.listing_date, c.offer_price, c.sector,
               p.first_day_return_pct, p.return_day30_pct, p.total_return_pct, p.performance_tier,
               d.oversubscription_retail, d.cornerstone_total_pct
        FROM gold.hk_ipo_performance p
        JOIN gold.hk_ipo_calendar c ON p.ticker = c.ticker
        LEFT JOIN gold.hk_ipo_details d ON p.ticker = d.ticker
        WHERE c.listing_date >= CURRENT_DATE - INTERVAL '2 years'
        ORDER BY {order_col} DESC NULLS LAST LIMIT :limit
    """), {"limit": limit}).fetchall()
    return {"leaderboard": [{"rank": i + 1, "ticker": r.ticker, "stock_name": r.stock_name,
                              "listing_date": str(r.listing_date), "sector": r.sector,
                              "first_day_return": float(r.first_day_return_pct) if r.first_day_return_pct else None,
                              "return_day30": float(r.return_day30_pct) if r.return_day30_pct else None,
                              "performance_tier": r.performance_tier}
                             for i, r in enumerate(result)], "count": len(result), "period": period}


@router.get("/ipos/sectors")
def get_hkex_ipo_sectors(db: Session = Depends(get_db)):
    result = db.execute(text("""
        SELECT c.sector, COUNT(*) as ipo_count,
               AVG(p.first_day_return_pct) as avg_first_day_return,
               AVG(p.return_day30_pct) as avg_day30_return,
               COUNT(CASE WHEN p.first_day_return_pct > 0 THEN 1 END)::DECIMAL / COUNT(*) * 100 as win_rate
        FROM gold.hk_ipo_calendar c
        JOIN gold.hk_ipo_performance p ON c.ticker = p.ticker
        WHERE c.listing_date >= CURRENT_DATE - INTERVAL '2 years'
        GROUP BY c.sector ORDER BY avg_first_day_return DESC NULLS LAST
    """)).fetchall()
    return {"sectors": [{"sector": r.sector, "ipo_count": r.ipo_count,
                          "avg_first_day_return": round(float(r.avg_first_day_return), 2) if r.avg_first_day_return else None,
                          "win_rate": round(float(r.win_rate), 1) if r.win_rate else None}
                         for r in result]}


@router.get("/ipos/{ticker}")
def get_hkex_ipo_detail(ticker: str, db: Session = Depends(get_db)):
    calendar = db.execute(text("SELECT * FROM gold.hk_ipo_calendar WHERE ticker = :ticker"), {"ticker": ticker}).fetchone()
    if not calendar:
        raise HTTPException(status_code=404, detail=f"IPO {ticker} not found")
    details = db.execute(text("SELECT * FROM gold.hk_ipo_details WHERE ticker = :ticker"), {"ticker": ticker}).fetchone()
    performance = db.execute(text("SELECT * FROM gold.hk_ipo_performance WHERE ticker = :ticker"), {"ticker": ticker}).fetchone()
    return {
        "ticker": calendar.ticker, "stock_name": calendar.stock_name,
        "listing_date": str(calendar.listing_date),
        "offer_price": float(calendar.offer_price) if calendar.offer_price else None,
        "sector": calendar.sector, "sponsor": calendar.sponsor,
        "details": {"oversubscription_retail": float(details.oversubscription_retail) if details and details.oversubscription_retail else None} if details else None,
        "performance": {"first_day_return": float(performance.first_day_return_pct) if performance and performance.first_day_return_pct else None,
                        "performance_tier": performance.performance_tier if performance else None} if performance else None,
    }
