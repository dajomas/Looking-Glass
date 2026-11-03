"""Transactional retirement bookkeeping; explicit offline collection only.

The normal CLI must hold storage_use for its complete serving lifetime.
Until CLI integration is delivered, stop ALL readers before maintenance.
"""
import argparse
from contextlib import contextmanager
import logging
from pathlib import Path, PurePosixPath
import sqlite3

log = logging.getLogger(__name__)


@contextmanager
def storage_use(maps_dir, *, exclusive=False):
    """Local-filesystem advisory lock. Never remove its stable lock inode."""
    try:
        import fcntl
    except ImportError:
        if exclusive:
            raise RuntimeError("Offline collection requires POSIX flock support")
        yield
        return
    root = Path(maps_dir).resolve()
    root.mkdir(parents=True, exist_ok=True)
    with (root / ".image-retirement.lock").open("a+b") as stream:
        try:
            fcntl.flock(stream, (fcntl.LOCK_EX if exclusive else fcntl.LOCK_SH) | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise RuntimeError("Image storage is busy; stop all readers before collection") from exc
        try:
            yield
        finally:
            fcntl.flock(stream, fcntl.LOCK_UN)


def retire_paths(conn, paths):
    """Caller owns the write transaction; never commit or unlink here."""
    if not conn.in_transaction:
        raise RuntimeError("Retirement requires the caller's write transaction")
    conn.execute("CREATE TABLE IF NOT EXISTS image_retirements (image_file TEXT PRIMARY KEY NOT NULL)")
    conn.executemany("INSERT OR IGNORE INTO image_retirements(image_file) VALUES(?)",
                     ((path,) for path in set(paths)))


def retire_maps(conn, map_ids):
    paths = []
    for mid in map_ids:
        paths.extend(row[0] for row in conn.execute(
            "SELECT image_file FROM maps WHERE id=? UNION SELECT image_file FROM double_reveal_maps WHERE map_id=?",
            (mid, mid)))
    retire_paths(conn, paths)


def _contained_file(root, relative):
    if not isinstance(relative, str) or not relative or "\\" in relative or "\x00" in relative:
        raise ValueError("Invalid retirement path")
    if relative == ".image-retirement.lock":
        raise ValueError("The storage lock is not artwork")
    parts = relative.split("/")
    if PurePosixPath(relative).is_absolute() or any(p in ("", ".", "..") for p in parts):
        raise ValueError("Invalid retirement path")
    path = root
    for part in parts:
        path = path / part
        if path.is_symlink():
            raise ValueError("Symlink retirement paths are not supported")
    if root not in path.resolve().parents:
        raise ValueError("Retirement path escapes image storage")
    return path


def collect(db, maps_dir):
    """Registered paths only; stop all uncoordinated readers before calling.

    Hold the SQLite writer lock across reference checks, unlink and queue removal.
    Missing files make retry safe after unlink followed by transaction failure.
    """
    counts = dict(removed=0, missing=0, referenced=0, blocked=0)
    with storage_use(maps_dir, exclusive=True):
        root = Path(maps_dir).resolve()
        with db.connect() as conn:
            conn.execute("BEGIN IMMEDIATE")
            if conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='image_retirements'").fetchone() is None:
                return counts
            rows = conn.execute("SELECT image_file FROM image_retirements ORDER BY image_file").fetchall()
            for (relative,) in rows:
                if conn.execute("SELECT 1 FROM maps WHERE image_file=? UNION ALL SELECT 1 FROM double_reveal_maps WHERE image_file=? LIMIT 1",
                                (relative, relative)).fetchone():
                    counts['referenced'] += 1
                    continue
                try:
                    path = _contained_file(root, relative)
                    try:
                        path.unlink()
                    except FileNotFoundError:
                        counts['missing'] += 1
                    else:
                        counts['removed'] += 1
                except (OSError, ValueError):
                    counts['blocked'] += 1
                    log.warning("Retaining blocked retirement candidate %r", relative, exc_info=True)
                    continue
                conn.execute("DELETE FROM image_retirements WHERE image_file=?", (relative,))
    return counts


def main(argv=None):
    parser = argparse.ArgumentParser(description="Collect registered artwork; stop ALL readers first")
    parser.add_argument('-c', '--config')
    parser.add_argument('--confirm-stopped', action='store_true', required=True)
    args = parser.parse_args(argv)
    from ..config import load_settings
    from ..db import Database
    settings = load_settings(args.config)
    if not settings.database_path.is_file():
        parser.error("Configured database does not exist; refusing to create one")
    try:
        result = collect(Database(settings.database_path), settings.maps_dir)
    except (RuntimeError, OSError, sqlite3.DatabaseError) as exc:
        parser.exit(1, f"Collection refused or failed: {exc}\n")
    print(" ".join(f"{key}={value}" for key, value in result.items()))
    return 1 if result['blocked'] else 0


if __name__ == '__main__':
    raise SystemExit(main())
