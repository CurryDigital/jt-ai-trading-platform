import { useEffect, useState } from 'react';
import { api, fmtK, fmtNum, fmtTime, pnlCl } from '../../utils.js';
import {
  DerivPanel, DerivEmptyState, DerivKpiStrip, DerivTable,
  TASK_DERIV_LEDGERS,
} from './shared.jsx';

// Derivatives ▸ Backtest — backtest runs for derivative strategies.
// Phase 2 (2026-10-02, t_d67907e4): LIVE on GET /api/derivatives/backtests
// (gold.derivatives_backtest_runs, qr_etl t_15d7e66a). The ledger is live and
// honestly EMPTY (0 runs) — KPI strip shows measured zeros, '—' where no run
// exists. Run Detail fetches GET /api/derivatives/backtests/{run_id} when a
// run row is clicked — activates automatically once runs land.

const TRADE_COLS = [
  { label: 'Contract', tip: 'Full contract id', key: 'contract', cl: 'text-slate-200 font-mono' },
  { label: 'Side', tip: 'BUY / SELL', key: 'side',
    cl: r => r.side === 'BUY' ? 'text-emerald-400' : r.side === 'SELL' ? 'text-rose-400' : 'text-slate-300' },
  { label: 'Qty', tip: 'Contracts', render: r => fmtNum(r.qty, 0), cl: 'text-slate-300 font-mono' },
  { label: 'Entry', tip: 'Entry date · price', render: r => `${r.entry_date || '—'} @ ${fmtNum(r.entry_price)}`, cl: 'text-slate-300 font-mono' },
  { label: 'Exit', tip: 'Exit date · price', render: r => r.exit_date ? `${r.exit_date} @ ${fmtNum(r.exit_price)}` : null, cl: 'text-slate-300 font-mono' },
  { label: 'P&L', tip: 'Realized P&L ($, net of recorded fees)', render: r => r.pnl == null ? null : fmtK(r.pnl),
    cl: r => pnlCl(r.pnl) + ' font-mono' },
  { label: 'P&L %', tip: 'P&L % as recorded — unit contract pins with the first run', render: r => fmtNum(r.pnl_pct), cl: 'text-slate-300 font-mono' },
  { label: 'Status', tip: 'Trade status', key: 'status' },
];

// Cumulative realized P&L curve — derived_from_trades (labeled server-side).
function DerivCurve({ points }) {
  const clean = (points || []).filter(p => p.cum_pnl != null);
  if (clean.length < 2) {
    return <DerivEmptyState line="Not enough closed trades to draw a curve." sub="Curve derives from gold.derivatives_backtest_trades exit dates." />;
  }
  const w = 600, h = 140, padL = 48, padB = 18, padT = 8, padR = 8;
  const vals = clean.map(p => p.cum_pnl);
  const min = Math.min(...vals), max = Math.max(...vals), range = (max - min) || 1;
  const x = i => padL + (i / (clean.length - 1)) * (w - padL - padR);
  const y = v => padT + (1 - (v - min) / range) * (h - padT - padB);
  const pts = clean.map((p, i) => `${x(i)},${y(p.cum_pnl)}`).join(' ');
  const last = vals[vals.length - 1];
  const stroke = last >= 0 ? '#34d399' : '#fb7185';
  return (
    <svg viewBox={`0 0 ${w} ${h}`} className="w-full block" preserveAspectRatio="none" style={{ height: 140 }}>
      {[min, (min + max) / 2, max].map((v, i) => (
        <g key={i}>
          <line x1={padL} y1={y(v)} x2={w - padR} y2={y(v)} stroke="rgba(255,255,255,0.08)" strokeWidth="1" />
          <text x={4} y={y(v) + 3} fontSize="8" fontFamily="ui-monospace, monospace" fill="#94a3b8" opacity="0.8">{fmtK(v)}</text>
        </g>
      ))}
      <polyline points={pts} fill="none" stroke={stroke} strokeWidth="1.5" strokeLinejoin="round" strokeLinecap="round" />
      <text x={padL} y={h - 4} fontSize="8" fontFamily="ui-monospace, monospace" fill="#64748b">{clean[0].d}</text>
      <text x={w - padR} y={h - 4} fontSize="8" fontFamily="ui-monospace, monospace" fill="#64748b" textAnchor="end">{clean[clean.length - 1].d}</text>
    </svg>
  );
}

