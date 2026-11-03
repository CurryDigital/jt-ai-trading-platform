"""Shared dependencies for all route modules."""
import logging
from fastapi import HTTPException
from sqlalchemy.exc import OperationalError
from app.db.session import SessionLocal

logger = logging.getLogger(__name__)


def get_db():
    """Yield a request-scoped session; always closed (=> rolled back) on exit.

    Cancel-on-abort (t_7213b685): FastAPI sync routes run in a threadpool, so
    a client disconnect does NOT interrupt the in-flight query — the route
    keeps running and this generator's finally only fires at completion. The
    effective bound on a query outliving its client is therefore the
    per-connection `statement_timeout` (8s) set on connect in
    app/db/session.py, plus `idle_in_transaction_session_timeout` for
    connections orphaned mid-transaction. Do not raise those values without
    revisiting the frontend's 10s abort budget.
    """
    db = None
    try:
        db = SessionLocal()
        yield db
    except OperationalError as e:
        error_str = str(e)
        if "QueuePool limit" in error_str or "connection timed out" in error_str or "timeout expired" in error_str:
            logger.warning(f"DB pool exhausted: {error_str[:120]}")
            raise HTTPException(
                status_code=503,
                detail={"error": "db_unavailable", "message": "Database temporarily unreachable", "retry_after": 30}
            )
        raise
    finally:
        if db is not None:
            db.rollback()  # no-op if clean; guarantees no open tx lingers
            db.close()


# Registry execution_mode values are constrained to SIMULATION / PAPER / PAPER_UAT / LIVE
# (qr_etl owns the CHECK constraint; the registry keeps the PAPER_UAT spelling).
# The UI/API vocabulary is SIMULATION / PAPER_TRADING / UAT / LIVE_TRADING —
# the book was renamed "Paper UAT" -> "UAT" (2026-08-31); the legacy API value
# PAPER_UAT is still accepted as an alias. Keep mapping in one place.
REGISTRY_API_MODE_MAP = {
    "SIMULATION": "SIMULATION",
    "PAPER": "PAPER_TRADING",
    "PAPER_UAT": "UAT",
    "LIVE": "LIVE_TRADING",
}
API_REGISTRY_MODE_MAP = {v: k for k, v in REGISTRY_API_MODE_MAP.items()}
# Legacy alias: pre-rename clients may still send PAPER_UAT as an API mode.
API_REGISTRY_MODE_MAP["PAPER_UAT"] = "PAPER_UAT"


def api_to_registry_mode(mode: str | None) -> str:
    """Map API-facing execution mode to the constrained registry values."""
    if not mode:
        return "SIMULATION"
    m = mode.upper().replace("_TRADING", "")
    if m == "UAT":
        return "PAPER_UAT"
    if m in ("SIMULATION", "PAPER", "PAPER_UAT", "LIVE"):
        return API_REGISTRY_MODE_MAP.get(mode.upper(), m)
    return "SIMULATION"


def registry_to_api_mode(mode: str | None) -> str:
    """Map constrained registry execution mode to API-facing values."""
    if not mode:
        return "SIMULATION"
    return REGISTRY_API_MODE_MAP.get(mode.upper(), "SIMULATION")
