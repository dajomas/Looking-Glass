"""Live campaign ZIP restore/recovery propagation and preview rejection.

Run: LG_RUN_LIVE_E2E=1 python -m pytest -q python/tests/live_e2e/test_live_zip_restore.py
Reuses native WebSocket observation/current-version checks from checkpoint tests.
All archives come from authenticated application endpoints; no HTTP/WS mocks.
"""
from html.parser import HTMLParser
import io
import json
import re
from urllib.parse import parse_qs, urlsplit
import zipfile

import pytest

from .test_live_checkpoints import Checkpoints, RED, GREEN, FOG


class RestoreHTML(HTMLParser):
    def __init__(self, action):
        super().__init__(convert_charrefs=True)
        self.expected_action = action
        self.action = None
        self.previews = []
        self.links = []
        self.headings = []
        self.heading = None

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "form":
            self.action = attrs.get("action")
        elif tag == "input" and self.action == self.expected_action and attrs.get("name") == "preview":
            self.previews.append(attrs.get("value", ""))
        elif tag == "a" and attrs.get("href"):
            self.links.append(attrs["href"])
        elif tag == "h1":
            self.heading = []

    def handle_data(self, data):
        if self.heading is not None:
            self.heading.append(data)

    def handle_endtag(self, tag):
        if tag == "form":
            self.action = None
        elif tag == "h1" and self.heading is not None:
            self.headings.append("".join(self.heading).strip())
            self.heading = None


def zip_contents(raw):
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        assert archive.testzip() is None
        names = archive.namelist()
        assert len(names) == len(set(names))
        members = {name:archive.read(name) for name in names}
    payload = json.loads(members["campaign.json"])
    assert payload["format"] == "looking-glass-campaign" and payload["version"] == 1
    assert not {"users", "sessions", "campaign_viewers", "campaign_checkpoints"}.intersection(payload["tables"])
    assert "owner_id" not in payload["campaign"]
    return payload, members


class ZipBackups(Checkpoints):
    def __init__(self, session):
        super().__init__(session)
        self.campaign = f"/campaigns/{session.cid}"
        self.restore_path = self.campaign + "/restore"
        cookies = [c["value"] for c in session.player.context.cookies([session.viewer_url])
                   if c["name"] == "lg_viewer_session"]
        assert len(cookies) == 1
        self.viewer_cookie = cookies[0]

    def connected(self):
        super().connected()
        if hasattr(self, "viewer_cookie"):
            cookies = [c["value"] for c in self.s.player.context.cookies([self.s.viewer_url])
                       if c["name"] == "lg_viewer_session"]
            assert cookies == [self.viewer_cookie], "The viewer session changed during ZIP restore"

    def export(self):
        s = self.s
        before = s.state()
        response = s.dm.request.post(s.admin_url + self.campaign + "/backup",
                                    form={"csrf_token":s.csrf}, max_redirects=0)
        assert response.status == 200, (response.status, response.text())
        assert response.headers["content-type"].split(";")[0] == "application/zip"
        assert response.headers.get("cache-control") == "no-store"
        raw = response.body()
        zip_contents(raw)
        assert s.state() == before, "Export changed viewer state"
        self.connected()
        return raw

    def multipart(self, raw, **fields):
        return {"csrf_token":self.s.csrf, **fields,
                "backup":{"name":"campaign.zip", "mimeType":"application/zip", "buffer":raw}}

    def inspect(self, raw):
        s = self.s
        before = s.state()
        response = s.dm.request.post(s.admin_url + self.restore_path + "/inspect",
                                    multipart=self.multipart(raw), max_redirects=0)
        assert response.status == 200, (response.status, response.text())
        assert response.headers.get("cache-control") == "no-store"
        page = RestoreHTML(self.restore_path)
        page.feed(response.text())
        assert "Compatible campaign backup" in page.headings
        assert len(page.previews) == 1 and page.previews[0]
        assert s.state() == before, "ZIP inspection changed viewer state"
        self.connected()
        return page.previews[0]

    def submit(self, raw, preview, *, confirm=None, error=False):
        s = self.s
        if confirm is None:
            confirm = s.state()["campaign"]
        index = len(self.probe()["messages"])
        response = s.dm.request.post(s.admin_url + self.restore_path,
            multipart=self.multipart(raw, preview=preview, confirm=confirm), max_redirects=0)
        if error:
            assert response.status == 303, (response.status, response.text())
            parts = urlsplit(response.headers["location"])
            query = parse_qs(parts.query, keep_blank_values=True)
            assert parts.path == self.campaign
            assert query.get("err") and "ok" not in query, response.headers["location"]
            return query["err"][0]
        assert response.status == 200, (response.status, response.text())
        assert response.headers.get("cache-control") == "no-store"
        page = RestoreHTML(self.restore_path)
        page.feed(response.text())
        assert "Campaign restored" in page.headings
        pattern = re.compile(re.escape(self.campaign) + rf"/recovery/campaign-{s.cid}-[0-9a-f]{{32}}\.zip$")
        recovery = [link for link in page.links if pattern.fullmatch(link)]
        assert len(recovery) == 1, page.links
        handle = s.player.wait_for_function("""index =>
          window.__checkpointProbe.messages.slice(index).some(
            m=>m.type==='refresh' && m.reason==='campaign')
        """, arg=index, timeout=10000)
        handle.dispose()
        download = s.dm.request.get(s.admin_url + recovery[0], max_redirects=0)
        assert download.status == 200, download.status
        assert download.headers["content-type"].split(";")[0] == "application/zip"
        assert download.headers.get("cache-control") == "no-store"
        recovered = download.body()
        zip_contents(recovered)
        self.connected()
        return recovered

    def map_id(self, name):
        data, _ = zip_contents(self.export())
        ids = [m["id"] for m in data["tables"]["maps"] if m["name"] == name]
        assert len(ids) == 1, (name, ids)
        return ids[0]

    def restore_notices(self):
        return sum(m.get("reason") == "campaign" for m in self.probe()["messages"])


