# Memory Log

---

## 2026-02-16

### Session Summary
Initial codebase ingestion from GitHub repository. Generated core documentation architecture. Made workspace structure error, corrected it.

### Completed
- [x] Cloned `jt-ai-trading-platform` repository
- [x] Scanned 60+ Python files, 8 frontend files
- [x] Generated `architecture.md` - Full system diagram and component breakdown
- [x] Generated `dependencies.md` - File-level dependency mapping
- [x] Generated `decisions.md` - ADR records for key architectural choices

### Mistakes & Corrections

**MISTAKE**: Merged `jt-ai-trading-platform` code files into root workspace (`/.openclaw/workspace/`)
- Incorrectly moved backend/, frontend/, db_setup/ to root
- Root workspace should only contain OpenClaw agent metadata (AGENTS.md, SOUL.md, USER.md, etc.)

**CORRECTION**: 
- Root workspace (`/.openclaw/workspace/`): OpenClaw metadata only
- Project workspace (`jt-ai-trading-platform/`): Trading platform code and docs
- Both workspaces have their own copies of identity files

**LESSON**: Never mix project code with root agent metadata. Projects live in subfolders.

**SECOND MISTAKE**: Pushed workspace structure to GitHub instead of clean project
- Pushed root workspace with nested `jt-ai-trading-platform/` folder
- Included OpenClaw metadata (AGENTS.md, SOUL.md, etc.) in GitHub repo
- Created messy duplicate structure

**CORRECTION**:
- Rebuilt clean git repo from `jt-ai-trading-platform/` contents only
- Removed all OpenClaw metadata from GitHub
- Force pushed clean structure to `main`
- GitHub now contains only project code, no agent metadata

**GITHUB PROTOCOL**:
| Location | Contents |
|----------|----------|
| GitHub Repository | Clean project files only (no OpenClaw metadata) |
| Workspace Root | OpenClaw metadata (AGENTS.md, SOUL.md, etc.) |
| Agent Workspace | `.openclaw/memory.md` (runtime state) |

**WORKSPACE SEPARATION PROTOCOL**:
| Layer | Location | Purpose |
|-------|----------|---------|
| Root Workspace | `/.openclaw/workspace/` | OpenClaw metadata (AGENTS.md, SOUL.md, USER.md, IDENTITY.md) |
| Agent Workspace | `/.openclaw/workspace/.openclaw/` | Agent memory (memory.md), workspace state |
| Project Workspace | `/.openclaw/workspace/<project>/` | Code, documentation, generated files |

**MEMORY FILE LOCATION**: Agent memory belongs in `/.openclaw/workspace/.openclaw/memory.md`, NOT root workspace.

### Key Findings

#### System Overview
- **Stack**: Python FastAPI + React + AWS RDS PostgreSQL
- **Broker**: Interactive Brokers (dual integration: socket + web)
- **AI**: Azure OpenAI via LangChain
- **Data**: yfinance (primary) + Alternative.me (sentiment)

#### Architecture Strengths
1. **4-tier data architecture**: Bronze → Silver → Gold → Consumption
2. **Multi-asset support**: Stocks, FX, Crypto, Commodities unified pipeline
3. **Execution modes**: SIMULATION → PAPER → LIVE graduation path
4. **FIFO PnL accounting**: Separate long/short queues per strategy

#### Identified Technical Debt
1. **Silent exception handling**: Multiple `try/except: pass` patterns
2. **Price source duality**: yfinance real-time + cached GlobalState inconsistency risk
3. **No test coverage**: Only `test_api.py`, no unit tests for core logic
4. **Scheduler coupling**: Strategy execution tightly coupled to data refresh

#### IBKR Assessment (for Jacky)
| Aspect | FX | Crypto |
|--------|-----|--------|
| Spreads | Competitive | Wide |
| Assets | All majors | 4 only (BTC, ETH, LTC, BCH) |
| Custody | N/A | **No withdrawal** (paper only) |
| Verdict | ✅ Good | ⚠️ Limited |

### Deployment Completed (2026-02-16)
- [x] SSL certificates moved to `jt-ai-trading-platform/certs/` (600 permissions, gitignored)
- [x] Cloudflare Origin CA configured in nginx
- [x] Nginx reverse proxy: HTTPS (443) → FastAPI (8000)
- [x] Frontend built and deployed (`dist/` served by nginx)
- [x] Environment variables configured (Azure OpenAI + Serper)
- [x] Backend running on port 8000 (localhost only)
- [x] Website live: https://trade.jtcml.com

