"""HTTP/WebSocket password-reset regressions; run with normal app dependencies."""
import pytest

from looking_glass.repositories import sessions, users
from test_user_role_socket_web import campaign, env, ping, receive


@pytest.mark.parametrize("self_reset", [False, True])
@pytest.mark.parametrize("must_change", [False, True])
def test_reset_revokes_old_sessions_and_closes_only_target_sockets(campaign, self_reset, must_change):
    ctx, client, cid, target, viewer_token, admin_token, root_token, root_csrf, alice = campaign
    with ctx.db.connect() as conn:
        other_admin, _ = sessions.create(conn, target, "admin", 3600)
        other_viewer, _ = sessions.create(conn, target, "viewer", 3600)
        target_csrf = sessions.lookup(conn, admin_token, "admin")["csrf_token"]
    actor = admin_token if self_reset else root_token
    csrf = target_csrf if self_reset else root_csrf
    with client.websocket_connect(f"/viewer/ws/c/{cid}",
            headers={"cookie": f"lg_viewer_session={viewer_token}"}) as first, \
         client.websocket_connect(f"/viewer/ws/c/{cid}",
            headers={"cookie": f"lg_viewer_session={other_viewer}"}) as second, \
         client.websocket_connect(f"/viewer/ws/c/{cid}",
            headers={"cookie": f"lg_viewer_session={alice}"}) as unaffected:
        for ws in (first, second, unaffected):
            ping(ws)
        response = client.post(f"/admin/users/{target}/password",
            headers={"cookie": f"lg_admin_session={actor}"},
            data={"csrf_token": csrf, "password": "replacement-pass", "must_change": str(must_change).lower()},
            follow_redirects=False)
        assert response.status_code == 303 and "ok=" in response.headers["location"]
        for ws in (first, second):
            frame = receive(ws)
            assert frame["type"] == "websocket.close" and frame["code"] == 4403
        ping(unaffected)
        with ctx.db.connect() as conn:
            retained = sessions.lookup(conn, admin_token, "admin")
            assert (retained is not None) == self_reset
            assert sessions.lookup(conn, other_admin, "admin") is None
            assert sessions.lookup(conn, viewer_token, "viewer") is None
            assert sessions.lookup(conn, other_viewer, "viewer") is None
            assert sessions.lookup(conn, root_token, "admin") is not None
            assert sessions.lookup(conn, alice, "viewer") is not None
            assert bool(users.get(conn, target)["must_change_password"]) == must_change
        for token in (viewer_token, other_viewer):
            assert client.get(f"/viewer/api/c/{cid}/state",
                headers={"cookie": f"lg_viewer_session={token}"}, follow_redirects=False).status_code in (401, 403, 404)
        for token in (other_admin,) if self_reset else (admin_token, other_admin):
            denied = client.get("/admin/account", headers={"cookie": f"lg_admin_session={token}"}, follow_redirects=False)
            assert denied.status_code == 303 and denied.headers["location"].startswith("/login")
        if self_reset:
            assert client.get("/admin/account", headers={"cookie": f"lg_admin_session={actor}"}).status_code == 200
        assert client.post("/admin/login", data={"username": "second-root", "password": "secondroot-pass"},
                           follow_redirects=False).status_code == 401
        assert client.post("/admin/login", data={"username": "second-root", "password": "replacement-pass"},
                           follow_redirects=False).status_code == 303


@pytest.mark.parametrize("invalid", ["csrf", "short", "unknown"])
def test_rejected_reset_preserves_password_sessions_and_socket(campaign, invalid):
    ctx, client, cid, target, token, admin_token, root_token, csrf, _ = campaign
    with ctx.db.connect() as conn:
        before = dict(users.get_with_hash(conn, "second-root"))
    with client.websocket_connect(f"/viewer/ws/c/{cid}",
            headers={"cookie": f"lg_viewer_session={token}"}) as ws:
        ping(ws)
        response = client.post(f"/admin/users/{999999 if invalid == 'unknown' else target}/password",
            headers={"cookie": f"lg_admin_session={root_token}"},
            data={"csrf_token": "wrong" if invalid == "csrf" else csrf,
                  "password": "tiny" if invalid == "short" else "replacement-pass"}, follow_redirects=False)
        assert response.status_code == {"csrf": 403, "short": 303, "unknown": 400}[invalid]
        if invalid == "short":
            assert "err=" in response.headers["location"]
        ping(ws)
        with ctx.db.connect() as conn:
            assert dict(users.get_with_hash(conn, "second-root")) == before
            assert sessions.lookup(conn, token, "viewer") is not None
            assert sessions.lookup(conn, admin_token, "admin") is not None
