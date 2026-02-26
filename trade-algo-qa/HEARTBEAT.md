# HEARTBEAT.md - QA Agent Configuration

## Cron Job: Hourly Check

**Job ID:** `c520905e-92bf-4430-8522-c89fd7585a7c`  
**Interval:** Every 1 hour (3600 seconds)  
**Cost:** ~7k tokens/day (~$1-2/month)  

### What Happens Each Hour

1. **Check Telegram group** (`-5190927139`) for new messages
2. **Check sessions** for verification requests from Research Agent
3. **Review GitHub** for pending PRs requiring verification
4. **Process any queued audit tasks**
5. **Reply with status** of what was checked

### Manual Trigger

If you need immediate response, message the QA Telegram group directly:
> "@botname Check for PR #1 verification"

---

## QA Agent Periodic Tasks

- Check for incoming verification requests from Research Agent via sessions_list
- Review GitHub for pending PRs requiring verification  
- Process any queued audit tasks
- Summarize weekly rejection patterns for Jacky
- Verify researcher hasn't bypassed QA process

## Active Monitoring Protocol

On each heartbeat:
1. Check sessions for new messages from agent:trade_algo_researcher
2. If verification request found, read SOUL.md and MEMORY.md, then process
3. Respond with APPROVED/REJECTED verdict via sessions_send
4. Log audit trail to memory/audit_log_YYYY-MM-DD.md
