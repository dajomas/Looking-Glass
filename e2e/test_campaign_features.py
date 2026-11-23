"""Wider campaign journeys: passages, restarts, backups, notes, roles and WebP."""
import re

import pytest
from playwright.sync_api import expect

from support import BLACK, BLUE, RED, Admin, Table, login, unique

pytestmark = pytest.mark.e2e


@pytest.fixture
def table(server, actors):
    return Table(server, actors)


def test_passage_travel_switches_the_player_to_the_destination_map(table):
    dm, player = table.dm, table.player
    upper = unique("Upper")
    upper_id = dm.import_map(table.cid, upper, colour=BLUE)
    # Endpoints are set up through the editors' API; travel goes through the dialog.
    base = f"/api/campaigns/{table.cid}/transitions"
    arrival = dm.api("POST", base, {"map_id": upper_id, "name": "Arrival", "player_label": "Up", "kind": "stairs",
                                    "x": 40, "y": 40})["saved_endpoint_id"]
    dm.api("POST", base, {"map_id": table.mid, "name": "Stairs", "player_label": "Down", "kind": "stairs",
                          "x": 40, "y": 40, "destination_id": arrival, "arrival": "area"})
    dm.open_map(table.mid)
    dm.fog("reveal", 100)
    player.expect_pixels(table.map_name, [((150, 150), RED), ((300, 100), BLACK)])
    page = dm.page
    page.locator("#map-passages-panel > summary").click()
    page.locator("#transition-list button", has_text="Stairs").click()
    page.locator("#tr-travel").click()
    expect(page.locator("#tr-confirm")).to_have_text(f"Travel to {upper}")
    page.locator("#tr-confirm").click()
    page.wait_for_url(re.compile(rf"/maps/{upper_id}\b"))
    # Arrival reveals the destination's left room; the right room stays hidden.
    player.expect_pixels(upper, [((150, 150), BLUE), ((300, 100), BLACK)])


def test_player_reconnects_after_a_server_restart(table):
    table.dm.fog("reveal", 100)
    table.player.expect_pixels(table.map_name, [((100, 100), RED), ((300, 100), BLACK)])
    table.dm.page.goto("about:blank")              # no editor polling a stopped server
    table.server.stop()
    expect(table.player.page.locator("#conn-dot")).not_to_have_class(re.compile(r"\bon\b"))
    table.server.start()
    table.player.expect_live()                      # reconnects by itself (backoff at most 15 s)
    table.dm.open_map(table.mid)                    # sessions and fog survived the restart
    table.dm.fog("reveal", 300)
    table.player.expect_pixels(table.map_name, [((100, 100), RED), ((300, 100), RED)])


def test_backup_restore_round_trip_reaches_the_player(table, tmp_path):
    dm, player = table.dm, table.player
    dm.fog("reveal", 100)
    player.expect_pixels(table.map_name, [((100, 100), RED), ((300, 100), BLACK)])
    dm.page.goto(f"{table.server.admin}/campaigns/{table.cid}")
    dm.page.locator("#campaign-backup").evaluate("el => { el.open = true; }")
    with dm.page.expect_download() as pending:
        dm.page.get_by_role("button", name="Download campaign backup").click()
    backup = tmp_path / "campaign.zip"
    pending.value.save_as(backup)
    assert backup.stat().st_size > 0
    dm.open_map(table.mid)
    dm.fog("hide", 100)
    player.expect_pixels(table.map_name, [((100, 100), BLACK), ((300, 100), BLACK)])
    # Inspect, then restore the same file; the form asks for confirmation.
    dm.page.goto(f"{table.server.admin}/campaigns/{table.cid}")
    dm.page.locator("#campaign-backup").evaluate("el => { el.open = true; }")
    inspect = dm.page.locator(f'form[action="/campaigns/{table.cid}/restore/inspect"]')
    inspect.locator('input[name="backup"]').set_input_files(str(backup))
    inspect.locator('button[type="submit"]').click()
    expect(dm.page.locator("h1")).to_have_text("Compatible campaign backup")
    restore = dm.page.locator(f'form[action="/campaigns/{table.cid}/restore"]')
    restore.locator('input[name="backup"]').set_input_files(str(backup))
    restore.locator('input[name="confirm"]').fill(table.campaign)
    dm.page.once("dialog", lambda dialog: dialog.accept())
    restore.locator('button[type="submit"]').click()
    expect(dm.page.locator("h1")).to_have_text("Campaign restored")
    expect(dm.page.get_by_role("link", name="Download pre-restore recovery backup")).to_be_visible()
    # The restored fog (left room revealed) reaches the connected player.
    player.expect_pixels(table.map_name, [((100, 100), RED), ((300, 100), BLACK)])


