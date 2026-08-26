"""Shared dependencies for all route modules."""
import logging
from fastapi import HTTPException
from sqlalchemy.exc import OperationalError
from app.db.session import SessionLocal

logger = logging.getLogger(__name__)


def get_db():
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
            db.close()


# Registry execution_mode values are constrained to SIMULATION / PAPER / PAPER_UAT / LIVE
# (PAPER_UAT requires the widened CHECK constraint — qr_etl kanban t_b64f7302;
# until it lands, registry writes of PAPER_UAT will fail with a CheckViolation).
# The UI/API use SIMULATION / PAPER_TRADING / PAPER_UAT / LIVE_TRADING.
# Keep mapping in one place.
REGISTRY_API_MODE_MAP = {
    "SIMULATION": "SIMULATION",
    "PAPER": "PAPER_TRADING",
    "PAPER_UAT": "PAPER_UAT",
    "LIVE": "LIVE_TRADING",
}
API_REGISTRY_MODE_MAP = {v: k for k, v in REGISTRY_API_MODE_MAP.items()}


def api_to_registry_mode(mode: str | None) -> str:
    """Map API-facing execution mode to the constrained registry values."""
    if not mode:
        return "SIMULATION"
    m = mode.upper().replace("_TRADING", "")
    if m in ("SIMULATION", "PAPER", "PAPER_UAT", "LIVE"):
        return API_REGISTRY_MODE_MAP.get(mode.upper(), m)
    return "SIMULATION"


def registry_to_api_mode(mode: str | None) -> str:
    """Map constrained registry execution mode to API-facing values."""
    if not mode:
        return "SIMULATION"
    return REGISTRY_API_MODE_MAP.get(mode.upper(), "SIMULATION")
