"""Bug 21's actual pure policy, loaded without importing the FastAPI application."""
import importlib.util
from pathlib import Path

import pytest


SOURCE = Path(__file__).resolve().parents[1] / "looking_glass/web/login_origin.py"
spec = importlib.util.spec_from_file_location("login_origin_policy", SOURCE)
policy = importlib.util.module_from_spec(spec)
spec.loader.exec_module(policy)


@pytest.mark.parametrize("target,origins,referers", [
    ("http://testserver/", ["http://testserver"], []),
    ("http://testserver/", ["http://testserver:80"], []),
    ("https://DM.example/", ["https://dm.example:443"], []),
    ("http://testserver/", [], ["http://testserver/login?next=%2Faccount"]),
    ("http://testserver:5000/", ["http://testserver:5000"], []),
    ("http://testserver:5100/", ["http://testserver:5100"], []),
    ("https://dm.example/", ["https://dm.example"], []),
    ("https://table.example/", [], ["https://table.example/login"]),
    ("http://[::1]:5000/", ["http://[::1]:5000"], []),
])
def test_authorized_same_origin(target, origins, referers):
    assert policy.login_request_allowed(target, origins, referers)


@pytest.mark.parametrize("origins,referers", [
    ([], []), (["null"], []), ([""], []), ([], [""]),
    (["https://example.invalid"], []), (["http://testserver.evil.invalid"], []),
    (["http://evil.testserver"], []), (["https://testserver"], []),
    (["http://testserver:5000"], []), (["http://testserver:5100"], []),
    (["http://testserver:0"], []), (["http://testserver:65536"], []),
    (["http://testserver:bad"], []), (["http://testserver:"], []),
    (["http://user@testserver"], []), (["http://testserver/"], []),
    (["http://testserver?x=1"], []), (["http://testserver#fragment"], []),
    (["http://testserver http://evil.invalid"], []),
    (["http://testserver,http://evil.invalid"], []),
    (["http://testserver", "http://testserver"], []),
    (["http://testserver"], ["http://testserver/login", "http://testserver/login"]),
    (["null"], ["http://testserver/login"]),
    (["https://evil.invalid"], ["http://testserver/login"]),
    ([], ["https://evil.invalid/login"]), ([], ["/login"]),
    ([], ["http://user@testserver/login"]),
    (["http://testserver\n"], []), (["http://testserver\\evil"], []),
    (["http://test%73erver"], []), (["http://[broken"], []),
])
def test_rejected_source(origins, referers):
    assert not policy.login_request_allowed("http://testserver/", origins, referers)


def test_source_port_cannot_cross_portal_boundary():
    assert not policy.login_request_allowed("http://testserver:5000/", ["http://testserver:5100"], [])


def test_bad_target_is_not_authorized():
    assert not policy.login_request_allowed("http://testserver:bad/", ["http://testserver"], [])


@pytest.mark.parametrize("origin", [None, "null", "https://evil.invalid"])
def test_route_rejects_before_authentication_context_access(origin):
    import ast
    from types import SimpleNamespace

    source = SOURCE.with_name("auth_routes.py")
    node = next(n for n in ast.parse(source.read_text()).body
                if isinstance(n, ast.FunctionDef) and n.name == "login_submit")
    node.decorator_list = []
    for arg in node.args.args:
        arg.annotation = None
    node.returns = None

    class Denied(Exception):
        def __init__(self, status_code, detail):
            self.status_code = status_code

    class Headers:
        def getlist(self, key):
            return {"host": ["testserver"], "origin": [] if origin is None else [origin]}.get(key, [])

    namespace = {"HTTPException": Denied, "login_request_allowed": policy.login_request_allowed}
    exec(compile(ast.Module(body=[node], type_ignores=[]), str(source), "exec"), namespace)
    request = SimpleNamespace(headers=Headers(), base_url="http://testserver/")
    with pytest.raises(Denied) as denied:
        namespace["login_submit"](request, object(), "root", "dummy-password")
    assert denied.value.status_code == 403