#### Deployment Stack
| Component | Status | Details |
|-----------|--------|---------|
| Nginx | ✅ Active | Ports 80, 443 |
| FastAPI | ✅ Running | Port 8000 (localhost) |
| SSL | ✅ Valid | Cloudflare Origin CA |
| API | ✅ 200 OK | `/api/signals/1` responding |

#### Created Files
| File | Purpose |
|------|---------|
| `DEPLOYMENT.md` | Complete deployment guide |
| `backend/.env.template` | Environment variable template |
| `nginx.conf` | Nginx configuration |
| `backend/start.sh` | Backend startup script |

### Deployment Fixes (2026-02-16)

**ISSUE**: 500 Internal Server Error on website access

**Root Causes & Fixes**:

| Issue | Symptom | Root Cause | Fix |
|-------|---------|------------|-----|
| Permission denied | Nginx 500 error | Nginx (www-data) couldn't read frontend files | `sudo chown -R www-data:www-data frontend/dist/` |
| API 404 | `/api/*` returning 404 | `proxy_pass` was stripping `/api/` prefix | Changed `proxy_pass http://127.0.0.1:8000/;` to `proxy_pass http://127.0.0.1:8000/api/;` |
| Missing route | IBKR calls failing | `/v1/api/*` not routed to backend | Added separate location block for `/v1/api/` |

**Commands Applied**:
```bash
# Fix permissions
sudo chown -R www-data:www-data /home/ubuntu/.openclaw/workspace/jt-ai-trading-platform/frontend/dist/
sudo chmod -R 755 /home/ubuntu/.openclaw/workspace/jt-ai-trading-platform/frontend/dist/
sudo chmod 755 /home/ubuntu/ /home/ubuntu/.openclaw/ /home/ubuntu/.openclaw/workspace/

# Fix nginx config
proxy_pass http://127.0.0.1:8000/api/;  # Keep /api/ prefix
```

**Verification**:
```
✅ https://trade.jtcml.com/ → 200 OK (frontend)
✅ https://trade.jtcml.com/api/signals/1 → 200 OK (backend API)
```

### FX Data Investigation (2026-02-16)
**Jacky's Requirements**:
- Frequency: Higher than 1-minute (current yfinance limit)
- Pairs: Majors only
- Account: 100% FX exposure (dedicated)
- Start: Phase 1.1

**Investigation Complete**: `FX_DATA_INVESTIGATION.md`

**Primary Recommendation**: IBKR (Interactive Brokers)
- **Frequency**: Tick-by-tick (every price change)
- **Latency**: ~50-200ms
- **Cost**: FREE with IBKR account (need ~$15/month FX market data sub for live)
- **Pros**: Same venue for data + execution (no slippage), already integrated
- **Cons**: Need IB Gateway running, requires live market data subscription

**Backup Options**:
| Source | Frequency | Cost | Use Case |
|--------|-----------|------|----------|
| yfinance | 1-minute | Free | Current (fallback only) |
| Alpha Vantage | 1-minute (free) / tick ($600/mo) | Free/Paid | Too expensive for ticks |
| Polygon.io | Real-time | $49/mo | Good redundancy |
| OANDA | Tick-by-tick | Free with account | Backup broker |

**Phase 1.1 Implementation**:
1. IBKR FX streaming service (tick data)
2. Tick aggregation (1s, 5s, 1m bars)
3. WebSocket broadcast to frontend
4. Frontend FX live grid
5. Spread monitoring & alerts

**Major Pairs Priority**:
1. 🔴 EURUSD, USDJPY, GBPUSD (Phase 1.1)
2. 🟡 AUDUSD, USDCAD, USDCHF (Phase 1.2)

**Decision Needed**: Confirm IBKR as primary source (requires $15/mo FX market data sub for live data)

### Next Steps (Pending Jacky's Direction)
1. ✅ SSL certificate setup for `trade.jtcml.com` - COMPLETED
2. ✅ 500 Error Fix - COMPLETED
3. ✅ GitHub Backup - COMPLETED
4. ✅ GitHub Cleanup (consolidated to main, deleted all other branches) - COMPLETED
5. 🔄 **FX Enhancement** - Jacky to select phase (1, 2, or 3)

### GitHub Backup (2026-02-16)

**Repository:** https://github.com/CurryDigital/jt-ai-trading-platform

**Branch Structure:**
| Branch | Commit | Status |
|--------|--------|--------|
| `main` | 197463b | ✅ Clean project structure |

**Structure Correction:**

**FIRST ATTEMPT (WRONG):**
- Pushed workspace root with nested `jt-ai-trading-platform/` folder
- OpenClaw metadata (AGENTS.md, SOUL.md, etc.) included at root
- Duplicate metadata inside nested folder
- ❌ Messy structure

