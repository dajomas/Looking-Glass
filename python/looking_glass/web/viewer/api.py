"""Viewer JSON/image API and the live-update WebSocket.

The viewer only ever receives the server-composited, fogged image of the
campaign's *active* map - never the raw battle map or wall data.
"""

import asyncio
import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse

from ...repositories import campaigns as campaigns_repo
from ...repositories import maps as maps_repo
from ..access import campaign_for_view, fog_inputs
from ..deps import CtxDep, NotFound, UserDep, cookie_name, resolve_user
from ... import rbac

log = logging.getLogger(__name__)
router = APIRouter()


@router.get("/api/c/{campaign_id}/state")
def state(ctx: CtxDep, user: UserDep, campaign_id: int):
    with ctx.db.connect() as conn:
        c = campaign_for_view(conn, user, campaign_id)
        m = maps_repo.get(conn, c["active_map_id"]) if c["active_map_id"] else None
    if m is None:
        return {"ok": True, "campaign": c["name"], "map": None}
    version = f"{m['id']}-{m['walls_version']}-{m['fog_version']}"
    return {"ok": True, "campaign": c["name"],
            "map": {"name": m["name"], "width": m["width"], "height": m["height"], "version": version,
                    "image_url": f"/api/c/{campaign_id}/image?v={version}"}}


@router.get("/api/c/{campaign_id}/image")
async def image(ctx: CtxDep, user: UserDep, campaign_id: int):
    with ctx.db.connect() as conn:
        c = campaign_for_view(conn, user, campaign_id)
        if not c["active_map_id"]:
            raise NotFound("No map is being shown.")
        spec, segs, ops = fog_inputs(ctx, conn, c["active_map_id"])
    path = await asyncio.to_thread(ctx.fog.viewer_image, spec, segs, ops)
    return FileResponse(path, media_type=ctx.fog.viewer_media_type,
                        headers={"Cache-Control": "private, max-age=86400"})


@router.websocket("/ws/c/{campaign_id}")
async def live(ws: WebSocket, campaign_id: int):
    ctx = ws.app.state.ctx
    user = resolve_user(ctx, "viewer", ws.cookies.get(cookie_name(ws)))
    if user is None:
        await ws.close(code=4401)
        return
    with ctx.db.connect() as conn:
        c = campaigns_repo.get(conn, campaign_id)
        allowed = c is not None and rbac.can_view_campaign(conn, user, c)
    if not allowed:
        await ws.close(code=4404)
        return
    await ws.accept()
    ws.state.user_id = user["id"]
    await ctx.hub.subscribe(campaign_id, ws)
    try:
        while True:
            msg = await ws.receive_text()   # keep-alive pings from the client
            if msg == "ping":
                await ws.send_text('{"type":"pong"}')
    except WebSocketDisconnect:
        pass
    finally:
        await ctx.hub.unsubscribe(campaign_id, ws)
