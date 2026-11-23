from browser_support import template_environment
"""I2: left-button drag moves wall endpoints; joined corners move together."""
import io
from pathlib import Path
import re
from urllib.parse import urlparse

import pytest
from PIL import Image

pw = pytest.importorskip("playwright.sync_api")
ROOT = Path(__file__).resolve().parents[3]
from test_portal_editor import apply, connect, open_popup  # noqa: E402

WALLS = [[100, 50, 200, 50, "wall", True],     # 0: joined to wall 1 at (200, 50)
         [200, 50, 200, 150, "door", True],    # 1
         [300, 50, 300, 150, "wall", False]]   # 2: separate; passive flag must survive
BLANK = {"sides": [{"role": "unconfigured"}, {"role": "unconfigured"}]}
PORTALS = [[10, 10, 390, 10, "wall", True], [100, 30, 100, 170, "portal", True, BLANK],
           [300, 30, 300, 170, "portal", True, BLANK]]


@pytest.fixture
def walls(browser, request):
    page = browser.new_page(viewport={"width": 1200, "height": 800})
    page.set_default_timeout(4000)
    initial = getattr(request, "param", WALLS)
    data = dict(ok=True, id=1, name="M", campaign_id=4, cache_token="token", image_version="image1",
                width=400, height=200, walls_version=1, walls=[[*w[:6], *[dict(x) for x in w[6:]]] for w in initial])
    templates = {"base.html": '<!doctype html><meta name="csrf-token" content="token"><link rel="stylesheet" href="/static/css/common.css"><link rel="stylesheet" href="/static/css/admin.css"><body class="editor-page"><main class="editor">{% block content %}{% endblock %}</main>{% block styles %}{% endblock %}{% block scripts %}{% endblock %}</body>',
                 "editor.html": (ROOT / "web_html/admin/wall_editor.html").read_text()}
    html = template_environment(templates).get_template("editor.html").render(map=data, campaign=dict(id=4, name="C"))
    image = io.BytesIO(); Image.new("RGB", (400, 200), (200, 200, 200)).save(image, "PNG")
    errors, writes = [], []
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.on("dialog", lambda dialog: dialog.dismiss())

    def route(r):
        path = urlparse(r.request.url).path
        if r.request.method == "POST":
            body = r.request.post_data_json; writes.append(body)
            data["walls"] = body["walls"]; data["walls_version"] += 1
            r.fulfill(json=dict(data, source_id=7))
        elif path == "/maps/1/walls": r.fulfill(content_type="text/html", body=html)
        elif path.startswith("/static/"):
            f = ROOT / path.lstrip("/")
            r.fulfill(content_type="application/javascript" if f.suffix == ".js" else "text/css", body=f.read_text())
        elif path == "/api/maps/1/wall-editor": r.fulfill(json=data)
        elif path == "/api/maps/1/image": r.fulfill(content_type="image/png", body=image.getvalue())
        else: r.fulfill(status=404, body="Not found")
    page.route("**/*", route)
    page.goto("http://looking-glass.test/maps/1/walls")
    pw.expect(page.locator("#wall-tool")).to_be_enabled()
    yield page, writes, data
    assert not errors
    page.close()


def point(page, x, y):
    return page.locator("#wall-overlay").evaluate(
        "(el,[x,y])=>{const p=new DOMPoint(x,y).matrixTransform(el.getScreenCTM());return [p.x,p.y];}", [x, y])


def no_snap(page):
    # The option sits in a collapsed panel; the editor reads it on every placement.
    page.locator("#snap-ends").evaluate("el => { el.checked = false; }")
    page.locator("#wall-viewport").focus()   # keyboard shortcuts ignore focused inputs


def drag(page, start, end, release=True):
    page.mouse.move(*point(page, *start)); page.mouse.down()
    page.mouse.move(*point(page, *end), steps=8)
    if release: page.mouse.up()


def saved(page, writes):
    page.click("#wall-save")
    pw.expect(page.locator("#wall-status")).to_contain_text("Saved")
    return writes[-1]["walls"]


def overlay(page):
    return page.locator("#wall-overlay").inner_html()


def transform(page):
    return page.locator("#wall-stage").get_attribute("style")


def test_corner_drag_moves_all_joined_walls_and_saves(walls):
    page, writes, _ = walls
    no_snap(page)
    before = transform(page)
    drag(page, (200, 50), (230, 80))
    pw.expect(page.locator("#wall-status")).to_contain_text("Moved 2 joined endpoints")
    assert transform(page) == before, "an endpoint drag must not pan"
    pw.expect(page.locator("#wall-undo")).to_be_enabled()
    result = saved(page, writes)
    assert result[0][:4] == pytest.approx([100, 50, 230, 80], abs=0.6)
    assert result[1][:4] == pytest.approx([230, 80, 200, 150], abs=0.6)
    assert result[0][2:4] == result[1][0:2], "the corner stays closed"
    assert result[0][4:] == ["wall", True] and result[1][4:] == ["door", True]
    assert result[2] == WALLS[2]


