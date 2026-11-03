"""
JTCML Trading Platform - FastAPI Backend
=========================================
Platform layer: API endpoints + IBKR execution.
Data ingestion/refresh is handled by the DE agent.
"""
import datetime
import json
import math
import os
import time
from fastapi import FastAPI, Request, BackgroundTasks, Depends, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import text
from sqlalchemy.exc import ProgrammingError, OperationalError
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import logging

# Route modules
from app.routes import market, stocks, fx, crypto, strategies, positions, research
from app.routes import performance, execution, ibkr, alerts, metadata, hkex, backtest, agents
from app.routes import command, markets_v2, macro, signals, settings as settings_routes
from app.routes import watchlist
from app.routes import derivatives

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Internal Imports
from app.db.session import (
    SessionLocal, Base, engine, Inventory, GlobalState,
    ConsumptionStock, ConsumptionMarket, ConsumptionFx, ConsumptionCommodity, ConsumptionCrypto, Trade, QuantStrategy, StrategyRegistry, AgentActivity
)
from app.db.safe_query import safe_query, safe_query_one
from app.dependencies import api_to_registry_mode, registry_to_api_mode
from app.core_logic.data.wholistic_pipeline import (
    refresh_indices_and_mood, refresh_fx_layer, refresh_commodity_layer, refresh_crypto_layer, refresh_stock_layer, refresh_hft_layer
)
# Optional imports - may not exist in all versions
try:
    from app.core_logic.data.wholistic_pipeline import refresh_etf_layer, refresh_accruals_quality
except ImportError:
    refresh_etf_layer = None
    refresh_accruals_quality = None
from app.core_logic.agents.research_swarm import research_swarm
try:
    from app.api.stock_detail import router as stock_detail_router
    HAS_STOCK_DETAIL_API = True
except ImportError:
    HAS_STOCK_DETAIL_API = False
    stock_detail_router = None
from app.services.ib_service import ib_quant_service
from app.services.ib_web_service import ib_web_service
from app.services.bookkeeping import non_strategy_leg_exists, fetch_closure_legs

# CLEANSE-1 (kanban t_070590de): skip-log labeled non-strategy closure legs
# (RESET_STALE_SIGNAL flattened / CLEANSE1_CLOSURE) are operator bookkeeping,
# never strategy performance — excluded from every realized-P&L aggregate over
# the synthetic paper ledger in this module. Queries here use the unaliased
# table, so the predicate targets gold.paper_trades_synthetic directly.
_NS_EXCL_SYNTH = "AND NOT " + non_strategy_leg_exists("gold.paper_trades_synthetic")
from app.services.strategy_manager import strategy_manager
from app.services.jt_strategy_executor import get_executor
from app.services.event_bus import event_bus
from app.auth import (
    AUTH_ENABLED, JTCML_USER, JTCML_PASSWORD,
    create_token, verify_token, is_public_path, TOKEN_TTL,
)

# JT Strategy Executor - initialized lazily
jt_strategy_executor = None

def _sanitize_nan(obj):
    """Recursively replace float NaN/Inf with None."""
    if isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            return None
        return obj
    if isinstance(obj, dict):
        return {k: _sanitize_nan(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_sanitize_nan(v) for v in obj]
    return obj

class NaNSafeJSONResponse(JSONResponse):
    def render(self, content) -> bytes:
        safe_content = _sanitize_nan(content)
        return json.dumps(safe_content, ensure_ascii=False, allow_nan=False, cls=CustomJSONEncoder).encode("utf-8")

class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, float):
            if math.isnan(obj) or math.isinf(obj):
                return None
        if isinstance(obj, datetime.datetime):
            return obj.isoformat()
        if isinstance(obj, datetime.date):
            return obj.isoformat()
        return super().default(obj)

app = FastAPI(default_response_class=NaNSafeJSONResponse)

# Include all routers
app.include_router(market.router)
app.include_router(stocks.router)
app.include_router(fx.router)
app.include_router(crypto.router)
app.include_router(strategies.router)
app.include_router(positions.router)
app.include_router(performance.router)
app.include_router(execution.router)
app.include_router(ibkr.router)
app.include_router(alerts.router)
app.include_router(metadata.router)
app.include_router(hkex.router)
app.include_router(backtest.router)
app.include_router(agents.router)
app.include_router(command.router)
app.include_router(markets_v2.router)
app.include_router(macro.router)
app.include_router(watchlist.router)
app.include_router(derivatives.router)
app.include_router(signals.router)
# Include research router
app.include_router(research.router)
app.include_router(settings_routes.router)

# Include stock detail router (conditional)
if HAS_STOCK_DETAIL_API and stock_detail_router:
    app.include_router(stock_detail_router)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://trade.jtcml.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

import asyncio

# ---------------------------------------------------------------------------
# Global Exception Handlers — fault tolerance for missing tables / DB errors
# ---------------------------------------------------------------------------

@app.exception_handler(ProgrammingError)
async def sqlalchemy_programming_error_handler(request: Request, exc: ProgrammingError):
    """Handle missing tables/columns — return endpoint-appropriate empty shape instead of 500."""
    error_msg = str(exc.orig) if exc.orig else str(exc)
    path = request.url.path
    logger.warning(f"DB schema error on {path}: {error_msg}")

    # Return shapes that match what the frontend expects for each endpoint
    # so the UI renders gracefully instead of crashing or showing wrong empty states.
    if path == "/api/paper-strategies":
        return JSONResponse(status_code=200, content={
            "strategies": [], "count": 0,
            "execution_mode": "SIMULATION",
            "message": "No paper strategies available yet."
        })
    if path == "/api/portfolio/positions":
        return JSONResponse(status_code=200, content={
            "positions": [], "total_positions": 0,
            "total_value": 0, "total_pnl": 0,
            "message": "No positions recorded yet."
        })
    if path == "/api/performance/strategy":
        return JSONResponse(status_code=200, content={
            "strategies": [], "monthly_returns": [],
            "summary": {"total_return": 0, "sharpe": 0, "max_drawdown": 0, "win_rate": 0},
            "message": "Performance data not yet available."
        })
    if path == "/api/strategies/researcher":
        return JSONResponse(status_code=200, content={
            "strategies": [], "count": 0,
            "message": "Researcher strategies not yet available."
        })

    # Generic fallback for any other endpoint
    return JSONResponse(status_code=200, content={
        "data": [], "count": 0,
        "error": "data_not_available",
        "message": "Data source not yet available. The DE pipeline may not have created this view yet.",
    })

@app.exception_handler(OperationalError)
async def sqlalchemy_operational_error_handler(request: Request, exc: OperationalError):
    """Handle DB connection errors — return 503 instead of 500."""
    logger.error(f"DB connection error on {request.url.path}: {exc.orig}")
    return JSONResponse(status_code=503, content={
        "error": "database_unavailable",
        "message": "Database temporarily unavailable. Please retry.",
    })

@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    """Catch-all — no unhandled exception ever returns a raw 500 traceback."""
    logger.error(f"Unhandled error on {request.url.path}: {type(exc).__name__}: {exc}")
    return JSONResponse(status_code=500, content={
        "error": "internal_error",
        "message": f"An unexpected error occurred: {type(exc).__name__}",
    })

# REMOVED: scheduler_loop() - Platform is READ-ONLY
# Data refresh schedules are managed by DE agent, not Platform
# See shared/references/inter-agent-protocol.md for data contract workflow

# ---------------------------------------------------------------------------
# WebSocket — real-time event stream
# ---------------------------------------------------------------------------
@app.websocket("/ws/events")
async def websocket_events(ws: WebSocket):
    await ws.accept()
    logger.info(f"WS client connected ({event_bus.subscriber_count + 1} total)")
    try:
        async for event in event_bus.subscribe():
            await ws.send_json(event)
    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.debug(f"WS client error: {e}")
    finally:
        logger.info(f"WS client disconnected ({event_bus.subscriber_count} remaining)")

# ---------------------------------------------------------------------------
# Auth — opt-in via JTCML_AUTH=1 env var
# ---------------------------------------------------------------------------
@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    """Verify bearer token on API routes when auth is enabled."""
    if AUTH_ENABLED and not is_public_path(request.url.path):
        auth = request.headers.get("Authorization", "")
        if not auth.startswith("Bearer ") or not verify_token(auth[7:]):
            return JSONResponse(status_code=401, content={"error": "unauthorized", "message": "Valid token required"})
    return await call_next(request)


@app.post("/api/auth/login")
def auth_login(payload: dict):
    username = (payload or {}).get("username", "")
    password = (payload or {}).get("password", "")
    if username != JTCML_USER or password != JTCML_PASSWORD:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_token(sub=username)
    return {"token": token, "token_type": "bearer", "expires_in": TOKEN_TTL}


@app.post("/api/auth/refresh")
def auth_refresh(request: Request):
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="No token")
    old = verify_token(auth[7:])
    if not old:
        raise HTTPException(status_code=401, detail="Token expired or invalid — re-login required")
    token = create_token(sub=old["sub"])
    return {"token": token, "token_type": "bearer", "expires_in": TOKEN_TTL}


@app.get("/api/auth/me")
def auth_me(request: Request):
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        return {"authenticated": False, "auth_enabled": AUTH_ENABLED}
    payload = verify_token(auth[7:])
    if not payload:
        return {"authenticated": False, "auth_enabled": AUTH_ENABLED}
    return {"authenticated": True, "auth_enabled": AUTH_ENABLED, "user": payload.get("sub")}


@app.middleware("http")
async def ibkr_session_middleware(request: Request, call_next):
    """
    Iteration 49: Automatically sync IBKR cookies from every incoming request.
    This ensures the backend always has the latest browser session.
    """
    cookies = request.cookies
    # Filter for IBKR-related cookies if possible, or just sync all
    if any(k in cookies for k in ['JSESSIONID', 'x-sess-uuid', 'IB_SESSION']):
        ib_web_service.set_cookies(cookies)

    response = await call_next(request)
    return response

@app.on_event("startup")
async def startup_event():
    # DISABLED: Scheduler initialization - Platform is READ-ONLY
    # Data schedules are managed by DE agent
    print("✅ Backend started - READ-ONLY mode (consumption views only)")

    # Auto-demote risk scanner — runs every JTCML_DEMOTE_SCAN_S seconds (default 300)
    # Disable with JTCML_DEMOTE_SCAN_S=0
    if DEMOTE_SCAN_INTERVAL_S > 0:
        asyncio.create_task(_demote_scanner_loop())
        print(f"✅ Auto-demote scanner started (interval: {DEMOTE_SCAN_INTERVAL_S}s)")

@app.on_event("shutdown")
async def shutdown_event():
    # Cleanly stop the IBKR worker thread so the TWS session disconnects
    # instead of lingering at the gateway until it times out. Guards against
    # instantiating the singleton when IB was never used in this process.
    try:
        from app.services import ib_service as _ibs
        if _ibs._ib_threaded_service_instance is not None:
            _ibs._ib_threaded_service_instance.stop()
            print("✅ IBKR service stopped cleanly on shutdown")
    except Exception as e:
        print(f"⚠️ IBKR shutdown stop failed: {e}")

async def run_deep_sell_analysis(db: Session):
    """
    Performs institutional-grade sell analysis for all inventory items.
    """
    # 1. Fetch Market Context (Regime and macro proxies)
    risk_row = db.query(GlobalState).filter(GlobalState.key == "system_risk_level").first()
    mood_row = db.query(GlobalState).filter(GlobalState.key == "market_mood_index").first()

    market_data = {
        "regime": "PANIC" if risk_row and risk_row.value == "CRITICAL" else "GROWTH",
        "mood": mood_row.value if mood_row else "Neutral"
    }

    items = db.query(Inventory).all()
    for item in items:
        try:
            # Prepare data for swarm
            inv_data = {
                "ticker": item.ticker,
                "purchase_price": item.buy_price,
                "quantity": item.quantity,
                "current_price": item.current_price
            }
            # Execute Swarm Debate (async) - only if research_swarm is available
            if research_swarm:
                try:
                    analysis_raw = await research_swarm.debate_sell_signal(inv_data, market_data)

                    # The swarm returns a dict with "analysis" as a content string
                    # We try to parse the content string if it's JSON
                    try:
                        cleaned_content = analysis_raw['analysis'].replace('```json', '').replace('```', '').strip()
                        item.analysis = json.loads(cleaned_content)
                    except:
                        item.analysis = {"decision": "HOLD", "reasoning": analysis_raw['analysis']}
                except Exception as e:
                    print(f"Sell analysis error for {item.ticker}: {e}")
                    item.analysis = {"decision": "HOLD", "reasoning": f"Analysis unavailable: {e}"}
            else:
                item.analysis = {"decision": "HOLD", "reasoning": "Research swarm not configured"}

            db.commit()
        except Exception as e:
            print(f"Sell analysis error for {item.ticker}: {e}")
            db.rollback()

def get_db():
    db = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

# ---------------------------------------------------------------------------
# System Health — workspace-ribbon summary (DB latency, status, asset counts)
# Used by the frontend top ribbon and Command Center
# ---------------------------------------------------------------------------
@app.get("/api/audit/events")
def get_audit_events(limit: int = 100, event_type: str = None, strategy_id: str = None, db: Session = Depends(get_db)):
    """Query the audit trail. Returns newest-first."""
    sql = "SELECT id, event_type, strategy_id, actor, payload, created_at FROM gold.audit_events WHERE 1=1"
    params = {}
    if event_type:
        sql += " AND event_type = :et"
        params["et"] = event_type
    if strategy_id:
        sql += " AND strategy_id = :sid"
        params["sid"] = strategy_id
    sql += " ORDER BY created_at DESC LIMIT :lim"
    params["lim"] = min(limit, 500)

    rows = safe_query(db, sql, params, label="audit_events")
    events = []
    for r in rows:
        payload = r.payload
        if isinstance(payload, str):
            try:
                payload = json.loads(payload)
            except Exception:
                pass
        events.append({
            "id": r.id,
            "event_type": r.event_type,
            "strategy_id": r.strategy_id,
            "actor": r.actor,
            "payload": payload,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        })
    return {"events": events, "count": len(events)}


@app.get("/api/operations/live")
def get_live_operations(db: Session = Depends(get_db)):
    """Live ops snapshot for the Command Center: active orders, today's fills,
    active signals. Single round-trip; safe_query everywhere."""

    # 1. Active / working orders (non-terminal status in trade_executions)
    active_orders = safe_query(db, """
        SELECT id, strategy_id, ticker, side, quantity, price, status, order_type,
               execution_mode, executed_at, ibkr_order_id
        FROM gold.trade_executions
        WHERE status IN ('PENDING', 'WORKING', 'SUBMITTED', 'PARTIAL')
        ORDER BY executed_at DESC
        LIMIT 50
    """, label="ops_active_orders")

    # 2. Today's fills (UTC day; FE renders local time)
    todays_fills = safe_query(db, """
        SELECT id, strategy_id, ticker, side, quantity, price, pnl, execution_mode, executed_at
        FROM gold.trade_executions
        WHERE status NOT IN ('PENDING', 'WORKING', 'SUBMITTED', 'PARTIAL')
          AND executed_at >= CURRENT_DATE
        ORDER BY executed_at DESC
        LIMIT 100
    """, label="ops_todays_fills")

    # 3. Active signals (BUY/SELL only)
    signals = safe_query(db, """
        SELECT strategy_id, ticker, signal, signal_strength, confidence_score,
               current_price, generated_at
        FROM consumption.Strategies_Signals_Current
        WHERE signal IN ('BUY', 'SELL')
        ORDER BY confidence_score DESC NULLS LAST
        LIMIT 30
    """, label="ops_signals")

    # 4. Aggregate today's P&L from fills
    today_pnl = sum(float(f.pnl or 0) for f in todays_fills if getattr(f, "pnl", None) is not None)
    today_winners = sum(1 for f in todays_fills if (f.pnl or 0) > 0)
    today_losers  = sum(1 for f in todays_fills if (f.pnl or 0) < 0)

    return {
        "active_orders": [{
            "id": r.id, "strategy_id": r.strategy_id, "ticker": r.ticker,
            "side": r.side, "quantity": float(r.quantity) if r.quantity is not None else None,
            "price": float(r.price) if r.price is not None else None,
            "status": r.status, "order_type": r.order_type,
            "execution_mode": r.execution_mode, "ibkr_order_id": r.ibkr_order_id,
            "submitted_at": r.executed_at.isoformat() if r.executed_at else None,
        } for r in active_orders],
        "todays_fills": [{
            "id": r.id, "strategy_id": r.strategy_id, "ticker": r.ticker,
            "side": r.side, "quantity": float(r.quantity) if r.quantity is not None else None,
            "price": float(r.price) if r.price is not None else None,
            "pnl": float(r.pnl) if r.pnl is not None else None,
            "execution_mode": r.execution_mode,
            "filled_at": r.executed_at.isoformat() if r.executed_at else None,
        } for r in todays_fills],
        "signals": [{
            "strategy_id": s.strategy_id, "ticker": s.ticker, "signal": s.signal,
            "strength": float(s.signal_strength) if s.signal_strength is not None else None,
            "confidence": float(s.confidence_score) if s.confidence_score is not None else None,
            "price": float(s.current_price) if s.current_price is not None else None,
            "ts": s.generated_at.isoformat() if getattr(s, "generated_at", None) else None,
        } for s in signals],
        "summary": {
            "active_order_count": len(active_orders),
            "todays_fill_count": len(todays_fills),
            "active_signal_count": len(signals),
            "today_pnl": round(today_pnl, 2),
            "today_winners": today_winners,
            "today_losers": today_losers,
        },
    }


@app.get("/api/system/health")
def system_health():
    """Return a small, fast health/status summary for the workspace ribbon.

    Latency-sensitive: uses a 2-second hard timeout on the DB ping so
    the frontend never freezes when RDS is unreachable.
    """
    started = time.perf_counter()
    db_status = "unreachable"
    counts = {}
    pipeline = {}

    # Hard 2-second timeout on DB ping
    try:
        with engine.connect().execution_options(timeout=2) as conn:
            conn.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception as e:
        logger.error(f"DB ping failed: {e}")

    # Only query data if DB is reachable
    if db_status == "connected":
        db = None
        try:
            db = SessionLocal()
            # Lightweight counts
            rows = safe_query(db, """
                SELECT
                    (SELECT COUNT(*) FROM gold.strategy_registry ) AS strategies,
                    (SELECT COUNT(*) FROM consumption.portfolio_positions_current WHERE status = 'ACTIVE') AS deployed,
                    (SELECT COUNT(*) FROM gold.asset_registry WHERE is_active = TRUE) AS assets
            """, label="health_counts")
            if rows:
                r = rows[0]
                counts = {
                    "strategies": int(r.strategies or 0),
                    "deployed":   int(r.deployed or 0),
                    "assets":     int(r.assets or 0),
                }
            # Pipeline summary
            rs = safe_query(db, "SELECT status, COUNT(*) c FROM gold.strategy_registry GROUP BY status", label="health_pipeline")
            pipeline = {row.status.lower(): int(row.c) for row in rs} if rs else {}
        except Exception:
            db_status = "degraded"
        finally:
            if db is not None:
                db.close()

    latency_ms = int((time.perf_counter() - started) * 1000)

    return {
        "status": "ok" if db_status == "connected" else "degraded",
        "db": db_status,
        "backend": "ok",
        "latency_ms": latency_ms,
        "ts": datetime.datetime.utcnow().isoformat() + "Z",
        "counts": counts,
        "pipeline": pipeline,
        "version": "v1",
    }


# bar_quality aggregate cache (t_7213b685): gold.v_us_equity_bar_quality is a
# MATERIALIZED VIEW refreshed twice daily (qr_etl.bar_quality_mv_refresh), and
# this endpoint is polled every few seconds by the frontend — caching the
# aggregate removes per-poll DB work entirely. Pre-matview, each uncached call
# was a 100s+ parallel seq scan of gold.daily_ohlcv (incident t_96e90169).
_BAR_QUALITY_TTL_S = float(os.getenv("BAR_QUALITY_CACHE_TTL_S", "120"))
_bar_quality_cache: dict = {"expires": 0.0, "data": None}


def _bar_quality_aggregate(db: Session):
    now = time.monotonic()
    if now < _bar_quality_cache["expires"]:
        return _bar_quality_cache["data"]

    bq_rows = safe_query(db, """
        SELECT
            MAX(date)            AS latest_suspect_date,
            COUNT(*)             AS total_rows,
            COUNT(*) FILTER (WHERE date >= CURRENT_DATE - 30) AS recent_30d_rows,
            COUNT(DISTINCT offending_ticker) AS distinct_tickers,
            ARRAY_AGG(DISTINCT offending_ticker)
                FILTER (WHERE date >= CURRENT_DATE - 30) AS recent_30d_tickers,
            COUNT(*) FILTER (WHERE date >= CURRENT_DATE - 30
                             AND layer = 'gold.daily_ohlcv') AS recent_30d_gold_rows,
            COUNT(*) FILTER (WHERE date >= CURRENT_DATE - 30
                             AND layer = 'bronze.yf_suspect_bars') AS recent_30d_quarantined_rows
        FROM gold.v_us_equity_bar_quality
    """, label="system_bar_quality")
    bar_quality = None
    if bq_rows:
        b = bq_rows[0]
        recent = int(b.recent_30d_rows or 0)
        bar_quality = {
            # YELLOW when unresolved suspects exist in the last 30d — a
            # warning signal, not a hard failure (self-heal is possible).
            "quality": "YELLOW" if recent > 0 else "GREEN",
            "latest_suspect_date": b.latest_suspect_date.isoformat() if b.latest_suspect_date else None,
            "total_rows": int(b.total_rows or 0),
            "recent_30d_rows": recent,
            "distinct_tickers": int(b.distinct_tickers or 0),
            "recent_30d_tickers": sorted(b.recent_30d_tickers) if b.recent_30d_tickers else [],
            "recent_30d_gold_rows": int(b.recent_30d_gold_rows or 0),
            "recent_30d_quarantined_rows": int(b.recent_30d_quarantined_rows or 0),
        }

    # Cache failures (None) for a short time too — a flapping DB must not be
    # re-hit on every poll — but only for 15s so recovery shows quickly.
    _bar_quality_cache["data"] = bar_quality
    _bar_quality_cache["expires"] = now + (_BAR_QUALITY_TTL_S if bar_quality else 15.0)
    return bar_quality


@app.get("/api/system/freshness")
def system_freshness(db: Session = Depends(get_db)):
    """Per-source data freshness registry (gold.v_source_freshness, qr_etl-owned).

    P0-1 Command-page contract: each row carries the source name, its
    configured staleness budget (expected_max_staleness_hours — per-source,
    config-driven, not hardcoded in the UI), the last refresh timestamp, and
    the precomputed staleness in hours. The frontend classifies
    FRESH/LAGGING/STALE/DISCONNECTED from these fields and propagates state to
    panels via its source→panel dependency map.

    Degrades to {"sources": None} when the registry view is missing so the
    client treats every source as UNKNOWN rather than FRESH.

    bar_quality section (gold.v_us_equity_bar_quality, qr_etl-owned, shipped
    2026-08-24): authoritative list of Yahoo synthetic zero-volume flat bars
    across gold.daily_ohlcv (pre-guard contamination) and bronze.yf_suspect_bars
    (post-guard quarantined). Recent unresolved suspects are a YELLOW-quality
    signal, NOT a hard failure — episodes can self-heal (EA 2026-08-05..10
    resolved on its own). Degrades to bar_quality=None when the view is
    missing so the client treats bar quality as UNKNOWN.
    """
    rows = safe_query(db, """
        SELECT source, asset_class, expected_frequency,
               expected_max_staleness_hours, last_refreshed_at, last_checked_at,
               last_error, notes, staleness_hours, freshness_status
        FROM gold.v_source_freshness
        ORDER BY source
    """, label="system_freshness")
    # safe_query falls back to [] on missing view — an empty registry is as
    # uninformative as a missing one, so degrade to sources=None (UNKNOWN).
    sources = None
    if rows:
        sources = [{
            "source": r.source,
            "asset_class": r.asset_class,
            "expected_frequency": r.expected_frequency,
            "max_staleness_h": int(r.expected_max_staleness_hours) if r.expected_max_staleness_hours is not None else None,
            "last_refreshed_at": r.last_refreshed_at.isoformat() if r.last_refreshed_at else None,
            "last_checked_at": r.last_checked_at.isoformat() if r.last_checked_at else None,
            "staleness_h": round(float(r.staleness_hours), 2) if r.staleness_hours is not None else None,
            "registry_status": r.freshness_status,
            "last_error": r.last_error,
        } for r in rows]

    bar_quality = _bar_quality_aggregate(db)

    return {
        "sources": sources,
        "bar_quality": bar_quality,
        "as_of": datetime.datetime.utcnow().isoformat() + "Z",
    }


# --- POSITION & EXECUTION TRACKING ---

@app.get("/api/positions")
def get_open_positions(db: Session = Depends(get_db)):
    """Get all open positions (inventory) with current P&L"""
    # Use safe_query to handle missing tables gracefully
    positions = safe_query(db, """
        SELECT 
            id,
            ticker,
            side,
            strategy_id,
            quantity,
            entry_price as buy_price,
            current_price,
            unrealized_pnl,
            market_value,
            entry_date as purchase_date,
            (CURRENT_DATE - entry_date) as days_held
        FROM consumption.portfolio_positions_current
        WHERE status = 'ACTIVE' AND quantity > 0
        ORDER BY market_value DESC
    """, label="open_positions")

    result = []
    for p in positions:
        current_price = float(p.current_price or p.buy_price or 0)
        quantity = float(p.quantity or 0)
        buy_price = float(p.buy_price or 0)
        unrealized_pnl = float(p.unrealized_pnl or 0)
        pnl_pct = ((current_price / buy_price) - 1) * 100 if buy_price > 0 else 0

        result.append({
            "id": p.id,
            "ticker": p.ticker,
            "asset_class": None,  # no asset_class column on portfolio_positions_current
            "side": p.side,
            "strategy_id": p.strategy_id,
            "quantity": quantity,
            "buy_price": buy_price,
            "current_price": current_price,
            "unrealized_pnl": round(unrealized_pnl, 2),
            "unrealized_pnl_pct": round(pnl_pct, 2),
            "purchase_date": p.purchase_date.isoformat() if p.purchase_date else None,
            "days_held": p.days_held,
            "estimates": {"1d": "---", "7d": "---", "1m": "---"},
            "analysis": {},
            "status": "held"
        })

    return {
        "positions": result,
        "summary": {
            "total_positions": len(result),
            "total_unrealized_pnl": round(sum(p["unrealized_pnl"] for p in result), 2),
            "by_asset_class": {}
        }
    }


@app.get("/api/execution/status")
def get_execution_status():
    """Get IBKR execution connectivity status"""
    from app.services.ib_service import ib_quant_service
    from app.services.ib_web_service import ib_web_service

    return {
        "tws_api": {
            "connected": ib_quant_service.is_connected,
            "host": ib_quant_service.host,
            "port": ib_quant_service.port
        },
        "web_api": {
            "authenticated": ib_web_service.check_auth()
        },
        "ready_for_live": ib_quant_service.is_connected or ib_web_service.check_auth()
    }


# --- BACKTESTING APIS ---
# NOTE: Backtest endpoints moved to app.routes.backtest
#       POST /api/backtest/request
#       GET  /api/backtest/{request_id}/status
#       GET  /api/backtest/strategy/{strategy_id}/history
#       GET  /api/backtest/strategy/{strategy_id}/vs-live
#       POST /api/strategies/{strategy_id}/backtest


# --- PORTFOLIO RISK DASHBOARD APIS ---

@app.get("/api/portfolio/risk-summary")
def get_portfolio_risk_summary(db: Session = Depends(get_db)):
    """Get overall portfolio risk summary"""
    try:
        from app.services.portfolio_risk import portfolio_risk_manager
        return portfolio_risk_manager.get_portfolio_summary()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/portfolio/correlations")
def get_portfolio_correlations(db: Session = Depends(get_db)):
    """Get correlation matrix between strategies"""
    try:
        from app.services.portfolio_risk import portfolio_risk_manager
        return portfolio_risk_manager.get_correlation_matrix()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/portfolio/var")
def get_portfolio_var(confidence: float = 0.95, db: Session = Depends(get_db)):
    """Get Value at Risk (VaR) analysis"""
    try:
        from app.services.portfolio_risk import portfolio_risk_manager
        return portfolio_risk_manager.get_var_analysis(confidence)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/portfolio/concentration")
def get_portfolio_concentration(db: Session = Depends(get_db)):
    """Get position concentration analysis"""
    try:
        from app.services.portfolio_risk import portfolio_risk_manager
        return portfolio_risk_manager.get_concentration_risk()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/portfolio/alerts")
def get_portfolio_risk_alerts(db: Session = Depends(get_db)):
    """Get active risk alerts"""
    try:
        from app.services.portfolio_risk import portfolio_risk_manager
        return portfolio_risk_manager.get_risk_alerts()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/portfolio/dashboard")
