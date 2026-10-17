"""In-process pub/sub hub pushing live updates to viewer WebSockets.

Both uvicorn servers run in the same asyncio loop, so an admin action can
notify viewer sockets directly without an external broker.
"""

import asyncio
import json
import logging
from collections import defaultdict

from fastapi import WebSocket

log = logging.getLogger(__name__)


class EventHub:
    def __init__(self) -> None:
        self._subs: dict[int, set[WebSocket]] = defaultdict(set)
        self._lock = asyncio.Lock()

    async def subscribe(self, campaign_id: int, ws: WebSocket) -> None:
        async with self._lock:
            self._subs[campaign_id].add(ws)

    async def unsubscribe(self, campaign_id: int, ws: WebSocket) -> None:
        async with self._lock:
            self._subs[campaign_id].discard(ws)

    def viewer_count(self, campaign_id: int) -> int:
        return len(self._subs.get(campaign_id, ()))

    async def publish(self, campaign_id: int, event: dict) -> None:
        payload = json.dumps(event)
        async with self._lock:
            targets = list(self._subs.get(campaign_id, ()))
        dead = []
        for ws in targets:
            try:
                await ws.send_text(payload)
            except Exception:  # client went away
                dead.append(ws)
        for ws in dead:
            await self.unsubscribe(campaign_id, ws)

    async def kick_user(self, user_id: int) -> None:
        """Close sockets of a user whose access was revoked."""
        async with self._lock:
            targets = [(cid, ws) for cid, s in self._subs.items() for ws in s
                       if getattr(ws.state, "user_id", None) == user_id]
        for cid, ws in targets:
            try:
                await ws.close(code=4403)
            except Exception:
                pass
            await self.unsubscribe(cid, ws)
