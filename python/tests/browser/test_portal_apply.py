"""Apply checkpoints the editor draft and keeps the portal dialog open."""
import pytest
from playwright.sync_api import expect
from test_portal_editor import editor,browser,open_popup,connect,apply_only


def close_popup(page):
    page.locator("#portal-close").click()
    expect(page.locator("#portal-dialog")).not_to_be_visible()


def save(page):
    page.locator("#wall-save").click()
    expect(page.locator("#wall-status")).to_contain_text("Saved")


def test_apply_keeps_dialog_selection_and_position(editor):
    page,writes,data=editor;open_popup(page);connect(page)
    page.locator("#portal-section").select_option("2")
    handle=page.locator("#portal-dialog-move");box=handle.bounding_box()
    page.mouse.move(box["x"]+15,box["y"]+box["height"]/2);page.mouse.down()
    page.mouse.move(box["x"]+65,box["y"]+box["height"]/2,steps=4);page.mouse.up()
    before=page.locator("#portal-dialog").bounding_box()
    apply_only(page)
    after=page.locator("#portal-dialog").bounding_box()
    assert after["x"]==pytest.approx(before["x"],abs=2) and after["y"]==pytest.approx(before["y"],abs=2)
    assert page.locator("#portal-section").input_value()=="2"
    assert page.locator("#portal-side-0-role").input_value()=="exit"
    expect(page.locator("#portal-apply-status")).to_contain_text("applied to draft")
    assert page.locator("#portal-error").text_content()=="" and not writes
    close_popup(page);save(page);assert len(writes)==1


def test_apply_noop_does_not_add_undo_or_change_pair_id(editor):
    page,writes,data=editor;open_popup(page);connect(page)
    apply_only(page);apply_only(page);apply_only(page)
    expect(page.locator("#portal-apply-status")).to_contain_text("No new changes")
    close_popup(page);page.locator("#wall-undo").click()
    expect(page.locator("#wall-undo")).to_be_disabled()
    open_popup(page);assert page.locator("#portal-side-0-role").input_value()=="unconfigured"
    close_popup(page);page.locator("#wall-redo").click();save(page)
    assert len(writes)==1 and data["walls"][1][6]["pair"]==data["walls"][2][6]["pair"]


def test_continue_after_apply_rebases_and_each_apply_undoes_separately(editor):
    page,writes,data=editor;open_popup(page);connect(page);apply_only(page)
    page.locator("#portal-side-0-kind").select_option("secret")
    page.locator("#portal-side-0-after").select_option("locked_door")
    expect(page.locator("#portal-apply-status")).to_contain_text("Unapplied changes")
    apply_only(page);assert page.locator("#portal-error").text_content()==""
    assert page.locator("#portal-side-0-kind").input_value()=="secret"
    close_popup(page);page.locator("#wall-undo").click()
    open_popup(page);assert page.locator("#portal-side-0-kind").input_value()=="door"
    close_popup(page);page.locator("#wall-undo").click()
    open_popup(page);assert page.locator("#portal-side-0-role").input_value()=="unconfigured"
    assert not writes


@pytest.mark.parametrize("action",["close","cancel","escape"])
def test_close_discards_only_edits_since_last_apply(editor,action):
    page,writes,data=editor;open_popup(page);connect(page);apply_only(page)
    page.locator("#portal-side-0-kind").select_option("secret")
    page.locator("#portal-side-0-after").select_option("locked_door")
    if action=="escape":page.keyboard.press("Escape")
    else:page.locator("#portal-close" if action=="close" else "#portal-cancel").click()
    expect(page.locator("#portal-dialog")).not_to_be_visible()
    assert not writes;save(page)
    assert data["walls"][1][6]["sides"][0]["kind"]=="door"
    open_popup(page);assert page.locator("#portal-side-0-kind").input_value()=="door"


def test_partial_apply_can_be_completed_without_reopening(editor):
    page,writes,data=editor;open_popup(page)
    page.locator("#portal-side-0-role").select_option("exit");apply_only(page)
    expect(page.locator("#portal-apply-status")).to_contain_text("Finish unconfigured")
    page.locator("#portal-section").select_option("2")
    page.locator("#portal-side-0-role").select_option("entry")
    page.locator("#portal-side-0-destination").select_option("1")
    page.locator("#portal-side-0-exit").select_option("0")
    apply_only(page);assert page.locator("#portal-error").text_content()==""
    close_popup(page);save(page);assert len(writes)==1


def test_stale_draft_error_does_not_close_or_apply(editor):
    page,writes,data=editor;open_popup(page);connect(page);apply_only(page)
    # Programmatic change exercises the existing stale guard; native modal blocks background clicks.
    page.evaluate("document.getElementById('wall-undo').click()")
    apply_only(page);expect(page.locator("#portal-error")).to_contain_text("draft changed")
    assert not writes
    close_popup(page);open_popup(page)
    assert page.locator("#portal-side-0-role").input_value()=="unconfigured"


def test_overview_and_submit_focus_after_apply(editor):
    page,writes,data=editor;open_popup(page);connect(page)
    page.locator("#portal-side-0-role").focus()
    page.locator("#portal-form").evaluate("form=>form.requestSubmit()")
    expect(page.locator("#portal-dialog")).to_be_visible()
    assert page.locator("#portal-side-0-role").evaluate("e=>document.activeElement===e")
    page.locator("#portal-popup-overview").click()
    expect(page.locator("#portal-overview-dialog")).to_be_visible()
    assert "Section 3 E" in page.locator("#portal-overview-body").text_content()
    page.keyboard.press("Escape");expect(page.locator("#portal-dialog")).to_be_visible();assert not writes


def test_request_submit_retains_scroll_and_reports_pending_edits(editor):
    page,writes,data=editor;open_popup(page);connect(page)
    page.set_viewport_size({"width":1100,"height":650})
    before=page.locator("#portal-dialog").evaluate("d=>{d.scrollTop=60;return d.scrollTop;}")
    page.locator("#portal-form").evaluate("form=>form.requestSubmit()")
    expect(page.locator("#portal-dialog")).to_be_visible()
    after=page.locator("#portal-dialog").evaluate("d=>d.scrollTop")
    assert after==pytest.approx(before,abs=2)
    page.locator("#portal-side-0-kind").select_option("locked_door")
    expect(page.locator("#portal-apply-status")).to_contain_text("Unapplied changes")
    assert not writes
