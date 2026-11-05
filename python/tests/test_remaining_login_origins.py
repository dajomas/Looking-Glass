"""Exercise the remaining login call sites without importing the application stack."""
import ast
from pathlib import Path
from types import SimpleNamespace
from urllib.parse import urlsplit

import pytest

ROOT = Path(__file__).resolve().parent


def viewer_login(client):
    source = ROOT / "test_viewer_session_web.py"
    node = next(n for n in ast.parse(source.read_text()).body
                if isinstance(n, ast.FunctionDef) and n.name == "sign_in")
    namespace = {"urlsplit": urlsplit}
    exec(compile(ast.Module(body=[node], type_ignores=[]), str(source), "exec"), namespace)
    return namespace["sign_in"](client)


def reset_login_checks(client):
    source = ROOT / "test_password_reset_revocation_web.py"
    node = next(n for n in ast.parse(source.read_text()).body
                if isinstance(n, ast.FunctionDef) and n.name ==
                "test_reset_revokes_old_sessions_and_closes_only_target_sockets")
    statements = [n for n in ast.walk(node)
                  if (isinstance(n, ast.Assign) and any(
                      isinstance(t, ast.Name) and t.id in {"origin", "login_headers"} for t in n.targets))
                  or (isinstance(n, ast.Assert) and any(
                      isinstance(c, ast.Call) and isinstance(c.func, ast.Attribute)
                      and c.func.attr == "post" and c.args and isinstance(c.args[0], ast.Constant)
                      and c.args[0].value == "/admin/login" for c in ast.walk(n)))]
    statements.sort(key=lambda n: n.lineno)
    assert sum(isinstance(n, ast.Assert) for n in statements) == 2
    exec(compile(ast.Module(body=statements, type_ignores=[]), str(source), "exec"),
         {"client": client, "urlsplit": urlsplit})


class Client:
    def __init__(self, base_url, overrides=None):
        self.base_url = base_url
        self.headers = {"Existing": "unchanged"}
        self.cookies = {"lg_viewer_session": "viewer-token"}
        self.calls = []
        self.overrides = overrides or {}

    def post(self, path, *, data, follow_redirects, headers=None):
        origin = urlsplit(self.base_url)
        expected = {"Origin": f"{origin.scheme}://{origin.netloc}"}
        self.calls.append((path, data, headers, follow_redirects))
        password = data["password"]
        status = 401 if password == "secondroot-pass" else 303
        if headers != expected:
            status = 403
        return SimpleNamespace(status_code=self.overrides.get(password, status))


@pytest.mark.parametrize("base_url", [
    "http://testserver/", "https://dm.example:8443/prefix/", "http://[::1]:5100/",
])
@pytest.mark.parametrize("kind", ["viewer", "reset"])
def test_login_calls_have_request_local_origin_and_preserve_outcomes(base_url, kind):
    client = Client(base_url)
    if kind == "viewer":
        assert viewer_login(client) == "viewer-token"
        assert len(client.calls) == 1 and client.calls[0][0] == "/login"
        assert client.calls[0][1] == {"username": "alice", "password": "alicepass"}
    else:
        reset_login_checks(client)
        assert [call[0] for call in client.calls] == ["/admin/login", "/admin/login"]
        assert [call[1] for call in client.calls] == [
            {"username": "second-root", "password": "secondroot-pass"},
            {"username": "second-root", "password": "replacement-pass"},
        ]
    assert all(call[3] is False for call in client.calls)
    assert client.headers == {"Existing": "unchanged"}


@pytest.mark.parametrize("kind,overrides", [
    ("viewer", {"alicepass": 403}),
    ("reset", {"secondroot-pass": 303}),
    ("reset", {"replacement-pass": 401}),
])
def test_existing_status_assertions_still_detect_failures(kind, overrides):
    client = Client("http://testserver/", overrides)
    with pytest.raises(AssertionError):
        viewer_login(client) if kind == "viewer" else reset_login_checks(client)
