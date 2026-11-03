from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]

def test_success_panel_assets_are_admin_only():
    html=(ROOT/"web_html/admin/map_editor.html").read_text()
    assert 'id="scrying-room-results"' in html and 'aria-atomic="true" hidden' in html
    assert 'scrying_glass.css?v=scrying-prefix-3' in html
    assert 'scrying_glass_room.js?v=scrying-prefix-3' in html
    assert 'id="scrying-room-check"' not in html
    assert 'id="double-fog-markers"' in html
    for path in (ROOT/"web_html/viewer").rglob("*.html"):
        assert "scrying-room-results" not in path.read_text()

def test_transport_cache_gate_preserved_and_prefix_is_on_room_path():
    source=(ROOT/"python/looking_glass/services/scrying_glass_access.py").read_text()
    assert 'expand_matches(sg.match_catalog(payload, campaign_name, room_name), payload)' in source
    assert 'if not gate["verified"]' in source
    assert 'SUCCESS_TTL = 60' in source and 'FAILURE_TTL = 30' in source
    js=(ROOT/"static/js/scrying_glass_room.js").read_text()
    assert 'this.cache.set(key,{until,result})' in js
    assert 'innerHTML' not in js
    css=(ROOT/"static/css/scrying_glass.css").read_text()
    assert '[hidden]' in css and 'overflow-wrap:anywhere' in css
