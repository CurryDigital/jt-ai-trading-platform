"""
JTCML Trading Platform — FastAPI Backend
=========================================
Platform layer: API endpoints + IBKR execution.
Data ingestion/refresh is handled by the DE agent.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

# TODO: stock_detail router may still use yfinance internally — audit and migrate to DB
from app.api.stock_detail import router as stock_detail_router

# Route modules
from app.routes import market, stocks, fx, crypto, strategies, positions
from app.routes import performance, execution, ibkr, alerts, metadata, hkex

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="JTCML Trading Platform",
    description="Trading platform API — DB reads + IBKR execution",
    version="2.0.0",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://trade.jtcml.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register route modules
app.include_router(stock_detail_router)
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


@app.get("/api/health")
def health_check():
    return {"status": "ok", "version": "2.0.0", "architecture": "platform-only"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
