"""Chromium regressions with real fetch/redirects and mocked HTTP endpoints.
Run: python -m pytest -q python/tests/browser/test_campaign_batch_import.py
Requires pytest, Jinja2, Playwright and installed Chromium; no app server.
"""
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Thread
from email.parser import BytesParser
from email.policy import default
from pathlib import Path
import re
from urllib.parse import urlparse

import pytest
from jinja2 import Environment

pw = pytest.importorskip("playwright.sync_api")
ROOT = Path(__file__).resolve().parents[3]
SCENES = [{"index": 8, "name": "Tower", "walls": 30},
          {"index": 5, "name": "Room 10", "walls": 20},
          {"index": 2, "name": "Room 2", "walls": 10}]




def upload(name, data=b"test"):
    return {"name": name, "mimeType": "application/octet-stream", "buffer": data}


@pytest.fixture
def app(browser):
    page = browser.new_page()
    page.on("dialog", lambda dialog: dialog.accept())
    state = {"uploads": [], "source_uploads": [], "applied": [], "next_id": 101,
             "sources": [{"id": 7, "filename": "saved.db", "scene_count": 3}],
             "fail_apply": set(), "fail_inspect": False, "errors": [], "initial_maps": [{"id": 1, "name": "Existing"}]}
    page.on("pageerror", lambda error: state["errors"].append(str(error)))
    template = (ROOT / "web_html/admin/_campaign_batch_import.html").read_text()
    def html():
        panel = Environment().from_string(template).render(campaign={"id": 4}, maps=state["initial_maps"])
        return '<!doctype html><meta name="csrf-token" content="test-token">' + panel + '<script src="/static/js/api.js"></script><script src="/static/js/campaign_batch_import.js"></script>'
    def route(r):
        req = r.request; path = urlparse(req.url).path
        def reply(data, status=200):
            r.fulfill(status=status, content_type="application/json", body=json.dumps(data))
        if path.startswith("/static/js/"):
            r.fulfill(content_type="application/javascript", body=(ROOT / path.lstrip("/")).read_text()); return
        if req.method == "POST":
            assert req.headers.get("x-csrf-token") == "test-token"
        if path == "/campaigns/4":
            r.fulfill(content_type="text/html", body=html()); return
        if path == "/campaigns/4/maps":
            msg = BytesParser(policy=default).parsebytes(b"Content-Type: " + req.headers["content-type"].encode() + b"\r\n\r\n" + req.post_data_buffer)
            parts = {p.get_param("name", header="content-disposition"): p for p in msg.iter_parts()}
            assert "walls" not in parts
            assert parts["csrf_token"].get_content() == "test-token"
            name = parts["image"].get_filename(); state["uploads"].append(name)
            if name.startswith("bad"):
                r.fulfill(status=303, headers={"Location": "/campaigns/4?err=Invalid+image"}); return
            mid = state["next_id"]; state["next_id"] += 1
            if name.startswith("editor-error"): state["editor_error_id"] = mid
            r.fulfill(status=303, headers={"Location": f"/maps/{mid}?ok=Imported"}); return
        if re.fullmatch(r"/maps/\d+", path):
            code = 500 if path == f"/maps/{state.get('editor_error_id')}" else 200
            r.fulfill(status=code, content_type="text/html", body="Editor"); return
        if path == "/api/campaigns/4/wall-sources":
            if req.method == "GET": reply({"ok": True, "sources": state["sources"]}); return
            msg = BytesParser(policy=default).parsebytes(b"Content-Type: " + req.headers["content-type"].encode() + b"\r\n\r\n" + req.post_data_buffer)
            name = next(msg.iter_parts()).get_filename(); state["source_uploads"].append(name)
            if name.startswith("bad"): reply({"ok": False, "error": "Invalid wall file"}, 400); return
            sid = 8 + len(state["source_uploads"])
            state["sources"].append({"id": sid, "filename": name, "scene_count": 3})
            reply({"ok": True, "source": {"id": sid}}); return
        if re.fullmatch(r"/api/maps/\d+/wall-sources/\d+", path):
            if state["fail_inspect"]: reply({"ok": False, "error": "Source unavailable"}, 400); return
            reply({"ok": True, "scenes": SCENES}); return
        if re.fullmatch(r"/api/maps/\d+/walls/from-source", path):
            mid = int(path.split("/")[3]); body = req.post_data_json
            state["applied"].append((mid, body))
            if mid in state["fail_apply"]: reply({"ok": False, "error": "Apply failed"}, 400); return
            scene = next(item for item in SCENES if item["index"] == body["scene_index"])
            reply({"ok": True, "imported": scene["walls"], "scene": scene["name"]}); return
        raise AssertionError(f"Unexpected request: {req.method} {path}")
    # Playwright routes only intercept the first URL in a redirect chain.
    # Serve redirect destinations locally so Chromium follows real HTTP 303s.
    class LandingHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            path = urlparse(self.path).path
            code = 500 if path == f"/maps/{state.get('editor_error_id')}" else 200
            body = html() if path == "/campaigns/4" else "Editor"
            self.send_response(code)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers(); self.wfile.write(body.encode())
        def log_message(self, *args):
            pass
    server = ThreadingHTTPServer(("127.0.0.1", 0), LandingHandler)
    thread = Thread(target=server.serve_forever, daemon=True); thread.start()
    try:
        page.route("**/*", route)
        page.goto(f"http://127.0.0.1:{server.server_port}/campaigns/4")
        pw.expect(page.locator("#campaign-batch-import")).to_have_attribute("aria-busy", "false")
        pw.expect(page.locator('#batch-assignment-rows select').nth(0)).to_be_enabled()
        pw.expect(page.locator('#batch-assignment-rows select').nth(0).locator('option[value="7"]')).to_have_count(1)
        pw.expect(page.locator("#batch-status")).to_be_empty()
        yield page, state
        assert state["errors"] == []
    finally:
        try:
            page.close()
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)


