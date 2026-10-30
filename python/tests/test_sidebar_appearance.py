from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


class Structure(HTMLParser):
    def __init__(self, text):
        super().__init__()
        self.stack = []
        self.nodes = {}
        self.feed(text)
        assert not self.stack

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if "id" in attrs:
            assert attrs["id"] not in self.nodes
            self.nodes[attrs["id"]] = (tag, attrs, list(self.stack))
        if tag not in {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}:
            self.stack.append((tag, attrs.get("id")))

    def handle_endtag(self, tag):
        assert self.stack and self.stack[-1][0] == tag, (tag, self.stack)
        self.stack.pop()


def test_battle_panels_and_control_ancestry():
    page = Structure((ROOT / "web_html/admin/map_editor.html").read_text())
    for ident in ("players-panel", "fog-panel", "map-passages-panel", "walls-panel", "saved-wall-library", "replace-map-panel"):
        tag, attrs, _ = page.nodes[ident]
        assert tag == "details" and "open" not in attrs
        assert attrs["name"] == "fog-editor-panels"
    assert "open" in page.nodes["wall-legend"][1]
    assert "name" not in page.nodes["wall-legend"][1]
    text=(ROOT / "web_html/admin/map_editor.html").read_text()
    assert text.index('id="map-passages-panel"') < text.index('id="walls-panel"')
    for ident, panel in (("btn-show", "players-panel"), ("fog-opacity", "fog-panel"), ("wall-width", "walls-panel"), ("calibration", "walls-panel"), ("apply-wall-types", "wall-legend")):
        assert ("details", panel) in page.nodes[ident][2]
    assert ("details", "walls-panel") in page.nodes["calibration"][2]
    for ident in ("saved-wall-library", "wall-legend"):
        assert not any(tag == "details" for tag, _ in page.nodes[ident][2])
    assert "open" not in page.nodes["calibration"][1]


def test_wall_editor_save_panel_below_tools():
    page = Structure((ROOT / "web_html/admin/wall_editor.html").read_text())
    tag, attrs, _ = page.nodes["wall-save-export"]
    assert tag == "details" and "open" in attrs
    for ident in ("pixels-per-grid", "wall-save", "include-image", "wall-download", "wall-reload"):
        assert ("details", "wall-save-export") in page.nodes[ident][2]
    assert ("details", "wall-save-export") not in page.nodes["wall-tool"][2]
    assert ("details", "wall-save-export") not in page.nodes["wall-width"][2]


def test_width_defaults_and_script_order():
    for name, script in (("map_editor.html", "admin_map_editor.js"), ("wall_editor.html", "admin_wall_editor.js")):
        text = (ROOT / "web_html/admin" / name).read_text()
        attrs = Structure(text).nodes["wall-width"][1]
        assert (attrs["min"], attrs["max"], attrs["step"], attrs["value"]) == ("0.5", "10", "0.5", "2")
        assert text.index("wall_appearance.js") < text.index(script)


def test_viewer_port_preserved():
    from looking_glass.config import DEFAULTS
    assert DEFAULTS["server"]["viewer_port"] == 5100
    # Check operational sections rather than the split guide's navigation index.
    text = "".join((ROOT / "docs/deployment" / section).read_text(encoding="utf-8")
                   for section in ("002-1-native-installation-rhel-rocky.md",
                                   "003-2-systemd-service.md",
                                   "004-3-networking.md",
                                   "005-4-podman-deployment.md"))
    assert "systemd service" in text and "viewer_port: 5100" in text
    assert "6000" not in text
