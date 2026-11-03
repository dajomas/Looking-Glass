"""Authentication / authorisation dependencies shared by both apps."""

from typing import Annotated, Any

from fastapi import Depends, Request

from .. import rbac
from ..repositories import sessions as sessions_repo
from ..security import constant_eq
from .context import AppContext

COOKIE_NAMES = {"admin": "lg_admin_session", "viewer": "lg_viewer_session"}

type User = dict[str, Any]


class LoginRequired(Exception):
    pass


class MustChangePassword(Exception):
    pass


class Forbidden(Exception):
    def __init__(self, message: str = "You do not have access to this resource."):
        super().__init__(message)
        self.message = message


class NotFound(Exception):
    def __init__(self, message: str = "Not found."):
        super().__init__(message)
        self.message = message


class BadRequest(Exception):
    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


def get_ctx(request: Request) -> AppContext:
    return request.app.state.ctx


def cookie_name(request: Request) -> str:
    return COOKIE_NAMES[request.app.state.entry]


def _portal_allows(entry: str, user: User) -> bool:
    return rbac.can_use_admin_portal(user) if entry == "admin" else rbac.can_use_viewer_portal(user)


def resolve_user(ctx: AppContext, entry: str, token: str | None) -> User | None:
    if not token:
        return None
    with ctx.db.connect() as conn:
        row = sessions_repo.lookup(conn, token, entry)
    if row is None:
        return None
    user = dict(row)
    if not _portal_allows(entry, user):
        return None
    return user


def optional_user(request: Request) -> User | None:
    user = resolve_user(get_ctx(request), request.app.state.entry, request.cookies.get(cookie_name(request)))
    request.state.user = user
    return user


def require_user(request: Request) -> User:
    user = optional_user(request)
    if user is None:
        raise LoginRequired()
    if user["must_change_password"] and request.url.path not in ("/account", "/logout"):
        raise MustChangePassword()
    return user


def require_superadmin(user: Annotated[User, Depends(require_user)]) -> User:
    if not rbac.can_manage_users(user):
        raise Forbidden("Only a superadmin can manage users.")
    return user


async def verify_csrf(request: Request, user: Annotated[User, Depends(require_user)]) -> User:
    """Double-check state-changing requests: header (JS) or hidden form field."""
    if request.method in ("GET", "HEAD", "OPTIONS"):
        return user
    supplied = request.headers.get("x-csrf-token")
    if not supplied:
        ctype = request.headers.get("content-type", "")
        if "form" in ctype:
            form = await request.form()
            supplied = form.get("csrf_token")  # type: ignore[assignment]
    if not constant_eq(supplied, user["csrf_token"]):
        raise Forbidden("Invalid or missing CSRF token. Reload the page and try again.")
    return user


CtxDep = Annotated[AppContext, Depends(get_ctx)]
UserDep = Annotated[User, Depends(require_user)]
CsrfUserDep = Annotated[User, Depends(verify_csrf)]
SuperadminDep = Annotated[User, Depends(require_superadmin)]
