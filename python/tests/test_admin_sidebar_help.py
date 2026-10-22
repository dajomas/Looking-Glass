"""Regression coverage for the fog-editor sidebar rendering."""
from pathlib import Path
from types import SimpleNamespace

import pytest
from jinja2 import Environment, FileSystemLoader
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[2]


def render_sidebar(count):
    env = Environment(loader=FileSystemLoader([str(ROOT / "web_html/admin"), str(ROOT / "templates")]))
    html = env.get_template("map_editor.html").render(
        map=SimpleNamespace(id=1, name="Map", wall_count=0, walls_source="none"),
        campaign=SimpleNamespace(id=1, name="Campaign"),
        siblings=[SimpleNamespace(id=i+1, name=f"Map {i+1}") for i in range(count)],
        fog_opacity=0.5, op_count=0,
    )
    return BeautifulSoup(html, "html.parser")


@pytest.mark.parametrize("count, hidden", [(1, True), (2, False), (3, False)])
def test_passages_visibility(count, hidden):
    page = render_sidebar(count)
    section = page.select_one("#map-passages-section")
    assert section.has_attr("hidden") is hidden
    assert section.select_one("#transition-add") is not None
    assert ("Map passages" in page.select_one("#editor-help").get_text()) is (not hidden)


def test_help_is_collapsed_and_independent_of_controls():
    page = render_sidebar(2)
    help_panel = page.select_one("#sidebar #editor-help")
    assert not help_panel.has_attr("open")
    assert not help_panel.has_attr("name")
    assert help_panel.select_one("summary")["aria-label"] == "Help for the map editor"
    for text in ["400 ms", "Show hides only", "Auto-align for this map", "LevelDB", "Delete source"]:
        assert text in help_panel.get_text()
    assert "400 ms" not in page.select_one("#fog-panel").get_text()
    assert page.select_one("#fog-panel #offline-reveal-warning") is not None
    assert page.select_one("#saved-wall-library #source-status") is not None
    assert page.select_one("#saved-wall-library #source-apply") is not None