def test_alt_drag_detaches_one_wall_from_the_corner(walls):
    page, writes, _ = walls
    no_snap(page)
    page.keyboard.down("Alt")
    drag(page, (200, 50), (230, 20))
    page.keyboard.up("Alt")
    pw.expect(page.locator("#wall-status")).to_contain_text("Moved an endpoint")
    result = saved(page, writes)
    moved = [w for w in result[:2] if [200, 50] not in (w[0:2], w[2:4])]
    assert len(moved) == 1, result
    assert result[2] == WALLS[2]


def test_single_step_undo_redo_and_escape_cancel(walls):
    page, writes, _ = walls
    no_snap(page)
    original = overlay(page)
    drag(page, (300, 150), (340, 180))
    moved = overlay(page)
    assert moved != original
    page.keyboard.press("Control+z"); assert overlay(page) == original
    pw.expect(page.locator("#wall-undo")).to_be_disabled()
    page.keyboard.press("Control+Shift+z"); assert overlay(page) == moved
    page.keyboard.press("Control+z")
    drag(page, (300, 150), (340, 180), release=False)
    assert overlay(page) != original, "the wall follows the pointer while dragging"
    page.keyboard.press("Escape")
    assert overlay(page) == original
    page.mouse.up()
    assert overlay(page) == original
    pw.expect(page.locator("#wall-status")).to_contain_text("cancelled")
    pw.expect(page.locator("#wall-undo")).to_be_disabled()
    assert not writes


@pytest.mark.parametrize("tool", ["add", "remove", "type", "edit"])
def test_drag_works_in_every_tool_without_the_tool_action(walls, tool):
    page, writes, _ = walls
    page.select_option("#wall-tool", tool)
    no_snap(page)
    drag(page, (300, 50), (320, 30))
    pw.expect(page.locator("#wall-edit-dialog")).to_be_hidden()
    pw.expect(page.locator("#wall-overlay circle")).to_have_count(0)
    result = saved(page, writes)
    assert len(result) == 3 and result[2][4:] == ["wall", False]
    assert result[2][:2] == pytest.approx([320, 30], abs=0.6) and result[2][2:4] == [300, 150]


def test_press_away_from_endpoints_still_pans_and_click_keeps_tool(walls):
    page, writes, _ = walls
    original, before = overlay(page), transform(page)
    drag(page, (250, 120), (270, 140))
    assert transform(page) != before and overlay(page) == original
    page.mouse.click(*point(page, 200, 50))          # Add tool: a click on an endpoint starts a wall
    pw.expect(page.locator("#wall-overlay circle")).to_have_count(1)
    pw.expect(page.locator("#wall-undo")).to_be_disabled()
    assert not writes


def test_snap_and_image_clamp_apply_on_release(walls):
    page, writes, _ = walls
    drag(page, (300, 150), (202, 148))              # within 10 screen px of the corner end (200, 150)
    result = saved(page, writes)
    assert result[2][2:4] == [200, 150]
    drag(page, (100, 50), (-40, -30))               # outside the image
    assert saved(page, writes)[0][:2] == [0, 0]


def test_zero_length_result_is_rejected(walls):
    page, writes, _ = walls
    original = overlay(page)
    drag(page, (300, 50), (301, 149))               # snaps onto the same wall's other end
    pw.expect(page.locator("#wall-status")).to_contain_text("must differ")
    assert overlay(page) == original
    pw.expect(page.locator("#wall-undo")).to_be_disabled()
    assert not writes


def test_hover_shows_a_grab_cursor_on_endpoints_only(walls):
    page, _, _ = walls
    viewport = page.locator("#wall-viewport")
    page.mouse.move(*point(page, 300, 150))
    pw.expect(viewport).to_have_class(re.compile(r"endpoint-hover"))
    assert viewport.evaluate("el=>getComputedStyle(el).cursor") == "grab"
    page.mouse.move(*point(page, 300, 100))
    assert "endpoint-hover" not in viewport.get_attribute("class")


@pytest.mark.parametrize("walls", [PORTALS], indirect=True)
def test_paired_portal_endpoint_drag_keeps_its_pairing(walls):
    page, writes, data = walls
    open_popup(page); connect(page); apply(page)
    saved(page, writes)
    pair = data["walls"][1][6]["pair"]
    assert pair and data["walls"][2][6]["pair"] == pair
    no_snap(page)
    drag(page, (100, 30), (120, 45))
    pw.expect(page.locator("#wall-status")).to_contain_text("Moved an endpoint")
    portal = saved(page, writes)[1]
    assert portal[:2] == pytest.approx([120, 45], abs=0.6) and portal[2:4] == [100, 170]
    assert portal[4] == "portal" and portal[6]["pair"] == pair == data["walls"][2][6]["pair"]
