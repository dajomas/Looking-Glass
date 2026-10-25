"""Campaign, viewer-assignment and battle-map management (form posts)."""

import asyncio
import sqlite3
from typing import Annotated
from urllib.parse import quote_plus

from fastapi import APIRouter, File, Form, UploadFile
from fastapi.responses import RedirectResponse

from ... import rbac
from ...rbac import Role
from ...repositories import campaigns as campaigns_repo
from ...repositories import maps as maps_repo
from ...repositories import users as users_repo
from ...repositories import walls as walls_repo
from ...repositories import wall_sources as sources_repo
from ...services import images
from ...services.map_display import activate
from ...services.foundry_import import WallImportError, parse_wall_file
from ..access import campaign_for_manage, map_for_manage
from ..context import AppContext
from ..deps import BadRequest, CsrfUserDep, CtxDep, Forbidden
from . import notify

router = APIRouter()


def _back(path: str, ok: str | None = None, err: str | None = None) -> RedirectResponse:
    if ok:
        path += f"?ok={quote_plus(ok)}"
    elif err:
        path += f"?err={quote_plus(err)}"
    return RedirectResponse(path, status_code=303)


async def _read_upload(ctx: AppContext, upload: UploadFile) -> bytes:
    limit = int(ctx.settings.section("storage")["max_upload_mb"]) * 1024 * 1024
    raw = await upload.read(limit + 1)
    if len(raw) > limit:
        raise BadRequest(f"File too large (max {limit // 1024 // 1024} MB).")
    return raw


def apply_walls(ctx: AppContext, conn: sqlite3.Connection, map_row: sqlite3.Row, raw: bytes, filename: str,
                scene_index: int = 0, use_scene_calibration: bool = True) -> tuple[int, str]:
    """Parse a wall file and store it on a map. Returns (segment_count, scene_name)."""
    sets = parse_wall_file(raw, filename)
    if not 0 <= scene_index < len(sets):
        raise BadRequest(f"Scene index {scene_index} out of range (file contains {len(sets)} scenes).")
    ws = sets[scene_index]
    count = walls_repo.replace(conn, map_row["id"], ws.segments)
    if use_scene_calibration:
        cal = ws.suggested_calibration(map_row["width"], map_row["height"])
        maps_repo.set_calibration(conn, map_row["id"], cal.offset_x, cal.offset_y, cal.scale_x, cal.scale_y,
                                  bool(map_row["doors_block"]))
    maps_repo.set_walls_source(conn, map_row["id"], f"{ws.source_format}: {filename} [{ws.name}]")
    ctx.fog.invalidate(map_row["id"])
    from ...services.room_notes import reconcile_map
    reconcile_map(ctx, conn, map_row["id"])
    return count, ws.name


# --------------------------------------------------------------------------- campaigns
@router.post("/campaigns")
def create_campaign(ctx: CtxDep, user: CsrfUserDep,
                    name: Annotated[str, Form(min_length=1, max_length=120)],
                    description: Annotated[str, Form(max_length=2000)] = ""):
    if not rbac.can_create_campaign(user):
        raise Forbidden()
    with ctx.db.connect() as conn:
        cid = campaigns_repo.create(conn, name, description, user["id"])
    return _back(f"/campaigns/{cid}", ok="Campaign created")


@router.post("/campaigns/{campaign_id}/update")
async def update_campaign(ctx: CtxDep, user: CsrfUserDep, campaign_id: int,
                          name: Annotated[str, Form(min_length=1, max_length=120)],
                          description: Annotated[str, Form(max_length=2000)] = "",
                          owner_id: Annotated[int | None, Form()] = None):
    with ctx.db.connect() as conn:
        campaign_for_manage(conn, user, campaign_id)
        if owner_id is not None:
            if not rbac.can_manage_users(user):
                raise Forbidden("Only a superadmin can transfer a campaign.")
            owner = users_repo.get(conn, owner_id)
            if owner is None or owner["role"] == Role.VIEWER:
                raise BadRequest("Owner must be an admin or superadmin.")
            campaigns_repo.remove_viewer(conn, campaign_id, owner_id)
        campaigns_repo.update(conn, campaign_id, name, description, owner_id)
    await notify.campaign_changed(ctx, campaign_id, "campaign")
    return _back(f"/campaigns/{campaign_id}", ok="Campaign saved")


