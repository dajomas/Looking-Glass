"""Deterministic delayed-response tests of the real viewer scripts.

Run: python -m pytest -q python/tests/browser/test_viewer_delayed_responses.py
HTTP payloads and WebSocket notifications are controlled test fixtures.
Native fetch, image HTTP loading and image decoding still run in Chromium.
"""
import copy
import io
from pathlib import Path
from urllib.parse import urlsplit

import pytest
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[3]
ORIGIN = "http://looking-glass.test"

HTML = """<!doctype html><style>
#viewport{position:relative;width:800px;height:500px;overflow:hidden}
#stage{position:absolute;transform-origin:0 0}#map{width:100%;height:100%}
</style><div id="viewport"><div id="stage"><img id="map"></div></div>
<div id="waiting"><span id="waiting-text"></span></div>
<i id="conn-dot"></i><span id="map-name"></span><span id="sync-status"></span>
<button id="btn-fit">Fit</button><button id="btn-full">Full</button><div id="hud"></div>
<script>window.LG_CAMPAIGN=1;</script>
<script src="/static/js/pan_zoom.js"></script>
<script src="/static/js/viewer_area_zoom.js"></script>
<script src="/static/js/viewer_display.js"></script>"""

PROBE = r"""(() => {
  const p = window.__delayProbe = {
    reports: [], fetchFinished: 0, decoded: [], held: null,
    armJSON: false, jsonHeld: false, jsonReleased: false
  };
  const fetchOriginal = window.fetch.bind(window);
  window.fetch = async (...args) => {
    const response = await fetchOriginal(...args);
    if (new URL(String(args[0]), location.href).pathname === '/api/c/1/state') {
      setTimeout(() => { p.fetchFinished++; }, 0);
      const readJSON = response.json.bind(response);
      response.json = async () => {
        const value = await readJSON();
        if (p.armJSON) {
          p.armJSON = false;
          await new Promise(resolve => { p.releaseJSON = resolve; p.jsonHeld = true; });
          setTimeout(() => { p.jsonReleased = true; }, 0);
        }
        return value;
      };
    }
    return response;
  };
  const decodeOriginal = HTMLImageElement.prototype.decode;
  HTMLImageElement.prototype.decode = function (...args) {
    const url = this.src;
    return decodeOriginal.apply(this, args).finally(() => {
      setTimeout(() => { p.decoded.push(new URL(url, location.href).pathname); }, 0);
    });
  };
  window.WebSocket = class {
    constructor() { this.readyState = 0; p.socket = this; }
    send(text) {
      if (text === 'ping') return;
      p.reports.push(JSON.parse(text));
    }
    close() { this.readyState = 3; this.onclose?.({code:1000}); }
  };
})();"""


def payload(version, name, image):
    return {"map": {"id":int(version.split('-')[0]), "name":name,
                    "width":400, "height":200, "version":version,
                    "image_url":f"/test-images/{image}.png",
                    "revealed_bounds":{"x":0,"y":0,"width":200,"height":200},
                    "revealed_area_signatures":["left"]}}


BASE = payload("1-v1", "Original map", "red")
NEW = payload("1-v2", "Updated map", "green")
LATEST = payload("1-v3", "Latest fog", "blue")
OTHER = payload("2-v1", "Other map", "blue")
COLORS = {"red":(200,30,30), "green":(30,200,30), "blue":(30,30,200)}


def png(color):
    image = Image.new("RGB", (400,200), (0,0,0))
    ImageDraw.Draw(image).rectangle((0,0,199,199), fill=color)
    stream = io.BytesIO()
    image.save(stream, "PNG")
    return stream.getvalue()


