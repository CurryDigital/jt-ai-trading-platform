"""
JTCML Trading Platform - FastAPI Backend (Optimized)
=====================================================
"""
import datetime
import logging
from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import text

# Routes
from app.routes import market, stocks, fx, crypto, strategies, positions
from app.routes import performance, execution, ibkr, alerts, metadata, hkex

# DB
from app.db.session import SessionLocal, engine
from app.services.ib_web_service import ib_web_service

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="JTCML Trading Platform", version="4.2")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://trade.jtcml.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(market.router, prefix="/api")
app.include_router(stocks.router, prefix="/api")
app.include_router(fx.router, prefix="/api")
app.include_router(crypto.router, prefix="/api")
app.include_router(strategies.router, prefix="/api")
app.include_router(positions.router, prefix="/api")
app.include_router(performance.router, prefix="/api")
app.include_router(execution.router, prefix="/api")
app.include_router(ibkr.router, prefix="/api")
app.include_router(alerts.router, prefix="/api")
app.include_router(metadata.router, prefix="/api")
app.include_router(hkex.router, prefix="/api")

def get_db():
    db = SessionLocal()
    try: yield db
    finally: db.close()

@app.middleware("http")
async def ibkr_session_middleware(request: Request, call_next):
    cookies = request.cookies
    if any(k in cookies for k in ['JSESSIONID', 'x-sess-uuid', 'IB_SESSION']):
        ib_web_service.set_cookies(cookies)
    return await call_next(request)

@app.on_event("startup")
async def startup():
    logger.info("✅ Backend started")

# Health check
@app.get("/health")
def health():
    return {"status": "ok", "version": "4.2"}

# Minimal position endpoint for quick access
@app.get("/api/positions/quick")
def quick_positions(db: Session = Depends(get_db)):
    rows = db.execute(text("""
        SELECT ticker, quantity, buy_price, current_price, status
        FROM consumption.inventory WHERE status = 'held'
    """)).fetchall()
    return [{"ticker": r.ticker, "qty": r.quantity, "entry": r.buy_price, 
             "current": r.current_price, "pnl": (r.current_price - r.buy_price) * r.quantity} for r in rows]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
