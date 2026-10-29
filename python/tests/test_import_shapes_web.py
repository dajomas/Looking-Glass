"""Real-app bug 12 HTTP/DB regressions. Requires normal runtime dependencies.

Prepared but not executed in the assistant sandbox. No import-time skips: missing
application dependencies must not be mistaken for passing acceptance.
"""
import json
from urllib.parse import unquote_plus

import pytest

from conftest import png_bytes, two_room_scene
from test_web import env, login, csrf_of  # noqa: F401
from test_wall_sources_web import _campaign, _map
from test_import_shapes import MALFORMED, encode, good_scene, make_pack
from looking_glass.repositories import wall_sources as sources_repo


CASES = ("door_string", "walls_number", "resolution_string", "missing_endpoint_y")


@pytest.fixture
def imports(env):
    ctx, admin, _ = env
    dm = login(admin, "dm", "dmpass123")
    token = csrf_of(dm)
    cid = _campaign(dm, token, "Malformed import policy")
    mid = _map(dm, token, cid, walls=json.dumps(two_room_scene()).encode())
    try:
        yield ctx, dm, token, {"X-CSRF-Token": token}, cid, mid
    finally:
        dm.close()


def snapshot(ctx, cid, mid):
    with ctx.db.connect() as conn:
        return {
            "map": tuple(conn.execute("SELECT * FROM maps WHERE id=?", (mid,)).fetchone()),
            "walls": [tuple(row) for row in conn.execute("SELECT * FROM walls WHERE map_id=? ORDER BY id", (mid,))],
            "sources": [tuple(row) for row in conn.execute("SELECT * FROM wall_sources WHERE campaign_id=? ORDER BY id", (cid,))],
            "campaign": tuple(conn.execute("SELECT * FROM campaigns WHERE id=?", (cid,)).fetchone()),
        }


@pytest.mark.parametrize("case", CASES)
@pytest.mark.parametrize("operation", ["inspect", "apply", "save"])
def test_direct_malformed_rejection_preserves_persistent_state(imports, case, operation):
    ctx, dm, token, headers, cid, mid = imports
    before = snapshot(ctx, cid, mid)
    raw = encode(MALFORMED[case])
    if operation == "save":
        endpoint = f"/api/campaigns/{cid}/wall-sources"
    else:
        endpoint = f"/api/maps/{mid}/walls" + ("/inspect" if operation == "inspect" else "")
    response = dm.post(endpoint, headers=headers, files={"file": ("malformed.json", raw, "application/json")})
    assert response.status_code == 400, response.text
    assert snapshot(ctx, cid, mid) == before


@pytest.mark.parametrize("case", CASES)
@pytest.mark.parametrize("operation", ["inspect", "apply"])
def test_legacy_saved_malformed_source_is_rejected_without_mutation(imports, case, operation):
    ctx, dm, token, headers, cid, mid = imports
    raw = encode(MALFORMED[case])
    # Deliberately seed source bytes without parsing to model existing stored data.
    with ctx.db.connect() as conn:
        sid = sources_repo.save(conn, cid, "legacy-malformed.json", raw, 1)["id"]
    before = snapshot(ctx, cid, mid)
    if operation == "inspect":
        response = dm.get(f"/api/maps/{mid}/wall-sources/{sid}")
    else:
        response = dm.post(f"/api/maps/{mid}/walls/from-source", headers=headers,
                           json={"source_id": sid, "scene_index": 0, "use_pack_image": True})
    assert response.status_code == 400, response.text
    assert snapshot(ctx, cid, mid) == before


