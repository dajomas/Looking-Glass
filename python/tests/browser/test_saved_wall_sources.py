"""Browser regressions for saved-source selection; no application server required.

Run from the repository root:
  python -m pytest -q python/tests/browser/test_saved_wall_sources.py
Requires pytest, playwright, and an installed Playwright Chromium browser.
"""
import json
import os
from pathlib import Path
import re

import pytest

playwright = pytest.importorskip("playwright.sync_api")
ROOT = Path(__file__).resolve().parents[3]
SCRIPT = Path(os.environ.get("LG_WALL_LIBRARY_SCRIPT", ROOT / "static/js/wall_source_library.js"))

PANEL = """<details open id="saved-wall-library">
<form id="source-save"><input id="source-file" type="file" required><button>Save source</button></form>
<select id="saved-source" disabled></select><select id="saved-scene" disabled></select>
<p id="saved-scene-info"></p><input id="saved-auto-align" type="checkbox" checked>
<button id="source-apply" disabled>Apply</button><button id="source-refresh">Refresh</button>
<button id="source-delete" disabled>Delete</button><p id="source-status"></p>
</details>"""
PACK = """<label id="pack-image-choice" hidden><input id="saved-pack-image" type="checkbox">Image</label>
<p id="pack-image-info"></p>"""
SCENES = [{"name": name, "index": index, "walls": index + 10, "doors": 1,
           "scene_width": 400, "scene_height": 200,
           "calibration": {"offset_x": 0, "offset_y": 0, "scale_x": 1, "scale_y": 1},
           "image_available": True} for name, index in
          [("Tower", 8), ("Room 10", 3), ("alpha", 4), ("Room 2", 5), ("Alpha", 2)]]




@pytest.fixture
def page(browser):
    page = browser.new_page()
    page.set_default_timeout(2000)
    yield page
    page.close()


def boot(page, pack=False, scenes=None, partial=False):
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    extra = PACK if pack else '<input id="saved-pack-image" type="checkbox">' if partial else ""
    page.set_content(PANEL.replace("</details>", extra + "</details>"))
    page.evaluate("""(scenes) => {
      window.LG_MAP = {id: 11, campaign_id: 4};
      window.scenes = scenes; window.rejectInspect = false; window.rejectList = false;
      window.savedSources = [{id: 7, filename: 'maps.db', scene_count: scenes.length}];
      window.calls = []; window.confirm = () => true;
      window.LGApi = {
        get: async url => {
          if (/wall-sources$/.test(url)) {
            if (window.rejectList) throw new Error('List unavailable');
            return {sources: window.savedSources};
          }
          if (window.rejectInspect) throw new Error('Inspection unavailable');
          return {scenes: window.scenes};
        },
        post: async (url, body) => {
          if (/from-source$/.test(url)) {
            window.calls.push({url, body});
            return new Promise(() => {}); // stop before reload; inspect submitted payload
          }
          window.savedSources.push({id: 9, filename: 'new.db', scene_count: scenes.length});
          return {source: {id: 9}};
        },
        del: async url => {window.savedSources = []; return {ok: true};}
      };
    }""", SCENES if scenes is None else scenes)
    page.add_script_tag(path=str(SCRIPT))
    return errors


def select_source(page, source="7"):
    playwright.expect(page.locator("#saved-source")).to_be_enabled()
    page.select_option("#saved-source", source)
    playwright.expect(page.locator("#saved-scene")).to_be_enabled()


def test_initializes_without_optional_pack_controls(page):
    errors = boot(page)
    playwright.expect(page.locator("#saved-source")).to_be_enabled()
    assert errors == []
    playwright.expect(page.locator("#source-apply")).to_be_disabled()
    select_source(page)
    page.select_option("#saved-scene", "5")
    playwright.expect(page.locator("#source-apply")).to_be_enabled()
    assert "scale 1.0000" in page.locator("#saved-scene-info").inner_text()
    assert errors == []


