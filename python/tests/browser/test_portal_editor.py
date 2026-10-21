"""Portal popup browser integration using the existing mocked editor fixture."""
import pytest
from test_wall_edit_dialog import editor,browser,open_edit
from playwright.sync_api import expect


def configure(page):
    page.locator("#portal-configure").click()
    expect(page.locator("#portal-dialog")).to_be_visible()
    page.locator("#portal-form button[type=submit]").click()
    expect(page.locator("#portal-dialog")).not_to_be_visible()


def test_pair_save_and_reload(editor):
    page,writes,data=editor;configure(page)
    expect(page.locator("#wall-overlay text")).to_have_count(4);assert not writes
    page.locator("#wall-save").click();expect(page.locator("#wall-status")).to_contain_text("Saved")
    a,b=data["walls"];assert a[4]==b[4]=="portal" and a[5] and b[5]
    assert a[6]["pair"]==b[6]["pair"] and a[6]["sides"][0]["exit"]==0
    page.locator("#wall-reload").click();expect(page.locator("#wall-count")).to_contain_text("saved")
    page.locator("#portal-configure").click()
    assert page.locator("#portal-0-0-role").input_value()=="entry"
    assert page.locator("#portal-1-0-role").input_value()=="exit"


def test_pair_undo_redo_remove_atomic(editor):
    page,writes,data=editor;configure(page)
    page.locator("#wall-undo").click();expect(page.locator("#wall-overlay text")).to_have_count(0)
    page.locator("#wall-redo").click();expect(page.locator("#wall-overlay text")).to_have_count(4)
    page.locator("#portal-configure").click();page.locator("#portal-remove").click()
    expect(page.locator("#wall-overlay text")).to_have_count(0)
    page.locator("#wall-undo").click();expect(page.locator("#wall-overlay text")).to_have_count(4)
    assert not writes


def test_invalid_same_element_none_and_unused_exit(editor):
    page,writes,data=editor;page.locator("#portal-configure").click()
    page.locator("#portal-b").select_option("0");page.locator("#portal-form button[type=submit]").click()
    expect(page.locator("#portal-error")).to_contain_text("different")
    page.locator("#portal-b").select_option("1");page.locator("#portal-0-0-role").select_option("none")
    page.locator("#portal-form button[type=submit]").click()
    expect(page.locator("#portal-error")).to_contain_text("at most",ignore_case=True)
    page.locator("#portal-0-0-role").select_option("entry");page.locator("#portal-1-1-role").select_option("exit")
    page.locator("#portal-form button[type=submit]").click()
    expect(page.locator("#portal-error")).to_contain_text("incoming");assert not writes


def test_shared_exit_secret_after_and_cancel(editor):
    page,writes,data=editor;page.locator("#portal-configure").click()
    page.locator("#portal-0-1-role").select_option("entry");page.locator("#portal-0-1-kind").select_option("secret")
    page.locator("#portal-0-1-after").select_option("locked_door");page.locator("#portal-form button[type=submit]").click()
    expect(page.locator("#portal-dialog")).not_to_be_visible()
    page.locator("#wall-save").click();expect(page.locator("#wall-status")).to_contain_text("Saved")
    sides=data["walls"][0][6]["sides"]
    assert sides[0]["exit"]==sides[1]["exit"]==0 and sides[1]["kind"]=="secret" and sides[1]["after"]=="locked_door"
    page.locator("#portal-configure").click();page.locator("#portal-0-1-after").select_option("unlocked_door")
    page.keyboard.press("Escape");expect(page.locator("#wall-count")).to_contain_text("saved");assert len(writes)==1


def test_secret_door_outcome(editor):
    page,writes,data=editor;open_edit(page)
    page.locator("#wall-edit-kind").select_option("secret");page.locator("#secret-after").select_option("locked_door")
    page.locator("#wall-edit-apply").click();page.locator("#wall-save").click()
    expect(page.locator("#wall-status")).to_contain_text("Saved")
    assert data["walls"][0][6]=={"after":"locked_door"}
