"""Connected-viewer checkpoint restore through real HTTP, DB, images and WS.

Run: LG_RUN_LIVE_E2E=1 python -m pytest -q python/tests/live_e2e/test_live_checkpoints.py
No response interception or synthetic WebSocket transport is used.
"""
import re
from urllib.parse import parse_qs, urlsplit

import pytest
from playwright.sync_api import expect

RED = (200,30,30)
GREEN = (30,200,30)
FOG = (0,0,0)

RECORDER = r"""(() => {
  const probe = window.__checkpointProbe = {
    documentId: crypto.randomUUID(), opens: 0, closes: 0, messages: [], reports: []
  };
  const NativeSocket = window.WebSocket;
  window.WebSocket = class extends NativeSocket {
    constructor(...args) {
      super(...args);
      this.addEventListener('open', () => { probe.opens++; });
      this.addEventListener('close', () => { probe.closes++; });
      this.addEventListener('message', event => {
        try {
          const value = JSON.parse(event.data);
          if (value?.type === 'refresh') probe.messages.push(value);
        } catch (_) {}
      });
    }
    send(data) {
      const result = super.send(data);
      try {
        const value = JSON.parse(data);
        if (value?.type === 'viewer-status') probe.reports.push(value);
      } catch (_) {}
      return result;
    }
  };
})();"""


class Checkpoints:
    def __init__(self, session):
        self.s = session
        self.base = f"/campaigns/{session.cid}/checkpoints"
        self.checkpoint_pattern = re.compile(re.escape(self.base) + r"/(\d+)$")
        # Install observation before the connection used by these cases opens.
        # This is setup only; no player navigation/reload occurs during restore.
        session.player.add_init_script(RECORDER)
        session.player.reload()
        self.expect_view("Red map", FOG, FOG)
        self.document_id = session.player.evaluate("window.__checkpointProbe.documentId")
        self.connected()

    def probe(self):
        return self.s.player.evaluate("window.__checkpointProbe")

    def connected(self):
        probe = self.probe()
        assert probe["documentId"] == self.document_id
        assert probe["opens"] == 1 and probe["closes"] == 0, probe
        expect(self.s.player.locator("#conn-dot")).to_have_class(re.compile(r"\bon\b"))

    def expect_view(self, name, left, right):
        s = self.s
        s.expect_pixels(name, left, right)
        state = s.state()
        assert state["ok"] and state["map"]["name"] == name, state
        m = state["map"]
        handle = s.player.wait_for_function("""expected => {
          const p=window.__checkpointProbe, image=document.getElementById('map');
          const report=p?.reports[p.reports.length-1];
          return p?.opens===1 && p.closes===0 && !document.getElementById('stage').hidden &&
            image.complete && image.src===new URL(expected.image_url,location.href).href &&
            report?.state==='ready' && report.version===expected.version;
        }""", arg=m, timeout=10000)
        handle.dispose()
        return state

    def post_form(self, path, fields, *, error=False):
        s = self.s
        response = s.dm.request.post(s.admin_url + path,
            form={"csrf_token":s.csrf, **fields}, max_redirects=0)
        assert response.status == 303, (response.status, response.text())
        location = response.headers["location"]
        parts = urlsplit(location)
        query = parse_qs(parts.query, keep_blank_values=True)
        if error:
            assert query.get("err") and "ok" not in query, location
        else:
            assert query.get("ok") and "err" not in query and "error" not in query, location
        return parts.path, query

    def entries(self):
        s = self.s
        s.dm.goto(s.admin_url + self.base)
        entries = {}
        for link in s.dm.locator("a[href]").all():
            match = self.checkpoint_pattern.fullmatch(urlsplit(link.get_attribute("href")).path)
            if match:
                checkpoint_id = int(match.group(1))
                assert checkpoint_id not in entries
                entries[checkpoint_id] = {
                    "name":link.inner_text().strip(),
                    "automatic":"Automatic safety" in link.locator("xpath=..").inner_text(),
                }
        return entries

    def create(self, name):
        s = self.s
        before = s.state()
        old = self.entries()
        path, _ = self.post_form(self.base, {"name":name})
        assert path == self.base
        entries = self.entries()
        assert set(old).issubset(entries)
        created = set(entries) - set(old)
        assert len(created) == 1, entries
        checkpoint_id = created.pop()
        assert entries[checkpoint_id] == {"name":name,"automatic":False}
        assert s.state() == before, "Saving a checkpoint changed viewer state"
        s.open_editor(s.mid)
        self.connected()
        return checkpoint_id

    def preview(self, checkpoint_id):
        s = self.s
        before = s.state()
        path = f"{self.base}/{checkpoint_id}"
        s.dm.goto(s.admin_url + path)
        form = s.dm.locator(f'form[action="{path}/restore"]')
        expect(form).to_have_count(1)
        token = form.locator('input[name="token"]').get_attribute("value")
        assert token and len(token) == 64
        assert s.state() == before, "Preview changed viewer state"
        self.connected()
        return token

    def restore(self, checkpoint_id):
        s = self.s
        before = s.state()
        entries_before = self.entries()
        token = self.preview(checkpoint_id)
        notice_index = len(self.probe()["messages"])
        path, _ = self.post_form(f"{self.base}/{checkpoint_id}/restore",
                                {"token":token,"confirm":before["campaign"]})
        assert path == self.base
        handle = s.player.wait_for_function("""index =>
          window.__checkpointProbe.messages.slice(index).some(
            m=>m.type==='refresh' && m.reason==='session-checkpoint')
        """, arg=notice_index, timeout=10000)
        handle.dispose()
        entries_after = self.entries()
        assert set(entries_before).issubset(entries_after)
        safety = set(entries_after) - set(entries_before)
        assert len(safety) == 1, entries_after
        assert entries_after[safety.pop()]["automatic"], entries_after
        self.connected()
        return before