@router.post("/campaigns/{campaign_id}/delete")
async def delete_campaign(ctx: CtxDep, user: CsrfUserDep, campaign_id: int,
                          confirm: Annotated[str, Form()] = ""):
    with ctx.db.connect() as conn:
        c = campaign_for_manage(conn, user, campaign_id)
        if confirm.strip() != c["name"]:
            return _back(f"/campaigns/{campaign_id}", err="Type the campaign name to confirm deletion")
        maps = maps_repo.list_for_campaign(conn, campaign_id)
        campaigns_repo.delete(conn, campaign_id)
    for m in maps:
        images.delete_map_image(ctx.settings.maps_dir, m["image_file"])
        ctx.fog.invalidate(m["id"])
    await notify.campaign_changed(ctx, campaign_id, "deleted")
    return _back("/", ok=f"Campaign '{c['name']}' deleted")


@router.post("/campaigns/{campaign_id}/active")
async def set_active(ctx: CtxDep, user: CsrfUserDep, campaign_id: int,
                     map_id: Annotated[str, Form()] = "",
                     fog_action: Annotated[str, Form()] = ""):
    with ctx.db.connect() as conn:
        campaign_for_manage(conn, user, campaign_id)
        try:
            mid = int(map_id) if map_id else None
        except ValueError as exc:
            raise BadRequest("Invalid map ID.") from exc
        if mid is not None:
            m = maps_repo.get(conn, mid)
            if m is None or m["campaign_id"] != campaign_id:
                raise BadRequest("Map does not belong to this campaign.")
        try:
            activate(conn, campaign_id, mid, fog_action, user["id"])
        except ValueError as exc:
            raise BadRequest(str(exc))
    if mid is not None:
        ctx.fog.invalidate(mid)
    await notify.campaign_changed(ctx, campaign_id, "active-map")
    return _back(f"/campaigns/{campaign_id}", ok="Viewer screen updated" if mid else "Viewer screen blanked")


# --------------------------------------------------------------------------- viewers
@router.post("/campaigns/{campaign_id}/viewers/add")
async def add_viewer(ctx: CtxDep, user: CsrfUserDep, campaign_id: int, user_id: Annotated[int, Form()]):
    with ctx.db.connect() as conn:
        c = campaign_for_manage(conn, user, campaign_id)
        target = users_repo.get(conn, user_id)
        if target is None or not target["active"]:
            raise BadRequest("Unknown or inactive user.")
        if target["id"] == c["owner_id"]:
            raise BadRequest("The campaign owner already has access.")
        campaigns_repo.add_viewer(conn, campaign_id, user_id, user["id"])
    return _back(f"/campaigns/{campaign_id}", ok=f"{target['username']} can now view this campaign")


@router.post("/campaigns/{campaign_id}/viewers/{user_id}/remove")
async def remove_viewer(ctx: CtxDep, user: CsrfUserDep, campaign_id: int, user_id: int):
    with ctx.db.connect() as conn:
        campaign_for_manage(conn, user, campaign_id)
        campaigns_repo.remove_viewer(conn, campaign_id, user_id)
    await ctx.hub.kick_user(user_id)
    return _back(f"/campaigns/{campaign_id}", ok="Viewer removed")


@router.post("/campaigns/{campaign_id}/viewers/create")
async def create_viewer(ctx: CtxDep, user: CsrfUserDep, campaign_id: int,
                        username: Annotated[str, Form(min_length=2, max_length=64, pattern=r"^[A-Za-z0-9_.@-]+$")],
                        password: Annotated[str, Form()],
                        display_name: Annotated[str, Form(max_length=120)] = ""):
    sec = ctx.settings.section("security")
    if not rbac.can_create_viewers(user, bool(sec["admins_can_create_viewers"])):
        raise Forbidden("You may not create user accounts.")
    if len(password) < int(sec["min_password_length"]):
        return _back(f"/campaigns/{campaign_id}", err=f"Password must be at least {sec['min_password_length']} characters")
    with ctx.db.connect() as conn:
        campaign_for_manage(conn, user, campaign_id)
        try:
            uid = users_repo.create(conn, username, password, Role.VIEWER, display_name, created_by=user["id"],
                                    must_change_password=True)
        except sqlite3.IntegrityError:
            return _back(f"/campaigns/{campaign_id}", err=f"Username '{username}' already exists")
        campaigns_repo.add_viewer(conn, campaign_id, uid, user["id"])
    return _back(f"/campaigns/{campaign_id}", ok=f"Viewer '{username}' created and assigned")


