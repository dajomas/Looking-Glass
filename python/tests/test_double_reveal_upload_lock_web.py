"""Bug 29 regression contracts for alternate-image upload write locks."""
import sqlite3
import pytest
pytest.importorskip("fastapi")
from test_web import env
from test_map_transitions_web import prepare
from test_double_reveal_web import upload
from looking_glass.services import images


def _files(root):
    return sorted(str(p.relative_to(root)) for p in root.rglob("*") if p.is_file())


def _can_write(path, map_id=None):
    """Probe a real independent writer, optionally changing the upload stamp."""
    conn = sqlite3.connect(path, timeout=0.2, isolation_level=None)
    try:
        conn.execute("PRAGMA busy_timeout=200")
        conn.execute("BEGIN IMMEDIATE")
        if map_id is not None:
            conn.execute("UPDATE maps SET fog_version=fog_version+1 WHERE id=?", (map_id,))
        conn.execute("COMMIT")
        return True
    except sqlite3.OperationalError as exc:
        if exc.sqlite_errorcode not in (sqlite3.SQLITE_BUSY, sqlite3.SQLITE_LOCKED):
            raise
        return False
    finally:
        conn.close()


def _spy(monkeypatch, ctx, map_id=None):
    seen = []
    real = images.store_map_image

    def wrapped(*args, **kwargs):
        seen.append(_can_write(ctx.db.path, map_id))
        return real(*args, **kwargs)

    monkeypatch.setattr(images, "store_map_image", wrapped)
    return seen


def test_upload_does_not_hold_write_lock_while_storing(env, monkeypatch):
    ctx, admin, viewer, dm, h, cid, mids = prepare(env)
    base = f"/api/maps/{mids[0]}/double-reveal"
    seen = _spy(monkeypatch, ctx)
    response = upload(dm, base, h)
    assert response.status_code == 200, response.text
    assert seen == [True], "store_map_image ran while the upload held the SQLite write lock"
    assert dm.get(base).json()["image_revision"] == 1


def test_change_during_processing_is_rejected_without_orphan(env, monkeypatch):
    ctx, admin, viewer, dm, h, cid, mids = prepare(env)
    base = f"/api/maps/{mids[0]}/double-reveal"
    before = _files(ctx.settings.maps_dir)
    seen = _spy(monkeypatch, ctx, mids[0])
    response = upload(dm, base, h)
    assert seen == [True], "a competing write could not proceed during image processing"
    assert response.status_code == 400, response.text
    assert _files(ctx.settings.maps_dir) == before
    assert dm.get(base).json()["image_revision"] == 0


def test_wrong_dimensions_leave_no_orphan(env):
    ctx, admin, viewer, dm, h, cid, mids = prepare(env)
    base = f"/api/maps/{mids[0]}/double-reveal"
    before = _files(ctx.settings.maps_dir)
    assert upload(dm, base, h, 10, 10).status_code == 400
    assert _files(ctx.settings.maps_dir) == before
    assert dm.get(base).json()["image_revision"] == 0


def test_replacement_upload_retains_prior_alternate_file(env):
    ctx, admin, viewer, dm, h, cid, mids = prepare(env)
    base = f"/api/maps/{mids[0]}/double-reveal"
    assert upload(dm, base, h).status_code == 200
    with ctx.db.connect() as conn:
        first = conn.execute("SELECT image_file FROM double_reveal_maps WHERE map_id=?", (mids[0],)).fetchone()[0]
    assert upload(dm, base, h).status_code == 200
    with ctx.db.connect() as conn:
        second = conn.execute("SELECT image_file FROM double_reveal_maps WHERE map_id=?", (mids[0],)).fetchone()[0]
    assert first != second and dm.get(base).json()["image_revision"] == 2
    assert (ctx.settings.maps_dir / first).is_file(), "superseded alternate must stay until offline collection"
