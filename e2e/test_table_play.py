"""At-the-table journeys: doors, switching maps, checkpoints, several players, zoom."""
import re
import time
from urllib.parse import urlsplit

import pytest
from playwright.sync_api import expect

from support import BLACK, BLUE, RED, Player, Table, door_walls, unique

pytestmark = pytest.mark.e2e
FAR_RIGHT = (330, 60)   # inside the right room, away from any door arrow or marker


def test_locked_door_single_double_click_rules(server, actors):
    table = Table(server, actors, walls=door_walls(locked=True))
    dm, player = table.dm, table.player
    dm.fog("reveal", 100)
    player.expect_pixels(table.map_name, [((100, 100), RED), (FAR_RIGHT, BLACK)])
    x, y = dm.arrow_point()
    assert dm.door(x, y, "single") == "none"         # locked: a single click does nothing
    assert dm.door(x, y, "double") == "unlock"       # double click unlocks, fog unchanged
    player.expect_pixels(table.map_name, [(FAR_RIGHT, BLACK)])
    assert dm.door(x, y, "single") == "reveal"       # now it opens into the next room
    player.expect_pixels(table.map_name, [((100, 100), RED), (FAR_RIGHT, RED)])


def test_plain_door_arrow_reveals_the_next_room(server, actors):
    table = Table(server, actors, walls=door_walls())
    dm, player = table.dm, table.player
    dm.fog("reveal", 100)
    x, y = dm.arrow_point()
    box = dm.page.locator("#map-img").bounding_box()
    with dm.page.expect_response(lambda r: urlsplit(r.url).path.endswith("/door-arrows/reveal")) as pending:
        dm.page.mouse.click(box["x"] + box["width"] * x / 400, box["y"] + box["height"] * y / 200)
    assert pending.value.status == 200, pending.value.text()
    player.expect_pixels(table.map_name, [((100, 100), RED), (FAR_RIGHT, RED)])


def test_switching_maps_offers_restore_or_reset(table):
    dm, player = table.dm, table.player
    dm.fog("reveal", 100)
    player.expect_pixels(table.map_name, [((100, 100), RED), ((300, 100), BLACK)])
    other = unique("Cellar")
    other_id = dm.import_map(table.cid, other, colour=BLUE)
    dm.show_map(table.cid, other_id)                  # fresh map: no dialog, fully fogged
    player.expect_pixels(other, [((100, 100), BLACK), ((300, 100), BLACK)])
    dm.show_map(table.cid, table.mid, choice="restore")
    player.expect_pixels(table.map_name, [((100, 100), RED), ((300, 100), BLACK)])
    dm.show_map(table.cid, other_id)
    player.expect_pixels(other, [((100, 100), BLACK)])
    dm.show_map(table.cid, table.mid, choice="reset")
    player.expect_pixels(table.map_name, [((100, 100), BLACK), ((300, 100), BLACK)])


def test_session_checkpoint_restore_reaches_the_player(table):
    dm, player = table.dm, table.player
    dm.fog("reveal", 100)
    player.expect_pixels(table.map_name, [((100, 100), RED), ((300, 100), BLACK)])
    page, admin = dm.page, table.server.admin
    page.goto(f"{admin}/campaigns/{table.cid}/checkpoints")
    name = unique("Before the fight")
    form = page.locator(f'form[action="/campaigns/{table.cid}/checkpoints"]')
    form.locator('input[name="name"]').fill(name)
    form.locator('textarea[name="notes"]').fill("Left room explored")
    form.get_by_role("button", name="Save session checkpoint").click()
    expect(page.get_by_role("link", name=name)).to_be_visible()
    dm.open_map(table.mid)
    dm.fog("reveal", 300)
    player.expect_pixels(table.map_name, [((100, 100), RED), ((300, 100), RED)])
    page.goto(f"{admin}/campaigns/{table.cid}/checkpoints")
    page.get_by_role("link", name=name).click()
    restore = page.locator('form[action$="/restore"]')
    restore.locator('input[name="confirm"]').fill(table.campaign)
    page.once("dialog", lambda dialog: dialog.accept())
    restore.get_by_role("button", name="Save safety checkpoint and restore").click()
    expect(page.locator(".flash-ok")).to_be_visible()
    player.expect_pixels(table.map_name, [((100, 100), RED), ((300, 100), BLACK)])


def test_two_players_follow_and_one_revocation_spares_the_other(table, actors):
    dm, first = table.dm, table.player
    second_name = unique("player")
    dm.create_viewer(table.cid, second_name, "temporary-pass-1")
    second = Player(actors("second player"), table.server.viewer, table.cid)
    second.first_login(second_name, "temporary-pass-1", "player-password-1")
    dm.open_map(table.mid)
    dm.fog("reveal", 100)
    for player in (first, second):
        player.expect_pixels(table.map_name, [((100, 100), RED), ((300, 100), BLACK)])
    dm.page.goto(f"{table.server.admin}/users")
    row = dm.page.locator("tr", has=dm.page.locator("strong", has_text=re.compile(rf"^{second_name}$")))
    row.locator('form[action$="/update"] input[name="active"]').uncheck()
    row.locator('form[action$="/update"] button[type="submit"]').click()
    expect(dm.page.locator(".flash-ok")).to_be_visible()
    expect(second.page).to_have_url(re.compile(r"/login"), timeout=30_000)
    first.expect_live()
    dm.open_map(table.mid)
    dm.fog("reveal", 300)
    first.expect_pixels(table.map_name, [((100, 100), RED), ((300, 100), RED)])


def test_dm_double_click_zooms_the_player_to_a_room(table):
    dm, player = table.dm, table.player
    dm.fog("reveal", 100)
    dm.fog("reveal", 300)
    player.expect_pixels(table.map_name, [((100, 100), RED), ((300, 100), RED)])
    player.page.keyboard.press("f")
    time.sleep(0.5)
    overview = player.map_width()
    box = dm.page.locator("#map-img").bounding_box()
    with dm.page.expect_response(lambda r: urlsplit(r.url).path.endswith("/viewer-zoom")) as pending:
        dm.page.mouse.dblclick(box["x"] + box["width"] * 100 / 400, box["y"] + box["height"] * 100 / 200)
    assert pending.value.json().get("viewers") == 1, pending.value.text()
    # The player's view fits the left room: the whole map is drawn larger.
    player.page.wait_for_function("(w) => document.querySelector('#map').getBoundingClientRect().width > w * 1.3",
                                  arg=overview)
    player.page.keyboard.press("f")                  # F always returns to the overview
    player.page.wait_for_function("(w) => Math.abs(document.querySelector('#map').getBoundingClientRect().width - w) < 2",
                                  arg=overview)


@pytest.fixture
def table(server, actors):
    return Table(server, actors)
