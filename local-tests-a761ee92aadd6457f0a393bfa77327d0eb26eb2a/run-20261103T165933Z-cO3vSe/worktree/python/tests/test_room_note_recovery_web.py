"""Additional recovery contracts; existing archive HTTP cases cover core recovery."""
import pytest
from fastapi.testclient import TestClient

from test_web import env
from test_room_note_archive_web import (
    flow, archives, detach, save, recover, recovery_body, ok, state, viewer_snapshot,
)
from looking_glass.services import room_note_recovery
from looking_glass.web import app_factory
from looking_glass.web.app_factory import create_admin_app, create_viewer_app


def test_archive_pagination_is_complete_disjoint_and_map_scoped(flow):
    f = flow
    source = detach(f)
    for index in range(5):
        save(f, f"Target {index}", f"Replacement {index}")
        ok(recover(f, source, recovery_body(f, overwrite=True)))
    primary = f.mid
    f.mid = f.other_mid
    detach(f)
    f.mid = primary
    with f.ctx.db.connect() as conn:
        expected = [r[0] for r in conn.execute(
            "SELECT id FROM room_note_archives WHERE map_id=? ORDER BY id DESC", (primary,)
        )]
    assert len(expected) == 6
    before, pixels = state(f.ctx), viewer_snapshot(f)
    f.publications.clear()
    seen, cursor = [], None
    while True:
        params = {"limit": 2}
        if cursor is not None:
            params["before_id"] = cursor
        response = f.dm.get(f"/api/maps/{primary}/room-note-archives", params=params)
        page = ok(response)
        assert response.headers["cache-control"] == "no-store"
        assert 0 < len(page["archives"]) <= 2
        assert all(row["map_id"] == primary for row in page["archives"])
        ids = [row["id"] for row in page["archives"]]
        assert not set(ids).intersection(seen)
        seen.extend(ids)
        cursor = page["next_before_id"]
        if cursor is None:
            break
        assert cursor == ids[-1]
        assert len(seen) < len(expected), "Pagination must terminate"
    assert seen == expected
    assert state(f.ctx) == before and viewer_snapshot(f) == pixels
    assert f.publications == []


@pytest.mark.parametrize("params", [
    {"limit": 0}, {"limit": 201}, {"limit": "bad"},
    {"before_id": 0}, {"before_id": -1}, {"before_id": "bad"},
])
def test_invalid_pagination_is_rejected_without_mutation(flow, params):
    detach(flow)
    before = state(flow.ctx)
    response = flow.dm.get(f"/api/maps/{flow.mid}/room-note-archives", params=params)
    assert response.status_code == 422, response.text
    assert state(flow.ctx) == before


@pytest.mark.parametrize("overwrite", [1, "true", None])
def test_recovery_overwrite_requires_a_json_boolean(flow, overwrite):
    source = detach(flow)
    body = recovery_body(flow)
    body["overwrite"] = overwrite
    before = state(flow.ctx)
    response = recover(flow, source, body)
    assert response.status_code == 422, response.text
    assert response.headers["content-type"].split(";")[0] == "application/json"
    error = response.json()
    assert error["ok"] is False
    assert isinstance(error["error"], str)
    assert error["error"].startswith("overwrite:"), error
    assert state(flow.ctx) == before
    assert archives(flow) == [source]


@pytest.mark.parametrize("field", ["name", "markdown"])
def test_recovery_rejects_client_supplied_replacement_content(flow, field):
    source = detach(flow)
    body = {**recovery_body(flow), field: "Do not substitute archive content"}
    before = state(flow.ctx)
    response = recover(flow, source, body)
    assert response.status_code == 422, response.text
    assert state(flow.ctx) == before
    assert archives(flow) == [source]


def test_recovery_services_require_caller_transactions(env):
    ctx, _, _ = env
    with ctx.db.connect() as conn:
        assert not conn.in_transaction
        with pytest.raises(RuntimeError, match="transaction"):
            room_note_recovery.list_archives(conn, 999)
        with pytest.raises(RuntimeError, match="transaction"):
            room_note_recovery.recover_archive(conn, 999, 1, "a" * 64, 1, 1, 0)
        assert not conn.in_transaction


def test_archive_routes_are_per_admin_app_and_absent_from_viewer(env, monkeypatch):
    ctx, _, _ = env
    expected = {
        ("/api/maps/{map_id}/room-note-archives", "GET"),
        ("/api/maps/{map_id}/room-note-archives/{archive_id}/recover", "POST"),
    }
    routers = []
    register = app_factory.register_room_note_archives

    def record_registration(router, *args, **kwargs):
        register(router, *args, **kwargs)
        routers.append(router)

    monkeypatch.setattr(app_factory, "register_room_note_archives", record_registration)
    apps = [create_admin_app(ctx), create_admin_app(ctx)]
    assert len(routers) == 2 and routers[0] is not routers[1]
    for app, router in zip(apps, routers):
        found = [(route.path, method) for route in router.routes
                 for method in getattr(route, "methods", ())
                 if (getattr(route, "path", ""), method) in expected]
        assert set(found) == expected and len(found) == 2
        paths = app.openapi()["paths"]
        assert all(method.lower() in paths.get(path, {}) for path, method in expected)
        with TestClient(app) as client:
            assert client.get("/api/maps/999/room-note-archives").status_code == 401
            assert client.post("/api/maps/999/room-note-archives/1/recover", json={}).status_code == 401
    viewer = create_viewer_app(ctx)
    assert len(routers) == 2
    assert not any("room-note-archives" in path for path in viewer.openapi()["paths"])
    with TestClient(viewer) as client:
        assert client.get("/api/maps/999/room-note-archives").status_code == 404
        assert client.post("/api/maps/999/room-note-archives/1/recover", json={}).status_code == 404
