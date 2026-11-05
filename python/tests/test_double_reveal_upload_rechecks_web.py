"""Bug 29 post-staging rechecks, rollback and cancellation contracts."""
import asyncio
import threading
from types import SimpleNamespace

import pytest
pytest.importorskip("fastapi")
from test_web import env
from test_map_transitions_web import prepare
from test_double_reveal_web import upload
from test_double_reveal_upload_lock_web import _files
from looking_glass.services import images
from looking_glass.web.admin import double_reveal as routes


@pytest.mark.parametrize("change,expected", [
    ("UPDATE maps SET fog_version=fog_version+1 WHERE id=?", 400),
    ("UPDATE maps SET width=width+1 WHERE id=?", 400),
    ("UPDATE maps SET cache_token='different-incarnation' WHERE id=?", 400),
    ("UPDATE campaigns SET owner_id=(SELECT id FROM users WHERE username='dm2') WHERE id=(SELECT campaign_id FROM maps WHERE id=?)", 403),
    ("DELETE FROM maps WHERE id=?", 404),
    ("UPDATE double_reveal_maps SET revision=revision+1 WHERE map_id=?", 400),
])
def test_processing_rechecks_current_state(env, monkeypatch, change, expected):
    ctx, admin, viewer, dm, h, cid, mids = prepare(env)
    mid = mids[0]
    base = f"/api/maps/{mid}/double-reveal"
    assert upload(dm, base, h).status_code == 200
    before = _files(ctx.settings.maps_dir)
    real = images.store_map_image
    notifications = []

    def store(*args, **kwargs):
        result = real(*args, **kwargs)
        with ctx.db.connect() as conn:
            conn.execute("PRAGMA busy_timeout=200")
            conn.execute("BEGIN IMMEDIATE")
            conn.execute(change, (mid,))
        return result

    async def notify(*args):
        notifications.append(args)

    monkeypatch.setattr(images, "store_map_image", store)
    monkeypatch.setattr(routes.notify, "map_changed", notify)
    response = upload(dm, base, h)
    assert response.status_code == expected, response.text
    assert _files(ctx.settings.maps_dir) == before
    assert notifications == []


def test_snapshot_failure_rolls_back_and_cleans_staged_file(env, monkeypatch):
    ctx, admin, viewer, dm, h, cid, mids = prepare(env)
    mid = mids[0]
    base = f"/api/maps/{mid}/double-reveal"
    assert upload(dm, base, h).status_code == 200
    before = _files(ctx.settings.maps_dir)
    original_store, original_snapshot = images.store_map_image, routes.snapshot
    processing = []

    def store(*args, **kwargs):
        result = original_store(*args, **kwargs)
        processing.append(True)
        return result

    def snapshot(*args, **kwargs):
        if processing:
            raise RuntimeError("injected snapshot failure")
        return original_snapshot(*args, **kwargs)

    monkeypatch.setattr(images, "store_map_image", store)
    monkeypatch.setattr(routes, "snapshot", snapshot)
    with pytest.raises(RuntimeError, match="injected snapshot failure"):
        upload(dm, base, h)
    assert _files(ctx.settings.maps_dir) == before
    with ctx.db.connect() as conn:
        assert conn.execute("SELECT revision FROM double_reveal_maps WHERE map_id=?", (mid,)).fetchone()[0] == 1


def test_notification_failure_does_not_delete_committed_image(env, monkeypatch):
    ctx, admin, viewer, dm, h, cid, mids = prepare(env)
    mid = mids[0]
    base = f"/api/maps/{mid}/double-reveal"

    async def notify(*args):
        raise RuntimeError("injected notification failure")

    monkeypatch.setattr(routes.notify, "map_changed", notify)
    with pytest.raises(RuntimeError, match="injected notification failure"):
        upload(dm, base, h)
    with ctx.db.connect() as conn:
        row = conn.execute("SELECT image_file,revision FROM double_reveal_maps WHERE map_id=?", (mid,)).fetchone()
    assert row["revision"] == 1
    assert (ctx.settings.maps_dir / row["image_file"]).is_file()


def test_cancelled_stage_cleans_late_worker_result(tmp_path, monkeypatch):
    entered, release, removed = threading.Event(), threading.Event(), threading.Event()
    ctx = SimpleNamespace(settings=SimpleNamespace(maps_dir=tmp_path))

    def store(raw, maps_dir, campaign_id):
        entered.set()
        if not release.wait(5):
            raise RuntimeError("worker release timeout")
        (maps_dir / "staged.png").write_bytes(raw)
        return images.StoredImage("staged.png", 4, 2)

    original_delete = images.delete_map_image

    def delete(maps_dir, path):
        original_delete(maps_dir, path)
        removed.set()

    monkeypatch.setattr(images, "store_map_image", store)
    monkeypatch.setattr(images, "delete_map_image", delete)

    async def run():
        task = asyncio.create_task(routes._stage_image(ctx, b"image", 1))
        try:
            assert await asyncio.to_thread(entered.wait, 5)
            task.cancel()
            with pytest.raises(asyncio.CancelledError):
                await task
        finally:
            release.set()
        assert await asyncio.to_thread(removed.wait, 5)
        assert not (tmp_path / "staged.png").exists()

    asyncio.run(run())
