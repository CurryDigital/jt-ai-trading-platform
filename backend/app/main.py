from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
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
    ConsumptionStock, ConsumptionMarket, ConsumptionFx, ConsumptionCommodity, ConsumptionCrypto
)
from app.core_logic.data.wholistic_pipeline import (
    refresh_indices_and_mood, refresh_fx_layer, refresh_commodity_layer, refresh_crypto_layer, refresh_stock_layer, refresh_hft_layer
)
from app.core_logic.backtesting.strategy_sim import simulate_strategy_performance

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class InventoryAdd(BaseModel):
    ticker: str
    asset_class: str
    quantity: float
    buy_price: float

def get_db():
    db = SessionLocal()
    try: yield db
    finally: db.close()

@app.get("/api/macro/pulse")
def get_macro_pulse(db: Session = Depends(get_db)):
    regions = {'US': 'DJI', 'HK': 'HSI', 'EU': 'STOXX50', 'CN': 'SSE', 'SG': 'STI'}
    pulse_data = {}
    for r, label in regions.items():
        try:
            yf_map = {'DJI':'^DJI', 'HSI':'^HSI', 'STOXX50':'^STOXX50E', 'SSE':'000001.SS', 'STI':'^STI'}
            sym = yf_map[label]
            ticker = yf.Ticker(sym); df = ticker.history(period="2d")
            price = df['Close'].iloc[-1] if not df.empty else 0
            prev = df['Close'].iloc[-2] if len(df) > 1 else price
            change = ((price - prev) / prev * 100) if prev != 0 else 0
        except: price, change = 0, 0
        rat = db.query(GlobalState).filter(GlobalState.key == f"index_rationale_{label}").first()
        pulse_data[r] = {
            "value": round(price, 2), "change": round(change, 2), "label": label,
            "rationale": rat.value if rat else "Awaiting swarm analysis...",
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
        price = s.close_price or 0.0
        change = s.daily_change or 0.0
        try:
            ticker = yf.Ticker(s.ticker)
            df = ticker.history(period="2d")
            if not df.empty:
                price = df['Close'].iloc[-1]
                prev = df['Close'].iloc[-2] if len(df) > 1 else price
                change = ((price - prev) / prev * 100) if prev != 0 else 0
        except: pass
        
        res.append({
            "ticker": s.ticker, "market": s.market, "horizon": s.horizon,
            "price": round(price, 2), "change": round(change, 2),
            "total_conf": s.final_score, "trad_conf": s.trad_confidence,
            "swarm_conf": s.swarm_confidence,
            "estimates": {"1d": s.est_1d, "7d": s.est_7d, "1m": s.est_1m},
            "metrics": s.metrics, "logic": s.logic_summary,
            "sparkline": s.sparkline, "timestamp": s.timestamp
        })
    return res

@app.get("/api/fx/pairs")
def get_fx_pairs(db: Session = Depends(get_db)):
    pairs = db.query(ConsumptionFx).all()
    res = []
    for p in pairs:
        price = p.close_price or 0.0
        change = p.daily_change or 0.0
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
            "logic": p.reasoning, "sparkline": p.sparkline, "timestamp": p.timestamp
        })
    return res

@app.get("/api/crypto/pairs")
def get_crypto_pairs(db: Session = Depends(get_db)):
    pairs = db.query(ConsumptionCrypto).all()
    res = []
    for p in pairs:
        price = p.close_price or 0.0
        change = p.daily_change or 0.0
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
            "logic": p.reasoning, "sparkline": p.sparkline, "timestamp": p.timestamp
        })
    return res

@app.get("/api/commodities/all")
def get_commodities(db: Session = Depends(get_db)):
    assets = db.query(ConsumptionCommodity).all()
    res = []
    for a in assets:
        price = a.close_price or 0.0
        change = a.daily_change or 0.0
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
            "logic": a.reasoning, "sparkline": a.sparkline, "timestamp": a.timestamp
        })
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
        # Normalize ticker
        ticker = item.ticker.strip().upper()
        sym = ticker if not item.asset_class == 'FX' else f"{ticker}=X"
        if item.asset_class == 'COMMODITY' and not (ticker.endswith("=F") or ticker.endswith("-USD")):
             sym = f"{ticker}=F"
        
        t_yf = yf.Ticker(sym)
        df = t_yf.history(period="1d")
        curr_p = df['Close'].iloc[-1] if not df.empty else item.buy_price
    except Exception as e:
        print(f"Inventory Add YFinance Error: {e}")
        curr_p = item.buy_price

    new_item = Inventory(
        ticker=ticker, 
        asset_class=item.asset_class, 
        quantity=item.quantity,
        buy_price=item.buy_price, 
        current_price=curr_p, 
        win_loss="0.0%",
        analysis={"decision": "HOLD", "reasoning": "Position added. AI Swarm analysis pending next sync."},
        status="held"
    )
    db.add(new_item)
    db.commit()
    return {"status": "success"}

@app.delete("/api/inventory/delete/{ticker}")
async def delete_from_inventory(ticker: str, db: Session = Depends(get_db)):
    db.execute(text("DELETE FROM consumption.inventory WHERE ticker = :t"), {"t": ticker})
    db.commit()
    return {"status": "success"}

@app.get("/api/metadata/formulas")
def get_formula_metadata(db: Session = Depends(get_db)):
    res = db.execute(text("SELECT asset_class, metric_name, formula_raw, description, weight_impact FROM gold.metric_definitions ORDER BY asset_class, metric_name"))
    return [dict(r._mapping) for r in res.fetchall()]

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
    bg.add_task(refresh_stock_layer)
    bg.add_task(simulate_strategy_performance) # Sync backtest as well
    return {"status": "Syncing"}

@app.get("/api/maintenance/status/stocks")
async def api_status_stocks(db: Session = Depends(get_db)):
    exists = db.execute(text("SELECT 1 FROM gold.stock_metrics WHERE date > NOW() - INTERVAL '5 minutes' LIMIT 1")).first()
    return {"status": "Live" if exists else "Idle"}

@app.get("/api/hft/matrix")
def get_hft_matrix(db: Session = Depends(get_db)):
    res = db.execute(text("SELECT * FROM consumption.hft_matrix ORDER BY timestamp DESC, ticker ASC"))
    return [dict(r._mapping) for r in res.fetchall()]

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
