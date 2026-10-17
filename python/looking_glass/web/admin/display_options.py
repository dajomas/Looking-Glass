"""Fresh, authorised restore availability for every display selection."""
import asyncio

from fastapi.responses import JSONResponse

from ...services.restore_options import checkpoint_operations, has_restorable_reveals
from ..access import fog_inputs, map_for_manage
from ..deps import BadRequest, CtxDep, UserDep


def register_display_options(router):
    @router.get("/maps/{map_id}/display-options")
    async def display_options(ctx: CtxDep, user: UserDep, map_id: int):
        with ctx.db.connect() as conn:
            m, campaign = map_for_manage(conn, user, map_id)
            spec, segments, live_ops = fog_inputs(ctx, conn, map_id)
            try:
                operations = live_ops if campaign["active_map_id"] == map_id else checkpoint_operations(conn, map_id)
            except (ValueError, TypeError, KeyError) as exc:
                raise BadRequest("Cannot read saved reveals; no display change was made.") from exc
        can_restore = await asyncio.to_thread(has_restorable_reveals, ctx.fog, spec, segments, operations)
        return JSONResponse({"ok": True, "map_id": map_id, "can_restore": can_restore},
                            headers={"Cache-Control": "no-store"})