@pytest.mark.parametrize("case", CASES)
def test_map_upload_malformed_walls_retains_map_not_source(imports, case):
    ctx, dm, token, headers, cid, mid = imports
    before = snapshot(ctx, cid, mid)
    with ctx.db.connect() as conn:
        map_count = conn.execute("SELECT COUNT(*) FROM maps WHERE campaign_id=?", (cid,)).fetchone()[0]
    response = dm.post(f"/campaigns/{cid}/maps", data={"csrf_token": token, "name": "Partial success"},
        files={"image": ("map.png", png_bytes(), "image/png"),
               "walls": ("malformed.json", encode(MALFORMED[case]), "application/json")},
        follow_redirects=False)
    assert response.status_code == 303, response.text
    assert "walls not imported" in unquote_plus(response.headers["location"])
    new_mid = int(response.headers["location"].split("/")[2].split("?")[0])
    with ctx.db.connect() as conn:
        assert conn.execute("SELECT COUNT(*) FROM maps WHERE campaign_id=?", (cid,)).fetchone()[0] == map_count + 1
        row = conn.execute("SELECT * FROM maps WHERE id=?", (new_mid,)).fetchone()
        assert row is not None and row["campaign_id"] == cid
        assert (ctx.settings.maps_dir / row["image_file"]).is_file()
        assert conn.execute("SELECT COUNT(*) FROM walls WHERE map_id=?", (new_mid,)).fetchone()[0] == 0
    after = snapshot(ctx, cid, mid)
    assert after["map"] == before["map"]
    assert after["walls"] == before["walls"]
    assert after["sources"] == before["sources"]


@pytest.mark.parametrize("mixed", [False, True])
def test_zip_http_policy_and_original_source_bytes(imports, mixed):
    ctx, dm, token, headers, cid, mid = imports
    entries = [("bad.json", encode(MALFORMED["missing_endpoint_y"]))]
    if mixed:
        entries.append(("good.json", encode(good_scene())))
    raw = make_pack(entries)
    before = snapshot(ctx, cid, mid)
    response = dm.post(f"/api/campaigns/{cid}/wall-sources", headers=headers,
                       files={"file": ("pack.zip", raw, "application/zip")})
    if not mixed:
        assert response.status_code == 400, response.text
        assert snapshot(ctx, cid, mid) == before
        return
    assert response.status_code == 200, response.text
    sid = response.json()["source"]["id"]
    assert response.json()["source"]["scene_count"] == 1
    with ctx.db.connect() as conn:
        assert sources_repo.get(conn, cid, sid)["raw"] == raw
    inspected = dm.get(f"/api/maps/{mid}/wall-sources/{sid}")
    assert inspected.status_code == 200, inspected.text
    assert [scene["name"] for scene in inspected.json()["scenes"]] == ["Kept"]
    applied = dm.post(f"/api/maps/{mid}/walls/from-source", headers=headers,
                      json={"source_id": sid, "scene_index": 0})
    assert applied.status_code == 200, applied.text
    assert applied.json()["imported"] == 1


@pytest.mark.parametrize("use_scene", [False, True])
def test_malformed_direct_apply_preserves_existing_calibration(imports, use_scene):
    ctx, dm, token, headers, cid, mid = imports
    before = snapshot(ctx, cid, mid)
    response = dm.post(f"/api/maps/{mid}/walls", headers=headers,
        data={"use_scene_calibration": str(use_scene).lower()},
        files={"file": ("malformed.json", encode(MALFORMED["door_string"]), "application/json")})
    assert response.status_code == 400, response.text
    assert snapshot(ctx, cid, mid) == before


def test_post_parse_target_rejection_retains_upload_source(imports):
    ctx, dm, token, headers, cid, mid = imports
    # Finite source coordinates parse, but actual target scaling overflows.
    raw = encode({"walls": [{"c": [0, 0, 1e308, 0]}], "width": 100, "height": 100, "padding": 0})
    response = dm.post(f"/campaigns/{cid}/maps", data={"csrf_token": token, "name": "Retained source"},
        files={"image": ("map.png", png_bytes(400, 200), "image/png"),
               "walls": ("target-rejected.json", raw, "application/json")}, follow_redirects=False)
    assert response.status_code == 303, response.text
    assert "walls not imported" in unquote_plus(response.headers["location"])
    new_mid = int(response.headers["location"].split("/")[2].split("?")[0])
    with ctx.db.connect() as conn:
        source = conn.execute("SELECT * FROM wall_sources WHERE campaign_id=? AND raw=?", (cid, raw)).fetchone()
        assert source is not None
        assert conn.execute("SELECT COUNT(*) FROM walls WHERE map_id=?", (new_mid,)).fetchone()[0] == 0
        row = conn.execute("SELECT * FROM maps WHERE id=?", (new_mid,)).fetchone()
        assert row is not None
        assert (ctx.settings.maps_dir / row["image_file"]).is_file()
