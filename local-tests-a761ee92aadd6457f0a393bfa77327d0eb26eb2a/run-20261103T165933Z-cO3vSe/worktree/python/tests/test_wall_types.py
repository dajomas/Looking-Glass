import json
import sqlite3

from conftest import two_room_scene, png_bytes
from looking_glass.config import DEFAULTS
from looking_glass.db import Database, MIGRATIONS
from looking_glass.services.fog import FogEngine, MapSpec
from looking_glass.services.foundry_import import parse_wall_file
from looking_glass.services.images import store_map_image
from looking_glass.services.wall_model import FogOp, WallSegment
from looking_glass.services.wall_types import WALL_TYPES, filter_segments
from PIL import Image
import numpy as np


def test_upgrade_v2_preserves_map(tmp_path):
    db = Database(tmp_path / "old.db")
    conn = sqlite3.connect(db.path)
    conn.executescript(MIGRATIONS[0] + MIGRATIONS[1])
    conn.executescript("CREATE TABLE schema_version(version INTEGER); INSERT INTO schema_version VALUES(2);"
                       "INSERT INTO campaigns(id,name) VALUES(1,'Existing');"
                       "INSERT INTO maps(campaign_id,name,image_file,width,height) VALUES(1,'Map','a.png',10,10);")
    conn.close()
    assert db.migrate() == len(MIGRATIONS) and db.migrate() == len(MIGRATIONS)
    with db.connect() as conn:
        row = conn.execute("SELECT * FROM maps").fetchone()
        from looking_glass.services.wall_type_settings import disabled_for_map
        assert row["image_file"] == "a.png" and disabled_for_map(conn,row) == []


def test_filters_non_destructive_all_types():
    walls = [WallSegment(0,0,10,0,kind,kind != "ethereal") for kind in WALL_TYPES]
    filtered = filter_segments(walls, list(WALL_TYPES))
    assert not any(w.blocks for w in filtered)
    assert all(w.blocks for w in walls if w.kind != "ethereal")
    assert filter_segments(walls, []) == walls


def test_disabled_wall_merges_rooms(tmp_path):
    engine = FogEngine(dict(DEFAULTS["fog"], work_max_dim=400, feather_px=0),
                       dict(DEFAULTS["viewer"], image_format="png"), tmp_path / "cache")
    ws = parse_wall_file(json.dumps(two_room_scene()).encode())[0]
    cal = ws.suggested_calibration(400,200)
    before = engine.build_area_map(400,200,ws.segments,cal,True)
    after = engine.build_area_map(400,200,filter_segments(ws.segments,["wall"]),cal,True)
    assert engine.label_at(before,100,100) != engine.label_at(before,300,100)
    assert engine.label_at(after,100,100) == engine.label_at(after,300,100)


def test_admin_base_matches_fully_revealed_viewer(tmp_path):
    stored = store_map_image(png_bytes(400,200,(10,120,230)),tmp_path / "maps",1)
    path = tmp_path / "maps" / stored.relative_path
    engine = FogEngine(dict(DEFAULTS["fog"], work_max_dim=400, feather_px=0),
                       dict(DEFAULTS["viewer"], image_format="png"), tmp_path / "cache")
    ws = parse_wall_file(json.dumps(two_room_scene()).encode())[0]
    spec = MapSpec(1,400,200,path,ws.suggested_calibration(400,200),True,1,1)
    output = engine.viewer_image(spec, ws.segments, [FogOp("reveal_all")])
    with Image.open(path) as admin, Image.open(output) as viewer:
        assert np.array_equal(np.asarray(admin.convert("RGB")),np.asarray(viewer.convert("RGB")))


def test_each_type_can_be_disabled_independently():
    walls = [WallSegment(0,0,10,0,k,k != "ethereal") for k in WALL_TYPES]
    for kind in WALL_TYPES:
        result = filter_segments(walls, [kind])
        assert result[WALL_TYPES.index(kind)].blocks is False
        for before, after in zip(walls, result):
            if before.kind != kind:
                assert before == after
