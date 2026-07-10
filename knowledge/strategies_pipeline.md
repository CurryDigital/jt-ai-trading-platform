# Strategies › Pipeline

**Purpose:** THE deployment control surface. Three columns = the real mode
ladder (Simulation → Paper → Live) driven by `execution_mode`. Each card
shows real registry metrics + annual backtest bars and the promote/demote
actions. Promotions run the backend gate engine and are audited; live
deployment requires a typed confirmation phrase.

**Component:** `frontend/src/components/StrategiesWorkspace.jsx`
(`StrategyPipelineBoard` + `PromoteModal`) — book poll 60s.

## Deployment flow (the contract that must not break)
1. Card button → `POST /api/strategies/{id}/promote/check` `{ target_mode }`
   ```jsonc
   { "strategy_id":"...","current_mode":"PAPER_TRADING","target_mode":"LIVE_TRADING",
     "is_promotion":true,"requires_confirmation_phrase":true,"confirmation_phrase":"PROMOTE TO LIVE",
     "passed":false,"blocked":false,
     "gates":[{"id":"live_trades","label":"Live trades ≥ 20","required":true,"pass":false,
               "actual":12,"threshold":20,"reason":"Insufficient paper trades..."}],
     "metrics":{...} }
   ```
2. Modal renders the gates; LIVE needs the exact phrase typed; failing gates
   can be overridden via explicit checkbox (`override_gates:true`, audited).
3. Confirm → `POST /api/strategies/{id}/promote`
   `{ target_mode, confirmation_phrase?, override_gates? }` →
   `{ success:true }` or `{ success:false, gates:[...] }` (HTTP 200) or 400
   (wrong phrase / unsupported transition).
4. On success the UI refetches `/api/strategies/researcher?fresh=1`
   (bypasses the 15s cache) — no optimistic state.

Supported transitions (`PROMOTION_GATES` in `backend/app/main.py`):
`SIM→PAPER` (backtest gates) · `PAPER→LIVE` (live gates + phrase) ·
demotions `LIVE→PAPER`, `PAPER→SIM`, `LIVE→SIM` (no gates).
Mode changes write `gold.strategy_registry.execution_mode` + a
`strategy.mode_change` row in `gold.audit_events` + an event-bus publish.

## Data
Book comes from `GET /api/strategies/researcher` (see
[strategies_lab.md](strategies_lab.md)); mapping to card shape lives in
`frontend/src/components/strategyProfiles.js` (`mapApiToBook` — unit-tested
in `src/test/strategyProfiles.test.js`).

## Known gaps
- Column placement uses `execution_mode` only; `priority`
  (EXPERIMENTAL/NEAR_GOLDEN/GOLDEN) shows as a stage chip on the card but
  is research-pipeline-owned — the UI never writes it.
- Gate thresholds are hardcoded in `main.py` `PROMOTION_GATES`; Settings →
  Risk Config edits a separate `settings.risk_config.*` namespace that the
  gate engine does not read yet. Unifying them is an open qr_frontend task.
