# QA Agent Workspace - Setup Summary

**Created:** 2026-02-25  
**Location:** `/home/ubuntu/.openclaw/workspace/trade-algo-qa`

---

## Files Created

| File | Purpose |
|------|---------|
| `SOUL.md` | QA agent personality, workflow, boundaries |
| `MEMORY.md` | Verification standards, common shortcuts, audit templates |
| `IDENTITY.md` | Basic metadata |
| `USER.md` | Jacky's context and escalation rules |
| `AGENTS.md` | Relationship to Research Agent |
| `TOOLS.md` | Environment notes and data sources |
| `HEARTBEAT.md` | Empty (add periodic tasks when ready) |
| `BOOTSTRAP.md` | First-run guide (delete after init) |

**Agent Config:** `/home/ubuntu/.openclaw/agents/trade_algo_qa/agent.json`

---

## Directory Structure

```
trade-algo-qa/
├── SOUL.md                 # Who you are
├── MEMORY.md               # What you know
├── IDENTITY.md             # Basic identity
├── USER.md                 # Who Jacky is
├── AGENTS.md               # Workspace relationships
├── TOOLS.md                # Environment notes
├── HEARTBEAT.md            # Periodic tasks (empty)
├── BOOTSTRAP.md            # First-run guide
├── memory/                 # Daily audit logs (empty)
└── audit_trail/            # Strategy-specific reports (empty)
```

---

## Next Steps

### 1. Register Agent in OpenClaw Config

Add to `/home/ubuntu/.openclaw/config.json` (or equivalent):

```json
{
  "agents": [
    {
      "agentId": "trade_algo_qa",
      "name": "Trade Algo QA",
      "workspace": "/home/ubuntu/.openclaw/workspace/trade-algo-qa",
      "model": "kimi-coding/k2p5"
    }
  ]
}
```

### 2. Connect Telegram Group

Create a new Telegram group for QA:
1. Create group: "JTCML Algo QA"
2. Add your bot (@your_bot_name)
3. Get chat ID (use @getidsbot)
4. Add to `openclaw.json` bindings:

```json
{
  "channels": {
    "telegram": {
      "groups": {
        "-CHAT_ID_HERE": {
          "groupPolicy": "open",
          "requireMention": false
        }
      }
    }
  },
  "bindings": [
    {
      "match": {
        "channel": "telegram",
        "peer": { "kind": "group", "id": "-CHAT_ID_HERE" }
      },
      "agentId": "trade_algo_qa"
    }
  ]
}
```

### 3. Restart Gateway

```bash
openclaw gateway restart
```

### 4. Test

Message the QA group and verify the agent responds.

---

## Workflow Integration

```
Research Agent Workspace          QA Agent Workspace
        │                                │
        ▼                                │
   [Develops Strategy]                   │
        │                                │
        ▼                                │
   GitHub PR created ───────────────────▶│
        │                                │
        │◄──────────────────────────── [Pulls code]
        │                                │
        │◄──────────────────────────── [Verifies independently]
        │                                │
        │◄──────────────────────────── [Issues APPROVE/REJECT]
        │                                │
   [Fixes if rejected]                   │
        │                                │
        ▼                                ▼
   Jacky reviews both ──────────────────▶ [Escalations]
```

---

## Key Design Decisions

1. **Isolated Memory**: QA agent cannot read researcher's private `MEMORY.md`
2. **GitHub as Neutral Ground**: Both clone from repo, no direct memory sharing
3. **Veto Power**: QA can block deployment
4. **Escalation Path**: Deadlock goes to Jacky

---

## Immediate Use Cases

Once connected, the QA agent can:
1. Review the researcher's pending strategies
2. Verify backtest claims
3. Audit for data leakage/lookahead bias
4. Track patterns of shortcuts

---

*Ready for Telegram connection. Provide the chat ID when available.*