export function DerivativesBacktest() {
  const [data, setData] = useState(null);
  const [loaded, setLoaded] = useState(false);
  const [selRun, setSelRun] = useState(null);
  const [detail, setDetail] = useState(null);
  const [detailFailed, setDetailFailed] = useState(false);

  useEffect(() => {
    let dead = false;
    api.get('/api/derivatives/backtests').then(d => {
      if (dead) return;
      setData(d && Array.isArray(d.runs) ? d : null);
      setLoaded(true);
    });
    return () => { dead = true; };
  }, []);

  useEffect(() => {
    if (!selRun) { setDetail(null); return; }
    let dead = false;
    setDetail(null);
    setDetailFailed(false);
    api.get(`/api/derivatives/backtests/${selRun}`).then(d => {
      if (dead) return;
      if (d && d.run && Array.isArray(d.trades)) setDetail(d);
      else setDetailFailed(true);
    });
    return () => { dead = true; };
  }, [selRun]);

  const sum = data?.summary || {};
  const failed = loaded && !data;

  return (
    <div className="space-y-3">
      <DerivKpiStrip
        tiles={[
          { label: 'Runs', tip: 'Total derivative backtest runs (gold.derivatives_backtest_runs)', value: sum.runs ?? null, sub: 'ledger live · empty' },
          { label: 'Strategies', tip: 'Strategies with at least one run', value: sum.strategies ?? null, sub: 'ledger live · empty' },
          { label: 'Latest run', tip: 'Most recent run date', value: sum.latest_run ? String(sum.latest_run).slice(0, 10) : null, sub: 'no runs yet' },
          { label: 'Best Sharpe OOS', tip: 'Best out-of-sample Sharpe across runs', value: sum.best_sharpe_oos != null ? fmtNum(sum.best_sharpe_oos) : null, sub: 'no runs yet' },
        ]}
      />

      <DerivPanel
        title="Backtest Runs"
        endpoint="GET /api/derivatives/backtests"
        task={TASK_DERIV_LEDGERS}
        live={!!data}
        failed={failed}
        note="Backtest results for derivative strategies — separate tables from equity strategy backtests, so existing performance views are unaffected. Click a run for drill-down."
      >
        <DerivTable
          cols={RUN_COLS}
          rows={data?.runs || []}
          rowKey={r => r.run_id}
          onRowClick={r => setSelRun(r.run_id)}
          selectedId={selRun}
          empty={failed ? 'Feed unavailable — see badge tooltip.' : 'No backtest runs yet — the ledger is live and empty.'}
          sub="Runs appear here when qr_research executes the first derivatives backtest into gold.derivatives_backtest_runs."
        />
      </DerivPanel>

      <DerivPanel
        title="Run Detail"
        endpoint="GET /api/derivatives/backtests/{run_id}"
        task={TASK_DERIV_LEDGERS}
        live={!!detail}
        failed={detailFailed}
        note={detail
          ? `${detail.run.strategy_id} · OOS ${detail.run.oos_start || '—'}→${detail.run.oos_end || '—'} · ${detail.trade_count} trades · risk gates ${detail.run.all_risk_gates_passed == null ? '—' : detail.run.all_risk_gates_passed ? 'PASSED' : 'FAILED'}`
          : 'Per-run drill-down — activates when a run is selected above.'}
      >
        {!detail ? (
          <div className="grid grid-cols-1 xl:grid-cols-2 gap-3">
            <DerivEmptyState
              line={detailFailed ? 'Detail feed unavailable — see badge tooltip.' : 'Equity curve renders here once a run is selected.'}
              sub="Cumulative realized P&L curve derived from gold.derivatives_backtest_trades (labelled derived_from_trades)."
            />
            <DerivEmptyState
              line={detailFailed ? 'Detail feed unavailable — see badge tooltip.' : 'Annual returns + trade ledger render here.'}
              sub="Per-year sums and round-trip ledger from gold.derivatives_backtest_trades."
            />
          </div>
        ) : (
          <div className="space-y-3">
            <div className="grid grid-cols-1 xl:grid-cols-2 gap-3">
              <div>
                <div className="qr-label mb-1">Cumulative realized P&L · derived from trades</div>
                <DerivCurve points={detail.curve?.points} />
              </div>
              <div>
                <div className="qr-label mb-1">Annual P&L · derived from trades</div>
                {(detail.annual?.years || []).length === 0 ? (
                  <DerivEmptyState line="No closed-trade years yet." />
                ) : (
                  <div className="space-y-1">
                    {detail.annual.years.map(y => (
                      <div key={y.year} className="flex items-center gap-2 text-[11px]">
                        <span className="w-10 font-mono text-slate-400">{y.year}</span>
                        <span className={`font-mono font-bold ${pnlCl(y.pnl)}`}>{fmtK(y.pnl)}</span>
                        <span className="text-[9px] text-slate-500">{y.trades} trades</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
            <DerivTable
              cols={TRADE_COLS}
              rows={detail.trades}
              rowKey={r => r.id}
              empty="No trade rows recorded for this run."
            />
          </div>
        )}
      </DerivPanel>
    </div>
  );
}

const RUN_COLS = [
  { label: 'Run date', tip: 'Backtest run timestamp (UTC)',
    render: r => r.created_at ? `${fmtTime(r.created_at)} ${String(r.created_at).slice(0, 10)}` : null, cl: 'text-slate-400 font-mono' },
  { label: 'Strategy', tip: 'Derivative strategy id', key: 'strategy_id', cl: 'text-slate-200 font-mono' },
  { label: 'Type', tip: 'OPTION / FUTURE', key: 'instrument_type' },
  { label: 'Window', tip: 'OOS span — bars honesty markers as in the equity Sim cards',
    render: r => r.oos_start && r.oos_end ? `OOS ${r.oos_start}→${r.oos_end}` : null, cl: 'text-slate-400 font-mono' },
  { label: 'Sharpe', tip: 'Out-of-sample Sharpe', render: r => fmtNum(r.sharpe_oos), cl: 'text-slate-300 font-mono' },
  { label: 'Return', tip: 'Out-of-sample return — per-field unit contract pins with the first run', render: r => fmtNum(r.returns_oos), cl: 'text-slate-300 font-mono' },
  { label: 'Win %', tip: 'Out-of-sample win rate', render: r => fmtNum(r.win_rate_oos), cl: 'text-slate-300 font-mono' },
  { label: 'MDD', tip: 'Out-of-sample max drawdown', render: r => fmtNum(r.max_drawdown_oos), cl: 'text-slate-300 font-mono' },
  { label: 'PF', tip: 'Profit factor', render: r => fmtNum(r.profit_factor_oos), cl: 'text-slate-300 font-mono' },
  { label: 'Trades', tip: 'Out-of-sample trade count', key: 'trade_count_oos', cl: 'text-slate-300 font-mono' },
];

