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


def test_viewer_status_has_actual_readonly_schema():
    calls = []
    route = SimpleNamespace(request=SimpleNamespace(url="http://test/api/campaigns/4/viewer-status", method="GET"),
                            fulfill=lambda **kwargs: calls.append(kwargs))
    assert support.fulfill_auxiliary(route, {"is_active": True}) is True
    assert calls == [{"json": {"ok": True, "viewers": [], "blank": False}}]


def test_viewer_status_does_not_match_unknown_route_or_write():
    for path, method in [("/unrelated/viewer-status", "GET"), ("/api/campaigns/4/viewer-status", "POST")]:
        route = SimpleNamespace(request=SimpleNamespace(url="http://test" + path, method=method))
        assert support.fulfill_auxiliary(route, {}) is False


def test_mock_base_has_utf8_without_mutating_override():
    original = {"base.html": "<!doctype html><title>é</title>"}
    rendered = support.template_environment(original).get_template("base.html").render()
    assert rendered.startswith('<!doctype html><meta charset="utf-8">')
    assert original["base.html"] == "<!doctype html><title>é</title>"