def row(page, mid):
    return page.locator(f'#batch-assignment-rows tr[data-map-id="{mid}"]')


def choose(page, mid, source="7", index="2"):
    r = row(page, mid)
    r.locator("select").nth(0).select_option(source)
    pw.expect(r.locator("select").nth(1)).to_be_enabled()
    r.locator("select").nth(1).select_option(index)


def test_import_multiple_maps_and_separate_wall_files(app):
    page, state = app
    page.set_input_files("#batch-map-files", [upload("a.png"), upload("b.jpg")])
    page.set_input_files("#batch-wall-files", [upload("a.uvtt"), upload("walls.db")])
    page.click('#batch-upload button[type="submit"]')
    pw.expect(page.locator("#batch-status")).to_contain_text("2 maps, 2 wall sources imported; 0 failed")
    assert state["uploads"] == ["a.png", "b.jpg"]
    assert state["source_uploads"] == ["a.uvtt", "walls.db"]
    assert page.locator("#batch-assignment-rows tr").count() == 3
    assert state["applied"] == []
    assert page.locator("#batch-map-files").input_value() == ""


def test_same_source_supplies_different_sets_to_existing_maps(app):
    page, state = app
    page.set_input_files("#batch-map-files", [upload("b.png")])
    page.click('#batch-upload button[type="submit"]')
    pw.expect(page.locator("#batch-status")).to_contain_text("1 maps, 0 wall sources imported; 0 failed")
    choose(page, 1, index="5"); choose(page, 101, index="2")
    row(page, 101).locator('input[type="checkbox"]').uncheck()
    page.click("#batch-apply-walls")
    pw.expect(page.locator("#batch-status")).to_contain_text("2 applied, 0 failed")
    assert state["applied"] == [(1, {"source_id": 7, "scene_index": 5, "use_scene_calibration": True, "use_pack_image": False}),
                                (101, {"source_id": 7, "scene_index": 2, "use_scene_calibration": False, "use_pack_image": False})]
    pw.expect(page.locator("#batch-apply-walls")).to_be_disabled()


def test_import_sources_only_and_assign_newly_uploaded_source(app):
    page, state = app
    page.set_input_files("#batch-wall-files", [upload("new.dd2vtt")])
    page.click('#batch-upload button[type="submit"]')
    pw.expect(page.locator("#batch-status")).to_contain_text("0 maps, 1 wall sources imported; 0 failed")
    assert state["uploads"] == []
    choose(page, 1, source="9", index="8")
    page.click("#batch-apply-walls")
    pw.expect(page.locator("#batch-status")).to_contain_text("1 applied")
    assert state["applied"][0][1]["source_id"] == 9


