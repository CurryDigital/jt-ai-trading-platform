"""
Agentic Research Routes (Hermes Agent Model)
============================================
Replaces the old openclaw_researcher 13-agent pipeline with 4 Hermes agents:
  qr_research, qr_etl, qr_qa, scrum_master

All data served from gold schema (strategy_research, backtest_runs, qa_reviews, etc.)
"""
import datetime
import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.db.session import SessionLocal
from app.services.agent_events import log_agent_event

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["agents"])

# ── Dependency ───────────────────────────────────────────────────────────

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ── Agent Registry (4 Hermes agents) ─────────────────────────────────────

AGENT_REGISTRY = {
    "qr_research": {
        "name": "Research",
        "icon": "🔍",
        "role": "Deep-dive market signals, academic research, and strategy ideation",
        "order": 1,
    },
    "qr_etl": {
        "name": "ETL",
        "icon": "🏭",
        "role": "Data pipelines — ingestion, cleaning, enrichment, and quality checks",
        "order": 2,
    },
    "qr_qa": {
        "name": "QA",
        "icon": "🚦",
        "role": "Quality assurance — tests strategy logic, validates backtests, gates deployment",
        "order": 3,
    },
    "scrum_master": {
        "name": "ScrumMaster",
        "icon": "📋",
        "role": "Orchestrates research pipeline, routes tasks, and manages kanban flow",
        "order": 4,
    },
}

# ── GET /api/agents ──────────────────────────────────────────────────────

@router.get("")
def get_agents():
    """List registered Hermes agents."""
    agents = []
    for agent_id, info in sorted(AGENT_REGISTRY.items(), key=lambda x: x[1]["order"]):
        agents.append({
            "agent_id": agent_id,
            "name": info["name"],
            "icon": info["icon"],
            "role": info["role"],
            "order": info["order"],
        })
    return {"agents": agents}

# ── GET /api/agents/workflow-summary ─────────────────────────────────────

@router.get("/workflow-summary")
def get_workflow_summary(db: Session = Depends(get_db)):
    """Aggregate workflow counts from gold.strategy_research."""
    try:
        rows = db.execute(text("""
            SELECT status, COUNT(*) AS cnt
            FROM gold.strategy_research
            GROUP BY status
        """)).fetchall()

        summary = {
            "total": 0,
            "pending": 0,
            "backtesting": 0,
            "risk_review": 0,
            "qa_review": 0,
            "approved": 0,
            "deployed": 0,
            "rejected": 0,
            "retired": 0,
            "golden": 0,
        }
        for r in rows:
            key = r.status.lower() if r.status else "unknown"
            if key in summary:
                summary[key] = int(r.cnt)
            summary["total"] += int(r.cnt)

        # Golden = approved + deployed
        summary["golden"] = summary["approved"] + summary["deployed"]

        return summary
    except Exception as e:
        logger.error(f"Workflow summary error: {e}")
        return {"total": 0, "error": str(e)}

# ── GET /api/agents/strategy-workflows ───────────────────────────────────

@router.get("/strategy-workflows")
def get_strategy_workflows(
    status: Optional[str] = None,
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
):
    """Strategy list with status, backtest count, and history."""
    try:
        query = """
            SELECT strategy_id, name, workflow_status, assigned_to,
                   workflow_result, event_count, latest_sharpe,
                   workflow_created, workflow_updated
            FROM gold.v_agent_workflows
            WHERE 1=1
        """
        params: dict = {}
        if status:
            query += " AND workflow_status = :status"
            params["status"] = status
        query += " ORDER BY workflow_updated DESC NULLS LAST LIMIT :limit"
        params["limit"] = limit

        rows = db.execute(text(query), params).fetchall()
        strategies = []
        for r in rows:
            strategies.append({
                "strategy_id": r.strategy_id,
                "name": r.name,
                "status": r.workflow_status,
                "assigned_to": r.assigned_to,
                "result": r.workflow_result,
                "event_count": r.event_count,
                "latest_sharpe": float(r.latest_sharpe) if r.latest_sharpe else None,
                "created_at": r.workflow_created.isoformat() if r.workflow_created else None,
                "updated_at": r.workflow_updated.isoformat() if r.workflow_updated else None,
            })
        return {"strategies": strategies, "count": len(strategies)}
    except Exception as e:
        logger.error(f"Strategy workflows error: {e}")
        return {"strategies": [], "count": 0}

