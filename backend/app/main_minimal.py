"""
JTCML Trading Platform — FastAPI Backend (Minimal - No DB)
==========================================================
Standalone version without database dependencies.
"""
import datetime
import json
import time
from fastapi import FastAPI, Request, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# CORS - allow all for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mock data store
mock_data = {
    "execution_mode": "SIMULATION",
    "strategies": [],
    "positions": [],
    "signals": [],
    "fx_pairs": [],
    "crypto_pairs": [],
    "commodities": [],
    "stocks": [],
    "trades": [],
    "performance": {
        "total_return": 0,
        "sharpe": 0,
        "max_drawdown": 0,
        "win_rate": 0
    }
}

# Health check
@app.get("/")
def root():
    return {"status": "JTCML Trading Platform API (Minimal Mode)", "version": "1.0.0"}

@app.get("/health")
def health():
    return {"status": "healthy", "mode": "minimal", "timestamp": datetime.datetime.now().isoformat()}

# Execution mode
@app.get("/api/execution/global-mode")
def get_global_mode():
    return {
        "execution_mode": mock_data["execution_mode"],
        "available_modes": ["SIMULATION", "PAPER_TRADING", "LIVE_TRADING"],
        "risk_level": "ZERO",
        "simulation_capital": 100000,
        "simulation_used": 0,
        "simulation_available": 100000,
        "simulation_positions": 0
    }

@app.post("/api/execution/global-mode")
def set_global_mode(payload: dict):
    mode = payload.get("execution_mode", "SIMULATION")
    if mode in ["SIMULATION", "PAPER_TRADING", "LIVE_TRADING"]:
        mock_data["execution_mode"] = mode
    return get_global_mode()

# Signals
@app.get("/api/signals/1")
def get_signals():
    return [
        {
            "ticker": "AAPL",
            "market": "US",
            "horizon": "1W",
            "price": 175.50,
            "change": 1.25,
            "action": "BUY",
            "total_conf": 75.5,
            "trad_conf": 75.5,
            "swarm_conf": 72.0,
            "win_rate": 65.0,
            "tags": ["MOMENTUM"],
            "timestamp": datetime.datetime.now().isoformat()
        },
        {
            "ticker": "MSFT",
            "market": "US",
            "horizon": "1W",
            "price": 420.25,
            "change": 0.85,
            "action": "HOLD",
            "total_conf": 60.0,
            "trad_conf": 60.0,
            "swarm_conf": 58.0,
            "win_rate": 55.0,
            "tags": ["VALUE"],
            "timestamp": datetime.datetime.now().isoformat()
        }
    ]

# FX Pairs
@app.get("/api/fx/pairs")
def get_fx_pairs():
    return [
        {"ticker": "EURUSD", "price": 1.0850, "change": 0.15, "trend": "NEUTRAL", "action": "HOLD", "confidence": 65.0, "rsi": 52.0},
        {"ticker": "USDJPY", "price": 148.50, "change": -0.25, "trend": "BEARISH", "action": "SELL", "confidence": 70.0, "rsi": 45.0},
        {"ticker": "GBPUSD", "price": 1.2650, "change": 0.35, "trend": "BULLISH", "action": "BUY", "confidence": 72.0, "rsi": 58.0}
    ]

# Crypto Pairs
@app.get("/api/crypto/pairs")
def get_crypto_pairs():
    return [
        {"ticker": "BTC-USD", "asset": "Bitcoin", "action": "HOLD", "total_confidence": 60.0, "price": 69750.0, "change": 2.5},
        {"ticker": "ETH-USD", "asset": "Ethereum", "action": "BUY", "total_confidence": 68.0, "price": 3850.0, "change": 3.2},
        {"ticker": "SOL-USD", "asset": "Solana", "action": "HOLD", "total_confidence": 55.0, "price": 108.0, "change": -1.5}
    ]

# Commodities
@app.get("/api/commodities/all")
def get_commodities():
    return [
        {"ticker": "GC=F", "asset": "Gold", "action": "BUY", "total_conf": 75.0, "price": 2050.0, "change": 0.5},
        {"ticker": "CL=F", "asset": "Crude Oil", "action": "HOLD", "total_conf": 50.0, "price": 72.50, "change": -0.8}
    ]

