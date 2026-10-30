"""Injected storage failures must preserve prior files and committed rows."""
import errno
import io
import os
from pathlib import Path
import sqlite3
import stat
from types import SimpleNamespace

from PIL import Image
import pytest

from test_campaign_backup import env
from looking_glass.services import images, campaign_backup


def file_snapshot(root):
    return {path.relative_to(root).as_posix():path.read_bytes()
            for path in root.rglob("*") if path.is_file()}


def database_snapshot(db):
    with db.connect() as conn:
        return tuple(conn.iterdump())


@pytest.mark.parametrize("failure", ["permission", "partial-disk-full"])
def test_map_image_write_failure_preserves_existing_files_and_allows_retry(tmp_path, monkeypatch, failure):
    maps = tmp_path / "maps"
    (maps / "1").mkdir(parents=True)
    buffer = io.BytesIO()
    Image.new("RGB", (20,30), (12,34,56)).save(buffer, "PNG")
    raw = buffer.getvalue()
    (maps / "1/existing.png").write_bytes(raw)
    before = file_snapshot(maps)
    reached = []
    real_open = Path.open
    with monkeypatch.context() as patch:
        if failure == "permission":
            def deny(path, *args, **kwargs):
                if args and args[0] == "xb" and path.parent == maps / "1":
                    reached.append(str(path))
                    raise PermissionError(errno.EACCES, "injected image permission failure")
                return real_open(path, *args, **kwargs)
            patch.setattr(Path, "open", deny)
        else:
            def fail_save(image, destination, format=None, **kwargs):
                reached.append(str(getattr(destination, "name", destination)))
                if hasattr(destination, "write"):
                    destination.write(b"partial-png")
                else:
                    Path(destination).write_bytes(b"partial-png")
                raise OSError(errno.ENOSPC, "injected partial image write")
            patch.setattr(Image.Image, "save", fail_save)
        with pytest.raises(OSError) as caught:
            images.store_map_image(raw, maps, 1)
        assert caught.value.errno == (errno.EACCES if failure == "permission" else errno.ENOSPC)
    assert len(reached) == 1
    assert file_snapshot(maps) == before
    stored = images.store_map_image(raw, maps, 1)
    assert (stored.width, stored.height) == (20,30)
    with Image.open(maps / stored.relative_path) as image:
        assert image.getpixel((1,1)) == (12,34,56)
    assert (maps / "1/existing.png").read_bytes() == raw


def test_image_name_collision_does_not_overwrite_or_delete_existing_file(tmp_path, monkeypatch):
    maps = tmp_path / "maps"
    (maps / "1").mkdir(parents=True)
    original = maps / "1/collision.png"
    original.write_bytes(b"preserve-existing-collision")
    buffer = io.BytesIO()
    Image.new("RGB", (20,30)).save(buffer, "PNG")
    monkeypatch.setattr(images.uuid, "uuid4", lambda:SimpleNamespace(hex="collision"))
    with pytest.raises(FileExistsError):
        images.store_map_image(buffer.getvalue(), maps, 1)
    assert original.read_bytes() == b"preserve-existing-collision"


@pytest.mark.parametrize("stage", ["create-permission", "partial-disk-full", "file-fsync", "directory-fsync"])
def test_failed_recovery_zip_is_removed_and_prior_state_is_preserved(env, tmp_path, monkeypatch, stage):
    db, maps, raw = env
    recovery = tmp_path / "recovery"
    recovery.mkdir()
    (recovery / "retained.zip").write_bytes(b"preserve-existing-backup")
    before_db = database_snapshot(db)
    before_maps = file_snapshot(maps)
    before_recovery = file_snapshot(recovery)
    reached = []
    real_open, real_fsync = Path.open, os.fsync

    class DiskFullFile:
        def __init__(self, stream): self.stream = stream
        def __enter__(self): return self
        def __exit__(self, *args): return self.stream.__exit__(*args)
        def __getattr__(self, name): return getattr(self.stream, name)
        def write(self, data):
            self.stream.write(data[:32])
            reached.append("write")
            raise OSError(errno.ENOSPC, "injected partial recovery write")

    def intercept_open(path, *args, **kwargs):
        target = path.parent == recovery and args and args[0] == "xb"
        if target and stage == "create-permission":
            reached.append("create")
            raise PermissionError(errno.EACCES, "injected recovery permission failure")
        stream = real_open(path, *args, **kwargs)
        return DiskFullFile(stream) if target and stage == "partial-disk-full" else stream

    def intercept_fsync(fd):
        mode = os.fstat(fd).st_mode
        target = (stage == "file-fsync" and stat.S_ISREG(mode)) or (stage == "directory-fsync" and stat.S_ISDIR(mode))
        if target:
            reached.append(stage)
            raise OSError(errno.EIO, "injected recovery durability failure")
        return real_fsync(fd)

    with monkeypatch.context() as patch:
        patch.setattr(Path, "open", intercept_open)
        patch.setattr(campaign_backup.os, "fsync", intercept_fsync)
        with pytest.raises(OSError):
            with db.connect() as conn:
                conn.execute("BEGIN IMMEDIATE")
                campaign_backup.save_recovery(conn, 1, maps, recovery, 10**7)
    assert len(reached) == 1
    assert database_snapshot(db) == before_db
    assert file_snapshot(maps) == before_maps
    assert file_snapshot(recovery) == before_recovery
    with db.connect() as conn:
        conn.execute("BEGIN IMMEDIATE")
        name = campaign_backup.save_recovery(conn, 1, maps, recovery, 10**7)
        assert campaign_backup.inspect_campaign(conn, 1, (recovery / name).read_bytes(), 10**7)["name"] == "Adventure"
        assert conn.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
        assert conn.execute("PRAGMA foreign_key_check").fetchall() == []
    assert (recovery / "retained.zip").read_bytes() == b"preserve-existing-backup"


def test_sqlite_write_contention_preserves_state_then_allows_retry(env):
    db, maps, raw = env
    before = database_snapshot(db)
    before_files = file_snapshot(maps)
    with db.connect() as blocker:
        blocker.execute("BEGIN IMMEDIATE")
        try:
            with pytest.raises(sqlite3.OperationalError, match="locked"):
                with db.connect() as contender:
                    contender.execute("PRAGMA busy_timeout=50")
                    contender.execute("BEGIN IMMEDIATE")
                    contender.execute("UPDATE campaigns SET description='must not commit' WHERE id=1")
        finally:
            blocker.rollback()
    assert database_snapshot(db) == before
    assert file_snapshot(maps) == before_files
    with db.connect() as conn:
        conn.execute("BEGIN IMMEDIATE")
        conn.execute("UPDATE campaigns SET description='after-lock-retry' WHERE id=1")
    with db.connect() as conn:
        assert conn.execute("SELECT description FROM campaigns WHERE id=1").fetchone()[0] == "after-lock-retry"
        assert conn.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
        assert conn.execute("PRAGMA foreign_key_check").fetchall() == []
    assert file_snapshot(maps) == before_files
