from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import text
from pydantic import BaseModel
import yfinance as yf
import json
import datetime

# Internal Imports
from app.db.session import (
    SessionLocal, Base, engine, Inventory, GlobalState,
    ConsumptionStock, ConsumptionMarket, ConsumptionFx, ConsumptionCommodity, ConsumptionCrypto, Trade, QuantStrategy
)
from app.core_logic.data.wholistic_pipeline import (
    refresh_indices_and_mood, refresh_fx_layer, refresh_commodity_layer, refresh_crypto_layer, refresh_stock_layer, refresh_hft_layer
)
from app.core_logic.agents.research_swarm import research_swarm

app = FastAPI()

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
                        strategy_manager.run_tick()
                    
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
    asyncio.create_task(scheduler_loop())

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

@app.post("/api/inventory/analyze/all")
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
    regions = {'US': 'DJI', 'HK': 'HSI', 'EU': 'STOXX50', 'CN': 'SSE', 'SG': 'STI'}
    pulse_data = {}
    for r, label in regions.items():
        # Iteration 38: API Performance Fix - DO NOT fetch yfinance in the request loop
        # Pull everything from GlobalState which is synced by the background scheduler
        price_row = db.query(GlobalState).filter(GlobalState.key == f"index_price_{label}").first()
        change_row = db.query(GlobalState).filter(GlobalState.key == f"index_change_{label}").first()
        rat = db.query(GlobalState).filter(GlobalState.key == f"index_rationale_{label}").first()
        
        pulse_data[r] = {
            "value": float(price_row.value) if price_row else 0.0,
            "change": float(change_row.value) if change_row else 0.0,
            "label": label,
            "rationale": rat.rationale if rat and rat.rationale else rat.value if rat else "Syncing...",
            "estimates": rat.estimates if rat and rat.estimates else {"1d": "---", "1w": "---", "1m": "---"}
        }
    risk = db.query(GlobalState).filter(GlobalState.key == "system_risk_level").first()
    shock = db.query(GlobalState).filter(GlobalState.key == "shock_monitor_text").first()
    return { "indices": pulse_data, "system_risk": risk.value if risk else "LOW", "shock_text": shock.value if shock else "Nominal" }

@app.get("/api/signals/1")
def get_signals(db: Session = Depends(get_db)):
    signals = db.query(ConsumptionStock).all()
    res = []
    for s in signals:
        try:
            ret_val = float(s.est_7d.replace('%', '').replace('+', '')) if s.est_7d and '%' in s.est_7d else 0.0
        except: ret_val = 0.0
        rec_score = (s.final_score or 0) * 0.6 + (ret_val / 10.0) * 0.4
        res.append({
            "ticker": s.ticker, "market": s.market, "horizon": s.horizon,
            "price": round(s.close_price or 0, 2), "change": round(s.daily_change or 0, 2),
            "total_conf": s.final_score, "trad_conf": s.trad_confidence,
            "swarm_conf": s.swarm_confidence,
            "estimates": {"1d": s.est_1d, "7d": s.est_7d, "1m": s.est_1m},
            "win_rate": s.win_rate, "tags": s.strategy_tags,
            "metrics": s.metrics, "logic": s.logic_summary,
            "sparkline": s.sparkline, "timestamp": s.timestamp,
            "rec_score": rec_score, "candlestick_pattern": s.candlestick_pattern
        })
    res.sort(key=lambda x: x['rec_score'], reverse=True)
    return res

@app.get("/api/fx/pairs")
def get_fx_pairs(db: Session = Depends(get_db)):
    pairs = db.query(ConsumptionFx).all()
    res = []
    for p in pairs:
        price = p.close_price or 0.0
        change = p.daily_change or 0.0
        try:
            ret_val = float(p.est_7d.replace('%', '').replace('+', '')) if p.est_7d and '%' in p.est_7d else 0.0
        except: ret_val = 0.0
        rec_score = (p.confidence or 0) * 0.6 + (ret_val / 5.0) * 0.4
        try:
            sym = p.pair if p.pair.endswith("=X") else f"{p.pair}=X"
            ticker = yf.Ticker(sym); df = ticker.history(period="2d")
            if not df.empty:
                price = df['Close'].iloc[-1]
                prev = df['Close'].iloc[-2] if len(df) > 1 else price
                change = ((price - prev) / prev * 100) if prev != 0 else 0
        except: pass
        res.append({ 
            "ticker": p.pair, "action": p.action, "total_conf": p.confidence, 
            "price": round(price, 4), "change": round(change, 2),
            "estimates": {"1d": p.est_1d, "7d": p.est_7d, "1m": p.est_1m}, 
            "trad_conf": p.trad_confidence, "swarm_conf": p.swarm_confidence,
            "logic": p.reasoning, "sparkline": p.sparkline, "timestamp": p.timestamp,
            "win_rate": p.win_rate, "rec_score": rec_score, "drivers": p.drivers,
            "candlestick_pattern": p.candlestick_pattern
        })
    res.sort(key=lambda x: x['rec_score'], reverse=True)
    return res

