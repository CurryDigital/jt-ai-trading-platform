# JT AI Trading Platform - API Documentation

## Base URL
- Local: `http://127.0.0.1:8000`
- Production: `https://trade.jtcml.com`

---

## 📊 Strategy Management APIs

### Get Strategy Templates
```
GET /api/strategies/templates
GET /api/strategies/templates/{asset_class}  # FX, STOCK, CRYPTO
```
**Response:**
```json
{
  "MR_FX": {
    "id": "MR_FX",
    "name": "Mean Reversion FX",
    "asset_class": "FX",
    "backtest_metrics": {
      "1d_accuracy": "68%",
      "30d_return": "+12.4%",
      "sharpe_ratio": 1.8,
      "max_drawdown": "-3.2%"
    }
  }
}
```

### Create Strategy
```
POST /api/strategies/create
```
**Body:**
```json
{
  "ticker": "AAPL",
  "template_id": "MOMENTUM_STOCK",
  "capital": 10000,
  "execution_mode": "SIMULATION"
}
```

### Get Strategies by Asset Class
```
GET /api/strategies/by-asset/{asset_class}  # FX, STOCK, CRYPTO
```

### Get Strategy Detail
```
GET /api/strategies/{strategy_id}/detail
```

### Get Daily P&L
```
GET /api/strategies/{strategy_id}/daily-pnl?start_date=2024-01-01&end_date=2024-12-31
```

### Get Backtest Summary
```
GET /api/strategies/{strategy_id}/backtest-summary
```

---

## 🔬 Backtesting APIs

### Run Backtest
```
POST /api/strategies/{strategy_id}/backtest
```
**Body:**
```json
{
  "start_date": "2024-01-01",
  "end_date": "2024-12-31",
  "initial_capital": 10000,
  "commission_rate": 0.001
}
```
**Response:**
```json
{
  "status": "queued",
  "strategy_id": 22,
  "message": "Backtest started in background"
}
```

### Get Backtest History
```
GET /api/strategies/{strategy_id}/backtest-history
```
**Response:**
```json
{
  "strategy_id": 22,
  "backtest_count": 2,
  "backtests": [
    {
      "id": 1,
      "run_date": "2026-02-17T16:51:10",
      "start_date": "2024-06-01",
      "end_date": "2024-07-01",
      "total_return_pct": 0.0,
      "sharpe_ratio": 0.0,
      "max_drawdown_pct": 0.0,
      "win_rate": 0.0,
      "total_trades": 0
    }
  ]
}
```

### Compare Backtest vs Live
```
GET /api/strategies/{strategy_id}/backtest-vs-live
```

### Get All Backtests
```
GET /api/backtests/all?limit=50
```

---

## 📈 Data Feed APIs

### FX Pairs
```
GET /api/fx/pairs
```

### FX Latest Bars
```
GET /api/fx/bars/latest?ticker=EURUSD&limit=20
```

### Stocks
```
GET /api/stocks/all
GET /api/stocks/{ticker}  # e.g., /api/stocks/NVDA
```

### Crypto
```
GET /api/crypto/pairs
GET /api/crypto/all
```

---

## 💼 Portfolio Risk APIs

### Risk Summary
```
GET /api/portfolio/risk-summary
```
**Response:**
```json
{
  "summary": {
    "total_strategies": 7,
    "open_positions": 0,
    "total_allocated": 70000,
    "total_pnl": 0,
    "total_return_pct": 0.0,
    "total_trades": 0,
    "max_drawdown_pct": 0.0,
    "risk_status": "NORMAL"
  },
  "asset_exposure": {
    "FX": {"allocated": 70000, "pnl": 0, "count": 7, "allocation_pct": 100.0},
    "STOCK": {"allocated": 0, "pnl": 0, "count": 0, "allocation_pct": 0.0},
    "CRYPTO": {"allocated": 0, "pnl": 0, "count": 0, "allocation_pct": 0.0}
  },
  "strategies": [...]
}
```

### Correlation Matrix
```
GET /api/portfolio/correlations
```

### Value at Risk (VaR)
```
GET /api/portfolio/var?confidence=0.95
```

### Concentration Risk
```
GET /api/portfolio/concentration
```

### Risk Alerts
```
GET /api/portfolio/alerts
```

### Full Dashboard
```
GET /api/portfolio/dashboard
```

---

## 💰 Execution & Positions

### Execution Status
```
GET /api/execution/status
```
**Response:**
```json
{
  "tws_api": {
    "connected": true,
    "host": "52.74.14.181",
    "port": 4001
  },
  "web_api": {
    "authenticated": false
  },
  "ready_for_live": true
}
```

### Get Positions
```
GET /api/positions
GET /api/positions/{ticker}
```

### Execute Trade
```
POST /api/positions/execute
```
**Body:**
```json
{
  "ticker": "AAPL",
  "side": "BUY",
  "quantity": 100,
  "order_type": "MKT"
}
```

---

## 🔧 System APIs

### IBKR Status
```
GET /api/ib/tws/status
GET /api/velocity/ib/status
```

### Refresh Data
```
POST /api/maintenance/refresh/stocks
POST /api/maintenance/refresh/fx
POST /api/maintenance/refresh/crypto
POST /api/maintenance/refresh/commodities
```

---

## Strategy Templates Reference

### FX Strategies (3)
| Template | Type | Win Rate | Sharpe | Max DD |
|----------|------|----------|--------|--------|
| MR_FX | Mean Reversion | 68% | 1.8 | -3.2% |
| TREND_FX | Trend Following | 55% | 1.45 | -6.1% |
| CARRY_FX | Carry Trade | 62% | 1.65 | -4.5% |

### Stock Strategies (4)
| Template | Type | Win Rate | Sharpe | Max DD |
|----------|------|----------|--------|--------|
| MOMENTUM_STOCK | Price Momentum | 54% | 1.35 | -8.3% |
| VALUE_STOCK | Value Investing | 58% | 1.42 | -6.9% |
| SECTOR_ROTATION | Sector Rotation | 61% | 1.55 | -5.2% |
| EARNINGS_GAP | Earnings Play | 56% | 1.25 | -12.4% |

### Crypto Strategies (3)
| Template | Type | Win Rate | Sharpe | Max DD |
|----------|------|----------|--------|--------|
| BREAKOUT_CRYPTO | Volatility Breakout | 48% | 1.15 | -18.2% |
| GRID_CRYPTO | Grid Trading | 72% | 1.45 | -14.5% |
| FUNDING_RATE | Funding Arb | 85% | 2.1 | -2.1% |

---

## Execution Modes
- `SIMULATION` - Paper trading with simulated fills
- `PAPER` - Paper trading via IBKR
- `LIVE` - Live trading via IBKR

---

*Last Updated: 2026-02-17*