**CORRECTED:**
- Clean project files at repository root
- Removed OpenClaw metadata (AGENTS.md, SOUL.md, USER.md, etc.)
- Removed nested folder structure
- Removed `certs/` and runtime files
- ✅ Clean structure

**GitHub Root Contents:**
```
backend/           # FastAPI application
frontend/          # React application
db_setup/          # Database DDL scripts
docs/              # Documentation
architecture.md    # System architecture
decisions.md       # ADRs
dependencies.md    # Dependency map
DEPLOYMENT.md      # Deployment guide
nginx.conf         # Nginx configuration
.gitignore         # Git exclusions
requirements.txt   # Python deps
run_pipeline.py    # Pipeline runner
```

**Excluded from GitHub:**
- ❌ OpenClaw metadata (AGENTS.md, SOUL.md, USER.md, BOOTSTRAP.md, etc.)
- ❌ `certs/` - SSL private keys
- ❌ `backend/.env` - Environment secrets
- ❌ `.openclaw/` - Agent workspace

**Clone Command:**
```bash
git clone https://github.com/CurryDigital/jt-ai-trading-platform.git
```

---

## 2026-02-16 (Continued)

### FX Phase 1.1 Implementation COMPLETED
**Status**: Core infrastructure COMPLETED

**Implemented**:
| Component | File | Status |
|-----------|------|--------|
| Database Schema | `db_setup/FX_STREAMING_DDL.sql` | ✅ Created tables |
| FX Streaming Service | `backend/app/services/fx_streaming_service.py` | ✅ 142 lines |
| Tick Aggregation | `FXBarAggregator` class | ✅ 5s bars |
| Spread Alerts | Auto-alert on wide spreads | ✅ Configured |
| ORM Models | `backend/app/db/session.py` | ✅ FXTicks, FXBars5S |
| API Endpoints | `backend/app/main.py` | ✅ 3 new endpoints |
| Startup Integration | Auto-start on boot | ✅ Added |

**API Endpoints**:
```
GET /api/fx/streaming/status    - Check if connected to IBKR
GET /api/fx/bars/latest         - Get latest 5s bars (EURUSD, USDJPY, GBPUSD)
GET /api/fx/streaming/alerts    - Get spread alerts
```

**Pairs**: EURUSD, USDJPY, GBPUSD (5-second bars)
**Spread Thresholds**: 3 bps (EURUSD/USDJPY), 5 bps (GBPUSD)
**Backup**: yfinance 1-minute (fallback not yet implemented)

**Testing**:
```bash
# After backend restart:
curl https://trade.jtcml.com/api/fx/streaming/status
curl https://trade.jtcml.com/api/fx/bars/latest
```

**Note**: Requires IB Gateway running. Without it, service will retry connection every 30s.

**Next Steps**:
- Restart backend to test FX streaming
- WebSocket (if frontend needs real-time push)
- Frontend FX live grid component
- yfinance fallback on IBKR disconnect


### Path 2: TWS API Migration COMPLETED (2026-02-16)
**Goal**: Migrate from Web API to TWS API for automated FX trading

**Architecture Change**:
- BEFORE (Hybrid): FX Data via TWS, Execution via Web API (session expires)
- AFTER (Path 2): FX Data + Execution via TWS API (persistent socket)
- Web API now: Emergency fallback only

**Code Changes**:
| File | Change |
|------|--------|
| trading_service.py | Rewritten for TWS primary, Web fallback |
| strategy_manager.py | FX execution uses ib_quant_service first |
| main.py | New TWS/Web status endpoints |
| DEPLOYMENT.md | IB Gateway installation guide |
| IB_GATEWAY_SETUP.md | Complete setup documentation |

**New API Endpoints**:
- GET /api/ib/tws/status - Check TWS API connection
- POST /api/ib/tws/connect - Manual reconnect  
- GET /api/ib/web/status - Check Web API fallback

**Execution Priority**:
1. TWS API (ib_insync socket) - Primary
2. Web API (cookie-based) - Emergency fallback
3. Simulation - Last resort

**Action Required by Jacky**:
1. SSH to EC2: ssh ubuntu@13.214.84.37
2. Install IB Gateway (see IB_GATEWAY_SETUP.md)
3. Login once with IBKR credentials
4. Enable API in settings
5. Start systemd service

**Cost**:
- IB Gateway: FREE
- FX Market Data: ~$15/month (optional)

---

*Last Updated: 2026-02-16 03:25 UTC*
