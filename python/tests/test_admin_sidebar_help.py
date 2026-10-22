"""Render the real sidebar and check disclosure structure without browser dependencies."""
from html.parser import HTMLParser
from pathlib import Path
from types import SimpleNamespace
import pytest
from jinja2 import Environment, FileSystemLoader

ROOT = Path(__file__).resolve().parents[2]

class Elements(HTMLParser):
    def __init__(self, html):
        super().__init__()
        self.by_id = {}
        self.details = []
        self.feed(html)
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if "id" in attrs:
            self.by_id[attrs["id"]] = attrs
        if tag == "details":
            self.details.append(attrs)

def render(count):
    env = Environment(loader=FileSystemLoader([str(ROOT / "web_html/admin"), str(ROOT / "templates")]))
    html = env.get_template("map_editor.html").render(
        map=SimpleNamespace(id=1, name="Map", wall_count=0, walls_source="none"),
        campaign=SimpleNamespace(id=1, name="Campaign"),
        siblings=[SimpleNamespace(id=i+1, name=f"Map {i+1}") for i in range(count)],
        fog_opacity=0.5, op_count=0,
    )
    return html, Elements(html)

@pytest.mark.parametrize("count", [1, 2, 3])
def test_passage_visibility_and_binding_targets(count):
    html, page = render(count)
    assert ("hidden" in page.by_id["map-passages-section"]) == (count == 1)
    assert ("help-passages" in page.by_id) == (count > 1)
    for target in ["transition-add", "transition-reset", "transition-status",
                   "transition-viewer-markers", "transition-viewer-labels"]:
        assert target in page.by_id

@pytest.mark.parametrize("count, expected", [(1, 7), (2, 8)])
def test_every_help_disclosure_starts_closed_and_independent(count, expected):
    _, page = render(count)
    main = [d for d in page.details if d.get("class") == "help-topic"]
    nested = [d for d in page.details if d.get("class") == "help-subtopic"]
    assert len(main) == expected
    assert len(nested) == 5
    for d in [page.by_id["editor-help"], *main, *nested]:
        assert "open" not in d
        assert "name" not in d
    assert page.by_id["editor-help"]["class"] == "sidebar-panel editor-help"

def test_reviewed_wording_and_live_status_preserved():
    html, page = render(2)
    for text in ["The offset is subtracted before scaling", "not door locking or unlocking",
                 "It does not change the fog boundaries", "Travel is a separate DM action",
                 "Selecting a source or wall set does not apply it", "arbitrary SQLite",
                 "Choose an image file, then select Upload"]:
        assert text in html
    for target in ["offline-reveal-warning", "source-status", "portal-cycle-status", "op-count"]:
        assert target in page.by_id
    template = (ROOT / "web_html/admin/map_editor.html").read_text()
    assert "400 ms" not in template
    assert "partials/_admin_sidebar_help.html" in template

def test_saved_subsections_are_nested_in_saved_topic():
    env = Environment(loader=FileSystemLoader(str(ROOT / "templates")))
    html = env.get_template("partials/_admin_sidebar_help.html").render(siblings=[1, 2])
    start = html.index('id="help-saved"')
    end = html.index('id="help-image"')
    saved = html[start:end]
    assert saved.count('class="help-subtopic"') == 5
    for key in ["sources", "apply", "changes", "reuse", "formats"]:
        assert f'id="help-saved-{key}"' in saved
