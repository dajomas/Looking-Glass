"""Bug 12 parser-boundary regressions; no HTTP or database fixtures.

Run from a normal checkout:
    PYTHONPATH=python python -m unittest discover -s python/tests -p test_import_shapes.py
"""
import io
import json
import unittest
from unittest.mock import patch
import zipfile

from looking_glass.services import foundry_import as fi
from looking_glass.services import uvtt_export as uv
from looking_glass.services.wall_model import WallSegment


def encode(data):
    return json.dumps(data).encode()


def good_scene():
    return {"name": "Kept", "walls": [{"c": [0, 0, 10, 10]}]}


def make_pack(entries):
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w") as archive:
        for name, content in entries:
            archive.writestr(name, content)
    return stream.getvalue()


MALFORMED = {
    "door_string": {"walls": [{"c": [0, 0, 10, 10], "door": "bad"}]},
    "door_list": {"walls": [{"c": [0, 0, 10, 10], "door": [1]}]},
    "door_object": {"walls": [{"c": [0, 0, 10, 10], "door": {"x": 1}}]},
    "door_infinity": {"walls": [{"c": [0, 0, 10, 10], "door": float("inf")}]},
    "walls_number": {"walls": 7},
    "resolution_string": {"resolution": "bad", "line_of_sight": []},
    "origin_list": {"resolution": {"map_origin": [1]}, "line_of_sight": []},
    "size_number": {"resolution": {"map_size": 2}, "line_of_sight": []},
    "los_number": {"resolution": {}, "line_of_sight": 4},
    "polyline_number": {"resolution": {}, "line_of_sight": [4]},
    "object_los_number": {"resolution": {}, "objects_line_of_sight": 4},
    "portals_number": {"resolution": {}, "portals": 4},
    "null_portal": {"resolution": {}, "portals": [None]},
    "bounds_number": {"resolution": {}, "portals": [{"bounds": 2}]},
    "null_endpoint": {"resolution": {}, "portals": [{"bounds": [None, {"x": 1, "y": 1}]}]},
    "missing_endpoint_y": {"resolution": {}, "portals": [{"bounds": [{"x": 0}, {"x": 1, "y": 1}]}]},
}


