"""JSON API used by the admin map editor (static/js/admin_map_editor.js)."""

import asyncio
import math
from typing import Annotated

from fastapi import APIRouter, File, Form, UploadFile
from fastapi.responses import FileResponse, JSONResponse, Response
from pydantic import BaseModel, Field

from ...repositories import campaigns as campaigns_repo
from ...repositories import fog_ops as fog_repo
from ...repositories import maps as maps_repo
from ...repositories import walls as walls_repo
from ...services.foundry_import import WallImportError, parse_wall_file
from ..access import campaign_for_manage, fog_inputs, map_for_manage
from ..deps import BadRequest, CsrfUserDep, CtxDep, UserDep
from . import notify
from .campaigns import _read_upload, apply_walls

router = APIRouter(prefix="/api")


class Point(BaseModel):
    x: float = Field(ge=-1e7, le=1e7)
    y: float = Field(ge=-1e7, le=1e7)


class CalibrationIn(BaseModel):
    offset_x: float
    offset_y: float
    scale_x: float = Field(gt=0, le=100)
    scale_y: float = Field(gt=0, le=100)
    doors_block: bool = True


def _map_payload(ctx, conn, map_id: int) -> dict:
    m = maps_repo.get(conn, map_id)
    campaign = conn.execute("SELECT active_map_id FROM campaigns WHERE id = ?", (m["campaign_id"],)).fetchone()
    segs = walls_repo.list_for_map(conn, map_id)
    sx, sy, ox, oy = m["wall_scale_x"], m["wall_scale_y"], m["wall_offset_x"], m["wall_offset_y"]
    walls = [[round((s.x1 - ox) * sx, 2), round((s.y1 - oy) * sy, 2),
              round((s.x2 - ox) * sx, 2), round((s.y2 - oy) * sy, 2), s.kind, s.blocks] for s in segs]
    scale = ctx.fog.work_scale(m["width"], m["height"])
    return {
        "ok": True,
        "id": m["id"], "name": m["name"], "campaign_id": m["campaign_id"],
        "width": m["width"], "height": m["height"],
        "work_width": max(1, math.ceil(m["width"] * scale)), "work_height": max(1, math.ceil(m["height"] * scale)),
        "fog_version": m["fog_version"], "walls_version": m["walls_version"],
        "walls_source": m["walls_source"],
        "calibration": {"offset_x": ox, "offset_y": oy, "scale_x": sx, "scale_y": sy,
                        "doors_block": bool(m["doors_block"])},
        "walls": walls,
        "op_count": fog_repo.count(conn, map_id),
        "is_active": campaign["active_map_id"] == map_id,
        "live_viewers": ctx.hub.viewer_count(m["campaign_id"]),
    }


@router.get("/maps/{map_id}")
def get_map(ctx: CtxDep, user: UserDep, map_id: int):
    with ctx.db.connect() as conn:
        map_for_manage(conn, user, map_id)
        return _map_payload(ctx, conn, map_id)


@router.get("/maps/{map_id}/image")
def map_image(ctx: CtxDep, user: UserDep, map_id: int):
    with ctx.db.connect() as conn:
        m, _ = map_for_manage(conn, user, map_id)
    return FileResponse(ctx.settings.maps_dir / m["image_file"], headers={"Cache-Control": "private, max-age=86400"})


@router.get("/maps/{map_id}/fog.png")
async def fog_mask(ctx: CtxDep, user: UserDep, map_id: int):
    with ctx.db.connect() as conn:
        map_for_manage(conn, user, map_id)
        spec, segs, ops = fog_inputs(ctx, conn, map_id)
    png = await asyncio.to_thread(ctx.fog.admin_mask_png, spec, segs, ops)
    return Response(png, media_type="image/png", headers={"Cache-Control": "private, max-age=3600"})


@router.get("/maps/{map_id}/viewer-preview")
async def viewer_preview(ctx: CtxDep, user: UserDep, map_id: int):
    """Exactly what the players get for this map."""
    with ctx.db.connect() as conn:
        map_for_manage(conn, user, map_id)
        spec, segs, ops = fog_inputs(ctx, conn, map_id)
    path = await asyncio.to_thread(ctx.fog.viewer_image, spec, segs, ops)
    return FileResponse(path, media_type=ctx.fog.viewer_media_type, headers={"Cache-Control": "no-store"})


async def _fog_op(ctx, user, map_id: int, op: str, point: Point | None = None) -> dict:
    info: dict = {}
    with ctx.db.connect() as conn:
        map_for_manage(conn, user, map_id)
        if point is not None:
            spec, segs, _ = fog_inputs(ctx, conn, map_id)
            area = await asyncio.to_thread(ctx.fog.area_map, spec, segs)
            res = ctx.fog.describe_click(area, point.x, point.y)
            if not res.label:
                raise BadRequest("No open area at that point (clicked on a wall?).")
            info = {"area_fraction": round(res.fraction, 4), "leak_warning": res.leak_warning}
        if op == "undo":
            if not fog_repo.undo(conn, map_id):
                raise BadRequest("Nothing to undo.")
        else:
            fog_repo.add(conn, map_id, op, point.x if point else None, point.y if point else None, user["id"])
        maps_repo.bump_fog(conn, map_id)
        payload = {**_map_payload(ctx, conn, map_id), **info}
    await notify.map_changed(ctx, map_id, "fog")
    return payload


