"""Real template/dependency boundaries for mocked browser integration pages."""
from pathlib import Path
import re
from jinja2 import ChoiceLoader, DictLoader, Environment, FileSystemLoader

ROOT = Path(__file__).resolve().parents[3]

def template_environment(overrides):
    overrides = dict(overrides)
    base = overrides.get("base.html")
    if base and "<" in base and "charset=" not in base.lower():
        if re.search(r"<!doctype html>", base, flags=re.I):
            base = re.sub(r"(<!doctype html>)", r'\1<meta charset="utf-8">', base, count=1, flags=re.I)
        else:
            base = '<meta charset="utf-8">' + base
        overrides["base.html"] = base
    return Environment(loader=ChoiceLoader([
        DictLoader(overrides), FileSystemLoader([str(ROOT / "web_html"), str(ROOT / "templates")])
    ]))

def fulfill_auxiliary(route, data):
    from urllib.parse import urlparse
    path = urlparse(route.request.url).path
    if route.request.method != "GET":
        return False
    if re.fullmatch(r"/api/campaigns/\d+/viewer-status", path):
        payload = {"ok": True, "viewers": [], "blank": not bool(data.get("is_active"))}
    elif path.endswith("/room-note-library"):
        payload = {"ok": True, "entries": []}
    elif path.endswith("/room-notes"):
        payload = {"ok": True, "rooms": []}
    elif path.endswith("/double-reveal"):
        payload = dict(ok=True, cache_token=data["cache_token"], walls_version=data["walls_version"],
                       fog_version=data["fog_version"], image_revision=0, active_map_id=None,
                       rooms=[], maps=[], can_undo=False)
    elif path.endswith("/transitions"):
        payload = dict(ok=True, active_map_id=None, endpoints=[], maps=[dict(id=1,name="M",
                       viewer_transition_markers=1,viewer_transition_labels=1)])
    else:
        return False
    route.fulfill(json=payload)
    return True
