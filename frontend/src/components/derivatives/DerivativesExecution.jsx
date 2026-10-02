import { useEffect, useState } from 'react';
import { api, fmtK, fmtNum, pnlCl } from '../../utils.js';
import {
  DerivPanel, DerivKpiStrip, DerivTable, DerivChipFilter,
  TASK_DERIV_LEDGERS, TASK_FUTURES_DATA,
} from './shared.jsx';

// Derivatives ▸ Execution — positions/fills for derivative strategies.
// Read-only by design: NO order placement here until explicitly approved.
// Phase 2 (2026-10-02, t_d67907e4): LIVE on GET /api/derivatives/positions
// and /api/derivatives/fills (gold.derivatives_positions / _fills, qr_etl
// t_15d7e66a). Both ledgers are live and honestly EMPTY — KPI strip shows
// measured zeros where countable and '—' where nothing exists to sum
// (null from the backend, never a fabricated $0). Separate ledgers — never
// gold.paper_trades* / trade_executions.

const POSITION_COLS = [
  { label: 'Contract', tip: 'Full contract id (e.g. option OCC symbol / futures contract month)', key: 'contract', cl: 'text-slate-200 font-mono' },
  { label: 'Strategy', tip: 'Originating derivative strategy — null = unattributed', key: 'strategy_id', cl: 'text-slate-400 font-mono' },
  { label: 'Book', tip: 'deriv_sim / deriv_paper — separate from the equity books', key: 'book' },
  { label: 'Side', tip: 'LONG (qty > 0) / SHORT (qty < 0)',
    render: r => r.qty == null ? null : (r.qty >= 0 ? 'LONG' : 'SHORT'),
    cl: r => r.qty == null ? 'text-slate-500' : (r.qty >= 0 ? 'text-emerald-400' : 'text-rose-400') },
  { label: 'Qty', tip: 'Contracts', render: r => fmtNum(r.qty, 0), cl: 'text-slate-300 font-mono' },
  { label: 'Entry', tip: 'Average cost (premium/price)', render: r => fmtNum(r.avg_cost), cl: 'text-slate-300 font-mono' },
  { label: 'Mark', tip: `Latest mark — futures contract-month marks depend on qr_etl ${TASK_FUTURES_DATA} (Databento ingest)`, render: r => fmtNum(r.market_price), cl: 'text-slate-300 font-mono' },
  { label: 'Unrealized', tip: 'Mark-to-market P&L — null marks render unscored (—), never $0',
    render: r => r.unrealized_pnl == null ? null : fmtK(r.unrealized_pnl),
    cl: r => pnlCl(r.unrealized_pnl) + ' font-mono' },
];

const FILL_COLS = [
  { label: 'Time', tip: 'Fill time (UTC)', render: r => r.fill_time ? `${String(r.fill_time).slice(0, 16).replace('T', ' ')}` : null, cl: 'text-slate-400 font-mono' },
  { label: 'Contract', tip: 'Full contract id', key: 'contract', cl: 'text-slate-200 font-mono' },
  { label: 'Side', tip: 'BUY / SELL', key: 'side',
    cl: r => r.side === 'BUY' ? 'text-emerald-400' : r.side === 'SELL' ? 'text-rose-400' : 'text-slate-300' },
  { label: 'Qty', tip: 'Contracts', render: r => fmtNum(r.qty, 0), cl: 'text-slate-300 font-mono' },
  { label: 'Price', tip: 'Fill price', render: r => fmtNum(r.price), cl: 'text-slate-300 font-mono' },
  { label: 'Strategy', tip: 'Originating derivative strategy (order_ref strat:<sid>) — null = unattributed', key: 'strategy_id', cl: 'text-slate-400 font-mono' },
];

// Book chip value -> API ?book= param ('all' = no filter).
const BOOKS = [
  { label: 'ALL', value: 'all' },
  { label: 'SIM', value: 'deriv_sim' },
  { label: 'PAPER', value: 'deriv_paper' },
];