# ── GET /api/agents/events ───────────────────────────────────────────────

@router.get("/events")
def get_agent_events(
    agent_id: Optional[str] = None,
    strategy_id: Optional[str] = None,
    domain: Optional[str] = None,
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
):
    """Agent event feed from gold.agent_events."""
    try:
        query = """
            SELECT id, event_type, strategy_id, domain,
                   agent_name, payload_json, status, created_at
            FROM gold.agent_events
            WHERE 1=1
        """
        params: dict = {}
        if agent_id:
            query += " AND agent_name = :agent_id"
            params["agent_id"] = agent_id
        if strategy_id:
            query += " AND strategy_id = :strategy_id"
            params["strategy_id"] = strategy_id
        if domain:
            query += " AND domain = :domain"
            params["domain"] = domain
        query += " ORDER BY created_at DESC LIMIT :limit"
        params["limit"] = limit

        rows = db.execute(text(query), params).fetchall()
        events = []
        for r in rows:
            agent_info = AGENT_REGISTRY.get(r.agent_name, {"name": r.agent_name, "icon": "🤖"})
            events.append({
                "id": str(r.id),
                "event_type": r.event_type,
                "strategy_id": r.strategy_id,
                "domain": r.domain,
                "agent_name": agent_info["name"],
                "agent_icon": agent_info["icon"],
                "payload": r.payload_json,
                "status": r.status,
                "timestamp": r.created_at.isoformat() if r.created_at else None,
            })
        return {"events": events, "count": len(events)}
    except Exception as e:
        logger.error(f"Agent events error: {e}")
        return {"events": [], "count": 0}

# ── GET /api/agents/pending-work ─────────────────────────────────────────

