"""Focused CSS source and default-theme contrast regression checks."""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CSS = (ROOT / "static/css/admin.css").read_text()
MARKER = "/* Lighter help surfaces, scoped so operational controls retain their theme. */"

def luminance(color):
    rgb = [int(color[i:i+2], 16) / 255 for i in (1, 3, 5)]
    rgb = [c / 12.92 if c <= .04045 else ((c + .055) / 1.055) ** 2.4 for c in rgb]
    return sum(c * w for c, w in zip(rgb, (.2126, .7152, .0722)))

def test_help_backgrounds_are_progressively_lighter():
    backgrounds = ["#1a202c", "#263143", "#303e53", "#3a4a61", "#435570"]
    values = [luminance(c) for c in backgrounds]
    assert values == sorted(values)
    for color in backgrounds[1:]:
        assert color in CSS.split(MARKER)[1]

def test_new_rules_are_scoped_to_help_only():
    new = CSS.split(MARKER)[1]
    rules = re.findall(r"([^{}]+)\{([^{}]*)\}", new)
    assert len(rules) == 6
    for selectors, _ in rules:
        assert all(s.strip().startswith("#editor-help") for s in selectors.split(","))
    assert "display:" not in new
    assert "content:" not in new

def test_text_and_focus_contrast():
    text = luminance("#e6e2d6")
    accent = luminance("#d8b25a")
    for bg in ["#263143", "#303e53", "#3a4a61", "#435570"]:
        lum = luminance(bg)
        assert (text + .05) / (lum + .05) >= 4.5
        assert (accent + .05) / (lum + .05) >= 3
    assert "outline: 2px solid var(--accent)" in CSS.split(MARKER)[1]