def get_full_portfolio_dashboard(db: Session = Depends(get_db)):
    """Get complete portfolio dashboard in one call"""
    try:
        from app.services.portfolio_risk import portfolio_risk_manager

        return {
            "summary": portfolio_risk_manager.get_portfolio_summary(),
            "correlations": portfolio_risk_manager.get_correlation_matrix(),
            "var": portfolio_risk_manager.get_var_analysis(),
            "concentration": portfolio_risk_manager.get_concentration_risk(),
            "alerts": portfolio_risk_manager.get_risk_alerts(),
            "timestamp": datetime.datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/inventory/analyze")
async def api_trigger_sell_analysis(bg: BackgroundTasks, db: Session = Depends(get_db)):
    bg.add_task(run_deep_sell_analysis, db)
    return {"status": "Analysis Started"}

@app.post("/api/inventory/analyze/{ticker}")
async def api_analyze_single(ticker: str, bg: BackgroundTasks, db: Session = Depends(get_db)):
    item = db.query(Inventory).filter(Inventory.ticker == ticker).first()
    if not item: raise HTTPException(status_code=404, detail="Asset not found")
    bg.add_task(run_deep_sell_analysis, db)
    return {"status": "Analysis Queued"}

class InventoryAdd(BaseModel):
    ticker: str
    asset_class: str
    quantity: float
    buy_price: float

@app.get("/api/macro/pulse")
def get_macro_pulse(db: Session = Depends(get_db)):
    """Get market pulse from consumption Dashboard_Market_Overview"""
    result = safe_query(db, """
        SELECT region, index_name, current_value, change_pct, trend, sentiment_score
        FROM consumption.Dashboard_Market_Overview
    """, label="macro_pulse")

    pulse_data = {}
    for row in result:
        pulse_data[row.region] = {
            "value": float(row.current_value or 0),
            "change": float(row.change_pct or 0),
            "label": row.index_name or row.region,
            "rationale": f"Market trend: {row.trend}",
            "estimates": {"1d": "---", "1w": "---", "1m": "---"}
        }

    # Get risk from system config
    risk = safe_query_one(db, "SELECT value FROM gold.system_config WHERE component='risk_mgmt' AND key='max_portfolio_risk_daily'", label="risk_config")

    return {
        "indices": pulse_data,
        "system_risk": "LOW" if not risk else ("HIGH" if float(risk.value) > 5 else "LOW"),
        "shock_text": "Markets operating normally"
    }

@app.get("/api/signals/1")
def get_signals(db: Session = Depends(get_db)):
    """Get trading signals from consumption views with live price updates"""
    import yfinance as yf
    from datetime import datetime

    # Get signals from consumption
    signals_result = safe_query(db, """
        SELECT
            s.strategy_id, s.ticker, s.signal as action, s.signal_strength as total_conf,
            s.confidence_score, s.current_price,
            s.win_rate, s.updated_at as timestamp, m.market, m.change_pct as daily_change
        FROM consumption.Strategies_Signals_Current s
        LEFT JOIN consumption.Markets_Stocks_Overview m ON s.ticker = m.ticker
        WHERE s.signal IN ('BUY', 'SELL')
        ORDER BY s.confidence_score DESC
        LIMIT 20
    """, label="signals_current")

    res = []
    for s in signals_result:
        ticker_symbol = s.ticker

        # Try to get live price from yfinance
        live_price = None
        live_change = None
        try:
            # Handle different ticker formats
            yf_ticker = ticker_symbol
            if ticker_symbol.endswith('.HK'):
                yf_ticker = ticker_symbol  # Already in correct format
            elif ticker_symbol in ['BTC-USD', 'ETH-USD', 'SOL-USD']:
                yf_ticker = ticker_symbol  # Crypto

            ticker = yf.Ticker(yf_ticker)
            info = ticker.info

            # Get current price
            live_price = info.get('currentPrice') or info.get('regularMarketPrice') or s.current_price

            # Get change percentage
            live_change = info.get('regularMarketChangePercent') or s.daily_change
            if live_change and isinstance(live_change, (int, float)):
                live_change = round(live_change, 2)

        except Exception as e:
            # Fallback to database price
            live_price = s.current_price
            live_change = s.daily_change

        res.append({
            "ticker": s.ticker,
            "market": s.market or "US",
            "horizon": "1W",
            "price": round(live_price or 0, 2),
            "change": round(live_change or 0, 2),
            "change5d": None,
            "change1m": None,
            "changeYTD": None,
            "action": s.action,
            "total_conf": round((s.total_conf or 0) * 100, 1),
            "trad_conf": round((s.total_conf or 0) * 100, 1),
            "swarm_conf": round((s.confidence_score or 0) * 100, 1),
            "estimates": {"1d": "---", "7d": "---", "1m": "---"},
            "win_rate": round((s.win_rate or 0) * 100, 1),
            "tags": [s.strategy_id],
            "metrics": {},
            "logic": f"Signal from {s.strategy_id}",
            "sparkline": [],
            "timestamp": s.timestamp.isoformat() if s.timestamp else None,
            "rec_score": s.confidence_score,
            "candlestick_pattern": None
        })

    return res

@app.get("/api/fx/pairs")
def get_fx_pairs(db: Session = Depends(get_db)):
    result = safe_query(db, """
        SELECT pair as ticker, bid as price, change_pct as change, trend,
               signal as action, signal_strength as confidence, rsi_14 as rsi,
               carry_annual_pct as carry, updated_at as timestamp
        FROM consumption.Markets_FX_Overview ORDER BY pair
    """, label="fx_pairs")
    return [{"ticker": r.ticker, "price": round(r.price or 0, 4), "change": round(r.change or 0, 2),
             "trend": r.trend or "NEUTRAL", "action": r.action or "HOLD",
             "confidence": round((r.confidence or 0) * 100, 1), "rsi": round(r.rsi or 50, 1),
             "carry": round(r.carry or 0, 2)} for r in result]


@app.get("/api/crypto/pairs")
def get_crypto_pairs(db: Session = Depends(get_db)):
    result = safe_query(db, """
        SELECT ticker, name, price, change_pct as change, change_24h_pct as change_24h,
               volume_24h as volume, market_cap, market_cap_rank as rank, trend,
               signal as action, signal_strength as confidence, rsi_14 as rsi,
               funding_rate, fear_greed_index, updated_at as timestamp
        FROM consumption.Markets_Crypto_Overview ORDER BY market_cap DESC NULLS LAST
    """, label="crypto_pairs")
    return [{"ticker": r.ticker, "asset": r.name, "action": r.action or "HOLD",
             "total_conf": round((r.confidence or 0) * 100, 1),
             "price": round(r.price or 0, 2), "change": round(r.change or 0, 2),
             "volume": r.volume, "market_cap": r.market_cap} for r in result]


@app.get("/api/commodities/all")
def get_commodities(db: Session = Depends(get_db)):
    result = safe_query(db, """
        SELECT ticker, name, category, exchange, price, change_pct as change, trend,
               signal as action, signal_strength as confidence, current_month_bias,
               next_month_bias, seasonal_strength, updated_at as timestamp
        FROM consumption.Markets_Commodities_Overview ORDER BY category, ticker
    """, label="commodities_overview")
    return [{"ticker": r.ticker, "asset": r.name, "action": r.action or "HOLD",
             "total_conf": round((r.confidence or 0) * 100, 1),
             "price": round(r.price or 0, 2), "change": round(r.change or 0, 2),
             "seasonality": {"current_month": r.current_month_bias,
                            "next_month": r.next_month_bias,
                            "strength": round((r.seasonal_strength or 0) * 100, 1)}} for r in result]


@app.get("/api/market-data")
def get_market_data(tickers: str = "", db: Session = Depends(get_db)):
    """
    Get current market data for multiple tickers.
    Priority: IBKR (live) > Yahoo Finance (delayed)
    IBKR for: Stocks, FX, Commodities (futures), ETFs
    Yahoo for: Crypto (BTC, ETH, SOL)

    Returns: price, change, changePercent for each ticker with source attribution
    """
    import yfinance as yf

    if not tickers:
        return {"success": True, "data": [], "ibkr_connected": False}

    ticker_list = tickers.split(',')
    results = []

    # Check if IBKR is connected
    ib_connected = False
    try:
        from app.services.ib_service import ib_quant_service
        ib_connected = ib_quant_service.is_connected
    except Exception as e:
        logger.warning(f"Could not check IBKR status: {e}")

    # Define which assets use which source
    YAHOO_ONLY_ASSETS = {'BTC', 'ETH', 'SOL', 'XRP', 'ADA', 'DOT', 'LINK'}

    for ticker in ticker_list:
        ticker = ticker.strip().upper()
        if not ticker:
            continue

        original_ticker = ticker
        price = None
        source = "unknown"
        is_crypto = ticker in YAHOO_ONLY_ASSETS or ticker.replace('-USD', '') in YAHOO_ONLY_ASSETS

        # Crypto always uses Yahoo (IBKR doesn't have crypto)
        if is_crypto:
            try:
                yf_ticker = ticker if '-USD' in ticker else f"{ticker}-USD"
                t = yf.Ticker(yf_ticker)
                df = t.history(period="2d")

                if not df.empty:
                    price = df['Close'].iloc[-1]
                    source = "yfinance"
            except Exception as e:
                logger.warning(f"Yahoo Finance price fetch failed for {ticker}: {e}")

        # For non-crypto, try IBKR first if connected
        elif ib_connected:
            try:
                from app.services.ib_service import ib_quant_service
                ib_price = ib_quant_service.get_price(ticker)
                if ib_price:
                    price = ib_price
                    source = "ibkr"
            except Exception as e:
                logger.warning(f"IBKR price fetch failed for {ticker}: {e}")

        # Fallback to Yahoo for non-crypto if IBKR failed or not connected
        if price is None and not is_crypto:
            try:
                yf_ticker = ticker
                # Handle HK stocks
                if ticker.endswith('.HK'):
                    yf_ticker = ticker

                t = yf.Ticker(yf_ticker)
                df = t.history(period="2d")

                if not df.empty:
                    price = df['Close'].iloc[-1]
                    source = "yfinance"
            except Exception as e:
                logger.warning(f"Yahoo Finance price fetch failed for {ticker}: {e}")

        # Format the response
        if price is not None:
            try:
                # Get historical data for change calculation
                if source == "yfinance":
                    prev_price = df['Close'].iloc[-2] if len(df) > 1 else price
                    change = price - prev_price
                    change_percent = (change / prev_price * 100) if prev_price != 0 else 0
                    volume = int(df['Volume'].iloc[-1]) if 'Volume' in df.columns else 0
                    timestamp = df.index[-1].isoformat() if hasattr(df.index[-1], 'isoformat') else str(df.index[-1])
                else:
                    # For IBKR, get change from Yahoo
                    try:
                        t = yf.Ticker(original_ticker)
                        df = t.history(period="2d")
                        if not df.empty:
                            prev_price = df['Close'].iloc[-2] if len(df) > 1 else price
                            change = price - prev_price
                            change_percent = (change / prev_price * 100) if prev_price != 0 else 0
                            volume = int(df['Volume'].iloc[-1]) if 'Volume' in df.columns else 0
                        else:
                            change = 0
                            change_percent = 0
                            volume = 0
                    except:
                        change = 0
                        change_percent = 0
                        volume = 0

                    timestamp = datetime.now().isoformat()

                results.append({
                    "ticker": original_ticker,
                    "price": round(price, 2),
                    "change": round(change, 2),
                    "changePercent": round(change_percent, 2),
                    "volume": volume,
                    "timestamp": timestamp,
                    "source": source
                })
            except Exception as e:
                results.append({
                    "ticker": original_ticker,
                    "price": round(price, 2),
                    "change": 0,
                    "changePercent": 0,
                    "volume": 0,
                    "timestamp": datetime.now().isoformat(),
                    "source": source
                })
        else:
            results.append({
                "ticker": original_ticker,
                "price": 0,
                "change": 0,
                "changePercent": 0,
                "error": "No price data available from IBKR or Yahoo Finance"
            })

    return {
        "success": True,
        "data": results,
        "count": len(results),
        "ibkr_connected": ib_connected
    }


@app.get("/api/sync/status")
def get_sync_status(db: Session = Depends(get_db)):
    """Get last sync timestamps for each data component"""
    try:
        components = ["stocks", "fx", "crypto", "commodities", "earnings", "consensus"]
        result = {}
        for comp in components:
            row = db.execute(text("""
                SELECT value FROM gold.platform_settings
                WHERE key = :key
            """), {"key": f"last_sync_{comp}"}).fetchone()
            result[comp] = {
                "last_sync": row.value if row else None,
                "status": "synced" if row else "unknown"
            }
        return result
    except Exception as e:
        logger.error(f"Sync status error: {e}")
        return {comp: {"last_sync": None, "status": "unknown"} for comp in ["stocks", "fx", "crypto", "commodities", "earnings", "consensus"]}


@app.post("/api/sync/{component}")
def trigger_sync(component: str, bg: BackgroundTasks, db: Session = Depends(get_db)):
    """Trigger data sync for a specific component"""
    valid_components = ["stocks", "fx", "crypto", "commodities", "earnings", "consensus"]
    if component not in valid_components:
        raise HTTPException(status_code=400, detail=f"Invalid component. Use one of: {valid_components}")

    refresh_map = {
        "stocks": refresh_stock_layer,
        "fx": refresh_fx_layer,
        "crypto": refresh_crypto_layer,
        "commodities": refresh_commodity_layer,
    }

    if component in refresh_map:
        bg.add_task(refresh_map[component], db)
        # Record sync timestamp
        db.execute(text("""
            INSERT INTO gold.platform_settings (key, value, updated_at)
            VALUES (:key, :ts, NOW())
            ON CONFLICT (key) DO UPDATE SET
                value = EXCLUDED.value,
                updated_at = NOW()
        """), {"key": f"last_sync_{component}", "ts": datetime.datetime.now().isoformat()})
        db.commit()
        return {"success": True, "message": f"{component} sync started"}
    else:
        return {"success": True, "message": f"{component} sync not yet implemented"}


@app.get("/api/earnings/upcoming")
def get_upcoming_earnings(db: Session = Depends(get_db)):
    """Get upcoming earnings from consumption data"""
    try:
        result = db.execute(text("""
            SELECT ticker, earnings_date, eps_estimate, revenue_estimate
            FROM consumption.stock
            WHERE earnings_date IS NOT NULL
              AND earnings_date >= CURRENT_DATE
              AND earnings_date <= CURRENT_DATE + INTERVAL '14 days'
            ORDER BY earnings_date ASC
            LIMIT 20
        """)).fetchall()

        return {
            "earnings": [{
                "ticker": r.ticker,
                "date": r.earnings_date.isoformat() if r.earnings_date else None,
                "eps_estimate": float(r.eps_estimate) if r.eps_estimate else None,
                "revenue_estimate": float(r.revenue_estimate) if r.revenue_estimate else None
            } for r in result]
        }
    except Exception as e:
        logger.error(f"Earnings fetch error: {e}")
        return {"earnings": []}


@app.get("/api/settings/data-sources")
def get_data_sources_breakdown(db: Session = Depends(get_db)):
    """
    Get breakdown of all data sources and their frequencies
    Shows which data comes from IBKR vs Yahoo Finance vs Database
    """
    # Check IBKR connection status
    ibkr_connected = False
    try:
        from app.services.ib_service import ib_quant_service
        ibkr_connected = ib_quant_service.is_connected
    except:
        pass

    # Define data source mapping
    data_sources = [
        # Market Data - Real-time
        {
            "category": "Market Data",
            "data_type": "Stock Prices (US)",
            "primary_source": "IBKR" if ibkr_connected else "Yahoo Finance",
            "fallback_source": "Yahoo Finance" if ibkr_connected else "Database",
            "frequency": "Real-time (IBKR) / 15-min delayed (Yahoo)",
            "status": "✅ Active" if ibkr_connected else "⚠️ Using Yahoo",
            "assets": "AAPL, MSFT, TSLA, etc."
        },
        {
            "category": "Market Data",
            "data_type": "Stock Prices (HK)",
            "primary_source": "IBKR" if ibkr_connected else "Yahoo Finance",
            "fallback_source": "Yahoo Finance" if ibkr_connected else "Database",
            "frequency": "Real-time (IBKR) / 15-min delayed (Yahoo)",
            "status": "✅ Active" if ibkr_connected else "⚠️ Using Yahoo",
            "assets": "0700.HK, 9988.HK, etc."
        },
        {
            "category": "Market Data",
            "data_type": "FX Rates",
            "primary_source": "IBKR" if ibkr_connected else "Yahoo Finance",
            "fallback_source": "Yahoo Finance" if ibkr_connected else "Database",
            "frequency": "Real-time streaming (IBKR)",
            "status": "✅ Active" if ibkr_connected else "⚠️ Using Yahoo",
            "assets": "EURUSD, USDJPY, GBPUSD, etc."
        },
        {
            "category": "Market Data",
            "data_type": "Crypto Prices",
            "primary_source": "Yahoo Finance",
            "fallback_source": "Database",
            "frequency": "Real-time",
            "status": "✅ Active",
            "assets": "BTC, ETH, SOL"
        },
        {
            "category": "Market Data",
            "data_type": "Commodity Futures",
            "primary_source": "IBKR" if ibkr_connected else "Yahoo Finance",
            "fallback_source": "Yahoo Finance" if ibkr_connected else "Database",
            "frequency": "Real-time (IBKR) / Delayed (Yahoo)",
            "status": "✅ Active" if ibkr_connected else "⚠️ Using Yahoo",
            "assets": "GC (Gold), CL (Oil), etc."
        },
        # Portfolio & Trading Data
        {
            "category": "Portfolio",
            "data_type": "Account Balance",
            "primary_source": "IBKR",
            "fallback_source": "Database (last known)",
            "frequency": "Real-time on connect",
            "status": "✅ Connected" if ibkr_connected else "❌ Disconnected",
            "assets": "Cash, Margin, Buying Power"
        },
        {
            "category": "Portfolio",
            "data_type": "Positions",
            "primary_source": "IBKR",
            "fallback_source": "Database",
            "frequency": "Real-time sync",
            "status": "✅ Live sync" if ibkr_connected else "⚠️ Cached",
            "assets": "All open positions"
        },
        {
            "category": "Portfolio",
            "data_type": "Order Execution",
            "primary_source": "IBKR",
            "fallback_source": "Database (simulated)",
            "frequency": "Real-time",
            "status": "✅ Active" if ibkr_connected else "🧪 Simulated",
            "assets": "All orders"
        },
        # Research & Analytics
        {
            "category": "Research",
            "data_type": "Earnings Data",
            "primary_source": "FMP API",
            "fallback_source": "Database",
            "frequency": "Daily update (8 AM HKT)",
            "status": "✅ Active",
            "assets": "All stocks"
        },
        {
            "category": "Research",
            "data_type": "Analyst Ratings",
            "primary_source": "FMP API",
            "fallback_source": "Database",
            "frequency": "Daily update",
            "status": "✅ Active",
            "assets": "All stocks"
        },
        {
            "category": "Research",
            "data_type": "SUE Scores",
            "primary_source": "Database (calculated)",
            "fallback_source": "N/A",
            "frequency": "Daily update (8 AM HKT)",
            "status": "✅ Active",
            "assets": "Stocks with earnings"
        },
        {
            "category": "Research",
            "data_type": "Seasonality Patterns",
            "primary_source": "Database (calculated)",
            "fallback_source": "N/A",
            "frequency": "Daily update",
            "status": "✅ Active",
            "assets": "Commodities, FX"
        },
        # Strategy Data
        {
            "category": "Strategies",
            "data_type": "Trading Signals",
            "primary_source": "Database (calculated)",
            "fallback_source": "N/A",
            "frequency": "Hourly refresh",
            "status": "✅ Active",
            "assets": "Per strategy"
        },
        {
            "category": "Strategies",
            "data_type": "Backtest Results",
            "primary_source": "Database",
            "fallback_source": "N/A",
            "frequency": "On deployment",
            "status": "✅ Active",
            "assets": "All strategies"
        },
    ]

    # Count by source
    source_counts = {}
    for ds in data_sources:
        src = ds["primary_source"]
        source_counts[src] = source_counts.get(src, 0) + 1

    return {
        "ibkr_connected": ibkr_connected,
        "ibkr_host": ib_quant_service.host,
        "ibkr_port": ib_quant_service.port,
        "ibkr_mode": "Paper Trading" if ib_quant_service.port == 4002 else "Live Trading",
        "data_sources": data_sources,
        "summary": {
            "total_feeds": len(data_sources),
            "ibkr_primary": source_counts.get("IBKR", 0),
            "yahoo_primary": source_counts.get("Yahoo Finance", 0),
            "database_primary": source_counts.get("Database (calculated)", 0) + source_counts.get("Database", 0),
            "fmp_primary": source_counts.get("FMP API", 0)
        }
    }


@app.get("/api/market/outlook")
def get_market_outlook(db: Session = Depends(get_db)):
    mood = db.query(GlobalState).filter(GlobalState.key == "market_mood_index").first()
    conc = db.query(GlobalState).filter(GlobalState.key == "swarm_conclusion").first()
    recs = db.query(ConsumptionMarket).all()
    return { "market_mood": mood.value if mood else "Stable", "swarm_conclusion": conc.value if conc else "...", "recommendations": [{"sector": r.sector, "ticker": r.ticker, "edge": r.edge_score, "est_1d": r.est_1d, "est_1m": r.est_1m} for r in recs] }

# =============================================================================
# MARKET INTELLIGENCE API ENDPOINTS
# =============================================================================

@app.get("/api/market/indices")
def get_market_indices(timeframe: str = "1D", db: Session = Depends(get_db)):
    """Get major market indices performance"""
    try:
        # Query indices from unified_prices
        indices = ['^GSPC', '^DJI', '^IXIC', '^RUT', '^VIX', '^HSI', '^N225', '^FTSE']
        result = []

        for idx in indices:
            try:
                # Get latest price
                row = db.execute(text("""
                    SELECT ticker, close, date,
                           LAG(close) OVER (ORDER BY date) as prev_close
                    FROM silver.unified_prices
                    WHERE ticker = :ticker
                    ORDER BY date DESC
                    LIMIT 1
                """), {"ticker": idx}).fetchone()

                if row and row.close:
                    change = row.close - (row.prev_close or row.close)
                    change_pct = (change / (row.prev_close or row.close)) * 100 if row.prev_close else 0

                    name_map = {
                        '^GSPC': 'S&P 500', '^DJI': 'Dow Jones', '^IXIC': 'Nasdaq',
                        '^RUT': 'Russell 2000', '^VIX': 'VIX', '^HSI': 'Hang Seng',
                        '^N225': 'Nikkei 225', '^FTSE': 'FTSE 100'
                    }

                    result.append({
                        "symbol": idx,
                        "name": name_map.get(idx, idx),
                        "price": float(row.close),
                        "change": float(change),
                        "change_percent": float(change_pct),
                        "date": row.date.isoformat() if row.date else None
                    })
            except Exception as e:
                logger.warning(f"Error fetching {idx}: {e}")

        return {"data": result}
    except Exception as e:
        logger.error(f"Error in market indices: {e}")
        return {"data": []}

@app.get("/api/market/movers")
def get_market_movers(timeframe: str = "1D", db: Session = Depends(get_db)):
    """Get top gainers and losers"""
    try:
        # Try to get from database first
        rows = db.execute(text("""
            WITH price_changes AS (
                SELECT
                    ticker,
                    close,
                    date,
                    LAG(close) OVER (PARTITION BY ticker ORDER BY date DESC) as prev_close,
                    ROW_NUMBER() OVER (PARTITION BY ticker ORDER BY date DESC) as rn
                FROM silver.unified_prices
                WHERE date >= CURRENT_DATE - INTERVAL '5 days'
            )
            SELECT ticker, close, prev_close,
                   CASE WHEN prev_close > 0 AND prev_close IS NOT NULL
                        THEN ((close - prev_close) / prev_close * 100)
                        ELSE 0
                   END as change_pct
            FROM price_changes
            WHERE rn = 1 AND prev_close IS NOT NULL
            ORDER BY change_pct DESC
        """)).fetchall()

        # If no data in DB, fetch from Yahoo Finance
        if not rows:
            logger.info("No movers data in DB, fetching from Yahoo Finance...")
            import yfinance as yf

            # Get some major tickers to check
            tickers = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'META', 'TSLA', 'AMD', 'INTC', 'NFLX',
                      '0700.HK', '9988.HK', '3690.HK', '0005.HK', '1299.HK']

            movers_data = []
            for ticker in tickers:
                try:
                    stock = yf.Ticker(ticker)
                    info = stock.info
                    if info and 'regularMarketChangePercent' in info:
                        change_pct = info['regularMarketChangePercent']
                        price = info.get('regularMarketPrice', 0)
                        name = info.get('shortName', ticker)
                        if change_pct is not None:
                            movers_data.append({
                                "ticker": ticker,
                                "name": name,
                                "price": float(price),
                                "change_percent": float(change_pct)
                            })
                except Exception as e:
                    continue

            # Sort for gainers and losers
            sorted_stocks = sorted(movers_data, key=lambda x: x["change_percent"], reverse=True)
            gainers = sorted_stocks[:5]
            losers = sorted_stocks[-5:][::-1]

            return {
                "gainers": gainers,
                "losers": losers,
                "source": "yahoo"
            }

        # Group by ticker and get latest
        ticker_changes = {}
        for row in rows:
            if row.ticker not in ticker_changes and row.change_pct is not None:
                ticker_changes[row.ticker] = {
                    "ticker": row.ticker,
                    "price": float(row.close),
                    "change_percent": float(row.change_pct),
                    "name": row.ticker
                }

        # Sort for gainers and losers
        sorted_stocks = sorted(ticker_changes.values(), key=lambda x: x["change_percent"], reverse=True)

        gainers = sorted_stocks[:10]
        losers = sorted_stocks[-10:][::-1]

        return {
            "gainers": gainers,
            "losers": losers,
            "source": "database"
        }
    except Exception as e:
        logger.error(f"Error in market movers: {e}")
        return {"gainers": [], "losers": [], "error": str(e)}

@app.get("/api/market/sectors")
def get_market_sectors(db: Session = Depends(get_db)):
    """Get sector performance from sector ETFs"""
    # Policy: No mock data - return empty/null if real data unavailable

    # Sector ETFs to track performance
    sector_etfs = {
        'XLK': {'name': 'Technology', 'icon': '💻'},
        'XLV': {'name': 'Healthcare', 'icon': '🏥'},
        'XLF': {'name': 'Finance', 'icon': '🏦'},
        'XLE': {'name': 'Energy', 'icon': '⛽'},
        'XLY': {'name': 'Consumer', 'icon': '🛒'},
        'XLI': {'name': 'Industrial', 'icon': '🏭'},
        'XLB': {'name': 'Materials', 'icon': '🏗️'},
        'XLU': {'name': 'Utilities', 'icon': '💡'},
    }

    sectors = []

    try:
        for ticker, info in sector_etfs.items():
            # Get latest price and previous close
            rows = db.execute(text("""
                SELECT close, date,
                       LAG(close) OVER (ORDER BY date) as prev_close
                FROM silver.unified_prices
                WHERE ticker = :ticker
                ORDER BY date DESC
                LIMIT 1
            """), {"ticker": ticker}).fetchall()

            if rows and rows[0].close:
                latest = rows[0]
                change_pct = 0
                if latest.prev_close and latest.prev_close > 0:
                    change_pct = ((float(latest.close) - float(latest.prev_close)) / float(latest.prev_close)) * 100

                sectors.append({
                    "name": info['name'],
                    "ticker": ticker,
                    "change_percent": round(change_pct, 2),
                    "icon": info['icon'],
                    "price": float(latest.close),
                    "last_update": latest.date.isoformat() if latest.date else None
                })
            else:
                # No data - include sector with null values
                sectors.append({
                    "name": info['name'],
                    "ticker": ticker,
                    "change_percent": None,
                    "icon": info['icon'],
                    "price": None,
                    "last_update": None
                })
    except Exception as e:
        logger.error(f"Error fetching sector data: {e}")
        # Return empty rather than mock data
        return {"data": [], "error": str(e)}

    return {"data": sectors}

@app.get("/api/market/volume-leaders")
def get_volume_leaders(db: Session = Depends(get_db)):
    """Get stocks with unusual volume"""
    try:
        rows = db.execute(text("""
            SELECT ticker, close as price, volume,
                   AVG(volume) OVER (PARTITION BY ticker ORDER BY date ROWS BETWEEN 20 PRECEDING AND 1 PRECEDING) as avg_volume
            FROM silver.unified_prices
            WHERE date >= CURRENT_DATE - INTERVAL '1 day'
            ORDER BY date DESC
            LIMIT 50
        """)).fetchall()

        leaders = []
        seen = set()
        for row in rows:
            if row.ticker not in seen and row.avg_volume and row.avg_volume > 0:
                volume_ratio = row.volume / row.avg_volume
                if volume_ratio > 1.5:  # 50% above average
                    leaders.append({
                        "ticker": row.ticker,
                        "name": row.ticker,
                        "price": float(row.price),
                        "volume_ratio": float(volume_ratio),
                        "change_percent": 0.0  # Could calculate
                    })
                    seen.add(row.ticker)

        return {"data": leaders[:12]}
    except Exception as e:
        logger.error(f"Error in volume leaders: {e}")
        return {"data": []}

@app.get("/api/market/global")
def get_global_markets(db: Session = Depends(get_db)):
    """Get global market indices with real data from database"""
    from datetime import datetime, timedelta
    from fastapi.responses import JSONResponse

    # Index mapping: ticker -> display info
    indices = {
        '^GSPC': {'name': 'S&P 500', 'region': 'US', 'flag': '🇺🇸'},
        '^IXIC': {'name': 'Nasdaq', 'region': 'US', 'flag': '🇺🇸'},
        '^FTSE': {'name': 'FTSE 100', 'region': 'Europe', 'flag': '🇬🇧'},
        '^GDAXI': {'name': 'DAX', 'region': 'Europe', 'flag': '🇩🇪'},
        '^N225': {'name': 'Nikkei 225', 'region': 'Asia', 'flag': '🇯🇵'},
        '^HSI': {'name': 'Hang Seng', 'region': 'Asia', 'flag': '🇭🇰'},
        '000001.SS': {'name': 'Shanghai', 'region': 'Asia', 'flag': '🇨🇳'},
        '^AXJO': {'name': 'ASX 200', 'region': 'Asia', 'flag': '🇦🇺'},
    }

    markets = []

    try:
        for ticker, info in indices.items():
            # Get latest price and previous day close for change calculation
            rows = db.execute(text("""
                SELECT close, date
                FROM silver.unified_prices
                WHERE ticker = :ticker
                ORDER BY date DESC
                LIMIT 2
            """), {"ticker": ticker}).fetchall()

            if rows and len(rows) >= 1:
                latest_close = float(rows[0].close) if rows[0].close else 0
                latest_date = rows[0].date

                # Calculate change percent from previous day
                change_percent = 0
                if len(rows) >= 2 and rows[1].close:
                    prev_close = float(rows[1].close)
                    if prev_close > 0:
                        change_percent = ((latest_close - prev_close) / prev_close) * 100

                # Determine market status based on region and time
                # This is simplified - in production you'd use actual market hours
                status = "Closed"
                now = datetime.utcnow()
                hour = now.hour

                if info['region'] == 'US':
                    # US markets: 14:30 - 21:00 UTC
                    status = "Open" if 14 <= hour < 21 else "Closed"
                elif info['region'] == 'Europe':
                    # European markets: 08:00 - 16:30 UTC
                    status = "Open" if 8 <= hour < 16 else "Closed"
                elif info['region'] == 'Asia':
                    # Asian markets (varies by exchange, simplified)
                    if info['name'] in ['Hang Seng', 'Shanghai']:
                        # HK/China: 01:30 - 08:00 UTC (morning), 09:00 - 12:00 (afternoon)
                        status = "Open" if (1 <= hour < 8) or (9 <= hour < 12) else "Closed"
                    elif info['name'] == 'Nikkei 225':
                        # Japan: 00:00 - 06:00 UTC (morning), 07:00 - 10:00 (afternoon)
                        status = "Open" if (0 <= hour < 6) or (7 <= hour < 10) else "Closed"
                    else:
                        status = "Closed"

                markets.append({
                    "name": info['name'],
                    "region": info['region'],
                    "flag": info['flag'],
                    "ticker": ticker,
                    "price": round(latest_close, 2),
                    "change_percent": round(change_percent, 2),
                    "status": status,
                    "last_update": latest_date.isoformat() if latest_date else None
                })
            else:
                # No data available - use placeholder
                markets.append({
                    "name": info['name'],
                    "region": info['region'],
                    "flag": info['flag'],
                    "ticker": ticker,
                    "price": None,
                    "change_percent": None,
                    "status": "No Data",
                    "last_update": None
                })
    except Exception as e:
        logger.error(f"Error fetching global markets: {e}")
        # Return empty list on error
        return {"data": [], "error": str(e)}

    # Return with cache-control headers to prevent browser caching
    return JSONResponse(
        content={"data": markets},
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0"
        }
    )

@app.get("/api/market/breadth")
def get_market_breadth(db: Session = Depends(get_db)):
    """Get market breadth indicators"""
    try:
        # Count advancing vs declining
        rows = db.execute(text("""
            WITH latest_changes AS (
                SELECT ticker,
                       close,
                       LAG(close) OVER (PARTITION BY ticker ORDER BY date) as prev_close
                FROM silver.unified_prices
                WHERE date >= CURRENT_DATE - INTERVAL '1 day'
            )
            SELECT
                SUM(CASE WHEN close > prev_close THEN 1 ELSE 0 END) as advancing,
                SUM(CASE WHEN close < prev_close THEN 1 ELSE 0 END) as declining,
                SUM(CASE WHEN close = prev_close THEN 1 ELSE 0 END) as unchanged
            FROM latest_changes
            WHERE prev_close IS NOT NULL
        """)).fetchone()

        return {
            "advancing": rows.advancing or 0,
            "declining": rows.declining or 0,
            "unchanged": rows.unchanged or 0,
            "newHighs": 0,  # Would need 52-week high calculation
            "newLows": 0,
            "above50MA": None,
            "above200MA": None,
            "overbought": None,
            "oversold": None
        }
    except Exception as e:
        logger.error(f"Error in market breadth: {e}")
        return {
            "advancing": 0, "declining": 0, "unchanged": 0,
            "newHighs": 0, "newLows": 0,
            "above50MA": None, "above200MA": None
        }

from app.services.cnn_fear_greed import fetch_cnn_fear_greed, get_fear_greed_label

@app.get("/api/market/sentiment")
def get_market_sentiment(country: str = "US", db: Session = Depends(get_db)):
    """Get market sentiment indicators — CNN Fear & Greed + CBOE VIX.
    Supports country=US (live CNN + VIX), country=HK/CN (null — no equivalent feed)."""
    try:
        # Only US has CNN Fear & Greed + CBOE VIX. HK/CN have no equivalent live feed.
        if country.upper() != "US":
            return {
                "fearGreed": None,
                "fearGreedLabel": None,
                "vix": None,
                "putCall": None,
                "country": country.upper(),
                "source": None,
                "note": f"Market sentiment data unavailable for {country.upper()}"
            }

        # 1. Try CNN Fear & Greed Index (live public feed)
        cnn = fetch_cnn_fear_greed()
        if cnn:
            fear_greed = cnn["score"]
            fear_greed_label = cnn["rating"] or get_fear_greed_label(fear_greed)
        else:
            fear_greed = None
            fear_greed_label = None

        # 2. Try CBOE VIX from database (primary: silver.unified_prices, fallback: consumption view)
        vix = None
        try:
            vix_row = db.execute(text("""
                SELECT close FROM silver.unified_prices
                WHERE ticker = '^VIX'
                ORDER BY date DESC
                LIMIT 1
            """)).fetchone()
            if vix_row and vix_row.close:
                vix = float(vix_row.close)
        except Exception:
            # silver.unified_prices may not exist — try consumption view
            try:
                vix_row = db.execute(text("""
                    SELECT price FROM consumption.markets_stocks_overview
                    WHERE ticker = '^VIX'
                    LIMIT 1
                """)).fetchone()
                if vix_row and vix_row.price:
                    vix = float(vix_row.price)
            except Exception:
                pass

        # 3. Build response — never derive synthetic fear/greed from VIX.
        #    If CNN is unavailable, return None so the frontend shows "—".
        return {
            "fearGreed": fear_greed,
            "fearGreedLabel": fear_greed_label,
            "vix": vix,
            "putCall": None,
            "country": "US",
            "source": "cnn" if cnn else ("vix" if vix is not None else None),
            "note": None if (fear_greed is not None or vix is not None) else "Market sentiment data unavailable"
        }
    except Exception as e:
        logger.error(f"Error in market sentiment: {e}")
        return {
            "fearGreed": None,
            "fearGreedLabel": None,
            "vix": None,
            "putCall": None,
            "country": country.upper(),
            "source": None,
            "error": str(e)
        }

@app.get("/api/inventory/evaluate")
def get_inventory_evaluate(db: Session = Depends(get_db)):
    result = safe_query(db, """
        SELECT id, ticker, side, quantity, strategy_id,
               entry_price, current_price, market_value,
               weight_pct as portfolio_weight, unrealized_pnl as pnl,
               entry_date, (CURRENT_DATE - entry_date) as days_held
        FROM consumption.portfolio_positions_current
        WHERE status = 'ACTIVE'
        ORDER BY market_value DESC
    """, label="inventory_evaluate")
    positions = [{"id": r.id, "ticker": r.ticker, "name": r.ticker,
                  "asset_class": None, "side": r.side,
                  "quantity": float(r.quantity or 0), "entry_price": float(r.entry_price or 0),
                  "current_price": float(r.current_price or 0),
                  "market_value": float(r.market_value or 0),
                  "pnl": float(r.pnl or 0), "strategy": r.strategy_id,
                  "days_held": r.days_held} for r in result]
    total_value = sum(p["market_value"] for p in positions)
    return {"positions": positions, "active_positions": len(positions),
            "inventory_value": total_value}


@app.post("/api/inventory/add")
async def add_to_inventory(item: InventoryAdd, db: Session = Depends(get_db)):
    try:
        ticker = item.ticker.strip().upper()
        sym = ticker if not item.asset_class == 'FX' else f"{ticker}=X"
        if item.asset_class == 'COMMODITY' and not (ticker.endswith("=F") or ticker.endswith("-USD")):
             sym = f"{ticker}=F"
        t_yf = yf.Ticker(sym); df = t_yf.history(period="1d")
        curr_p = df['Close'].iloc[-1] if not df.empty else item.buy_price
    except: curr_p = item.buy_price
    new_item = Inventory(ticker=ticker, asset_class=item.asset_class, quantity=item.quantity, buy_price=item.buy_price, current_price=curr_p, win_loss="0.0%", analysis={"decision": "HOLD", "reasoning": "Position added. AI Swarm analysis pending next sync."}, status="held")
    db.add(new_item); db.commit(); return {"status": "success"}

@app.delete("/api/inventory/delete/{ticker}")
async def delete_from_inventory(ticker: str, db: Session = Depends(get_db)):
    db.execute(text("DELETE FROM consumption.inventory WHERE ticker = :t"), {"t": ticker})
    db.commit(); return {"status": "success"}

@app.get("/api/metadata/formulas")
def get_formula_metadata(db: Session = Depends(get_db)):
    res = db.execute(text("SELECT asset_class, metric_name, formula_raw, description, weight_impact FROM gold.metric_definitions ORDER BY asset_class, metric_name"))
    return [dict(r._mapping) for r in res.fetchall()]

@app.get("/api/metadata/thresholds")
def get_strategy_thresholds(db: Session = Depends(get_db)):
    res = db.execute(text("SELECT horizon, target_pct, win_criteria_days FROM gold.strategy_thresholds WHERE is_active = True ORDER BY win_criteria_days ASC"))
    return [dict(r._mapping) for r in res.fetchall()]

@app.get("/api/metadata/sync_schedules")
def get_sync_schedules(db: Session = Depends(get_db)):
    res = db.execute(text("SELECT component, frequency, last_run FROM gold.sync_schedules ORDER BY component"))
    return [dict(r._mapping) for r in res.fetchall()]

@app.post("/api/metadata/sync_schedules/update")
async def update_sync_schedule(payload: dict, db: Session = Depends(get_db)):
    db.execute(text("UPDATE gold.sync_schedules SET frequency = :freq WHERE component = :comp"), {"freq": payload['frequency'], "comp": payload['component']})
    db.commit()
    return {"status": "success"}

@app.get("/api/metadata/strategy_configs")
def get_strategy_configs(db: Session = Depends(get_db)):
    res = db.execute(text("SELECT asset_class, win_rate_target, default_margin FROM gold.strategy_configs WHERE is_active = True ORDER BY asset_class"))
    return [dict(r._mapping) for r in res.fetchall()]

@app.post("/api/metadata/strategy_configs/update")
async def update_strategy_config(payload: dict, db: Session = Depends(get_db)):
    db.execute(text("UPDATE gold.strategy_configs SET win_rate_target = :wrt WHERE asset_class = :ac"), {"wrt": payload['win_rate_target'], "ac": payload['asset_class']})
    db.commit(); return {"status": "success"}

