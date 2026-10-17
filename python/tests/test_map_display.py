"""Restore/reset policy, cascade cleanup, and migration regression tests."""
import json

import pytest

from looking_glass.db import Database, MIGRATIONS
from looking_glass.repositories import campaigns, maps, fog_ops
from looking_glass.services.map_display import activate, checkpoint_if_active


@pytest.fixture
def display_db(tmp_path):
    db = Database(tmp_path / "display.db")
    db.migrate()
    with db.connect() as conn:
        conn.execute("INSERT INTO users(id, username, password_hash, role) VALUES (1, 'dm', '', 'admin')")
        cid = campaigns.create(conn, "C", "", 1)
        a = maps.create(conn, cid, "A", "a.png", 400, 200, True)
        b = maps.create(conn, cid, "B", "b.png", 400, 200, True)
    return db, cid, a, b


def points(conn, mid):
    return [(o.op, o.x, o.y) for o in fog_ops.list_for_map(conn, mid)]


def test_explicit_choice_required_and_cancel_has_no_write(display_db):
    db, cid, a, _ = display_db
    with db.connect() as c:
        fog_ops.add(c, a, "reveal", 100, 100, 1)
        with pytest.raises(ValueError):
            activate(c, cid, a, None, 1)
        assert campaigns.get(c, cid)["active_map_id"] is None
        assert len(points(c, a)) == 1


def test_first_display_can_keep_prepared_reveals(display_db):
    db, cid, a, _ = display_db
    with db.connect() as c:
        fog_ops.add(c, a, "reveal", 100, 100, 1)
        activate(c, cid, a, "restore", 1)
        assert points(c, a) == [("reveal", 100, 100)]


def test_restore_uses_last_display_not_later_offline_edits(display_db):
    db, cid, a, b = display_db
    with db.connect() as c:
        activate(c, cid, a, "reset", 1)
        fog_ops.add(c, a, "reveal", 100, 100, 1)
        checkpoint_if_active(c, a)
        activate(c, cid, b, "reset", 1)
        fog_ops.add(c, a, "reveal", 300, 100, 1)
        activate(c, cid, a, "restore", 1)
        assert points(c, a) == [("reveal", 100, 100)]


def test_reset_erases_undo_history_and_does_not_touch_other_map(display_db):
    db, cid, a, b = display_db
    with db.connect() as c:
        fog_ops.add(c, a, "reveal_all", None, None, 1)
        fog_ops.add(c, b, "reveal", 20, 20, 1)
        activate(c, cid, a, "reset", 1)
        assert points(c, a) == []
        assert not fog_ops.undo(c, a)
        assert len(points(c, b)) == 1
        assert json.loads(c.execute("SELECT operations FROM map_fog_snapshots WHERE map_id = ?", (a,)).fetchone()[0]) == []


def test_blank_checkpoints_without_reset(display_db):
    db, cid, a, _ = display_db
    with db.connect() as c:
        activate(c, cid, a, "restore", 1)
        fog_ops.add(c, a, "reveal", 100, 100, 1)
        activate(c, cid, None, None, 1)
        fog_ops.clear(c, a)
        activate(c, cid, a, "restore", 1)
        assert points(c, a) == [("reveal", 100, 100)]


def test_checkpoint_survives_reopen(display_db):
    db, cid, a, _ = display_db
    with db.connect() as c:
        activate(c, cid, a, "reset", 1)
        fog_ops.add(c, a, "reveal", 100, 100, 1)
        checkpoint_if_active(c, a)
    reopened = Database(db.path)
    with reopened.connect() as c:
        assert c.execute("SELECT operations FROM map_fog_snapshots WHERE map_id = ?", (a,)).fetchone()
        assert points(c, a) == [("reveal", 100, 100)]


def test_reused_numeric_id_has_new_identity_and_no_history(display_db):
    db, cid, a, b = display_db
    with db.connect() as c:
        activate(c, cid, b, "restore", 1)
        fog_ops.add(c, b, "reveal", 100, 100, 1)
        checkpoint_if_active(c, b)
        old_token = maps.get(c, b)["cache_token"]
        maps.delete(c, b)
        new = maps.create(c, cid, "New", "new.png", 400, 200, True)
        assert new == b  # reproduces SQLite ID reuse
        assert maps.get(c, new)["cache_token"] != old_token
        assert points(c, new) == []
        assert not c.execute("SELECT 1 FROM map_fog_snapshots WHERE map_id = ?", (new,)).fetchone()


def test_cross_campaign_target_rejected_without_side_effects(display_db):
    db, cid, a, _ = display_db
    with db.connect() as c:
        other = campaigns.create(c, "Other", "", 1)
        with pytest.raises(ValueError):
            activate(c, other, a, "reset", 1)
        assert campaigns.get(c, other)["active_map_id"] is None


def test_upgrade_preserves_existing_history_and_is_idempotent(tmp_path):
    db = Database(tmp_path / "old.db")
    with db.connect() as c:
        c.executescript(MIGRATIONS[0] + MIGRATIONS[1])
        c.executescript("CREATE TABLE schema_version(version INTEGER NOT NULL); INSERT INTO schema_version VALUES (2);")
        c.execute("INSERT INTO users(id,username,password_hash,role) VALUES(1,'dm','','admin')")
        cid = campaigns.create(c, "Old", "", 1)
        a = maps.create(c, cid, "A", "a.png", 400, 200, True)
        fog_ops.add(c, a, "reveal", 100, 100, 1)
        fog_ops.add(c, a, "hide_all", None, None, 1)
    assert db.migrate() == 3
    assert db.migrate() == 3
    with db.connect() as c:
        assert maps.get(c, a)["cache_token"]
        saved = json.loads(c.execute("SELECT operations FROM map_fog_snapshots WHERE map_id = ?", (a,)).fetchone()[0])
        assert [o["op"] for o in saved] == ["reveal", "hide_all"]
        assert c.execute("PRAGMA foreign_key_check").fetchall() == []
