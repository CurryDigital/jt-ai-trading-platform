---
name: trade-algo-qa
slug: trade-algo-qa
description: Automated trading strategy verification toolkit for QA agents. Validates backtest results, detects lookahead bias, verifies database claims, and reproduces researcher findings.
version: 1.0.0
author: Digital (CurryDigital)
metadata:
  {
    "openclaw":
      {
        "requires": { "bins": ["python3", "psql"] },
        "install": [],
      },
  }
---

# Trade Algo QA Skill

Tools for verifying trading strategy research submissions.

## Capabilities

### 1. Backtest Verification
- Reproduce researcher backtests independently
- Test with modified transaction costs
- Generate equity curves and drawdown analysis
- Validate Sharpe, win rate, max DD calculations

### 2. Database Integrity Checks
- Query RDS for claimed trade counts
- Verify no lookahead bias in timestamps
- Check data availability for claimed date ranges
- Validate ticker universe coverage

### 3. Statistical Tests
- Calculate statistical significance (p-values)
- Walk-forward validation
- Parameter sensitivity analysis
- Monte Carlo simulation

### 4. Code Review
- Check for common researcher shortcuts
- Validate signal timing (no lookahead)
- Verify stop loss and position sizing logic
- Detect data leakage

## Usage

```bash
# Verify a strategy against database
taq-verify --strategy S001 --start 2023-01-01 --end 2024-12-31

# Reproduce with different costs
taq-backtest --strategy S001 --cost 0.003

# Check database for claims
taq-db-check --trades 2053 --ticker S002

# Full audit
taq-audit --pr 1 --repo jt-ai-trading-platform-strategy
```

## Files

- `verify_backtest.py` - Core verification engine
- `db_checks.py` - Database integrity queries
- `stats.py` - Statistical calculations
- `report.py` - Generate QA reports

## Requirements

- Python 3.10+
- psycopg2
- pandas, numpy
- boto3 (for RDS IAM auth)

## License

Private - JTCML Trading Platform
