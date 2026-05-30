"""
Agent Event Logger
==================
Shared helper for all Hermes agents to log key actions to gold.agent_events.

Schema (gold.agent_events):
    id            SERIAL PRIMARY KEY
    agent_name    TEXT NOT NULL
    event_type    TEXT NOT NULL
    payload       JSONB
    ts            TIMESTAMPTZ DEFAULT now()

Usage:
    from app.services.agent_events import log_agent_event
    log_agent_event(db, "qr_research", "hypothesis.promoted",
                     {"strategy_id": "S42", "sharpe": 2.1})
"""
import json
import logging
from typing import Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text

logger = logging.getLogger(__name__)


def log_agent_event(
    db: Session,
    agent_name: str,
    event_type: str,
    payload: Optional[dict[str, Any]] = None,
) -> bool:
    """
    Insert a single event into gold.agent_events.
    """
    try:
        db.execute(
            text("""
                INSERT INTO gold.agent_events (agent_name, event_type, payload_json, created_at)
                VALUES (:agent_name, :event_type, :payload, now())
            """),
            {
                "agent_name": agent_name,
                "event_type": event_type,
                "payload": json.dumps(payload) if payload else None,
            },
        )
        return True
    except Exception as e:
        logger.error(f"agent_events insert failed: {e}")
        return False
