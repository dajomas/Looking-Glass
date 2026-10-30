"""Isolated import-policy route checks; parser/DB/auth/image boundaries are doubles.

These checks are NOT HTTP, real parser, migrated-DB, rollback or deployment acceptance.
Run in a normal checkout with stdlib unittest discovery for this module.
"""
import ast
import asyncio
from contextlib import contextmanager
from pathlib import Path
import sys
from types import ModuleType, SimpleNamespace
import unittest
from unittest.mock import AsyncMock, Mock, patch


class InputError(ValueError):
    pass


class ClientError(Exception):
    pass


def load_function(filename, name, namespace):
    path = Path(__file__).resolve().parents[1] / "looking_glass/web/admin" / filename
    matches = [n for n in ast.walk(ast.parse(path.read_text()))
               if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name == name]
    if len(matches) != 1:
        raise AssertionError(f"Expected one {name} in {path}")
    node = matches[0]
    node.decorator_list = []
    for arg in (*node.args.posonlyargs, *node.args.args, *node.args.kwonlyargs):
        arg.annotation = None
    node.returns = None
    namespace["__package__"] = "looking_glass.web.admin"
    exec(compile(ast.fix_missing_locations(ast.Module(body=[node], type_ignores=[])), str(path), "exec"), namespace)
    return namespace[name]


class Upload:
    def __init__(self, filename, raw):
        self.filename, self.raw = filename, raw

    async def read(self, limit):
        return self.raw[:limit]


