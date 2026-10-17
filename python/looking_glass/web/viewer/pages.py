"""Viewer pages: campaign picker and the fullscreen display."""

from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse

from ...repositories import campaigns as campaigns_repo
from ..access import campaign_for_view
from ..deps import CtxDep, UserDep, optional_user
from ..templating import render

router = APIRouter()


@router.get("/")
def index(request: Request, ctx: CtxDep):
    user = optional_user(request)
    if user is None:
        return RedirectResponse("/login", status_code=303)
    if user["must_change_password"]:
        return RedirectResponse("/account", status_code=303)
    with ctx.db.connect() as conn:
        campaigns = campaigns_repo.list_viewable(conn, user)
    if len(campaigns) == 1 and request.query_params.get("pick") is None:
        return RedirectResponse(f"/c/{campaigns[0]['id']}", status_code=303)
    return render(request, "viewer/index.html", campaigns=campaigns)


@router.get("/c/{campaign_id}")
def display(request: Request, ctx: CtxDep, user: UserDep, campaign_id: int):
    with ctx.db.connect() as conn:
        campaign = campaign_for_view(conn, user, campaign_id)
    return render(request, "viewer/display.html", campaign=campaign)
