from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import text
from pydantic import BaseModel
import time
import yfinance as yf
import json
import datetime
import numpy as np
import logging

# Setup logger
logger = logging.getLogger(__name__)

# Internal Imports
from app.db.session import (
    SessionLocal, Base, engine, Inventory, GlobalState,
    ConsumptionStock, ConsumptionMarket, ConsumptionFx, ConsumptionCommodity, ConsumptionCrypto, Trade, QuantStrategy
)
from app.core_logic.data.wholistic_pipeline import (
    refresh_indices_and_mood, refresh_fx_layer, refresh_commodity_layer, refresh_crypto_layer, refresh_stock_layer, refresh_hft_layer,
    refresh_etf_layer, refresh_accruals_quality
)
from app.core_logic.agents.research_swarm import research_swarm
from app.api.stock_detail import router as stock_detail_router
from app.services.ib_service import ib_quant_service
from app.services.ib_web_service import ib_web_service

app = FastAPI()

# Include stock detail router
app.include_router(stock_detail_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://trade.jtcml.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from app.core_logic.agents.research_swarm import research_swarm
import asyncio

async def scheduler_loop():
    """
    Continuous background loop that checks gold.sync_schedules and triggers refreshes.
    """
    freq_map = {
        "1min": 60,
        "5min": 300,
        "1hr": 3600,
        "1day": 86400
    }
    
    while True:
        db = SessionLocal()
        try:
            schedules = db.execute(text("SELECT component, frequency, last_run FROM gold.sync_schedules WHERE frequency != 'pause'")).fetchall()
            now = datetime.datetime.now()
            
            for s in schedules:
                comp, freq, last_run = s
                interval = freq_map.get(freq)
                if not interval: continue
                
                should_run = False
                if last_run is None:
                    should_run = True
                else:
                    # last_run is in Asia/Hong_Kong time, adjust current time
                    hkt_now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).replace(tzinfo=None)
                    if (hkt_now - last_run).total_seconds() >= interval:
                        should_run = True
                
                if should_run:
                    print(f"Scheduler: Triggering refresh for {comp} (Frequency: {freq})")
                    # Update last_run immediately to prevent double triggers
                    db.execute(text("UPDATE gold.sync_schedules SET last_run = :lr WHERE component = :comp"), {"lr": datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).replace(tzinfo=None), "comp": comp})
                    db.commit()
                    
                    # Trigger the actual refresh task
                    if comp == 'indices': await refresh_indices_and_mood()
                    elif comp == 'stocks': 
                        await refresh_stock_layer()
                        # Iteration 56: Trigger automated trading evaluation after stock refresh
                        print("Scheduler: Evaluating Automated Trading Signals...")
                        await trading_service.run_signal_execution()
                    elif comp == 'fx': await refresh_fx_layer()
                    elif comp == 'commodities': await refresh_commodity_layer()
                    elif comp == 'crypto': await refresh_crypto_layer()
                    elif comp == 'hft': 
                        await refresh_hft_layer()
                        # Iteration 65: Trigger Quant Strategy execution tick
                        print("Scheduler: Running Quant Strategy Tick...")
                        await strategy_manager.run_tick()
                    elif comp == 'etfs':
                        # NEW: ETF daily data refresh
                        from app.core_logic.data.wholistic_pipeline import refresh_etf_layer
                        print("Scheduler: Refreshing ETF data...")
                        await refresh_etf_layer()
                    elif comp == 'accruals':
                        # NEW: Accruals Quality weekly refresh
                        from app.core_logic.data.wholistic_pipeline import refresh_accruals_quality
                        print("Scheduler: Refreshing Accruals Quality data...")
                        await refresh_accruals_quality()
            
            # Force run tick every loop for testing responsiveness
            print("Scheduler: Force Running Quant Strategy Tick...")
            await strategy_manager.run_tick()
            
            # JT-Ready Strategy Execution
            print("Scheduler: Running JT-Ready Strategy Execution...")
            global jt_strategy_executor
            if jt_strategy_executor is None:
                jt_strategy_executor = get_executor(db)
            
            # Get current global execution mode
            mode_result = db.execute(text("SELECT value FROM gold.platform_settings WHERE key = 'global_execution_mode'")).fetchone()
            current_mode = mode_result.value if mode_result else 'SIMULATION'
            jt_strategy_executor.set_execution_mode(current_mode)
            
            # Run execution cycle
            try:
                trades = await jt_strategy_executor.run_execution_cycle()
                if trades > 0:
                    print(f"Scheduler: JT-Ready execution completed - {trades} trades")
            except Exception as exec_err:
                print(f"Scheduler: JT-Ready execution error: {exec_err}")
                    
        except Exception as e:
            print(f"Scheduler Error: {e}")
        finally:
            db.close()
            
        await asyncio.sleep(30) # Check every 30 seconds

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
    # Initialize new data schedules if they don't exist
    db = SessionLocal()
    try:
        # Add ETF daily schedule
        existing = db.execute(text("SELECT 1 FROM gold.sync_schedules WHERE component = 'etfs'")).fetchone()
        if not existing:
            db.execute(text("""
                INSERT INTO gold.sync_schedules (component, frequency, last_run)
                VALUES ('etfs', '1day', NULL)
            """))
            print("✅ Scheduler: Added ETF daily refresh schedule")
        
        # Add Accruals weekly schedule
        existing = db.execute(text("SELECT 1 FROM gold.sync_schedules WHERE component = 'accruals'")).fetchone()
        if not existing:
            db.execute(text("""
                INSERT INTO gold.sync_schedules (component, frequency, last_run)
                VALUES ('accruals', '1day', NULL)
            """))
            print("✅ Scheduler: Added Accruals weekly refresh schedule")
        
        db.commit()
    except Exception as e:
        print(f"⚠️ Failed to initialize schedules: {e}")
    finally:
        db.close()
    
    # Start scheduler
    asyncio.create_task(scheduler_loop())
    print("✅ Yahoo Finance: Primary data source active")
    
    # Send startup notification
    try:
        from app.services.telegram_alerts import telegram_alerts
        telegram_alerts.alert_backend_restart("Systemd service startup")
    except Exception as e:
        print(f"⚠️ Failed to send startup alert: {e}")

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
            # Execute Swarm Debate (async)
            analysis_raw = await research_swarm.debate_sell_signal(inv_data, market_data)
            
            # The swarm returns a dict with "analysis" as a content string
            # We try to parse the content string if it's JSON
            try:
                cleaned_content = analysis_raw['analysis'].replace('```json', '').replace('```', '').strip()
                item.analysis = json.loads(cleaned_content)
            except:
                item.analysis = {"decision": "HOLD", "reasoning": analysis_raw['analysis']}
            
            db.commit()
        except Exception as e:
            print(f"Sell analysis error for {item.ticker}: {e}")
            db.rollback()

def get_db():
    db = SessionLocal()
    try: yield db
    finally: db.close()

# --- POSITION & EXECUTION TRACKING ---