export function DerivativesExecution() {
  const [book, setBook] = useState('all');
  const [pos, setPos] = useState(null);
  const [fills, setFills] = useState(null);
  const [posLoaded, setPosLoaded] = useState(false);
  const [fillsLoaded, setFillsLoaded] = useState(false);

  useEffect(() => {
    let dead = false;
    setPosLoaded(false);
    setFillsLoaded(false);
    const q = book === 'all' ? '' : `?book=${book}`;
    api.get(`/api/derivatives/positions${q}`).then(d => {
      if (dead) return;
      setPos(d && Array.isArray(d.positions) ? d : null);
      setPosLoaded(true);
    });
    api.get(`/api/derivatives/fills${q}`).then(d => {
      if (dead) return;
      setFills(d && Array.isArray(d.fills) ? d : null);
      setFillsLoaded(true);
    });
    return () => { dead = true; };
  }, [book]);

  const sum = pos?.summary || {};
  const posFailed = posLoaded && !pos;
  const fillsFailed = fillsLoaded && !fills;

  return (
    <div className="space-y-3">
      <div className="qr-surface px-3 py-2 text-[10px] text-slate-500">
        Read-only by design — no order placement for derivatives until explicitly approved.
        Derivatives positions live in their own ledgers and never feed the Sim / Paper / UAT / Live
        books or Command P&L aggregates.
      </div>

      <DerivChipFilter
        groups={[
          { label: 'Book', value: book, onChange: setBook, options: BOOKS },
        ]}
      />

      <DerivKpiStrip
        tiles={[
          { label: 'Open', tip: 'Open derivative positions (gold.derivatives_positions)', value: sum.open ?? null, sub: 'ledger live · empty' },
          { label: 'Gross notional', tip: 'Gross notional exposure across open positions (sum |market value|)', value: sum.gross_notional != null ? fmtK(sum.gross_notional) : null, sub: 'no open rows' },
          { label: 'Unrealized', tip: 'Open mark-to-market P&L — null when no marks, never $0', value: sum.unrealized_pnl != null ? fmtK(sum.unrealized_pnl) : null, cl: pnlCl(sum.unrealized_pnl), sub: sum.unrealized_unscored ? `${sum.unrealized_unscored} unscored` : 'no open rows' },
          { label: 'Realized YTD', tip: 'Current-year realized P&L — null when no closed trades (round-trip ledger is qr_etl domain)', value: sum.realized_ytd != null ? fmtK(sum.realized_ytd) : null, cl: pnlCl(sum.realized_ytd), sub: 'no closed trades' },
          { label: 'Fills today', tip: 'Fill count today (UTC, gold.derivatives_fills)', value: sum.fills_today ?? null, sub: 'ledger live · empty' },
        ]}
      />

      <DerivPanel
        title="Derivative Positions"
        endpoint={`GET /api/derivatives/positions${book === 'all' ? '' : `?book=${book}`}`}
        task={TASK_DERIV_LEDGERS}
        live={!!pos}
        failed={posFailed}
        note="Open positions per derivatives book. Futures marks additionally depend on the contract-month data build."
      >
        <DerivTable
          cols={POSITION_COLS}
          rows={pos?.positions || []}
          rowKey={r => r.id}
          empty={posFailed ? 'Feed unavailable — see badge tooltip.' : 'No derivative positions — the ledger is live and empty.'}
          sub={`Positions appear when a derivatives sync job populates gold.derivatives_positions · futures marks pending qr_etl ${TASK_FUTURES_DATA} (Databento).`}
        />
      </DerivPanel>

      <DerivPanel
        title="Derivative Fills"
        endpoint={`GET /api/derivatives/fills${book === 'all' ? '' : `?book=${book}`}`}
        task={TASK_DERIV_LEDGERS}
        live={!!fills}
        failed={fillsFailed}
        note="Fill blotter per derivatives book — gold.derivatives_fills."
      >
        <DerivTable
          cols={FILL_COLS}
          rows={fills?.fills || []}
          rowKey={r => r.id}
          empty={fillsFailed ? 'Feed unavailable — see badge tooltip.' : 'No derivative fills — the ledger is live and empty.'}
          sub="Fills appear when a derivatives execution sync populates gold.derivatives_fills."
        />
      </DerivPanel>
    </div>
  );
}
