"""Full-app calibration HTTP/SQLite regressions; no import-time dependency skips."""
import json

import pytest

from conftest import two_room_scene
from test_web import env, login, csrf_of
from test_wall_sources_web import _campaign, _map
from looking_glass.web.admin import calibration as calibration_routes


@pytest.fixture
def setup(env):
    ctx, admin, _ = env
    dm = login(admin, "dm", "dmpass123")
    token = csrf_of(dm)
    cid = _campaign(dm, token, "Manual calibration")
    mid = _map(dm, token, cid, walls=json.dumps(two_room_scene()).encode())
    try:
        yield ctx, admin, dm, {"X-CSRF-Token": token}, cid, mid
    finally:
        dm.close()


def snapshot(ctx):
    with ctx.db.connect() as conn:
        return tuple(conn.iterdump())


def body(**changes):
    return {**dict(offset_x=0, offset_y=0, scale_x=1, scale_y=1, doors_block=True), **changes}


@pytest.mark.parametrize("field", ["offset_x", "offset_y", "scale_x", "scale_y"])
@pytest.mark.parametrize("value", ["Infinity", "-Infinity", "NaN"])
@pytest.mark.parametrize("with_walls", [False, True])
def test_nonfinite_rejected_without_state_or_render_changes(setup, monkeypatch, field, value, with_walls):
    ctx, _, dm, headers, cid, mid = setup
    if not with_walls:
        token = headers["X-CSRF-Token"]
        mid = _map(dm, token, cid)
    assert dm.get(f"/api/maps/{mid}").status_code == 200
    preview = dm.get(f"/api/maps/{mid}/viewer-preview")
    assert preview.status_code == 200
    before = snapshot(ctx)
    calls = []
    monkeypatch.setattr(ctx.fog, "invalidate", lambda *args: calls.append("invalidate"))
    async def changed(*args):
        calls.append("notify")
    monkeypatch.setattr(calibration_routes.notify, "map_changed", changed)
    response = dm.post(f"/api/maps/{mid}/calibration", json=body(**{field: value}), headers=headers)
    assert response.status_code == 422, response.text
    assert snapshot(ctx) == before and calls == []
    assert dm.get(f"/api/maps/{mid}").status_code == 200
    after = dm.get(f"/api/maps/{mid}/viewer-preview")
    assert after.status_code == 200 and after.content == preview.content


@pytest.mark.parametrize("changes", [dict(offset_x=1e308, scale_x=100),
                                     dict(offset_y=-1e308, scale_y=100)])
def test_finite_transform_overflow_is_400_and_has_no_effects(setup, monkeypatch, changes):
    ctx, _, dm, headers, _, mid = setup
    assert dm.get(f"/api/maps/{mid}").status_code == 200
    preview = dm.get(f"/api/maps/{mid}/viewer-preview")
    assert preview.status_code == 200
    before = snapshot(ctx)
    calls = []
    monkeypatch.setattr(ctx.fog, "invalidate", lambda *args: calls.append("invalidate"))
    async def changed(*args):
        calls.append("notify")
    monkeypatch.setattr(calibration_routes.notify, "map_changed", changed)
    response = dm.post(f"/api/maps/{mid}/calibration", json=body(**changes), headers=headers)
    assert response.status_code == 400, response.text
    assert response.json()["ok"] is False
    assert snapshot(ctx) == before and calls == []
    after = dm.get(f"/api/maps/{mid}/viewer-preview")
    assert after.status_code == 200 and after.content == preview.content


def test_valid_negative_offsets_and_scale_still_work(setup):
    ctx, _, dm, headers, _, mid = setup
    before = dm.get(f"/api/maps/{mid}").json()
    values = body(offset_x=-10, offset_y=-20, scale_x=0.5, scale_y=2, doors_block=False)
    response = dm.post(f"/api/maps/{mid}/calibration", json=values, headers=headers)
    assert response.status_code == 200, response.text
    result = response.json()
    assert result["calibration"] == values
    assert result["walls_version"] == before["walls_version"] + 1
    assert result["fog_version"] == before["fog_version"] + 1
    assert dm.get(f"/api/maps/{mid}/viewer-preview").status_code == 200


def test_registration_preserves_authorization_and_csrf(setup):
    ctx, admin, dm, headers, _, mid = setup
    with ctx.db.connect() as conn:
        before = tuple(conn.execute("SELECT * FROM maps WHERE id=?", (mid,)).fetchone())
    assert dm.post(f"/api/maps/{mid}/calibration", json=body()).status_code == 403
    other = login(admin, "dm2", "dmpass123")
    try:
        assert other.post(f"/api/maps/{mid}/calibration", json=body(),
                          headers={"X-CSRF-Token": csrf_of(other)}).status_code == 403
    finally:
        other.close()
    # The second login legitimately creates a session; only the map must be unchanged.
    with ctx.db.connect() as conn:
        row = tuple(conn.execute("SELECT * FROM maps WHERE id=?", (mid,)).fetchone())
    assert row == before
