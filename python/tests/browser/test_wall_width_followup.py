from browser_support import template_environment, fulfill_auxiliary
"""Follow-up regressions: native slider input, immediate paint, independent panels."""
import io
from pathlib import Path
from urllib.parse import urlparse

import pytest
from PIL import Image
from jinja2 import DictLoader, Environment

pw = pytest.importorskip("playwright.sync_api")
from test_editor_controls import png


@pytest.fixture
def page(browser):
    page = browser.new_page(viewport={"width": 1200, "height": 800})
    try:
        yield page
    finally:
        page.close()


ROOT = Path(__file__).resolve().parents[3]


def load_editor(page, kind):
    walls = [[100, 20, 100, 180, "wall", True], [200, 20, 200, 180, "door", True]]
    data = dict(ok=True, id=1, name="M", campaign_id=4, cache_token="token", image_version="image1",
                width=400, height=200, work_width=400, work_height=200, walls_version=1,
                fog_version=1, walls=walls, walls_source="test", wall_count=2, op_count=0,
                is_active=False, live_viewers=0, disabled_wall_types=[],
                calibration=dict(offset_x=0, offset_y=0, scale_x=1, scale_y=1, doors_block=True))
    name = "wall_editor.html" if kind == "wall" else "map_editor.html"
    path = "/maps/1/walls" if kind == "wall" else "/maps/1"
    templates = {"base.html": '<!doctype html><meta name="csrf-token" content="token"><link rel="stylesheet" href="/static/css/common.css"><body class="editor-page"><main class="editor">{% block content %}{% endblock %}</main>{% block styles %}{% endblock %}{% block scripts %}{% endblock %}</body>',
                 "editor.html": (ROOT / "web_html/admin" / name).read_text(),
                 "partials/_csrf.html": '<input type="hidden" name="csrf_token" value="token">',
                 "partials/_map_display_dialog.html": '<dialog id="map-display-dialog"></dialog>'}
    html = template_environment(templates).get_template("editor.html").render(
        map=data, campaign=dict(id=4, name="C"), siblings=[dict(id=1, name="M")], fog_opacity=.55, op_count=0)
    state = {"posts": [], "errors": []}
    page.on("pageerror", lambda error: state["errors"].append(str(error)))
    def route(r):
        if fulfill_auxiliary(r, data): return
        req = r.request
        p = urlparse(req.url).path
        if req.method == "POST":
            state["posts"].append(p)
            r.fulfill(json=data)
        elif p == path:
            r.fulfill(content_type="text/html", body=html)
        elif p.startswith("/static/"):
            f = ROOT / p.lstrip("/")
            r.fulfill(content_type="application/javascript" if f.suffix == ".js" else "text/css", body=f.read_text())
        elif p == "/api/maps/1/image":
            r.fulfill(content_type="image/png", body=png())
        elif p == "/api/maps/1/fog.png":
            r.fulfill(content_type="image/png", body=png("RGBA", (255, 255, 255, 0)))
        elif p in ("/api/maps/1", "/api/maps/1/wall-editor"):
            r.fulfill(json=data)
        elif p == "/api/campaigns/4/wall-sources":
            r.fulfill(json={"sources": []})
        else:
            r.fulfill(status=404, body="Not found")
    page.route("**/*", route)
    page.goto("http://looking-glass.test" + path)
    overlay = "#wall-overlay" if kind == "wall" else "#walls-svg"
    pw.expect(page.locator(overlay + " path")).to_have_count(2)
    pw.expect(page.locator("#wall-width")).to_be_enabled()
    return state, overlay


def painted_width(page, overlay):
    x, y = page.locator(overlay + " .w-wall").evaluate("""el => {
      const point = new DOMPoint(100, 100).matrixTransform(el.getScreenCTM());
      return [point.x, point.y];
    }""")
    image = Image.open(io.BytesIO(page.screenshot())).convert("RGB")
    row = int(round(y))
    return sum(1 for col in range(int(x) - 15, int(x) + 16)
               if (lambda c: c[0] > 235 and 65 < c[1] < 130 and c[2] > 180)(image.getpixel((col, row))))


@pytest.mark.parametrize("kind", ["battle", "wall"])
def test_native_drag_changes_label_and_painted_stroke_before_any_edit(page, kind):
    state, overlay = load_editor(page, kind)
    before = painted_width(page, overlay)
    slider = page.locator("#wall-width")
    slider.scroll_into_view_if_needed()
    box = slider.bounding_box()
    x0 = box["x"] + 8 + (2 - .5) / 9.5 * (box["width"] - 16)
    page.mouse.move(x0, box["y"] + box["height"] / 2)
    page.mouse.down()
    page.mouse.move(box["x"] + box["width"] - 10, box["y"] + box["height"] / 2, steps=12)
    # Check while the thumb is still held, not after a separate click or wall edit.
    width = float(slider.input_value())
    assert width >= 8
    pw.expect(page.locator("#wall-width-value")).to_have_text(f"{width:g} px")
    assert painted_width(page, overlay) >= before + 4
    page.mouse.up()
    assert not state["posts"] and not state["errors"]


@pytest.mark.parametrize("kind", ["battle", "wall"])
def test_keyboard_width_zoom_and_reload(page, kind):
    state, overlay = load_editor(page, kind)
    slider = page.locator("#wall-width")
    slider.focus()
    slider.press("Home")
    slider.press("ArrowRight")
    pw.expect(page.locator("#wall-width-value")).to_have_text("1 px")
    slider.press("End")
    pw.expect(page.locator("#wall-width-value")).to_have_text("10 px")
    before = painted_width(page, overlay)
    page.click("#wall-zoom-in" if kind == "wall" else "#zoom-in")
    assert abs(painted_width(page, overlay) - before) <= 1
    page.reload()
    pw.expect(page.locator(overlay + " path")).to_have_count(2)
    pw.expect(page.locator("#wall-width-value")).to_have_text("10 px")
    assert not state["posts"] and not state["errors"]


def test_sources_and_legend_are_independent_siblings(page):
    state, _ = load_editor(page, "battle")
    page.locator("#walls-panel > summary").click()
    pw.expect(page.locator("#wall-width")).to_be_hidden()
    pw.expect(page.locator("#source-save")).to_be_visible()
    pw.expect(page.locator("#apply-wall-types")).to_be_visible()
    for ident in ("saved-wall-library", "wall-legend"):
        assert page.locator(f"#{ident}").evaluate("el => !el.parentElement.closest('details')")
        page.locator(f"#{ident} > summary").click()
        assert not page.locator(f"#{ident}").evaluate("el => el.open")
    assert not state["posts"] and not state["errors"]
