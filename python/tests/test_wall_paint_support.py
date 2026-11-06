"""Exercise screenshot-oracle rejection/retry logic without a browser."""
import copy
import importlib.util
import io
import json
from pathlib import Path
from types import SimpleNamespace

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


@pytest.fixture
def clock(monkeypatch):
    value = SimpleNamespace(now=0.0)
    monkeypatch.setattr(module, "time", SimpleNamespace(monotonic=lambda: value.now))
    return value


def diagnostic(tmp_path):
    return json.loads(next(tmp_path.glob("*.json")).read_text())


@pytest.mark.parametrize("failure", ["screenshot", "after-probe"])
def test_completed_rejection_survives_later_failure(tmp_path, clock, failure):
    class FailingPage(Page):
        shots = 0
        def evaluate(self, script, overlay):
            self.calls += 1
            if failure == "after-probe" and self.calls == 4:
                clock.now = 2
                raise RuntimeError("probe failed after newer screenshot")
            return dict(self.base, node=1 if self.calls <= 2 else 2)
        def screenshot(self, **kwargs):
            self.shots += 1
            assert kwargs["timeout"] > 0
            if self.shots == 2:
                if failure == "screenshot":
                    clock.now = 2
                    raise TimeoutError("waiting for fonts")
                return bitmap(4)
            return self.body
    page = FailingPage(width=0)
    with pytest.raises(AssertionError):
        painted_width(page, "#walls", expected=10, timeout=1000, diagnostic_dir=tmp_path)
    result = diagnostic(tmp_path)
    assert result["last_completed"]["painted_width"] == 0
    assert result["saved_sample"]["before"]["node"] == 1
    assert result["saved_sample"]["after"]["node"] == 1
    assert result["capture_source"] == "last_completed"
    assert result["latest_error"]["before"]["node"] == 2
    assert result["latest_error"]["phase"] == ("screenshot" if failure == "screenshot" else "probe-after")
    assert next(tmp_path.glob("*.png")).read_bytes() == bitmap(0)
    assert len(result["history"]) == 2
    assert page.shots == 2


def test_budget_exhausted_during_probe_starts_no_capture(tmp_path, clock):
    class SlowProbe(Page):
        shots = 0
        def evaluate(self, *args):
            clock.now = 2
            return self.base
        def screenshot(self, **kwargs):
            self.shots += 1
            raise AssertionError("capture must not start")
    page = SlowProbe()
    with pytest.raises(AssertionError):
        painted_width(page, "#walls", expected=10, timeout=1000, diagnostic_dir=tmp_path)
    result = diagnostic(tmp_path)
    assert page.shots == 0
    assert result["latest_attempt"]["reason"] == "budget exhausted before capture"
    assert result["screenshot"] is None and result["saved_sample"] is None
    assert not list(tmp_path.glob("*.png"))


def test_attempt_history_is_bounded(tmp_path, clock):
    class ManyCaptures(Page):
        def screenshot(self, **kwargs):
            clock.now += .01
            return self.body
    with pytest.raises(AssertionError):
        painted_width(ManyCaptures(width=0), "#walls", expected=10, timeout=1000, diagnostic_dir=tmp_path)
    result = diagnostic(tmp_path)
    assert result["attempts"] > 8
    assert len(result["history"]) == 8
    assert result["last_completed"]["painted_width"] == 0


def test_png_write_failure_still_writes_json(tmp_path, clock, monkeypatch):
    def cannot_write_png(path, data):
        raise OSError("PNG storage failure")
    monkeypatch.setattr(Path, "write_bytes", cannot_write_png)
    class OneCapture(Page):
        def screenshot(self, **kwargs):
            clock.now = 2
            return self.body
    with pytest.raises(AssertionError):
        painted_width(OneCapture(width=0), "#walls", expected=10, timeout=1000, diagnostic_dir=tmp_path)
    result = diagnostic(tmp_path)
    assert result["last_completed"]["painted_width"] == 0
    assert result["screenshot"] is None
    assert "PNG storage failure" in result["diagnostic_errors"][0]
