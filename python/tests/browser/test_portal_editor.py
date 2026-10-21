"""Single-section portal editing with real scripts and mocked HTTP responses."""
import io,json
from pathlib import Path
from urllib.parse import urlparse
import pytest
from jinja2 import Environment,DictLoader
from PIL import Image
pw=pytest.importorskip("playwright.sync_api")
ROOT=Path(__file__).resolve().parents[3]

@pytest.fixture(scope="module")
def browser():
    with pw.sync_playwright() as p:
        b=p.chromium.launch(headless=True,args=["--no-sandbox"]);yield b;b.close()

@pytest.fixture
def editor(browser):
    page=browser.new_page(viewport={"width":1400,"height":1000});page.set_default_timeout(4000)
    blank=lambda:{"sides":[{"role":"unconfigured"},{"role":"unconfigured"}]}
    data=dict(ok=True,id=1,name="M",campaign_id=4,cache_token="token",image_version="v1",width=400,height=200,walls_version=1,
              walls=[[10,10,390,10,"wall",True],[100,30,100,170,"portal",True,blank()],[300,30,300,170,"portal",True,blank()]])
    templates={"base.html":'<!doctype html><meta charset="utf-8"><meta name="csrf-token" content="token"><link rel="stylesheet" href="/static/css/common.css"><body class="editor-page"><main class="editor">{% block content %}{% endblock %}</main>{% block styles %}{% endblock %}{% block scripts %}{% endblock %}</body>',"editor.html":(ROOT/"web_html/admin/wall_editor.html").read_text()}
    html=Environment(loader=DictLoader(templates)).get_template("editor.html").render(map=data,campaign=dict(id=4,name="C"))
    image=io.BytesIO();Image.new("RGB",(400,200),"white").save(image,"PNG")
    writes,errors=[],[];page.on("pageerror",lambda e:errors.append(str(e)))
    page.on("dialog",lambda d:d.dismiss())
    def route(r):
        path=urlparse(r.request.url).path
        if r.request.method=="POST":
            body=r.request.post_data_json;writes.append((path,body));data["walls"]=body["walls"];data["walls_version"]+=1;r.fulfill(json=dict(data,source_id=99))
        elif path=="/maps/1/walls":r.fulfill(content_type="text/html",body=html)
        elif path.startswith("/static/"):
            f=ROOT/path.lstrip("/");content=f.read_text()
            if f.name=="pan_zoom.js":content+="\nwindow.PanZoom=class extends window.PanZoom { constructor(...a){super(...a);window.testPZ=this;} };"
            r.fulfill(content_type="application/javascript" if f.suffix==".js" else "text/css",body=content)
        elif path=="/api/maps/1/wall-editor":r.fulfill(json=data)
        elif path=="/api/maps/1/image":r.fulfill(content_type="image/png",body=image.getvalue())
        else:r.fulfill(status=404)
    page.route("**/*",route);page.goto("http://looking-glass.test/maps/1/walls")
    pw.expect(page.locator("#wall-tool")).to_be_enabled()
    yield page,writes,data
    assert not errors;page.close()

def open_popup(page):page.locator("#portal-configure").click();pw.expect(page.locator("#portal-dialog")).to_be_visible()
def apply_only(page):
    page.locator("#portal-apply").click()
    pw.expect(page.locator("#portal-dialog")).to_be_visible()

def apply(page):
    """Apply and explicitly close for workflows that next use the main editor."""
    apply_only(page)
    page.locator("#portal-close").click()
    pw.expect(page.locator("#portal-dialog")).not_to_be_visible()
def connect(page):
    page.locator("#portal-side-0-role").select_option("entry")
    page.locator("#portal-side-0-destination").select_option("2")
    page.locator("#portal-side-0-exit").select_option("0")

def test_initial_unconfigured_two_panels_portal_only(editor):
    page,writes,data=editor;open_popup(page)
    assert page.locator("#portal-side-0-role").input_value()==page.locator("#portal-side-1-role").input_value()=="unconfigured"
    assert page.locator("#portal-sides fieldset").count()==2
    assert page.locator("#portal-section option").evaluate_all("els=>els.map(e=>e.value)")==["1","2"]
    page.locator("#portal-side-0-role").select_option("entry")
    assert page.locator("#portal-side-1-role").input_value()=="none"
    assert page.locator("#portal-side-0-destination option").evaluate_all("els=>els.filter(e=>e.value).map(e=>e.value)")==["2"]
    assert not writes

