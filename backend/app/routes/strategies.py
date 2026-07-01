"""Strategy endpoints — CRUD, templates, screener, deploy, capital management."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
import time

from app.dependencies import get_db, logger
from app.db.safe_query import safe_query, safe_query_one

router = APIRouter(prefix="/api", tags=["strategies"])



@router.get("/quant/templates")
def get_strategy_templates_quant():
    from app.services.strategy_manager import StrategyManager
    return StrategyManager().get_templates()


@router.get("/quant/strategies")
def get_quant_strategies(db: Session = Depends(get_db)):
    try:
        result = db.execute(text("SELECT strategy_id, name, asset_class, universe_tickers, frequency, execution_mode, status, sharpe_oos, max_drawdown_oos, trade_count_oos, win_rate_oos, conviction_score, assigned_capital, in_market_capital, signal_logic, exit_logic, created_at, updated_at FROM gold.strategy_registry WHERE asset_class = 'quant'")).fetchall()
        return [dict(r._mapping) for r in result]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/quant/strategies/bulk-create")
def bulk_create_strategies(payload: dict, db: Session = Depends(get_db)):
    from app.services.strategy_manager import StrategyManager
    sm = StrategyManager()
    strats = sm.bulk_create_strategies(payload.get("selections", []))
    return {"status": "success", "count": len(strats)}


@router.post("/quant/strategies/mode")
def set_strategy_mode_quant(payload: dict, db: Session = Depends(get_db)):
    from app.services.strategy_manager import StrategyManager
    success = StrategyManager().toggle_mode(payload.get("id"), payload.get("mode"))
    return {"status": "success" if success else "failed"}


@router.post("/quant/strategies/create")
def create_quant_strategy(payload: dict, db: Session = Depends(get_db)):
    from app.services.strategy_manager import StrategyManager
    sm = StrategyManager()
    strat = sm.create_fx_strategy(
        payload.get("pair", "EURUSD=X"), payload.get("lot_size", 1000),
        payload.get("template_id", "MR_FX"), payload.get("execution_mode", "SIMULATION"),
    )
    return strat


@router.post("/quant/strategies/clear-logs")
def clear_trade_logs(db: Session = Depends(get_db)):
    try:
        db.execute(text("DELETE FROM gold.trade_executions"))
        db.commit()
        return {"status": "success", "message": "Simulation logs cleared."}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/quant/strategies/toggle/{strat_id}")
def toggle_strategy(strat_id: int, db: Session = Depends(get_db)):
    result = db.execute(text("UPDATE gold.strategy_registry SET status = CASE WHEN status = 'ACTIVE' THEN 'INACTIVE' ELSE 'ACTIVE' END, updated_at = NOW() WHERE strategy_id = :sid AND asset_class = 'quant' RETURNING strategy_id, status"), {"sid": strat_id}).fetchone()
    if result:
        db.commit()
    return {"status": "success"}


@router.delete("/quant/strategies/delete/{strat_id}")
def delete_strategy(strat_id: int, db: Session = Depends(get_db)):
    db.execute(text("DELETE FROM gold.strategy_registry WHERE asset_class = 'quant' WHERE id = :sid"), {"sid": strat_id})
    db.commit()
    return {"status": "success"}


# =============================================================================
# Researcher Strategies
# =============================================================================

@router.get("/strategies/researcher")
def get_researcher_strategies(asset_class: str = None, priority: str = None, status: str = None, db: Session = Depends(get_db)):
    """Get JT Researcher strategies from strategy_registry with backtest data and top signals."""
    try:
        # Build query with all columns - safe_query handles errors gracefully
        query = """
            SELECT strategy_id as id, name, asset_class, universe_tickers,
                   execution_mode, status, sharpe_oos, max_drawdown_oos,
                   trade_count_oos, win_rate_oos, conviction_score,
                   assigned_capital, in_market_capital, signal_logic, exit_logic
            FROM gold.strategy_registry
            WHERE status != 'DEPRECATED'
        """
        params = {}
        if asset_class:
            query += " AND asset_class = :asset_class"
            params["asset_class"] = asset_class
        if status and status != 'ALL':
            query += " AND status = :status"
            params["status"] = status
        query += " ORDER BY sharpe_oos DESC NULLS LAST"

        result = safe_query(db, query, params, label="route_researcher_strategies")
        
        # Fetch yearly backtest data from gold.strategy_backtest_runs
        yearly_backtest_data = {}
        try:
            yearly_bt = safe_query(db, """
                SELECT strategy_id,
                       annual_pnl_2024 as pnl_2024,
                       annual_pnl_2025 as pnl_2025,
                       annual_pnl_2026 as pnl_2026,
                       trade_count_oos,
                       sharpe_oos,
                       max_drawdown_oos,
                       win_rate_oos
                FROM gold.strategy_backtest_runs
                WHERE strategy_id IS NOT NULL
            """, {}, label="route_yearly_bt")
            for yb in yearly_bt:
                sid = yb.strategy_id
                if sid:
                    if sid not in yearly_backtest_data:
                        yearly_backtest_data[sid] = {}
                    if yb.pnl_2024 is not None:
                        yearly_backtest_data[sid]['2024'] = {
                            'return_pct': float(yb.pnl_2024),
                            'trades': int(yb.trade_count_oos) if yb.trade_count_oos else 0,
                            'sharpe': float(yb.sharpe_oos) if yb.sharpe_oos else None,
                            'max_drawdown': float(yb.max_drawdown_oos) if yb.max_drawdown_oos else None,
                            'win_rate': float(yb.win_rate_oos) if yb.win_rate_oos else None
                        }
                    if yb.pnl_2025 is not None:
                        yearly_backtest_data[sid]['2025'] = {
                            'return_pct': float(yb.pnl_2025),
                            'trades': int(yb.trade_count_oos) if yb.trade_count_oos else 0,
                            'sharpe': float(yb.sharpe_oos) if yb.sharpe_oos else None,
                            'max_drawdown': float(yb.max_drawdown_oos) if yb.max_drawdown_oos else None,
                            'win_rate': float(yb.win_rate_oos) if yb.win_rate_oos else None
                        }
                    if yb.pnl_2026 is not None:
                        yearly_backtest_data[sid]['2026'] = {
                            'return_pct': float(yb.pnl_2026),
                            'trades': int(yb.trade_count_oos) if yb.trade_count_oos else 0,
                            'sharpe': float(yb.sharpe_oos) if yb.sharpe_oos else None,
                            'max_drawdown': float(yb.max_drawdown_oos) if yb.max_drawdown_oos else None,
                            'win_rate': float(yb.win_rate_oos) if yb.win_rate_oos else None
                        }
        except Exception as e:
            logger.error(f"Yearly backtest fetch error: {e}")
        
        # Fetch top 5 signals by confidence from gold.strategy_signals
        top_signals_data = {}
        try:
            top_signals = safe_query(db, """
                SELECT DISTINCT ON (strategy_id, strategy_name)
                    strategy_id, strategy_name, signal, confidence, regime
                FROM gold.strategy_signals
                WHERE active = TRUE
                ORDER BY strategy_id, strategy_name, confidence DESC NULLS LAST
            """, {}, label="route_top_signals")
            for sig in top_signals:
                if sig.strategy_id not in top_signals_data:
                    top_signals_data[sig.strategy_id] = []
                if len(top_signals_data[sig.strategy_id]) < 5:
                    top_signals_data[sig.strategy_id].append({
                        'ticker': sig.strategy_name,
                        'signal': 'BUY' if sig.signal == 1 else 'SELL' if sig.signal == -1 else 'HOLD',
                        'confidence': float(sig.confidence) if sig.confidence else None,
                        'strength': sig.regime
                    })
        except Exception as e:
            logger.error(f"Top signals fetch error: {e}")

        # Signal-family linkage — unifies Research vocabulary with the strategy registry (redesign addition)
        family_by_strategy = {}
        families = safe_query(db, """
            SELECT family_key, strategy_id FROM gold.signal_families WHERE strategy_id IS NOT NULL
        """, {}, label="route_signal_families")
        for fam in families:
            family_by_strategy[fam.strategy_id] = fam.family_key

        strategies = []
        for row in result:
            tickers = row.universe_tickers
            if isinstance(tickers, str):
                tickers = tickers.split(",") if tickers else []
            elif tickers is None:
                tickers = []
            
            sid = row.id
            strategy_signals = top_signals_data.get(sid, [])
            top_tickers = strategy_signals if strategy_signals else [
                {'ticker': t, 'signal': 'HOLD', 'confidence': None, 'strength': None} for t in tickers[:5]
            ]
            yearly_data = yearly_backtest_data.get(sid, {})
            
            strategies.append({
                "id": sid, "name": row.name,
                "asset_class": row.asset_class,
                "sharpe_ratio": float(row.sharpe_oos) if row.sharpe_oos else 0,
                "max_drawdown": float(row.max_drawdown_oos) if row.max_drawdown_oos else 0,
                "win_rate": float(row.win_rate_oos) if row.win_rate_oos else 0,
                "universe": tickers, "universe_count": len(tickers),
                "status": row.status, "source": "trade_algo_researcher",
                "execution_mode": row.execution_mode,
                "conviction_score": float(row.conviction_score) if row.conviction_score else None,
                "assigned_capital": float(row.assigned_capital) if row.assigned_capital else None,
                "in_market_capital": float(row.in_market_capital) if row.in_market_capital else None,
                "signal_logic": row.signal_logic,
                "exit_logic": row.exit_logic,
                "entry_logic": row.signal_logic,
                "priority": None,
                "version": None,
                "top_tickers": top_tickers,
                "yearly_backtest": yearly_data,
                "signal_family_key": family_by_strategy.get(sid),
            })
        # Also fetch from strategy_templates if they have different strategies
        template_strategies = []
        try:
            templates = safe_query(db, """
                SELECT id, name, description, asset_class, min_win_rate, min_sharpe, max_holding_days
                FROM gold.strategy_templates
                WHERE id NOT IN (SELECT strategy_id FROM gold.strategy_registry)
            """, {}, label="route_templates")
            for t in templates:
                template_strategies.append({
                    "id": t.id, "name": t.name,
                    "asset_class": t.asset_class,
                    "sharpe_ratio": float(t.min_sharpe) if t.min_sharpe else 0,
                    "max_drawdown": 0,
                    "win_rate": float(t.min_win_rate) if t.min_win_rate else 0,
                    "universe": [], "universe_count": 0,
                    "status": "template", "source": "template",
                    "execution_mode": "SIMULATION",
                    "conviction_score": None,
                    "assigned_capital": None,
                    "in_market_capital": None,
                    "signal_logic": t.description,
                    "exit_logic": None,
                    "entry_logic": t.description,
                    "priority": None,
                    "version": None,
                    "top_tickers": [],
                    "yearly_backtest": {},
                    "signal_family_key": None,
                })
        except Exception as e:
            logger.error(f"Template fetch error: {e}")
        
        # Also fetch from quant_strategies if they have different strategies
        quant_strategies = []
        try:
            quant = safe_query(db, """
                SELECT strategy_id, name, asset_class, status, execution_mode,
                       sharpe_oos, max_drawdown_oos, trade_count_oos, win_rate_oos,
                       conviction_score, assigned_capital, in_market_capital,
                       signal_logic, exit_logic
                FROM gold.strategy_registry
                WHERE asset_class = 'quant'
            """, {}, label="route_quant")
            for q in quant:
                if q.strategy_id not in [s["id"] for s in strategies]:
                    quant_strategies.append({
                        "id": q.strategy_id, "name": q.name,
                        "asset_class": q.asset_class,
                        "sharpe_ratio": float(q.sharpe_oos) if q.sharpe_oos else 0,
                        "max_drawdown": float(q.max_drawdown_oos) if q.max_drawdown_oos else 0,
                        "win_rate": float(q.win_rate_oos) if q.win_rate_oos else 0,
                        "universe": [], "universe_count": 0,
                        "status": q.status, "source": "quant",
                        "execution_mode": q.execution_mode,
                        "conviction_score": float(q.conviction_score) if q.conviction_score else None,
                        "assigned_capital": float(q.assigned_capital) if q.assigned_capital else None,
                        "in_market_capital": float(q.in_market_capital) if q.in_market_capital else None,
                        "signal_logic": q.signal_logic,
                        "exit_logic": q.exit_logic,
                        "entry_logic": q.signal_logic,
                        "priority": None,
                        "version": None,
                        "top_tickers": [],
                        "yearly_backtest": {},
                        "signal_family_key": family_by_strategy.get(q.strategy_id),
                    })
        except Exception as e:
            logger.error(f"Quant fetch error: {e}")
        
        # Combine all strategies
        all_strategies = strategies + template_strategies + quant_strategies
        
        return {"strategies": all_strategies, "count": len(all_strategies)}
    except Exception as e:
        logger.error(f"Route researcher strategies error: {e}")
        return {"strategies": [], "count": 0}


# =============================================================================
# Strategy Templates by Asset
# =============================================================================

@router.get("/strategies/templates")
def get_strategy_templates(asset_class: str = None):
    from app.services.strategy_manager import StrategyManager
    templates = StrategyManager().get_templates()
    if asset_class:
        templates = [t for t in templates if t.asset_class == asset_class]
    return [{"id": t.id, "name": t.name, "description": t.description,
             "asset_class": t.asset_class, "min_win_rate": t.min_win_rate,
             "min_sharpe": t.min_sharpe, "max_holding_days": t.max_holding_days} for t in templates]


@router.get("/strategies/templates/{asset_class}")
def get_templates_for_asset(asset_class: str):
    from app.services.strategy_manager import StrategyManager
    return StrategyManager().get_templates_by_asset(asset_class.upper())


# =============================================================================
# Strategy Create / Deploy
# =============================================================================

@router.post("/strategies/create")
def create_strategy_api(payload: dict, db: Session = Depends(get_db)):
    from app.services.strategy_manager import StrategyManager
    sm = StrategyManager()
    try:
        strategy = sm.create_strategy(
            ticker=payload.get("ticker"), template_id=payload.get("template_id"),
            capital=payload.get("capital", 10000), execution_mode=payload.get("execution_mode", "SIMULATION"),
        )
        return {"status": "success", "strategy_id": strategy.id, "name": strategy.name,
                "asset_class": strategy.params.get("asset_class") if strategy.params else None}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/strategies/deploy-with-pool")
def deploy_strategy_with_pool(payload: dict, db: Session = Depends(get_db)):
    """Deploy strategy with capital pool — 25% per trade, max 4 positions."""
    strategy_id = payload.get("strategy_id")
    tickers = payload.get("tickers", [])
    total_pool = payload.get("total_pool", 100000)
    trade_size_pct = payload.get("trade_size_pct", 0.25)

    if not strategy_id or not tickers:
        raise HTTPException(status_code=400, detail="strategy_id and tickers required")

    mode_result = db.execute(text(
        "SELECT value FROM gold.platform_settings WHERE key = 'global_execution_mode'"
    )).fetchone()
    current_mode = mode_result.value if mode_result else "SIMULATION"

    strategy = db.execute(text(
        "SELECT * FROM gold.strategy_registry WHERE strategy_id = :sid "
    ), {"sid": strategy_id}).fetchone()
    if not strategy:
        raise HTTPException(status_code=404, detail=f"Strategy {strategy_id} not found")

    pool_status = db.execute(text("""
        SELECT COALESCE(SUM(capital), 0) as used FROM consumption.portfolio_positions_current
        WHERE strategy_id = :strategy_id AND status = 'ACTIVE' AND execution_mode = :mode
    """), {"strategy_id": strategy_id, "mode": current_mode}).fetchone()

    current_used = float(pool_status.used) if pool_status else 0
    available = total_pool - current_used
    trade_size = total_pool * trade_size_pct

    if available < trade_size:
        return {"success": False, "error": "Capital pool exhausted", "available": available, "required": trade_size}

    created = []
    for ticker in tickers:
        if available < trade_size:
            break
        try:
            db.execute(text("""
                INSERT INTO consumption.portfolio_positions_current (strategy_id, ticker, capital, status, execution_mode, created_at, updated_at)
                VALUES (:strategy_id, :ticker, :capital, 'ACTIVE', :mode, NOW(), NOW())
                ON CONFLICT (strategy_id, ticker) DO UPDATE SET
                    status = 'ACTIVE', capital = EXCLUDED.capital,
                    execution_mode = EXCLUDED.execution_mode, updated_at = NOW()
            """), {"strategy_id": strategy_id, "ticker": ticker.upper(), "capital": trade_size, "mode": current_mode})
            available -= trade_size
            created.append(ticker)
        except Exception:
            pass
    db.commit()
    return {"success": True, "positions_created": len(created), "tickers": created,
            "pool_remaining": available, "execution_mode": current_mode}


@router.post("/strategies/add-to-paper")
def add_stocks_to_paper(payload: dict, db: Session = Depends(get_db)):
    strategy_id = payload.get("strategy_id")
    tickers = payload.get("tickers", [])
    capital = payload.get("capital_per_position", 10000)

    if not strategy_id or not tickers:
        raise HTTPException(status_code=400, detail="strategy_id and tickers required")

    created, failed = [], []
    for ticker in tickers:
        try:
            db.execute(text("""
                INSERT INTO consumption.portfolio_positions_current (strategy_id, ticker, capital, status, created_at, updated_at)
                VALUES (:strategy_id, :ticker, :capital, 'ACTIVE', NOW(), NOW())
                ON CONFLICT (strategy_id, ticker) DO UPDATE SET status = 'ACTIVE', capital = EXCLUDED.capital, updated_at = NOW()
            """), {"strategy_id": strategy_id, "ticker": ticker.upper(), "capital": capital})
            created.append(ticker)
        except Exception as e:
            failed.append({"ticker": ticker, "error": str(e)})
    db.commit()
    return {"success": True, "strategy_id": strategy_id, "added": created, "failed": failed, "total_added": len(created)}


# =============================================================================
# Strategy Detail / Mode / Capital
# =============================================================================

@router.get("/strategies/by-asset/{asset_class}")
def get_strategies_by_asset(asset_class: str, db: Session = Depends(get_db)):
    from app.services.strategy_manager import StrategyManager
    strategies = StrategyManager().get_strategies_by_asset(asset_class)
    return [{"id": s.id, "name": s.name, "ticker": s.target_ticker, "is_active": s.is_active,
             "current_pnl": s.current_pnl, "total_trades": s.total_trades, "params": s.params} for s in strategies]


@router.get("/strategies/{strategy_id:path}/daily-pnl")
def get_strategy_daily_pnl_api(strategy_id: int, start_date: str = None, end_date: str = None, db: Session = Depends(get_db)):
    from app.services.strategy_manager import StrategyManager
    result = StrategyManager().get_strategy_daily_pnl(strategy_id, start_date, end_date)
    if result is None:
        raise HTTPException(status_code=404, detail=f"Strategy {strategy_id} not found")
    return result


@router.get("/strategies/{strategy_id:path}/backtest-summary")
def get_strategy_backtest_summary_api(strategy_id: int, db: Session = Depends(get_db)):
    from app.services.strategy_manager import StrategyManager
    result = StrategyManager().get_strategy_backtest_summary(strategy_id)
    if result is None:
        raise HTTPException(status_code=404, detail=f"Strategy {strategy_id} not found")
    return result


@router.get("/strategies/{strategy_id:path}/detail")
def get_strategy_detail(strategy_id: int, db: Session = Depends(get_db)):
    from app.services.strategy_manager import StrategyManager
    sm = StrategyManager()
    strategy_row = db.execute(text("SELECT strategy_id, name, asset_class, universe_tickers, frequency, execution_mode, status, sharpe_oos, max_drawdown_oos, trade_count_oos, win_rate_oos, conviction_score, assigned_capital, in_market_capital, signal_logic, exit_logic, created_at, updated_at FROM gold.strategy_registry WHERE strategy_id = :sid"), {"sid": strategy_id}).fetchone()
    if not strategy_row:
        raise HTTPException(status_code=404, detail=f"Strategy {strategy_id} not found")

    strategy = dict(strategy_row._mapping)
    daily_pnl = sm.get_strategy_daily_pnl(strategy_id)
    backtest = sm.get_strategy_backtest_summary(strategy_id)
    trades = db.execute(text("SELECT executed_at, ticker, side, quantity, price, pnl FROM gold.trade_executions WHERE strategy_id = :sid ORDER BY executed_at DESC LIMIT 50"), {"sid": strategy_id}).fetchall()

    return {
        "strategy": {
            "id": strategy.get("strategy_id"), "name": strategy.get("name"),
            "asset_class": strategy.get("asset_class"),
            "is_active": strategy.get("status") == "ACTIVE",
            "current_pnl": strategy.get("in_market_capital"),
            "total_trades": strategy.get("trade_count_oos"),
            "win_rate": round((strategy.get("win_rate_oos") or 0) * 100, 1),
        },
        "backtest": backtest.get("template_backtest") if backtest else {},
        "actual_performance": backtest.get("actual_performance") if backtest else {},
        "daily_pnl_summary": daily_pnl.get("summary") if daily_pnl else {},
        "recent_trades": [{"timestamp": t.executed_at.isoformat() if t.executed_at else None,
                           "ticker": t.ticker, "side": t.side,
                           "quantity": float(t.quantity) if t.quantity else 0,
                           "price": float(t.price) if t.price else 0,
                           "pnl": float(t.pnl) if t.pnl else 0} for t in trades],
    }


@router.post("/strategies/{strategy_id:path}/mode")
def set_execution_mode(strategy_id: str, payload: dict, db: Session = Depends(get_db)):
    mode = payload.get("execution_mode", "SIMULATION")
    if mode not in ["SIMULATION", "PAPER_TRADING", "LIVE_TRADING"]:
        raise HTTPException(status_code=400, detail="Invalid mode")

    result = db.execute(text("""
        UPDATE gold.strategy_registry SET execution_mode = :mode, updated_at = NOW()
        WHERE strategy_id = :strategy_id RETURNING strategy_id, name, execution_mode
    """), {"strategy_id": strategy_id, "mode": mode}).fetchone()
    if not result:
        raise HTTPException(status_code=404, detail=f"Strategy {strategy_id} not found")
    db.commit()
    return {"success": True, "strategy_id": result.strategy_id, "strategy_name": result.name, "execution_mode": result.execution_mode}


@router.get("/strategies/{strategy_id:path}/mode")
def get_execution_mode(strategy_id: str, db: Session = Depends(get_db)):
    result = db.execute(text("""
        SELECT strategy_id, name, execution_mode, venue FROM gold.strategy_registry WHERE strategy_id = :strategy_id
    """), {"strategy_id": strategy_id}).fetchone()
    if not result:
        raise HTTPException(status_code=404, detail="Strategy not found")
    return {
        "strategy_id": result.strategy_id, "strategy_name": result.name,
        "execution_mode": result.execution_mode or "SIMULATION", "venue": result.venue,
        "available_modes": ["SIMULATION", "PAPER_TRADING", "LIVE_TRADING"],
        "risk_level": {"SIMULATION": "ZERO", "PAPER_TRADING": "LOW", "LIVE_TRADING": "HIGH"}.get(result.execution_mode or "SIMULATION"),
    }


@router.get("/strategies/{strategy_id:path}/capital")
def get_strategy_capital(strategy_id: str, db: Session = Depends(get_db)):
    result = db.execute(text("""
        SELECT strategy_id, name, assigned_capital, in_market_capital, capacity_millions
        FROM gold.strategy_registry WHERE strategy_id = :strategy_id 
    """), {"strategy_id": strategy_id}).fetchone()
    if not result:
        raise HTTPException(status_code=404, detail=f"Strategy {strategy_id} not found")
    in_market = db.execute(text("""
        SELECT COALESCE(SUM(invested_capital), 0) FROM consumption.portfolio_positions_current WHERE strategy_id = :strategy_id
    """), {"strategy_id": strategy_id}).scalar() or 0
    return {
        "strategy_id": result.strategy_id, "name": result.name,
        "assigned_capital": float(result.assigned_capital) if result.assigned_capital else 100000,
        "in_market_capital": float(in_market),
        "available_for_buying": max(0, float(result.assigned_capital or 100000) - float(in_market)),
        "capacity_millions": float(result.capacity_millions) if result.capacity_millions else 100,
    }


@router.post("/strategies/{strategy_id:path}/capital")
def update_strategy_capital(strategy_id: str, payload: dict, db: Session = Depends(get_db)):
    assigned_capital = payload.get("assigned_capital")
    if assigned_capital is None or assigned_capital < 0:
        raise HTTPException(status_code=400, detail="assigned_capital must be >= 0")
    result = db.execute(text("""
        SELECT strategy_id FROM gold.strategy_registry WHERE strategy_id = :strategy_id 
    """), {"strategy_id": strategy_id}).fetchone()
    if not result:
        raise HTTPException(status_code=404, detail=f"Strategy {strategy_id} not found")
    db.execute(text("""
        UPDATE gold.strategy_registry SET assigned_capital = :capital, updated_at = NOW() WHERE strategy_id = :strategy_id
    """), {"strategy_id": strategy_id, "capital": assigned_capital})
    db.commit()
    return {"success": True, "strategy_id": strategy_id, "assigned_capital": assigned_capital}


@router.post("/strategies/{strategy_id:path}/can-buy")
def can_strategy_buy(strategy_id: str, payload: dict, db: Session = Depends(get_db)):
    proposed = payload.get("amount", 0)
    result = db.execute(text(
        "SELECT assigned_capital FROM gold.strategy_registry WHERE strategy_id = :strategy_id"
    ), {"strategy_id": strategy_id}).fetchone()
    if not result:
        raise HTTPException(status_code=404, detail="Strategy not found")
    assigned = float(result.assigned_capital or 100000)
    in_market = db.execute(text(
        "SELECT COALESCE(SUM(invested_capital), 0) FROM consumption.portfolio_positions_current WHERE strategy_id = :strategy_id"
    ), {"strategy_id": strategy_id}).scalar() or 0
    available = assigned - in_market
    can_buy = available >= proposed
    return {"can_buy": can_buy, "assigned_capital": assigned, "in_market_capital": float(in_market),
            "available_for_buying": available, "proposed_investment": proposed,
            "reason": None if can_buy else f"Only ${available:,.2f} available"}


@router.get("/strategies/{strategy_id:path}/capital-pool")
def get_strategy_capital_pool(strategy_id: str, db: Session = Depends(get_db)):
    strategy = db.execute(text(
        "SELECT strategy_id, name, assigned_capital FROM gold.strategy_registry WHERE strategy_id = :strategy_id"
    ), {"strategy_id": strategy_id}).fetchone()
    if not strategy:
        raise HTTPException(status_code=404, detail="Strategy not found")
    pool_usage = db.execute(text("""
        SELECT COALESCE(SUM(capital), 0) as used_capital, COUNT(*) as active_positions
        FROM consumption.portfolio_positions_current WHERE strategy_id = :strategy_id AND status = 'ACTIVE'
    """), {"strategy_id": strategy_id}).fetchone()
    total = float(strategy.assigned_capital) if strategy.assigned_capital else 100000
    used = float(pool_usage.used_capital) if pool_usage else 0
    trade_size = total * 0.25
    return {
        "strategy_id": strategy.strategy_id, "strategy_name": strategy.name,
        "total_assigned": total, "used": used, "available": total - used,
        "trade_size": trade_size, "active_positions": pool_usage.active_positions if pool_usage else 0,
        "max_positions": 4, "can_trade": (total - used) >= trade_size,
        "usage_pct": (used / total * 100) if total > 0 else 0,
    }


@router.post("/strategies/{strategy_id:path}/capital-pool")
def update_strategy_capital_pool(strategy_id: str, payload: dict, db: Session = Depends(get_db)):
    new_total = payload.get("total_assigned", 100000)
    result = db.execute(text("""
        UPDATE gold.strategy_registry SET assigned_capital = :total, updated_at = NOW()
        WHERE strategy_id = :strategy_id RETURNING strategy_id, name, assigned_capital
    """), {"strategy_id": strategy_id, "total": new_total}).fetchone()
    if not result:
        raise HTTPException(status_code=404, detail="Strategy not found")
    db.commit()
    return {"success": True, "strategy_id": result.strategy_id, "total_assigned": result.assigned_capital}


@router.post("/strategies/{strategy_id:path}/deactivate")
def deactivate_strategy(strategy_id: str, payload: dict = None, db: Session = Depends(get_db)):
    action = (payload or {}).get("action", "keep")
    positions = db.execute(text("""
        SELECT id, ticker, invested_capital, status FROM consumption.portfolio_positions_current WHERE strategy_id = :strategy_id
    """), {"strategy_id": strategy_id}).fetchall()
    if not positions:
        raise HTTPException(status_code=404, detail=f"No positions found for {strategy_id}")

    positions_closed = 0
    for pos in positions:
        if action == "close" and pos.invested_capital and pos.invested_capital > 0:
            db.execute(text("""
                UPDATE consumption.portfolio_positions_current SET status = 'CLOSED',
                    realized_pnl = realized_pnl + unrealized_pnl, unrealized_pnl = 0,
                    invested_capital = 0, available_capital = capital, updated_at = NOW()
                WHERE id = :id
            """), {"id": pos.id})
            positions_closed += 1
        else:
            db.execute(text("UPDATE consumption.portfolio_positions_current SET status = 'PAUSED', updated_at = NOW() WHERE id = :id"), {"id": pos.id})

    db.execute(text("""
        UPDATE gold.strategy_registry SET is_active = FALSE, updated_at = NOW() WHERE strategy_id = :strategy_id
    """), {"strategy_id": strategy_id})
    db.commit()
    return {"success": True, "strategy_id": strategy_id, "action": action,
            "positions_affected": len(positions), "positions_closed": positions_closed if action == "close" else 0}


@router.get("/strategies/{strategy_id:path}/description")
def get_strategy_description(strategy_id: str, db: Session = Depends(get_db)):
    result = db.execute(text("""
        SELECT strategy_id as id, name, description, asset_class, direction, time_horizon,
               sharpe_ratio, max_drawdown, win_rate, avg_hold_days, universe_count,
               max_position_pct, venue, capacity_millions, backtest_period
        FROM gold.strategy_registry WHERE strategy_id = :sid 
    """), {"sid": strategy_id}).fetchone()
    if result:
        return {
            "id": result.id, "name": result.name, "description": result.description,
            "asset_class": result.asset_class, "direction": result.direction, "time_horizon": result.time_horizon,
            "metrics": {
                "sharpe_ratio": float(result.sharpe_ratio) if result.sharpe_ratio else None,
                "max_drawdown": float(result.max_drawdown) if result.max_drawdown else None,
                "win_rate": float(result.win_rate) if result.win_rate else None,
            },
            "venue": result.venue, "source": "trade_algo_researcher",
        }
    raise HTTPException(status_code=404, detail=f"Strategy {strategy_id} not found")


@router.get("/strategies/{strategy_id:path}")
def get_strategy_by_id(strategy_id: str, db: Session = Depends(get_db)):
    result = db.execute(text("""
        SELECT strategy_id, name, description, asset_class, direction, time_horizon,
               sharpe_ratio, max_drawdown, win_rate, universe_tickers, max_position_pct,
               venue, status, signal_logic, exit_logic, trigger_example, why_it_works, execution_mode
        FROM gold.strategy_registry WHERE strategy_id = :strategy_id
    """), {"strategy_id": strategy_id}).fetchone()
    if not result:
        raise HTTPException(status_code=404, detail=f"Strategy {strategy_id} not found")
    tickers = result.universe_tickers.split(",") if result.universe_tickers else []
    return {
        "strategy_id": result.strategy_id, "name": result.name, "description": result.description,
        "asset_class": result.asset_class, "direction": result.direction, "time_horizon": result.time_horizon,
        "sharpe_ratio": float(result.sharpe_ratio) if result.sharpe_ratio else 0,
        "max_drawdown": float(result.max_drawdown) if result.max_drawdown else 0,
        "win_rate": float(result.win_rate) if result.win_rate else 0,
        "universe": tickers, "universe_count": len(tickers),
        "venue": result.venue, "status": result.status, "execution_mode": result.execution_mode,
        "signal_logic": result.signal_logic or "Entry conditions not specified",
        "exit_logic": result.exit_logic or "Exit at +5% profit or -5% stop loss",
        "buy_signal": result.signal_logic or "BUY signal triggered by strategy logic",
        "sell_signal": result.exit_logic or "SELL at +5% profit target or -5% stop loss",
        "take_profit": "+5% profit target", "stop_loss": "-5% stop loss limit",
    }


# =============================================================================
# Strategy Screener
# =============================================================================

@router.get("/strategies/screen/{strategy_id:path}")
def screen_stocks(strategy_id: str, min_win_rate: float = 0.5, min_sharpe: float = 0.8,
                  max_drawdown: float = 15.0, market: str = None, limit: int = 50,
                  db: Session = Depends(get_db)):
    """Screen stocks with a strategy using pre-computed backtests."""
    strategy = db.execute(text(
        "SELECT id, name, description, asset_class FROM gold.strategy_templates WHERE id = :strategy_id"
    ), {"strategy_id": strategy_id}).fetchone()
    if not strategy:
        strategy = db.execute(text("""
            SELECT strategy_id as id, name, description, asset_class
            FROM gold.strategy_registry WHERE strategy_id = :strategy_id 
        """), {"strategy_id": strategy_id}).fetchone()
    if not strategy:
        raise HTTPException(status_code=404, detail=f"Strategy {strategy_id} not found")

    market_filter = "AND b.market = :market" if market else ""
    params = {"strategy_id": strategy_id, "min_win_rate": min_win_rate / 100,
              "min_sharpe": min_sharpe, "max_drawdown": max_drawdown, "limit": limit}
    if market:
        params["market"] = market

    result = db.execute(text(f"""
        SELECT b.ticker, b.market, b.win_rate, b.sharpe_ratio, b.profit_factor,
               b.total_return, b.max_drawdown, b.num_trades, b.avg_trade_return,
               b.current_signal, b.signal_strength, b.entry_price, b.stop_loss,
               b.target_price, b.strategy_score, b.rationale, b.calculated_at,
               s.close_price as current_price
        FROM gold.strategy_backtests b
        LEFT JOIN LATERAL (SELECT close_price FROM consumption.stock WHERE ticker = b.ticker ORDER BY timestamp DESC LIMIT 1) s ON true
        WHERE b.strategy_id = :strategy_id AND b.win_rate >= :min_win_rate
        AND b.sharpe_ratio >= :min_sharpe AND b.max_drawdown <= :max_drawdown {market_filter}
        ORDER BY b.strategy_score DESC LIMIT :limit
    """), params).fetchall()

    results = [{"rank": i + 1, "ticker": r.ticker, "market": r.market, "current_price": r.current_price or r.entry_price,
                "strategy_score": float(r.strategy_score or 0), "win_rate": float(r.win_rate or 0),
                "sharpe_ratio": float(r.sharpe_ratio or 0), "signal": r.current_signal or "HOLD",
                "signal_strength": float(r.signal_strength or 0),
                "entry_price": float(r.entry_price) if r.entry_price else None,
                "stop_loss": float(r.stop_loss) if r.stop_loss else None,
                "target": float(r.target_price) if r.target_price else None}
               for i, r in enumerate(result)]

    return {"strategy": {"id": strategy.id, "name": strategy.name, "description": strategy.description},
            "results": results, "total": len(results)}


@router.get("/strategies/export/{strategy_id}")
def export_strategy_results(strategy_id: str, format: str = "csv", min_win_rate: float = 0.5,
                            min_sharpe: float = 0.8, market: str = None, db: Session = Depends(get_db)):
    """Export screening results to CSV."""
    from fastapi.responses import StreamingResponse
    import csv, io

    market_filter = "AND b.market = :market" if market else ""
    params = {"strategy_id": strategy_id, "min_win_rate": min_win_rate / 100, "min_sharpe": min_sharpe, "limit": 1000}
    if market:
        params["market"] = market

    result = db.execute(text(f"""
        SELECT b.ticker, b.market, b.win_rate, b.sharpe_ratio, b.profit_factor, b.total_return,
               b.max_drawdown, b.num_trades, b.current_signal, b.strategy_score, b.entry_price, b.stop_loss, b.target_price
        FROM gold.strategy_backtests b WHERE b.strategy_id = :strategy_id
        AND b.win_rate >= :min_win_rate AND b.sharpe_ratio >= :min_sharpe {market_filter}
        ORDER BY b.strategy_score DESC LIMIT :limit
    """), params).fetchall()

    if format == "csv":
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["Rank", "Ticker", "Market", "Signal", "Score", "Win Rate", "Sharpe", "Trades"])
        for i, r in enumerate(result, 1):
            writer.writerow([i, r.ticker, r.market, r.current_signal or "HOLD",
                             f"{r.strategy_score:.3f}" if r.strategy_score else "0",
                             f"{r.win_rate * 100:.1f}%" if r.win_rate else "0%",
                             f"{r.sharpe_ratio:.2f}" if r.sharpe_ratio else "0", r.num_trades or 0])
        output.seek(0)
        return StreamingResponse(io.BytesIO(output.getvalue().encode()), media_type="text/csv",
                                 headers={"Content-Disposition": f"attachment; filename={strategy_id}_screening.csv"})
    return {"strategy_id": strategy_id, "results": [{"rank": i + 1, "ticker": r.ticker} for i, r in enumerate(result)]}


@router.get("/strategies/stats")
def get_strategy_stats(db: Session = Depends(get_db)):
    """Get actual performance stats for all deployed strategies."""
    result = db.execute(text("""
        SELECT ps.strategy_id, sd.name as strategy_name, COUNT(*) as total_positions,
               SUM(CASE WHEN ps.trades_count > 0 THEN 1 ELSE 0 END) as active_positions,
               SUM(COALESCE(ps.invested_capital, 0)) as total_invested,
               SUM(COALESCE(ps.realized_pnl, 0)) as total_realized_pnl,
               SUM(COALESCE(ps.unrealized_pnl, 0)) as total_unrealized_pnl,
               SUM(ps.capital) as total_allocated,
               COUNT(CASE WHEN (COALESCE(ps.realized_pnl, 0) + COALESCE(ps.unrealized_pnl, 0)) > 0 THEN 1 END) as winning_positions,
               SUM(ps.trades_count) as total_trades
        FROM consumption.portfolio_positions_current ps
        LEFT JOIN gold.strategy_registry sd ON ps.strategy_id = sd.strategy_id
        WHERE ps.status = 'ACTIVE' GROUP BY ps.strategy_id, sd.name
    """)).fetchall()

    stats = {}
    for r in result:
        total_pnl = (r.total_realized_pnl or 0) + (r.total_unrealized_pnl or 0)
        win_rate = (r.winning_positions / r.active_positions * 100) if r.active_positions and r.active_positions > 0 else 0
        stats[r.strategy_id] = {
            "strategy_id": r.strategy_id, "strategy_name": r.strategy_name,
            "total_positions": r.total_positions, "active_positions": r.active_positions,
            "total_invested": float(r.total_invested or 0), "total_allocated": float(r.total_allocated or 0),
            "total_pnl": total_pnl, "actual_win_rate": round(win_rate, 1), "total_trades": r.total_trades or 0,
        }
    return {"success": True, "stats": stats, "count": len(stats)}


@router.post("/strategies/execute-order")
def execute_strategy_order(payload: dict, db: Session = Depends(get_db)):
    """Execute order based on execution mode."""
    from app.services.ib_service import ib_quant_service
    strategy_id = payload.get("strategy_id")
    ticker = payload.get("ticker")
    side = payload.get("side")
    quantity = payload.get("quantity", 100)
    order_type = payload.get("order_type", "MKT")

    strategy = db.execute(text("""
        SELECT strategy_id, name, execution_mode, venue FROM gold.strategy_registry WHERE strategy_id = :strategy_id
    """), {"strategy_id": strategy_id}).fetchone()
    if not strategy:
        raise HTTPException(status_code=404, detail="Strategy not found")

    execution_mode = strategy.execution_mode or "SIMULATION"

    db.execute(text("""
        INSERT INTO gold.trade_executions (strategy_id, ticker, execution_mode, order_type, side, quantity, status)
        VALUES (:strategy_id, :ticker, :mode, :order_type, :side, :qty, 'PENDING')
    """), {"strategy_id": strategy_id, "ticker": ticker, "mode": execution_mode, "order_type": order_type, "side": side, "qty": quantity})
    db.commit()

    if execution_mode == "SIMULATION":
        amount = quantity * 100
        if side == "BUY":
            db.execute(text("""
                UPDATE consumption.portfolio_positions_current SET invested_capital = invested_capital + :amount,
                    available_capital = available_capital - :amount, trades_count = trades_count + 1,
                    last_order_status = 'SIMULATED_BUY' WHERE strategy_id = :sid AND ticker = :ticker
            """), {"sid": strategy_id, "ticker": ticker, "amount": amount})
        else:
            db.execute(text("""
                UPDATE consumption.portfolio_positions_current SET invested_capital = GREATEST(0, invested_capital - :amount),
                    available_capital = available_capital + :amount, trades_count = trades_count + 1,
                    last_order_status = 'SIMULATED_SELL' WHERE strategy_id = :sid AND ticker = :ticker
            """), {"sid": strategy_id, "ticker": ticker, "amount": amount})
        db.commit()
        return {"success": True, "execution_mode": "SIMULATION",
                "message": f"Simulated {side} order for {quantity} of {ticker}",
                "order_id": f"SIM_{int(time.time())}", "status": "COMPLETED"}

    return {"success": True, "execution_mode": execution_mode,
            "message": f"{execution_mode} order submitted for {ticker}",
            "order_id": f"PENDING_{int(time.time())}", "status": "PENDING"}
