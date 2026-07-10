# Strategies › Golden

**Purpose:** the curated "golden book" operations view — deployed strategies
grouped with their capital pools, plus the Available list for deploying
research-validated strategies with custom capital allocation (multi-select
deploy, priority/status filters).

**Component:** `frontend/src/components/GoldenStrategies.jsx` — poll ~60s.

## APIs

### `GET /api/strategies/researcher` — Available list
Shared strategy book (see [strategies_lab.md](strategies_lab.md)); filter
pills use `priority` (GOLDEN / NEAR_GOLDEN / EXPERIMENTAL) and `status`.

### `GET /api/paper-strategies` — Deployed list
Deployed/paper strategies with positions, grouped per strategy. Backing:
`consumption.portfolio_positions_current` (+ registry join).

### `GET/POST /api/strategies/{id}/capital-pool`
Read/set a strategy's capital pool (slider + presets in the deploy card).

### `POST /api/strategies/deploy-with-pool`
`{ strategy_id, tickers[], total_pool }` — same endpoint as the Lab.

### `POST /api/strategies/{id}/mode` · `GET /api/execution/global-mode`
Legacy per-strategy mode toggle + global mode banner. Prefer the Pipeline's
gate-checked `/promote` flow for mode changes (this page's direct toggle
bypasses gates — see gap below).

## Known gaps
- **Two mode-change paths exist**: this page's direct `/strategies/{id}/mode`
  toggle (no gates) vs Pipeline's audited `/promote` (gates + phrase).
  Direct toggle should eventually be removed or routed through /promote.
  Owner: qr_frontend.
- Overlaps heavily with Lab (deploy) and Pipeline (mode) — candidate for
  consolidation once the workflows settle.
