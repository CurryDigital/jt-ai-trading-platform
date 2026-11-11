// Command home — Portfolio Command Center (v7.1 correction pass).
// Analytical front page supporting three inspection speeds:
//   5s  — ROW 0 status header + ROW 1 book overview (Performance with a
//         VISIBLE curve, Exposure & Risk, Actions)
//   30s — ROW 2 explanation (per-strategy performance, P&L drivers)
//   2m  — ROW 3 investigation (full-width positions: filter, sort, group,
//         paginate) + ROW 4 activity dock (Orders | Fills | Signals |
//         Context — secondary; nothing analytical hides behind these tabs)
//
// A SIM | PAPER | UAT | LIVE selector in the status header scopes the ENTIRE
// page, persisted in the URL (?env=). EnvBook mounts with key={env} so
// switching remounts and refetches every section from the selected
// environment only — never mixed, never relabeled; unsupported data renders
// an explicit no-data state.
//
// v7.1 corrections (layout frozen — no redesign):
//   1. Risk terminology — the SIM/PAPER curve is cumulative REALIZED P&L, so
//      its drawdown is labeled "Realized P&L drawdown · YTD", never "Max
//      drawdown"; only LIVE draws down a genuine equity series.
//   2. Per-strategy realized P&L comes from the authoritative full-ledger
//      aggregate /api/execution/strategy-pnl (SQL GROUP BY, no row cap) —
//      the old /trades?limit=500 page aggregation silently under-reported
//      books over 500 trades. Σ per-strategy is reconciled against
//      book-overview stats.cum_pnl and shown in the panel header.
//   3. Financial bases — native/base currency, realized/unrealized and
//      period on every figure; PAPER cash labeled "Estimated cash"
//      (equity × cash_pct derivation); mixed currencies are never summed
//      (per-currency segments only); contribution percentages are suppressed
//      when the book total is zero/negative/near-zero (signed currency
//      contribution shown instead).
//   4. Readability only — larger section headings and primary labels,
//      higher-contrast microtext, top-5 allocation bars plus "Other".
//   5. Actions ordered critical alerts → execution/monitoring issues →
//      working orders → recent activity, absolute timestamps everywhere;
//      strategies sorted by absolute P&L/exposure, split active holdings vs
//      historical/closed, each linked to its strategy detail page.
//   6. Engineering — the monolith is split into focused components under
//      components/command/ with pure, unit-tested aggregation/currency
//      utilities in aggregate.js.
//
// Typography: primary P&L 30px tabular mono; secondary KPIs 18px; body/table
// 13px; labels 11px uppercase. Palette: colour carries meaning only —
// rose = critical, emerald/rose text = signed values (pnlCl), blue = links,
// everything else neutral slate/white. Bars are neutral slate.

import React, { useState, useEffect } from 'react';
import { useParams, useSearchParams } from 'react-router-dom';
import { api, usePoll } from '../../utils';
import { ENVS } from './meta';
import { StatusBar } from './StatusBar';
import { EnvBook } from './EnvBook';

// Environment lives in the URL (?env=sim|paper|uat|live), restored on
// reload; absent the param the route mode seeds the default
// (/sim/command → SIM).
export const CommandCenter = ({ navigateToTab, onSelectStrategy }) => {
  const { mode } = useParams();
  const [searchParams, setSearchParams] = useSearchParams();
  const rawEnv = (searchParams.get('env') || '').toLowerCase();
  const routeEnv = ENVS.includes((mode || '').toLowerCase()) ? mode.toLowerCase() : null;
  const env = ENVS.includes(rawEnv) ? rawEnv : (routeEnv || 'paper');
  const setEnv = (e) => {
    const next = new URLSearchParams(searchParams);
    next.set('env', e);
    setSearchParams(next, { replace: true });
  };

  const [limits, setLimits] = useState(null);
  const [sess, setSess] = useState(null); // { env, res } — env-tagged
  const [dataAsOf, setDataAsOf] = useState(null);
  const [regimeFc, setRegimeFc] = useState(null);
  const [regimeChg, setRegimeChg] = useState(null);
  const [stratNames, setStratNames] = useState({});

  usePoll(async () => {
    const res = await api.get('/api/execution/limits');
    if (res) setLimits(res);
  }, 60000, 3000);

  // Session status for the ACTIVE environment only.
  useEffect(() => {
    let cancelled = false;
    const load = async () => {
      let res = null;
      if (env === 'uat') res = await api.get('/api/ib/tws/uat/status');
      else if (env === 'live') res = await api.get('/api/execution/gateway');
      else if (env === 'paper') res = await api.get('/api/agents/paper/system-status');
      if (!cancelled) setSess({ env, res });
    };
    load();
    const id = setInterval(load, 60000);
    return () => { cancelled = true; clearInterval(id); };
  }, [env]);

  // strategy_id → display name map (used by every environment for labels).
  useEffect(() => {
    let cancelled = false;
    const t = setTimeout(() => {
      api.get('/api/paper-strategies').then(res => {
        const rows = Array.isArray(res) ? res : (res?.strategies || res?.data || []);
        if (!cancelled && Array.isArray(rows)) {
          const map = {};
          for (const r of rows) if (r.strategy_id && r.strategy_name) map[r.strategy_id] = r.strategy_name;
          setStratNames(map);
        }
      });
    }, 6000);
    return () => { cancelled = true; clearTimeout(t); };
  }, []);

  // Market context (environment-agnostic, dock Context tab).
  usePoll(async () => {
    const res = await api.get('/api/command/regime-forecast');
    if (res) setRegimeFc(res.markets || {});
  }, 300000, 6000);

  usePoll(async () => {
    const res = await api.get('/api/command/regime-change');
    if (res) setRegimeChg(res.regions || {});
  }, 300000, 6500);

  return (
    <div className="space-y-4">
      {/* ROW 0 — status header (env selector, HALT, session, freshness, clocks) */}
      <StatusBar env={env} onEnv={setEnv} limits={limits} sess={sess} dataAsOf={dataAsOf} />

      {/* ROWS 1–4 — environment-scoped analytical workspace. key={env}
          remounts on switch so every section refetches from the selected
          environment and no stale figure can linger. */}
      <EnvBook key={env} env={env} limits={limits} stratNames={stratNames}
        onDataAsOf={setDataAsOf} regimeFc={regimeFc} regimeChg={regimeChg}
        navigateToTab={navigateToTab} onSelectStrategy={onSelectStrategy} />
    </div>
  );
};

export default CommandCenter;