# --------------------------------------------------------------------------- maps
@router.post("/campaigns/{campaign_id}/maps")
async def upload_map(ctx: CtxDep, user: CsrfUserDep, campaign_id: int,
                     image: Annotated[UploadFile, File()],
                     name: Annotated[str, Form(max_length=120)] = "",
                     walls: Annotated[UploadFile | None, File()] = None):
    with ctx.db.connect() as conn:
        campaign_for_manage(conn, user, campaign_id)
    raw = await _read_upload(ctx, image)
    try:
        stored = await asyncio.to_thread(images.store_map_image, raw, ctx.settings.maps_dir, campaign_id)
    except images.ImageImportError as exc:
        return _back(f"/campaigns/{campaign_id}", err=str(exc))
    map_name = name.strip() or (image.filename or "Battle map").rsplit(".", 1)[0]
    msg = f"Map '{map_name}' imported ({stored.width}x{stored.height})"
    with ctx.db.connect() as conn:
        mid = maps_repo.create(conn, campaign_id, map_name, stored.relative_path, stored.width, stored.height,
                               bool(ctx.settings.section("fog")["doors_block"]))
        if walls is not None and walls.filename:
            wraw = await _read_upload(ctx, walls)
            try:
                sets = parse_wall_file(wraw, walls.filename)
                sources_repo.save(conn, campaign_id, walls.filename, wraw, len(sets))
                if len(sets) == 1:
                    count, scene = apply_walls(ctx, conn, maps_repo.get(conn, mid), wraw, walls.filename)
                    msg += f", {count} walls from '{scene}'"
                else:
                    msg += (f", wall source saved ({len(sets)} wall sets). "
                            "Choose a source and wall set under Saved wall sources, then apply.")
            except (WallImportError, BadRequest, ValueError, TypeError, OverflowError) as exc:
                msg += f" - walls not imported: {exc}"
    return _back(f"/maps/{mid}", ok=msg)


@router.post("/maps/{map_id}/rename")
async def rename_map(ctx: CtxDep, user: CsrfUserDep, map_id: int,
                     name: Annotated[str, Form(min_length=1, max_length=120)]):
    with ctx.db.connect() as conn:
        m, c = map_for_manage(conn, user, map_id)
        maps_repo.rename(conn, map_id, name)
    return _back(f"/campaigns/{c['id']}", ok="Map renamed")


@router.post("/maps/{map_id}/move")
async def move_map(ctx: CtxDep, user: CsrfUserDep, map_id: int, direction: Annotated[int, Form()]):
    with ctx.db.connect() as conn:
        m, c = map_for_manage(conn, user, map_id)
        maps_repo.move(conn, map_id, -1 if direction < 0 else 1)
    return _back(f"/campaigns/{c['id']}")


@router.post("/maps/{map_id}/image")
async def replace_image(ctx: CtxDep, user: CsrfUserDep, map_id: int, image: Annotated[UploadFile, File()]):
    with ctx.db.connect() as conn:
        m, c = map_for_manage(conn, user, map_id)
    raw = await _read_upload(ctx, image)
    try:
        stored = await asyncio.to_thread(images.store_map_image, raw, ctx.settings.maps_dir, c["id"])
    except images.ImageImportError as exc:
        return _back(f"/maps/{map_id}", err=str(exc))
    with ctx.db.connect() as conn:
        maps_repo.replace_image(conn, map_id, stored.relative_path, stored.width, stored.height)
        from ...services.room_notes import reconcile_map
        reconcile_map(ctx, conn, map_id)
    images.delete_map_image(ctx.settings.maps_dir, m["image_file"])
    ctx.fog.invalidate(map_id)
    await notify.map_changed(ctx, map_id, "image")
    return _back(f"/maps/{map_id}", ok="Image replaced - check the wall calibration")


@router.post("/maps/{map_id}/delete")
async def delete_map(ctx: CtxDep, user: CsrfUserDep, map_id: int):
    with ctx.db.connect() as conn:
        m, c = map_for_manage(conn, user, map_id)
        was_active = c["active_map_id"] == map_id
        maps_repo.delete(conn, map_id)
    images.delete_map_image(ctx.settings.maps_dir, m["image_file"])
    ctx.fog.invalidate(map_id)
    if was_active:
        await notify.campaign_changed(ctx, c["id"], "active-map")
    return _back(f"/campaigns/{c['id']}", ok=f"Map '{m['name']}' deleted")
