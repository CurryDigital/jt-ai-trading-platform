# Trade Algo QA Skill

Custom skill for verifying trading strategy research submissions.

## Installation

### Option 1: Use Locally
```bash
cd /home/ubuntu/.openclaw/workspace/trade-algo-qa/skills/trade-algo-qa
python3 verify_backtest.py --strategy S001 --trades 994 --wr 52.3
```

### Option 2: Publish to ClawHub
```bash
# Install clawhub CLI
npm i -g clawhub

# Login and publish
clawhub login
clawhub publish ./trade-algo-qa \
  --slug trade-algo-qa \
  --name "Trade Algo QA" \
  --version 1.0.0
```

## Usage

### Basic Verification
```bash
python3 verify_backtest.py \
  --strategy S001 \
  --trades 994 \
  --wr 52.3 \
  --start 2023-01-01 \
  --end 2024-12-31
```

### Sector-Specific Strategy
```bash
python3 verify_backtest.py \
  --strategy S002 \
  --trades 88 \
  --wr 59.1 \
  --type sector \
  --start 2023-01-01 \
  --end 2024-12-31
```

### With Lookahead Check
```bash
python3 verify_backtest.py \
  --strategy S001 \
  --trades 994 \
  --wr 52.3 \
  --script /path/to/backtest_script.py
```

## What It Checks

### 1. Data Availability
- Verifies tickers exist in `silver.unified_prices`
- Checks date range coverage
- Shows market breakdown (US/HK/CN/Crypto)

### 2. Database Verification
- Cross-checks claims against `openclaw_researcher.backtest_results`
- Validates trade counts and win rates
- Flags mismatches

### 3. Statistical Quality (Updated Standards)

**Trade Count Thresholds by Strategy Type:**
| Type | Minimum/Year | Target/Year |
|------|--------------|-------------|
| Sector | 30 | 50 |
| Market | 50 | 100 |
| Multi | 75 | 150 |

**Confidence Interval Evaluation:**
| CI Width | Verdict |
|----------|---------|
| < 20% | ✅ Robust |
| 20-28% | 🟡 Acceptable |
| 28-35% | ⚠️ Marginal |
| > 35% | ❌ Insufficient |

### 4. Lookahead Detection
- Scans scripts for `.shift(1)` protection
- Detects common bias patterns
- Flags critical issues

### 5. Market Regimes
- Shows test period regime distribution
- Identifies bull/bear/sideways periods

## Output

```
======================================================================
🔍 QA VERIFICATION REPORT: S001
======================================================================

📊 DATA AVAILABILITY
   Total Tickers: 204
   Markets: US(99), HK(50), CN(49), CRYPTO(6)
   Date Range: 2023-01-01 to 2024-12-31
   Status: ✅ OK

📈 CLAIM VERIFICATION
   Trades: 994 claimed vs 994 in DB ✅
   Win Rate: 52.3% claimed vs 52.1% in DB ✅

📉 STATISTICAL QUALITY
   Test Period: 2.0 years
   Total Trades: 994
   Trades/Year: 497.0
   Strategy Type: MARKET
   Minimum Required: 50/year
   Target: 100/year
   95% CI: 49.2% - 55.4% (width: 6.2%)
   Significance: ✅ Robust (CI < 20%)
   Threshold: ✅ Exceeds target

🔎 LOOKAHEAD BIAS CHECK
   ✅ Proper protection detected (.shift(1) used)

======================================================================
✅ VERDICT: APPROVED — Strategy passes all checks
======================================================================
```

## Requirements

- Python 3.10+
- boto3 (RDS IAM auth)
- psycopg2
- pandas, numpy
- Access to aitrading RDS database

## Files

- `verify_backtest.py` - Main verification tool
- `SKILL.md` - Skill manifest
- `README.md` - This file

## License

Private - JTCML Trading Platform
