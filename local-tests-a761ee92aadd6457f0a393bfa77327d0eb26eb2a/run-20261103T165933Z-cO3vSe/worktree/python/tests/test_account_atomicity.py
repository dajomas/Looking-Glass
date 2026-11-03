"""Isolated account-route atomicity tests using real repositories and scrypt.

AST loading removes routing decorators and postpones annotations only. A small
SQLite context models the application's commit-on-return/rollback-on-error rule;
request/settings/render/redirect boundaries are doubles, not HTTP execution.
"""
import ast
from contextlib import contextmanager
from pathlib import Path
import sqlite3
from types import SimpleNamespace

import pytest

from looking_glass.rbac import Role
from looking_glass.repositories import users, sessions
from looking_glass.security import verify_password


class Database:
    def __init__(self, path):
        self.path, self.fail_commit, self.statements = path, False, []

    @contextmanager
    def connect(self):
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys=ON")
        conn.set_trace_callback(self.statements.append)
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


def load_route():
    path = Path(__file__).resolve().parents[1] / "looking_glass/web/auth_routes.py"
    functions = [node for node in ast.parse(path.read_text()).body
                 if isinstance(node, ast.FunctionDef) and node.name == "account_submit"]
    assert len(functions) == 1
    functions[0].decorator_list = []
    module = ast.Module(body=[ast.ImportFrom(module="__future__",
                        names=[ast.alias(name="annotations")], level=0), *functions], type_ignores=[])
    def render(request, template, status_code=200, **kwargs):
        return SimpleNamespace(status_code=status_code, template=template, **kwargs)
    namespace = dict(users_repo=users, sessions_repo=sessions, verify_password=verify_password,
                     cookie_name=lambda request: f"lg_{request.entry}_session", render=render,
                     RedirectResponse=lambda target, status_code: SimpleNamespace(status_code=status_code, location=target))
    exec(compile(ast.fix_missing_locations(module), str(path), "exec"), namespace)
    return namespace["account_submit"]


def snapshot(db):
    with db.connect() as conn:
        return (tuple(tuple(row) for row in conn.execute("SELECT * FROM users ORDER BY id")),
                tuple(tuple(row) for row in conn.execute("SELECT * FROM sessions ORDER BY token_hash")))


@pytest.fixture(params=["admin", "viewer"])
def setup(tmp_path, request):
    db = Database(tmp_path / "account.db")
    with db.connect() as conn:
        conn.executescript("""
            CREATE TABLE users (
                id INTEGER PRIMARY KEY, username TEXT NOT NULL UNIQUE COLLATE NOCASE,
                display_name TEXT NOT NULL DEFAULT '', password_hash TEXT NOT NULL,
                role TEXT NOT NULL, active INTEGER NOT NULL DEFAULT 1,
                must_change_password INTEGER NOT NULL DEFAULT 0,
                created_by INTEGER, created_at TEXT NOT NULL DEFAULT 'fixture');
            CREATE TABLE sessions (
                token_hash TEXT PRIMARY KEY, user_id INTEGER NOT NULL REFERENCES users(id),
                entry TEXT NOT NULL, csrf_token TEXT NOT NULL, expires_at INTEGER NOT NULL,
                created_at TEXT NOT NULL DEFAULT 'fixture');
        """)
        uid = users.create(conn, "account", "current-pass-123", Role.ADMIN, "Original")
        other = users.create(conn, "other", "other-pass-123", Role.VIEWER, "Other")
        token, _ = sessions.create(conn, uid, request.param, 3600)
        sessions.create(conn, uid, request.param, 3600)
        sessions.create(conn, uid, "viewer" if request.param == "admin" else "admin", 3600)
        sessions.create(conn, other, "viewer", 3600)
    ctx = SimpleNamespace(db=db, settings=SimpleNamespace(section=lambda name: {"min_password_length": 8}))
    req = SimpleNamespace(entry=request.param, cookies={f"lg_{request.param}_session": token})
    return load_route(), ctx, req, uid, token


def user_for(setup, required=False):
    _, ctx, _, uid, _ = setup
    with ctx.db.connect() as conn:
        conn.execute("UPDATE users SET must_change_password=? WHERE id=?", (int(required), uid))
        return dict(users.get_with_hash(conn, "account"))


