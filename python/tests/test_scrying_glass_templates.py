from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]

def test_admin_only_and_script_order():
    html=(ROOT/"web_html/admin/map_editor.html").read_text()
    assert html.index("scrying_glass_room.js") < html.index("room_notes.js")
    assert 'id="scrying-room-check"' not in html
    assert 'aria-live="polite" hidden></p>' in html
    assert 'href="/static/css/scrying_glass.css?v=scrying-prefix-3"' in html
    assert 'src="/static/js/scrying_glass_room.js?v=scrying-prefix-3"' in html
    app=(ROOT/"python/looking_glass/web/app_factory.py").read_text()
    assert "admin_scrying_glass.router" in app.split("def create_admin_app",1)[1].split("def create_viewer_app",1)[0]
    assert "admin_scrying_glass.router" not in app.split("def create_viewer_app",1)[1]
    for path in (ROOT/"web_html/viewer").rglob("*.html"):
        assert "scrying-room" not in path.read_text()

def test_both_routes_are_csrf_and_ownership_protected():
    source=(ROOT/"python/looking_glass/web/admin/scrying_glass.py").read_text()
    for route in ('@router.post("/access")','@router.post("/check")'):
        block=source.split(route,1)[1].split('@router.',1)[0]
        assert 'user: CsrfUserDep' in block and 'map_for_manage(conn, user, map_id)' in block