@app.get("/api/positions")
def get_open_positions(db: Session = Depends(get_db)):
    """Get all open positions (inventory) with current P&L"""
    try:
        positions = db.execute(text("""
            SELECT i.*, s.close_price as current_market_price
            FROM consumption.inventory i
            LEFT JOIN consumption.stock s ON i.ticker = s.ticker
            WHERE i.status = 'held'
            ORDER BY i.purchase_date DESC
        """)).fetchall()
        
        result = []
        for p in positions:
            current_price = p.current_market_price or p.current_price or p.buy_price
            quantity = float(p.quantity) if p.quantity else 0
            buy_price = float(p.buy_price) if p.buy_price else 0
            
            unrealized_pnl = (current_price - buy_price) * quantity
            pnl_pct = ((current_price / buy_price) - 1) * 100 if buy_price > 0 else 0
            
            result.append({
                "id": p.id,
                "ticker": p.ticker,
                "asset_class": p.asset_class,
                "quantity": quantity,
                "buy_price": buy_price,
                "current_price": current_price,
                "unrealized_pnl": round(unrealized_pnl, 2),
                "unrealized_pnl_pct": round(pnl_pct, 2),
                "purchase_date": p.purchase_date.isoformat() if p.purchase_date else None,
                "estimates": {
                    "1d": p.est_1d,
                    "7d": p.est_7d,
                    "1m": p.est_1m
                },
                "analysis": p.analysis,
                "status": p.status
            })
        
        return {
            "positions": result,
            "summary": {
                "total_positions": len(result),
                "total_unrealized_pnl": round(sum(p["unrealized_pnl"] for p in result), 2),
                "by_asset_class": {}
            }
        }
    except Exception as e:
        print(f"Positions API Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


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


@app.get("/api/system/status")
def get_system_status(db: Session = Depends(get_db)):
    """Get comprehensive system status with last refresh times"""
    from app.services.ib_service import ib_quant_service
    
    try:
        # Get last refresh times from each layer
        refresh_times = {}
        
        # Bronze layer (raw data) - handle missing tables gracefully
        try:
            bronze_update = db.execute(text("""
                SELECT MAX(timestamp) FROM bronze.ibkr_fx_ticks
            """)).fetchone()
            refresh_times['bronze'] = bronze_update[0].isoformat() if bronze_update and bronze_update[0] else None
        except:
            refresh_times['bronze'] = None
        
        # Silver layer (unified)
        try:
            silver_update = db.execute(text("""
                SELECT MAX(date) FROM silver.unified_prices
            """)).fetchone()
            refresh_times['silver'] = silver_update[0].isoformat() if silver_update and silver_update[0] else None
        except:
            refresh_times['silver'] = None
        
        # Gold layer (positions)
        try:
            gold_update = db.execute(text("""
                SELECT MAX(updated_at) FROM gold.paper_strategies
            """)).fetchone()
            refresh_times['gold'] = gold_update[0].isoformat() if gold_update and gold_update[0] else None
        except:
            refresh_times['gold'] = None
        
        # Consumption layer
        try:
            consumption_update = db.execute(text("""
                SELECT MAX(last_updated) FROM consumption.Portfolio_Positions_Current
            """)).fetchone()
            refresh_times['consumption'] = consumption_update[0].isoformat() if consumption_update and consumption_update[0] else None
        except:
            refresh_times['consumption'] = None
        
        # Get current mode
        mode_result = db.execute(text("""
            SELECT value FROM gold.platform_settings WHERE key = 'global_execution_mode'
        """)).fetchone()
        current_mode = mode_result[0] if mode_result else 'SIMULATION'
        
        # Get IBKR price sample
        price_source = 'unknown'
        try:
            market_data = db.execute(text("""
                SELECT source FROM silver.unified_prices 
                WHERE ticker = 'AAPL' AND date = CURRENT_DATE
                LIMIT 1
            """)).fetchone()
            if market_data:
                price_source = market_data[0]
        except:
            pass
        
        return {
            "status": "operational",
            "mode": current_mode,
            "ibkr_connected": ib_quant_service.is_connected,
            "price_source": price_source,
            "last_refresh": refresh_times,
            "server_time": datetime.datetime.now().isoformat()
        }
    except Exception as e:
        db.rollback()
        logger.error(f"System status error: {e}")
        return {
            "status": "error",
            "error": str(e),
            "server_time": datetime.datetime.now().isoformat()
        }


# --- BACKTESTING APIS ---

@app.get("/api/market-data/live")
def get_live_market_data(tickers: str = ""):
    """
    Get LIVE market data for trade execution.
    Forces fresh price fetch from IBKR (no cache).
    Use this when placing orders to get accurate execution price.
    """
    from app.services.ib_service import ib_quant_service
    
    if not tickers:
        return {"success": False, "error": "No tickers provided"}
    
    ticker_list = tickers.split(',')
    results = []
    
    for ticker in ticker_list:
        ticker = ticker.strip().upper()
        if not ticker:
            continue
        
        # Force live price fetch (bypasses cache)
        price = ib_quant_service.get_live_price_for_execution(ticker)
        
        results.append({
            "ticker": ticker,
            "price": price,
            "source": "ibkr_live" if price else None,
            "timestamp": datetime.datetime.now().isoformat()
        })
    
    return {
        "success": True,
        "data": results,
        "timestamp": datetime.datetime.now().isoformat()
    }


@app.post("/api/strategies/{strategy_id}/backtest")
async def run_strategy_backtest(
    strategy_id: int,
    payload: dict,
    bg: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Run a backtest for a strategy
    
    Payload: {
        "start_date": "2024-01-01",
        "end_date": "2024-12-31",
        "initial_capital": 10000,
        "commission_rate": 0.001
    }
    """
    try:
        from app.services.backtest_engine import backtest_engine
        
        # Check if strategy exists
        strategy = db.query(QuantStrategy).filter(QuantStrategy.id == strategy_id).first()
        if not strategy:
            raise HTTPException(status_code=404, detail=f"Strategy {strategy_id} not found")
        
        # Queue backtest in background
        bg.add_task(
            backtest_engine.run_backtest,
            strategy_id=strategy_id,
            start_date=payload.get("start_date", "2024-01-01"),
            end_date=payload.get("end_date", "2024-12-31"),
            initial_capital=payload.get("initial_capital", 10000),
            commission_rate=payload.get("commission_rate", 0.001)
        )
        
        return {
            "status": "queued",
            "strategy_id": strategy_id,
            "strategy_name": strategy.name,
            "message": "Backtest started in background. Check status in a few minutes."
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/strategies/{strategy_id}/backtest-history")
def get_backtest_history(strategy_id: int, db: Session = Depends(get_db)):
    """Get all backtest runs for a strategy"""
    try:
        from app.services.backtest_engine import backtest_engine
        history = backtest_engine.get_backtest_history(strategy_id)
        return {
            "strategy_id": strategy_id,
            "backtest_count": len(history),
            "backtests": history
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/strategies/{strategy_id}/backtest-vs-live")
def get_backtest_vs_live(strategy_id: int, db: Session = Depends(get_db)):
    """Compare backtest results with live performance"""
    try:
        from app.services.backtest_engine import backtest_engine
        comparison = backtest_engine.compare_backtest_vs_live(strategy_id)
        
        if "error" in comparison:
            raise HTTPException(status_code=404, detail=comparison["error"])
        
        return comparison
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


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
    result = db.execute(text("""
        SELECT region, index_name, current_value, change_pct, trend, sentiment_score
        FROM consumption.Dashboard_Market_Overview
    """)).fetchall()
    
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
    risk = db.execute(text("SELECT value FROM gold.system_config WHERE component='risk_mgmt' AND key='max_portfolio_risk_daily'")).fetchone()
    
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
    signals_result = db.execute(text("""
        SELECT 
            s.strategy_id, s.ticker, s.signal as action, s.signal_strength as total_conf,
            s.confidence_score, s.entry_price, s.current_price, s.stop_loss, s.take_profit,
            s.win_rate, s.updated_at as timestamp, m.market, m.change_pct as daily_change
        FROM consumption.Strategies_Signals_Current s
        LEFT JOIN consumption.Markets_Stocks_Overview m ON s.ticker = m.ticker
        WHERE s.signal IN ('BUY', 'SELL')
        ORDER BY s.confidence_score DESC
        LIMIT 20
    """)).fetchall()
    
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
            live_price = info.get('currentPrice') or info.get('regularMarketPrice') or s.current_price or s.entry_price
            
            # Get change percentage
            live_change = info.get('regularMarketChangePercent') or s.daily_change
            if live_change and isinstance(live_change, (int, float)):
                live_change = round(live_change, 2)
            
        except Exception as e:
            # Fallback to database price
            live_price = s.current_price or s.entry_price
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
    result = db.execute(text("""
        SELECT pair as ticker, bid as price, change_pct as change, trend,
               signal as action, signal_strength as confidence, rsi_14 as rsi,
               carry_annual_pct as carry, updated_at as timestamp
        FROM consumption.Markets_FX_Overview ORDER BY pair
    """)).fetchall()
    return [{"ticker": r.ticker, "price": round(r.price or 0, 4), "change": round(r.change or 0, 2),
             "trend": r.trend or "NEUTRAL", "action": r.action or "HOLD",
             "confidence": round((r.confidence or 0) * 100, 1), "rsi": round(r.rsi or 50, 1),
             "carry": round(r.carry or 0, 2)} for r in result]


@app.get("/api/crypto/pairs")
def get_crypto_pairs(db: Session = Depends(get_db)):
    result = db.execute(text("""
        SELECT ticker, name, price, change_pct as change, change_24h_pct as change_24h,
               volume_24h as volume, market_cap, market_cap_rank as rank, trend,
               signal as action, signal_strength as confidence, rsi_14 as rsi,
               funding_rate, fear_greed_index, updated_at as timestamp
        FROM consumption.Markets_Crypto_Overview ORDER BY market_cap DESC NULLS LAST
    """)).fetchall()
    return [{"ticker": r.ticker, "asset": r.name, "action": r.action or "HOLD",
             "total_conf": round((r.confidence or 0) * 100, 1),
             "price": round(r.price or 0, 2), "change": round(r.change or 0, 2),
             "volume": r.volume, "market_cap": r.market_cap} for r in result]


@app.get("/api/commodities/all")
def get_commodities(db: Session = Depends(get_db)):
    result = db.execute(text("""
        SELECT ticker, name, category, exchange, price, change_pct as change, trend,
               signal as action, signal_strength as confidence, current_month_bias,
               next_month_bias, seasonal_strength, updated_at as timestamp
        FROM consumption.Markets_Commodities_Overview ORDER BY category, ticker
    """)).fetchall()
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
                    
                    timestamp = datetime.datetime.now().isoformat()
                
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
                    "timestamp": datetime.datetime.now().isoformat(),
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
        "ibkr_host": "52.74.14.181",
        "ibkr_port": 4002,
        "ibkr_mode": "Paper Trading",
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
    """Get sector performance"""
    # Return mock data for now - could be enhanced with real sector ETFs
    sectors = [
        {"name": "Technology", "change_percent": 1.2, "icon": "💻", "top_mover": "AAPL", "market_cap": 12e12},
        {"name": "Healthcare", "change_percent": -0.3, "icon": "🏥", "top_mover": "JNJ", "market_cap": 6e12},
        {"name": "Finance", "change_percent": 0.8, "icon": "🏦", "top_mover": "JPM", "market_cap": 8e12},
        {"name": "Energy", "change_percent": -1.2, "icon": "⛽", "top_mover": "XOM", "market_cap": 4e12},
        {"name": "Consumer", "change_percent": 0.5, "icon": "🛒", "top_mover": "WMT", "market_cap": 5e12},
        {"name": "Industrial", "change_percent": 0.2, "icon": "🏭", "top_mover": "GE", "market_cap": 3e12},
        {"name": "Materials", "change_percent": -0.5, "icon": "🏗️", "top_mover": "CAT", "market_cap": 2e12},
        {"name": "Utilities", "change_percent": 0.1, "icon": "💡", "top_mover": "NEE", "market_cap": 1.5e12},
    ]
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
    """Get global market indices"""
    markets = [
        {"name": "S&P 500", "region": "US", "flag": "🇺🇸", "price": 4500, "change_percent": 0.5, "status": "Open"},
        {"name": "Nasdaq", "region": "US", "flag": "🇺🇸", "price": 14000, "change_percent": 0.8, "status": "Open"},
        {"name": "FTSE 100", "region": "Europe", "flag": "🇬🇧", "price": 7500, "change_percent": -0.2, "status": "Closed"},
        {"name": "DAX", "region": "Europe", "flag": "🇩🇪", "price": 16000, "change_percent": 0.3, "status": "Closed"},
        {"name": "Nikkei 225", "region": "Asia", "flag": "🇯🇵", "price": 29000, "change_percent": 1.2, "status": "Closed"},
        {"name": "Hang Seng", "region": "Asia", "flag": "🇭🇰", "price": 17000, "change_percent": -0.5, "status": "Closed"},
        {"name": "Shanghai", "region": "Asia", "flag": "🇨🇳", "price": 3200, "change_percent": 0.1, "status": "Closed"},
        {"name": "ASX 200", "region": "Asia", "flag": "🇦🇺", "price": 7200, "change_percent": 0.4, "status": "Closed"},
    ]
    return {"data": markets}

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

@app.get("/api/market/sentiment")
def get_market_sentiment(db: Session = Depends(get_db)):
    """Get market sentiment indicators"""
    try:
        # Try to fetch real VIX data
        vix_row = db.execute(text("""
            SELECT close FROM silver.unified_prices
            WHERE ticker = '^VIX'
            ORDER BY date DESC
            LIMIT 1
        """)).fetchone()
        
        vix = float(vix_row.close) if vix_row and vix_row.close else 20.0
        
        # Calculate fear/greed index based on VIX and market breadth
        # VIX < 15 = Greed, VIX > 30 = Fear
        if vix < 15:
            fear_greed = 75  # Greed
        elif vix < 20:
            fear_greed = 55  # Neutral-Greed
        elif vix < 25:
            fear_greed = 50  # Neutral
        elif vix < 30:
            fear_greed = 35  # Fear
        else:
            fear_greed = 20  # Extreme Fear
        
        return {
            "fearGreed": fear_greed,
            "vix": vix,
            "putCall": 1.0  # Would need options data
        }
    except Exception as e:
        logger.error(f"Error in market sentiment: {e}")
        # Return defaults
        return {
            "fearGreed": 50,
            "vix": 20.0,
            "putCall": 1.0
        }

@app.get("/api/inventory/evaluate")
def get_inventory_evaluate(db: Session = Depends(get_db)):
    result = db.execute(text("""
        SELECT position_id, ticker, name, asset_class, side, quantity,
               avg_entry_price as entry_price, current_price, market_value,
               weight_pct as portfolio_weight, unrealized_pnl as pnl,
               unrealized_pnl_pct as pnl_pct, strategy_name, days_held
        FROM consumption.Portfolio_Positions_Current ORDER BY market_value DESC
    """)).fetchall()
    positions = [{"id": r.position_id, "ticker": r.ticker, "name": r.name,
                  "asset_class": r.asset_class, "side": r.side,
                  "quantity": float(r.quantity or 0), "entry_price": float(r.entry_price or 0),
                  "current_price": float(r.current_price or 0),
                  "market_value": float(r.market_value or 0),
                  "pnl": float(r.pnl or 0), "strategy": r.strategy_name,
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
            FROM gold.paper_strategies 
            WHERE id = :position_id
        """), {"position_id": position_id}).fetchone()
        
        if not position:
            raise HTTPException(status_code=404, detail="Position not found")
        
        # Get current market price - prioritize LIVE IBKR price for execution
        ticker = position.ticker
        close_price = None
        price_source = "unknown"
        
        # Try IBKR live price first (for execution accuracy)
        try:
            from app.services.ib_service import ib_quant_service
            if ib_quant_service.is_connected:
                # Force fresh price fetch (no cache)
                ib_price = ib_quant_service.get_live_price_for_execution(ticker)
                if ib_price:
                    close_price = float(ib_price)
                    price_source = "ibkr_live"
                    logger.info(f"Using IBKR live price for {ticker}: ${close_price}")
        except Exception as e:
            logger.warning(f"IBKR live price fetch failed for {ticker}: {e}")
        
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
                close_price = float(df['Close'].iloc[-1])
                price_source = "yfinance"
                # Handle crypto micro-units
                if ticker in ['BTC', 'ETH', 'SOL']:
                    close_price = close_price / 1000
        
        if close_price is None:
            raise HTTPException(status_code=500, detail="Could not fetch current market price")
        
        # Calculate final P&L
        # Convert Decimal to float to avoid type errors
        entry_price = float(position.entry_price) if position.entry_price else 0
        invested = float(position.invested_capital) if position.invested_capital else 0
        quantity = float(position.quantity) if position.quantity else 0
        
        if entry_price > 0 and invested > 0:
            shares = invested / entry_price
            exit_value = shares * float(close_price)
            trade_pnl = exit_value - invested
            pnl_pct = (trade_pnl / invested) * 100 if invested > 0 else 0
        else:
            trade_pnl = 0
            pnl_pct = 0
        
        # Record the trade execution - convert all values to native Python types
        db.execute(text("""
            INSERT INTO gold.trade_executions 
            (strategy_id, ticker, side, quantity, entry_price, exit_price, 
             pnl, pnl_pct, status, executed_at, execution_mode)
            VALUES (:strategy_id, :ticker, 'SELL', :quantity, :entry_price, :exit_price,
                    :pnl, :pnl_pct, 'CLOSED', NOW(), 'PAPER_TRADING')
        """), {
            "strategy_id": str(position.strategy_id),
            "ticker": str(ticker),
            "quantity": float(quantity),
            "entry_price": float(entry_price),
            "exit_price": float(close_price),
            "pnl": float(trade_pnl),
            "pnl_pct": float(pnl_pct)
        })
        
        # Update the paper strategy position
        db.execute(text("""
            UPDATE gold.paper_strategies 
            SET realized_pnl = COALESCE(realized_pnl, 0) + :trade_pnl,
                unrealized_pnl = 0,
                invested_capital = 0,
                status = 'CLOSED',
                closed_at = NOW(),
                close_price = :close_price
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
            "price_source": price_source,
            "pnl": round(trade_pnl, 2),
            "pnl_pct": round(pnl_pct, 2),
            "message": f"Closed {ticker} at ${close_price:.2f} ({price_source}) with P&L ${trade_pnl:.2f} ({pnl_pct:+.2f}%)"
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
    try:
        # Get positions from consumption view
        result = db.execute(text("""
            SELECT 
                position_id as id,
                ticker,
                name as strategy_name,
                asset_class,
                side,
                quantity,
                avg_entry_price as entry_price,
                current_price,
                market_value,
                unrealized_pnl as pnl,
                unrealized_pnl_pct as pnl_pct,
                strategy_name as strategy,
                days_held
            FROM consumption.Portfolio_Positions_Current
            WHERE quantity > 0
            ORDER BY market_value DESC
        """)).fetchall()
        
        positions = []
        for r in result:
            positions.append({
                "id": r.id,
                "ticker": r.ticker,
                "strategy": r.strategy,
                "asset_class": r.asset_class,
                "side": r.side,
                "quantity": float(r.quantity or 0),
                "entry_price": float(r.entry_price or 0),
                "current_price": float(r.current_price or 0),
                "market_value": float(r.market_value or 0),
                "pnl": float(r.pnl or 0),
                "pnl_pct": float(r.pnl_pct or 0),
                "days_held": r.days_held
            })
        
        # Calculate totals
        total_value = sum(p["market_value"] for p in positions)
        total_pnl = sum(p["pnl"] for p in positions)
        
        return {
            "positions": positions,
            "total_positions": len(positions),
            "total_value": total_value,
            "total_pnl": total_pnl,
            "active_positions": len([p for p in positions if p["quantity"] > 0])
        }
        
    except Exception as e:
        logger.error(f"Error fetching portfolio positions: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch positions: {str(e)}")

# --- MAINTENANCE & REFRESH APIS (5 DOMAINS) ---
@app.post("/api/maintenance/refresh/indices")
async def api_refresh_indices(bg: BackgroundTasks):
    bg.add_task(refresh_indices_and_mood); return {"status": "Syncing"}

@app.get("/api/maintenance/status/indices")
async def api_status_indices(db: Session = Depends(get_db)):
    exists = db.execute(text("SELECT 1 FROM consumption.global_state WHERE timestamp > NOW() - INTERVAL '5 minutes' AND category = 'index' LIMIT 1")).first()
    return {"status": "Live" if exists else "Idle"}

@app.post("/api/maintenance/refresh/fx")
async def api_refresh_fx(bg: BackgroundTasks):
    bg.add_task(refresh_fx_layer); return {"status": "Syncing"}

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
    bg.add_task(refresh_commodity_layer); return {"status": "Syncing"}

@app.get("/api/maintenance/status/commodities")
async def api_status_commodities(db: Session = Depends(get_db)):
    exists = db.execute(text("SELECT 1 FROM gold.commodity_metrics WHERE date > NOW() - INTERVAL '5 minutes' LIMIT 1")).first()
    return {"status": "Live" if exists else "Idle"}

@app.post("/api/maintenance/refresh/crypto")
async def api_refresh_crypto(bg: BackgroundTasks):
    bg.add_task(refresh_crypto_layer); return {"status": "Syncing"}

@app.get("/api/maintenance/status/crypto")
async def api_status_crypto(db: Session = Depends(get_db)):
    exists = db.execute(text("SELECT 1 FROM gold.crypto_metrics WHERE date > NOW() - INTERVAL '5 minutes' LIMIT 1")).first()
    return {"status": "Live" if exists else "Idle"}

@app.post("/api/maintenance/refresh/stocks")
async def api_refresh_stocks(bg: BackgroundTasks):
    bg.add_task(refresh_stock_layer); return {"status": "Syncing"}

@app.post("/api/maintenance/refresh/stocks/daily")
async def api_refresh_stocks_daily(bg: BackgroundTasks):
    """Trigger daily stock data refresh for all 400+ tickers via cron pipeline"""
    import subprocess
    def run_daily_refresh():
        try:
            result = subprocess.run(
                ["python3", "/home/ubuntu/.openclaw/workspace/jtcml_trading/daily_stock_refresh.py"],
                capture_output=True,
                text=True,
                timeout=600
            )
            return {"status": "success" if result.returncode == 0 else "error", 
                    "output": result.stdout, "error": result.stderr}
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    bg.add_task(run_daily_refresh)
    return {"status": "Daily stock refresh triggered", "tickers": 400}

@app.get("/api/maintenance/status/stocks")
async def api_status_stocks(db: Session = Depends(get_db)):
    exists = db.execute(text("SELECT 1 FROM gold.stock_metrics WHERE date > NOW() - INTERVAL '5 minutes' LIMIT 1")).first()
    return {"status": "Live" if exists else "Idle"}

@app.get("/api/velocity/trades")
def get_velocity_trades(db: Session = Depends(get_db)):
    result = db.execute(text("""
        SELECT trade_id, ticker, side, entry_date, entry_price, entry_quantity as quantity,
               exit_date, exit_price, realized_pnl as pnl, realized_pnl_pct as pnl_pct,
               strategy_id, holding_days, exit_reason
        FROM consumption.Performance_Trades_History ORDER BY created_at DESC LIMIT 100
    """)).fetchall()
    return [{"id": r.trade_id, "ticker": r.ticker, "side": r.side,
             "entry_price": float(r.entry_price or 0), "pnl": float(r.pnl or 0),
             "strategy": r.strategy_id, "holding_period": r.holding_days} for r in result]

@app.get("/api/velocity/summary")
def get_velocity_summary(db: Session = Depends(get_db)):
    trades = db.execute(text("SELECT COUNT(*) as cnt FROM consumption.Performance_Trades_History")).fetchone()
    summary = db.execute(text("""
        SELECT total_value, total_pnl, win_rate, sharpe_ratio
        FROM consumption.Performance_Portfolio_Summary WHERE portfolio_type = 'PAPER'
    """)).fetchone()
    return {"total_trades": trades.cnt if trades else 0,
            "portfolio_value": float(summary.total_value or 0) if summary else 0,
            "total_pnl": float(summary.total_pnl or 0) if summary else 0,
            "win_rate": float(summary.win_rate or 0) * 100 if summary else 0,
            "sharpe_ratio": float(summary.sharpe_ratio or 0) if summary else 0,
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
            current_year = datetime.datetime.now().year
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
            "timestamp": datetime.datetime.now().isoformat(),
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
        # Clear the consumption.trades table
        # Using DELETE instead of TRUNCATE for safer permission handling
        db.execute(text("DELETE FROM consumption.trades"))
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
    db.execute(text("DELETE FROM gold.quant_strategies WHERE id = :sid"), {"sid": strat_id})
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
    """Get strategy performance with both backtest and actual win rates + CURRENT SIGNAL"""
    # Get strategy attribution
    attribution = db.execute(text("""
        SELECT strategy_id, strategy_name, allocated_capital_pct as allocation,
               contribution_pct as contribution, return_pct as returns, num_trades,
               win_rate, sharpe_ratio
        FROM consumption.Performance_Strategy_Attribution
        WHERE portfolio_type = 'PAPER' ORDER BY return_pct DESC
    """)).fetchall()
    
    # Get backtest win rates
    backtests = db.execute(text("""
        SELECT strategy_id, AVG(win_rate) as backtest_win_rate,
               AVG(total_return_pct) as backtest_return,
               SUM(total_trades) as backtest_total_trades
        FROM consumption.Strategies_Backtest_Results
        GROUP BY strategy_id
    """)).fetchall()
    
    # Get actual/live win rates from trade history
    live_stats = db.execute(text("""
        SELECT strategy_id,
               COUNT(*) as total_trades,
               SUM(CASE WHEN realized_pnl > 0 THEN 1 ELSE 0 END) as winning_trades
        FROM consumption.Performance_Trades_History
        WHERE exit_date IS NOT NULL
        GROUP BY strategy_id
    """)).fetchall()
    
    # Get CURRENT SIGNALS - the strongest active signal for each strategy
    current_signals = db.execute(text("""
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
    """)).fetchall()
    
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
            # CURRENT SIGNAL - This is the critical key!
            "current_signal": {
                "action": sig.signal if sig else "HOLD",
                "ticker": sig.ticker if sig else None,
                "strength": round((sig.signal_strength or 0) * 100, 1) if sig else 0,
                "confidence": round((sig.confidence_score or 0) * 100, 1) if sig else 0,
                "price": float(sig.current_price or 0) if sig else None
            } if sig else None
        })
    
    # Get monthly returns
    monthly = db.execute(text("""
        SELECT year, month, return_pct
        FROM consumption.Performance_Monthly_Returns
        WHERE portfolio_type = 'PAPER' ORDER BY year DESC, month DESC LIMIT 12
    """)).fetchall()
    
    # Get summary
    summary = db.execute(text("""
        SELECT * FROM consumption.Performance_Portfolio_Summary
        WHERE portfolio_type = 'PAPER'
    """)).fetchone()
    
    return {
        "strategies": strategies,
        "monthly_returns": [{"year": r.year, "month": r.month, "return": float(r.return_pct or 0)} for r in monthly],
        "summary": {
            "total_return": float(summary.total_pnl_pct or 0) if summary else 0,
            "sharpe": float(summary.sharpe_ratio or 0) if summary else 0,
            "max_drawdown": float(summary.max_drawdown_pct or 0) if summary else 0,
            "win_rate": float(summary.win_rate or 0) * 100 if summary else 0
        }
    }

@app.get("/api/performance/daily-pnl")
def get_daily_pnl(days: int = 7, db: Session = Depends(get_db)):
    """Get daily P&L - shows actual position entry and exit data"""
    
    # Get closed trades (realized P&L)
    closed_trades = db.execute(text("""
        SELECT 
            DATE(exit_date) as trade_date,
            SUM(realized_pnl) as day_pnl,
            COUNT(*) as trade_count
        FROM consumption.Performance_Trades_History
        WHERE exit_date IS NOT NULL
        GROUP BY DATE(exit_date)
        ORDER BY trade_date DESC
        LIMIT :days
    """), {"days": days}).fetchall()
    
    # Get open positions by entry date (unrealized P&L)
    open_positions = db.execute(text("""
        SELECT 
            DATE(entry_date) as entry_date,
            SUM(unrealized_pnl) as day_pnl,
            COUNT(*) as position_count
        FROM consumption.Portfolio_Positions_Current
        WHERE side = 'LONG'
        GROUP BY DATE(entry_date)
        ORDER BY entry_date DESC
        LIMIT :days
    """), {"days": days}).fetchall()
    
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
    bg.add_task(refresh_hft_layer); return {"status": "Syncing"}

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
    
    # Only show positions created in the current mode (exclude CLOSED positions from active list)
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
        FROM gold.paper_strategies ps
        LEFT JOIN gold.strategy_definitions sd ON ps.strategy_id = sd.strategy_id
        WHERE ps.execution_mode = :mode
          AND ps.ticker != '__MONITORING__'
          AND ps.status != 'CLOSED'
        ORDER BY ps.created_at DESC
    """), {"mode": current_mode}).fetchall()
    
    # Also get MONITORING strategies (for the monitoring tab)
    monitoring = db.execute(text("""
        SELECT 
            ps.id,
            ps.strategy_id,
            sd.name as strategy_name,
            ps.ticker,
            ps.capital,
            ps.target_price,
            ps.stop_loss,
            ps.status,
            ps.created_at,
            ps.execution_mode
        FROM gold.paper_strategies ps
        LEFT JOIN gold.strategy_definitions sd ON ps.strategy_id = sd.strategy_id
        WHERE ps.status = 'MONITORING'
          AND ps.ticker = '__MONITORING__'
          AND ps.execution_mode = :mode
        ORDER BY ps.created_at DESC
    """), {"mode": current_mode}).fetchall()
    
    strategies = []
    monitoring_list = []
    
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
    
    for row in monitoring:
        monitoring_list.append({
            "id": row.id,
            "strategy_id": row.strategy_id,
            "strategy_name": row.strategy_name or row.strategy_id,
            "status": "MONITORING",
            "max_positions": int(row.target_price) if row.target_price else 4,
            "capital_per_trade": float(row.stop_loss) if row.stop_loss else 25000,
            "created_at": row.created_at.isoformat() if row.created_at else None,
        })
    
    return {
        "strategies": strategies, 
        "monitoring": monitoring_list,
        "count": len(strategies),
        "monitoring_count": len(monitoring_list),
        "execution_mode": current_mode,
        "message": f"Showing {len(strategies)} positions, {len(monitoring_list)} monitoring for {current_mode} mode"
    }


