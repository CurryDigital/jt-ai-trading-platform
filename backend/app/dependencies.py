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
