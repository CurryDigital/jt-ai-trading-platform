"""In-process event bus for broadcasting real-time events to WebSocket clients.

Usage
-----
    from app.services.event_bus import event_bus

    # From any endpoint — fire-and-forget:
    await event_bus.publish("mode_change", {"from": "SIM", "to": "PAPER"})

    # In the WebSocket handler:
    async for event in event_bus.subscribe():
        await ws.send_json(event)
"""

import asyncio
import datetime
import json
import logging
from typing import AsyncGenerator

logger = logging.getLogger(__name__)


class EventBus:
    """Lightweight async broadcast channel backed by asyncio.Queue per subscriber."""

    def __init__(self, maxlen: int = 256):
        self._subscribers: list[asyncio.Queue] = []
        self._maxlen = maxlen

    async def publish(self, event_type: str, payload: dict | None = None):
        envelope = {
            "type": event_type,
            "ts": datetime.datetime.utcnow().isoformat() + "Z",
            "data": payload or {},
        }
        dead = []
        for q in self._subscribers:
            try:
                q.put_nowait(envelope)
            except asyncio.QueueFull:
                dead.append(q)
        for q in dead:
            self._subscribers.remove(q)

    def publish_sync(self, event_type: str, payload: dict | None = None):
        """Non-async convenience wrapper — safe to call from sync endpoints."""
        envelope = {
            "type": event_type,
            "ts": datetime.datetime.utcnow().isoformat() + "Z",
            "data": payload or {},
        }
        dead = []
        for q in self._subscribers:
            try:
                q.put_nowait(envelope)
            except asyncio.QueueFull:
                dead.append(q)
        for q in dead:
            self._subscribers.remove(q)

    async def subscribe(self) -> AsyncGenerator[dict, None]:
        q: asyncio.Queue = asyncio.Queue(maxsize=self._maxlen)
        self._subscribers.append(q)
        try:
            while True:
                event = await q.get()
                yield event
        finally:
            if q in self._subscribers:
                self._subscribers.remove(q)

    @property
    def subscriber_count(self) -> int:
        return len(self._subscribers)


event_bus = EventBus()
