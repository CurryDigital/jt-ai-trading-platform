"""Command Center endpoints — home-page aggregator + account equity curve.

New surfaces added by the JTCML workspace redesign (see design-bundle
handoff/API_SPEC_v2.md + DB_CHANGES_v2.md). All reads degrade to empty via
safe_query() until the underlying gold/consumption objects are materialized
by the qr_etl data-engineering process.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from app.dependencies import get_db, logger
from app.db.safe_query import safe_query, safe_query_one

router = APIRouter(prefix="/api", tags=["command"])


def _now_iso():
    return datetime.now(timezone.utc).isoformat()


@router.get("/command/overview")
def get_command_overview(db: Session = Depends(get_db)):
    """Single aggregator for the Command page: account, equity curve, pipeline, deployed health, attention queue."""
    account_row = safe_query_one(db, """
        SELECT equity, day_pnl, day_pnl_pct, open_pnl, buying_power, cash_pct,
               gross_exp_pct, net_exp_pct, positions
        FROM consumption.account_summary WHERE book = 'live'
    """, label="command_account_summary")

    account = None
    if account_row:
        m = account_row._mapping
        account = {
            "equity": float(m["equity"]) if m["equity"] is not None else None,
            "day_pnl": float(m["day_pnl"]) if m["day_pnl"] is not None else None,
            "day_pnl_pct": float(m["day_pnl_pct"]) if m["day_pnl_pct"] is not None else None,
            "buying_power": float(m["buying_power"]) if m["buying_power"] is not None else None,
            "cash_pct": float(m["cash_pct"]) if m["cash_pct"] is not None else None,
            "open_pnl": float(m["open_pnl"]) if m["open_pnl"] is not None else None,
            "gross_exp_pct": float(m["gross_exp_pct"]) if m["gross_exp_pct"] is not None else None,
            "net_exp_pct": float(m["net_exp_pct"]) if m["net_exp_pct"] is not None else None,
            "positions": int(m["positions"]) if m["positions"] is not None else None,
        }

    curve_rows = safe_query(db, """
        SELECT d, equity FROM consumption.account_equity_curve
        WHERE book = 'live' ORDER BY d DESC LIMIT 30
    """, label="command_equity_curve")
    equity_curve = [{"d": str(r.d), "equity": float(r.equity)} for r in reversed(curve_rows)]

    pipeline_row = safe_query_one(db, """
        SELECT
            COUNT(*) FILTER (WHERE priority = 'EXPERIMENTAL') AS experimental,
            COUNT(*) FILTER (WHERE priority = 'NEAR_GOLDEN') AS near_golden,
            COUNT(*) FILTER (WHERE priority = 'GOLDEN' AND approved_at IS NULL) AS golden,
            COUNT(*) FILTER (WHERE approved_at IS NOT NULL) AS deployed,
            COUNT(*) AS total
        FROM gold.strategy_registry WHERE status != 'DEPRECATED'
    """, label="command_pipeline_counts")
    pipeline = None
    if pipeline_row:
        m = pipeline_row._mapping
        pipeline = {k: int(m[k] or 0) for k in ["experimental", "near_golden", "golden", "deployed", "total"]}

    deployed_rows = safe_query(db, """
        SELECT strategy_id, name, asset_class AS asset, trade_count_oos AS live_trades,
               win_rate_oos AS live_win_rate, sharpe_oos
        FROM gold.strategy_registry
        WHERE approved_at IS NOT NULL AND status != 'DEPRECATED'
        ORDER BY sharpe_oos DESC NULLS LAST LIMIT 10
    """, label="command_deployed_health")
    deployed_health = [{
        "strategy_id": r.strategy_id, "name": r.name, "asset": r.asset,
        "live_trades": r.live_trades, "live_win_rate": float(r.live_win_rate) if r.live_win_rate is not None else None,
        "return_pct": float(r.sharpe_oos) if r.sharpe_oos is not None else None,
    } for r in deployed_rows]

    attention_rows = safe_query(db, """
        SELECT item_id, severity AS sev, tag, title, impact, target, ref_id, created_at
        FROM consumption.attention_queue
        ORDER BY CASE severity WHEN 'critical' THEN 0 WHEN 'warning' THEN 1 ELSE 2 END, created_at DESC
        LIMIT 20
    """, label="command_attention_queue")
    attention = [{
        "sev": r.sev, "tag": r.tag, "title": r.title, "impact": r.impact,
        "target": r.target, "ref_id": r.ref_id,
        "created_at": r.created_at.isoformat() if r.created_at else None,
    } for r in attention_rows]

    return {
        "account": account,
        "equity_curve": equity_curve,
        "pipeline": pipeline,
        "deployed_health": deployed_health,
        "attention": attention,
        "as_of": _now_iso(),
    }


@router.get("/account/equity-curve")
def get_account_equity_curve(days: int = 30, book: str = "live", db: Session = Depends(get_db)):
    rows = safe_query(db, """
        SELECT d, equity FROM consumption.account_equity_curve
        WHERE book = :book ORDER BY d DESC LIMIT :days
    """, {"book": book, "days": days}, label="account_equity_curve")
    data = [{"d": str(r.d), "equity": float(r.equity)} for r in reversed(rows)]
    return {"data": data, "as_of": _now_iso() if data else None}
