# Frontend Modernization — Quant Researcher Edition

This release modernizes the JTCML platform UI specifically for **quant researchers**:
information-dense, keyboard-driven, and data-first.

---

## What changed

### 1. Workspace Ribbon (new)

A sticky strip below the navbar showing **at-a-glance**:

- **Market clocks** for HK / LON / NYC with live "open/closed" dots that pulse during trading hours
- **API latency** measurement (round-trip to `/api/system/health` every 15s)
- **Active mode** (SIM / PAPER / LIVE) with semantic color coding
- **Today's P&L**, win rate, total trades, and last refresh age

This replaces the pattern of redundant KPI cards on every screen — the ribbon is always visible, so individual screens can focus on their specific data.

### 2. Quant-density CSS tokens

New `qr-*` utility classes in `index.css` give every component a consistent dense look:

- `qr-num` — monospace, tabular-nums, right-aligned numeric column
- `qr-label` — tiny uppercase 9px slate-500 label
- `qr-surface` / `qr-surface-strong` — surface backgrounds with subtle borders
- `qr-row` / `qr-row-compact` — fixed 28px / 22px row heights
- `qr-chip-{emerald|rose|blue|amber|violet|slate}` — consistent badge palette
- `qr-btn-{primary|ghost|danger}` — compact buttons (~24px tall)
- `qr-kbd` — keyboard shortcut chips
- `qr-pnl-{pos|neg|nul}` — semantic P&L colors
- `qr-dot-{live|stale|down|idle}` — status indicator dots with pulsing animation

### 3. Keyboard navigation

Pressing **1–9** anywhere in the app switches tabs (when not in an input). Each tab pill in the navbar shows its number key on `lg:` screens.

| Key | Tab |
|-----|-----|
| `1` | Command |
| `2` | Lab |
| `3` | Strategies |
| `4` | Agents |
| `5` | Performance |
| `6` | Research |
| `7` | Portfolio |
| `8` | Markets |
| `9` | Settings |

### 4. Sortable tables

The `useSort()` hook + `SortableHeader` component make columns clickable for sorting in:

- **Portfolio tab** — sort by ticker, side, qty, entry, last, value, P&L $, P&L %
- **Performance tab** — sort by strategy name, asset class, BT WR, Live WR, Δ WR, BT PF, Live PF, trades, returns

### 5. Denser layout

The fixed header is now **40px** (down from ~56px) and the workspace ribbon adds 28px — same total height, but more useful information.

Card padding, font sizes, and spacing have all been tightened. KPI tiles now use:
- 11px qr-num font for big numbers (was 14px)
- 9px uppercase labels (was 10px)
- 12px horizontal padding (was 16px)

The `max-w-[1600px]` content region has been widened to `max-w-[1800px]` to give quant researchers more horizontal real estate for tables.

### 6. Typography

- Default body font size dropped to 13px
- All tables use `tabular-nums` and `font-feature-settings: "tnum" 1, "zero" 1` so numeric columns stay perfectly aligned

### 7. Backend `/api/system/health` endpoint

A new lightweight endpoint that returns:

```json
{
  "status": "healthy",
  "latency_ms": 12,
  "ts": "2026-05-02T12:34:56Z",
  "counts": { "strategies": 42, "deployed": 8, "assets": 312 },
  "pipeline": { "golden": 3, "near_golden": 5, "experimental": 12 },
  "version": "v1"
}
```

Used by:
- The workspace ribbon (DB latency badge)
- The Command Center DB Latency KPI tile

---

## Files changed

| File | Change |
|------|--------|
| `frontend/src/index.css` | +qr-* utility tokens, density CSS variables, pulse-dot animation |
| `frontend/src/utils.js` | +`fmtNum`, `fmtSigned`, `fmtBps`, `fmtTime`, `fmtAge`, `marketClock`, `marketStatus` |
| `frontend/src/App.jsx` | Full rewrite: WorkspaceRibbon, sortable tables, keyboard shortcuts, dense Command Center |
| `backend/app/main.py` | +`/api/system/health` endpoint |

## Files **not** changed but should be considered for future polish

- `frontend/src/components/GoldenStrategies.jsx` (1500 LOC, mature) — could use `qr-chip-*` tokens for consistency
- `frontend/src/components/AgenticResearch.jsx` (600 LOC) — pipeline visualization could move into a sticky bar
- `frontend/src/components/StrategyPerformance.jsx` (2300 LOC) — opportunity to apply density tokens
- `frontend/src/components/ResearchTab.jsx` — emoji-heavy section tabs could be replaced with stroke icons

---

## Quant researcher UX principles applied

1. **Information density over whitespace** — every pixel must earn its place
2. **Numbers are first-class** — monospace, right-aligned, tabular-nums
3. **Keyboard before mouse** — 1-9 for tab switching, sortable tables
4. **At-a-glance state** — workspace ribbon means you never lose track of mode/P&L/clock
5. **Semantic color** — green for buy/positive, red for sell/negative, amber for warn/near-golden, slate for idle/experimental
6. **Live signals** — status dots pulse during market hours; latency is visible
