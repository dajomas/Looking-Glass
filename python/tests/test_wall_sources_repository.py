"""Source persistence and migration tests; no web framework required."""

import sqlite3

import pytest

from looking_glass.db import Database, MIGRATIONS
from looking_glass.repositories import wall_sources as repo


@pytest.fixture
def source_db(tmp_path):
    db = Database(tmp_path / "library.db")
    assert db.migrate() == 2
    with db.connect() as conn:
        conn.execute("INSERT INTO campaigns (id, name) VALUES (1, 'A'), (2, 'B')")
    return db


def test_upgrade_v1_preserves_data(tmp_path):
    db = Database(tmp_path / "old.db")
    conn = sqlite3.connect(db.path)
    conn.executescript(MIGRATIONS[0])
    conn.execute("CREATE TABLE schema_version (version INTEGER NOT NULL)")
    conn.execute("INSERT INTO schema_version VALUES (1)")
    conn.execute("INSERT INTO campaigns (name) VALUES ('Existing')")
    conn.commit(); conn.close()
    assert db.migrate() == 2
    assert db.migrate() == 2
    with db.connect() as conn:
        assert conn.execute("SELECT name FROM campaigns").fetchone()[0] == "Existing"
        assert conn.execute("SELECT count(*) FROM wall_sources").fetchone()[0] == 0


def test_round_trip_and_restart(source_db):
    with source_db.connect() as conn:
        saved = repo.save(conn, 1, "maps.db", b"immutable bytes", 13)
        sid = saved["id"]
    assert Database(source_db.path).migrate() == 2
    with Database(source_db.path).connect() as conn:
        source = repo.get(conn, 1, sid)
        assert source["raw"] == b"immutable bytes"
        assert source["scene_count"] == 13
        assert repo.list_for_campaign(conn, 1)[0]["filename"] == "maps.db"
        assert "raw" not in repo.list_for_campaign(conn, 1)[0].keys()


def test_dedup_retains_first_filename(source_db):
    with source_db.connect() as conn:
        a = repo.save(conn, 1, "first.db", b"same", 2)
        b = repo.save(conn, 1, "renamed.db", b"same", 2)
        assert a["id"] == b["id"]
        assert b["filename"] == "first.db"
        assert len(repo.list_for_campaign(conn, 1)) == 1


def test_changed_content_is_new_source(source_db):
    with source_db.connect() as conn:
        a = repo.save(conn, 1, "maps.db", b"old", 2)
        b = repo.save(conn, 1, "maps.db", b"new", 3)
        assert a["id"] != b["id"]


def test_campaign_isolation(source_db):
    with source_db.connect() as conn:
        a = repo.save(conn, 1, "maps.db", b"same", 2)
        b = repo.save(conn, 2, "maps.db", b"same", 2)
        assert a["id"] != b["id"]
        assert repo.get(conn, 2, a["id"]) is None
        repo.delete(conn, 2, a["id"])
        assert repo.get(conn, 1, a["id"]) is not None


@pytest.mark.parametrize("filename, expected", [
    ("../../maps.db", "maps.db"),
    ("C:\\exports\\maps.db", "maps.db"),
    ("", "walls"),
    ("a" * 300, "a" * 255),
])
def test_filename_normalization(source_db, filename, expected):
    with source_db.connect() as conn:
        assert repo.save(conn, 1, filename, b"x", 1)["filename"] == expected


def test_campaign_delete_cascades(source_db):
    with source_db.connect() as conn:
        a = repo.save(conn, 1, "maps.db", b"one", 2)
        b = repo.save(conn, 2, "maps.db", b"two", 2)
        conn.execute("DELETE FROM campaigns WHERE id = 1")
        assert repo.get(conn, 1, a["id"]) is None
        assert repo.get(conn, 2, b["id"]) is not None


def test_source_delete_keeps_map_walls_and_ids_not_reused(source_db):
    with source_db.connect() as conn:
        a = repo.save(conn, 1, "maps.db", b"one", 1)
        conn.execute("INSERT INTO maps (id,campaign_id,name,image_file,width,height) "
                     "VALUES (1,1,'Map','x.png',400,200)")
        conn.execute("INSERT INTO walls (map_id,x1,y1,x2,y2) VALUES (1,0,0,10,10)")
        repo.delete(conn, 1, a["id"])
        b = repo.save(conn, 1, "maps.db", b"two", 1)
        assert b["id"] > a["id"]
        assert conn.execute("SELECT count(*) FROM walls WHERE map_id = 1").fetchone()[0] == 1


def test_transaction_rollback(source_db):
    with pytest.raises(RuntimeError):
        with source_db.connect() as conn:
            repo.save(conn, 1, "maps.db", b"rollback", 1)
            raise RuntimeError("abort")
    with source_db.connect() as conn:
        assert not repo.list_for_campaign(conn, 1)
