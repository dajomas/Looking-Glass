"""Dedicated manage-authorized wall editor; mounted only on the admin app."""

import base64
from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel, Field

from ...repositories import maps as maps_repo
from ...repositories import walls as walls_repo
from ...repositories import wall_sources as sources_repo
from ...services.uvtt_export import MAX_SEGMENTS, encode_uvtt, export_uvtt, rows_for, validate_segments
from ...services.wall_model import WallSegment
from ..access import map_for_manage
from ..deps import BadRequest, CsrfUserDep, CtxDep, UserDep
from ..templating import render
from . import notify

router = APIRouter()


class WallEditIn(BaseModel):
    walls_version: int = Field(ge=0)
    cache_token: str = Field(min_length=1, max_length=128)
    walls: list[list[Any]] = Field(max_length=MAX_SEGMENTS)
    pixels_per_grid: float = Field(default=70, gt=0, le=1e7, allow_inf_nan=False)


class DraftExportIn(WallEditIn):
    width: int = Field(gt=0, le=1000000)
    height: int = Field(gt=0, le=1000000)
    image_version: str = Field(min_length=1, max_length=4096)
    include_image: bool = False


def _image_segments(conn, m):
    sx, sy, ox, oy = m["wall_scale_x"], m["wall_scale_y"], m["wall_offset_x"], m["wall_offset_y"]
    return [WallSegment((s.x1 - ox) * sx, (s.y1 - oy) * sy, (s.x2 - ox) * sx, (s.y2 - oy) * sy,
                        s.kind, s.blocks, passage=s.passage) for s in walls_repo.list_for_map(conn, m["id"], designed=True)]


def _payload(conn, m):
    return {"ok": True, "id": m["id"], "name": m["name"], "campaign_id": m["campaign_id"],
            "width": m["width"], "height": m["height"], "cache_token": m["cache_token"],
            "walls_version": m["walls_version"], "image_version": m["image_file"],
            "walls": rows_for(_image_segments(conn, m))}


def _limit(ctx):
    return int(ctx.settings.section("storage")["max_upload_mb"]) * 1024 * 1024


def _image(ctx, m):
    path = ctx.settings.maps_dir / m["image_file"]
    if path.stat().st_size * 4 // 3 > _limit(ctx):
        raise BadRequest("Embedded image exceeds storage.max_upload_mb; export walls only.")
    return base64.b64encode(path.read_bytes()).decode("ascii")


def _download(ctx, map_id, segments, width, height, name, ppg, image=""):
    try:
        raw = encode_uvtt(export_uvtt(segments, width, height, name, ppg, image))
    except ValueError as exc:
        raise BadRequest(str(exc)) from exc
    if len(raw) > _limit(ctx):
        raise BadRequest("Export exceeds storage.max_upload_mb; export walls only or fewer walls.")
    return Response(raw, media_type="application/json", headers={
        "Content-Disposition": f'attachment; filename="map-{map_id}-walls.uvtt"', "Cache-Control": "no-store"})


@router.get("/maps/{map_id}/walls")
def editor_page(request: Request, ctx: CtxDep, user: UserDep, map_id: int):
    with ctx.db.connect() as conn:
        m, campaign = map_for_manage(conn, user, map_id)
    return render(request, "admin/wall_editor.html", map=m, campaign=campaign)


@router.get("/api/maps/{map_id}/wall-editor")
def editor_state(ctx: CtxDep, user: UserDep, map_id: int):
    with ctx.db.connect() as conn:
        conn.execute("BEGIN")
        m, _ = map_for_manage(conn, user, map_id)
        return JSONResponse(_payload(conn, m), headers={"Cache-Control": "no-store"})


@router.post("/api/maps/{map_id}/wall-editor")
async def save_editor(ctx: CtxDep, user: CsrfUserDep, map_id: int, body: WallEditIn):
    with ctx.db.connect() as conn:
        map_for_manage(conn, user, map_id)
    try:
        segments = validate_segments(body.walls)
    except ValueError as exc:
        raise BadRequest(str(exc)) from exc
    with ctx.db.connect() as conn:
        conn.execute("BEGIN IMMEDIATE")
        m, _ = map_for_manage(conn, user, map_id)
        if m["walls_version"] != body.walls_version or m["cache_token"] != body.cache_token:
            return JSONResponse({"ok": False, "error": "Walls, alignment or artwork changed in another tab. "
                                 "Download your draft, then reload before saving."}, status_code=409)
        try:
            raw = encode_uvtt(export_uvtt(segments, m["width"], m["height"], m["name"], body.pixels_per_grid))
        except ValueError as exc:
            raise BadRequest(str(exc)) from exc
        if len(raw) > _limit(ctx):
            raise BadRequest("Edited UVTT exceeds storage.max_upload_mb; reduce the wall count.")
        filename = f"map-{map_id}-walls.uvtt"
        source = sources_repo.save(conn, m["campaign_id"], filename, raw, 1)
        walls_repo.replace(conn, map_id, segments)
        maps_repo.set_calibration(conn, map_id, 0, 0, 1, 1, bool(m["doors_block"]))
        maps_repo.set_walls_source(conn, map_id, filename)
        payload = _payload(conn, maps_repo.get(conn, map_id))
        payload["source_id"] = source["id"]
    ctx.fog.invalidate(map_id)
    await notify.map_changed(ctx, map_id, "walls")
    return payload


@router.get("/api/maps/{map_id}/walls.uvtt")
def download_uvtt(ctx: CtxDep, user: UserDep, map_id: int, include_image: bool = False,
                  pixels_per_grid: float = 70):
    with ctx.db.connect() as conn:
        conn.execute("BEGIN")
        m, _ = map_for_manage(conn, user, map_id)
        return _download(ctx, map_id, _image_segments(conn, m), m["width"], m["height"], m["name"],
                         pixels_per_grid, _image(ctx, m) if include_image else "")


@router.post("/api/maps/{map_id}/wall-editor/export")
def export_draft(ctx: CtxDep, user: CsrfUserDep, map_id: int, body: DraftExportIn):
    with ctx.db.connect() as conn:
        conn.execute("BEGIN")
        m, _ = map_for_manage(conn, user, map_id)
        image = ""
        if body.include_image:
            if (m["cache_token"] != body.cache_token or m["image_file"] != body.image_version
                    or m["width"] != body.width or m["height"] != body.height):
                return JSONResponse({"ok": False, "error": "Artwork changed. Download this draft "
                                     "without the image, then reload."}, status_code=409)
            image = _image(ctx, m)
        try:
            segments = validate_segments(body.walls)
        except ValueError as exc:
            raise BadRequest(str(exc)) from exc
        return _download(ctx, map_id, segments, body.width, body.height, m["name"], body.pixels_per_grid, image)
