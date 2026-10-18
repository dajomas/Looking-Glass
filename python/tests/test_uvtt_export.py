import pytest
from looking_glass.services.foundry_import import WallImportError, parse_wall_file
from looking_glass.services.uvtt_export import KINDS, encode_uvtt, export_uvtt, rows_for, validate_segments
from looking_glass.services.wall_model import WallSegment


@pytest.mark.parametrize("kind", KINDS)
def test_type_roundtrip(kind):
    seg = WallSegment(12.3456789, -5.75, 300.123, 45.25, kind, kind != "ethereal")
    ws = parse_wall_file(encode_uvtt(export_uvtt([seg], 400, 200, "A room", 137)), "walls.uvtt")[0]
    assert ws.name == "A room"
    assert (ws.scene_width, ws.scene_height) == pytest.approx((400, 200))
    assert (ws.segments[0].kind, ws.segments[0].blocks) == (kind, kind != "ethereal")
    assert rows_for(ws.segments)[0][:4] == pytest.approx(rows_for([seg])[0][:4])


def test_empty_roundtrip():
    ws = parse_wall_file(encode_uvtt(export_uvtt([], 400, 200, "Empty")))[0]
    assert ws.segments == []
    assert ws.suggested_calibration(400, 200).scale_x == 1


def test_standard_fallback():
    data = export_uvtt([WallSegment(0, i * 10, 100, i * 10, k, k != "ethereal") for i, k in enumerate(KINDS)], 400, 200, "Types")
    assert len(data["line_of_sight"]) == 3
    assert len(data["portals"]) == len(data["objects_line_of_sight"]) == 1
    del data["looking_glass"]
    ws = parse_wall_file(encode_uvtt(data))[0]
    assert len(ws.segments) == 5
    assert sum(w.kind == "door" for w in ws.segments) == 1


def test_nonblocking_roundtrip():
    data = export_uvtt([WallSegment(1, 2, 3, 4, "wall", False)], 100, 100, "Passive")
    assert not data["line_of_sight"]
    assert not parse_wall_file(encode_uvtt(data))[0].segments[0].blocks


@pytest.mark.parametrize("row", [
    [0, 0, 0, 0, "wall", True], [0, 0, 1, 1, "bogus", True],
    [0, 0, 1, 1, "ethereal", True], [0, 0, 1, 1, "wall", 1],
    [False, 0, 1, 1, "wall", True], ["0", 0, 1, 1, "wall", True],
    [0, 0, float("nan"), 1, "wall", True], [0, 0, float("inf"), 1, "wall", True],
    [0, 0, 1e8, 1, "wall", True], [0, 0, 10**500, 1, "wall", True], [0, 0, 1, 1, "wall"],
])
def test_invalid_segments(row):
    with pytest.raises(ValueError): validate_segments([row])


@pytest.mark.parametrize("ppg", [0, -1, float("nan"), float("inf")])
def test_bad_grid(ppg):
    with pytest.raises(ValueError): export_uvtt([], 400, 200, "Bad", ppg)


def test_stale_extension():
    data = export_uvtt([WallSegment(1, 2, 3, 4)], 100, 100, "Changed")
    data["line_of_sight"][0][0]["x"] = 0.5
    with pytest.raises(WallImportError, match="geometry changed"): parse_wall_file(encode_uvtt(data))
    del data["looking_glass"]
    assert len(parse_wall_file(encode_uvtt(data))[0].segments) == 1


def test_bad_extension_version():
    data = export_uvtt([], 100, 100, "Bad"); data["looking_glass"]["version"] = 999
    with pytest.raises(WallImportError, match="version"): parse_wall_file(encode_uvtt(data))


def test_embedded_image():
    assert parse_wall_file(encode_uvtt(export_uvtt([], 400, 200, "Image", image="aGVsbG8=")))[0].image_data == "aGVsbG8="


def test_calibration_baked_once():
    from looking_glass.services.wall_model import Calibration
    c = Calibration(100, 50, 2, 3)
    a, b = c.apply(110.123456, 60.123456); d, e = c.apply(150.123456, 90.123456)
    ws = parse_wall_file(encode_uvtt(export_uvtt([WallSegment(a, b, d, e)], 800, 600, "Calibrated")))[0]
    assert rows_for(ws.segments)[0][:4] == pytest.approx([a, b, d, e])
    assert ws.suggested_calibration(800, 600).scale_x == 1
