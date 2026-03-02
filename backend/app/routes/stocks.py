"""Stock endpoints — overview and detail, all DB-only."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.dependencies import get_db, logger

router = APIRouter(prefix="/api/stocks", tags=["stocks"])


@router.get("/all")
def get_all_stocks(db: Session = Depends(get_db)):
    """Get all stock data from consumption layer."""
    try:
        stocks = db.execute(text("""
            SELECT ticker, name, sector, market, price, change_pct as daily_change,
                   volume, trend, rsi_14, top_strategy_score as final_score,
                   signal as action, signal_strength as confidence, pe_ratio, market_cap
            FROM consumption.Markets_Stocks_Overview
            ORDER BY top_strategy_score DESC NULLS LAST
        """)).fetchall()

        return [{
            "ticker": s.ticker,
            "name": s.name,
            "sector": s.sector,
            "market": s.market,
            "price": float(s.price or 0),
            "change": round(float(s.daily_change or 0), 2),
            "change5d": None,
            "change1m": None,
            "changeYTD": None,
            "volume": s.volume,
            "trend": s.trend or "NEUTRAL",
            "rsi": float(s.rsi_14 or 50),
            "score": float(s.final_score or 0) * 100 if s.final_score else 0,
            "action": s.action or "HOLD",
            "confidence": round((s.confidence or 0) * 100, 1),
            "pe": float(s.pe_ratio or 0) if s.pe_ratio else None,
            "market_cap": s.market_cap,
        } for s in stocks]
    except Exception as e:
        logger.error(f"Error fetching stocks: {e}")
        return []


@router.get("/consensus/top-upside")
def get_top_upside_stocks(limit: int = 20, db: Session = Depends(get_db)):
    """Get stocks with highest analyst upside potential."""
    result = db.execute(text("""
        SELECT c.ticker, c.target_mean, c.current_price, c.upside_pct, c.total_analysts,
               (c.strong_buy + c.buy) as buy_count, c.hold, (c.sell + c.strong_sell) as sell_count
        FROM gold.consensus_ratings c
        WHERE c.upside_pct IS NOT NULL AND c.total_analysts >= 5
        ORDER BY c.upside_pct DESC LIMIT :limit
    """), {"limit": limit}).fetchall()

    return [{
        "ticker": r.ticker,
        "target": float(r.target_mean) if r.target_mean else None,
        "current": float(r.current_price) if r.current_price else None,
        "upside_pct": float(r.upside_pct) if r.upside_pct else None,
        "analysts": r.total_analysts,
        "buy": r.buy_count, "hold": r.hold, "sell": r.sell_count,
        "rating": "STRONG_BUY" if (r.buy_count / r.total_analysts) > 0.7
                  else "BUY" if (r.buy_count / r.total_analysts) > 0.5 else "HOLD",
    } for r in result]


@router.get("/{ticker}")
def get_stock_detail(ticker: str, timeframe: str = "ytd", db: Session = Depends(get_db)):
    """Get detailed stock data with technicals — DB only, no yfinance."""
    ticker = ticker.upper()
    try:
        # Get overview data
        overview = db.execute(text("""
            SELECT ticker, name, sector, market, price, change_pct as daily_change,
                   rsi_14, trend, signal, signal_strength, pe_ratio, market_cap
            FROM consumption.Markets_Stocks_Overview
            WHERE ticker = :ticker
        """), {"ticker": ticker}).fetchone()

        if not overview:
            raise HTTPException(status_code=404, detail=f"Ticker {ticker} not found in consumption layer")

        # Get chart data from silver.unified_prices
        period_map = {"1m": "1 month", "ytd": "1 year", "12m": "1 year", "all": "5 years"}
        interval = period_map.get(timeframe, "1 year")

        prices = db.execute(text(f"""
            SELECT date, open, high, low, close, volume
            FROM silver.unified_prices
            WHERE ticker = :ticker AND date >= CURRENT_DATE - INTERVAL '{interval}'
            ORDER BY date ASC
        """), {"ticker": ticker}).fetchall()

        # Calculate SMAs and RSI from DB data
        closes = [float(p.close) for p in prices if p.close]
        chart_data = []
        for i, p in enumerate(prices):
            row = {
                "date": str(p.date),
                "price": round(float(p.close or 0), 2),
                "open": round(float(p.open or 0), 2),
                "high": round(float(p.high or 0), 2),
                "low": round(float(p.low or 0), 2),
                "volume": int(p.volume or 0),
                "sma_20": round(sum(closes[max(0, i - 19):i + 1]) / min(i + 1, 20), 2) if i >= 19 else None,
                "sma_50": round(sum(closes[max(0, i - 49):i + 1]) / min(i + 1, 50), 2) if i >= 49 else None,
                "sma_200": round(sum(closes[max(0, i - 199):i + 1]) / min(i + 1, 200), 2) if i >= 199 else None,
                "rsi": None,
            }
            chart_data.append(row)

        # SMA trend
        sma_signal = "NEUTRAL"
        current_price = float(overview.price or 0)
        if len(closes) >= 50:
            sma20 = sum(closes[-20:]) / 20
            sma50 = sum(closes[-50:]) / 50
            if current_price > sma20 > sma50:
                sma_signal = "BULLISH"
            elif current_price < sma20 < sma50:
                sma_signal = "BEARISH"

        current_rsi = float(overview.rsi_14) if overview.rsi_14 else None

        return {
            "ticker": ticker,
            "market": overview.market or "US",
            "name": overview.name or ticker,
            "price": current_price,
            "daily_change": float(overview.daily_change or 0),
            "changeYTD": None,
            "ytd_high": max(closes[-252:]) if len(closes) >= 252 else (max(closes) if closes else None),
            "ytd_low": min(closes[-252:]) if len(closes) >= 252 else (min(closes) if closes else None),
            "final_score": None,
            "estimates": {"1d": None, "7d": None, "1m": None},
            "win_rate": None,
            "strategy_tags": None,
            "stop_loss": None,
            "rr_ratio": None,
            "vol_category": None,
            "candlestick_pattern": None,
            "logic_summary": None,
            "confidence_drivers": None,
            "metrics": None,
            "sparkline": None,
            "timestamp": None,
            "chart_data": chart_data,
            "indicators": {
                "rsi": current_rsi,
                "rsi_signal": "OVERBOUGHT" if current_rsi and current_rsi > 70
                              else "OVERSOLD" if current_rsi and current_rsi < 30
                              else "NEUTRAL",
                "sma_signal": sma_signal,
                "sma_20": round(sum(closes[-20:]) / 20, 2) if len(closes) >= 20 else None,
                "sma_50": round(sum(closes[-50:]) / 50, 2) if len(closes) >= 50 else None,
                "sma_200": round(sum(closes[-200:]) / 200, 2) if len(closes) >= 200 else None,
            },
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Stock Detail API Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{ticker}/institutional")
def get_institutional_data(ticker: str, db: Session = Depends(get_db)):
    """Get institutional holdings and analyst ratings."""
    ticker = ticker.upper()

    consensus = db.execute(text("""
        SELECT * FROM gold.consensus_ratings WHERE ticker = :ticker
        ORDER BY report_date DESC LIMIT 1
    """), {"ticker": ticker}).fetchone()

    holders = db.execute(text("""
        SELECT holder_name, shares, pct_out, value FROM gold.institutional_holdings
        WHERE ticker = :ticker ORDER BY shares DESC LIMIT 10
    """), {"ticker": ticker}).fetchall()

    if not consensus and not holders:
        raise HTTPException(status_code=404, detail=f"No institutional data for {ticker}")

    def _rating_text(c):
        if not c or c.total_analysts == 0:
            return "N/A"
        ratio = (c.strong_buy + c.buy) / c.total_analysts
        if ratio >= 0.8: return "STRONG_BUY"
        if ratio >= 0.6: return "BUY"
        if ratio >= 0.4: return "HOLD"
        if ratio >= 0.2: return "SELL"
        return "STRONG_SELL"

    return {
        "ticker": ticker,
        "consensus": {
            "strong_buy": consensus.strong_buy, "buy": consensus.buy,
            "hold": consensus.hold, "sell": consensus.sell, "strong_sell": consensus.strong_sell,
            "total_analysts": consensus.total_analysts,
            "target_mean": float(consensus.target_mean) if consensus.target_mean else None,
            "target_high": float(consensus.target_high) if consensus.target_high else None,
            "target_low": float(consensus.target_low) if consensus.target_low else None,
            "current_price": float(consensus.current_price) if consensus.current_price else None,
            "upside_pct": float(consensus.upside_pct) if consensus.upside_pct else None,
            "rating": _rating_text(consensus),
        } if consensus else None,
        "institutional_holders": [{
            "holder": h.holder_name, "shares": h.shares,
            "pct_out": float(h.pct_out) if h.pct_out else None, "value": h.value,
        } for h in holders],
        "total_institutional_shares": sum(h.shares for h in holders) if holders else 0,
    }
