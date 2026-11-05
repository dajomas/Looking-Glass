"""Isolated contracts for the real login helpers; no global header injection."""
import ast
from pathlib import Path
import re
from types import SimpleNamespace
from urllib.parse import urlsplit

import pytest

ROOT = Path(__file__).resolve().parent


def load_login(relative):
    source = ROOT / relative
    node = next(n for n in ast.parse(source.read_text(encoding="utf-8")).body
                if isinstance(n, ast.FunctionDef) and n.name == "login")
    node.returns = None
    namespace = {"urlsplit": urlsplit, "re": re, "TestClient": lambda app, **kwargs: app}
    exec(compile(ast.Module(body=[node], type_ignores=[]), str(source), "exec"), namespace)
    return namespace["login"]


class Client:
    def __init__(self, base_url, status=303):
        self.base_url = base_url
        self.headers = {"Existing": "unchanged"}
        self.calls = []
        self.status = status

    def post(self, path, **kwargs):
        self.calls.append((path, kwargs))
        url = urlsplit(self.base_url)
        valid = kwargs.get("headers") == {"Origin": f"{url.scheme}://{url.netloc}"}
        return SimpleNamespace(status_code=self.status if valid else 403, text="login response")

    def get(self, path, **kwargs):
        assert path == "/" and kwargs == {"follow_redirects": True}
        return SimpleNamespace(status_code=200, text='<meta name="csrf-token" content="token-value">')


@pytest.mark.parametrize("base_url", [
    "http://127.0.0.1:49153/", "http://127.0.0.1:57211/",
    "https://table.example:8443/prefix/", "http://[::1]:53123/",
])
def test_recovery_uses_exact_client_origin_without_path(base_url):
    client = Client(base_url)
    assert load_login("recovery/test_restart.py")(client, "user", "password") == "token-value"
    path, kwargs = client.calls[0]
    assert path == "/login" and kwargs["follow_redirects"] is False
    assert kwargs["data"] == {"username": "user", "password": "password"}
    assert client.headers == {"Existing": "unchanged"}


def test_shared_web_helper_only_sets_origin_on_login_request():
    client = Client("http://testserver/")
    assert load_login("test_web.py")(client, "user", "password") is client
    assert client.calls == [("/login", {
        "data": {"username": "user", "password": "password"},
        "headers": {"Origin": "http://testserver"}, "follow_redirects": False,
    })]
    assert client.headers == {"Existing": "unchanged"}


@pytest.mark.parametrize("relative", ["test_web.py", "recovery/test_restart.py"])
def test_helpers_keep_login_failure_assertions(relative):
    with pytest.raises(AssertionError):
        load_login(relative)(Client("http://testserver/", status=403), "user", "password")
