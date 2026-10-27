from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]

def test_admin_only_and_script_order():
    html=(ROOT/"web_html/admin/map_editor.html").read_text()
    assert html.index("scrying_glass_room.js") < html.index("room_notes.js")
    assert 'id="scrying-room-check" type="button" disabled' in html
    app=(ROOT/"python/looking_glass/web/app_factory.py").read_text()
    assert "admin_scrying_glass.router" in app.split("def create_admin_app",1)[1].split("def create_viewer_app",1)[0]
    assert "admin_scrying_glass.router" not in app.split("def create_viewer_app",1)[1]
    for path in (ROOT/"web_html/viewer").rglob("*.html"):
        assert "scrying-room" not in path.read_text()
