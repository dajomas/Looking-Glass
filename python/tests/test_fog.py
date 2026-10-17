import numpy as np
import pytest
from PIL import Image

from conftest import two_room_scene
from looking_glass.config import DEFAULTS
from looking_glass.services.fog import FogEngine, MapSpec
from looking_glass.services.foundry_import import parse_wall_file
from looking_glass.services.wall_model import FogOp
import json


@pytest.fixture
def engine(tmp_path):
    fog = dict(DEFAULTS["fog"], work_max_dim=400, feather_px=0)
    return FogEngine(fog, dict(DEFAULTS["viewer"], image_format="png"), tmp_path / "cache")


def _setup(tmp_path, door=False, doors_block=True):
    ws = parse_wall_file(json.dumps(two_room_scene(door=door)).encode(), "s.json")[0]
    img = tmp_path / "map.png"
    Image.new("RGB", (400, 200), (250, 0, 0)).save(img)
    spec = MapSpec(1, 400, 200, img, ws.suggested_calibration(400, 200), doors_block, 1, 1)
    return spec, ws.segments


def test_click_reveals_only_that_room(engine, tmp_path):
    spec, segs = _setup(tmp_path)
    m = engine.mask(spec, segs, [FogOp("reveal", 100, 100)])
    assert m[100, 100] and m[100, 50]
    assert not m[100, 300]            # other room stays fogged
    assert not m[5, 5]                # outside the building stays fogged
    assert m[10, 100]                 # bounding wall itself becomes visible


def test_hide_and_reveal_all(engine, tmp_path):
    spec, segs = _setup(tmp_path)
    ops = [FogOp("reveal", 100, 100), FogOp("reveal", 300, 100), FogOp("hide", 100, 100)]
    m = engine.mask(spec, segs, ops)
    assert not m[100, 100] and m[100, 300]
    spec.fog_version = 2
    assert engine.mask(spec, segs, ops + [FogOp("reveal_all")]).all()
    spec.fog_version = 3
    assert not engine.mask(spec, segs, ops + [FogOp("reveal_all"), FogOp("hide_all")]).any()


def test_doors_toggle(engine, tmp_path):
    spec, segs = _setup(tmp_path, door=True, doors_block=True)
    assert not engine.mask(spec, segs, [FogOp("reveal", 100, 100)])[100, 300]
    spec2, _ = _setup(tmp_path, door=True, doors_block=False)
    spec2.id, spec2.walls_version = 2, 5
    assert engine.mask(spec2, segs, [FogOp("reveal", 100, 100)])[100, 300]   # door open -> one area


def test_click_on_wall_snaps_to_nearest_area(engine, tmp_path):
    spec, segs = _setup(tmp_path)
    area = engine.area_map(spec, segs)
    assert engine.label_at(area, 199, 100) != 0


def test_leak_warning_without_walls(engine, tmp_path):
    spec, _ = _setup(tmp_path)
    area = engine.area_map(spec, [])
    res = engine.describe_click(area, 10, 10)
    assert res.fraction == pytest.approx(1.0) and res.leak_warning


def test_viewer_image_hides_unrevealed_pixels(engine, tmp_path):
    spec, segs = _setup(tmp_path)
    path = engine.viewer_image(spec, segs, [FogOp("reveal", 100, 100)])
    arr = np.asarray(Image.open(path).convert("RGB"))
    assert tuple(arr[100, 100]) == (250, 0, 0)     # revealed: map colour
    assert tuple(arr[100, 300]) == (0, 0, 0)       # fogged: pure fog colour, nothing leaks
    spec.fog_version = 9
    path2 = engine.viewer_image(spec, segs, [])
    assert not np.asarray(Image.open(path2).convert("RGB")).any()
    assert not path.exists()                       # stale cache cleaned
