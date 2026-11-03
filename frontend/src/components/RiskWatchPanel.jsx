import React, { useEffect, useState } from 'react';
import { api, fmtAge, fmtK } from '../utils';

const fmtRule = (id, v) => {
  if (v == null) return '—';
  if (id === 'consecutive_losses') return v;
  if (id === 'min_live_pf') return Number(v).toFixed(2);
  return `${Number(v).toFixed(2)}%`;
};

// Calculation basis per rule, mirroring backend _evaluate_demote_rules
// (app/main.py). The API does not serve a basis field — these strings are
// display-only documentation of the served rule semantics and never alter
// the evaluation itself. {pool} = assigned capital from the registry.
const RULE_BASIS = {
  max_drawdown: (pool) => `Peak-to-trough of cumulative realized P&L as % of the ${pool} pool · closed trades only`,
  max_daily_loss: (pool) => `Worst single-day realized P&L as % of the ${pool} pool · grouped by exit/execution date`,
  consecutive_losses: () => 'Longest losing streak over the last 50 closed trades',
  min_live_pf: () => 'Gross win ÷ gross loss over the last 20 closed trades',
};

export const RiskWatchPanel = ({ strategyId, executionMode, onDemoted, title = 'Risk Watch', poolCapital = null }) => {
  const [status, setStatus] = useState(null);
  const [error, setError] = useState(false);
  const [refreshedAt, setRefreshedAt] = useState(null);
  const [busy, setBusy] = useState(false);

  const load = async () => {
    setError(false);
    const res = await api.get(`/api/strategies/${encodeURIComponent(strategyId)}/risk-status?t=${Date.now()}`);
    if (res) {
      setStatus(res);
      setError(false);
    } else {
      setError(true);
      setStatus(null);
    }
    setRefreshedAt(new Date().toISOString());
  };

  useEffect(() => {
    load();
    const id = setInterval(load, 30000);
    return () => clearInterval(id);
  }, [strategyId]);

  const forceCheck = async () => {
    setBusy(true);
    setError(false);
    const res = await api.post(`/api/strategies/${encodeURIComponent(strategyId)}/auto-demote-check`, {});
    setBusy(false);
    if (res?.demoted) onDemoted?.();
    if (res) {
      setStatus(res);
      setError(false);
    } else {
      setStatus(null);
      setError(true);
    }
    setRefreshedAt(new Date().toISOString());
  };

  if (error) {
    return (
      <div className="qr-surface px-3 py-2.5">
        <div className="flex items-center justify-between gap-2 flex-wrap">
          <div className="text-[11px] text-rose-300">
            ⚠ Risk status unavailable · endpoint returned an error.
          </div>
          <button onClick={load} className="qr-btn-ghost">↻ Retry</button>
        </div>
      </div>
    );
  }

  if (!status) {
    return (
      <div className="qr-surface px-3 py-2.5 flex items-center gap-2 text-[11px] text-slate-500">
        <div className="w-3 h-3 border-2 border-slate-700 border-t-blue-500 rounded-full animate-spin" />
        Loading risk status…
      </div>
    );
  }

  const breached = status.breaches?.length || 0;
  const eligible = executionMode === 'LIVE_TRADING';
  const poolText = poolCapital != null ? fmtK(poolCapital) : 'assigned-capital';
  // The backend picks the ledger by deployment mode (see _evaluate_demote_rules).
  const sourceTable = status.execution_mode === 'LIVE' ? 'gold.trade_executions' : 'gold.paper_trades_synthetic';

  return (
    <div className="qr-surface overflow-hidden">
      <div className="px-3 py-2 border-b border-white/[0.05] flex items-center justify-between flex-wrap gap-2">
        <div className="flex items-center gap-2">
          <span className="qr-label">{title}</span>
          <span className={`qr-chip ${
            !eligible ? 'qr-chip-slate' :
            breached === 0 ? 'qr-chip-emerald' : 'qr-chip-rose'
          }`}>
            {!eligible ? 'NOT LIVE' : breached === 0 ? 'ALL OK' : `${breached} BREACH${breached > 1 ? 'ES' : ''}`}
          </span>
          {!eligible && <span className="text-[10px] text-slate-500">— rules only enforced in LIVE mode</span>}
        </div>
        <div className="flex items-center gap-2">
          <span className="qr-num text-[10px] text-slate-500" title={`Evaluated at ${refreshedAt || '—'} · the endpoint evaluates the rules on request`}>
            {status.trades_analyzed ?? '—'} trades · evaluated {fmtAge(refreshedAt)}
          </span>
          <button onClick={forceCheck} disabled={busy} className="qr-btn-ghost">
            {busy ? '…' : '↻ Check now'}
          </button>
        </div>
      </div>

      <div className="px-3 py-1.5 border-b border-white/[0.05] text-[9px] text-slate-600" title="Ledger the rules are evaluated against — picked by deployment mode">
        Calculation basis: closed trades · {sourceTable}
      </div>

      <div className="divide-y divide-white/[0.04]">
        {(status.rules || []).map(r => (
          <div key={r.id} className="px-3 py-1.5">
            <div className="flex items-center justify-between gap-2">
              <span className="text-[10px] text-slate-300 font-semibold" title={r.reason || undefined}>{r.label}</span>
              <span className={`qr-chip text-[9px] ${r.breach ? 'qr-chip-rose' : 'qr-chip-slate'}`}>{r.breach ? 'BREACH' : 'OK'}</span>
            </div>
            <div className="qr-num text-[10px] text-slate-400 mt-0.5">
              now <span className={r.breach ? 'text-rose-300 font-bold' : 'text-slate-200 font-semibold'}>{fmtRule(r.id, r.actual)}</span>
              <span className="text-slate-700 mx-1">·</span>
              limit <span className="text-slate-300">{fmtRule(r.id, r.threshold)}</span>
            </div>
            <div className="text-[9px] text-slate-600 mt-0.5">
              {RULE_BASIS[r.id] ? RULE_BASIS[r.id](poolText) : 'Calculation basis not documented for this rule'}
            </div>
            {r.breach && r.reason && (
              <div className="text-[9px] text-rose-300/80 mt-0.5">{r.reason}</div>
            )}
          </div>
        ))}
      </div>

      {breached > 0 && eligible && (
        <div className="m-3 text-[11px] text-rose-200 bg-rose-500/10 ring-1 ring-rose-500/25 rounded px-3 py-2">
          <span className="font-bold">⚠ Auto-demote pending.</span> The background scanner will demote this strategy to PAPER on its next pass (every ~5 min). Click <span className="text-white font-semibold">Check now</span> to demote immediately.
        </div>
      )}
    </div>
  );
};

export default RiskWatchPanel;
