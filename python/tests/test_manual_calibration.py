"""Isolated calibration regressions: real Pydantic/SQLite, auth/render/hub doubles."""
import ast
import asyncio
from contextlib import contextmanager
from pathlib import Path
import sqlite3
from types import SimpleNamespace

from pydantic import BaseModel, Field, ValidationError
import pytest

from looking_glass.services.foundry_import import WallImportError, validated_calibration
from looking_glass.services.wall_model import Calibration, WallSegment, WallSet

ROOT = Path(__file__).resolve().parents[1] / "looking_glass"


class BadRequest(Exception):
    pass


def definitions(path, names, namespace):
    nodes = [n for n in ast.parse(path.read_text()).body
             if isinstance(n, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)) and n.name in names]
    assert len(nodes) == len(names)
    for node in ast.walk(ast.Module(body=nodes, type_ignores=[])):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            node.decorator_list = []
    module = ast.Module(body=[ast.ImportFrom(module="__future__",
        names=[ast.alias(name="annotations")], level=0), *nodes], type_ignores=[])
    exec(compile(ast.fix_missing_locations(module), str(path), "exec"), namespace)
    return namespace


def load(namespace):
    path = ROOT / "web/admin/calibration.py"
    if path.exists():
        ns = definitions(path, {"CalibrationIn", "register_calibration"}, namespace)
        router = SimpleNamespace(post=lambda _: lambda fn: fn)
        return ns["CalibrationIn"], ns["register_calibration"](router, namespace["map_payload"])
    ns = definitions(ROOT / "web/admin/api.py", {"CalibrationIn", "calibration"}, namespace)
    return ns["CalibrationIn"], ns["calibration"]


@pytest.fixture
def setup(tmp_path):
    db_path = tmp_path / "calibration.db"
    @contextmanager
    def connect():
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except BaseException:
            conn.rollback()
            raise
        finally:
            conn.close()
    with connect() as conn:
        conn.executescript("""
            CREATE TABLE maps (id INTEGER PRIMARY KEY,width INTEGER,height INTEGER,
                wall_offset_x REAL,wall_offset_y REAL,wall_scale_x REAL,wall_scale_y REAL,
                doors_block INTEGER,walls_version INTEGER,fog_version INTEGER);
            INSERT INTO maps VALUES (1,400,200,0,0,1,1,1,3,7);
            CREATE TABLE walls (x1 REAL,y1 REAL,x2 REAL,y2 REAL);
            INSERT INTO walls VALUES (0,0,10,20);
        """)
    calls = []
    def snapshot():
        with connect() as conn:
            return tuple(conn.execute("SELECT * FROM maps").fetchone())
    def payload(ctx, conn, mid):
        return dict(conn.execute("SELECT * FROM maps WHERE id=?", (mid,)).fetchone())
    maps = definitions(ROOT / "repositories/maps.py", {"set_calibration"}, {})
    async def changed(*args):
        calls.append(("notify", snapshot()))
    ctx = SimpleNamespace(db=SimpleNamespace(connect=connect),
                          fog=SimpleNamespace(invalidate=lambda mid: calls.append(("invalidate", mid))))
    ns = dict(BaseModel=BaseModel, Field=Field, Calibration=Calibration, WallSet=WallSet,
        WallImportError=WallImportError, validated_calibration=validated_calibration, BadRequest=BadRequest,
        map_for_manage=lambda conn, user, mid: (dict(conn.execute("SELECT * FROM maps WHERE id=?", (mid,)).fetchone()), {}),
        walls_repo=SimpleNamespace(list_for_map=lambda conn, mid: [WallSegment(*row) for row in conn.execute("SELECT * FROM walls")]),
        maps_repo=SimpleNamespace(set_calibration=maps["set_calibration"]),
        notify=SimpleNamespace(map_changed=changed), map_payload=payload, _map_payload=payload)
    model, route = load(ns)
    return SimpleNamespace(model=model, route=route, ctx=ctx, calls=calls, snapshot=snapshot, connect=connect)


def apply(setup, **changes):
    body = setup.model(**{**dict(offset_x=0, offset_y=0, scale_x=1, scale_y=1), **changes})
    return asyncio.run(setup.route(setup.ctx, {"id": 1}, 1, body))


@pytest.mark.parametrize("field", ["offset_x", "offset_y", "scale_x", "scale_y"])
@pytest.mark.parametrize("value", ["Infinity", "-Infinity", "NaN"])
def test_nonfinite_fields_rejected_without_effects(setup, field, value):
    before = setup.snapshot()
    with pytest.raises(ValidationError):
        apply(setup, **{field: value})
    assert setup.snapshot() == before and setup.calls == []


@pytest.mark.parametrize("changes", [dict(offset_x=1e308, scale_x=100),
    dict(offset_y=-1e308, scale_y=100)])
def test_finite_multiplication_overflow_rejected_before_write(setup, changes):
    before = setup.snapshot()
    with pytest.raises(BadRequest):
        apply(setup, **changes)
    assert setup.snapshot() == before and setup.calls == []


def test_subtraction_overflow_rejected_before_write(setup):
    with setup.connect() as conn:
        conn.execute("UPDATE walls SET x2=1e308")
    before = setup.snapshot()
    with pytest.raises(BadRequest):
        apply(setup, offset_x=-1e308, scale_x=0.1)
    assert setup.snapshot() == before and setup.calls == []


def test_valid_negative_offsets_keep_response_and_notification(setup):
    result = apply(setup, offset_x=-10, offset_y=-20, scale_x=2, scale_y=0.5, doors_block=False)
    assert (result["wall_offset_x"], result["wall_offset_y"]) == (-10, -20)
    assert (result["walls_version"], result["fog_version"], result["doors_block"]) == (4, 8, 0)
    assert setup.calls == [("invalidate", 1), ("notify", setup.snapshot())]


def test_wall_free_map_still_rejects_infinite_offset(setup):
    with setup.connect() as conn:
        conn.execute("DELETE FROM walls")
    before = setup.snapshot()
    with pytest.raises(ValidationError):
        apply(setup, offset_x="Infinity")
    assert setup.snapshot() == before and setup.calls == []
