"""Real-template/browser regressions for the wall Edit modal (API responses mocked)."""
import io
import json
from pathlib import Path
from urllib.parse import urlparse

import pytest
from PIL import Image
from jinja2 import DictLoader, Environment

pw = pytest.importorskip("playwright.sync_api")
ROOT = Path(__file__).resolve().parents[3]


@pytest.fixture(scope="module")
def browser():
    with pw.sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True, args=["--no-sandbox"])
        yield browser
        browser.close()


@pytest.fixture
def editor(browser):
    page = browser.new_page(viewport={"width": 1200, "height": 800})
    data = dict(ok=True, id=1, name="Map", campaign_id=4, cache_token="token", image_version="image1",
                width=400, height=200, walls_version=1,
                walls=[[100.125, 30.25, 100.125, 170.75, "wall", False], [200, 30, 200, 170, "door", True]])
    templates = {"base.html": '<!doctype html><meta name="csrf-token" content="token"><link rel="stylesheet" href="/static/css/common.css"><body class="editor-page"><main class="editor">{% block content %}{% endblock %}</main>{% block styles %}{% endblock %}{% block scripts %}{% endblock %}</body>',
                 "editor.html": (ROOT/"web_html/admin/wall_editor.html").read_text()}
    html = Environment(loader=DictLoader(templates)).get_template("editor.html").render(map=data, campaign=dict(id=4, name="C"))
    out = io.BytesIO()
    Image.new("RGB", (400,200), (200,30,30)).save(out, "PNG")
    artwork = out.getvalue()
    records, errors = [], []
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.on("dialog", lambda dialog: dialog.dismiss())
    def route(r):
        p = urlparse(r.request.url).path
        if r.request.method == "POST":
            body = r.request.post_data_json
            records.append((p, body))
            assert r.request.headers.get("x-csrf-token") == "token"
            from looking_glass.services.uvtt_export import validate_segments
            validate_segments(body["walls"])
            if p.endswith("/export"):
                r.fulfill(content_type="application/json", body=json.dumps(body))
            else:
                data["walls"] = body["walls"]
                data["walls_version"] += 1
                r.fulfill(json=dict(data, source_id=99))
        elif p == "/maps/1/walls":
            r.fulfill(content_type="text/html", body=html)
        elif p.startswith("/static/"):
            f = ROOT/p.lstrip("/")
            r.fulfill(content_type="application/javascript" if f.suffix==".js" else "text/css", body=f.read_text())
        elif p == "/api/maps/1/wall-editor":
            r.fulfill(json=data)
        elif p == "/api/maps/1/image":
            r.fulfill(content_type="image/png", body=artwork)
        else:
            r.fulfill(status=404, body="Not found")
    page.route("**/*", route)
    page.goto("http://looking-glass.test/maps/1/walls")
    pw.expect(page.locator("#wall-overlay path")).to_have_count(2)
    pw.expect(page.locator("#wall-tool")).to_be_enabled()
    yield page, records, errors, data
    assert not errors
    page.close()


def tap(page, x=100.125, y=100):
    point = page.locator("#wall-overlay").evaluate("(el, [x,y]) => {const p=new DOMPoint(x,y).matrixTransform(el.getScreenCTM());return [p.x,p.y];}", [x,y])
    page.mouse.click(*point)


def open_edit(page, x=100.125):
    page.select_option("#wall-tool", "edit")
    tap(page, x)
    pw.expect(page.locator("#wall-edit-dialog")).to_be_visible()


def path(page, kind="wall"):
    return page.locator("#wall-overlay .w-"+kind).get_attribute("d")


def set_coords(page, coords):
    for name, value in zip(("x1", "y1", "x2", "y2"), coords):
        page.locator("#wall-edit-"+name).fill(str(value))


def test_prefill_precision_and_draft_only_undo_redo(editor):
    page, records, _, _ = editor
    original = path(page)
    open_edit(page)
    for name, value in zip(("x1","y1","x2","y2"), (100.125,30.25,100.125,170.75)):
        assert float(page.locator("#wall-edit-"+name).input_value()) == value
    pw.expect(page.locator("#wall-edit-kind")).to_have_value("wall")
    pw.expect(page.locator("#wall-edit-x1")).to_be_focused()
    set_coords(page, [110.125,35.5,115.75,180.25])
    page.select_option("#wall-edit-kind", "secret")
    page.click("#wall-edit-apply")
    pw.expect(page.locator("#wall-edit-dialog")).to_be_hidden()
    assert path(page,"secret") == "M110.125 35.5L115.75 180.25"
    assert not records
    pw.expect(page.locator("#wall-count")).to_contain_text("unsaved")
    page.click("#wall-undo")
    assert path(page) == original
    assert page.locator("#wall-overlay .w-secret").count() == 0
    pw.expect(page.locator("#wall-undo")).to_be_disabled()
    page.click("#wall-redo")
    assert path(page,"secret") == "M110.125 35.5L115.75 180.25"


@pytest.mark.parametrize("close", ["cancel", "escape", "unchanged"])
def test_cancel_escape_and_noop_do_not_dirty_or_add_history(editor, close):
    page, records, _, _ = editor
    before = path(page)
    open_edit(page)
    if close != "unchanged":
        set_coords(page,[120,40,130,160])
    if close == "escape":
        page.locator("#wall-edit-x1").press("Escape")
    else:
        page.click("#wall-edit-apply" if close == "unchanged" else "#wall-edit-cancel")
    pw.expect(page.locator("#wall-edit-dialog")).to_be_hidden()
    assert path(page) == before and not records
    pw.expect(page.locator("#wall-undo")).to_be_disabled()
    pw.expect(page.locator("#wall-count")).to_contain_text("saved")
    pw.expect(page.locator("#wall-viewport")).to_be_focused()


