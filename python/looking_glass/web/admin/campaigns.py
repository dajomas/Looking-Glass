"""Campaign, viewer-assignment and battle-map management (form posts)."""

import asyncio
import logging
import sqlite3
from contextlib import contextmanager
from typing import Annotated
from urllib.parse import quote_plus

from fastapi import APIRouter, File, Form, UploadFile, Request
from fastapi.responses import RedirectResponse, Response, FileResponse

from ... import rbac
from ...rbac import Role
from ...repositories import campaigns as campaigns_repo
from ...repositories import maps as maps_repo
from ...repositories import users as users_repo
from ...repositories import walls as walls_repo
from ...repositories import wall_sources as sources_repo
from ...services import images, campaign_backup
from ...services.map_display import activate
from ...services.foundry_import import WallImportError, parse_wall_file
from ..access import campaign_for_manage, map_for_manage
from ..context import AppContext
from ..deps import BadRequest, CsrfUserDep, CtxDep, Forbidden, UserDep
from ..templating import render
from . import notify

log = logging.getLogger(__name__)
router = APIRouter()


def _back(path: str, ok: str | None = None, err: str | None = None) -> RedirectResponse:
    if ok:
        path += f"?ok={quote_plus(ok)}"
    elif err:
        path += f"?err={quote_plus(err)}"
    return RedirectResponse(path, status_code=303)


@contextmanager
def _image_write_connection(ctx: AppContext, relative_path: str):
    """Remove a newly stored image if its database write fails.

    Pass only the path returned by this request's successful image store.
    Never pass the existing image being replaced.
    """
    try:
        with ctx.db.connect() as conn:
            yield conn
    except BaseException:
        try:
            with ctx.db.connect() as check:
                referenced = check.execute(
                    "SELECT 1 FROM maps WHERE image_file = ? LIMIT 1",
                    (relative_path,),
                ).fetchone() is not None
            if referenced:
                log.warning(
                    "Retaining map image %s after a database error: "
                    "a committed map still references it", relative_path,
                )
            else:
                images.delete_map_image(ctx.settings.maps_dir, relative_path)
        except Exception:
            log.warning(
                "Could not verify or remove map image %s after a database write failure; "
                "retaining any remaining file", relative_path, exc_info=True,
            )
        raise


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
    from ...services.foundry_import import validated_calibration
    from ...services.wall_model import Calibration
    current = None if use_scene_calibration else Calibration(
        map_row["wall_offset_x"], map_row["wall_offset_y"], map_row["wall_scale_x"], map_row["wall_scale_y"])
    cal = validated_calibration(ws, map_row["width"], map_row["height"], calibration=current)
    count = walls_repo.replace(conn, map_row["id"], ws.segments)
    if use_scene_calibration:
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
    with _image_write_connection(ctx, stored.relative_path) as conn:
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
    with _image_write_connection(ctx, stored.relative_path) as conn:
        # Serialize the compatibility check with alternate uploads and replacement.
        conn.execute("BEGIN IMMEDIATE")
        m, c = map_for_manage(conn, user, map_id)
        if (stored.width, stored.height) != (m["width"], m["height"]) and conn.execute(
                "SELECT 1 FROM double_reveal_maps WHERE map_id = ?", (map_id,)).fetchone():
            raise BadRequest(
                f"Original image must remain {m['width']} × {m['height']} pixels while "
                "alternate artwork exists. Resize the replacement to match; "
                "existing artwork and play state were not changed.")
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
    ctx.fog.invalidate(m["id"])
    if was_active:
        await notify.campaign_changed(ctx, c["id"], "active-map")
    return _back(f"/campaigns/{c['id']}", ok=f"Map '{m['name']}' deleted")


@router.post("/campaigns/{campaign_id}/backup")
def backup_campaign(ctx: CtxDep, user: CsrfUserDep, campaign_id: int):
    with ctx.db.connect() as conn:
        campaign_for_manage(conn, user, campaign_id)
        try:
            raw = campaign_backup.export_campaign(conn, campaign_id, ctx.settings.maps_dir)
        except (OSError, ValueError):
            return _back(f"/campaigns/{campaign_id}", err="Backup failed: a map image is missing or invalid")
    return Response(raw, media_type="application/zip", headers={
        "Content-Disposition": f'attachment; filename="campaign-{campaign_id}-backup.zip"',
        "Cache-Control": "no-store", "X-Content-Type-Options": "nosniff"})


@router.post("/campaigns/{campaign_id}/restore/inspect")
async def inspect_backup(request: Request, ctx: CtxDep, user: CsrfUserDep, campaign_id: int,
                         backup: Annotated[UploadFile, File()]):
    import zipfile
    with ctx.db.connect() as conn:
        campaign = campaign_for_manage(conn, user, campaign_id)
        raw = await _read_upload(ctx, backup)
        limit = int(ctx.settings.section("storage")["max_upload_mb"]) * 1024 * 1024
        try:
            conn.execute("BEGIN")
            report = campaign_backup.inspect_campaign(conn, campaign_id, raw, limit)
            token = campaign_backup.preview_token(conn, campaign_id, user["id"], raw)
        except (ValueError, KeyError, TypeError, OSError, sqlite3.DatabaseError, zipfile.BadZipFile, RuntimeError, OverflowError):
            return _back(f"/campaigns/{campaign_id}", err="Inspection failed: invalid, incompatible or oversized backup; nothing changed")
    response = render(request, "admin/backup_inspect.html", campaign=campaign, report=report, preview=token)
    response.headers["Cache-Control"] = "no-store"
    return response


