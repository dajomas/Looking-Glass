"""Viewer JSON/image API and the live-update WebSocket.

The viewer only ever receives the server-composited, fogged image of the
campaign's *active* map - never the raw battle map or wall data.
"""

import asyncio
import logging
import json

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from fastapi.responses import Response, JSONResponse

from ...services.viewer_sync import display_version
from ...services.reveal_bounds import revealed_bounds
from ...services.revealed_regions import revealed_area_signatures
from ...services.viewer_area import revealed_area_bounds
from ...repositories import campaigns as campaigns_repo
from ...repositories import maps as maps_repo
from ..access import campaign_for_view, fog_inputs
from ..deps import BadRequest, CtxDep, NotFound, UserDep, cookie_name, resolve_user
from ... import rbac

log = logging.getLogger(__name__)
router = APIRouter()


def _version(m):
    return display_version(m)


@router.get("/api/c/{campaign_id}/state")
def state(ctx: CtxDep, user: UserDep, campaign_id: int):
    with ctx.db.connect() as conn:
        conn.execute("BEGIN")
        c = campaign_for_view(conn, user, campaign_id)
        m = maps_repo.get(conn, c["active_map_id"]) if c["active_map_id"] else None
        if m is not None: spec, segments, ops = fog_inputs(ctx, conn, m["id"])
    if m is None:
        return {"ok": True, "campaign": c["name"], "map": None}
    bounds = revealed_bounds(ctx.fog.mask(spec, segments, ops), m["width"], m["height"])
    signatures = revealed_area_signatures(ctx.fog, spec, segments, ops)
    version = _version(m)
    return {"ok": True, "campaign": c["name"],
            "map": {"name": m["name"], "width": m["width"], "height": m["height"], "version": version, "revealed_bounds": bounds,
                    "revealed_area_signatures": signatures,
                    "image_url": f"/api/c/{campaign_id}/image?v={version}"}}


@router.get("/api/c/{campaign_id}/image")
async def image(ctx: CtxDep, user: UserDep, campaign_id: int, v: str | None = None):
    with ctx.db.connect() as conn:
        c = campaign_for_view(conn, user, campaign_id)
        if not c["active_map_id"]:
            raise NotFound("No map is being shown.")
        m = maps_repo.get(conn, c["active_map_id"])
        expected = _version(m)
        if v is not None and v != expected:
            raise BadRequest("Map display changed; refresh the campaign state.")
        spec, segs, ops = fog_inputs(ctx, conn, c["active_map_id"])
    content = await asyncio.to_thread(ctx.fog.viewer_bytes, spec, segs, ops)
    with ctx.db.connect() as conn:
        c = campaign_for_view(conn, user, campaign_id)
        current = maps_repo.get(conn, c["active_map_id"]) if c["active_map_id"] else None
        if current is None or _version(current) != expected:
            raise BadRequest("Map display changed during rendering; refresh the campaign state.")
    return Response(content, media_type=ctx.fog.viewer_media_type,
                        headers={"Cache-Control": "no-store"})


@router.get("/api/c/{campaign_id}/area-bounds")
async def area_bounds(ctx: CtxDep, user: UserDep, campaign_id: int, x: float, y: float, v: str):
    with ctx.db.connect() as conn:
        conn.execute("BEGIN")
        c = campaign_for_view(conn, user, campaign_id)
        if not c["active_map_id"]:
            raise NotFound("No map is being shown.")
        m = maps_repo.get(conn, c["active_map_id"])
        expected = _version(m)
        if v != expected:
            raise BadRequest("Map display changed; refresh before zooming.")
        spec, segs, ops = fog_inputs(ctx, conn, c["active_map_id"])
    bounds = await asyncio.to_thread(revealed_area_bounds, ctx.fog, spec, segs, ops, x, y)
    with ctx.db.connect() as conn:
        c = campaign_for_view(conn, user, campaign_id)
        current = maps_repo.get(conn, c["active_map_id"]) if c["active_map_id"] else None
        if current is None or _version(current) != expected:
            raise BadRequest("Map display changed during zoom lookup; refresh the campaign state.")
    return JSONResponse({"ok": True, "version": expected, "bounds": bounds},
                        headers={"Cache-Control": "no-store"})


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
    ws.state.username = user["username"]
    await ctx.hub.subscribe(campaign_id, ws)
    try:
        while True:
            msg = await ws.receive_text()   # keep-alive pings from the client
            if len(msg) > 2048:
                await ws.close(code=1009)
                break
            if msg == "ping":
                ctx.hub.sync.touch(ws.state.sync_id)
                await ws.send_text('{"type":"pong"}')
            else:
                try:
                    report = json.loads(msg)
                except (ValueError,TypeError):
                    continue
                ctx.hub.sync.report(ws.state.sync_id, report)
    except WebSocketDisconnect:
        pass
    finally:
        await ctx.hub.unsubscribe(campaign_id, ws)
