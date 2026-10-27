"""Builds the two FastAPI applications (one per entry point)."""

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware

from .. import __version__
from . import auth_routes, errors
from .admin import scrying_glass as admin_scrying_glass
from .admin import double_reveal as admin_double_reveal
from .admin import api as admin_api
from .admin import campaigns as admin_campaigns
from .admin import pages as admin_pages
from .admin import session_checkpoints as admin_checkpoints
from .admin import users as admin_users
from .admin import wall_editor as admin_wall_editor
from .admin import viewer_zoom as admin_viewer_zoom
from .context import AppContext
from .templating import build_templates
from .viewer import api as viewer_api
from .viewer import pages as viewer_pages


class SecurityHeaders(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        resp = await call_next(request)
        resp.headers.setdefault("X-Content-Type-Options", "nosniff")
        resp.headers.setdefault("X-Frame-Options", "SAMEORIGIN")
        resp.headers.setdefault("Referrer-Policy", "same-origin")
        return resp


def _base_app(ctx: AppContext, entry: str, title: str) -> FastAPI:
    app = FastAPI(title=title, version=__version__, docs_url=None, redoc_url=None, openapi_url=None)
    app.state.ctx = ctx
    app.state.entry = entry
    app.state.templates = build_templates(ctx.settings)
    app.add_middleware(SecurityHeaders)
    app.mount("/static", StaticFiles(directory=ctx.settings.static_dir), name="static")
    errors.install(app)
    app.include_router(auth_routes.router)

    @app.get("/healthz", include_in_schema=False)
    def healthz():
        return {"ok": True, "entry": entry, "version": __version__}

    return app


def create_admin_app(ctx: AppContext) -> FastAPI:
    app = _base_app(ctx, "admin", "Looking Glass - Admin")
    app.include_router(admin_pages.router)
    app.include_router(admin_checkpoints.router)
    app.include_router(admin_campaigns.router)
    app.include_router(admin_users.router)
    app.include_router(admin_api.router)
    app.include_router(admin_double_reveal.router)
    app.include_router(admin_scrying_glass.router)
    app.include_router(admin_wall_editor.router)
    app.include_router(admin_viewer_zoom.router)
    return app


def create_viewer_app(ctx: AppContext) -> FastAPI:
    app = _base_app(ctx, "viewer", "Looking Glass - Viewer")
    app.include_router(viewer_pages.router)
    app.include_router(viewer_api.router)
    return app
