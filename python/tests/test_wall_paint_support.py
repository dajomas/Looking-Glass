"""Exercise screenshot-oracle rejection/retry logic without a browser."""
import copy
import importlib.util
import io
from pathlib import Path

import pytest
from PIL import Image, ImageDraw

spec = importlib.util.spec_from_file_location("wall_paint_support", Path(__file__).parent / "browser/wall_paint_support.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
painted_width = module.painted_width


def bitmap(width=10):
    image = Image.new("RGB", (100, 100), "black")
    if width:
        ImageDraw.Draw(image).rectangle((50-width//2, 0, 50-width//2+width-1, 99), fill=(255, 91, 209))
    output = io.BytesIO()
    image.save(output, "PNG")
    return output.getvalue()


class Page:
    def __init__(self, width=10, samples=None, screen_width=10):
        self.body = bitmap(width)
        self.calls = 0
        self.samples = samples
        self.base = dict(ready=True, node=1, revision=0, viewport=[100,100], strip=[35,65,50], screenWidth=screen_width)

    def evaluate(self, script, overlay):
        self.calls += 1
        return copy.deepcopy(self.samples(self.calls, self.base) if self.samples else self.base)

    def screenshot(self, **kwargs):
        assert kwargs["scale"] == "css"
        return self.body


def test_accepts_visible_correct_wall(tmp_path):
    assert painted_width(Page(), "#walls", expected=10, diagnostic_dir=tmp_path) == 10
    assert not list(tmp_path.iterdir())


@pytest.mark.parametrize("mode", ["zero", "wrong-css", "missing", "clipped", "unstable", "wrong-zoom", "viewport-size"])
def test_rejects_invalid_samples_and_retains_diagnostics(tmp_path, mode):
    page = Page(width=0 if mode == "zero" else 10, screen_width=4 if mode == "wrong-css" else 10)
    if mode in ("missing", "clipped"):
        page.base.update(ready=False, reason=mode)
    if mode == "unstable":
        page.samples = lambda n, b: dict(b, node=n)
    if mode == "viewport-size":
        page.base["viewport"] = [101,100]
    with pytest.raises(AssertionError, match="Wall paint did not converge"):
        painted_width(page, "#walls", expected=10, reference=7 if mode == "wrong-zoom" else None,
                      timeout=20, diagnostic_dir=tmp_path)
    assert len(list(tmp_path.glob("*.png"))) == 1
    assert len(list(tmp_path.glob("*.json"))) == 1


@pytest.mark.parametrize("field", ["node", "revision", "strip"])
def test_retries_changed_sample_then_accepts_fresh_pair(tmp_path, field):
    def samples(n, base):
        if field == "strip":
            return dict(base, strip=[34,64,50] if n == 1 else [35,65,50])
        return dict(base, **{field: 1 if n == 1 else 2})
    page = Page(samples=samples)
    assert painted_width(page, "#walls", expected=10, diagnostic_dir=tmp_path) == 10
    assert page.calls >= 4


def test_zero_cannot_pass_relative_zero_comparison(tmp_path):
    with pytest.raises(AssertionError):
        painted_width(Page(width=0), "#walls", expected=10, reference=0,
                      timeout=20, diagnostic_dir=tmp_path)


def test_native_growth_minimum_is_required(tmp_path):
    with pytest.raises(AssertionError):
        painted_width(Page(width=8, screen_width=8), "#walls", expected=8, minimum=9,
                      timeout=20, diagnostic_dir=tmp_path)