# --- POSITION MANAGEMENT APIS ---
@app.post("/api/positions/{position_id}/close")
def close_position(position_id: str, payload: dict = None, db: Session = Depends(get_db)):
    """
    Close a position at market price.
    Updates inventory and propagates closing P&L to strategies.
    """
    try:
        # Get the position details
        position = db.execute(text("""
            SELECT id, ticker, strategy_id, quantity, entry_price,
                   invested_capital, realized_pnl, unrealized_pnl, trades_count
            FROM consumption.portfolio_positions_current
            WHERE id = :position_id
        """), {"position_id": position_id}).fetchone()

        if not position:
            raise HTTPException(status_code=404, detail="Position not found")

        # Get current market price
        ticker = position.ticker
        close_price = None

        # Fallback to Yahoo Finance
        if close_price is None:
            import yfinance as yf
            yf_ticker = ticker
            if ticker == 'BTC':
                yf_ticker = 'BTC-USD'
            elif ticker == 'ETH':
                yf_ticker = 'ETH-USD'
            elif ticker == 'SOL':
                yf_ticker = 'SOL-USD'

            t = yf.Ticker(yf_ticker)
            df = t.history(period="1d")
            if not df.empty:
                close_price = df['Close'].iloc[-1]
                # Handle crypto micro-units
                if ticker in ['BTC', 'ETH', 'SOL']:
                    close_price = close_price / 1000

        if close_price is None:
            raise HTTPException(status_code=500, detail="Could not fetch current market price")

        # Calculate final P&L
        entry_price = position.entry_price or 0
        invested = position.invested_capital or 0
        quantity = position.quantity or 0

        if entry_price > 0 and invested > 0:
            shares = invested / entry_price
            exit_value = shares * close_price
            trade_pnl = exit_value - invested
            pnl_pct = (trade_pnl / invested) * 100 if invested > 0 else 0
        else:
            trade_pnl = 0
            pnl_pct = 0

        # Record the trade execution
        db.execute(text("""
            INSERT INTO gold.trade_executions
            (strategy_id, ticker, side, quantity, entry_price, exit_price,
             pnl, pnl_pct, status, executed_at, execution_mode)
            VALUES (:strategy_id, :ticker, 'SELL', :quantity, :entry_price, :exit_price,
                    :pnl, :pnl_pct, 'CLOSED', NOW(), 'PAPER_TRADING')
        """), {
            "strategy_id": position.strategy_id,
            "ticker": ticker,
            "quantity": quantity,
            "entry_price": entry_price,
            "exit_price": close_price,
            "pnl": trade_pnl,
            "pnl_pct": pnl_pct
        })

        # Update the paper strategy position
        db.execute(text("""
            UPDATE consumption.portfolio_positions_current
            SET realized_pnl = COALESCE(realized_pnl, 0) + :trade_pnl,
                unrealized_pnl = 0,
                invested_capital = 0,
                status = 'CLOSED',
                current_price = :close_price,
                updated_at = NOW()
            WHERE id = :position_id
        """), {
            "position_id": position_id,
            "trade_pnl": trade_pnl,
            "close_price": close_price
        })

        db.commit()

        return {
            "status": "success",
            "position_id": position_id,
            "ticker": ticker,
            "close_price": round(close_price, 2),
            "pnl": round(trade_pnl, 2),
            "pnl_pct": round(pnl_pct, 2),
            "message": f"Closed {ticker} at ${close_price:.2f} with P&L ${trade_pnl:.2f} ({pnl_pct:+.2f}%)"
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error closing position: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to close position: {str(e)}")

@app.get("/api/portfolio/positions")
def get_portfolio_positions(db: Session = Depends(get_db)):
    """
    Get all portfolio positions with current market data.
    Unified view of all assets across strategies.
    """
    result = safe_query(db, """
        SELECT
            id,
            ticker,
            strategy_id,
            side,
            quantity,
            entry_price,
            current_price,
            market_value,
            unrealized_pnl as pnl,
            entry_date,
            (CURRENT_DATE - entry_date) as days_held
        FROM consumption.portfolio_positions_current
        WHERE status = 'ACTIVE' AND quantity > 0
        ORDER BY market_value DESC
    """, label="portfolio_positions")

    positions = []
    for r in result:
        entry_price = float(r.entry_price or 0)
        current_price = float(r.current_price or 0)
        pnl_pct = ((current_price / entry_price) - 1) * 100 if entry_price > 0 else 0
        positions.append({
            "id": r.id,
            "ticker": r.ticker,
            "strategy": r.strategy_id,
            "asset_class": None,  # no asset_class column on portfolio_positions_current
            "side": r.side,
            "quantity": float(r.quantity or 0),
            "entry_price": entry_price,
            "current_price": current_price,
            "market_value": float(r.market_value or 0),
            "pnl": float(r.pnl or 0),
            "pnl_pct": round(pnl_pct, 2),
            "days_held": r.days_held
        })

    total_value = sum(p["market_value"] for p in positions)
    total_pnl = sum(p["pnl"] for p in positions)

    return {
        "positions": positions,
        "total_positions": len(positions),
        "total_value": total_value,
        "total_pnl": total_pnl,
        "active_positions": len([p for p in positions if p["quantity"] > 0])
    }

# --- MAINTENANCE & REFRESH APIS (5 DOMAINS) ---
@app.post("/api/maintenance/refresh/indices")
async def api_refresh_indices(bg: BackgroundTasks):
    # DISABLED: Read-only mode - data refresh handled by DE agent
    return {"status": "Read-only mode - refresh disabled"}

@app.get("/api/maintenance/status/indices")
async def api_status_indices(db: Session = Depends(get_db)):
    exists = db.execute(text("SELECT 1 FROM consumption.global_state WHERE timestamp > NOW() - INTERVAL '5 minutes' AND category = 'index' LIMIT 1")).first()
    return {"status": "Live" if exists else "Idle"}

@app.post("/api/maintenance/refresh/fx")
async def api_refresh_fx(bg: BackgroundTasks):
    # DISABLED: Read-only mode - data refresh handled by DE agent
    return {"status": "Read-only mode - refresh disabled"}

@app.get("/api/maintenance/status/fx")
async def api_status_fx(db: Session = Depends(get_db)):
    exists = db.execute(text("SELECT 1 FROM gold.fx_metrics WHERE date > NOW() - INTERVAL '5 minutes' LIMIT 1")).first()
    return {"status": "Live" if exists else "Idle"}

# --- FX STREAMING ENDPOINTS (Phase 1.1) ---
@app.get("/api/fx/streaming/status")
async def api_fx_streaming_status(db: Session = Depends(get_db)):
    """Get FX streaming service status"""
    try:
        from app.services.fx_streaming_service import fx_streaming_service
        status = {
            "is_connected": fx_streaming_service.is_connected,
            "pairs": fx_streaming_service.FX_PAIRS,
            "subscribed": list(fx_streaming_service.tickers.keys()) if fx_streaming_service.tickers else []
        }
        return status
    except Exception as e:
        return {"error": str(e)}

@app.get("/api/fx/bars/latest")
async def api_fx_bars_latest(ticker: str = None, limit: int = 12, db: Session = Depends(get_db)):
    """Get latest 5-second FX bars (default: last 60 seconds = 12 bars)"""
    try:
        if ticker:
            bars = db.execute(text("""
                SELECT bucket, ticker, open, high, low, close,
                       bid_close, ask_close, spread_avg_bps, tick_count
                FROM gold.fx_bars_5s
                WHERE ticker = :ticker
                ORDER BY bucket DESC
                LIMIT :limit
            """), {"ticker": ticker, "limit": limit}).fetchall()
        else:
            # Get latest bar for each major pair
            bars = db.execute(text("""
                SELECT DISTINCT ON (ticker)
                    bucket, ticker, open, high, low, close,
                    bid_close, ask_close, spread_avg_bps, tick_count
                FROM gold.fx_bars_5s
                WHERE ticker IN ('EURUSD', 'USDJPY', 'GBPUSD')
                ORDER BY ticker, bucket DESC
            """)).fetchall()

        return [{
            "bucket": b.bucket.isoformat() if b.bucket else None,
            "ticker": b.ticker,
            "open": b.open,
            "high": b.high,
            "low": b.low,
            "close": b.close,
            "bid": b.bid_close,
            "ask": b.ask_close,
            "spread_bps": b.spread_avg_bps,
            "ticks": b.tick_count
        } for b in bars]
    except Exception as e:
        return {"error": str(e)}

@app.get("/api/fx/streaming/alerts")
async def api_fx_streaming_alerts(limit: int = 10, db: Session = Depends(get_db)):
    """Get recent FX spread alerts"""
    try:
        alerts = db.execute(text("""
            SELECT timestamp, ticker, alert_type, spread_bps, threshold_bps, message
            FROM gold.fx_alerts
            ORDER BY timestamp DESC
            LIMIT :limit
        """), {"limit": limit}).fetchall()

        return [{
            "timestamp": a.timestamp.isoformat() if a.timestamp else None,
            "ticker": a.ticker,
            "type": a.alert_type,
            "spread_bps": a.spread_bps,
            "threshold_bps": a.threshold_bps,
            "message": a.message
        } for a in alerts]
    except Exception as e:
        return {"error": str(e)}

# --- TWS API Status Endpoints (Path 2 Implementation) ---
@app.get("/api/ib/tws/status")
async def api_ib_tws_status():
    """Check TWS API (ib_insync) connection status"""
    try:
        from app.services.ib_service import ib_quant_service
        status = {
            "is_connected": ib_quant_service.is_connected,
            "host": ib_quant_service.host,
            "port": ib_quant_service.port,
            "client_id": ib_quant_service.client_id,
            "recommended": True  # TWS API is recommended for automation
        }
        return status
    except Exception as e:
        return {"error": str(e), "is_connected": False}

@app.post("/api/ib/tws/connect")
async def api_ib_tws_connect():
    """Manually trigger TWS API connection"""
    try:
        from app.services.ib_service import ib_quant_service
        result = await ib_quant_service.connect()
        return result
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/api/ib/web/status")
async def api_ib_web_status():
    """Check Web API (Client Portal) authentication status"""
    try:
        is_auth = ib_web_service.check_auth()
        return {
            "is_authenticated": is_auth,
            "recommended": False,  # Web API is fallback only
            "note": "Use TWS API for automation. Web API for emergency only."
        }
    except Exception as e:
        return {"error": str(e), "is_authenticated": False}

@app.post("/api/maintenance/refresh/commodities")
async def api_refresh_commodities(bg: BackgroundTasks):
    # DISABLED: Read-only mode - data refresh handled by DE agent
    return {"status": "Read-only mode - refresh disabled"}

@app.get("/api/maintenance/status/commodities")
async def api_status_commodities(db: Session = Depends(get_db)):
    exists = db.execute(text("SELECT 1 FROM gold.commodity_metrics WHERE date > NOW() - INTERVAL '5 minutes' LIMIT 1")).first()
    return {"status": "Live" if exists else "Idle"}

@app.post("/api/maintenance/refresh/crypto")
async def api_refresh_crypto(bg: BackgroundTasks):
    # DISABLED: Read-only mode - data refresh handled by DE agent
    return {"status": "Read-only mode - refresh disabled"}

@app.get("/api/maintenance/status/crypto")
async def api_status_crypto(db: Session = Depends(get_db)):
    exists = db.execute(text("SELECT 1 FROM gold.crypto_metrics WHERE date > NOW() - INTERVAL '5 minutes' LIMIT 1")).first()
    return {"status": "Live" if exists else "Idle"}

@app.post("/api/maintenance/refresh/stocks")
async def api_refresh_stocks(bg: BackgroundTasks):
    # DISABLED: Read-only mode - data refresh handled by DE agent
    return {"status": "Read-only mode - refresh disabled"}

@app.post("/api/maintenance/refresh/stocks/daily")
async def api_refresh_stocks_daily(bg: BackgroundTasks):
    # DISABLED: Read-only mode - data refresh handled by DE agent
    return {"status": "Read-only mode - refresh disabled"}

    bg.add_task(run_daily_refresh)
    return {"status": "Daily stock refresh triggered", "tickers": 400}

@app.get("/api/maintenance/status/stocks")
async def api_status_stocks(db: Session = Depends(get_db)):
    exists = db.execute(text("SELECT 1 FROM gold.stock_metrics WHERE date > NOW() - INTERVAL '5 minutes' LIMIT 1")).first()
    return {"status": "Live" if exists else "Idle"}

@app.get("/api/velocity/trades")
def get_velocity_trades(db: Session = Depends(get_db)):
    result = db.execute(text("""
        SELECT id as trade_id, ticker, side, executed_at as entry_date,
               price as entry_price, quantity,
               pnl
        FROM gold.trade_executions ORDER BY executed_at DESC LIMIT 100
    """)).fetchall()
    return [{"id": r.trade_id, "ticker": r.ticker, "side": r.side,
             "entry_price": float(r.entry_price or 0), "pnl": float(r.pnl or 0),
             "strategy": None, "holding_period": 0} for r in result]

@app.get("/api/velocity/summary")
def get_velocity_summary(db: Session = Depends(get_db)):
    trades = db.execute(text("SELECT COUNT(*) as cnt FROM gold.trade_executions")).fetchone()
    summary = db.execute(text("""
        SELECT
            COALESCE(SUM(realized_pnl) + SUM(unrealized_pnl), 0) as total_pnl
        FROM consumption.portfolio_positions_current WHERE status = 'ACTIVE'
    """)).fetchone()
    return {"total_trades": trades.cnt if trades else 0,
            "portfolio_value": 0,
            "total_pnl": float(summary.total_pnl or 0) if summary else 0,
            "win_rate": 0,
            "sharpe_ratio": 0,
            "active_strategies": 8, "status": "active"}


@app.get("/api/stocks/all")
def get_all_stocks(db: Session = Depends(get_db)):
    """Get all stock data from consumption layer"""
    try:
        stocks = db.execute(text("""
            SELECT ticker, name, sector, market, price, change_pct as daily_change,
                   volume, trend, rsi_14, top_strategy_score as final_score,
                   signal as action, signal_strength as confidence, pe_ratio, market_cap
            FROM consumption.Markets_Stocks_Overview
            ORDER BY top_strategy_score DESC NULLS LAST
        """)).fetchall()

        result = []
        for s in stocks:
            result.append({
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
                "market_cap": s.market_cap
            })

        return result
    except Exception as e:
        print(f"Error fetching stocks: {e}")
        return []

@app.get("/api/stocks/{ticker}")
def get_stock_detail(ticker: str, timeframe: str = "ytd", db: Session = Depends(get_db)):
    """Get detailed stock data with technical indicators for a specific ticker"""
    try:
        # Check if ticker exists in asset_registry
        asset = db.execute(text("""
            SELECT ticker, name, asset_class, market
            FROM gold.asset_registry
            WHERE ticker = :ticker AND is_active = TRUE
        """), {"ticker": ticker.upper()}).fetchone()

        if not asset:
            # Try to fetch from yfinance anyway (for non-registered tickers)
            pass

        # Fetch historical data based on timeframe
        import yfinance as yf
        import pandas_ta as ta
        from datetime import datetime, timedelta

        t = yf.Ticker(ticker.upper())
        info = t.info

        # Map timeframe to period
        period_map = {
            "1m": "1mo",
            "ytd": "ytd",
            "12m": "1y",
            "all": "5y"
        }
        yf_period = period_map.get(timeframe, "ytd")

        import pandas as pd

        try:
            df = t.history(period=yf_period)
            if df.empty:
                df = t.history(period="1y")  # fallback
        except:
            df = t.history(period="1y")

        if df.empty:
            raise HTTPException(status_code=404, detail=f"No price data available for {ticker}")

        # Calculate technical indicators
        if not df.empty:
            # SMA lines
            df['SMA_20'] = ta.sma(df['Close'], length=20)
            df['SMA_50'] = ta.sma(df['Close'], length=50)
            df['SMA_200'] = ta.sma(df['Close'], length=200)

            # RSI
            df['RSI'] = ta.rsi(df['Close'], length=14)

            # Prepare chart data
            chart_data = []
            for idx, row in df.iterrows():
                chart_data.append({
                    "date": idx.strftime("%Y-%m-%d"),
                    "price": round(float(row['Close']), 2),
                    "open": round(float(row['Open']), 2),
                    "high": round(float(row['High']), 2),
                    "low": round(float(row['Low']), 2),
                    "volume": int(row['Volume']),
                    "sma_20": round(float(row['SMA_20']), 2) if pd.notna(row['SMA_20']) else None,
                    "sma_50": round(float(row['SMA_50']), 2) if pd.notna(row['SMA_50']) else None,
                    "sma_200": round(float(row['SMA_200']), 2) if pd.notna(row['SMA_200']) else None,
                    "rsi": round(float(row['RSI']), 1) if pd.notna(row['RSI']) else None
                })

            # Current indicator values
            latest = df.iloc[-1]
            current_rsi = round(float(latest['RSI']), 1) if pd.notna(latest['RSI']) else None

            # SMA trend signals
            sma_signal = "NEUTRAL"
            if pd.notna(latest['SMA_20']) and pd.notna(latest['SMA_50']):
                if latest['Close'] > latest['SMA_20'] > latest['SMA_50']:
                    sma_signal = "BULLISH"
                elif latest['Close'] < latest['SMA_20'] < latest['SMA_50']:
                    sma_signal = "BEARISH"
        else:
            chart_data = []
            current_rsi = None
            sma_signal = "UNKNOWN"

        # Calculate YTD
        ytd = None
        try:
            current_year = datetime.now().year
            start_date = f"{current_year}-01-01"
            df_ytd = t.history(start=start_date)
            if not df_ytd.empty and len(df_ytd) > 1:
                year_start_price = float(df_ytd['Close'].iloc[0])
                latest_price = float(df_ytd['Close'].iloc[-1])
                ytd = round(((latest_price - year_start_price) / year_start_price) * 100, 2)
        except:
            ytd = info.get('regularMarketChangePercent', 0) * 100 if info else None

        # Get 52 week high/low
        try:
            ytd_high = info.get('fiftyTwoWeekHigh')
            ytd_low = info.get('fiftyTwoWeekLow')
            current_price = info.get('currentPrice') or info.get('regularMarketPrice') or float(latest['Close'])
            daily_change = info.get('regularMarketChangePercent')
            company_name = info.get('shortName') or info.get('longName') or ticker.upper()
        except:
            ytd_high = None
            ytd_low = None
            current_price = float(latest['Close'])
            daily_change = None
            company_name = ticker.upper()

        return {
            "ticker": ticker.upper(),
            "market": asset.market if asset else "US",
            "name": company_name,
            "price": current_price,
            "daily_change": daily_change,
            "changeYTD": ytd,
            "ytd_high": ytd_high,
            "ytd_low": ytd_low,
            "final_score": None,
            "estimates": {
                "1d": None,
                "7d": None,
                "1m": None
            },
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
            "timestamp": datetime.now().isoformat(),
            # New technical indicator data
            "chart_data": chart_data,
            "indicators": {
                "rsi": current_rsi,
                "rsi_signal": "OVERBOUGHT" if current_rsi and current_rsi > 70 else "OVERSOLD" if current_rsi and current_rsi < 30 else "NEUTRAL",
                "sma_signal": sma_signal,
                "sma_20": round(float(latest['SMA_20']), 2) if pd.notna(latest.get('SMA_20')) else None,
                "sma_50": round(float(latest['SMA_50']), 2) if pd.notna(latest.get('SMA_50')) else None,
                "sma_200": round(float(latest['SMA_200']), 2) if pd.notna(latest.get('SMA_200')) else None
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"Stock Detail API Error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/crypto/all")
def get_all_crypto(db: Session = Depends(get_db)):
    """Get all crypto data from consumption layer"""
    try:
        cryptos = db.execute(text("""
            SELECT * FROM consumption.crypto
            ORDER BY total_confidence DESC
        """)).fetchall()

        return [{
            "ticker": c.ticker,
            "asset": c.asset_name,
            "price": c.close_price,
            "change": c.daily_change,
            "action": c.action,
            "total_confidence": c.total_confidence,
            "trad_confidence": c.trad_confidence,
            "swarm_confidence": c.swarm_confidence,
            "est_1d": c.est_1d,
            "est_7d": c.est_7d,
            "est_1m": c.est_1m,
            "win_rate": c.win_rate,
            "rec_score": c.rec_score,
            "mvrv_z_score": c.mvrv_z_score,
            "fear_greed_index": c.fear_greed_index,
            "funding_rate": c.funding_rate,
            "gas_price_gwei": c.gas_price_gwei,
            "candlestick_pattern": c.candlestick_pattern,
            "logic": c.logic,
            "sparkline": c.sparkline,
            "timestamp": c.timestamp.isoformat() if c.timestamp else None
        } for c in cryptos]
    except Exception as e:
        print(f"Crypto API Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# --- QUANT STRATEGY APIS ---
@app.get("/api/quant/templates")
def get_strategy_templates():
    return strategy_manager.get_templates()

@app.get("/api/quant/strategies")
def get_quant_strategies(db: Session = Depends(get_db)):
    try:
        # Iteration 65: Performance update moved to background scheduler to support real trading
        # strategy_manager.update_live_performance()
        strats = db.query(QuantStrategy).all()
        return strats
    except Exception as e:
        print(f"Quant Strategy API Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/quant/strategies/bulk-create")
def bulk_create_strategies_api(payload: dict, db: Session = Depends(get_db)):
    try:
        selections = payload.get("selections", [])
        strats = strategy_manager.bulk_create_strategies(selections)
        return {"status": "success", "count": len(strats)}
    except Exception as e:
        print(f"Bulk Create Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/quant/strategies/mode")
def set_strategy_mode(payload: dict, db: Session = Depends(get_db)):
    # payload: { id: int, mode: "SIMULATION" | "PAPER" }
    success = strategy_manager.toggle_mode(payload.get("id"), payload.get("mode"))
    return {"status": "success" if success else "failed"}

@app.post("/api/quant/strategies/create")
def create_strategy(payload: dict, db: Session = Depends(get_db)):
    try:
        pair = payload.get("pair", "EURUSD=X")
        qty = payload.get("lot_size", 1000)
        template_id = payload.get("template_id", "MR_FX")
        mode = payload.get("execution_mode", "SIMULATION")
        strat = strategy_manager.create_fx_strategy(pair, qty, template_id, mode)
        return strat
    except Exception as e:
        print(f"Quant Strategy Create Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/quant/strategies/clear-logs")
def clear_trade_logs(db: Session = Depends(get_db)):
    try:
        # Clear the gold.trade_executions table
        # Using DELETE instead of TRUNCATE for safer permission handling
        db.execute(text("DELETE FROM gold.trade_executions"))
        db.commit()
        return {"status": "success", "message": "Simulation logs cleared from consumption layer."}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/quant/strategies/toggle/{strat_id}")
def toggle_strategy(strat_id: int, db: Session = Depends(get_db)):
    strat = db.query(QuantStrategy).filter(QuantStrategy.id == strat_id).first()
    if strat:
        strat.is_active = not strat.is_active
        db.commit()
    return {"status": "success"}

@app.delete("/api/quant/strategies/delete/{strat_id}")
def delete_strategy(strat_id: int, db: Session = Depends(get_db)):
    db.query(QuantStrategy).filter(QuantStrategy.id == strat_id).delete()
    db.commit()
    return {"status": "success"}

# ========== NEW: Asset Class Strategy Management ==========

@app.get("/api/strategies/templates")
def get_templates_by_asset(asset_class: str = None):
    """Get strategy templates filtered by asset class (FX, STOCK, CRYPTO)"""
    return strategy_manager.get_templates_by_asset(asset_class)

@app.get("/api/strategies/templates/{asset_class}")
def get_templates_for_asset(asset_class: str):
    """Get all templates for a specific asset class"""
    return strategy_manager.get_templates_by_asset(asset_class.upper())

@app.post("/api/strategies/create")
def create_strategy_api(payload: dict, db: Session = Depends(get_db)):
    """Create a strategy for any asset class
    payload: {
        "ticker": "AAPL" or "EURUSD=X" or "BTC-USD",
        "template_id": "MOMENTUM_STOCK",
        "capital": 10000,
        "execution_mode": "SIMULATION"
    }
    """
    try:
        strategy = strategy_manager.create_strategy(
            ticker=payload.get("ticker"),
            template_id=payload.get("template_id"),
            capital=payload.get("capital", 10000),
            execution_mode=payload.get("execution_mode", "SIMULATION")
        )
        return {
            "status": "success",
            "strategy_id": strategy.id,
            "name": strategy.name,
            "asset_class": strategy.params.get("asset_class") if strategy.params else None
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/strategies/by-asset/{asset_class}")
def get_strategies_by_asset(asset_class: str, db: Session = Depends(get_db)):
    """Get all strategies for a specific asset class"""
    strategies = strategy_manager.get_strategies_by_asset(asset_class)
    return [{
        "id": s.id,
        "name": s.name,
        "ticker": s.target_ticker,
        "is_active": s.is_active,
        "current_pnl": s.current_pnl,
        "total_trades": s.total_trades,
        "params": s.params
    } for s in strategies]

# ========== NEW: Daily P&L Analytics ==========

@app.get("/api/strategies/{strategy_id}/daily-pnl")
def get_strategy_daily_pnl_api(
    strategy_id: int,
    start_date: str = None,
    end_date: str = None,
    db: Session = Depends(get_db)
):
    """Get daily P&L breakdown for a specific strategy

    Query params:
    - start_date: YYYY-MM-DD (optional)
    - end_date: YYYY-MM-DD (optional)
    """
    result = strategy_manager.get_strategy_daily_pnl(strategy_id, start_date, end_date)
    if result is None:
        raise HTTPException(status_code=404, detail=f"Strategy {strategy_id} not found")
    return result

@app.get("/api/strategies/{strategy_id}/backtest-summary")
def get_strategy_backtest_summary_api(strategy_id: int, db: Session = Depends(get_db)):
    """Get backtest metrics vs actual performance comparison"""
    result = strategy_manager.get_strategy_backtest_summary(strategy_id)
    if result is None:
        raise HTTPException(status_code=404, detail=f"Strategy {strategy_id} not found")
    return result

@app.get("/api/strategies/{strategy_id}/detail")
def get_strategy_detail(strategy_id: int, db: Session = Depends(get_db)):
    """Get comprehensive strategy details including backtest, daily P&L, and trades"""
    strategy = db.query(QuantStrategy).filter(QuantStrategy.id == strategy_id).first()
    if not strategy:
        raise HTTPException(status_code=404, detail=f"Strategy {strategy_id} not found")

    # Get daily P&L
    daily_pnl = strategy_manager.get_strategy_daily_pnl(strategy_id)

    # Get backtest summary
    backtest = strategy_manager.get_strategy_backtest_summary(strategy_id)

    # Get recent trades
    trades = db.query(Trade).filter(
        Trade.strategy.like(f"{strategy.name}%")
    ).order_by(Trade.timestamp.desc()).limit(50).all()

    return {
        "strategy": {
            "id": strategy.id,
            "name": strategy.name,
            "ticker": strategy.target_ticker,
            "is_active": strategy.is_active,
            "params": strategy.params,
            "current_pnl": strategy.current_pnl,
            "total_trades": strategy.total_trades,
            "winning_trades": strategy.winning_trades,
            "win_rate": round((strategy.winning_trades / strategy.total_trades * 100), 1) if strategy.total_trades else 0,
            "equity_curve": strategy.equity_curve
        },
        "backtest": backtest.get("template_backtest") if backtest else {},
        "actual_performance": backtest.get("actual_performance") if backtest else {},
        "daily_pnl_summary": daily_pnl.get("summary") if daily_pnl else {},
        "recent_trades": [{
            "timestamp": t.timestamp.isoformat(),
            "ticker": t.ticker,
            "side": t.side,
            "quantity": float(t.quantity),
            "price": float(t.price),
            "pnl": float(t.pnl) if t.pnl else 0
        } for t in trades]
    }

@app.get("/api/quant/performance/matrix")
def get_performance_matrix(db: Session = Depends(get_db)):
    # Use the manager to aggregate data
    return strategy_manager.get_performance_matrix()

@app.get("/api/velocity/ib/status")
async def get_ib_status():
    socket_ok = ib_quant_service.is_connected
    web_ok = ib_web_service.check_auth()
    return {
        "status": "Connected" if (socket_ok or web_ok) else "Disconnected",
        "socket": "Connected" if socket_ok else "Offline",
        "web": "Authenticated" if web_ok else "Unauthorized"
    }

@app.post("/api/velocity/ib/connect")
async def trigger_ib_connect():
    result = await ib_quant_service.connect()
    return result

@app.post("/api/velocity/ib/sync-session")
async def sync_ib_session(request: Request):
    """
    Iteration 45: Transparently bridge the browser's IBKR session to the backend.
    """
    cookies = request.cookies
    print(f"Sync Session Received Cookies: {cookies.keys()}")
    if cookies:
        ib_web_service.set_cookies(cookies)
        is_auth = ib_web_service.check_auth()
        print(f"Backend Auth Check: {is_auth}")
        return {"status": "Authenticated" if is_auth else "Unauthorized"}
    return {"status": "No Cookies Found"}

class TradeRequest(BaseModel):
    ticker: str
    action: str # BUY, SELL
    quantity: float
    account_id: str

@app.post("/api/velocity/trade/execute")
async def api_execute_trade(trade: TradeRequest, db: Session = Depends(get_db)):
    """
    Iteration 47: Manual execution API for the dashboard.
    """
    # 1. Execute via IB Web Service
    result = ib_web_service.execute_order(trade.account_id, trade.ticker, trade.action, trade.quantity)

    if result['status'] == 'success':
        # 2. Record the trade in the audit log
        try:
            # Try to get the latest price for auditing
            t_yf = yf.Ticker(trade.ticker); df = t_yf.history(period="1d")
            price = df['Close'].iloc[-1] if not df.empty else 0

            new_trade = Trade(
                ticker=trade.ticker, side=trade.action, price=price,
                quantity=trade.quantity, total_value=price * trade.quantity,
                strategy="MANUAL_OVERRIDE"
            )
            db.add(new_trade); db.commit()
        except: pass
        return result
    else:
        raise HTTPException(status_code=400, detail=result['message'])

@app.get("/api/hft/matrix")
def get_hft_matrix(db: Session = Depends(get_db)):
    res = db.execute(text("SELECT * FROM consumption.hft_matrix ORDER BY timestamp DESC, ticker ASC"))
    return [{
        "ticker": r.ticker,
        "asset_class": r.asset_class,
        "liquidity_momentum": r.liquidity_momentum,
        "fusion_signal": r.fusion_signal,
        "shock_warning": r.shock_warning,
        "pressure_value": r.pressure_value,
        "reasoning": r.reasoning,
        "velocity_estimates": r.velocity_estimates
    } for r in res.fetchall()]

@app.get("/api/performance/strategy")
def get_strategy_performance(db: Session = Depends(get_db)):
    """Get strategy performance with both backtest and actual win rates + CURRENT SIGNAL

    Only returns strategies for the current execution mode (SIMULATION/PAPER_TRADING/LIVE_TRADING)
    """
    _empty_perf = {
        "strategies": [], "monthly_returns": [],
        "summary": {"total_return": 0, "sharpe": 0, "max_drawdown": 0, "win_rate": 0},
    }

    # Get current execution mode
    mode_result = safe_query_one(db, """
        SELECT value FROM gold.platform_settings
        WHERE key = 'global_execution_mode'
    """, label="perf_mode")

    current_mode = mode_result.value if mode_result else 'SIMULATION'

    # Map execution mode to portfolio_type
    portfolio_type_map = {
        'SIMULATION': 'SIMULATION',
        'PAPER_TRADING': 'PAPER',
        'LIVE_TRADING': 'LIVE'
    }
    portfolio_type = portfolio_type_map.get(current_mode, 'SIMULATION')

    # Get strategy attribution for CURRENT MODE ONLY
    attribution = safe_query(db, """
        SELECT strategy_id, strategy_name, allocated_capital_pct as allocation,
               contribution_pct as contribution, return_pct as returns, num_trades,
               win_rate, sharpe_ratio
        FROM consumption.Performance_Strategy_Attribution
        WHERE portfolio_type = :portfolio_type
        ORDER BY return_pct DESC
    """, {"portfolio_type": portfolio_type}, label="perf_attribution")

    # If no data for current mode, return empty (not historical data from other modes)
    if not attribution:
        return {**_empty_perf, "execution_mode": current_mode,
                "note": f"No strategies deployed in {current_mode} mode"}

    # Get backtest win rates
    backtests = safe_query(db, """
        SELECT strategy_id, AVG(win_rate) as backtest_win_rate,
               AVG(profit_factor) as profit_factor,
               AVG(max_drawdown_pct) as max_drawdown,
               AVG(sharpe_ratio) as sharpe,
               SUM(total_trades) as backtest_total_trades,
               AVG(total_return_pct) as backtest_return
        FROM consumption.Strategies_Backtest_Results
        GROUP BY strategy_id
    """, label="perf_backtests")

    # Get actual/live win rates from trade history (using paper_strategies)
    live_stats = safe_query(db, """
        SELECT strategy_id,
               COUNT(*) as total_trades,
               SUM(CASE WHEN realized_pnl > 0 THEN 1 ELSE 0 END) as winning_trades
        FROM consumption.portfolio_positions_current
        WHERE status = 'ACTIVE'
        GROUP BY strategy_id
    """, label="perf_live_stats")

    # Get CURRENT SIGNALS - the strongest active signal for each strategy
    current_signals = safe_query(db, """
        SELECT DISTINCT ON (strategy_id)
            strategy_id,
            ticker,
            signal,
            signal_strength,
            confidence_score,
            current_price
        FROM consumption.Strategies_Signals_Current
        WHERE signal IN ('BUY', 'SELL')
        ORDER BY strategy_id, confidence_score DESC
    """, label="perf_signals")

    # Create lookup dicts
    backtest_data = {b.strategy_id: b for b in backtests}
    live_data = {l.strategy_id: l for l in live_stats}
    signal_data = {s.strategy_id: s for s in current_signals}

    # Build response with both metrics
    strategies = []
    for a in attribution:
        bt = backtest_data.get(a.strategy_id)
        live = live_data.get(a.strategy_id)
        sig = signal_data.get(a.strategy_id)

        # Calculate live win rate from actual trades
        live_win_rate = None
        if live and live.total_trades > 0:
            live_win_rate = round((live.winning_trades / live.total_trades) * 100, 1)

        strategies.append({
            "strategy_id": a.strategy_id,
            "strategy_name": a.strategy_name,
            "allocation": float(a.allocation or 0),
            "contribution": float(a.contribution or 0),
            "returns": float(a.returns or 0),
            "num_trades": a.num_trades or 0,
            "sharpe_ratio": float(a.sharpe_ratio or 0),
            # Live/Actual metrics
            "live_win_rate": live_win_rate,
            "live_trades": live.total_trades if live else 0,
            # Backtest metrics
            "backtest_win_rate": round((bt.backtest_win_rate or 0) * 100, 1) if bt and bt.backtest_win_rate else None,
            "backtest_return": round(bt.backtest_return or 0, 2) if bt else None,
            "backtest_trades": bt.backtest_total_trades if bt else 0,
            # CURRENT SIGNAL
            "current_signal": {
                "action": sig.signal if sig else "HOLD",
                "ticker": sig.ticker if sig else None,
                "strength": round((sig.signal_strength or 0) * 100, 1) if sig else 0,
                "confidence": round((sig.confidence_score or 0) * 100, 1) if sig else 0,
                "price": float(sig.current_price or 0) if sig else None
            } if sig else None
        })

    # Get monthly returns for CURRENT MODE
    monthly = safe_query(db, """
        SELECT year, month, return_pct
        FROM consumption.Performance_Monthly_Returns
        WHERE portfolio_type = :portfolio_type
        ORDER BY year DESC, month DESC LIMIT 12
    """, {"portfolio_type": portfolio_type}, label="perf_monthly")

    # Get summary for CURRENT MODE
    summary = safe_query_one(db, """
        SELECT * FROM consumption.Performance_Portfolio_Summary
        WHERE portfolio_type = :portfolio_type
    """, {"portfolio_type": portfolio_type}, label="perf_portfolio_summary")

    return {
        "strategies": strategies,
        "monthly_returns": [{"year": r.year, "month": r.month, "return": float(r.return_pct or 0)} for r in monthly],
        "summary": {
            "total_return": float(summary.total_pnl_pct or 0) if summary else 0,
            "sharpe": float(summary.sharpe_ratio or 0) if summary else 0,
            "max_drawdown": float(summary.max_drawdown_pct or 0) if summary else 0,
            "win_rate": float(summary.win_rate or 0) * 100 if summary else 0
        },
        "execution_mode": current_mode
    }

@app.get("/api/performance/daily-pnl")
def get_daily_pnl(days: int = 7, db: Session = Depends(get_db)):
    """Get daily P&L - shows actual position entry and exit data"""

    # Get closed trades (realized P&L) - using trade_executions
    closed_trades = db.execute(text("""
        SELECT
            DATE(executed_at) as trade_date,
            SUM(pnl) as day_pnl,
            COUNT(*) as trade_count
        FROM gold.trade_executions
        WHERE pnl IS NOT NULL
        GROUP BY DATE(executed_at)
        ORDER BY trade_date DESC
        LIMIT :days
    """), {"days": days}).fetchall()

    # Get open positions by entry date (unrealized P&L)
    open_positions = safe_query(db, """
        SELECT
            DATE(entry_date) as entry_date,
            SUM(unrealized_pnl) as day_pnl,
            COUNT(*) as position_count
        FROM consumption.Portfolio_Positions_Current
        WHERE side = 'LONG'
        GROUP BY DATE(entry_date)
        ORDER BY entry_date DESC
        LIMIT :days
    """, {"days": days}, label="daily_pnl_open_positions")

    # Combine data
    daily_map = {}

    # Add closed trades
    for t in closed_trades:
        if t.trade_date:
            date_str = str(t.trade_date)
            if date_str not in daily_map:
                daily_map[date_str] = {"pnl": 0, "trades": 0}
            daily_map[date_str]["pnl"] += float(t.day_pnl or 0)
            daily_map[date_str]["trades"] += t.trade_count

    # Add open positions
    for p in open_positions:
        if p.entry_date:
            date_str = str(p.entry_date)
            if date_str not in daily_map:
                daily_map[date_str] = {"pnl": 0, "trades": 0}
            daily_map[date_str]["pnl"] += float(p.day_pnl or 0)
            daily_map[date_str]["trades"] += p.position_count

    # If no data at all
    if not daily_map:
        return {
            "daily": [],
            "summary": {
                "total_pnl": 0,
                "avg_daily_pnl": 0,
                "message": "No positions recorded yet"
            }
        }

    # Build sorted daily data
    sorted_dates = sorted(daily_map.keys())
    daily_data = []
    total_pnl = 0

    for date_str in sorted_dates:
        data = daily_map[date_str]
        daily_data.append({
            "date": date_str,
            "pnl": round(data["pnl"], 2),
            "trades": data["trades"]
        })
        total_pnl += data["pnl"]

    return {
        "daily": daily_data,
        "summary": {
            "total_pnl": round(total_pnl, 2),
            "avg_daily_pnl": round(total_pnl / len(daily_data), 2) if daily_data else 0,
            "best_day": round(max(d["pnl"] for d in daily_data), 2) if daily_data else 0,
            "worst_day": round(min(d["pnl"] for d in daily_data), 2) if daily_data else 0,
            "days_with_activity": len(daily_data)
        }
    }

@app.post("/api/maintenance/refresh/hft")
async def api_refresh_hft(bg: BackgroundTasks):
    # DISABLED: Read-only mode - data refresh handled by DE agent
    return {"status": "Read-only mode - refresh disabled"}

@app.get("/api/maintenance/status/hft")
async def api_status_hft(db: Session = Depends(get_db)):
    exists = db.execute(text("SELECT 1 FROM consumption.hft_matrix WHERE timestamp > NOW() - INTERVAL '5 minutes' LIMIT 1")).first()
    return {"status": "Live" if exists else "Idle"}


# --- TELEGRAM ALERT APIs ---

@app.get("/api/alerts/status")
def get_alert_status():
    """Get Telegram alert service status"""
    from app.services.telegram_alerts import telegram_alerts
    return telegram_alerts.get_status()


@app.post("/api/alerts/configure")
def configure_alerts(config: dict):
    """
    Configure Telegram alerts

    Body: {
        "bot_token": "123456:ABC-DEF...",
        "chat_id": "-5001038390"
    }
    """
    from app.services.telegram_alerts import telegram_alerts

    bot_token = config.get("bot_token")
    chat_id = config.get("chat_id")

    if not bot_token or not chat_id:
        raise HTTPException(status_code=400, detail="bot_token and chat_id required")

    success = telegram_alerts.configure(bot_token, chat_id)

    if success:
        return {
            "status": "success",
            "message": "Telegram alerts configured successfully",
            "test_message_sent": telegram_alerts.send_custom_alert(
                "Configuration Test",
                "✅ Telegram alerts are now configured and working!"
            )
        }
    else:
        raise HTTPException(status_code=400, detail="Failed to configure Telegram. Check bot token and chat ID.")


@app.post("/api/alerts/test")
def test_alert(payload: dict):
    """
    Send a test alert

    Body: {
        "type": "trade|drawdown|custom",
        "message": "optional custom message"
    }
    """
    from app.services.telegram_alerts import telegram_alerts

    if not telegram_alerts.enabled:
        raise HTTPException(status_code=400, detail="Telegram not configured. Use /api/alerts/configure first.")

    alert_type = payload.get("type", "custom")

    if alert_type == "trade":
        success = telegram_alerts.alert_trade_executed(
            strategy_name="TEST_STRATEGY",
            ticker="EURUSD",
            side="BUY",
            quantity=10000,
            price=1.0850,
            pnl=125.50
        )
    elif alert_type == "drawdown":
        success = telegram_alerts.alert_drawdown(
            strategy_name="TEST_STRATEGY",
            drawdown_pct=8.5,
            current_pnl=-850.0,
            allocated=10000.0
        )
    else:
        success = telegram_alerts.send_custom_alert(
            title="Test Alert",
            message=payload.get("message", "This is a test alert from JT Trading Platform"),
            level="INFO"
        )

    return {"status": "sent" if success else "failed"}


@app.post("/api/alerts/daily-summary")
def trigger_daily_summary(db: Session = Depends(get_db)):
    """Manually trigger daily summary alert"""
    from app.services.telegram_alerts import telegram_alerts

    if not telegram_alerts.enabled:
        raise HTTPException(status_code=400, detail="Telegram not configured")

    strategies = db.query(QuantStrategy).filter(QuantStrategy.is_active == True).all()

    total_pnl = sum(s.current_pnl or 0 for s in strategies)
    total_allocated = sum(s.params.get('allocated_capital', 10000) for s in strategies if s.params)
    total_trades = sum(s.total_trades or 0 for s in strategies)

    strategy_list = [{
        "name": s.name,
        "current_pnl": s.current_pnl or 0
    } for s in strategies]

    success = telegram_alerts.send_daily_summary(
        strategies=strategy_list,
        total_pnl=total_pnl,
        total_allocated=total_allocated,
        total_trades=total_trades
    )

    return {"status": "sent" if success else "failed"}


# --- PAPER STRATEGIES API ---

@app.get("/api/paper-strategies")
def get_paper_strategies(db: Session = Depends(get_db)):
    """Get all paper trading strategies with their status - filtered by current execution mode"""

    # Get current execution mode
    mode_result = db.execute(text("""
        SELECT value FROM gold.platform_settings
        WHERE key = 'global_execution_mode'
    """)).fetchone()
    current_mode = mode_result.value if mode_result else 'SIMULATION'

    # Only show positions created in the current mode
    result = db.execute(text("""
        SELECT
            ps.id,
            ps.strategy_id,
            sd.name as strategy_name,
            ps.ticker,
            ps.capital,
            ps.invested_capital,
            ps.available_capital,
            ps.status,
            ps.entry_price,
            ps.current_price,
            ps.unrealized_pnl,
            ps.realized_pnl,
            ps.trades_count,
            ps.created_at,
            ps.execution_mode
        FROM consumption.portfolio_positions_current ps
        LEFT JOIN gold.strategy_registry sd ON ps.strategy_id = sd.strategy_id
        WHERE ps.execution_mode = :mode
        ORDER BY ps.created_at DESC
    """), {"mode": current_mode}).fetchall()

    strategies = []
    for row in result:
        strategies.append({
            "id": row.id,
            "strategy_id": row.strategy_id,
            "strategy_name": row.strategy_name or row.strategy_id,
            "ticker": row.ticker,
            "capital": float(row.capital) if row.capital else 10000,
            "invested_capital": float(row.invested_capital) if row.invested_capital else 0,
            "available_capital": float(row.available_capital) if row.available_capital else 10000,
            "status": row.status,
            "entry_price": float(row.entry_price) if row.entry_price else None,
            "current_price": float(row.current_price) if row.current_price else None,
            "unrealized_pnl": float(row.unrealized_pnl) if row.unrealized_pnl else 0,
            "realized_pnl": float(row.realized_pnl) if row.realized_pnl else 0,
            "trades_count": row.trades_count or 0,
            "created_at": row.created_at.isoformat() if row.created_at else None,
            "execution_mode": row.execution_mode
        })

    return {
        "strategies": strategies,
        "count": len(strategies),
        "execution_mode": current_mode,
        "message": f"Showing {len(strategies)} positions for {current_mode} mode"
    }


@app.delete("/api/paper-strategies/{id}")
def delete_paper_strategy(id: int, db: Session = Depends(get_db)):
    """Delete a paper strategy by ID (undeploy)"""
    try:
        # Delete the paper strategy
        result = db.execute(text("""
            DELETE FROM consumption.portfolio_positions_current WHERE id = :id
        """), {"id": id})
        
        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="Strategy not found")
        
        db.commit()
        return {"success": True, "message": "Strategy undeployed"}
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting paper strategy {id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/strategies/{strategy_id}/score")
def get_strategy_score(strategy_id: str, db: Session = Depends(get_db)):
    """Get dynamic score (0-100) for a strategy based on current signals"""
    try:
        # Get strategy from registry
        strategy = db.query(StrategyRegistry).filter(StrategyRegistry.strategy_id == strategy_id).first()
        
        if not strategy:
            raise HTTPException(status_code=404, detail=f"Strategy {strategy_id} not found")
        
        # Get backtest data for this strategy
        backtest = safe_query_one(db, """
            SELECT win_rate, profit_factor, sharpe_ratio, max_drawdown_pct
            FROM consumption.Strategies_Backtest_Results
            WHERE strategy_id = :sid
            LIMIT 1
        """, {"sid": strategy_id}, label="strategy_score_backtest")
        
        # Get recent trade performance
        trades = db.execute(text("""
            SELECT 
                COUNT(*) as total_trades,
                SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END) as winning_trades,
                AVG(pnl) as avg_pnl,
                MAX(executed_at) as last_trade
            FROM gold.trade_executions
            WHERE strategy_id = :sid AND executed_at > NOW() - INTERVAL '30 days'
        """), {"sid": strategy_id}).fetchone()
        
        # Calculate dynamic score (0-100)
        win_rate = float(backtest.win_rate if backtest and backtest.win_rate else (strategy.win_rate_oos if strategy.win_rate_oos is not None else 0.5))
        profit_factor = float(backtest.profit_factor if backtest and backtest.profit_factor else 1.5)
        
        base_wr = win_rate * 100  # 0-100
        base_pf = min(3, profit_factor or 1.5) * 10  # 0-30
        
        # Live performance adjustment
        live_score = 50  # neutral
        if trades and trades.total_trades > 0:
            live_wr = (trades.winning_trades / trades.total_trades) * 100
            live_score = min(100, live_wr * 0.8 + 20)
        
        # Combine scores
        final_score = min(100, max(0, int((base_wr * 0.3) + (base_pf * 0.3) + (live_score * 0.4))))
        
        # Determine trend
        trend = "NEUTRAL"
        if trades and trades.last_trade:
            days_since = (datetime.datetime.now() - trades.last_trade).days
            if days_since < 1:
                trend = "ACTIVE"
            elif days_since < 3:
                trend = "WARM"
            else:
                trend = "COLD"
        
        return {
            "strategy_id": strategy_id,
            "score": final_score,
            "trend": trend,
            "components": {
                "backtest_win_rate": round(base_wr, 1),
                "profit_factor": round(profit_factor or 1.5, 2),
                "recent_performance": round(live_score, 1)
            },
            "last_updated": datetime.datetime.now().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting score for {strategy_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/strategies/{strategy_id}/signals")
def get_strategy_signals(strategy_id: str, db: Session = Depends(get_db)):
    """Get active buy/sell signals for a strategy"""
    try:
        # Get strategy from registry
        strategy = db.query(StrategyRegistry).filter(StrategyRegistry.strategy_id == strategy_id).first()
        
        if not strategy:
            raise HTTPException(status_code=404, detail=f"Strategy {strategy_id} not found")
        
        # Get deployed tickers for this strategy
        positions = db.execute(text("""
            SELECT ticker, entry_price, current_price, unrealized_pnl, realized_pnl
            FROM consumption.portfolio_positions_current
            WHERE strategy_id = :sid AND status = 'ACTIVE'
        """), {"sid": strategy_id}).fetchall()
        
        buy_signals = []
        sell_signals = []
        
        # Parse entry/exit logic from strategy
        entry_logic = strategy.signal_logic or ""
        exit_logic = strategy.exit_logic or ""
        
        # Generate signals based on position status
        for pos in positions:
            ticker = pos.ticker
            
            # Check for sell signals first (risk management)
            if pos.unrealized_pnl and pos.unrealized_pnl < -500:
                sell_signals.append({
                    "ticker": ticker,
                    "signal": "STOP_LOSS",
                    "criteria": f"Unrealized P&L ${pos.unrealized_pnl:.0f}",
                    "severity": "HIGH",
                    "timestamp": datetime.datetime.now().isoformat()
                })
            
            if pos.realized_pnl and pos.realized_pnl > 1000:
                buy_signals.append({
                    "ticker": ticker,
                    "signal": "PROFIT_TAKEN",
                    "criteria": f"Realized P&L ${pos.realized_pnl:.0f}",
                    "confidence": 80,
                    "timestamp": datetime.datetime.now().isoformat()
                })
            
            # Default entry signal for active positions
            if pos.entry_price:
                buy_signals.append({
                    "ticker": ticker,
                    "signal": "POSITION_ACTIVE",
                    "criteria": f"Entry @ ${pos.entry_price:.2f}" if pos.entry_price else "Deployed",
                    "confidence": min(95, 60 + (float(strategy.win_rate_oos) * 40 if strategy.win_rate_oos is not None else 0.5 * 40)),
                    "timestamp": datetime.datetime.now().isoformat()
                })
        
        # Add strategy-level signals from logic
        if "SMA" in entry_logic.upper():
            buy_signals.append({
                "ticker": "ALL",
                "signal": "GOLDEN_CROSS",
                "criteria": "SMA 50/200 Bullish",
                "confidence": 75,
                "timestamp": datetime.datetime.now().isoformat()
            })
        
        if "RSI" in entry_logic.upper():
            buy_signals.append({
                "ticker": "ALL", 
                "signal": "RSI_OVERSOLD",
                "criteria": "RSI < 30 Entry",
                "confidence": 70,
                "timestamp": datetime.datetime.now().isoformat()
            })
        
        # Calculate strategy-level signal
        high_score_count = len([s for s in buy_signals if s.get("confidence", 0) >= 70])
        total_signals = len(buy_signals) + len(sell_signals)
        
        if high_score_count >= 3:
            strategy_signal = "BUY"
        elif len(sell_signals) > 0:
            strategy_signal = "SELL"
        else:
            strategy_signal = "HOLD"
        
        # Get top tickers by confidence
        top_tickers = [s["ticker"] for s in sorted(buy_signals, key=lambda x: x.get("confidence", 0), reverse=True)[:5] if s["ticker"] != "ALL"]
        
        # Sell candidates
        sell_candidates = [s["ticker"] for s in sell_signals[:3]]
        
        return {
            "strategy_id": strategy_id,
            "strategy_level": {
                "signal": strategy_signal,
                "trigger": f"{high_score_count} tickers >70 score" if high_score_count > 0 else "No strong signals"
            },
            "top_tickers": top_tickers,
            "sell_candidates": sell_candidates,
            "buy_signals": buy_signals,
            "sell_signals": sell_signals,
            "signal_count": len(buy_signals) + len(sell_signals),
            "last_updated": datetime.datetime.now().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting signals for {strategy_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/strategies/{strategy_id}/ticker-scores")
def get_strategy_ticker_scores(strategy_id: str, db: Session = Depends(get_db)):
    """Get per-ticker scores and signals from gold.strategy_ticker_scores table"""
    try:
        # Query real ticker scores from DE's table
        rows = db.execute(text("""
            SELECT ticker, score, criteria_met, signal_action 
            FROM gold.strategy_ticker_scores 
            WHERE strategy_id = :sid
            ORDER BY score DESC
        """), {"sid": strategy_id}).fetchall()
        
        if not rows:
            # Fallback: return empty if no scores yet
            return {
                "strategy_id": strategy_id,
                "universe_scores": [],
                "last_updated": datetime.datetime.now().isoformat()
            }
        
        universe_scores = []
        for row in rows:
            # Clean ticker name (remove quotes and brackets)
            ticker_clean = str(row.ticker).replace('[', '').replace(']', '').replace('"', '').replace("'", '').strip()
            
            # Parse criteria_met (could be JSON array or comma-separated string)
            criteria = []
            if row.criteria_met:
                try:
                    import json
                    criteria = json.loads(row.criteria_met) if isinstance(row.criteria_met, str) and row.criteria_met.startswith('[') else [str(row.criteria_met)]
                except:
                    criteria = [str(row.criteria_met)]
            
            universe_scores.append({
                "ticker": ticker_clean,
                "score": int(row.score) if row.score else 50,
                "signal": row.signal_action or "HOLD",
                "criteria": criteria[:3]
            })
        
        return {
            "strategy_id": strategy_id,
            "universe_scores": universe_scores,
            "last_updated": datetime.datetime.now().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting ticker scores for {strategy_id}: {e}")
        # Return empty on error rather than crash
        return {
            "strategy_id": strategy_id,
            "universe_scores": [],
            "error": str(e),
            "last_updated": datetime.datetime.now().isoformat()
        }


@app.get("/api/paper-strategies/{strategy_id:path}/daily-pnl")
def get_paper_strategy_daily_pnl(strategy_id: str, days: int = 7, db: Session = Depends(get_db)):
    """Get daily P&L breakdown for a paper strategy - shows actual position data"""
    from datetime import datetime, timedelta

    # First check: Get closed trades (realized P&L) for this strategy
    closed_trades = db.execute(text("""
        SELECT
            DATE(executed_at) as trade_date,
            SUM(pnl) as day_realized,
            COUNT(*) as trade_count
        FROM gold.trade_executions
        WHERE strategy_id = :strategy_id
          AND pnl IS NOT NULL
        GROUP BY DATE(executed_at)
        ORDER BY trade_date DESC
        LIMIT :days
    """), {"strategy_id": strategy_id, "days": days}).fetchall()

    # Second check: Get open positions by entry date (unrealized P&L)
    open_positions = safe_query(db, """
        SELECT
            DATE(entry_date) as entry_date,
            SUM(unrealized_pnl) as day_unrealized,
            COUNT(*) as position_count
        FROM consumption.Portfolio_Positions_Current
        WHERE strategy_id = :strategy_id
          AND side = 'LONG'
        GROUP BY DATE(entry_date)
        ORDER BY entry_date DESC
        LIMIT :days
    """, {"strategy_id": strategy_id, "days": days}, label="strategy_daily_pnl_open")

    # Combine data
    daily_map = {}

    # Add closed trades
    for t in closed_trades:
        if t.trade_date:
            date_str = str(t.trade_date)
            if date_str not in daily_map:
                daily_map[date_str] = {"realized": 0, "unrealized": 0, "trades": 0}
            daily_map[date_str]["realized"] += float(t.day_realized or 0)
            daily_map[date_str]["trades"] += t.trade_count

    # Add open positions
    for p in open_positions:
        if p.entry_date:
            date_str = str(p.entry_date)
            if date_str not in daily_map:
                daily_map[date_str] = {"realized": 0, "unrealized": 0, "trades": 0}
            daily_map[date_str]["unrealized"] += float(p.day_unrealized or 0)

    # If no data at all, return empty
    if not daily_map:
        return {
            "daily": [],
            "summary": {
                "total_realized": 0,
                "total_unrealized": 0,
                "total_pnl": 0,
                "message": "No positions or trades for this strategy"
            }
        }

    # Build sorted daily data
    sorted_dates = sorted(daily_map.keys())
    daily_data = []
    total_realized = 0
    total_unrealized = 0

    for date_str in sorted_dates:
        data = daily_map[date_str]
        daily_data.append({
            "date": date_str,
            "realized_pnl": round(data["realized"], 2),
            "unrealized_pnl": round(data["unrealized"], 2),
            "total_pnl": round(data["realized"] + data["unrealized"], 2),
            "trades": data["trades"]
        })
        total_realized += data["realized"]
        total_unrealized += data["unrealized"]

    return {
        "daily": daily_data,
        "summary": {
            "total_realized": round(total_realized, 2),
            "total_unrealized": round(total_unrealized, 2),
            "total_pnl": round(total_realized + total_unrealized, 2),
            "days_with_activity": len(daily_data)
        }
    }


@app.post("/api/strategies/{strategy_id:path}/deactivate")
def deactivate_strategy(strategy_id: str, request: Request, db: Session = Depends(get_db)):
    """
    Deactivate a strategy with two options:
    - action='close': Close all positions and deactivate
    - action='keep': Just deactivate, keep positions open
    """
    try:
        body = request.json()
        action = body.get('action', 'keep')  # 'close' or 'keep'
    except:
        action = 'keep'

    # Get all positions for this strategy
    positions = db.execute(text("""
        SELECT id, ticker, invested_capital, status, mode
        FROM consumption.portfolio_positions_current
        WHERE strategy_id = :strategy_id
    """), {"strategy_id": strategy_id}).fetchall()

    if not positions:
        raise HTTPException(status_code=404, detail=f"No positions found for strategy {strategy_id}")

    positions_closed = 0

    for pos in positions:
        if action == 'close' and pos.invested_capital > 0:
            # Close the position - mark as closed
            db.execute(text("""
                UPDATE consumption.portfolio_positions_current
                SET
                    status = 'CLOSED',
                    realized_pnl = realized_pnl + unrealized_pnl,
                    unrealized_pnl = 0,
                    invested_capital = 0,
                    available_capital = capital,
                    updated_at = NOW()
                WHERE id = :id
            """), {"id": pos.id})
            positions_closed += 1

            # If IBKR order exists, cancel it
            if pos.status == 'ACTIVE' and pos.mode in ['PAPER_TRADING', 'LIVE_TRADING']:
                try:
                    # Cancel any open orders for this position
                    db.execute(text("""
                        UPDATE gold.ib_orders
                        SET status = 'CANCELLED', updated_at = NOW()
                        WHERE paper_strategy_id = :id AND status IN ('PENDING', 'SUBMITTED')
                    """), {"id": pos.id})
                except:
                    pass
        else:
            # Just mark as inactive/paused but keep position
            db.execute(text("""
                UPDATE consumption.portfolio_positions_current
                SET
                    status = 'PAUSED',
                    updated_at = NOW()
                WHERE id = :id
            """), {"id": pos.id})

    # Mark strategy as inactive in strategy_definitions
    db.execute(text("""
        UPDATE gold.strategy_registry
        SET
            is_active = FALSE,
            updated_at = NOW()
        WHERE strategy_id = :strategy_id
    """), {"strategy_id": strategy_id})

    db.commit()

    return {
        "success": True,
        "strategy_id": strategy_id,
        "action": action,
        "positions_affected": len(positions),
        "positions_closed": positions_closed if action == 'close' else 0
    }


@app.get("/api/strategies/{strategy_id:path}/capital")
def get_strategy_capital(strategy_id: str, db: Session = Depends(get_db)):
    """Get capital allocation for a strategy"""
    result = db.execute(text("""
        SELECT
            strategy_id,
            name,
            assigned_capital,
            in_market_capital
        FROM gold.strategy_registry
        WHERE strategy_id = :strategy_id 
    """), {"strategy_id": strategy_id}).fetchone()

    if not result:
        raise HTTPException(status_code=404, detail=f"Strategy {strategy_id} not found")

    # Calculate total in-market across all positions
    in_market = db.execute(text("""
        SELECT COALESCE(SUM(invested_capital), 0)
        FROM consumption.portfolio_positions_current
        WHERE strategy_id = :strategy_id
    """), {"strategy_id": strategy_id}).scalar() or 0

    return {
        "strategy_id": result.strategy_id,
        "name": result.name,
        "assigned_capital": float(result.assigned_capital) if result.assigned_capital else 100000,
        "in_market_capital": float(in_market),
        "available_for_buying": max(0, float(result.assigned_capital or 100000) - float(in_market)),
        "capacity_millions": 100
    }


@app.post("/api/strategies/{strategy_id:path}/capital")
def update_strategy_capital(strategy_id: str, payload: dict, db: Session = Depends(get_db)):
    """Update assigned capital for a strategy"""
    assigned_capital = payload.get("assigned_capital")

    if assigned_capital is None or assigned_capital < 0:
        raise HTTPException(status_code=400, detail="assigned_capital must be >= 0")

    # Check strategy exists
    result = db.execute(text("""
        SELECT strategy_id FROM gold.strategy_registry
        WHERE strategy_id = :strategy_id 
    """), {"strategy_id": strategy_id}).fetchone()

    if not result:
        raise HTTPException(status_code=404, detail=f"Strategy {strategy_id} not found")

    # Update assigned capital
    db.execute(text("""
        UPDATE gold.strategy_registry
        SET assigned_capital = :capital,
            updated_at = NOW()
        WHERE strategy_id = :strategy_id
    """), {"strategy_id": strategy_id, "capital": assigned_capital})

    db.commit()

    return {
        "success": True,
        "strategy_id": strategy_id,
        "assigned_capital": assigned_capital,
        "message": f"Capital assigned: ${assigned_capital:,.2f}"
    }


@app.post("/api/strategies/{strategy_id:path}/can-buy")
def can_strategy_buy(strategy_id: str, payload: dict, db: Session = Depends(get_db)):
    """Check if strategy can buy (in-market < assigned)"""
    proposed_investment = payload.get("amount", 0)

    # Get assigned capital
    result = db.execute(text("""
        SELECT assigned_capital FROM gold.strategy_registry
        WHERE strategy_id = :strategy_id
    """), {"strategy_id": strategy_id}).fetchone()

    if not result:
        raise HTTPException(status_code=404, detail="Strategy not found")

    assigned = float(result.assigned_capital or 100000)

    # Get current in-market
    in_market = db.execute(text("""
        SELECT COALESCE(SUM(invested_capital), 0)
        FROM consumption.portfolio_positions_current
        WHERE strategy_id = :strategy_id
    """), {"strategy_id": strategy_id}).scalar() or 0

    available = assigned - in_market
    can_buy = available >= proposed_investment

    return {
        "can_buy": can_buy,
        "assigned_capital": assigned,
        "in_market_capital": float(in_market),
        "available_for_buying": available,
        "proposed_investment": proposed_investment,
        "reason": None if can_buy else f"Only ${available:,.2f} available (assigned: ${assigned:,.2f})"
    }


# --- GLOBAL EXECUTION MODE ---

# Cache for IBKR account balance (refresh every 5 minutes)
_ibkr_balance_cache = {"data": None, "timestamp": None}

@app.get("/api/execution/global-mode")
def get_global_execution_mode(db: Session = Depends(get_db)):
    """
    Get the global platform execution mode and account balance info.
    Returns mode, capital source, and available balance.
    """
    import time

    # Get current mode
    mode_result = db.execute(text("""
        SELECT value FROM gold.platform_settings
        WHERE key = 'global_execution_mode'
    """)).fetchone()

    current_mode = mode_result.value if mode_result else 'SIMULATION'

    # Get simulation capital config
    sim_capital = db.execute(text("""
        SELECT value FROM gold.platform_settings
        WHERE key = 'simulation_capital'
    """)).fetchone()

    sim_amount = float(sim_capital.value) if sim_capital else 100000

    # Calculate simulation capital usage (only for SIMULATION mode)
    sim_used = 0
    sim_positions = 0
    if current_mode == "SIMULATION":
        sim_stats = db.execute(text("""
            SELECT
                COALESCE(SUM(capital), 0) as total_allocated,
                COUNT(*) as position_count
            FROM consumption.portfolio_positions_current
            WHERE status = 'ACTIVE'
        """)).fetchone()
        sim_used = float(sim_stats.total_allocated) if sim_stats else 0
        sim_positions = int(sim_stats.position_count) if sim_stats else 0

    response = {
        "execution_mode": current_mode,
        "available_modes": ["SIMULATION", "PAPER_TRADING", "LIVE_TRADING"],
        "risk_level": {
            "SIMULATION": "ZERO",
            "PAPER_TRADING": "LOW",
            "LIVE_TRADING": "HIGH"
        }.get(current_mode, "UNKNOWN"),
        "simulation_capital": sim_amount,
        "simulation_used": sim_used,
        "simulation_available": sim_amount - sim_used,
        "simulation_positions": sim_positions
    }

    # Try to get IBKR account balance for paper/live modes (with caching)
    if current_mode in ["PAPER_TRADING", "LIVE_TRADING"]:
        try:
            # Import IBKR service
            from app.services.ib_service import ib_quant_service

            # Check cache first (5 minute TTL)
            cache_ttl = 300  # 5 minutes
            now = time.time()

            if _ibkr_balance_cache["data"] and _ibkr_balance_cache["timestamp"] and \
               (now - _ibkr_balance_cache["timestamp"]) < cache_ttl:
                # Use cached data
                cached = _ibkr_balance_cache["data"]
                response.update(cached)
                response["cached"] = True
            else:
                # Fetch fresh data - just check connection status quickly
                try:
                    tws_status = ib_quant_service.get_status()

                    if tws_status.get("is_connected"):
                        account_info = ib_quant_service.get_account_summary()

                        if account_info:
                            # Currency-labeled contract (t_22dee93d) — mirrors
                            # routes/execution.py global-mode. NOTE: this handler
                            # is shadowed by the execution router (registered
                            # first); kept consistent so it can never resurrect
                            # the HKD-as-USD mislabel.
                            ibkr_data = {
                                "ibkr_connected": True,
                                "account_currency": account_info.get("base_currency"),
                                "account_balance": account_info.get("available_funds"),
                                "account_balance_currency": account_info.get("available_funds_currency"),
                                "account_balance_usd": account_info.get("available_funds_usd"),
                                "net_liquidation": account_info.get("net_liquidation"),
                                "net_liquidation_currency": account_info.get("net_liquidation_currency"),
                                "net_liquidation_usd": account_info.get("net_liquidation_usd"),
                                "buying_power": account_info.get("buying_power"),
                                "buying_power_currency": account_info.get("buying_power_currency"),
                                "buying_power_usd": account_info.get("buying_power_usd"),
                                "excess_liquidity": account_info.get("excess_liquidity"),
                                "excess_liquidity_currency": account_info.get("excess_liquidity_currency"),
                                "excess_liquidity_usd": account_info.get("excess_liquidity_usd"),
                                "cash_hkd": account_info.get("cash_hkd"),
                                "cash_usd": account_info.get("cash_usd"),
                                "fx": account_info.get("fx"),
                                "fx_error": account_info.get("fx_error"),
                                "account": account_info.get("account", "Unknown"),
                                "account_type": "PAPER" if current_mode == "PAPER_TRADING" else "LIVE"
                            }

                            # Update cache
                            _ibkr_balance_cache["data"] = ibkr_data
                            _ibkr_balance_cache["timestamp"] = now
                            response.update(ibkr_data)
                            response["cached"] = False
                        else:
                            response["ibkr_connected"] = True
                            response["account_balance"] = 0
                            response["account_currency"] = "USD"
                            response["warning"] = "Connected but could not fetch account details"
                    else:
                        response["ibkr_connected"] = False
                        response["account_balance"] = 0
                        response["account_currency"] = "USD"
                        response["warning"] = "TWS not connected"
                except Exception as ibkr_err:
                    response["ibkr_connected"] = False
                    response["account_balance"] = 0
                    response["account_currency"] = "USD"
                    response["warning"] = f"IBKR check failed: {str(ibkr_err)}"

        except Exception as e:
            # Don't expose internal errors to frontend for IBKR checks
            response["ibkr_connected"] = False
            response["account_balance"] = 0
            response["account_currency"] = "USD"

    return response


@app.post("/api/execution/global-mode")
def set_global_execution_mode(payload: dict, db: Session = Depends(get_db)):
    """
    Set the global platform execution mode.
    Modes: SIMULATION, PAPER_TRADING, LIVE_TRADING
    """
    mode = payload.get("execution_mode", "SIMULATION")
    sim_capital = payload.get("simulation_capital")

    if mode not in ["SIMULATION", "PAPER_TRADING", "LIVE_TRADING"]:
        raise HTTPException(status_code=400, detail="Invalid mode. Use SIMULATION, PAPER_TRADING, or LIVE_TRADING")

    # Update mode in database
    db.execute(text("""
        INSERT INTO gold.platform_settings (key, value, updated_at)
        VALUES ('global_execution_mode', :mode, NOW())
        ON CONFLICT (key) DO UPDATE SET
            value = EXCLUDED.value,
            updated_at = NOW()
    """), {"mode": mode})

    # Update simulation capital if provided
    if sim_capital is not None and mode == "SIMULATION":
        db.execute(text("""
            INSERT INTO gold.platform_settings (key, value, updated_at)
            VALUES ('simulation_capital', :capital::text, NOW())
            ON CONFLICT (key) DO UPDATE SET
                value = EXCLUDED.value,
                updated_at = NOW()
        """), {"capital": float(sim_capital)})

    db.commit()

    event_bus.publish_sync("global_mode_change", {"mode": mode})

    # Get updated state
    return get_global_execution_mode(db)


@app.post("/api/execution/halt")
def halt_all_live(payload: dict = None, db: Session = Depends(get_db)):
    """Emergency kill switch — demote ALL live strategies to PAPER per-strategy.
    Keeps PAPER/SIM strategies running so the quant can still observe signals,
    but no real-money orders fire.

    Requires confirmation_phrase = "HALT LIVE" in the payload.

    Note (2026-08-25): no longer flips gold.platform_settings.global_execution_mode —
    the global mode concept was removed from the UI; each strategy's own
    execution_mode is the truth (4-book lifecycle).
    """
    phrase = (payload or {}).get("confirmation_phrase", "")
    if phrase != "HALT LIVE":
        raise HTTPException(status_code=400,
            detail="Kill switch requires confirmation_phrase = 'HALT LIVE'")

    # 1. Count and demote LIVE strategies
    affected = db.execute(text("""
        UPDATE gold.strategy_registry
        SET execution_mode = 'PAPER', updated_at = NOW()
        WHERE execution_mode = 'LIVE'
        RETURNING strategy_id
    """)).fetchall()

    affected_ids = [r.strategy_id for r in affected]
    db.commit()

    # 2. Audit
    _audit(db, "kill_switch.fire", None, {
        "affected_strategies": affected_ids,
        "count": len(affected_ids),
    })

    logger.warning(f"KILL SWITCH activated — {len(affected_ids)} strategies demoted to PAPER")

    event_bus.publish_sync("kill_switch", {
        "halted": len(affected_ids),
        "strategy_ids": affected_ids,
    })

    return {
        "success": True,
        "halted": len(affected_ids),
        "strategy_ids": affected_ids,
        "message": f"Kill switch activated. {len(affected_ids)} LIVE strategies demoted to PAPER_TRADING.",
    }


# NOTE (2026-08-25): /api/ib/place-order and /api/positions/sync-to-ibkr are
# served exclusively by app/routes/ibkr.py (registered via include_router before
# these duplicates). The shadowed copies that lived here were removed as part of
# the per-book routing change (book=sim|paper|uat|live + order_ref tagging).


@app.post("/api/simulation/reset")
def reset_simulation(db: Session = Depends(get_db)):
    """
    Reset all simulation data. Deletes all paper strategies and trade history.
    Only works in SIMULATION mode.
    """
    import time

    # Get current execution mode
    mode_result = db.execute(text("""
        SELECT value FROM gold.platform_settings
        WHERE key = 'global_execution_mode'
    """)).fetchone()

    current_mode = mode_result.value if mode_result else 'SIMULATION'

    if current_mode != "SIMULATION":
        raise HTTPException(
            status_code=400,
            detail=f"Cannot reset in {current_mode} mode. Switch to SIMULATION first."
        )

    try:
        # Count before deletion for reporting
        count_result = db.execute(text("""
            SELECT COUNT(*) as cnt FROM consumption.portfolio_positions_current
        """)).fetchone()
        positions_count = count_result.cnt if count_result else 0

        trades_result = db.execute(text("""
            SELECT COUNT(*) as cnt FROM gold.trade_executions
        """)).fetchone()
        trades_count = trades_result.cnt if trades_result else 0

        # Delete all paper strategies
        db.execute(text("""
            DELETE FROM consumption.portfolio_positions_current
        """))

        # Delete all trade executions
        db.execute(text("""
            DELETE FROM gold.trade_executions
        """))

        # Also delete from gold.positions if exists
        try:
            db.execute(text("""
                DELETE FROM gold.positions WHERE strategy_id IS NOT NULL
            """))
        except:
            pass  # Table might not exist or have different structure

        # Delete from consumption tables (safer than TRUNCATE in transactions)
        try:
            db.execute(text("""
                DELETE FROM consumption.Portfolio_Positions_Current
            """))
        except Exception as e:
            logger.warning(f"Could not clear Portfolio_Positions_Current: {e}")

        try:
            db.execute(text("""
                DELETE FROM gold.trade_executions WHERE strategy_id IN (SELECT strategy_id FROM consumption.portfolio_positions_current)
            """))
        except Exception as e:
            logger.warning(f"Could not clear trade_executions: {e}")

        # NOTE: Performance_Trades_History dropped - no longer need to clear

        # NOTE: Performance_Portfolio_Summary dropped - no longer exists

        # Reset simulation capital to default
        db.execute(text("""
            INSERT INTO gold.platform_settings (key, value, updated_at)
            VALUES ('simulation_capital', '100000', NOW())
            ON CONFLICT (key) DO UPDATE SET
                value = EXCLUDED.value,
                updated_at = NOW()
        """))

        # Also reset simulation used/available tracking
        db.execute(text("""
            INSERT INTO gold.platform_settings (key, value, updated_at)
            VALUES ('simulation_used', '0', NOW())
            ON CONFLICT (key) DO UPDATE SET
                value = EXCLUDED.value,
                updated_at = NOW()
        """))

        db.execute(text("""
            INSERT INTO gold.platform_settings (key, value, updated_at)
            VALUES ('simulation_positions', '0', NOW())
            ON CONFLICT (key) DO UPDATE SET
                value = EXCLUDED.value,
                updated_at = NOW()
        """))

        db.commit()

        return {
            "success": True,
            "message": f"Simulation reset complete. Deleted {positions_count} positions and {trades_count} trades. Capital reset to $100,000.",
            "positions_deleted": positions_count,
            "trades_deleted": trades_count,
            "simulation_capital_reset": 100000
        }

    except Exception as e:
        db.rollback()
        logger.error(f"Error resetting simulation: {e}")
        raise HTTPException(status_code=500, detail=f"Reset failed: {str(e)}")


# --- CASH POSITION MANAGEMENT ---

@app.post("/api/positions/close-fx-cash")
def close_fx_cash_positions(payload: dict, db: Session = Depends(get_db)):
    """
    Close FX cash positions and convert to base currency (HKD).
    Expects: { "positions": { "AUD": -215086.00, "CAD": 226465.89, ... } }
    """
    positions = payload.get("positions", {})
    executed = []
    failed = []

    for currency, amount in positions.items():
        currency = currency.upper()
        if abs(amount) < 100:
            continue

        try:
            # Determine action
            if amount > 0:
                action = "SELL"  # Long position - sell to close
            else:
                action = "BUY"   # Short position - buy to close

            quantity = abs(amount)
            pair = f"{currency}HKD"

            # Log the intended trade
            db.execute(text("""
                INSERT INTO gold.trade_executions
                (strategy_id, ticker, execution_mode, order_type, side, quantity, status, executed_at)
                VALUES ('cash_closure', :ticker, 'PAPER_TRADING', 'FX', :side, :qty, 'PENDING', NOW())
            """), {
                "ticker": pair,
                "side": action,
                "qty": quantity
            })

            db.commit()

            executed.append({
                "currency": currency,
                "action": action,
                "pair": pair,
                "quantity": quantity,
                "original_amount": amount
            })

        except Exception as e:
            failed.append({
                "currency": currency,
                "error": str(e)
            })

    return {
        "success": True,
        "executed_count": len(executed),
        "failed_count": len(failed),
        "executed": executed,
        "failed": failed,
        "message": f"Submitted {len(executed)} FX closure orders to convert to HKD"
    }


# --- STRATEGY CAPITAL POOL MANAGEMENT ---

@app.get("/api/strategies/{strategy_id:path}/capital-pool")
def get_strategy_capital_pool(strategy_id: str, db: Session = Depends(get_db)):
    """Get capital pool status for a strategy - pool shared across universe assets"""
    strategy = db.execute(text("""
        SELECT strategy_id, name, assigned_capital
        FROM gold.strategy_registry WHERE strategy_id = :strategy_id
    """), {"strategy_id": strategy_id}).fetchone()

    if not strategy:
        raise HTTPException(status_code=404, detail="Strategy not found")

    pool_usage = db.execute(text("""
        SELECT COALESCE(SUM(capital), 0) as used_capital, COUNT(*) as active_positions
        FROM consumption.portfolio_positions_current WHERE strategy_id = :strategy_id AND status = 'ACTIVE'
    """), {"strategy_id": strategy_id}).fetchone()

    total_assigned = float(strategy.assigned_capital) if strategy.assigned_capital else 100000
    used = float(pool_usage.used_capital) if pool_usage else 0
    available = total_assigned - used
    trade_size = total_assigned * 0.25

    return {
        "strategy_id": strategy.strategy_id, "strategy_name": strategy.name,
        "total_assigned": total_assigned, "used": used, "available": available,
        "trade_size": trade_size, "active_positions": pool_usage.active_positions if pool_usage else 0,
        "max_positions": 4, "can_trade": available >= trade_size,
        "usage_pct": (used / total_assigned * 100) if total_assigned > 0 else 0
    }


@app.post("/api/strategies/{strategy_id:path}/capital-pool")
def update_strategy_capital_pool(strategy_id: str, payload: dict, db: Session = Depends(get_db)):
    """Update the total capital pool for a strategy"""
    new_total = payload.get("total_assigned", 100000)
    result = db.execute(text("""
        UPDATE gold.strategy_registry SET assigned_capital = :total, updated_at = NOW()
        WHERE strategy_id = :strategy_id RETURNING strategy_id, name, assigned_capital
    """), {"strategy_id": strategy_id, "total": new_total}).fetchone()

    if not result:
        raise HTTPException(status_code=404, detail="Strategy not found")
    db.commit()
    return {"success": True, "strategy_id": result.strategy_id, "total_assigned": result.assigned_capital}


@app.post("/api/strategies/deploy-with-pool")
def deploy_strategy_with_pool(payload: dict, db: Session = Depends(get_db)):
    """Deploy strategy with capital pool - 25% per trade, max 4 positions"""
    strategy_id = payload.get("strategy_id")
    tickers = payload.get("tickers", [])
    total_pool = payload.get("total_pool", 100000)
    trade_size_pct = payload.get("trade_size_pct", 0.25)

    if not strategy_id or not tickers:
        raise HTTPException(status_code=400, detail="strategy_id and tickers required")

    # Get current execution mode
    mode_result = safe_query_one(db, """
        SELECT value FROM gold.platform_settings
        WHERE key = 'global_execution_mode'
    """, label="deploy_pool_mode")
    current_mode = mode_result.value if mode_result else 'SIMULATION'

    strategy = safe_query_one(db, """
        SELECT strategy_id, name, execution_mode FROM gold.strategy_registry WHERE strategy_id = :sid
    """, {"sid": strategy_id}, label="deploy_pool_strategy")
    if not strategy:
        raise HTTPException(status_code=404, detail=f"Strategy {strategy_id} not found")

    # Used capital is read the same way /api/strategies/{id}/capital-pool does:
    # post-sync consumption rows for the strategy, no execution_mode filter.
    pool_status = safe_query_one(db, """
        SELECT COALESCE(SUM(capital), 0) as used FROM consumption.portfolio_positions_current
        WHERE strategy_id = :strategy_id AND status = 'ACTIVE'
    """, {"strategy_id": strategy_id}, label="deploy_pool_status")

    current_used = float(pool_status.used) if pool_status else 0
    available = total_pool - current_used
    trade_size = total_pool * trade_size_pct

    if available < trade_size:
        return {"success": False, "error": "Capital pool exhausted", "available": available, "required": trade_size}

    # For PAPER/SIMULATION registry strategies the paper ledger
    # (gold.paper_trades_synthetic, written by the ETL rebalancer and synced
    # into consumption.portfolio_positions_current) is the source of truth.
    # Do NOT write placeholder capital rows here.
    registry_api_mode = registry_to_api_mode(getattr(strategy, "execution_mode", None))
    if registry_api_mode in ("PAPER_TRADING", "SIMULATION"):
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
                "No placeholder rows written."
            ),
        }

    created = []
    for ticker in tickers:
        if available < trade_size:
            break
        try:
            db.execute(text("""
                INSERT INTO consumption.portfolio_positions_current (strategy_id, ticker, capital, status, execution_mode, created_at, updated_at)
                VALUES (:strategy_id, :ticker, :capital, 'ACTIVE', :mode, NOW(), NOW())
                ON CONFLICT (strategy_id, ticker) DO UPDATE SET
                    status = 'ACTIVE',
                    capital = EXCLUDED.capital,
                    execution_mode = EXCLUDED.execution_mode,
                    updated_at = NOW()
            """), {"strategy_id": strategy_id, "ticker": ticker.upper(), "capital": trade_size, "mode": current_mode})
            available -= trade_size
            created.append(ticker)
        except Exception as e:
            pass

    db.commit()
    return {
        "success": True,
        "positions_created": len(created),
        "tickers": created,
        "pool_remaining": available,
        "execution_mode": current_mode
    }


@app.post("/api/strategies/deploy-auto")
def deploy_strategy_auto(payload: dict, db: Session = Depends(get_db)):
    """
    Auto-deploy strategy with full universe.
    Only deploys tickers that have BUY signals.
    Max 5 positions.
    """
    strategy_id = payload.get("strategy_id")
    total_pool = payload.get("total_pool", 100000)
    trade_size_pct = payload.get("trade_size_pct", 0.25)
    max_positions = payload.get("max_positions", 5)

    if not strategy_id:
        raise HTTPException(status_code=400, detail="strategy_id required")

    # Get current execution mode
    mode_result = safe_query_one(db, """
        SELECT value FROM gold.platform_settings
        WHERE key = 'global_execution_mode'
    """, label="deploy_mode")
    current_mode = mode_result.value if mode_result else 'SIMULATION'

    # Get strategy from registry
    strategy = db.query(StrategyRegistry).filter(
        StrategyRegistry.strategy_id == strategy_id,
        StrategyRegistry.status.in_(['ACTIVE', 'TESTING'])
    ).first()

    if not strategy:
        raise HTTPException(status_code=404, detail=f"Strategy {strategy_id} not found")

    # Parse universe_tickers as an array; filter out CASH placeholder
    raw_universe = strategy.universe_tickers or []
    if isinstance(raw_universe, str):
        raw_universe = [t.strip() for t in raw_universe.split(',') if t.strip()]
    universe = [t for t in raw_universe if t and t.upper() != 'CASH']

    if not universe:
        return {
            "success": False,
            "error": "Strategy has no universe defined",
            "strategy_id": strategy_id
        }

    # Check which tickers in universe have BUY signals
    # NOTE: consumption.Strategies_Signals_Current does not exist — deploy from universe directly
    tickers_with_buy = universe[:max_positions]  # Deploy top N tickers from universe

    if not tickers_with_buy:
        return {
            "success": False,
            "error": "No tickers in universe to deploy",
            "strategy_id": strategy_id,
            "universe_checked": universe,
            "universe_size": len(universe)
        }

    # Check pool availability — same source as /api/strategies/{id}/capital-pool:
    # post-sync consumption rows for the strategy, no execution_mode filter.
    pool_status = safe_query_one(db, """
        SELECT COALESCE(SUM(capital), 0) as used, COUNT(*) as position_count
        FROM consumption.portfolio_positions_current
        WHERE strategy_id = :strategy_id AND status = 'ACTIVE'
    """, {"strategy_id": strategy_id}, label="deploy_pool")

    current_used = float(pool_status.used) if pool_status else 0
    current_positions = int(pool_status.position_count) if pool_status else 0
    available = total_pool - current_used
    trade_size = total_pool * trade_size_pct

    # Respect max positions limit
    positions_remaining = max_positions - current_positions
    if positions_remaining <= 0:
        return {
            "success": False,
            "error": f"Max positions ({max_positions}) already reached",
            "current_positions": current_positions,
            "max_positions": max_positions
        }

    # For PAPER/SIMULATION registry strategies the paper ledger
    # (gold.paper_trades_synthetic, written by the ETL rebalancer and synced
    # into consumption.portfolio_positions_current) is the source of truth.
    # Do NOT write placeholder capital rows here.
    registry_api_mode = registry_to_api_mode(getattr(strategy, "execution_mode", None))
    if registry_api_mode in ("PAPER_TRADING", "SIMULATION"):
        return {
            "success": True,
            "strategy_id": strategy_id,
            "execution_mode": current_mode,
            "positions_created": 0,
            "tickers_deployed": [],
            "tickers_skipped": [],
            "universe_size": len(universe),
            "tickers_with_buy_signal": len(tickers_with_buy),
            "pool_remaining": available,
            "total_pool": total_pool,
            "trade_size": trade_size,
            "note": (
                f"Registry execution_mode is {registry_api_mode}; positions are owned by the "
                "paper ledger (gold.paper_trades_synthetic) and synced into "
                "consumption.portfolio_positions_current by ETL each signal cycle. "
                "No placeholder rows written."
            ),
        }

    # Deploy up to max positions
    created = []
    skipped = []
    for ticker in tickers_with_buy:
        if len(created) >= positions_remaining:
            skipped.append(f"{ticker} (max positions reached)")
            continue
        if available < trade_size:
            skipped.append(f"{ticker} (insufficient capital)")
            continue

        try:
            db.execute(text("""
                INSERT INTO consumption.portfolio_positions_current (strategy_id, ticker, capital, status, execution_mode, created_at, updated_at)
                VALUES (:strategy_id, :ticker, :capital, 'ACTIVE', :mode, NOW(), NOW())
                ON CONFLICT (strategy_id, ticker) DO UPDATE SET
                    status = 'ACTIVE',
                    capital = EXCLUDED.capital,
                    execution_mode = EXCLUDED.execution_mode,
                    updated_at = NOW()
            """), {"strategy_id": strategy_id, "ticker": ticker.upper(), "capital": trade_size, "mode": current_mode})
            available -= trade_size
            created.append(ticker)
        except Exception as e:
            skipped.append(f"{ticker} (error: {str(e)})")

    db.commit()

    return {
        "success": len(created) > 0,
        "strategy_id": strategy_id,
        "execution_mode": current_mode,
        "positions_created": len(created),
        "tickers_deployed": created,
        "tickers_skipped": skipped,
        "universe_size": len(universe),
        "tickers_with_buy_signal": len(tickers_with_buy),
        "pool_remaining": available,
        "total_pool": total_pool,
        "trade_size": trade_size
    }


@app.get("/api/positions/cash-summary")
def get_cash_position_summary(db: Session = Depends(get_db)):
    """Get summary of cash positions that need closing"""
    # Default to the known positions from the request
    positions = {
        "AUD": -215086.00,
        "CAD": 226465.89,
        "CNH": -2272.68,
        "EUR": -312806.00,
        "GBP": -9259.00,
        "NOK": 3226468.43,
        "NZD": -185180.00,
        "USD": -162784.73,
        "HKD": 3343700.43
    }

    # Calculate net FX exposure
    fx_exposure = {k: v for k, v in positions.items() if k != "HKD"}

    # Estimate trades needed
    trades_needed = []
    for currency, amount in fx_exposure.items():
        if abs(amount) >= 100:
            action = "BUY" if amount < 0 else "SELL"
            trades_needed.append({
                "currency": currency,
                "action": action,
                "quantity": abs(amount),
                "pair": f"{currency}HKD",
                "reason": f"Close {currency} position of {amount:,.2f}"
            })

    return {
        "base_currency": "HKD",
        "base_balance": positions.get("HKD", 0),
        "fx_positions": fx_exposure,
        "trades_to_close": trades_needed,
        "total_trades": len(trades_needed),
        "estimated_proceeds_hkd": "Will depend on market rates"
    }


# --- TRADE ALGO RESEARCHER STRATEGIES ---

@app.get("/api/strategies/review-queue")
def get_strategy_review_queue(db: Session = Depends(get_db)):
    """Get strategies awaiting review (TESTING status with GOLDEN or NEAR_GOLDEN priority)"""
    try:
        strategies = db.query(StrategyRegistry).filter(
            StrategyRegistry.status == 'TESTING',
            StrategyRegistry.priority.in_(['GOLDEN', 'NEAR_GOLDEN'])
        ).all()

        result = []
        for s in strategies:
            raw_universe = s.universe_tickers or []
            if isinstance(raw_universe, str):
                raw_universe = [t.strip() for t in raw_universe.split(',') if t.strip()]
            tickers = [t for t in raw_universe if t and t.upper() != 'CASH']
            result.append({
                "id": s.strategy_id,
                "name": s.name,
                "priority": s.priority,
                "status": s.status,
                "version": None,
                "win_rate": float(s.win_rate_oos) if s.win_rate_oos is not None else None,
                "entry_logic": s.signal_logic,
                "exit_logic": s.exit_logic,
                "target_assets": tickers,
            })
        return {"strategies": result, "count": len(result)}
    except Exception as e:
        logger.error(f"Review queue error: {e}")
        return {"strategies": [], "count": 0}


@app.post("/api/strategies/{strategy_id:path}/approve")
def approve_strategy(strategy_id: str, db: Session = Depends(get_db)):
    """Approve a TESTING strategy — sets status to ACTIVE"""
    try:
        strategy = db.query(StrategyRegistry).filter(
            StrategyRegistry.strategy_id == strategy_id
        ).first()
        if not strategy:
            raise HTTPException(status_code=404, detail="Strategy not found")

        strategy.status = 'ACTIVE'
        db.commit()
        return {"success": True, "strategy_id": strategy_id, "new_status": "ACTIVE"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Approve error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/strategies/{strategy_id:path}/reject")
def reject_strategy(strategy_id: str, db: Session = Depends(get_db)):
    """Reject a strategy — sets status to DEPRECATED"""
    try:
        strategy = db.query(StrategyRegistry).filter(
            StrategyRegistry.strategy_id == strategy_id
        ).first()
        if not strategy:
            raise HTTPException(status_code=404, detail="Strategy not found")

        strategy.status = 'DEPRECATED'
        db.commit()
        return {"success": True, "strategy_id": strategy_id, "new_status": "DEPRECATED"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Reject error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/strategies/researcher")
def get_researcher_strategies(asset_class: str = None, priority: str = None, db: Session = Depends(get_db)):
    """Get JT Researcher strategies from strategy_registry with real backtest data"""
    try:
        # Query from StrategyRegistry (canonical source of truth from DE)
        query = db.query(StrategyRegistry)

        # Filter by status - include all statuses for full visibility
        # Allow filtering by specific status if requested
        # Default: show all non-DEPRECATED strategies
        query = query.filter(StrategyRegistry.status != 'DEPRECATED')

        # Filter by priority - default to GOLDEN + NEAR_GOLDEN, or allow all
        if priority and priority != 'ALL':
            query = query.filter(StrategyRegistry.priority == priority)
        else:
            query = query.filter(StrategyRegistry.priority.in_(['GOLDEN', 'NEAR_GOLDEN', 'EXPERIMENTAL']))

        strategies = query.all()

        # Fetch real backtest data from consumption
        backtest_data = {}
        try:
            backtests = db.execute(text("""
                SELECT
                    strategy_id,
                    AVG(win_rate) as win_rate,
                    AVG(profit_factor) as profit_factor,
                    AVG(max_drawdown_pct) as max_drawdown,
                    AVG(sharpe_ratio) as sharpe,
                    SUM(total_trades) as total_trades,
                    AVG(total_return_pct) as total_return
                FROM consumption.Strategies_Backtest_Results
                GROUP BY strategy_id
            """)).fetchall()

            for bt in backtests:
                backtest_data[bt.strategy_id] = {
                    'win_rate': float(bt.win_rate) if bt.win_rate else None,
                    'profit_factor': float(bt.profit_factor) if bt.profit_factor else None,
                    'max_drawdown': float(bt.max_drawdown) if bt.max_drawdown else None,
                    'sharpe': float(bt.sharpe) if bt.sharpe else None,
                    'total_trades': int(bt.total_trades) if bt.total_trades else None,
                    'total_return': float(bt.total_return) if bt.total_return else None
                }
        except Exception as e:
            logger.error(f"Error fetching backtest data: {e}")

        # Fetch yearly backtest returns by strategy
        yearly_backtest_data = {}
        try:
            yearly_bt = db.execute(text("""
                SELECT
                    strategy_id,
                    EXTRACT(YEAR FROM backtest_date) as year,
                    AVG(total_return_pct) as avg_return,
                    SUM(total_trades) as total_trades
                FROM consumption.Strategies_Backtest_Results
                WHERE backtest_date IS NOT NULL
                GROUP BY strategy_id, EXTRACT(YEAR FROM backtest_date)
                ORDER BY strategy_id, year DESC
            """)).fetchall()

            for yb in yearly_bt:
                sid = yb.strategy_id
                year = int(yb.year) if yb.year else None
                if sid and year:
                    if sid not in yearly_backtest_data:
                        yearly_backtest_data[sid] = {}
                    yearly_backtest_data[sid][str(year)] = {
                        'return_pct': float(yb.avg_return) if yb.avg_return else 0,
                        'trades': int(yb.total_trades) if yb.total_trades else 0
                    }
        except Exception as e:
            logger.error(f"Error fetching yearly backtest data: {e}")

        # Fetch top 5 signals by confidence for each strategy
        top_signals_data = {}
        try:
            top_signals = db.execute(text("""
                SELECT DISTINCT ON (strategy_id)
                    strategy_id,
                    ticker,
                    signal,
                    confidence_score,
                    signal_strength
                FROM consumption.Strategies_Signals_Current
                ORDER BY strategy_id, confidence_score DESC NULLS LAST
            """)).fetchall()

            for sig in top_signals:
                if sig.strategy_id not in top_signals_data:
                    top_signals_data[sig.strategy_id] = []
                top_signals_data[sig.strategy_id].append({
                    'ticker': sig.ticker,
                    'signal': sig.signal,
                    'confidence': float(sig.confidence_score) if sig.confidence_score else None,
                    'strength': float(sig.signal_strength) if sig.signal_strength else None
                })
        except Exception as e:
            logger.error(f"Error fetching top signals: {e}")

        result = []
        for s in strategies:
            # Parse universe_tickers as an array; filter out CASH placeholder
            raw_universe = s.universe_tickers or []
            if isinstance(raw_universe, str):
                raw_universe = [t.strip() for t in raw_universe.split(',') if t.strip()]
            tickers = [t for t in raw_universe if t and t.upper() != 'CASH']

            # Get backtest data for this strategy
            bt = backtest_data.get(s.strategy_id, {})

            # Compute win_rate from registry or backtest
            win_rate = bt.get('win_rate') or (float(s.win_rate_oos) if s.win_rate_oos is not None else None)
            total_return = bt.get('total_return')
            total_trades = bt.get('total_trades')

            # Get top 5 signals by confidence for this strategy
            strategy_signals = top_signals_data.get(s.strategy_id, [])
            # If no signals, use universe tickers as fallback
            top_tickers = []
            if strategy_signals:
                top_tickers = strategy_signals[:5]
            else:
                top_tickers = [{'ticker': t, 'signal': 'HOLD', 'confidence': None, 'strength': None} for t in tickers[:5]]

            # Get yearly backtest data for this strategy
            yearly_data = yearly_backtest_data.get(s.strategy_id, {})
            # Get current year
            current_year = 2026  # Hardcoded for now, can be dynamic

            result.append({
                "strategy_id": s.strategy_id,
                "strategy_name": s.name or s.strategy_id,
                "name": s.name or s.strategy_id,
                "description": f"{s.priority} strategy" if s.priority else "Strategy",
                "asset_class": "STOCK",
                "direction": "LONG",
                "time_horizon": s.frequency,
                "win_rate": win_rate,
                "returns": total_return,
                "live_trades": total_trades,
                "backtest_win_rate": round((bt.get('win_rate') or 0) * 100, 1) if bt.get('win_rate') else None,
                "live_win_rate": round(win_rate * 100, 1) if win_rate else None,
                "profit_factor": bt.get('profit_factor'),
                "max_drawdown": bt.get('max_drawdown'),
                "sharpe_ratio": bt.get('sharpe'),
                "backtest_trades": total_trades,
                "backtest_return": total_return,
                "universe": tickers,
                "universe_count": len(tickers),
                "max_position_pct": 0.05,
                "venue": "IBKR",
                "status": s.status,
                "priority": s.priority,
                "tier": s.priority,
                "version": None,
                "entry_logic": s.signal_logic,
                "exit_logic": s.exit_logic,
                "top_tickers": top_tickers,
                "yearly_backtest": yearly_data,
                "source": "strategy_registry"
            })

        return {"strategies": result, "count": len(result)}
    except Exception as e:
        logger.error(f"Error fetching from strategy_registry: {e}")
        # Fallback to legacy table for backward compatibility during migration
        return _get_strategies_from_definitions(db, asset_class)


def _get_strategies_from_definitions(db: Session, asset_class: str = None):
    """Fallback - read from gold.strategy_registry when ORM query fails"""
    query = """
        SELECT
            strategy_id as id,
            name,
            description,
            asset_class,
            universe_tickers,
            status,
            sharpe_oos,
            max_drawdown_oos,
            win_rate_oos,
            trade_count_oos,
            frequency,
            execution_mode
        FROM gold.strategy_registry
        WHERE 1=1
    """
    if asset_class:
        query += " AND asset_class = :asset_class"
    query += " ORDER BY sharpe_oos DESC NULLS LAST"

    result = db.execute(text(query), {"asset_class": asset_class} if asset_class else {})

    strategies = []
    for row in result:
        raw_universe = row.universe_tickers or []
        if isinstance(raw_universe, str):
            raw_universe = [t.strip() for t in raw_universe.split(',') if t.strip()]
        tickers = [t for t in raw_universe if t and t.upper() != 'CASH']
        strategies.append({
            "id": row.id,
            "name": row.name,
            "description": row.description,
            "asset_class": row.asset_class,
            "direction": "LONG",
            "time_horizon": row.frequency,
            "sharpe_ratio": float(row.sharpe_oos) if row.sharpe_oos else 0,
            "max_drawdown": float(row.max_drawdown_oos) if row.max_drawdown_oos else 0,
            "win_rate": float(row.win_rate_oos) if row.win_rate_oos else 0,
            "universe": tickers,
            "universe_count": len(tickers),
            "max_position_pct": 0.05,
            "venue": "IBKR",
            "status": row.status,
            "source": "strategy_registry_fallback"
        })

    return {"strategies": strategies, "count": len(strategies)}


@app.get("/api/strategies/compare")
def compare_strategies(ids: str, days: int = 90, db: Session = Depends(get_db)):
    """Compare two or more strategies side-by-side.

    Returns a slim payload (no per-trade rows) suitable for the comparator
    UI: header metadata, BT + live metric snapshots, equity curve, monthly
    returns. `ids` is a comma-separated list, max 6 strategies.
    """
    strategy_ids = [s.strip() for s in ids.split(",") if s.strip()]
    if not strategy_ids:
        raise HTTPException(status_code=400, detail="ids query param required (comma-separated)")
    if len(strategy_ids) > 6:
        raise HTTPException(status_code=400, detail="Compare up to 6 strategies at a time")

    results = []
    for sid in strategy_ids:
        strategy = safe_query_one(db, """
            SELECT strategy_id, name, asset_class, universe_tickers, frequency, execution_mode, status,
                   sharpe_oos, max_drawdown_oos, trade_count_oos, win_rate_oos, conviction_score,
                   assigned_capital, in_market_capital, signal_logic, exit_logic, description,
                   created_at, updated_at, priority
            FROM gold.strategy_registry WHERE strategy_id = :sid
        """, {"sid": sid}, label="cmp_strategy")

        if not strategy:
            results.append({"strategy_id": sid, "found": False})
            continue

        bt = safe_query_one(db, """
            SELECT AVG(win_rate) AS win_rate,
                   AVG(profit_factor) AS profit_factor,
                   AVG(sharpe_ratio) AS sharpe,
                   AVG(max_drawdown_pct) AS max_drawdown,
                   SUM(total_trades) AS total_trades,
                   AVG(total_return_pct) AS total_return
            FROM consumption.Strategies_Backtest_Results
            WHERE strategy_id = :sid
        """, {"sid": sid}, label="cmp_bt")

        live = safe_query_one(db, """
            SELECT COUNT(*) AS total_trades,
                   SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END) AS winners,
                   SUM(CASE WHEN pnl > 0 THEN pnl ELSE 0 END) AS gross_win,
                   SUM(CASE WHEN pnl < 0 THEN -pnl ELSE 0 END) AS gross_loss,
                   COALESCE(SUM(pnl), 0) AS total_pnl
            FROM gold.trade_executions
            WHERE strategy_id = :sid AND pnl IS NOT NULL
        """, {"sid": sid}, label="cmp_live")

        equity_rows = safe_query(db, """
            SELECT DATE(executed_at) AS d, COALESCE(SUM(pnl), 0) AS day_pnl
            FROM gold.trade_executions
            WHERE strategy_id = :sid AND pnl IS NOT NULL
              AND executed_at > NOW() - (:days || ' days')::INTERVAL
            GROUP BY DATE(executed_at) ORDER BY d ASC
        """, {"sid": sid, "days": str(days)}, label="cmp_equity")

        cum = 0.0
        equity_curve = []
        for r in equity_rows:
            cum += float(r.day_pnl or 0)
            equity_curve.append({"date": r.d.isoformat(), "cum_pnl": round(cum, 2)})

        monthly = safe_query(db, """
            SELECT year, month, return_pct
            FROM consumption.Performance_Monthly_Returns
            WHERE strategy_id = :sid
            ORDER BY year DESC, month DESC LIMIT 12
        """, {"sid": sid}, label="cmp_monthly")

        live_total = int(live.total_trades) if live and live.total_trades else 0
        live_pf = (float(live.gross_win) / float(live.gross_loss)) if (live and live.gross_loss and live.gross_loss > 0) else None
        live_wr = (float(live.winners) / live_total) if live_total else None

        results.append({
            "strategy_id": sid,
            "found": True,
            "name": strategy.name or sid,
            "priority": strategy.priority,
            "status": strategy.status,
            "execution_mode": strategy.execution_mode,
            "asset_class": strategy.asset_class,
            "direction": "LONG",
            "metrics": {
                "backtest": {
                    "win_rate":      float(bt.win_rate) if bt and bt.win_rate is not None else None,
                    "profit_factor": float(bt.profit_factor) if bt and bt.profit_factor is not None else None,
                    "sharpe":        float(bt.sharpe) if bt and bt.sharpe is not None else None,
                    "max_drawdown":  float(bt.max_drawdown) if bt and bt.max_drawdown is not None else None,
                    "total_trades":  int(bt.total_trades) if bt and bt.total_trades is not None else None,
                    "total_return":  float(bt.total_return) if bt and bt.total_return is not None else None,
                },
                "live": {
                    "total_trades":  live_total,
                    "win_rate":      round(live_wr, 4) if live_wr is not None else None,
                    "profit_factor": round(live_pf, 3) if live_pf is not None else None,
                    "total_pnl":     float(live.total_pnl or 0) if live else 0.0,
                },
            },
            "equity_curve": equity_curve,
            "monthly_returns": [{"year": int(r.year), "month": int(r.month),
                                 "return": float(r.return_pct or 0)} for r in monthly],
        })

    return {"strategies": results, "count": len(results), "window_days": days}


# NOTE: this route must be declared BEFORE the catch-all
# `/api/strategies/{strategy_id:path}` so that `/evaluation` is matched first.
@app.get("/api/strategies/{strategy_id}/evaluation")
def get_strategy_evaluation(strategy_id: str, days: int = 90, trade_limit: int = 50,
                            book: str = "auto", db: Session = Depends(get_db)):
    """One-shot evaluation payload powering the Strategy Detail page.

    Aggregates: header metadata, backtest metrics, live metrics, monthly returns,
    equity curve (cumulative live PnL), recent trades, recent signals, and a
    backtest-vs-live divergence verdict. Resilient to missing consumption views.

    Also returns `metrics_by_mode` — per-book headline stats (win rate / P&L /
    trade count) for SIM (OOS backtest), PAPER (gold.paper_trades_synthetic),
    UAT (gold.paper_uat_fills) and LIVE (gold.trade_executions) — so the
    detail page can render the 4-mode toggle strip without extra round-trips.
    Fields are NULL when a book has no data — never a fake zero.

    Query parameters:
      days: rolling window for the equity curve (default 90).
      trade_limit: max trade events to return for the ledger (default 50, capped at 1000).
      book: which ledger the live block (live metrics / equity curve / recent
            trades) reads — auto (current deployment mode), paper, or live.
    """
    # ---- Header / metadata -------------------------------------------------
    strategy = safe_query_one(db, """
        SELECT strategy_id, name, asset_class, universe_tickers, frequency, execution_mode, status,
               sharpe_oos, max_drawdown_oos, trade_count_oos, win_rate_oos, profit_factor_oos, returns_oos,
               conviction_score, assigned_capital, in_market_capital, signal_logic, exit_logic, description,
               created_at, updated_at, priority, retirement_reason
        FROM gold.strategy_registry
        WHERE strategy_id = :sid
    """, {"sid": strategy_id}, label="eval_strategy")

    if not strategy:
        raise HTTPException(status_code=404, detail=f"Strategy {strategy_id} not found")

    name = strategy.name or strategy_id
    asset_class = strategy.asset_class or "STOCK"
    direction = "LONG"  # No direction column in registry; default to LONG
    raw_universe = strategy.universe_tickers or []
    if isinstance(raw_universe, str):
        # Defensive: some legacy paths may still return a comma-separated string
        raw_universe = [t.strip() for t in raw_universe.split(',') if t.strip()]
    # CASH is a cash-bucket placeholder, not a tradeable ticker; exclude it from
    # the universe display so the UI never renders CASH as a ticker chip.
    universe = [t for t in raw_universe if t and t.upper() != 'CASH']

    # ---- Backtest metrics --------------------------------------------------
    # Prefer gold.strategy_backtest_runs (IS/OOS metrics keyed by text strategy_id),
    # fall back to registry OOS columns.
    backtest_row = safe_query_one(db, """
        SELECT win_rate_oos, profit_factor_oos, sharpe_oos, max_drawdown_oos,
               trade_count_oos, returns_oos,
               annual_pnl_2024, annual_pnl_2025, annual_pnl_2026
        FROM gold.strategy_backtest_runs
        WHERE strategy_id = :sid
        ORDER BY run_number DESC, created_at DESC
        LIMIT 1
    """, {"sid": strategy_id}, label="eval_backtest_runs")

    backtest_metrics = {
        "win_rate": None,
        "profit_factor": None,
        "sharpe": None,
        "max_drawdown": None,
        "total_trades": None,
        "total_return": None,
        "avg_holding_days": None,
    }

    if backtest_row:
        if backtest_row.win_rate_oos is not None:
            backtest_metrics["win_rate"] = float(backtest_row.win_rate_oos)
        if backtest_row.profit_factor_oos is not None:
            backtest_metrics["profit_factor"] = float(backtest_row.profit_factor_oos)
        if backtest_row.sharpe_oos is not None:
            backtest_metrics["sharpe"] = float(backtest_row.sharpe_oos)
        if backtest_row.max_drawdown_oos is not None:
            backtest_metrics["max_drawdown"] = float(backtest_row.max_drawdown_oos)
        if backtest_row.trade_count_oos is not None:
            backtest_metrics["total_trades"] = int(backtest_row.trade_count_oos)
        if backtest_row.returns_oos is not None:
            backtest_metrics["total_return"] = float(backtest_row.returns_oos)
    else:
        # Fallback to registry OOS metrics if no backtest run record
        if strategy.win_rate_oos is not None:
            backtest_metrics["win_rate"] = float(strategy.win_rate_oos)
        if strategy.profit_factor_oos is not None:
            backtest_metrics["profit_factor"] = float(strategy.profit_factor_oos)
        if strategy.sharpe_oos is not None:
            backtest_metrics["sharpe"] = float(strategy.sharpe_oos)
        if strategy.max_drawdown_oos is not None:
            backtest_metrics["max_drawdown"] = float(strategy.max_drawdown_oos)
        if strategy.trade_count_oos is not None:
            backtest_metrics["total_trades"] = int(strategy.trade_count_oos)
        if strategy.returns_oos is not None:
            backtest_metrics["total_return"] = float(strategy.returns_oos)

    # Average holding duration over ALL OOS per-trade rows (not the
    # trade_limit-trimmed ledger below). holding_days column preferred, date
    # diff as fallback. NULL when the strategy stored aggregate metrics only
    # (no per-trade rows) — the UI renders '—', never a fake zero.
    bt_hold_row = safe_query_one(db, """
        SELECT AVG(COALESCE(holding_days, exit_date - entry_date)) AS avg_hold
        FROM gold.strategy_backtest_trades
        WHERE strategy_id = :sid
          AND period = 'OOS'
          AND exit_date IS NOT NULL
          AND (ticker IS NULL OR ticker != 'CASH')
    """, {"sid": strategy_id}, label="eval_bt_avg_hold")
    if bt_hold_row and bt_hold_row.avg_hold is not None:
        backtest_metrics["avg_holding_days"] = round(float(bt_hold_row.avg_hold), 1)

    # ---- Live data source selection ----------------------------------------
    # Prefer gold.trade_executions for LIVE_TRADING only. For PAPER/SIMULATION
    # strategies the canonical live ledger is gold.paper_trades_synthetic, which
    # is maintained by the position-aware rebalancer and enforces one open
    # position per ticker. The `book` query param overrides the source so the
    # detail page's mode toggle can read a specific ledger regardless of the
    # strategy's current deployment mode.
    api_mode = registry_to_api_mode(strategy.execution_mode)
    book_req = (book or "auto").lower()
    if book_req == "paper":
        use_trade_executions = False
    elif book_req == "live":
        use_trade_executions = True
    else:
        use_trade_executions = api_mode == 'LIVE_TRADING'

    # ---- Live metrics -------------------------------------------------------
    # CASH is a cash-bucket placeholder, not a tradeable ticker; exclude it from
    # live performance metrics so they reflect security trades only.
    if use_trade_executions:
        live = safe_query_one(db, """
            SELECT COUNT(*)                                                AS total_trades,
                   SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END)                AS winners,
                   SUM(CASE WHEN pnl > 0 THEN pnl ELSE 0 END)              AS gross_win,
                   SUM(CASE WHEN pnl < 0 THEN -pnl ELSE 0 END)             AS gross_loss,
                   COALESCE(SUM(pnl), 0)                                   AS total_pnl,
                   MAX(executed_at)                                        AS last_trade_at,
                   MIN(executed_at)                                        AS first_trade_at
            FROM gold.trade_executions
            WHERE strategy_id = :sid AND pnl IS NOT NULL
              AND (ticker IS NULL OR ticker != 'CASH')
        """, {"sid": strategy_id}, label="eval_live_summary")
    else:
        # t_8b58b2bc (memo 2026-08-17 section 2.3): metrics must be computed
        # from CLOSED round-trips only. Open rows previously carried pnl=0 and
        # passed the `pnl IS NOT NULL` filter, so every open position was
        # counted as a losing closed trade (WR/PF/trade-count corruption).
        live = safe_query_one(db, """
            SELECT COUNT(*)                                                AS total_trades,
                   SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END)                AS winners,
                   SUM(CASE WHEN pnl > 0 THEN pnl ELSE 0 END)              AS gross_win,
                   SUM(CASE WHEN pnl < 0 THEN -pnl ELSE 0 END)             AS gross_loss,
                   COALESCE(SUM(pnl), 0)                                   AS total_pnl,
                   MAX(exit_date)                                          AS last_trade_at,
                   MIN(entry_date)                                         AS first_trade_at,
                   AVG(exit_date - entry_date)                             AS avg_hold_days
            FROM gold.paper_trades_synthetic
            WHERE strategy_id = :sid AND status = 'closed' AND pnl IS NOT NULL
              AND (ticker IS NULL OR ticker != 'CASH')
        """ + _NS_EXCL_SYNTH, {"sid": strategy_id}, label="eval_live_summary_synthetic")

    live_metrics = {"total_trades": 0, "win_rate": None, "profit_factor": None,
                    "total_pnl": 0.0, "last_trade_at": None, "first_trade_at": None,
                    "avg_holding_days": None}
    if live and live.total_trades and live.total_trades > 0:
        wr = (live.winners or 0) / live.total_trades
        pf = float(live.gross_win) / float(live.gross_loss) if live.gross_loss and live.gross_loss > 0 else None
        live_metrics = {
            "total_trades": int(live.total_trades),
            "win_rate": round(wr, 4),
            "profit_factor": round(pf, 3) if pf is not None else None,
            "total_pnl": float(live.total_pnl or 0),
            "last_trade_at": live.last_trade_at.isoformat() if live.last_trade_at else None,
            "first_trade_at": live.first_trade_at.isoformat() if live.first_trade_at else None,
            # NULL for LIVE_TRADING (trade_executions has no entry/exit pairing)
            # and when no closed paper round-trips exist yet.
            "avg_holding_days": (round(float(live.avg_hold_days), 1)
                                 if getattr(live, "avg_hold_days", None) is not None else None),
        }

    # ---- Per-mode headline metrics (4-mode toggle strip) --------------------
    # One aggregate per book so the detail page can show 4 win rates + 4 P&L
    # figures that stay on screen while the lower panels switch with the
    # toggle. Empty books return NULL fields — the UI renders an honest
    # no-data state, never a fake zero.
    def _shape_book_metrics(row):
        if not row or not row.total_trades or row.total_trades <= 0:
            return {"total_trades": 0, "win_rate": None, "profit_factor": None,
                    "total_pnl": None, "last_trade_at": None}
        wr = (row.winners or 0) / row.total_trades
        pf = float(row.gross_win) / float(row.gross_loss) if row.gross_loss and row.gross_loss > 0 else None
        return {
            "total_trades": int(row.total_trades),
            "win_rate": round(wr, 4),
            "profit_factor": round(pf, 3) if pf is not None else None,
            "total_pnl": float(row.total_pnl or 0),
            "last_trade_at": row.last_trade_at.isoformat() if row.last_trade_at else None,
        }

    if use_trade_executions:
        paper_book_row = safe_query_one(db, """
            SELECT COUNT(*)                                        AS total_trades,
                   SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END)        AS winners,
                   SUM(CASE WHEN pnl > 0 THEN pnl ELSE 0 END)      AS gross_win,
                   SUM(CASE WHEN pnl < 0 THEN -pnl ELSE 0 END)     AS gross_loss,
                   COALESCE(SUM(pnl), 0)                           AS total_pnl,
                   MAX(exit_date)                                  AS last_trade_at
            FROM gold.paper_trades_synthetic
            WHERE strategy_id = :sid AND status = 'closed' AND pnl IS NOT NULL
              AND (ticker IS NULL OR ticker != 'CASH')
        """ + _NS_EXCL_SYNTH, {"sid": strategy_id}, label="eval_paper_book_summary")
        paper_book_metrics = _shape_book_metrics(paper_book_row)
        live_book_metrics = dict(live_metrics)
        if live_book_metrics.get("total_trades", 0) == 0:
            live_book_metrics["total_pnl"] = None
    else:
        live_book_row = safe_query_one(db, """
            SELECT COUNT(*)                                        AS total_trades,
                   SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END)        AS winners,
                   SUM(CASE WHEN pnl > 0 THEN pnl ELSE 0 END)      AS gross_win,
                   SUM(CASE WHEN pnl < 0 THEN -pnl ELSE 0 END)     AS gross_loss,
                   COALESCE(SUM(pnl), 0)                           AS total_pnl,
                   MAX(executed_at)                                AS last_trade_at
            FROM gold.trade_executions
            WHERE strategy_id = :sid AND pnl IS NOT NULL
              AND (ticker IS NULL OR ticker != 'CASH')
        """, {"sid": strategy_id}, label="eval_live_book_summary")
        live_book_metrics = _shape_book_metrics(live_book_row)
        paper_book_metrics = dict(live_metrics)
        if paper_book_metrics.get("total_trades", 0) == 0:
            paper_book_metrics["total_pnl"] = None

    # UAT: broker-rehearsal fills synced from the IBKR UAT session.
    # gold.paper_uat_fills has no per-fill pnl column (fills, not round-trips),
    # so only the fill count / last-fill timestamp are knowable here; WR / PF /
    # P&L stay NULL until a per-strategy UAT round-trip ledger exists.
    uat_book_row = safe_query_one(db, """
        SELECT COUNT(*)            AS total_fills,
               MAX(fill_time)      AS last_fill_at
        FROM gold.paper_uat_fills
        WHERE strategy_id = :sid
    """, {"sid": strategy_id}, label="eval_uat_book_summary")
    uat_book_metrics = {
        "total_fills": int(uat_book_row.total_fills) if uat_book_row and uat_book_row.total_fills else 0,
        "total_trades": None,
        "win_rate": None,
        "profit_factor": None,
        "total_pnl": None,
        "last_trade_at": (uat_book_row.last_fill_at.isoformat()
                          if uat_book_row and uat_book_row.last_fill_at else None),
    }

    metrics_by_mode = {
        # SIM = OOS backtest baseline. Backtests store per-trade pnl_pct, not
        # dollars, so total_pnl is NULL and total_return (OOS %) is the honest
        # performance figure.
        "sim": {**backtest_metrics, "total_pnl": None},
        "paper": paper_book_metrics,
        "uat": uat_book_metrics,
        "live": live_book_metrics,
    }

    # Per-strategy UAT fills for the UAT detail view (empty until the
    # UAT book accrues broker-rehearsal fills attributed to this strategy).
    uat_fill_rows = safe_query(db, """
        SELECT fill_time, symbol, side, qty, price, currency, exec_id, order_ref
        FROM gold.paper_uat_fills
        WHERE strategy_id = :sid
        ORDER BY fill_time DESC
        LIMIT 500
    """, {"sid": strategy_id}, label="eval_uat_fills")
    uat_fills = [{
        "ts": f.fill_time.isoformat() if f.fill_time else None,
        "ticker": f.symbol,
        "side": f.side,
        "quantity": float(f.qty) if f.qty is not None else None,
        "price": float(f.price) if f.price is not None else None,
        "currency": f.currency,
        "exec_id": f.exec_id,
        "order_ref": f.order_ref,
    } for f in uat_fill_rows]

    # ---- Equity curve (cumulative live pnl per day, last `days` days) ------
    # Exclude CASH-bucket placeholder trades so the curve reflects security P&L only.
    if use_trade_executions:
        equity_rows = safe_query(db, """
            SELECT DATE(executed_at) AS d, COALESCE(SUM(pnl), 0) AS day_pnl
            FROM gold.trade_executions
            WHERE strategy_id = :sid
              AND pnl IS NOT NULL
              AND (ticker IS NULL OR ticker != 'CASH')
              AND executed_at > NOW() - (:days || ' days')::INTERVAL
            GROUP BY DATE(executed_at)
            ORDER BY d ASC
        """, {"sid": strategy_id, "days": str(days)}, label="eval_equity")
    else:
        equity_rows = safe_query(db, """
            SELECT exit_date AS d, COALESCE(SUM(pnl), 0) AS day_pnl
            FROM gold.paper_trades_synthetic
            WHERE strategy_id = :sid
              AND pnl IS NOT NULL
              AND (ticker IS NULL OR ticker != 'CASH')
              AND status = 'closed'
              AND exit_date > CURRENT_DATE - (:days || ' days')::INTERVAL
        """ + _NS_EXCL_SYNTH + """
            GROUP BY exit_date
            ORDER BY d ASC
        """, {"sid": strategy_id, "days": str(days)}, label="eval_equity_synthetic")

    equity_curve = []
    cum = 0.0
    for r in equity_rows:
        cum += float(r.day_pnl or 0)
        equity_curve.append({"date": r.d.isoformat(), "pnl": float(r.day_pnl or 0), "cum_pnl": round(cum, 2)})

    # ---- Monthly returns ---------------------------------------------------
    # Source: consumption.strategy_monthly_returns (qr_etl-managed view keyed by strategy_id).
    # This view aggregates closed backtest trades from gold.strategy_backtest_trades and
    # normalizes pnl_pct units to decimal fractions. See refresh_strategy_monthly_returns.py
    # in the qr_etl profile for implementation details.
    monthly_rows = safe_query(db, """
        SELECT year, month, return_pct
        FROM consumption.strategy_monthly_returns
        WHERE strategy_id = :sid
        ORDER BY year, month
    """, {"sid": strategy_id}, label="eval_monthly_returns")

    monthly_returns = [{"year": int(r.year), "month": int(r.month),
                        "return": float(r.return_pct or 0)} for r in monthly_rows]

    # ---- Yearly returns (SIM) + paper-book monthly/yearly realized returns ----
    # SIM yearly must reconcile with the heatmap beside it, so prefer the
    # annual_pnl_* of the SAME run the published monthly series was built from
    # (gold.strategy_backtest_monthly_returns.run_id) — a newer backtest run can
    # exist whose annuals differ from the published monthly series. Fallbacks:
    # compound the monthly rows, then the latest run's annuals (aggregate-only
    # strategies have no monthly rows at all).
    yearly_sim = {}
    _mr = safe_query_one(db, """
        SELECT run_id FROM gold.strategy_backtest_monthly_returns
        WHERE strategy_id = :sid
        ORDER BY created_at DESC
        LIMIT 1
    """, {"sid": strategy_id}, label="eval_monthly_run_id")
    if _mr and _mr.run_id:
        _ar = safe_query_one(db, """
            SELECT annual_pnl_2024, annual_pnl_2025, annual_pnl_2026
            FROM gold.strategy_backtest_runs
            WHERE run_id = CAST(:rid AS uuid)
        """, {"rid": str(_mr.run_id)}, label="eval_annual_same_run")
        if _ar:
            for _y in (2024, 2025, 2026):
                _v = getattr(_ar, f"annual_pnl_{_y}", None)
                if _v is not None:
                    yearly_sim[_y] = float(_v)
    if not yearly_sim and monthly_returns:
        _by_year = {}
        for _r in monthly_returns:
            _by_year.setdefault(_r["year"], 1.0)
            _by_year[_r["year"]] *= (1.0 + (_r["return"] or 0.0))
        yearly_sim = {y: v - 1.0 for y, v in _by_year.items()}
    if not yearly_sim and backtest_row:
        for _y in (2024, 2025, 2026):
            _v = getattr(backtest_row, f"annual_pnl_{_y}", None)
            if _v is not None:
                yearly_sim[_y] = float(_v)

    # Paper monthly/yearly: realized P&L from the same ledger the Paper panel
    # renders (gold.paper_trades_synthetic closed rows), normalized by the
    # strategy's assigned capital. Simple sum (not compounded) — the capital
    # base is fixed assigned capital, not a reinvested balance.
    monthly_returns_paper = []
    yearly_paper = {}
    _capital_base = float(strategy.assigned_capital) if strategy.assigned_capital else None
    if _capital_base and _capital_base > 0:
        _p_rows = safe_query(db, """
            SELECT EXTRACT(YEAR FROM exit_date)::int AS year,
                   EXTRACT(MONTH FROM exit_date)::int AS month,
                   SUM(pnl) AS month_pnl
            FROM gold.paper_trades_synthetic
            WHERE strategy_id = :sid
              AND status = 'closed'
              AND pnl IS NOT NULL
              AND exit_date IS NOT NULL
              AND (ticker IS NULL OR ticker != 'CASH')
        """ + _NS_EXCL_SYNTH + """
            GROUP BY 1, 2
            ORDER BY 1, 2
        """, {"sid": strategy_id}, label="eval_monthly_returns_paper")
        monthly_returns_paper = [{"year": int(r.year), "month": int(r.month),
                                  "return": float(r.month_pnl or 0) / _capital_base}
                                 for r in _p_rows]
        _yp = {}
        for r in _p_rows:
            _yp[int(r.year)] = _yp.get(int(r.year), 0.0) + float(r.month_pnl or 0)
        yearly_paper = {y: v / _capital_base for y, v in _yp.items()}

    # ---- Recent trades (last 50) ------------------------------------------
    # Exclude CASH placeholder trades from the ticker-level ledger.
    # For PAPER/SIMULATION strategies, gold.paper_trades_synthetic stores one row
    # per position. We expand each closed position into a BUY entry event and a SELL
    # exit event so the UI can show round-trips and group them by rebalance date.
    # For LIVE trading, gold.trade_executions already contains one row per execution.
    trade_limit = max(1, min(trade_limit, 1000))
    if use_trade_executions:
        trades = safe_query(db, """
            SELECT executed_at, ticker, side, quantity, price, pnl, execution_mode AS mode
            FROM gold.trade_executions
            WHERE strategy_id = :sid
              AND (ticker IS NULL OR ticker != 'CASH')
            ORDER BY executed_at DESC
            LIMIT :limit
        """, {"sid": strategy_id, "limit": trade_limit}, label="eval_trades")

        recent_trades = [{
            "ts": t.executed_at.isoformat() if t.executed_at else None,
            "ticker": t.ticker,
            "side": t.side,
            "quantity": float(t.quantity) if t.quantity is not None else None,
            "price": float(t.price) if t.price is not None else None,
            "pnl": float(t.pnl) if t.pnl is not None else None,
            "mode": getattr(t, "mode", None),
        } for t in trades]
    else:
        # Fetch up to 1000 positions then expand into round-trip events. The event
        # list is then trimmed to the requested trade_limit so we never return
        # more than the UI asked for, but we still capture the full BUY/SELL pair.
        pos_limit = 1000
        trades = safe_query(db, """
            SELECT entry_date, exit_date, ticker, direction, n_shares AS quantity,
                   entry_price, exit_price, pnl, status
            FROM gold.paper_trades_synthetic
            WHERE strategy_id = :sid
              AND (ticker IS NULL OR ticker != 'CASH')
            ORDER BY entry_date DESC, exit_date DESC
            LIMIT :limit
        """, {"sid": strategy_id, "limit": pos_limit}, label="eval_trades_synthetic")

        # CLEANSE-1 (t_070590de): ledger rows stay listed (they ARE the book's
        # history) but closure-labeled legs are flagged non-strategy so the UI
        # annotates them instead of letting them read as strategy performance.
        _closures = fetch_closure_legs(db, [strategy_id])
        recent_trades = []
        for t in trades:
            _ns = None
            if t.status == 'closed' and t.exit_date:
                _cl = _closures.get((strategy_id, t.ticker))
                if _cl and _cl.get("skip_date") == (t.exit_date.isoformat() if t.exit_date else None):
                    _ns = {"skip_kind": _cl["skip_kind"], "reason": _cl["reason"]}
            if t.status == 'closed' and t.exit_date:
                recent_trades.append({
                    "ts": t.entry_date.isoformat() if t.entry_date else None,
                    "ticker": t.ticker,
                    "side": "BUY",
                    "quantity": float(t.quantity) if t.quantity is not None else None,
                    "price": float(t.entry_price) if t.entry_price is not None else None,
                    "pnl": None,
                    "mode": strategy.execution_mode,
                    "non_strategy": bool(_ns),
                })
                recent_trades.append({
                    "ts": t.exit_date.isoformat() if t.exit_date else None,
                    "ticker": t.ticker,
                    "side": "SELL",
                    "quantity": float(t.quantity) if t.quantity is not None else None,
                    "price": float(t.exit_price) if t.exit_price is not None else None,
                    "pnl": float(t.pnl) if t.pnl is not None else None,
                    "mode": strategy.execution_mode,
                    "non_strategy": bool(_ns),
                    "non_strategy_label": _ns,
                })
            else:
                recent_trades.append({
                    "ts": t.entry_date.isoformat() if t.entry_date else None,
                    "ticker": t.ticker,
                    "side": "BUY",
                    "quantity": float(t.quantity) if t.quantity is not None else None,
                    "price": float(t.entry_price) if t.entry_price is not None else None,
                    "pnl": None,
                    "mode": strategy.execution_mode,
                })
        recent_trades.sort(key=lambda x: x['ts'] or '', reverse=True)
        recent_trades = recent_trades[:trade_limit]

    # ---- Recent signals ----------------------------------------------------
    # CASH is a cash-bucket placeholder, not a tradeable ticker; exclude it from
    # the active-signals table. safe_query swallows the error if the view is missing.
    # ORDER BY updated_at is meaningless here (batch refresh gives every row the
    # same timestamp), and a bare LIMIT 50 silently dropped BUY rows when the
    # universe exceeded 50 tickers (hk_stk_52wh_mom_04 showed Allocation (4)
    # instead of 10). Actionable signals first, deterministic tiebreak, and a
    # limit sized so BUY/SELL rows can never be truncated by HOLD noise.
    signal_rows = safe_query(db, """
        SELECT ticker, signal, signal_strength, confidence_score, current_price, updated_at
        FROM consumption.strategies_signals_current
        WHERE strategy_id = :sid
          AND (ticker IS NULL OR ticker != 'CASH')
        ORDER BY CASE signal WHEN 'BUY' THEN 0 WHEN 'SELL' THEN 1 ELSE 2 END,
                 ticker
        LIMIT 200
    """, {"sid": strategy_id}, label="eval_signals")
    recent_signals = [{
        "ticker": s.ticker,
        "signal": s.signal,
        "strength": float(s.signal_strength) if s.signal_strength is not None else None,
        "confidence": float(s.confidence_score) if s.confidence_score is not None else None,
        "price": float(s.current_price) if s.current_price is not None else None,
        "ts": s.updated_at.isoformat() if s.updated_at else None,
    } for s in signal_rows]

    # ---- Backtest trade ledger (simulation side of the detail page) --------
    # Per-trade OOS records from gold.strategy_backtest_trades. Not all
    # strategies have per-trade rows (portfolio-level backtests only store
    # aggregate metrics) — the UI shows an honest empty state in that case.
    # Scoped to the SAME latest run the metrics header reads
    # (run_number DESC, created_at DESC): without the run filter a re-run
    # strategy renders its ledger twice (hk_ipo_day1_green_momentum_v1 showed
    # 35 rows = 18 + 17 from two runs, with identical trades duplicated).
    bt_trade_rows = safe_query(db, """
        SELECT t.entry_date, t.exit_date, t.ticker, t.entry_price, t.exit_price,
               t.pnl_pct, t.holding_days, t.exit_reason
        FROM gold.strategy_backtest_trades t
        JOIN (
            SELECT run_id
            FROM gold.strategy_backtest_runs
            WHERE strategy_id = :sid
            ORDER BY run_number DESC, created_at DESC
            LIMIT 1
        ) latest ON latest.run_id = t.run_id
        WHERE t.strategy_id = :sid
          AND t.period = 'OOS'
          AND (t.ticker IS NULL OR t.ticker != 'CASH')
        ORDER BY t.entry_date DESC
        LIMIT :limit
    """, {"sid": strategy_id, "limit": trade_limit}, label="eval_bt_trades")

    backtest_trades = [{
        "entry_date": r.entry_date.isoformat() if r.entry_date else None,
        "exit_date": r.exit_date.isoformat() if r.exit_date else None,
        "ticker": r.ticker,
        "entry_price": float(r.entry_price) if r.entry_price is not None else None,
        "exit_price": float(r.exit_price) if r.exit_price is not None else None,
        "pnl_pct": float(r.pnl_pct) if r.pnl_pct is not None else None,
        "holding_days": int(r.holding_days) if r.holding_days is not None else None,
        "exit_reason": r.exit_reason,
    } for r in bt_trade_rows]

    # Mark-to-market for open OOS positions: latest close per open ticker so
    # the UI can show unrealized P&L instead of a bare "open" / "—".
    # silver.unified_prices is the canonical mark (same source as the
    # open-positions view), gold.daily_ohlcv is the daily fallback.
    # Closed rows are untouched. Open rows are few (current book), so a
    # per-ticker lookup is fine and avoids array-binding pitfalls.
    open_bt_tickers = sorted({t["ticker"] for t in backtest_trades if not t["exit_date"] and t["ticker"]})
    bt_marks = {}
    for tk in open_bt_tickers:
        mark = safe_query_one(db, """
            SELECT close, date FROM silver.unified_prices
            WHERE ticker = :t AND close IS NOT NULL
            ORDER BY date DESC LIMIT 1
        """, {"t": tk}, label="eval_bt_mark_silver")
        src = "silver.unified_prices"
        if not mark:
            mark = safe_query_one(db, """
                SELECT close, date FROM gold.daily_ohlcv
                WHERE ticker = :t AND close IS NOT NULL
                ORDER BY date DESC LIMIT 1
            """, {"t": tk}, label="eval_bt_mark_gold")
            src = "gold.daily_ohlcv"
        if mark and mark.close is not None:
            bt_marks[tk] = {
                "current_price": float(mark.close),
                "current_price_date": mark.date.isoformat() if mark.date else None,
                "price_source": src,
            }
    for t in backtest_trades:
        if t["exit_date"] or not t["ticker"]:
            continue
        m = bt_marks.get(t["ticker"])
        if m:
            t.update(m)
            if t["entry_price"]:
                t["unrealized_pnl_pct"] = m["current_price"] / t["entry_price"] - 1.0

    # ---- Non-strategy bookkeeping excluded totals (CLEANSE-1, t_070590de) ---
    # Every paper aggregate above excludes skip-log labeled closure legs
    # (RESET_STALE_SIGNAL flattened / CLEANSE1_CLOSURE); the held-back amount
    # is disclosed in the payload as non_strategy_excluded.
    ns_row = safe_query_one(db, """
        SELECT COUNT(*) AS legs, SUM(pnl) AS pnl
        FROM gold.paper_trades_synthetic
        WHERE strategy_id = :sid AND status = 'closed'
          AND (ticker IS NULL OR ticker != 'CASH')
    """ + "AND " + non_strategy_leg_exists("gold.paper_trades_synthetic"),
        {"sid": strategy_id}, label="eval_non_strategy_excluded")

    # ---- Paper-book skip surface -------------------------------------------
    # consumption.strategy_paper_skips_current (qr_etl, refreshed every paper
    # rebalancer run): one row per (strategy_id, ticker) BUY signal the paper
    # rebalancer sized to zero — explains why the paper book is flat despite an
    # active BUY signal. skip_kind: BELOW_ONE_LOT | UNSUPPORTED_ASSET_CLASS |
    # NO_PRICE. Rows disappear when the skip no longer applies. Empty table =
    # no skips; safe_query returns [] if the table is missing, so this never
    # breaks the payload.
    skip_rows = safe_query(db, """
        SELECT ticker, signal_action, score, weight, slot_notional, price,
               lot_size, lot_cost, skip_kind, reason, skip_date, updated_at
        FROM consumption.strategy_paper_skips_current
        WHERE strategy_id = :sid
        ORDER BY ticker
    """, {"sid": strategy_id}, label="eval_paper_skips")
    paper_skips = [{
        "ticker": r.ticker,
        "signal_action": r.signal_action,
        "score": float(r.score) if r.score is not None else None,
        "weight": float(r.weight) if r.weight is not None else None,
        "slot_notional": float(r.slot_notional) if r.slot_notional is not None else None,
        "price": float(r.price) if r.price is not None else None,
        "lot_size": float(r.lot_size) if r.lot_size is not None else None,
        "lot_cost": float(r.lot_cost) if r.lot_cost is not None else None,
        "skip_kind": r.skip_kind,
        "reason": r.reason,
        "skip_date": r.skip_date.isoformat() if r.skip_date else None,
        "updated_at": r.updated_at.isoformat() if r.updated_at else None,
    } for r in skip_rows]

    # ---- Divergence verdict ------------------------------------------------
    bt_wr = backtest_metrics["win_rate"]
    lv_wr = live_metrics["win_rate"]
    bt_pf = backtest_metrics["profit_factor"]
    lv_pf = live_metrics["profit_factor"]
    wr_delta_pp = round((lv_wr - bt_wr) * 100, 2) if (bt_wr is not None and lv_wr is not None) else None
    pf_delta = round(lv_pf - bt_pf, 3) if (bt_pf is not None and lv_pf is not None) else None

    if live_metrics["total_trades"] < 10:
        verdict = "insufficient_live_data"
    elif wr_delta_pp is None:
        verdict = "no_backtest_baseline"
    elif wr_delta_pp >= 2 and (pf_delta is None or pf_delta >= 0):
        verdict = "outperforming"
    elif wr_delta_pp <= -5 or (pf_delta is not None and pf_delta <= -0.3):
        verdict = "underperforming"
    else:
        verdict = "in_line"

    return {
        "strategy_id": strategy_id,
        "name": name,
        "version": None,
        "status": strategy.status,
        # CLEANSE-1 (t_070590de): operator reason text for halted books —
        # the detail page renders the PAUSED/PENDING/RETIRED banner from these.
        "retirement_reason": getattr(strategy, 'retirement_reason', None),
        "priority": strategy.priority,
        "asset_class": asset_class,
        "direction": direction,
        "time_horizon": strategy.frequency,
        "execution_mode": registry_to_api_mode(strategy.execution_mode),
        "venue": "IBKR",
        "assigned_capital": float(strategy.assigned_capital) if strategy.assigned_capital is not None else None,
        "in_market_capital": float(strategy.in_market_capital) if strategy.in_market_capital is not None else None,
        "conviction_score": float(strategy.conviction_score) if strategy.conviction_score is not None else None,
        "created_at": strategy.created_at.isoformat() if strategy.created_at else None,
        "updated_at": strategy.updated_at.isoformat() if strategy.updated_at else None,
        "universe": universe,
        "universe_count": len(universe),
        "entry_logic": strategy.signal_logic,
        "exit_logic": strategy.exit_logic,
        "description": strategy.description,
        "metrics": {
            "backtest": backtest_metrics,
            "live": live_metrics,
        },
        "metrics_by_mode": metrics_by_mode,
        "uat_fills": uat_fills,
        # Which ledger the live block (metrics.live / equity_curve /
        # recent_trades) was read from — echoes the `book` override.
        "book": "live" if use_trade_executions else "paper",
        "divergence": {
            "win_rate_delta_pp": wr_delta_pp,
            "profit_factor_delta": pf_delta,
            "verdict": verdict,
        },
        "equity_curve": equity_curve,
        "monthly_returns": monthly_returns,
        "monthly_returns_paper": monthly_returns_paper,
        "yearly_returns": {
            "sim": {str(y): v for y, v in yearly_sim.items()},
            "paper": {str(y): v for y, v in yearly_paper.items()},
        },
        "recent_trades": recent_trades,
        "recent_signals": recent_signals,
        "backtest_trades": backtest_trades,
        "paper_skips": paper_skips,
        # CLEANSE-1 (t_070590de): closure-labeled non-strategy legs excluded
        # from every aggregate above — surfaced so the page can disclose the
        # held-back amount instead of silently diverging from the raw ledger.
        "non_strategy_excluded": {
            "legs": int(ns_row.legs or 0) if ns_row else 0,
            "pnl": float(ns_row.pnl) if ns_row and ns_row.pnl is not None else None,
        },
        "window_days": days,
    }


def _evaluate_demote_rules(db: Session, strategy_id: str) -> dict:
    """Evaluate risk rules against live trade history. Returns rule status list."""
    # CASH is a cash-bucket placeholder, not a tradeable ticker; exclude from risk math.
    # Determine data source by strategy execution mode. Paper/simulation strategies
    # are tracked in gold.paper_trades_synthetic; live strategies in gold.trade_executions.
    mode_row = safe_query_one(db, """
        SELECT execution_mode FROM gold.strategy_registry WHERE strategy_id = :sid
    """, {"sid": strategy_id}, label="demote_mode")
    use_trade_executions = bool(mode_row and registry_to_api_mode(mode_row.execution_mode) == 'LIVE_TRADING')

    if use_trade_executions:
        recent = safe_query(db, """
            SELECT executed_at, pnl
            FROM gold.trade_executions
            WHERE strategy_id = :sid AND pnl IS NOT NULL
              AND (ticker IS NULL OR ticker != 'CASH')
            ORDER BY executed_at DESC
            LIMIT 50
        """, {"sid": strategy_id}, label="demote_recent")

        daily = safe_query(db, """
            SELECT DATE(executed_at) AS d, COALESCE(SUM(pnl), 0) AS day_pnl
            FROM gold.trade_executions
            WHERE strategy_id = :sid AND pnl IS NOT NULL
              AND (ticker IS NULL OR ticker != 'CASH')
            GROUP BY DATE(executed_at)
            ORDER BY d ASC
        """, {"sid": strategy_id}, label="demote_daily")
    else:
        recent = safe_query(db, """
            SELECT COALESCE(exit_date, entry_date) AS executed_at, pnl
            FROM gold.paper_trades_synthetic
            WHERE strategy_id = :sid AND pnl IS NOT NULL
              AND (ticker IS NULL OR ticker != 'CASH')
              AND status = 'closed'
        """ + _NS_EXCL_SYNTH + """
            ORDER BY COALESCE(exit_date, entry_date) DESC
            LIMIT 50
        """, {"sid": strategy_id}, label="demote_recent_synthetic")

        daily = safe_query(db, """
            SELECT exit_date AS d, COALESCE(SUM(pnl), 0) AS day_pnl
            FROM gold.paper_trades_synthetic
            WHERE strategy_id = :sid AND pnl IS NOT NULL
              AND (ticker IS NULL OR ticker != 'CASH')
              AND status = 'closed'
        """ + _NS_EXCL_SYNTH + """
            GROUP BY exit_date
            ORDER BY d ASC
        """, {"sid": strategy_id}, label="demote_daily_synthetic")

    # Pool size to compute pct losses
    pool = safe_query_one(db, """
        SELECT assigned_capital
        FROM gold.strategy_registry
        WHERE strategy_id = :sid
    """, {"sid": strategy_id}, label="demote_pool")
    pool_size = float(pool.assigned_capital) if pool and pool.assigned_capital else 100_000.0

    rules = []

    # Rule 1: rolling max drawdown from peak cumulative P&L
    cum = 0.0
    peak = 0.0
    max_dd_pct = 0.0
    for r in daily:
        cum += float(r.day_pnl or 0)
        peak = max(peak, cum)
        if peak > 0:
            dd_pct = ((cum - peak) / pool_size) * 100
            max_dd_pct = min(max_dd_pct, dd_pct)
    rules.append({
        "id": "max_drawdown",
        "label": f"Max DD ≥ {DEMOTE_RULES['max_drawdown_pct']:.1f}%",
        "actual": round(max_dd_pct, 2),
        "threshold": DEMOTE_RULES["max_drawdown_pct"],
        "breach": max_dd_pct < DEMOTE_RULES["max_drawdown_pct"],
        "reason": "Live drawdown exceeds risk limit",
    })

    # Rule 2: worst daily loss (% of pool)
    worst_daily_pct = 0.0
    if daily:
        worst_day = min((float(r.day_pnl or 0) for r in daily), default=0)
        worst_daily_pct = (worst_day / pool_size) * 100
    rules.append({
        "id": "max_daily_loss",
        "label": f"Daily loss ≥ {DEMOTE_RULES['max_daily_loss_pct']:.1f}%",
        "actual": round(worst_daily_pct, 2),
        "threshold": DEMOTE_RULES["max_daily_loss_pct"],
        "breach": worst_daily_pct < DEMOTE_RULES["max_daily_loss_pct"],
        "reason": "Single-day loss exceeds risk limit",
    })

    # Rule 3: consecutive losses (most recent streak)
    streak = 0
    for r in recent:  # already DESC
        if (r.pnl or 0) < 0:
            streak += 1
        else:
            break
    rules.append({
        "id": "consecutive_losses",
        "label": f"Consecutive losses ≤ {DEMOTE_RULES['max_consecutive_losses']}",
        "actual": streak,
        "threshold": DEMOTE_RULES["max_consecutive_losses"],
        "breach": streak >= DEMOTE_RULES["max_consecutive_losses"],
        "reason": f"{streak} losing trades in a row",
    })

    # Rule 4: live PF over last 20 trades
    last_n = recent[:20]
    gross_win = sum(float(r.pnl) for r in last_n if (r.pnl or 0) > 0)
    gross_loss = sum(-float(r.pnl) for r in last_n if (r.pnl or 0) < 0)
    pf = (gross_win / gross_loss) if gross_loss > 0 else None
    eligible = len(last_n) >= DEMOTE_RULES["min_live_trades_for_pf"]
    rules.append({
        "id": "min_live_pf",
        "label": f"Rolling PF ≥ {DEMOTE_RULES['min_live_pf']:.2f} (last 20 trades)",
        "actual": round(pf, 3) if pf is not None else None,
        "threshold": DEMOTE_RULES["min_live_pf"],
        "breach": eligible and pf is not None and pf < DEMOTE_RULES["min_live_pf"],
        "reason": "Profit factor degraded below threshold",
    })

    breaches = [r for r in rules if r["breach"]]
    return {
        "strategy_id": strategy_id,
        "rules": rules,
        "breaches": breaches,
        "should_demote": len(breaches) > 0,
        "trades_analyzed": len(recent),
    }


@app.get("/api/strategies/{strategy_id:path}/risk-status")
def get_risk_status(strategy_id: str, db: Session = Depends(get_db)):
    """Return the demote-rule status for a strategy without taking action."""
    strat = db.execute(text("""
        SELECT strategy_id, name, execution_mode
        FROM gold.strategy_registry WHERE strategy_id = :sid
    """), {"sid": strategy_id}).fetchone()
    if not strat:
        raise HTTPException(status_code=404, detail=f"Strategy {strategy_id} not found")

    status = _evaluate_demote_rules(db, strategy_id)
    return {
        **status,
        "name": strat.name,
        "execution_mode": strat.execution_mode,
    }


def _demote_strategy(db: Session, strategy_id: str, breaches: list, source: str = "auto"):
    """Demote a LIVE strategy to PAPER. Audits + emits WS event."""
    strat = db.execute(text("""
        SELECT strategy_id, name, execution_mode
        FROM gold.strategy_registry WHERE strategy_id = :sid
    """), {"sid": strategy_id}).fetchone()
    if not strat or strat.execution_mode != "LIVE":
        return False

    db.execute(text("""
        UPDATE gold.strategy_registry
        SET execution_mode = 'PAPER', updated_at = NOW()
        WHERE strategy_id = :sid
    """), {"sid": strategy_id})
    db.commit()

    _audit(db, "strategy.auto_demote", strategy_id, {
        "from": "LIVE_TRADING",
        "to": "PAPER_TRADING",
        "source": source,
        "breaches": [{"id": b["id"], "actual": b["actual"], "threshold": b["threshold"]} for b in breaches],
    })

    event_bus.publish_sync("auto_demote", {
        "strategy_id": strategy_id,
        "name": strat.name,
        "from": "LIVE_TRADING",
        "to": "PAPER_TRADING",
        "breaches": [b["id"] for b in breaches],
    })
    logger.warning(f"AUTO-DEMOTE {strategy_id} ({strat.name}) — breaches: {[b['id'] for b in breaches]}")
    return True


# Background scanner — checks every LIVE strategy and demotes breached ones.
DEMOTE_SCAN_INTERVAL_S = int(os.environ.get("JTCML_DEMOTE_SCAN_S", "300"))

async def _demote_scanner_loop():
    while True:
        try:
            await asyncio.sleep(DEMOTE_SCAN_INTERVAL_S)
            db = SessionLocal()
            try:
                live = db.execute(text("""
                    SELECT strategy_id FROM gold.strategy_registry
                    WHERE execution_mode = 'LIVE'
                """)).fetchall()
                for row in live:
                    sid = row.strategy_id
                    try:
                        status = _evaluate_demote_rules(db, sid)
                        if status["should_demote"]:
                            _demote_strategy(db, sid, status["breaches"], source="auto_scanner")
                    except Exception as e:
                        logger.error(f"Demote check failed for {sid}: {e}")
                        db.rollback()
            finally:
                db.close()
        except asyncio.CancelledError:
            raise
        except Exception as e:
            logger.error(f"Demote scanner loop error: {e}")


@app.post("/api/strategies/{strategy_id}/auto-demote-check")
def force_demote_check(strategy_id: str, db: Session = Depends(get_db)):
    """Manually trigger an auto-demote check for one strategy (for testing/UI)."""
    strat = db.execute(text("""
        SELECT strategy_id, name, execution_mode
        FROM gold.strategy_registry WHERE strategy_id = :sid
    """), {"sid": strategy_id}).fetchone()
    if not strat:
        raise HTTPException(status_code=404, detail="Strategy not found")

    status = _evaluate_demote_rules(db, strategy_id)
    demoted = False
    if status["should_demote"] and registry_to_api_mode(strat.execution_mode) == "LIVE_TRADING":
        demoted = _demote_strategy(db, strategy_id, status["breaches"], source="manual_check")

    return {**status, "demoted": demoted, "execution_mode": registry_to_api_mode(strat.execution_mode)}

@app.get("/api/strategies/{strategy_id:path}")
def get_strategy_by_id(strategy_id: str, db: Session = Depends(get_db)):
    """Get strategy details including signal logic and entry/exit conditions"""
    result = db.execute(text("""
        SELECT
            strategy_id,
            name,
            description,
            asset_class,
            universe_tickers,
            status,
            sharpe_oos,
            max_drawdown_oos,
            win_rate_oos,
            trade_count_oos,
            signal_logic,
            exit_logic,
            execution_mode,
            frequency,
            assigned_capital,
            in_market_capital,
            conviction_score,
            created_at,
            updated_at,
            priority
        FROM gold.strategy_registry
        WHERE strategy_id = :strategy_id
    """), {"strategy_id": strategy_id}).fetchone()

    if not result:
        raise HTTPException(status_code=404, detail=f"Strategy {strategy_id} not found")

    # Parse universe_tickers as an array; filter out the CASH placeholder.
    raw_universe = result.universe_tickers or []
    if isinstance(raw_universe, str):
        raw_universe = [t.strip() for t in raw_universe.split(',') if t.strip()]
    tickers = [t for t in raw_universe if t and t.upper() != 'CASH']

    return {
        "strategy_id": result.strategy_id,
        "name": result.name,
        "description": result.description,
        "asset_class": result.asset_class,
        "direction": "LONG",
        "time_horizon": result.frequency,
        "sharpe_ratio": float(result.sharpe_oos) if result.sharpe_oos else 0,
        "max_drawdown": float(result.max_drawdown_oos) if result.max_drawdown_oos else 0,
        "win_rate": float(result.win_rate_oos) if result.win_rate_oos else 0,
        "universe": tickers,
        "universe_count": len(tickers),
        "max_position_pct": 0.05,
        "venue": "IBKR",
        "status": result.status,
        "execution_mode": result.execution_mode,
        "signal_logic": result.signal_logic or "Entry conditions not specified",
        "exit_logic": result.exit_logic or "Exit at +5% profit (win) or -5% loss (stop loss)",
        "trigger_example": result.signal_logic or "See strategy description",
        "why_it_works": result.description or "",
        # Derived fields for frontend
        "buy_signal": result.signal_logic or "BUY signal triggered by strategy logic",
        "sell_signal": result.exit_logic or "SELL at +5% profit target or -5% stop loss",
        "take_profit": "+5% profit target",
        "stop_loss": "-5% stop loss limit"
    }


# --- STRATEGY SCREENER APIs ---

# ---------------------------------------------------------------------------
# Promotion gates — SIM → PAPER → UAT → LIVE
# ---------------------------------------------------------------------------

PROMOTION_GATES = {
    # SIM → PAPER: gates must pass against backtest data
    "SIMULATION->PAPER_TRADING": {
        "min_backtest_trades":   100,
        "min_backtest_win_rate": 0.45,
        "min_backtest_pf":       1.30,
        "min_backtest_sharpe":   1.00,
        "max_drawdown_pct":      -25.0,    # not worse than -25%
    },
    # PAPER → UAT: stage move into broker rehearsal (IBKR UAT session,
    # paper money). Strategy is already paper-qualified; allowed but logged.
    "PAPER_TRADING->UAT": {},
    # UAT → LIVE: intentionally ABSENT — transition is blocked until
    # qr_research/QA define the gate criteria (proposal: ≥10 clean UAT fills,
    # zero rejects, median |slippage| vs signal within tolerance, ≥5 UAT
    # sessions). Phase 4 kanban t_b64f7302 tracks the mirror that supplies
    # those metrics. override_gates=true can force it (audited).
    # PAPER → LIVE: gates must pass against live (paper) data + recency
    "PAPER_TRADING->LIVE_TRADING": {
        "min_live_trades":          30,
        "min_live_days":            14,
        "min_live_pf":              1.20,
        "min_live_vs_bt_wr_ratio":  0.85,  # live WR ≥ 85% of BT WR
        "max_drawdown_pct":         -15.0,
    },
    # LIVE → PAPER (demote, always allowed but logged)
    "LIVE_TRADING->PAPER_TRADING": {},
    # UAT → PAPER (demote out of broker rehearsal)
    "UAT->PAPER_TRADING": {},
    # UAT → SIM (full demote)
    "UAT->SIMULATION": {},
    # PAPER → SIM (demote)
    "PAPER_TRADING->SIMULATION":   {},
    # LIVE → SIM (full halt)
    "LIVE_TRADING->SIMULATION":    {},
}

VALID_MODES = {"SIMULATION", "PAPER_TRADING", "UAT", "LIVE_TRADING"}

# Ladder rank: promotion = moving to a strictly higher rung.
MODE_RANK = {"SIMULATION": 0, "PAPER_TRADING": 1, "UAT": 2, "LIVE_TRADING": 3}


def _gather_promotion_metrics(db: Session, strategy_id: str) -> dict:
    """Gather backtest + live metrics needed by promotion gates.

    The canonical OOS backtest results live in gold.strategy_backtest_runs (DE-owned).
    The live/paper ledger is gold.paper_trades_synthetic (maintained by the position-aware
    rebalancer); gold.trade_executions is reserved for actual LIVE_TRADING executions.
    """
    bt = safe_query_one(db, """
        SELECT win_rate_oos            AS win_rate,
               profit_factor_oos       AS profit_factor,
               sharpe_oos              AS sharpe,
               max_drawdown_oos        AS max_drawdown,
               trade_count_oos         AS total_trades
        FROM gold.strategy_backtest_runs
        WHERE strategy_id = :sid
        ORDER BY run_number DESC, is_end DESC
        LIMIT 1
    """, {"sid": strategy_id}, label="promote_bt")

    live = safe_query_one(db, """
        SELECT COUNT(*)                                                AS total_trades,
               SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END)                AS winners,
               SUM(CASE WHEN pnl > 0 THEN pnl ELSE 0 END)              AS gross_win,
               SUM(CASE WHEN pnl < 0 THEN -pnl ELSE 0 END)             AS gross_loss,
               COALESCE(SUM(pnl), 0)                                   AS total_pnl,
               MAX(CASE WHEN status = 'closed' THEN exit_date ELSE entry_date END) AS last_trade_at,
               MIN(entry_date)                                           AS first_trade_at
        FROM gold.paper_trades_synthetic
        WHERE strategy_id = :sid AND pnl IS NOT NULL
          AND (ticker IS NULL OR ticker != 'CASH')
    """ + _NS_EXCL_SYNTH, {"sid": strategy_id}, label="promote_live")

    bt_metrics = {
        "win_rate":     float(bt.win_rate) if bt and bt.win_rate is not None else None,
        "profit_factor":float(bt.profit_factor) if bt and bt.profit_factor is not None else None,
        "sharpe":       float(bt.sharpe) if bt and bt.sharpe is not None else None,
        "max_drawdown": float(bt.max_drawdown) if bt and bt.max_drawdown is not None else None,
        "total_trades": int(bt.total_trades) if bt and bt.total_trades is not None else 0,
    }
    live_total = int(live.total_trades) if live and live.total_trades else 0
    live_pf = (float(live.gross_win) / float(live.gross_loss)) if (live and live.gross_loss and live.gross_loss > 0) else None
    live_wr = (float(live.winners) / live_total) if live_total else None
    live_days = 0
    if live and live.first_trade_at and live.last_trade_at:
        live_days = max(0, (live.last_trade_at - live.first_trade_at).days)
    live_metrics = {
        "total_trades":  live_total,
        "win_rate":      live_wr,
        "profit_factor": live_pf,
        "days_active":   live_days,
        "first_trade_at": live.first_trade_at.isoformat() if live and live.first_trade_at else None,
        "last_trade_at":  live.last_trade_at.isoformat() if live and live.last_trade_at else None,
    }
    return {"backtest": bt_metrics, "live": live_metrics}


def _evaluate_gates(transition: str, metrics: dict, current_mode: str) -> dict:
    """Returns {gates: [{id, label, required, pass, actual, threshold, reason}], passed, blocked}.
    `passed` means every required gate passes. `blocked` is True when no rules exist
    for the requested transition (i.e. the transition is invalid/unsupported)."""
    rules = PROMOTION_GATES.get(transition)
    if rules is None:
        return {"gates": [], "passed": False, "blocked": True,
                "reason": f"Transition {transition} is not supported"}

    bt = metrics["backtest"]; lv = metrics["live"]
    gates = []

    def add(gid, label, ok, actual, threshold, required=True, hint=None):
        gates.append({
            "id": gid, "label": label, "required": required,
            "pass": bool(ok), "actual": actual, "threshold": threshold,
            "reason": hint if not ok else None,
        })

    # current mode must match the source of the transition
    src = transition.split("->")[0]
    add("current_mode", f"Currently in {src}", current_mode == src,
        current_mode, src,
        hint=f"Strategy is in {current_mode}, expected {src}")

    if transition == "SIMULATION->PAPER_TRADING":
        add("bt_trades", f"Backtest trades ≥ {rules['min_backtest_trades']}",
            (bt["total_trades"] or 0) >= rules["min_backtest_trades"],
            bt["total_trades"], rules["min_backtest_trades"],
            hint="Need more backtest trades for statistical confidence")
        add("bt_win_rate", f"Backtest WR ≥ {rules['min_backtest_win_rate']*100:.0f}%",
            (bt["win_rate"] or 0) >= rules["min_backtest_win_rate"],
            round((bt["win_rate"] or 0) * 100, 1), rules["min_backtest_win_rate"] * 100,
            hint="Backtest win rate below threshold")
        add("bt_pf", f"Backtest PF ≥ {rules['min_backtest_pf']:.2f}",
            (bt["profit_factor"] or 0) >= rules["min_backtest_pf"],
            bt["profit_factor"], rules["min_backtest_pf"],
            hint="Profit factor below threshold")
        add("bt_sharpe", f"Backtest Sharpe ≥ {rules['min_backtest_sharpe']:.2f}",
            (bt["sharpe"] or 0) >= rules["min_backtest_sharpe"],
            bt["sharpe"], rules["min_backtest_sharpe"],
            hint="Sharpe below threshold")
        add("bt_dd", f"Max DD ≥ {rules['max_drawdown_pct']:.0f}%",
            (bt["max_drawdown"] if bt["max_drawdown"] is not None else 0) >= rules["max_drawdown_pct"],
            bt["max_drawdown"], rules["max_drawdown_pct"],
            hint="Drawdown exceeds limit")

    elif transition == "PAPER_TRADING->LIVE_TRADING":
        add("live_trades", f"Live trades ≥ {rules['min_live_trades']}",
            lv["total_trades"] >= rules["min_live_trades"],
            lv["total_trades"], rules["min_live_trades"],
            hint="Insufficient paper trades; let it run longer")
        add("live_days", f"Live days ≥ {rules['min_live_days']}",
            lv["days_active"] >= rules["min_live_days"],
            lv["days_active"], rules["min_live_days"],
            hint="Strategy needs more paper-trading runtime")
        add("live_pf", f"Live PF ≥ {rules['min_live_pf']:.2f}",
            (lv["profit_factor"] or 0) >= rules["min_live_pf"],
            lv["profit_factor"], rules["min_live_pf"],
            hint="Live profit factor below threshold")
        # live WR vs backtest WR ratio
        if bt["win_rate"] and lv["win_rate"] is not None:
            ratio = lv["win_rate"] / bt["win_rate"] if bt["win_rate"] > 0 else 0
            add("live_vs_bt_wr",
                f"Live WR ≥ {rules['min_live_vs_bt_wr_ratio']*100:.0f}% of BT WR",
                ratio >= rules["min_live_vs_bt_wr_ratio"],
                round(ratio, 3), rules["min_live_vs_bt_wr_ratio"],
                hint="Live performance diverging from backtest")
        else:
            add("live_vs_bt_wr",
                f"Live WR ≥ {rules['min_live_vs_bt_wr_ratio']*100:.0f}% of BT WR",
                False, None, rules["min_live_vs_bt_wr_ratio"],
                hint="Missing backtest or live win rate")

    # Demotion paths: no extra gates beyond current_mode check
    required = [g for g in gates if g["required"]]
    passed = all(g["pass"] for g in required)
    return {"gates": gates, "passed": passed, "blocked": False, "reason": None}


def _audit(db: Session, event_type: str, strategy_id: str, payload: dict):
    """Best-effort write to gold.audit_events. If table is missing, log only."""
    try:
        db.execute(text("""
            INSERT INTO gold.audit_events (event_type, strategy_id, payload, created_at)
            VALUES (:t, :sid, CAST(:p AS jsonb), NOW())
        """), {"t": event_type, "sid": strategy_id, "p": json.dumps(payload)})
        db.commit()
    except (ProgrammingError, OperationalError) as e:
        db.rollback()
        logger.info(f"[AUDIT-FALLBACK] {event_type} {strategy_id}: {payload} ({e.orig})")
    except Exception as e:
        db.rollback()
        logger.info(f"[AUDIT-FALLBACK] {event_type} {strategy_id}: {payload} ({e})")


@app.post("/api/strategies/{strategy_id}/promote/check")
def promote_check(strategy_id: str, payload: dict, db: Session = Depends(get_db)):
    """Evaluate promotion gates for a target mode without making changes."""
    target = (payload or {}).get("target_mode")
    if target == "PAPER_UAT":  # legacy pre-rename API vocabulary
        target = "UAT"
    if target not in VALID_MODES:
        raise HTTPException(status_code=400, detail=f"target_mode must be one of {sorted(VALID_MODES)}")

    strat = db.execute(text("""
        SELECT strategy_id, name, execution_mode
        FROM gold.strategy_registry WHERE strategy_id = :sid
    """), {"sid": strategy_id}).fetchone()
    if not strat:
        raise HTTPException(status_code=404, detail=f"Strategy {strategy_id} not found")

    current_mode = registry_to_api_mode(strat.execution_mode)
    if current_mode == target:
        return {"strategy_id": strategy_id, "current_mode": current_mode, "target_mode": target,
                "passed": True, "blocked": False, "gates": [],
                "reason": "Already in target mode"}

    transition = f"{current_mode}->{target}"
    metrics = _gather_promotion_metrics(db, strategy_id)
    eval_result = _evaluate_gates(transition, metrics, current_mode)
    is_promotion = MODE_RANK.get(target, -1) > MODE_RANK.get(current_mode, -1)
    requires_phrase = (target == "LIVE_TRADING" and is_promotion)

    return {
        "strategy_id": strategy_id,
        "name": strat.name,
        "current_mode": current_mode,
        "target_mode": target,
        "transition": transition,
        "is_promotion": is_promotion,
        "requires_confirmation_phrase": requires_phrase,
        "confirmation_phrase": "PROMOTE TO LIVE" if requires_phrase else None,
        "metrics": metrics,
        **eval_result,
    }


@app.post("/api/strategies/{strategy_id}/promote")
def promote(strategy_id: str, payload: dict, db: Session = Depends(get_db)):
    """Run gate checks then promote/demote a strategy. LIVE requires confirmation phrase."""
    target = (payload or {}).get("target_mode")
    if target == "PAPER_UAT":  # legacy pre-rename API vocabulary
        target = "UAT"
    if target not in VALID_MODES:
        raise HTTPException(status_code=400, detail=f"target_mode must be one of {sorted(VALID_MODES)}")

    override = bool((payload or {}).get("override_gates", False))
    confirm  = (payload or {}).get("confirmation_phrase", "")

    strat = db.execute(text("""
        SELECT strategy_id, name, execution_mode
        FROM gold.strategy_registry WHERE strategy_id = :sid
    """), {"sid": strategy_id}).fetchone()
    if not strat:
        raise HTTPException(status_code=404, detail=f"Strategy {strategy_id} not found")

    current_mode = registry_to_api_mode(strat.execution_mode)
    if current_mode == target:
        return {"success": True, "no_op": True, "current_mode": current_mode,
                "message": f"Strategy already in {target}"}

    transition = f"{current_mode}->{target}"
    is_promotion = MODE_RANK.get(target, -1) > MODE_RANK.get(current_mode, -1)

    # LIVE requires a typed confirmation phrase regardless of override
    if target == "LIVE_TRADING" and is_promotion and confirm != "PROMOTE TO LIVE":
        raise HTTPException(status_code=400,
            detail="LIVE promotion requires confirmation_phrase = 'PROMOTE TO LIVE'")

    metrics = _gather_promotion_metrics(db, strategy_id)
    eval_result = _evaluate_gates(transition, metrics, current_mode)

    if eval_result["blocked"]:
        raise HTTPException(status_code=400, detail=eval_result["reason"] or "Invalid transition")

    if is_promotion and not eval_result["passed"] and not override:
        return {
            "success": False,
            "current_mode": current_mode,
            "target_mode": target,
            "passed": False,
            "gates": eval_result["gates"],
            "message": "Promotion blocked by gates. Pass override_gates=true to force (audited).",
        }

    # Apply mode change (registry stores constrained values)
    registry_mode = api_to_registry_mode(target)
    db.execute(text("""
        UPDATE gold.strategy_registry
        SET execution_mode = :mode, updated_at = NOW()
        WHERE strategy_id = :sid
    """), {"sid": strategy_id, "mode": registry_mode})
    db.commit()

    _audit(db, "strategy.mode_change", strategy_id, {
        "from": current_mode, "to": target,
        "is_promotion": is_promotion,
        "gates_passed": eval_result["passed"],
        "override_gates": override,
        "metrics": metrics,
    })

    event_bus.publish_sync("mode_change", {
        "strategy_id": strategy_id,
        "name": strat.name,
        "from": current_mode,
        "to": target,
        "is_promotion": is_promotion,
    })

    return {
        "success": True,
        "strategy_id": strategy_id,
        "name": strat.name,
        "previous_mode": current_mode,
        "current_mode": target,
        "is_promotion": is_promotion,
        "gates_passed": eval_result["passed"],
        "override_gates": override,
        "gates": eval_result["gates"],
        "message": f"Strategy {strategy_id} → {target}",
    }


# ---------------------------------------------------------------------------
# Auto-demote risk rules — LIVE strategies that breach risk limits get
# automatically demoted to PAPER. Pairs with the kill switch as the
# safety counterpart of the promotion gates.
# ---------------------------------------------------------------------------

DEMOTE_RULES = {
    "max_drawdown_pct":          -10.0,   # 10% rolling drawdown from peak P&L
    "max_daily_loss_pct":        -5.0,    # 5% loss in a single trading day
    "max_consecutive_losses":    5,
    "min_live_pf":               0.70,    # PF below 0.7 over last 20 trades
    "min_live_trades_for_pf":    10,      # need at least 10 trades to evaluate PF
}



# NOTE (2026-08-25): /api/strategies/{id}/mode is served by app/routes/strategies.py
# (router registered first; this copy was shadowed dead code). Removed during the
# PAPER_UAT 4-book change; the router version accepts UAT (legacy PAPER_UAT aliased).


@app.post("/api/strategies/execute-order")
def execute_strategy_order(payload: dict, db: Session = Depends(get_db)):
    """
    Execute an order based on execution mode:
    - SIMULATION: Record in database only
    - PAPER_TRADING: Send to IBKR paper account
    - LIVE_TRADING: Send to IBKR live account
    """
    strategy_id = payload.get("strategy_id")
    ticker = payload.get("ticker")
    side = payload.get("side")  # BUY or SELL
    quantity = payload.get("quantity", 100)
    order_type = payload.get("order_type", "MKT")

    # Get strategy execution mode
    strategy = db.execute(text("""
        SELECT strategy_id, name, execution_mode
        FROM gold.strategy_registry
        WHERE strategy_id = :strategy_id
    """), {"strategy_id": strategy_id}).fetchone()

    if not strategy:
        raise HTTPException(status_code=404, detail="Strategy not found")

    execution_mode = strategy.execution_mode or "SIMULATION"

    # Log the execution attempt
    db.execute(text("""
        INSERT INTO gold.trade_executions
        (strategy_id, ticker, execution_mode, order_type, side, quantity, status)
        VALUES (:strategy_id, :ticker, :mode, :order_type, :side, :qty, 'PENDING')
    """), {
        "strategy_id": strategy_id,
        "ticker": ticker,
        "mode": execution_mode,
        "order_type": order_type,
        "side": side,
        "qty": quantity
    })

    db.commit()

    event_bus.publish_sync("order_placed", {
        "strategy_id": strategy_id, "ticker": ticker, "side": side,
        "quantity": quantity, "execution_mode": execution_mode,
    })

    if execution_mode == "SIMULATION":
        # Simulation mode - just update database
        if side == "BUY":
            db.execute(text("""
                UPDATE consumption.portfolio_positions_current
                SET invested_capital = invested_capital + :amount,
                    available_capital = available_capital - :amount,
                    trades_count = trades_count + 1,
                    last_order_status = 'SIMULATED_BUY'
                WHERE strategy_id = :strategy_id AND ticker = :ticker
            """), {"strategy_id": strategy_id, "ticker": ticker, "amount": quantity * 100})
        else:
            db.execute(text("""
                UPDATE consumption.portfolio_positions_current
                SET invested_capital = GREATEST(0, invested_capital - :amount),
                    available_capital = available_capital + :amount,
                    trades_count = trades_count + 1,
                    last_order_status = 'SIMULATED_SELL'
                WHERE strategy_id = :strategy_id AND ticker = :ticker
            """), {"strategy_id": strategy_id, "ticker": ticker, "amount": quantity * 100})

        db.commit()

        return {
            "success": True,
            "execution_mode": "SIMULATION",
            "message": f"Simulated {side} order for {quantity} shares of {ticker}",
            "order_id": f"SIM_{int(time.time())}",
            "status": "COMPLETED"
        }

    elif execution_mode in ["PAPER_TRADING", "LIVE_TRADING"]:
        # TODO: Implement actual IBKR order submission
        # For now, return pending status
        return {
            "success": True,
            "execution_mode": execution_mode,
            "message": f"{execution_mode} order submitted for {ticker}",
            "order_id": f"PENDING_{int(time.time())}",
            "status": "PENDING",
            "note": "IBKR integration pending - order queued"
        }

    raise HTTPException(status_code=400, detail="Unknown execution mode")


@app.post("/api/strategies/execute-jt-ready")
async def execute_jt_ready_strategies(db: Session = Depends(get_db)):
    """
    Manually trigger JT-Ready strategy execution cycle.
    Evaluates all active positions and executes trades based on signals.
    """
    from app.services.jt_strategy_executor import get_executor

    try:
        executor = get_executor(db)

        # Get current mode
        mode_result = db.execute(text("SELECT value FROM gold.platform_settings WHERE key = 'global_execution_mode'")).fetchone()
        current_mode = mode_result.value if mode_result else 'SIMULATION'
        executor.set_execution_mode(current_mode)

        # Run execution
        trades_executed = await executor.run_execution_cycle()

        return {
            "success": True,
            "execution_mode": current_mode,
            "trades_executed": trades_executed,
            "message": f"Execution cycle completed. {trades_executed} trades executed in {current_mode} mode."
        }
    except Exception as e:
        logger.error(f"JT-Ready execution error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/strategies/{strategy_id:path}/mode")
def get_execution_mode(strategy_id: str, db: Session = Depends(get_db)):
    """Get current execution mode for a strategy"""
    result = db.execute(text("""
        SELECT strategy_id, name, execution_mode
        FROM gold.strategy_registry
        WHERE strategy_id = :strategy_id
    """), {"strategy_id": strategy_id}).fetchone()

    if not result:
        raise HTTPException(status_code=404, detail="Strategy not found")

    api_mode = registry_to_api_mode(result.execution_mode)

    # Count positions by mode
    sim_count = db.execute(text("""
        SELECT COUNT(*) FROM consumption.portfolio_positions_current
        WHERE strategy_id = :strategy_id AND execution_mode = 'SIMULATION'
    """), {"strategy_id": strategy_id}).scalar() or 0

    return {
        "strategy_id": result.strategy_id,
        "strategy_name": result.name,
        "execution_mode": api_mode,
        "venue": "IBKR",
        "positions_count": sim_count,
        "available_modes": ["SIMULATION", "PAPER_TRADING", "LIVE_TRADING"],
        "risk_level": {
            "SIMULATION": "ZERO",
            "PAPER_TRADING": "LOW",
            "LIVE_TRADING": "HIGH"
        }.get(api_mode, "UNKNOWN")
    }


@app.post("/api/strategies/add-to-paper")
def add_stocks_to_paper_trading(payload: dict, db: Session = Depends(get_db)):
    """
    Add selected stocks to paper trading for a strategy
    payload: {
        "strategy_id": "araso_factor_model",
        "tickers": ["AAPL", "MSFT"],
        "capital_per_position": 5000
    }
    """
    strategy_id = payload.get("strategy_id")
    tickers = payload.get("tickers", [])
    capital = payload.get("capital_per_position", 10000)

    if not strategy_id or not tickers:
        raise HTTPException(status_code=400, detail="strategy_id and tickers required")

    # Get strategy definition
    registry_row = db.execute(text("""
        SELECT * FROM gold.strategy_registry
        WHERE strategy_id = :sid 
    """), {"sid": strategy_id}).fetchone()

    strategy = registry_row

    if not strategy:
        # Check if it's a regular template
        strategy = db.execute(text("""
            SELECT * FROM gold.strategy_templates
            WHERE id = :sid
        """), {"sid": strategy_id}).fetchone()

    if not strategy:
        raise HTTPException(status_code=404, detail=f"Strategy {strategy_id} not found")

    # For PAPER/SIMULATION registry strategies the paper ledger
    # (gold.paper_trades_synthetic, written by the ETL rebalancer and synced
    # into consumption.portfolio_positions_current) is the source of truth.
    # Do NOT write placeholder capital rows here.
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

    created = []
    failed = []

    for ticker in tickers:
        try:
            # Create paper trading strategy instance
            db.execute(text("""
                INSERT INTO consumption.portfolio_positions_current
                (strategy_id, ticker, capital, status, created_at, updated_at)
                VALUES (:strategy_id, :ticker, :capital, 'ACTIVE', NOW(), NOW())
                ON CONFLICT (strategy_id, ticker) DO UPDATE SET
                    status = 'ACTIVE',
                    capital = EXCLUDED.capital,
                    updated_at = NOW()
            """), {
                "strategy_id": strategy_id,
                "ticker": ticker.upper(),
                "capital": capital
            })
            created.append(ticker)
        except Exception as e:
            failed.append({"ticker": ticker, "error": str(e)})

    db.commit()

    return {
        "success": True,
        "strategy_id": strategy_id,
        "added": created,
        "failed": failed,
        "total_added": len(created)
    }


@app.get("/api/strategies/{strategy_id:path}/description")
def get_strategy_description(strategy_id: str, db: Session = Depends(get_db)):
    """Get detailed description for a strategy"""
    # Try researcher strategies first
    result = db.execute(text("""
        SELECT
            strategy_id as id,
            name,
            description,
            asset_class,
            universe_tickers,
            frequency,
            sharpe_oos,
            max_drawdown_oos,
            win_rate_oos,
            trade_count_oos,
            profit_factor_oos,
            returns_oos,
            assigned_capital,
            signal_logic,
            exit_logic,
            execution_mode,
            status,
            priority
        FROM gold.strategy_registry
        WHERE strategy_id = :sid 
    """), {"sid": strategy_id}).fetchone()

    if result:
        raw_universe = result.universe_tickers or []
        if isinstance(raw_universe, str):
            raw_universe = [t.strip() for t in raw_universe.split(',') if t.strip()]
        tickers = [t for t in raw_universe if t and t.upper() != 'CASH']

        return {
            "id": result.id,
            "name": result.name,
            "description": result.description,
            "asset_class": result.asset_class,
            "direction": "LONG",
            "time_horizon": result.frequency,
            "metrics": {
                "sharpe_ratio": float(result.sharpe_oos) if result.sharpe_oos else None,
                "max_drawdown": float(result.max_drawdown_oos) if result.max_drawdown_oos else None,
                "win_rate": float(result.win_rate_oos) if result.win_rate_oos else None,
                "avg_hold_days": None,
                "universe_count": len(tickers),
                "max_position_pct": 0.05,
                "capacity_millions": None
            },
            "venue": "IBKR",
            "backtest_period": None,
            "source": "trade_algo_researcher"
        }

    # Fall back to regular templates
    result = db.execute(text("""
        SELECT id, name, description, asset_class, min_win_rate, min_sharpe, max_holding_days
        FROM gold.strategy_templates
        WHERE id = :sid
    """), {"sid": strategy_id}).fetchone()

    if result:
        return {
            "id": result.id,
            "name": result.name,
            "description": result.description,
            "asset_class": result.asset_class,
            "metrics": {
                "min_win_rate": float(result.min_win_rate) if result.min_win_rate else None,
                "min_sharpe": float(result.min_sharpe) if result.min_sharpe else None,
                "max_holding_days": result.max_holding_days
            },
            "source": "template"
        }

    raise HTTPException(status_code=404, detail=f"Strategy {strategy_id} not found")


# --- STRATEGY SCREENER APIs ---

@app.get("/api/strategies/templates")
def get_strategy_templates(asset_class: str = None):
    """Get all available strategy templates for screening"""
    from app.core_logic.strategies.strategy_config import get_all_strategy_templates

    templates = get_all_strategy_templates()

    # Filter by asset class if provided
    if asset_class:
        templates = [t for t in templates if t.asset_class == asset_class]

    return [{
        "id": t.id,
        "name": t.name,
        "description": t.description,
        "asset_class": t.asset_class,
        "min_win_rate": t.min_win_rate,
        "min_sharpe": t.min_sharpe,
        "max_holding_days": t.max_holding_days
    } for t in templates]


@app.get("/api/strategies/screen/{strategy_id:path}")
def screen_stocks(strategy_id: str,
                  min_win_rate: float = 0.5,
                  min_sharpe: float = 0.8,
                  max_drawdown: float = 15.0,
                  market: str = None,
                  limit: int = 50,
                  db: Session = Depends(get_db)):
    """
    Screen all stocks with a specific strategy using pre-computed backtests

    Returns stocks ranked by strategy_score
    """
    # Verify strategy exists (templates or researcher)
    strategy = db.execute(text("""
        SELECT id, name, description, asset_class
        FROM gold.strategy_templates
        WHERE id = :strategy_id
    """), {"strategy_id": strategy_id}).fetchone()

    # Fall back to researcher strategies from trade-algo-researcher
    if not strategy:
        strategy = db.execute(text("""
            SELECT strategy_id as id, name, description, asset_class
            FROM gold.strategy_registry
            WHERE strategy_id = :strategy_id 
        """), {"strategy_id": strategy_id}).fetchone()

    if not strategy:
        raise HTTPException(status_code=404, detail=f"Strategy {strategy_id} not found")

    # Build query with filters
    market_filter = "AND b.market = :market" if market else ""
    query_params = {
        "strategy_id": strategy_id,
        "min_win_rate": min_win_rate / 100,  # Convert percentage to decimal
        "min_sharpe": min_sharpe,
        "max_drawdown": max_drawdown,
        "limit": limit
    }
    if market:
        query_params["market"] = market

    # Query pre-computed backtest results
    result = db.execute(text(f"""
        SELECT
            b.ticker,
            b.market,
            b.win_rate,
            b.sharpe_ratio,
            b.profit_factor,
            b.total_return,
            b.max_drawdown,
            b.num_trades,
            b.avg_trade_return,
            b.current_signal,
            b.signal_strength,
            b.entry_price,
            b.stop_loss,
            b.target_price,
            b.strategy_score,
            b.rationale,
            b.calculated_at,
            s.close_price as current_price
        FROM gold.strategy_backtests b
        LEFT JOIN LATERAL (
            SELECT close_price
            FROM consumption.stock
            WHERE ticker = b.ticker
            ORDER BY timestamp DESC
            LIMIT 1
        ) s ON true
        WHERE b.strategy_id = :strategy_id
        AND b.win_rate >= :min_win_rate
        AND b.sharpe_ratio >= :min_sharpe
        AND b.max_drawdown <= :max_drawdown
        {market_filter}
        ORDER BY b.strategy_score DESC
        LIMIT :limit
    """), query_params).fetchall()

    if not result:
        # Return empty result with last updated time
        last_update = db.execute(text("""
            SELECT MAX(calculated_at) FROM gold.strategy_backtests
            WHERE strategy_id = :strategy_id
        """), {"strategy_id": strategy_id}).fetchone()

        return {
            "strategy": {
                "id": strategy.id,
                "name": strategy.name,
                "description": strategy.description
            },
            "filters": {
                "min_win_rate": min_win_rate,
                "min_sharpe": min_sharpe,
                "max_drawdown": max_drawdown,
                "market": market
            },
            "results": [],
            "total": 0,
            "last_updated": last_update[0].isoformat() if last_update and last_update[0] else None,
            "message": "No results match your filters. Try adjusting thresholds."
        }

    # Format results
    results = [{
        "rank": i + 1,
        "ticker": row.ticker,
        "market": row.market,
        "current_price": row.current_price or row.entry_price,
        "strategy_score": float(row.strategy_score) if row.strategy_score else 0,
        "win_rate": float(row.win_rate) if row.win_rate else 0,
        "sharpe_ratio": float(row.sharpe_ratio) if row.sharpe_ratio else 0,
        "profit_factor": float(row.profit_factor) if row.profit_factor else 0,
        "total_return": float(row.total_return) if row.total_return else 0,
        "max_drawdown": float(row.max_drawdown) if row.max_drawdown else 0,
        "num_trades": row.num_trades or 0,
        "avg_trade_return": float(row.avg_trade_return) if row.avg_trade_return else 0,
        "signal": row.current_signal or "HOLD",
        "signal_strength": float(row.signal_strength) if row.signal_strength else 0,
        "entry_price": float(row.entry_price) if row.entry_price else None,
        "stop_loss": float(row.stop_loss) if row.stop_loss else None,
        "target": float(row.target_price) if row.target_price else None,
        "rationale": row.rationale or ""
    } for i, row in enumerate(result)]

    # Get last updated time
    last_update = db.execute(text("""
        SELECT MAX(calculated_at) FROM gold.strategy_backtests
        WHERE strategy_id = :strategy_id
    """), {"strategy_id": strategy_id}).fetchone()

    return {
        "strategy": {
            "id": strategy.id,
            "name": strategy.name,
            "description": strategy.description,
            "asset_class": strategy.asset_class
        },
        "filters": {
            "min_win_rate": min_win_rate,
            "min_sharpe": min_sharpe,
            "max_drawdown": max_drawdown,
            "market": market
        },
        "results": results,
        "total": len(results),
        "last_updated": last_update[0].isoformat() if last_update and last_update[0] else None
    }


@app.get("/api/strategies/export/{strategy_id}")
def export_strategy_results(
    strategy_id: str,
    format: str = "csv",
    min_win_rate: float = 0.5,
    min_sharpe: float = 0.8,
    market: str = None,
    db: Session = Depends(get_db)
):
    """
    Export screening results to CSV

    Query: format=csv|json
    """
    from fastapi.responses import StreamingResponse
    import csv
    import io

    # Query backtest results
    market_filter = "AND b.market = :market" if market else ""
    query_params = {
        "strategy_id": strategy_id,
        "min_win_rate": min_win_rate / 100,
        "min_sharpe": min_sharpe,
        "limit": 1000
    }
    if market:
        query_params["market"] = market

    result = db.execute(text(f"""
        SELECT
            b.ticker,
            b.market,
            b.win_rate,
            b.sharpe_ratio,
            b.profit_factor,
            b.total_return,
            b.max_drawdown,
            b.num_trades,
            b.current_signal,
            b.strategy_score,
            b.entry_price,
            b.stop_loss,
            b.target_price
        FROM gold.strategy_backtests b
        WHERE b.strategy_id = :strategy_id
        AND b.win_rate >= :min_win_rate
        AND b.sharpe_ratio >= :min_sharpe
        {market_filter}
        ORDER BY b.strategy_score DESC
        LIMIT :limit
    """), query_params).fetchall()

    if format == "csv":
        output = io.StringIO()
        writer = csv.writer(output)

        # Header
        writer.writerow([
            "Rank", "Ticker", "Market", "Signal", "Score",
            "Win Rate", "Sharpe", "Profit Factor", "Total Return %",
            "Max DD %", "Trades", "Entry", "Stop", "Target"
        ])

        # Data
        for i, row in enumerate(result, 1):
            writer.writerow([
                i,
                row.ticker,
                row.market,
                row.current_signal or "HOLD",
                f"{row.strategy_score:.3f}" if row.strategy_score else "0",
                f"{row.win_rate * 100:.1f}%" if row.win_rate else "0%",
                f"{row.sharpe_ratio:.2f}" if row.sharpe_ratio else "0",
                f"{row.profit_factor:.2f}" if row.profit_factor else "0",
                f"{row.total_return:.2f}%" if row.total_return else "0%",
                f"{row.max_drawdown:.2f}%" if row.max_drawdown else "0%",
                row.num_trades or 0,
                f"${row.entry_price:.2f}" if row.entry_price else "",
                f"${row.stop_loss:.2f}" if row.stop_loss else "",
                f"${row.target_price:.2f}" if row.target_price else ""
            ])

        output.seek(0)

        return StreamingResponse(
            io.BytesIO(output.getvalue().encode()),
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename={strategy_id}_screening.csv"
            }
        )

    else:
        # JSON format
        return {
            "strategy_id": strategy_id,
            "results": [{
                "rank": i + 1,
                "ticker": row.ticker,
                "market": row.market,
                "signal": row.current_signal,
                "score": float(row.strategy_score) if row.strategy_score else 0,
                "win_rate": float(row.win_rate) if row.win_rate else 0,
                "sharpe": float(row.sharpe_ratio) if row.sharpe_ratio else 0
            } for i, row in enumerate(result)]
        }


@app.get("/api/strategies/compare")
def compare_strategies(tickers: str = "AAPL,MSFT,NVDA"):
    """
    Compare how different strategies perform on the same set of stocks

    Query: tickers=comma-separated list
    """
    from app.core_logic.strategies.strategy_config import get_all_strategy_templates
    from app.core_logic.strategies.strategy_screener import screen_stocks_with_strategy

    ticker_list = [t.strip() for t in tickers.split(",") if t.strip()]
    templates = get_all_strategy_templates()

    comparison = {}

    for template in templates:
        results = screen_stocks_with_strategy(
            strategy_id=template.id,
            tickers=ticker_list,
            min_trades=3
        )

        comparison[template.id] = {
            "name": template.name,
            "stocks": [{
                "ticker": r.ticker,
                "score": r.strategy_score,
                "win_rate": r.win_rate,
                "sharpe": r.sharpe_ratio,
                "signal": r.signal
            } for r in results]
        }

    return {
        "tickers": ticker_list,
        "strategies": comparison
    }


# --- INSTITUTIONAL HOLDINGS & ANALYST RATINGS APIs ---

@app.get("/api/stocks/{ticker}/institutional")
def get_institutional_data(ticker: str, db: Session = Depends(get_db)):
    """Get institutional holdings and analyst ratings for a stock"""
    ticker = ticker.upper()

    # Get consensus ratings
    consensus = db.execute(text("""
        SELECT * FROM gold.consensus_ratings
        WHERE ticker = :ticker
        ORDER BY report_date DESC
        LIMIT 1
    """), {"ticker": ticker}).fetchone()

    # Get top institutional holders
    holders = db.execute(text("""
        SELECT holder_name, shares, pct_out, value
        FROM gold.institutional_holdings
        WHERE ticker = :ticker
        ORDER BY shares DESC
        LIMIT 10
    """), {"ticker": ticker}).fetchall()

    if not consensus and not holders:
        raise HTTPException(status_code=404, detail=f"No institutional data for {ticker}")

    return {
        "ticker": ticker,
        "consensus": {
            "strong_buy": consensus.strong_buy if consensus else 0,
            "buy": consensus.buy if consensus else 0,
            "hold": consensus.hold if consensus else 0,
            "sell": consensus.sell if consensus else 0,
            "strong_sell": consensus.strong_sell if consensus else 0,
            "total_analysts": consensus.total_analysts if consensus else 0,
            "target_mean": float(consensus.target_mean) if consensus and consensus.target_mean else None,
            "target_high": float(consensus.target_high) if consensus and consensus.target_high else None,
            "target_low": float(consensus.target_low) if consensus and consensus.target_low else None,
            "current_price": float(consensus.current_price) if consensus and consensus.current_price else None,
            "upside_pct": float(consensus.upside_pct) if consensus and consensus.upside_pct else None,
            "rating": calculate_rating_text(consensus) if consensus else "N/A"
        } if consensus else None,
        "institutional_holders": [{
            "holder": h.holder_name,
            "shares": h.shares,
            "pct_out": float(h.pct_out) if h.pct_out else None,
            "value": h.value
        } for h in holders],
        "total_institutional_shares": sum([h.shares for h in holders]) if holders else 0
    }

def calculate_rating_text(consensus):
    """Convert consensus numbers to rating text"""
    if not consensus or consensus.total_analysts == 0:
        return "N/A"

    buy_ratio = (consensus.strong_buy + consensus.buy) / consensus.total_analysts

    if buy_ratio >= 0.8:
        return "STRONG_BUY"
    elif buy_ratio >= 0.6:
        return "BUY"
    elif buy_ratio >= 0.4:
        return "HOLD"
    elif buy_ratio >= 0.2:
        return "SELL"
    else:
        return "STRONG_SELL"


@app.get("/api/stocks/consensus/top-upside")
def get_top_upside_stocks(limit: int = 20, db: Session = Depends(get_db)):
    """Get stocks with highest analyst upside potential"""
    result = db.execute(text("""
        SELECT
            c.ticker,
            c.target_mean,
            c.current_price,
            c.upside_pct,
            c.total_analysts,
            (c.strong_buy + c.buy) as buy_count,
            c.hold,
            (c.sell + c.strong_sell) as sell_count
        FROM gold.consensus_ratings c
        WHERE c.upside_pct IS NOT NULL
        AND c.total_analysts >= 5
        ORDER BY c.upside_pct DESC
        LIMIT :limit
    """), {"limit": limit}).fetchall()

    return [{
        "ticker": r.ticker,
        "target": float(r.target_mean) if r.target_mean else None,
        "current": float(r.current_price) if r.current_price else None,
        "upside_pct": float(r.upside_pct) if r.upside_pct else None,
        "analysts": r.total_analysts,
        "buy": r.buy_count,
        "hold": r.hold,
        "sell": r.sell_count,
        "rating": "STRONG_BUY" if (r.buy_count / r.total_analysts) > 0.7 else "BUY" if (r.buy_count / r.total_analysts) > 0.5 else "HOLD"
    } for r in result]


@app.get("/api/strategies/stats")
def get_strategy_stats_endpoint(db: Session = Depends(get_db)):
    """Get actual performance stats for all deployed strategies including actual win rate"""
    result = db.execute(text("""
        SELECT
            ps.strategy_id,
            sd.name as strategy_name,
            COUNT(*) as total_positions,
            SUM(CASE WHEN ps.trades_count > 0 THEN 1 ELSE 0 END) as active_positions,
            SUM(CASE WHEN ps.trades_count = 0 THEN 1 ELSE 0 END) as pending_positions,
            SUM(COALESCE(ps.invested_capital, 0)) as total_invested,
            SUM(COALESCE(ps.realized_pnl, 0)) as total_realized_pnl,
            SUM(COALESCE(ps.unrealized_pnl, 0)) as total_unrealized_pnl,
            SUM(ps.capital) as total_allocated,
            COUNT(CASE WHEN (COALESCE(ps.realized_pnl, 0) + COALESCE(ps.unrealized_pnl, 0)) > 0 THEN 1 END) as winning_positions,
            SUM(ps.trades_count) as total_trades
        FROM consumption.portfolio_positions_current ps
        LEFT JOIN gold.strategy_registry sd ON ps.strategy_id = sd.strategy_id
        WHERE ps.status = 'ACTIVE'
        GROUP BY ps.strategy_id, sd.name
    """)).fetchall()

    stats = {}
    for row in result:
        strategy_id = row.strategy_id
        total_pnl = (row.total_realized_pnl or 0) + (row.total_unrealized_pnl or 0)
        win_rate = (row.winning_positions / row.active_positions * 100) if row.active_positions and row.active_positions > 0 else 0

        stats[strategy_id] = {
            "strategy_id": strategy_id,
            "strategy_name": row.strategy_name,
            "total_positions": row.total_positions,
            "active_positions": row.active_positions,
            "pending_positions": row.pending_positions,
            "total_invested": float(row.total_invested or 0),
            "total_allocated": float(row.total_allocated or 0),
            "total_realized_pnl": float(row.total_realized_pnl or 0),
            "total_unrealized_pnl": float(row.total_unrealized_pnl or 0),
            "total_pnl": total_pnl,
            "winning_positions": row.winning_positions,
            "actual_win_rate": round(win_rate, 1),
            "total_trades": row.total_trades or 0
        }

    return {"success": True, "stats": stats, "count": len(stats)}


@app.get("/api/positions/signals")
def get_position_signals(db: Session = Depends(get_db)):
    """
    Get current signal status for all positions.
    Shows real-time metrics and how close each position is to triggering buy/sell.
    """
    from app.services.jt_strategy_executor import JTStrategyExecutor

    executor = JTStrategyExecutor(db)
    positions = executor.get_active_paper_positions()

    signals = []
    for pos in positions:
        ticker = pos['ticker'].strip().strip('"').strip("[").strip("]")

        # Fetch market data
        df = executor.fetch_market_data(ticker, period="10d")

        if df is None or df.empty:
            signals.append({
                "position_id": pos['id'],
                "ticker": ticker,
                "strategy_id": pos['strategy_id'],
                "strategy_name": pos['strategy_name'],
                "status": pos['status'],
                "invested": pos['invested_capital'] > 0,
                "signal_status": "NO_DATA",
                "metrics": {},
                "buy_signal": False,
                "sell_signal": False,
                "message": "No market data available"
            })
            continue

        closes = df['Close']
        volumes = df['Volume']
        current_price = closes.iloc[-1]
        current_volume = volumes.iloc[-1]
        avg_volume = volumes.mean()

        strategy_id = pos['strategy_id']
        metrics = {}
        buy_signal = False
        sell_signal = False
        message = ""
        signal_strength = 0  # 0-100 how close to triggering

        # Calculate metrics based on strategy type
        if 'rsi' in strategy_id.lower():
            rsi = executor.calculate_rsi(closes).iloc[-1]
            volume_spike = current_volume / avg_volume if avg_volume > 0 else 1

            metrics = {
                "rsi": round(rsi, 2),
                "rsi_threshold_buy": 30,
                "rsi_threshold_sell": 50,
                "volume_spike": round(volume_spike, 2),
                "volume_threshold": 1.3,
                "current_price": round(current_price, 2)
            }

            if pos['invested_capital'] == 0:
                # Looking for buy signal
                buy_signal = rsi < 30 and volume_spike > 1.3
                signal_strength = max(0, min(100, (30 - rsi) / 30 * 100)) if rsi < 50 else 0
                if volume_spike < 1.3:
                    signal_strength *= 0.5  # Volume not there yet
                message = f"RSI {rsi:.1f} (buy <30), Volume {volume_spike:.1f}x (need >1.3x)"
            else:
                # Looking for sell signal
                sell_signal = rsi > 50
                signal_strength = max(0, min(100, (rsi - 50) / 50 * 100)) if rsi > 50 else 0
                message = f"RSI {rsi:.1f} (sell >50)"

        elif 'three_day' in strategy_id.lower() or '3day' in strategy_id.lower():
            if len(df) >= 4:
                day1_change = (closes.iloc[-3] - closes.iloc[-4]) / closes.iloc[-4] * 100
                day2_change = (closes.iloc[-2] - closes.iloc[-3]) / closes.iloc[-3] * 100
                day3_change = (closes.iloc[-1] - closes.iloc[-2]) / closes.iloc[-2] * 100
                total_decline = (closes.iloc[-1] - closes.iloc[-4]) / closes.iloc[-4] * 100
                volume_spike = current_volume / avg_volume if avg_volume > 0 else 1

                metrics = {
                    "day1_change": round(day1_change, 2),
                    "day2_change": round(day2_change, 2),
                    "day3_change": round(day3_change, 2),
                    "total_decline_pct": round(total_decline, 2),
                    "decline_threshold": -5,
                    "volume_spike": round(volume_spike, 2),
                    "volume_threshold": 1.3,
                    "current_price": round(current_price, 2)
                }

                three_down = day1_change < 0 and day2_change < 0 and day3_change < 0

                if pos['invested_capital'] == 0:
                    buy_signal = three_down and total_decline <= -5 and volume_spike > 1.3
                    signal_strength = max(0, min(100, abs(total_decline) / 5 * 100)) if three_down else 0
                    message = f"3Down: {three_down}, Decline: {total_decline:.1f}% (need <-5%), Vol: {volume_spike:.1f}x"
                else:
                    # Exit when price recovers
                    entry_price = pos['entry_price'] or current_price
                    recovery = (current_price - entry_price) / entry_price * 100
                    sell_signal = recovery > 0
                    signal_strength = max(0, min(100, recovery / 3 * 100))
                    message = f"Recovery: {recovery:.1f}% from entry"

        elif 'gap' in strategy_id.lower():
            if len(df) >= 2:
                prev_close = closes.iloc[-2]
                gap = (closes.iloc[-1] - prev_close) / prev_close * 100

                metrics = {
                    "gap_pct": round(gap, 2),
                    "gap_threshold": 0.5,
                    "prev_close": round(prev_close, 2),
                    "current_price": round(current_price, 2)
                }

                if pos['invested_capital'] == 0:
                    buy_signal = abs(gap) > 0.5
                    signal_strength = max(0, min(100, abs(gap) / 0.5 * 100))
                    message = f"Gap: {gap:.2f}% (threshold ±0.5%)"
                else:
                    # Intraday exit
                    entry_price = pos['entry_price'] or current_price
                    pnl = (current_price - entry_price) / entry_price * 100
                    sell_signal = abs(pnl) > 0.5
                    signal_strength = max(0, min(100, abs(pnl) / 0.5 * 100))
                    message = f"P&L: {pnl:.2f}% (exit at ±0.5%)"

        elif 'momentum' in strategy_id.lower():
            if len(df) >= 20:
                price_20d_ago = closes.iloc[-20]
                momentum = (current_price - price_20d_ago) / price_20d_ago * 100

                metrics = {
                    "momentum_20d": round(momentum, 2),
                    "momentum_threshold": 5,
                    "price_20d_ago": round(price_20d_ago, 2),
                    "current_price": round(current_price, 2)
                }

                if pos['invested_capital'] == 0:
                    buy_signal = momentum > 5
                    signal_strength = max(0, min(100, momentum / 5 * 100))
                    message = f"20D Momentum: {momentum:.1f}% (buy >5%)"
                else:
                    entry_price = pos['entry_price'] or current_price
                    current_momentum = (current_price - entry_price) / entry_price * 100
                    sell_signal = current_momentum < 0
                    signal_strength = max(0, min(100, (5 - current_momentum) / 5 * 100)) if current_momentum < 5 else 0
                    message = f"Position momentum: {current_momentum:.1f}% (exit <0%)"

        elif 'macd' in strategy_id.lower():
            macd_line, signal_line, hist = executor.calculate_macd(closes)
            current_hist = hist.iloc[-1]
            prev_hist = hist.iloc[-2] if len(hist) > 1 else current_hist

            metrics = {
                "macd_histogram": round(current_hist, 4),
                "macd_signal": round(signal_line.iloc[-1], 4),
                "prev_histogram": round(prev_hist, 4),
                "current_price": round(current_price, 2)
            }

            # Divergence check
            price_change = closes.iloc[-1] - closes.iloc[-3]
            hist_change = current_hist - prev_hist
            divergence = (price_change > 0 and hist_change < 0) or (price_change < 0 and hist_change > 0)

            if pos['invested_capital'] == 0:
                buy_signal = divergence
                signal_strength = 80 if divergence else 0
                message = f"Divergence: {divergence}, Histogram: {current_hist:.4f}"
            else:
                sell_signal = current_hist > 0  # MACD crosses zero
                signal_strength = max(0, min(100, current_hist / 0.01 * 100)) if current_hist > 0 else 0
                message = f"Histogram: {current_hist:.4f} (exit when >0)"

        # Generic exit logic for ALL active positions - Take Profit +5%, Stop Loss -5%
        entry_price = pos.get('entry_price') or current_price
        if entry_price and pos.get('invested_capital', 0) > 0:
            pnl_pct = (current_price - entry_price) / entry_price * 100

            # Take Profit at +5%
            if pnl_pct >= 5:
                sell_signal = True
                signal_strength = 100
                message = f"🎯 TAKE PROFIT: +{pnl_pct:.1f}% (target +5%)"
            # Stop Loss at -5%
            elif pnl_pct <= -5:
                sell_signal = True
                signal_strength = 100
                message = f"🛑 STOP LOSS: {pnl_pct:.1f}% (limit -5%)"
            # Approaching take profit
            elif pnl_pct > 0:
                sell_signal = False
                signal_strength = min(100, (pnl_pct / 5) * 100)  # % toward +5% target
                message = f"📈 Profitable: +{pnl_pct:.1f}% (sell at +5%)"
            # Approaching stop loss
            else:
                sell_signal = False
                signal_strength = min(100, (abs(pnl_pct) / 5) * 100)  # % toward -5% limit
                message = f"📉 Losing: {pnl_pct:.1f}% (stop at -5%)"

            # Add P&L to metrics for all positions
            metrics["pnl_pct"] = round(pnl_pct, 2)
            metrics["entry_price"] = round(entry_price, 2)
            metrics["take_profit_target"] = round(entry_price * 1.05, 2)
            metrics["stop_loss_limit"] = round(entry_price * 0.95, 2)

        signals.append({
            "position_id": pos['id'],
            "ticker": ticker,
            "strategy_id": strategy_id,
            "strategy_name": pos['strategy_name'],
            "status": pos['status'],
            "invested": pos['invested_capital'] > 0,
            "signal_status": "BUY" if buy_signal else "SELL" if sell_signal else "HOLD",
            "signal_strength": round(float(signal_strength), 1) if not np.isnan(signal_strength) else 0,
            "metrics": {k: (float(v) if isinstance(v, (np.floating, float)) and not np.isnan(v) else 0 if isinstance(v, (np.floating, float)) and np.isnan(v) else int(v) if isinstance(v, (np.integer, int)) else bool(v) if isinstance(v, np.bool_) else v) for k, v in metrics.items()},
            "buy_signal": bool(buy_signal),
            "sell_signal": bool(sell_signal),
            "message": message
        })

    return {
        "success": True,
        "signals": signals,
        "count": len(signals),
        "timestamp": datetime.datetime.now().isoformat()
    }


# =============================================================================
# HKEX IPO DATA APIs
# =============================================================================

@app.get("/api/hkex/ipos")
def get_hkex_ipos(
    status: str = None,
    sector: str = None,
    year: int = None,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """
    Get HKEX IPO data with optional filtering

    Query params:
    - status: 'upcoming', 'listed', 'all'
    - sector: Filter by sector
    - year: Filter by listing year
    - limit: Max results (default: 50)
    """
    query = """
        SELECT
            c.ticker,
            c.stock_name,
            c.listing_date,
            c.offer_price,
            c.market_cap_hkd,
            c.sector,
            c.sub_sector,
            c.sponsor,
            d.oversubscription_retail,
            d.oversubscription_institutional,
            d.cornerstone_total_pct,
            p.first_day_return_pct,
            p.return_day30_pct,
            p.performance_tier,
            CASE
                WHEN c.listing_date > CURRENT_DATE THEN 'Upcoming'
                WHEN c.listing_date = CURRENT_DATE THEN 'Listing Today'
                ELSE 'Listed'
            END as status
        FROM gold.hk_ipo_calendar c
        LEFT JOIN gold.hk_ipo_details d ON c.ticker = d.ticker
        LEFT JOIN gold.hk_ipo_performance p ON c.ticker = p.ticker
        WHERE 1=1
    """

    params = {}

    if status == 'upcoming':
        query += " AND c.listing_date >= CURRENT_DATE"
    elif status == 'listed':
        query += " AND c.listing_date < CURRENT_DATE"

    if sector:
        query += " AND c.sector = :sector"
        params['sector'] = sector

    if year:
        query += " AND EXTRACT(YEAR FROM c.listing_date) = :year"
        params['year'] = year

    query += " ORDER BY c.listing_date DESC LIMIT :limit"
    params['limit'] = limit

    result = db.execute(text(query), params).fetchall()

    return {
        "ipos": [{
            "ticker": r.ticker,
            "stock_name": r.stock_name,
            "listing_date": str(r.listing_date),
            "offer_price": float(r.offer_price) if r.offer_price else None,
            "market_cap_hkd": float(r.market_cap_hkd) if r.market_cap_hkd else None,
            "sector": r.sector,
            "sub_sector": r.sub_sector,
            "sponsor": r.sponsor,
            "oversubscription_retail": float(r.oversubscription_retail) if r.oversubscription_retail else None,
            "oversubscription_institutional": float(r.oversubscription_institutional) if r.oversubscription_institutional else None,
            "cornerstone_pct": float(r.cornerstone_total_pct) if r.cornerstone_total_pct else None,
            "first_day_return": float(r.first_day_return_pct) if r.first_day_return_pct else None,
            "return_day30": float(r.return_day30_pct) if r.return_day30_pct else None,
            "performance_tier": r.performance_tier,
            "status": r.status
        } for r in result],
        "count": len(result)
    }


@app.get("/api/hkex/ipos/leaderboard")
def get_hkex_ipo_leaderboard(
    period: str = "first_day",
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """
    Get HKEX IPO performance leaderboard

    Query params:
    - period: 'first_day', 'day30', 'total'
    - limit: Max results (default: 20)
    """
    order_col = {
        "first_day": "p.first_day_return_pct",
        "day30": "p.return_day30_pct",
        "total": "p.total_return_pct"
    }.get(period, "p.first_day_return_pct")

    result = db.execute(text(f"""
        SELECT
            c.ticker,
            c.stock_name,
            c.listing_date,
            c.offer_price,
            c.sector,
            p.first_day_return_pct,
            p.return_day30_pct,
            p.total_return_pct,
            p.performance_tier,
            d.oversubscription_retail,
            d.cornerstone_total_pct
        FROM gold.hk_ipo_performance p
        JOIN gold.hk_ipo_calendar c ON p.ticker = c.ticker
        LEFT JOIN gold.hk_ipo_details d ON p.ticker = d.ticker
        WHERE c.listing_date >= CURRENT_DATE - INTERVAL '2 years'
        ORDER BY {order_col} DESC NULLS LAST
        LIMIT :limit
    """), {"limit": limit}).fetchall()

    return {
        "leaderboard": [{
            "rank": i + 1,
            "ticker": r.ticker,
            "stock_name": r.stock_name,
            "listing_date": str(r.listing_date),
            "sector": r.sector,
            "first_day_return": float(r.first_day_return_pct) if r.first_day_return_pct else None,
            "return_day30": float(r.return_day30_pct) if r.return_day30_pct else None,
            "total_return": float(r.total_return_pct) if r.total_return_pct else None,
            "performance_tier": r.performance_tier,
            "oversubscription": float(r.oversubscription_retail) if r.oversubscription_retail else None,
            "cornerstone_pct": float(r.cornerstone_total_pct) if r.cornerstone_total_pct else None
        } for i, r in enumerate(result)],
        "count": len(result),
        "period": period
    }


@app.get("/api/hkex/ipos/sectors")
def get_hkex_ipo_sectors(db: Session = Depends(get_db)):
    """Get IPO performance by sector"""
    result = db.execute(text("""
        SELECT
            c.sector,
            COUNT(*) as ipo_count,
            AVG(p.first_day_return_pct) as avg_first_day_return,
            AVG(p.return_day30_pct) as avg_day30_return,
            COUNT(CASE WHEN p.first_day_return_pct > 0 THEN 1 END)::DECIMAL / COUNT(*) * 100 as win_rate
        FROM gold.hk_ipo_calendar c
        JOIN gold.hk_ipo_performance p ON c.ticker = p.ticker
        WHERE c.listing_date >= CURRENT_DATE - INTERVAL '2 years'
        GROUP BY c.sector
        ORDER BY avg_first_day_return DESC NULLS LAST
    """)).fetchall()

    return {
        "sectors": [{
            "sector": r.sector,
            "ipo_count": r.ipo_count,
            "avg_first_day_return": round(float(r.avg_first_day_return), 2) if r.avg_first_day_return else None,
            "avg_day30_return": round(float(r.avg_day30_return), 2) if r.avg_day30_return else None,
            "win_rate": round(float(r.win_rate), 1) if r.win_rate else None
        } for r in result]
    }


@app.get("/api/hkex/ipos/{ticker}")
def get_hkex_ipo_detail(ticker: str, db: Session = Depends(get_db)):
    """Get detailed information for a specific IPO"""
    # Calendar data
    calendar = db.execute(text("""
        SELECT * FROM gold.hk_ipo_calendar WHERE ticker = :ticker
    """), {"ticker": ticker}).fetchone()

    if not calendar:
        raise HTTPException(status_code=404, detail=f"IPO {ticker} not found")

    # Details
    details = db.execute(text("""
        SELECT * FROM gold.hk_ipo_details WHERE ticker = :ticker
    """), {"ticker": ticker}).fetchone()

    # Performance
    performance = db.execute(text("""
        SELECT * FROM gold.hk_ipo_performance WHERE ticker = :ticker
    """), {"ticker": ticker}).fetchone()

    return {
        "ticker": calendar.ticker,
        "stock_name": calendar.stock_name,
        "listing_date": str(calendar.listing_date),
        "offer_price": float(calendar.offer_price) if calendar.offer_price else None,
        "market_cap_hkd": float(calendar.market_cap_hkd) if calendar.market_cap_hkd else None,
        "sector": calendar.sector,
        "sub_sector": calendar.sub_sector,
        "sponsor": calendar.sponsor,
        "board": calendar.board,
        "details": {
            "oversubscription_retail": float(details.oversubscription_retail) if details and details.oversubscription_retail else None,
            "oversubscription_institutional": float(details.oversubscription_institutional) if details and details.oversubscription_institutional else None,
            "cornerstone_total_pct": float(details.cornerstone_total_pct) if details and details.cornerstone_total_pct else None,
            "lockup_period_days": details.lockup_period_days if details else None,
            "greenshoe_pct": float(details.greenshoe_pct) if details and details.greenshoe_pct else None
        } if details else None,
        "performance": {
            "first_day_return": float(performance.first_day_return_pct) if performance and performance.first_day_return_pct else None,
            "return_day30": float(performance.return_day30_pct) if performance and performance.return_day30_pct else None,
            "total_return": float(performance.total_return_pct) if performance and performance.total_return_pct else None,
            "performance_tier": performance.performance_tier if performance else None
        } if performance else None
    }


# Static SPA hosting from the production frontend build
# main.py is at backend/app/main.py, so go up two dirs from backend/app to workspace root, then into frontend/dist.
_FRONTEND_DIST = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "frontend", "dist")
if os.path.isdir(_FRONTEND_DIST):
    app.mount("/assets", StaticFiles(directory=os.path.join(_FRONTEND_DIST, "assets")), name="assets")

    @app.get("/")
    def serve_index():
        return FileResponse(os.path.join(_FRONTEND_DIST, "index.html"))

    @app.get("/{path:path}")
    def serve_spa(path: str):
        # API routes are handled first; unknown paths fall back to index.html for client-side routing
        if path.startswith("api/") or path.startswith("ws/"):
            raise HTTPException(status_code=404, detail="Not found")
        return FileResponse(os.path.join(_FRONTEND_DIST, "index.html"))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
