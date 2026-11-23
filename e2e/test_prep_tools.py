"""Preparation and administration journeys: walls, notes, copies, status, security, search."""
import re
import time

import pytest
from playwright.sync_api import expect

from support import BLACK, BLUE, RED, Table, login, unique

pytestmark = pytest.mark.e2e
TO_SCREEN = "(el, [x, y]) => { const p = new DOMPoint(x, y).matrixTransform(el.getScreenCTM()); return [p.x, p.y]; }"
NOTES_MD = """## Entrance Hall
A cold breeze blows through the broken doors.

### Features
- Two cracked statues.

## Burial Chamber
Dust covers the stone coffins.
"""


@pytest.fixture
def table(server, actors):
    return Table(server, actors)


def wall_click(page, x, y):
    page.mouse.click(*page.locator("#wall-overlay").evaluate(TO_SCREEN, [x, y]))


def test_wall_tools_and_uvtt_round_trip(table, tmp_path):
    dm, player, page = table.dm, table.player, table.dm.page
    page.goto(f"{table.server.admin}/maps/{table.mid}/walls")
    expect(page.locator("#wall-tool")).to_be_enabled()
    page.select_option("#wall-tool", "add"); page.select_option("#wall-kind", "wall")
    wall_click(page, 200, 100); wall_click(page, 390, 100)          # splits the right room
    wall_click(page, 100, 40); wall_click(page, 100, 160)           # a stray wall to remove
    page.select_option("#wall-tool", "type"); page.select_option("#wall-kind", "door")
    wall_click(page, 300, 100)                                       # the new wall becomes a door
    page.select_option("#wall-tool", "remove")
    wall_click(page, 100, 100)
    page.locator("#wall-save").click()
    expect(page.locator("#wall-status")).to_contain_text("Saved")
    saved = dm.api("GET", f"/api/maps/{table.mid}/wall-editor")["walls"]
    assert len(saved) == 6, saved
    door = [w for w in saved if w[4] == "door"]
    assert len(door) == 1 and abs(door[0][1] - 100) < 2 and abs(door[0][3] - 100) < 2, saved
    assert not [w for w in saved if abs(w[0] - 100) < 2 and abs(w[2] - 100) < 2], "stray wall was not removed"

    with page.expect_download() as pending:
        page.locator("#wall-download").click()
    uvtt = tmp_path / "walls.uvtt"
    pending.value.save_as(uvtt)
    copy = unique("Imported")
    copy_id = dm.import_map(table.cid, copy, walls_file=uvtt)
    imported = dm.api("GET", f"/api/maps/{copy_id}/wall-editor")["walls"]
    assert sorted(w[4] for w in imported) == sorted(w[4] for w in saved)
    for a, b in zip(sorted(imported), sorted(saved)):
        assert all(abs(p - q) <= 1 for p, q in zip(a[:4], b[:4])), (a, b)

    # The closed door now separates the right room's top from its bottom.
    dm.open_map(table.mid)
    dm.fog("reveal", 300, 50)
    player.expect_pixels(table.map_name, [((300, 50), RED), ((300, 150), BLACK), ((100, 100), BLACK)])


def test_room_notes_imported_from_markdown(table):
    dm, page = table.dm, table.dm.page
    page.locator("#room-library-import").evaluate("el => { el.open = true; }")
    page.locator("#room-import-file").set_input_files(
        {"name": "rooms.md", "mimeType": "text/markdown", "buffer": NOTES_MD.encode()})
    page.locator("#room-import-submit").click()
    expect(page.locator("#room-import-status")).to_contain_text("2 sections at H2")
    for x, name, text in ((100, "Entrance Hall", "cold breeze"), (300, "Burial Chamber", "stone coffins")):
        page.locator("#room-select-mode").check()
        dm.click_map(x)
        expect(page.locator("#room-form")).to_be_visible()
        expect(page.locator("#room-import-choice")).to_be_visible()
        page.locator("#room-import-select").select_option(label=name)
        expect(page.locator("#room-name")).to_have_value(name)
        expect(page.locator("#room-markdown")).to_have_value(re.compile(text))
        page.locator("#room-form").get_by_role("button", name="Save room").click()
        expect(page.locator("#room-title")).to_have_text(name)
        expect(page.locator("#room-preview")).to_contain_text(text)
        page.locator("#room-select-mode").uncheck()
    dm.fog("reveal", 100)
    expect(page.locator("#room-title")).to_have_text("Entrance Hall")
    # The lower "Features" heading stays inside Entrance Hall's note.
    expect(page.locator("#room-preview")).to_contain_text("Two cracked statues")


def test_clean_campaign_copy_keeps_content_but_not_play_state(table):
    dm, player, page = table.dm, table.player, table.dm.page
    dm.save_room_note(100, "Crypt", "A **cursed** altar.")
    dm.fog("reveal", 100)
    player.expect_pixels(table.map_name, [((100, 100), RED), ((300, 100), BLACK)])
    page.goto(f"{table.server.admin}/campaigns/{table.cid}")
    copy = unique("Copy")
    form = page.locator(f'form[action="/campaigns/{table.cid}/duplicate"]')
    form.evaluate("el => el.closest('details').open = true")
    form.locator('input[name="name"]').fill(copy)
    form.get_by_role("button", name="Create clean campaign copy").click()
    expect(page.locator(".flash-ok")).to_contain_text("Clean copy created")
    copy_cid = int(re.search(r"/campaigns/(\d+)", page.url).group(1))
    assert copy_cid != table.cid
    rename = page.locator('form[action$="/rename"]')
    expect(rename).to_have_count(1)
    expect(rename.locator('input[name="name"]')).to_have_value(table.map_name)
    expect(page.locator(".pill-live")).to_have_count(0)               # not shown to players
    copy_mid = int(re.search(r"/maps/(\d+)/rename", rename.get_attribute("action")).group(1))
    # Walls and notes were copied.
    assert len(dm.api("GET", f"/api/maps/{copy_mid}/wall-editor")["walls"]) == 5
    dm.open_map(copy_mid)
    dm.page.locator("#room-select-mode").check()
    dm.click_map(100)
    expect(dm.page.locator("#room-title")).to_have_text("Crypt")
    # The player has no access to the copy; the original keeps playing.
    assert player.page.goto(f"{table.server.viewer}/c/{copy_cid}").status == 404
    player.page.goto(f"{table.server.viewer}/c/{table.cid}")
    player.expect_pixels(table.map_name, [((100, 100), RED), ((300, 100), BLACK)])


