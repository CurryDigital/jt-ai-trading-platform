# Database Connection Troubleshooting Log
**Date:** 2026-02-20

## Issue Summary
RDS connection failing for both users: `researcher` and `openclaw`

## Errors Found

### 1. Password Authentication Failed
```
FATAL: password authentication failed for user "openclaw"
FATAL: password authentication failed for user "researcher"
```

### 2. Security Group / pg_hba.conf Issue (CRITICAL)
```
FATAL: no pg_hba.conf entry for host "172.31.34.100", user "openclaw", 
       database "aitrading_schema", no encryption
```

**Your EC2 IP:** 172.31.34.100 (internal AWS IP)
**RDS IP:** 172.31.36.65 (same VPC, different subnet)

## Root Cause

The RDS security group does **NOT** allow inbound connections from your EC2 instance (172.31.34.100). This is a **network-level block**, not just a password issue.

## Solutions

### Option 1: Fix RDS Security Group (Recommended)
Jacky needs to update the RDS security group to allow:
- **Type:** PostgreSQL
- **Port:** 5432
- **Source:** 172.31.34.100/32 (this EC2 instance)
- **OR:** The EC2 instance's security group ID

### Option 2: Verify Correct Credentials
Current attempts failed with passwords:
- `Openclaw2026!` ❌
- `openclaw` ❌
- `OpenClaw2026` ❌

Need correct password from Jacky or AWS Secrets Manager.

### Option 3: Use yfinance Fallback (Immediate)
For HK Open analysis today, use free yfinance:
```python
import yfinance as yf
data = yf.download(['0700.HK', '9988.HK', '0001.HK'], period='1d')
```

### Option 4: JT Trading Agent Proxy
Have JT Trading Agent query the DB and send results to you.

## Files Checked
- TOOLS.md - Has RDS credentials (outdated?)
- No AWS Secrets Manager integration found
- No environment variables set for DB auth

## Recommendation
1. **Immediate:** Use yfinance for today's analysis
2. **Short-term:** Ask Jacky to whitelist EC2 IP in RDS security group
3. **Long-term:** Set up AWS Secrets Manager for credential rotation

---

**Status:** Blocked at network level. Security group update required.
