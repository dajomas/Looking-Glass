"""Wall endpoint editing and image-edge clamping regressions; mocked API responses."""
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
        browser=playwright.chromium.launch(headless=True,args=["--no-sandbox"])
        yield browser
        browser.close()


@pytest.fixture
def editor(browser):
    page=browser.new_page(viewport={"width":1200,"height":800})
    page.set_default_timeout(5000)
    data=dict(ok=True,id=1,name="M",campaign_id=4,cache_token="token",image_version="v1",width=400,height=200,walls_version=1,
              walls=[[100.125,30.25,100.125,170.75,"wall",False],[-30,20,-30,180,"door",True]])
    templates={"base.html":'<!doctype html><meta name="csrf-token" content="token"><link rel="stylesheet" href="/static/css/common.css"><body class="editor-page"><main class="editor">{% block content %}{% endblock %}</main>{% block styles %}{% endblock %}{% block scripts %}{% endblock %}</body>',
               "editor.html":(ROOT/"web_html/admin/wall_editor.html").read_text()}
    html=Environment(loader=DictLoader(templates)).get_template("editor.html").render(map=data,campaign=dict(id=4,name="C"))
    image=io.BytesIO();Image.new("RGB",(400,200),(200,30,30)).save(image,"PNG")
    errors,writes=[],[]
    page.on("pageerror",lambda error:errors.append(str(error)))
    page.on("dialog",lambda dialog:dialog.dismiss())
    def route(r):
        path=urlparse(r.request.url).path
        if r.request.method=="POST":
            body=r.request.post_data_json;writes.append((path,body))
            assert r.request.headers.get("x-csrf-token")=="token"
            from looking_glass.services.uvtt_export import validate_segments
            validate_segments(body["walls"])
            if path.endswith("/export"):r.fulfill(content_type="application/json",body=json.dumps(body))
            else:
                data["walls"]=body["walls"];data["walls_version"]+=1
                r.fulfill(json=dict(data,source_id=99))
        elif path=="/maps/1/walls":r.fulfill(content_type="text/html",body=html)
        elif path.startswith("/static/"):
            f=ROOT/path.lstrip("/");content=f.read_text()
            if f.name=="pan_zoom.js":content+="\nwindow.PanZoom=class extends window.PanZoom { constructor(...args){super(...args);window.testPZ=this;} };"
            r.fulfill(content_type="application/javascript" if f.suffix==".js" else "text/css",body=content)
        elif path=="/api/maps/1/wall-editor":r.fulfill(json=data)
        elif path=="/api/maps/1/image":r.fulfill(content_type="image/png",body=image.getvalue())
        else:r.fulfill(status=404,body="Not found")
    page.route("**/*",route);page.goto("http://looking-glass.test/maps/1/walls")
    pw.expect(page.locator("#wall-overlay path")).to_have_count(2)
    pw.expect(page.locator("#wall-tool")).to_be_enabled()
    page.evaluate("()=>{const pz=window.testPZ,r=pz.vp.getBoundingClientRect();pz.scale=1;pz.x=(r.width-pz.w)/2;pz.y=(r.height-pz.h)/2;pz.apply();}")
    yield page,writes,data
    assert not errors
    page.close()


def tap(page,x=100.125,y=100,button="left",ctrl=False):
    p=page.locator("#wall-overlay").evaluate("(el,[x,y])=>{const p=new DOMPoint(x,y).matrixTransform(el.getScreenCTM());return [p.x,p.y];}",[x,y])
    if ctrl:page.keyboard.down("Control")
    try:page.mouse.click(*p,button=button)
    finally:
        if ctrl:page.keyboard.up("Control")


def open_edit(page,x=100.125):
    tap(page,x,button="right")
    pw.expect(page.locator("#wall-edit-dialog")).to_be_visible()


def coords(page,values):
    for name,value in zip(("x1","y1","x2","y2"),values):page.locator("#wall-edit-"+name).fill(str(value))


def geometry(page,kind="wall"):
    return page.locator("#wall-overlay .w-"+kind).get_attribute("d")


@pytest.mark.parametrize("outside,edge",[((-20,80),(0,80)),((420,80),(400,80)),((80,-20),(80,0)),((80,220),(80,200)),((-20,-20),(0,0)),((420,220),(400,200)),((-20,220),(0,200)),((420,-20),(400,0))])
def test_outside_add_click_places_dot_and_segment_at_nearest_image_edge(editor,outside,edge):
    page,writes,_=editor
    page.locator("#snap-ends").evaluate("el=>el.checked=false")
    tap(page,*outside)
    circle=page.locator("#wall-overlay circle")
    assert float(circle.get_attribute("cx"))==edge[0]
    assert float(circle.get_attribute("cy"))==edge[1]
    tap(page,200,100)
    assert f"M{edge[0]} {edge[1]}L200 100" in geometry(page)
    pw.expect(page.locator("#wall-count")).to_contain_text("3 segments")
    assert not writes


def test_snapping_to_imported_outside_endpoint_stays_on_image_edge(editor):
    page,writes,_=editor
    tap(page,-20,20)
    circle=page.locator("#wall-overlay circle")
    assert circle.get_attribute("cx")=="0" and circle.get_attribute("cy")=="20"
    assert not writes


