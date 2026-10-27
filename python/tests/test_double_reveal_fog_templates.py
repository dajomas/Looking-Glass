from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]

def test_admin_assets_and_viewer_exclusion():
    html = (ROOT / "web_html/admin/map_editor.html").read_text()
    assert 'id="double-fog-markers" aria-hidden="true" hidden' in html
    assert 'id="double-fog-legend"' in html
    assert html.index("double_reveal_markers.js") < html.index("double_reveal.js") < html.index("admin_map_editor.js")
    for path in (ROOT / "web_html/viewer").rglob("*.html"):
        assert "double-fog-markers" not in path.read_text()
        assert "double_reveal_markers.js" not in path.read_text()

def test_checkbox_wrapping_and_removed_description():
    html = (ROOT / "templates/partials/_double_reveal.html").read_text()
    assert 'for="double-select"' in html
    assert 'id="double-done" type="button"' in html
    assert "double-mode-status" not in html
    css = (ROOT / "static/css/admin.css").read_text()
    rule = css.split("#double-reveal-panel .check {", 1)[1].split("}", 1)[0]
    assert "white-space:normal" in rule and "min-width:0" in rule
    assert "pointer-events:none" in css.split("#double-fog-markers {", 1)[1].split("}", 1)[0]