@pytest.fixture
def checkpoints(live_session):
    return Checkpoints(live_session)


def test_live_checkpoint_restore_reinstalls_same_map_fog(live_session, checkpoints):
    s, h = live_session, checkpoints
    s.gesture("reveal")
    saved = h.expect_view("Red map", RED, FOG)
    checkpoint_id = h.create("Before fog change")
    s.gesture("hide")
    h.expect_view("Red map", FOG, FOG)
    s.gesture("reveal", x=300)
    changed = h.expect_view("Red map", FOG, RED)
    h.restore(checkpoint_id)
    restored = h.expect_view("Red map", RED, FOG)
    assert restored["map"]["version"] not in {
        saved["map"]["version"], changed["map"]["version"]}
    assert restored["map"]["revealed_bounds"] == saved["map"]["revealed_bounds"]
    assert restored["map"]["revealed_area_signatures"] == saved["map"]["revealed_area_signatures"]
    h.connected()
    # Verify normal delivery and undo still work after restore.
    s.open_editor(s.a)
    s.gesture("hide")
    h.expect_view("Red map", FOG, FOG)
    s.undo()
    h.expect_view("Red map", RED, FOG)
    h.connected()


def test_live_checkpoint_restore_switches_active_map_and_saved_fog(live_session, checkpoints):
    s, h = live_session, checkpoints
    s.gesture("reveal")
    saved = h.expect_view("Red map", RED, FOG)
    checkpoint_id = h.create("Before changing active map")
    s.open_editor(s.b)
    s.gesture("reveal", x=300)
    s.activate(s.b)
    h.expect_view("Green map", FOG, GREEN)
    h.restore(checkpoint_id)
    restored = h.expect_view("Red map", RED, FOG)
    assert restored["map"]["version"] != saved["map"]["version"]
    assert restored["map"]["revealed_bounds"] == saved["map"]["revealed_bounds"]
    h.connected()
    # Campaign-wide restore also removes exploration added to the other map.
    s.activate(s.b)
    h.expect_view("Green map", FOG, FOG)
    h.connected()


def test_live_rejected_checkpoint_restore_preserves_connected_viewer(live_session, checkpoints):
    s, h = live_session, checkpoints
    s.gesture("reveal")
    h.expect_view("Red map", RED, FOG)
    checkpoint_id = h.create("Before rejected restore")
    s.gesture("hide")
    h.expect_view("Red map", FOG, FOG)
    s.gesture("reveal", x=300)
    before = h.expect_view("Red map", FOG, RED)
    entries_before = h.entries()
    token = h.preview(checkpoint_id)
    notice_count = sum(m.get("reason") == "session-checkpoint" for m in h.probe()["messages"])
    installed = s.player.locator("#map").get_attribute("src")
    path, query = h.post_form(f"{h.base}/{checkpoint_id}/restore",
        {"token":token,"confirm":before["campaign"] + " WRONG"}, error=True)
    assert path == f"{h.base}/{checkpoint_id}"
    assert "confirm" in query["err"][0].lower(), query
    assert s.state() == before
    assert h.entries() == entries_before, "Rejected restore created/deleted a checkpoint"
    h.expect_view("Red map", FOG, RED)
    assert s.player.locator("#map").get_attribute("src") == installed
    assert sum(m.get("reason") == "session-checkpoint" for m in h.probe()["messages"]) == notice_count
    h.connected()
    s.open_editor(s.a)
    s.gesture("hide", x=300)
    h.expect_view("Red map", FOG, FOG)
    s.undo()
    h.expect_view("Red map", FOG, RED)
    h.connected()
