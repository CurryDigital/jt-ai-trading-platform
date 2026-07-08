"""Safe database query helpers with graceful degradation for missing tables."""
import re
import logging
from sqlalchemy.orm import Session
from sqlalchemy import text
from sqlalchemy.exc import ProgrammingError, OperationalError

logger = logging.getLogger(__name__)

# Cache of tables known to be missing (avoids repeated failed queries per process)
_missing_tables: set = set()


def safe_query(db: Session, sql: str, params: dict = None, fallback=None, label: str = ""):
    """Execute a SQL query with graceful fallback if the table doesn't exist.

    After a PostgreSQL error, the transaction is in an aborted state.
    This function calls db.rollback() to reset it, preventing cascade failures
    on subsequent queries within the same request.

    Args:
        db: SQLAlchemy session
        sql: Raw SQL string
        params: Query parameters
        fallback: Value to return if query fails (default: empty list)
        label: Human-readable label for logging

    Returns:
        Query result rows, or fallback value
    """
    if fallback is None:
        fallback = []

    # Fast path: skip query if a referenced table is known-missing
    sql_lower = sql.lower()
    for table in _missing_tables:
        if table.lower() in sql_lower:
            logger.debug(f"Skipping query [{label}]: known missing table {table}")
            return fallback

    try:
        result = db.execute(text(sql), params or {})
        return result.fetchall()
    except ProgrammingError as e:
        error_str = str(e.orig) if e.orig else str(e)
        if "does not exist" in error_str and "column" not in error_str.lower():
            match = re.search(r'relation "([^"]+)" does not exist', error_str)
            if match:
                _missing_tables.add(match.group(1))
            logger.warning(f"Table missing [{label}]: {error_str}")
            db.rollback()
            return fallback
        db.rollback()
        raise
    except OperationalError as e:
        error_str = str(e)
        if "QueuePool limit" in error_str or "connection timed out" in error_str or "timeout expired" in error_str:
            logger.error(f"DB pool exhausted [{label}]: {error_str[:120]}")
            db.rollback()
            raise  # re-raise so FastAPI exception handler returns 503
        logger.error(f"DB operational error [{label}]: {e}")
        db.rollback()
        return fallback
    except Exception as e:
        logger.error(f"Query error [{label}]: {e}")
        db.rollback()
        return fallback


def safe_query_one(db: Session, sql: str, params: dict = None, fallback=None, label: str = ""):
    """Like safe_query but returns a single row (fetchone)."""
    sql_lower = sql.lower()
    for table in _missing_tables:
        if table.lower() in sql_lower:
            logger.debug(f"Skipping query [{label}]: known missing table {table}")
            return fallback

    try:
        result = db.execute(text(sql), params or {})
        return result.fetchone() or fallback
    except ProgrammingError as e:
        error_str = str(e.orig) if e.orig else str(e)
        if "does not exist" in error_str and "column" not in error_str.lower():
            match = re.search(r'relation "([^"]+)" does not exist', error_str)
            if match:
                _missing_tables.add(match.group(1))
            logger.warning(f"Table missing [{label}]: {error_str}")
            db.rollback()
            return fallback
        db.rollback()
        raise
    except OperationalError as e:
        error_str = str(e)
        if "QueuePool limit" in error_str or "connection timed out" in error_str or "timeout expired" in error_str:
            logger.error(f"DB pool exhausted [{label}]: {error_str[:120]}")
            db.rollback()
            raise  # re-raise so FastAPI exception handler returns 503
        logger.error(f"DB operational error [{label}]: {e}")
        db.rollback()
        return fallback
    except Exception as e:
        logger.error(f"Query error [{label}]: {e}")
        db.rollback()
        return fallback


def clear_missing_table_cache():
    """Clear the cache (e.g., after DDL migration creates the tables)."""
    _missing_tables.clear()


# Auto-clear cache on module import so a fresh backend process always tries once.
# This makes the cache per-request safety rather than a hard persistent skip.
clear_missing_table_cache()
