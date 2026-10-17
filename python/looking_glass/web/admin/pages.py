"""Admin HTML pages (read-only views)."""

from fastapi import APIRouter, Request

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
