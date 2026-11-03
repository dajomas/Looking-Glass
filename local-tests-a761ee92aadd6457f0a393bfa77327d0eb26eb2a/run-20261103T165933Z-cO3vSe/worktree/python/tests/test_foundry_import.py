import json

import pytest

from conftest import two_room_scene
from looking_glass.services.foundry_import import (WallImportError, classify_foundry_wall,
                                                   foundry_scene_origin, parse_wall_file)


def test_scene_export_with_padding():
    sets = parse_wall_file(json.dumps(two_room_scene()).encode(), "scene.json")
    assert len(sets) == 1
    ws = sets[0]
    assert ws.name == "Test scene"
    assert len(ws.segments) == 5
    assert (ws.origin_x, ws.origin_y) == (100, 100)   # ceil(400*.25/100)*100, ceil(200*.25/100)*100
    cal = ws.suggested_calibration(800, 400)           # image twice the scene size
    assert cal.scale_x == 2 and cal.scale_y == 2
    assert cal.apply(110, 110) == (20, 20)


def test_v9_grid_number_and_shift():
    scene = {"width": 1000, "height": 1000, "padding": 0.25, "grid": 50, "shiftX": 5, "shiftY": -5, "walls": []}
    assert foundry_scene_origin(scene) == (255, 245)


def test_classification():
    assert classify_foundry_wall({"move": 20, "sight": 20}) == ("wall", True)
    assert classify_foundry_wall({"move": 20, "sight": 20, "door": 1}) == ("door", True)
    assert classify_foundry_wall({"move": 20, "sight": 20, "door": 2}) == ("secret", True)
    assert classify_foundry_wall({"move": 20, "sight": 0}) == ("invisible", True)
    assert classify_foundry_wall({"move": 0, "sight": 0}) == ("ethereal", False)
    assert classify_foundry_wall({"move": 20, "sight": 10}) == ("window", True)
    assert classify_foundry_wall({"move": 1, "sense": 2}) == ("window", True)      # v9 limited
    assert classify_foundry_wall({"move": 1, "sense": 1}) == ("wall", True)        # v9 normal


def test_nedb_scenes_db_multiple_scenes():
    a = two_room_scene(); a["_id"] = "a"; a["name"] = "Cellar"
    b = two_room_scene(); b["_id"] = "b"; b["name"] = "Tower"
    old = dict(b, name="Old tower")
    raw = "\n".join(json.dumps(x) for x in (a, old, b)).encode()
    sets = parse_wall_file(raw, "scenes.db")
    assert sorted(s.name for s in sets) == ["Cellar", "Tower"]   # later line supersedes
    assert all(s.source_format == "foundry-nedb" for s in sets)


def test_nedb_walls_db():
    raw = "\n".join(json.dumps({"_id": str(i), "c": [0, i * 10, 100, i * 10]}) for i in range(1, 4)).encode()
    sets = parse_wall_file(raw, "walls.db")
    assert len(sets[0].segments) == 3


def test_plain_wall_list_and_zero_length_ignored():
    raw = json.dumps([{"c": [0, 0, 10, 0]}, {"c": [5, 5, 5, 5]}, {"nope": 1}]).encode()
    assert len(parse_wall_file(raw)[0].segments) == 1


def test_uvtt():
    data = {"format": 0.3, "resolution": {"map_origin": {"x": 0, "y": 0}, "map_size": {"x": 4, "y": 2},
                                          "pixels_per_grid": 100},
            "line_of_sight": [[{"x": 0, "y": 0}, {"x": 4, "y": 0}, {"x": 4, "y": 2}]],
            "portals": [{"bounds": [{"x": 2, "y": 0}, {"x": 2, "y": 1}]}]}
    ws = parse_wall_file(json.dumps(data).encode(), "map.dd2vtt")[0]
    assert ws.source_format == "uvtt"
    assert [s.kind for s in ws.segments] == ["wall", "wall", "door"]
    assert ws.segments[0].x2 == 400 and ws.scene_width == 400


def test_garbage():
    with pytest.raises(WallImportError):
        parse_wall_file(b"\x89PNG\r\n\x1a\n\x00\x00", "x.png")
    with pytest.raises(WallImportError):
        parse_wall_file(b'{"hello": 1}', "x.json")