@router.get("/pending-work")
def get_pending_work(
    agent_id: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """Pending work items from gold.v_agent_pending_work."""
    try:
        query = """
            SELECT domain, target_agent, strategy_id, work_status,
                   strategy_name, created_at, updated_at
            FROM gold.v_agent_pending_work
            WHERE 1=1
        """
        params: dict = {}
        if agent_id:
            query += " AND target_agent = :agent_id"
            params["agent_id"] = agent_id
        query += " ORDER BY updated_at DESC NULLS LAST"

        rows = db.execute(text(query), params).fetchall()
        work_items = []
        for r in rows:
            agent_info = AGENT_REGISTRY.get(r.target_agent, {"name": r.target_agent, "icon": "🤖"})
            work_items.append({
                "domain": r.domain,
                "target_agent": r.target_agent,
                "target_agent_name": agent_info["name"],
                "target_agent_icon": agent_info["icon"],
                "strategy_id": r.strategy_id,
                "strategy_name": r.strategy_name,
                "work_status": r.work_status,
                "created_at": r.created_at.isoformat() if r.created_at else None,
                "updated_at": r.updated_at.isoformat() if r.updated_at else None,
            })

        by_agent: dict = {}
        for w in work_items:
            key = w["target_agent"]
            by_agent[key] = by_agent.get(key, 0) + 1

        return {"work_items": work_items, "count": len(work_items), "by_agent": by_agent}
    except Exception as e:
        logger.error(f"Pending work error: {e}")
        return {"work_items": [], "count": 0, "by_agent": {}}

# ── GET /api/agents/completed-work ───────────────────────────────────────

@router.get("/completed-work")
def get_completed_work(
    agent_id: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    """Completed work items from QA and Risk reviews."""
    try:
        query = """
            SELECT work_type, strategy_id, processed_by,
                   processing_status, conviction_score, processed_at
            FROM gold.v_agent_completed_work
            WHERE 1=1
        """
        params: dict = {}
        if agent_id:
            query += " AND processed_by = :agent_id"
            params["agent_id"] = agent_id
        if date_from:
            query += " AND processed_at >= :date_from"
            params["date_from"] = date_from
        if date_to:
            query += " AND processed_at < :date_to"
            params["date_to"] = date_to
        query += " ORDER BY processed_at DESC LIMIT :limit"
        params["limit"] = limit

        rows = db.execute(text(query), params).fetchall()
        completed = []
        for r in rows:
            agent_info = AGENT_REGISTRY.get(r.processed_by, {"name": r.processed_by, "icon": "🤖"})
            completed.append({
                "work_type": r.work_type,
                "strategy_id": r.strategy_id,
                "processed_by": r.processed_by,
                "processor_name": agent_info["name"],
                "processor_icon": agent_info["icon"],
                "processing_status": r.processing_status,
                "conviction_score": float(r.conviction_score) if r.conviction_score else None,
                "processed_at": r.processed_at.isoformat() if r.processed_at else None,
            })
        return {"completed_items": completed, "count": len(completed)}
    except Exception as e:
        logger.error(f"Completed work error: {e}")
        return {"completed_items": [], "count": 0}

# ── GET /api/agents/routing-rules ────────────────────────────────────────

@router.get("/routing-rules")
def get_routing_rules():
    """
    Routing rules are deprecated in the Hermes model.
    Returns empty — agents are managed via kanban, not event routing.
    """
    return {"rules": [], "count": 0, "note": "Routing rules deprecated. Use kanban task assignment."}

# ── GET /api/agents/strategy/{strategy_id} ───────────────────────────────

@router.get("/strategy/{strategy_id}")
def get_strategy_agent_detail(strategy_id: str, db: Session = Depends(get_db)):
    """Full strategy detail: research + backtests + qa reviews + risk reviews."""
    try:
        # Research / workflow state
        wf = db.execute(text("""
            SELECT strategy_id, name, thesis, asset_class, status,
                   source, generation, parent_strategy_id,
                   entry_logic, exit_logic, position_sizing,
                   created_at, updated_at
            FROM gold.strategy_research
            WHERE strategy_id = :sid
        """), {"sid": strategy_id}).fetchone()

        if not wf:
            raise HTTPException(status_code=404, detail="Strategy not found")

        # Backtest runs
        backtests = db.execute(text("""
            SELECT run_id, run_number, run_by, is_start, is_end, oos_start, oos_end,
                   sharpe_is, sharpe_oos, max_drawdown_oos, trade_count_oos,
                   win_rate_oos, all_risk_gates_passed, parameters_used, notes, created_at
            FROM gold.strategy_backtest_runs
            WHERE strategy_id = :sid
            ORDER BY created_at DESC
        """), {"sid": strategy_id}).fetchall()

        # QA reviews
        qa = db.execute(text("""
            SELECT review_id, reviewed_by, decision, conviction_score,
                   sharpe_stability, trade_count_score, drawdown_score, regime_score,
                   failed_gates, passed_gates, warnings, full_comment, reviewed_at
            FROM gold.strategy_qa_reviews
            WHERE strategy_id = :sid
            ORDER BY reviewed_at DESC
        """), {"sid": strategy_id}).fetchall()

        # Risk reviews
        risk = db.execute(text("""
            SELECT review_id, reviewed_by, decision, risk_score,
                   failed_gates, passed_gates, suggested_fixes, full_comment, reviewed_at
            FROM gold.strategy_risk_reviews
            WHERE strategy_id = :sid
            ORDER BY reviewed_at DESC
        """), {"sid": strategy_id}).fetchall()

        bt_list = []
        for b in backtests:
            bt_list.append({
                "run_id": str(b.run_id),
                "run_number": b.run_number,
                "run_by": b.run_by,
                "is_period": f"{b.is_start} to {b.is_end}" if b.is_start else None,
                "oos_period": f"{b.oos_start} to {b.oos_end}" if b.oos_start else None,
                "sharpe_is": float(b.sharpe_is) if b.sharpe_is else None,
                "sharpe_oos": float(b.sharpe_oos) if b.sharpe_oos else None,
                "max_drawdown_oos": float(b.max_drawdown_oos) if b.max_drawdown_oos else None,
                "trade_count_oos": b.trade_count_oos,
                "win_rate_oos": float(b.win_rate_oos) if b.win_rate_oos else None,
                "all_gates_passed": b.all_risk_gates_passed,
                "parameters": b.parameters_used,
                "notes": b.notes,
                "created_at": b.created_at.isoformat() if b.created_at else None,
            })

        qa_list = []
        for q in qa:
            qa_list.append({
                "review_id": str(q.review_id),
                "reviewed_by": q.reviewed_by,
                "decision": q.decision,
                "conviction_score": float(q.conviction_score) if q.conviction_score else None,
                "scores": {
                    "sharpe_stability": float(q.sharpe_stability) if q.sharpe_stability else None,
                    "trade_count": float(q.trade_count_score) if q.trade_count_score else None,
                    "drawdown": float(q.drawdown_score) if q.drawdown_score else None,
                    "regime": float(q.regime_score) if q.regime_score else None,
                },
                "failed_gates": q.failed_gates,
                "passed_gates": q.passed_gates,
                "warnings": q.warnings,
                "comment": q.full_comment,
                "reviewed_at": q.reviewed_at.isoformat() if q.reviewed_at else None,
            })

        risk_list = []
        for rr in risk:
            risk_list.append({
                "review_id": str(rr.review_id),
                "reviewed_by": rr.reviewed_by,
                "decision": rr.decision,
                "risk_score": float(rr.risk_score) if rr.risk_score else None,
                "failed_gates": rr.failed_gates,
                "passed_gates": rr.passed_gates,
                "suggested_fixes": rr.suggested_fixes,
                "comment": rr.full_comment,
                "reviewed_at": rr.reviewed_at.isoformat() if rr.reviewed_at else None,
            })

        return {
            "workflow": {
                "strategy_id": wf.strategy_id,
                "name": wf.name,
                "thesis": wf.thesis,
                "asset_class": wf.asset_class,
                "status": wf.status,
                "source": wf.source,
                "generation": wf.generation,
                "parent_strategy_id": wf.parent_strategy_id,
                "entry_logic": wf.entry_logic,
                "exit_logic": wf.exit_logic,
                "position_sizing": wf.position_sizing,
                "created_at": wf.created_at.isoformat() if wf.created_at else None,
                "updated_at": wf.updated_at.isoformat() if wf.updated_at else None,
            },
            "backtests": bt_list,
            "qa_reviews": qa_list,
            "risk_reviews": risk_list,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Strategy detail error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ── GET /api/agents/gold-layer-status ────────────────────────────────────

@router.get("/gold-layer-status")
def get_gold_layer_status(db: Session = Depends(get_db)):
    """Gold layer refresh health from sync_schedules."""
    try:
        row = db.execute(text("""
            SELECT state, refreshed_at, hours_since_refresh,
                   sources_ok, sources_failed, notes
            FROM gold.v_agent_gold_layer_status
            LIMIT 1
        """)).fetchone()
        if not row:
            return {"state": "unknown"}
        return {
            "state": row.state,
            "refreshed_at": row.refreshed_at.isoformat() if row.refreshed_at else None,
            "hours_since_refresh": float(row.hours_since_refresh) if row.hours_since_refresh else None,
            "sources_ok": row.sources_ok,
            "sources_failed": row.sources_failed,
            "notes": row.notes,
        }
    except Exception as e:
        logger.error(f"Gold layer status error: {e}")
        return {"state": "error", "error": str(e)}


# ── POST /api/agents/events (manual injection for testing) ───────────────

class AgentEventPayload(BaseModel):
    agent_name: str
    event_type: str
    payload: Optional[dict] = None


@router.post("/events")
def create_agent_event(
    body: AgentEventPayload,
    db: Session = Depends(get_db),
):
    """Manually inject an agent event. Used by agents or for testing."""
    ok = log_agent_event(db, body.agent_name, body.event_type, body.payload)
    if ok:
        db.commit()
        return {"success": True, "message": "Event logged"}
    db.rollback()
    raise HTTPException(status_code=500, detail="Failed to log event")


# ═══════════════════════════════════════════════════════════════════════════
# PAPER TRADING ENDPOINTS — Section A-D + Gateway + Cron
# ═══════════════════════════════════════════════════════════════════════════

# ── GET /api/paper/system-status ─────────────────────────────────────────

@router.get("/paper/system-status")
def get_paper_system_status(db: Session = Depends(get_db)):
    """Section A status bar — regime, last run, NAV."""
    try:
        row = db.execute(text("SELECT * FROM gold.v_paper_system_status LIMIT 1")).fetchone()
        if not row:
            return {"state": "unknown"}
        return {
            "regime_label": row.regime_label,
            "regime_confidence": float(row.regime_confidence) if row.regime_confidence else None,
            "regime_override": row.regime_override,
            "regime_date": row.regime_date.isoformat() if row.regime_date else None,
            "regime_staleness_days": row.regime_staleness_days,
            "last_run_date": row.last_run_date.isoformat() if row.last_run_date else None,
            "last_run_type": row.last_run_type,
            "last_run_status": row.last_run_status,
            "last_orders_placed": row.last_orders_placed,
            "last_orders_skipped": row.last_orders_skipped,
            "paper_nav_usd": row.paper_nav_usd,
            "paper_nav_hkd": row.paper_nav_hkd,
        }
    except Exception as e:
        logger.error(f"Paper system status error: {e}")
        return {"state": "error", "error": str(e)}


# ── GET /api/paper/open-positions ────────────────────────────────────────

@router.get("/paper/open-positions")
def get_paper_open_positions(db: Session = Depends(get_db)):
    """Section B — current open positions with unrealised PnL."""
    try:
        rows = db.execute(text("SELECT * FROM gold.v_paper_open_positions")).fetchall()
        positions = []
        for r in rows:
            positions.append({
                "id": str(r.id),
                "strategy_id": r.strategy_id,
                "instrument": r.instrument,
                "ticker": r.ticker,
                "direction": r.direction,
                "contracts": float(r.contracts) if r.contracts else None,
                "shares": float(r.shares) if r.shares else None,
                "entry_price": float(r.entry_price) if r.entry_price else None,
                "current_price": float(r.current_price) if r.current_price else None,
                "unrealised_pnl": float(r.unrealised_pnl) if r.unrealised_pnl else None,
                "regime_at_entry": r.regime_at_entry,
                "ic_at_entry": float(r.ic_at_entry) if r.ic_at_entry else None,
                "confidence_at_entry": float(r.confidence_at_entry) if r.confidence_at_entry else None,
                "opened_at": r.opened_at.isoformat() if r.opened_at else None,
                "hold_duration": str(r.hold_duration) if r.hold_duration else None,
            })
        return {"positions": positions, "count": len(positions)}
    except Exception as e:
        logger.error(f"Paper open positions error: {e}")
        return {"positions": [], "count": 0, "error": str(e)}


# ── GET /api/paper/daily-runs ────────────────────────────────────────────

@router.get("/paper/daily-runs")
def get_paper_daily_runs(db: Session = Depends(get_db)):
    """Section C — today's run cards."""
    try:
        rows = db.execute(text("SELECT * FROM gold.v_paper_daily_runs")).fetchall()
        runs = []
        for r in rows:
            runs.append({
                "run_date": r.run_date.isoformat() if r.run_date else None,
                "run_type": r.run_type,
                "signals_eval": r.signals_eval,
                "orders_placed": r.orders_placed,
                "orders_skipped": r.orders_skipped,
                "gate_reasons": r.gate_reasons,
                "total_pnl": float(r.total_pnl) if r.total_pnl else None,
                "drawdown_pct": float(r.drawdown_pct) if r.drawdown_pct else None,
                "status": r.status,
                "duration_ms": r.duration_ms,
            })
        return {"runs": runs, "count": len(runs)}
    except Exception as e:
        logger.error(f"Paper daily runs error: {e}")
        return {"runs": [], "count": 0, "error": str(e)}


# ── GET /api/paper/trade-history ─────────────────────────────────────────

@router.get("/paper/trade-history")
def get_paper_trade_history(
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
):
    """Section D — closed trade history (last 30 days)."""
    try:
        rows = db.execute(
            text("SELECT * FROM gold.v_paper_trade_history LIMIT :limit"),
            {"limit": limit}
        ).fetchall()
        trades = []
        for r in rows:
            trades.append({
                "id": str(r.id),
                "strategy_id": r.strategy_id,
                "instrument": r.instrument,
                "ticker": r.ticker,
                "direction": r.direction,
                "contracts": float(r.contracts) if r.contracts else None,
                "shares": float(r.shares) if r.shares else None,
                "entry_price": float(r.entry_price) if r.entry_price else None,
                "exit_price": float(r.exit_price) if r.exit_price else None,
                "pnl": float(r.pnl) if r.pnl else None,
                "pnl_pct": float(r.pnl_pct) if r.pnl_pct else None,
                "regime": r.regime,
                "ic_at_entry": float(r.ic_at_entry) if r.ic_at_entry else None,
                "opened_at": r.opened_at.isoformat() if r.opened_at else None,
                "closed_at": r.closed_at.isoformat() if r.closed_at else None,
                "hold_days": r.hold_days,
            })
        return {"trades": trades, "count": len(trades)}
    except Exception as e:
        logger.error(f"Paper trade history error: {e}")
        return {"trades": [], "count": 0, "error": str(e)}


# ── GET /api/paper/trade-summary ─────────────────────────────────────────

@router.get("/paper/trade-summary")
def get_paper_trade_summary(db: Session = Depends(get_db)):
    """Summary row above trade history."""
    try:
        row = db.execute(text("SELECT * FROM gold.v_paper_trade_summary LIMIT 1")).fetchone()
        if not row:
            return {}
        return {
            "total_trades": row.total_trades,
            "win_rate_pct": float(row.win_rate_pct) if row.win_rate_pct else None,
            "total_pnl": float(row.total_pnl) if row.total_pnl else None,
            "avg_pnl": float(row.avg_pnl) if row.avg_pnl else None,
            "max_loss": float(row.max_loss) if row.max_loss else None,
            "max_win": float(row.max_win) if row.max_win else None,
            "max_drawdown_pct": float(row.max_drawdown_pct) if row.max_drawdown_pct else None,
        }
    except Exception as e:
        logger.error(f"Paper trade summary error: {e}")
        return {"error": str(e)}


# ── GET /api/paper/strategy-book ─────────────────────────────────────────

@router.get("/paper/strategy-book")
def get_paper_strategy_book(db: Session = Depends(get_db)):
    """Section A on agentic_research — strategy book."""
    try:
        rows = db.execute(text("SELECT * FROM gold.v_strategy_book")).fetchall()
        strategies = []
        for r in rows:
            strategies.append({
                "strategy_id": r.strategy_id,
                "name": r.name,
                "status": r.status,
                "asset_class": r.asset_class,
                "entry_logic": r.entry_logic,
                "exit_logic": r.exit_logic,
                "agent_source": r.agent_source,
                "sharpe_ratio": float(r.sharpe_ratio) if r.sharpe_ratio else None,
                "win_rate": float(r.win_rate) if r.win_rate else None,
                "backtest_date": r.backtest_date.isoformat() if r.backtest_date else None,
                "sort_order": r.sort_order,
                "last_entry_price": float(r.last_entry_price) if r.last_entry_price else None,
                "last_traded_at": r.last_traded_at.isoformat() if r.last_traded_at else None,
                "last_direction": r.last_direction,
            })
        return {"strategies": strategies, "count": len(strategies)}
    except Exception as e:
        logger.error(f"Strategy book error: {e}")
        return {"strategies": [], "count": 0, "error": str(e)}


# ── GET /api/paper/agent-activity ────────────────────────────────────────

@router.get("/paper/agent-activity")
def get_paper_agent_activity(
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    """Section B — agent activity feed."""
    try:
        rows = db.execute(
            text("SELECT * FROM gold.v_agent_activity_feed LIMIT :limit"),
            {"limit": limit}
        ).fetchall()
        events = []
        for r in rows:
            events.append({
                "agent_name": r.agent_name,
                "event_type": r.event_type,
                "payload": r.payload,
                "detail": r.detail,
                "strategy_id": r.strategy_id,
                "instrument": r.instrument,
                "ts": r.ts.isoformat() if r.ts else None,
            })
        return {"events": events, "count": len(events)}
    except Exception as e:
        logger.error(f"Agent activity error: {e}")
        return {"events": [], "count": 0, "error": str(e)}


# ── GET /api/paper/upcoming-events ───────────────────────────────────────

@router.get("/paper/upcoming-events")
def get_paper_upcoming_events(db: Session = Depends(get_db)):
    """Section C — earnings + macro calendar."""
    try:
        rows = db.execute(text("SELECT * FROM gold.v_upcoming_events")).fetchall()
        events = []
        for r in rows:
            events.append({
                "event_category": r.event_category,
                "event_date": r.event_date.isoformat() if r.event_date else None,
                "event_label": r.event_label,
                "description": r.description,
                "related_strategy": r.related_strategy,
                "days_away": r.days_away,
            })
        return {"events": events, "count": len(events)}
    except Exception as e:
        logger.error(f"Upcoming events error: {e}")
        return {"events": [], "count": 0, "error": str(e)}


# ── GET /api/paper/strategy-book-extended ────────────────────────────────

@router.get("/paper/strategy-book-extended")
def get_paper_strategy_book_extended(db: Session = Depends(get_db)):
    """Extended strategy book with backtest metrics + last trade."""
    try:
        rows = db.execute(text("SELECT * FROM gold.v_strategy_book_extended")).fetchall()
        strategies = []
        for r in rows:
            strategies.append({
                "strategy_id": r.strategy_id,
                "name": r.name,
                "display_name": r.display_name,
                "instrument": r.instrument,
                "regime_scope": r.regime_scope,
                "status": r.status,
                "asset_class": r.asset_class,
                "entry_logic": r.entry_logic,
                "exit_logic": r.exit_logic,
                "source": r.source,
                "sharpe_ratio": float(r.sharpe_ratio) if r.sharpe_ratio else None,
                "returns": float(r.returns) if r.returns else None,
                "win_rate": float(r.win_rate) if r.win_rate else None,
                "max_drawdown": float(r.max_drawdown) if r.max_drawdown else None,
                "trade_count": int(r.trade_count) if r.trade_count is not None else None,
                "turnover": float(r.turnover) if r.turnover else None,
                "profit_factor": float(r.profit_factor) if r.profit_factor else None,
                "cvar_95": float(r.cvar_95) if r.cvar_95 else None,
                "backtest_date": r.backtest_date.isoformat() if r.backtest_date else None,
                "last_direction": r.last_direction,
                "last_entry_price": float(r.last_entry_price) if r.last_entry_price else None,
                "last_traded_at": r.last_traded_at.isoformat() if r.last_traded_at else None,
                "min_nav_usd": r.min_nav_usd,
                "annual_pnl_2024": float(r.annual_pnl_2024) if r.annual_pnl_2024 else None,
                "annual_pnl_2025": float(r.annual_pnl_2025) if r.annual_pnl_2025 else None,
                "annual_pnl_2026": float(r.annual_pnl_2026) if r.annual_pnl_2026 else None,
                "live_pnl": float(r.live_pnl) if r.live_pnl is not None else None,
                "live_win_rate": float(r.live_win_rate) if r.live_win_rate is not None else None,
                "live_trades": int(r.live_trades) if r.live_trades is not None else None,
            })
        return {"strategies": strategies, "count": len(strategies)}
    except Exception as e:
        logger.error(f"Strategy book extended error: {e}")
        return {"strategies": [], "count": 0, "error": str(e)}


# ── GET /api/paper/gateway-status ────────────────────────────────────────

@router.get("/paper/gateway-status")
def get_paper_gateway_status():
    """IBKR gateway connection check."""
    try:
        # Try to import IBKR client; fallback if not available
        try:
            from app.services.ib_service import IBKRClient
            client = IBKRClient()
            connected = client.is_connected()
        except Exception:
            connected = False
        return {
            "connected": connected,
            "host": "127.0.0.1:14002",
            "ts": datetime.datetime.utcnow().isoformat(),
        }
    except Exception as e:
        logger.error(f"Gateway status error: {e}")
        return {"connected": False, "host": "127.0.0.1:14002", "error": str(e)}


# ── GET /api/agents/paper/signal-proximity ───────────────────────────────

@router.get("/paper/signal-proximity")
def get_paper_signal_proximity(db: Session = Depends(get_db)):
    """Signal proximity to threshold — ordered by distance_pct DESC."""
    try:
        rows = db.execute(text("""
            SELECT strategy_id, instrument_or_ticker, signal_type,
                   current_value, threshold, distance_to_threshold,
                   distance_pct, signal_active, days_until_relevant, last_updated
            FROM gold.v_signal_proximity
            ORDER BY distance_pct DESC
        """)).fetchall()
        signals = []
        for r in rows:
            signals.append({
                "strategy_id": r.strategy_id,
                "instrument_or_ticker": r.instrument_or_ticker,
                "signal_type": r.signal_type,
                "current_value": float(r.current_value) if r.current_value is not None else None,
                "threshold": float(r.threshold) if r.threshold is not None else None,
                "distance_to_threshold": float(r.distance_to_threshold) if r.distance_to_threshold is not None else None,
                "distance_pct": float(r.distance_pct) if r.distance_pct is not None else None,
                "signal_active": bool(r.signal_active) if r.signal_active is not None else False,
                "days_until_relevant": r.days_until_relevant,
                "last_updated": r.last_updated.isoformat() if r.last_updated else None,
            })
        return {"signals": signals, "count": len(signals)}
    except Exception as e:
        logger.error(f"Signal proximity error: {e}")
        return {"signals": [], "count": 0, "error": str(e)}


# ── GET /api/agents/paper/open-positions-pnl ─────────────────────────────

@router.get("/paper/open-positions-pnl")
def get_paper_open_positions_pnl(db: Session = Depends(get_db)):
    """Open positions with unrealised PnL from gold.v_paper_open_positions."""
    try:
        rows = db.execute(text("""
            SELECT strategy_id, instrument, ticker, direction,
                   entry_price, current_price, unrealised_pnl_pct,
                   unrealised_pnl_usd, days_held, price_source
            FROM gold.v_paper_open_positions
            ORDER BY unrealised_pnl_pct DESC
        """)).fetchall()
        positions = []
        for r in rows:
            positions.append({
                "strategy_id": r.strategy_id,
                "instrument": r.instrument,
                "ticker": r.ticker,
                "direction": r.direction,
                "entry_price": float(r.entry_price) if r.entry_price is not None else None,
                "current_price": float(r.current_price) if r.current_price is not None else None,
                "unrealised_pnl_pct": float(r.unrealised_pnl_pct) if r.unrealised_pnl_pct is not None else None,
                "unrealised_pnl_usd": float(r.unrealised_pnl_usd) if r.unrealised_pnl_usd is not None else None,
                "days_held": r.days_held,
                "price_source": r.price_source,
            })
        return {"positions": positions, "count": len(positions)}
    except Exception as e:
        logger.error(f"Open positions PnL error: {e}")
        return {"positions": [], "count": 0, "error": str(e)}


# ── GET /api/paper/cron-status ───────────────────────────────────────────

@router.get("/paper/cron-status")
def get_paper_cron_status():
    """Hermes cron job status — parsed from `hermes cron list`."""
    try:
        import subprocess, json as _json
        result = subprocess.run(
            ["hermes", "cron", "list"],
            capture_output=True, text=True, timeout=10
        )
        jobs = []
        # hermes cron list outputs JSON-like lines; try JSON first
        try:
            data = _json.loads(result.stdout)
            if isinstance(data, list):
                jobs = data
            elif isinstance(data, dict) and "jobs" in data:
                jobs = data["jobs"]
        except _json.JSONDecodeError:
            # Fallback: parse plain text
            for line in result.stdout.strip().split("\n"):
                if line.strip() and not line.startswith("-"):
                    parts = line.split()
                    if len(parts) >= 3:
                        jobs.append({
                            "job_id": parts[0],
                            "name": parts[1] if len(parts) > 1 else "",
                            "status": parts[2] if len(parts) > 2 else "unknown",
                            "next_run": None,
                            "last_run": None,
                        })
        return {"jobs": jobs, "count": len(jobs)}
    except Exception as e:
        logger.error(f"Cron status error: {e}")
        return {"jobs": [], "count": 0, "error": str(e)}
