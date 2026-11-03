"""HTTP/WebSocket acceptance for role-update kicks; normal dependencies required."""
import queue
import threading

import pytest
pytest.importorskip("fastapi")
from fastapi import FastAPI
from fastapi.testclient import TestClient

from test_web import env
from looking_glass.rbac import Role
from looking_glass.repositories import users, sessions


@pytest.fixture
def campaign(env):
    ctx, admin, viewer = env
    with ctx.db.connect() as conn:
        target = users.create(conn, "second-root", "secondroot-pass", Role.SUPERADMIN)
        viewer_token, _ = sessions.create(conn, target, "viewer", 3600)
        admin_token, _ = sessions.create(conn, target, "admin", 3600)
        root_token, csrf = sessions.create(conn, 1, "admin", 3600)
        alice_token, _ = sessions.create(conn, 4, "viewer", 3600)
        dm_token, dm_csrf = sessions.create(conn, 2, "admin", 3600)
    app = FastAPI()
    app.mount("/admin", admin)
    app.mount("/viewer", viewer)
    with TestClient(app) as client:
        response = client.post("/admin/campaigns", headers={"cookie": f"lg_admin_session={dm_token}"},
                               data={"csrf_token": dm_csrf, "name": "Role revocation"}, follow_redirects=False)
        assert response.status_code == 303
        cid = int(response.headers["location"].split("/")[2].split("?")[0])
        response = client.post(f"/admin/campaigns/{cid}/viewers/add",
                               headers={"cookie": f"lg_admin_session={dm_token}"},
                               data={"csrf_token": dm_csrf, "user_id": 4}, follow_redirects=False)
        assert response.status_code == 303
        yield ctx, client, cid, target, viewer_token, admin_token, root_token, csrf, alice_token


def receive(ws):
    result = queue.Queue()
    def read():
        try:
            result.put(ws.receive())
        except Exception as error:
            result.put(error)
    threading.Thread(target=read, daemon=True).start()
    try:
        frame = result.get(timeout=3)
    except queue.Empty:
        pytest.fail("No immediate server frame after user update")
    if isinstance(frame, Exception):
        raise frame
    return frame


def ping(ws):
    ws.send_text("ping")
    assert receive(ws) == {"type": "websocket.send", "text": '{"type":"pong"}'}


@pytest.mark.parametrize("new_role", ["admin", "viewer"])
def test_demotion_kicks_without_waiting_for_event_or_idle_timer(campaign, new_role):
    ctx, client, cid, target, token, admin_token, root_token, csrf, alice = campaign
    with client.websocket_connect(f"/viewer/ws/c/{cid}", headers={"cookie": f"lg_viewer_session={token}"}) as ws, \
         client.websocket_connect(f"/viewer/ws/c/{cid}", headers={"cookie": f"lg_viewer_session={alice}"}) as other:
        ping(ws)
        ping(other)
        response = client.post(f"/admin/users/{target}/update",
                               headers={"cookie": f"lg_admin_session={root_token}"},
                               data={"csrf_token": csrf, "role": new_role, "active": "true"}, follow_redirects=False)
        assert response.status_code == 303
        assert receive(ws)["code"] == 4403
        ping(other)
        assert ctx.hub.viewer_count(cid) == 1
        with ctx.db.connect() as conn:
            assert sessions.lookup(conn, token, "viewer") is None
            assert sessions.lookup(conn, admin_token, "admin") is None
            fresh, _ = sessions.create(conn, target, "viewer", 3600)
        denied = client.get(f"/viewer/api/c/{cid}/state", headers={"cookie": f"lg_viewer_session={fresh}"})
        assert denied.status_code in (403, 404)


def test_unchanged_role_profile_save_keeps_socket_and_sessions(campaign):
    ctx, client, cid, target, token, admin_token, root_token, csrf, _ = campaign
    with client.websocket_connect(f"/viewer/ws/c/{cid}", headers={"cookie": f"lg_viewer_session={token}"}) as ws:
        ping(ws)
        response = client.post(f"/admin/users/{target}/update",
                               headers={"cookie": f"lg_admin_session={root_token}"},
                               data={"csrf_token": csrf, "role": "superadmin", "active": "true",
                                     "display_name": "Renamed"}, follow_redirects=False)
        assert response.status_code == 303
        ping(ws)
        with ctx.db.connect() as conn:
            assert sessions.lookup(conn, token, "viewer") is not None
            assert sessions.lookup(conn, admin_token, "admin") is not None


def test_bad_csrf_cannot_change_role_or_disconnect(campaign):
    ctx, client, cid, target, token, _, root_token, _, _ = campaign
    with client.websocket_connect(f"/viewer/ws/c/{cid}", headers={"cookie": f"lg_viewer_session={token}"}) as ws:
        ping(ws)
        response = client.post(f"/admin/users/{target}/update",
                               headers={"cookie": f"lg_admin_session={root_token}"},
                               data={"role": "viewer", "active": "true"}, follow_redirects=False)
        assert response.status_code == 403
        ping(ws)
        with ctx.db.connect() as conn:
            assert users.get(conn, target)["role"] == "superadmin"
