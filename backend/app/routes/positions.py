"""Position endpoints — portfolio, paper strategies, inventory, close, cash."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

from app.dependencies import get_db, logger
from app.db.session import Inventory

router = APIRouter(prefix="/api", tags=["positions"])


# =============================================================================
# Portfolio Positions
# =============================================================================

@router.get("/portfolio/positions")
def get_portfolio_positions(db: Session = Depends(get_db)):
    """Get current portfolio positions from consumption layer."""
    try:
        positions = db.execute(text("""
            SELECT
                id, strategy_id, ticker, side, entry_date, entry_price,
                current_price, quantity, market_value, weight_pct,
                unrealized_pnl, realized_pnl, status, updated_at
            FROM consumption.portfolio_positions_current
            WHERE status = 'ACTIVE' AND quantity > 0
            ORDER BY market_value DESC
        """)).fetchall()

        result = []
        total_value = 0.0
        total_pnl = 0.0
        for p in positions:
            mv = float(p.market_value or 0)
            upnl = float(p.unrealized_pnl or 0)
            total_value += mv
            total_pnl += upnl
            result.append({
                "id": p.id,
                "strategy_id": p.strategy_id,
                "ticker": p.ticker,
                "name": p.ticker,
                "asset_class": "STOCK",
                "side": p.side or "LONG",
                "entry_date": p.entry_date.isoformat() if p.entry_date else None,
                "entry_price": float(p.entry_price or 0),
                "current_price": float(p.current_price or 0),
                "quantity": float(p.quantity or 0),
                "market_value": mv,
                "weight_pct": float(p.weight_pct or 0),
                "unrealized_pnl": upnl,
                "realized_pnl": float(p.realized_pnl or 0),
                "status": p.status or "ACTIVE",
                "updated_at": p.updated_at.isoformat() if p.updated_at else None,
            })

        return {
            "positions": result,
            "total_positions": len(result),
            "total_value": round(total_value, 2),
            "total_pnl": round(total_pnl, 2),
        }
    except Exception as e:
        logger.error(f"Portfolio Positions Error: {e}")
        return {"positions": [], "total_positions": 0, "total_value": 0, "total_pnl": 0}


@router.get("/portfolio/dashboard")
def get_portfolio_dashboard(db: Session = Depends(get_db)):
    """Portfolio risk dashboard."""
    try:
        # Calculate summary from consumption.portfolio_positions_current
        summary = db.execute(text("""
            SELECT
                COALESCE(SUM(market_value), 0) as total_value,
                COALESCE(SUM(unrealized_pnl), 0) as total_pnl,
                COALESCE(SUM(realized_pnl), 0) as total_realized_pnl,
                COUNT(*) as total_positions
            FROM consumption.portfolio_positions_current
            WHERE status = 'ACTIVE' AND quantity > 0
        """)).fetchone()

        positions = db.execute(text("""
            SELECT
                id, strategy_id, ticker, side, entry_date, entry_price,
                current_price, quantity, market_value, weight_pct,
                unrealized_pnl, realized_pnl, status
            FROM consumption.portfolio_positions_current
            WHERE status = 'ACTIVE' AND quantity > 0
            ORDER BY market_value DESC
        """)).fetchall()

        total_value = float(summary.total_value or 0) if summary else 0
        total_pnl = float(summary.total_pnl or 0) if summary else 0
        total_pnl_pct = ((total_pnl / total_value) * 100) if total_value > 0 else 0

        return {
            "summary": {
                "total_value": round(total_value, 2),
                "total_pnl": round(total_pnl, 2),
                "total_pnl_pct": round(total_pnl_pct, 2),
                "win_rate": 0,
                "sharpe_ratio": 0,
                "max_drawdown": 0,
            },
            "positions": [{"id": p.id, "ticker": p.ticker, "value": float(p.market_value or 0),
                           "weight": float(p.weight_pct or 0), "side": p.side or "LONG",
                           "quantity": float(p.quantity or 0), "unrealized_pnl": float(p.unrealized_pnl or 0),
                           "entry_price": float(p.entry_price or 0), "current_price": float(p.current_price or 0)} for p in positions],
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
    """Get all paper trading strategies filtered by current execution mode.

    Falls back to active positions from any mode if the platform execution mode
    does not match any recorded positions, so the Deployed tab shows real positions
    instead of an empty state.
    """
    mode_result = db.execute(text(
        "SELECT value FROM gold.platform_settings WHERE key = 'global_execution_mode'"
    )).fetchone()
    current_mode = mode_result.value if mode_result else "SIMULATION"

    # Primary: positions that match the current platform execution mode.
    try:
        result = db.execute(text("""
            SELECT ps.id, ps.strategy_id, sd.name as strategy_name, ps.ticker, ps.capital,
                   ps.invested_capital, ps.available_capital, ps.status, ps.entry_price,
                   ps.current_price, ps.unrealized_pnl, ps.realized_pnl, ps.trades_count,
                   ps.created_at, ps.execution_mode
            FROM consumption.portfolio_positions_current ps
            LEFT JOIN gold.strategy_registry sd ON ps.strategy_id = sd.strategy_id
            WHERE ps.execution_mode = :mode AND ps.status = 'ACTIVE' AND ps.quantity > 0
            ORDER BY ps.created_at DESC
        """), {"mode": current_mode}).fetchall()
    except Exception:
        db.rollback()
        result = []

    # Fallback: if no positions match the current mode, show active positions
    # from any mode. This prevents the Deployed tab from being empty when the
    # platform mode and stored positions are out of sync.
    if not result:
        try:
            result = db.execute(text("""
                SELECT ps.id, ps.strategy_id, sd.name as strategy_name, ps.ticker, ps.capital,
                       ps.invested_capital, ps.available_capital, ps.status, ps.entry_price,
                       ps.current_price, ps.unrealized_pnl, ps.realized_pnl, ps.trades_count,
                       ps.created_at, ps.execution_mode
                FROM consumption.portfolio_positions_current ps
                LEFT JOIN gold.strategy_registry sd ON ps.strategy_id = sd.strategy_id
                WHERE ps.status = 'ACTIVE' AND ps.quantity > 0
                ORDER BY ps.created_at DESC
            """)).fetchall()
            current_mode = result[0].execution_mode if result else current_mode
        except Exception:
            db.rollback()
            result = []

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
        "execution_mode": r.execution_mode or current_mode,
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


@router.get("/strategies/positions")
def get_strategies_positions(db: Session = Depends(get_db)):
    """Alias of /api/portfolio/positions for the Golden Strategies UI."""
    return get_portfolio_positions(db=db)


@router.get("/strategies/signals")
def get_strategies_signals(db: Session = Depends(get_db)):
    """Active BUY/SELL signals per strategy from gold.strategy_signals.

    Returns the strongest active signal per strategy. This endpoint lets the
    Golden Strategies UI render a signal tag without depending on the generic
    /api/signals/feed route.
    """
    try:
        rows = db.execute(text("""
            SELECT DISTINCT ON (strategy_id)
                   strategy_id,
                   strategy_name,
                   signal,
                   confidence,
                   regime,
                   computed_at
            FROM gold.strategy_signals
            WHERE active = TRUE
            ORDER BY strategy_id, confidence DESC NULLS LAST
        """)).fetchall()
        signals = []
        for r in rows:
            signals.append({
                "strategy_id": r.strategy_id,
                "strategy_name": r.strategy_name,
                "signal": "BUY" if r.signal == 1 else "SELL" if r.signal == -1 else "HOLD",
                "confidence": float(r.confidence) if r.confidence is not None else None,
                "regime": r.regime,
                "computed_at": r.computed_at.isoformat() if r.computed_at else None,
            })
        return {"signals": signals, "count": len(signals)}
    except Exception as e:
        logger.error(f"Strategies signals error: {e}")
        return {"signals": [], "count": 0}


# @router.get("/agents/paper/strategy-book-extended") is implemented in app/routes/agents.py
# under the same /api prefix; keep this file scoped to positions only.


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

# =============================================================================
# Live Positions (Execution Live tab)
# =============================================================================

_LIVE_STALE_SECONDS = 24 * 3600  # snapshot older than this is flagged stale


def _net_ledger_positions(db):
    """Net open positions from the live ledger (gold.trade_executions,
    execution_mode='LIVE_TRADING') using weighted-average-cost netting."""
    try:
        rows = db.execute(text("""
            SELECT id, ticker, side, quantity, price, executed_at
            FROM gold.trade_executions
            WHERE execution_mode = 'LIVE_TRADING'
            ORDER BY executed_at ASC, id ASC
        """)).fetchall()
    except Exception:
        db.rollback()
        return []

    books = {}  # ticker -> {net, avg, last_id, last_ts}
    for r in rows:
        qty = float(r.quantity or 0)
        px = float(r.price or 0)
        signed = qty if (r.side or "").upper() == "BUY" else -qty
        b = books.setdefault(r.ticker, {"net": 0.0, "avg": 0.0, "last_id": 0, "last_ts": None})
        net = b["net"]
        if net == 0 or (signed > 0) == (net > 0):  # same direction -> blend
            new_abs = abs(net) + abs(signed)
            b["avg"] = (b["avg"] * abs(net) + px * abs(signed)) / new_abs if new_abs else 0.0
            b["net"] = net + signed
        elif abs(signed) < abs(net):               # partial reduce -> keep avg
            b["net"] = net + signed
        elif abs(signed) == abs(net):              # flat
            b["net"], b["avg"] = 0.0, 0.0
        else:                                      # flip -> reset avg to fill price
            b["net"], b["avg"] = net + signed, px
        b["last_id"] = r.id
        b["last_ts"] = r.executed_at

    out = []
    for ticker, b in books.items():
        if b["net"] == 0:
            continue
        price_row = db.execute(text("""
            SELECT close FROM silver.unified_prices WHERE ticker = :ticker ORDER BY date DESC LIMIT 1
        """), {"ticker": ticker}).fetchone()
        current_price = float(price_row.close) if price_row else b["avg"]
        out.append({
            "id": b["last_id"],
            "ticker": ticker,
            "side": "LONG" if b["net"] > 0 else "SHORT",
            "quantity": abs(b["net"]),
            "avg_entry": round(b["avg"], 4),
            "current_price": current_price,
            "unrealized_pnl": round((current_price - b["avg"]) * b["net"], 2),
            "as_of": b["last_ts"].isoformat() if b["last_ts"] else None,
            "source": "ledger",
        })
    return out


@router.get("/positions/live")
def get_live_positions(db: Session = Depends(get_db)):
    """Net live positions for the Execution Live tab per-row Close buttons.

    Primary source: gold.ibkr_positions_live — the broker snapshot synced from
    the connected IBKR session by sync_ibkr_to_gold (TRUNCATE + full reload).
    Fallback: net open positions from the live ledger (gold.trade_executions,
    execution_mode='LIVE_TRADING') for tickers not present in the snapshot.
    """
    positions = []
    snapshot_ts = None

    try:
        rows = db.execute(text("""
            SELECT id, ticker, side, quantity, avg_cost, market_price,
                   unrealized_pnl, fetched_at
            FROM gold.ibkr_positions_live
            WHERE quantity <> 0
            ORDER BY ABS(market_value) DESC NULLS LAST
        """)).fetchall()
    except Exception:
        db.rollback()
        rows = []

    seen = set()
    for r in rows:
        seen.add(r.ticker)
        if snapshot_ts is None or (r.fetched_at and r.fetched_at > snapshot_ts):
            snapshot_ts = r.fetched_at
        positions.append({
            "id": r.id,
            "ticker": r.ticker,
            "side": r.side or ("LONG" if float(r.quantity or 0) > 0 else "SHORT"),
            "quantity": abs(float(r.quantity or 0)),
            "avg_entry": float(r.avg_cost or 0),
            "current_price": float(r.market_price or 0),
            "unrealized_pnl": float(r.unrealized_pnl or 0),
            "as_of": r.fetched_at.isoformat() if r.fetched_at else None,
            "source": "ibkr_snapshot",
        })

    # Ledger fallback for tickers missing from the broker snapshot
    for p in _net_ledger_positions(db):
        if p["ticker"] not in seen:
            positions.append(p)

    # Overall as_of = newest timestamp across both sources
    stamps = [p["as_of"] for p in positions if p["as_of"]]
    as_of = max(stamps) if stamps else None
    stale = True
    if as_of:
        try:
            age = (datetime.utcnow() - datetime.fromisoformat(as_of)).total_seconds()
            stale = age > _LIVE_STALE_SECONDS
        except Exception:
            stale = True

    return {
        "positions": positions,
        "count": len(positions),
        "as_of": as_of,
        "stale": stale,
        "source": "ibkr_snapshot" if seen else ("ledger" if positions else "none"),
    }


@router.post("/positions/{position_id}/close")
def close_position(position_id: int, db: Session = Depends(get_db)):
    """Close a position — uses DB price or IBKR, no yfinance."""
    pos = db.execute(text("""
        SELECT id, ticker, entry_price, invested_capital FROM consumption.portfolio_positions_current WHERE id = :id
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
        UPDATE consumption.portfolio_positions_current SET status = 'CLOSED',
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
