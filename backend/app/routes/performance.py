"""Performance endpoints — strategy performance, daily P&L, velocity, HFT."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.dependencies import get_db, logger

router = APIRouter(prefix="/api", tags=["performance"])


# =============================================================================
# Strategy Performance
# =============================================================================

@router.get("/performance/strategy")
def get_strategy_performance(db: Session = Depends(get_db)):
    """Strategy performance with backtest vs actual win rates + current signal."""
    attribution = db.execute(text("""
        SELECT strategy_id, strategy_name, allocated_capital_pct as allocation,
               contribution_pct as contribution, return_pct as returns, num_trades,
               win_rate, sharpe_ratio
        FROM consumption.Performance_Strategy_Attribution
        WHERE portfolio_type = 'PAPER' ORDER BY return_pct DESC
    """)).fetchall()

    backtests = db.execute(text("""
        SELECT strategy_id, AVG(win_rate) as backtest_win_rate,
               AVG(total_return_pct) as backtest_return, SUM(total_trades) as backtest_total_trades
        FROM consumption.Strategies_Backtest_Results GROUP BY strategy_id
    """)).fetchall()

    # NOTE: Performance_Trades_History dropped - using paper_strategies for live stats
    live_stats = db.execute(text("""
        SELECT strategy_id, COUNT(*) as total_trades,
               SUM(CASE WHEN realized_pnl > 0 THEN 1 ELSE 0 END) as winning_trades
        FROM gold.paper_strategies
        WHERE status = 'ACTIVE' GROUP BY strategy_id
    """)).fetchall()

    current_signals = db.execute(text("""
        SELECT DISTINCT ON (strategy_id) strategy_id, ticker, signal, signal_strength,
               confidence_score, current_price
        FROM consumption.Strategies_Signals_Current
        WHERE signal IN ('BUY', 'SELL') ORDER BY strategy_id, confidence_score DESC
    """)).fetchall()

    backtest_data = {b.strategy_id: b for b in backtests}
    live_data = {l.strategy_id: l for l in live_stats}
    signal_data = {s.strategy_id: s for s in current_signals}

    strategies = []
    for a in attribution:
        bt = backtest_data.get(a.strategy_id)
        live = live_data.get(a.strategy_id)
        sig = signal_data.get(a.strategy_id)
        live_win_rate = round((live.winning_trades / live.total_trades) * 100, 1) if live and live.total_trades > 0 else None

        strategies.append({
            "strategy_id": a.strategy_id, "strategy_name": a.strategy_name,
            "allocation": float(a.allocation or 0), "contribution": float(a.contribution or 0),
            "returns": float(a.returns or 0), "num_trades": a.num_trades or 0,
            "sharpe_ratio": float(a.sharpe_ratio or 0),
            "live_win_rate": live_win_rate, "live_trades": live.total_trades if live else 0,
            "backtest_win_rate": round((bt.backtest_win_rate or 0) * 100, 1) if bt and bt.backtest_win_rate else None,
            "backtest_return": round(bt.backtest_return or 0, 2) if bt else None,
            "backtest_trades": bt.backtest_total_trades if bt else 0,
            "current_signal": {
                "action": sig.signal, "ticker": sig.ticker,
                "strength": round((sig.signal_strength or 0) * 100, 1),
                "confidence": round((sig.confidence_score or 0) * 100, 1),
                "price": float(sig.current_price or 0),
            } if sig else None,
        })

    monthly = db.execute(text("""
        SELECT year, month, return_pct FROM consumption.Performance_Monthly_Returns
        WHERE portfolio_type = 'PAPER' ORDER BY year DESC, month DESC LIMIT 12
    """)).fetchall()

    # NOTE: Performance_Portfolio_Summary dropped - using gold.paper_strategies for summary
    summary = db.execute(text("""
        SELECT 
            COALESCE(SUM(realized_pnl), 0) as total_pnl,
            COALESCE(SUM(unrealized_pnl), 0) as unrealized_pnl
        FROM gold.paper_strategies WHERE status = 'ACTIVE'
    """)).fetchone()

    return {
        "strategies": strategies,
        "monthly_returns": [{"year": r.year, "month": r.month, "return": float(r.return_pct or 0)} for r in monthly],
        "summary": {
            "total_return": float(summary.total_pnl or 0) if summary else 0,
            "sharpe": 0,  # TODO: Calculate from available data
            "max_drawdown": 0,  # TODO: Calculate from available data
            "win_rate": 0,  # TODO: Calculate from available data
        },
    }


# =============================================================================
# Daily P&L
# =============================================================================

@router.get("/performance/daily-pnl")
def get_daily_pnl(days: int = 7, db: Session = Depends(get_db)):
    """Get daily P&L from position entries and exits."""
    # NOTE: Performance_Trades_History dropped - using trade_executions
    closed_trades = db.execute(text("""
        SELECT DATE(executed_at) as trade_date, SUM(pnl) as day_pnl, COUNT(*) as trade_count
        FROM gold.trade_executions WHERE pnl IS NOT NULL
        GROUP BY DATE(executed_at) ORDER BY trade_date DESC LIMIT :days
    """), {"days": days}).fetchall()

    # NOTE: Using paper_strategies with available columns
    open_positions = db.execute(text("""
        SELECT strategy_id, SUM(unrealized_pnl) as day_pnl, COUNT(*) as position_count
        FROM gold.paper_strategies WHERE status = 'ACTIVE'
        GROUP BY strategy_id
    """)).fetchall()

    daily_map = {}
    for t in closed_trades:
        if t.trade_date:
            d = str(t.trade_date)
            daily_map.setdefault(d, {"pnl": 0, "trades": 0})
            daily_map[d]["pnl"] += float(t.day_pnl or 0)
            daily_map[d]["trades"] += t.trade_count
    # NOTE: Skipping open_positions - paper_strategies lacks date column for grouping

    if not daily_map:
        return {"daily": [], "summary": {"total_pnl": 0, "avg_daily_pnl": 0, "message": "No positions recorded yet"}}

    daily_data = [{"date": d, "pnl": round(v["pnl"], 2), "trades": v["trades"]} for d, v in sorted(daily_map.items())]
    total_pnl = sum(d["pnl"] for d in daily_data)

    return {
        "daily": daily_data,
        "summary": {
            "total_pnl": round(total_pnl, 2),
            "avg_daily_pnl": round(total_pnl / len(daily_data), 2),
            "best_day": round(max(d["pnl"] for d in daily_data), 2),
            "worst_day": round(min(d["pnl"] for d in daily_data), 2),
            "days_with_activity": len(daily_data),
        },
    }


# =============================================================================
# Velocity
# =============================================================================

@router.get("/velocity/trades")
def get_velocity_trades(db: Session = Depends(get_db)):
    # NOTE: Performance_Trades_History dropped - using trade_executions
    result = db.execute(text("""
        SELECT id as trade_id, ticker, side, executed_at as entry_date, 
               price as entry_price, quantity,
               pnl
        FROM gold.trade_executions ORDER BY executed_at DESC LIMIT 100
    """)).fetchall()
    return [{"id": r.trade_id, "ticker": r.ticker, "side": r.side,
             "entry_price": float(r.entry_price or 0), "pnl": float(r.pnl or 0),
             "strategy": None, "holding_period": 0} for r in result]


@router.get("/velocity/summary")
def get_velocity_summary(db: Session = Depends(get_db)):
    # NOTE: Performance_Trades_History dropped
    trades = db.execute(text("SELECT COUNT(*) as cnt FROM gold.trade_executions")).fetchone()
    # NOTE: Performance_Portfolio_Summary dropped
    summary = db.execute(text("""
        SELECT 
            COALESCE(SUM(realized_pnl) + SUM(unrealized_pnl), 0) as total_pnl
        FROM gold.paper_strategies WHERE status = 'ACTIVE'
    """)).fetchone()
    return {
        "total_trades": trades.cnt if trades else 0,
        "portfolio_value": 0,  # TODO: Calculate from available data
        "total_pnl": float(summary.total_pnl or 0) if summary else 0,
        "win_rate": 0,  # TODO: Calculate from available data
        "sharpe_ratio": 0,  # TODO: Calculate from available data
        "active_strategies": 8, "status": "active",
    }


# =============================================================================
# HFT Matrix
# =============================================================================

@router.get("/hft/matrix")
def get_hft_matrix(db: Session = Depends(get_db)):
    res = db.execute(text("SELECT * FROM consumption.hft_matrix ORDER BY timestamp DESC, ticker ASC"))
    return [{
        "ticker": r.ticker, "asset_class": r.asset_class,
        "liquidity_momentum": r.liquidity_momentum, "fusion_signal": r.fusion_signal,
        "shock_warning": r.shock_warning, "pressure_value": r.pressure_value,
        "reasoning": r.reasoning, "velocity_estimates": r.velocity_estimates,
    } for r in res.fetchall()]


# =============================================================================
# Quant Performance Matrix
# =============================================================================

@router.get("/quant/performance/matrix")
def get_performance_matrix(db: Session = Depends(get_db)):
    from app.services.strategy_manager import StrategyManager
    sm = StrategyManager()
    return sm.get_performance_matrix()
