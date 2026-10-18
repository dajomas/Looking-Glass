"""Run with the application's normal requirements installed."""
import json

from conftest import png_bytes
from test_web import env, login, csrf_of  # noqa: F401 -- import shared fixture
from looking_glass.services.foundry_import import parse_wall_file


def prepare(env):
    ctx, admin, viewer = env
    dm = login(admin, "dm", "dmpass123")
    token = csrf_of(dm)
    response = dm.post("/campaigns", data={"csrf_token": token, "name": "Walls"}, follow_redirects=False)
    cid = int(response.headers["location"].split("/")[2].split("?")[0])
    response = dm.post(f"/campaigns/{cid}/maps", data={"csrf_token": token, "name": "Room"},
                       files={"image": ("room.png", png_bytes(), "image/png")}, follow_redirects=False)
    mid = int(response.headers["location"].split("/")[2].split("?")[0])
    return ctx, admin, viewer, dm, {"X-CSRF-Token": token}, mid


def draft(dm, mid, walls=None):
    data = dm.get(f"/api/maps/{mid}/wall-editor").json()
    return {"walls_version": data["walls_version"], "cache_token": data["cache_token"],
            "walls": walls or [], "pixels_per_grid": 70,
            "width": data["width"], "height": data["height"], "image_version": data["image_version"]}


def test_wall_editor_save_source_export_and_conflict(env):
    ctx, admin, viewer, dm, headers, mid = prepare(env)
    body = draft(dm, mid, [[10, 20, 100, 20, "secret", True], [100, 20, 100, 80, "ethereal", False]])
    assert dm.get(f"/maps/{mid}/walls").status_code == 200
    assert f'/maps/{mid}/walls' in dm.get(f"/maps/{mid}").text
    assert dm.post(f"/api/maps/{mid}/wall-editor", json=body).status_code == 403
    saved = dm.post(f"/api/maps/{mid}/wall-editor", json=body, headers=headers)
    assert saved.status_code == 200, saved.text
    assert saved.json()["walls"] == body["walls"]
    assert dm.post(f"/api/maps/{mid}/wall-editor", json=body, headers=headers).status_code == 409
    with ctx.db.connect() as conn:
        source = conn.execute("SELECT raw FROM wall_sources WHERE id=?", (saved.json()["source_id"],)).fetchone()
        assert [s.kind for s in parse_wall_file(source["raw"])[0].segments] == ["secret", "ethereal"]
        m = conn.execute("SELECT * FROM maps WHERE id=?", (mid,)).fetchone()
        assert (m["wall_offset_x"], m["wall_offset_y"], m["wall_scale_x"], m["wall_scale_y"]) == (0, 0, 1, 1)
    export = dm.get(f"/api/maps/{mid}/walls.uvtt?include_image=true")
    assert export.status_code == 200
    assert export.json()["image"]
    assert export.headers["cache-control"] == "no-store"
    assert dm.get(f"/api/maps/{mid}/wall-editor").headers["cache-control"] == "no-store"


def test_editor_permission_and_viewer_isolation(env):
    _, admin, viewer, dm, headers, mid = prepare(env)
    dm2 = login(admin, "dm2", "dmpass123")
    body = draft(dm, mid)
    for path in (f"/maps/{mid}/walls", f"/api/maps/{mid}/wall-editor", f"/api/maps/{mid}/walls.uvtt"):
        assert dm2.get(path).status_code == 403
        from fastapi.testclient import TestClient
        assert TestClient(viewer).get(path).status_code == 404
    token2 = csrf_of(dm2)
    assert dm2.post(f"/api/maps/{mid}/wall-editor", json=body, headers={"X-CSRF-Token": token2}).status_code == 403


def test_draft_export_does_not_save_and_can_rescue_conflicts(env):
    ctx, _, _, dm, headers, mid = prepare(env)
    body = draft(dm, mid, [[1, 2, 3, 4, "door", True]])
    assert dm.post(f"/api/maps/{mid}/wall-editor", json=body, headers=headers).status_code == 200
    body["walls"] = [[5, 6, 7, 8, "window", True]]
    response = dm.post(f"/api/maps/{mid}/wall-editor/export", json=body, headers=headers)
    assert response.status_code == 200
    assert parse_wall_file(response.content)[0].segments[0].kind == "window"
    assert dm.get(f"/api/maps/{mid}/wall-editor").json()["walls"][0][4] == "door"
    body["include_image"] = True
    body["image_version"] = "obsolete.png"
    assert dm.post(f"/api/maps/{mid}/wall-editor/export", json=body, headers=headers).status_code == 409


def test_empty_save_and_invalid_input_are_atomic(env):
    ctx, _, _, dm, headers, mid = prepare(env)
    body = draft(dm, mid, [[1, 2, 3, 4, "wall", True]])
    assert dm.post(f"/api/maps/{mid}/wall-editor", json=body, headers=headers).status_code == 200
    bad = draft(dm, mid, [[1, 2, 1, 2, "wall", True]])
    assert dm.post(f"/api/maps/{mid}/wall-editor", json=bad, headers=headers).status_code == 400
    assert len(dm.get(f"/api/maps/{mid}/wall-editor").json()["walls"]) == 1
    body = draft(dm, mid)
    assert dm.post(f"/api/maps/{mid}/wall-editor", json=body, headers=headers).status_code == 200
    assert parse_wall_file(dm.get(f"/api/maps/{mid}/walls.uvtt").content)[0].segments == []


def test_existing_fog_and_type_settings_are_retained(env):
    ctx, _, _, dm, headers, mid = prepare(env)
    dm.post(f"/api/maps/{mid}/reveal-all", headers=headers)
    with ctx.db.connect() as conn:
        conn.execute("INSERT OR REPLACE INTO map_wall_type_settings(map_id, disabled_types) VALUES (?, ?)", (mid, '["window"]'))
        conn.execute("UPDATE maps SET doors_block=0 WHERE id=?", (mid,))
        before = conn.execute("SELECT COUNT(*) FROM fog_ops WHERE map_id=?", (mid,)).fetchone()[0]
    body = draft(dm, mid, [[1, 2, 3, 4, "window", True]])
    assert dm.post(f"/api/maps/{mid}/wall-editor", json=body, headers=headers).status_code == 200
    with ctx.db.connect() as conn:
        assert conn.execute("SELECT COUNT(*) FROM fog_ops WHERE map_id=?", (mid,)).fetchone()[0] == before
        assert conn.execute("SELECT doors_block FROM maps WHERE id=?", (mid,)).fetchone()[0] == 0
        assert json.loads(conn.execute("SELECT disabled_types FROM map_wall_type_settings WHERE map_id=?", (mid,)).fetchone()[0]) == ["window"]
