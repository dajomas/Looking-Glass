"""End-to-end RBAC + workflow tests against both FastAPI apps."""

import json
import re

import pytest
from fastapi.testclient import TestClient

from conftest import png_bytes, two_room_scene
from looking_glass.rbac import Role
from looking_glass.repositories import users as users_repo
from looking_glass.services import images
from looking_glass.web.app_factory import create_admin_app, create_viewer_app
from looking_glass.web.context import AppContext


@pytest.fixture
def env(settings):
    images.configure(10**8)
    ctx = AppContext.build(settings)
    with ctx.db.connect() as conn:
        users_repo.create(conn, "root", "rootpass1", Role.SUPERADMIN)
        users_repo.create(conn, "dm", "dmpass123", Role.ADMIN)
        users_repo.create(conn, "dm2", "dmpass123", Role.ADMIN)
        users_repo.create(conn, "alice", "alicepass", Role.VIEWER)
        users_repo.create(conn, "bob", "bobpass12", Role.VIEWER)
    return ctx, create_admin_app(ctx), create_viewer_app(ctx)


def login(app, username, password) -> TestClient:
    c = TestClient(app, base_url="http://testserver")
    r = c.post("/login", data={"username": username, "password": password}, follow_redirects=False)
    assert r.status_code == 303, r.text
    return c


def csrf_of(client: TestClient, path="/") -> str:
    html = client.get(path).text
    return re.search(r'name="csrf-token" content="([^"]+)"', html).group(1)


def test_viewer_cannot_use_admin_port(env):
    _, admin, _ = env
    c = TestClient(admin)
    r = c.post("/login", data={"username": "alice", "password": "alicepass"}, follow_redirects=False)
    assert r.status_code == 403


def test_unauthenticated_redirects(env):
    _, admin, viewer = env
    assert TestClient(admin).get("/", follow_redirects=False).headers["location"].startswith("/login")
    assert TestClient(viewer).get("/", follow_redirects=False).headers["location"] == "/login"
    assert TestClient(admin).get("/api/maps/1").status_code == 401


def test_admin_cookie_not_valid_on_viewer_port(env):
    _, admin, viewer = env
    a = login(admin, "dm", "dmpass123")
    v = TestClient(viewer, cookies={"lg_viewer_session": a.cookies.get("lg_admin_session")})
    assert v.get("/", follow_redirects=False).headers["location"] == "/login"


def test_user_management_is_superadmin_only(env):
    _, admin, _ = env
    dm = login(admin, "dm", "dmpass123")
    assert dm.get("/users").status_code == 403
    root = login(admin, "root", "rootpass1")
    token = csrf_of(root, "/users")
    r = root.post("/users", data={"csrf_token": token, "username": "carol", "password": "carolpass",
                                  "role": "viewer"}, follow_redirects=False)
    assert r.status_code == 303 and "ok=" in r.headers["location"]
    # CSRF required
    assert root.post("/users", data={"username": "x", "password": "y" * 10, "role": "viewer"}).status_code == 403


def test_last_superadmin_protected(env):
    ctx, admin, _ = env
    root = login(admin, "root", "rootpass1")
    token = csrf_of(root, "/users")
    r = root.post("/users/1/update", data={"csrf_token": token, "role": "admin", "active": "true"})
    assert r.status_code == 400


