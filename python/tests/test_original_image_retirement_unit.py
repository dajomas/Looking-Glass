"""Bugs 17/18: isolated production-route lifecycle checks, not HTTP tests.

Run without application dependencies:
python python/tests/test_original_image_retirement_unit.py

Extract the current route and cleanup helper with AST. Permission, upload,
notification and room-reconciliation dependencies are doubles. SQLite and file
operations are real. This does not exercise ASGI FileResponse or fog workers.
"""
import ast
import asyncio
from contextlib import contextmanager
import logging
from pathlib import Path
import sqlite3
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import AsyncMock, Mock

ROOT = Path(__file__).resolve().parents[2]


def load_functions(path, names, namespace):
    class InjectReconciliation(ast.NodeTransformer):
        def visit_ImportFrom(self, node):
            if node.level == 3 and node.module == "services.room_notes":
                if [alias.name for alias in node.names] != ["reconcile_map"]:
                    raise AssertionError("Unexpected room-note dependency")
                return None
            return node

    tree = ast.parse(path.read_text(encoding="utf-8"))
    nodes = [node for node in tree.body
             if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
             and node.name in names]
    if {node.name for node in nodes} != set(names):
        raise AssertionError(f"Missing production functions: {names}")
    for node in nodes:
        node.decorator_list = ([ast.Name(id="contextmanager", ctx=ast.Load())]
                               if node.name == "_image_write_connection" else [])
        node.returns = None
        for arg in node.args.posonlyargs + node.args.args + node.args.kwonlyargs:
            arg.annotation = None
        # Only room-note reconciliation is imported inside the selected route.
        # Inject its double rather than importing the application package.
        InjectReconciliation().visit(node)
    module = ast.fix_missing_locations(ast.Module(body=nodes, type_ignores=[]))
    exec(compile(module, str(path), "exec"), namespace)


class OriginalRetirementTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.database = self.root / "state.sqlite"
        (self.root / "old.png").write_bytes(b"old reader bytes")
        with sqlite3.connect(self.database) as conn:
            conn.execute("CREATE TABLE maps(id INTEGER PRIMARY KEY, image_file TEXT, width INT, height INT)")
            conn.execute("INSERT INTO maps VALUES(1, 'old.png', 4, 2)")
            conn.execute("CREATE TABLE double_reveal_maps(map_id INTEGER)")

        @contextmanager
        def connect():
            conn = sqlite3.connect(self.database)
            conn.row_factory = sqlite3.Row
            try:
                with conn:
                    yield conn
            finally:
                conn.close()

        self.connect = connect

        def store(*args):
            (self.root / "new.png").write_bytes(b"new reader bytes")
            return SimpleNamespace(relative_path="new.png", width=4, height=2)

        def delete(root, path):
            (root / path).unlink()

        def update(conn, mid, path, width, height):
            conn.execute("UPDATE maps SET image_file=?, width=?, height=? WHERE id=?",
                         (path, width, height, mid))

        def access(conn, user, mid):
            return dict(conn.execute("SELECT * FROM maps WHERE id=?", (mid,)).fetchone()), {"id": 1}

        self.images = SimpleNamespace(store_map_image=store,
            delete_map_image=Mock(side_effect=delete), ImageImportError=ValueError)
        self.ctx = SimpleNamespace(db=SimpleNamespace(connect=connect),
            settings=SimpleNamespace(maps_dir=self.root), fog=SimpleNamespace(invalidate=Mock()))
        self.notify = SimpleNamespace(map_changed=AsyncMock())
        self.reconcile = Mock()
        retirement = {}
        load_functions(ROOT / "python/looking_glass/services/image_retirement.py",
                       {"retire_paths"}, retirement)
        namespace = dict(asyncio=asyncio, contextmanager=contextmanager,
            log=logging.getLogger(__name__), map_for_manage=access,
            _read_upload=AsyncMock(return_value=b"new reader bytes"), images=self.images,
            _back=lambda path, **kwargs: (path, kwargs),
            maps_repo=SimpleNamespace(replace_image=update), reconcile_map=self.reconcile,
            BadRequest=ValueError, image_retirement=SimpleNamespace(**retirement),
            notify=self.notify)
        load_functions(ROOT / "python/looking_glass/web/admin/campaigns.py",
                       {"replace_image", "_image_write_connection"}, namespace)
        self.replace = namespace["replace_image"]

    def request(self):
        return asyncio.run(self.replace(self.ctx, {}, 1, None))

    def test_selected_old_path_and_new_reader_both_complete(self):
        selected = self.root / "old.png"
        self.request()
        self.assertEqual(selected.read_bytes(), b"old reader bytes")
        with self.connect() as conn:
            self.assertEqual(conn.execute("SELECT image_file FROM image_retirements").fetchone()[0], "old.png")
            current = conn.execute("SELECT image_file FROM maps").fetchone()[0]
        self.assertEqual((self.root / current).read_bytes(), b"new reader bytes")
        self.images.delete_map_image.assert_not_called()

    def test_unlink_failure_cannot_skip_postcommit_notification(self):
        self.images.delete_map_image.side_effect = PermissionError("injected unlink failure")
        response = self.request()
        self.assertIn("ok", response[1])
        self.ctx.fog.invalidate.assert_called_once_with(1)
        self.notify.map_changed.assert_awaited_once_with(self.ctx, 1, "image")
        self.images.delete_map_image.assert_not_called()
        with self.connect() as conn:
            self.assertEqual(conn.execute("SELECT image_file FROM maps").fetchone()[0], "new.png")

    def test_precommit_failure_rolls_back_retirement_and_reference(self):
        self.reconcile.side_effect = sqlite3.OperationalError("injected before commit")
        with self.assertRaises(sqlite3.OperationalError):
            self.request()
        with self.connect() as conn:
            self.assertEqual(conn.execute("SELECT image_file FROM maps").fetchone()[0], "old.png")
            self.assertIsNone(conn.execute(
                "SELECT name FROM sqlite_master WHERE name='image_retirements'").fetchone())
        self.assertEqual((self.root / "old.png").read_bytes(), b"old reader bytes")
        self.assertFalse((self.root / "new.png").exists())
        self.notify.map_changed.assert_not_awaited()
        self.ctx.fog.invalidate.assert_not_called()


if __name__ == "__main__":
    unittest.main()