@app.get("/api/crypto/pairs")
def get_crypto_pairs(db: Session = Depends(get_db)):
    pairs = db.query(ConsumptionCrypto).all()
    res = []
    for p in pairs:
        price = p.close_price or 0.0
        change = p.daily_change or 0.0
        try:
            ret_val = float(p.est_7d.replace('%', '').replace('+', '')) if p.est_7d and '%' in p.est_7d else 0.0
        except: ret_val = 0.0
        rec_score = (p.swarm_confidence or 0) * 0.5 + (ret_val / 20.0) * 0.5
        try:
            ticker = yf.Ticker(p.ticker); df = ticker.history(period="2d")
            if not df.empty:
                price = df['Close'].iloc[-1]
                prev = df['Close'].iloc[-2] if len(df) > 1 else price
                change = ((price - prev) / prev * 100) if prev != 0 else 0
        except: pass
        res.append({ 
            "ticker": p.ticker, "asset": p.asset, "action": p.action, "total_conf": p.swarm_confidence, 
            "price": round(price, 2), "change": round(change, 2),
            "estimates": {"1d": p.est_1d, "7d": p.est_7d, "1m": p.est_1m}, 
            "trad_conf": p.trad_confidence, "swarm_conf": p.swarm_confidence,
            "logic": p.reasoning, "sparkline": p.sparkline, "timestamp": p.timestamp,
            "mvrv_z_score": p.mvrv_z_score, "fear_greed_index": p.fear_greed_index,
            "funding_rate": p.funding_rate, "gas_price_gwei": p.gas_price_gwei,
            "hash_rate_th_s": p.hash_rate_th_s, "win_rate": p.win_rate,
            "rec_score": rec_score, "candlestick_pattern": p.candlestick_pattern
        })
    res.sort(key=lambda x: x['rec_score'], reverse=True)
    return res

@app.get("/api/commodities/all")
def get_commodities(db: Session = Depends(get_db)):
    assets = db.query(ConsumptionCommodity).all()
    res = []
    for a in assets:
        price = a.close_price or 0.0
        change = a.daily_change or 0.0
        try:
            ret_val = float(a.est_7d.replace('%', '').replace('+', '')) if a.est_7d and '%' in a.est_7d else 0.0
        except: ret_val = 0.0
        rec_score = (a.swarm_confidence or 0) * 0.6 + (ret_val / 8.0) * 0.4
        try:
            ticker = a.ticker; ticker = ticker if ticker.endswith("-USD") or ticker.endswith("=F") else f"{ticker}=F"
            t = yf.Ticker(ticker); df = t.history(period="2d")
            if not df.empty:
                price = df['Close'].iloc[-1]
                prev = df['Close'].iloc[-2] if len(df) > 1 else price
                change = ((price - prev) / prev * 100) if prev != 0 else 0
        except: pass
        res.append({ 
            "ticker": a.ticker, "asset": a.asset, "action": a.action, "total_conf": a.swarm_confidence, 
            "price": round(price, 2), "change": round(change, 2),
            "estimates": {"1d": a.est_1d, "7d": a.est_7d, "1m": a.est_1m}, 
            "trad_conf": a.trad_confidence, "swarm_conf": a.swarm_confidence,
            "logic": a.reasoning, "sparkline": a.sparkline, "timestamp": a.timestamp,
            "win_rate": a.win_rate, "rec_score": rec_score,
            "candlestick_pattern": a.candlestick_pattern
        })
    res.sort(key=lambda x: x['rec_score'], reverse=True)
    return res

@app.get("/api/market/outlook")
def get_market_outlook(db: Session = Depends(get_db)):
    mood = db.query(GlobalState).filter(GlobalState.key == "market_mood_index").first()
    conc = db.query(GlobalState).filter(GlobalState.key == "swarm_conclusion").first()
    recs = db.query(ConsumptionMarket).all()
    return { "market_mood": mood.value if mood else "Stable", "swarm_conclusion": conc.value if conc else "...", "recommendations": [{"sector": r.sector, "ticker": r.ticker, "edge": r.edge_score, "est_1d": r.est_1d, "est_1m": r.est_1m} for r in recs] }

