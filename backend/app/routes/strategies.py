"""Strategy endpoints — CRUD, templates, screener, deploy, capital management."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime, timezone
from decimal import Decimal
import time
import logging

from app.dependencies import get_db, logger, api_to_registry_mode, registry_to_api_mode
from app.db.safe_query import safe_query, safe_query_one


logger = logging.getLogger(__name__)

def _coerce_number(v):
    """Convert Decimal/numeric DB values to JSON-serializable floats; preserve None."""
    if v is None:
        return None
    if isinstance(v, Decimal):
        return float(v)
    if isinstance(v, (int, float)):
        return float(v) if isinstance(v, float) else v
    try:
        return float(v)
    except Exception:
        return v


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
def delete_strategy(strat_id: str, db: Session = Depends(get_db)):
    db.execute(text("DELETE FROM gold.strategy_registry WHERE asset_class = 'quant' AND strategy_id = :sid"), {"sid": strat_id})
    db.commit()
    return {"status": "success"}


# =============================================================================
# Researcher Strategies
# =============================================================================

# /strategies/researcher fans out into ~8 registry/backtest/signal queries and is
# polled by six different frontend surfaces at 60s intervals. A short in-process
# cache collapses those overlapping polls into one query burst. `fresh=1` bypasses
# it (the promote flow uses this so a confirmed mode change is visible immediately).
_RESEARCHER_TTL_S = 15
_researcher_cache = {}  # (asset_class, priority, status) -> (monotonic_ts, payload)


@router.get("/strategies/researcher")
def get_researcher_strategies(asset_class: str = None, priority: str = None, status: str = None, fresh: int = 0, db: Session = Depends(get_db)):
    """Get JT Researcher strategies from strategy_registry with backtest data and top signals."""
    cache_key = (asset_class, priority, status)
    if not fresh:
        cached = _researcher_cache.get(cache_key)
        if cached and (time.monotonic() - cached[0]) < _RESEARCHER_TTL_S:
            return cached[1]
    try:
        # Build query with all columns - safe_query handles errors gracefully.
        # Only publish strategies that are not retired/paused/rejected and have
        # baseline backtest metrics (sharpe>=0.5, |dd|<=20%, trades>=30, returns set).
        query = """
            SELECT r.strategy_id as id, r.name, r.asset_class, r.universe_tickers, r.frequency,
                   r.execution_mode, r.status, r.sharpe_oos, r.max_drawdown_oos,
                   r.trade_count_oos, r.win_rate_oos, r.profit_factor_oos, r.returns_oos,
                   r.conviction_score, r.description,
                   r.assigned_capital, r.in_market_capital, r.signal_logic, r.exit_logic,
                   r.priority, r.approved_at, res.status as research_status
            FROM gold.strategy_registry r
            JOIN gold.strategy_research res ON res.strategy_id = r.strategy_id
            WHERE r.status != 'DEPRECATED'
              AND r.status != 'retired'
              AND res.status NOT IN ('rejected', 'retired')
              AND r.priority IN ('EXPERIMENTAL', 'NEAR_GOLDEN', 'GOLDEN')
        """
        params = {}
        if asset_class:
            query += " AND r.asset_class = :asset_class"
            params["asset_class"] = asset_class
        if status and status != 'ALL':
            query += " AND r.status = :status"
            params["status"] = status
        if priority:
            query += " AND r.priority = :priority"
            params["priority"] = priority.upper()
        query += " ORDER BY r.sharpe_oos DESC NULLS LAST"

        result = safe_query(db, query, params, label="route_researcher_strategies")

        # Latest OOS metrics per strategy come from the most recent backtest run,
        # not the registry snapshot. Registry OOS fields are stale after each new
        # backtest, so we overlay the latest backtest row on top of registry data.
        latest_backtest_data = {}
        yearly_backtest_data = {}
        try:
            all_bt = safe_query(db, """
                SELECT DISTINCT ON (strategy_id)
                       strategy_id,
                       annual_pnl_2024 as pnl_2024,
                       annual_pnl_2025 as pnl_2025,
                       annual_pnl_2026 as pnl_2026,
                       trade_count_oos,
                       sharpe_oos,
                       max_drawdown_oos,
                       win_rate_oos,
                       profit_factor_oos,
                       returns_oos
                FROM gold.strategy_backtest_runs
                WHERE strategy_id IS NOT NULL
                ORDER BY strategy_id, created_at DESC
            """, {}, label="route_latest_bt")
            for yb in all_bt:
                sid = getattr(yb, 'strategy_id', None)
                if not sid:
                    continue
                pnl_2024 = getattr(yb, 'pnl_2024', None)
                pnl_2025 = getattr(yb, 'pnl_2025', None)
                pnl_2026 = getattr(yb, 'pnl_2026', None)
                latest_backtest_data[sid] = {
                    'trade_count_oos': int(yb.trade_count_oos) if yb.trade_count_oos is not None else 0,
                    'sharpe_oos': float(yb.sharpe_oos) if yb.sharpe_oos is not None else None,
                    'max_drawdown_oos': float(yb.max_drawdown_oos) if yb.max_drawdown_oos is not None else None,
                    'win_rate_oos': float(yb.win_rate_oos) if yb.win_rate_oos is not None else None,
                    'profit_factor_oos': float(yb.profit_factor_oos) if yb.profit_factor_oos is not None else None,
                    'returns_oos': float(yb.returns_oos) if yb.returns_oos is not None else None,
                }
                if sid not in yearly_backtest_data:
                    yearly_backtest_data[sid] = {}
                if pnl_2024 is not None:
                    yearly_backtest_data[sid]['2024'] = {
                        'return_pct': float(pnl_2024),
                        'trades': int(yb.trade_count_oos) if yb.trade_count_oos is not None else 0,
                        'sharpe': float(yb.sharpe_oos) if yb.sharpe_oos is not None else None,
                        'max_drawdown': float(yb.max_drawdown_oos) if yb.max_drawdown_oos is not None else None,
                        'win_rate': float(yb.win_rate_oos) if yb.win_rate_oos is not None else None
                    }
                if pnl_2025 is not None:
                    yearly_backtest_data[sid]['2025'] = {
                        'return_pct': float(pnl_2025),
                        'trades': int(yb.trade_count_oos) if yb.trade_count_oos is not None else 0,
                        'sharpe': float(yb.sharpe_oos) if yb.sharpe_oos is not None else None,
                        'max_drawdown': float(yb.max_drawdown_oos) if yb.max_drawdown_oos is not None else None,
                        'win_rate': float(yb.win_rate_oos) if yb.win_rate_oos is not None else None
                    }
                if pnl_2026 is not None:
                    yearly_backtest_data[sid]['2026'] = {
                        'return_pct': float(pnl_2026),
                        'trades': int(yb.trade_count_oos) if yb.trade_count_oos is not None else 0,
                        'sharpe': float(yb.sharpe_oos) if yb.sharpe_oos is not None else None,
                        'max_drawdown': float(yb.max_drawdown_oos) if yb.max_drawdown_oos is not None else None,
                        'win_rate': float(yb.win_rate_oos) if yb.win_rate_oos is not None else None
                    }
        except Exception as e:
            logger.error(f"Backtest overlay fetch error: {e}")
        
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

        # ------------------------------------------------------------------
        # Paper-trading monitoring state + real paper metrics (same source of
        # truth used by /api/strategies/pipeline-feed). Registry execution_mode
        # can be stale (many rows marked PAPER_TRADING but not actively
        # deployed), so the UI also needs the live monitoring flag.
        # kanban t_1f3bee9f: `is_paper_monitoring` = ETL paper monitor running
        # (gold.strategy_paper_monitoring.is_active); `paper_state` separates
        # 'engaged' (open paper positions now) from 'watching' (monitored but
        # flat book) and 'off'.
        # ------------------------------------------------------------------
        registry_ids = [r.id for r in result if r.id]
        monitoring_ids = set()
        engaged_counts = {}
        paper_metrics = {}
        if registry_ids:
            try:
                monitored_rows = safe_query(
                    db,
                    """
                    SELECT strategy_id
                    FROM gold.strategy_paper_monitoring
                    WHERE strategy_id = ANY(:ids)
                      AND is_active = true
                    """,
                    {"ids": registry_ids},
                    label="route_paper_monitoring_flag",
                )
                monitoring_ids = {r.strategy_id for r in monitored_rows}
            except Exception as e:
                logger.error(f"paper monitoring flag query error: {e}")
            try:
                engaged_rows = safe_query(
                    db,
                    """
                    SELECT strategy_id, COUNT(*) AS open_positions
                    FROM consumption.portfolio_positions_current
                    WHERE strategy_id = ANY(:ids)
                      AND status = 'ACTIVE'
                      AND execution_mode = 'PAPER_TRADING'
                    GROUP BY strategy_id
                    """,
                    {"ids": registry_ids},
                    label="route_paper_engaged",
                )
                engaged_counts = {r.strategy_id: int(r.open_positions or 0) for r in engaged_rows}
            except Exception as e:
                logger.error(f"paper engaged state query error: {e}")

        # Paper metrics are computed for every registry row that has real closed
        # paper trades — not only currently-monitored ones. Gating on
        # monitoring_ids hid the track record (P&L / PF / WR) for strategies
        # whose paper runs already closed trades.
        # t_f51d67fe: read the canonical paper ledger gold.paper_trades_synthetic
        # (same source as /api/strategies/pipeline-feed and the Strategy Detail
        # evaluation endpoint), not the legacy gold.paper_trades — the two
        # ledgers diverged and showed contradictory track records for the same
        # strategy. CASH bucket placeholder excluded as in pipeline-feed.
        if registry_ids:
            try:
                paper_rows = safe_query(
                    db,
                    """
                    SELECT strategy_id,
                           COUNT(*) FILTER (WHERE status = 'closed') AS closed_trades,
                           COUNT(*) FILTER (WHERE status = 'closed' AND pnl > 0) AS winning_trades,
                           SUM(pnl) FILTER (WHERE status = 'closed') AS total_pnl,
                           SUM(pnl) FILTER (WHERE status = 'closed' AND pnl > 0) AS gross_profit,
                           SUM(pnl) FILTER (WHERE status = 'closed' AND pnl < 0) AS gross_loss
                    FROM gold.paper_trades_synthetic
                    WHERE strategy_id = ANY(:ids)
                      AND (ticker IS NULL OR ticker != 'CASH')
                    GROUP BY strategy_id
                    """,
                    {"ids": registry_ids},
                    label="route_paper_metrics",
                )
                for r in paper_rows:
                    closed = int(r.closed_trades or 0)
                    wins = int(r.winning_trades or 0)
                    pnl = _coerce_number(r.total_pnl)
                    gross_profit = _coerce_number(r.gross_profit) or 0
                    gross_loss = _coerce_number(r.gross_loss) or 0
                    paper_metrics[r.strategy_id] = {
                        "paper_wr": (wins / closed * 100) if closed > 0 else None,
                        "paper_pf": (gross_profit / abs(gross_loss)) if gross_loss and gross_loss != 0 else None,
                        "paper_pnl_realized": pnl,
                        "paper_trades": closed,
                    }
            except Exception as e:
                logger.error(f"paper metrics query error: {e}")

        # Unrealized P&L for OPEN paper positions (mark-to-market).
        # consumption.portfolio_positions_current paper rows ARE marked to
        # market by the ETL (sync_paper_positions_current.py, t_646c098a:
        # latest gold.daily_ohlcv close, fallback entry_price), so read
        # unrealized_pnl directly — no serve-time recomputation.
        if registry_ids:
            try:
                open_rows = safe_query(
                    db,
                    """
                    SELECT p.strategy_id, p.unrealized_pnl
                    FROM consumption.portfolio_positions_current p
                    WHERE p.strategy_id = ANY(:ids)
                      AND p.status = 'ACTIVE'
                      AND p.quantity > 0
                      AND p.execution_mode = 'PAPER_TRADING'
                      AND (p.ticker IS NULL OR p.ticker != 'CASH')
                    """,
                    {"ids": registry_ids},
                    label="route_paper_unrealized",
                )
                for r in open_rows:
                    m = paper_metrics.setdefault(r.strategy_id, {
                        "paper_wr": None, "paper_pf": None,
                        "paper_pnl_realized": None, "paper_trades": 0,
                    })
                    unr = _coerce_number(r.unrealized_pnl)
                    if unr is not None:
                        m["paper_pnl_unrealized"] = (m.get("paper_pnl_unrealized") or 0) + unr
                    else:
                        m["paper_unpriced"] = (m.get("paper_unpriced") or 0) + 1
            except Exception as e:
                logger.error(f"paper unrealized query error: {e}")

        # Total = realized + unrealized: an open book with no closed trades
        # yet shows mark-to-market P&L instead of NULL.
        for m in paper_metrics.values():
            m["paper_pnl"] = (m.get("paper_pnl_realized") or 0) + (m.get("paper_pnl_unrealized") or 0)

        # Per-year realized paper P&L for the Performance tab's paper bars.
        # Same canonical ledger as the metrics above; return_pct is expressed
        # in PERCENTAGE POINTS of the strategy's assigned capital (unlike
        # yearly_backtest, which is a ratio) — the frontend renders it raw.
        paper_yearly_data = {}
        if registry_ids:
            try:
                py_rows = safe_query(
                    db,
                    """
                    SELECT strategy_id,
                           EXTRACT(YEAR FROM exit_date)::int AS y,
                           SUM(pnl) AS pnl,
                           COUNT(*) AS trades
                    FROM gold.paper_trades_synthetic
                    WHERE status = 'closed'
                      AND strategy_id = ANY(:ids)
                      AND (ticker IS NULL OR ticker != 'CASH')
                    GROUP BY strategy_id, EXTRACT(YEAR FROM exit_date)
                    """,
                    {"ids": registry_ids},
                    label="route_paper_yearly",
                )
                for r in py_rows:
                    paper_yearly_data.setdefault(r.strategy_id, {})[str(int(r.y))] = {
                        "pnl": float(r.pnl or 0),
                        "trades": int(r.trades or 0),
                    }
            except Exception as e:
                logger.error(f"paper yearly query error: {e}")

        strategies = []
        for row in result:
            tickers = row.universe_tickers
            if isinstance(tickers, str):
                tickers = [t.strip() for t in tickers.split(",") if t.strip()] if tickers else []
            elif tickers is None:
                tickers = []
            elif hasattr(tickers, '__iter__') and not isinstance(tickers, (str, bytes)):
                tickers = [str(t).strip() for t in tickers if str(t).strip()]
            else:
                tickers = []
            tickers = [t for t in tickers if t.upper() != 'CASH']
            
            sid = row.id
            strategy_signals = top_signals_data.get(sid, [])
            top_tickers = strategy_signals if strategy_signals else [
                {'ticker': t, 'signal': 'HOLD', 'confidence': None, 'strength': None} for t in tickers[:5]
            ]
            yearly_data = yearly_backtest_data.get(sid, {})
            # Paper yearly bars: realized P&L per exit year as percentage
            # points of assigned capital (raw scale — NOT a ratio).
            _cap = float(row.assigned_capital) if row.assigned_capital else None
            paper_yearly = {
                y: {
                    "return_pct": (v["pnl"] / _cap * 100) if _cap else None,
                    "pnl": v["pnl"],
                    "trades": v["trades"],
                }
                for y, v in paper_yearly_data.get(sid, {}).items()
            }
            oos = latest_backtest_data.get(sid, {})

            # Open-book summary for the Performance tab paper bars: when a
            # strategy is engaged but has no closed trades yet, the realized
            # bars are legitimately empty — surface the mark-to-market open
            # book as a clearly-labelled unrealized overlay instead of a
            # bare empty state. Never mixed into paper_yearly (realized only).
            _unr = paper_metrics.get(sid, {}).get("paper_pnl_unrealized")
            _open_n = int(engaged_counts.get(sid, 0))
            paper_open = None
            if _unr is not None and _open_n > 0:
                paper_open = {
                    "unrealized_pnl": round(float(_unr), 2),
                    "return_pct": (float(_unr) / _cap * 100) if _cap else None,
                    "positions": _open_n,
                }
            
            # Backtest row is the source of truth for OOS metrics; fallback to registry only
            # when no backtest run exists. Preserve nulls so the frontend can distinguish
            # genuinely missing metrics from zeros; coerce None to 0 only for trade_count.
            r_trade_count = getattr(row, 'trade_count_oos', None)
            r_sharpe = getattr(row, 'sharpe_oos', None)
            r_maxdd = getattr(row, 'max_drawdown_oos', None)
            r_winrate = getattr(row, 'win_rate_oos', None)
            r_profit = getattr(row, 'profit_factor_oos', None)
            r_returns = getattr(row, 'returns_oos', None)

            trade_count = oos.get('trade_count_oos') if oos.get('trade_count_oos') is not None else (
                int(r_trade_count) if r_trade_count is not None else 0
            )
            sharpe = oos.get('sharpe_oos') if oos.get('sharpe_oos') is not None else (
                float(r_sharpe) if r_sharpe is not None else None
            )
            max_drawdown = oos.get('max_drawdown_oos') if oos.get('max_drawdown_oos') is not None else (
                float(r_maxdd) if r_maxdd is not None else None
            )
            win_rate = oos.get('win_rate_oos') if oos.get('win_rate_oos') is not None else (
                float(r_winrate) if r_winrate is not None else None
            )
            profit_factor = oos.get('profit_factor_oos') if oos.get('profit_factor_oos') is not None else (
                float(r_profit) if r_profit is not None else None
            )
            returns_oos = oos.get('returns_oos') if oos.get('returns_oos') is not None else (
                float(r_returns) if r_returns is not None else None
            )

            # Include all registry rows that passed the status/priority filters. Metric gates
            # are intentionally NOT used to drop rows here; they only filter the Researcher
            # tab when the consumer applies them. Strategy Lab needs the metadata (description,
            # universe, logic) for every approved pipeline strategy, and pipeline-feed already
            # applies its own quality gates for the table metrics.

            # Normalize percentage metrics: registry + backtest store win_rate/max_drawdown as
            # fractions (0.625 = 62.5%, -0.11 = -11%), but Strategy Lab renders them with a
            # '%' suffix. Multiply decimals to percentage points for display consistency.
            if win_rate is not None and abs(win_rate) <= 1.0:
                win_rate = win_rate * 100.0
            if max_drawdown is not None and abs(max_drawdown) <= 1.0:
                max_drawdown = max_drawdown * 100.0

            # Derive UI dimensions from registry fields (frequency -> time_horizon, asset_class -> venue,
            # signal_logic long/short -> direction). Fallback to safe defaults if data is missing.
            freq = (row.frequency or '').lower() if hasattr(row, 'frequency') else ''
            if freq in ('daily', '1d', 'intraday', 'hourly', '4h'):
                time_horizon = 'Short-term'
            elif freq in ('weekly', '1w', 'week'):
                time_horizon = 'Medium-term'
            elif freq in ('monthly', '1m', 'month'):
                time_horizon = 'Long-term'
            else:
                time_horizon = 'Medium-term'

            sig = (row.signal_logic or '').lower() if row.signal_logic else ''
            if 'short' in sig or 'short' in (row.exit_logic or '').lower():
                direction = 'Short'
            elif 'long' in sig or 'long' in (row.exit_logic or '').lower():
                direction = 'Long'
            else:
                direction = 'Long'

            ac = (row.asset_class or '').lower()
            tickers = row.universe_tickers or []
            if 'us stock' in ac or 'us_stk' in ac or 'equity' in ac:
                venue = 'US Equities'
            elif 'hk' in ac:
                venue = 'HK Equities'
            elif 'etf' in ac:
                venue = 'ETFs'
            elif 'crypto' in ac:
                venue = 'Crypto'
            elif 'commodity' in ac or 'future' in ac:
                venue = 'Futures'
            elif 'fx' in ac or 'currency' in ac or 'forex' in ac:
                venue = 'FX'
            else:
                venue = 'Multi-Asset'

            strategies.append({
                "id": sid, "name": row.name,
                "description": row.description,
                "asset_class": row.asset_class,
                "sharpe_ratio": sharpe,
                "max_drawdown": max_drawdown,
                "win_rate": win_rate,
                "profit_factor": profit_factor,
                "backtest_trades": trade_count,
                "trade_count_oos": trade_count,
                "returns_oos": returns_oos,
                "time_horizon": time_horizon,
                "direction": direction,
                "venue": venue,
                "universe": tickers, "universe_count": len(tickers),
                "status": row.status, "source": "trade_algo_researcher",
                "execution_mode": registry_to_api_mode(row.execution_mode),
                "conviction_score": float(row.conviction_score) if row.conviction_score else None,
                "assigned_capital": float(row.assigned_capital) if row.assigned_capital else None,
                "in_market_capital": float(row.in_market_capital) if row.in_market_capital else None,
                "signal_logic": row.signal_logic,
                "exit_logic": row.exit_logic,
                "entry_logic": row.signal_logic,
                "priority": row.priority if row.priority else None,
                "version": None,
                "top_tickers": top_tickers,
                "yearly_backtest": yearly_data,
                "paper_yearly": paper_yearly,
                "signal_family_key": family_by_strategy.get(sid),
                "is_paper_monitoring": sid in monitoring_ids,
                "paper_engaged": engaged_counts.get(sid, 0) > 0,
                "paper_open_positions": engaged_counts.get(sid, 0),
                "paper_state": ('engaged' if engaged_counts.get(sid, 0) > 0
                                 else ('watching' if sid in monitoring_ids else 'off')),
                "paper_wr": paper_metrics.get(sid, {}).get("paper_wr"),
                "paper_pf": paper_metrics.get(sid, {}).get("paper_pf"),
                "paper_pnl": paper_metrics.get(sid, {}).get("paper_pnl"),
                "paper_pnl_realized": paper_metrics.get(sid, {}).get("paper_pnl_realized"),
                "paper_pnl_unrealized": paper_metrics.get(sid, {}).get("paper_pnl_unrealized"),
                "paper_unpriced": paper_metrics.get(sid, {}).get("paper_unpriced", 0),
                "paper_trades": paper_metrics.get(sid, {}).get("paper_trades"),
                "paper_open": paper_open,
            })
        # Also fetch from strategy_templates if they have different strategies
        template_strategies = []
        try:
            templates = safe_query(db, """
                SELECT template_id AS id, name, description, asset_class, min_win_rate, min_sharpe, max_holding_days
                FROM gold.strategy_templates
                WHERE template_id NOT IN (SELECT strategy_id FROM gold.strategy_registry)
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
                        "execution_mode": registry_to_api_mode(q.execution_mode),
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
                        "is_paper_monitoring": False,
                        "paper_engaged": False,
                        "paper_open_positions": 0,
                        "paper_state": "off",
                        "paper_wr": None,
                        "paper_pf": None,
                        "paper_pnl": None,
                        "paper_trades": None,
                        })
        except Exception as e:
            logger.error(f"Quant fetch error: {e}")
        
        # Combine all strategies. Templates (source="template") are intentionally
        # excluded from the main Performance grid because they have no registry
        # row, no live trades, no equity curve, and no signals. The templates
        # endpoint remains available for the "Create Strategy" / template browser
        # workflow when the UI wires it up.
        all_strategies = strategies + quant_strategies

        payload = {"strategies": all_strategies, "count": len(all_strategies)}
        _researcher_cache[cache_key] = (time.monotonic(), payload)
        return payload
    except Exception as e:
        logger.error(f"Route researcher strategies error: {e}")
        return {"strategies": [], "count": 0}


