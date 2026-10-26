"""Source-contract regressions; deliberately do not import FastAPI or claim HTTP coverage."""
import ast
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[2]
API = ast.parse((ROOT / "python/looking_glass/web/admin/api.py").read_text())
SOURCES = ast.parse((ROOT / "python/looking_glass/web/admin/wall_sources.py").read_text())


def function(tree, name):
    return next(n for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name == name)


def payload_expression(key):
    node = function(API, "_map_payload")
    returned = next(n.value for n in node.body if isinstance(n, ast.Return))
    assert isinstance(returned, ast.Dict)
    values = [v for k,v in zip(returned.keys,returned.values) if isinstance(k,ast.Constant) and k.value == key]
    assert len(values) == 1, f"Shared map payload must contain exactly one {key!r} field"
    return values[0]


@pytest.mark.parametrize("map_id", [1, 23, 987654])
def test_shared_payload_provides_relative_authenticated_image_url(map_id):
    value = payload_expression("image_url")
    expression = ast.Expression(body=value)
    ast.fix_missing_locations(expression)
    assert eval(compile(expression,"<production image_url>","eval"), {"__builtins__":{}}, {"map_id":map_id}) == f"/api/maps/{map_id}/image"


def test_existing_artwork_and_double_reveal_fields_are_preserved():
    payload_expression("image_version")
    payload_expression("double_reveal_image")


def test_wall_source_import_reuses_shared_payload():
    handler = function(SOURCES,"import_source")
    assert any(isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id == "map_payload" for n in ast.walk(handler))


def test_raw_artwork_route_retains_management_check_and_no_store():
    handler = function(API,"map_image")
    assert any(isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id == "map_for_manage" for n in ast.walk(handler))
    responses = [n for n in ast.walk(handler) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id == "FileResponse"]
    assert len(responses) == 1
    headers = next(k.value for k in responses[0].keywords if k.arg == "headers")
    assert ast.literal_eval(headers)["Cache-Control"] == "no-store"
