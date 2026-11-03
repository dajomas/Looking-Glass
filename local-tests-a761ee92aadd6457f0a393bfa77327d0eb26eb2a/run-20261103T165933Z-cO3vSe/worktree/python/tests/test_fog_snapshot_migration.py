"""Ordered initialization without rewriting previously saved display state."""
import json
import sqlite3

import pytest

from looking_glass.db import Database, MIGRATIONS
from looking_glass import migration_hooks


@pytest.fixture
def legacy(tmp_path):
    db = Database(tmp_path / "legacy.db")
    with db.connect() as conn:
        conn.executescript(MIGRATIONS[0] + MIGRATIONS[1])
        conn.executescript(
            "CREATE TABLE schema_version(version INTEGER NOT NULL);"
            "INSERT INTO schema_version VALUES(2);"
        )
        conn.execute("INSERT INTO users(id,username,password_hash,role) VALUES(1,'dm','','admin')")
        conn.execute("INSERT INTO campaigns(id,name,owner_id) VALUES(1,'Legacy',1)")
        conn.executemany(
            "INSERT INTO maps(id,campaign_id,name,image_file,width,height) VALUES(?,1,?,'map.png',400,200)",
            [(1, "A"), (2, "B"), (3, "Empty")],
        )
        conn.executemany(
            "INSERT INTO fog_ops(id,map_id,op,x,y,created_by) VALUES(?,?,?,?,?,1)",
            [(8, 1, "hide_all", None, None), (2, 1, "reveal", 12.5, 20.5),
             (5, 2, "hide", 3, 4), (1, 2, "reveal_all", None, None)],
        )
    return db


def test_interleaved_history_preserves_order_coordinates_and_empty_maps(legacy):
    assert legacy.migrate() == len(MIGRATIONS)
    assert legacy.migrate() == len(MIGRATIONS)
    with legacy.connect() as conn:
        for mid in (1, 2):
            expected = [dict(row) for row in conn.execute(
                "SELECT op,x,y FROM fog_ops WHERE map_id=? ORDER BY id", (mid,)
            )]
            actual = json.loads(conn.execute(
                "SELECT operations FROM map_fog_snapshots WHERE map_id=?", (mid,)
            ).fetchone()[0])
            assert actual == expected
        assert conn.execute("SELECT 1 FROM map_fog_snapshots WHERE map_id=3").fetchone() is None
        assert conn.execute("PRAGMA foreign_key_check").fetchall() == []


def test_already_migrated_snapshot_is_not_rebuilt(legacy, monkeypatch):
    legacy.migrate()
    with legacy.connect() as conn:
        conn.execute("UPDATE map_fog_snapshots SET operations='[]',updated_at='sentinel' WHERE map_id=1")
    def unexpected(_conn):
        raise AssertionError("Must not rerun migration 3's initialization")
    monkeypatch.setattr(migration_hooks, "_initialize_ordered_fog_snapshots", unexpected)
    assert legacy.migrate() == len(MIGRATIONS)
    with legacy.connect() as conn:
        assert tuple(conn.execute(
            "SELECT operations,updated_at FROM map_fog_snapshots WHERE map_id=1"
        ).fetchone()) == ("[]", "sentinel")


def test_later_upgrade_preserves_saved_snapshot(legacy, monkeypatch):
    with legacy.connect() as conn:
        migration_hooks.apply_migration(conn, 3, MIGRATIONS[2])
        conn.execute("UPDATE map_fog_snapshots SET operations='[]',updated_at='sentinel' WHERE map_id=1")
    def unexpected(_conn):
        raise AssertionError("Existing saved state must remain untouched")
    monkeypatch.setattr(migration_hooks, "_initialize_ordered_fog_snapshots", unexpected)
    assert legacy.migrate() == len(MIGRATIONS)
    with legacy.connect() as conn:
        assert tuple(conn.execute(
            "SELECT operations,updated_at FROM map_fog_snapshots WHERE map_id=1"
        ).fetchone()) == ("[]", "sentinel")


def test_initialization_failure_rolls_back_schema_data_and_version(legacy, monkeypatch):
    original = migration_hooks._initialize_ordered_fog_snapshots
    def fail(conn):
        assert conn.in_transaction
        assert conn.execute("SELECT MAX(version) FROM schema_version").fetchone()[0] == 2
        original(conn)
        raise RuntimeError("injected initialization failure")
    with monkeypatch.context() as context:
        context.setattr(migration_hooks, "_initialize_ordered_fog_snapshots", fail)
        with pytest.raises(RuntimeError, match="injected"):
            legacy.migrate()
    with legacy.connect() as conn:
        assert conn.execute("SELECT MAX(version) FROM schema_version").fetchone()[0] == 2
        assert "cache_token" not in [r["name"] for r in conn.execute("PRAGMA table_info(maps)")]
        assert conn.execute("SELECT name FROM sqlite_master WHERE name='map_fog_snapshots'").fetchone() is None
        assert conn.execute("SELECT COUNT(*) FROM fog_ops").fetchone()[0] == 4
    assert legacy.migrate() == len(MIGRATIONS)


def test_version_record_failure_rolls_back_initialization(legacy):
    with legacy.connect() as conn:
        conn.executescript(
            "CREATE TRIGGER reject_version3 BEFORE INSERT ON schema_version "
            "WHEN NEW.version=3 BEGIN SELECT RAISE(ABORT,'injected version failure'); END;"
        )
    with pytest.raises(sqlite3.IntegrityError, match="injected version failure"):
        legacy.migrate()
    with legacy.connect() as conn:
        assert conn.execute("SELECT MAX(version) FROM schema_version").fetchone()[0] == 2
        assert "cache_token" not in [r["name"] for r in conn.execute("PRAGMA table_info(maps)")]
        assert conn.execute("SELECT name FROM sqlite_master WHERE name='map_fog_snapshots'").fetchone() is None
        conn.execute("DROP TRIGGER reject_version3")
    assert legacy.migrate() == len(MIGRATIONS)
