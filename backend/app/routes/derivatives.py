"""Derivatives vertical endpoints — contained namespace for options/futures
research, backtests, and execution books.

Containment contract (.hermes/plans/2026-10-01_060404-derivatives-tab.md):
- Own router, own /api/derivatives/* prefix. No edits to existing routers.
- Reads ONLY gold.derivatives_* (+ nothing else). Never touches
  gold.paper_trades*, gold.paper_uat_fills, gold.trade_executions,
  gold.manual_* — Sim/Paper/UAT/Live books and Command P&L aggregates are
  unaffected by anything here.
- Read-only: no order-placement endpoints in this phase.
- Honest-empty: tables that exist but have no rows return measured zeros /
  empty arrays; nothing is fabricated. Missing tables degrade via safe_query.

Data owners: registry = qr_research (t_736850c6), ledgers = qr_etl
(t_15d7e66a), futures contract marks = qr_etl (t_822b6365).
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timezone, date
from decimal import Decimal

from app.dependencies import get_db
from app.db.safe_query import safe_query, safe_query_one

router = APIRouter(prefix="/api/derivatives", tags=["derivatives"])

DERIV_BOOKS = ("deriv_sim", "deriv_paper")


def _now_iso():
    return datetime.now(timezone.utc).isoformat()


def _num(v):
    if v is None:
        return None
    if isinstance(v, Decimal):
        return float(v)
    if isinstance(v, (int, float)):
        return v
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _iso(v):
    if v is None:
        return None
    if isinstance(v, (datetime, date)):
        return v.isoformat()
    return str(v)


def _check_book(book: str) -> str:
    if book not in ("all",) + DERIV_BOOKS:
        raise HTTPException(
            status_code=400,
            detail=f"book must be one of all, {', '.join(DERIV_BOOKS)}",
        )
    return book


# ---------------------------------------------------------------------------
# Research registry
# ---------------------------------------------------------------------------

@router.get("/strategies")
def get_derivative_strategies(db: Session = Depends(get_db)):
    """Derivatives research registry (gold.derivatives_strategies), enriched
    with the latest backtest run's OOS metrics per strategy (null until
    qr_etl's backtest ledger has rows)."""
    rows = safe_query(db, """
        SELECT s.strategy_id, s.name, s.instrument, s.venue, s.underlyings,
               s.thesis, s.entry_logic, s.exit_logic, s.status, s.phase,
               s.research_rank, s.expression_template, s.baseline_spec,
               s.max_loss_per_position_usd, s.max_pct_nav_at_risk, s.nav_basis,
               s.kill_conditions, s.data_blocker, s.source_doc,
               s.structure_params, s.risk_template,
               s.updated_at,
               r.run_id AS latest_run_id,
               r.sharpe_oos, r.returns_oos, r.win_rate_oos,
               r.max_drawdown_oos, r.trade_count_oos, r.profit_factor_oos,
               r.oos_start, r.oos_end
        FROM gold.derivatives_strategies s
        LEFT JOIN LATERAL (
            SELECT run_id, sharpe_oos, returns_oos, win_rate_oos,
                   max_drawdown_oos, trade_count_oos, profit_factor_oos,
                   oos_start, oos_end
            FROM gold.derivatives_backtest_runs r
            WHERE r.strategy_id = s.strategy_id
            ORDER BY r.created_at DESC
            LIMIT 1
        ) r ON TRUE
        ORDER BY s.research_rank ASC NULLS LAST, s.strategy_id
    """, label="derivatives.strategies")

    strategies = []
    counts = {"options": 0, "futures": 0, "us": 0, "hk": 0, "backtested": 0}
    for r in rows or []:
        has_run = r.latest_run_id is not None
        inst = (r.instrument or "").upper()
        ven = (r.venue or "").upper()
        if inst == "OPTION":
            counts["options"] += 1
        elif inst == "FUTURE":
            counts["futures"] += 1
        if ven == "US":
            counts["us"] += 1
        elif ven == "HK":
            counts["hk"] += 1
        if has_run:
            counts["backtested"] += 1
        strategies.append({
            "strategy_id": r.strategy_id,
            "name": r.name,
            "instrument": r.instrument,
            "venue": r.venue,
            "underlyings": list(r.underlyings) if r.underlyings else [],
            "thesis": r.thesis,
            "entry_logic": r.entry_logic,
            "exit_logic": r.exit_logic,
            "status": r.status,
            "phase": r.phase,
            "research_rank": r.research_rank,
            "expression_template": r.expression_template,
            "baseline_spec": r.baseline_spec,
            "max_loss_per_position_usd": _num(r.max_loss_per_position_usd),
            "max_pct_nav_at_risk": _num(r.max_pct_nav_at_risk),
            "nav_basis": r.nav_basis,
            "kill_conditions": list(r.kill_conditions) if r.kill_conditions else [],
            "data_blocker": r.data_blocker,
            "source_doc": r.source_doc,
            "updated_at": _iso(r.updated_at),
            # Latest-run OOS metrics — null until the backtest ledger lands.
            "latest_run_id": str(r.latest_run_id) if r.latest_run_id else None,
            "sharpe_oos": _num(r.sharpe_oos),
            "returns_oos": _num(r.returns_oos),
            "win_rate_oos": _num(r.win_rate_oos),
            "max_drawdown_oos": _num(r.max_drawdown_oos),
            "trade_count_oos": r.trade_count_oos,
            "profit_factor_oos": _num(r.profit_factor_oos),
            "oos_start": _iso(r.oos_start),
            "oos_end": _iso(r.oos_end),
        })

    return {
        "strategies": strategies,
        "count": len(strategies),
        "summary": {"total": len(strategies), **counts},
        "as_of": _now_iso(),
    }


