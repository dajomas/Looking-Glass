"""Authorised, CSRF-protected wall-type boundary settings."""
from typing import Literal

from pydantic import BaseModel

from ...services.wall_type_settings import save_disabled
from ..access import map_for_manage
from ..deps import CtxDep, CsrfUserDep
from . import notify


class WallTypesIn(BaseModel):
    disabled_wall_types: list[Literal["wall", "door", "secret", "window", "invisible", "ethereal"]]


def register_wall_types(router, map_payload):
    @router.post("/maps/{map_id}/wall-types")
    async def apply_wall_types(ctx: CtxDep, user: CsrfUserDep, map_id: int, body: WallTypesIn):
        with ctx.db.connect() as conn:
            map_for_manage(conn, user, map_id)
            save_disabled(conn, map_id, body.disabled_wall_types)
            payload = map_payload(ctx, conn, map_id)
        ctx.fog.invalidate(map_id)
        await notify.map_changed(ctx, map_id, "walls")
        return payload
