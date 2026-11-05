"""Bug 28 HTTP/SQLite/pixel regressions; production fix is deliberately separate."""
import io
import json

import pytest
from PIL import Image
from fastapi.testclient import TestClient

from conftest import two_room_scene
from test_web import env, csrf_of, login
from test_fog_response_web import prepare
from looking_glass.web.admin import api
from looking_glass.web.access import fog_inputs


OUTSIDE = [
    pytest.param(-1, 100, id="left"),
    pytest.param(-0.01, 100, id="fractional-left"),
    pytest.param(400, 100, id="exact-width"),
    pytest.param(401, 100, id="right"),
    pytest.param(100, -1, id="top"),
    pytest.param(100, -0.01, id="fractional-top"),
    pytest.param(100, 200, id="exact-height"),
    pytest.param(100, 201, id="bottom"),
    pytest.param(-1, -1, id="negative-corner"),
    pytest.param(400, 200, id="upper-corner"),
]


def state(ctx):
    tables = ("campaigns", "maps", "fog_ops", "map_fog_snapshots")
    with ctx.db.connect() as conn:
        return {table: [tuple(row) for row in conn.execute(
            f"SELECT * FROM {table} ORDER BY rowid")]
            for table in tables}


def pixels(response, mode):
    assert response.status_code == 200, response.text
    with Image.open(io.BytesIO(response.content)) as image:
        converted = image.convert(mode)
        return converted.size, converted.tobytes()


@pytest.fixture
def setup(env):
    ctx, dm, alice, cid, mid = prepare(env)
    headers = {"X-CSRF-Token": csrf_of(dm)}
    return ctx, dm, alice, cid, mid, headers


@pytest.mark.parametrize("op", ["reveal", "hide"])
@pytest.mark.parametrize("x,y", OUTSIDE)
def test_outside_point_rejected_without_side_effects(setup, monkeypatch, op, x, y):
    ctx, dm, alice, cid, mid, headers = setup
    prefix = f"/api/maps/{mid}"
    # The wall-free map has a real area on every edge. Select the baseline
    # so clamping would change visibility rather than take the no-op return.
    initial = "reset" if op == "reveal" else "reveal-all"
    response = dm.post(f"{prefix}/{initial}", headers=headers)
    assert response.status_code == 200, response.text
    before = state(ctx)
    mask = pixels(dm.get(f"{prefix}/fog.png"), "RGBA")
    viewer = pixels(alice.get(f"/api/c/{cid}/image"), "RGB")
    notices, interpreted = [], []
    describe = ctx.fog.describe_click

    async def changed(*args):
        notices.append(args)

    def tracked(*args):
        interpreted.append(args[1:])
        return describe(*args)

    monkeypatch.setattr(api.notify, "map_changed", changed)
    monkeypatch.setattr(ctx.fog, "describe_click", tracked)
    response = dm.post(f"{prefix}/{op}", json={"x": x, "y": y}, headers=headers)
    assert response.status_code == 400, response.text
    assert "Point is outside the map." in response.text
    assert interpreted == []
    assert notices == []
    assert state(ctx) == before
    assert pixels(dm.get(f"{prefix}/fog.png"), "RGBA") == mask
    assert pixels(alice.get(f"/api/c/{cid}/image"), "RGB") == viewer


@pytest.mark.parametrize("x,y", [(0, 0), (100, 100), (399.999, 199.999)])
def test_in_map_reveal_hide_still_change_pixels_and_checkpoint(setup, monkeypatch, x, y):
    ctx, dm, alice, cid, mid, headers = setup
    prefix = f"/api/maps/{mid}"
    response = dm.post(f"{prefix}/reset", headers=headers)
    assert response.status_code == 200, response.text
    notices = []

    async def changed(*args):
        notices.append(args)

    monkeypatch.setattr(api.notify, "map_changed", changed)
    previous = response.json()
    for op, alpha in [("reveal", 255), ("hide", 0)]:
        before_image = pixels(alice.get(f"/api/c/{cid}/image"), "RGB")
        response = dm.post(f"{prefix}/{op}", json={"x": x, "y": y}, headers=headers)
        assert response.status_code == 200, response.text
        current = response.json()
        assert current["op_count"] == previous["op_count"] + 1
        assert current["fog_version"] == previous["fog_version"] + 1
        mask = dm.get(f"{prefix}/fog.png")
        assert mask.status_code == 200
        with Image.open(io.BytesIO(mask.content)) as image:
            assert image.getpixel((100, 100))[3] == alpha
        assert pixels(alice.get(f"/api/c/{cid}/image"), "RGB") != before_image
        with ctx.db.connect() as conn:
            row = conn.execute("SELECT operations FROM map_fog_snapshots WHERE map_id=?", (mid,)).fetchone()
            assert row is not None
            assert len(json.loads(row["operations"])) == current["op_count"]
        previous = current
    assert len(notices) == 2


def test_in_map_wall_click_keeps_nearest_area_snapping(setup):
    ctx, dm, _, _, mid, headers = setup
    prefix = f"/api/maps/{mid}"
    response = dm.post(f"{prefix}/reset", headers=headers)
    assert response.status_code == 200, response.text
    response = dm.post(f"{prefix}/walls", headers=headers,
        files={"file": ("scene.json", json.dumps(two_room_scene()).encode(), "application/json")})
    assert response.status_code == 200, response.text
    with ctx.db.connect() as conn:
        spec, segments, _ = fog_inputs(ctx, conn, mid)
    area = ctx.fog.area_map(spec, segments)
    assert area.labels[int(100 * area.scale), int(199 * area.scale)] == 0
    snapped = ctx.fog.label_at(area, 199, 100)
    assert snapped != 0
    response = dm.post(f"{prefix}/reveal", json={"x": 199, "y": 100}, headers=headers)
    assert response.status_code == 200, response.text
    mask = dm.get(f"{prefix}/fog.png")
    assert mask.status_code == 200
    with Image.open(io.BytesIO(mask.content)) as image:
        for x in (100, 300):
            expected = 255 if ctx.fog.label_at(area, x, 100) == snapped else 0
            assert image.getpixel((int(x * area.scale), int(100 * area.scale)))[3] == expected


def test_bounds_rejection_does_not_replace_auth_or_csrf_checks(setup, env):
    ctx, dm, _, _, mid, headers = setup
    point = {"x": -1, "y": 100}
    path = f"/api/maps/{mid}/reveal"
    before = state(ctx)
    assert dm.post(path, json=point).status_code == 403
    assert TestClient(env[1]).post(path, json=point, headers=headers).status_code == 401
    other = login(env[1], "dm2", "dmpass123")
    assert other.post(path, json=point, headers={"X-CSRF-Token": csrf_of(other)}).status_code == 403
    assert state(ctx) == before