# =============================================================================
# Strategy Templates by Asset
# =============================================================================

@router.get("/strategies/templates")
def get_strategy_templates(asset_class: str = None, db: Session = Depends(get_db)):
    query = "SELECT template_id, name, description, asset_class, min_win_rate, min_sharpe, max_holding_days FROM gold.strategy_templates"
    params = {}
    if asset_class:
        query += " WHERE asset_class = :asset_class"
        params["asset_class"] = asset_class.upper()
    result = db.execute(text(query), params).fetchall()
    return [{
        "id": r.template_id,
        "name": r.name,
        "description": r.description,
        "asset_class": r.asset_class,
        "min_win_rate": float(r.min_win_rate) if r.min_win_rate is not None else None,
        "min_sharpe": float(r.min_sharpe) if r.min_sharpe is not None else None,
        "max_holding_days": r.max_holding_days
    } for r in result]


@router.get("/strategies/templates/{asset_class}")
def get_templates_for_asset(asset_class: str, db: Session = Depends(get_db)):
    result = db.execute(text("""
        SELECT template_id, name, description, asset_class, min_win_rate, min_sharpe, max_holding_days
        FROM gold.strategy_templates WHERE asset_class = :asset_class
    """), {"asset_class": asset_class.upper()}).fetchall()
    return {r.template_id: {
        "id": r.template_id, "name": r.name, "description": r.description,
        "asset_class": r.asset_class, "min_win_rate": float(r.min_win_rate) if r.min_win_rate is not None else None,
        "min_sharpe": float(r.min_sharpe) if r.min_sharpe is not None else None,
        "max_holding_days": r.max_holding_days
    } for r in result}


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
    """Deploy strategy with capital pool — 25% per trade, max 4 positions.

    The caller may pass `mode` to override the global execution mode; Strategy Lab
    sends `PAPER_TRADING` so that "Deploy" starts paper-trading monitoring and the
    live columns are populated from real paper trades.
    """
    strategy_id = payload.get("strategy_id")
    tickers = payload.get("tickers", [])
    total_pool = payload.get("total_pool", 100000)
    trade_size_pct = payload.get("trade_size_pct", 0.25)
    requested_mode = payload.get("mode")

    if not strategy_id or not tickers:
        raise HTTPException(status_code=400, detail="strategy_id and tickers required")

    mode_result = db.execute(text(
        "SELECT value FROM gold.platform_settings WHERE key = 'global_execution_mode'"
    )).fetchone()
    current_mode = requested_mode or (mode_result.value if mode_result else "SIMULATION")
    if current_mode == "PAPER_UAT":  # legacy pre-rename API vocabulary
        current_mode = "UAT"
    if current_mode not in ("SIMULATION", "PAPER_TRADING", "UAT", "LIVE_TRADING"):
        current_mode = "SIMULATION"

    strategy = db.execute(text(
        "SELECT * FROM gold.strategy_registry WHERE strategy_id = :sid "
    ), {"sid": strategy_id}).fetchone()
    if not strategy:
        raise HTTPException(status_code=404, detail=f"Strategy {strategy_id} not found")

    # Used capital is read the same way /api/strategies/{id}/capital-pool does:
    # post-sync consumption rows for the strategy, no execution_mode filter.
    pool_status = db.execute(text("""
        SELECT COALESCE(SUM(capital), 0) as used FROM consumption.portfolio_positions_current
        WHERE strategy_id = :strategy_id AND status = 'ACTIVE'
    """), {"strategy_id": strategy_id}).fetchone()

    current_used = float(pool_status.used) if pool_status else 0
    available = total_pool - current_used
    trade_size = total_pool * trade_size_pct

    # For PAPER/SIMULATION registry strategies the paper ledger
    # (gold.paper_trades_synthetic, written by the ETL rebalancer and synced
    # into consumption.portfolio_positions_current) is the source of truth.
    # For UAT strategies positions live at the IBKR UAT session (broker
    # rehearsal) — also never written here.
    # Do NOT write placeholder capital rows here — only persist the requested
    # execution mode to the registry so the rebalancer picks the strategy up.
    registry_api_mode = registry_to_api_mode(getattr(strategy, "execution_mode", None))
    if registry_api_mode in ("PAPER_TRADING", "SIMULATION", "UAT") or current_mode == "UAT":
        registry_mode = api_to_registry_mode(current_mode)
        db.execute(text("""
            UPDATE gold.strategy_registry
            SET execution_mode = :mode,
                status = CASE WHEN status = 'paused' THEN 'paper' ELSE status END,
                deployed_at = COALESCE(deployed_at, NOW()),
                updated_at = NOW()
            WHERE strategy_id = :sid
        """), {"sid": strategy_id, "mode": registry_mode})
        db.commit()
        return {
            "success": True,
            "positions_created": 0,
            "tickers": [],
            "pool_remaining": available,
            "execution_mode": current_mode,
            "note": (
                f"Registry execution_mode is {registry_api_mode}; positions are owned by the "
                "paper ledger (gold.paper_trades_synthetic) and synced into "
                "consumption.portfolio_positions_current by ETL each signal cycle. "
                "No placeholder rows written; registry mode updated so the rebalancer "
                "picks the strategy up."
            ),
        }

    if available < trade_size:
        return {"success": False, "error": "Capital pool exhausted", "available": available, "required": trade_size}

    created = []
    for ticker in tickers:
        if available < trade_size:
            break
        try:
            with db.begin_nested():
                db.execute(text("""
                    INSERT INTO consumption.portfolio_positions_current (strategy_id, ticker, capital, status, execution_mode, created_at, updated_at)
                    VALUES (:strategy_id, :ticker, :capital, 'ACTIVE', :mode, NOW(), NOW())
                    ON CONFLICT (strategy_id, ticker) DO UPDATE SET
                        status = 'ACTIVE', capital = EXCLUDED.capital,
                        execution_mode = EXCLUDED.execution_mode, updated_at = NOW()
                """), {"strategy_id": strategy_id, "ticker": ticker.upper(), "capital": trade_size, "mode": current_mode})
            available -= trade_size
            created.append(ticker)
        except Exception as exc:
            logger.warning(f"deploy-with-pool failed for {strategy_id}/{ticker}: {exc}")

    if not created:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Could not create any positions for {strategy_id}. Check ticker/capital constraints or existing positions.")

    # Persist the mode to the registry so the strategy moves into the Pipeline board
    # column matching its execution mode (Paper / Live) and paper WR/PF columns can be
    # sourced from real monitoring data.
    registry_mode = api_to_registry_mode(current_mode)
    db.execute(text("""
        UPDATE gold.strategy_registry
        SET execution_mode = :mode,
            status = CASE WHEN status = 'paused' THEN 'paper' ELSE status END,
            deployed_at = COALESCE(deployed_at, NOW()),
            updated_at = NOW()
        WHERE strategy_id = :sid
    """), {"sid": strategy_id, "mode": registry_mode})

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

    # For PAPER/SIMULATION registry strategies the paper ledger
    # (gold.paper_trades_synthetic, written by the ETL rebalancer and synced
    # into consumption.portfolio_positions_current) is the source of truth.
    # Do NOT write placeholder capital rows here.
    registry_row = db.execute(text(
        "SELECT execution_mode FROM gold.strategy_registry WHERE strategy_id = :sid"
    ), {"sid": strategy_id}).fetchone()
    if registry_row is not None:
        registry_api_mode = registry_to_api_mode(getattr(registry_row, "execution_mode", None))
        if registry_api_mode in ("PAPER_TRADING", "SIMULATION"):
            return {
                "success": True,
                "strategy_id": strategy_id,
                "added": [],
                "failed": [],
                "total_added": 0,
                "note": (
                    f"Registry execution_mode is {registry_api_mode}; positions are owned by the "
                    "paper ledger (gold.paper_trades_synthetic) and synced into "
                    "consumption.portfolio_positions_current by ETL each signal cycle. "
                    "No placeholder rows written."
                ),
            }

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
def get_strategy_detail(strategy_id: str, db: Session = Depends(get_db)):
    """Comprehensive strategy detail keyed by the gold.strategy_registry string ID.

    Surfaces registry metadata (including assigned_capital / in_market_capital)
    plus the open paper book from gold.paper_trades_synthetic. Legacy integer-ID
    analytics (daily P&L, backtest summary) are only computed for numeric IDs.
    """
    from app.services.strategy_manager import StrategyManager
    strategy_row = db.execute(text("SELECT strategy_id, name, asset_class, universe_tickers, frequency, execution_mode, status, sharpe_oos, max_drawdown_oos, trade_count_oos, win_rate_oos, conviction_score, assigned_capital, in_market_capital, signal_logic, exit_logic, created_at, updated_at FROM gold.strategy_registry WHERE strategy_id = :sid"), {"sid": strategy_id}).fetchone()
    if not strategy_row:
        raise HTTPException(status_code=404, detail=f"Strategy {strategy_id} not found")

    strategy = dict(strategy_row._mapping)

    # Legacy ORM analytics are keyed on integer QuantStrategy.id — only for numeric IDs.
    daily_pnl = backtest = None
    if strategy_id.isdigit():
        sm = StrategyManager()
        daily_pnl = sm.get_strategy_daily_pnl(int(strategy_id))
        backtest = sm.get_strategy_backtest_summary(int(strategy_id))

    # Open paper legs: SIM/PAPER book lives in gold.paper_trades_synthetic.
    # For open rows the ETL stores the latest mark in exit_price (see entry/exit_price_basis).
    leg_rows = db.execute(text("""
        SELECT ticker, direction, n_shares, entry_date, entry_price,
               exit_price AS mark_price, signal_weight, assigned_capital, updated_at
        FROM gold.paper_trades_synthetic
        WHERE strategy_id = :sid AND status = 'open'
        ORDER BY ticker
    """), {"sid": strategy_id}).fetchall()

    open_legs = []
    for leg in leg_rows:
        entry = float(leg.entry_price) if leg.entry_price is not None else None
        mark = float(leg.mark_price) if leg.mark_price is not None else None
        shares = float(leg.n_shares) if leg.n_shares is not None else None
        market_value = round(shares * mark, 2) if shares is not None and mark is not None else None
        unrealized_pnl = round(shares * (mark - entry), 2) if shares is not None and mark is not None and entry is not None else None
        open_legs.append({
            "ticker": leg.ticker,
            "direction": leg.direction,
            "n_shares": shares,
            "entry_date": leg.entry_date.isoformat() if leg.entry_date else None,
            "entry_price": entry,
            "mark_price": mark,
            "market_value": market_value,
            "unrealized_pnl": unrealized_pnl,
            "signal_weight": float(leg.signal_weight) if leg.signal_weight is not None else None,
        })

    trades = db.execute(text("SELECT executed_at, ticker, side, quantity, price, pnl FROM gold.trade_executions WHERE strategy_id = :sid ORDER BY executed_at DESC LIMIT 50"), {"sid": strategy_id}).fetchall()

    status = strategy.get("status") or ""
    return {
        "strategy": {
            "id": strategy.get("strategy_id"), "name": strategy.get("name"),
            "asset_class": strategy.get("asset_class"),
            "execution_mode": strategy.get("execution_mode"),
            "status": status,
            "is_active": status.upper() in ("ACTIVE", "PAPER", "LIVE"),
            "assigned_capital": float(strategy["assigned_capital"]) if strategy.get("assigned_capital") is not None else None,
            "in_market_capital": float(strategy["in_market_capital"]) if strategy.get("in_market_capital") is not None else None,
            "current_pnl": float(strategy["in_market_capital"]) if strategy.get("in_market_capital") is not None else None,
            "total_trades": strategy.get("trade_count_oos"),
            "win_rate": round((strategy.get("win_rate_oos") or 0) * 100, 1),
        },
        "open_legs": open_legs,
        "open_legs_count": len(open_legs),
        "open_legs_source": "gold.paper_trades_synthetic",
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
    if mode not in ["SIMULATION", "PAPER_TRADING", "UAT", "LIVE_TRADING"]:
        raise HTTPException(status_code=400, detail="Invalid mode")

    registry_mode = api_to_registry_mode(mode)
    result = db.execute(text("""
        UPDATE gold.strategy_registry SET execution_mode = :mode, updated_at = NOW()
        WHERE strategy_id = :strategy_id RETURNING strategy_id, name, execution_mode
    """), {"strategy_id": strategy_id, "mode": registry_mode}).fetchone()
    if not result:
        raise HTTPException(status_code=404, detail=f"Strategy {strategy_id} not found")
    db.commit()
    return {"success": True, "strategy_id": result.strategy_id, "strategy_name": result.name, "execution_mode": registry_to_api_mode(result.execution_mode)}


@router.get("/strategies/{strategy_id:path}/mode")
def get_execution_mode(strategy_id: str, db: Session = Depends(get_db)):
    result = db.execute(text("""
        SELECT strategy_id, name, execution_mode FROM gold.strategy_registry WHERE strategy_id = :strategy_id
    """), {"strategy_id": strategy_id}).fetchone()
    if not result:
        raise HTTPException(status_code=404, detail="Strategy not found")
    api_mode = registry_to_api_mode(result.execution_mode)
    return {
        "strategy_id": result.strategy_id, "strategy_name": result.name,
        "execution_mode": api_mode, "venue": "IBKR",
        "available_modes": ["SIMULATION", "PAPER_TRADING", "UAT", "LIVE_TRADING"],
        "risk_level": {"SIMULATION": "ZERO", "PAPER_TRADING": "LOW", "UAT": "LOW", "LIVE_TRADING": "HIGH"}.get(api_mode, "UNKNOWN"),
    }


@router.get("/strategies/{strategy_id:path}/capital")
def get_strategy_capital(strategy_id: str, db: Session = Depends(get_db)):
    result = db.execute(text("""
        SELECT strategy_id, name, assigned_capital, in_market_capital
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
        "capacity_millions": 100,
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

    # Design-driven slot math (kanban t_ee1ab601): slot count and the
    # concentration cap derive from the strategy's declared design
    # (gold.strategy_configs paper_design / max_position_pct), not from a
    # hardcoded 4 slots / 25%-of-pool per trade. Mirrors the precedence in
    # agents/etl/gold/strategy/rebuild_paper_positions.py resolve_cap_with_source.
    cfg_rows = db.execute(text("""
        SELECT config_key, config_value FROM gold.strategy_configs
        WHERE strategy_id = :strategy_id AND config_key IN ('paper_design', 'max_position_pct')
    """), {"strategy_id": strategy_id}).fetchall()
    cfg = {r.config_key: r.config_value for r in cfg_rows}
    design = cfg.get('paper_design')
    design = design if isinstance(design, dict) else {}
    override_cap = cfg.get('max_position_pct')
    if isinstance(override_cap, dict):
        override_cap = override_cap.get('value')
    try:
        override_cap = float(override_cap) if override_cap is not None else None
        if override_cap is not None and not (0 < override_cap <= 1.0):
            override_cap = None
    except (TypeError, ValueError):
        override_cap = None
    design_cap = design.get('design_max_position_pct')
    try:
        design_cap = float(design_cap) if design_cap is not None else None
        if design_cap is not None and not (0 < design_cap <= 1.0):
            design_cap = None
    except (TypeError, ValueError):
        design_cap = None
    if override_cap is not None:
        eff_cap, cap_source = override_cap, 'override'
    elif design_cap is not None:
        eff_cap, cap_source = design_cap, 'design'
    else:
        eff_cap, cap_source = 0.20, 'default'
    slot_count = design.get('slot_count')
    try:
        slot_count = int(slot_count) if slot_count else None
        if slot_count is not None and slot_count < 1:
            slot_count = None
    except (TypeError, ValueError):
        slot_count = None
    if slot_count is None:
        slot_count = max(1, round(1.0 / eff_cap))  # cap-implied slots
    slot_capital = total / slot_count
    available = total - used
    return {
        "strategy_id": strategy.strategy_id, "strategy_name": strategy.name,
        "total_assigned": total, "used": used, "available": available,
        "trade_size": slot_capital, "active_positions": pool_usage.active_positions if pool_usage else 0,
        "max_positions": slot_count, "can_trade": available >= slot_capital,
        "usage_pct": (used / total * 100) if total > 0 else 0,
        "slot_pct": (slot_capital / total) if total > 0 else 0,
        "concentration_cap_pct": eff_cap, "cap_source": cap_source,
        "residual_cash_policy": design.get('residual_cash_policy'),
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

    # Purge paper-trading records for this strategy so the live columns clear after Stop.
    # Rehearsal/synthetic trades (rehearsal = true) are left untouched.
    try:
        db.execute(text("""
            DELETE FROM gold.paper_trades
            WHERE strategy_id = :strategy_id AND rehearsal = false
        """), {"strategy_id": strategy_id})
    except Exception as e:
        logger.error(f"paper trade purge error for {strategy_id}: {e}")

    db.execute(text("""
        UPDATE gold.strategy_registry SET is_active = FALSE, updated_at = NOW() WHERE strategy_id = :strategy_id
    """), {"strategy_id": strategy_id})

    # Flip the ETL paper-monitoring flag off (kanban t_1f3bee9f). The registry
    # trigger only fires on execution_mode/status changes, which this endpoint
    # does not touch — without this, gold.strategy_paper_monitoring.is_active
    # stayed true after Stop and the ETL position sync re-upserted the closed
    # positions on its next run.
    db.execute(text("""
        UPDATE gold.strategy_paper_monitoring
        SET is_active = FALSE, deactivated_at = NOW(), updated_at = NOW()
        WHERE strategy_id = :strategy_id
    """), {"strategy_id": strategy_id})
    db.commit()
    return {"success": True, "strategy_id": strategy_id, "action": action,
            "positions_affected": len(positions), "positions_closed": positions_closed if action == "close" else 0,
            "paper_trades_purged": True}


@router.get("/strategies/{strategy_id:path}/description")
def get_strategy_description(strategy_id: str, db: Session = Depends(get_db)):
    result = db.execute(text("""
        SELECT strategy_id as id, name, description, asset_class, frequency,
               sharpe_oos, max_drawdown_oos, win_rate_oos, universe_tickers,
               execution_mode, status, priority
        FROM gold.strategy_registry WHERE strategy_id = :sid
    """), {"sid": strategy_id}).fetchone()
    if result:
        universe = result.universe_tickers or []
        if isinstance(universe, str):
            universe = universe.split(",") if universe else []
        universe = [t for t in universe if t and t.upper() != 'CASH']
        return {
            "id": result.id, "name": result.name, "description": result.description,
            "asset_class": result.asset_class, "direction": "Long", "time_horizon": result.frequency or "Medium-term",
            "metrics": {
                "sharpe_ratio": float(result.sharpe_oos) if result.sharpe_oos else None,
                "max_drawdown": float(result.max_drawdown_oos) if result.max_drawdown_oos else None,
                "win_rate": float(result.win_rate_oos) if result.win_rate_oos else None,
            },
            "universe_count": len(universe),
            "venue": result.execution_mode or "IBKR",
            "source": "trade_algo_researcher",
            "status": result.status,
            "priority": result.priority,
        }
    raise HTTPException(status_code=404, detail=f"Strategy {strategy_id} not found")


@router.get("/strategies/stats")
def get_strategy_stats(db: Session = Depends(get_db)):
    """Get actual performance stats for all deployed strategies."""
    try:
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
    except Exception as e:
        logger.error(f"get_strategy_stats query error: {e}")
        raise

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


@router.get("/strategies/pipeline-feed")
def get_pipeline_ui_feed(db: Session = Depends(get_db)):
    """Return the full pipeline UI feed from the research view.

    Source of truth for the Strategy Lab table and Golden Strategies "Available"
    tab. Includes rejected/retired strategies and keeps NULL metrics as JSON null
    so the UI can distinguish missing data from zero.

    Live/paper-trading metrics are NOT taken from the view. They are computed
    from `gold.paper_trades_synthetic` — the same canonical ledger used by the
    Strategy Detail evaluation endpoint — and only for strategies whose paper
    monitor is running (`gold.strategy_paper_monitoring.is_active = true`). This
    makes the live columns reflect real paper-trading performance only after a
    user has clicked Deploy, and lets the Stop action purge those records. The
    CASH bucket placeholder is excluded so metrics reflect security trades only.

    Monitoring semantics (kanban t_1f3bee9f): `is_paper_monitoring` means the
    ETL paper monitor is running; `paper_state` distinguishes 'engaged'
    (monitored + open paper positions in consumption.portfolio_positions_current)
    from 'watching' (monitored but flat book) and 'off' (not monitored).
    """
    try:
        rows = safe_query(
            db,
            """
            SELECT id, name, asset, horizon, tier, stage, btwr, btpf, trades,
                   returns, sharpe, dd, livewr, livepf, live_pnl,
                   mode, db_status, frequency, agent_source, updated_at,
                   metric_valid_flag
            FROM gold.v_pipeline_ui_feed
            """,
            {},
            label="route_pipeline_ui_feed",
        )
        strategy_ids = [r.id for r in rows if r.id]

        # ------------------------------------------------------------------
        # Paper-trading monitoring state, two distinct facts (kanban t_1f3bee9f):
        #   monitored_ids — is_active in gold.strategy_paper_monitoring (ETL-owned
        #     flag kept in sync with registry execution_mode by trigger). This is
        #     the authoritative "is the paper monitor running" state.
        #   engaged_counts — open paper positions RIGHT NOW from
        #     consumption.portfolio_positions_current. A monitored strategy with
        #     an all-flat book is "watching", not "idle/off".
        # `is_paper_monitoring` now means monitored (previously it meant engaged).
        # ------------------------------------------------------------------
        monitored_ids = set()
        engaged_counts = {}
        if strategy_ids:
            try:
                monitored_rows = safe_query(
                    db,
                    """
                    SELECT strategy_id
                    FROM gold.strategy_paper_monitoring
                    WHERE strategy_id = ANY(:ids)
                      AND is_active = true
                    """,
                    {"ids": strategy_ids},
                    label="route_paper_monitoring_flag",
                )
                monitored_ids = {r.strategy_id for r in monitored_rows}
            except Exception as e:
                logger.error(f"paper monitoring flag query error: {e}")
            try:
                engaged_rows = safe_query(
                    db,
                    """
                    SELECT strategy_id, COUNT(*) AS open_positions
                    FROM consumption.portfolio_positions_current
                    WHERE strategy_id = ANY(:ids)
                      AND status = 'ACTIVE'
                      AND execution_mode = 'PAPER_TRADING'
                    GROUP BY strategy_id
                    """,
                    {"ids": strategy_ids},
                    label="route_paper_engaged",
                )
                engaged_counts = {r.strategy_id: int(r.open_positions or 0) for r in engaged_rows}
            except Exception as e:
                logger.error(f"paper engaged state query error: {e}")

        # ------------------------------------------------------------------
        # Live paper metrics from real paper trades.
        # For PAPER/SIMULATION strategies the canonical ledger is
        # gold.paper_trades_synthetic (the same source used by the Strategy Detail
        # evaluation endpoint), not gold.paper_trades. We exclude the CASH bucket
        # placeholder so metrics reflect security trades only.
        # Only computed for actively monitored strategies; null otherwise.
        # ------------------------------------------------------------------
        paper_metrics = {}
        if monitored_ids:
            try:
                paper_rows = safe_query(
                    db,
                    """
                    SELECT strategy_id,
                           COUNT(*) FILTER (WHERE status = 'closed') AS closed_trades,
                           COUNT(*) FILTER (WHERE status = 'closed' AND pnl > 0) AS winning_trades,
                           SUM(pnl) FILTER (WHERE status = 'closed') AS total_pnl,
                           SUM(pnl) FILTER (WHERE status = 'closed' AND pnl > 0) AS gross_profit,
                           SUM(pnl) FILTER (WHERE status = 'closed' AND pnl < 0) AS gross_loss
                    FROM gold.paper_trades_synthetic
                    WHERE strategy_id = ANY(:ids)
                      AND (ticker IS NULL OR ticker != 'CASH')
                    GROUP BY strategy_id
                    """,
                    {"ids": list(monitored_ids)},
                    label="route_paper_metrics",
                )
                for r in paper_rows:
                    closed = int(r.closed_trades or 0)
                    wins = int(r.winning_trades or 0)
                    pnl = _coerce_number(r.total_pnl)
                    gross_profit = _coerce_number(r.gross_profit) or 0
                    gross_loss = _coerce_number(r.gross_loss) or 0
                    paper_metrics[r.strategy_id] = {
                        "paper_wr": (wins / closed * 100) if closed > 0 else None,
                        "paper_pf": (gross_profit / abs(gross_loss)) if gross_loss and gross_loss != 0 else None,
                        "paper_pnl_realized": pnl,
                        "paper_trades": closed,
                    }
            except Exception as e:
                logger.error(f"paper metrics query error: {e}")

            # ----------------------------------------------------------
            # Unrealized P&L for OPEN paper positions (mark-to-market).
            # consumption.portfolio_positions_current paper rows ARE marked to
            # market by the ETL (sync_paper_positions_current.py, t_646c098a:
            # latest gold.daily_ohlcv close, fallback entry_price), so read
            # unrealized_pnl directly — no serve-time recomputation.
            # ----------------------------------------------------------
            try:
                open_rows = safe_query(
                    db,
                    """
                    SELECT p.strategy_id, p.unrealized_pnl
                    FROM consumption.portfolio_positions_current p
                    WHERE p.strategy_id = ANY(:ids)
                      AND p.status = 'ACTIVE'
                      AND p.quantity > 0
                      AND p.execution_mode = 'PAPER_TRADING'
                      AND (p.ticker IS NULL OR p.ticker != 'CASH')
                    """,
                    {"ids": list(monitored_ids)},
                    label="route_paper_unrealized",
                )
                for r in open_rows:
                    m = paper_metrics.setdefault(r.strategy_id, {
                        "paper_wr": None, "paper_pf": None,
                        "paper_pnl_realized": None, "paper_trades": 0,
                    })
                    unr = _coerce_number(r.unrealized_pnl)
                    if unr is not None:
                        m["paper_pnl_unrealized"] = (m.get("paper_pnl_unrealized") or 0) + unr
                    else:
                        m["paper_unpriced"] = (m.get("paper_unpriced") or 0) + 1
            except Exception as e:
                logger.error(f"paper unrealized query error: {e}")

            # Total = realized + unrealized. A monitored strategy with an open
            # book but no closed trades yet shows its mark-to-market P&L
            # instead of NULL; a flat monitored book shows an honest $0.
            for m in paper_metrics.values():
                m["paper_pnl"] = (m.get("paper_pnl_realized") or 0) + (m.get("paper_pnl_unrealized") or 0)

        # ------------------------------------------------------------------
        # Paper-book skip counts (kanban t_6c1ab779):
        # consumption.strategy_paper_skips_current holds one row per
        # (strategy_id, ticker) BUY signal the paper rebalancer could not fill
        # (below one lot / unsupported asset class / no price). Expose the
        # count per strategy so the list view can badge strategies with
        # unfilled BUY signals. Empty table = no skips = count 0.
        # ------------------------------------------------------------------
        skip_counts = {}
        if strategy_ids:
            try:
                skip_rows = safe_query(
                    db,
                    """
                    SELECT strategy_id, COUNT(*) AS skips
                    FROM consumption.strategy_paper_skips_current
                    WHERE strategy_id = ANY(:ids)
                    GROUP BY strategy_id
                    """,
                    {"ids": strategy_ids},
                    label="route_paper_skip_counts",
                )
                skip_counts = {r.strategy_id: int(r.skips or 0) for r in skip_rows}
            except Exception as e:
                logger.error(f"paper skip counts query error: {e}")

        data = []
        for r in rows:
            sid = r.id
            is_monitoring = sid in monitored_ids
            open_positions = engaged_counts.get(sid, 0)
            is_engaged = open_positions > 0
            # 'engaged' = monitored with open paper positions right now;
            # 'watching' = monitored but flat book (e.g. all-SELL scores or a
            # mostly-cash design); 'off' = paper monitor not running.
            paper_state = 'engaged' if is_engaged else ('watching' if is_monitoring else 'off')
            paper = paper_metrics.get(sid, {}) if is_monitoring else {}
            # The view's live* fields come from synthetic paper trades; we deliberately
            # overwrite them with real paper-trading metrics only when monitoring is active.
            btwr = _coerce_number(r.btwr)
            data.append({
                "id": sid,
                "name": r.name,
                "asset": r.asset,
                "horizon": r.horizon,
                "tier": r.tier,
                "stage": r.stage,
                # Simulation metrics: left-hand columns (backtest / current-year simulation).
                # The view currently returns the latest OOS backtest win rate; the true
                # current-year simulation WR is pending a `gold.v_pipeline_ui_feed` update
                # by qr_etl (see kanban task). We expose both `btwr` (legacy) and `sim_wr`
                # so the UI can label the column as "Sim WR".
                "btwr": btwr,
                "sim_wr": btwr,
                "btpf": _coerce_number(r.btpf),
                "trades": int(r.trades) if r.trades is not None else None,
                "returns": _coerce_number(r.returns),
                "sharpe": _coerce_number(r.sharpe),
                "dd": _coerce_number(r.dd),
                # Live / paper-trading metrics: only populated after Deploy, from real paper trades.
                # is_paper_monitoring = paper monitor running (gold.strategy_paper_monitoring).
                # paper_engaged / paper_open_positions = open positions right now.
                "is_paper_monitoring": is_monitoring,
                "paper_engaged": is_engaged,
                "paper_open_positions": open_positions,
                "paper_state": paper_state,
                "paper_skip_count": skip_counts.get(sid, 0),
                "paper_wr": paper.get("paper_wr"),
                "paper_pf": paper.get("paper_pf"),
                "paper_pnl": paper.get("paper_pnl"),
                "paper_pnl_realized": paper.get("paper_pnl_realized"),
                "paper_pnl_unrealized": paper.get("paper_pnl_unrealized"),
                "paper_unpriced": paper.get("paper_unpriced", 0),
                "paper_trades": paper.get("paper_trades"),
                # Legacy fields kept for consumers that haven't migrated yet.
                "livewr": paper.get("paper_wr"),
                "livepf": paper.get("paper_pf"),
                "live_pnl": paper.get("paper_pnl"),
                "mode": registry_to_api_mode(r.mode),
                "db_status": r.db_status,
                "frequency": r.frequency,
                "agent_source": r.agent_source,
                "updated_at": r.updated_at.isoformat() if r.updated_at else None,
                "metric_valid_flag": r.metric_valid_flag,
            })
        return {
            "data": data,
            "count": len(data),
            "as_of": datetime.now(timezone.utc).isoformat(),
        }
    except Exception as e:
        logger.error(f"pipeline-feed query error: {e}")
        return {
            "data": [],
            "count": 0,
            "as_of": datetime.now(timezone.utc).isoformat(),
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
        SELECT strategy_id, name, execution_mode FROM gold.strategy_registry WHERE strategy_id = :strategy_id
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
