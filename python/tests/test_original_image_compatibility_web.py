"""Bug 13: original replacements must preserve alternate-artwork compatibility.

Run with installed application dependencies:
PYTHONPATH=python python -m pytest -q python/tests/test_original_image_compatibility_web.py
"""
import io
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest
from PIL import Image

from conftest import png_bytes
from test_web import env, login, csrf_of
from test_image_database_failures import image_case, files, row_snapshot, viewer_output, GREEN
from looking_glass.services import images
from looking_glass.web.admin import campaigns


def stamp(state):
    return {key: state[key] for key in
            ("cache_token", "walls_version", "fog_version", "image_revision")}


def alternate(case):
    base = f"/api/maps/{case.mid}/double-reveal"
    state = case.dm.get(base)
    assert state.status_code == 200, state.text
    result = case.dm.post(base + "/image", data=stamp(state.json()),
        files={"file": ("alternate.png", png_bytes(400, 200, (10, 200, 10)), "image/png")},
        headers={"X-CSRF-Token": case.csrf})
    assert result.status_code == 200, result.text
    return base


def configure(case, base):
    headers = {"X-CSRF-Token": case.csrf}
    selected = case.dm.get(base + "/room?x=100&y=100")
    assert selected.status_code == 200, selected.text
    result = case.dm.post(base + "/room", headers=headers,
        json=stamp(selected.json()) | dict(x=100, y=100, revision=0, enabled=True))
    assert result.status_code == 200, result.text
    state = result.json()
    room = state["rooms"][0]
    result = case.dm.post(base + "/appearance", headers=headers,
        json=stamp(state) | dict(area_key=room["area_key"], revision=room["revision"], true_active=True))
    assert result.status_code == 200, result.text
    # Valid saved custom notes, independent of the imported-note library.
    with case.ctx.db.connect() as conn:
        conn.execute("INSERT INTO room_notes(map_id,area_key,x,y,name,markdown) VALUES(?,?,?,?,?,?)",
            (case.mid, room["area_key"], 100, 100, "Custom name", "Exact **custom** notes\n"))


def replace(case, width=400, height=200, client=None, csrf=None):
    return (client or case.dm).post(f"/maps/{case.mid}/image",
        data={"csrf_token": case.csrf if csrf is None else csrf},
        files={"image": ("replacement.png", png_bytes(width, height, GREEN), "image/png")},
        follow_redirects=False)


def snapshot(case):
    output = viewer_output(case)
    return row_snapshot(case.ctx), files(case.ctx.settings.maps_dir), output


def map_row(case):
    with case.ctx.db.connect() as conn:
        return dict(conn.execute("SELECT * FROM maps WHERE id=?", (case.mid,)).fetchone())


@pytest.mark.parametrize("width,height", [(500, 200), (400, 250), (500, 250)])
@pytest.mark.parametrize("configured", [False, True])
def test_dimension_change_with_alternate_is_lossless_rejection(image_case, monkeypatch, width, height, configured):
    case = image_case
    base = alternate(case)
    if configured:
        configure(case, base)
    before = snapshot(case)
    publish = AsyncMock(wraps=case.ctx.hub.publish)
    invalidate = Mock(wraps=case.ctx.fog.invalidate)
    monkeypatch.setattr(case.ctx.hub, "publish", publish)
    monkeypatch.setattr(case.ctx.fog, "invalidate", invalidate)
    result = replace(case, width, height)
    assert result.status_code == 400, result.text
    assert "400" in result.text and "200" in result.text and "alternate artwork" in result.text
    publish.assert_not_awaited()
    invalidate.assert_not_called()
    assert snapshot(case) == before
    with case.ctx.db.connect() as conn:
        assert conn.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
        assert conn.execute("PRAGMA foreign_key_check").fetchall() == []
    # A failed attempt must not poison the subsequent supported operation.
    result = replace(case)
    assert result.status_code == 303 and "ok=" in result.headers["location"], result.text
    publish.assert_awaited_once()


