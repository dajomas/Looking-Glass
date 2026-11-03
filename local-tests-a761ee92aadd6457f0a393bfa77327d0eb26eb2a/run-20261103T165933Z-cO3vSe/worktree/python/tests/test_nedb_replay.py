"""NeDB replay and public parser regressions, without HTTP fixtures."""
import io
import json
import unittest
import zipfile

from looking_glass.services.foundry_import import WallImportError, _parse_ndjson, parse_wall_file


def history(*records):
    return "\n".join(json.dumps(record) for record in records)


def wall(identity="w", x=10):
    return {"_id": identity, "c": [0, 0, x, 0]}


def scene(identity="s", name="Scene", x=10):
    return {"_id": identity, "name": name, "walls": [wall(x=x)]}


def deleted(identity):
    return {"_id": identity, "$$deleted": True}


def pack_file(raw):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as archive:
        archive.writestr("data/walls.db", raw)
    return buf.getvalue()


class NeDBReplayTests(unittest.TestCase):
    def test_wall_deletion_removes_document(self):
        self.assertEqual(_parse_ndjson(history(wall(), deleted("w"))), [])

    def test_scene_deletion_removes_document(self):
        self.assertEqual(_parse_ndjson(history(scene(), deleted("s"))), [])

    def test_latest_update_wins(self):
        self.assertEqual(_parse_ndjson(history(wall(), wall(x=20))), [wall(x=20)])

    def test_update_then_delete(self):
        self.assertEqual(_parse_ndjson(history(wall(), wall(x=20), deleted("w"))), [])

    def test_delete_then_recreate(self):
        self.assertEqual(_parse_ndjson(history(wall(), deleted("w"), wall(x=30))), [wall(x=30)])

    def test_unknown_and_repeated_deletions_are_harmless(self):
        self.assertEqual(_parse_ndjson(history(deleted("unknown"), wall(), deleted("w"), deleted("w"))), [])

    def test_other_ids_and_case_are_independent(self):
        self.assertEqual(_parse_ndjson(history(wall("w"), wall("W", 20), deleted("w"))), [wall("W", 20)])

    def test_anonymous_records_are_independent_and_last(self):
        anon = {"c": [0, 1, 10, 1]}
        self.assertEqual(_parse_ndjson(history(anon, wall(), anon, deleted("w"), wall("keep"))),
                         [wall("keep"), anon, anon])

    def test_anonymous_tombstones_are_ignored(self):
        anon = {"c": [0, 1, 10, 1]}
        self.assertEqual(_parse_ndjson(history(anon, {"$$deleted": True, "c": [0, 2, 10, 2]})), [anon])

    def test_false_marker_is_a_live_record(self):
        record = dict(wall(), **{"$$deleted": False})
        self.assertEqual(_parse_ndjson(history(deleted("w"), record)), [record])

    def test_truthy_marker_preserves_deletion_semantics(self):
        self.assertEqual(_parse_ndjson(history(wall(), {"_id": "w", "$$deleted": 1})), [])

    def test_order_after_update_and_recreation_is_deterministic(self):
        self.assertEqual(_parse_ndjson(history(wall("a"), wall("b"), wall("a", 20))),
                         [wall("a", 20), wall("b")])
        self.assertEqual(_parse_ndjson(history(wall("a"), wall("b"), deleted("a"), wall("a", 30))),
                         [wall("b"), wall("a", 30)])

    def test_blank_lines_and_nonobjects_are_ignored(self):
        text = "\n  " + history(None, [], 42, wall()) + "\n\n"
        self.assertEqual(_parse_ndjson(text), [wall()])

    def test_malformed_identity_is_controlled(self):
        for identity in (None, [], {}, 12, True, ""):
            for tombstone in (False, True):
                with self.subTest(identity=identity, tombstone=tombstone):
                    record = dict(wall(identity), **{"$$deleted": tombstone})
                    with self.assertRaisesRegex(WallImportError, "Invalid NeDB _id"):
                        _parse_ndjson(history(wall("valid"), record))

    def test_invalid_line_error_is_preserved(self):
        with self.assertRaisesRegex(WallImportError, "Invalid NeDB line"):
            _parse_ndjson(history(wall()) + "\nnot json")

    def test_public_walls_import_omits_deleted_wall(self):
        sets = parse_wall_file(history(wall(), wall("keep", 20), deleted("w")).encode(), "walls.db")
        self.assertEqual(len(sets), 1)
        self.assertEqual([s.x2 for s in sets[0].segments], [20])
        self.assertEqual(sets[0].source_format, "foundry-nedb")

    def test_public_scene_import_omits_deleted_scene(self):
        sets = parse_wall_file(history(scene(), scene("keep", "Kept", 20), deleted("s")).encode(), "scenes.db")
        self.assertEqual([s.name for s in sets], ["Kept"])
        self.assertEqual(sets[0].segments[0].x2, 20)

    def test_public_recreated_scene_has_latest_content(self):
        sets = parse_wall_file(history(scene(), deleted("s"), scene(name="Recreated", x=30)).encode(), "scenes.db")
        self.assertEqual([s.name for s in sets], ["Recreated"])
        self.assertEqual(sets[0].segments[0].x2, 30)

    def test_public_deleted_only_histories_report_no_walls(self):
        for record in (wall(), scene()):
            with self.subTest(record=record):
                raw = history(record, deleted(record["_id"])).encode()
                with self.assertRaisesRegex(WallImportError, "No walls found"):
                    parse_wall_file(raw, "source.db")

    def test_public_malformed_identity_is_controlled(self):
        with self.assertRaisesRegex(WallImportError, "Invalid NeDB _id"):
            parse_wall_file(history(wall(), wall([])).encode(), "walls.db")

    def test_json_list_is_not_a_nedb_log(self):
        sets = parse_wall_file(json.dumps([wall(), deleted("w")]).encode(), "walls.json")
        self.assertEqual(len(sets[0].segments), 1)
        self.assertEqual(sets[0].source_format, "foundry-json")

    def test_single_json_wall_and_bom_are_supported(self):
        raw = b"\xef\xbb\xbf" + json.dumps(wall()).encode()
        self.assertEqual(parse_wall_file(raw, "wall.json")[0].segments[0].x2, 10)

    def test_zip_pack_uses_replayed_geometry(self):
        raw = history(wall(), wall("keep", 20), deleted("w")).encode()
        sets = parse_wall_file(pack_file(raw), "pack.zip")
        self.assertEqual([s.x2 for s in sets[0].segments], [20])

    def test_zip_with_only_deleted_geometry_reports_no_sets(self):
        raw = history(wall(), deleted("w")).encode()
        with self.assertRaisesRegex(WallImportError, "No supported wall sets"):
            parse_wall_file(pack_file(raw), "pack.zip")


if __name__ == "__main__":
    unittest.main()
