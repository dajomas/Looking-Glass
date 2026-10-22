"""Compass labels and explicit None-to-Exit selection; mocked HTTP, real editor."""
import pytest
from test_portal_editor import editor,browser,open_popup,apply,connect
from playwright.sync_api import expect


def test_compass_labels_on_map_panels_and_target_selector(editor):
    page,writes,data=editor
    labels=page.locator("#wall-overlay text").all_text_contents()
    assert labels==["2.E","2.W","3.E","3.W"]
    open_popup(page)
    assert page.locator("#portal-sides legend").all_text_contents()==["Portal section 2 — East (E)","Portal section 2 — West (W)"]
    page.locator("#portal-side-0-role").select_option("entry")
    page.locator("#portal-side-0-destination").select_option("2")
    text=page.locator("#portal-side-0-exit option").all_text_contents()
    assert any("East (E)" in t for t in text) and any("West (W)" in t for t in text)
    assert not any("Side 1" in t or "Side 2" in t for t in text)
    assert not writes


@pytest.mark.parametrize("initial",["none","exit","unconfigured"])
def test_destination_selectable_and_converts_immediately(editor,initial):
    page,writes,data=editor;open_popup(page)
    page.locator("#portal-section").select_option("2")
    if initial!="unconfigured":page.locator("#portal-side-0-role").select_option(initial)
    page.locator("#portal-section").select_option("1")
    page.locator("#portal-side-0-role").select_option("entry")
    page.locator("#portal-side-0-destination").select_option("2")
    option=page.locator('#portal-side-0-exit option[value="0"]')
    assert not option.evaluate("e=>e.disabled")
    page.locator("#portal-side-0-exit").select_option("0")
    page.locator("#portal-section").select_option("2")
    assert page.locator("#portal-side-0-role").input_value()=="exit"
    assert page.locator("#portal-side-1-role").input_value()=="none"
    assert not writes
    apply(page);page.locator("#wall-save").click();expect(page.locator("#wall-status")).to_contain_text("Saved")
    assert data["walls"][2][6]["sides"]==[{"role":"exit"},{"role":"none"}]
    assert data["walls"][1][6]["sides"][0]["exit"]==0


def test_both_not_demoted_and_entry_only_disabled(editor):
    page,writes,data=editor;open_popup(page)
    page.locator("#portal-section").select_option("2")
    page.locator("#portal-side-0-role").select_option("entry")
    page.locator("#portal-section").select_option("1")
    page.locator("#portal-side-0-role").select_option("entry")
    page.locator("#portal-side-0-destination").select_option("2")
    assert page.locator('#portal-side-0-exit option[value="0"]').evaluate("e=>e.disabled")
    assert not page.locator('#portal-side-0-exit option[value="1"]').evaluate("e=>e.disabled")
    page.locator("#portal-section").select_option("2")
    page.locator("#portal-side-0-role").select_option("both")
    page.locator("#portal-side-0-kind").select_option("secret")
    page.locator("#portal-side-0-after").select_option("locked_door")
    page.locator("#portal-section").select_option("1")
    page.locator("#portal-side-0-destination").select_option("2")
    page.locator("#portal-side-0-exit").select_option("0")
    page.locator("#portal-section").select_option("2")
    assert page.locator("#portal-side-0-role").input_value()=="both"
    assert page.locator("#portal-side-0-kind").input_value()=="secret"
    assert page.locator("#portal-side-0-after").input_value()=="locked_door"


def test_cancel_none_conversion_and_undo(editor):
    page,writes,data=editor;open_popup(page)
    page.locator("#portal-section").select_option("2");page.locator("#portal-side-0-role").select_option("none")
    apply(page)
    open_popup(page);connect(page);page.keyboard.press("Escape")
    open_popup(page);page.locator("#portal-section").select_option("2")
    assert page.locator("#portal-side-0-role").input_value()=="none"
    page.locator("#portal-section").select_option("1");connect(page);apply(page)
    page.locator("#wall-undo").click();open_popup(page)
    page.locator("#portal-section").select_option("2")
    assert page.locator("#portal-side-0-role").input_value()=="none";assert not writes


def test_diagonal_and_reversed_endpoint_labels(editor):
    page,writes,data=editor
    def edit(coords):
        page.locator("#wall-tool").select_option("edit")
        x=(coords[0]+coords[2])/2;y=(coords[1]+coords[3])/2
        # The first edit selects the existing vertical portal; subsequent select uses new midpoint.
        point=page.locator("#wall-overlay").evaluate("(el,[x,y])=>{const p=new DOMPoint(x,y).matrixTransform(el.getScreenCTM());return [p.x,p.y];}",[100,100] if coords[0]==80 else [120,80])
        page.mouse.click(*point);expect(page.locator("#wall-edit-dialog")).to_be_visible()
        for key,value in zip(["x1","y1","x2","y2"],coords):page.locator("#wall-edit-"+key).fill(str(value))
        page.locator("#wall-edit-apply").click()
    edit([80,40,160,120])
    assert page.locator("#wall-overlay text").all_text_contents()[:2]==["2.NE","2.SW"]
    open_popup(page);assert "North-East (NE)" in page.locator("#portal-sides legend").first.text_content()
    page.locator("#portal-close").click();edit([160,120,80,40])
    assert page.locator("#wall-overlay text").all_text_contents()[:2]==["2.SW","2.NE"]
