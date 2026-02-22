# IBKR Gateway Setup Documentation

**Date:** 2026-02-16  
**Purpose:** IBKR Gateway on t3.small EC2 for paper trading API access  
**Architecture:** ARM App Instance → t3.small Gateway → IBKR

---

## Architecture Overview

```
[ARM App Instance]      [IBKR Gateway EC2]        [IBKR]
13.214.84.37      →     52.74.14.181      →     Paper Trading
(Singapore)             (Singapore)               (US)
   ↓                           ↓
   ↓ TCP 4001                  ↓ TCP 4001/4002/443
   ↓                           ↓
[JT AI Trading Platform]    [Docker Container]
                            [IB Gateway + VNC]
```

---

## Prerequisites

- **EC2 Instance:** t3.small (x86_64) in ap-southeast-1
- **Security Groups:** Separate from app instance (`sg-ibkr-gw`)
- **IBKR Account:** Paper trading credentials ready
- **App Instance:** ARM instance (13.214.84.37) needs access to Gateway

---

## Security Group Configuration

### Gateway EC2 Security Group (`sg-ibkr-gw`)

| Type | Protocol | Port Range | Source | Purpose |
|------|----------|------------|--------|---------|
| SSH | TCP | 22 | YOUR_IP/32 | Admin access only |
| Custom TCP | TCP | 4001-4002 | sg-app-prod | App instance access |
| Custom TCP | TCP | 4001-4002 | 208.135.165.0/24 | IBKR order routing |
| Custom TCP | TCP | 4001-4002 | 208.135.166.0/24 | IBKR order routing |
| Custom TCP | TCP | 4001-4002 | 208.135.167.0/24 | IBKR order routing |
| Custom TCP | TCP | 4001-4002 | 69.22.132.0/24 | IBKR HDC/backup |
| HTTPS | TCP | 443 | 208.135.165.0/24 | IBKR auth/handshake |
| HTTPS | TCP | 443 | 208.135.166.0/24 | IBKR auth/handshake |
| HTTPS | TCP | 443 | 208.135.167.0/24 | IBKR auth/handshake |
| HTTPS | TCP | 443 | 69.22.132.0/24 | IBKR auth/handshake |
| Custom TCP | TCP | 5900 | YOUR_IP/32 | VNC (temporary setup) |

**⚠️ Important:** Remove VNC (port 5900) from security group after setup is complete.

---

## Installation Steps

### 1. Launch EC2 Instance

- **Instance Type:** t3.small (2 vCPU, 2 GB RAM)
- **AMI:** Ubuntu 22.04 LTS (x86_64)
- **Storage:** 20 GB gp3
- **Security Group:** `sg-ibkr-gw` (as defined above)
- **Public IP:** Yes (for initial setup)
- **IAM Role:** None required for basic operation

### 2. Install Docker

```bash
sudo apt-get update
sudo apt-get install -y docker.io
sudo usermod -aG docker ubuntu
```

### 3. Create Docker Configuration

```bash
sudo mkdir -p /opt/ibkr-docker
cd /opt/ibkr-docker

sudo tee Dockerfile > /dev/null <<'EOF'
FROM ubuntu:22.04

RUN apt-get update && apt-get install -y \
    wget default-jre xvfb x11vnc net-tools \
    && rm -rf /var/lib/apt/lists/*

# Download IB Gateway
RUN wget -q https://download2.interactivebrokers.com/installers/ibgateway/stable-standalone/ibgateway-stable-standalone-linux-x64.sh -O /tmp/ibgw.sh \
    && chmod +x /tmp/ibgw.sh \
    && /tmp/ibgw.sh -q -dir /opt/ibgateway \
    && rm /tmp/ibgw.sh

ENV DISPLAY=:99
ENV VNC_PASSWORD=ibkr123

EXPOSE 4001 4002 5900

# Create startup script with proper delay
RUN echo '#!/bin/bash\n\
Xvfb :99 -screen 0 1280x800x24 -ac +extension GLX +render -noreset &\n\
sleep 5\n\
x11vnc -display :99 -nopw -forever -shared -rfbport 5900 &\n\
sleep 2\n\
/opt/ibgateway/ibgateway\n\
' > /start.sh && chmod +x /start.sh

CMD ["/start.sh"]
EOF
```

### 4. Build and Run Container

```bash
sudo docker build -t ibgateway-local .

sudo docker run -d \
  --name ibgateway \
  --restart unless-stopped \
  -p 4001:4001 \
  -p 4002:4002 \
  -p 5900:5900 \
  ibgateway-local
```

### 5. Verify Container Status

