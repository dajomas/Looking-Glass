"""Real viewer reconnect and multi-tab/session convergence regressions."""
import copy
from contextlib import ExitStack
import re

import pytest
from playwright.sync_api import expect


def test_live_reconnect_fetches_changes_missed_while_offline(live_session):
    s = live_session
    s.player.add_init_script("""(() => {
      const Native = window.WebSocket;
      window.__lgTestSockets = [];
      window.WebSocket = class extends Native {
        constructor(...args) {super(...args); window.__lgTestSockets.push(this);}
      };
    })();""")
    s.player.reload()
    s.expect_pixels("Red map", (0,0,0), (0,0,0))
    context = s.player.context
    try:
        context.set_offline(True)
        s.player.evaluate("window.__lgTestSockets.forEach(socket => socket.close())")
        expect(s.player.locator("#conn-dot")).not_to_have_class(re.compile(r"\bon\b"), timeout=10000)
        s.gesture("reveal")
    finally:
        context.set_offline(False)
    s.expect_pixels("Red map", (200,30,30), (0,0,0))


@pytest.mark.parametrize("independent_session", [False, True], ids=["shared-session-tabs", "independent-sessions"])
def test_live_other_viewer_survives_one_tab_closing(live_session, live_browser, independent_session):
    s = live_session
    with ExitStack() as stack:
        context = stack.enter_context(live_browser.new_context()) if independent_session else s.player.context
        page = context.new_page()
        try:
            other = copy.copy(s)
            other.player = page
            page.on("pageerror", lambda error: s.page_errors.append(f"extra-player: {error}"))
            if independent_session:
                s.login(page, s.viewer_url, "live-player", "live-player-password")
            page.goto(f"{s.viewer_url}/c/{s.cid}")
            other.expect_pixels("Red map", (0,0,0), (0,0,0))
            s.gesture("reveal")
            s.expect_pixels("Red map", (200,30,30), (0,0,0))
            other.expect_pixels("Red map", (200,30,30), (0,0,0))
            s.player.close()
            s.gesture("hide")
            other.expect_pixels("Red map", (0,0,0), (0,0,0))
            s.undo()
            other.expect_pixels("Red map", (200,30,30), (0,0,0))
        finally:
            page.close()