@app.get("/api/paper-strategies/{strategy_id:path}/daily-pnl")
def get_paper_strategy_daily_pnl(strategy_id: str, days: int = 7, db: Session = Depends(get_db)):
    """Get daily P&L breakdown for a paper strategy - shows actual position data"""
    from datetime import datetime, timedelta
    
    # First check: Get closed trades (realized P&L) for this strategy
    closed_trades = db.execute(text("""
        SELECT 
            DATE(exit_date) as trade_date,
            SUM(realized_pnl) as day_realized,
            COUNT(*) as trade_count
        FROM consumption.Performance_Trades_History
        WHERE strategy_id = :strategy_id 
          AND exit_date IS NOT NULL
        GROUP BY DATE(exit_date)
        ORDER BY trade_date DESC
        LIMIT :days
    """), {"strategy_id": strategy_id, "days": days}).fetchall()
    
    # Second check: Get open positions by entry date (unrealized P&L)
    open_positions = db.execute(text("""
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
    """), {"strategy_id": strategy_id, "days": days}).fetchall()
    
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
        FROM gold.paper_strategies
        WHERE strategy_id = :strategy_id
    """), {"strategy_id": strategy_id}).fetchall()
    
    if not positions:
        raise HTTPException(status_code=404, detail=f"No positions found for strategy {strategy_id}")
    
    positions_closed = 0
    
    for pos in positions:
        if action == 'close' and pos.invested_capital > 0:
            # Close the position - mark as closed
            db.execute(text("""
                UPDATE gold.paper_strategies
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
                UPDATE gold.paper_strategies
                SET 
                    status = 'PAUSED',
                    updated_at = NOW()
                WHERE id = :id
            """), {"id": pos.id})
    
    # Mark strategy as inactive in strategy_definitions
    db.execute(text("""
        UPDATE gold.strategy_definitions
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
            in_market_capital,
            capacity_millions
        FROM gold.strategy_definitions
        WHERE strategy_id = :strategy_id AND jt_ready = TRUE
    """), {"strategy_id": strategy_id}).fetchone()
    
    if not result:
        raise HTTPException(status_code=404, detail=f"Strategy {strategy_id} not found")
    
    # Calculate total in-market across all positions
    in_market = db.execute(text("""
        SELECT COALESCE(SUM(invested_capital), 0) 
        FROM gold.paper_strategies 
        WHERE strategy_id = :strategy_id
    """), {"strategy_id": strategy_id}).scalar() or 0
    
    return {
        "strategy_id": result.strategy_id,
        "name": result.name,
        "assigned_capital": float(result.assigned_capital) if result.assigned_capital else 100000,
        "in_market_capital": float(in_market),
        "available_for_buying": max(0, float(result.assigned_capital or 100000) - float(in_market)),
        "capacity_millions": float(result.capacity_millions) if result.capacity_millions else 100
    }


@app.post("/api/strategies/{strategy_id:path}/capital")
def update_strategy_capital(strategy_id: str, payload: dict, db: Session = Depends(get_db)):
    """Update assigned capital for a strategy"""
    assigned_capital = payload.get("assigned_capital")
    
    if assigned_capital is None or assigned_capital < 0:
        raise HTTPException(status_code=400, detail="assigned_capital must be >= 0")
    
    # Check strategy exists
    result = db.execute(text("""
        SELECT strategy_id FROM gold.strategy_definitions
        WHERE strategy_id = :strategy_id AND jt_ready = TRUE
    """), {"strategy_id": strategy_id}).fetchone()
    
    if not result:
        raise HTTPException(status_code=404, detail=f"Strategy {strategy_id} not found")
    
    # Update assigned capital
    db.execute(text("""
        UPDATE gold.strategy_definitions
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
        SELECT assigned_capital FROM gold.strategy_definitions
        WHERE strategy_id = :strategy_id
    """), {"strategy_id": strategy_id}).fetchone()
    
    if not result:
        raise HTTPException(status_code=404, detail="Strategy not found")
    
    assigned = float(result.assigned_capital or 100000)
    
    # Get current in-market
    in_market = db.execute(text("""
        SELECT COALESCE(SUM(invested_capital), 0) 
        FROM gold.paper_strategies 
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
            FROM gold.paper_strategies 
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
                    
                    if tws_status.get("connected"):
                        account_info = ib_quant_service.get_account_summary()
                        
                        if account_info:
                            # Check if this is an HKD account
                            is_hkd = account_info.get("currency") == "HKD" or account_info.get("cash_hkd", 0) > 0
                            
                            if is_hkd:
                                # Use HKD values for HK accounts
                                ibkr_data = {
                                    "ibkr_connected": True,
                                    "account_currency": "HKD",
                                    "account_balance": account_info.get("cash_hkd", 0) or account_info.get("available_funds_hkd", 0),
                                    "account_balance_hkd": account_info.get("cash_hkd", 0) or account_info.get("available_funds_hkd", 0),
                                    "account_balance_usd": account_info.get("available_funds", 0),
                                    "net_liquidation": account_info.get("net_liquidation_hkd", 0) or account_info.get("net_liquidation", 0),
                                    "buying_power": account_info.get("buying_power_hkd", 0) or account_info.get("buying_power", 0),
                                    "excess_liquidity": account_info.get("excess_liquidity_hkd", 0) or account_info.get("excess_liquidity", 0),
                                    "account": account_info.get("account", "Unknown"),
                                    "account_type": "PAPER" if current_mode == "PAPER_TRADING" else "LIVE"
                                }
                            else:
                                # Use USD values (default)
                                ibkr_data = {
                                    "ibkr_connected": True,
                                    "account_currency": account_info.get("currency", "USD"),
                                    "account_balance": account_info.get("available_funds", 0),
                                    "account_balance_hkd": account_info.get("available_funds_hkd", 0),
                                    "account_balance_usd": account_info.get("available_funds", 0),
                                    "net_liquidation": account_info.get("net_liquidation", 0),
                                    "buying_power": account_info.get("buying_power", 0),
                                    "excess_liquidity": account_info.get("excess_liquidity", 0),
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
    
    # Get updated state
    return get_global_execution_mode(db)


@app.post("/api/ib/place-order")
def place_ibkr_order(payload: dict, db: Session = Depends(get_db)):
    """
    Place an order through IBKR TWS API.
    Works in PAPER_TRADING or LIVE_TRADING mode.
    """
    # Get current execution mode
    mode_result = db.execute(text("""
        SELECT value FROM gold.platform_settings 
        WHERE key = 'global_execution_mode'
    """)).fetchone()
    
    current_mode = mode_result.value if mode_result else 'SIMULATION'
    
    symbol = payload.get("symbol", "AAPL")
    action = payload.get("action", "BUY")
    quantity = payload.get("quantity", 1)
    order_type = payload.get("order_type", "MKT")
    
    if current_mode == "SIMULATION":
        # Get current simulation balance
        sim_capital = db.execute(text("""
            SELECT value FROM gold.platform_settings 
            WHERE key = 'simulation_capital'
        """)).fetchone()
        sim_amount = float(sim_capital.value) if sim_capital else 100000
        
        # Get current allocated capital
        sim_stats = db.execute(text("""
            SELECT COALESCE(SUM(capital), 0) as total_allocated
            FROM gold.paper_strategies 
            WHERE status = 'ACTIVE'
        """)).fetchone()
        sim_used = float(sim_stats.total_allocated) if sim_stats else 0
        sim_available = sim_amount - sim_used
        
        return {
            "success": True,
            "simulated": True,
            "message": f"SIMULATION: {action} {quantity} shares of {symbol} would be placed",
            "order_id": f"SIM_{int(time.time())}",
            "mode": current_mode,
            "simulation_balance": {
                "total": sim_amount,
                "used": sim_used,
                "available": sim_available
            }
        }
    
    # Get strategy_id from payload if provided
    strategy_id = payload.get("strategy_id", "manual")
    
    # Get current price for the symbol
    current_price = None
    try:
        # Try to get from database first
        price_result = db.execute(text("""
            SELECT close FROM silver.unified_prices 
            WHERE ticker = :symbol 
            ORDER BY date DESC LIMIT 1
        """), {"symbol": symbol}).fetchone()
        if price_result:
            current_price = float(price_result[0])
    except:
        pass
    
    # Place real order through IBKR
    try:
        order_result = ib_quant_service.place_order(
            symbol=symbol,
            action=action,
            quantity=int(quantity),
            order_type=order_type,
            account=None,
            strategy_id=strategy_id,
            current_price=current_price
        )
        
        if order_result and order_result.get("success"):
            return {
                "success": True,
                "order_id": order_result.get("order_id"),
                "status": order_result.get("status", "Submitted"),
                "mode": current_mode,
                "symbol": symbol,
                "action": action,
                "quantity": quantity,
                "price": current_price,
                "message": f"{current_mode} order submitted: {action} {quantity} {symbol}"
            }
        else:
            raise HTTPException(
                status_code=500, 
                detail=f"Order failed: {order_result.get('error', 'Unknown error')}"
            )
    
    except Exception as e:
        logger.error(f"Error placing IBKR order: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/ib/pending-orders")
def get_pending_orders(db: Session = Depends(get_db)):
    """
    Get pending/submitted orders from IBKR that haven't filled yet.
    """
    try:
        result = db.execute(text("""
            SELECT order_id, strategy_id, ticker, action, quantity, status, filled, remaining, 
                   order_type, gtc, created_at, notes as account, price
            FROM gold.ibkr_orders 
            WHERE status IN ('PendingSubmit', 'PreSubmitted', 'Submitted', 'PendingCancel')
            ORDER BY created_at DESC
        """)).fetchall()
        
        orders = []
        for row in result:
            orders.append({
                "order_id": row.order_id,
                "strategy_id": row.strategy_id,
                "ticker": row.ticker,
                "action": row.action,
                "quantity": row.quantity,
                "status": row.status,
                "filled": row.filled,
                "remaining": row.remaining,
                "order_type": row.order_type,
                "gtc": row.gtc,
                "created_at": row.created_at.isoformat() if row.created_at else None,
                "account": row.account,
                "price": float(row.price) if row.price else None
            })
        
        return {
            "orders": orders,
            "count": len(orders)
        }
    except Exception as e:
        logger.error(f"Error fetching pending orders: {e}")
        return {"orders": [], "count": 0}


@app.get("/api/ibkr/portfolio")
def get_ibkr_portfolio():
    """
    Get real portfolio data from IBKR - Golden Source for P&L and positions
    """
    try:
        import asyncio
        from ib_insync import IB
        
        async def fetch_portfolio():
            ib = IB()
            try:
                # Connect with fresh client ID
                import random
                client_id = random.randint(100, 200)
                await ib.connectAsync('52.74.14.181', 4002, clientId=client_id, timeout=15)
                
                account = ib.managedAccounts()[0]
                
                # Get account values
                values = ib.accountValues(account)
                account_data = {}
                for v in values:
                    if v.tag == "NetLiquidation":
                        account_data['total_value'] = float(v.value)
                    elif v.tag == "AvailableFunds":
                        account_data['cash'] = float(v.value)
                    elif v.tag == "UnrealizedPnL":
                        account_data['unrealized_pnl'] = float(v.value)
                    elif v.tag == "RealizedPnL":
                        account_data['realized_pnl'] = float(v.value)
                    elif v.tag == "BuyingPower":
                        account_data['buying_power'] = float(v.value)
                
                # Get positions
                positions = ib.positions(account)
                position_list = []
                total_pnl = 0
                
                for pos in positions:
                    # Get current market price
                    ticker = ib.reqMktData(pos.contract)
                    await asyncio.sleep(0.5)  # Wait for price
                    market_price = ticker.last or ticker.close or pos.avgCost
                    
                    market_value = pos.position * market_price
                    cost_basis = pos.position * pos.avgCost
                    pnl = market_value - cost_basis
                    total_pnl += pnl
                    
                    position_list.append({
                        'symbol': pos.contract.symbol,
                        'secType': pos.contract.secType,
                        'currency': pos.contract.currency,
                        'exchange': pos.contract.exchange,
                        'position': pos.position,
                        'avgCost': pos.avgCost,
                        'marketPrice': market_price,
                        'marketValue': market_value,
                        'pnl': pnl,
                        'pnlPercent': ((market_price - pos.avgCost) / pos.avgCost * 100) if pos.avgCost else 0
                    })
                    
                    ib.cancelMktData(pos.contract)
                
                ib.disconnect()
                
                return {
                    'account': account,
                    'cash': account_data.get('cash', 0),
                    'total_value': account_data.get('total_value', 0),
                    'buying_power': account_data.get('buying_power', 0),
                    'unrealized_pnl': account_data.get('unrealized_pnl', 0),
                    'realized_pnl': account_data.get('realized_pnl', 0),
                    'total_pnl': total_pnl,
                    'position_count': len(position_list),
                    'positions': position_list
                }
                
            except Exception as e:
                logger.error(f"Error fetching IBKR portfolio: {e}")
                return {'error': str(e)}
            finally:
                if ib.isConnected():
                    ib.disconnect()
        
        result = asyncio.run(fetch_portfolio())
        
        # Handle NaN values for JSON compliance
        def clean_nan(obj):
            if isinstance(obj, dict):
                return {k: clean_nan(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [clean_nan(i) for i in obj]
            elif isinstance(obj, float) and (obj != obj or obj == float('inf') or obj == float('-inf')):  # NaN check
                return 0.0
            return obj
        
        result = clean_nan(result)
        
        if 'error' in result:
            raise HTTPException(status_code=500, detail=result['error'])
        
        return result
        
    except Exception as e:
        logger.error(f"Error in portfolio endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/positions/sync-to-ibkr")
def sync_positions_to_ibkr(payload: dict, db: Session = Depends(get_db)):
    """
    Sync existing paper positions to IBKR by placing real orders.
    This is used when switching from SIMULATION to PAPER_TRADING mode
    to actually submit the orders to IBKR.
    
    Expects: { "max_positions": 10 } (optional, defaults to 5)
    """
    max_positions = payload.get("max_positions", 5)
    
    # Get current execution mode
    mode_result = db.execute(text("""
        SELECT value FROM gold.platform_settings 
        WHERE key = 'global_execution_mode'
    """)).fetchone()
    
    current_mode = mode_result.value if mode_result else 'SIMULATION'
    
    if current_mode == "SIMULATION":
        return {
            "success": False,
            "error": "Cannot sync in SIMULATION mode. Switch to PAPER_TRADING first."
        }
    
    # Check IBKR connection
    try:
        tws_status = ib_quant_service.get_status()
        if not tws_status.get("is_connected"):
            return {
                "success": False,
                "error": "IBKR not connected. Check TWS Gateway."
            }
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to check IBKR status: {str(e)}"
        }
    
    # Get positions that need IBKR orders
    result = db.execute(text("""
        SELECT id, strategy_id, ticker, capital, entry_price, execution_mode
        FROM gold.paper_strategies
        WHERE status = 'ACTIVE' 
        AND invested_capital > 0
        AND (ibkr_order_id IS NULL OR ibkr_order_id = '')
        AND execution_mode = 'PAPER_TRADING'
        ORDER BY id
        LIMIT :limit
    """), {"limit": max_positions})
    
    positions = []
    for row in result:
        positions.append({
            'id': row.id,
            'strategy_id': row.strategy_id,
            'ticker': row.ticker,
            'capital': float(row.capital),
            'entry_price': float(row.entry_price) if row.entry_price else None
        })
    
    submitted = []
    failed = []
    
    for pos in positions:
        # Clean up ticker format
        ticker = pos['ticker']
        # Remove quotes, brackets, and extra whitespace
        ticker = ticker.replace('[', '').replace(']', '').replace('"', '').replace("'", '').strip()
        
        # Skip FX pairs for now (need special handling)
        if '/' in ticker:
            failed.append({
                "ticker": ticker,
                "error": "FX pairs require special handling"
            })
            continue
        
        # Clean up HK ticker format - convert "0006.HK" to "6.HK" or keep as is
        if ticker.endswith('.HK'):
            # Keep the HK suffix but clean up leading zeros if needed
            parts = ticker.split('.')
            if len(parts) == 2 and parts[0].isdigit():
                # Keep original format - IBKR should handle it
                pass
        
        # Calculate quantity
        if pos['entry_price'] and pos['entry_price'] > 0:
            quantity = int(pos['capital'] / pos['entry_price'])
        else:
            # Fetch current price
            try:
                import yfinance as yf
                t = yf.Ticker(ticker)
                info = t.info
                current_price = info.get('regularMarketPrice', 100)
                quantity = int(pos['capital'] / current_price)
            except:
                quantity = 10
        
        if quantity < 1:
            quantity = 1
        
        try:
            order_result = ib_quant_service.place_order(
                symbol=ticker,
                action="BUY",
                quantity=quantity,
                order_type="MKT",
                account=None
            )
            
            if order_result and order_result.get('success'):
                order_id = order_result.get('order_id', 'UNKNOWN')
                fill_price = order_result.get('fill_price')  # IBKR golden source price
                
                # Use IBKR fill price if available, otherwise fall back to estimated price
                entry_price = fill_price if fill_price else (pos['entry_price'] or 0)
                
                # Update database with IBKR golden source price
                db.execute(text("""
                    UPDATE gold.paper_strategies
                    SET ibkr_order_id = :order_id,
                        entry_price = :entry_price,
                        current_price = :entry_price,
                        invested_capital = :capital,
                        last_order_status = 'BUY_FILLED_IBKR',
                        updated_at = NOW()
                    WHERE id = :id
                """), {
                    "order_id": str(order_id), 
                    "id": pos['id'],
                    "entry_price": entry_price,
                    "capital": pos['capital']
                })
                
                db.execute(text("""
                    INSERT INTO gold.trade_executions
                    (strategy_id, ticker, execution_mode, order_type, side, quantity, price, status, ibkr_order_id, executed_at)
                    VALUES (:strategy_id, :ticker, :mode, 'MARKET', 'BUY', :qty, :price, 'FILLED_IBKR', :order_id, NOW())
                """), {
                    "strategy_id": pos['strategy_id'],
                    "ticker": ticker,
                    "mode": current_mode,
                    "qty": quantity,
                    "price": entry_price,
                    "order_id": str(order_id)
                })
                
                submitted.append({
                    "ticker": ticker,
                    "quantity": quantity,
                    "order_id": order_id,
                    "fill_price": entry_price,  # Include the golden source price
                    "capital": pos['capital']
                })
            else:
                error = order_result.get('error', 'Unknown error') if order_result else 'No result'
                failed.append({
                    "ticker": ticker,
                    "error": error
                })
                
        except Exception as e:
            failed.append({
                "ticker": ticker,
                "error": str(e)
            })
    
    db.commit()
    
    return {
        "success": True,
        "mode": current_mode,
        "total_pending": len(positions),
        "submitted": len(submitted),
        "failed": len(failed),
        "orders": submitted,
        "errors": failed
    }


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
            SELECT COUNT(*) as cnt FROM gold.paper_strategies
        """)).fetchone()
        positions_count = count_result.cnt if count_result else 0
        
        trades_result = db.execute(text("""
            SELECT COUNT(*) as cnt FROM gold.trade_executions
        """)).fetchone()
        trades_count = trades_result.cnt if trades_result else 0
        
        # Delete all paper strategies
        db.execute(text("""
            DELETE FROM gold.paper_strategies
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
                DELETE FROM consumption.Performance_Trades_History
            """))
        except Exception as e:
            logger.warning(f"Could not clear Performance_Trades_History: {e}")
            
        # Also try to delete from consumption.Performance_Portfolio_Summary if it exists
        try:
            db.execute(text("""
                DELETE FROM consumption.Performance_Portfolio_Summary WHERE portfolio_type = 'PAPER'
            """))
        except:
            pass
        
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
        FROM gold.strategy_definitions WHERE strategy_id = :strategy_id
    """), {"strategy_id": strategy_id}).fetchone()
    
    if not strategy:
        raise HTTPException(status_code=404, detail="Strategy not found")
    
    pool_usage = db.execute(text("""
        SELECT COALESCE(SUM(capital), 0) as used_capital, COUNT(*) as active_positions
        FROM gold.paper_strategies WHERE strategy_id = :strategy_id AND status = 'ACTIVE'
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
        UPDATE gold.strategy_definitions SET assigned_capital = :total, updated_at = NOW()
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
    mode_result = db.execute(text("""
        SELECT value FROM gold.platform_settings 
        WHERE key = 'global_execution_mode'
    """)).fetchone()
    current_mode = mode_result.value if mode_result else 'SIMULATION'
    
    strategy = db.execute(text("SELECT * FROM gold.strategy_definitions WHERE strategy_id = :sid AND jt_ready = TRUE"),
                         {"sid": strategy_id}).fetchone()
    if not strategy:
        raise HTTPException(status_code=404, detail=f"Strategy {strategy_id} not found")
    
    pool_status = db.execute(text("""
        SELECT COALESCE(SUM(capital), 0) as used FROM gold.paper_strategies
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
                INSERT INTO gold.paper_strategies (strategy_id, ticker, capital, status, execution_mode, created_at, updated_at)
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


@app.post("/api/strategies/deploy-monitoring")
def deploy_strategy_monitoring(payload: dict, db: Session = Depends(get_db)):
    """Deploy strategy in monitoring mode - monitors all universe tickers, auto-trades on signal"""
    strategy_id = payload.get("strategy_id")
    capital_per_trade = payload.get("capital_per_trade", 25000)
    max_positions = payload.get("max_positions", 4)
    
    # Get current execution mode
    mode_result = db.execute(text("""
        SELECT value FROM gold.platform_settings WHERE key = 'global_execution_mode'
    """)).fetchone()
    current_mode = mode_result.value if mode_result else 'SIMULATION'
    
    # Mark strategy as deployed for monitoring
    # This creates a "monitoring entry" that the signal checker will use
    db.execute(text("""
        INSERT INTO gold.paper_strategies (
            strategy_id, ticker, capital, status, execution_mode, 
            created_at, updated_at, target_price, stop_loss
        ) VALUES (
            :strategy_id, '__MONITORING__', :capital, 'MONITORING', :mode, 
            NOW(), NOW(), :target_price, :stop_loss
        )
        ON CONFLICT (strategy_id, ticker) DO UPDATE SET 
            status = 'MONITORING',
            execution_mode = EXCLUDED.execution_mode,
            updated_at = NOW()
    """), {
        "strategy_id": strategy_id,
        "capital": capital_per_trade,
        "mode": current_mode,
        "target_price": str(max_positions),  # Store max positions here
        "stop_loss": str(capital_per_trade)  # Store capital per trade
    })
    
    db.commit()
    
    return {
        "success": True,
        "strategy_id": strategy_id,
        "mode": "MONITORING",
        "execution_mode": current_mode,
        "capital_per_trade": capital_per_trade,
        "max_positions": max_positions,
        "message": f"Strategy {strategy_id} now monitoring all universe tickers. Auto-trading enabled on signal."
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


@app.get("/api/strategies/{strategy_id:path}/top-signals")
def get_strategy_top_signals(strategy_id: str, limit: int = 5, db: Session = Depends(get_db)):
    """Get top signals closest to trigger for a strategy from consumption views"""
    
    # Map strategy IDs to consumption view names
    view_map = {
        # Legacy strategies
        'bb_extreme_monday': 'signals_bb_monday_gold',
        'inside_day_breakout': 'signals_inside_day',
        'rsi_mean_reversion': 'signals_rsi_mean_reversion',
        'volume_breakout': 'signals_volume_breakout',
        'coin_strong_uptrend_gold': 'signals_coin_uptrend',
        'iwm_spy_regime': 'signals_iwm_regime',
        'bb_rsi15_monday': 'signals_bb_rsi15_monday',
        'three_day_monday': 'signals_three_day_monday',
        'dummy_test_always_buy': 'signals_dummy_test',
        # JT Tech Pack G001-G015
        'G001': 'signals_g001',
        'G002': 'signals_g002',
        'G003': 'signals_g003',
        'G004': 'signals_g004',
        'G005': 'signals_g005',
        'G006': 'signals_g006',
        'G007': 'signals_g007',
        'G008': 'signals_g008',
        'G009': 'signals_g009',
        'G010': 'signals_g010',
        'G011': 'signals_g011',
        'G012': 'signals_g012',
        'G013': 'signals_g013',
        'G014': 'signals_g014',
        'G015': 'signals_g015',
    }
    
    view_name = view_map.get(strategy_id)
    if not view_name:
        return {"error": "Unknown strategy", "signals": []}
    
    # Get FIXED universe count from strategy_universes (this never changes per research spec)
    fixed_universe_count = db.execute(text("""
        SELECT COUNT(*) FROM gold.strategy_universes 
        WHERE strategy_id = :sid AND is_active = TRUE
    """), {"sid": strategy_id}).fetchone()[0]
    
    # Query the consumption view - get only the LATEST signal per ticker
    try:
        # Use DISTINCT ON to get only the most recent signal per ticker
        result = db.execute(text(f"""
            SELECT DISTINCT ON (ticker)
                ticker,
                market,
                current_price,
                signal_score,
                signal_triggered,
                win_rate,
                take_profit,
                max_hold,
                sharpe_ratio,
                signal_date
            FROM consumption.{view_name}
            ORDER BY ticker, signal_date DESC
        """)).fetchall()
        
        # Sort by signal_score descending (best signals first)
        signals = []
        for row in result:
            signals.append({
                "ticker": row.ticker,
                "market": row.market,
                "current_price": float(row.current_price) if row.current_price else None,
                "signal_score": int(row.signal_score) if row.signal_score else 0,
                "triggered": bool(row.signal_triggered) if row.signal_triggered is not None else False,
                "win_rate": float(row.win_rate) if row.win_rate else 0,
                "take_profit": row.take_profit,
                "max_hold_days": row.max_hold,
                "sharpe_ratio": float(row.sharpe_ratio) if row.sharpe_ratio else 0,
                "signal_date": str(row.signal_date) if row.signal_date else None
            })
        
        # Sort by signal_score descending
        signals.sort(key=lambda x: x['signal_score'], reverse=True)
        
        # Count triggered vs watching (from ALL signals before limiting)
        triggered_count = sum(1 for s in signals if s['triggered'])
        watching_count = len(signals) - triggered_count
        
        # Limit to top N for display
        signals = signals[:limit]
        
        return {
            "strategy_id": strategy_id,
            "view_name": view_name,
            "universe_count": fixed_universe_count,  # FIXED - from research spec, never changes
            "total_signals": len(signals),
            "triggered_count": triggered_count,
            "watching_count": watching_count,
            "monitoring_count": watching_count,  # For backward compatibility
            "signals": signals
        }
    
    except Exception as e:
        return {"error": str(e), "signals": []}


# --- TRADE ALGO RESEARCHER STRATEGIES ---

@app.get("/api/strategies/researcher")
def get_researcher_strategies(asset_class: str = None, db: Session = Depends(get_db)):
    """Get JT Tech Pack strategies from strategy_registry - ACTIVE only with v2.1 signals"""
    
    # Get strategies from new strategy_registry table
    query = """
        SELECT 
            strategy_id,
            strategy_name as name,
            strategy_name as description,
            priority,
            win_rate,
            signals_per_year,
            entry_logic,
            exit_logic,
            position_size_rules,
            target_assets,
            version,
            status
        FROM gold.strategy_registry
        WHERE status = 'ACTIVE'
    """
    
    result = db.execute(text(query))
    
    strategies = []
    for row in result:
        # Get actual universe count from strategy_universes table
        univ_count = db.execute(text("""
            SELECT COUNT(*) FROM gold.strategy_universes 
            WHERE strategy_id = :sid AND is_active = TRUE
        """), {"sid": row.strategy_id}).fetchone()[0]
        
        # Get sample tickers (first 5)
        sample_tickers = db.execute(text("""
            SELECT ticker FROM gold.strategy_universes 
            WHERE strategy_id = :sid AND is_active = TRUE
            ORDER BY ticker
            LIMIT 5
        """), {"sid": row.strategy_id}).fetchall()
        
        tickers = [t[0] for t in sample_tickers]
        
        # Get yearly win rates from trade history ONLY - no mocking
        yearly_win_rates = {}
        try:
            yearly_result = db.execute(text("""
                SELECT 
                    EXTRACT(YEAR FROM executed_at) as year,
                    COUNT(*) as total_trades,
                    SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END) as winning_trades
                FROM gold.trade_executions
                WHERE strategy_id = :sid
                AND executed_at >= NOW() - INTERVAL '3 years'
                GROUP BY EXTRACT(YEAR FROM executed_at)
                ORDER BY year DESC
            """), {"sid": row.strategy_id}).fetchall()
            
            for yr in yearly_result:
                if yr.total_trades > 0:
                    yearly_win_rates[str(int(yr.year))] = round((yr.winning_trades / yr.total_trades) * 100, 1)
        except:
            pass
        
        # If no historical data, leave empty - NEVER MOCK
        
        # Calculate ACTUAL win rate from historical trade data
        actual_win_rate = 0
        try:
            win_rate_result = db.execute(text("""
                SELECT 
                    COUNT(*) as total_trades,
                    SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END) as winning_trades
                FROM gold.trade_executions
                WHERE strategy_id = :sid
                AND executed_at >= NOW() - INTERVAL '3 years'
            """), {"sid": row.strategy_id}).fetchone()
            
            if win_rate_result and win_rate_result.total_trades > 0:
                actual_win_rate = round((win_rate_result.winning_trades / win_rate_result.total_trades) * 100, 1)
        except:
            pass
        
        # Use strategy definition win rate as fallback only
        display_win_rate = actual_win_rate if actual_win_rate > 0 else (float(row.win_rate) if row.win_rate else 0)
        
        # Check if strategy is deployed (in paper_strategies with MONITORING status)
        deployed_check = db.execute(text("""
            SELECT COUNT(*) FROM gold.paper_strategies 
            WHERE strategy_id = :sid AND status = 'MONITORING'
        """), {"sid": row.strategy_id}).fetchone()[0]
        is_deployed = deployed_check > 0
        
        strategies.append({
            "id": row.strategy_id,
            "name": row.name,
            "description": f"JT Tech Pack: {row.name}",
            "priority": row.priority,
            "win_rate": display_win_rate,
            "actual_win_rate": actual_win_rate,
            "backtest_win_rate": float(row.win_rate) if row.win_rate else 0,
            "yearly_win_rates": yearly_win_rates,
            "signals_per_year": row.signals_per_year,
            "universe": tickers,
            "universe_count": univ_count,
            "status": row.status,
            "is_deployed": is_deployed,
            "source": "trade_algo_researcher",
            "signal_logic": row.entry_logic,
            "exit_logic": row.exit_logic,
            "position_size": row.position_size_rules,
            "version": row.version
        })
    
    return {"strategies": strategies, "count": len(strategies)}


@app.get("/api/strategies/{strategy_id:path}")
def get_strategy_by_id(strategy_id: str, db: Session = Depends(get_db)):
    """Get strategy details including signal logic and entry/exit conditions"""
    result = db.execute(text("""
        SELECT 
            strategy_id,
            name,
            description,
            asset_class,
            direction,
            time_horizon,
            sharpe_ratio,
            max_drawdown,
            win_rate,
            universe_tickers,
            max_position_pct,
            venue,
            status,
            signal_logic,
            exit_logic,
            trigger_example,
            why_it_works,
            execution_mode
        FROM gold.strategy_definitions
        WHERE strategy_id = :strategy_id
    """), {"strategy_id": strategy_id}).fetchone()
    
    if not result:
        raise HTTPException(status_code=404, detail=f"Strategy {strategy_id} not found")
    
    # Parse signal logic and exit logic
    tickers = result.universe_tickers.split(',') if result.universe_tickers else []
    
    return {
        "strategy_id": result.strategy_id,
        "name": result.name,
        "description": result.description,
        "asset_class": result.asset_class,
        "direction": result.direction,
        "time_horizon": result.time_horizon,
        "sharpe_ratio": float(result.sharpe_ratio) if result.sharpe_ratio else 0,
        "max_drawdown": float(result.max_drawdown) if result.max_drawdown else 0,
        "win_rate": float(result.win_rate) if result.win_rate else 0,
        "universe": tickers,
        "universe_count": len(tickers),
        "max_position_pct": float(result.max_position_pct) if result.max_position_pct else 0.05,
        "venue": result.venue,
        "status": result.status,
        "execution_mode": result.execution_mode,
        "signal_logic": result.signal_logic or "Entry conditions not specified",
        "exit_logic": result.exit_logic or "Exit at +5% profit (win) or -5% loss (stop loss)",
        "trigger_example": result.trigger_example or "See strategy description",
        "why_it_works": result.why_it_works or "",
        # Derived fields for frontend
        "buy_signal": result.signal_logic or "BUY signal triggered by strategy logic",
        "sell_signal": result.exit_logic or "SELL at +5% profit target or -5% stop loss",
        "take_profit": "+5% profit target",
        "stop_loss": "-5% stop loss limit"
    }


# --- STRATEGY SCREENER APIs ---

@app.post("/api/strategies/{strategy_id:path}/mode")
def set_execution_mode(strategy_id: str, payload: dict, db: Session = Depends(get_db)):
    """Set execution mode: SIMULATION, PAPER_TRADING, or LIVE_TRADING"""
    mode = payload.get("execution_mode", "SIMULATION")
    
    if mode not in ["SIMULATION", "PAPER_TRADING", "LIVE_TRADING"]:
        raise HTTPException(status_code=400, detail="Invalid mode. Use SIMULATION, PAPER_TRADING, or LIVE_TRADING")
    
    result = db.execute(text("""
        UPDATE gold.strategy_definitions
        SET execution_mode = :mode,
            updated_at = NOW()
        WHERE strategy_id = :strategy_id
        RETURNING strategy_id, name, execution_mode
    """), {"strategy_id": strategy_id, "mode": mode}).fetchone()
    
    if not result:
        raise HTTPException(status_code=404, detail=f"Strategy {strategy_id} not found")
    
    db.commit()
    
    return {
        "success": True,
        "strategy_id": result.strategy_id,
        "strategy_name": result.name,
        "execution_mode": result.execution_mode,
        "message": f"Execution mode set to {mode}"
    }


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
        SELECT strategy_id, name, execution_mode, venue
        FROM gold.strategy_definitions
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
    
    if execution_mode == "SIMULATION":
        # Simulation mode - just update database
        if side == "BUY":
            db.execute(text("""
                UPDATE gold.paper_strategies
                SET invested_capital = invested_capital + :amount,
                    available_capital = available_capital - :amount,
                    trades_count = trades_count + 1,
                    last_order_status = 'SIMULATED_BUY'
                WHERE strategy_id = :strategy_id AND ticker = :ticker
            """), {"strategy_id": strategy_id, "ticker": ticker, "amount": quantity * 100})
        else:
            db.execute(text("""
                UPDATE gold.paper_strategies
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
        SELECT strategy_id, name, execution_mode, venue
        FROM gold.strategy_definitions
        WHERE strategy_id = :strategy_id
    """), {"strategy_id": strategy_id}).fetchone()
    
    if not result:
        raise HTTPException(status_code=404, detail="Strategy not found")
    
    # Count positions by mode
    sim_count = db.execute(text("""
        SELECT COUNT(*) FROM gold.paper_strategies
        WHERE strategy_id = :strategy_id AND execution_mode = 'SIMULATION'
    """), {"strategy_id": strategy_id}).scalar() or 0
    
    return {
        "strategy_id": result.strategy_id,
        "strategy_name": result.name,
        "execution_mode": result.execution_mode or "SIMULATION",
        "venue": result.venue,
        "positions_count": sim_count,
        "available_modes": ["SIMULATION", "PAPER_TRADING", "LIVE_TRADING"],
        "risk_level": {
            "SIMULATION": "ZERO",
            "PAPER_TRADING": "LOW",
            "LIVE_TRADING": "HIGH"
        }.get(result.execution_mode or "SIMULATION", "UNKNOWN")
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
    strategy = db.execute(text("""
        SELECT * FROM gold.strategy_definitions
        WHERE strategy_id = :sid AND jt_ready = TRUE
    """), {"sid": strategy_id}).fetchone()
    
    if not strategy:
        # Check if it's a regular template
        strategy = db.execute(text("""
            SELECT * FROM gold.strategy_templates
            WHERE id = :sid
        """), {"sid": strategy_id}).fetchone()
    
    if not strategy:
        raise HTTPException(status_code=404, detail=f"Strategy {strategy_id} not found")
    
    created = []
    failed = []
    
    for ticker in tickers:
        try:
            # Create paper trading strategy instance
            db.execute(text("""
                INSERT INTO gold.paper_strategies 
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
            direction,
            time_horizon,
            sharpe_ratio,
            max_drawdown,
            win_rate,
            avg_hold_days,
            universe_count,
            max_position_pct,
            venue,
            capacity_millions,
            backtest_period
        FROM gold.strategy_definitions
        WHERE strategy_id = :sid AND jt_ready = TRUE
    """), {"sid": strategy_id}).fetchone()
    
    if result:
        return {
            "id": result.id,
            "name": result.name,
            "description": result.description,
            "asset_class": result.asset_class,
            "direction": result.direction,
            "time_horizon": result.time_horizon,
            "metrics": {
                "sharpe_ratio": float(result.sharpe_ratio) if result.sharpe_ratio else None,
                "max_drawdown": float(result.max_drawdown) if result.max_drawdown else None,
                "win_rate": float(result.win_rate) if result.win_rate else None,
                "avg_hold_days": float(result.avg_hold_days) if result.avg_hold_days else None,
                "universe_count": result.universe_count,
                "max_position_pct": float(result.max_position_pct) if result.max_position_pct else None,
                "capacity_millions": float(result.capacity_millions) if result.capacity_millions else None
            },
            "venue": result.venue,
            "backtest_period": result.backtest_period,
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
            FROM gold.strategy_definitions
            WHERE strategy_id = :strategy_id AND jt_ready = TRUE
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
        FROM gold.paper_strategies ps
        LEFT JOIN gold.strategy_definitions sd ON ps.strategy_id = sd.strategy_id
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


@app.post("/api/positions/close-by-ticker")
async def close_position_by_ticker(payload: dict, db: Session = Depends(get_db)):
    """
    Close a position by ticker symbol (for IBKR golden source positions).
    Expects: { "ticker": "AAPL", "quantity": 100, "action": "SELL" }
    """
    from ib_insync import IB, MarketOrder, Stock
    
    try:
        ticker = payload.get("ticker")
        quantity = payload.get("quantity", 0)
        action = payload.get("action", "SELL")
        
        if not ticker:
            raise HTTPException(status_code=400, detail="Ticker required")
        
        # Connect to IBKR directly with fresh client ID
        ib = IB()
        try:
            import random
            client_id = random.randint(50, 99)
            await ib.connectAsync('52.74.14.181', 4002, clientId=client_id, timeout=10)
            
            # Create contract
            contract = Stock(ticker, 'SMART', 'USD')
            qualified = ib.qualifyContracts(contract)
            if not qualified:
                # Try without exchange for international
                contract = Stock(ticker, '', 'USD')
                qualified = ib.qualifyContracts(contract)
            
            if qualified:
                contract = qualified[0]
            
            # Place market order
            order = MarketOrder(action, quantity)
            trade = ib.placeOrder(contract, order)
            
            # Wait briefly for order confirmation
            await asyncio.sleep(2)
            
            order_id = trade.order.orderId if trade.order else None
            order_status = trade.orderStatus.status if trade.orderStatus else 'Pending'
            
            ib.disconnect()
            
            # Record the trade in DB
            db.execute(text("""
                INSERT INTO gold.trade_executions 
                (ticker, side, quantity, exit_price, pnl, status, executed_at, execution_mode, strategy_id, order_id)
                VALUES (:ticker, :side, :qty, 0, 0, :status, NOW(), 'PAPER_TRADING', 'manual_close', :order_id)
            """), {
                "ticker": ticker,
                "side": action,
                "qty": quantity,
                "status": order_status,
                "order_id": order_id
            })
            db.commit()
            
            return {
                "success": True,
                "ticker": ticker,
                "action": action,
                "quantity": quantity,
                "order_id": order_id,
                "status": order_status,
                "message": f"{action} order {order_id} placed for {ticker} x{quantity} - Status: {order_status}"
            }
            
        except Exception as e:
            try:
                ib.disconnect()
            except:
                pass
            raise e
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error closing position: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/performance/deployment-stats")
def get_deployment_stats(range: str = "7d", db: Session = Depends(get_db)):
    """
    Get deployment performance stats with real vs potential P&L analysis.
    Shows what was actually captured vs what could have been captured.
    """
    try:
        # Get all deployed strategies
        deployed_strategies = db.execute(text("""
            SELECT DISTINCT ON (strategy_id) 
                strategy_id, 
                ticker,
                capital,
                status,
                created_at
            FROM gold.paper_strategies 
            WHERE status IN ('ACTIVE', 'CLOSED')
            ORDER BY strategy_id, created_at DESC
        """)).fetchall()
        
        total_strategies_query = db.execute(text("""
            SELECT COUNT(*) FROM gold.strategy_definitions WHERE jt_ready = TRUE
        """)).fetchone()
        
        total_strategies = total_strategies_query[0] if total_strategies_query else 0
        
        # Aggregate stats
        real_pnl = 0
        potential_pnl = 0
        signals_generated = 0
        signals_executed = 0
        total_win_rate = 0
        
        strategy_breakdown = []
        
        for deploy in deployed_strategies:
            strategy_id = deploy.strategy_id
            
            # Get strategy info
            strat_info = db.execute(text("""
                SELECT name, win_rate FROM gold.strategy_definitions WHERE strategy_id = :sid
            """), {"sid": strategy_id}).fetchone()
            
            strat_name = strat_info.name if strat_info else strategy_id
            win_rate = strat_info.win_rate if strat_info else 0
            total_win_rate += win_rate
            
            # Count signals generated (from golden_strategy_signals)
            signals = db.execute(text("""
                SELECT COUNT(*) as count, 
                       AVG(CASE WHEN signal_type = 'BUY' THEN expected_return ELSE 0 END) as avg_return
                FROM gold.golden_strategy_signals 
                WHERE strategy_id = :sid 
                AND signal_date >= NOW() - INTERVAL '7 days'
            """), {"sid": strategy_id}).fetchone()
            
            strat_signals = signals.count if signals else 0
            avg_expected_return = signals.avg_return or 0
            
            # Count actual trades executed
            trades = db.execute(text("""
                SELECT COUNT(*) as count,
                       SUM(pnl) as total_pnl
                FROM gold.trade_executions 
                WHERE strategy_id = :sid 
                AND executed_at >= NOW() - INTERVAL '7 days'
            """), {"sid": strategy_id}).fetchone()
            
            strat_trades = trades.count if trades else 0
            strat_real_pnl = float(trades.total_pnl) if trades and trades.total_pnl else 0
            
            # Calculate potential P&L (if all signals were traded)
            # Assume 25% of capital per trade
            capital_per_trade = float(deploy.capital) * 0.25 if deploy.capital else 25000
            expected_ret = float(avg_expected_return) if avg_expected_return else 0
            strat_potential_pnl = strat_signals * capital_per_trade * (expected_ret / 100)
            
            real_pnl += strat_real_pnl
            potential_pnl += strat_potential_pnl
            signals_generated += strat_signals
            signals_executed += strat_trades
            
            strategy_breakdown.append({
                "id": strategy_id,
                "name": strat_name,
                "win_rate": win_rate,
                "signals_generated": strat_signals,
                "signals_executed": strat_trades,
                "real_pnl": strat_real_pnl,
                "potential_pnl": strat_potential_pnl,
                "capital_deployed": deploy.capital
            })
        
        avg_win_rate = total_win_rate / len(deployed_strategies) if deployed_strategies else 0
        
        return {
            "success": True,
            "strategies_deployed": len(deployed_strategies),
            "strategies_total": total_strategies,
            "aggregated_win_rate": round(avg_win_rate, 1),
            "real_pnl": round(real_pnl, 2),
            "potential_pnl": round(potential_pnl, 2),
            "signals_generated": signals_generated,
            "signals_executed": signals_executed,
            "strategy_breakdown": strategy_breakdown,
            "period": range
        }
        
    except Exception as e:
        logger.error(f"Error getting deployment stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
# Add these endpoints to backend/app/main.py

@app.get("/api/orders/pending")
def get_pending_orders(db: Session = Depends(get_db)):
    """Get all pending and recently filled orders for display in frontend"""
    try:
        result = db.execute(text("""
            SELECT 
                strategy_id,
                strategy_name,
                ticker,
                action,
                quantity,
                status,
                filled,
                remaining,
                avg_fill_price,
                submit_time,
                execution_time,
                display_status,
                execution_note
            FROM consumption.pending_orders
            LIMIT 50
        """)).fetchall()
        
        orders = []
        for row in result:
            orders.append({
                "strategy_id": row.strategy_id,
                "strategy_name": row.strategy_name,
                "ticker": row.ticker,
                "action": row.action,
                "quantity": row.quantity,
                "status": row.status,
                "filled": row.filled,
                "remaining": row.remaining,
                "avg_fill_price": float(row.avg_fill_price) if row.avg_fill_price else None,
                "submit_time": str(row.submit_time) if row.submit_time else None,
                "execution_time": str(row.execution_time) if row.execution_time else None,
                "display_status": row.display_status,
                "execution_note": row.execution_note
            })
        
        return {
            "orders": orders,
            "pending_count": sum(1 for o in orders if o["status"] in ["Submitted", "PreSubmitted", "PendingSubmit"]),
            "filled_count": sum(1 for o in orders if o["status"] == "Filled")
        }
    except Exception as e:
        logger.error(f"Error fetching pending orders: {e}")
        return {"orders": [], "error": str(e), "pending_count": 0, "filled_count": 0}

@app.get("/api/orders/history")
def get_order_history(limit: int = 50, db: Session = Depends(get_db)):
    """Get full order history"""
    try:
        result = db.execute(text(f"""
            SELECT * FROM consumption.order_history
            LIMIT {limit}
        """)).fetchall()
        
        orders = []
        for row in result:
            orders.append({
                "id": row.id,
                "strategy_id": row.strategy_id,
                "strategy_name": row.strategy_name,
                "ticker": row.ticker,
                "action": row.action,
                "quantity": row.quantity,
                "status": row.status,
                "filled": row.filled,
                "avg_fill_price": float(row.avg_fill_price) if row.avg_fill_price else None,
                "submit_time": str(row.submit_time) if row.submit_time else None,
                "status_display": row.status_display
            })
        
        return {"orders": orders, "count": len(orders)}
    except Exception as e:
        logger.error(f"Error fetching order history: {e}")
        return {"orders": [], "error": str(e), "count": 0}
