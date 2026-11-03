"""Shared HTTP imports work with either pytest conftest bound by name."""
import importlib.util
import io
from pathlib import Path
import sys

from PIL import Image
import pytest

import looking_glass_test_helpers as helpers


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize("selected", ["root", "browser"])
def test_http_module_import_with_either_conftest(monkeypatch, selected):
    tests = Path(__file__).resolve().parent
    monkeypatch.syspath_prepend(str(tests.parent))
    root = load_module("_lg_root_conftest", tests / "conftest.py")
    browser = load_module("_lg_browser_conftest", tests / "browser/conftest.py")
    for module in (root, browser):
        assert module.png_bytes is helpers.png_bytes
        assert module.two_room_scene is helpers.two_room_scene
    monkeypatch.setitem(sys.modules, "conftest", root if selected == "root" else browser)
    web = load_module("_lg_http_import_regression", tests / "test_web.py")
    assert web.png_bytes is helpers.png_bytes
    assert web.two_room_scene is helpers.two_room_scene
    assert callable(web.env)


def test_shared_builders_preserve_image_and_scene_contract():
    with Image.open(io.BytesIO(helpers.png_bytes())) as image:
        image.load()
        assert image.format == "PNG" and image.size == (400, 200)
        assert image.getpixel((100, 50)) == (200, 30, 30)
    scene = helpers.two_room_scene()
    assert scene["width"] == 400 and scene["height"] == 200
    assert len(scene["walls"]) == 5
    assert scene["walls"][-1]["c"] == [300.0, 110.0, 300.0, 290.0]
    doors = helpers.two_room_scene(door=True)["walls"]
    assert len(doors) == 7 and sum(wall.get("door", 0) == 1 for wall in doors) == 1