@app.get("/api/inventory/evaluate")
async def get_inventory(db: Session = Depends(get_db)):
    items = db.query(Inventory).all()
    res = []
    for i in items:
        curr_p = i.current_price
        try:
            sym = i.ticker if not i.asset_class == 'FX' else f"{i.ticker}=X"
            if i.asset_class == 'COMMODITY' and not (i.ticker.endswith("=F") or i.ticker.endswith("-USD")):
                 sym = f"{i.ticker}=F"
            t = yf.Ticker(sym); df = t.history(period="1d")
            if not df.empty: curr_p = round(df['Close'].iloc[-1], 4 if i.asset_class == 'FX' else 2)
        except: pass
        e1d, e7d, e1m = "---", "---", "---"
        s = db.query(ConsumptionStock).filter(ConsumptionStock.ticker == i.ticker).order_by(ConsumptionStock.timestamp.desc()).first()
        if s: e1d, e7d, e1m = s.est_1d, s.est_7d, s.est_1m
        else:
            f = db.query(ConsumptionFx).filter(ConsumptionFx.pair == i.ticker.replace("=X","")).order_by(ConsumptionFx.timestamp.desc()).first()
            if f: e1d, e7d, e1m = f.est_1h, f.est_1d, f.est_7d
            else:
                c = db.query(ConsumptionCommodity).filter(ConsumptionCommodity.ticker == i.ticker).order_by(ConsumptionCommodity.timestamp.desc()).first()
                if c: e1d, e7d, e1m = c.est_1d, c.est_7d, c.est_1m
                else:
                    cry = db.query(ConsumptionCrypto).filter(ConsumptionCrypto.ticker == i.ticker).order_by(ConsumptionCrypto.timestamp.desc()).first()
                    if cry: e1d, e7d, e1m = cry.est_1d, cry.est_7d, cry.est_1m
        res.append({
            "ticker": i.ticker, "asset_class": i.asset_class, "quantity": i.quantity,
            "buy": i.buy_price, "current": curr_p, 
            "win_loss": f"{((curr_p - i.buy_price)/i.buy_price*100):+.2f}%" if i.buy_price else "0.00%",
            "est_1d": e1d, "est_7d": e7d, "est_1m": e1m,
            "swarm_dec": i.analysis.get('decision') if i.analysis and isinstance(i.analysis, dict) else 'HOLD',
            "rationale": i.analysis.get('reasoning') if i.analysis and isinstance(i.analysis, dict) else '...'
        })
    return res

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

@app.get("/api/maintenance/status/stocks")
async def api_status_stocks(db: Session = Depends(get_db)):
    exists = db.execute(text("SELECT 1 FROM gold.stock_metrics WHERE date > NOW() - INTERVAL '5 minutes' LIMIT 1")).first()
    return {"status": "Live" if exists else "Idle"}

@app.get("/api/velocity/trades")
async def get_velocity_trades(db: Session = Depends(get_db)):
    trades = db.query(Trade).order_by(Trade.timestamp.desc()).all()
    return trades

@app.get("/api/velocity/summary")
async def get_velocity_summary(db: Session = Depends(get_db)):
    # 1. Calculate Inventory Value
    inventory = db.query(Inventory).all()
    total_val = sum([i.current_price * i.quantity for i in inventory])
    
    # 2. Today's P&L (from executed trades today)
    today = datetime.date.today()
    trades_today = db.query(Trade).filter(Trade.timestamp >= today).all()
    pnl_today = sum([t.pnl for t in trades_today if t.pnl is not None])
    
    return {
        "inventory_value": total_val,
        "today_pnl": pnl_today,
        "active_positions": len(inventory),
        "executions_today": len(trades_today)
    }

from app.services.ib_service import ib_quant_service
from app.services.ib_web_service import ib_web_service
from app.services.trading_service import trading_service
from app.services.strategy_manager import strategy_manager

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
        strat = strategy_manager.create_fx_strategy(pair, qty)
        return strat
    except Exception as e:
        print(f"Quant Strategy Create Error: {e}")
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
    perf = db.execute(text("SELECT period, strategy_return, benchmark_return FROM gold.strategy_performance")).fetchall()
    curve = db.execute(text("SELECT timestamp, equity_value, benchmark_value FROM gold.backtest_curve_data ORDER BY timestamp ASC")).fetchall()
    return {
        "metrics": [dict(r._mapping) for r in perf],
        "curve": [{"ts": r.timestamp.strftime('%m-%d'), "strat": r.equity_value, "bench": r.benchmark_value} for r in curve]
    }

@app.post("/api/maintenance/refresh/hft")
async def api_refresh_hft(bg: BackgroundTasks):
    bg.add_task(refresh_hft_layer); return {"status": "Syncing"}

@app.get("/api/maintenance/status/hft")
async def api_status_hft(db: Session = Depends(get_db)):
    exists = db.execute(text("SELECT 1 FROM consumption.hft_matrix WHERE timestamp > NOW() - INTERVAL '5 minutes' LIMIT 1")).first()
    return {"status": "Live" if exists else "Idle"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
