"""Room identity, migration, persistence and Markdown safety regression tests."""
import sqlite3
from types import SimpleNamespace
import numpy as np
import pytest
from looking_glass.db import Database
from looking_glass.services.room_notes import area_key, render, payload


def area(labels):
    return SimpleNamespace(labels=np.array(labels), scale=1.0, shape=np.array(labels).shape, region_signatures={})


def test_geometry_identity_not_component_number():
    a=area([[1,0,2],[1,0,2]])
    b=area([[7,0,9],[7,0,9]])
    assert area_key(a,1,3,2)==area_key(b,7,3,2)
    assert area_key(a,1,3,2)!=area_key(a,2,3,2)
    assert area_key(a,1,3,2)!=area_key(area([[1,1,2],[1,0,2]]),1,3,2)


def test_markdown_safety_and_formatting():
    html=render("# Crypt\n\n**Treasure** and *danger*.\n\n- gold\n- bones\n\n<script>alert(1)</script>\n\n[x](javascript:alert(1))\n\n![remote](https://example.org/track)")
    assert "<h1>Crypt</h1>" in html and "<strong>Treasure</strong>" in html
    assert "<ul>" in html
    assert "<script>" not in html and 'href="javascript:' not in html and "<img" not in html


def test_migration_idempotent_and_foreign_key_cascade(tmp_path):
    db=Database(tmp_path/"rooms.db")
    version=db.migrate()
    assert db.migrate()==version
    with db.connect() as conn:
        assert {r[1] for r in conn.execute("PRAGMA table_info(room_notes)")} >= {"map_id","area_key","name","markdown","revision"}
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute("INSERT INTO room_notes(map_id,area_key,x,y,name) VALUES(999,'k',1,1,'Crypt')")
        conn.rollback()
        conn.execute("BEGIN")
        with pytest.raises(RuntimeError, match="Map disappeared"):
            payload(conn,999,'k',False)


def test_payload_requires_an_active_transaction(tmp_path):
    db = Database(tmp_path / "payload-transaction.db")
    db.migrate()
    with db.connect() as conn:
        assert not conn.in_transaction
        with pytest.raises(RuntimeError, match="active transaction"):
            payload(conn, 999, "a" * 64, False)
        assert not conn.in_transaction


def test_payload_context_tracks_saved_content_and_preserves_other_maps(tmp_path):
    db = Database(tmp_path / "payload-context.db")
    db.migrate()
    key = "a" * 64
    markdown = "# Secret\r\n\n**Gold** and café 🐉\n"
    with db.connect() as conn:
        conn.execute("INSERT INTO campaigns(id,name) VALUES(1,'Adventure')")
        for mid in (1, 2):
            conn.execute("""INSERT INTO maps(
                id,campaign_id,name,image_file,width,height,walls_version,fog_version
            ) VALUES(?,1,'Map','fixture.png',100,100,7,11)""", (mid,))
        context = dict(conn.execute("SELECT * FROM maps WHERE id=1").fetchone())
        empty = payload(conn, 1, key, False)
        assert empty["name"] == empty["markdown"] == empty["html"] == ""
        assert empty["revision"] == empty["room_notes_version"] == 0
        assert empty["cache_token"] == context["cache_token"]
        assert empty["walls_version"] == 7
        assert empty["area_key"] == key and empty["revealed"] is False
        conn.execute("""INSERT INTO room_notes(
            map_id,area_key,x,y,name,markdown,revision
        ) VALUES(1,?,10,20,'Crypt',?,7)""", (key, markdown))
        saved = payload(conn, 1, key, True)
        assert saved["name"] == "Crypt" and saved["markdown"] == markdown
        assert saved["revision"] == 7 and saved["room_notes_version"] == 1
        assert "<strong>Gold</strong>" in saved["html"]
        assert saved["revealed"] is True
        conn.execute("UPDATE room_notes SET markdown='Changed',revision=revision+1 WHERE map_id=1 AND area_key=?", (key,))
        updated = payload(conn, 1, key, True)
        assert updated["markdown"] == "Changed"
        assert updated["revision"] == 8 and updated["room_notes_version"] == 2
        assert updated["cache_token"] == context["cache_token"]
        assert updated["walls_version"] == 7
        assert payload(conn, 2, key, False)["room_notes_version"] == 0
        assert conn.execute("SELECT fog_version FROM maps WHERE id=1").fetchone()[0] == 11
        assert conn.execute("SELECT COUNT(*) FROM fog_ops").fetchone()[0] == 0
        assert conn.execute("SELECT COUNT(*) FROM room_note_archives").fetchone()[0] == 0


def test_payload_generation_and_content_follow_transaction_rollback(tmp_path):
    db = Database(tmp_path / "payload-rollback.db")
    db.migrate()
    key = "b" * 64
    with db.connect() as conn:
        conn.execute("INSERT INTO campaigns(id,name) VALUES(1,'Adventure')")
        conn.execute("INSERT INTO maps(id,campaign_id,name,image_file,width,height) VALUES(1,1,'Map','fixture.png',100,100)")
        conn.execute("INSERT INTO room_notes(map_id,area_key,x,y,name,markdown) VALUES(1,?,10,20,'Room','Original')", (key,))
    with pytest.raises(RuntimeError, match="abort update"):
        with db.connect() as conn:
            conn.execute("UPDATE room_notes SET markdown='Temporary',revision=revision+1 WHERE map_id=1 AND area_key=?", (key,))
            temporary = payload(conn, 1, key, False)
            assert temporary["revision"] == temporary["room_notes_version"] == 2
            raise RuntimeError("abort update")
    with db.connect() as conn:
        conn.execute("BEGIN")
        restored = payload(conn, 1, key, False)
        assert restored["markdown"] == "Original"
        assert restored["revision"] == restored["room_notes_version"] == 1
