"""Shared dependencies for all route modules."""
import logging
from app.db.session import SessionLocal

logger = logging.getLogger(__name__)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