# ---------------------------------------------------------------------------
# Backtests
# ---------------------------------------------------------------------------

def _run_row(r):
    return {
        "run_id": str(r.run_id),
        "strategy_id": r.strategy_id,
        "run_number": r.run_number,
        "instrument_type": r.instrument_type,
        "underlying": r.underlying,
        "venue": r.venue,
        "run_by": r.run_by,
        "is_start": _iso(r.is_start), "is_end": _iso(r.is_end),
        "oos_start": _iso(r.oos_start), "oos_end": _iso(r.oos_end),
        "sharpe_is": _num(r.sharpe_is), "returns_is": _num(r.returns_is),
        "max_drawdown_is": _num(r.max_drawdown_is),
        "trade_count_is": r.trade_count_is, "win_rate_is": _num(r.win_rate_is),
        "sharpe_oos": _num(r.sharpe_oos), "returns_oos": _num(r.returns_oos),
        "max_drawdown_oos": _num(r.max_drawdown_oos),
        "trade_count_oos": r.trade_count_oos, "win_rate_oos": _num(r.win_rate_oos),
        "cvar_95_oos": _num(r.cvar_95_oos),
        "profit_factor_oos": _num(r.profit_factor_oos),
        "all_risk_gates_passed": r.all_risk_gates_passed,
        "notes": r.notes,
        "created_at": _iso(r.created_at),
    }


@router.get("/backtests")
def get_derivative_backtests(db: Session = Depends(get_db)):
    """All derivative backtest runs + summary KPIs for the Backtest strip."""
    rows = safe_query(db, """
        SELECT * FROM gold.derivatives_backtest_runs
        ORDER BY created_at DESC
        LIMIT 500
    """, label="derivatives.backtests")

    runs = [_run_row(r) for r in rows or []]
    sharpes = [r["sharpe_oos"] for r in runs if r["sharpe_oos"] is not None]
    return {
        "runs": runs,
        "count": len(runs),
        "summary": {
            "runs": len(runs),
            "strategies": len({r["strategy_id"] for r in runs}),
            "latest_run": runs[0]["created_at"] if runs else None,
            "best_sharpe_oos": max(sharpes) if sharpes else None,
        },
        "as_of": _now_iso(),
    }