# Stocks
@app.get("/api/stocks/all")
def get_all_stocks():
    return [
        {"ticker": "AAPL", "name": "Apple Inc.", "sector": "Technology", "market": "US", "price": 175.50, "change": 1.25, "trend": "BULLISH", "rsi": 55.0, "score": 75.0, "action": "BUY", "confidence": 75.5},
        {"ticker": "MSFT", "name": "Microsoft", "sector": "Technology", "market": "US", "price": 420.25, "change": 0.85, "trend": "BULLISH", "rsi": 58.0, "score": 70.0, "action": "HOLD", "confidence": 60.0},
        {"ticker": "0700.HK", "name": "Tencent", "sector": "Technology", "market": "HK", "price": 285.0, "change": -0.5, "trend": "NEUTRAL", "rsi": 50.0, "score": 55.0, "action": "HOLD", "confidence": 50.0}
    ]

# Portfolio
@app.get("/api/portfolio/positions")
def get_portfolio_positions():
    return {
        "positions": [],
        "total_positions": 0,
        "total_value": 0,
        "total_pnl": 0,
        "active_positions": 0
    }

# Paper Strategies
@app.get("/api/paper-strategies")
def get_paper_strategies():
    return {
        "strategies": [],
        "count": 0,
        "execution_mode": mock_data["execution_mode"],
        "message": "No positions deployed yet"
    }

# Performance
@app.get("/api/performance/strategy")
def get_strategy_performance():
    return {
        "strategies": [],
        "monthly_returns": [],
        "summary": {
            "total_return": 0,
            "sharpe": 0,
            "max_drawdown": 0,
            "win_rate": 0
        },
        "execution_mode": mock_data["execution_mode"]
    }

@app.get("/api/performance/daily-pnl")
def get_daily_pnl(days: int = 7):
    return {
        "daily": [],
        "summary": {
            "total_pnl": 0,
            "avg_daily_pnl": 0,
            "message": "No positions recorded yet"
        }
    }

# Macro Pulse
@app.get("/api/macro/pulse")
def get_macro_pulse():
    return {
        "indices": {
            "US": {"value": 4500, "change": 0.5, "label": "S&P 500", "rationale": "Market trend: BULLISH"},
            "HK": {"value": 16500, "change": -0.2, "label": "Hang Seng", "rationale": "Market trend: NEUTRAL"}
        },
        "system_risk": "LOW",
        "shock_text": "Markets operating normally"
    }

# Velocity
@app.get("/api/velocity/trades")
def get_velocity_trades():
    return []

@app.get("/api/velocity/summary")
def get_velocity_summary():
    return {
        "total_trades": 0,
        "portfolio_value": 0,
        "total_pnl": 0,
        "win_rate": 0,
        "sharpe_ratio": 0,
        "active_strategies": 0,
        "status": "active"
    }

@app.get("/api/velocity/ib/status")
def get_ib_status():
    return {
        "status": "Disconnected",
        "socket": "Offline",
        "web": "Unauthorized"
    }

# Inventory
@app.get("/api/inventory/evaluate")
def get_inventory_evaluate():
    return {
        "positions": [],
        "active_positions": 0,
        "inventory_value": 0
    }

# Market Data
@app.get("/api/market-data")
def get_market_data(tickers: str = ""):
    if not tickers:
        return {"success": True, "data": [], "ibkr_connected": False}
    
    ticker_list = tickers.split(",")
    results = []
    for ticker in ticker_list:
        ticker = ticker.strip().upper()
        results.append({
            "ticker": ticker,
            "price": 100.0,
            "change": 0.0,
            "changePercent": 0.0,
            "volume": 1000000,
            "timestamp": datetime.datetime.now().isoformat(),
            "source": "mock"
        })
    
    return {
        "success": True,
        "data": results,
        "count": len(results),
        "ibkr_connected": False
    }

# Stock Detail
@app.get("/api/stocks/{ticker}")
def get_stock_detail(ticker: str, timeframe: str = "ytd"):
    return {
        "ticker": ticker.upper(),
        "market": "US",
        "name": f"{ticker.upper()} Inc.",
        "price": 100.0,
        "daily_change": 0.5,
        "changeYTD": 5.0,
        "chart_data": [],
        "indicators": {
            "rsi": 50.0,
            "rsi_signal": "NEUTRAL",
            "sma_signal": "NEUTRAL"
        },
        "timestamp": datetime.datetime.now().isoformat()
    }

