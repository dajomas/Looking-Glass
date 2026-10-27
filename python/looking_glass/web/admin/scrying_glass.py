"""Admin-only, CSRF-protected lookup of a saved room name; no remote activation."""
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field
from ...services import room_notes, scrying_glass
from ..access import map_for_manage, fog_inputs
from ..deps import CtxDep, CsrfUserDep, BadRequest

router = APIRouter(prefix="/api/maps/{map_id}/scrying-glass")

class RoomLookup(BaseModel):
    model_config = ConfigDict(extra="forbid")
    x: float = Field(ge=0, allow_inf_nan=False)
    y: float = Field(ge=0, allow_inf_nan=False)
    area_key: str = Field(min_length=64, max_length=64)
    revision: int = Field(ge=0)

@router.post("/check")
def check(ctx: CtxDep, user: CsrfUserDep, map_id: int, body: RoomLookup):
    with ctx.db.connect() as conn:
        conn.execute("BEGIN")
        _, campaign = map_for_manage(conn, user, map_id)
        spec, segments, _ = fog_inputs(ctx, conn, map_id)
        if not (body.x < spec.width and body.y < spec.height):
            raise BadRequest("Point is outside the map.")
        area = ctx.fog.area_map(spec, segments)
        label = int(area.labels[int(body.y * area.scale), int(body.x * area.scale)])
        if not label:
            raise BadRequest("Select the interior of a room, not a wall.")
        key = room_notes.area_key(area, label, spec.width, spec.height)
        row = conn.execute("SELECT name,revision FROM room_notes WHERE map_id=? AND area_key=?", (map_id, key)).fetchone()
        revision = row["revision"] if row else 0
        if key != body.area_key or revision != body.revision:
            raise BadRequest("Room geometry or saved name changed. Select the room again.")
        name = row["name"] if row else ""
        campaign_name = campaign["name"]
    # Sync route runs in FastAPI's thread pool; never hold a DB transaction across HTTP.
    try:
        result = scrying_glass.lookup(ctx.settings.section("scrying_glass"), campaign_name, name)
    except scrying_glass.LookupError as exc:
        return JSONResponse({"ok": False, "error": str(exc)}, status_code=502, headers={"Cache-Control": "no-store"})
    return JSONResponse({"ok": True, **result}, headers={"Cache-Control": "no-store"})
