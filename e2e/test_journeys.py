"""Player and DM journeys through the real UI, in Chromium and Firefox."""
import re

import pytest
from playwright.sync_api import expect

from support import BLACK, RED, Admin, Table, login, path_of

pytestmark = pytest.mark.e2e


@pytest.fixture
def table(server, actors):
    return Table(server, actors)


def test_wrong_password_is_rejected(server, actors):
    page = actors("visitor")
    login(page, server.admin, "superadmin", "not-the-password")
    assert path_of(page) == "/login"
    expect(page.get_by_role("alert")).to_contain_text("Invalid username or password")


def test_first_login_change_lands_on_the_map_and_reveals_reach_the_player(table):
    # Table already covered: campaign, map import with walls, viewer creation, Show,
    # forced password change from a direct /c/<id> link landing on the live map.
    table.dm.fog("reveal", 100)
    table.player.expect_pixels(table.map_name, [((100, 100), RED), ((300, 100), BLACK)])


def test_hide_and_undo_reach_the_player(table):
    table.dm.fog("reveal", 100)
    table.player.expect_pixels(table.map_name, [((100, 100), RED), ((300, 100), BLACK)])
    table.dm.fog("hide", 100)
    table.player.expect_pixels(table.map_name, [((100, 100), BLACK), ((300, 100), BLACK)])
    table.dm.undo()
    table.player.expect_pixels(table.map_name, [((100, 100), RED), ((300, 100), BLACK)])


def test_wall_editor_drag_moves_the_room_boundary_for_players(table):
    page = table.dm.page
    page.goto(f"{table.server.admin}/maps/{table.mid}/walls")
    expect(page.locator("#wall-tool")).to_be_enabled()
    overlay = page.locator("#wall-overlay")
    to_screen = "(el, [x, y]) => { const p = new DOMPoint(x, y).matrixTransform(el.getScreenCTM()); return [p.x, p.y]; }"
    page.mouse.move(*overlay.evaluate(to_screen, [200, 10]))
    page.mouse.down()
    page.mouse.move(*overlay.evaluate(to_screen, [300, 10]), steps=10)
    page.mouse.up()
    expect(page.locator("#wall-status")).to_contain_text("Moved an endpoint")
    page.locator("#wall-save").click()
    expect(page.locator("#wall-status")).to_contain_text("Saved")
    # The divider now runs from (300, 10) to (200, 190): (230, 30) joins the left room.
    table.dm.open_map(table.mid)
    table.dm.fog("reveal", 100)
    table.player.expect_pixels(table.map_name, [((100, 100), RED), ((230, 30), RED),
                                                ((230, 170), BLACK), ((350, 100), BLACK)])


def test_voluntary_password_change_stays_on_the_account_page(table):
    page = table.player.page
    page.goto(f"{table.server.viewer}/account")
    page.locator('input[name="current_password"]').fill(table.password)
    page.locator('input[name="new_password"]').fill("player-password-2")
    page.locator('input[name="confirm_password"]').fill("player-password-2")
    page.locator('form[action="/account"] button[type="submit"]').click()
    expect(page).to_have_url(re.compile(r"/account\?ok="))
    expect(page.locator(".flash-ok")).to_contain_text("Account updated")


def test_player_cannot_use_the_admin_portal_and_can_log_out(table, actors):
    other = actors("player-on-admin")
    login(other, table.server.admin, table.username, table.password)
    assert path_of(other) == "/login"
    expect(other.get_by_role("alert")).to_contain_text("can only use the viewer screen")
    page = table.player.page
    page.goto(f"{table.server.viewer}/account")
    page.locator('form[action="/logout"] button').click()
    expect(page).to_have_url(re.compile(r"/login"))
    page.goto(f"{table.server.viewer}/c/{table.cid}")
    expect(page).to_have_url(re.compile(r"/login"))


def test_deactivating_the_player_ends_their_live_view(table):
    admin = Admin(table.dm.page, table.server.admin)
    admin.page.goto(f"{table.server.admin}/users")
    row = admin.page.locator("tr", has=admin.page.locator("strong", has_text=re.compile(rf"^{table.username}$")))
    form = row.locator('form[action$="/update"]')
    form.locator('input[name="active"]').uncheck()
    form.locator('button[type="submit"]').click()
    expect(admin.page.locator(".flash-ok")).to_be_visible()
    # The live socket is revoked; the viewer refreshes, gets 401 and goes to login.
    expect(table.player.page).to_have_url(re.compile(r"/login"), timeout=30_000)
