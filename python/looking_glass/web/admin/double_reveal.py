"""DM-only double reveal API. Raw alternate artwork is never mounted on viewer app."""
import asyncio
import io
from typing import Annotated, Literal
from fastapi import APIRouter, File, Form, UploadFile
from fastapi.responses import FileResponse, Response
from pydantic import BaseModel, ConfigDict, Field
from PIL import Image
from ...services import double_reveal as service, images
from ..access import map_for_manage, fog_inputs
from ..deps import CtxDep, UserDep, CsrfUserDep, BadRequest
from .campaigns import _read_upload
from . import notify

router = APIRouter(prefix="/api/maps/{map_id}/double-reveal")

class Stamp(BaseModel):
    model_config = ConfigDict(extra="forbid")
    cache_token: str
    walls_version: int = Field(ge=0)
    fog_version: int = Field(ge=0)
    image_revision: int = Field(ge=0)

class Configure(Stamp):
    x: float = Field(ge=0, allow_inf_nan=False)
    y: float = Field(ge=0, allow_inf_nan=False)
    revision: int = Field(ge=0)
    enabled: bool = Field(strict=True)
    destination_map_id: int | None = Field(default=None, gt=0)

class Appearance(Stamp):
    area_key: str = Field(min_length=64, max_length=64)
    revision: int = Field(ge=1)
    true_active: bool = Field(strict=True)

class Travel(Stamp):
    area_key: str = Field(min_length=64, max_length=64)
    revision: int = Field(ge=1)
    expected_active_map_id: int = Field(gt=0)


def snapshot(ctx, conn, map_id):
    spec, segs, ops = fog_inputs(ctx, conn, map_id)
    result = service.listing(conn, ctx.fog, spec, segs, ops)
    cid = conn.execute("SELECT campaign_id FROM maps WHERE id=?", (map_id,)).fetchone()[0]
    active = conn.execute("SELECT active_map_id FROM campaigns WHERE id=?", (cid,)).fetchone()[0]
    return dict(ok=True, **result, cache_token=spec.cache_token, walls_version=spec.walls_version,
        fog_version=spec.fog_version, active_map_id=active,
        maps=[dict(r) for r in conn.execute("SELECT id,name FROM maps WHERE campaign_id=? AND id!=? ORDER BY name,id", (cid, map_id))])


def checked(ctx, conn, user, map_id, body):
    m, _ = map_for_manage(conn, user, map_id)
    image = conn.execute("SELECT revision FROM double_reveal_maps WHERE map_id=?", (map_id,)).fetchone()
    if (body.cache_token, body.walls_version, body.fog_version, body.image_revision) != (
            m["cache_token"], m["walls_version"], m["fog_version"], image[0] if image else 0):
        raise ValueError("Map or appearance changed. Refresh and select the room again.")
    return m, *fog_inputs(ctx, conn, map_id)


@router.get("")
def get_state(ctx: CtxDep, user: UserDep, map_id: int):
    with ctx.db.connect() as conn:
        conn.execute("BEGIN")
        map_for_manage(conn, user, map_id)
        return snapshot(ctx, conn, map_id)


@router.get("/room")
def get_room(ctx: CtxDep, user: UserDep, map_id: int, x: float, y: float):
    with ctx.db.connect() as conn:
        conn.execute("BEGIN")
        map_for_manage(conn, user, map_id)
        spec, segs, ops = fog_inputs(ctx, conn, map_id)
        area = ctx.fog.area_map(spec, segs)
        try: label, key = service.locate(area, spec, x, y)
        except ValueError as exc: raise BadRequest(str(exc))
        result = snapshot(ctx, conn, map_id)
        selected = next((r for r in result["rooms"] if r["area_key"] == key), None)
        result["selected"] = selected or dict(area_key=key, x=x, y=y, revision=0, true_active=0,
            destination_map_id=None, name="", revealed=label in ctx.fog.revealed_labels(area, ops), valid_geometry=True)
        return result


@router.get("/room-mask")
def room_mask(ctx: CtxDep, user: UserDep, map_id: int, x: float, y: float):
    from ...services.room_notes import edit_mask_png
    with ctx.db.connect() as conn:
        conn.execute("BEGIN")
        map_for_manage(conn, user, map_id)
        spec, segs, _ = fog_inputs(ctx, conn, map_id)
        area = ctx.fog.area_map(spec, segs)
        try: label, _ = service.locate(area, spec, x, y)
        except ValueError as exc: raise BadRequest(str(exc))
        png = edit_mask_png(area, label)
    return Response(png, media_type="image/png", headers={"Cache-Control": "no-store"})


