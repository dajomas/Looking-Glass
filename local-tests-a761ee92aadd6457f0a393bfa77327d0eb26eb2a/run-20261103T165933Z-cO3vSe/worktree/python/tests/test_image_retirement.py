"""Isolated real-SQLite retirement tests; not application/HTTP execution."""
from contextlib import contextmanager
from pathlib import Path
import sqlite3
import subprocess
import sys
import threading

import pytest
from looking_glass.services import image_retirement as retirement


class SQLiteFixture:
    def __init__(self, path):
        self.path = path

    @contextmanager
    def connect(self):
        conn = sqlite3.connect(self.path)
        try:
            yield conn
            conn.commit()
        except BaseException:
            conn.rollback()
            raise
        finally:
            conn.close()


@pytest.fixture
def store(tmp_path):
    root = tmp_path / 'maps'
    root.mkdir()
    db = SQLiteFixture(tmp_path / 'test.db')
    with db.connect() as conn:
        conn.executescript('CREATE TABLE maps(id INTEGER PRIMARY KEY,image_file TEXT); '
                           'CREATE TABLE double_reveal_maps(map_id INTEGER,image_file TEXT);')
    return db, root


def queue(db, *paths):
    with db.connect() as conn:
        conn.execute('BEGIN IMMEDIATE')
        retirement.retire_paths(conn, paths)


def pending(db):
    with db.connect() as conn:
        return {r[0] for r in conn.execute('SELECT image_file FROM image_retirements')}


def test_no_queue_does_not_scan(store):
    db, root = store
    (root / 'untracked.png').write_bytes(b'keep')
    assert retirement.collect(db, root) == dict(removed=0, missing=0, referenced=0, blocked=0)
    assert (root / 'untracked.png').read_bytes() == b'keep'


def test_capture_deduplicate_and_rollback(store):
    db, _ = store
    with db.connect() as conn:
        conn.execute("INSERT INTO maps VALUES(1,'original.png')")
        conn.execute("INSERT INTO double_reveal_maps VALUES(1,'alternate.png')")
    with pytest.raises(ValueError):
        with db.connect() as conn:
            conn.execute('BEGIN IMMEDIATE')
            retirement.retire_maps(conn, [1, 1])
            conn.execute('DELETE FROM maps')
            raise ValueError('rollback')
    with db.connect() as conn:
        assert conn.execute('SELECT COUNT(*) FROM maps').fetchone()[0] == 1
        assert conn.execute("SELECT 1 FROM sqlite_master WHERE name='image_retirements'").fetchone() is None
        conn.execute('BEGIN IMMEDIATE')
        retirement.retire_maps(conn, [1, 1])
    assert pending(db) == {'original.png', 'alternate.png'}
    with db.connect() as conn:
        with pytest.raises(RuntimeError, match='transaction'):
            retirement.retire_paths(conn, ['outside.png'])


def test_references_in_both_tables_and_idempotence(store):
    db, root = store
    for name in ['original.png', 'alternate.png', 'old.png', 'control.png']:
        (root / name).write_bytes(name.encode())
    with db.connect() as conn:
        conn.execute("INSERT INTO maps VALUES(1,'original.png')")
        conn.execute("INSERT INTO double_reveal_maps VALUES(1,'alternate.png')")
    queue(db, 'original.png', 'alternate.png', 'old.png', 'missing.png')
    assert retirement.collect(db, root) == dict(removed=1, missing=1, referenced=2, blocked=0)
    assert pending(db) == {'original.png', 'alternate.png'}
    assert (root / 'original.png').read_bytes() == b'original.png'
    assert (root / 'alternate.png').read_bytes() == b'alternate.png'
    assert (root / 'control.png').read_bytes() == b'control.png'
    with db.connect() as conn:
        conn.execute('DELETE FROM maps')
        conn.execute('DELETE FROM double_reveal_maps')
    assert retirement.collect(db, root)['removed'] == 2
    assert not pending(db)
    assert retirement.collect(db, root)['removed'] == 0


@pytest.mark.parametrize('unsafe', ['../outside.png', '/outside.png', 'a/../outside.png',
                                   './outside.png', 'a//b.png', 'a\\b.png', '.image-retirement.lock'])
