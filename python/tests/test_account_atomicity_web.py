"""HTTP account atomicity acceptance on both portals; normal dependencies required."""
import pytest
pytest.importorskip("fastapi")

from test_web import env, login
from looking_glass.repositories import users, sessions
from looking_glass.security import verify_password


@pytest.fixture(params=["admin", "viewer"])
def account(env, request):
    ctx, admin, viewer = env
    app = admin if request.param == "admin" else viewer
    client = login(app, "dm", "dmpass123")
    token = client.cookies.get(f"lg_{request.param}_session")
    with ctx.db.connect() as conn:
        user = dict(sessions.lookup(conn, token, request.param))
        sessions.create(conn, user["id"], request.param, 3600)
        sessions.create(conn, user["id"], "viewer" if request.param == "admin" else "admin", 3600)
    with client:
        yield ctx, client, request.param, token, user


def snapshot(ctx):
    with ctx.db.connect() as conn:
        return "\n".join(conn.iterdump())


def force(ctx, user, required):
    with ctx.db.connect() as conn:
        conn.execute("UPDATE users SET must_change_password=? WHERE id=?", (int(required), user["id"]))


def data(user, **overrides):
    result = dict(csrf_token=user["csrf_token"], display_name="Changed", current_password="dmpass123",
                  new_password="new-password-456", confirm_password="new-password-456")
    result.update(overrides)
    return result


@pytest.mark.parametrize("required", [False, True])
@pytest.mark.parametrize("overrides", [
    {"current_password": "wrong-password"},
    {"new_password": "short", "confirm_password": "short"},
    {"confirm_password": "not-the-same"},
    {"new_password": "dmpass123", "confirm_password": "dmpass123"},
])
def test_failed_account_form_preserves_all_database_state(account, required, overrides):
    ctx, client, _, _, user = account
    force(ctx, user, required)
    before = snapshot(ctx)
    result = client.post("/account", data=data(user, **overrides), follow_redirects=False)
    assert result.status_code == 400
    assert snapshot(ctx) == before


def test_required_empty_password_failure_is_atomic(account):
    ctx, client, _, _, user = account
    force(ctx, user, True)
    before = snapshot(ctx)
    result = client.post("/account", data=data(user, new_password="", confirm_password=""), follow_redirects=False)
    assert result.status_code == 400 and snapshot(ctx) == before


def test_profile_only_update_preserves_hash_flag_and_sessions(account):
    ctx, client, _, _, user = account
    with ctx.db.connect() as conn:
        before = dict(users.get_with_hash(conn, "dm"))
        before_sessions = [tuple(row) for row in conn.execute("SELECT * FROM sessions ORDER BY token_hash")]
    result = client.post("/account", data=data(user, display_name="  Changed  ", new_password="", confirm_password=""),
                         follow_redirects=False)
    assert result.status_code == 303 and result.headers["location"] == "/account?ok=Account+updated"
    with ctx.db.connect() as conn:
        after = dict(users.get_with_hash(conn, "dm"))
        assert [tuple(row) for row in conn.execute("SELECT * FROM sessions ORDER BY token_hash")] == before_sessions
    assert after.pop("display_name") == "Changed"
    before.pop("display_name")
    assert after == before


@pytest.mark.parametrize("required", [False, True])
def test_valid_password_update_keeps_current_session_and_revokes_others(account, required):
    ctx, client, entry, token, user = account
    force(ctx, user, required)
    result = client.post("/account", data=data(user), follow_redirects=False)
    assert result.status_code == 303 and result.headers["location"] == "/account?ok=Account+updated"
    with ctx.db.connect() as conn:
        saved = users.get_with_hash(conn, "dm")
        assert saved["display_name"] == "Changed" and not saved["must_change_password"]
        assert verify_password("new-password-456", saved["password_hash"])
        assert not verify_password("dmpass123", saved["password_hash"])
        assert sessions.lookup(conn, token, entry) is not None
        assert conn.execute("SELECT count(*) FROM sessions WHERE user_id=?", (user["id"],)).fetchone()[0] == 1
    assert client.get("/account").status_code == 200


def test_failed_csrf_is_read_only(account):
    ctx, client, _, _, user = account
    before = snapshot(ctx)
    result = client.post("/account", data=data(user, csrf_token="invalid"), follow_redirects=False)
    assert result.status_code == 403 and snapshot(ctx) == before