def test_entry_destination_save_and_reload(editor):
    page,writes,data=editor;open_popup(page);connect(page);apply(page)
    page.locator("#wall-save").click();pw.expect(page.locator("#wall-status")).to_contain_text("Saved")
    a,b=data["walls"][1:];assert a[6]["pair"]==b[6]["pair"]
    assert b[6]["sides"]==[{"role":"exit"},{"role":"none"}]
    open_popup(page);assert page.locator("#portal-side-0-destination").input_value()=="2"
    assert page.locator("#portal-side-0-exit").input_value()=="0"
    page.locator("#portal-section").select_option("2")
    assert page.locator("#portal-side-0-role").input_value()=="exit"

def test_partial_apply_blocks_save_and_keeps_edits_on_switch(editor):
    page,writes,data=editor;open_popup(page)
    page.locator("#portal-side-0-role").select_option("exit")
    page.locator("#portal-section").select_option("2");page.locator("#portal-section").select_option("1")
    assert page.locator("#portal-side-0-role").input_value()=="exit"
    apply(page);page.locator("#wall-save").click()
    pw.expect(page.locator("#wall-status")).to_contain_text("not paired");assert not writes
    open_popup(page);page.locator("#portal-section").select_option("2")
    page.locator("#portal-side-0-role").select_option("entry")
    page.locator("#portal-side-0-destination").select_option("1");page.locator("#portal-side-0-exit").select_option("0")
    apply(page);page.locator("#wall-save").click();pw.expect(page.locator("#wall-status")).to_contain_text("Saved")

def test_cancel_escape_and_batch_undo_redo(editor):
    page,writes,data=editor;open_popup(page);connect(page);page.keyboard.press("Escape")
    pw.expect(page.locator("#wall-count")).to_contain_text("saved")
    open_popup(page);assert page.locator("#portal-side-0-role").input_value()=="unconfigured"
    connect(page);apply(page);page.locator("#wall-undo").click()
    open_popup(page);assert page.locator("#portal-side-0-role").input_value()=="unconfigured"
    page.locator("#portal-cancel").click();page.locator("#wall-redo").click()
    page.locator("#wall-save").click();pw.expect(page.locator("#wall-status")).to_contain_text("Saved")

def test_configured_opposite_not_overwritten_and_shared_exit(editor):
    page,writes,data=editor;open_popup(page);connect(page)
    page.locator("#portal-side-1-role").select_option("entry")
    page.locator("#portal-side-1-destination").select_option("2");page.locator("#portal-side-1-exit").select_option("0")
    page.locator("#portal-side-0-kind").select_option("secret")
    assert page.locator("#portal-side-1-role").input_value()=="entry"
    page.locator("#portal-side-0-after").select_option("locked_door");apply(page)
    page.locator("#wall-save").click();pw.expect(page.locator("#wall-status")).to_contain_text("Saved")
    sides=data["walls"][1][6]["sides"];assert sides[0]["exit"]==sides[1]["exit"]==0 and sides[0]["after"]=="locked_door"

def test_unpair_keeps_portal_sections_unconfigured(editor):
    page,writes,data=editor;open_popup(page);connect(page);apply(page)
    open_popup(page);page.locator("#portal-remove").click();apply(page)
    open_popup(page);assert page.locator("#portal-section option").count()==2
    assert page.locator("#portal-side-0-role").input_value()=="unconfigured"
    page.locator("#portal-section").select_option("2");assert page.locator("#portal-side-1-role").input_value()=="unconfigured"
    assert not writes

def test_newly_drawn_portal_has_unconfigured_sides(editor):
    page,writes,data=editor
    page.locator("#wall-kind").select_option("portal")
    points=page.locator("#wall-overlay").evaluate("el=>[[180,40],[180,160]].map(([x,y])=>{const p=new DOMPoint(x,y).matrixTransform(el.getScreenCTM());return [p.x,p.y];})")
    for point in points:page.mouse.click(*point)
    open_popup(page);page.locator("#portal-section").select_option("3")
    assert page.locator("#portal-side-0-role").input_value()==page.locator("#portal-side-1-role").input_value()=="unconfigured"
