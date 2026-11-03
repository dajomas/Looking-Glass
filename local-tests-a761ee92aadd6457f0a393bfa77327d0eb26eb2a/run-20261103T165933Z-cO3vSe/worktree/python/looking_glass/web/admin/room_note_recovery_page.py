"""Management-only recovery workspace; GET renders without changing play state."""
from fastapi import APIRouter, Request

from ..access import map_for_manage
from ..deps import CtxDep, UserDep
from ..templating import render

router = APIRouter()


@router.get("/maps/{map_id}/room-note-recovery")
def recovery_page(request: Request, ctx: CtxDep, user: UserDep, map_id: int):
    with ctx.db.connect() as conn:
        m, campaign = map_for_manage(conn, user, map_id)
        context = {"map": dict(m), "campaign": dict(campaign)}
    response = render(request, "admin/room_note_recovery.html", **context)
    response.headers["Cache-Control"] = "no-store"
    return response