class Viewer:
    def __init__(self, page):
        self.page = page
        self.current = copy.deepcopy(BASE)
        self.arm_headers = False
        self.arm_image = None
        self.pending = None
        self.errors = []
        self.images = {f"/test-images/{name}.png":png(color) for name,color in COLORS.items()}
        page.on("pageerror", lambda error:self.errors.append(str(error)))
        page.add_init_script(PROBE)
        page.route("**/*", self.route)

    def route(self, route):
        path = urlsplit(route.request.url).path
        if route.request.method != "GET":
            self.errors.append(f"Unexpected write: {route.request.method} {path}")
            route.fulfill(status=405, body="Unexpected write")
        elif path == "/c/1":
            route.fulfill(content_type="text/html", body=HTML)
        elif path.startswith("/static/js/"):
            route.fulfill(content_type="application/javascript",
                          body=(ROOT / path.lstrip("/")).read_text(encoding="utf-8"))
        elif path == "/api/c/1/state":
            state = copy.deepcopy(self.current)
            if self.arm_headers:
                self.arm_headers = False
                self.capture(route, "state", state)
            else:
                route.fulfill(json=state, headers={"Cache-Control":"no-store"})
        elif path in self.images:
            if path == self.arm_image:
                self.arm_image = None
                self.capture(route, path, self.images[path])
            else:
                route.fulfill(content_type="image/png", body=self.images[path],
                              headers={"Cache-Control":"no-store"})
        elif path == "/favicon.ico":
            route.fulfill(status=204)
        else:
            self.errors.append(f"Unexpected request: {path}")
            route.fulfill(status=404, body="Unexpected request")

    def capture(self, route, kind, body):
        assert self.pending is None, "Only one HTTP barrier may be armed per test"
        self.pending = (route, kind, body)
        self.page.evaluate("kind => { window.__delayProbe.held = kind; }", kind)

    def wait(self, expression, arg=None):
        result = self.page.wait_for_function(expression, arg=arg, timeout=5000)
        result.dispose()

    def start(self):
        self.page.goto(ORIGIN + "/c/1")
        self.wait("() => !document.getElementById('stage').hidden && document.getElementById('map').complete")
        self.page.evaluate("() => { const s=window.__delayProbe.socket; s.readyState=1; s.onopen(); }")
        self.wait("() => window.__delayProbe.reports.filter(r => r.state === 'ready' && r.version === '1-v1').length >= 2")
        self.expect_display(BASE, COLORS["red"])

    def refresh(self, state=None):
        if state is not None:
            self.current = copy.deepcopy(state)
        self.page.evaluate("() => window.__delayProbe.socket.onmessage({data:JSON.stringify({type:'refresh'})})")

    def wait_held(self, kind):
        self.wait("kind => window.__delayProbe.held === kind", kind)
        assert self.pending is not None

    def release(self, *, broken=False):
        assert self.pending is not None
        route, kind, body = self.pending
        self.pending = None
        if kind == "state":
            before = self.page.evaluate("window.__delayProbe.fetchFinished")
            route.fulfill(json=body, headers={"Cache-Control":"no-store"})
            self.wait("before => window.__delayProbe.fetchFinished > before", before)
        else:
            route.fulfill(content_type="image/png", body=b"invalid PNG" if broken else body,
                          headers={"Cache-Control":"no-store"})
            self.wait("path => window.__delayProbe.decoded.includes(path)", kind)

    def reports(self):
        return self.page.evaluate("window.__delayProbe.reports")

    def assert_ready_since(self, index, version):
        ready = [r for r in self.reports()[index:] if r.get("state") == "ready"]
        assert all(r["version"] == version for r in ready), ready

    def expect_display(self, state, color):
        m = state["map"]
        self.wait("expected => { const im=document.getElementById('map'); return !document.getElementById('stage').hidden && document.getElementById('waiting').hidden && document.getElementById('map-name').textContent===expected.name && im.complete && im.naturalWidth===400 && new URL(im.src).pathname===expected.image_url && document.getElementById('sync-status').textContent==='Up to date'; }", m)
        pixels = self.page.evaluate("""() => {
          const canvas=document.createElement('canvas'); canvas.width=400; canvas.height=200;
          const ctx=canvas.getContext('2d'); ctx.drawImage(document.getElementById('map'),0,0);
          return [Array.from(ctx.getImageData(50,100,1,1).data).slice(0,3),
                  Array.from(ctx.getImageData(350,100,1,1).data).slice(0,3)];
        }""")
        assert pixels == [list(color), [0,0,0]]
        assert self.reports()[-1]["state"] == "ready"
        assert self.reports()[-1]["version"] == m["version"]

    def expect_blank(self):
        self.wait("() => document.getElementById('stage').hidden && !document.getElementById('waiting').hidden && document.getElementById('map-name').textContent==='' && document.getElementById('sync-status').textContent==='Up to date'")
        assert self.reports()[-1]["state"] == "ready"
        assert self.reports()[-1]["version"] == "blank"


