"""Readable SVG labels and high-contrast admin route phases; mocked API responses."""
import io
import math
from time import monotonic
import pytest
from PIL import Image
from playwright.sync_api import expect, TimeoutError as PlaywrightTimeoutError
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


def _phase_sample(page, time, timeout=5000):
    try:
        result = page.wait_for_function("""time => {
          const svg=document.getElementById('portal-cycle-overlay');
          const els=svg ? [...svg.querySelectorAll('polygon')] : [];
          const busy=document.getElementById('busy'), arrows=document.getElementById('door-arrows');
          if (!svg?.dataset.routeId || els.length!==2 || els.some(e=>!e.isConnected) ||
              (busy && !busy.hidden) || (arrows && (!arrows.complete || !arrows.naturalWidth))) return false;
          const animations=els.map(e=>e.getAnimations().filter(a=>a.animationName==='portal-route-flash'));
          if (animations.some(group=>group.length!==1)) return false;
          for (const group of animations) for (const a of group) {a.pause();a.currentTime=time;}
          const styles=els.map(e=>{const s=getComputedStyle(e);return {
            fill:s.fill,stroke:s.stroke,opacity:s.opacity,width:s.strokeWidth,
            vector:s.vectorEffect,filter:s.filter};});
          const points=[...els[0].points], matrix=els[0].getScreenCTM();
          if (!points.length || !matrix) return false;
          const p=new DOMPoint(points.reduce((s,p)=>s+p.x,0)/points.length,
                               points.reduce((s,p)=>s+p.y,0)/points.length).matrixTransform(matrix);
          if (!Number.isFinite(p.x) || !Number.isFinite(p.y)) return false;
          const point=[Math.round(p.x),Math.round(p.y)], mask=getComputedStyle(svg).maskImage;
          window.__portalPhaseCapture={els,time,route:svg.dataset.routeId,mask,point};
          return {styles,point};
        }""", arg=time, timeout=timeout)
    except PlaywrightTimeoutError:
        diagnostic = page.evaluate("""() => {
          const s=document.getElementById('portal-cycle-overlay');
          return {route:s?.dataset.routeId, count:s?.querySelectorAll('polygon').length,
            status:document.getElementById('portal-cycle-status')?.textContent,
            busy:document.getElementById('busy')?.hidden,
            animations:s ? [...s.querySelectorAll('polygon')].map(e=>e.getAnimations().map(a=>a.animationName)) : []};
        }""")
        pytest.fail(f"Portal phase {time} ms did not become sampleable: {diagnostic}")
    try:
        return result.json_value()
    finally:
        result.dispose()


def phase(page, time):
    return _phase_sample(page, time)["styles"]


def phase_screenshot(page, time, timeout=5000):
    deadline = monotonic() + timeout / 1000
    while monotonic() < deadline:
        sample = _phase_sample(page, time, timeout=max(1, int((deadline-monotonic())*1000)))
        image = Image.open(io.BytesIO(page.screenshot(timeout=max(1, int((deadline-monotonic())*1000))))).convert("RGB")
        unchanged = page.evaluate("""() => {
          const c=window.__portalPhaseCapture,s=document.getElementById('portal-cycle-overlay');
          const els=s ? [...s.querySelectorAll('polygon')] : [];
          if (!c || els.length!==2 || els.some((e,i)=>e!==c.els[i] || !e.isConnected) ||
              s.dataset.routeId!==c.route || getComputedStyle(s).maskImage!==c.mask) return false;
          const points=[...els[0].points],matrix=els[0].getScreenCTM();
          if (!points.length || !matrix) return false;
          const p=new DOMPoint(points.reduce((s,p)=>s+p.x,0)/points.length,
                               points.reduce((s,p)=>s+p.y,0)/points.length).matrixTransform(matrix);
          return Math.round(p.x)===c.point[0] && Math.round(p.y)===c.point[1] &&
            els.every(e=>{const a=e.getAnimations().filter(a=>a.animationName==='portal-route-flash');
              return a.length===1 && a[0].playState==='paused' && Math.abs(a[0].currentTime-c.time)<0.01;});
        }""")
        if unchanged:
            return image, sample["point"]
    pytest.fail(f"Portal overlay kept changing during phase {time} ms screenshot capture")


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
    # Reject captures invalidated by redraw, not captures with incorrect colors.
    for time,rgb in [(100,(255,234,0)),(800,(21,56,208))]:
        image,point=phase_screenshot(page,time)
        pixel=image.getpixel(tuple(point));assert all(abs(a-b)<=3 for a,b in zip(pixel,rgb)),(pixel,rgb)
    overlay=page.locator("#portal-cycle-overlay")
    assert overlay.evaluate("e=>getComputedStyle(e).pointerEvents")=="none"
    assert "url(" in overlay.evaluate("e=>getComputedStyle(e).maskImage")
    assert not posts


def test_admin_reduced_motion_is_bright_and_steady(admin):
    page, posts, data = admin
    page.emulate_media(reduced_motion="reduce")
    page.wait_for_function(
        "window.matchMedia('(prefers-reduced-motion: reduce)').matches",
        timeout=5000,
    )
    polygons = page.locator("#portal-cycle-overlay polygon")
    expect(polygons).to_have_count(2, timeout=5000)
    # Media emulation and computed-style updates need not settle in one turn.
    # Locator assertions wait for each exact value and report actual CSS on failure.
    for index in range(2):
        polygon = polygons.nth(index)
        expect(polygon).to_have_css("animation-name", "none", timeout=5000)
        expect(polygon).to_have_css("fill", "rgb(255, 234, 0)", timeout=5000)
        expect(polygon).to_have_css("stroke", "rgb(0, 0, 0)", timeout=5000)
        expect(polygon).to_have_css("opacity", "1", timeout=5000)
    assert not posts