```bash
# Check if running
sudo docker ps

# View logs
sudo docker logs -f ibgateway

# Check processes
sudo docker exec ibgateway ps aux | grep -E "Xvfb|x11vnc|ibgateway"

# Verify ports are listening
sudo ss -tlnp | grep -E "4001|4002|5900"
```

---

## Initial Configuration via VNC

### 1. Establish SSH Tunnel

From your local machine:
```bash
ssh -i ~/.ssh/your-key.pem -L 5900:localhost:5900 ubuntu@52.74.14.181
```

### 2. Connect VNC Viewer

- **Address:** `localhost:5900`
- **Password:** `ibkr123` (or as set in Dockerfile)

### 3. IB Gateway Login

1. Select **"IB API"** (not FIX CTCI)
2. Enter your **IBKR username** and **password**
3. Check **"Remember me"**
4. Click **"Paper Trading"**
5. Login

### 4. Configure API Settings

Navigate to: **Edit → Settings → API → Settings**

| Setting | Value |
|---------|-------|
| Socket port | `4001` |
| Listen for connections from | `0.0.0.0` or `13.214.84.37` |
| Allow connections from localhost only | **UNCHECK** |
| Create API message log | CHECK (for debugging) |
| Trusted IP Addresses | Add `13.214.84.37` |
| Master Client ID | `0` |

Click **Apply → OK**

### 5. Verify API is Active

In the Gateway window, the API status should show **green/connected**.

---

## Testing Connectivity

### From App Instance (ARM)

```bash
# Test TCP connection to Gateway
nc -zv 52.74.14.181 4001

# Expected output:
# Connection to 52.74.14.181 4001 port [tcp/*] succeeded!

# Alternative test
telnet 52.74.14.181 4001
```

### Check Gateway Logs

```bash
# Real-time logs
sudo docker logs -f ibgateway

# Last 50 lines
sudo docker logs --tail 50 ibgateway
```

---

## Integration with Trading Platform

### Connection Settings

| Parameter | Value |
|-----------|-------|
| Host | `52.74.14.181` |
| Port | `4001` |
| Client ID | `0` (or unique per connection) |
| Account | Paper trading account |

### Example Python (ib_insync)

```python
from ib_insync import IB, Stock

ib = IB()
ib.connect('52.74.14.181', 4001, clientId=0)

# Test connection
print(ib.reqCurrentTime())

# Disconnect
ib.disconnect()
```

---

## Post-Setup Security Hardening

### 1. Remove VNC Access

After confirming everything works:

```bash
# AWS Console: Security Group sg-ibkr-gw
# Remove rule: TCP 5900 from 0.0.0.0/0 or YOUR_IP/32
```

### 2. Lock Down SSH

Ensure SSH (port 22) in `sg-ibkr-gw` is restricted to your IP only (`x.x.x.x/32`), not `0.0.0.0/0`.

### 3. Consider Removing Public IP

If using AWS Systems Manager (SSM) for access:
- Remove public IP from Gateway EC2
- Attach IAM role with `AmazonSSMManagedInstanceCore`
- Connect via: `aws ssm start-session --target i-xxxxxx`

---

## Maintenance Commands

### Restart Gateway

```bash
sudo docker restart ibgateway
```

### View Status

```bash
sudo docker ps
sudo docker logs ibgateway
sudo ss -tlnp | grep 4001
```

### Update IB Gateway

```bash
# Stop container
sudo docker stop ibgateway
sudo docker rm ibgateway

# Rebuild with latest version
cd /opt/ibkr-docker
sudo docker build --no-cache -t ibgateway-local .

# Restart
sudo docker run -d \
  --name ibgateway \
  --restart unless-stopped \
  -p 4001:4001 \
  -p 4002:4002 \
  -p 5900:5900 \
  ibgateway-local
```

### Full Reset

```bash
# Stop and remove container
sudo docker stop ibgateway
sudo docker rm ibgateway

# Remove image
sudo docker rmi ibgateway-local

# Rebuild from scratch
cd /opt/ibkr-docker
sudo docker build -t ibgateway-local .
sudo docker run -d \
  --name ibgateway \
  --restart unless-stopped \
  -p 4001:4001 \
  -p 4002:4002 \
  -p 5900:5900 \
  ibgateway-local
```

---

## Troubleshooting

### Gateway not listening on 4001

```bash
# Check if container is running
sudo docker ps

# Check logs for errors
sudo docker logs ibgateway

# Restart container
sudo docker restart ibgateway
```

### Cannot connect from App Instance

1. Verify security group allows port 4001 from `sg-app-prod`
2. Test with `nc -zv 52.74.14.181 4001`
3. Check if using IP-based SG rule works (add `13.214.84.37/32` directly)