@router.get("/backtests/{run_id}")
def get_derivative_backtest_detail(run_id: str, db: Session = Depends(get_db)):
    """Per-run drill-down: run row, trade ledger, and views derived strictly
    from the ledger rows (cumulative realized P&L curve by exit date, annual
    P&L sums). No stored curve table exists yet — the derivation is labeled."""
    run = safe_query_one(db, """
        SELECT * FROM gold.derivatives_backtest_runs WHERE run_id = :rid
    """, {"rid": run_id}, label="derivatives.backtest_detail")
    if run is None:
        raise HTTPException(status_code=404, detail="run not found")

    trades = safe_query(db, """
        SELECT * FROM gold.derivatives_backtest_trades
        WHERE run_id = :rid
        ORDER BY entry_date NULLS LAST, id
        LIMIT 2000
    """, {"rid": run_id}, label="derivatives.backtest_trades")

    trade_rows = []
    for t in trades or []:
        trade_rows.append({
            "id": t.id,
            "strategy_id": t.strategy_id,
            "instrument_type": t.instrument_type,
            "underlying": t.underlying,
            "contract": t.contract,
            "option_right": t.option_right,
            "strike": _num(t.strike),
            "expiry": _iso(t.expiry),
            "side": t.side,
            "qty": _num(t.qty),
            "multiplier": _num(t.multiplier),
            "entry_date": _iso(t.entry_date),
            "entry_price": _num(t.entry_price),
            "exit_date": _iso(t.exit_date),
            "exit_price": _num(t.exit_price),
            "fees": _num(t.fees),
            "pnl": _num(t.pnl),
            "pnl_pct": _num(t.pnl_pct),
            "status": t.status,
        })

    # Derived views — computed only from the real trade rows above.
    closed = [t for t in trade_rows if t["exit_date"] and t["pnl"] is not None]
    closed.sort(key=lambda t: t["exit_date"])
    curve, cum = [], 0.0
    for t in closed:
        cum += t["pnl"]
        curve.append({"d": t["exit_date"], "cum_pnl": round(cum, 2)})
    annual = {}
    for t in closed:
        yr = t["exit_date"][:4]
        a = annual.setdefault(yr, {"year": yr, "pnl": 0.0, "trades": 0})
        a["pnl"] = round(a["pnl"] + t["pnl"], 2)
        a["trades"] += 1

    return {
        "run": _run_row(run),
        "trades": trade_rows,
        "trade_count": len(trade_rows),
        "curve": {"source": "derived_from_trades", "points": curve},
        "annual": {"source": "derived_from_trades", "years": sorted(annual.values(), key=lambda a: a["year"])},
        "as_of": _now_iso(),
    }


# ---------------------------------------------------------------------------
# Execution books (read-only)
# ---------------------------------------------------------------------------

