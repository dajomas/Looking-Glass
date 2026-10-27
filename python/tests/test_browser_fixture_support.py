"""Template and route-helper checks without launching a browser."""
import importlib.util
from pathlib import Path
from types import SimpleNamespace

SPEC = importlib.util.spec_from_file_location("browser_support_checks", Path(__file__).with_name("browser") / "browser_support.py")
support = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(support)


def test_real_partials_resolve_and_overrides_win():
    env = support.template_environment({"base.html": "override base"})
    assert env.get_template("base.html").render() == "override base"
    source, _, _ = env.loader.get_source(env, "partials/_admin_sidebar_help.html")
    assert "editor-help" in source
    env.get_template("admin/map_editor.html")


def test_auxiliary_unknown_routes_remain_unhandled():
    route = SimpleNamespace(request=SimpleNamespace(url="http://test/unknown", method="GET"))
    assert support.fulfill_auxiliary(route, {}) is False


def test_auxiliary_writes_are_not_swallowed():
    route = SimpleNamespace(request=SimpleNamespace(url="http://test/api/maps/1/room-notes", method="POST"))
    assert support.fulfill_auxiliary(route, {}) is False


def test_auxiliary_empty_library_payload():
    calls = []
    route = SimpleNamespace(request=SimpleNamespace(url="http://test/api/maps/1/room-note-library", method="GET"),
                            fulfill=lambda **kwargs: calls.append(kwargs))
    assert support.fulfill_auxiliary(route, {}) is True
    assert calls == [{"json": {"ok": True, "entries": []}}]