@pytest.fixture
def backups(live_session):
    return ZipBackups(live_session)


def test_live_zip_restore_and_downloaded_recovery_reach_connected_player(live_session, backups):
    s, h = live_session, backups
    s.gesture("reveal")
    saved = h.expect_view("Red map", RED, FOG)
    original = h.export()
    original_data, _ = zip_contents(original)
    assert {m["name"] for m in original_data["tables"]["maps"]} == {"Red map", "Green map"}

    s.open_editor(s.b)
    s.gesture("reveal", x=300)
    s.activate(s.b)
    changed = h.expect_view("Green map", FOG, GREEN)
    before_restore = h.export()
    preview = h.inspect(original)
    h.expect_view("Green map", FOG, GREEN)
    recovery = h.submit(original, preview)
    restored = h.expect_view("Red map", RED, FOG)
    assert restored["map"]["version"] != saved["map"]["version"]
    assert restored["map"]["revealed_bounds"] == saved["map"]["revealed_bounds"]
    assert restored["map"]["revealed_area_signatures"] == saved["map"]["revealed_area_signatures"]
    # Compare ZIP member content, not timestamp/compression-dependent ZIP bytes.
    assert zip_contents(recovery) == zip_contents(before_restore)

    # Re-resolve imported map identities; numeric IDs are not a restore contract.
    green_id = h.map_id("Green map")
    s.activate(green_id)
    h.expect_view("Green map", FOG, FOG)
    preview = h.inspect(recovery)
    h.expect_view("Green map", FOG, FOG)
    h.submit(recovery, preview)
    returned = h.expect_view("Green map", FOG, GREEN)
    assert returned["map"]["version"] != changed["map"]["version"]
    h.connected()

    s.open_editor(h.map_id("Green map"))
    s.gesture("hide", x=300)
    h.expect_view("Green map", FOG, FOG)
    s.undo()
    h.expect_view("Green map", FOG, GREEN)
    h.connected()


@pytest.mark.parametrize("reason", ["wrong-confirmation", "different-zip", "stale-preview"])
def test_live_rejected_zip_restore_preserves_connected_viewer(live_session, backups, reason):
    s, h = live_session, backups
    s.gesture("reveal")
    h.expect_view("Red map", RED, FOG)
    original = h.export()
    s.gesture("hide")
    h.expect_view("Red map", FOG, FOG)
    alternative = h.export()
    assert zip_contents(original) != zip_contents(alternative)
    preview = h.inspect(original)
    if reason == "stale-preview":
        s.gesture("reveal", x=300)
        h.expect_view("Red map", FOG, RED)
    expected_left, expected_right = FOG, RED if reason == "stale-preview" else FOG
    before = h.expect_view("Red map", expected_left, expected_right)
    before_archive = h.export()
    installed = s.player.locator("#map").get_attribute("src")
    notices = h.restore_notices()
    raw = alternative if reason == "different-zip" else original
    confirm = before["campaign"] + " WRONG" if reason == "wrong-confirmation" else before["campaign"]
    message = h.submit(raw, preview, confirm=confirm, error=True)
    assert ("confirm" if reason == "wrong-confirmation" else "Restore blocked") in message
    assert s.state() == before
    assert zip_contents(h.export()) == zip_contents(before_archive)
    h.expect_view("Red map", expected_left, expected_right)
    assert s.player.locator("#map").get_attribute("src") == installed
    assert h.restore_notices() == notices
    h.connected()

    # Continue real delivery after rejection without navigation or reconnection.
    if reason == "stale-preview":
        s.gesture("hide", x=300)
        h.expect_view("Red map", FOG, FOG)
    else:
        s.gesture("reveal")
        h.expect_view("Red map", RED, FOG)
    s.undo()
    h.expect_view("Red map", expected_left, expected_right)
    h.connected()