@router.post("/image")
async def upload_image(ctx: CtxDep, user: CsrfUserDep, map_id: int, file: Annotated[UploadFile, File()],
        cache_token: Annotated[str, Form()], walls_version: Annotated[int, Form(ge=0)],
        fog_version: Annotated[int, Form(ge=0)], image_revision: Annotated[int, Form(ge=0)]):
    with ctx.db.connect() as conn:
        map_for_manage(conn, user, map_id)
    raw = await _read_upload(ctx, file)
    stored = None
    try:
        with ctx.db.connect() as conn:
            conn.execute("BEGIN IMMEDIATE")
            stamp = Stamp(cache_token=cache_token, walls_version=walls_version, fog_version=fog_version, image_revision=image_revision)
            m, _, _, _ = checked(ctx, conn, user, map_id, stamp)
            stored = await asyncio.to_thread(images.store_map_image, raw, ctx.settings.maps_dir, m["campaign_id"])
            if (stored.width, stored.height) != (m["width"], m["height"]):
                raise ValueError(f"Alternate image must be exactly {m['width']} × {m['height']} pixels, aligned with the original.")
            conn.execute("""INSERT INTO double_reveal_maps(map_id,image_file) VALUES(?,?)
                ON CONFLICT(map_id) DO UPDATE SET image_file=excluded.image_file,revision=double_reveal_maps.revision+1""",
                (map_id, stored.relative_path))
            result = snapshot(ctx, conn, map_id)
    except (ValueError, OSError) as exc:
        if stored: images.delete_map_image(ctx.settings.maps_dir, stored.relative_path)
        raise BadRequest(str(exc))
    except BaseException:
        if stored: images.delete_map_image(ctx.settings.maps_dir, stored.relative_path)
        raise
    # Preserve replaced files for in-flight render and backup readers.
    await notify.map_changed(ctx, map_id, "appearance")
    return result


@router.get("/artwork")
async def artwork(ctx: CtxDep, user: UserDep, map_id: int, appearance: Literal["current", "initial", "true"] = "current"):
    with ctx.db.connect() as conn:
        conn.execute("BEGIN")
        map_for_manage(conn, user, map_id)
        spec, segs, _ = fog_inputs(ctx, conn, map_id)
    if appearance == "initial":
        return FileResponse(spec.image_path, headers={"Cache-Control": "no-store"})
    if appearance == "true":
        if spec.alternate_image_path is None: raise BadRequest("Upload an alternate image first.")
        return FileResponse(spec.alternate_image_path, headers={"Cache-Control": "no-store"})
    def render():
        with Image.open(spec.image_path) as src:
            img = service.composite(ctx.fog, spec, segs, src.convert("RGB"))
        out = io.BytesIO(); img.save(out, "PNG"); return out.getvalue()
    png = await asyncio.to_thread(render)
    return Response(png, media_type="image/png", headers={"Cache-Control": "no-store"})


@router.post("/room")
async def configure_room(ctx: CtxDep, user: CsrfUserDep, map_id: int, body: Configure):
    with ctx.db.connect() as conn:
        conn.execute("BEGIN IMMEDIATE")
        try:
            _, spec, segs, _ = checked(ctx, conn, user, map_id, body)
            service.configure(conn, spec, ctx.fog.area_map(spec, segs), body.x, body.y, body.revision, body.enabled, body.destination_map_id)
        except ValueError as exc: raise BadRequest(str(exc))
        result = snapshot(ctx, conn, map_id)
    await notify.map_changed(ctx, map_id, "appearance")
    return result


@router.post("/appearance")
async def change_appearance(ctx: CtxDep, user: CsrfUserDep, map_id: int, body: Appearance):
    with ctx.db.connect() as conn:
        conn.execute("BEGIN IMMEDIATE")
        try:
            _, spec, segs, _ = checked(ctx, conn, user, map_id, body)
            service.change(conn, spec, ctx.fog.area_map(spec, segs), body.area_key, body.revision, body.true_active)
        except ValueError as exc: raise BadRequest(str(exc))
        result = snapshot(ctx, conn, map_id)
    await notify.map_changed(ctx, map_id, "appearance")
    return result


@router.post("/undo")
async def undo_appearance(ctx: CtxDep, user: CsrfUserDep, map_id: int, body: Stamp):
    with ctx.db.connect() as conn:
        conn.execute("BEGIN IMMEDIATE")
        try:
            _, spec, segs, _ = checked(ctx, conn, user, map_id, body)
            service.undo(conn, spec, ctx.fog.area_map(spec, segs))
        except ValueError as exc: raise BadRequest(str(exc))
        result = snapshot(ctx, conn, map_id)
    await notify.map_changed(ctx, map_id, "appearance")
    return result


@router.delete("/rooms/{area_key}")
async def remove_configuration(ctx: CtxDep, user: CsrfUserDep, map_id: int, area_key: str, body: Stamp):
    with ctx.db.connect() as conn:
        conn.execute("BEGIN IMMEDIATE")
        try: checked(ctx, conn, user, map_id, body)
        except ValueError as exc: raise BadRequest(str(exc))
        conn.execute("DELETE FROM double_reveal_rooms WHERE map_id=? AND area_key=?", (map_id, area_key))
        result = snapshot(ctx, conn, map_id)
    await notify.map_changed(ctx, map_id, "appearance")
    return result


@router.post("/travel")
async def travel(ctx: CtxDep, user: CsrfUserDep, map_id: int, body: Travel):
    with ctx.db.connect() as conn:
        conn.execute("BEGIN IMMEDIATE")
        try:
            _, spec, segs, ops = checked(ctx, conn, user, map_id, body)
            target, campaign_id = service.navigate(conn, ctx.fog, spec, segs, ops, body.area_key, body.revision, body.expected_active_map_id)
        except ValueError as exc: raise BadRequest(str(exc))
    await notify.campaign_changed(ctx, campaign_id, "active-map")
    return dict(ok=True, map_id=target, editor_url=f"/maps/{target}")
