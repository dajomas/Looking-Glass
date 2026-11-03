"""Management/CSRF protected live door actions; no viewer mutation endpoint."""
from typing import Literal
from pydantic import BaseModel, Field
from ...services.door_actions import perform
from ..access import map_for_manage, fog_inputs
from ..deps import CtxDep, CsrfUserDep, BadRequest
from . import notify


class DoorActionIn(BaseModel):
    x: float = Field(ge=-1e7,le=1e7,allow_inf_nan=False)
    y: float = Field(ge=-1e7,le=1e7,allow_inf_nan=False)
    wall_id: int = Field(gt=0)
    side: int = Field(default=-1,ge=-1,le=1)
    gesture: Literal["single","double"]
    hit: Literal["arrow","wall"]
    mode: Literal["reveal","hide"] = "reveal"
    tolerance: float = Field(default=10,gt=0,le=500)
    cache_token: str = Field(min_length=1,max_length=128)
    walls_version: int = Field(ge=0)
    fog_version: int = Field(ge=0)


def register_door_states(router,map_payload):
    @router.post("/maps/{map_id}/door-action")
    async def door_action(ctx: CtxDep,user: CsrfUserDep,map_id: int,body: DoorActionIn):
        with ctx.db.connect() as conn:
            conn.execute("BEGIN IMMEDIATE")
            map_for_manage(conn,user,map_id)
            spec,segs,ops=fog_inputs(ctx,conn,map_id)
            try:
                info,changed=perform(conn,ctx.fog,spec,segs,ops,body,user["id"])
            except ValueError as exc:
                raise BadRequest(str(exc)) from exc
            payload={**map_payload(ctx,conn,map_id),**info}
        if changed:
            await notify.map_changed(ctx,map_id,"door")
        return payload
