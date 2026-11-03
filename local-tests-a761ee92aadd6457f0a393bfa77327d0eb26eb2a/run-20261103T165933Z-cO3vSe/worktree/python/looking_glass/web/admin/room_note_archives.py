"""Management-only retained room-note listing and explicit recovery."""

from typing import Annotated

from fastapi import Path, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field

from ...services import room_notes, room_note_recovery
from ..access import map_for_manage
from ..deps import BadRequest, CsrfUserDep, CtxDep, NotFound, UserDep


class RoomRecoveryIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    x: float = Field(ge=-1e7, le=1e7)
    y: float = Field(ge=-1e7, le=1e7)
    area_key: str = Field(min_length=64, max_length=64, strict=True)
    revision: int = Field(ge=0, strict=True)
    cache_token: str = Field(min_length=1, max_length=128, strict=True)
    walls_version: int = Field(ge=0, strict=True)
    room_notes_version: int = Field(ge=0, strict=True)
    overwrite: bool = Field(default=False, strict=True)


def register_room_note_archives(router, room_at, require_current_room):
    @router.get("/maps/{map_id}/room-note-archives")
    def list_room_note_archives(
        ctx: CtxDep, user: UserDep, map_id: int,
        limit: Annotated[int, Query(ge=1, le=200)] = 50,
        before_id: Annotated[int | None, Query(gt=0)] = None,
    ):
        with ctx.db.connect() as conn:
            conn.execute("BEGIN IMMEDIATE")
            map_for_manage(conn, user, map_id)
            room_notes.reconcile_map(ctx, conn, map_id)
            page = room_note_recovery.list_archives(conn, map_id, limit, before_id)
            return JSONResponse({"ok": True, **page}, headers={"Cache-Control": "no-store"})

    @router.post("/maps/{map_id}/room-note-archives/{archive_id}/recover")
    def recover_room_note_archive(
        ctx: CtxDep, user: CsrfUserDep, map_id: int,
        archive_id: Annotated[int, Path(gt=0)], body: RoomRecoveryIn,
    ):
        with ctx.db.connect() as conn:
            conn.execute("BEGIN IMMEDIATE")
            map_for_manage(conn, user, map_id)
            # Scope the archive before target geometry work; never expose another map's content.
            if not conn.execute(
                "SELECT 1 FROM room_note_archives WHERE map_id=? AND id=?",
                (map_id, archive_id),
            ).fetchone():
                raise NotFound("Retained room note not found on this map.")
            current = room_at(ctx, conn, map_id, body)
            require_current_room(current, body)
            try:
                room_note_recovery.recover_archive(
                    conn, map_id, archive_id, body.area_key, body.x, body.y,
                    body.revision, overwrite=body.overwrite,
                )
            except room_note_recovery.ArchiveNotFound as exc:
                raise NotFound(str(exc)) from exc
            except room_note_recovery.RecoveryConflict as exc:
                raise BadRequest(str(exc)) from exc
            updated = room_at(ctx, conn, map_id, body)
            return JSONResponse({"ok": True, **updated}, headers={"Cache-Control": "no-store"})
