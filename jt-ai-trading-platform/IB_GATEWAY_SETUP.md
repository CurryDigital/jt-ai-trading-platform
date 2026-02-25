# IB Gateway Production Setup - Path 2 Implementation

**Date**: 2026-02-16  
**Goal**: Migrate from Web API to TWS API for 24/7 automated FX trading  
**Status**: IN PROGRESS

---

## Overview

**Current State**: Hybrid (Web API for trading, TWS for data)  
**Target State**: TWS API primary, Web API emergency-only  
**Benefits**: No session expiry, persistent connection, true automation

---

## Phase 1: IB Gateway Installation (Server-Side)

### 1.1 Download IB Gateway

```bash
# SSH to your EC2 instance (13.214.84.37)
ssh ubuntu@13.214.84.37

# Download IB Gateway (Linux x64)
cd /tmp
wget https://download2.interactivebrokers.com/installers/ibgateway/stable-standalone/ibgateway-stable-standalone-linux-x64.sh

# Make executable
chmod +x ibgateway-stable-standalone-linux-x64.sh

# Run installer
./ibgateway-stable-standalone-linux-x64.sh
# Follow prompts, install to ~/IBGateway
```

### 1.2 First-Time Configuration (Interactive)

```bash
# Start IBGateway manually for initial setup
cd ~/Jts/ibgateway/10xx  # version number
./ibgateway

# Login with your IBKR credentials
# Check "Remember me for 30 days"
# Enable API:
#   Edit → Configure → API → Settings
#   ☑️ "Enable ActiveX and Socket Clients"
#   Socket port: 4001
#   ☑️ "Allow connections from localhost only" (security)
#   Master Client ID: 0
#   ☑️ "Create API message log"
#   ☑️ "Allow connections from 127.0.0.1"
```

### 1.3 Create systemd Service

```bash
sudo tee /etc/systemd/system/ibgateway.service > /dev/null <<EOF
[Unit]
Description=Interactive Brokers Gateway
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/Jts/ibgateway/10xx
Environment="DISPLAY=:0"
Environment="TZ=Asia/Hong_Kong"
ExecStart=/home/ubuntu/Jts/ibgateway/10xx/ibgateway
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable ibgateway
sudo systemctl start ibgateway
```

### 1.4 Auto-Login (Headless)

For true headless operation, use `IBC` (IB Controller):

```bash
# Download IBC
cd /opt
sudo git clone https://github.com/IbcAlpha/IBC.git
sudo chown -R ubuntu:ubuntu IBC

# Configure IBC
cd IBC
cp config.ini.template config.ini
# Edit config.ini with your credentials
```

---

## Phase 2: Code Migration (Trading Service)

### 2.1 Update Trading Execution

**File**: `backend/app/services/trading_service.py`

**Current (Web API)**:
```python
result = ib_web_service.execute_order(account_id, ticker, action, qty)
```

**New (TWS API)**:
```python
result = await ib_quant_service.execute_quant_trade(pair, action, qty)
```

### 2.2 Update Strategy Manager

**File**: `backend/app/services/strategy_manager.py`

**Change execution path**:
```python
# Line ~400 in run_tick()
if ib_quant_service.is_connected and mode != "SIMULATION":
    result = await ib_quant_service.execute_quant_trade(pair, side, qty)
else:
    # Fallback to web API or simulation
```

### 2.3 Connection Health Monitoring

**New File**: `backend/app/services/ib_connection_monitor.py`

```python
"""
Monitors IB Gateway connection health
Switches between TWS API and Web API as needed
"""
```

---

## Phase 3: Reconnection Logic

### 3.1 Enhanced Reconnection

**Update**: `backend/app/services/ib_service.py`

```python
async def ensure_connection(self, max_retries=5):
    """Ensure connection with exponential backoff"""
    for attempt in range(max_retries):
        if self.is_connected:
            return True
        result = await self.connect()
        if result['status'] == 'Connected':
            return True
        wait = min(30, 2 ** attempt)  # 2, 4, 8, 16, 30s
        await asyncio.sleep(wait)
    return False
```

### 3.2 Circuit Breaker

**New**: Auto-disable trading if connection fails for >5 minutes

---

## Phase 4: API Updates

### 4.1 New Endpoints

```python
# Check TWS API connection status
GET /api/ib/tws/status

# Force reconnect TWS
POST /api/ib/tws/reconnect

# Switch execution mode
POST /api/ib/execution-mode
{
  "mode": "TWS_API" | "WEB_API" | "SIMULATION"
}
```

### 4.2 Health Check Integration

Update existing endpoints to report which API is active

---

## Implementation Tasks

| # | Task | File | Status |
|---|------|------|--------|
| 2.1 | Update `trading_service.py` to use TWS | `backend/app/services/trading_service.py` | ⏳ |
| 2.2 | Update `strategy_manager.py` execution | `backend/app/services/strategy_manager.py` | ⏳ |
| 2.3 | Create connection monitor | `backend/app/services/ib_connection_monitor.py` | ⏳ |
| 2.4 | Enhance reconnection logic | `backend/app/services/ib_service.py` | ⏳ |
| 2.5 | Add API endpoints | `backend/app/main.py` | ⏳ |
| 2.6 | Update documentation | `DEPLOYMENT.md` | ⏳ |

---

## Testing Checklist

- [ ] IB Gateway starts on boot
- [ ] TWS API connects automatically
- [ ] FX streaming works via TWS
- [ ] Trade execution via TWS API
- [ ] Reconnection after disconnect
- [ ] Fallback to Web API if TWS fails
- [ ] Circuit breaker on prolonged disconnect

---

## Notes for Jacky

**Manual Step Required**: 
You need to SSH to the server and run IB Gateway once interactively to:
1. Accept license agreement
2. Enter IBKR credentials
3. Enable API in settings
4. Check "Remember me"

**Security**:
- IB Gateway listens on localhost only (127.0.0.1:4001)
- No external exposure
- Credentials stored in IB Gateway (not in code)

**Cost**:
- IB Gateway: FREE
- FX Market Data: ~$15/month (if you want live, not delayed)

---

*Implementation started: 2026-02-16*
