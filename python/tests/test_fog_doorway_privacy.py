"""Bug 30: a revealed room must not show hidden-side artwork across a door line."""
import numpy as np
import pytest
from PIL import Image

from looking_glass.config import DEFAULTS
from looking_glass.services.fog import FogEngine, MapSpec
from looking_glass.services.wall_model import Calibration, FogOp, WallSegment

W, H, X = 300, 210, 150.0  # vertical wall at x=150: left room revealed, right room hidden
HIDDEN = (0, 255, 0)       # hidden-side artwork; must never appear on the player image


def _scene(tmp_path, kind, image_format, feather, work):
    fog = dict(DEFAULTS["fog"], work_max_dim=work, feather_px=feather, wall_thickness=3)
    viewer = dict(DEFAULTS["viewer"], max_image_dim=W, image_format=image_format, image_quality=85)
    engine = FogEngine(fog, viewer, tmp_path / "cache")
    art = np.zeros((H, W, 3), np.uint8)
    art[:, :int(X)] = (200, 40, 40)
    art[:, int(X):] = HIDDEN       # hidden-side artwork starts exactly at the line
    image = tmp_path / "map.png"
    Image.fromarray(art).save(image)
    spec = MapSpec(1, W, H, image, Calibration(), True, 1, 1,
                   door_arrows_enabled=False, viewer_door_arrows_enabled=False)
    walls = [WallSegment(X, 0, X, 80), WallSegment(X, 80, X, 130, kind), WallSegment(X, 130, X, H - 1)]
    return engine, spec, walls


@pytest.mark.parametrize("image_format", ["png", "jpeg", "webp"])
@pytest.mark.parametrize("feather", [0, 2, 8])
@pytest.mark.parametrize("work", [300, 205, 97])    # 1:1 and non-integer work-to-map scales
@pytest.mark.parametrize("kind", ["door", "wall"])
def test_hidden_side_of_door_and_wall_lines_stays_fogged(tmp_path, image_format, feather, work, kind):
    engine, spec, walls = _scene(tmp_path, kind, image_format, feather, work)
    with Image.open(engine.viewer_image(spec, walls, [FogOp("reveal", W / 4, H / 2)])) as src:
        out = np.asarray(src.convert("RGB")).astype(int)
    assert out.shape[:2] == (H, W)
    hidden_side = out[:, int(X):]
    tolerance = 0 if image_format == "png" else 24      # lossy codecs may ring near edges
    assert hidden_side[..., 1].max() <= tolerance, (
        f"hidden artwork visible: green up to {hidden_side[..., 1].max()} at "
        f"x={int(X) + int(np.argmax(hidden_side[..., 1].max(axis=0)))}")
    # The revealed room itself stays visible right up to its side of the line.
    assert out[H // 2, int(X) - 6, 0] > 120


def test_revealing_both_sides_shows_the_line_and_hiding_one_keeps_privacy(tmp_path):
    engine, spec, walls = _scene(tmp_path, "door", "png", 0, 300)
    both = [FogOp("reveal", W / 4, H / 2), FogOp("reveal", W * 0.75, H / 2)]
    with Image.open(engine.viewer_image(spec, walls, both)) as src:
        out = np.asarray(src.convert("RGB")).astype(int)
    assert (out[:, int(X) - 3:int(X) + 3].sum(axis=2) > 0).all(), "a wall between two revealed rooms is shown"
    mask = engine.mask(spec, walls, [FogOp("reveal", W * 0.75, H / 2)])
    left = engine.label_at(engine.area_map(spec, walls), W / 4, H / 2)
    assert not mask[engine.area_map(spec, walls).labels == left].any()
