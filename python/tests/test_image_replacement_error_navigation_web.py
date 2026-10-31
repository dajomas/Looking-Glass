"""Bug 13 acceptance follow-up: return from replacement errors to the fog editor."""
from contextlib import contextmanager
from html.parser import HTMLParser
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest

from conftest import png_bytes
from test_web import env, login, csrf_of
from test_image_database_failures import image_case
from test_original_image_compatibility_web import alternate, configure, replace, snapshot
from looking_glass.web import errors
from looking_glass.web.deps import Forbidden, NotFound


class Links(HTMLParser):
    def __init__(self, html):
        super().__init__()
        self.links = []
        self.current = None
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            self.current = [dict(attrs).get("href"), ""]

    def handle_data(self, data):
        if self.current is not None:
            self.current[1] += data

    def handle_endtag(self, tag):
        if tag == "a" and self.current is not None:
            self.links.append(tuple(self.current))
            self.current = None


@pytest.mark.parametrize("configured", [False, True])
def test_rejected_replacement_links_to_same_editor_without_state_changes(image_case, monkeypatch, configured):
    case = image_case
    base = alternate(case)
    if configured:
        configure(case, base)
    before = snapshot(case)
    publish = AsyncMock(wraps=case.ctx.hub.publish)
    monkeypatch.setattr(case.ctx.hub, "publish", publish)
    response = case.dm.post(
        f"/maps/{case.mid}/image?next=https://untrusted.invalid/elsewhere",
        data={"csrf_token": case.csrf},
        headers={"Referer": "https://untrusted.invalid/elsewhere"},
        files={"image": ("smaller.png", png_bytes(360, 180), "image/png")},
        follow_redirects=False)
    assert response.status_code == 400, response.text
    assert "Original image must remain" in response.text
    links = Links(response.text).links
    assert (f"/maps/{case.mid}", "Back to map") in links
    assert not any(label == "Back to start" for _, label in links)
    assert snapshot(case) == before
    editor = case.dm.get(f"/maps/{case.mid}", follow_redirects=False)
    assert editor.status_code == 200, editor.text
    assert 'id="replace-map-panel"' in editor.text
    assert snapshot(case) == before
    publish.assert_not_awaited()
    retry = replace(case)
    assert retry.status_code == 303 and "ok=" in retry.headers["location"], retry.text


def test_json_rejection_keeps_existing_error_envelope(image_case):
    case = image_case
    alternate(case)
    before = snapshot(case)
    response = case.dm.post(f"/maps/{case.mid}/image",
        headers={"Accept": "application/json"}, data={"csrf_token": case.csrf},
        files={"image": ("smaller.png", png_bytes(360, 180), "image/png")})
    assert response.status_code == 400, response.text
    body = response.json()
    assert set(body) == {"ok", "error"} and body["ok"] is False
    assert "Original image must remain" in body["error"]
    assert snapshot(case) == before


@pytest.mark.parametrize("actor", ["missing-csrf", "wrong-owner"])
def test_forbidden_replacement_keeps_generic_navigation(image_case, actor):
    case = image_case
    alternate(case)
    stranger = login(case.dm.app, "dm2", "dmpass123") if actor == "wrong-owner" else None
    try:
        before = snapshot(case)
        response = replace(case, 360, 180, client=stranger,
                           csrf=csrf_of(stranger) if stranger else "")
        assert response.status_code == 403, response.text
        links = Links(response.text).links
        assert ("/", "Back to start") in links
        assert not any(label == "Back to map" for _, label in links)
        assert snapshot(case) == before
    finally:
        if stranger:
            stranger.close()


def test_unrelated_error_keeps_generic_navigation(image_case):
    response = image_case.dm.get("/maps/999999999", follow_redirects=False)
    assert response.status_code == 404, response.text
    links = Links(response.text).links
    assert ("/", "Back to start") in links
    assert not any(label == "Back to map" for _, label in links)


@pytest.mark.parametrize("denied", [Forbidden, NotFound])
def test_return_link_rechecks_map_access(monkeypatch, denied):
    @contextmanager
    def connection():
        yield object()

    access = Mock(side_effect=denied())
    monkeypatch.setattr(errors, "map_for_manage", access)
    request = SimpleNamespace(method="POST", url=SimpleNamespace(path="/maps/7/image"),
        path_params={"map_id": 7}, state=SimpleNamespace(user={"must_change_password": False}),
        app=SimpleNamespace(state=SimpleNamespace(entry="admin",
            ctx=SimpleNamespace(db=SimpleNamespace(connect=connection)))))
    assert errors._replacement_return_map(request) is None
    access.assert_called_once()
