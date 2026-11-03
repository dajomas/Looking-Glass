"""Batch 1: actual browser -> HTTP -> database/hub -> viewer image updates."""


def test_live_reveal_keeps_adjacent_room_hidden(live_session):
    s = live_session
    before = s.player.locator("#map").get_attribute("src")
    s.gesture("reveal")
    s.expect_pixels("Red map", (200,30,30), (0,0,0))
    assert s.player.locator("#map").get_attribute("src") != before


def test_live_hide_and_undo_reach_player(live_session):
    s = live_session
    s.gesture("reveal")
    s.expect_pixels("Red map", (200,30,30), (0,0,0))
    s.gesture("hide")
    s.expect_pixels("Red map", (0,0,0), (0,0,0))
    s.undo()
    s.expect_pixels("Red map", (200,30,30), (0,0,0))


def test_live_map_switch_uses_destination_artwork_and_fog(live_session):
    s = live_session
    s.gesture("reveal")
    s.expect_pixels("Red map", (200,30,30), (0,0,0))
    s.open_editor(s.b)
    s.gesture("reveal", x=300)
    s.activate(s.b)
    s.expect_pixels("Green map", (0,0,0), (30,200,30))
    s.activate(s.a)
    s.expect_pixels("Red map", (200,30,30), (0,0,0))


def test_live_offline_preparation_does_not_publish(live_session):
    s = live_session
    s.gesture("reveal")
    s.expect_pixels("Red map", (200,30,30), (0,0,0))
    before = s.state()["map"]
    installed = s.player.locator("#map").get_attribute("src")
    s.open_editor(s.b)
    s.gesture("reveal", x=300)
    assert s.state()["map"] == before
    s.expect_pixels("Red map", (200,30,30), (0,0,0))
    assert s.player.locator("#map").get_attribute("src") == installed
    # Confirm the preparation was saved and becomes visible only on activation.
    s.activate(s.b)
    s.expect_pixels("Green map", (0,0,0), (30,200,30))