def test_alphabetical_natural_order_preserves_original_indices(page):
    boot(page); select_source(page)
    assert page.locator("#saved-scene option").evaluate_all("els => els.map(e => e.value)") == ["", "2", "4", "5", "3", "8"]
    page.select_option("#saved-scene", "3")
    page.click("#source-apply")
    playwright.expect(page.locator("#source-status")).to_have_text("Working...")
    body = page.evaluate("window.calls[0].body")
    assert body == {"source_id": 7, "scene_index": 3, "use_scene_calibration": True, "use_pack_image": False}


def test_changing_source_clears_previous_wall_selection(page):
    boot(page)
    page.evaluate("window.savedSources.push({id: 9, filename: 'other.db', scene_count: 5})")
    page.click("#source-refresh")
    select_source(page)
    page.select_option("#saved-scene", "5")
    page.select_option("#saved-source", "9")
    playwright.expect(page.locator("#saved-scene")).to_be_enabled()
    assert page.locator("#saved-scene").input_value() == ""
    playwright.expect(page.locator("#source-apply")).to_be_disabled()


def test_inspection_error_recovers_and_cannot_apply_stale_walls(page):
    boot(page); select_source(page)
    page.select_option("#saved-scene", "5")
    page.evaluate("window.rejectInspect = true")
    page.select_option("#saved-source", "")
    page.select_option("#saved-source", "7")
    playwright.expect(page.locator("#source-status")).to_have_text("Inspection unavailable")
    playwright.expect(page.locator("#saved-source")).to_be_enabled()
    playwright.expect(page.locator("#source-apply")).to_be_disabled()
    page.evaluate("window.rejectInspect = false")
    page.select_option("#saved-source", "")
    select_source(page)


def test_save_selects_new_source_without_optional_controls(page):
    boot(page)
    page.set_input_files("#source-file", {"name": "new.db", "mimeType": "text/plain", "buffer": b"test"})
    page.click("#source-save button")
    playwright.expect(page.locator("#saved-scene")).to_be_enabled()
    assert page.locator("#saved-source").input_value() == "9"
    assert page.locator("#saved-scene").input_value() == ""


def test_optional_pack_controls_remain_opt_in_and_reset_on_selection(page):
    boot(page, pack=True); select_source(page)
    page.select_option("#saved-scene", "5")
    playwright.expect(page.locator("#pack-image-choice")).to_be_visible()
    page.check("#saved-pack-image")
    page.select_option("#saved-scene", "3")
    assert not page.is_checked("#saved-pack-image")
    page.check("#saved-pack-image")
    page.click("#source-apply")
    assert page.evaluate("window.calls[0].body.use_pack_image") is True


def test_partial_pack_controls_do_not_block_wall_selection(page):
    errors = boot(page, partial=True); select_source(page)
    page.select_option("#saved-scene", "5")
    playwright.expect(page.locator("#source-apply")).to_be_enabled()
    playwright.expect(page.locator("#saved-pack-image")).to_be_disabled()
    assert errors == []


def test_no_wall_sets_cannot_be_applied(page):
    boot(page, scenes=[])
    playwright.expect(page.locator("#saved-source")).to_be_enabled()
    page.select_option("#saved-source", "7")
    playwright.expect(page.locator("#source-status")).to_contain_text("No wall sets found")
    playwright.expect(page.locator("#saved-scene")).to_be_disabled()
    playwright.expect(page.locator("#source-apply")).to_be_disabled()


def test_untrusted_names_are_option_text_not_html(page):
    item = dict(SCENES[0], name='<img src=x onerror="window.injected=true">', index=99)
    errors = boot(page, scenes=[item]); select_source(page)
    assert page.locator("#saved-scene option").nth(1).text_content().startswith("<img")
    assert page.locator("#saved-scene img").count() == 0
    assert page.evaluate("window.injected === true") is False
    assert errors == []


def test_delete_leaves_empty_library_usable_for_another_upload(page):
    boot(page); select_source(page)
    page.click("#source-delete")
    playwright.expect(page.locator("#source-status")).to_have_text("No saved sources yet.")
    playwright.expect(page.locator("#saved-source")).to_be_disabled()
    playwright.expect(page.locator("#source-file")).to_be_enabled()