@router.get("/campaigns/{campaign_id}/recovery/{name}")
def download_recovery(ctx: CtxDep, user: UserDep, campaign_id: int, name: str):
    import re
    from ..deps import NotFound
    with ctx.db.connect() as conn:
        campaign_for_manage(conn, user, campaign_id)
    if not re.fullmatch(rf"campaign-{campaign_id}-[0-9a-f]{{32}}\.zip", name):
        raise NotFound()
    path = ctx.settings.data_dir / "recovery" / name
    if not path.is_file():
        raise NotFound()
    return FileResponse(path, media_type="application/zip", filename=name,
                        headers={"Cache-Control": "no-store", "X-Content-Type-Options": "nosniff"})


@router.post("/campaigns/{campaign_id}/restore")
async def restore_campaign(request: Request, ctx: CtxDep, user: CsrfUserDep, campaign_id: int,
                           backup: Annotated[UploadFile, File()],
                           confirm: Annotated[str, Form()] = "",
                           preview: Annotated[str, Form()] = ""):
    import zipfile
    created_files = []
    old_maps = []
    try:
        with ctx.db.connect() as conn:
            conn.execute("BEGIN IMMEDIATE")
            campaign = campaign_for_manage(conn, user, campaign_id)
            if confirm.strip() != campaign["name"]:
                return _back(f"/campaigns/{campaign_id}", err="Type the campaign name to confirm restore")
            raw = await _read_upload(ctx, backup)
            old_maps = maps_repo.list_for_campaign(conn, campaign_id)
            limit = int(ctx.settings.section("storage")["max_upload_mb"]) * 1024 * 1024
            campaign_backup.verify_preview(conn, campaign_id, user["id"], raw, preview)
            campaign_backup.inspect_campaign(conn, campaign_id, raw, limit)
            recovery = campaign_backup.save_recovery(conn, campaign_id, ctx.settings.maps_dir,
                                                     ctx.settings.data_dir / "recovery", limit)
            campaign_backup.restore_campaign(conn, campaign_id, ctx.settings.maps_dir, raw, limit, created_files)
            conn.execute("UPDATE campaigns SET session_version=session_version+1 WHERE id=?", (campaign_id,))
            if conn.execute("PRAGMA foreign_key_check").fetchone():
                raise ValueError("Invalid restored references")
    except (ValueError, KeyError, TypeError, OSError, sqlite3.DatabaseError, zipfile.BadZipFile, RuntimeError, OverflowError):
        for path in created_files:
            images.delete_map_image(ctx.settings.maps_dir, path)
        return _back(f"/campaigns/{campaign_id}", err="Restore blocked: inspect the same ZIP again, check its compatibility and limits, and ensure recovery storage is writable")
    except BaseException:
        for path in created_files:
            images.delete_map_image(ctx.settings.maps_dir, path)
        raise
    for m in old_maps:
        images.delete_map_image(ctx.settings.maps_dir, m["image_file"])
        ctx.fog.invalidate(m["id"])
    await notify.campaign_changed(ctx, campaign_id, "campaign")
    response = render(request, "admin/backup_restored.html", campaign_id=campaign_id, recovery=recovery)
    response.headers["Cache-Control"] = "no-store"
    return response


@router.post("/campaigns/{campaign_id}/duplicate")
def duplicate_campaign(ctx: CtxDep, user: CsrfUserDep, campaign_id: int,
                       name: Annotated[str, Form(min_length=1, max_length=120)]):
    return _duplicate_content(ctx, user, campaign_id, name)


@router.post("/maps/{map_id}/duplicate")
def duplicate_map(ctx: CtxDep, user: CsrfUserDep, map_id: int,
                  name: Annotated[str, Form(min_length=1, max_length=120)]):
    with ctx.db.connect() as conn:
        m, campaign = map_for_manage(conn, user, map_id)
        campaign_id = campaign["id"]
    return _duplicate_content(ctx, user, campaign_id, name, map_id)


def _duplicate_content(ctx, user, campaign_id, name, map_id=None):
    from ...services.duplication import duplicate
    created = []
    try:
        with ctx.db.connect() as conn:
            conn.execute("BEGIN IMMEDIATE")
            campaign_for_manage(conn, user, campaign_id)
            if map_id is None and not rbac.can_create_campaign(user):
                raise Forbidden()
            target, mapping = duplicate(conn, campaign_id, ctx.settings.maps_dir, created,
                                        name, user["id"], map_id)
    except BaseException as exc:
        for path in created:
            images.delete_map_image(ctx.settings.maps_dir, path)
        if isinstance(exc, (ValueError, OSError, sqlite3.DatabaseError)):
            return _back(f"/campaigns/{campaign_id}", err="Copy failed: check source images and writable storage; nothing copied")
        raise
    path = f"/maps/{mapping[map_id]}" if map_id is not None else f"/campaigns/{target}"
    return _back(path, ok="Clean copy created; play state reset and not shown to players")