def test_unsafe_paths(store, unsafe):
    db, root = store
    outside = root.parent / 'outside.png'
    outside.write_bytes(b'outside')
    queue(db, unsafe)
    assert retirement.collect(db, root)['blocked'] == 1
    assert pending(db) == {unsafe}
    assert outside.read_bytes() == b'outside'


def test_symlink_and_unlink_failure_retry(store, monkeypatch):
    db, root = store
    outside = root.parent / 'outside.png'
    outside.write_bytes(b'outside')
    (root / 'link.png').symlink_to(outside)
    target = root / 'old.png'
    target.write_bytes(b'old')
    queue(db, 'link.png', 'old.png')
    original = Path.unlink
    def fail(path, *args, **kwargs):
        if path == target:
            raise PermissionError('injected unlink failure')
        return original(path, *args, **kwargs)
    with monkeypatch.context() as patch:
        patch.setattr(Path, 'unlink', fail)
        assert retirement.collect(db, root)['blocked'] == 2
    assert pending(db) == {'link.png', 'old.png'}
    assert outside.read_bytes() == b'outside' and target.read_bytes() == b'old'
    assert retirement.collect(db, root)['removed'] == 1
    assert pending(db) == {'link.png'}


def test_selected_and_open_reader(store):
    db, root = store
    path = root / 'old.png'
    path.write_bytes(b'selected bytes')
    queue(db, 'old.png')
    selected, resume = threading.Event(), threading.Event()
    result, errors = [], []
    def reader():
        try:
            with retirement.storage_use(root):
                selected.set()
                assert resume.wait(10)
                with path.open('rb') as stream:
                    result.append(stream.read())
                    with pytest.raises(RuntimeError, match='busy'):
                        retirement.collect(db, root)
        except BaseException as exc:
            errors.append(exc)
    thread = threading.Thread(target=reader, daemon=True)
    thread.start()
    try:
        assert selected.wait(10)
        with pytest.raises(RuntimeError, match='busy'):
            retirement.collect(db, root)
        assert path.read_bytes() == b'selected bytes'
    finally:
        resume.set()
        thread.join(10)
    assert not thread.is_alive() and not errors
    assert result == [b'selected bytes']
    assert retirement.collect(db, root)['removed'] == 1


def test_cross_process_lock_and_exception_release(store, tmp_path):
    db, root = store
    ready = tmp_path / 'ready'
    program = ('import pathlib,sys,time; '
               'from looking_glass.services.image_retirement import storage_use; '
               '\nwith storage_use(sys.argv[1]):\n '
               'pathlib.Path(sys.argv[2]).write_text("ready"); time.sleep(60)\n')
    child = subprocess.Popen([sys.executable, '-c', program, str(root), str(ready)],
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    import time
    diagnostics = ('', '')
    try:
        deadline = time.monotonic() + 10
        while not ready.exists() and child.poll() is None and time.monotonic() < deadline:
            time.sleep(0.01)
        acquired = ready.exists()
        if acquired:
            with pytest.raises(RuntimeError, match='busy'):
                retirement.collect(db, root)
    finally:
        if child.poll() is None:
            child.terminate()
        try:
            diagnostics = child.communicate(timeout=5)
        except subprocess.TimeoutExpired:
            child.kill()
            diagnostics = child.communicate(timeout=5)
        assert child.poll() is not None, diagnostics
    assert acquired, ('child did not acquire lock before deadline', diagnostics)
    with pytest.raises(ValueError):
        with retirement.storage_use(root, exclusive=True):
            with pytest.raises(RuntimeError, match='busy'):
                with retirement.storage_use(root):
                    pytest.fail('reader entered collector lock')
            raise ValueError('release')
    assert retirement.collect(db, root)['removed'] == 0


def test_collection_commit_failure_retry(store):
    db, root = store
    (root / 'old.png').write_bytes(b'old')
    queue(db, 'old.png')
    class FailingCommit:
        @contextmanager
        def connect(self):
            conn = sqlite3.connect(db.path)
            try:
                yield conn
                raise sqlite3.OperationalError('injected collector commit')
            finally:
                conn.rollback()
                conn.close()
    with pytest.raises(sqlite3.OperationalError, match='collector commit'):
        retirement.collect(FailingCommit(), root)
    assert not (root / 'old.png').exists() and pending(db) == {'old.png'}
    assert retirement.collect(db, root)['missing'] == 1
    assert not pending(db)