@router.get("/positions")
def get_derivative_positions(book: str = "all", db: Session = Depends(get_db)):
    """Open derivative positions per book + summary KPIs for the Execution
    strip. Marks/unrealized come from the ledger as recorded by qr_etl —
    futures contract marks are pending t_822b6365 (null until then)."""
    book = _check_book(book)
    where = "WHERE book = :book" if book != "all" else ""
    params = {"book": book} if book != "all" else {}

    rows = safe_query(db, f"""
        SELECT * FROM gold.derivatives_positions
        {where}
        ORDER BY as_of DESC NULLS LAST, id
        LIMIT 1000
    """, params, label="derivatives.positions")

    positions = []
    for p in rows or []:
        positions.append({
            "id": p.id,
            "book": p.book,
            "strategy_id": p.strategy_id,
            "instrument_type": p.instrument_type,
            "underlying": p.underlying,
            "contract": p.contract,
            "option_right": p.option_right,
            "strike": _num(p.strike),
            "expiry": _iso(p.expiry),
            "exchange": p.exchange,
            "currency": p.currency,
            "qty": _num(p.qty),
            "avg_cost": _num(p.avg_cost),
            "market_price": _num(p.market_price),
            "market_value": _num(p.market_value),
            "unrealized_pnl": _num(p.unrealized_pnl),
            "realized_pnl": _num(p.realized_pnl),
            "as_of": _iso(p.as_of),
        })

    gross_vals = [abs(p["market_value"]) for p in positions if p["market_value"] is not None]
    unl_vals = [p["unrealized_pnl"] for p in positions if p["unrealized_pnl"] is not None]

    year_start = date(datetime.now(timezone.utc).year, 1, 1).isoformat()
    realized_row = safe_query_one(db, f"""
        SELECT SUM(realized_pnl) AS realized_ytd
        FROM gold.derivatives_positions
        {where} {"AND" if where else "WHERE"} as_of >= CAST(:year_start AS timestamptz)
          AND realized_pnl IS NOT NULL
    """, {**params, "year_start": year_start}, label="derivatives.positions.realized_ytd")
    realized_ytd = _num(realized_row.realized_ytd) if realized_row else None

    fills_today_row = safe_query_one(db, f"""
        SELECT COUNT(*) AS n FROM gold.derivatives_fills
        {where} {"AND" if where else "WHERE"} fill_time >= CAST(date_trunc('day', now() AT TIME ZONE 'UTC') AS timestamptz)
    """, params, label="derivatives.fills_today")
    fills_today = int(fills_today_row.n) if fills_today_row else 0

    return {
        "book": book,
        "positions": positions,
        "count": len(positions),
        "summary": {
            "open": len(positions),
            # null (not $0) when there is nothing to sum — no open rows or no marks.
            "gross_notional": round(sum(gross_vals), 2) if gross_vals else None,
            "unrealized_pnl": round(sum(unl_vals), 2) if unl_vals else None,
            "unrealized_unscored": len(positions) - len(unl_vals),
            "realized_ytd": realized_ytd,
            "fills_today": fills_today,
        },
        "marks_note": "Futures contract-month marks pending qr_etl t_822b6365 (Databento ingest); null marks render unscored.",
        "as_of": _now_iso(),
    }


@router.get("/fills")
def get_derivative_fills(book: str = "all", limit: int = 200, db: Session = Depends(get_db)):
    """Derivative fill blotter per book (gold.derivatives_fills)."""
    book = _check_book(book)
    limit = max(1, min(limit, 1000))
    where = "WHERE book = :book" if book != "all" else ""
    params = {"book": book, "lim": limit} if book != "all" else {"lim": limit}

    rows = safe_query(db, f"""
        SELECT * FROM gold.derivatives_fills
        {where}
        ORDER BY fill_time DESC NULLS LAST, id DESC
        LIMIT :lim
    """, params, label="derivatives.fills")

    fills = []
    for f in rows or []:
        fills.append({
            "id": f.id,
            "book": f.book,
            "exec_id": f.exec_id,
            "strategy_id": f.strategy_id,
            "instrument_type": f.instrument_type,
            "underlying": f.underlying,
            "contract": f.contract,
            "option_right": f.option_right,
            "strike": _num(f.strike),
            "expiry": _iso(f.expiry),
            "side": f.side,
            "qty": _num(f.qty),
            "price": _num(f.price),
            "multiplier": _num(f.multiplier),
            "currency": f.currency,
            "fill_time": _iso(f.fill_time),
        })

    return {"book": book, "fills": fills, "count": len(fills), "as_of": _now_iso()}


# ---------------------------------------------------------------------------
# Tab-level aggregate (kanban t_d67907e4 scope item 4)
# ---------------------------------------------------------------------------

def _table_exists(db, name):
    row = safe_query_one(db, "SELECT to_regclass(:n) AS t", {"n": name},
                         label=f"derivatives.probe.{name}")
    return bool(row and row.t)