class ImportPolicyRouteTests(unittest.TestCase):
    def setUp(self):
        self.events = []
        self.row = {"id": 11, "campaign_id": 7, "width": 400, "height": 200, "image_file": "old.png"}
        self.source = {"id": 3, "filename": "walls.json", "raw": b"walls", "scene_count": 1, "created_at": "fixed"}
        self.ws = SimpleNamespace(name="Scene", segments=[SimpleNamespace(kind="wall")],
            source_format="foundry-json", scene_width=None, scene_height=None,
            image_data="", image_is_thumbnail=False, image_reference="")
        self.parse = Mock(return_value=[self.ws])
        self.apply = Mock(return_value=(1, "Scene"))
        self.calibrate = Mock(return_value=SimpleNamespace(offset_x=0, offset_y=0, scale_x=1, scale_y=1))
        support = ModuleType("looking_glass.services.foundry_import")
        support.validated_calibration = self.calibrate
        support.WallImportError = InputError
        self.modules_patch = patch.dict(sys.modules, {support.__name__: support})
        self.modules_patch.start()
        self.addCleanup(self.modules_patch.stop)
        self.reference_row = None
        self.log = Mock(spec=["warning"])
        def reference_query(sql, parameters):
            self.assertEqual(sql, "SELECT 1 FROM maps WHERE image_file = ? LIMIT 1")
            self.assertEqual(parameters, ("new.png",))
            self.events.append("reference_check")
            return SimpleNamespace(fetchone=lambda: self.reference_row)
        self.reference_query = Mock(side_effect=reference_query)
        @contextmanager
        def connect():
            self.events.append("open")
            try:
                yield SimpleNamespace(execute=self.reference_query)
            except BaseException:
                self.events.append("exception_exit")
                raise
            else:
                self.events.append("normal_exit")
        def create(*args):
            self.events.append("create_map")
            return 11
        def save(*args):
            self.events.append("save_source")
            return self.source
        self.maps = SimpleNamespace(create=Mock(side_effect=create), get=Mock(return_value=self.row), replace_image=Mock())
        self.sources = SimpleNamespace(save=Mock(side_effect=save), get=Mock(return_value=self.source), delete=Mock())
        self.images = SimpleNamespace(store_map_image=Mock(return_value=SimpleNamespace(relative_path="new.png",width=400,height=200)),
                                      delete_map_image=Mock(), ImageImportError=type("ImageError", (Exception,), {}))
        self.notify = SimpleNamespace(map_changed=AsyncMock())
        self.ctx = SimpleNamespace(db=SimpleNamespace(connect=connect), fog=SimpleNamespace(invalidate=Mock()),
            settings=SimpleNamespace(maps_dir=Path("unused"), section=lambda section:
                {"max_upload_mb": 1} if section == "storage" else {"doors_block": True}))
        self.ns = dict(asyncio=asyncio, log=self.log, WallImportError=InputError, BadRequest=ClientError,
            parse_wall_file=self.parse, apply_walls=self.apply, images=self.images,
            maps_repo=self.maps, sources_repo=self.sources, notify=self.notify,
            campaign_for_manage=Mock(), map_for_manage=Mock(return_value=(self.row, {})),
            _back=Mock(side_effect=lambda path, **kwargs: {"path": path, **kwargs}),
            _map_payload=Mock(return_value={"ok": True}), map_payload=Mock(return_value={"ok": True}),
            image_bytes=Mock(return_value=b"image"), vars_cal=vars)
        self.read = load_function("campaigns.py", "_read_upload", self.ns)
        # load_function strips decorators; restore the actual contextmanager wrapper.
        self.ns["_image_write_connection"] = contextmanager(
            load_function("campaigns.py", "_image_write_connection", self.ns))
        self.upload = load_function("campaigns.py", "upload_map", self.ns)
        for name in ("_source", "_summary", "_parse", "save_source", "inspect_source", "import_source"):
            load_function("wall_sources.py", name, self.ns)
        self.inspect = load_function("api.py", "inspect_walls", self.ns)
        self.direct = load_function("api.py", "import_walls", self.ns)
        self.file = Upload("walls.json", b"walls")
        self.image = Upload("map.png", b"image")
        self.body = SimpleNamespace(source_id=3, scene_index=0, use_scene_calibration=True, use_pack_image=False)

    def call(self, function, *args):
        return asyncio.run(function(*args))

    def assert_failed_upload_cleanup(self):
        self.assertEqual(self.events, ["open", "normal_exit", "open", "create_map",
                                      "exception_exit", "open", "reference_check", "normal_exit"])
        self.reference_query.assert_called_once_with(
            "SELECT 1 FROM maps WHERE image_file = ? LIMIT 1", ("new.png",))
        self.images.delete_map_image.assert_called_once_with(Path("unused"), "new.png")
        self.log.warning.assert_not_called()

    def test_image_write_helper_retains_referenced_image(self):
        self.reference_row = (1,)
        error = KeyError("original")
        with self.assertRaises(KeyError) as caught:
            with self.ns["_image_write_connection"](self.ctx, "new.png"):
                raise error
        self.assertIs(caught.exception, error)
        self.assertEqual(self.events, ["open", "exception_exit", "open", "reference_check", "normal_exit"])
        self.reference_query.assert_called_once_with(
            "SELECT 1 FROM maps WHERE image_file = ? LIMIT 1", ("new.png",))
        self.images.delete_map_image.assert_not_called()
        self.log.warning.assert_called_once()

    def test_image_write_helper_preserves_error_when_reference_check_fails(self):
        self.reference_query.side_effect = OSError("verification unavailable")
        error = KeyError("original")
        with self.assertRaises(KeyError) as caught:
            with self.ns["_image_write_connection"](self.ctx, "new.png"):
                raise error
        self.assertIs(caught.exception, error)
        self.reference_query.assert_called_once_with(
            "SELECT 1 FROM maps WHERE image_file = ? LIMIT 1", ("new.png",))
        self.images.delete_map_image.assert_not_called()
        self.log.warning.assert_called_once()
        self.assertTrue(self.log.warning.call_args.kwargs["exc_info"])

    def test_image_write_helper_preserves_error_when_delete_fails(self):
        self.images.delete_map_image.side_effect = OSError("unlink denied")
        error = KeyError("original")
        with self.assertRaises(KeyError) as caught:
            with self.ns["_image_write_connection"](self.ctx, "new.png"):
                raise error
        self.assertIs(caught.exception, error)
        self.assertEqual(self.events, ["open", "exception_exit", "open", "reference_check", "normal_exit"])
        self.images.delete_map_image.assert_called_once_with(Path("unused"), "new.png")
        self.log.warning.assert_called_once()
        self.assertTrue(self.log.warning.call_args.kwargs["exc_info"])

    def assert_no_import_effects(self):
        self.maps.create.assert_not_called()
        self.maps.replace_image.assert_not_called()
        self.sources.save.assert_not_called()
        self.sources.delete.assert_not_called()
        self.images.store_map_image.assert_not_called()
        self.images.delete_map_image.assert_not_called()
        self.ctx.fog.invalidate.assert_not_called()
        self.notify.map_changed.assert_not_called()

    def test_direct_inspection_normalized_error_has_no_effects(self):
        error = InputError("UVTT point must contain x and y")
        self.parse.side_effect = error
        with self.assertRaisesRegex(ClientError, "UVTT point"):
            self.call(self.inspect, self.ctx, {}, 11, self.file)
        self.calibrate.assert_not_called()
        self.ns["_map_payload"].assert_not_called()
        self.assert_no_import_effects()

    def test_direct_apply_normalized_error_has_no_followup_effects(self):
        self.apply.side_effect = InputError("Foundry door is invalid")
        with self.assertRaisesRegex(ClientError, "Foundry door"):
            self.call(self.direct, self.ctx, {}, 11, self.file)
        self.ns["_map_payload"].assert_not_called()
        self.assert_no_import_effects()

    def test_saved_source_save_rejects_before_persisting(self):
        self.parse.side_effect = InputError("malformed resolution")
        with self.assertRaisesRegex(ClientError, "Cannot read wall source"):
            self.call(self.ns["save_source"], self.ctx, {}, 7, self.file)
        self.assert_no_import_effects()

    def test_saved_source_inspection_does_not_delete_or_mutate_source(self):
        self.parse.side_effect = InputError("malformed portal")
        with self.assertRaises(ClientError):
            self.call(self.ns["inspect_source"], self.ctx, {}, 11, 3)
        self.calibrate.assert_not_called()
        self.assert_no_import_effects()

    def test_saved_source_apply_rejects_before_pack_artwork_or_apply(self):
        self.parse.side_effect = InputError("malformed bounds")
        self.body.use_pack_image = True
        with self.assertRaises(ClientError):
            self.call(self.ns["import_source"], self.ctx, {}, 11, self.body)
        self.apply.assert_not_called()
        self.ns["image_bytes"].assert_not_called()
        self.assert_no_import_effects()

    def test_map_upload_invalid_walls_keeps_partial_success(self):
        self.parse.side_effect = InputError("malformed walls")
        response = self.call(self.upload, self.ctx, {}, 7, self.image, "", self.file)
        self.assertEqual(response["path"], "/maps/11")
        self.assertIn("walls not imported: malformed walls", response["ok"])
        self.maps.create.assert_called_once()
        self.images.store_map_image.assert_called_once()
        self.sources.save.assert_not_called()
        self.apply.assert_not_called()
        self.images.delete_map_image.assert_not_called()
        self.assertEqual(self.events[-1], "normal_exit")

    def test_map_upload_apply_rejection_retains_already_saved_source(self):
        self.apply.side_effect = InputError("target calibration rejected")
        response = self.call(self.upload, self.ctx, {}, 7, self.image, "", self.file)
        self.assertIn("walls not imported", response["ok"])
        self.sources.save.assert_called_once()
        self.sources.delete.assert_not_called()
        self.assertLess(self.events.index("create_map"), self.events.index("save_source"))
        self.assertEqual(self.events[-1], "normal_exit")
        self.images.delete_map_image.assert_not_called()

    def test_valid_single_set_upload_saves_then_applies(self):
        response = self.call(self.upload, self.ctx, {}, 7, self.image, "", self.file)
        self.assertIn("1 walls from 'Scene'", response["ok"])
        self.sources.save.assert_called_once()
        self.apply.assert_called_once()
        self.assertNotIn("walls not imported", response["ok"])

    def test_valid_multiset_upload_waits_for_explicit_selection(self):
        self.parse.return_value = [self.ws, self.ws]
        response = self.call(self.upload, self.ctx, {}, 7, self.image, "", self.file)
        self.assertIn("2 wall sets", response["ok"])
        self.assertEqual(self.sources.save.call_args.args[-1], 2)
        self.apply.assert_not_called()

    def test_upload_without_walls_does_not_parse_or_save(self):
        self.call(self.upload, self.ctx, {}, 7, self.image, "", None)
        self.parse.assert_not_called()
        self.sources.save.assert_not_called()
        self.apply.assert_not_called()

    def test_saved_source_bytes_are_retained_exactly(self):
        raw = b"original ZIP or JSON bytes"
        self.file.raw = raw
        response = self.call(self.ns["save_source"], self.ctx, {}, 7, self.file)
        self.assertTrue(response["ok"])
        args = self.sources.save.call_args.args
        self.assertEqual(args[1:], (7, "walls.json", raw, 1))

    def test_saved_source_index_rejection_precedes_artwork(self):
        self.body.scene_index = 4
        self.body.use_pack_image = True
        with self.assertRaisesRegex(ClientError, "index out of range"):
            self.call(self.ns["import_source"], self.ctx, {}, 11, self.body)
        self.apply.assert_not_called()
        self.ns["image_bytes"].assert_not_called()
        self.assert_no_import_effects()

    def test_valid_direct_import_keeps_arguments_and_notifies(self):
        response = self.call(self.direct, self.ctx, {}, 11, self.file, 2, False)
        self.assertEqual(response["imported"], 1)
        self.assertEqual(self.apply.call_args.args[-2:], (2, False))
        self.notify.map_changed.assert_awaited_once_with(self.ctx, 11, "walls")

    def test_valid_saved_import_keeps_calibration_choice(self):
        self.body.use_scene_calibration = False
        response = self.call(self.ns["import_source"], self.ctx, {}, 11, self.body)
        self.assertEqual(response["source_id"], 3)
        self.assertEqual(self.apply.call_args.args[-2:], (0, False))
        self.sources.delete.assert_not_called()
        self.images.store_map_image.assert_not_called()
        self.notify.map_changed.assert_awaited_once_with(self.ctx, 11, "walls")

    def test_direct_inspection_programming_error_propagates(self):
        error = KeyError("unrelated bug")
        self.parse.side_effect = error
        with self.assertRaises(KeyError) as caught:
            self.call(self.inspect, self.ctx, {}, 11, self.file)
        self.assertIs(caught.exception, error)
        self.assert_no_import_effects()

    def test_direct_apply_programming_error_propagates(self):
        error = AttributeError("unrelated bug")
        self.apply.side_effect = error
        with self.assertRaises(AttributeError) as caught:
            self.call(self.direct, self.ctx, {}, 11, self.file)
        self.assertIs(caught.exception, error)
        self.assert_no_import_effects()

    def test_upload_uncaught_programming_error_is_not_newly_swallowed(self):
        error = KeyError("unrelated bug")
        self.parse.side_effect = error
        with self.assertRaises(KeyError) as caught:
            self.call(self.upload, self.ctx, {}, 7, self.image, "", self.file)
        self.assertIs(caught.exception, error)
        self.sources.save.assert_not_called()
        self.assert_failed_upload_cleanup()

    def test_upload_wall_size_error_remains_outside_partial_parse_handler(self):
        self.file.raw = b"x" * (1024 * 1024 + 1)
        with self.assertRaisesRegex(ClientError, "File too large"):
            self.call(self.upload, self.ctx, {}, 7, self.image, "", self.file)
        self.parse.assert_not_called()
        self.sources.save.assert_not_called()
        self.assert_failed_upload_cleanup()

    def test_missing_source_remains_client_rejection(self):
        self.sources.get.return_value = None
        with self.assertRaisesRegex(ClientError, "not found"):
            self.call(self.ns["inspect_source"], self.ctx, {}, 11, 3)
        self.parse.assert_not_called()
        self.assert_no_import_effects()

    def test_map_upload_client_apply_rejection_retains_source(self):
        self.apply.side_effect = ClientError("selection rejected")
        response = self.call(self.upload, self.ctx, {}, 7, self.image, "", self.file)
        self.assertIn("walls not imported: selection rejected", response["ok"])
        self.sources.save.assert_called_once()
        self.sources.delete.assert_not_called()


