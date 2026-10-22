"""Adaptive travel labels against mocked preflight responses in a real browser."""
from test_portal_tools import admin
from playwright.sync_api import expect


def test_approval_labels_follow_each_fresh_preview(admin):
    page,posts,data=admin
    item=dict(id="a",map_id=1,name="Source",player_label="Up",kind="stairs",x=100,y=100,visibility="discovered",availability="usable",current_visibility="discovered",current_availability="usable",arrival="preserve",notes="",destination_id="b",revision=1,runtime_visibility=None,runtime_availability=None)
    listing=dict(ok=True,active_map_id=1,maps=[dict(id=1,name="M",viewer_transition_markers=1,viewer_transition_labels=1),dict(id=2,name="Upper")],endpoints=[item,dict(id="b",map_id=2,name="Target",revision=1)])
    preview=dict(ok=True,source_revision=1,destination_revision=1,destination_version=["t",0,1],destination_map_name="Upper",destination_name="Target",arrival="preserve",source_visibility="discovered",source_state="usable",needs_override=False)
    page.route("**/api/campaigns/4/transitions",lambda r:r.fulfill(json=listing))
    page.route("**/api/campaigns/4/transitions/a/preview",lambda r:r.fulfill(json=preview))
    page.evaluate("()=>window.dispatchEvent(new Event('focus'))")
    page.locator("#map-passages-panel > summary").click();page.locator("#transition-list button").click()
    for visibility,state,label in [("secret","approval","Allow this trip despite passage restrictions"),("discovered","approval","I approve this trip"),("discovered","usable",None)]:
        preview.update(source_visibility=visibility,source_state=state,needs_override=visibility=="secret" or state!="usable")
        page.locator("#tr-travel").click()
        if label:
            expect(page.locator("#tr-approval-control")).to_be_visible()
            expect(page.locator("#tr-approval-label")).to_have_text(label)
            expect(page.locator("#tr-approve")).not_to_be_checked()
            assert page.locator("#tr-approve").evaluate("e=>e.required")
            page.locator("#tr-approve").check()
        else:
            expect(page.locator("#tr-approval-control")).not_to_be_visible()
            expect(page.locator("#tr-approve")).to_be_disabled()
            assert not page.locator("#tr-approve").evaluate("e=>e.required")
        page.locator("#tr-cancel-travel").click()
        expect(page.locator("#transition-editor")).to_be_visible()
        assert not posts