def test_same_size_preserves_configuration_history_notes_and_alternate(image_case):
    case = image_case
    base = alternate(case)
    configure(case, base)
    before = map_row(case)
    before_files = files(case.ctx.settings.maps_dir)
    tables = ("double_reveal_maps", "double_reveal_rooms", "double_reveal_history", "room_notes", "room_note_archives", "fog_ops")
    def rows():
        with case.ctx.db.connect() as conn:
            return {table: [tuple(row) for row in conn.execute(f"SELECT * FROM {table} ORDER BY rowid")]
                    for table in tables}
    before_rows = rows()
    result = replace(case)
    assert result.status_code == 303 and "ok=" in result.headers["location"], result.text
    after = map_row(case)
    assert (after["width"], after["height"]) == (400, 200)
    assert after["walls_version"] == before["walls_version"] + 1
    assert after["fog_version"] == before["fog_version"] + 1
    assert rows() == before_rows
    after_files = files(case.ctx.settings.maps_dir)
    kept = set(before_files) - {before["image_file"]}
    assert set(after_files) == kept | {after["image_file"]}
    assert all(after_files[path] == before_files[path] for path in kept)
    with Image.open(io.BytesIO(after_files[after["image_file"]])) as image:
        assert image.size == (400, 200) and image.convert("RGB").getpixel((100, 100)) == GREEN
    state = case.dm.get(base).json()
    assert state["rooms"][0]["valid_geometry"] and state["rooms"][0]["true_active"] == 1
    assert viewer_output(case)[2] == ((10, 200, 10), (0, 0, 0))


def test_dimension_change_without_alternate_remains_supported(image_case):
    case = image_case
    before = map_row(case)
    result = replace(case, 500, 250)
    assert result.status_code == 303 and "ok=" in result.headers["location"], result.text
    after = map_row(case)
    assert (after["width"], after["height"]) == (500, 250)
    assert after["image_file"] != before["image_file"]
    assert not (case.ctx.settings.maps_dir / before["image_file"]).exists()
    with Image.open(case.ctx.settings.maps_dir / after["image_file"]) as image:
        assert image.size == (500, 250)


def test_alternate_committed_during_storage_is_rechecked_under_write_lock(image_case, monkeypatch):
    case = image_case
    real_store = images.store_map_image
    real_access = campaigns.map_for_manage
    observed = SimpleNamespace(accesses=0, stored=None, before=None)

    def store(*args, **kwargs):
        observed.stored = real_store(*args, **kwargs)
        alt = real_store(png_bytes(400, 200, (10, 200, 10)), case.ctx.settings.maps_dir, case.cid)
        with case.ctx.db.connect() as conn:
            conn.execute("INSERT INTO double_reveal_maps(map_id,image_file) VALUES(?,?)",
                         (case.mid, alt.relative_path))
        observed.before = row_snapshot(case.ctx)
        observed.files = files(case.ctx.settings.maps_dir)
        del observed.files[observed.stored.relative_path]
        return observed.stored

    def access(conn, *args, **kwargs):
        observed.accesses += 1
        if observed.accesses == 2:
            assert conn.in_transaction, "Recheck must be inside the replacement write transaction"
        return real_access(conn, *args, **kwargs)

    monkeypatch.setattr(images, "store_map_image", store)
    monkeypatch.setattr(campaigns, "map_for_manage", access)
    publish = AsyncMock(wraps=case.ctx.hub.publish)
    monkeypatch.setattr(case.ctx.hub, "publish", publish)
    result = replace(case, 500, 200)
    assert result.status_code == 400, result.text
    assert observed.accesses == 2
    assert row_snapshot(case.ctx) == observed.before
    assert files(case.ctx.settings.maps_dir) == observed.files
    publish.assert_not_awaited()


@pytest.mark.parametrize("actor", ["missing-csrf", "wrong-owner"])
def test_replacement_authorization_precedes_image_storage(image_case, monkeypatch, actor):
    case = image_case
    alternate(case)
    stranger = None
    if actor == "wrong-owner":
        stranger = login(case.dm.app, "dm2", "dmpass123")
    try:
        token = csrf_of(stranger) if stranger else ""
        before = snapshot(case)
        store = Mock(side_effect=AssertionError("Unauthorized request reached image storage"))
        monkeypatch.setattr(images, "store_map_image", store)
        result = replace(case, 500, 250, client=stranger, csrf=token)
        assert result.status_code == 403, result.text
        store.assert_not_called()
        assert snapshot(case) == before
    finally:
        if stranger:
            stranger.close()
