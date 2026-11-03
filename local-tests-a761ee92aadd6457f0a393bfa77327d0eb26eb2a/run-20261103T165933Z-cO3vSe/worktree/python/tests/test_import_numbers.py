"""Numeric importer regressions; structural validation remains separate."""
import copy
import io
import json
import math
import zipfile

import pytest

from looking_glass.services import foundry_import as fi
from looking_glass.services.wall_model import Calibration


WALL = {"_id": "w", "c": [0, 0, 10, 0]}
SCENE = {"walls": [WALL], "width": 100, "height": 100, "padding": 0, "grid": 100}
UVTT = {"resolution": {"pixels_per_grid": 70, "map_origin": {"x": 0, "y": 0},
                       "map_size": {"x": 2, "y": 2}},
        "line_of_sight": [[{"x": 0, "y": 0}, {"x": 1, "y": 0}]], "portals": []}
NONFINITE = [float("nan"), float("inf"), -float("inf"), "NaN", "Infinity", "-Infinity"]


def parse(data):
    return fi.parse_wall_file(json.dumps(data).encode(), "source.json")


def change(base, path, value):
    data = copy.deepcopy(base)
    p = data
    for key in path[:-1]:
        p = p[key]
    p[path[-1]] = value
    return data


def calibration(ws, width=400, height=200, **kwargs):
    if hasattr(fi, "validated_calibration"):
        return fi.validated_calibration(ws, width, height, **kwargs)
    return kwargs.get("calibration") or ws.suggested_calibration(width, height)


@pytest.mark.parametrize("coordinate", range(4))
@pytest.mark.parametrize("value", NONFINITE)
def test_nonfinite_foundry_coordinates_are_controlled(coordinate, value):
    with pytest.raises(fi.WallImportError):
        parse(change(WALL, ["c", coordinate], value))


def test_huge_integer_coordinate_is_controlled():
    with pytest.raises(fi.WallImportError):
        parse(change(WALL, ["c", 0], 10 ** 400))


@pytest.mark.parametrize("field", ["width", "height"])
@pytest.mark.parametrize("value", [0, -1, *NONFINITE])
def test_explicit_scene_dimensions_must_be_positive_and_finite(field, value):
    with pytest.raises(fi.WallImportError):
        parse(change(SCENE, [field], value))


@pytest.mark.parametrize("value", [0, -1, "bad", 10 ** 400, *NONFINITE])
@pytest.mark.parametrize("as_object", [False, True])
def test_grid_requires_positive_finite_value(value, as_object):
    with pytest.raises(fi.WallImportError):
        parse(change(SCENE, ["grid"], {"size": value} if as_object else value))


@pytest.mark.parametrize("field", ["offsetX", "offsetY"])
@pytest.mark.parametrize("value", NONFINITE)
def test_background_offsets_are_finite(field, value):
    with pytest.raises(fi.WallImportError):
        parse(dict(SCENE, background={field: value}))


@pytest.mark.parametrize("value", [-1, *NONFINITE])
def test_padding_must_be_nonnegative_and_finite(value):
    with pytest.raises(fi.WallImportError):
        parse(dict(SCENE, padding=value))


def test_foundry_padded_origin_overflow_is_controlled():
    with pytest.raises(fi.WallImportError):
        parse(dict(SCENE, width=1e308, padding=1e308))


@pytest.mark.parametrize("value", [0, -1, "bad", 10 ** 400, *NONFINITE])
def test_uvtt_grid_requires_positive_finite_value(value):
    with pytest.raises(fi.WallImportError):
        parse(change(UVTT, ["resolution", "pixels_per_grid"], value))


@pytest.mark.parametrize("field", ["x", "y"])
@pytest.mark.parametrize("value", [0, -1, *NONFINITE])
def test_uvtt_explicit_sizes_are_positive_and_finite(field, value):
    with pytest.raises(fi.WallImportError):
        parse(change(UVTT, ["resolution", "map_size", field], value))


@pytest.mark.parametrize("field", ["x", "y"])
@pytest.mark.parametrize("value", NONFINITE)
def test_uvtt_origins_are_finite(field, value):
    with pytest.raises(fi.WallImportError):
        parse(change(UVTT, ["resolution", "map_origin", field], value))