@pytest.mark.parametrize("coords", [["",30,100,170], [10000001,30,100,170], [-10000001,30,100,170], [50,60,50,60]])
def test_invalid_coordinates_keep_dialog_and_draft_unchanged(editor, coords):
    page, records, _, _ = editor
    before = path(page)
    open_edit(page)
    set_coords(page,coords)
    page.click("#wall-edit-apply")
    pw.expect(page.locator("#wall-edit-dialog")).to_be_visible()
    pw.expect(page.locator("#wall-edit-error")).to_be_visible()
    assert path(page)==before and not records
    pw.expect(page.locator("#wall-undo")).to_be_disabled()


@pytest.mark.parametrize("kind", ["wall", "door", "secret", "window", "invisible", "ethereal"])
def test_all_types_and_coordinate_only_blocking_preservation_saved(editor, kind):
    page, records, _, _ = editor
    open_edit(page)
    set_coords(page,[-10.5,0,400.25,200.75])
    page.select_option("#wall-edit-kind",kind)
    page.click("#wall-edit-apply")
    assert not records
    page.click("#wall-save")
    page.wait_for_function("document.getElementById('wall-status').textContent.startsWith('Saved')")
    _, body = records[-1]
    assert body["walls"][0] == [-10.5,0,400.25,200.75,kind,kind not in ("wall","ethereal")]
    assert body["walls"][1] == [200,30,200,170,"door",True]
    assert body["walls_version"]==1 and body["cache_token"]=="token"
    pw.expect(page.locator("#wall-undo")).to_be_disabled()


def test_enter_applies_and_download_includes_unsaved_edit(editor):
    page, records, _, _ = editor
    open_edit(page)
    set_coords(page,[90,25,95,175])
    page.locator("#wall-edit-y2").press("Enter")
    pw.expect(page.locator("#wall-edit-dialog")).to_be_hidden()
    assert not records
    with page.expect_download() as download:
        page.click("#wall-download")
    assert download.value.suggested_filename == "map-1-walls.uvtt"
    assert records[-1][0].endswith("/export")
    assert records[-1][1]["walls"][0] == [90,25,95,175,"wall",False]
    pw.expect(page.locator("#wall-count")).to_contain_text("unsaved")


def test_modal_traps_focus_and_blocks_viewport_shortcuts(editor):
    page, records, _, _ = editor
    open_edit(page)
    original = path(page)
    page.locator("#wall-edit-cancel").focus()
    page.keyboard.press("Tab")
    pw.expect(page.locator("#wall-edit-x1")).to_be_focused()
    page.locator("#wall-edit-apply").focus()
    page.keyboard.press("Control+z")
    assert path(page) == original and not records
    pw.expect(page.locator("#wall-edit-dialog")).to_be_visible()
    page.locator("#wall-edit-cancel").focus()
    page.keyboard.press("Space")
    pw.expect(page.locator("#wall-edit-dialog")).to_be_hidden()


def test_near_miss_and_drag_do_not_open_modal(editor):
    page, records, _, _ = editor
    page.select_option("#wall-tool","edit")
    tap(page,150)
    pw.expect(page.locator("#wall-edit-dialog")).to_be_hidden()
    point = page.locator("#wall-overlay").evaluate("el => {const p=new DOMPoint(100.125,100).matrixTransform(el.getScreenCTM());return [p.x,p.y];}")
    page.mouse.move(*point);page.mouse.down();page.mouse.move(point[0]+40,point[1]+20,steps=8);page.mouse.up()
    pw.expect(page.locator("#wall-edit-dialog")).to_be_hidden()
    assert not records


def test_width_consistency_survives_edit_and_zoom(editor):
    page, _, _, _ = editor
    page.locator("#wall-width").evaluate("el => {el.value='2';el.dispatchEvent(new Event('input'));}")
    open_edit(page)
    set_coords(page,[110,30,110,170])
    page.click("#wall-edit-apply")
    def screen_width():
        return page.locator("#wall-overlay .w-wall").evaluate("el => parseFloat(getComputedStyle(el).strokeWidth)*el.getScreenCTM().a")
    assert screen_width()==pytest.approx(2,abs=.001)
    page.click("#wall-zoom-in")
    assert screen_width()==pytest.approx(2,abs=.001)


def test_existing_add_remove_and_type_tools_remain_usable(editor):
    page, records, _, _ = editor
    before = path(page)
    page.select_option("#wall-tool", "type")
    page.select_option("#wall-kind", "invisible")
    tap(page)
    assert page.locator("#wall-overlay .w-invisible").count() == 1
    page.click("#wall-undo")
    assert path(page) == before
    page.select_option("#wall-tool", "remove")
    tap(page)
    assert page.locator("#wall-overlay path").count() == 1
    page.click("#wall-undo")
    assert path(page) == before
    page.select_option("#wall-tool", "add")
    page.select_option("#wall-kind", "window")
    tap(page,250,50);tap(page,300,150)
    assert path(page,"window") == "M250 50L300 150"
    pw.expect(page.locator("#wall-edit-dialog")).to_be_hidden()
    assert not records


def test_edit_after_zoom_targets_correct_wall(editor):
    page, records, _, _ = editor
    page.click("#wall-zoom-in")
    open_edit(page,200)
    pw.expect(page.locator("#wall-edit-title")).to_have_text("Edit wall 2")
    pw.expect(page.locator("#wall-edit-kind")).to_have_value("door")
    set_coords(page,[205,35,205,165])
    page.click("#wall-edit-apply")
    assert path(page,"door") == "M205 35L205 165"
    assert not records
