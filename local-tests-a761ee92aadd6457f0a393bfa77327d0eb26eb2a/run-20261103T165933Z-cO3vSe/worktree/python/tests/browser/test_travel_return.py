"""Real-browser return path with mock HTTP; no live campaign mutations."""
from test_portal_tools import admin
from playwright.sync_api import expect


def test_back_and_escape_keep_pending_passage_fields(admin):
    page,posts,data=admin
    source=dict(id="a",map_id=1,name="Source",player_label="Up",kind="stairs",x=100,y=100,visibility="secret",availability="usable",current_visibility="secret",current_availability="usable",arrival="preserve",notes="",destination_id="b",revision=1,runtime_visibility=None,runtime_availability=None)
    payload=dict(ok=True,active_map_id=1,maps=[dict(id=1,name="M",viewer_transition_markers=1,viewer_transition_labels=1),dict(id=2,name="Upper")],endpoints=[source,dict(id="b",map_id=2,name="Target",revision=1)])
    preview=dict(ok=True,source_revision=1,destination_revision=1,destination_version=["t",0,1],destination_map_name="Upper",destination_name="Target",arrival="preserve",needs_override=True,source_visibility="secret",source_state="usable")
    page.route("**/api/campaigns/4/transitions",lambda r:r.fulfill(json=payload))
    page.route("**/api/campaigns/4/transitions/a/preview",lambda r:r.fulfill(json=preview))
    page.evaluate("()=>window.dispatchEvent(new Event('focus'))")
    page.locator("#map-passages-panel > summary").click();page.locator("#transition-list button").click()
    page.locator("#tr-name").fill("Pending name");page.locator("#tr-current-availability").select_option("blocked")
    for escape in (False,True):
        page.once("dialog",lambda d:d.accept())
        page.locator("#tr-travel").click()
        expect(page.locator("#tr-confirm")).to_have_text("Travel to Upper")
        if escape:page.keyboard.press("Escape")
        else:page.get_by_role("button",name="Back to passage").click()
        expect(page.locator("#transition-editor")).to_be_visible()
        expect(page.locator("#tr-name")).to_have_value("Pending name")
        expect(page.locator("#tr-current-availability")).to_have_value("blocked")
        expect(page.locator("#tr-config-status")).to_contain_text("Unsaved")
        expect(page.locator("#tr-session-status")).to_contain_text("Unsaved")
        assert not posts