@router.get("/overview")
def get_derivatives_overview(db: Session = Depends(get_db)):
    """KPI aggregate for the Derivatives tab headers.

    status: ok (rows exist) / empty (tables exist, 0 rows) / pending (a
    table is missing). Absent aggregates are null — never fabricated zeros.
    Round-trip realized YTD is NOT derived from fills serve-time (same rule
    as UAT; that ledger is qr_etl's domain), so it stays null until an
    owning ETL job lands it.
    """
    tables = {
        "strategies": _table_exists(db, "gold.derivatives_strategies"),
        "backtest_runs": _table_exists(db, "gold.derivatives_backtest_runs"),
        "positions": _table_exists(db, "gold.derivatives_positions"),
        "fills": _table_exists(db, "gold.derivatives_fills"),
    }

    strat_row = safe_query_one(db, """
        SELECT COUNT(*) AS n,
               COUNT(*) FILTER (WHERE instrument = 'OPTION') AS options,
               COUNT(*) FILTER (WHERE instrument = 'FUTURE') AS futures,
               COUNT(*) FILTER (WHERE venue = 'US') AS us,
               COUNT(*) FILTER (WHERE venue = 'HK') AS hk
        FROM gold.derivatives_strategies
    """, label="derivatives.overview.strategies") if tables["strategies"] else None

    run_row = safe_query_one(db, """
        SELECT COUNT(*) AS runs,
               COUNT(DISTINCT strategy_id) AS strategies,
               MAX(created_at) AS latest_run,
               MAX(sharpe_oos) AS best_sharpe_oos
        FROM gold.derivatives_backtest_runs
    """, label="derivatives.overview.runs") if tables["backtest_runs"] else None

    pos_row = safe_query_one(db, """
        SELECT COUNT(*) AS open,
               SUM(ABS(market_value)) AS gross_notional,
               SUM(unrealized_pnl) AS unrealized,
               SUM(realized_pnl) AS realized,
               MAX(as_of) AS as_of
        FROM gold.derivatives_positions
    """, label="derivatives.overview.positions") if tables["positions"] else None

    fills_today_row = safe_query_one(db, """
        SELECT COUNT(*) AS n FROM gold.derivatives_fills
        WHERE fill_time >= CAST(date_trunc('day', now() AT TIME ZONE 'UTC') AS timestamptz)
    """, label="derivatives.overview.fills_today") if tables["fills"] else None

    any_rows = any([
        strat_row and strat_row.n,
        run_row and run_row.runs,
        pos_row and pos_row.open,
    ])
    status = "ok" if any_rows else ("empty" if all(tables.values()) else "pending")

    return {
        "status": status,
        "tables": tables,
        "strategies": {
            "total": int(strat_row.n) if strat_row else None,
            "options": int(strat_row.options) if strat_row else None,
            "futures": int(strat_row.futures) if strat_row else None,
            "us": int(strat_row.us) if strat_row else None,
            "hk": int(strat_row.hk) if strat_row else None,
        },
        "backtests": {
            "runs": int(run_row.runs) if run_row else None,
            "strategies": int(run_row.strategies) if run_row else None,
            "latest_run": _iso(run_row.latest_run) if run_row else None,
            "best_sharpe_oos": _num(run_row.best_sharpe_oos) if run_row else None,
        },
        "positions": {
            "open": int(pos_row.open) if pos_row else None,
            "gross_notional": _num(pos_row.gross_notional) if pos_row else None,
            # null (not $0) when there are no rows / no marks.
            "unrealized": _num(pos_row.unrealized) if pos_row else None,
            "realized": _num(pos_row.realized) if pos_row else None,
            "realized_ytd": None,
            "as_of": _iso(pos_row.as_of) if pos_row else None,
        },
        "fills_today": int(fills_today_row.n) if fills_today_row else None,
        "as_of": _now_iso(),
    }
