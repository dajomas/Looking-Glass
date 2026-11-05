"""Isolated bug-20 policy tests, extracting the actual helper without the app stack."""
import ast
from pathlib import Path

import pytest


SOURCE = Path(__file__).resolve().parents[1] / "looking_glass/web/auth_routes.py"


def load_policy():
    tree = ast.parse(SOURCE.read_text(encoding="utf-8"))
    nodes = [node for node in tree.body
             if (isinstance(node, ast.ImportFrom) and node.module in {"posixpath", "urllib.parse"})
             or (isinstance(node, ast.FunctionDef) and node.name == "_safe_next")]
    namespace = {}
    exec(compile(ast.Module(body=nodes, type_ignores=[]), str(SOURCE), "exec"), namespace)
    return namespace["_safe_next"]


REJECTED = [
    None, "", "https://example.invalid", "example.invalid", " //example.invalid",
    "//example.invalid", "///example.invalid", "/\\example.invalid",
    "/\texample.invalid", "/\nexample.invalid", "/\rexample.invalid",
    "/\x00example.invalid", "/\x1fexample.invalid", "/\x7fexample.invalid",
    "/%5cexample.invalid", "/%5Cexample.invalid", "/%2fexample.invalid",
    "/%2Fexample.invalid", "/%255cexample.invalid", "/%252fexample.invalid",
    "/%09example.invalid", "/%0aexample.invalid", "/%0dexample.invalid",
    "/%00example.invalid", "/%7fexample.invalid", "/%ff",
    "/login", "/login?next=/", "/login/again", "/%6cogin",
    "/a/../login", "/%2e/login", "/account?bad=\\value",
    "/" + "%25" + "25" * 10 + "5c" + "example.invalid",
]
ACCEPTED = [
    "/", "/account", "/campaigns/1?tab=maps", "/c/2", "/account?ok=hello%20world",
    "/campaigns/1?next=https%3A%2F%2Fexample.invalid", "/account#profile",
    "/maps/a%20b", "/maps/caf%C3%A9", "/account?value=%255c",
]


@pytest.mark.parametrize("target", REJECTED)
def test_unsafe_or_looping_return_target_falls_back(target):
    assert load_policy()(target) == "/"


@pytest.mark.parametrize("target", ACCEPTED)
def test_local_return_target_is_preserved_exactly(target):
    assert load_policy()(target) == target
