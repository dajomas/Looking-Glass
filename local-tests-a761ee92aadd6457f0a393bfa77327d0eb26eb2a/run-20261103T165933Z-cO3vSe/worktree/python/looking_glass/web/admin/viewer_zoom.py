"""Authorized, ephemeral camera commands for viewers; no fog/door writes."""
import asyncio
from uuid import uuid4
from fastapi import APIRouter
from pydantic import BaseModel, Field
from ...services.viewer_area import revealed_area_bounds
from ..access import map_for_manage, fog_inputs
from ..deps import CtxDep, CsrfUserDep, BadRequest

router = APIRouter(prefix="/api")


class ViewerZoomIn(BaseModel):
    x: float = Field(ge=0,le=1e7,allow_inf_nan=False)
    y: float = Field(ge=0,le=1e7,allow_inf_nan=False)
    cache_token: str = Field(min_length=1,max_length=128)
    walls_version: int = Field(ge=0)
    fog_version: int = Field(ge=0)


def check_target(row,campaign,body):
    if campaign["active_map_id"] != row["id"]:
        raise BadRequest("This map is not shown to players. Show it first to control viewer zoom.")
    if (row["cache_token"],row["walls_version"],row["fog_version"]) != (body.cache_token,body.walls_version,body.fog_version):
        raise BadRequest("The map changed; refresh and double-click again.")


@router.post("/maps/{map_id}/viewer-zoom")
async def viewer_zoom(ctx: CtxDep,user: CsrfUserDep,map_id: int,body: ViewerZoomIn):
    with ctx.db.connect() as conn:
        conn.execute("BEGIN")
        row,campaign = map_for_manage(conn,user,map_id)
        check_target(row,campaign,body)
        spec,segs,ops = fog_inputs(ctx,conn,map_id)
        campaign_id = row["campaign_id"]
        version = f"{row['id']}:{row['cache_token']}-{row['walls_version']}-{row['fog_version']}"
    bounds = await asyncio.to_thread(revealed_area_bounds,ctx.fog,spec,segs,ops,body.x,body.y)
    with ctx.db.connect() as conn:
        row,campaign = map_for_manage(conn,user,map_id)
        check_target(row,campaign,body)
    if bounds is None:
        return {"ok":True,"sent":False,"reason":"not-revealed","viewers":0}
    viewers = ctx.hub.viewer_count(campaign_id)
    if viewers:
        await ctx.hub.publish(campaign_id,{"type":"viewer-zoom","command_id":uuid4().hex,
            "version":version,"point":{"x":body.x,"y":body.y}})
    return {"ok":True,"sent":bool(viewers),"viewers":viewers}
