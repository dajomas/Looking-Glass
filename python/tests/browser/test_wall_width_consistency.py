"""Compare the real fog/wall renderers at multiple map sizes, zooms and widths."""
import io
from pathlib import Path
from urllib.parse import urlparse

import pytest
from PIL import Image
from jinja2 import DictLoader, Environment

pw = pytest.importorskip("playwright.sync_api")
ROOT = Path(__file__).resolve().parents[3]


def png(w, h, rgba=False):
    out = io.BytesIO()
    Image.new("RGBA" if rgba else "RGB", (w, h), (255, 255, 255, 0) if rgba else (200, 30, 30)).save(out, "PNG")
    return out.getvalue()




def open_editor(browser, kind, size):
    page = browser.new_page(viewport={"width": 1200, "height": 800})
    width, height = size, size // 2
    walls = [[width/4, height/10, width/4, height*.9, "wall", True],
             [width/2, height/10, width/2, height*.9, "door", True],
             [width*.75, height/10, width*.75, height*.9, "secret", True]]
    data = dict(ok=True, id=1, name="M", campaign_id=4, cache_token="token", image_version="v1",
                width=width, height=height, work_width=width, work_height=height,
                walls_version=1, fog_version=1, walls=walls, walls_source="test", wall_count=3,
                op_count=0, is_active=False, live_viewers=0, disabled_wall_types=[],
                calibration=dict(offset_x=0, offset_y=0, scale_x=1, scale_y=1, doors_block=True))
    name = "wall_editor.html" if kind == "wall" else "map_editor.html"
    path = "/maps/1/walls" if kind == "wall" else "/maps/1"
    base = '<!doctype html><meta name="csrf-token" content="token"><link rel="stylesheet" href="/static/css/common.css"><body class="editor-page"><main class="editor">{% block content %}{% endblock %}</main>{% block styles %}{% endblock %}{% block scripts %}{% endblock %}</body>'
    templates = {"base.html": base, "editor.html": (ROOT/"web_html/admin"/name).read_text(),
                 "partials/_csrf.html": '<input type="hidden" name="csrf_token" value="token">',
                 "partials/_map_display_dialog.html": '<dialog id="map-display-dialog"></dialog>'}
    html = Environment(loader=DictLoader(templates)).get_template("editor.html").render(
        map=data, campaign=dict(id=4, name="C"), siblings=[dict(id=1, name="M")], fog_opacity=.55, op_count=0)
    errors, writes = [], []
    page.on("pageerror", lambda error: errors.append(str(error)))
    artwork, mask = png(width, height), png(width, height, True)
    def route(r):
        p = urlparse(r.request.url).path
        if r.request.method == "POST":
            writes.append(p)
            r.fulfill(json=data)
        elif p == path:
            r.fulfill(content_type="text/html", body=html)
        elif p.startswith("/static/"):
            f = ROOT / p.lstrip("/")
            content = f.read_text()
            if f.name == "pan_zoom.js":
                content += "\nwindow.PanZoom = class extends window.PanZoom { constructor(...args) { super(...args); window.testPanZoom = this; } };"
            r.fulfill(content_type="application/javascript" if f.suffix == ".js" else "text/css", body=content)
        elif p == "/api/maps/1/image":
            r.fulfill(content_type="image/png", body=artwork)
        elif p == "/api/maps/1/fog.png":
            r.fulfill(content_type="image/png", body=mask)
        elif p in ("/api/maps/1", "/api/maps/1/wall-editor"):
            r.fulfill(json=data)
        elif p == "/api/campaigns/4/wall-sources":
            r.fulfill(json={"sources": []})
        else:
            r.fulfill(status=404, body="Not found")
    page.route("**/*", route)
    page.goto("http://looking-glass.test" + path)
    overlay = "#wall-overlay" if kind == "wall" else "#walls-svg"
    pw.expect(page.locator(overlay + " path")).to_have_count(3)
    pw.expect(page.locator("#wall-width")).to_be_enabled()
    page.wait_for_timeout(150)
    page.add_style_tag(content=".viewport {background: #000 !important;} .stage > img, .stage > canvas {visibility: hidden !important;}")
    return page, overlay, errors, writes


def set_view(page, scale, x, y):
    page.evaluate("""([scale, x, y]) => {
      const pz = window.testPanZoom, rect = pz.vp.getBoundingClientRect();
      pz.scale = scale; pz.x = rect.width/2 - x*scale; pz.y = rect.height/2 - y*scale; pz.apply();
    }""", [scale, x, y])


def screen_width(page, selector):
    return page.locator(selector).evaluate("el => parseFloat(getComputedStyle(el).strokeWidth) * el.getScreenCTM().a")


def painted_width(page, selector, x, y, green):
    sx, sy = page.locator(selector).evaluate("""(el, [x,y]) => {
      const point = new DOMPoint(x,y).matrixTransform(el.getScreenCTM());
      return [point.x, point.y];
    }""", [x, y])
    page.locator(selector).evaluate("el => { for (const sibling of el.parentNode.querySelectorAll('path')) if (sibling !== el) sibling.style.visibility = 'hidden'; }")
    image = Image.open(io.BytesIO(page.screenshot())).convert("RGB")
    page.locator(selector).evaluate("el => { for (const sibling of el.parentNode.querySelectorAll('path')) sibling.style.visibility = ''; }")
    px, py = round(sx), round(sy)
    background = image.getpixel((px+30, py))[1]
    return sum(max(0, min(1, (image.getpixel((col, py))[1]-background)/(green-background)))
               for col in range(px-24, px+25))


@pytest.mark.parametrize("size", [400, 4000])
def test_widths_match_between_editors_at_every_zoom(browser, size):
    views = [open_editor(browser, kind, size) for kind in ("fog", "wall")]
    try:
        for scale in (.125, .5, 1, 2, 4):
            for width in (.5, 1, 2, 2.5, 5, 10):
                measurements = []
                for page, overlay, errors, writes in views:
                    set_view(page, scale, size/4, size/4)
                    page.locator("#wall-width").evaluate("(el,w) => {el.value=String(w);el.dispatchEvent(new Event('input',{bubbles:true}));}", width)
                    pw.expect(page.locator("#wall-width-value")).to_have_text(f"{width:g} px")
                    assert screen_width(page, overlay+" .w-wall") == pytest.approx(width, abs=.001)
                    for kind in ("door", "secret"):
                        assert screen_width(page, overlay+" .w-"+kind) == pytest.approx(width*2, abs=.001)
                    measurements.append(painted_width(page, overlay+" .w-wall", size/4, size/4, 91))
                    assert not errors and not writes
                # Compositor antialiasing can quantize subpixel strokes at extreme zoom-out.
                tolerance = .65 if scale < .5 and width < 1 else .3
                assert measurements[0] == pytest.approx(measurements[1], abs=tolerance)
                for measured in measurements:
                    assert measured == pytest.approx(width, abs=.55 if scale < .5 else .15)
    finally:
        for page, *_ in views:
            page.close()
