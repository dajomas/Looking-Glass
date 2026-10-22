"""DM-only endpoint configuration and atomic cross-map travel."""
from typing import Literal
from fastapi import APIRouter
from pydantic import BaseModel,Field,ConfigDict
from ..access import campaign_for_manage,map_for_manage
from ..deps import CtxDep,UserDep,CsrfUserDep,BadRequest
from ...services import map_transitions as service
from . import notify
router=APIRouter()

class StrictInput(BaseModel):
    model_config=ConfigDict(extra="forbid")

class EndpointIn(StrictInput):
    map_id:int=Field(gt=0)
    name:str=Field(min_length=1,max_length=120)
    player_label:str=Field(default="",max_length=120)
    kind:Literal["stairs","ladder","hole","portal","climb","custom"]="stairs"
    x:float=Field(ge=0,allow_inf_nan=False)
    y:float=Field(ge=0,allow_inf_nan=False)
    visibility:Literal["secret","discovered","admin"]="discovered"
    availability:Literal["usable","blocked","approval"]="usable"
    destination_id:str|None=Field(default=None,max_length=64)
    arrival:Literal["area","preserve"]="area"
    notes:str=Field(default="",max_length=2000)
    revision:int|None=Field(default=None,ge=1)
    return_link:bool=Field(default=False,strict=True)

class RuntimeIn(StrictInput):
    revision:int=Field(ge=1)
    visibility:Literal["secret","discovered","admin"]|None=None
    availability:Literal["usable","blocked","approval"]|None=None

class MarkerIn(StrictInput):
    enabled:bool=Field(strict=True)
    labels:bool=Field(strict=True)

class TravelIn(StrictInput):
    source_endpoint_id:str=Field(min_length=1,max_length=64)
    expected_active_map_id:int=Field(gt=0)
    source_revision:int=Field(ge=1)
    destination_revision:int=Field(ge=1)
    destination_version:list[str|int]=Field(min_length=3,max_length=3)
    request_id:str=Field(min_length=8,max_length=128)
    override:bool=Field(default=False,strict=True)
    allow_large_reveal:bool=Field(default=False,strict=True)


def listing(conn,campaign_id):
    c=conn.execute("SELECT active_map_id FROM campaigns WHERE id=?",(campaign_id,)).fetchone()
    return dict(ok=True,active_map_id=c["active_map_id"],endpoints=service.overview(conn,campaign_id),
        maps=[dict(r) for r in conn.execute("SELECT id,name,width,height,viewer_transition_markers,viewer_transition_labels FROM maps WHERE campaign_id=? ORDER BY id",(campaign_id,))])

@router.get("/campaigns/{campaign_id}/transitions")
def get_transitions(ctx:CtxDep,user:UserDep,campaign_id:int):
    with ctx.db.connect() as conn:
        conn.execute("BEGIN")
        campaign_for_manage(conn,user,campaign_id)
        return listing(conn,campaign_id)

async def save_endpoint(ctx,user,campaign_id,body,endpoint_id=None):
    with ctx.db.connect() as conn:
        conn.execute("BEGIN IMMEDIATE")
        campaign_for_manage(conn,user,campaign_id)
        try: service.save(conn,campaign_id,body.map_id,body.model_dump(),endpoint_id,body.revision,body.return_link)
        except ValueError as exc: raise BadRequest(str(exc))
        result=listing(conn,campaign_id)
    await notify.campaign_changed(ctx,campaign_id,"transitions")
    return result

@router.post("/campaigns/{campaign_id}/transitions")
async def create_endpoint(ctx:CtxDep,user:CsrfUserDep,campaign_id:int,body:EndpointIn):
    return await save_endpoint(ctx,user,campaign_id,body)

@router.post("/campaigns/{campaign_id}/transitions/{endpoint_id}")
async def update_endpoint(ctx:CtxDep,user:CsrfUserDep,campaign_id:int,endpoint_id:str,body:EndpointIn):
    return await save_endpoint(ctx,user,campaign_id,body,endpoint_id)

@router.delete("/campaigns/{campaign_id}/transitions/{endpoint_id}")
async def delete_endpoint(ctx:CtxDep,user:CsrfUserDep,campaign_id:int,endpoint_id:str,revision:int):
    with ctx.db.connect() as conn:
        conn.execute("BEGIN IMMEDIATE")
        campaign_for_manage(conn,user,campaign_id)
        try:
            row=service.endpoint(conn,endpoint_id,campaign_id)
            if row["revision"]!=revision: raise ValueError("Endpoint changed. Reload first.")
            conn.execute("DELETE FROM map_transitions WHERE id=?",(endpoint_id,))
        except ValueError as exc: raise BadRequest(str(exc))
        result=listing(conn,campaign_id)
    await notify.campaign_changed(ctx,campaign_id,"transitions")
    return result

@router.post("/campaigns/{campaign_id}/transitions/{endpoint_id}/runtime")
async def runtime_endpoint(ctx:CtxDep,user:CsrfUserDep,campaign_id:int,endpoint_id:str,body:RuntimeIn):
    with ctx.db.connect() as conn:
        conn.execute("BEGIN IMMEDIATE")
        campaign_for_manage(conn,user,campaign_id)
        try: service.runtime(conn,campaign_id,endpoint_id,body.revision,body.visibility,body.availability)
        except ValueError as exc: raise BadRequest(str(exc))
        result=listing(conn,campaign_id)
    await notify.campaign_changed(ctx,campaign_id,"transitions")
    return result

@router.post("/maps/{map_id}/transitions/reset")
async def reset_endpoints(ctx:CtxDep,user:CsrfUserDep,map_id:int):
    with ctx.db.connect() as conn:
        conn.execute("BEGIN IMMEDIATE")
        m,_=map_for_manage(conn,user,map_id)
        service.reset_runtime(conn,map_id)
        result=listing(conn,m["campaign_id"])
    await notify.map_changed(ctx,map_id,"transitions")
    return result

@router.post("/maps/{map_id}/transition-markers")
async def set_markers(ctx:CtxDep,user:CsrfUserDep,map_id:int,body:MarkerIn):
    with ctx.db.connect() as conn:
        conn.execute("BEGIN IMMEDIATE")
        m,_=map_for_manage(conn,user,map_id)
        conn.execute("UPDATE maps SET viewer_transition_markers=?,viewer_transition_labels=?,fog_version=fog_version+1 WHERE id=?",(int(body.enabled),int(body.labels),map_id))
        result=listing(conn,m["campaign_id"])
    await notify.map_changed(ctx,map_id,"transitions")
    return result

@router.get("/campaigns/{campaign_id}/transitions/{endpoint_id}/preview")
def preview(ctx:CtxDep,user:UserDep,campaign_id:int,endpoint_id:str):
    with ctx.db.connect() as conn:
        conn.execute("BEGIN")
        campaign_for_manage(conn,user,campaign_id)
        try: _,_,info=service.arrival_info(conn,ctx,campaign_id,endpoint_id)
        except ValueError as exc: raise BadRequest(str(exc))
        return dict(ok=True,**info)

@router.post("/campaigns/{campaign_id}/travel")
async def travel(ctx:CtxDep,user:CsrfUserDep,campaign_id:int,body:TravelIn):
    with ctx.db.connect() as conn:
        conn.execute("BEGIN IMMEDIATE")
        campaign_for_manage(conn,user,campaign_id)
        try: result=service.travel(conn,ctx,campaign_id,user["id"],body.model_dump())
        except ValueError as exc: raise BadRequest(str(exc))
    await notify.campaign_changed(ctx,campaign_id,"active-map")
    return result
