"""Real-browser regression for configuration/session draft isolation (mocked HTTP)."""
from test_portal_tools import admin
from playwright.sync_api import expect


def test_session_update_retains_pending_configuration(admin):
    page,posts,data=admin
    item=dict(id="a",map_id=1,name="Source",player_label="Up",kind="stairs",x=100,y=100,visibility="secret",availability="usable",current_visibility="secret",current_availability="usable",arrival="preserve",notes="",destination_id=None,revision=1,runtime_visibility=None,runtime_availability=None)
    payload=dict(ok=True,active_map_id=1,maps=[dict(id=1,name="M",viewer_transition_markers=1,viewer_transition_labels=1)],endpoints=[item])
    page.route("**/api/campaigns/4/transitions",lambda r:r.fulfill(json=payload))
    def update(route):
        body=route.request.post_data_json
        item.update(runtime_visibility=body["visibility"],runtime_availability=body["availability"],revision=item["revision"]+1)
        route.fulfill(json=payload)
    page.route("**/api/campaigns/4/transitions/a/runtime",update)
    page.evaluate("()=>window.dispatchEvent(new Event('focus'))")
    page.locator("#map-passages-panel > summary").click()
    page.locator("#transition-list button").click()
    page.locator("#tr-name").fill("Pending authored name")
    page.locator("#tr-current-visibility").select_option("discovered")
    page.get_by_role("button",name="Update session state",exact=True).click()
    expect(page.locator("#tr-name")).to_have_value("Pending authored name")
    expect(page.locator("#tr-config-status")).to_contain_text("Unsaved")
    expect(page.locator("#tr-session-status")).not_to_contain_text("Unsaved")
    expect(page.locator("#transition-editor")).to_be_visible()
    page.once("dialog",lambda d:d.dismiss())
    page.get_by_role("button",name="Close",exact=True).click()
    expect(page.locator("#transition-editor")).to_be_visible()
