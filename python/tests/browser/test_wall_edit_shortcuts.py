from browser_support import template_environment, fulfill_auxiliary
"""Regression tests for Ctrl-click editing and context menus arriving after modal open."""
import io
from pathlib import Path
from urllib.parse import urlparse

import pytest
from PIL import Image
from jinja2 import DictLoader, Environment

pw = pytest.importorskip("playwright.sync_api")
ROOT = Path(__file__).resolve().parents[3]




@pytest.fixture
def editor(browser):
    page = browser.new_page(viewport={"width":1200,"height":800})
    data = dict(ok=True,id=1,name="M",campaign_id=4,cache_token="token",image_version="v1",width=400,height=200,walls_version=1,
                walls=[[100.125,30.25,100.125,170.75,"wall",False],[200,30,200,170,"door",True]])
    templates = {"base.html": '<!doctype html><meta name="csrf-token" content="token"><link rel="stylesheet" href="/static/css/common.css"><body class="editor-page"><a id="outside-map" href="#">Outside editor</a><main class="editor">{% block content %}{% endblock %}</main>{% block styles %}{% endblock %}{% block scripts %}{% endblock %}</body>',
                 "editor.html":(ROOT/"web_html/admin/wall_editor.html").read_text()}
    html=template_environment(templates).get_template("editor.html").render(map=data,campaign=dict(id=4,name="C"))
    output=io.BytesIO();Image.new("RGB",(400,200),(200,30,30)).save(output,"PNG")
    errors,writes=[],[]
    page.on("pageerror",lambda error:errors.append(str(error)))
    page.on("dialog",lambda dialog:dialog.dismiss())
    def route(r):
        path=urlparse(r.request.url).path
        if r.request.method=="POST":writes.append((path,r.request.post_data_json));r.fulfill(json=data)
        elif path=="/maps/1/walls":r.fulfill(content_type="text/html",body=html)
        elif path.startswith("/static/"):
            f=ROOT/path.lstrip("/")
            r.fulfill(content_type="application/javascript" if f.suffix==".js" else "text/css",body=f.read_text())
        elif path=="/api/maps/1/wall-editor":r.fulfill(json=data)
        elif path=="/api/maps/1/image":r.fulfill(content_type="image/png",body=output.getvalue())
        else:r.fulfill(status=404,body="Not found")
    page.route("**/*",route)
    page.goto("http://looking-glass.test/maps/1/walls")
    pw.expect(page.locator("#wall-overlay path")).to_have_count(2)
    pw.expect(page.locator("#wall-tool")).to_be_enabled()
    page.evaluate("window.contextEvents=[];document.addEventListener('contextmenu',e=>window.contextEvents.push({id:e.target.id,prevented:e.defaultPrevented}));")
    yield page,writes
    assert not errors
    page.close()


def point(page,x=100.125,y=100):
    return page.locator("#wall-overlay").evaluate("(el,[x,y])=>{const p=new DOMPoint(x,y).matrixTransform(el.getScreenCTM());return [p.x,p.y];}",[x,y])


def ctrl_click(page,x=100.125):
    page.keyboard.down("Control")
    try:page.mouse.click(*point(page,x))
    finally:page.keyboard.up("Control")


@pytest.mark.parametrize("tool",["add","remove","type","edit"])
def test_ctrl_left_click_opens_existing_dialog_without_primary_action(editor,tool):
    page,writes=editor
    page.select_option("#wall-tool",tool)
    page.select_option("#wall-kind","invisible")
    before=page.locator("#wall-overlay").inner_html()
    ctrl_click(page)
    pw.expect(page.locator("#wall-edit-dialog")).to_be_visible()
    pw.expect(page.locator("#wall-edit-kind")).to_have_value("wall")
    pw.expect(page.locator("#wall-tool")).to_have_value(tool)
    assert float(page.locator("#wall-edit-x1").input_value())==100.125
    assert page.locator("#wall-overlay").inner_html()==before and not writes
    page.click("#wall-edit-cancel")
    pw.expect(page.locator("#wall-undo")).to_be_disabled()


