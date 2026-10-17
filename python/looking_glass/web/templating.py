"""Jinja2 setup.

Lookup order: web_html/ (page templates per entry point) then templates/
(shared layouts, partials, login/account/error pages).
"""

from typing import Any

from fastapi import Request
from fastapi.templating import Jinja2Templates
from jinja2 import ChoiceLoader, Environment, FileSystemLoader, select_autoescape

from ..config import Settings
from ..rbac import Role


def build_templates(settings: Settings) -> Jinja2Templates:
    env = Environment(
        loader=ChoiceLoader([FileSystemLoader(settings.web_html_dir), FileSystemLoader(settings.templates_dir)]),
        autoescape=select_autoescape(["html", "xml"]),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    env.globals.update(app_title=settings.section("viewer")["title"], Role=Role)
    return Jinja2Templates(env=env)


def render(request: Request, name: str, status_code: int = 200, **context: Any):
    templates: Jinja2Templates = request.app.state.templates
    user = getattr(request.state, "user", None)
    base = {
        "user": user,
        "csrf_token": user["csrf_token"] if user else "",
        "entry": request.app.state.entry,
        "ok_msg": request.query_params.get("ok"),
        "err_msg": request.query_params.get("err"),
    }
    base.update(context)
    return templates.TemplateResponse(request, name, base, status_code=status_code)
