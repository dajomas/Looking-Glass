"""Readable SVG labels and high-contrast admin route phases; mocked API responses."""
import io
import math
import pytest
from PIL import Image
from playwright.sync_api import expect
from test_portal_editor import editor
from test_portal_tools import admin


def background_paint_sample(page, fill_override=None):
    """Measure fill, not glyph ink or a border pixel; screenshot styles are temporary."""
    rects = page.locator("#wall-overlay .portal-label rect")
    bounds = [rects.nth(i).bounding_box() for i in range(rects.count())]
    style = "#wall-overlay .portal-label-text { visibility: hidden !important; }"
    if fill_override is not None:
        style += f"#wall-overlay .portal-label-background {{ fill: {fill_override} !important; }}"
    image = Image.open(io.BytesIO(page.screenshot(style=style))).convert("RGB")
    samples = []
    for rect in bounds:
        assert rect is not None and rect["width"] >= 8 and rect["height"] >= 8
        x = math.floor(rect["x"] + rect["width"] / 2)
        y = math.floor(rect["y"] + rect["height"] / 2)
        samples.append([image.getpixel((x + dx, y + dy))
                        for dy in (-1, 0, 1) for dx in (-1, 0, 1)])
    assert len(samples) == 4
    return image, samples


@pytest.mark.parametrize("zoom",[0.5,1,2.5])
def test_label_background_padding_and_screen_size(editor,zoom,tmp_path):
    page,writes,data=editor
    page.evaluate("zoom=>{const p=window.testPZ,r=p.vp.getBoundingClientRect();p.scale=zoom;p.x=(r.width-p.w*zoom)/2;p.y=(r.height-p.h*zoom)/2;p.apply();}",zoom)
    assert page.locator(".stage").evaluate("el => getComputedStyle(el).willChange") == "auto"
    badges=page.locator("#wall-overlay .portal-label")
    expect(badges).to_have_count(4)
    boxes=badges.evaluate_all("""els=>els.map(g=>{const r=g.querySelector('rect'),t=g.querySelector('text'),a=r.getBBox(),b=t.getBBox(),s=getComputedStyle(r);return {rect:{x:a.x,y:a.y,width:a.width,height:a.height},text:{x:b.x,y:b.y,width:b.width,height:b.height},fill:s.fill,stroke:s.stroke,vector:s.vectorEffect,font:getComputedStyle(t).fontSize,pointer:getComputedStyle(g).pointerEvents,order:g.firstElementChild===r};})""")
    for box in boxes:
        a,b=box["rect"],box["text"]
        assert box["order"] and box["pointer"]=="none" and box["vector"]=="non-scaling-stroke"
        assert box["fill"]=="rgba(8, 12, 20, 0.78)"
        assert (b["x"]-a["x"])*zoom==pytest.approx(4,abs=.02)
        assert (b["y"]-a["y"])*zoom==pytest.approx(2.5,abs=.02)
        assert (a["width"]-b["width"])*zoom==pytest.approx(8,abs=.02)
        assert (a["height"]-b["height"])*zoom==pytest.approx(5,abs=.02)
        assert float(box["font"].removesuffix("px"))*zoom==pytest.approx(12,abs=.02)
    # Geometry above checks padding with text visible. Isolate the actual fill
    # for paint checks, away from the rounded border and font-dependent ink.
    image, samples = background_paint_sample(page)
    if any(max(pixel) >= 110 for patch in samples for pixel in patch):
        image.save(tmp_path / "portal-label-background.png")
        (tmp_path / "portal-label-background.txt").write_text(
            f"zoom={zoom!r} samples={samples!r}; threshold remains <110")
        page.screenshot(path=str(tmp_path / "portal-label-normal.png"))
    assert all(max(pixel) < 110 for patch in samples for pixel in patch), samples
    assert badges.first.locator("text").evaluate("el => getComputedStyle(el).visibility") == "visible"
    assert not writes


@pytest.mark.parametrize("zoom", [0.5, 1, 2.5])
@pytest.mark.parametrize("fill", ["none", "#fff"])
def test_background_paint_probe_rejects_missing_or_white_fill(editor, zoom, fill):
    page, writes, data = editor
    page.evaluate("zoom=>{const p=window.testPZ,r=p.vp.getBoundingClientRect();p.scale=zoom;p.x=(r.width-p.w*zoom)/2;p.y=(r.height-p.h*zoom)/2;p.apply();}", zoom)
    _, samples = background_paint_sample(page, fill_override=fill)
    assert all(max(pixel) >= 110 for patch in samples for pixel in patch), samples
    # Neither the temporary text hiding nor the control fill persists.
    assert page.locator("#wall-overlay .portal-label-text").first.evaluate(
        "el => getComputedStyle(el).visibility") == "visible"
    assert page.locator("#wall-overlay .portal-label-background").first.evaluate(
        "el => getComputedStyle(el).fill") == "rgba(8, 12, 20, 0.78)"
    assert not writes


