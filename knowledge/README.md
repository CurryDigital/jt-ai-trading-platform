# JTCML Platform Knowledge Base

One file per UI tab/sub-tab. Each documents: what the page is for, the React
components behind it, every backend API it calls with the expected response
shape, the DB objects those APIs read, refresh cadence, and known gaps with
an owner (qr_frontend = FastAPI/React platform code, qr_etl = DB objects,
ingestion, refresh pipelines).

**How to use:** when a page shows empty/wrong data, open its file, find the
API involved, check the "Backing DB objects" column — if the object is
missing/stale it's a qr_etl task; if the response shape mismatches the
documented one it's a qr_frontend task. These files are the contract.

| File | Route | View component |
|---|---|---|
| [command.md](command.md) | `/{mode}/command` | `CommandCenter.jsx` |
| [research_macro.md](research_macro.md) | `/{mode}/research` › Macro | `MacroTab.jsx` |
| [research_signals.md](research_signals.md) | `/{mode}/research` › Signals | `SignalsTab.jsx` |
| [research_analytics.md](research_analytics.md) | `/{mode}/research` › Analytics | `AnalyticsTab.jsx` |
| [research_screener.md](research_screener.md) | `/{mode}/research` › Screener | `ResearchTab.jsx` |
| [strategies_lab.md](strategies_lab.md) | `/{mode}/strategies` › Lab | `StrategyLab.jsx` |
| [strategies_pipeline.md](strategies_pipeline.md) | `/{mode}/strategies` › Pipeline | `StrategiesWorkspace.jsx` |
| [strategies_performance.md](strategies_performance.md) | `/{mode}/strategies` › Performance | `StrategiesWorkspace.jsx` |
| [strategies_golden.md](strategies_golden.md) | `/{mode}/strategies` › Golden | `GoldenStrategies.jsx` |
| [execution_live.md](execution_live.md) | `/{mode}/execution` › Live | `PortfolioTab` (in `App.jsx`) |
| [execution_paper.md](execution_paper.md) | `/{mode}/execution` › Paper | `PaperStrategiesPage.jsx` |
| [execution_ops.md](execution_ops.md) | `/{mode}/execution` › Ops | `LiveOpsPanel.jsx` |
| [settings.md](settings.md) | `/{mode}/settings` | `SettingsTab.jsx` |

## Platform-wide conventions
- All list endpoints degrade to empty (`[]` / `{}` / `data_not_available`)
  via `safe_query()` when a backing DB object is missing — HTTP 200, never
  500. Empty panel = missing/empty DB object, not a crash.
- **Missing tables degrade; missing columns crash.** `safe_query()` only
  swallows `relation does not exist` — a renamed/absent column raises and
  the global handler blanks the whole response. Schema changes must match
  the documented column lists exactly.
- Percentages: `gold.strategy_registry` OOS fields store **fractions**
  (0.6792); UI-facing endpoints normalize to percent. New endpoints should
  return percents and say so.
- Polling: all frontend pollers use `usePoll` (pauses when tab hidden).
  Server-side TTL caches: `/api/markets/overview` 12s,
  `/api/strategies/researcher` 15s (`?fresh=1` bypasses).
- Full DDL for redesign objects: `DB_CHANGES_v2.md` (repo root).
