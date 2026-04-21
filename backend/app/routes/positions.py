"""Position endpoints — portfolio, paper strategies, inventory, close, cash."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from pydantic import BaseModel
from typing import Optional

from app.dependencies import get_db, logger
from app.db.session import Inventory

router = APIRouter(prefix="/api", tags=["positions"])


# =============================================================================
# Portfolio Positions
# =============================================================================

@router.get("/portfolio/positions")
def get_portfolio_positions(db: Session = Depends(get_db)):
    """Get current portfolio positions from consumption layer, with IBKR fallback."""
    positions = []
    
    # Primary source: consumption portfolio positions view
    try:
        rows = db.execute(text("""
            SELECT ticker, market_value, weight_pct, side, quantity, 
                avg_entry_price as entry_price, current_price,
                unrealized_pnl as pnl, unrealized_pnl_pct as pnl_pct,
                strategy_name as strategy, days_held
            FROM consumption.Portfolio_Positions_Current 
            WHERE ABS(quantity) > 0
            ORDER BY market_value DESC
        """)).fetchall()
        for r in rows:
            positions.append({
                "ticker": r.ticker,
                "market_value": float(r.market_value or 0),
                "weight_pct": float(r.weight_pct or 0),
                "side": r.side,
                "quantity": float(r.quantity or 0),
                "entry_price": float(r.entry_price or 0),
                "current_price": float(r.current_price or 0),
                "pnl": float(r.pnl or 0),
                "pnl_pct": float(r.pnl_pct or 0),
                "strategy": r.strategy,
                "days_held": r.days_held,
                "source": "portfolio_view"
            })
    except Exception as e:
        logger.error(f"Portfolio Positions primary query error: {e}")
    
    # Fallback: IBKR live positions (when ETL hasn't synced to consumption layer)
    if not positions:
        try:
            rows = db.execute(text("""
                SELECT
                    id,
                    ticker,
                    asset_class,
                    side,
                    quantity,
                    avg_cost as entry_price,
                    market_price as current_price,
                    market_value,
                    unrealized_pnl as pnl,
                    unrealized_pnl_pct as pnl_pct,
                    currency,
                    fetched_at
                FROM gold.ibkr_positions_live
                WHERE ABS(quantity) > 0
                ORDER BY ABS(market_value) DESC
            """)).fetchall()
            for r in rows:
                positions.append({
                    "ticker": r.ticker,
                    "market_value": abs(float(r.market_value or 0)),
                    "weight_pct": 0,
                    "side": r.side,
                    "quantity": abs(float(r.quantity or 0)),
                    "entry_price": float(r.entry_price or 0),
                    "current_price": float(r.current_price or 0),
                    "pnl": float(r.pnl or 0),
                    "pnl_pct": float(r.pnl_pct or 0),
                    "strategy": "IBKR Live",
                    "days_held": None,
                    "currency": r.currency,
                    "source": "ibkr_live"
                })
        except Exception as e:
            logger.error(f"IBKR fallback query error: {e}")
    
    return positions


@router.get("/portfolio/dashboard")
def get_portfolio_dashboard(db: Session = Depends(get_db)):
    """Portfolio risk dashboard."""
    try:
        # NOTE: Performance_Portfolio_Summary dropped - calculating summary manually
        summary = db.execute(text("""
            SELECT 
                COALESCE(SUM(realized_pnl) + SUM(unrealized_pnl), 0) as total_pnl
            FROM gold.paper_strategies
            WHERE status = 'ACTIVE'
        """)).fetchone()
        positions = db.execute(text("""
            SELECT ticker, market_value, weight_pct FROM consumption.Portfolio_Positions_Current
        """)).fetchall()
        return {
            "summary": {
                "total_value": float(summary.total_value or 0) if summary else 0,
                "total_pnl": float(summary.total_pnl or 0) if summary else 0,
                "total_pnl_pct": float(summary.total_pnl_pct or 0) if summary else 0,
                "win_rate": float(summary.win_rate or 0) * 100 if summary else 0,
                "sharpe_ratio": float(summary.sharpe_ratio or 0) if summary else 0,
                "max_drawdown": float(summary.max_drawdown_pct or 0) if summary else 0,
            } if summary else {},
            "positions": [{"ticker": p.ticker, "value": float(p.market_value or 0),
                           "weight": float(p.weight_pct or 0)} for p in positions],
            "position_count": len(positions),
        }
    except Exception as e:
        logger.error(f"Dashboard Error: {e}")
        return {"summary": {}, "positions": [], "position_count": 0}


# =============================================================================
# Paper Strategies
# =============================================================================

@router.get("/paper-strategies")
def get_paper_strategies(db: Session = Depends(get_db)):
    """Get all paper trading strategies filtered by current execution mode."""
    mode_result = db.execute(text(
        "SELECT value FROM gold.platform_settings WHERE key = 'global_execution_mode'"
    )).fetchone()
    current_mode = mode_result.value if mode_result else "SIMULATION"

    result = db.execute(text("""
        SELECT ps.id, ps.strategy_id, sd.name as strategy_name, ps.ticker, ps.capital,
               ps.invested_capital, ps.available_capital, ps.status, ps.entry_price,
               ps.current_price, ps.unrealized_pnl, ps.realized_pnl, ps.trades_count,
               ps.created_at, ps.execution_mode
        FROM gold.paper_strategies ps
        LEFT JOIN gold.strategy_definitions sd ON ps.strategy_id = sd.strategy_id
        WHERE ps.execution_mode = :mode ORDER BY ps.created_at DESC
    """), {"mode": current_mode}).fetchall()

    strategies = [{
        "id": r.id, "strategy_id": r.strategy_id, "strategy_name": r.strategy_name or r.strategy_id,
        "ticker": r.ticker, "capital": float(r.capital) if r.capital else 10000,
        "invested_capital": float(r.invested_capital) if r.invested_capital else 0,
        "available_capital": float(r.available_capital) if r.available_capital else 10000,
        "status": r.status,
        "entry_price": float(r.entry_price) if r.entry_price else None,
        "current_price": float(r.current_price) if r.current_price else None,
        "unrealized_pnl": float(r.unrealized_pnl) if r.unrealized_pnl else 0,
        "realized_pnl": float(r.realized_pnl) if r.realized_pnl else 0,
        "trades_count": r.trades_count or 0,
        "created_at": r.created_at.isoformat() if r.created_at else None,
        "execution_mode": r.execution_mode,
    } for r in result]

    return {"strategies": strategies, "count": len(strategies),
            "execution_mode": current_mode, "message": f"Showing {len(strategies)} positions for {current_mode} mode"}


@router.get("/paper-strategies/{strategy_id:path}/daily-pnl")
def get_paper_strategy_daily_pnl(strategy_id: str, days: int = 7, db: Session = Depends(get_db)):
    """Get daily P&L breakdown for a paper strategy."""
    # NOTE: Performance_Trades_History dropped - using trade_executions
    closed_trades = db.execute(text("""
        SELECT DATE(executed_at) as trade_date, SUM(pnl) as day_realized, COUNT(*) as trade_count
        FROM gold.trade_executions
        WHERE strategy_id = :strategy_id AND pnl IS NOT NULL
        GROUP BY DATE(executed_at) ORDER BY trade_date DESC LIMIT :days
    """), {"strategy_id": strategy_id, "days": days}).fetchall()

    open_positions = db.execute(text("""
        SELECT DATE(entry_date) as entry_date, SUM(unrealized_pnl) as day_unrealized, COUNT(*) as position_count
        FROM consumption.Portfolio_Positions_Current
        WHERE strategy_id = :strategy_id AND side = 'LONG'
        GROUP BY DATE(entry_date) ORDER BY entry_date DESC LIMIT :days
    """), {"strategy_id": strategy_id, "days": days}).fetchall()

    daily_map = {}
    for t in closed_trades:
        if t.trade_date:
            d = str(t.trade_date)
            daily_map.setdefault(d, {"realized": 0, "unrealized": 0, "trades": 0})
            daily_map[d]["realized"] += float(t.day_realized or 0)
            daily_map[d]["trades"] += t.trade_count
    for p in open_positions:
        if p.entry_date:
            d = str(p.entry_date)
            daily_map.setdefault(d, {"realized": 0, "unrealized": 0, "trades": 0})
            daily_map[d]["unrealized"] += float(p.day_unrealized or 0)

    if not daily_map:
        return {"daily": [], "summary": {"total_realized": 0, "total_unrealized": 0, "total_pnl": 0,
                                          "message": "No positions or trades for this strategy"}}

    daily_data = [{"date": d, "realized_pnl": round(v["realized"], 2), "unrealized_pnl": round(v["unrealized"], 2),
                   "total_pnl": round(v["realized"] + v["unrealized"], 2), "trades": v["trades"]}
                  for d, v in sorted(daily_map.items())]
    total_r = sum(d["realized_pnl"] for d in daily_data)
    total_u = sum(d["unrealized_pnl"] for d in daily_data)
    return {"daily": daily_data, "summary": {"total_realized": round(total_r, 2), "total_unrealized": round(total_u, 2),
                                              "total_pnl": round(total_r + total_u, 2), "days_with_activity": len(daily_data)}}


# =============================================================================
# Inventory (Manual Portfolio)
# =============================================================================

class InventoryAdd(BaseModel):
    ticker: str
    name: Optional[str] = None
    buy_price: float
    quantity: float
    sector: Optional[str] = None


@router.get("/inventory")
def get_inventory(db: Session = Depends(get_db)):
    try:
        items = db.query(Inventory).all()
        return [{"id": i.id, "ticker": i.ticker, "name": i.name, "buy_price": float(i.buy_price),
                 "quantity": float(i.quantity), "sector": i.sector, "source": "manual"} for i in items]
    except Exception as e:
        logger.error(f"Inventory get error: {e}")
        return []


@router.post("/inventory/add")
def add_inventory(item: InventoryAdd, db: Session = Depends(get_db)):
    """Add item to inventory — uses provided buy_price, no yfinance."""
    new_item = Inventory(
        ticker=item.ticker.upper(), name=item.name or item.ticker.upper(),
        buy_price=item.buy_price, quantity=item.quantity, sector=item.sector,
    )
    db.add(new_item)
    db.commit()
    return {"status": "added", "ticker": new_item.ticker, "buy_price": float(new_item.buy_price)}


@router.delete("/inventory/delete/{item_id}")
def delete_inventory(item_id: int, db: Session = Depends(get_db)):
    item = db.query(Inventory).filter(Inventory.id == item_id).first()
    if item:
        db.delete(item)
        db.commit()
    return {"status": "deleted"}


@router.get("/inventory/evaluate")
def evaluate_inventory(db: Session = Depends(get_db)):
    """Evaluate inventory — reads current prices from DB."""
    try:
        items = db.query(Inventory).all()
        evaluated = []
        for item in items:
            price_row = db.execute(text("""
                SELECT close FROM silver.unified_prices WHERE ticker = :ticker ORDER BY date DESC LIMIT 1
            """), {"ticker": item.ticker}).fetchone()
            current_price = float(price_row.close) if price_row else float(item.buy_price)
            pnl = (current_price - float(item.buy_price)) * float(item.quantity)
            pnl_pct = ((current_price - float(item.buy_price)) / float(item.buy_price) * 100) if float(item.buy_price) > 0 else 0
            evaluated.append({
                "id": item.id, "ticker": item.ticker, "name": item.name,
                "buy_price": float(item.buy_price), "current_price": current_price,
                "quantity": float(item.quantity), "pnl": round(pnl, 2), "pnl_pct": round(pnl_pct, 2),
            })
        total_pnl = sum(e["pnl"] for e in evaluated)
        return {"positions": evaluated, "total_pnl": round(total_pnl, 2)}
    except Exception as e:
        logger.error(f"Inventory evaluate error: {e}")
        return {"positions": [], "total_pnl": 0}


# =============================================================================
# Close Position
# =============================================================================

@router.post("/positions/{position_id}/close")
def close_position(position_id: int, db: Session = Depends(get_db)):
    """Close a position — uses DB price or IBKR, no yfinance."""
    pos = db.execute(text("""
        SELECT id, ticker, entry_price, invested_capital FROM gold.paper_strategies WHERE id = :id
    """), {"id": position_id}).fetchone()
    if not pos:
        raise HTTPException(status_code=404, detail="Position not found")

    # Get current price from DB
    price_row = db.execute(text("""
        SELECT close FROM silver.unified_prices WHERE ticker = :ticker ORDER BY date DESC LIMIT 1
    """), {"ticker": pos.ticker}).fetchone()
    current_price = float(price_row.close) if price_row else float(pos.entry_price or 0)
    entry_price = float(pos.entry_price or current_price)
    pnl = (current_price - entry_price) / entry_price * float(pos.invested_capital or 0) if entry_price > 0 else 0

    db.execute(text("""
        UPDATE gold.paper_strategies SET status = 'CLOSED',
            realized_pnl = COALESCE(realized_pnl, 0) + :pnl, unrealized_pnl = 0,
            invested_capital = 0, current_price = :price, updated_at = NOW()
        WHERE id = :id
    """), {"id": position_id, "pnl": pnl, "price": current_price})
    db.commit()
    return {"success": True, "position_id": position_id, "closing_price": current_price, "realized_pnl": round(pnl, 2)}


# =============================================================================
# Cash Position Management
# =============================================================================

@router.post("/positions/close-fx-cash")
def close_fx_cash_positions(payload: dict, db: Session = Depends(get_db)):
    positions = payload.get("positions", {})
    executed, failed = [], []
    for currency, amount in positions.items():
        currency = currency.upper()
        if abs(amount) < 100:
            continue
        try:
            action = "SELL" if amount > 0 else "BUY"
            pair = f"{currency}HKD"
            db.execute(text("""
                INSERT INTO gold.trade_executions (strategy_id, ticker, execution_mode, order_type, side, quantity, status, executed_at)
                VALUES ('cash_closure', :ticker, 'PAPER_TRADING', 'FX', :side, :qty, 'PENDING', NOW())
            """), {"ticker": pair, "side": action, "qty": abs(amount)})
            db.commit()
            executed.append({"currency": currency, "action": action, "pair": pair, "quantity": abs(amount)})
        except Exception as e:
            failed.append({"currency": currency, "error": str(e)})
    return {"success": True, "executed_count": len(executed), "failed_count": len(failed),
            "executed": executed, "failed": failed}


@router.get("/positions/cash-summary")
def get_cash_position_summary(db: Session = Depends(get_db)):
    positions = {"AUD": -215086, "CAD": 226465.89, "CNH": -2272.68, "EUR": -312806,
                 "GBP": -9259, "NOK": 3226468.43, "NZD": -185180, "USD": -162784.73, "HKD": 3343700.43}
    fx_exposure = {k: v for k, v in positions.items() if k != "HKD"}
    trades_needed = [{"currency": c, "action": "BUY" if a < 0 else "SELL", "quantity": abs(a), "pair": f"{c}HKD"}
                     for c, a in fx_exposure.items() if abs(a) >= 100]
    return {"base_currency": "HKD", "base_balance": positions.get("HKD", 0),
            "fx_positions": fx_exposure, "trades_to_close": trades_needed, "total_trades": len(trades_needed)}
