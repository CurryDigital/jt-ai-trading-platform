"""Performance endpoints — strategy performance, daily P&L, velocity, HFT."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.dependencies import get_db, logger
from app.db.safe_query import safe_query, safe_query_one

router = APIRouter(prefix="/api", tags=["performance"])

_EMPTY_PERF = {
    "strategies": [], "monthly_returns": [], "strategies_source": "error",
    # Honest nulls — never render placeholder zeros as measured values.
    "summary": {"total_return": None, "sharpe": None, "max_drawdown": None,
                "win_rate": None, "total_trades": None},
}


# =============================================================================
# Strategy Performance
# =============================================================================

@router.get("/performance/strategy")
def get_strategy_performance(db: Session = Depends(get_db)):
    """Strategy performance with backtest vs actual win rates + current signal."""
    try:
        # Try primary attribution view first.
        # t_f25d9ea5: portfolio_type is stored lowercase ('paper') in the table;
        # the old `= 'PAPER'` predicate matched zero rows and silently forced
        # the registry fallback forever. Match case-insensitively.
        # Junk-row hygiene (root-cause cleanup tracked by qr_etl): exclude
        # test/manual artifacts (TEST_*, dummy_test_always_buy, manual_close)
        # and rows with zero measured trades — their 0.000 metrics are ETL
        # placeholders, not measured-neutral values, and rendering them as
        # performance rows would be misleading zeros.
        attribution = safe_query(db, """
            SELECT strategy_id, strategy_name, allocated_capital_pct as allocation,
                   contribution_pct as contribution, return_pct as returns, num_trades,
                   win_rate, sharpe_ratio
            FROM consumption.Performance_Strategy_Attribution
            WHERE LOWER(portfolio_type) = 'paper'
              AND num_trades > 0
              AND strategy_id NOT ILIKE 'test%'
              AND strategy_id NOT IN ('manual_close', 'dummy_test_always_buy')
              AND (strategy_name IS NULL OR strategy_name NOT ILIKE 'test%')
            ORDER BY return_pct DESC
        """, label="perf_attribution")
        attribution_source = "attribution"

        # Fallback: build attribution from strategy_registry + portfolio_positions_current
        if not attribution:
            attribution = safe_query(db, """
                SELECT sr.strategy_id,
                       sr.name AS strategy_name,
                       NULL as allocation, NULL as contribution, NULL as returns,
                       0 as num_trades,
                       sr.win_rate_oos AS win_rate,
                       NULL as sharpe_ratio
                FROM gold.strategy_registry sr
                WHERE sr.status = 'paper'
                ORDER BY sr.win_rate_oos DESC
            """, label="perf_attribution_fallback")
            attribution_source = "registry_fallback"

        backtests = safe_query(db, """
            SELECT strategy_id, AVG(win_rate) as backtest_win_rate,
                   AVG(total_return_pct) as backtest_return, SUM(total_trades) as backtest_total_trades
            FROM consumption.Strategies_Backtest_Results GROUP BY strategy_id
        """, label="perf_backtests")

        # Live stats from portfolio_positions_current (paper_strategies may not exist)
        live_stats = safe_query(db, """
            SELECT strategy_id, COUNT(*) as total_positions,
                   SUM(CASE WHEN unrealized_pnl > 0 THEN 1 ELSE 0 END) as winning_positions
            FROM consumption.portfolio_positions_current
            WHERE status = 'ACTIVE' AND quantity > 0 GROUP BY strategy_id
        """, label="perf_live_stats")

        current_signals = safe_query(db, """
            SELECT DISTINCT ON (strategy_id) strategy_id, ticker, signal, signal_strength,
                   confidence_score, current_price
            FROM consumption.Strategies_Signals_Current
            WHERE signal IN ('BUY', 'SELL') ORDER BY strategy_id, confidence_score DESC
        """, label="perf_signals")

        backtest_data = {b.strategy_id: b for b in backtests}
        live_data = {l.strategy_id: l for l in live_stats}
        signal_data = {s.strategy_id: s for s in current_signals}

        strategies = []
        for a in attribution:
            bt = backtest_data.get(a.strategy_id)
            live = live_data.get(a.strategy_id)
            sig = signal_data.get(a.strategy_id)
            live_win_rate = round((live.winning_positions / live.total_positions) * 100, 1) if live and live.total_positions > 0 else None

            strategies.append({
                "strategy_id": a.strategy_id, "strategy_name": a.strategy_name,
                # Honest nulls: absent source values stay None — never coerced
                # to placeholder 0.0 (contribution_pct is NULL for every row
                # in the attribution table today).
                "allocation": float(a.allocation) if a.allocation is not None else None,
                "contribution": float(a.contribution) if a.contribution is not None else None,
                "returns": float(a.returns) if a.returns is not None else None,
                "num_trades": a.num_trades or 0,
                "win_rate": float(a.win_rate) if a.win_rate is not None else None,
                "sharpe_ratio": float(a.sharpe_ratio) if a.sharpe_ratio is not None else None,
                "live_win_rate": live_win_rate, "live_trades": live.total_positions if live else 0,
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

        monthly = safe_query(db, """
            SELECT year, month, return_pct FROM consumption.Performance_Monthly_Returns
            WHERE LOWER(portfolio_type) = 'paper' ORDER BY year DESC, month DESC LIMIT 12
        """, label="perf_monthly")

        # Summary — honest nulls for anything not measured at portfolio level.
        # win_rate / total_trades: trade-weighted aggregates over the real
        # per-strategy measurements in the attribution table (win_rate is a
        # fraction 0-1; the weighted mean over num_trades>0 rows is the exact
        # aggregate fraction of winning trades). NOTE: portfolio_type is stored
        # lowercase in the table, so match case-insensitively.
        # sharpe / max_drawdown: no portfolio-level source exists
        # (performance_monthly_returns has no paper rows) -> null, not 0.
        # total_return: previously SUM(realized_pnl) over ACTIVE positions only,
        # which measures realized P&L of the open book (all zeros) while ignoring
        # unrealized P&L and closed ledgers — not a total return -> null.
        summary = safe_query_one(db, """
            SELECT
                SUM(num_trades) AS total_trades,
                SUM(win_rate * num_trades)
                    / NULLIF(SUM(num_trades) FILTER (WHERE win_rate IS NOT NULL), 0) AS win_rate
            FROM consumption.Performance_Strategy_Attribution
            WHERE LOWER(portfolio_type) = 'paper' AND num_trades > 0
        """, label="perf_summary")

        return {
            "strategies": strategies,
            # Provenance: which path served strategies[] — the live
            # attribution table or the registry fallback. t_f25d9ea5.
            "strategies_source": attribution_source,
            "monthly_returns": [{"year": r.year, "month": r.month, "return": float(r.return_pct or 0)} for r in monthly],
            "summary": {
                "total_return": None,
                "sharpe": None,
                "max_drawdown": None,
                "win_rate": float(summary.win_rate) if summary and summary.win_rate is not None else None,
                "total_trades": int(summary.total_trades) if summary and summary.total_trades is not None else None,
            },
        }
    except Exception as e:
        logger.error(f"Strategy performance error: {e}")
        return _EMPTY_PERF


# =============================================================================
# Daily P&L
# =============================================================================

@router.get("/performance/daily-pnl")
def get_daily_pnl(days: int = 7, db: Session = Depends(get_db)):
    """Get daily P&L from position entries and exits."""
    try:
        # NOTE: Performance_Trades_History dropped - using trade_executions
        closed_trades = safe_query(db, """
            SELECT DATE(executed_at) as trade_date, SUM(pnl) as day_pnl, COUNT(*) as trade_count
            FROM gold.trade_executions WHERE pnl IS NOT NULL
            GROUP BY DATE(executed_at) ORDER BY trade_date DESC LIMIT :days
        """, {"days": days}, label="daily_pnl_closed")

        # NOTE: Using paper_strategies with available columns
        open_positions = safe_query(db, """
            SELECT strategy_id, SUM(unrealized_pnl) as day_pnl, COUNT(*) as position_count
            FROM consumption.portfolio_positions_current WHERE status = 'ACTIVE'
            GROUP BY strategy_id
        """, label="daily_pnl_open")

        daily_map = {}
        for t in closed_trades:
            if t.trade_date:
                d = str(t.trade_date)
                daily_map.setdefault(d, {"pnl": 0, "trades": 0})
                daily_map[d]["pnl"] += float(t.day_pnl or 0)
                daily_map[d]["trades"] += t.trade_count

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
    except Exception as e:
        logger.error(f"Daily P&L error: {e}")
        return {"daily": [], "summary": {"total_pnl": 0, "avg_daily_pnl": 0, "message": "Error loading P&L data"}}


# =============================================================================
# Velocity
# =============================================================================

@router.get("/velocity/trades")
def get_velocity_trades(db: Session = Depends(get_db)):
    try:
        # NOTE: Performance_Trades_History dropped - using trade_executions
        result = safe_query(db, """
            SELECT id as trade_id, ticker, side, executed_at as entry_date,
                   price as entry_price, quantity,
                   pnl
            FROM gold.trade_executions ORDER BY executed_at DESC LIMIT 100
        """, label="velocity_trades")
        return [{"id": r.trade_id, "ticker": r.ticker, "side": r.side,
                 "entry_price": float(r.entry_price or 0), "pnl": float(r.pnl or 0),
                 "strategy": None, "holding_period": 0} for r in result]
    except Exception as e:
        logger.error(f"Velocity trades error: {e}")
        return []


@router.get("/velocity/summary")
def get_velocity_summary(db: Session = Depends(get_db)):
    try:
        trades = safe_query_one(db, "SELECT COUNT(*) as cnt FROM gold.trade_executions", label="velocity_count")
        summary = safe_query_one(db, """
            SELECT
                COALESCE(SUM(realized_pnl) + SUM(unrealized_pnl), 0) as total_pnl
            FROM consumption.portfolio_positions_current WHERE status = 'ACTIVE'
        """, label="velocity_summary")
        return {
            "total_trades": trades.cnt if trades else 0,
            "portfolio_value": 0,
            "total_pnl": float(summary.total_pnl or 0) if summary else 0,
            "win_rate": 0,
            "sharpe_ratio": 0,
            "active_strategies": 8, "status": "active",
        }
    except Exception as e:
        logger.error(f"Velocity summary error: {e}")
        return {"total_trades": 0, "portfolio_value": 0, "total_pnl": 0, "win_rate": 0, "sharpe_ratio": 0, "active_strategies": 0, "status": "error"}


# =============================================================================
# HFT Matrix
# =============================================================================

@router.get("/hft/matrix")
def get_hft_matrix(db: Session = Depends(get_db)):
    try:
        result = safe_query(db, "SELECT * FROM consumption.hft_matrix ORDER BY timestamp DESC, ticker ASC", label="hft_matrix")
        return [{
            "ticker": r.ticker, "asset_class": r.asset_class,
            "liquidity_momentum": r.liquidity_momentum, "fusion_signal": r.fusion_signal,
            "shock_warning": r.shock_warning, "pressure_value": r.pressure_value,
            "reasoning": r.reasoning, "velocity_estimates": r.velocity_estimates,
        } for r in result]
    except Exception as e:
        logger.error(f"HFT matrix error: {e}")
        return []


# =============================================================================
# Quant Performance Matrix
# =============================================================================

@router.get("/quant/performance/matrix")
def get_performance_matrix(db: Session = Depends(get_db)):
    try:
        from app.services.strategy_manager import StrategyManager
        sm = StrategyManager()
        return sm.get_performance_matrix()
    except Exception as e:
        logger.error(f"Performance matrix error: {e}")
        return []
