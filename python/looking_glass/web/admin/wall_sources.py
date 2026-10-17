"""Reusable source API, registered only on the admin router."""

import asyncio
from typing import Annotated

from fastapi import File, UploadFile
from pydantic import BaseModel, Field

from ...repositories import wall_sources as sources_repo
from ...repositories import maps as maps_repo
from ...services import images
from ...services.pack_images import image_bytes
from ...services.foundry_import import WallImportError, parse_wall_file
from ..access import campaign_for_manage, map_for_manage
from ..deps import BadRequest, CsrfUserDep, CtxDep, UserDep
from . import notify
from .campaigns import _read_upload, apply_walls


class SourceImportIn(BaseModel):
    source_id: int = Field(gt=0)
    scene_index: int = Field(ge=0)
    use_scene_calibration: bool = True
    use_pack_image: bool = False


def _source(conn, campaign_id, source_id):
    source = sources_repo.get(conn, campaign_id, source_id)
    if source is None:
        raise BadRequest("Wall source not found in this campaign.")
    return source


def _summary(source):
    return {k: source[k] for k in ("id", "filename", "scene_count", "created_at")}


def _parse(raw, filename):
    try:
        return parse_wall_file(raw, filename)
    except (WallImportError, ValueError, TypeError, OverflowError) as exc:
        raise BadRequest(f"Cannot read wall source: {exc}") from exc


def register_routes(router, map_payload):
    @router.get("/campaigns/{campaign_id}/wall-sources")
    def list_sources(ctx: CtxDep, user: UserDep, campaign_id: int):
        with ctx.db.connect() as conn:
            campaign_for_manage(conn, user, campaign_id)
            return {"ok": True, "sources": [_summary(s) for s in
                    sources_repo.list_for_campaign(conn, campaign_id)]}

    @router.post("/campaigns/{campaign_id}/wall-sources")
    async def save_source(ctx: CtxDep, user: CsrfUserDep, campaign_id: int,
                          file: Annotated[UploadFile, File()]):
        with ctx.db.connect() as conn:
            campaign_for_manage(conn, user, campaign_id)
        raw = await _read_upload(ctx, file)
        sets = await asyncio.to_thread(_parse, raw, file.filename or "walls")
        with ctx.db.connect() as conn:
            campaign_for_manage(conn, user, campaign_id)
            source = sources_repo.save(conn, campaign_id, file.filename or "walls", raw, len(sets))
            return {"ok": True, "source": _summary(source)}

    @router.get("/maps/{map_id}/wall-sources/{source_id}")
    async def inspect_source(ctx: CtxDep, user: UserDep, map_id: int, source_id: int):
        with ctx.db.connect() as conn:
            m, _ = map_for_manage(conn, user, map_id)
            source = _source(conn, m["campaign_id"], source_id)
        sets = await asyncio.to_thread(_parse, source["raw"], source["filename"])
        scenes = []
        for index, ws in enumerate(sets):
            cal = ws.suggested_calibration(m["width"], m["height"])
            scenes.append({
                "index": index, "name": ws.name, "format": ws.source_format,
                "walls": len(ws.segments),
                "doors": sum(w.kind in ("door", "secret") for w in ws.segments),
                "scene_width": ws.scene_width, "scene_height": ws.scene_height,
                "image_available": bool(ws.image_data),
                "image_is_thumbnail": ws.image_is_thumbnail,
                "image_reference": ws.image_reference,
                "calibration": {k: getattr(cal, k) for k in
                                ("offset_x", "offset_y", "scale_x", "scale_y")},
            })
        return {"ok": True, "source": _summary(source), "scenes": scenes}

    @router.post("/maps/{map_id}/walls/from-source")
    async def import_source(ctx: CtxDep, user: CsrfUserDep, map_id: int, body: SourceImportIn):
        with ctx.db.connect() as conn:
            m, _ = map_for_manage(conn, user, map_id)
            source = _source(conn, m["campaign_id"], body.source_id)
        sets = await asyncio.to_thread(_parse, source["raw"], source["filename"])
        if body.scene_index >= len(sets):
            raise BadRequest("Wall set index out of range.")
        stored = None
        try:
            if body.use_pack_image:
                limit = int(ctx.settings.section("storage")["max_upload_mb"]) * 1024 * 1024
                raw_image = image_bytes(sets[body.scene_index], limit)
                stored = await asyncio.to_thread(images.store_map_image, raw_image,
                                                 ctx.settings.maps_dir, m["campaign_id"])
            with ctx.db.connect() as conn:
                m, _ = map_for_manage(conn, user, map_id)
                _source(conn, m["campaign_id"], body.source_id)
                old_image = m["image_file"]
                if stored:
                    maps_repo.replace_image(conn, map_id, stored.relative_path, stored.width, stored.height)
                    m = maps_repo.get(conn, map_id)
                count, scene = apply_walls(ctx, conn, m, source["raw"], source["filename"],
                                           body.scene_index, body.use_scene_calibration)
                payload = {**map_payload(ctx, conn, map_id), "imported": count, "scene": scene,
                           "source_id": source["id"]}
        except BaseException as exc:
            if stored:
                images.delete_map_image(ctx.settings.maps_dir, stored.relative_path)
            if isinstance(exc, (WallImportError, ValueError, TypeError, OverflowError)):
                raise BadRequest(f"Cannot import wall source: {exc}") from exc
            raise
        if stored:
            images.delete_map_image(ctx.settings.maps_dir, old_image)
        ctx.fog.invalidate(map_id)
        await notify.map_changed(ctx, map_id, "walls")
        return payload

    @router.delete("/campaigns/{campaign_id}/wall-sources/{source_id}")
    def delete_source(ctx: CtxDep, user: CsrfUserDep, campaign_id: int, source_id: int):
        with ctx.db.connect() as conn:
            campaign_for_manage(conn, user, campaign_id)
            _source(conn, campaign_id, source_id)
            sources_repo.delete(conn, campaign_id, source_id)
        return {"ok": True}
