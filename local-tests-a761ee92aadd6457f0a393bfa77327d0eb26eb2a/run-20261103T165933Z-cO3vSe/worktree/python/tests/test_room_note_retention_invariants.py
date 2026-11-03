"""Schema-17 upgrade and archive/detach atomicity with real SQLite.

Synthetic label maps isolate retention semantics; HTTP/real geometry, browser
and portability acceptance remain in their existing suites.
"""
import sqlite3
from types import SimpleNamespace

import numpy as np
import pytest

from looking_glass import db as storage
from looking_glass.services import room_notes
from looking_glass.services.room_note_import import list_entries


TEXT = '  # Custom\r\n\n**Gold** and café 🐉\n<script>secret()</script>\n'
TABLES = ('campaigns', 'maps', 'room_notes', 'imported_room_notes',
          'fog_ops', 'map_fog_snapshots')


def area(rows):
    labels = np.array(rows, dtype=np.int32)
    return SimpleNamespace(labels=labels, shape=labels.shape, scale=1.0, region_signatures={})


def old_area():
    return area([[1, 1, 0, 2, 2]] * 3)


def snapshot(conn):
    return {table: [dict(r) for r in conn.execute(f'SELECT * FROM {table} ORDER BY rowid')]
            for table in TABLES}


def dump(conn):
    return tuple(conn.iterdump())


def generations(conn):
    return [r[0] for r in conn.execute('SELECT room_notes_version FROM maps ORDER BY id')]


@pytest.fixture
def schema17(tmp_path, monkeypatch):
    database = storage.Database(tmp_path / 'retention.db')
    with monkeypatch.context() as patch:
        patch.setattr(storage, 'MIGRATIONS', storage.MIGRATIONS[:17])
        assert database.migrate() == 17
    with database.connect() as conn:
        conn.execute("INSERT INTO campaigns(id,name) VALUES(1,'Legacy campaign')")
        for mid in (1, 2):
            conn.execute("INSERT INTO maps(id,campaign_id,name,image_file,width,height,walls_version,fog_version) VALUES(?,1,?,'unused.png',5,3,7,11)", (mid, f'Map {mid}'))
            for label, x, name in ((1, 0, 'Crypt'), (2, 3, 'Hall')):
                key = room_notes.area_key(old_area(), label, 5, 3)
                conn.execute('INSERT INTO room_notes(map_id,area_key,x,y,name,markdown,revision) VALUES(?,?,?,0,?,?,9)', (mid, key, x, name, TEXT))
                conn.execute('INSERT INTO imported_room_notes(map_id,name,markdown,digest) VALUES(?,?,?,?)', (mid, name, 'Original library text', name))
        conn.execute('UPDATE campaigns SET active_map_id=1 WHERE id=1')
        conn.execute("INSERT INTO fog_ops(map_id,op,x,y) VALUES(1,'reveal',0,0)")
        conn.execute("INSERT INTO map_fog_snapshots(map_id,operations,updated_at) VALUES(1,'[]','legacy snapshot')")
    return database


@pytest.fixture
def current(schema17):
    assert schema17.migrate() == len(storage.MIGRATIONS)
    return schema17


def test_upgrade_preserves_every_existing_column_and_is_idempotent(schema17):
    with schema17.connect() as conn:
        before = snapshot(conn)
    assert schema17.migrate() == len(storage.MIGRATIONS)
    with schema17.connect() as conn:
        after = snapshot(conn)
        assert generations(conn) == [0, 0]
        for row in after['maps']:
            row.pop('room_notes_version')
        assert after == before
        assert conn.execute('SELECT COUNT(*) FROM room_note_archives').fetchone()[0] == 0
        assert conn.execute('PRAGMA foreign_key_check').fetchall() == []
        first = dump(conn)
    assert schema17.migrate() == len(storage.MIGRATIONS)
    with schema17.connect() as conn:
        assert dump(conn) == first


