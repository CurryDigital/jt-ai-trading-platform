# JT AI Trading Platform - Memory Log

**Last Updated:** 2026-02-16  
**Session:** IBKR Gateway Connection Fix & Platform Revamp

---

## Key Infrastructure Changes (2026-02-16)

### 1. IBKR Gateway Setup (COMPLETED)

**Gateway EC2:**
- **IP:** 52.74.14.181 (Singapore)
- **Instance:** t3.small (x86_64)
- **Docker:** IB Gateway running in container
- **Status:** ✅ Connected to backend

**Security Groups:**
```
Inbound:
- SSH (22): Your IP only
- API Ports (4001-4002): ARM instance SG only
- VNC (5900): Your IP only (temporary setup)
Outbound:
- IBKR IPs: 208.135.165-167.0/24, 69.22.132.0/24
```

**Fixes Applied:**
- Threaded IBKR service to avoid asyncio loop conflicts
- Keep-alive script for persistent connection
- Read-Only API disabled for trading

---

### 2. Backend Stability Fixes (COMPLETED)

**Problems Fixed:**
1. **Prophet Forecasting CPU Overload**
   - Disabled Prophet ML training (was causing 100% CPU crashes)
   - Switched to lightweight momentum-based predictions
   - Added caching to prevent redundant calculations

2. **FX Streaming Service Crashes**
   - Disabled async FX streaming (event loop conflicts)
   - Using Yahoo Finance as primary data source
   - IBKR as optional execution layer

3. **Process Monitoring**
   - Created `/tmp/keep_alive.sh` auto-restart script
   - Runs every 30 seconds, restarts backend if crashed
   - Maintains IBKR connection persistence

---

### 3. Frontend v3.0 Revamp (COMPLETED)

**New Tab Structure (6 tabs vs 10):**
| Tab | Purpose | Key Features |
|-----|---------|--------------|
| **📊 Dashboard** | Executive overview | P&L cards, top signals, market mood, risk alerts |
| **💼 Portfolio** | Position management | Manual entry form, quant-style table, real metrics |
| **🔬 Research** | AI signals | Confidence meters (backtest WR + AI), realistic estimates |
| **📈 Markets** | Unified view | Asset class tabs (FX/Crypto/Commod/Stocks) |
| **🎯 Strategies** | Strategy lab | Paper/live toggle, execution mode |
| **⚙️ Settings** | Configuration | IBKR diagnostics, sync schedules |

**Key Improvements:**
- Realistic monthly return caps (8-15% max)
- Win Rate + AI Confidence displayed separately
- Momentum metrics (1D, 5D, 1M, YTD)
- Manual position entry (ticker, qty, avg price)
- No more fake hardcoded metrics

---

### 4. Data Pipeline (Yahoo Finance Primary)

**Current Sources:**
- **Yahoo Finance:** Stocks, FX, Crypto, Commodities (delayed ~15-20min)
- **IBKR Gateway:** Execution only (when connected)
- **RDS PostgreSQL:** Position storage, signal history

**Scheduler Intervals:**
```
- Indices: 5min
- Stocks: 5min  
- FX: 1min
- Commodities: 5min
- Crypto: 5min
- HFT: 5min
```

---

### 5. Critical Configuration

**Backend Environment Variables:**
```bash
AZURE_OPENAI_API_KEY="9Hjt8RDYsjBflHI9C0qSJRQYSqfb04qgNyjm6JA42AnnV4BKb7qVJQQJ99BFACqBBLyXJ3w3AAABACOGWJK7"
AZURE_OPENAI_ENDPOINT="https://databricksllmpoc.openai.azure.com/"
AZURE_OPENAI_DEPLOYMENT="gpt-4.1-nano"
AZURE_OPENAI_API_VERSION="2025-03-01-preview"
SERPER_API_KEY="fbccff7e2b07f4c417387bafadd141b97f1583be"
```