def submit(setup, user, **overrides):
    route, ctx, request, _, _ = setup
    data = dict(display_name="  Changed  ", current_password="current-pass-123",
                new_password="new-password-456", confirm_password="new-password-456")
    data.update(overrides)
    return route(request, ctx, user, **data)


@pytest.mark.parametrize("required", [False, True])
@pytest.mark.parametrize("values,error", [
    ({"current_password": "wrong-password"}, "Current password is incorrect."),
    ({"new_password": "short", "confirm_password": "short"}, "New password must be at least 8 characters."),
    ({"confirm_password": "not-the-same"}, "Passwords do not match."),
    ({"new_password": "current-pass-123", "confirm_password": "current-pass-123"}, "Choose a different password."),
])
def test_invalid_password_form_is_read_only(setup, required, values, error):
    user = user_for(setup, required)
    ctx = setup[1]
    before = snapshot(ctx.db)
    ctx.db.statements.clear()
    response = submit(setup, user, **values)
    assert response.status_code == 400 and response.error == error
    assert snapshot(ctx.db) == before
    assert not any(sql.lstrip().upper().startswith(("UPDATE", "DELETE", "INSERT")) for sql in ctx.db.statements)


def test_required_change_with_empty_new_password_is_read_only(setup):
    user = user_for(setup, True)
    ctx = setup[1]
    before = snapshot(ctx.db)
    response = submit(setup, user, new_password="", confirm_password="")
    assert response.status_code == 400
    assert snapshot(ctx.db) == before


def test_profile_only_save_preserves_hash_flag_and_sessions(setup):
    user = user_for(setup)
    _, ctx, _, _, _ = setup
    before = snapshot(ctx.db)
    response = submit(setup, user, current_password="ignored", new_password="", confirm_password="ignored")
    after = snapshot(ctx.db)
    assert response.status_code == 303 and response.location == "/account?ok=Account+updated"
    with ctx.db.connect() as conn:
        row = users.get_with_hash(conn, "account")
    assert row["display_name"] == "Changed" and row["password_hash"] == user["password_hash"]
    assert not row["must_change_password"] and before[1] == after[1] and before[0][1] == after[0][1]


@pytest.mark.parametrize("required", [False, True])
def test_valid_password_save_commits_all_fields_and_preserves_current_session(setup, required):
    user = user_for(setup, required)
    _, ctx, req, uid, token = setup
    response = submit(setup, user)
    assert response.status_code == 303
    with ctx.db.connect() as conn:
        row = users.get_with_hash(conn, "account")
        assert row["display_name"] == "Changed" and not row["must_change_password"]
        assert verify_password("new-password-456", row["password_hash"])
        assert not verify_password("current-pass-123", row["password_hash"])
        assert sessions.lookup(conn, token, req.entry) is not None
        assert conn.execute("SELECT count(*) FROM sessions WHERE user_id=?", (uid,)).fetchone()[0] == 1
        assert conn.execute("SELECT count(*) FROM sessions WHERE user_id!=?", (uid,)).fetchone()[0] == 1


@pytest.mark.parametrize("module,attribute", [(users, "set_password"), (sessions, "delete_for_user"), (users, "update")])
def test_write_failure_rolls_back_profile_password_flag_and_sessions(setup, monkeypatch, module, attribute):
    user = user_for(setup, True)
    ctx = setup[1]
    before = snapshot(ctx.db)
    original = getattr(module, attribute)
    def fail_after_write(*args, **kwargs):
        original(*args, **kwargs)
        raise sqlite3.OperationalError("injected write failure")
    monkeypatch.setattr(module, attribute, fail_after_write)
    with pytest.raises(sqlite3.OperationalError, match="write failure"):
        submit(setup, user)
    assert snapshot(ctx.db) == before


def test_commit_boundary_failure_rolls_back_everything(setup):
    user = user_for(setup, True)
    ctx = setup[1]
    before = snapshot(ctx.db)
    ctx.db.fail_commit = True
    with pytest.raises(sqlite3.OperationalError, match="commit failure"):
        submit(setup, user)
    ctx.db.fail_commit = False
    assert snapshot(ctx.db) == before
