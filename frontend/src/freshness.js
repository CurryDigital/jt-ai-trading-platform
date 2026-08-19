// Per-source freshness model — Command page P0-1.
//
// Backend: GET /api/system/freshness → rows from gold.v_source_freshness
// (qr_etl-owned). Every row carries its own staleness budget
// (max_staleness_h) so thresholds stay per-source and config-driven in the
// DB — the UI only applies the state ratios below.
//
// States (rank = severity, worst wins on propagation):
//   FRESH        normal render
//   LAGGING      past half the staleness budget — warn timestamp
//   UNKNOWN      source row absent from the registry — never assume fresh
//   STALE        past the budget — numbers desaturate + hatch overlay
//   DISCONNECTED never refreshed — numbers masked, last-known footer

import { useState, useEffect } from 'react';
import { api, usePoll } from './utils';

export const FR = { FRESH: 0, LAGGING: 1, UNKNOWN: 2, STALE: 3, DISCONNECTED: 4 };
export const FR_NAME = ['FRESH', 'LAGGING', 'UNKNOWN', 'STALE', 'DISCONNECTED'];

// LAGGING begins past this fraction of the per-source budget. UI-level
// policy constant; the budgets themselves come from the registry.
const LAG_FRACTION = 0.5;

// Dev-only freshness override — makes degraded states reachable for review
// and screenshot capture without waiting for a real outage.
//   ?fresh_override=ibkr:stale            force one source
//   ?fresh_override=ibkr:disconnected,attention_items:stale
// Honored ONLY on localhost or when localStorage['command.freshnessDebug']='1'
// is set — inert for normal viewers of the production site. Display-only:
// it never touches data, only this client's classification.
const OVERRIDE = (() => {
  try {
    const isLocal = ['localhost', '127.0.0.1'].includes(window.location.hostname);
    const debugOn = window.localStorage?.getItem('command.freshnessDebug') === '1';
    if (!isLocal && !debugOn) return null;
    const q = new URLSearchParams(window.location.search).get('fresh_override');
    if (!q) return null;
    const map = {};
    for (const pair of q.split(',')) {
      const [name, state] = pair.split(':').map(s => s && s.trim());
      const idx = FR_NAME.indexOf((state || '').toUpperCase());
      if (name && idx >= 0) map[name] = idx;
    }
    return Object.keys(map).length ? map : null;
  } catch { return null; }
})();

// Source → panel dependency map. Panels are NEVER tagged by hand; they
// inherit the worst state of their upstream sources from this map.
// ibkr staleness deliberately propagates to the book, exposures and the
// paper book by asset class (mark-to-market prices come from the ibkr feed).
export const PANEL_SOURCES = {
  market:         ['consumption:market_overview', 'market_breadth', 'market_movers', 'market_sentiment', 'bronze:ingest_vix'],
  myBook:         ['ibkr', 'consumption:build_account_summary', 'gold:build_account_nav_daily', 'gold:promote_ibkr', 'ib_gateway_state'],
  paperBookAsset: ['ibkr', 'consumption:portfolio_positions_risk', 'gold:refresh_paper_trades_synthetic'],
  monthlyPnl:     ['gold:refresh_paper_trades_synthetic', 'consumption:portfolio_performance_attribution'],
  paperBookMonth: ['gold:refresh_paper_trades_synthetic'],
  strategyRisks:  ['gold:refresh_paper_trades_synthetic', 'consumption:performance_strategy_results'],
  platform:       ['attention_items'],
  regime:         ['market_sentiment', 'regime_forecast', 'gold:gold_builder'],
};
// Merged Command attention panel inherits from both alert feeds.
PANEL_SOURCES.attention = [...PANEL_SOURCES.strategyRisks, ...PANEL_SOURCES.platform];

export function classifySource(row, name) {
  const srcName = name ?? row?.source;
  if (OVERRIDE && srcName && OVERRIDE[srcName] != null) {
    const state = OVERRIDE[srcName];
    const ageSec = row?.last_refreshed_at
      ? Math.max(0, (Date.now() - new Date(row.last_refreshed_at).getTime()) / 1000)
      : null;
    return { state, ageSec, budgetH: row?.max_staleness_h ?? null, row, overridden: true };
  }
  if (!row) return { state: FR.UNKNOWN, ageSec: null, budgetH: null };
  const budgetH = row.max_staleness_h ?? null;
  if (!row.last_refreshed_at) return { state: FR.DISCONNECTED, ageSec: null, budgetH, row };
  const ageSec = Math.max(0, (Date.now() - new Date(row.last_refreshed_at).getTime()) / 1000);
  const staleH = row.staleness_h ?? ageSec / 3600;
  if (budgetH == null) {
    // No configured budget — fall back to the registry's own verdict.
    const s = row.registry_status === 'never_refreshed' ? FR.DISCONNECTED
      : row.registry_status === 'stale' ? FR.STALE : FR.FRESH;
    return { state: s, ageSec, budgetH, row };
  }
  if (staleH > budgetH) return { state: FR.STALE, ageSec, budgetH, row };
  if (staleH > budgetH * LAG_FRACTION) return { state: FR.LAGGING, ageSec, budgetH, row };
  return { state: FR.FRESH, ageSec, budgetH, row };
}

// Worst state across a list of source names; returns the offending source so
// panels can say WHICH feed is holding them back, plus the oldest known age
// (the panel's "as-of").
export function panelFreshness(sourceNames, registry) {
  let state = FR.FRESH, culprit = null, asOfSec = null;
  for (const name of sourceNames) {
    const c = classifySource(registry ? registry[name] : null, name);
    if (c.state > state) { state = c.state; culprit = { name, ...c }; }
    if (c.ageSec != null && (asOfSec == null || c.ageSec > asOfSec)) asOfSec = c.ageSec;
  }
  return { state, culprit, asOfSec };
}

// Shared registry hook. Polls the freshness endpoint and re-ticks every 30s
// so relative ages ("14s", "22m") advance between polls.
export function useFreshness(pollMs = 60000) {
  const [registry, setRegistry] = useState(null); // null = registry itself UNKNOWN
  const [, setTick] = useState(0);

  usePoll(async () => {
    const res = await api.get('/api/system/freshness');
    if (res && Array.isArray(res.sources)) {
      const m = {};
      for (const s of res.sources) m[s.source] = s;
      setRegistry(m);
    } else if (res && res.sources == null) {
      setRegistry({}); // endpoint answered but registry missing → all UNKNOWN
    }
  }, pollMs);

  useEffect(() => {
    const id = setInterval(() => setTick(t => t + 1), 30000);
    return () => clearInterval(id);
  }, []);

  return registry;
}

export const fmtAgeSec = (ageSec) => {
  if (ageSec == null) return '—';
  const s = Math.floor(ageSec);
  if (s < 60) return `${s}s`;
  if (s < 3600) return `${Math.floor(s / 60)}m`;
  if (s < 86400) return `${Math.floor(s / 3600)}h`;
  return `${Math.floor(s / 86400)}d`;
};