@router.post("/maps/{map_id}/reveal")
async def reveal(ctx: CtxDep, user: CsrfUserDep, map_id: int, point: Point):
    return await _fog_op(ctx, user, map_id, "reveal", point)


@router.post("/maps/{map_id}/hide")
async def hide(ctx: CtxDep, user: CsrfUserDep, map_id: int, point: Point):
    return await _fog_op(ctx, user, map_id, "hide", point)


@router.post("/maps/{map_id}/reveal-all")
async def reveal_all(ctx: CtxDep, user: CsrfUserDep, map_id: int):
    return await _fog_op(ctx, user, map_id, "reveal_all")


@router.post("/maps/{map_id}/reset")
async def reset(ctx: CtxDep, user: CsrfUserDep, map_id: int):
    return await _fog_op(ctx, user, map_id, "hide_all")


@router.post("/maps/{map_id}/undo")
async def undo(ctx: CtxDep, user: CsrfUserDep, map_id: int):
    return await _fog_op(ctx, user, map_id, "undo")


@router.post("/maps/{map_id}/calibration")
async def calibration(ctx: CtxDep, user: CsrfUserDep, map_id: int, body: CalibrationIn):
    with ctx.db.connect() as conn:
        map_for_manage(conn, user, map_id)
        maps_repo.set_calibration(conn, map_id, body.offset_x, body.offset_y, body.scale_x, body.scale_y,
                                  body.doors_block)
        ctx.fog.invalidate(map_id)
        payload = _map_payload(ctx, conn, map_id)
    await notify.map_changed(ctx, map_id, "walls")
    return payload


@router.post("/maps/{map_id}/walls/inspect")
async def inspect_walls(ctx: CtxDep, user: CsrfUserDep, map_id: int, file: Annotated[UploadFile, File()]):
    with ctx.db.connect() as conn:
        m, _ = map_for_manage(conn, user, map_id)
    raw = await _read_upload(ctx, file)
    try:
        sets = parse_wall_file(raw, file.filename or "")
    except WallImportError as exc:
        raise BadRequest(str(exc))
    return {"ok": True, "scenes": [
        {"index": i, "name": s.name, "format": s.source_format, "walls": len(s.segments),
         "doors": sum(1 for w in s.segments if w.kind in ("door", "secret")),
         "scene_width": s.scene_width, "scene_height": s.scene_height,
         "calibration": vars_cal(s.suggested_calibration(m["width"], m["height"]))}
        for i, s in enumerate(sets)]}


def vars_cal(c) -> dict:
    return {"offset_x": c.offset_x, "offset_y": c.offset_y, "scale_x": c.scale_x, "scale_y": c.scale_y}


@router.post("/maps/{map_id}/walls")
async def import_walls(ctx: CtxDep, user: CsrfUserDep, map_id: int, file: Annotated[UploadFile, File()],
                       scene_index: Annotated[int, Form()] = 0,
                       use_scene_calibration: Annotated[bool, Form()] = True):
    raw = await _read_upload(ctx, file)
    with ctx.db.connect() as conn:
        m, _ = map_for_manage(conn, user, map_id)
        try:
            count, scene = apply_walls(ctx, conn, m, raw, file.filename or "walls", scene_index, use_scene_calibration)
        except WallImportError as exc:
            raise BadRequest(str(exc))
        payload = {**_map_payload(ctx, conn, map_id), "imported": count, "scene": scene}
    await notify.map_changed(ctx, map_id, "walls")
    return payload


@router.delete("/maps/{map_id}/walls")
async def clear_walls(ctx: CtxDep, user: CsrfUserDep, map_id: int):
    with ctx.db.connect() as conn:
        map_for_manage(conn, user, map_id)
        walls_repo.clear(conn, map_id)
        maps_repo.set_walls_source(conn, map_id, "")
        ctx.fog.invalidate(map_id)
        payload = _map_payload(ctx, conn, map_id)
    await notify.map_changed(ctx, map_id, "walls")
    return payload


class ActiveMapIn(BaseModel):
    map_id: int | None = None


@router.post("/campaigns/{campaign_id}/active")
async def api_set_active(ctx: CtxDep, user: CsrfUserDep, campaign_id: int, body: ActiveMapIn):
    mid = body.map_id
    with ctx.db.connect() as conn:
        campaign_for_manage(conn, user, campaign_id)
        if mid is not None:
            m = maps_repo.get(conn, int(mid))
            if m is None or m["campaign_id"] != campaign_id:
                raise BadRequest("Map does not belong to this campaign.")
        campaigns_repo.set_active_map(conn, campaign_id, int(mid) if mid is not None else None)
    await notify.campaign_changed(ctx, campaign_id, "active-map")
    return JSONResponse({"ok": True, "active_map_id": mid})