@pytest.fixture
def viewer(browser):
    context = browser.new_context(viewport={"width":1000,"height":700})
    h = Viewer(context.new_page())
    try:
        h.start()
        yield h
        assert not h.errors, h.errors
    finally:
        if h.pending is not None:
            try:
                h.pending[0].abort()
            except Exception:
                pass
        context.close()


def test_old_state_headers_cannot_revert_newer_display(viewer):
    h = viewer
    h.arm_headers = True
    h.refresh()
    h.wait_held("state")
    h.refresh(NEW)
    h.expect_display(NEW, COLORS["green"])
    cut = len(h.reports())
    h.release()
    h.expect_display(NEW, COLORS["green"])
    h.assert_ready_since(cut, NEW["map"]["version"])


def test_old_state_json_cannot_revert_newer_display(viewer):
    h = viewer
    h.page.evaluate("window.__delayProbe.armJSON = true")
    h.refresh()
    h.wait("() => window.__delayProbe.jsonHeld")
    h.refresh(NEW)
    h.expect_display(NEW, COLORS["green"])
    cut = len(h.reports())
    h.page.evaluate("window.__delayProbe.releaseJSON()")
    h.wait("() => window.__delayProbe.jsonReleased")
    h.expect_display(NEW, COLORS["green"])
    h.assert_ready_since(cut, NEW["map"]["version"])


@pytest.mark.parametrize("target", ["same-map", "other-map", "blank"])
def test_old_image_cannot_replace_newer_scene(viewer, target):
    h = viewer
    h.arm_image = NEW["map"]["image_url"]
    h.refresh(NEW)
    h.wait_held(h.arm_image or NEW["map"]["image_url"])
    state = {"same-map":LATEST, "other-map":OTHER, "blank":{"map":None}}[target]
    h.refresh(state)
    if target == "blank":
        h.expect_blank()
    else:
        h.expect_display(state, COLORS["blue"])
    cut = len(h.reports())
    h.release()
    if target == "blank":
        h.expect_blank()
    else:
        h.expect_display(state, COLORS["blue"])
    h.assert_ready_since(cut, "blank" if target == "blank" else state["map"]["version"])


def test_current_delayed_image_is_not_ready_before_decode(viewer):
    h = viewer
    cut = len(h.reports())
    h.arm_image = NEW["map"]["image_url"]
    h.refresh(NEW)
    h.wait_held(NEW["map"]["image_url"])
    assert h.page.locator("#sync-status").inner_text() == "Loading"
    reports = h.reports()[cut:]
    assert any(r.get("state") == "loading" and r.get("version") == "1-v2" for r in reports)
    assert not any(r.get("state") == "ready" and r.get("version") == "1-v2" for r in reports)
    assert h.page.locator("#map").get_attribute("src").endswith("/test-images/red.png")
    h.release()
    h.expect_display(NEW, COLORS["green"])


def test_delayed_failed_image_retries_without_version_change_or_reload(viewer):
    h = viewer
    h.arm_image = NEW["map"]["image_url"]
    h.refresh(NEW)
    h.wait_held(NEW["map"]["image_url"])
    h.release(broken=True)
    h.wait("() => document.getElementById('sync-status').textContent === 'Display failed'")
    assert h.reports()[-1]["state"] == "failed"
    cut = len(h.reports())
    h.refresh()
    h.expect_display(NEW, COLORS["green"])
    h.assert_ready_since(cut, NEW["map"]["version"])
