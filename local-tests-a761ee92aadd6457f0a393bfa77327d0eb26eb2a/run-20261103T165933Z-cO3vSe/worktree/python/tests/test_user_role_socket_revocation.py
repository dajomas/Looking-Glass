"""Isolated route-body tests; no HTTP, dependency injection or ASGI transport.

Load the unchanged function bodies through AST so these regressions also run
without FastAPI. SQLite is real; repository and hub boundaries are test doubles.
"""
import ast
import asyncio
from contextlib import contextmanager
from enum import StrEnum
from pathlib import Path
import sqlite3
from types import SimpleNamespace

import pytest


class Role(StrEnum):
    SUPERADMIN = "superadmin"
    ADMIN = "admin"
    VIEWER = "viewer"


class BadRequest(Exception):
    pass


class Users:
    @staticmethod
    def get(conn, user_id):
        return conn.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()

    @staticmethod
    def count_superadmins(conn):
        return conn.execute("SELECT count(*) FROM users WHERE role='superadmin' AND active=1").fetchone()[0]

    @staticmethod
    def update(conn, user_id, *, display_name, role, active):
        conn.execute("UPDATE users SET display_name=?,role=?,active=? WHERE id=?",
                     (display_name, role.value, int(active), user_id))


class Sessions:
    @staticmethod
    def delete_for_user(conn, user_id):
        conn.execute("DELETE FROM sessions WHERE user_id=?", (user_id,))


def load_route():
    path = Path(__file__).resolve().parents[1] / "looking_glass/web/admin/users.py"
    tree = ast.parse(path.read_text())
    functions = [n for n in tree.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
                 and n.name in ("_guard_last_superadmin", "update_user")]
    assert len(functions) == 2
    for function in functions:
        function.decorator_list = []
    module = ast.Module(body=[ast.ImportFrom(module="__future__",
                        names=[ast.alias(name="annotations")], level=0), *functions], type_ignores=[])
    namespace = dict(Role=Role, BadRequest=BadRequest, users_repo=Users, sessions_repo=Sessions,
                     _back=lambda path, **kwargs: (path, kwargs))
    exec(compile(ast.fix_missing_locations(module), str(path), "exec"), namespace)
    return namespace["update_user"]


class Database:
    def __init__(self, path):
        self.path, self.fail_commit = path, False

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


def state(db):
    with sqlite3.connect(db.path) as conn:
        return (conn.execute("SELECT * FROM users ORDER BY id").fetchall(),
                conn.execute("SELECT * FROM sessions ORDER BY token").fetchall())


@pytest.fixture
def setup(tmp_path):
    db = Database(tmp_path / "role.db")
    with db.connect() as conn:
        conn.executescript("""
            CREATE TABLE users (id INTEGER PRIMARY KEY,username TEXT,display_name TEXT,role TEXT,active INTEGER);
            CREATE TABLE sessions (token TEXT PRIMARY KEY,user_id INTEGER);
            INSERT INTO users VALUES (1,'actor','Actor','superadmin',1),
                                     (2,'target','Target','admin',1),(3,'other','Other','viewer',1);
            INSERT INTO sessions VALUES ('actor',1),('target-admin',2),('target-viewer',2),('other',3);
        """)
    calls = []
    async def kick_user(user_id):
        calls.append((user_id, state(db)))
    ctx = SimpleNamespace(db=db, hub=SimpleNamespace(kick_user=kick_user))
    return load_route(), ctx, calls


def update(setup, role, active=True, user_id=2, actor_id=1):
    route, ctx, _ = setup
    return asyncio.run(route(ctx, {"id": actor_id}, user_id,
                             role=role, display_name="Edited", active=active))


@pytest.mark.parametrize("old", list(Role))
@pytest.mark.parametrize("new", list(Role))
def test_active_role_transitions_and_unchanged_roles(setup, old, new):
    _, ctx, calls = setup
    with ctx.db.connect() as conn:
        conn.execute("UPDATE users SET role=? WHERE id=2", (old.value,))
    response = update(setup, new)
    users, sessions = state(ctx.db)
    assert response[0] == "/users" and users[1][2:5] == ("Edited", new.value, 1)
    revoked = old != new
    assert [call[0] for call in calls] == ([2] if revoked else [])
    assert [token for token, uid in sessions if uid == 2] == ([] if revoked else ["target-admin", "target-viewer"])
    assert ("actor", 1) in sessions and ("other", 3) in sessions
    if revoked:
        assert calls[0][1] == (users, sessions), "Kick must observe committed changes on an independent connection"


@pytest.mark.parametrize("old", list(Role))
def test_deactivation_still_revokes_and_kicks_after_commit(setup, old):
    _, ctx, calls = setup
    with ctx.db.connect() as conn:
        conn.execute("UPDATE users SET role=? WHERE id=2", (old.value,))
    update(setup, old, active=False)
    assert [call[0] for call in calls] == [2]
    assert calls[0][1] == state(ctx.db)
    assert not any(uid == 2 for _, uid in state(ctx.db)[1])


def test_reactivation_without_role_change_preserves_existing_policy(setup):
    _, ctx, calls = setup
    with ctx.db.connect() as conn:
        conn.execute("UPDATE users SET active=0 WHERE id=2")
    update(setup, Role.ADMIN)
    assert calls == []
    assert sum(uid == 2 for _, uid in state(ctx.db)[1]) == 2


def test_unknown_user_is_rejected_without_writes_or_kicks(setup):
    _, ctx, calls = setup
    before = state(ctx.db)
    with pytest.raises(BadRequest, match="Unknown user"):
        update(setup, Role.VIEWER, user_id=999)
    assert state(ctx.db) == before and calls == []


@pytest.mark.parametrize("role,active", [(Role.VIEWER, True), (Role.SUPERADMIN, False)])
def test_self_revocation_is_rejected(setup, role, active):
    _, ctx, calls = setup
    before = state(ctx.db)
    with pytest.raises(BadRequest, match="yourself"):
        update(setup, role, active=active, user_id=1)
    assert state(ctx.db) == before and calls == []


@pytest.mark.parametrize("role,active", [(Role.ADMIN, True), (Role.SUPERADMIN, False)])
def test_last_superadmin_is_protected(setup, role, active):
    _, ctx, calls = setup
    with ctx.db.connect() as conn:
        conn.execute("UPDATE users SET role='superadmin' WHERE id=2")
        conn.execute("UPDATE users SET role='viewer' WHERE id=1")
    before = state(ctx.db)
    with pytest.raises(BadRequest, match="At least one"):
        update(setup, role, active=active, actor_id=999)
    assert state(ctx.db) == before and calls == []


def test_failed_session_delete_rolls_back_and_does_not_kick(setup, monkeypatch):
    _, ctx, calls = setup
    before = state(ctx.db)
    def fail(conn, user_id):
        conn.execute("DELETE FROM sessions WHERE user_id=?", (user_id,))
        raise sqlite3.OperationalError("injected deletion failure")
    monkeypatch.setattr(Sessions, "delete_for_user", fail)
    with pytest.raises(sqlite3.OperationalError):
        update(setup, Role.VIEWER)
    assert state(ctx.db) == before and calls == []


def test_failed_commit_rolls_back_and_does_not_kick(setup):
    _, ctx, calls = setup
    before = state(ctx.db)
    ctx.db.fail_commit = True
    with pytest.raises(sqlite3.OperationalError, match="commit failure"):
        update(setup, Role.VIEWER)
    assert state(ctx.db) == before and calls == []