# Settings
@app.get("/api/settings/data-sources")
def get_data_sources():
    return {
        "ibkr_connected": False,
        "data_sources": [
            {"category": "Market Data", "data_type": "Stock Prices", "primary_source": "Yahoo Finance", "status": "Active"}
        ],
        "summary": {"total_feeds": 1, "yahoo_primary": 1}
    }

# Metadata
@app.get("/api/metadata/formulas")
def get_formula_metadata():
    return []

@app.get("/api/metadata/thresholds")
def get_strategy_thresholds():
    return []

@app.get("/api/metadata/sync_schedules")
def get_sync_schedules():
    return []

@app.get("/api/metadata/strategy_configs")
def get_strategy_configs():
    return []

# Maintenance
@app.post("/api/maintenance/refresh/{component}")
def trigger_refresh(component: str):
    return {"status": f"Mock refresh triggered for {component}"}

@app.get("/api/maintenance/status/{component}")
def get_maintenance_status(component: str):
    return {"status": "Idle"}

# Strategy templates
@app.get("/api/quant/templates")
def get_quant_templates():
    return []

@app.get("/api/quant/strategies")
def get_quant_strategies():
    return []

@app.get("/api/quant/performance/matrix")
def get_performance_matrix():
    return {}

# Strategies
@app.get("/api/strategies/templates")
def get_strategy_templates():
    return [
        {"id": "MOMENTUM", "name": "Momentum Strategy", "asset_class": "STOCK"},
        {"id": "VALUE", "name": "Value Strategy", "asset_class": "STOCK"}
    ]

@app.get("/api/strategies/researcher")
def get_researcher_strategies():
    return {"strategies": [], "count": 0}

@app.get("/api/strategies/stats")
def get_strategy_stats():
    return {"success": True, "stats": {}, "count": 0}

# Alerts
@app.get("/api/alerts/status")
def get_alert_status():
    return {"enabled": False, "message": "Telegram not configured"}

# HFT
@app.get("/api/hft/matrix")
def get_hft_matrix():
    return []

# Market endpoints
@app.get("/api/market/indices")
def get_market_indices():
    return {
        "data": [
            {"symbol": "^GSPC", "name": "S&P 500", "price": 4500, "change": 10, "change_percent": 0.22},
            {"symbol": "^IXIC", "name": "Nasdaq", "price": 14000, "change": 50, "change_percent": 0.35}
        ]
    }

@app.get("/api/market/movers")
def get_market_movers():
    return {"gainers": [], "losers": []}

@app.get("/api/market/sectors")
def get_market_sectors():
    return {"data": []}

@app.get("/api/market/global")
def get_global_markets():
    return {"data": []}

@app.get("/api/market/breadth")
def get_market_breadth():
    return {"advancing": 0, "declining": 0, "unchanged": 0}

@app.get("/api/market/sentiment")
def get_market_sentiment():
    return {"fearGreed": 50, "vix": 15.0}

@app.get("/api/market/outlook")
def get_market_outlook():
    return {"market_mood": "Stable", "swarm_conclusion": "Neutral", "recommendations": []}

# Positions
@app.get("/api/positions")
def get_open_positions():
    return {"positions": [], "summary": {"total_positions": 0, "total_unrealized_pnl": 0}}

@app.post("/api/positions/{position_id}/close")
def close_position(position_id: str, payload: dict = None):
    return {"status": "success", "message": "Position closed (mock)"}

# IBKR endpoints
@app.get("/api/execution/status")
def get_execution_status():
    return {
        "tws_api": {"connected": False, "host": "127.0.0.1", "port": 4002},
        "web_api": {"authenticated": False},
        "ready_for_live": False
    }

@app.get("/api/ib/tws/status")
def get_tws_status():
    return {"is_connected": False, "host": "127.0.0.1", "port": 4002}

@app.get("/api/ib/web/status")
def get_web_status():
    return {"is_authenticated": False}

# Simulation reset
@app.post("/api/simulation/reset")
def reset_simulation():
    mock_data["positions"] = []
    mock_data["trades"] = []
    return {"success": True, "message": "Simulation reset"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
