# Telegram Alert Setup Guide

## Overview
Get instant notifications for trades, drawdowns, and system events via Telegram.

---

## Step 1: Create a Telegram Bot

1. **Open Telegram** and search for **@BotFather**
2. **Start a chat** and type `/newbot`
3. **Give your bot a name** (e.g., "JT Trading Alerts")
4. **Give it a username** (e.g., "jt_trading_alerts_bot")
5. **Copy the Bot Token** - it looks like: `123456789:ABCdefGHIjklMNOpqrSTUvwxyz`

**Save this token - you'll need it!**

---

## Step 2: Get Your Chat ID

### Option A: Personal Chat (just you)
1. Search for **@userinfobot** in Telegram
2. Start the bot
3. It will reply with your info including **ID**
4. Copy the number (e.g., `123456789`)

### Option B: Group Chat (multiple people)
1. Create a new group in Telegram
2. Add your bot to the group
3. Send a message in the group: `/start`
4. Visit this URL in browser:
   ```
   https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates
   ```
5. Look for `"chat":{"id":-123456789` - copy the number including the minus sign

**This is your Chat ID!**

---

## Step 3: Configure Alerts

### Via API
```bash
# Configure Telegram
curl -X POST http://127.0.0.1:8000/api/alerts/configure \
  -H "Content-Type: application/json" \
  -d '{
    "bot_token": "YOUR_BOT_TOKEN_HERE",
    "chat_id": "YOUR_CHAT_ID_HERE"
  }'
```

**Expected response:**
```json
{
  "status": "success",
  "message": "Telegram alerts configured successfully",
  "test_message_sent": true
}
```

You should receive a test message in Telegram immediately!

---

## Step 4: Test Alerts

### Test Trade Alert
```bash
curl -X POST http://127.0.0.1:8000/api/alerts/test \
  -H "Content-Type: application/json" \
  -d '{"type": "trade"}'
```

### Test Drawdown Alert
```bash
curl -X POST http://127.0.0.1:8000/api/alerts/test \
  -H "Content-Type: application/json" \
  -d '{"type": "drawdown"}'
```

### Test Custom Message
```bash
curl -X POST http://127.0.0.1:8000/api/alerts/test \
  -H "Content-Type: application/json" \
  -d '{"type": "custom", "message": "Hello from trading platform!"}'
```

### Send Daily Summary
```bash
curl -X POST http://127.0.0.1:8000/api/alerts/daily-summary
```

---

## What Alerts You'll Get

### 🔴 Automatic Alerts

| Event | When |
|-------|------|
| **Trade Executed** | Every BUY/SELL order filled |
| **Trade Signal** | Strategy generates entry/exit signal |
| **Drawdown >5%** | Strategy down 5% from peak |
| **Drawdown >10%** | Strategy down 10% from peak (HIGH) |
| **Drawdown >15%** | Strategy down 15% from peak (CRITICAL) |
| **Portfolio Drawdown** | Total portfolio down >5% |
| **Backend Restart** | Service restarts (crash or deploy) |
| **Strategy Mode Change** | SIM → PAPER → LIVE transitions |
| **IBKR Disconnect** | Lost connection to Interactive Brokers |

### 📊 Daily Summary
Every day at market close, you'll get:
- Total portfolio return
- Total P&L
- Number of trades
- Top 3 performing strategies

---

## API Reference

### Check Status
```bash
GET /api/alerts/status
```

### Configure
```bash
POST /api/alerts/configure
Body: {"bot_token": "...", "chat_id": "..."}
```

### Test Alert
```bash
POST /api/alerts/test
Body: {"type": "trade|drawdown|custom", "message": "..."}
```

### Daily Summary
```bash
POST /api/alerts/daily-summary
```

---

## Troubleshooting

### "Telegram not configured" error
- You haven't called `/api/alerts/configure` yet
- Or the configuration failed

### Test message not received
1. Check bot token is correct (no extra spaces)
2. Check chat ID is correct (include minus sign for groups)
3. Make sure you started the bot (send `/start`)
4. Check bot is added to the group (if using group)

### Alerts not sending
- Check `/api/alerts/status` shows `enabled: true`
- Check logs: `sudo journalctl -u trading-backend -f | grep -i telegram`

### Reset configuration
```bash
# Just reconfigure with new token/chat_id
POST /api/alerts/configure
```

---

## Example Alert Messages

### Trade Alert
```
🟢 TRADE EXECUTED

📊 Strategy: MR_FX_EURUSD
💱 Ticker: EURUSD=X
📈 Side: BUY
🔢 Quantity: 10,000
💵 Price: $1.0850
💵 Value: $10,850.00

⏰ 2026-02-17 15:30:45 HKT
```

### Drawdown Alert
```
🟡 MEDIUM DRAWDOWN ALERT

📊 Strategy: TREND_FX_GBPUSD
📉 Drawdown: 7.5%
💰 Current P&L: -$750.00
💵 Allocated: $10,000.00

⚠️ Consider reviewing or stopping this strategy.

⏰ 2026-02-17 15:30:45 HKT
```

### Daily Summary
```
📊 DAILY PORTFOLIO SUMMARY

🟢 Total Return: +2.35%
💰 Total P&L: +$1,645.00
📈 Total Trades: 12
💵 Total Allocated: $70,000.00

🏆 Top Strategies:
  • MR_FX_EURUSD: $450.00
  • TREND_FX_GBPUSD: $380.00
  • CARRY_FX_AUDUSD: $215.00

⏰ 2026-02-17 16:00:00 HKT
```

---

## Security Notes

- **Bot Token** is sensitive - keep it private
- **Chat ID** is less sensitive but still private
- Store in environment variables, not in code
- The API doesn't expose full bot token in responses

---

## Next Steps

1. ✅ Create bot with @BotFather
2. ✅ Get your chat ID
3. ✅ Configure via API
4. ✅ Test with sample alerts
5. ✅ Wait for real alerts to come in!

---

*Need help? Check the backend logs: `sudo journalctl -u trading-backend -f`*