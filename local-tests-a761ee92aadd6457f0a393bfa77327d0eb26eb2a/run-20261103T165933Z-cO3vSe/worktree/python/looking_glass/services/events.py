"""In-process pub/sub hub pushing live updates to viewer WebSockets.

Both uvicorn servers run in the same asyncio loop, so an admin action can
notify viewer sockets directly without an external broker.
"""

from __future__ import annotations

import asyncio
import json
import logging
from collections import defaultdict
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from fastapi import WebSocket
from .viewer_sync import ViewerSync

log = logging.getLogger(__name__)


class EventHub:
    def __init__(self) -> None:
        self._subs: dict[int, set[WebSocket]] = defaultdict(set)
        self._lock = asyncio.Lock()
        self.sync = ViewerSync()

    async def subscribe(self, campaign_id: int, ws: WebSocket) -> None:
        async with self._lock:
            ws.state.delivery_lock = asyncio.Lock()
            self._subs[campaign_id].add(ws)
            ws.state.sync_id = self.sync.connect(campaign_id, getattr(ws.state,"user_id",None),
                                                 getattr(ws.state,"username","Viewer"))

    async def unsubscribe(self, campaign_id: int, ws: WebSocket) -> None:
        async with self._lock:
            sockets = self._subs.get(campaign_id)
            if sockets is not None:
                sockets.discard(ws)
                if not sockets:
                    del self._subs[campaign_id]
            self.sync.disconnect(getattr(ws.state,"sync_id",None))

    def viewer_count(self, campaign_id: int) -> int:
        return len(self._subs.get(campaign_id, ()))

    async def _drop(self, campaign_id: int, ws: WebSocket) -> None:
        """Caller holds delivery_lock; detach even if transport close fails."""
        try:
            await ws.close(code=4403)
        except Exception:
            pass
        finally:
            await self.unsubscribe(campaign_id, ws)

    def _allowed(self, ws: WebSocket) -> bool:
        check = getattr(ws.state, "access_check", None)
        try:
            return check is None or bool(check())
        except Exception:
            log.exception("Viewer socket access check failed; closing connection")
            return False

    async def check_access(self, campaign_id: int, ws: WebSocket) -> bool:
        async with ws.state.delivery_lock:
            if ws not in self._subs.get(campaign_id, ()):
                return False
            if not self._allowed(ws):
                await self._drop(campaign_id, ws)
                return False
            return True

    async def send_text(self, campaign_id: int, ws: WebSocket, payload: str) -> bool:
        """Check access immediately before delivery; serialize with explicit kicks."""
        async with ws.state.delivery_lock:
            if ws not in self._subs.get(campaign_id, ()):
                return False
            if not self._allowed(ws):
                await self._drop(campaign_id, ws)
                return False
            try:
                await ws.send_text(payload)
            except Exception:
                await self.unsubscribe(campaign_id, ws)
                return False
            return True

    async def publish(self, campaign_id: int, event: dict) -> None:
        payload = json.dumps(event)
        async with self._lock:
            targets = list(self._subs.get(campaign_id, ()))
        for ws in targets:
            await self.send_text(campaign_id, ws, payload)

    async def _kick(self, attribute: str, value) -> None:
        async with self._lock:
            targets = [(cid, ws) for cid, sockets in self._subs.items() for ws in sockets
                       if getattr(ws.state, attribute, None) == value]
        for cid, ws in targets:
            async with ws.state.delivery_lock:
                if ws in self._subs.get(cid, ()):
                    await self._drop(cid, ws)

    async def kick_session(self, session_hash: str) -> None:
        """Close only sockets belonging to this already hashed session identity."""
        await self._kick("session_hash", session_hash)

    async def kick_user(self, user_id: int) -> None:
        """Close sockets of a user whose access was revoked."""
        await self._kick("user_id", user_id)
