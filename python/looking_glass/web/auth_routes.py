"""Login / logout / account routes, mounted on both entry points."""

from typing import Annotated

from fastapi import APIRouter, Form, Request
from fastapi.responses import RedirectResponse

from .. import rbac
from ..repositories import sessions as sessions_repo
from ..repositories import users as users_repo
from ..security import token_hash, verify_password
from .deps import CsrfUserDep, CtxDep, UserDep, cookie_name, optional_user
from .templating import render

router = APIRouter()


def _safe_next(target: str | None) -> str:
    if target and target.startswith("/") and not target.startswith("//") and not target.startswith("/login"):
        return target
    return "/"


@router.get("/login")
def login_page(request: Request, next: str = "/"):
    if optional_user(request):
        return RedirectResponse(_safe_next(next), status_code=303)
    return render(request, "login.html", next=_safe_next(next))


@router.post("/login")
def login_submit(request: Request, ctx: CtxDep,
                 username: Annotated[str, Form()], password: Annotated[str, Form()],
                 next: Annotated[str, Form()] = "/"):
    entry = request.app.state.entry
    ip = request.client.host if request.client else "?"
    username = username.strip()

    def fail(msg: str, code: int = 401):
        return render(request, "login.html", status_code=code, next=_safe_next(next), username=username, error=msg)

    if ctx.throttle.blocked(ip, username):
        return fail("Too many failed attempts. Try again in a few minutes.", 429)
    with ctx.db.connect() as conn:
        row = users_repo.get_with_hash(conn, username)
        if row is None or not row["active"] or not verify_password(password, row["password_hash"]):
            ctx.throttle.fail(ip, username)
            return fail("Invalid username or password.")
        user = dict(row)
        if entry == "admin" and not rbac.can_use_admin_portal(user):
            return fail("This account can only use the viewer screen.", 403)
        ttl = int(float(ctx.settings.section("security")["session_hours"]) * 3600)
        token, _ = sessions_repo.create(conn, user["id"], entry, ttl)
        sessions_repo.purge_expired(conn)
    ctx.throttle.reset(ip, username)
    dest = "/account" if user["must_change_password"] else _safe_next(next)
    resp = RedirectResponse(dest, status_code=303)
    resp.set_cookie(cookie_name(request), token, max_age=ttl, httponly=True, samesite="lax",
                    secure=bool(ctx.settings.section("security")["secure_cookies"]), path="/")
    return resp


@router.post("/logout")
async def logout(request: Request, ctx: CtxDep, user: CsrfUserDep):
    token = request.cookies.get(cookie_name(request))
    if token:
        with ctx.db.connect() as conn:
            sessions_repo.delete(conn, token)
        await ctx.hub.kick_session(token_hash(token))
    resp = RedirectResponse("/login", status_code=303)
    resp.delete_cookie(cookie_name(request), path="/")
    return resp


@router.get("/account")
def account_page(request: Request, user: UserDep):
    return render(request, "account.html")


@router.post("/account")
def account_submit(request: Request, ctx: CtxDep, user: CsrfUserDep,
                   display_name: Annotated[str, Form()] = "",
                   current_password: Annotated[str, Form()] = "",
                   new_password: Annotated[str, Form()] = "",
                   confirm_password: Annotated[str, Form()] = ""):
    min_len = int(ctx.settings.section("security")["min_password_length"])
    with ctx.db.connect() as conn:
        if new_password or user["must_change_password"]:
            row = users_repo.get_with_hash(conn, user["username"])
            if not verify_password(current_password, row["password_hash"]):
                return render(request, "account.html", status_code=400, error="Current password is incorrect.")
            if len(new_password) < min_len:
                return render(request, "account.html", status_code=400,
                              error=f"New password must be at least {min_len} characters.")
            if new_password != confirm_password:
                return render(request, "account.html", status_code=400, error="Passwords do not match.")
            if new_password == current_password:
                return render(request, "account.html", status_code=400, error="Choose a different password.")
            users_repo.set_password(conn, user["id"], new_password, must_change=False)
            sessions_repo.delete_for_user(conn, user["id"], keep_token=request.cookies.get(cookie_name(request)))
        users_repo.update(conn, user["id"], display_name=display_name)
    return RedirectResponse("/account?ok=Account+updated", status_code=303)
