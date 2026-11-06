"""Fractional/blended PNG coverage regressions for the controlled wall fixture."""
import copy
import importlib.util
import io
import json
from pathlib import Path
from types import SimpleNamespace

import pytest
from PIL import Image, ImageDraw

spec = importlib.util.spec_from_file_location("coverage_helper", Path(__file__).parent / "browser/wall_paint_support.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def blended(width=2, center=50.3, background=(90, 13, 13), blur=True,
            foreground=(255, 91, 209)):
    weights = [max(0., min(x + 1, center + width / 2) - max(x, center - width / 2)) for x in range(100)]
    if blur:
        weights = [.25 * (weights[x-1] if x else 0) + .5 * weights[x] +
                   .25 * (weights[x+1] if x < 99 else 0) for x in range(100)]
    image = Image.new("RGB", (100, 100), background)
    draw = ImageDraw.Draw(image)
    for x, weight in enumerate(weights):
        color = tuple(round(background[c] + weight * (foreground[c] - background[c])) for c in range(3))
        draw.line((x, 0, x, 99), fill=color)
    return image


class Page:
    def __init__(self, image, clock=None):
        output = io.BytesIO()
        image.save(output, "PNG")
        self.body = output.getvalue()
        self.clock = clock

    def evaluate(self, *args):
        return copy.deepcopy(dict(ready=True, node=1, revision=0, viewport=[100, 100],
                                  strip=[35, 65, 50], screenWidth=2))

    def screenshot(self, **kwargs):
        if self.clock is not None:
            self.clock.now = 2
        return self.body


@pytest.mark.parametrize("width", [2, 4, 10])
@pytest.mark.parametrize("center", [50.1, 50.3, 50.75])
@pytest.mark.parametrize("background", [(0, 0, 0), (90, 13, 13)])
@pytest.mark.parametrize("blur", [False, True])
def test_fractional_coverage_preserves_equivalent_width(width, center, background, blur):
    result = module.wall_coverage(blended(width, center, background, blur), (35, 65, 50))
    assert result["valid"], result
    assert result["width"] == pytest.approx(width, abs=.05)


def test_no_solid_magenta_pixels_can_still_be_a_two_pixel_wall(tmp_path):
    image = blended()
    solid = sum(1 for x in range(35, 66) if (lambda p: p[0] > 235 and 65 < p[1] < 130 and p[2] > 180)(image.getpixel((x, 50))))
    assert solid == 0
    width = module.painted_width(Page(image), "#walls", expected=2, diagnostic_dir=tmp_path)
    assert width == pytest.approx(2, abs=.05)
    assert not list(tmp_path.iterdir())


@pytest.mark.parametrize("mode", ["blank", "low-noise", "wrong-hue", "split", "displaced",
                                 "nonuniform-background", "speck", "too-wide", "inconsistent-rows"])
def test_invalid_paint_cannot_pass_css_alone(tmp_path, monkeypatch, mode):
    image = blended()
    draw = ImageDraw.Draw(image)
    if mode in ("blank", "low-noise", "split", "speck"):
        image = Image.new("RGB", (100, 100), (90, 13, 13))
        draw = ImageDraw.Draw(image)
    if mode == "low-noise":
        for x in range(100):
            draw.line((x, 0, x, 99), fill=(90 + x % 3, 13, 13))
    elif mode == "wrong-hue":
        image = blended(foreground=(46, 192, 255))
    elif mode == "split":
        for x in (48, 52):
            draw.line((x, 0, x, 99), fill=(255, 91, 209))
    elif mode == "displaced":
        image = blended(center=56)
    elif mode == "nonuniform-background":
        draw.rectangle((35, 0, 37, 99), fill=(0, 0, 0))
    elif mode == "speck":
        draw.point((50, 50), fill=(255, 91, 209))
    elif mode == "too-wide":
        image = blended(width=6)
    elif mode == "inconsistent-rows":
        wide = blended(width=4)
        image.paste(wide.crop((0, 48, 100, 49)), (0, 48))
    clock = SimpleNamespace(now=0.)
    monkeypatch.setattr(module, "time", SimpleNamespace(monotonic=lambda: clock.now))
    with pytest.raises(AssertionError, match="Wall paint did not converge"):
        module.painted_width(Page(image, clock), "#walls", expected=2, timeout=1000, diagnostic_dir=tmp_path)
    data = json.loads(next(tmp_path.glob("*.json")).read_text())
    assert not data["last_completed"]["credible"]
    assert "coverage" in data["saved_sample"]
    assert next(tmp_path.glob("*.png")).read_bytes() == Page(image).body


def test_sample_rows_must_fit_inside_image():
    assert not module.wall_coverage(blended(), (35, 65, 1))["valid"]
