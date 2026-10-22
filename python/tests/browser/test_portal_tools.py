"""Movable dialogs, authored overview and admin-only rotating presentation."""
import io
from pathlib import Path
from urllib.parse import urlparse
import pytest
from PIL import Image,ImageDraw
from jinja2 import Environment,DictLoader
from test_portal_editor import editor,browser,open_popup,apply,connect
from playwright.sync_api import expect
ROOT=Path(__file__).resolve().parents[3]


def test_move_portal_editor_with_drag_keyboard_and_center(editor):
    page,writes,data=editor;open_popup(page)
    handle=page.locator("#portal-dialog-move");dialog=page.locator("#portal-dialog")
    before=dialog.bounding_box();r=handle.bounding_box()
    page.mouse.move(r["x"]+20,r["y"]+r["height"]/2);page.mouse.down();page.mouse.move(r["x"]+100,r["y"]+r["height"]/2,steps=5);page.mouse.up()
    after=dialog.bounding_box();assert after["x"]>before["x"]+40
    handle.focus();page.keyboard.press("ArrowLeft");assert abs(dialog.bounding_box()["x"]-(after["x"]-10))<2
    page.locator("#portal-dialog-center").click();assert abs(dialog.bounding_box()["x"]-before["x"])<2
    assert not writes


def test_title_bar_stays_reachable_on_resize(editor):
    page,writes,data=editor;open_popup(page)
    page.set_viewport_size({"width":700,"height":550})
    r=page.locator("#portal-dialog-move").bounding_box();assert 0<=r["x"]<700 and 0<=r["y"]<550
    assert not writes


def test_overview_button_lists_unconfigured_and_counterparts(editor):
    page,writes,data=editor
    page.locator("#portal-overview").click();expect(page.locator("#portal-overview-dialog")).to_be_visible()
    expect(page.locator("#portal-overview-body tr")).to_have_count(4)
    assert "Unconfigured" in page.locator("#portal-overview-body").text_content()
    assert "authored initial states" in page.locator("#portal-overview-caption").text_content()
    page.locator("#portal-overview-close").click();open_popup(page);connect(page)
    page.locator("#portal-side-0-kind").select_option("secret");page.locator("#portal-side-0-after").select_option("locked_door")
    page.locator("#portal-popup-overview").click()
    assert "Pending popup edits" in page.locator("#portal-overview-caption").text_content()
    text=page.locator("#portal-overview-body").text_content();assert "Section 3 E" in text and "Section 2 E" in text and "Locked" in text and "Secret" in text
    page.keyboard.press("Escape");expect(page.locator("#portal-dialog")).to_be_visible()
    assert page.locator("#portal-side-0-kind").input_value()=="secret"
    page.locator("#portal-close").click();page.locator("#portal-overview").click()
    assert "Section 3 E" not in page.locator("#portal-overview-body").text_content();assert not writes


def test_overview_does_not_undo_draft_or_submit(editor):
    page,writes,data=editor;open_popup(page);connect(page);apply(page)
    page.locator("#portal-overview").click();page.keyboard.press("Control+z")
    page.locator("#portal-overview-close").click();page.locator("#wall-save").click()
    expect(page.locator("#wall-status")).to_contain_text("Saved");assert len(writes)==1
    assert data["walls"][1][6]["pair"]==data["walls"][2][6]["pair"]


def _png(kind="image",routes=()):
    image=Image.new("RGBA",(400,200),(255,255,255,255) if kind!="arrows" else (0,0,0,0))
    if kind=="arrows":
        draw=ImageDraw.Draw(image)
        for route in routes:
            for endpoint in (route["entry"],route["exit"]):draw.polygon([tuple(p) for p in endpoint["polygon"]],fill=(192,192,192,255))
    out=io.BytesIO();image.save(out,"PNG");return out.getvalue()


