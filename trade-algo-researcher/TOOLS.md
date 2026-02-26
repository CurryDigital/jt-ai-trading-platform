# TOOLS.md - Local Notes

Skill definitions define _how_ tools work. This file is for _your_ specifics — the stuff that's unique to your setup.

## What Goes Here

Things like:

- Data sources (Alpha Vantage, Yahoo Finance, Quandl, etc.)
- Backtesting frameworks (Backtrader, Zipline, QuantConnect)
- Python environment setup
- Research libraries (pandas, numpy, scipy, scikit-learn, etc.)
- Visualization tools (matplotlib, plotly, etc.)
- Database connections for historical data

## Search APIs

- **Serper API** → Web search for academic papers, financial news
  - Key: `fbccff7e2b07f4c417387bafadd141b97f1583be`
  - Use via `web_search` tool with Serper provider
  - Good for: SSRN papers, quant blogs, news sentiment sources

## Data Sources

- **Yahoo Finance** → Price data via yfinance (free)
- **IBKR TWS API** → Real-time data and execution (free)
- **RavenPack/Benzinga** → News sentiment ($500-2000/mo) — *pending*
- **PostgreSQL (AWS RDS)** → Historical data storage
  - Host: `openclaw.cjs04usueagu.ap-southeast-1.rds.amazonaws.com`
  - Schemas: bronze (raw), silver (cleaned), gold (signals), researcher (backtests)

## Backtesting

- **Backtrader** → Primary backtesting framework
- **Custom engine** → For HFT/edge strategies
- **researcher schema** → Strategy testing sandbox in RDS

## Python Stack

- pandas → Data manipulation
- numpy → Numerical computing
- scipy → Statistical tests
- scikit-learn → ML models
- statsmodels → Time series analysis
- hmmlearn → Hidden Markov Models for regime detection
- ib_insync → IBKR API integration

## Why Separate?

Skills are shared. Your setup is yours. Keeping them apart means you can update skills without losing your notes, and share skills without leaking your infrastructure.

---

## Agent-to-Agent Communication

### QA Agent Target

To send messages to the QA agent:

```json
{
  "sessionKey": "agent:trade_algo_qa:telegram:group:-5190927139"
}
```

**Usage:**
- Submit strategies for verification
- Respond to QA questions
- Escalate if needed

### Receiving QA Verdicts

**Where to check:**

1. **GitHub PR Comment** (detailed verdict)
   - URL format: `https://github.com/CurryDigital/jt-ai-trading-platform-strategy/pull/<PR_NUMBER>`
   - QA posts full analysis with line-by-line issues

2. **Telegram Chat** (notification)
   - Brief status: ✅ APPROVED or ❌ REJECTED
   - Link to GitHub PR comment

**Example workflow:**
```
1. Submit PR #5
2. Wait for Telegram notification from QA
3. Click link to GitHub PR comment
4. Read detailed verdict
5. Fix issues → push → re-request review
```

### Protocol

See `MEMORY.md` → "QA Handoff Protocol" for full workflow.

---

Add whatever helps you do your job. This is your cheat sheet.