class ZipPolicyTests(unittest.TestCase):
    def setUp(self):
        import base64
        import posixpath
        import zipfile
        from urllib.parse import unquote
        path = Path(__file__).resolve().parents[1] / "looking_glass/services/pack_images.py"
        tree = ast.parse(path.read_text())
        nodes = [node for node in tree.body if
                 isinstance(node, ast.FunctionDef) and node.name in ("_safe_name", "parse_zip_pack") or
                 isinstance(node, ast.Assign) and any(isinstance(target, ast.Name) and
                     target.id in ("MAX_PACK_BYTES", "MAX_ENTRIES") for target in node.targets)]
        self.ns = dict(base64=base64, posixpath=posixpath, zipfile=zipfile, unquote=unquote,
                       io=__import__("io"), WallImportError=InputError)
        exec(compile(ast.fix_missing_locations(ast.Module(body=nodes, type_ignores=[])), str(path), "exec"), self.ns)
        self.parse = self.ns["parse_zip_pack"]

    def pack(self, entries):
        import io
        import zipfile
        stream = io.BytesIO()
        with zipfile.ZipFile(stream, "w") as archive:
            for name, data in entries:
                archive.writestr(name, data)
        return stream.getvalue()

    def wallset(self, name):
        return SimpleNamespace(name=name, image_reference="", image_data="", image_is_thumbnail=False)

    def test_mixed_pack_skips_normalized_input_rejection(self):
        def parser(raw, name):
            if raw == b"bad":
                raise InputError("malformed input")
            return [self.wallset(name)]
        result = self.parse(self.pack([("bad.json", b"bad"), ("good.json", b"good")]), parser)
        self.assertEqual([s.name for s in result], ["good.json"])

    def test_invalid_only_pack_reports_no_supported_sets(self):
        with self.assertRaisesRegex(InputError, "No supported wall sets"):
            self.parse(self.pack([("bad.json", b"bad")]), Mock(side_effect=InputError("bad")))

    def test_sorted_entry_order_is_preserved(self):
        result = self.parse(self.pack([("z.json", b"z"), ("a.json", b"a")]),
                            lambda raw, name: [self.wallset(name)])
        self.assertEqual([s.name for s in result], ["a.json", "z.json"])

    def test_unrelated_programming_error_is_not_skipped(self):
        sentinel = KeyError("programming bug")
        with self.assertRaises(KeyError) as caught:
            self.parse(self.pack([("a.json", b"a")]), Mock(side_effect=sentinel))
        self.assertIs(caught.exception, sentinel)

    def test_nested_archives_remain_rejected(self):
        with self.assertRaisesRegex(InputError, "Nested archives"):
            self.parse(self.pack([("a.json", b"PKnested")]), Mock())

    def test_traversal_remains_rejected(self):
        with self.assertRaisesRegex(InputError, "Unsafe path"):
            self.parse(self.pack([("../a.json", b"a")]), Mock())

    def test_duplicate_normalized_paths_remain_rejected(self):
        with self.assertRaisesRegex(InputError, "Duplicate path"):
            self.parse(self.pack([("a/./b.json", b"a"), ("a/b.json", b"b")]), Mock())

    def test_entry_limit_value_and_enforcement_preserved(self):
        self.assertEqual(self.ns["MAX_ENTRIES"], 2000)
        self.ns["MAX_ENTRIES"] = 1
        with self.assertRaisesRegex(InputError, "entry limit"):
            self.parse(self.pack([("a.json", b"a"), ("b.json", b"b")]), Mock())

    def test_expanded_limit_value_and_enforcement_preserved(self):
        self.assertEqual(self.ns["MAX_PACK_BYTES"], 150 * 1024 * 1024)
        self.ns["MAX_PACK_BYTES"] = 1
        with self.assertRaisesRegex(InputError, "expanded size"):
            self.parse(self.pack([("a.json", b"ab")]), Mock())

    def test_relative_artwork_resolution_preserved(self):
        import base64
        ws = self.wallset("Scene")
        ws.image_reference = "art/map.png"
        ws.image_is_thumbnail = True
        self.parse(self.pack([("scenes/a.json", b"scene"), ("scenes/art/map.png", b"artwork")]),
                   lambda raw, name: [ws])
        self.assertEqual(base64.b64decode(ws.image_data), b"artwork")
        self.assertFalse(ws.image_is_thumbnail)


if __name__ == "__main__":
    unittest.main()