def test_room_notes_are_saved_for_the_dm_and_never_sent_to_players(table):
    dm, player = table.dm, table.player
    secret = "A cursed altar hums"
    dm.page.locator("#room-select-mode").check()
    dm.click_map(100)
    form = dm.page.locator("#room-form")
    expect(form).to_be_visible()                    # unnamed rooms open straight into editing
    dm.page.locator("#room-name").fill("Crypt")
    dm.page.locator("#room-markdown").fill(f"## Altar\n\n{secret} with **dark** power.")
    form.get_by_role("button", name="Save room").click()
    expect(dm.page.locator("#room-read")).to_be_visible()
    expect(dm.page.locator("#room-title")).to_have_text("Crypt")
    expect(dm.page.locator("#room-preview strong")).to_have_text("dark")
    dm.page.locator("#room-select-mode").uncheck()
    dm.fog("reveal", 100)
    expect(dm.page.locator("#room-preview")).to_contain_text(secret)
    player.expect_pixels(table.map_name, [((100, 100), RED), ((300, 100), BLACK)])
    assert secret not in player.page.content()
    state = player.page.evaluate(f"fetch('/api/c/{table.cid}/state').then(r => r.text())")
    assert secret not in state and "Altar" not in state
    # Saved: after a reload the named room opens in read mode with its notes.
    dm.open_map(table.mid)
    dm.page.locator("#room-select-mode").check()
    dm.click_map(100)
    expect(dm.page.locator("#room-read")).to_be_visible()
    expect(dm.page.locator("#room-preview")).to_contain_text(secret)


def test_admin_role_manages_only_its_own_campaigns(server, actors):
    root = Admin(actors("superadmin"), server.admin)
    login(root.page, server.admin, "superadmin", "e2e-superadmin-password")
    private = unique("Private")
    private_id = root.create_campaign(private)
    name, password = unique("dm"), "admin-password-1"
    root.page.goto(f"{server.admin}/users")
    form = root.page.locator('form[action="/users"]')
    form.locator('input[name="username"]').fill(name)
    form.locator('input[name="password"]').fill(password)
    form.locator('select[name="role"]').select_option("admin")
    form.locator('input[name="must_change"]').uncheck()
    form.get_by_role("button", name="Create").click()
    expect(root.page.locator(".flash-ok")).to_be_visible()

    admin = Admin(actors("admin"), server.admin)
    login(admin.page, server.admin, name, password)
    expect(admin.page).not_to_have_url(re.compile(r"/login|/account"))
    expect(admin.page.locator('a[href="/users"]')).to_have_count(0)
    assert private not in admin.page.content()
    assert admin.page.goto(f"{server.admin}/users").status == 403
    assert admin.page.goto(f"{server.admin}/campaigns/{private_id}").status == 403
    own = unique("Own")
    own_id = admin.create_campaign(own)
    assert admin.page.goto(f"{server.admin}/campaigns/{own_id}").status == 200
    # The superadmin manages every campaign, including the admin's.
    assert root.page.goto(f"{server.admin}/campaigns/{own_id}").status == 200
    root.page.goto(f"{server.admin}/")
    expect(root.page.get_by_text(own)).to_be_visible()


def test_webp_player_image_with_default_feathering(webp_server, actors):
    table = Table(webp_server, actors, tolerance=16)
    table.dm.fog("reveal", 100)
    # Lossy WebP: compare colours within a tolerance at room centres, away from edges.
    table.player.expect_pixels(table.map_name, [((100, 100), RED), ((300, 100), BLACK)], tolerance=16)
    kind = table.player.page.evaluate("fetch(document.querySelector('#map').src).then(r => r.headers.get('content-type'))")
    assert kind.startswith("image/webp"), kind