def test_label_layer_on_top_and_clicks_still_edit(editor):
    page,writes,data=editor
    assert page.locator("#wall-overlay").evaluate("svg=>{const l=svg.querySelector('.portal-label-layer');return [...svg.querySelectorAll('path')].every(p=>!!(p.compareDocumentPosition(l)&Node.DOCUMENT_POSITION_FOLLOWING));}")
    assert page.locator("#wall-overlay .portal-label-text").all_text_contents()==["2.E","2.W","3.E","3.W"]
    page.locator("#wall-tool").select_option("edit")
    point=page.locator("#wall-overlay").evaluate("el=>{const p=new DOMPoint(100,100).matrixTransform(el.getScreenCTM());return [p.x,p.y];}")
    page.mouse.click(*point);expect(page.locator("#wall-edit-dialog")).to_be_visible();assert not writes


def test_long_section_labels_fit_their_backgrounds(editor):
    page,writes,data=editor
    original=data["walls"]
    data["walls"]=[original[0][:] for _ in range(99)]+original[1:]
    page.locator("#wall-reload").click()
    expect(page.locator("#wall-overlay .portal-label-text").first).to_have_text("100.E")
    sizes=page.locator("#wall-overlay .portal-label").evaluate_all("els=>els.map(g=>[g.firstElementChild.getBBox().width,g.lastElementChild.getBBox().width])")
    assert all(a>b for a,b in sizes);assert not writes


def phase(page,time):
    return page.locator("#portal-cycle-overlay polygon").evaluate_all("""(els,time)=>els.map(e=>{for(const a of e.getAnimations()){a.pause();a.currentTime=time;}const s=getComputedStyle(e);return {fill:s.fill,stroke:s.stroke,opacity:s.opacity,width:s.strokeWidth,vector:s.vectorEffect,filter:s.filter};})""",time)


def test_admin_highlight_phases_have_distinct_color_and_outline(admin):
    page,posts,data=admin
    first=phase(page,100);second=phase(page,800)
    assert len(first)==len(second)==2
    for value in first:
        assert value["fill"]=="rgb(255, 234, 0)" and value["stroke"]=="rgb(0, 0, 0)"
        assert value["opacity"]=="1" and value["width"]=="4px" and value["vector"]=="non-scaling-stroke"
    for value in second:
        assert value["fill"]=="rgb(21, 56, 208)" and value["stroke"]=="rgb(255, 255, 255)"
        assert value["opacity"]=="1"
    # Inspect an interior pixel in each rendered phase (the normal arrow alpha mask remains active).
    point=page.locator("#portal-cycle-overlay").evaluate("e=>{const p=new DOMPoint(68,55).matrixTransform(e.getScreenCTM());return [Math.round(p.x),Math.round(p.y)];}")
    for time,rgb in [(100,(255,234,0)),(800,(21,56,208))]:
        phase(page,time);image=Image.open(io.BytesIO(page.screenshot())).convert("RGB")
        pixel=image.getpixel(tuple(point));assert all(abs(a-b)<=3 for a,b in zip(pixel,rgb)),(pixel,rgb)
    overlay=page.locator("#portal-cycle-overlay")
    assert overlay.evaluate("e=>getComputedStyle(e).pointerEvents")=="none"
    assert "url(" in overlay.evaluate("e=>getComputedStyle(e).maskImage")
    assert not posts


def test_admin_reduced_motion_is_bright_and_steady(admin):
    page,posts,data=admin;page.emulate_media(reduced_motion="reduce")
    values=page.locator("#portal-cycle-overlay polygon").evaluate_all("els=>els.map(e=>{const s=getComputedStyle(e);return {animation:s.animationName,fill:s.fill,stroke:s.stroke,opacity:s.opacity};})")
    assert len(values)==2
    assert all(v==dict(animation="none",fill="rgb(255, 234, 0)",stroke="rgb(0, 0, 0)",opacity="1") for v in values)
    assert not posts
