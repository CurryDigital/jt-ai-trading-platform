# IBKR Gateway Setup Guide for Tier 2 Strategies

**Date:** 2026-02-18  
**Purpose:** Connect to IBKR Gateway for forex and futures data

---

## Prerequisites

1. **IBKR Gateway installed**
2. **Paper trading account** (recommended for testing)
3. **API enabled** in account settings

---

## Step 1: Start IBKR Gateway

```bash
# Navigate to IBKR Gateway installation
cd ~/Jts/ibgateway/10xx/

# Start Gateway
./ibgateway

# Or use the desktop shortcut
```

---

## Step 2: Login

1. Login with paper trading credentials
2. Go to **Edit → Global Configuration**
3. Select **API → Settings**
4. Enable:
   - ☑️ "Enable ActiveX and Socket Clients"
   - Socket port: `7497` (paper) or `7496` (live)
   - ☑️ "Allow connections from localhost only"

---

## Step 3: Test Connection

```python
from ib_insync import *

# Connect to Gateway
ib = IB()
ib.connect('127.0.0.1', 7497, clientId=1)

print("Connected!" if ib.isConnected() else "Failed")

# Test: Get EURUSD data
contract = Forex('EURUSD')
bars = ib.reqHistoricalData(
    contract,
    endDateTime='',
    durationStr='1 D',
    barSizeSetting='1 hour',
    whatToShow='MIDPOINT',
    useRTH=True
)

print(f"Got {len(bars)} bars")
ib.disconnect()
```

---

## Step 4: Run Tier 2 Backtests

### FX Carry + Momentum
```bash
cd strategies
python3 fx_carry_momentum_ibkr.py
```

### Asian Session Liquidity
```bash
python3 asian_session_liquidity_ibkr.py
```

### VIX Futures Contango
```bash
python3 vix_futures_contango_ibkr.py
```

---

## Data Subscriptions

| Market | Subscription | Cost |
|--------|-------------|------|
| Forex | IdealPro | Free |
| CBOE VIX Futures | US Securities Snapshot | ~$10/mo |
| Europe stocks | Various | Varies |

**To subscribe:**
1. Login to IBKR Client Portal
2. User Settings → Market Data Subscriptions
3. Add required subscriptions

---

## Troubleshooting

### "Connection refused"
- Gateway not running? Start it first
- Wrong port? Check 7497 for paper
- Firewall blocking? Allow localhost:7497

### "No market data"
- Subscription missing? Check Client Portal
- Market closed? Try during trading hours
- Wrong contract? Verify symbol

### "Rate limit exceeded"
- IBKR limits: 100 messages/sec
- Add `ib.sleep(1)` between requests
- Use `reqHistoricalData` with endDateTime for bulk

---

## Production Checklist

Before live trading:
- [ ] Tested on paper account for 1 month
- [ ] Market data subscriptions active
- [ ] Margin requirements calculated
- [ ] Error handling for disconnects
- [ ] Position sizing validated
- [ ] Emergency stop procedure

---

## Strategy-Specific Notes

### FX Carry
- **Pairs:** AUDJPY, NZDJPY most reliable
- **Data:** Need central bank rates for carry calc
- **Time:** Best entries during London open

### Asian Session
- **Hours:** Tokyo 19:00-04:00 ET
- **Data:** Hourly bars minimum
- **Liquidity:** Thinnest 00:00-02:00 ET

### VIX Futures
- **Symbols:** VX1, VX2 (front 2 months)
- **Settlement:** Cash (no delivery)
- **Margin:** ~$15k per contract

---

## Next Steps

1. Start IBKR Gateway
2. Run test connection script
3. Subscribe to required data
4. Run Tier 2 backtests
5. Report results

Ready when you are.