def test_contextmenu_is_cancelled_in_viewport_and_modal_even_after_open(editor):
    page,writes=editor
    page.mouse.click(*point(page),button="right")
    pw.expect(page.locator("#wall-edit-dialog")).to_be_visible()
    events=page.evaluate("window.contextEvents")
    assert events and all(event["prevented"] for event in events)
    for selector in ("#wall-viewport","#wall-edit-dialog","#wall-edit-x1","#wall-edit-kind"):
        # Exercise delayed/re-targeted contextmenu events independently of pointerup.
        assert page.locator(selector).evaluate("el=>{const e=new MouseEvent('contextmenu',{bubbles:true,cancelable:true,button:2});el.dispatchEvent(e);return e.defaultPrevented;}")
    page.locator("#wall-edit-title").click(button="right")
    assert all(event["prevented"] for event in page.evaluate("window.contextEvents"))
    assert not writes


def test_contextmenu_remains_available_outside_map_and_popup(editor):
    page,_=editor
    assert not page.locator("#outside-map").evaluate("el=>{const e=new MouseEvent('contextmenu',{bubbles:true,cancelable:true,button:2});el.dispatchEvent(e);return e.defaultPrevented;}")


@pytest.mark.parametrize("gesture",["right","ctrl-left"])
def test_drag_pans_and_does_not_open_or_edit(editor,gesture):
    page,writes=editor
    before=page.locator("#wall-overlay").inner_html()
    transform=page.locator("#wall-stage").get_attribute("style")
    x,y=point(page)
    if gesture=="ctrl-left":page.keyboard.down("Control")
    button="right" if gesture=="right" else "left"
    page.mouse.move(x,y);page.mouse.down(button=button)
    page.mouse.move(x+60,y+25,steps=8);page.mouse.up(button=button)
    if gesture=="ctrl-left":page.keyboard.up("Control")
    pw.expect(page.locator("#wall-edit-dialog")).to_be_hidden()
    assert page.locator("#wall-stage").get_attribute("style")!=transform
    assert page.locator("#wall-overlay").inner_html()==before and not writes


def test_ctrl_click_miss_and_pending_start_behavior(editor):
    page,writes=editor
    page.mouse.click(*point(page,250,50))
    pw.expect(page.locator("#wall-overlay circle")).to_have_count(1)
    ctrl_click(page,150)
    pw.expect(page.locator("#wall-edit-dialog")).to_be_hidden()
    pw.expect(page.locator("#wall-overlay circle")).to_have_count(1)
    ctrl_click(page)
    pw.expect(page.locator("#wall-edit-dialog")).to_be_visible()
    pw.expect(page.locator("#wall-overlay circle")).to_have_count(0)
    page.locator("#wall-edit-x1").press("Escape")
    assert not writes


def test_ctrl_click_apply_still_one_undoable_draft_change(editor):
    page,writes=editor
    before=page.locator("#wall-overlay").inner_html()
    page.click("#wall-zoom-in")
    ctrl_click(page)
    page.locator("#wall-edit-x1").fill("110.5")
    page.select_option("#wall-edit-kind","secret")
    page.click("#wall-edit-apply")
    assert page.locator("#wall-overlay .w-secret").count()==1
    assert not writes
    page.click("#wall-undo")
    assert page.locator("#wall-overlay .w-wall").get_attribute("d")=="M100.125 30.25L100.125 170.75"
    pw.expect(page.locator("#wall-undo")).to_be_disabled()
    page.click("#wall-redo")
    assert page.locator("#wall-overlay .w-secret").count()==1


@pytest.mark.parametrize("tool",["add","remove","type","edit"])
def test_unmodified_left_click_preserves_primary_tools(editor,tool):
    page,writes=editor
    page.select_option("#wall-tool",tool);page.select_option("#wall-kind","window")
    page.mouse.click(*point(page))
    if tool=="edit":pw.expect(page.locator("#wall-edit-dialog")).to_be_visible()
    else:
        pw.expect(page.locator("#wall-edit-dialog")).to_be_hidden()
        if tool=="add":pw.expect(page.locator("#wall-overlay circle")).to_have_count(1)
        elif tool=="remove":pw.expect(page.locator("#wall-overlay path")).to_have_count(1)
        else:pw.expect(page.locator("#wall-overlay .w-window")).to_have_count(1)
    assert not writes