def test_full_campaign_flow(env):
    ctx, admin, viewer = env
    dm = login(admin, "dm", "dmpass123")
    token = csrf_of(dm)
    r = dm.post("/campaigns", data={"csrf_token": token, "name": "Curse of Strahd"}, follow_redirects=False)
    cid = int(r.headers["location"].split("/")[2].split("?")[0])

    # other admin cannot see / manage it
    dm2 = login(admin, "dm2", "dmpass123")
    assert dm2.get(f"/campaigns/{cid}").status_code == 403

    # import map + Foundry walls in one go
    r = dm.post(f"/campaigns/{cid}/maps", data={"csrf_token": token, "name": "Crypt"},
                files={"image": ("crypt.png", png_bytes(), "image/png"),
                       "walls": ("scene.json", json.dumps(two_room_scene()).encode(), "application/json")},
                follow_redirects=False)
    assert r.status_code == 303 and "5+walls" in r.headers["location"], r.headers["location"]
    mid = int(r.headers["location"].split("/")[2].split("?")[0])

    hdr = {"X-CSRF-Token": token}
    m = dm.get(f"/api/maps/{mid}").json()
    assert len(m["walls"]) == 5 and m["calibration"]["offset_x"] == 100
    assert dm.post(f"/api/maps/{mid}/reveal", json={"x": 100, "y": 100}).status_code == 403  # no csrf
    res = dm.post(f"/api/maps/{mid}/reveal", json={"x": 100, "y": 100}, headers=hdr).json()
    assert res["op_count"] == 1 and not res["leak_warning"] and 0.3 < res["area_fraction"] < 0.5

    # assign alice, show map
    dm.post(f"/campaigns/{cid}/viewers/add", data={"csrf_token": token, "user_id": 4})
    assert dm.post(f"/api/campaigns/{cid}/active", json={"map_id": mid, "fog_action": "restore"}, headers=hdr).json()["ok"]

    alice = login(viewer, "alice", "alicepass")
    assert alice.get("/", follow_redirects=False).headers["location"] == f"/c/{cid}"
    st = alice.get(f"/api/c/{cid}/state").json()
    assert st["map"]["name"] == "Crypt"
    img = alice.get(st["map"]["image_url"])
    assert img.status_code == 200 and img.headers["content-type"] == "image/png"
    # viewers never get the raw map or the admin API
    assert alice.get(f"/api/maps/{mid}/image").status_code == 404

    # bob is not assigned
    bob = login(viewer, "bob", "bobpass12")
    assert bob.get(f"/c/{cid}").status_code == 404
    assert bob.get(f"/api/c/{cid}/state").status_code == 404

    # live update over websocket
    with alice.websocket_connect(f"/ws/c/{cid}") as ws:
        dm.post(f"/api/maps/{mid}/reveal", json={"x": 300, "y": 100}, headers=hdr)
        assert json.loads(ws.receive_text())["type"] == "refresh"
    assert alice.get(f"/api/c/{cid}/state").json()["map"]["version"] != st["map"]["version"]

    # undo / reveal-all / reset
    assert dm.post(f"/api/maps/{mid}/undo", headers=hdr).json()["op_count"] == 1
    dm.post(f"/api/maps/{mid}/reveal-all", headers=hdr)
    dm.post(f"/api/maps/{mid}/reset", headers=hdr)

    # bob cannot open websocket
    with pytest.raises(Exception):
        with bob.websocket_connect(f"/ws/c/{cid}") as ws:
            ws.receive_text()

    # pages render
    for path in ("/", f"/campaigns/{cid}", f"/maps/{mid}", "/account"):
        assert dm.get(path).status_code == 200, path
    assert alice.get(f"/c/{cid}").status_code == 200


def test_admin_creates_viewer_who_must_change_password(env):
    _, admin, viewer = env
    dm = login(admin, "dm", "dmpass123")
    token = csrf_of(dm)
    cid = int(dm.post("/campaigns", data={"csrf_token": token, "name": "C"}, follow_redirects=False)
              .headers["location"].split("/")[2].split("?")[0])
    r = dm.post(f"/campaigns/{cid}/viewers/create",
                data={"csrf_token": token, "username": "newbie", "password": "temp-pass-1"}, follow_redirects=False)
    assert "ok=" in r.headers["location"]
    v = TestClient(viewer)
    r = v.post("/login", data={"username": "newbie", "password": "temp-pass-1"}, follow_redirects=False)
    assert r.headers["location"] == "/account"
    assert v.get(f"/c/{cid}", follow_redirects=False).headers["location"] == "/account"
    t = csrf_of(v, "/account")
    v.post("/account", data={"csrf_token": t, "current_password": "temp-pass-1",
                             "new_password": "brand-new-pw", "confirm_password": "brand-new-pw"})
    assert v.get(f"/c/{cid}").status_code == 200
