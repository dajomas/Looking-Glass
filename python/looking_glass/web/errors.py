"""Exception handlers shared by both apps (HTML pages vs JSON for /api)."""

from urllib.parse import quote

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, RedirectResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from .access import map_for_manage
from .deps import BadRequest, Forbidden, LoginRequired, MustChangePassword, NotFound
from .templating import render


def _wants_json(request: Request) -> bool:
    return request.url.path.startswith("/api/") or "application/json" in request.headers.get("accept", "")


def _replacement_return_map(request: Request) -> str | None:
    """Offer a fixed local editor link only for an authorized replacement POST."""
    map_id = request.path_params.get("map_id")
    if (request.app.state.entry != "admin" or request.method != "POST"
            or type(map_id) is not int or map_id <= 0
            or request.url.path != f"/maps/{map_id}/image"):
        return None
    user = getattr(request.state, "user", None)
    if user is None or user["must_change_password"]:
        return None
    ctx = request.app.state.ctx
    try:
        with ctx.db.connect() as conn:
            map_for_manage(conn, user, map_id)
    except (Forbidden, NotFound):
        return None
    return f"/maps/{map_id}"


def _error(request: Request, status: int, message: str):
    if _wants_json(request):
        return JSONResponse({"ok": False, "error": message}, status_code=status)
    return_map_url = _replacement_return_map(request) if status == 400 else None
    return render(request, "error.html", status_code=status, status=status, message=message,
                  return_map_url=return_map_url)


def install(app: FastAPI) -> None:
    @app.exception_handler(LoginRequired)
    async def _login(request: Request, exc: LoginRequired):
        if _wants_json(request):
            return JSONResponse({"ok": False, "error": "Login required"}, status_code=401)
        target = request.url.path + (f"?{request.url.query}" if request.url.query else "")
        return RedirectResponse(f"/login?next={quote(target)}", status_code=303)

    @app.exception_handler(MustChangePassword)
    async def _mcp(request: Request, exc: MustChangePassword):
        if _wants_json(request):
            return JSONResponse({"ok": False, "error": "Password change required"}, status_code=403)
        return RedirectResponse("/account", status_code=303)

    @app.exception_handler(Forbidden)
    async def _forbidden(request: Request, exc: Forbidden):
        return _error(request, 403, exc.message)

    @app.exception_handler(NotFound)
    async def _nf(request: Request, exc: NotFound):
        return _error(request, 404, exc.message)

    @app.exception_handler(BadRequest)
    async def _bad(request: Request, exc: BadRequest):
        return _error(request, 400, exc.message)

    @app.exception_handler(RequestValidationError)
    async def _validation(request: Request, exc: RequestValidationError):
        msg = "; ".join(f"{'.'.join(str(p) for p in e['loc'][1:])}: {e['msg']}" for e in exc.errors())
        return _error(request, 422, msg or "Invalid input")

    @app.exception_handler(StarletteHTTPException)
    async def _http(request: Request, exc: StarletteHTTPException):
        return _error(request, exc.status_code, str(exc.detail))
