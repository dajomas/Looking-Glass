"""Isolated actual route-body checks, not HTTP or DB acceptance."""
import ast
import asyncio
from contextlib import contextmanager
import json
from pathlib import Path
import sys
from types import ModuleType, SimpleNamespace

import pytest
from looking_glass.services import foundry_import as fi


class BadRequest(Exception):
    pass


def load(name, namespace):
    path = Path(__file__).resolve().parents[1] / "looking_glass/web/admin" / name
    functions = [node for node in ast.walk(ast.parse(path.read_text()))
                 if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
                 and node.name in ("apply_walls", "inspect_walls", "inspect_source")]
    assert len(functions) == 1
    func = functions[0]
    func.decorator_list = []
    for arg in (*func.args.posonlyargs, *func.args.args, *func.args.kwonlyargs):
        arg.annotation = None
    func.returns = None
    module = ast.fix_missing_locations(ast.Module(body=[func], type_ignores=[]))
    namespace["__package__"] = "looking_glass.web.admin"
    exec(compile(module, str(path), "exec"), namespace)
    return namespace[func.name]


def environment(monkeypatch, data):
    calls = []
    m = dict(id=1, campaign_id=2, width=400, height=200, doors_block=1,
             wall_offset_x=0, wall_offset_y=0, wall_scale_x=4, wall_scale_y=2)
    @contextmanager
    def connect():
        yield object()
    ctx = SimpleNamespace(db=SimpleNamespace(connect=connect),
                          fog=SimpleNamespace(invalidate=lambda mid: calls.append("invalidate")))
    module = ModuleType("looking_glass.services.room_notes")
    module.reconcile_map = lambda *args: calls.append("reconcile")
    monkeypatch.setitem(sys.modules, module.__name__, module)
    def replace(conn, mid, segments):
        calls.append("replace")
        return len(segments)
    async def read(*args):
        return json.dumps(data).encode()
    def parse(raw, filename):
        try:
            return fi.parse_wall_file(raw, filename)
        except (fi.WallImportError, ValueError, TypeError, OverflowError) as exc:
            raise BadRequest(str(exc)) from exc
    ns = dict(asyncio=asyncio, parse_wall_file=fi.parse_wall_file, WallImportError=fi.WallImportError,
              BadRequest=BadRequest, _read_upload=read, map_for_manage=lambda *args: (m, {}),
              vars_cal=lambda c: dict(offset_x=c.offset_x, offset_y=c.offset_y, scale_x=c.scale_x, scale_y=c.scale_y),
              walls_repo=SimpleNamespace(replace=replace),
              maps_repo=SimpleNamespace(set_calibration=lambda *args: calls.append("calibration"),
                                        set_walls_source=lambda *args: calls.append("source")),
              _parse=parse, _source=lambda *args: dict(raw=json.dumps(data).encode(), filename="walls.json", id=3),
              _summary=lambda source: dict(id=source["id"]))
    return ctx, m, ns, calls


INVALID = [
    {"walls": [{"c": ["NaN", 0, 10, 0]}]},
    {"walls": [{"c": [0, 0, 10, 0]}], "width": 1e-307, "height": 100, "padding": 0},
    {"walls": [{"c": [0, 0, 1e308, 0]}], "width": 100, "height": 100, "padding": 0},
]


@pytest.mark.parametrize("data", INVALID)
@pytest.mark.parametrize("use_scene", [False, True])
def test_apply_rejects_numeric_errors_before_any_write(monkeypatch, data, use_scene):
    ctx, m, ns, calls = environment(monkeypatch, data)
    apply = load("campaigns.py", ns)
    if not use_scene and data.get("width") == 1e-307:
        assert apply(ctx, object(), m, json.dumps(data).encode(), "walls.json", 0, use_scene)[0] == 1
        assert calls == ["replace", "source", "invalidate", "reconcile"]
    else:
        with pytest.raises(fi.WallImportError):
            apply(ctx, object(), m, json.dumps(data).encode(), "walls.json", 0, use_scene)
        assert calls == []


@pytest.mark.parametrize("data", INVALID)
@pytest.mark.parametrize("name", ["api.py", "wall_sources.py"])
def test_inspection_normalizes_numeric_failures(monkeypatch, data, name):
    ctx, m, ns, calls = environment(monkeypatch, data)
    inspect = load(name, ns)
    with pytest.raises(BadRequest):
        if name == "api.py":
            asyncio.run(inspect(ctx, {}, 1, SimpleNamespace(filename="walls.json")))
        else:
            asyncio.run(inspect(ctx, {}, 1, 3))
    assert calls == []


@pytest.mark.parametrize("use_scene", [False, True])
def test_valid_apply_preserves_write_sequence(monkeypatch, use_scene):
    data = {"walls": [{"c": [0, 0, 10, 0]}], "width": 100, "height": 100, "padding": 0}
    ctx, m, ns, calls = environment(monkeypatch, data)
    result = load("campaigns.py", ns)(ctx, object(), m, json.dumps(data).encode(), "walls.json", 0, use_scene)
    assert result == (1, "Unnamed scene")
    assert calls == (["replace", "calibration", "source", "invalidate", "reconcile"] if use_scene else
                     ["replace", "source", "invalidate", "reconcile"])


@pytest.mark.parametrize("name", ["api.py", "wall_sources.py"])
def test_valid_inspection_returns_finite_calibration(monkeypatch, name):
    data = {"walls": [{"c": [0, 0, 10, 0]}], "width": 100, "height": 100, "padding": 0}
    ctx, m, ns, calls = environment(monkeypatch, data)
    inspect = load(name, ns)
    if name == "api.py":
        result = asyncio.run(inspect(ctx, {}, 1, SimpleNamespace(filename="walls.json")))
    else:
        result = asyncio.run(inspect(ctx, {}, 1, 3))
    assert result["scenes"][0]["calibration"]["scale_x"] == 4
    assert calls == []
