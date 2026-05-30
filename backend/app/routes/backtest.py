"""Backtest endpoints — request, run, and retrieve backtest results for researcher strategies."""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Optional, List
from datetime import datetime, timedelta
import uuid
import json
import logging

from app.dependencies import get_db, logger
from app.db.safe_query import safe_query, safe_query_one

router = APIRouter(prefix="/api", tags=["backtest"])

# In-memory store for backtest job status (could be moved to DB later)
_backtest_jobs = {}


class BacktestRequest:
    """Represents a backtest request payload."""
    strategy_id: str
    name: str
    asset_class: str
    direction: str
    time_horizon: str
    venue: str
    tickers: Optional[List[str]] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    initial_capital: float = 100000.0
    position_size: float = 0.1


# Strategy-specific ticker fallbacks when DB is unavailable
_STRATEGY_TICKER_FALLBACKS = {
    "AI_INFRA_POST_EARNINGS_MOMENTUM": ["NVDA", "AMD", "AVGO", "MRVL", "TSM", "ARM", "SMCI", "DELL", "HPE", "INTC"],
    "US_FINANCIAL_PANIC_BOUNCE": ["SPY", "XLF", "KRE", "JPM", "BAC", "GS", "MS", "C", "WFC", "USB"],
}
_DEFAULT_TICKERS = ["SPY", "XLF", "KRE", "JPM", "BAC", "GS", "MS", "C", "WFC", "USB"]


def _get_fallback_tickers(strategy_id: str, name: str) -> List[str]:
    """Return strategy-appropriate tickers when DB universe is not available."""
    for key, tickers in _STRATEGY_TICKER_FALLBACKS.items():
        if key in name.upper() or key in strategy_id.upper():
            return tickers
    return _DEFAULT_TICKERS


