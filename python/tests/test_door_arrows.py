from dataclasses import replace
import io
import numpy as np
import pytest
from PIL import Image
from test_fog import engine, _setup
from looking_glass.services.wall_model import FogOp, Calibration
from looking_glass.db import Database


@pytest.mark.parametrize("x, direction", [(100, -1), (300, 1)])
def test_arrow_on_revealed_side_only(engine, tmp_path, x, direction):
    spec, segs = _setup(tmp_path, door=True)
    ops = [FogOp("reveal", x, 100)]
    arr = np.array(engine.door_arrow_overlay(spec, segs, ops))
    ys, xs = np.nonzero(arr[:, :, 3])
    assert len(xs)
    assert np.all((xs - 200) * direction > 0)
    area = engine.area_map(spec, segs)
    assert set(area.labels[ys, xs]) == engine.revealed_labels(area, ops)
    assert tuple(arr[ys[0], xs[0], :3]) == (70, 192, 255)
    # Shaft is farther from the door than the broad arrow head.
    tip_x = xs.max() if direction == -1 else xs.min()
    assert abs(tip_x - 200) < abs(xs.mean() - 200)


@pytest.mark.parametrize("ops", [[], [FogOp("reveal_all")], [FogOp("hide_all")],
    [FogOp("reveal", 100, 100), FogOp("reveal", 300, 100)],
    [FogOp("reveal", 100, 100), FogOp("hide", 100, 100)]])
def test_no_arrow_without_revealed_hidden_boundary(engine, tmp_path, ops):
    spec, segs = _setup(tmp_path, door=True)
    assert not np.array(engine.door_arrow_overlay(spec, segs, ops))[:, :, 3].any()


@pytest.mark.parametrize("kind, blocks, doors_block", [("secret", True, True),
    ("door", False, True), ("door", True, False), ("wall", True, True)])
def test_excluded_doors(engine, tmp_path, kind, blocks, doors_block):
    spec, segs = _setup(tmp_path, door=True, doors_block=doors_block)
    segs = [replace(s, kind=kind, blocks=blocks) if s.kind == "door" else s for s in segs]
    assert not np.array(engine.door_arrow_overlay(spec, segs, [FogOp("reveal", 100, 100)]))[:, :, 3].any()


def test_color_cache_viewer_and_admin_match(engine, tmp_path):
    spec, segs = _setup(tmp_path, door=True)
    ops = [FogOp("reveal", 100, 100)]
    old = engine.viewer_image(spec, segs, ops)
    custom = replace(spec, door_arrow_color="#00ff00")
    overlay = np.array(Image.open(io.BytesIO(engine.door_arrows_png(custom, segs, ops))))
    visible = overlay[:, :, 3] > 0
    path = engine.viewer_image(custom, segs, ops)
    assert path != old
    viewer = np.array(Image.open(path))
    assert np.all(viewer[visible] == [0, 255, 0])
    assert np.all(viewer[100, 300] == 0)


def test_calibrated_and_downscaled(engine, tmp_path):
    spec, segs = _setup(tmp_path, door=True)
    shifted = []
    for s in segs:
        x1, y1 = spec.calibration.apply(s.x1, s.y1)
        x2, y2 = spec.calibration.apply(s.x2, s.y2)
        shifted.append(replace(s, x1=x1 * 2 + 20, x2=x2 * 2 + 20,
                               y1=y1 * 2 + 30, y2=y2 * 2 + 30))
    calibrated = replace(spec, calibration=Calibration(20, 30, .5, .5))
    ops = [FogOp("reveal", 100, 100)]
    expected = np.array(engine.door_arrow_overlay(spec, segs, ops))
    assert np.array_equal(expected, np.array(engine.door_arrow_overlay(calibrated, shifted, ops)))
    engine.work_max_dim = 200
    engine.invalidate(spec.id)
    arr = np.array(engine.door_arrow_overlay(calibrated, shifted, ops))
    assert arr.shape == (100, 200, 4) and arr[:, :, 3].any()


def test_migration_is_idempotent(tmp_path):
    db = Database(tmp_path / "test.sqlite")
    assert db.migrate() == db.migrate() == 5
    with db.connect() as conn:
        columns = {row["name"]: row for row in conn.execute("PRAGMA table_info(maps)")}
        assert columns["door_arrow_color"]["dflt_value"] == "'#46c0ff'"


def test_upgrade_preserves_existing_fog(tmp_path):
    from looking_glass.db import MIGRATIONS
    db = Database(tmp_path / "upgrade.sqlite")
    with db.connect() as conn:
        conn.executescript("".join(MIGRATIONS[:4]))
        conn.executescript("CREATE TABLE schema_version(version INTEGER); INSERT INTO schema_version VALUES(4);")
        conn.execute("INSERT INTO campaigns(id,name) VALUES(1,'Campaign')")
        conn.execute("INSERT INTO maps(id,campaign_id,name,image_file,width,height) VALUES(1,1,'Map','a.png',400,200)")
        conn.execute("INSERT INTO fog_ops(map_id,op,x,y) VALUES(1,'reveal',100,100)")
        before = dict(conn.execute("SELECT * FROM maps").fetchone())
    assert db.migrate() == 5
    with db.connect() as conn:
        after = dict(conn.execute("SELECT * FROM maps").fetchone())
        assert after.pop("door_arrow_color") == "#46c0ff"
        assert after == before
        assert conn.execute("SELECT count(*) FROM fog_ops").fetchone()[0] == 1
