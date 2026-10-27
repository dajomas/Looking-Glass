"""Guard shared vector paint policy without launching Chromium."""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_editor_stage_does_not_force_bitmap_promotion():
    css = (ROOT / "static/css/admin.css").read_text()
    rules = re.findall(r"\.stage\s*\{([^}]+)\}", css)
    assert rules
    for rule in rules:
        assert "will-change" not in rule
        assert "translateZ" not in rule
    assert "transform-origin: 0 0" in " ".join(rules)


def test_both_editors_share_stage_paint_policy():
    for name in ("map_editor.html", "wall_editor.html"):
        template = (ROOT / "web_html/admin" / name).read_text()
        assert "css/admin.css" in template
        assert 'class="stage"' in template