@pytest.mark.parametrize("field", ["x", "y"])
@pytest.mark.parametrize("value", NONFINITE)
def test_uvtt_points_are_finite(field, value):
    with pytest.raises(fi.WallImportError):
        parse(change(UVTT, ["line_of_sight", 0, 0, field], value))


@pytest.mark.parametrize("path,value", [
    (["line_of_sight", 0, 1, "x"], 1e308),
    (["resolution", "map_size", "x"], 1e308),
])
def test_finite_uvtt_input_cannot_overflow_output(path, value):
    with pytest.raises(fi.WallImportError):
        parse(change(UVTT, path, value))


def test_actual_target_scale_overflow_is_controlled():
    ws = parse(dict(SCENE, width=1e-307))[0]
    with pytest.raises(fi.WallImportError):
        calibration(ws)


@pytest.mark.parametrize("existing", [False, True])
def test_actual_target_wall_transform_overflow_is_controlled(existing):
    ws = parse(dict(SCENE, walls=[dict(WALL, c=[0, 0, 1e308, 0])]))[0]
    kwargs = {"calibration": Calibration(scale_x=4)} if existing else {}
    with pytest.raises(fi.WallImportError):
        calibration(ws, **kwargs)


@pytest.mark.parametrize("cal", [Calibration(scale_x=0), Calibration(scale_y=-1),
                                Calibration(offset_x=float("inf")), Calibration(scale_x=float("nan"))])
def test_existing_calibration_is_validated(cal):
    with pytest.raises(fi.WallImportError):
        calibration(parse(WALL)[0], calibration=cal)


@pytest.mark.parametrize("value", [0, -1, float("inf"), float("nan")])
def test_target_image_dimensions_are_validated(value):
    with pytest.raises(fi.WallImportError):
        calibration(parse(WALL)[0], width=value)


@pytest.mark.parametrize("data", [WALL, {"walls": [WALL]}, dict(SCENE, width=None, height=None, grid=None, padding=None),
                                 {"resolution": {}, "line_of_sight": UVTT["line_of_sight"]}])
def test_optional_metadata_defaults_are_supported(data):
    sets = parse(data)
    assert len(sets[0].segments) == 1
    cal = calibration(sets[0])
    assert all(math.isfinite(getattr(cal, k)) for k in ("offset_x", "offset_y", "scale_x", "scale_y"))


def test_negative_coordinates_offsets_and_numeric_strings_are_supported():
    data = dict(SCENE, width="100", height="100", grid={"size": "10"},
                background={"offsetX": "-5", "offsetY": "-10"},
                walls=[dict(WALL, c=["-20", "-10", "0", "0"])])
    ws = parse(data)[0]
    assert ws.origin_x == -5 and ws.origin_y == -10
    assert ws.segments[0].x1 == -20
    assert calibration(ws).scale_x == 4


def test_nedb_replay_is_preserved():
    docs = [dict(WALL, c=["NaN", 0, 10, 0]), {"_id": "w", "$$deleted": True}, dict(WALL, c=[0, 0, 20, 0])]
    ws = fi.parse_wall_file("\n".join(map(json.dumps, docs)).encode(), "walls.db")[0]
    assert ws.segments[0].x2 == 20


def test_live_invalid_nedb_coordinate_is_rejected():
    docs = [WALL, dict(WALL, c=["Infinity", 0, 10, 0])]
    with pytest.raises(fi.WallImportError):
        fi.parse_wall_file("\n".join(map(json.dumps, docs)).encode(), "walls.db")


@pytest.mark.parametrize("mixed", [False, True])
def test_zip_retains_its_entry_skip_policy(mixed):
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("invalid.json", json.dumps(dict(WALL, c=["NaN", 0, 10, 0])))
        if mixed:
            archive.writestr("valid.json", json.dumps(WALL))
    if mixed:
        sets = fi.parse_wall_file(buffer.getvalue(), "walls.zip")
        assert len(sets) == 1 and len(sets[0].segments) == 1
    else:
        with pytest.raises(fi.WallImportError, match="No supported wall sets"):
            fi.parse_wall_file(buffer.getvalue(), "walls.zip")


def test_zero_length_and_nonnumeric_wall_skip_policy_is_unchanged():
    ws = parse([WALL, {"c": [0, 0, 0, 0]}, {"c": ["bad", 0, 10, 0]}])[0]
    assert len(ws.segments) == 1