@pytest.fixture
def admin(browser):
    page=browser.new_page(viewport={"width":1400,"height":900});page.set_default_timeout(5000)
    def point(x,y,section,side,compass):return dict(wall_id=section,section=section,side=side,compass=compass,polygon=[[x,y],[x+16,y],[x+8,y+16]])
    routes=[dict(id="r1",entry=point(60,50,1,0,"E"),exit=point(260,50,2,1,"W"),state="locked_door"),dict(id="r2",entry=point(60,130,3,0,"E"),exit=point(260,130,4,1,"W"),state="secret")]
    data=dict(ok=True,id=1,name="M",campaign_id=4,cache_token="token",image_version="v1",width=400,height=200,work_width=400,work_height=200,work_scale=1,walls_version=1,fog_version=1,walls_source="",walls=[],op_count=0,is_active=True,live_viewers=0,disabled_wall_types=[],door_arrows_enabled=True,viewer_door_arrows_enabled=True,door_arrow_color="#46c0ff",locked_door_arrow_color="#ff9f43",door_arrows=[],managed_doors=[],portal_routes=routes,calibration=dict(offset_x=0,offset_y=0,scale_x=1,scale_y=1,doors_block=True))
    base='<!doctype html><html><head><meta charset="utf-8"><meta name="csrf-token" content="token"><link rel="stylesheet" href="/static/css/common.css">{% block styles %}{% endblock %}</head><body class="editor-page"><main class="editor">{% block content %}{% endblock %}</main>{% block scripts %}{% endblock %}</body></html>'
    templates={"base.html":base,"editor.html":(ROOT/"web_html/admin/map_editor.html").read_text(),"partials/_csrf.html":'<input type="hidden" name="csrf_token" value="token">',"partials/_map_display_dialog.html":(ROOT/"templates/partials/_map_display_dialog.html").read_text(),"partials/_map_transitions.html":(ROOT/"templates/partials/_map_transitions.html").read_text()}
    html=Environment(loader=DictLoader(templates)).get_template("editor.html").render(map=dict(data,wall_count=0),campaign=dict(id=4,name="C"),siblings=[dict(id=1,name="M")],fog_opacity=.55,op_count=0)
    errors,posts=[],[];page.on("pageerror",lambda e:errors.append(str(e)))
    def route(r):
        path=urlparse(r.request.url).path
        if r.request.method=="POST":posts.append((path,r.request.post_data_json));r.fulfill(json=data)
        elif path=="/maps/1":r.fulfill(content_type="text/html",body=html)
        elif path.startswith("/static/"):
            f=ROOT/path.lstrip("/");content=f.read_text()
            if f.name=="pan_zoom.js":content+="\nwindow.PanZoom=class extends window.PanZoom{constructor(...a){super(...a);window.testPZ=this;}};"
            r.fulfill(content_type="application/javascript" if f.suffix==".js" else "text/css",body=content)
        elif path=="/api/maps/1":r.fulfill(json=data)
        elif path=="/api/maps/1/image":r.fulfill(content_type="image/png",body=_png())
        elif path=="/api/maps/1/fog.png":r.fulfill(content_type="image/png",body=_png("fog"))
        elif path=="/api/maps/1/door-arrows.png":r.fulfill(content_type="image/png",body=_png("arrows",routes))
        elif path=="/api/campaigns/4/transitions":r.fulfill(json=dict(ok=True,active_map_id=1,endpoints=[],maps=[dict(id=1,name="M",viewer_transition_markers=1,viewer_transition_labels=1)]))
        elif path=="/api/campaigns/4/wall-sources":r.fulfill(json=dict(sources=[]))
        else:r.fulfill(status=404)
    page.route("**/*",route);page.goto("http://looking-glass.test/maps/1")
    page.wait_for_function("document.getElementById('portal-cycle-overlay').dataset.routeId")
    yield page,posts,data
    assert not errors;page.close()


def test_admin_default_rotation_slider_pause_and_no_writes(admin):
    page,posts,data=admin;overlay=page.locator("#portal-cycle-overlay")
    page.locator("#fog-panel > summary").click()
    assert page.locator("#portal-cycle-seconds").input_value()=="5"
    expect(overlay.locator("polygon")).to_have_count(2)
    original=overlay.get_attribute("data-route-id")
    page.locator("#portal-cycle-seconds").evaluate("e=>{e.value=1;e.dispatchEvent(new Event('input',{bubbles:true}));}")
    page.wait_for_function("old=>document.getElementById('portal-cycle-overlay').dataset.routeId!==old",arg=original)
    page.locator("#portal-cycle-enabled").uncheck();expect(overlay.locator("polygon")).to_have_count(0)
    assert "paused" in page.locator("#portal-cycle-status").text_content()
    assert overlay.evaluate("e=>getComputedStyle(e).pointerEvents")=="none"
    assert page.locator("#door-arrows").evaluate("e=>e.naturalWidth")==400
    assert not posts


def test_admin_viewport_visibility_and_reduced_motion(admin):
    page,posts,data=admin;page.emulate_media(reduced_motion="reduce")
    expect(page.locator("#portal-cycle-overlay polygon")).to_have_count(2)
    assert page.locator("#portal-cycle-overlay polygon").first.evaluate("e=>getComputedStyle(e).animationName")=="none"
    page.evaluate("()=>{window.testPZ.x=10000;window.testPZ.apply();}")
    expect(page.locator("#portal-cycle-overlay polygon")).to_have_count(0)
    page.evaluate("()=>window.testPZ.fit()")
    expect(page.locator("#portal-cycle-overlay polygon")).to_have_count(2)
    assert not posts


def test_admin_hidden_tab_and_disabled_admin_arrows_clear_overlay(admin):
    page,posts,data=admin
    page.evaluate("()=>{Object.defineProperty(document,'hidden',{configurable:true,value:true});document.dispatchEvent(new Event('visibilitychange'));}")
    expect(page.locator("#portal-cycle-overlay polygon")).to_have_count(0)
    page.evaluate("()=>{Object.defineProperty(document,'hidden',{configurable:true,value:false});document.dispatchEvent(new Event('visibilitychange'));}")
    expect(page.locator("#portal-cycle-overlay polygon")).to_have_count(2)
    data["door_arrows_enabled"]=False;data["fog_version"]+=1
    page.locator("#retry-map-load").click()
    expect(page.locator("#portal-cycle-overlay polygon")).to_have_count(0)
    assert not posts
