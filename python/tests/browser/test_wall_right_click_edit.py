"""Stationary right-click opens wall Edit; drags and primary tools stay unchanged."""
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
    data = dict(ok=True,id=1,name="M",campaign_id=4,cache_token="token",image_version="image1",
                width=400,height=200,walls_version=1,
                walls=[[100.125,30.25,100.125,170.75,"wall",False],[200,30,200,170,"door",True]])
    templates = {"base.html": '<!doctype html><meta name="csrf-token" content="token"><link rel="stylesheet" href="/static/css/common.css"><body class="editor-page"><main class="editor">{% block content %}{% endblock %}</main>{% block styles %}{% endblock %}{% block scripts %}{% endblock %}</body>',
                 "editor.html":(ROOT/"web_html/admin/wall_editor.html").read_text()}
    html = Environment(loader=DictLoader(templates)).get_template("editor.html").render(map=data,campaign=dict(id=4,name="C"))
    image = io.BytesIO();Image.new("RGB",(400,200),(200,30,30)).save(image,"PNG")
    errors, writes = [], []
    page.on("pageerror",lambda error:errors.append(str(error)))
    page.on("dialog",lambda dialog:dialog.dismiss())
    def route(r):
        path = urlparse(r.request.url).path
        if r.request.method=="POST":
            writes.append((path,r.request.post_data_json));r.fulfill(json=data)
        elif path=="/maps/1/walls":r.fulfill(content_type="text/html",body=html)
        elif path.startswith("/static/"):
            f=ROOT/path.lstrip("/")
            r.fulfill(content_type="application/javascript" if f.suffix==".js" else "text/css",body=f.read_text())
        elif path=="/api/maps/1/wall-editor":r.fulfill(json=data)
        elif path=="/api/maps/1/image":r.fulfill(content_type="image/png",body=image.getvalue())
        else:r.fulfill(status=404,body="Not found")
    page.route("**/*",route)
    page.goto("http://looking-glass.test/maps/1/walls")
    pw.expect(page.locator("#wall-overlay path")).to_have_count(2)
    pw.expect(page.locator("#wall-tool")).to_be_enabled()
    page.evaluate("window.contextSuppressed=[];document.getElementById('wall-viewport').addEventListener('contextmenu',e=>window.contextSuppressed.push(e.defaultPrevented));")
    yield page,writes,errors
    assert not errors
    page.close()


def point(page,x=100.125,y=100):
    return page.locator("#wall-overlay").evaluate("(el,[x,y])=>{const p=new DOMPoint(x,y).matrixTransform(el.getScreenCTM());return [p.x,p.y];}",[x,y])


def tap(page,x=100.125,y=100,button="left"):
    page.mouse.click(*point(page,x,y),button=button)


def paths(page):
    return page.locator("#wall-overlay").inner_html()


@pytest.mark.parametrize("tool",["add","remove","type","edit"])
def test_right_click_opens_modal_from_any_tool_without_primary_action(editor,tool):
    page,writes,_=editor
    page.select_option("#wall-tool",tool)
    page.select_option("#wall-kind","invisible")
    before=paths(page)
    tap(page,150,button="right")
    pw.expect(page.locator("#wall-edit-dialog")).to_be_hidden()
    assert paths(page)==before
    tap(page,button="right")
    pw.expect(page.locator("#wall-edit-dialog")).to_be_visible()
    pw.expect(page.locator("#wall-edit-kind")).to_have_value("wall")
    assert float(page.locator("#wall-edit-x1").input_value())==100.125
    pw.expect(page.locator("#wall-tool")).to_have_value(tool)
    pw.expect(page.locator("#wall-kind")).to_have_value("invisible")
    assert paths(page)==before and not writes
    context_events = page.evaluate("window.contextSuppressed")
    assert context_events and all(context_events)
    page.click("#wall-edit-cancel")
    pw.expect(page.locator("#wall-undo")).to_be_disabled()