@pytest.mark.parametrize("scale",[.5,2])
def test_clamping_uses_image_edges_after_zoom_not_viewport_edges(editor,scale):
    page,_,_=editor
    page.locator("#snap-ends").evaluate("el=>el.checked=false")
    page.evaluate("scale=>{const pz=window.testPZ,r=pz.vp.getBoundingClientRect();pz.scale=scale;pz.x=(r.width-pz.w*scale)/2;pz.y=(r.height-pz.h*scale)/2;pz.apply();}",scale)
    tap(page,410,100)
    assert page.locator("#wall-overlay circle").get_attribute("cx")=="400"


@pytest.mark.parametrize("close",["cancel","escape","apply"])
def test_selecting_outside_imported_wall_clamps_dialog_not_draft_until_apply(editor,close):
    page,writes,_=editor
    before=geometry(page,"door")
    open_edit(page,-30)
    for name,value in zip(("x1","y1","x2","y2"),(0,20,0,180)):
        assert float(page.locator("#wall-edit-"+name).input_value())==value
    pw.expect(page.locator("#wall-edit-clamp-note")).to_be_visible()
    assert geometry(page,"door")==before
    if close=="escape":page.locator("#wall-edit-x1").press("Escape")
    else:page.click("#wall-edit-apply" if close=="apply" else "#wall-edit-cancel")
    if close=="apply":
        assert geometry(page,"door")=="M0 20L0 180"
        page.click("#wall-undo");assert geometry(page,"door")==before
    else:
        assert geometry(page,"door")==before
        pw.expect(page.locator("#wall-undo")).to_be_disabled()
    assert not writes


@pytest.mark.parametrize("kind",["wall","door","secret","window","invisible","ethereal"])
def test_typed_outside_coordinates_clamp_and_save_with_existing_type_rules(editor,kind):
    page,writes,_=editor
    open_edit(page)
    coords(page,[-1000000000000,-20,1000000000000,220])
    page.select_option("#wall-edit-kind",kind)
    page.click("#wall-edit-apply")
    assert not writes
    page.click("#wall-save")
    page.wait_for_function("document.getElementById('wall-status').textContent.startsWith('Saved')")
    assert writes[-1][1]["walls"][0]==[0,0,400,200,kind,kind not in ("wall","ethereal")]
    assert writes[-1][1]["walls"][1]==[-30,20,-30,180,"door",True]


def test_clamped_edit_is_one_undo_redo_operation(editor):
    page,writes,_=editor
    before=geometry(page)
    open_edit(page);coords(page,[-10,35,410,170]);page.click("#wall-edit-apply")
    assert geometry(page)=="M0 35L400 170"
    page.click("#wall-undo");assert geometry(page)==before
    pw.expect(page.locator("#wall-undo")).to_be_disabled()
    page.click("#wall-redo");assert geometry(page)=="M0 35L400 170"
    assert not writes


def test_coincident_endpoints_after_clamping_are_rejected(editor):
    page,writes,_=editor
    before=geometry(page)
    open_edit(page);coords(page,[-10,25,-20,25]);page.click("#wall-edit-apply")
    pw.expect(page.locator("#wall-edit-error")).to_contain_text("must differ")
    pw.expect(page.locator("#wall-edit-dialog")).to_be_visible()
    assert geometry(page)==before and not writes


def test_missing_coordinates_still_rejected_and_focus_stays_in_dialog(editor):
    page,writes,_=editor
    open_edit(page);page.locator("#wall-edit-x1").fill("");page.click("#wall-edit-apply")
    pw.expect(page.locator("#wall-edit-error")).to_be_visible()
    pw.expect(page.locator("#wall-edit-x1")).to_be_focused()
    page.locator("#wall-edit-cancel").focus();page.keyboard.press("Tab")
    pw.expect(page.locator("#wall-edit-x1")).to_be_focused()
    assert not writes


def test_unchanged_in_bounds_values_remain_noop_and_full_precision(editor):
    page,writes,_=editor
    open_edit(page)
    assert page.locator("#wall-edit-x1").input_value()=="100.125"
    page.click("#wall-edit-apply")
    pw.expect(page.locator("#wall-undo")).to_be_disabled()
    assert not writes


def test_ctrl_shortcut_contextmenu_and_download_keep_working(editor):
    page,writes,_=editor
    tap(page,ctrl=True)
    pw.expect(page.locator("#wall-edit-dialog")).to_be_visible()
    assert page.locator("#wall-edit-dialog").evaluate("el=>{const e=new MouseEvent('contextmenu',{bubbles:true,cancelable:true,button:2});el.dispatchEvent(e);return e.defaultPrevented;}")
    coords(page,[-10,35,410,170]);page.locator("#wall-edit-y2").press("Enter")
    with page.expect_download():page.click("#wall-download")
    assert writes[-1][0].endswith("/export")
    assert writes[-1][1]["walls"][0]==[0,35,400,170,"wall",False]


def test_width_stays_screen_relative_after_clamp(editor):
    page,_,_=editor
    open_edit(page);coords(page,[-10,35,410,170]);page.click("#wall-edit-apply")
    page.click("#wall-zoom-in")
    width=page.locator("#wall-overlay .w-wall").evaluate("el=>parseFloat(getComputedStyle(el).strokeWidth)*el.getScreenCTM().a")
    assert width==pytest.approx(2,abs=.001)