class ImportShapeTests(unittest.TestCase):
    def assert_import_error(self, raw, message=None):
        try:
            fi.parse_wall_file(raw, "input.json")
        except fi.WallImportError as exc:
            if message:
                self.assertIn(message, str(exc))
            return
        except Exception as exc:
            self.fail(f"Expected WallImportError; got {type(exc).__name__}: {exc}")
        self.fail("Expected WallImportError; input was accepted")

    def test_valid_standard_uvtt(self):
        data = {"resolution": {"pixels_per_grid": 100},
                "line_of_sight": [[{"x": 0, "y": 0}, {"x": 2, "y": 1}]],
                "portals": [{"bounds": [{"x": 1, "y": 0}, {"x": 1, "y": 1}]}]}
        ws = fi.parse_wall_file(encode(data))[0]
        self.assertEqual([s.kind for s in ws.segments], ["wall", "door"])
        self.assertEqual((ws.segments[0].x2, ws.segments[0].y2), (200, 100))

    def test_foundry_omissions_preserved(self):
        data = good_scene()
        data["walls"] += [None, 7, {}, {"c": [0, 0, "bad", 1]}, {"c": [1, 1, 1, 1]}]
        self.assertEqual(len(fi.parse_wall_file(encode(data))[0].segments), 1)

    def test_uvtt_point_filtering_preserved(self):
        data = {"resolution": {}, "line_of_sight":
                [[None, {"x": 0, "y": 0}, {"x": 5}, {"x": 1, "y": 1}]]}
        self.assertEqual(len(fi.parse_wall_file(encode(data))[0].segments), 1)

    def test_uvtt_short_bounds_preserved(self):
        data = {"resolution": {}, "portals": [{}, {"bounds": []}, {"bounds": [{"x": 0}]}]}
        self.assertEqual(fi.parse_wall_file(encode(data))[0].segments, [])

    def test_numeric_strings_and_negative_coordinates_preserved(self):
        data = {"walls": [{"c": ["-5", "-6", "10", "12"]}], "width": "100", "height": None,
                "grid": "50", "padding": "0", "background": {"offsetX": "-2"}}
        ws = fi.parse_wall_file(encode(data))[0]
        self.assertEqual((ws.segments[0].x1, ws.origin_x), (-5, -2))
        self.assertEqual(ws.scene_width, 100)
        self.assertIsNone(ws.scene_height)

    def test_bug10_invalid_identity_remains_controlled(self):
        self.assert_import_error(b'{"_id":[],"c":[0,0,1,1]}\n{}', "Invalid NeDB _id")

    def test_bug10_deletion_replay_remains_lossless(self):
        raw = b'{"_id":"w","c":[0,0,1,1]}\n{"_id":"k","c":[0,0,2,2]}\n{"_id":"w","$$deleted":true}'
        self.assertEqual([s.x2 for s in fi.parse_wall_file(raw)[0].segments], [2])

    def test_bug10_json_array_is_not_replayed(self):
        data = [{"_id": "w", "c": [0, 0, 1, 1]}, {"_id": "w", "$$deleted": True}]
        self.assertEqual(len(fi.parse_wall_file(encode(data))[0].segments), 1)

    def test_bug11_nonfinite_coordinates_remain_controlled(self):
        self.assert_import_error(encode({"walls": [{"c": [0, 0, float("nan"), 1]}]}))

    def test_bug11_numeric_zip_rejection_is_per_entry(self):
        raw = make_pack([("bad.json", encode({"walls": [{"c": [0, 0, float("inf"), 1]}]})),
                         ("good.json", encode(good_scene()))])
        self.assertEqual([s.name for s in fi.parse_wall_file(raw)], ["Kept"])

    def test_valid_scenes_and_wall_lists(self):
        wall = good_scene()["walls"][0]
        for data in (wall, [wall], {"scenes": [None, good_scene()]}, [None, good_scene()]):
            with self.subTest(data=data):
                self.assertEqual(len(fi.parse_wall_file(encode(data))[0].segments), 1)

    def test_empty_edited_extension_remains_valid(self):
        ws = fi.parse_wall_file(uv.encode_uvtt(uv.export_uvtt([], 400, 200, "Empty")))[0]
        self.assertEqual(ws.name, "Empty")
        self.assertEqual(ws.segments, [])

    def test_v1_nonblocking_extension_remains_valid(self):
        data = uv.export_uvtt([WallSegment(0, 0, 70, 70, "wall", False)], 400, 200, "Passive")
        self.assertEqual(data["looking_glass"]["version"], 1)
        ws = fi.parse_wall_file(uv.encode_uvtt(data))[0]
        self.assertFalse(ws.segments[0].blocks)
        self.assertEqual(ws.segments[0].x2, 70)

    def test_v2_portal_graph_remains_valid(self):
        a = {"pair": "p", "end": "a", "sides": [{"role": "entry", "kind": "door", "exit": 0}, {"role": "none"}]}
        b = {"pair": "p", "end": "b", "sides": [{"role": "exit"}, {"role": "none"}]}
        segments = [WallSegment(0, 0, 70, 0, "portal", True, passage=a),
                    WallSegment(140, 0, 210, 0, "portal", True, passage=b)]
        data = uv.export_uvtt(segments, 400, 200, "Portals")
        self.assertEqual(data["looking_glass"]["version"], 2)
        parsed = fi.parse_wall_file(uv.encode_uvtt(data))[0].segments
        self.assertEqual([s.passage for s in parsed], [a, b])
        self.assertEqual([s.kind for s in parsed], ["portal", "portal"])

    def test_stale_extension_stays_rejected(self):
        data = uv.export_uvtt([], 400, 200, "Changed")
        data["line_of_sight"] = [[{"x": 0, "y": 0}, {"x": 1, "y": 1}]]
        self.assert_import_error(uv.encode_uvtt(data), "geometry changed")

    def test_invalid_extension_passage_is_controlled(self):
        data = uv.export_uvtt([], 400, 200, "Malformed")
        data["looking_glass"]["segments"] = [[0, 0, 1, 1, "portal", True, []]]
        self.assert_import_error(uv.encode_uvtt(data), "Passage configuration")

    def test_invalid_extension_graph_is_controlled(self):
        data = uv.export_uvtt([], 400, 200, "Malformed")
        p = {"pair": "p", "end": "a", "sides": [{"role": "entry", "kind": "door", "exit": 0}, {"role": "none"}]}
        data["looking_glass"]["segments"] = [[0, 0, 1, 1, "portal", True, p]]
        self.assert_import_error(uv.encode_uvtt(data), "exactly two")

    def test_zip_sorted_order_and_unrelated_metadata_preserved(self):
        a = dict(good_scene(), name="A")
        b = dict(good_scene(), name="B")
        raw = make_pack([("z.json", encode(b)), ("metadata.json", b'{"metadata":1}'), ("a.json", encode(a))])
        self.assertEqual([s.name for s in fi.parse_wall_file(raw)], ["A", "B"])

    def test_nested_zip_stays_rejected(self):
        inner = make_pack([("good.json", encode(good_scene()))])
        self.assert_import_error(make_pack([("nested.json", inner)]), "Nested archives")

    def test_traversal_stays_rejected(self):
        self.assert_import_error(make_pack([("../bad.json", encode(good_scene()))]), "Unsafe path")

    def test_duplicate_normalized_zip_path_stays_rejected(self):
        raw = make_pack([("a/./good.json", encode(good_scene())), ("a/good.json", encode(good_scene()))])
        self.assert_import_error(raw, "Duplicate path")