**Keep-Alive Script Location:**
```bash
/tmp/keep_alive.sh  # Running as PID 37131
```

---

### 6. Known Issues & Limitations

**IBKR Connection:**
- ✅ Network path working
- ✅ Backend connects successfully
- ⚠️ Historical Data Farm inactive (paper trading limitation)
- ⚠️ Market data subscriptions needed for live prices

**Backend Stability:**
- ⚠️ Scheduler still CPU-intensive during Prophet runs (disabled)
- ⚠️ Requires keep-alive script to stay running
- ✅ Auto-restart handles crashes

**Missing Features (Next Phase):**
- Paper trading execution engine
- Real-time WebSocket feeds
- Mobile alerts/notifications
- Proper backtesting framework

---

### 7. Next Steps (Prioritized)

1. **Paper Trading Engine** - Execute strategy signals as simulated orders
2. **Real-time Data** - Subscribe to Polygon.io or similar for live prices
3. **Position Management** - Delete/edit manual positions, stop losses
4. **Strategy Optimization** - Grid search, parameter tuning

---

### 8. Files Modified Today

**Backend:**
- `/app/services/ib_service.py` - Threaded IBKR connection
- `/app/core_logic/analysis/time_series/prophet_forecast.py` - Disabled Prophet
- `/app/main.py` - Disabled FX streaming

**Frontend:**
- `/src/App.jsx` - Complete v3.0 revamp
- `/src/components/IbkrGatewayTester.jsx` - Diagnostics panel

**Documentation:**
- `/docs/IBKR_GATEWAY_SETUP.md` - Full setup guide
- `MEMORY.md` - This file

---

### 9. Cost Estimate (Monthly)

| Component | Cost |
|-----------|------|
| t3.small Gateway (on-demand) | ~$15 |
| RDS t3.micro | ~$13 |
| Data transfer | ~$5 |
| **Total** | **~$33/month** |

---

## Session Notes

**2026-02-16 - Jacky Session:**
- Successfully deployed IBKR Gateway on separate EC2
- Fixed asyncio event loop conflicts with threaded service
- Frontend revamp to quant-style professional UI
- Manual position entry implemented
- Keep-alive monitoring in place
- Platform stable on Yahoo Finance data

**Key Insight:**
IBKR connection works but requires persistent process monitoring. Yahoo Finance sufficient for signals; IBKR for execution only.

**Next Priority:**
Implement paper trading execution loop (strategy signal → IBKR order → fill tracking).

---

## 10. OpenClaw Agent & Telegram Group Setup Pattern (2026-02-16)

### Adding New Telegram Groups to Agents

**Symptom:** Bot says "this group is not allowed" or doesn't respond to @mentions

**Root Cause:** New Telegram groups must be explicitly added to `channels.telegram.groups` and routed via `bindings`

**Quick Fix Process:**
1. Get chat ID by polling `getUpdates` or using @getidsbot
2. Add to `openclaw.json`:
```json
"channels": {
  "telegram": {
    "groups": {
      "<CHAT_ID>": {
        "groupPolicy": "open",
        "requireMention": false
      }
    }
  }
},
"bindings": [
  {
    "match": { "channel": "telegram", "peer": { "kind": "group", "id": "<CHAT_ID>" } },
    "agentId": "<AGENT_ID>"
  }
]
```
3. Restart gateway: `openclaw gateway restart`

**Current Telegram Groups:**
| Group | Chat ID | Agent |
|-------|---------|-------|
| JTCML Trading | `-5001038390` | `jtcml_trading` |
| JTCML Algo Researcher | `-5175536290` | `trade_algo_researcher` |
| Tang Inventory | `-5167679762` | `tang_inventory` |

**Prerequisites:**
- Bot must be in group (check Group Info → Members)
- Bot privacy mode OFF in @BotFather (`/setprivacy` → Disable)
- If privacy was just changed, remove and re-add bot to group