def test_failed_version18_record_rolls_back_schema_and_data_then_retries(schema17):
    with schema17.connect() as conn:
        conn.executescript("CREATE TRIGGER reject_18 BEFORE INSERT ON schema_version WHEN NEW.version=18 BEGIN SELECT RAISE(ABORT,'injected migration18 failure'); END;")
        before = dump(conn)
    with pytest.raises(sqlite3.IntegrityError, match='injected migration18 failure'):
        schema17.migrate()
    with schema17.connect() as conn:
        assert dump(conn) == before
        assert conn.execute('SELECT MAX(version) FROM schema_version').fetchone()[0] == 17
        assert 'room_notes_version' not in [r['name'] for r in conn.execute('PRAGMA table_info(maps)')]
        assert conn.execute("SELECT 1 FROM sqlite_master WHERE name='room_note_archives'").fetchone() is None
        conn.execute('DROP TRIGGER reject_18')
    assert schema17.migrate() == len(storage.MIGRATIONS)
    with schema17.connect() as conn:
        assert conn.execute('SELECT COUNT(*) FROM room_notes').fetchone()[0] == 4
        assert generations(conn) == [0, 0]
        assert conn.execute('PRAGMA foreign_key_check').fetchall() == []


@pytest.mark.parametrize('rollback', [False, True])
def test_generation_insert_update_move_delete_and_rollback(current, rollback):
    key = room_notes.area_key(old_area(), 1, 5, 3)
    with current.connect() as conn:
        conn.execute('BEGIN IMMEDIATE')
        before = dump(conn)
        protected = snapshot(conn)
        conn.execute("UPDATE room_notes SET markdown='Edited' WHERE map_id=1 AND area_key=?", (key,))
        assert generations(conn) == [1, 0]
        conn.execute("UPDATE room_notes SET map_id=2,area_key='moved' WHERE map_id=1 AND area_key=?", (key,))
        assert generations(conn) == [2, 1]
        conn.execute("DELETE FROM room_notes WHERE map_id=2 AND area_key='moved'")
        assert generations(conn) == [2, 2]
        conn.execute("INSERT INTO room_notes(map_id,area_key,x,y,name,markdown) VALUES(1,'new',0,0,'New','Saved')")
        assert generations(conn) == [3, 2]
        after = snapshot(conn)
        for table in ('campaigns', 'fog_ops', 'map_fog_snapshots', 'imported_room_notes'):
            assert after[table] == protected[table]
        for row in after['maps']:
            row['room_notes_version'] = 0
        assert after['maps'] == protected['maps']
        assert conn.execute('SELECT COUNT(*) FROM room_note_archives').fetchone()[0] == 0
        if rollback:
            conn.rollback()
            assert dump(conn) == before
    with current.connect() as conn:
        assert generations(conn) == ([0, 0] if rollback else [3, 2])
        assert conn.execute('PRAGMA foreign_key_check').fetchall() == []


