import requests
from app.db.session import get_db_session
from app.dependencies import logger

def update_registry_oos_from_latest_backtest():
    """Backfill gold.strategy_registry OOS columns from latest strategy_backtest_runs.
    
    Intended to run from the trading-platform backend context."""
    try:
        with get_db_session() as db:
            # Find strategies whose registry OOS columns are null or stale
            rows = db.execute("""
                SELECT sr.strategy_id
                FROM gold.strategy_registry sr
                JOIN (
                    SELECT DISTINCT ON (strategy_id) strategy_id, created_at,
                           sharpe_oos, max_drawdown_oos, trade_count_oos, win_rate_oos, returns_oos
                    FROM gold.strategy_backtest_runs
                    ORDER BY strategy_id, created_at DESC
                ) latest ON sr.strategy_id = latest.strategy_id
                WHERE sr.status != 'DEPRECATED'
            """).fetchall()
            updated = 0
            for row in rows:
                db.execute("""
                    UPDATE gold.strategy_registry sr
                    SET sharpe_oos = latest.sharpe_oos,
                        max_drawdown_oos = latest.max_drawdown_oos,
                        trade_count_oos = latest.trade_count_oos,
                        win_rate_oos = latest.win_rate_oos,
                        returns_oos = latest.returns_oos,
                        updated_at = NOW()
                    FROM (
                        SELECT DISTINCT ON (strategy_id) strategy_id,
                               sharpe_oos, max_drawdown_oos, trade_count_oos, win_rate_oos, returns_oos
                        FROM gold.strategy_backtest_runs
                        ORDER BY strategy_id, created_at DESC
                    ) latest
                    WHERE sr.strategy_id = latest.strategy_id AND sr.strategy_id = :sid
                """, {"sid": row.strategy_id})
                updated += 1
            db.commit()
            logger.info(f"Updated {updated} strategy_registry OOS rows from latest backtest runs.")
            return {"updated": updated}
    except Exception as e:
        logger.error(f"update_registry_oos_from_latest_backtest error: {e}")
        raise
