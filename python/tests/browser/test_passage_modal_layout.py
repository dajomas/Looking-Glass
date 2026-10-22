"""Real-browser regressions with mocked routes; no live campaign writes."""
from test_portal_tools import admin
from playwright.sync_api import expect


def test_sidebar_defaults_and_legend_independence(admin):
    page,posts,data=admin
    expect(page.locator('details[name="fog-editor-panels"][open]')).to_have_count(0)
    expect(page.locator("#wall-legend")).to_have_attribute("open","")
    page.locator("#map-passages-panel > summary").click()
    page.locator("#walls-panel > summary").click()
    expect(page.locator("#map-passages-panel")).not_to_have_attribute("open","")
    expect(page.locator("#wall-legend")).to_have_attribute("open","")
    page.locator("#wall-legend > summary").click()
    page.locator("#fog-panel > summary").click()
    expect(page.locator("#wall-legend")).not_to_have_attribute("open","")
    expect(page.locator('details[name="fog-editor-panels"][open]')).to_have_count(1)
    assert not posts


def test_footer_remains_visible_when_body_scrolls(admin):
    page,posts,data=admin
    page.set_viewport_size(dict(width=1100,height=650))
    page.locator("#map-passages-panel > summary").click()
    page.locator("#transition-add").click()
    page.evaluate("()=>window.dispatchEvent(new KeyboardEvent('keydown',{key:'Escape'}))")
    # Place through screen coordinates after fitting the map.
    page.locator("#transition-add").click()
    point=page.evaluate("()=>{const p=window.testPZ,r=document.getElementById('viewport').getBoundingClientRect();return {x:r.left+p.x+100*p.scale,y:r.top+p.y+100*p.scale};}")
    page.mouse.click(point["x"],point["y"])
    expect(page.locator("#transition-editor")).to_be_visible()
    footer=page.locator("#transition-editor .transition-actions")
    before=footer.bounding_box()
    page.locator("#transition-editor .transition-body").evaluate("e=>e.scrollTop=e.scrollHeight")
    after=footer.bounding_box()
    assert abs(before["y"]-after["y"])<2
    assert after["y"]>=0 and after["y"]+after["height"]<=650
    expect(page.locator("#tr-close")).to_be_in_viewport()
    expect(page.locator('#transition-form button[type="submit"]')).to_be_in_viewport()
    assert not posts


def test_open_destination_cancel_does_not_activate(admin):
    page,posts,data=admin
    payload=dict(ok=True,active_map_id=1,maps=[dict(id=1,name="M",viewer_transition_markers=1,viewer_transition_labels=1),dict(id=2,name="Upper")],endpoints=[
        dict(id="a",map_id=1,name="Source",player_label="Up",kind="stairs",x=100,y=100,visibility="discovered",availability="usable",current_visibility="discovered",current_availability="usable",arrival="preserve",notes="",destination_id="b",revision=1),
        dict(id="b",map_id=2,name="Target",kind="stairs",x=100,y=100,revision=1)])
    page.route("**/api/campaigns/4/transitions",lambda r:r.fulfill(json=payload))
    page.route("**/api/maps/2/display-options",lambda r:r.fulfill(json=dict(ok=True,can_restore=False,has_current_reveals=True)))
    page.evaluate("()=>window.dispatchEvent(new Event('focus'))")
    page.locator("#map-passages-panel > summary").click()
    page.locator("#transition-list button").first.click()
    with page.context.expect_page() as new_page:
        page.locator("#tr-open").click()
    reserved=new_page.value
    expect(page.locator("#map-display-dialog")).to_be_visible()
    page.locator('#map-display-dialog button[value="cancel"]').click()
    expect(page.locator("#transition-editor")).to_be_visible()
    page.wait_for_function("document.getElementById('transition-status').textContent.includes('cancelled')")
    assert not posts
