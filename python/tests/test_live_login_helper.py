"""Isolated tests of the live login method; no browser/network coverage."""
import ast
from pathlib import Path

import pytest


@pytest.fixture
def login():
    source = Path(__file__).parent / "live_e2e" / "support.py"
    tree = ast.parse(source.read_text(encoding="utf-8"))
    session = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "Session")
    method = next(n for n in session.body if isinstance(n, ast.FunctionDef) and n.name == "login")
    namespace = {}
    exec(compile(ast.Module(body=[method], type_ignores=[]), str(source), "exec"), namespace)
    return namespace["login"]


class Page:
    def __init__(self, current_url):
        self.current_url = current_url
        self.actions = []

    def goto(self, url):
        self.actions.append(("goto", url))

    def locator(self, selector):
        self.selector = selector
        return self

    def fill(self, value):
        self.actions.append(("fill", self.selector, value))

    def click(self):
        self.actions.append(("click", self.selector))

    def wait_for_url(self, predicate):
        self.result = predicate(self.current_url)


@pytest.mark.parametrize(("url", "expected"), [
    ("http://127.0.0.1:5000/login", False),
    ("http://127.0.0.1:5000/login?next=/", False),
    ("http://127.0.0.1:5100/login/", False),
    ("http://127.0.0.1:5000/", True),
    ("http://127.0.0.1:5100/c/1", True),
    ("http://127.0.0.1:5000/?next=/login", True),
    ("http://127.0.0.1:5000/#/login", True),
])
def test_login_wait_handles_url_strings(login, url, expected):
    page = Page(url)
    login(None, page, "http://127.0.0.1:5000", "dm", "password")
    assert page.result is expected
    assert page.actions == [
        ("goto", "http://127.0.0.1:5000/login"),
        ("fill", 'input[name="username"]', "dm"),
        ("fill", 'input[name="password"]', "password"),
        ("click", 'button[type="submit"]'),
    ]
