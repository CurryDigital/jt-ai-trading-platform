"""
Backtest Engine Service
=======================
Runs backtests for strategies using the StrategyBacktester framework.
Stores results in the database for retrieval and comparison.

Used by:
  - POST /api/strategies/{strategy_id}/backtest
  - GET /api/strategies/{strategy_id}/backtest-history
  - GET /api/strategies/{strategy_id}/backtest-vs-live
  - POST /api/backtest/request
"""
import json
import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import text

from app.db.session import SessionLocal, Base, engine
from app.db.safe_query import safe_query, safe_query_one

logger = logging.getLogger(__name__)


class BacktestEngine:
    """
    Service-layer backtest engine.
    Bridges FastAPI endpoints with the core StrategyBacktester logic.
    """

    def __init__(self):
        self._ensure_table()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def request_backtest(
        self,
        strategy_id: str,
        strategy_name: str,
        asset_class: str,
        direction: str,
        time_horizon: str,
        venue: str,
        tickers: Optional[List[str]] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        initial_capital: float = 100000.0,
        commission_rate: float = 0.001,
        parameters: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Create a backtest request record and optionally queue it for execution.
        Returns the request ID immediately so callers can poll status.
        """
        request_id = f"bt-{uuid.uuid4().hex[:12]}"
        db = SessionLocal()
        try:
            db.execute(
                text(
                    """
                    INSERT INTO gold.backtest_runs (
                        request_id, strategy_id, strategy_name, asset_class,
                        direction, time_horizon, venue, tickers,
                        start_date, end_date, initial_capital, commission_rate,
                        parameters, status, created_at, updated_at
                    ) VALUES (
                        :request_id, :strategy_id, :strategy_name, :asset_class,
                        :direction, :time_horizon, :venue, :tickers,
                        :start_date, :end_date, :initial_capital, :commission_rate,
                        :parameters, 'REQUESTED', NOW(), NOW()
                    )
                    """
                ),
                {
                    "request_id": request_id,
                    "strategy_id": strategy_id,
                    "strategy_name": strategy_name,
                    "asset_class": asset_class,
                    "direction": direction,
                    "time_horizon": time_horizon,
                    "venue": venue,
                    "tickers": json.dumps(tickers or []),
                    "start_date": start_date,
                    "end_date": end_date,
                    "initial_capital": initial_capital,
                    "commission_rate": commission_rate,
                    "parameters": json.dumps(parameters or {}),
                },
            )
            db.commit()
            logger.info(f"Backtest requested: {request_id} for strategy {strategy_id}")
            return {
                "request_id": request_id,
                "strategy_id": strategy_id,
                "strategy_name": strategy_name,
                "status": "REQUESTED",
                "message": "Backtest request accepted. Poll /api/backtest/{request_id}/status for progress.",
            }
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to create backtest request: {e}")
            raise
        finally:
            db.close()

    def run_backtest(
        self,
        strategy_id: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        initial_capital: float = 100000.0,
        commission_rate: float = 0.001,
    ) -> Dict[str, Any]:
        """
        Execute a backtest for a strategy.
        This is the method called by BackgroundTasks.
        """
        db = SessionLocal()
        try:
            # Resolve strategy metadata
            strat = safe_query_one(
                db,
                """
                SELECT strategy_id, name, asset_class, direction, time_horizon, venue,
                       universe_tickers, signal_logic, exit_logic
                FROM gold.strategy_definitions
                WHERE strategy_id = :sid
                """,
                {"sid": strategy_id},
                label="backtest_resolve_strategy",
            )
            if not strat:
                logger.warning(f"Strategy {strategy_id} not found for backtest")
                return {"error": f"Strategy {strategy_id} not found"}

            tickers = []
            if strat.universe_tickers:
                tickers = [t.strip().upper() for t in strat.universe_tickers.split(",") if t.strip()]

            if not tickers:
                tickers = ["SPY"]  # Fallback benchmark

            # Run backtest on each ticker (simplified — aggregate later)
            backtester = StrategyBacktester(initial_capital=initial_capital)
            results_by_ticker: Dict[str, Any] = {}

            for ticker in tickers[:10]:  # Cap at 10 to avoid timeouts
                try:
                    # Fetch price data via yfinance
                    import yfinance as yf

                    period = "2y"
                    if start_date and end_date:
                        df = yf.Ticker(ticker).history(start=start_date, end=end_date)
                    else:
                        df = yf.Ticker(ticker).history(period=period)

                    if df.empty or len(df) < 50:
                        continue

                    # Run all strategies and pick best
                    strategy_name, result = backtester.get_best_strategy(df)
                    results_by_ticker[ticker] = self._serialize_backtest_result(
                        result, strategy_name
                    )
                except Exception as e:
                    logger.warning(f"Backtest failed for {ticker}: {e}")
                    continue

            # Aggregate metrics
            aggregated = self._aggregate_results(results_by_ticker)

            # Store result
            db.execute(
                text(
                    """
                    INSERT INTO gold.backtest_runs (
                        request_id, strategy_id, strategy_name, asset_class,
                        direction, time_horizon, venue, tickers,
                        start_date, end_date, initial_capital, commission_rate,
                        status, result_json, created_at, updated_at
                    ) VALUES (
                        :request_id, :strategy_id, :strategy_name, :asset_class,
                        :direction, :time_horizon, :venue, :tickers,
                        :start_date, :end_date, :initial_capital, :commission_rate,
                        'COMPLETED', :result_json, NOW(), NOW()
                    )
                    """
                ),
                {
                    "request_id": f"bt-{uuid.uuid4().hex[:12]}",
                    "strategy_id": strategy_id,
                    "strategy_name": strat.name,
                    "asset_class": strat.asset_class or "Equity",
                    "direction": strat.direction or "LONG",
                    "time_horizon": strat.time_horizon or "SHORT_TERM",
                    "venue": strat.venue or "US_EQUITY",
                    "tickers": json.dumps(tickers),
                    "start_date": start_date,
                    "end_date": end_date,
                    "initial_capital": initial_capital,
                    "commission_rate": commission_rate,
                    "result_json": json.dumps(
                        {"tickers": results_by_ticker, "aggregated": aggregated}
                    ),
                },
            )
            db.commit()

            return {
                "strategy_id": strategy_id,
                "strategy_name": strat.name,
                "status": "COMPLETED",
                "tickers_tested": list(results_by_ticker.keys()),
                "aggregated": aggregated,
            }

        except Exception as e:
            db.rollback()
            logger.error(f"Backtest execution failed for {strategy_id}: {e}")
            return {"error": str(e), "strategy_id": strategy_id}
        finally:
            db.close()

    def get_backtest_history(self, strategy_id: str) -> List[Dict[str, Any]]:
        """Return all backtest runs for a strategy."""
        db = SessionLocal()
        try:
            rows = safe_query(
                db,
                """
                SELECT request_id, strategy_id, strategy_name, status,
                       result_json, created_at, updated_at
                FROM gold.backtest_runs
                WHERE strategy_id = :sid
                ORDER BY created_at DESC
                """,
                {"sid": strategy_id},
                label="backtest_history",
            )
            history = []
            for r in rows:
                result = {}
                if r.result_json:
                    try:
                        result = json.loads(r.result_json)
                    except Exception:
                        pass
                history.append(
                    {
                        "request_id": r.request_id,
                        "strategy_id": r.strategy_id,
                        "strategy_name": r.strategy_name,
                        "status": r.status,
                        "result": result,
                        "created_at": r.created_at.isoformat() if r.created_at else None,
                        "updated_at": r.updated_at.isoformat() if r.updated_at else None,
                    }
                )
            return history
        finally:
            db.close()

    def compare_backtest_vs_live(self, strategy_id: str) -> Dict[str, Any]:
        """Compare backtest results with live/paper performance."""
        db = SessionLocal()
        try:
            # Latest backtest
            bt = safe_query_one(
                db,
                """
                SELECT result_json, created_at
                FROM gold.backtest_runs
                WHERE strategy_id = :sid AND status = 'COMPLETED'
                ORDER BY created_at DESC LIMIT 1
                """,
                {"sid": strategy_id},
                label="backtest_latest",
            )

            # Live/paper stats
            live = safe_query_one(
                db,
                """
                SELECT COUNT(*) as positions,
                       COALESCE(SUM(realized_pnl), 0) as realized_pnl,
                       COALESCE(SUM(unrealized_pnl), 0) as unrealized_pnl
                FROM gold.paper_strategies
                WHERE strategy_id = :sid AND status = 'ACTIVE'
                """,
                {"sid": strategy_id},
                label="backtest_live",
            )

            backtest_metrics = {}
            if bt and bt.result_json:
                try:
                    backtest_metrics = json.loads(bt.result_json).get("aggregated", {})
                except Exception:
                    pass

            live_pnl = float(live.realized_pnl or 0) + float(live.unrealized_pnl or 0) if live else 0

            return {
                "strategy_id": strategy_id,
                "backtest": backtest_metrics,
                "live": {
                    "total_pnl": live_pnl,
                    "active_positions": live.positions if live else 0,
                },
                "comparison": {
                    "backtest_win_rate": backtest_metrics.get("win_rate"),
                    "live_pnl": live_pnl,
                    "discrepancy_note": "Backtest uses historical data; live uses actual fills.",
                },
            }
        finally:
            db.close()

    def get_request_status(self, request_id: str) -> Optional[Dict[str, Any]]:
        """Poll the status of a backtest request."""
        db = SessionLocal()
        try:
            row = safe_query_one(
                db,
                """
                SELECT request_id, strategy_id, strategy_name, status,
                       result_json, created_at, updated_at
                FROM gold.backtest_runs
                WHERE request_id = :rid
                """,
                {"rid": request_id},
                label="backtest_status",
            )
            if not row:
                return None
            result = {}
            if row.result_json:
                try:
                    result = json.loads(row.result_json)
                except Exception:
                    pass
            return {
                "request_id": row.request_id,
                "strategy_id": row.strategy_id,
                "strategy_name": row.strategy_name,
                "status": row.status,
                "result": result,
                "created_at": row.created_at.isoformat() if row.created_at else None,
                "updated_at": row.updated_at.isoformat() if row.updated_at else None,
            }
        finally:
            db.close()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _serialize_backtest_result(
        self, result: Any, strategy_name: str
    ) -> Dict[str, Any]:
        """Convert StrategyBacktestResult to JSON-serializable dict."""
        return {
            "strategy_name": strategy_name,
            "total_return": result.total_return,
            "sharpe_ratio": result.sharpe_ratio,
            "max_drawdown": result.max_drawdown,
            "win_rate": result.win_rate,
            "profit_factor": result.profit_factor,
            "avg_trade_return": result.avg_trade_return,
            "num_trades": result.num_trades,
            "winning_trades": result.winning_trades,
            "losing_trades": result.losing_trades,
        }

    def _aggregate_results(self, results_by_ticker: Dict[str, Any]) -> Dict[str, Any]:
        """Aggregate per-ticker backtest results into strategy-level summary."""
        if not results_by_ticker:
            return {}

        returns = [r["total_return"] for r in results_by_ticker.values()]
        sharpes = [r["sharpe_ratio"] for r in results_by_ticker.values()]
        win_rates = [r["win_rate"] for r in results_by_ticker.values()]
        drawdowns = [r["max_drawdown"] for r in results_by_ticker.values()]
        trades = [r["num_trades"] for r in results_by_ticker.values()]

        return {
            "tickers_tested": len(results_by_ticker),
            "avg_total_return": round(sum(returns) / len(returns), 2) if returns else 0,
            "avg_sharpe_ratio": round(sum(sharpes) / len(sharpes), 2) if sharpes else 0,
            "avg_win_rate": round(sum(win_rates) / len(win_rates), 4) if win_rates else 0,
            "avg_max_drawdown": round(sum(drawdowns) / len(drawdowns), 2) if drawdowns else 0,
            "total_trades": sum(trades),
        }

    def _ensure_table(self):
        """Create the backtest_runs table if it doesn't exist (idempotent)."""
        try:
            with engine.connect() as conn:
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS gold.backtest_runs (
                        id SERIAL PRIMARY KEY,
                        request_id VARCHAR(32) UNIQUE NOT NULL,
                        strategy_id VARCHAR(50) NOT NULL,
                        strategy_name VARCHAR(100),
                        asset_class VARCHAR(20),
                        direction VARCHAR(10),
                        time_horizon VARCHAR(20),
                        venue VARCHAR(20),
                        tickers JSONB DEFAULT '[]',
                        start_date DATE,
                        end_date DATE,
                        initial_capital NUMERIC(15,2) DEFAULT 100000.0,
                        commission_rate NUMERIC(8,6) DEFAULT 0.001,
                        parameters JSONB DEFAULT '{}',
                        status VARCHAR(20) DEFAULT 'REQUESTED',
                        result_json JSONB,
                        created_at TIMESTAMPTZ DEFAULT NOW(),
                        updated_at TIMESTAMPTZ DEFAULT NOW()
                    )
                """))
                conn.commit()
        except Exception as e:
            logger.warning(f"Could not ensure backtest_runs table: {e}")


# Singleton instance
backtest_engine = BacktestEngine()