@router.post("/backtest/request")
def create_backtest_request(payload: dict, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """
    Accept a backtest request for a researcher strategy and queue it for execution.

    Request body:
    {
        "strategy_id": "S-20260227-001",
        "name": "US_FINANCIAL_PANIC_BOUNCE",
        "asset_class": "Equity",
        "direction": "LONG",
        "time_horizon": "SHORT_TERM",
        "venue": "US_EQUITY",
        "tickers": ["SPY", "XLF", "KRE", "JPM", "BAC"],
        "start_date": "2024-01-01",
        "end_date": "2025-12-31",
        "initial_capital": 100000,
        "position_size": 0.1
    }
    """
    strategy_id = payload.get("strategy_id")
    name = payload.get("name")
    asset_class = payload.get("asset_class", "Equity")
    direction = payload.get("direction", "LONG")
    time_horizon = payload.get("time_horizon", "SHORT_TERM")
    venue = payload.get("venue", "US_EQUITY")

    if not strategy_id or not name:
        raise HTTPException(status_code=400, detail="strategy_id and name are required")

    # Look up the strategy in gold.strategy_definitions to validate it exists
    try:
        result = db.execute(text("""
            SELECT strategy_id, name, universe_tickers, sharpe_ratio, max_drawdown, win_rate
            FROM gold.strategy_registry WHERE strategy_id = :sid 
        """), {"sid": strategy_id}).fetchone()
    except Exception as e:
        logger.error(f"DB error validating strategy {strategy_id}: {e}")
        result = None

    if not result:
        logger.warning(f"Strategy {strategy_id} not found in gold.strategy_registry. Proceeding anyway.")

    # Resolve tickers: use payload if provided, else fall back to DB universe
    tickers = payload.get("tickers")
    if not tickers and result and result.universe_tickers:
        tickers = [t.strip() for t in result.universe_tickers.split(",") if t.strip()]
    if not tickers:
        tickers = _get_fallback_tickers(strategy_id, name)

    request_id = str(uuid.uuid4())
    job = {
        "request_id": request_id,
        "strategy_id": strategy_id,
        "name": name,
        "asset_class": asset_class,
        "direction": direction,
        "time_horizon": time_horizon,
        "venue": venue,
        "tickers": tickers,
        "start_date": payload.get("start_date", "2024-01-01"),
        "end_date": payload.get("end_date", (datetime.utcnow() - timedelta(days=1)).strftime("%Y-%m-%d")),
        "initial_capital": payload.get("initial_capital", 100000.0),
        "position_size": payload.get("position_size", 0.1),
        "status": "queued",
        "created_at": datetime.utcnow().isoformat(),
        "completed_at": None,
        "result": None,
        "error": None,
    }
    _backtest_jobs[request_id] = job

    background_tasks.add_task(_run_backtest_job, request_id)

    logger.info(f"Backtest request {request_id} queued for strategy {strategy_id} ({name}) with {len(tickers)} tickers")
    return {
        "request_id": request_id,
        "status": "queued",
        "strategy_id": strategy_id,
        "name": name,
        "tickers": tickers,
        "message": "Backtest queued. Use GET /api/backtest/{request_id} to check status."
    }


@router.get("/backtest/{request_id}")
def get_backtest_status(request_id: str):
    """Get the status and result of a backtest request."""
    job = _backtest_jobs.get(request_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Backtest request {request_id} not found")
    return {
        "request_id": job["request_id"],
        "status": job["status"],
        "strategy_id": job["strategy_id"],
        "name": job["name"],
        "created_at": job["created_at"],
        "completed_at": job["completed_at"],
        "result": job["result"],
        "error": job["error"],
    }


@router.get("/backtest")
def list_backtest_jobs(strategy_id: Optional[str] = None, status: Optional[str] = None):
    """List backtest jobs, optionally filtered by strategy_id or status."""
    jobs = list(_backtest_jobs.values())
    if strategy_id:
        jobs = [j for j in jobs if j["strategy_id"] == strategy_id]
    if status:
        jobs = [j for j in jobs if j["status"] == status]
    return {
        "jobs": [{k: v for k, v in j.items() if k != "result"} for j in jobs],
        "count": len(jobs)
    }


def _run_backtest_job(request_id: str):
    """Execute the backtest in the background."""
    job = _backtest_jobs.get(request_id)
    if not job:
        return

    job["status"] = "running"
    logger.info(f"Backtest {request_id} started")

    try:
        from app.core_logic.backtesting.strategy_backtester import StrategyBacktester
        import yfinance as yf
        import pandas as pd

        tickers = job["tickers"]
        start_date = job["start_date"]
        end_date = job["end_date"]
        initial_capital = job["initial_capital"]
        position_size = job["position_size"]

        backtester = StrategyBacktester(initial_capital=initial_capital)
        results_by_ticker = {}
        aggregated_trades = []
        equity_curves = {}

        for ticker in tickers:
            try:
                df = yf.Ticker(ticker).history(start=start_date, end=end_date)
                if df.empty or len(df) < 50:
                    results_by_ticker[ticker] = {"error": "Insufficient data"}
                    continue

                strategy_name, result = backtester.get_best_strategy(df)

                trades = []
                for t in result.trades:
                    trades.append({
                        "entry_date": t.entry_date.isoformat() if t.entry_date else None,
                        "exit_date": t.exit_date.isoformat() if t.exit_date else None,
                        "entry_price": round(t.entry_price, 2),
                        "exit_price": round(t.exit_price, 2) if t.exit_price else None,
                        "position": t.position,
                        "pnl": round(t.pnl, 2),
                        "pnl_pct": round(t.pnl_pct, 2),
                        "exit_reason": t.exit_reason,
                    })
                    aggregated_trades.append({
                        "ticker": ticker,
                        "pnl": t.pnl,
                        "pnl_pct": t.pnl_pct,
                    })

                results_by_ticker[ticker] = {
                    "best_strategy": strategy_name,
                    "total_return": result.total_return,
                    "sharpe_ratio": result.sharpe_ratio,
                    "max_drawdown": result.max_drawdown,
                    "win_rate": result.win_rate,
                    "profit_factor": result.profit_factor,
                    "avg_trade_return": result.avg_trade_return,
                    "num_trades": result.num_trades,
                    "winning_trades": result.winning_trades,
                    "losing_trades": result.losing_trades,
                    "trades": trades,
                }
                equity_curves[ticker] = [round(e, 2) for e in result.equity_curve]
            except Exception as e:
                logger.error(f"Backtest error for {ticker}: {e}")
                results_by_ticker[ticker] = {"error": str(e)}

        total_trades = sum(r.get("num_trades", 0) for r in results_by_ticker.values() if "error" not in r)
        winning_trades = sum(r.get("winning_trades", 0) for r in results_by_ticker.values() if "error" not in r)
        losing_trades = sum(r.get("losing_trades", 0) for r in results_by_ticker.values() if "error" not in r)
        avg_return = sum(r.get("total_return", 0) for r in results_by_ticker.values() if "error" not in r) / max(1, len([r for r in results_by_ticker.values() if "error" not in r]))

        portfolio_equity = None
        for ticker, curve in equity_curves.items():
            if portfolio_equity is None:
                portfolio_equity = curve.copy()
            else:
                min_len = min(len(portfolio_equity), len(curve))
                portfolio_equity = [portfolio_equity[i] + curve[i] for i in range(min_len)]

        job["status"] = "completed"
        job["completed_at"] = datetime.utcnow().isoformat()
        job["result"] = {
            "strategy_id": job["strategy_id"],
            "name": job["name"],
            "asset_class": job["asset_class"],
            "direction": job["direction"],
            "time_horizon": job["time_horizon"],
            "venue": job["venue"],
            "period": {"start": start_date, "end": end_date},
            "portfolio_summary": {
                "tickers_tested": len(tickers),
                "tickers_successful": len([r for r in results_by_ticker.values() if "error" not in r]),
                "total_trades": total_trades,
                "winning_trades": winning_trades,
                "losing_trades": losing_trades,
                "portfolio_win_rate": round(winning_trades / max(1, total_trades), 2),
                "avg_ticker_return_pct": round(avg_return, 2),
                "initial_capital": initial_capital,
                "position_size": position_size,
            },
            "tickers": results_by_ticker,
            "portfolio_equity_curve": [round(e, 2) for e in portfolio_equity] if portfolio_equity else [],
        }
        logger.info(f"Backtest {request_id} completed successfully")
    except Exception as e:
        logger.error(f"Backtest {request_id} failed: {e}")
        job["status"] = "failed"
        job["error"] = str(e)
        job["completed_at"] = datetime.utcnow().isoformat()
