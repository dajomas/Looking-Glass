"""ASGI WebSocket regressions; requires the normal application dependencies."""
import queue
import threading

import pytest

pytest.importorskip("fastapi")
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from test_web import env, login, csrf_of
from looking_glass.repositories import sessions
from looking_glass.security import token_hash
from looking_glass.web.viewer import api


@pytest.fixture
def campaign(env):
    ctx, admin, viewer = env
    dm = login(admin, "dm", "dmpass123")
    csrf = csrf_of(dm)
    result = dm.post("/campaigns", data={"csrf_token": csrf, "name": "Socket lifetime"},
                     follow_redirects=False)
    cid = int(result.headers["location"].split("/")[2].split("?")[0])
    dm.post(f"/campaigns/{cid}/viewers/add", data={"csrf_token": csrf, "user_id": 4})

    @viewer.post("/__test__/publish")
    async def publish():
        await ctx.hub.publish(cid, {"type": "refresh"})
        return {"ok": True}

    return ctx, viewer, cid


def sign_in(client):
    result = client.post("/login", data={"username": "alice", "password": "alicepass"},
                         follow_redirects=False)
    assert result.status_code == 303
    return client.cookies.get("lg_viewer_session")


def headers(token):
    return {"cookie": f"lg_viewer_session={token}"}


def receive(ws):
    """Bound failed regressions rather than hanging on an absent server frame."""
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
        pytest.fail("Timed out waiting for a WebSocket frame")
    if isinstance(frame, Exception):
        raise frame
    return frame


def ping(ws):
    ws.send_text("ping")
    assert receive(ws) == {"type": "websocket.send", "text": '{"type":"pong"}'}


def test_logout_closes_only_matching_session_and_all_its_tabs(campaign):
    ctx, viewer, cid = campaign
    with TestClient(viewer) as client:
        a = sign_in(client)
        b = sign_in(client)
        with client.websocket_connect(f"/ws/c/{cid}", headers=headers(a)) as first, \
             client.websocket_connect(f"/ws/c/{cid}", headers=headers(a)) as second, \
             client.websocket_connect(f"/ws/c/{cid}", headers=headers(b)) as other:
            for ws in (first, second, other):
                ping(ws)
            with ctx.db.connect() as conn:
                csrf = sessions.lookup(conn, a, "viewer")["csrf_token"]
            response = client.post("/logout", data={"csrf_token": csrf}, headers=headers(a),
                                   follow_redirects=False)
            assert response.status_code == 303
            assert receive(first)["code"] == receive(second)["code"] == 4403
            ping(other)
            assert ctx.hub.viewer_count(cid) == 1
            with ctx.db.connect() as conn:
                assert sessions.lookup(conn, a, "viewer") is None
                assert sessions.lookup(conn, b, "viewer") is not None


def test_expired_session_gets_no_broadcast(campaign):
    ctx, viewer, cid = campaign
    with TestClient(viewer) as client:
        token = sign_in(client)
        with client.websocket_connect(f"/ws/c/{cid}") as ws:
            ping(ws)
            with ctx.db.connect() as conn:
                conn.execute("UPDATE sessions SET expires_at=0 WHERE token_hash=?", (token_hash(token),))
            assert client.post("/__test__/publish").status_code == 200
            assert receive(ws)["code"] == 4403
            assert ctx.hub.viewer_count(cid) == 0


def test_idle_revoked_socket_closes_without_ping_or_broadcast(campaign, monkeypatch):
    ctx, viewer, cid = campaign
    monkeypatch.setattr(api, "SESSION_RECHECK_SECONDS", 0.01)
    with TestClient(viewer) as client:
        token = sign_in(client)
        with client.websocket_connect(f"/ws/c/{cid}") as ws:
            ping(ws)
            with ctx.db.connect() as conn:
                sessions.delete(conn, token)
            assert receive(ws)["code"] == 4403
            assert ctx.hub.viewer_count(cid) == 0


def test_removed_campaign_assignment_prevents_event(campaign):
    ctx, viewer, cid = campaign
    with TestClient(viewer) as client:
        sign_in(client)
        with client.websocket_connect(f"/ws/c/{cid}") as ws:
            ping(ws)
            with ctx.db.connect() as conn:
                conn.execute("DELETE FROM campaign_viewers WHERE campaign_id=?", (cid,))
            client.post("/__test__/publish")
            assert receive(ws)["code"] == 4403


def test_revoked_socket_cannot_report_ready(campaign):
    ctx, viewer, cid = campaign
    with TestClient(viewer) as client:
        token = sign_in(client)
        with client.websocket_connect(f"/ws/c/{cid}") as ws:
            ping(ws)
            with ctx.db.connect() as conn:
                sessions.delete(conn, token)
            ws.send_json({"type": "viewer-status", "state": "ready", "version": "blank"})
            assert receive(ws)["code"] == 4403
            rows = ctx.hub.sync.snapshot(cid, "blank")
            assert rows["counts"]["up-to-date"] == 0


def test_logout_during_accept_is_caught_after_subscription(campaign, monkeypatch):
    ctx, viewer, cid = campaign
    original = ctx.hub.subscribe
    async def subscribe_after_revoke(campaign_id, ws):
        with ctx.db.connect() as conn:
            conn.execute("DELETE FROM sessions WHERE token_hash=?", (ws.state.session_hash,))
        await original(campaign_id, ws)
    monkeypatch.setattr(ctx.hub, "subscribe", subscribe_after_revoke)
    with TestClient(viewer) as client:
        sign_in(client)
        with client.websocket_connect(f"/ws/c/{cid}") as ws:
            assert receive(ws)["code"] == 4403
            assert ctx.hub.viewer_count(cid) == 0


def test_missing_session_still_fails_admission(campaign):
    _, viewer, cid = campaign
    with TestClient(viewer) as client:
        with pytest.raises(WebSocketDisconnect) as error:
            with client.websocket_connect(f"/ws/c/{cid}"):
                pass
        assert error.value.code == 4401