@pytest.mark.parametrize('change', ['split', 'merge', 'wall_anchor', 'alignment', 'outside'])
def test_detachment_preserves_exact_content_provenance_and_other_map(current, change):
    variants = {
        'split': [[1, 1, 0, 2, 2], [0, 0, 0, 2, 2], [3, 3, 0, 2, 2]],
        'merge': [[1, 1, 0, 2, 2], [1, 1, 1, 2, 2], [1, 1, 0, 2, 2]],
        'wall_anchor': [[0, 1, 0, 2, 2], [1, 1, 0, 2, 2], [1, 1, 0, 2, 2]],
        'alignment': [[0, 1, 1, 2, 2]] * 3,
        'outside': [[1, 1, 0, 2, 2]] * 3,
    }
    with current.connect() as conn:
        conn.execute('BEGIN IMMEDIATE')
        if change == 'outside':
            conn.execute("UPDATE room_notes SET x=50 WHERE map_id=1 AND name='Crypt'")
        before = snapshot(conn)
        source = next(r for r in before['room_notes'] if r['map_id'] == 1 and r['name'] == 'Crypt')
        owner = before['maps'][0]
        assert room_notes.remove_stale(conn, 1, area(variants[change]), 5, 3) == 1
        archive = dict(conn.execute('SELECT * FROM room_note_archives').fetchone())
        for field in ('map_id', 'area_key', 'x', 'y', 'name', 'markdown'):
            assert archive[field] == source[field]
        assert archive['source_revision'] == source['revision']
        assert archive['source_map_id'] == owner['id']
        assert archive['source_campaign_id'] == owner['campaign_id']
        assert archive['source_map_name'] == owner['name']
        assert archive['source_campaign_name'] == 'Legacy campaign'
        assert archive['source_map_token'] == owner['cache_token']
        assert (archive['source_width'], archive['source_height'], archive['observed_walls_version']) == (5, 3, 7)
        assert archive['reason'] == 'geometry_changed' and archive['origin_uuid'] and archive['archived_at']
        expected = [r for r in before['room_notes'] if r != source]
        assert snapshot(conn)['room_notes'] == expected
        assert not next(entry for entry in list_entries(conn, 1) if entry['name'] == 'Crypt')['assigned']
        assert room_notes.remove_stale(conn, 1, area(variants[change]), 5, 3) == 0
        assert room_notes.remove_stale(conn, 1, old_area(), 5, 3) == 0
        assert [dict(r) for r in conn.execute('SELECT * FROM room_note_archives')] == [archive]
        assert snapshot(conn)['room_notes'] == expected
        after = snapshot(conn)
        for table in ('campaigns', 'fog_ops', 'map_fog_snapshots', 'imported_room_notes'):
            assert after[table] == before[table]
        assert after['maps'][1] == before['maps'][1]
        assert after['maps'][0]['room_notes_version'] == owner['room_notes_version'] + 1
        after['maps'][0]['room_notes_version'] = owner['room_notes_version']
        assert after['maps'] == before['maps']
        assert conn.execute('PRAGMA foreign_key_check').fetchall() == []


@pytest.mark.parametrize('stage', ['second_archive', 'first_delete'])
def test_reconcile_savepoint_failure_preserves_all_notes_and_outer_work(current, stage):
    with current.connect() as conn:
        if stage == 'second_archive':
            conn.executescript("CREATE TRIGGER fail_reconcile BEFORE INSERT ON room_note_archives WHEN (SELECT COUNT(*) FROM room_note_archives WHERE map_id=1)>=1 BEGIN SELECT RAISE(ABORT,'injected reconciliation failure'); END;")
        else:
            conn.executescript("CREATE TRIGGER fail_reconcile AFTER DELETE ON room_notes WHEN OLD.map_id=1 BEGIN SELECT RAISE(ABORT,'injected reconciliation failure'); END;")
    with current.connect() as conn:
        conn.execute('BEGIN IMMEDIATE')
        conn.execute("UPDATE campaigns SET description='outer work' WHERE id=1")
        before = dump(conn)
        with pytest.raises(sqlite3.IntegrityError, match='injected reconciliation failure'):
            room_notes.remove_stale(conn, 1, area([[0] * 5] * 3), 5, 3)
        assert conn.in_transaction
        assert dump(conn) == before
    with current.connect() as conn:
        assert conn.execute('SELECT description FROM campaigns WHERE id=1').fetchone()[0] == 'outer work'
        assert conn.execute('SELECT COUNT(*) FROM room_notes').fetchone()[0] == 4
        assert conn.execute('SELECT COUNT(*) FROM room_note_archives').fetchone()[0] == 0
        conn.execute('DROP TRIGGER fail_reconcile')
    with current.connect() as conn:
        assert room_notes.remove_stale(conn, 1, area([[0] * 5] * 3), 5, 3) == 2
        assert conn.execute('SELECT COUNT(*) FROM room_note_archives WHERE map_id=1').fetchone()[0] == 2
        assert conn.execute('SELECT COUNT(*) FROM room_notes WHERE map_id=2').fetchone()[0] == 2
        assert generations(conn) == [2, 0]
        assert conn.execute('PRAGMA foreign_key_check').fetchall() == []