@pytest.mark.parametrize("tool",["add","remove","type","edit"])
def test_right_drag_pans_without_opening_or_mutating(editor,tool):
    page,writes,_=editor
    page.select_option("#wall-tool",tool)
    before=paths(page)
    transform=page.locator("#wall-stage").get_attribute("style")
    x,y=point(page)
    page.mouse.move(x,y);page.mouse.down(button="right")
    page.mouse.move(x+60,y+30,steps=10);page.mouse.up(button="right")
    pw.expect(page.locator("#wall-edit-dialog")).to_be_hidden()
    assert page.locator("#wall-stage").get_attribute("style")!=transform
    assert paths(page)==before and not writes
    pw.expect(page.locator("#wall-undo")).to_be_disabled()


def test_right_click_apply_undo_redo_uses_existing_draft_workflow(editor):
    page,writes,_=editor
    before=paths(page)
    tap(page,button="right")
    for name,value in zip(("x1","y1","x2","y2"),(110.5,35.25,115.75,175.5)):
        page.locator("#wall-edit-"+name).fill(str(value))
    page.select_option("#wall-edit-kind","secret")
    page.click("#wall-edit-apply")
    assert page.locator("#wall-overlay .w-secret").get_attribute("d")=="M110.5 35.25L115.75 175.5"
    pw.expect(page.locator("#wall-count")).to_contain_text("unsaved")
    page.click("#wall-undo");assert paths(page)==before
    page.click("#wall-redo")
    assert page.locator("#wall-overlay .w-secret").count()==1
    assert not writes


def test_right_click_cancels_pending_start_only_when_wall_hit(editor):
    page,writes,_=editor
    tap(page,250,50)
    pw.expect(page.locator("#wall-overlay circle")).to_have_count(1)
    tap(page,150,button="right")
    pw.expect(page.locator("#wall-overlay circle")).to_have_count(1)
    pw.expect(page.locator("#wall-edit-dialog")).to_be_hidden()
    tap(page,button="right")
    pw.expect(page.locator("#wall-edit-dialog")).to_be_visible()
    pw.expect(page.locator("#wall-overlay circle")).to_have_count(0)
    page.click("#wall-edit-cancel")
    tap(page,300,150)
    pw.expect(page.locator("#wall-overlay circle")).to_have_count(1)
    assert not writes


def test_hit_tolerance_is_screen_pixels_after_zoom(editor):
    page,writes,_=editor
    page.click("#wall-zoom-in")
    x,y=point(page,200)
    page.mouse.click(x+11,y,button="right")
    pw.expect(page.locator("#wall-edit-dialog")).to_be_hidden()
    page.mouse.click(x+9,y,button="right")
    pw.expect(page.locator("#wall-edit-dialog")).to_be_visible()
    pw.expect(page.locator("#wall-edit-kind")).to_have_value("door")
    assert not writes


def test_small_pointer_jitter_opens_dialog_but_cancelled_pointer_does_not(editor):
    page,writes,_=editor
    x,y=point(page)
    page.mouse.move(x,y);page.mouse.down(button="right")
    page.mouse.move(x+2,y+1);page.mouse.up(button="right")
    pw.expect(page.locator("#wall-edit-dialog")).to_be_visible()
    page.locator("#wall-edit-x1").press("Escape")
    pw.expect(page.locator("#wall-edit-dialog")).to_be_hidden()
    page.mouse.move(x,y);page.mouse.down(button="right")
    page.locator("#wall-viewport").dispatch_event("pointercancel",dict(pointerId=1,pointerType="mouse",button=2))
    page.mouse.up(button="right")
    pw.expect(page.locator("#wall-edit-dialog")).to_be_hidden()
    assert not writes


@pytest.mark.parametrize("tool",["add","remove","type","edit"])
def test_primary_click_keeps_selected_tool_behavior(editor,tool):
    page,writes,_=editor
    page.select_option("#wall-tool",tool)
    page.select_option("#wall-kind","window")
    tap(page)
    if tool=="edit":pw.expect(page.locator("#wall-edit-dialog")).to_be_visible()
    else:
        pw.expect(page.locator("#wall-edit-dialog")).to_be_hidden()
        if tool=="add":pw.expect(page.locator("#wall-overlay circle")).to_have_count(1)
        elif tool=="remove":pw.expect(page.locator("#wall-overlay path")).to_have_count(1)
        else:pw.expect(page.locator("#wall-overlay .w-window")).to_have_count(1)
    assert not writes
