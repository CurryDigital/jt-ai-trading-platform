"""
JTCML Trading Platform - FastAPI Backend (Optimized)
=====================================================
Compact version: 2.6KB vs 217KB original
"""
import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

# Import all route modules
from app.routes import market, stocks, fx, crypto, strategies, positions, agents
from app.routes import performance, execution, ibkr, alerts, metadata, hkex
from app.services.ib_web_service import ib_web_service

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="JTCML Trading Platform", version="4.2-compact")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://trade.jtcml.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include all routers (routes already have /api prefix)
routers = [market, stocks, fx, crypto, strategies, positions, agents,
           performance, execution, ibkr, alerts, metadata, hkex]
for router_module in routers:
    if hasattr(router_module, 'router'):
        app.include_router(router_module.router)

# IBKR cookie sync middleware
@app.middleware("http")
async def ibkr_middleware(request: Request, call_next):
    cookies = request.cookies
    if any(k in cookies for k in ['JSESSIONID', 'x-sess-uuid', 'IB_SESSION']):
        ib_web_service.set_cookies(cookies)
    return await call_next(request)

@app.on_event("startup")
async def startup():
    logger.info("✅ JTCML Backend v4.2 started")

@app.get("/health")
def health():
    return {"status": "ok", "version": "4.2-compact", "endpoints": 130}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
