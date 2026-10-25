"""JSON API used by the admin map editor (static/js/admin_map_editor.js)."""

import asyncio
import math
from typing import Annotated, Literal

from fastapi import APIRouter, File, Form, UploadFile
from fastapi.responses import FileResponse, JSONResponse, Response
from pydantic import BaseModel, Field

from ...services import room_notes
from ...repositories import campaigns as campaigns_repo
from ...repositories import fog_ops as fog_repo
from ...repositories import maps as maps_repo
from ...repositories import walls as walls_repo
from ...services.wall_type_settings import disabled_for_map
from ...services.arrow_visibility import resolve_visibility
from ...services.map_display import activate, checkpoint_if_active
from ...services.foundry_import import WallImportError, parse_wall_file
from ..access import campaign_for_manage, fog_inputs, map_for_manage
from ..deps import BadRequest, CsrfUserDep, CtxDep, UserDep
from . import notify
from .campaigns import _read_upload, apply_walls
from .wall_sources import register_routes

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
    spec, boundary, ops = fog_inputs(ctx, conn, map_id)
    from ...services.door_arrows import arrows as make_arrows
    arrow_objects = make_arrows(ctx.fog, spec, boundary, ops)
    from ...services.passages import entry_kind
    from ...services.portal_presentation import visible_routes
    portal_styles = [{"x1":(s.x1-ox)*sx,"y1":(s.y1-oy)*sy,"x2":(s.x2-ox)*sx,"y2":(s.y2-oy)*sy,
                      "sides":[{"role":v["role"],"kind":entry_kind(s,i)} for i,v in enumerate(s.passage["sides"])]}
                     for s in segs if s.kind == "portal"]
    return {
        "portal_styles": portal_styles,
        "portal_routes": visible_routes(spec, segs, arrow_objects),
        "ok": True,
        "id": m["id"], "cache_token": m["cache_token"], "name": m["name"], "campaign_id": m["campaign_id"],
        "width": m["width"], "height": m["height"],
        "work_scale": scale,
        "work_width": max(1, math.ceil(m["width"] * scale)), "work_height": max(1, math.ceil(m["height"] * scale)),
        "fog_version": m["fog_version"], "walls_version": m["walls_version"],
        "walls_source": m["walls_source"],
        "door_arrow_color": m["door_arrow_color"],
        "locked_door_arrow_color": m["locked_door_arrow_color"],
        "door_arrows": [{"wall_id": a.wall_id, "kind": a.kind, "polygon": a.polygon, "side": a.side, "portal": a.portal, "exit_only": a.exit_only, "secret_origin": a.secret_origin} for a in arrow_objects],
        "managed_doors": [{"wall_id": s.id, "kind": s.kind,
            "x1": (s.x1-ox)*sx, "y1": (s.y1-oy)*sy, "x2": (s.x2-ox)*sx, "y2": (s.y2-oy)*sy}
            for s in segs if s.kind in ("locked_door", "unlocked_door")],
        "door_arrows_enabled": bool(m["door_arrows_enabled"]),
        "admin_door_arrows_enabled": bool(m["door_arrows_enabled"]),
        "viewer_door_arrows_enabled": bool(m["viewer_door_arrows_enabled"]),
        "viewer_portal_arrows_enabled": bool(m["viewer_portal_arrows_enabled"]),
        "viewer_secret_arrows_enabled": bool(m["viewer_secret_arrows_enabled"]),
        "image_version": m["image_file"],
        "disabled_wall_types": disabled_for_map(conn, m),
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
    return FileResponse(ctx.settings.maps_dir / m["image_file"], headers={"Cache-Control": "no-store"})


@router.get("/maps/{map_id}/fog.png")
async def fog_mask(ctx: CtxDep, user: UserDep, map_id: int):
    with ctx.db.connect() as conn:
        map_for_manage(conn, user, map_id)
        spec, segs, ops = fog_inputs(ctx, conn, map_id)
    png = await asyncio.to_thread(ctx.fog.admin_mask_png, spec, segs, ops)
    return Response(png, media_type="image/png", headers={"Cache-Control": "no-store"})


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
            spec, segs, ops = fog_inputs(ctx, conn, map_id)
            area = await asyncio.to_thread(ctx.fog.area_map, spec, segs)
            res = ctx.fog.describe_click(area, point.x, point.y)
            if not res.label:
                raise BadRequest("No open area at that point (clicked on a wall?).")
            info = {"area_fraction": round(res.fraction, 4), "leak_warning": res.leak_warning}
            revealed = res.label in ctx.fog.revealed_labels(area, ops)
            if (op == "reveal" and revealed) or (op == "hide" and not revealed):
                return {**_map_payload(ctx, conn, map_id), **info, "changed": False}

        if op == "undo":
            if not fog_repo.undo(conn, map_id):
                raise BadRequest("Nothing to undo.")
        else:
            fog_repo.add(conn, map_id, op, point.x if point else None, point.y if point else None, user["id"])
        maps_repo.bump_fog(conn, map_id)
        checkpoint_if_active(conn, map_id)
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
         "doors": sum(1 for w in s.segments if w.kind in ("door", "secret", "locked_door", "unlocked_door")),
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
    fog_action: Literal["restore", "reset"] | None = None


@router.post("/campaigns/{campaign_id}/active")
async def api_set_active(ctx: CtxDep, user: CsrfUserDep, campaign_id: int, body: ActiveMapIn):
    mid = body.map_id
    with ctx.db.connect() as conn:
        campaign_for_manage(conn, user, campaign_id)
        if mid is not None:
            m = maps_repo.get(conn, int(mid))
            if m is None or m["campaign_id"] != campaign_id:
                raise BadRequest("Map does not belong to this campaign.")
        try:
            activate(conn, campaign_id, mid, body.fog_action, user["id"])
        except ValueError as exc:
            raise BadRequest(str(exc))
    if mid is not None:
        ctx.fog.invalidate(mid)
    await notify.campaign_changed(ctx, campaign_id, "active-map")
    return JSONResponse({"ok": True, "active_map_id": mid})


register_routes(router, _map_payload)


from .display_options import register_display_options  # noqa: E402

register_display_options(router)


from .wall_types import register_wall_types  # noqa: E402

register_wall_types(router, _map_payload)


class DoorArrowAppearanceIn(BaseModel):
    viewer_portal_enabled: bool | None = Field(default=None, strict=True)
    viewer_secret_enabled: bool | None = Field(default=None, strict=True)
    admin_enabled: bool | None = Field(default=None, strict=True)
    viewer_enabled: bool | None = Field(default=None, strict=True)
    locked_color: str | None = Field(default=None, pattern=r"^#[0-9a-fA-F]{6}$")
    color: str | None = Field(default=None, pattern=r"^#[0-9a-fA-F]{6}$")
    enabled: bool | None = Field(default=None, strict=True)


@router.post("/maps/{map_id}/door-arrows")
async def set_door_arrows(ctx: CtxDep, user: CsrfUserDep, map_id: int, body: DoorArrowAppearanceIn):
    with ctx.db.connect() as conn:
        conn.execute("BEGIN IMMEDIATE")
        m, _ = map_for_manage(conn, user, map_id)
        color = body.color.lower() if body.color is not None else m["door_arrow_color"]
        admin_enabled, viewer_enabled = resolve_visibility(m, enabled=body.enabled,
            admin_enabled=getattr(body, "admin_enabled", None), viewer_enabled=getattr(body, "viewer_enabled", None))
        locked_color = body.locked_color.lower() if body.locked_color is not None else m["locked_door_arrow_color"]
        portal_update = getattr(body, "viewer_portal_enabled", None)
        secret_update = getattr(body, "viewer_secret_enabled", None)
        portal_enabled = bool(m["viewer_portal_arrows_enabled"]) if portal_update is None else portal_update
        secret_enabled = bool(m["viewer_secret_arrows_enabled"]) if secret_update is None else secret_update
        conn.execute("UPDATE maps SET viewer_portal_arrows_enabled = ?, viewer_secret_arrows_enabled = ? WHERE id = ?",
                     (int(portal_enabled), int(secret_enabled), map_id))
        conn.execute("UPDATE maps SET door_arrow_color = ?, door_arrows_enabled = ?, viewer_door_arrows_enabled = ?, locked_door_arrow_color = ? WHERE id = ?",
                     (color, int(admin_enabled), int(viewer_enabled), locked_color, map_id))
        viewer_changed = (portal_enabled != bool(m["viewer_portal_arrows_enabled"]) or
                          secret_enabled != bool(m["viewer_secret_arrows_enabled"]) or viewer_enabled != bool(m["viewer_door_arrows_enabled"]) or
                          color != m["door_arrow_color"] or locked_color != m["locked_door_arrow_color"])
        if viewer_changed:
            maps_repo.bump_fog(conn, map_id)
        payload = _map_payload(ctx, conn, map_id)
    if viewer_changed:
        await notify.map_changed(ctx, map_id, "appearance")
    return payload


@router.get("/maps/{map_id}/door-arrows.png")
async def door_arrows(ctx: CtxDep, user: UserDep, map_id: int):
    with ctx.db.connect() as conn:
        map_for_manage(conn, user, map_id)
        spec, segs, ops = fog_inputs(ctx, conn, map_id)
    png = await asyncio.to_thread(ctx.fog.door_arrows_png, spec, segs, ops)
    return Response(png, media_type="image/png", headers={"Cache-Control": "no-store"})


class DoorArrowClickIn(Point):
    cache_token: str = Field(max_length=128)
    walls_version: int = Field(ge=0)
    fog_version: int = Field(ge=0)


@router.post("/maps/{map_id}/door-arrows/reveal")
async def reveal_door_arrow(ctx: CtxDep, user: CsrfUserDep, map_id: int, body: DoorArrowClickIn):
    from ...services.door_arrows import target_at
    with ctx.db.connect() as conn:
        # Serialize validation and mutation so duplicate/stale clicks cannot reveal twice.
        conn.execute("BEGIN IMMEDIATE")
        m, _ = map_for_manage(conn, user, map_id)
        if (m["cache_token"], m["walls_version"], m["fog_version"]) != (
                body.cache_token, body.walls_version, body.fog_version):
            raise BadRequest("The map changed. Refresh and click the arrow again.")
        spec, segs, ops = fog_inputs(ctx, conn, map_id)
        target = target_at(ctx.fog, spec, segs, ops, body.x, body.y)
        if target is None:
            raise BadRequest("No enabled door arrow at that point. Refresh the map.")
        area = ctx.fog.area_map(spec, segs)
        res = ctx.fog.describe_click(area, *target)
        if res.label in ctx.fog.revealed_labels(area, ops):
            return {**_map_payload(ctx, conn, map_id), "area_fraction": round(res.fraction,4), "leak_warning": res.leak_warning}
        fog_repo.add(conn, map_id, "reveal", *target, user["id"])
        maps_repo.bump_fog(conn, map_id)
        checkpoint_if_active(conn, map_id)
        payload = {**_map_payload(ctx, conn, map_id), "area_fraction": round(res.fraction, 4),
                   "leak_warning": res.leak_warning}
    await notify.map_changed(ctx, map_id, "fog")
    return payload


from .door_states import register_door_states  # noqa: E402
register_door_states(router, _map_payload)


from .map_transitions import router as transitions_router
router.include_router(transitions_router)


class RoomPoint(Point):
    pass

class RoomNoteIn(Point):
    area_key: str = Field(min_length=64, max_length=64)
    name: str = Field(min_length=1, max_length=200)
    markdown: str = Field(default="", max_length=100000)
    revision: int = Field(ge=0)


def _room_at(ctx, conn, map_id, point):
    spec, segments, ops = fog_inputs(ctx, conn, map_id)
    if not (0 <= point.x < spec.width and 0 <= point.y < spec.height):
        raise BadRequest("Point is outside the map.")
    area = ctx.fog.area_map(spec, segments)
    # Room selection does not snap wall pixels into adjacent rooms.
    label = int(area.labels[int(point.y * area.scale), int(point.x * area.scale)])
    if not label:
        raise BadRequest("Select the interior of a room, not a wall.")
    key = room_notes.area_key(area, label, spec.width, spec.height)
    return room_notes.payload(conn, map_id, key, label in ctx.fog.revealed_labels(area, ops))


@router.post("/maps/{map_id}/room-at")
def room_at(ctx: CtxDep, user: CsrfUserDep, map_id: int, point: RoomPoint):
    with ctx.db.connect() as conn:
        map_for_manage(conn, user, map_id)
        return {"ok": True, **_room_at(ctx, conn, map_id, point)}


@router.post("/maps/{map_id}/room-notes")
def save_room_note(ctx: CtxDep, user: CsrfUserDep, map_id: int, body: RoomNoteIn):
    with ctx.db.connect() as conn:
        map_for_manage(conn, user, map_id)
        conn.execute("BEGIN IMMEDIATE")
        current = _room_at(ctx, conn, map_id, body)
        if current["area_key"] != body.area_key or current["revision"] != body.revision:
            raise BadRequest("Room geometry or notes changed. Select the room again before saving.")
        if not body.name.strip():
            raise BadRequest("A room name is required.")
        conn.execute("""INSERT INTO room_notes(map_id,area_key,x,y,name,markdown) VALUES(?,?,?,?,?,?)
            ON CONFLICT(map_id,area_key) DO UPDATE SET name=excluded.name,
            markdown=excluded.markdown,revision=room_notes.revision+1""",
            (map_id, body.area_key, body.x, body.y, body.name.strip(), body.markdown))
        return {"ok": True, **_room_at(ctx, conn, map_id, body)}


@router.get("/maps/{map_id}/room-notes")
def list_room_notes(ctx: CtxDep, user: UserDep, map_id: int):
    with ctx.db.connect() as conn:
        map_for_manage(conn, user, map_id)
        result = []
        for row in conn.execute("SELECT * FROM room_notes WHERE map_id=? ORDER BY name", (map_id,)):
            try:
                current = _room_at(ctx, conn, map_id, Point(x=row["x"], y=row["y"]))
            except BadRequest:
                current = None
            active = current is not None and current["area_key"] == row["area_key"]
            result.append({"area_key": row["area_key"], "name": row["name"], "x": row["x"], "y": row["y"],
                           "active": active, "revealed": active and current["revealed"]})
        return {"ok": True, "rooms": result}


@router.get("/maps/{map_id}/room-note-library")
def room_note_library(ctx: CtxDep, user: UserDep, map_id: int):
    from ...services import room_note_import
    with ctx.db.connect() as conn:
        map_for_manage(conn, user, map_id)
        return {"ok": True, "entries": room_note_import.list_entries(conn, map_id)}


@router.post("/maps/{map_id}/room-note-library/import")
async def import_room_note_library(ctx: CtxDep, user: CsrfUserDep, map_id: int,
                                   file: Annotated[UploadFile, File()]):
    from ...services import room_note_import
    with ctx.db.connect() as conn:
        map_for_manage(conn, user, map_id)
    raw = await file.read(room_note_import.MAX_BYTES + 1)
    try:
        parsed = room_note_import.parse(raw)
    except room_note_import.ImportError as exc:
        raise BadRequest(str(exc))
    with ctx.db.connect() as conn:
        map_for_manage(conn, user, map_id)
        conn.execute("BEGIN IMMEDIATE")
        added = room_note_import.store(conn, map_id, parsed["entries"])
        return {"ok": True, "added": added, "sections": len(parsed["entries"]),
                "heading_level": parsed["level"], "ignored_preamble": parsed["ignored_preamble"],
                "entries": room_note_import.list_entries(conn, map_id)}