def test_viewer_sync_panel_tracks_the_player(table):
    page = table.dm.page
    page.goto(f"{table.server.admin}/campaigns/{table.cid}")
    sync = page.locator("[data-sync-list]")
    expect(sync).to_contain_text(re.compile(rf"{table.username} · .*Up to date"), timeout=20_000)
    table.player.page.close()
    page.wait_for_function("""(name) => !Array.from(document.querySelectorAll('[data-sync-list] li'))
        .some(li => li.textContent.startsWith(name + ' ') && li.textContent.includes('Up to date'))""",
                           arg=table.username, timeout=30_000)


def test_login_lockout_and_expiry(table, actors):
    page = actors("attacker")
    for _ in range(5):
        login(page, table.server.viewer, table.username, "wrong-password")
        expect(page.get_by_role("alert")).to_contain_text("Invalid username or password")
    login(page, table.server.viewer, table.username, table.password)   # even the right password
    expect(page.get_by_role("alert")).to_contain_text("Too many failed attempts")
    time.sleep(5.5)                                                     # e2e server: 5 s lockout
    login(page, table.server.viewer, table.username, table.password)
    expect(page).to_have_url(re.compile(rf"/c/{table.cid}$"))


def test_readiness_check_reports_a_map_without_walls(table):
    dm, page = table.dm, table.dm.page
    bare = unique("Bare")
    dm.import_map(table.cid, bare, walls=None)
    page.goto(f"{table.server.admin}/campaigns/{table.cid}")
    page.get_by_role("link", name="Check campaign").click()
    expect(page.locator("h1")).to_have_text("Campaign readiness")
    expect(page.locator("main")).to_contain_text(re.compile(r"2 maps checked · 0 errors"))
    finding = page.locator("li", has_text=bare)
    expect(finding).to_have_count(1)
    finding.get_by_role("link", name="Inspect map (DM only)").click()
    expect(page.locator("h1")).to_have_text(f"{bare} — DM inspection")
    table.player.expect_pixels(table.map_name, [((100, 100), BLACK)])   # checks change nothing


def test_campaign_search_finds_notes_and_maps(table):
    dm, page = table.dm, table.dm.page
    dm.save_room_note(100, "Crypt", "A golden idol rests here.")
    page.goto(f"{table.server.admin}/campaigns/{table.cid}")
    page.keyboard.press("Control+k")                          # not typing in an input
    dialog = page.locator("#campaign-quick-nav")
    expect(dialog).to_be_visible()
    page.locator("#quick-nav-query").fill("golden idol")
    expect(page.locator("#quick-nav-results")).to_contain_text(f"Crypt — {table.map_name} [room]")
    page.locator("#quick-nav-query").press("Enter")
    expect(page.locator("main")).to_contain_text("A golden idol rests here.")
    page.goto(f"{table.server.admin}/campaigns/{table.cid}")
    page.get_by_role("link", name=re.compile("Search campaign")).click()
    page.locator("#quick-nav-kind").select_option("map")
    page.locator("#quick-nav-query").fill(table.map_name)
    expect(page.locator("#quick-nav-results")).to_contain_text(f"{table.map_name} — {table.map_name} [map]")


def test_secret_passage_needing_approval_requires_the_dm_override(table):
    dm, player, page = table.dm, table.player, table.dm.page
    upper = unique("Upper")
    upper_id = dm.import_map(table.cid, upper, colour=BLUE)
    base = f"/api/campaigns/{table.cid}/transitions"
    arrival = dm.api("POST", base, {"map_id": upper_id, "name": "Arrival", "x": 40, "y": 40})["saved_endpoint_id"]
    dm.api("POST", base, {"map_id": table.mid, "name": "Hidden stair", "player_label": "Down", "x": 40, "y": 40,
                          "visibility": "secret", "availability": "approval", "destination_id": arrival})
    dm.open_map(table.mid)
    dm.fog("reveal", 100)
    # A secret endpoint draws no player marker: its position shows plain map art.
    player.expect_pixels(table.map_name, [((40, 40), RED), ((150, 150), RED), ((300, 100), BLACK)])
    page.locator("#map-passages-panel > summary").click()
    page.locator("#transition-list button", has_text="Hidden stair").click()
    page.locator("#tr-travel").click()
    expect(page.locator("#tr-confirm")).to_have_text(f"Travel to {upper}")
    expect(page.locator("#tr-approve")).to_be_enabled()
    page.locator("#tr-confirm").click()                       # required override not given
    time.sleep(1)
    expect(page).to_have_url(re.compile(rf"/maps/{table.mid}\b"))
    player.expect_pixels(table.map_name, [((150, 150), RED)])
    page.locator("#tr-approve").check()
    page.locator("#tr-confirm").click()
    page.wait_for_url(re.compile(rf"/maps/{upper_id}\b"))
    player.expect_pixels(upper, [((150, 150), BLUE), ((300, 100), BLACK)])