### VNC connection refused

```bash
# Check if x11vnc is running
sudo docker exec ibgateway ps aux | grep vnc

# Restart VNC manually
sudo docker exec ibgateway pkill -f x11vnc
sudo docker exec ibgateway x11vnc -display :99 -nopw -forever -shared -rfbport 5900 &
```

### Container keeps restarting

```bash
# Check for errors
sudo docker logs --tail 100 ibgateway

# Common issues:
# - Xvfb failed to start
# - IB Gateway binary missing
# - Port conflicts
```

---

## Cost Estimate

| Component | Monthly Cost (Singapore) |
|-----------|-------------------------|
| t3.small on-demand | ~$15 |
| 20 GB gp3 storage | ~$2 |
| Data transfer (minimal) | ~$1-5 |
| **Total** | **~$18-22/month** |

---

## References

- **IBKR Connectivity:** https://www.interactivebrokers.com/en/index.php?f=16457
- **IB Gateway Download:** https://www.interactivebrokers.com/en/index.php?f=16457
- **IBKR API Documentation:** https://interactivebrokers.github.io/tws-api/
- **IBC (IB Controller):** https://github.com/IbcAlpha/IBC

---

## Notes

- **Paper Trading:** Use `TRADING_MODE=paper` environment variable if using pre-configured images
- **Live Trading:** Requires additional compliance checks and risk controls
- **Latency:** Singapore to IBKR US = ~200-250ms (acceptable for non-HFT strategies)
- **Backups:** IB Gateway stores settings in container; no persistent volume needed if "Remember me" is checked

---

**Last Updated:** 2026-02-16  
**Gateway IP:** 52.74.14.181  
**App Instance IP:** 13.214.84.37
---

## Additional Troubleshooting (Added 2026-02-16)

### Backend connection keeps dropping

**Problem:** API Client shows "disconnected" in Gateway window

**Solution:**
1. Backend uses threaded IBKR service (avoids asyncio conflicts)
2. Keep-alive script monitors and auto-restarts backend:
```bash
# On ARM instance, keep-alive is running at /tmp/keep_alive.sh
# Check status:
ps aux | grep keep_alive

# View log:
tail -f /tmp/keep_alive.log
```

### API Client "Read-Only Mode"

**Problem:** Can connect but cannot place trades

**Solution:**
1. VNC to Gateway: `ssh -L 5900:localhost:5900 ubuntu@52.74.14.181`
2. In Gateway window: **Edit → Settings → API → Settings**
3. **UNCHECK** "Read-Only API"
4. Click **Apply → OK**

### Historical Data Farm "inactive"

**Problem:** Shows "inactive: ushmds" in Gateway

**Solution:**
- This is **normal for paper trading** without market data subscriptions
- For live market data, subscribe via IBKR Client Portal:
  - US Securities Snapshot: $10/month
  - Forex: Free with IBKR
  - Crypto: Free
- Platform works fine with Yahoo Finance for signals, IBKR for execution only

---

## Backend Threaded Service Implementation

The backend uses a threaded wrapper to avoid asyncio conflicts:

```python
# app/services/ib_service.py
class IBKRThreadedService:
    def __init__(self, host='52.74.14.181', port=4001, client_id=1):
        self.host = host
        self.port = port
        self.client_id = client_id
        self._thread = None
        self._ib = None
        
    def _run_in_thread(self):
        """Isolated event loop for ib_insync"""
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        self._ib = IB()
        self._ib.connect(self.host, self.port, clientId=self.client_id)
        # ... keep alive
```

This isolates IBKR's event loop from FastAPI's asyncio loop, preventing crashes.

---

## Keep-Alive Monitoring

The ARM instance runs a keep-alive script that:
1. Pings backend every 30 seconds
2. Detects crashes automatically
3. Restarts backend within 10 seconds
4. Maintains IBKR connection persistence

**Script location:** `/tmp/keep_alive.sh`  
**Process:** `ps aux | grep keep_alive`

---

## Updated Configuration (2026-02-16)

**Changes Made:**
- Threaded IBKR service to avoid asyncio conflicts
- Disabled Prophet forecasting (CPU overload)
- Disabled FX streaming (event loop conflicts)
- Keep-alive script for backend persistence
- Gateway IP updated to 52.74.14.181

**Current Status:**
- ✅ Backend: Stable with keep-alive
- ✅ IBKR Gateway: Connected
- ✅ Data: Yahoo Finance primary, IBKR execution
- ⚠️ Historical Data: Inactive (paper trading)

---

**Last Updated:** 2026-02-16  
**Gateway IP:** 52.74.14.181  
**App Instance IP:** 13.214.84.37