def test_partial_upload_failures_keep_successes(app):
    page, state = app
    page.set_input_files("#batch-map-files", [upload("bad.png"), upload("good.png")])
    page.set_input_files("#batch-wall-files", [upload("bad.db"), upload("good.uvtt")])
    page.click('#batch-upload button[type="submit"]')
    pw.expect(page.locator("#batch-status")).to_contain_text("1 maps, 1 wall sources imported; 2 failed")
    assert page.locator("#batch-assignment-rows tr").count() == 2
    assert state["uploads"] == ["bad.png", "good.png"]
    assert state["source_uploads"] == ["bad.db", "good.uvtt"]
    assert page.locator("#batch-import-results").count() == 0


def test_sorted_sets_keep_original_import_indices(app):
    page, state = app
    choose(page, 1, index="5")
    values = row(page, 1).locator("select").nth(1).locator("option").evaluate_all("els => els.map(e => e.value)")
    assert values == ["", "2", "5", "8"]
    page.click("#batch-apply-walls")
    pw.expect(page.locator("#batch-status")).to_contain_text("1 applied")
    assert state["applied"][0][1]["scene_index"] == 5


def test_source_change_clears_selection_and_inspect_failure_is_retryable(app):
    page, state = app
    choose(page, 1)
    r = row(page, 1)
    r.locator("select").nth(0).select_option("")
    pw.expect(page.locator("#batch-apply-walls")).to_be_disabled()
    state["fail_inspect"] = True
    r.locator("select").nth(0).select_option("7")
    pw.expect(page.locator("#batch-status")).to_have_text("Source unavailable")
    pw.expect(r.locator("select").nth(0)).to_be_enabled()
    pw.expect(page.locator("#batch-apply-walls")).to_be_disabled()
    state["fail_inspect"] = False
    r.locator("select").nth(0).select_option("")
    choose(page, 1)


def test_failed_assignment_retains_selection_for_retry(app):
    page, state = app
    state["fail_apply"].add(1); choose(page, 1)
    page.click("#batch-apply-walls")
    pw.expect(page.locator("#batch-status")).to_contain_text("0 applied, 1 failed")
    assert row(page, 1).locator("select").nth(1).input_value() == "2"
    state["fail_apply"].clear(); page.click("#batch-apply-walls")
    pw.expect(page.locator("#batch-status")).to_contain_text("1 applied, 0 failed")


def test_map_created_before_editor_failure_is_not_reported_as_failed_upload(app):
    page, state = app
    page.set_input_files("#batch-map-files", upload("editor-error.png"))
    page.click('#batch-upload button[type="submit"]')
    pw.expect(page.locator("#batch-status")).to_contain_text("1 maps, 0 wall sources imported; 0 failed, 1 editor warnings")
    assert state["uploads"] == ["editor-error.png"]
    assert page.locator("#batch-import-results").count() == 0
    assert page.locator("#batch-assignment-rows tr").count() == 2


def test_empty_upload_is_noop_and_apply_does_not_confirm(app):
    page, state = app
    page.click('#batch-upload button[type="submit"]')
    pw.expect(page.locator("#batch-status")).to_contain_text("Choose map images")
    choose(page, 1)
    page.evaluate("window.confirmCalls = 0; window.confirm = () => { window.confirmCalls++; return false; }")
    page.click("#batch-apply-walls")
    pw.expect(page.locator("#batch-status")).to_contain_text("1 applied, 0 failed")
    assert len(state["applied"]) == 1
    assert page.evaluate("window.confirmCalls") == 0


def test_labels_expose_uvtt_and_original_single_import_remains():
    campaign = (ROOT / "web_html/admin/campaign.html").read_text()
    editor = (ROOT / "web_html/admin/map_editor.html").read_text()
    assert "UVTT (Universal VTT) walls (optional)" in campaign
    assert 'name="image" accept="image/*" required' in campaign
    assert 'name="walls"' in campaign
    assert "UVTT (Universal VTT) file" in editor
    assert "UVTT (Universal VTT) source" in editor
