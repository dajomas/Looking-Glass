"""Admin HTML pages (read-only views)."""

from fastapi import APIRouter, Request, Query
from typing import Annotated, Literal
from fastapi.responses import JSONResponse

from ... import rbac
from ...repositories import campaigns as campaigns_repo
from ...repositories import fog_ops as fog_repo
from ...repositories import maps as maps_repo
from ...repositories import users as users_repo
from ...rbac import Role
from ..access import campaign_for_manage, map_for_manage
from ..deps import CtxDep, UserDep
from ..templating import render

router = APIRouter()


@router.get("/")
def dashboard(request: Request, ctx: CtxDep, user: UserDep):
    with ctx.db.connect() as conn:
        campaigns = campaigns_repo.list_manageable(conn, user)
    return render(request, "admin/dashboard.html", campaigns=campaigns,
                  viewer_port=ctx.settings.viewer_port)


@router.get("/campaigns/{campaign_id}")
def campaign_page(request: Request, ctx: CtxDep, user: UserDep, campaign_id: int):
    with ctx.db.connect() as conn:
        campaign = campaign_for_manage(conn, user, campaign_id)
        maps = maps_repo.list_for_campaign(conn, campaign_id)
        viewers = campaigns_repo.list_viewers(conn, campaign_id)
        assignable = campaigns_repo.list_assignable_users(conn, campaign_id, campaign["owner_id"])
        admins = [u for u in users_repo.list_all(conn) if u["role"] != Role.VIEWER] \
            if rbac.can_manage_users(user) else []
    return render(request, "admin/campaign.html", campaign=campaign, maps=maps, viewers=viewers,
                  recovery_files=sorted(p.name for p in (ctx.settings.data_dir / "recovery").glob(f"campaign-{campaign_id}-*.zip")),
                  assignable=assignable, admins=admins,
                  can_create_viewers=rbac.can_create_viewers(
                      user, bool(ctx.settings.section("security")["admins_can_create_viewers"])),
                  live_viewers=ctx.hub.viewer_count(campaign_id),
                  viewer_port=ctx.settings.viewer_port)


@router.get("/maps/{map_id}")
def map_editor(request: Request, ctx: CtxDep, user: UserDep, map_id: int):
    with ctx.db.connect() as conn:
        m, campaign = map_for_manage(conn, user, map_id)
        siblings = maps_repo.list_for_campaign(conn, campaign["id"])
        ops = fog_repo.count(conn, map_id)
    return render(request, "admin/map_editor.html", map=m, campaign=campaign, siblings=siblings, op_count=ops,
                  fog_opacity=ctx.settings.section("fog")["admin_fog_opacity"])


@router.get("/campaigns/{campaign_id}/readiness")
def campaign_readiness(request: Request, ctx: CtxDep, user: UserDep, campaign_id: int):
    from ...services.campaign_readiness import check_campaign
    with ctx.db.connect() as conn:
        conn.execute("PRAGMA query_only=ON")
        conn.execute("BEGIN")
        campaign = campaign_for_manage(conn, user, campaign_id)
        report = check_campaign(conn, campaign, ctx.settings.maps_dir, ctx.fog,
                                int(ctx.settings.section("storage")["max_upload_mb"]) * 1024 * 1024)
    response = render(request, "admin/campaign_readiness.html", campaign=campaign, report=report)
    response.headers["Cache-Control"] = "no-store"
    return response


@router.get("/campaigns/{campaign_id}/inspect/maps/{map_id}")
@router.get("/campaigns/{campaign_id}/readiness/maps/{map_id}")
def readiness_inspect(request: Request, ctx: CtxDep, user: UserDep, campaign_id: int, map_id: int,
                       x: float | None = None, y: float | None = None,
                       kind: Literal["map", "room", "passage", "library"] = "map",
                       key: Annotated[str, Query(max_length=200)] = ""):
    import math
    from ..deps import NotFound
    with ctx.db.connect() as conn:
        conn.execute("PRAGMA query_only=ON")
        conn.execute("BEGIN")
        campaign = campaign_for_manage(conn, user, campaign_id)
        m, _ = map_for_manage(conn, user, map_id)
        if m["campaign_id"] != campaign_id:
            raise NotFound("Map not found in this campaign.")
        from ...services.campaign_search import inspect_target
        try:
            selected = inspect_target(conn,map_id,kind,key)
        except (LookupError,ValueError) as exc:
            raise NotFound(str(exc)) from exc
        if selected and "x" in selected:
            x,y=selected["x"],selected["y"]
        endpoints = conn.execute("SELECT name,x,y FROM map_transitions WHERE map_id=? ORDER BY name,id", (map_id,)).fetchall()
        notes = conn.execute("SELECT name,x,y FROM room_notes WHERE map_id=? ORDER BY name,area_key", (map_id,)).fetchall()
    from ...services.campaign_readiness import image_path
    image_safe = True
    try:
        image_path(ctx.settings.maps_dir, m["image_file"])
    except (ValueError, OSError):
        image_safe = False
    marker = None
    if x is not None and y is not None and math.isfinite(x) and math.isfinite(y):
        marker = {"x": min(max(x,0),max(0,m["width"]-1)), "y": min(max(y,0),max(0,m["height"]-1)),
                  "original_x":x,"original_y":y}
    response = render(request,"admin/readiness_inspect.html", campaign=campaign, map=m,
                      marker=marker, endpoints=endpoints, notes=notes, image_safe=image_safe, selected=selected)
    response.headers["Cache-Control"] = "no-store"
    return response


def _campaign_search_response(request,ctx,user,campaign_id,q,kind,as_json):
    from ...services.campaign_search import search_campaign
    with ctx.db.connect() as conn:
        conn.execute("PRAGMA query_only=ON")
        conn.execute("BEGIN")
        campaign=campaign_for_manage(conn,user,campaign_id)
        result=search_campaign(conn,campaign_id,q,kind)
    response=JSONResponse(result) if as_json else render(request,"admin/campaign_search.html",campaign=campaign,search=result)
    response.headers["Cache-Control"]="no-store"
    return response


@router.get("/campaigns/{campaign_id}/search")
def campaign_search(request: Request,ctx: CtxDep,user: UserDep,campaign_id: int,
                    q: Annotated[str,Query(max_length=200)] = "",
                    kind: Literal["all","map","room","passage","library"] = "all"):
    return _campaign_search_response(request,ctx,user,campaign_id,q,kind,False)


@router.get("/api/campaigns/{campaign_id}/search")
def campaign_search_json(request: Request,ctx: CtxDep,user: UserDep,campaign_id: int,
                         q: Annotated[str,Query(max_length=200)] = "",
                         kind: Literal["all","map","room","passage","library"] = "all"):
    return _campaign_search_response(request,ctx,user,campaign_id,q,kind,True)
