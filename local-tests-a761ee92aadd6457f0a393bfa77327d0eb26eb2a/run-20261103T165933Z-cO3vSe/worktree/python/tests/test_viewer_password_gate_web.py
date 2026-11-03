"""ASGI acceptance for the viewer password-change gate; normal dependencies required."""
import queue
import threading

import pytest
pytest.importorskip("fastapi")
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from test_web import env, login, csrf_of
from looking_glass.repositories import sessions
from looking_glass.web.viewer import api


@pytest.fixture
def campaign(env):
    ctx, admin, viewer = env
    dm = login(admin, "dm", "dmpass123")
    csrf = csrf_of(dm)
    result = dm.post("/campaigns", data={"csrf_token": csrf, "name": "Password gate"},
                     follow_redirects=False)
    assert result.status_code == 303
    cid = int(result.headers["location"].split("/")[2].split("?")[0])
    result = dm.post(f"/campaigns/{cid}/viewers/add", data={"csrf_token": csrf, "user_id": 4},
                     follow_redirects=False)
    assert result.status_code == 303
    @viewer.post("/__test__/publish")
    async def publish():
        await ctx.hub.publish(cid, {"type": "refresh"})
        return {"ok": True}
    return ctx, viewer, cid


def session(ctx, user_id):
    with ctx.db.connect() as conn:
        return sessions.create(conn, user_id, "viewer", 3600)


def flag(ctx, user_id, required):
    with ctx.db.connect() as conn:
        conn.execute("UPDATE users SET must_change_password=? WHERE id=?", (int(required), user_id))


def headers(token):
    return {"cookie": f"lg_viewer_session={token}"}


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
        pytest.fail("Timed out waiting for password-gate WebSocket response")
    if isinstance(frame, Exception):
        raise frame
    return frame


def ping(ws):
    ws.send_text("ping")
    assert receive(ws) == {"type": "websocket.send", "text": '{"type":"pong"}'}


@pytest.mark.parametrize("user_id", [1, 2, 4], ids=["superadmin", "admin", "viewer"])
def test_required_change_cannot_subscribe_for_any_role(campaign, user_id):
    ctx, viewer, cid = campaign
    token, _ = session(ctx, user_id)
    flag(ctx, user_id, True)
    with TestClient(viewer) as client:
        with pytest.raises(WebSocketDisconnect) as error:
            with client.websocket_connect(f"/ws/c/{cid}", headers=headers(token)):
                pass
        assert error.value.code == 4403
        assert ctx.hub.viewer_count(cid) == 0


def test_new_flag_blocks_broadcast_without_disrupting_other_user(campaign):
    ctx, viewer, cid = campaign
    alice, _ = session(ctx, 4)
    other, _ = session(ctx, 1)
    with TestClient(viewer) as client:
        with client.websocket_connect(f"/ws/c/{cid}", headers=headers(alice)) as ws, \
             client.websocket_connect(f"/ws/c/{cid}", headers=headers(other)) as valid:
            ping(ws)
            ping(valid)
            flag(ctx, 4, True)
            assert client.post("/__test__/publish").status_code == 200
            assert receive(ws)["code"] == 4403
            assert '"refresh"' in receive(valid)["text"]
            ping(valid)
            assert ctx.hub.viewer_count(cid) == 1


def test_idle_connection_observes_new_flag(campaign, monkeypatch):
    ctx, viewer, cid = campaign
    monkeypatch.setattr(api, "SESSION_RECHECK_SECONDS", 0.01)
    token, _ = session(ctx, 4)
    with TestClient(viewer) as client:
        with client.websocket_connect(f"/ws/c/{cid}", headers=headers(token)) as ws:
            ping(ws)
            flag(ctx, 4, True)
            assert receive(ws)["code"] == 4403


def test_account_change_clears_requirement_and_allows_reconnect(campaign):
    ctx, viewer, cid = campaign
    token, csrf = session(ctx, 4)
    flag(ctx, 4, True)
    with TestClient(viewer) as client:
        client.cookies.set("lg_viewer_session", token)
        assert client.get("/account").status_code == 200
        with pytest.raises(WebSocketDisconnect) as error:
            with client.websocket_connect(f"/ws/c/{cid}"):
                pass
        assert error.value.code == 4403
        response = client.post("/account", data={"csrf_token": csrf, "current_password": "alicepass",
                               "new_password": "alicepass-new", "confirm_password": "alicepass-new"},
                               follow_redirects=False)
        assert response.status_code == 303 and response.headers["location"].startswith("/account?ok=")
        with ctx.db.connect() as conn:
            assert not sessions.lookup(conn, token, "viewer")["must_change_password"]
        with client.websocket_connect(f"/ws/c/{cid}") as ws:
            ping(ws)


def test_required_change_user_can_still_logout(campaign):
    ctx, viewer, _ = campaign
    token, csrf = session(ctx, 4)
    flag(ctx, 4, True)
    with TestClient(viewer) as client:
        response = client.post("/logout", headers=headers(token), data={"csrf_token": csrf},
                               follow_redirects=False)
        assert response.status_code == 303
        with ctx.db.connect() as conn:
            assert sessions.lookup(conn, token, "viewer") is None
