"""Real socket revocation, old-cookie denial and unaffected viewer updates."""
import copy
import json
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

import httpx2 as httpx
import pytest

ROOT = Path(__file__).resolve().parents[3]
RECORDER = r"""(() => {
  const key = 'lg-test-revocation-closes';
  const Native = window.WebSocket;
  window.WebSocket = class extends Native {
    constructor(...args) {
      super(...args);
      this.addEventListener('close', event => {
        const values = JSON.parse(sessionStorage.getItem(key) || '[]');
        values.push(event.code);
        sessionStorage.setItem(key, JSON.stringify(values));
      });
    }
  };
})();"""
CLOSES = "lg-test-revocation-closes"


def session_token(context, url):
    values = [cookie["value"] for cookie in context.cookies([url]) if cookie["name"] == "lg_viewer_session"]
    assert len(values) == 1
    return values[0]


def expect_revoked(page):
    page.wait_for_function(
        "key => JSON.parse(sessionStorage.getItem(key) || '[]').includes(4403)",
        arg=CLOSES, timeout=10000,
    )


class Actors:
    def __init__(self, session, browser, temporary):
        self.session, self.browser, self.temporary = session, browser, temporary
        self.contexts = []
        self.pages = {"main":session.player}
        self.denials = []
        session.player.add_init_script(RECORDER)
        session.player.reload()
        session.expect_pixels("Red map", (0,0,0), (0,0,0))

    def page(self, label, shared=False):
        if shared:
            context = self.session.player.context
        else:
            context = self.browser.new_context(viewport={"width":1280,"height":900})
            self.contexts.append((label, context))
            context.tracing.start(screenshots=True, snapshots=True, sources=True)
        page = context.new_page()
        self.pages[label] = page
        page.on("pageerror", lambda error:self.session.page_errors.append(f"{label}: {error}"))
        page.add_init_script(RECORDER)
        return page

    def viewer(self, label, username="live-player", password="live-player-password", shared=False):
        s = self.session
        page = self.page(label, shared)
        if not shared:
            s.login(page, s.viewer_url, username, password)
        page.goto(f"{s.viewer_url}/c/{s.cid}")
        view = copy.copy(s)
        view.player = page
        view.expect_pixels("Red map", (0,0,0), (0,0,0))
        return view

    def root(self):
        page = self.page("root")
        self.session.login(page, self.session.admin_url, "live-root", "live-root-password")
        return page

    def denied(self, token, image_url, status):
        s = self.session
        with httpx.Client(base_url=s.viewer_url, timeout=5, trust_env=False,
                          headers={"Cookie":f"lg_viewer_session={token}"}) as client:
            for path in (f"/api/c/{s.cid}/state", image_url):
                response = client.get(path)
                assert response.status_code == status, (path, response.status_code, response.text)
                self.denials.append({"path":path,"status":response.status_code})

    def finish(self, failed, evidence):
        observed = {}
        try:
            for label, page in self.pages.items():
                try:
                    observed[label] = page.evaluate("key => JSON.parse(sessionStorage.getItem(key) || '[]')", CLOSES)
                    if failed:
                        page.screenshot(path=str(self.temporary / f"player-{label}.png"))
                except Exception as error:
                    observed[label] = {"diagnostic_error":repr(error)}
            evidence.mkdir(parents=True, exist_ok=True)
            (evidence / "observations.json").write_text(json.dumps({"close_codes":observed,"denials":self.denials}, indent=2), encoding="utf-8")
            for label, context in self.contexts:
                if failed:
                    context.tracing.stop(path=str(self.temporary / f"player-{label}-trace.zip"))
                else:
                    context.tracing.stop()
        finally:
            for label, context in reversed(self.contexts):
                context.close()
            for label, page in self.pages.items():
                if label != "main" and not page.is_closed():
                    page.close()


@pytest.fixture
def actors(live_session, live_browser, tmp_path, request):
    group = Actors.__new__(Actors)
    group.session, group.browser, group.temporary = live_session, live_browser, tmp_path
    group.contexts, group.pages, group.denials = [], {}, []
    setup_failed = False
    try:
        group.__init__(live_session, live_browser, tmp_path)
        yield group
    except BaseException:
        setup_failed = True
        raise
    finally:
        failed = setup_failed or any(getattr(request.node, "rep_" + phase, None) and
                    getattr(request.node, "rep_" + phase).failed for phase in ("setup", "call"))
        group.finish(failed, ROOT / "test-results/live-revocation" / request.node.name)


def exercise_survivor(s, view):
    s.gesture("hide")
    view.expect_pixels("Red map", (0,0,0), (0,0,0))
    s.undo()
    view.expect_pixels("Red map", (200,30,30), (0,0,0))


def test_live_logout_revokes_shared_tabs_but_preserves_independent_session(live_session, actors):
    s = live_session
    shared = actors.viewer("shared", shared=True)
    other = actors.viewer("independent")
    token = session_token(s.player.context, s.viewer_url)
    assert token == session_token(shared.player.context, s.viewer_url)
    assert token != session_token(other.player.context, s.viewer_url)
    s.gesture("reveal")
    for view in (s, shared, other):
        view.expect_pixels("Red map", (200,30,30), (0,0,0))
    image_url = s.state()["map"]["image_url"]
    csrf = s.player.locator('meta[name="csrf-token"]').get_attribute("content")
    response = s.player.request.post(s.viewer_url + "/logout", form={"csrf_token":csrf}, max_redirects=0)
    assert response.status == 303
    expect_revoked(s.player)
    expect_revoked(shared.player)
    actors.denied(token, image_url, 401)
    exercise_survivor(s, other)
    actors.denied(token, image_url, 401)
    assert 4403 not in other.player.evaluate("key => JSON.parse(sessionStorage.getItem(key) || '[]')", CLOSES)


@pytest.mark.parametrize("action", ["remove-assignment", "deactivate", "change-role"])
def test_live_user_revocation_preserves_another_authorized_account(live_session, actors, action):
    s = live_session
    location = s.form(f"/campaigns/{s.cid}/viewers/add", {"user_id":"3"})
    assert "err" not in parse_qs(urlsplit(location).query)
    second = actors.viewer("second-target-session")
    survivor = actors.viewer("other-account", "live-other-player", "live-other-player-password")
    tokens = [session_token(view.player.context, s.viewer_url) for view in (s, second)]
    assert tokens[0] != tokens[1]
    s.gesture("reveal")
    for view in (s, second, survivor):
        view.expect_pixels("Red map", (200,30,30), (0,0,0))
    image_url = s.state()["map"]["image_url"]
    if action == "remove-assignment":
        location = s.form(f"/campaigns/{s.cid}/viewers/2/remove", {})
        assert "err" not in parse_qs(urlsplit(location).query)
        denied_status = 404
    else:
        root = actors.root()
        csrf = root.locator('meta[name="csrf-token"]').get_attribute("content")
        values = {"csrf_token":csrf,"role":"viewer"}
        if action == "change-role":
            values.update(role="admin", active="true")
        response = root.request.post(s.admin_url + "/users/2/update", form=values, max_redirects=0)
        assert response.status == 303
        assert "err" not in parse_qs(urlsplit(response.headers["location"]).query)
        denied_status = 401
    for view in (s, second):
        expect_revoked(view.player)
    for token in tokens:
        actors.denied(token, image_url, denied_status)
    exercise_survivor(s, survivor)
    for token in tokens:
        actors.denied(token, image_url, denied_status)
    assert 4403 not in survivor.player.evaluate("key => JSON.parse(sessionStorage.getItem(key) || '[]')", CLOSES)
