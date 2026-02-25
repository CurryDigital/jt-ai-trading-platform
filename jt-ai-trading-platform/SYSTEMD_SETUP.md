# Systemd Service Setup - COMPLETE ✅

## Service Configuration

**Service Name:** `trading-backend.service`
**Status:** ✅ Active and running
**Auto-restart:** ✅ Enabled

---

## What Was Set Up

### Systemd Service File
Location: `/etc/systemd/system/trading-backend.service`

Features:
- ✅ Auto-starts on system boot
- ✅ Auto-restarts on crash (Restart=always)
- ✅ 10-second delay between restarts
- ✅ Runs as ubuntu user
- ✅ Logs to journald (view with journalctl)

---

## Management Commands

### Check Status
```bash
sudo systemctl status trading-backend
```

### Start/Stop/Restart
```bash
sudo systemctl start trading-backend
sudo systemctl stop trading-backend
sudo systemctl restart trading-backend
```

### View Logs
```bash
# Recent logs
sudo journalctl -u trading-backend --no-pager -n 50

# Follow logs in real-time
sudo journalctl -u trading-backend -f

# Logs since today
sudo journalctl -u trading-backend --since today
```

### Enable/Disable Auto-start
```bash
# Enable (auto-start on boot)
sudo systemctl enable trading-backend

# Disable (don't auto-start)
sudo systemctl disable trading-backend
```

---

## Current Status

```
Service:     active (running) ✅
PID:         55869
Memory:      ~202 MB
Port:        8000 (listening)
FX Pairs:    13 ✅
Stocks:      13 ✅
Crypto:      9 ✅
Website:     200 OK ✅
Auto-restart: always ✅
```

---

## Testing Auto-Restart

To verify auto-restart works, you can kill the process:

```bash
# Kill the process (simulates crash)
sudo pkill -f uvicorn

# Check that it restarts automatically
sudo systemctl status trading-backend
```

You should see it restart within 10 seconds.

---

## Troubleshooting

### If service won't start
```bash
# Check for errors
sudo journalctl -u trading-backend --no-pager -n 20

# Check port conflict
sudo ss -tlnp | grep 8000

# Manual test
 cd /home/ubuntu/.openclaw/workspace/jt-ai-trading-platform/backend
./start.sh
```

### If data not showing on website
1. Check service status: `sudo systemctl status trading-backend`
2. Check API directly: `curl http://127.0.0.1:8000/api/fx/pairs`
3. Check Cloudflare: `curl https://trade.jtcml.com/api/fx/pairs`

### Restart everything fresh
```bash
sudo systemctl restart trading-backend
sleep 5
curl https://trade.jtcml.com/api/fx/pairs
```

---

## Verification

Test that everything works:

```bash
# 1. Service is running
sudo systemctl is-active trading-backend
# Expected: active

# 2. API responds
 curl http://127.0.0.1:8000/api/execution/status
# Expected: JSON with "connected":true

# 3. FX data flowing
curl http://127.0.0.1:8000/api/fx/pairs | jq length
# Expected: 13

# 4. Website works
curl -s -o /dev/null -w "%{http_code}" https://trade.jtcml.com/api/fx/pairs
# Expected: 200
```

---

## Next Steps

✅ **DONE:** Systemd service with auto-restart

**Optional additions:**
1. Telegram alerts when service restarts
2. Cloudflare health check notifications
3. Log rotation (journald handles this automatically)

---

*Setup completed: 2026-02-17*
*Service will now auto-restart on crash or system reboot*