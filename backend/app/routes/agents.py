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
router = APIRouter(prefix="/api/agents", tags=["agents"])

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