def shape_case(data, mode):
    def test(self):
        raw = encode(data)
        if mode == "direct":
            self.assert_import_error(raw)
        elif mode == "invalid_zip":
            self.assert_import_error(make_pack([("bad.json", raw)]), "No supported wall sets")
        else:
            packed = make_pack([("a-bad.json", raw), ("z-good.json", encode(good_scene()))])
            try:
                sets = fi.parse_wall_file(packed, "input.zip")
            except Exception as exc:
                self.fail(f"Expected usable companion; got {type(exc).__name__}: {exc}")
            self.assertEqual([s.name for s in sets], ["Kept"])
            self.assertEqual(len(sets[0].segments), 1)
    return test


for label, data in MALFORMED.items():
    for mode in ("direct", "invalid_zip", "mixed_zip"):
        setattr(ImportShapeTests, f"test_shape_{label}_{mode}", shape_case(data, mode))


def door_case(value, expected):
    def test(self):
        data = {"walls": [{"c": [0, 0, 10, 10], "door": value}]}
        self.assertEqual(fi.parse_wall_file(encode(data))[0].segments[0].kind, expected)
    return test


for index, (value, expected) in enumerate([(None, "wall"), (False, "wall"), (0, "wall"),
        ("", "wall"), ([], "wall"), ({}, "wall"), ("1", "door"), ("2", "secret"), (1.7, "door")]):
    setattr(ImportShapeTests, f"test_compat_door_{index}", door_case(value, expected))


def propagation_case(error_type, packed):
    def test(self):
        sentinel = error_type("unrelated constructor bug")
        raw = encode(good_scene())
        if packed:
            raw = make_pack([("good.json", raw)])
        with patch.object(fi, "WallSegment", side_effect=sentinel):
            with self.assertRaises(error_type) as caught:
                fi.parse_wall_file(raw)
        self.assertIs(caught.exception, sentinel)
    return test


for error_type in (AttributeError, KeyError, TypeError, ValueError, OverflowError, AssertionError):
    for packed in (False, True):
        setattr(ImportShapeTests, f"test_programming_error_{error_type.__name__}_{'zip' if packed else 'direct'}",
                propagation_case(error_type, packed))


if __name__ == "__main__":
    unittest.main()
