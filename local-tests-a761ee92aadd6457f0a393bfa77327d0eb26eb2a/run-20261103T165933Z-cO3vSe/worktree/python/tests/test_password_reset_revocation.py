"""Isolated password-reset route regressions, with real SQLite.

AST-loaded route and session deletion bodies; user/password and hub doubles.
No HTTP dependency injection, password hashing or actual WebSocket transport.
"""
import ast
import asyncio
from contextlib import contextmanager
import hashlib
import inspect
from pathlib import Path
import sqlite3
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[1] / "looking_glass"


class BadRequest(Exception):
    pass


def load_function(path, name, namespace):
    nodes = [node for node in ast.parse(path.read_text()).body
             if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name]
    assert len(nodes) == 1
    nodes[0].decorator_list = []
    module = ast.Module(body=[ast.ImportFrom(module="__future__",
        names=[ast.alias(name="annotations")], level=0), *nodes], type_ignores=[])
    exec(compile(ast.fix_missing_locations(module), str(path), "exec"), namespace)
    return namespace[name]


class Database:
    def __init__(self, path):
        self.path = path
        self.fail_commit = False

    @contextmanager
    def connect(self):
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            if self.fail_commit:
                raise sqlite3.OperationalError("injected commit failure")
            conn.commit()
        except BaseException:
            conn.rollback()
            raise
        finally:
            conn.close()


def snapshot(db):
    with sqlite3.connect(db.path) as conn:
        return (conn.execute("SELECT * FROM users ORDER BY id").fetchall(),
                conn.execute("SELECT * FROM sessions ORDER BY token_hash").fetchall())


@pytest.fixture
def setup(tmp_path):
    db = Database(tmp_path / "reset.db")
    token_hash = lambda token: hashlib.sha256(token.encode()).hexdigest()
    with db.connect() as conn:
        conn.executescript("""
            CREATE TABLE users (id INTEGER PRIMARY KEY, username TEXT, password TEXT, must_change INTEGER);
            CREATE TABLE sessions (token_hash TEXT PRIMARY KEY, user_id INTEGER);
            INSERT INTO users VALUES (1,'root','old-password',0),(2,'other','other-password',0);
        """)
        conn.executemany("INSERT INTO sessions VALUES (?,?)",
                         [(token_hash(token), uid) for token, uid in
                          [('current',1),('other-admin',1),('viewer',1),('other-user',2)]])
    def get(conn, uid):
        return conn.execute("SELECT * FROM users WHERE id=?", (uid,)).fetchone()
    def set_password(conn, uid, password, *, must_change):
        conn.execute("UPDATE users SET password=?,must_change=? WHERE id=?", (password, must_change, uid))
    deletion = load_function(ROOT / "repositories/sessions.py", "delete_for_user", {"token_hash": token_hash})
    sessions = SimpleNamespace(delete_for_user=deletion)
    calls = []
    async def kick_user(uid):
        calls.append((uid, snapshot(db)))
    ctx = SimpleNamespace(db=db, settings=SimpleNamespace(section=lambda _: {"min_password_length": 8}),
                          hub=SimpleNamespace(kick_user=kick_user))
    route = load_function(ROOT / "web/admin/users.py", "reset_password", dict(
        users_repo=SimpleNamespace(get=get, set_password=set_password), sessions_repo=sessions,
        cookie_name=lambda _: "lg_admin_session", BadRequest=BadRequest,
        _back=lambda path, **kwargs: (path, kwargs)))
    return SimpleNamespace(db=db, ctx=ctx, route=route, calls=calls, sessions=sessions, token_hash=token_hash)


def reset(setup, target=1, password="new-password", must_change=False):
    request = SimpleNamespace(cookies={"lg_admin_session": "current"})
    kwargs = dict(ctx=setup.ctx, user={"id": 1}, user_id=target,
                  password=password, must_change=must_change)
    if "request" in inspect.signature(setup.route).parameters:
        kwargs["request"] = request
    return asyncio.run(setup.route(**kwargs))


@pytest.mark.parametrize("must_change", [False, True])
def test_self_reset_keeps_only_requesting_session_and_kicks_after_commit(setup, must_change):
    response = reset(setup, must_change=must_change)
    rows, tokens = snapshot(setup.db)
    assert "ok" in response[1]
    assert rows[0] == (1, "root", "new-password", int(must_change))
    assert set(tokens) == {(setup.token_hash("current"), 1), (setup.token_hash("other-user"), 2)}
    assert setup.calls == [(1, (rows, tokens))]


def test_other_user_reset_revokes_all_target_sessions_only(setup):
    response = reset(setup, target=2)
    rows, tokens = snapshot(setup.db)
    assert "ok" in response[1] and rows[1][2] == "new-password"
    assert len(tokens) == 3 and all(uid == 1 for _, uid in tokens)
    assert setup.calls == [(2, (rows, tokens))]


def test_short_password_does_not_write_or_kick(setup):
    before = snapshot(setup.db)
    assert "err" in reset(setup, password="short")[1]
    assert snapshot(setup.db) == before and setup.calls == []


def test_unknown_user_does_not_write_or_kick(setup):
    before = snapshot(setup.db)
    with pytest.raises(BadRequest, match="Unknown user"):
        reset(setup, target=999)
    assert snapshot(setup.db) == before and setup.calls == []


def test_session_deletion_failure_rolls_back_password_and_does_not_kick(setup):
    before = snapshot(setup.db)
    def fail(conn, uid, keep_token=None):
        conn.execute("DELETE FROM sessions WHERE user_id=?", (uid,))
        raise sqlite3.OperationalError("injected deletion failure")
    setup.sessions.delete_for_user = fail
    with pytest.raises(sqlite3.OperationalError, match="deletion failure"):
        reset(setup)
    assert snapshot(setup.db) == before and setup.calls == []


def test_commit_failure_rolls_back_password_and_sessions_without_kick(setup):
    before = snapshot(setup.db)
    setup.db.fail_commit = True
    with pytest.raises(sqlite3.OperationalError, match="commit failure"):
        reset(setup)
    assert snapshot(setup.db) == before and setup.calls == []
