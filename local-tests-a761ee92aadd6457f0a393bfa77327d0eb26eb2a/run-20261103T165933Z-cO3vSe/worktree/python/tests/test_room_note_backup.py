"""Retained-note backup regressions using real migrated SQLite and PNG storage."""
import sqlite3

import pytest

from test_campaign_backup import env
from looking_glass.services import campaign_backup as service, images, room_notes


@pytest.fixture
def retained(env):
    db,maps,_=env
    with db.connect() as conn:
        conn.execute("UPDATE room_notes SET name='  Custom  ',markdown=?,revision=9 WHERE map_id=1",
                     ("# Secret\r\n\n**Gold** and café 🐉\n",))
        aid=room_notes.archive_assignment(conn,1,"area","geometry_changed")
        conn.execute("DELETE FROM room_notes WHERE map_id=1 AND area_key='area'")
        conn.execute("UPDATE room_note_archives SET source_map_id=999,source_campaign_id=888 WHERE id=?",(aid,))
        original=dict(conn.execute("SELECT * FROM room_note_archives WHERE id=?",(aid,)).fetchone())
    with db.connect() as conn:
        raw=service.export_campaign(conn,1,maps)
    return db,maps,raw,original


def test_archive_roundtrip_remaps_only_ownership_and_keeps_detached_content(retained):
    db,maps,raw,original=retained
    with db.connect() as conn:
        conn.execute("BEGIN IMMEDIATE")
        report=service.inspect_campaign(conn,2,raw,10**7)
        assert report["counts"]["room_note_archives"]==1
        service.restore_campaign(conn,2,maps,raw,10**7,[])
    with db.connect() as conn:
        restored=dict(conn.execute("""SELECT a.* FROM room_note_archives a
            JOIN maps m ON m.id=a.map_id WHERE m.campaign_id=2""").fetchone())
        assert restored["map_id"]!=original["map_id"]
        assert restored["id"]!=original["id"]
        historical=lambda row:{k:v for k,v in row.items() if k not in ("id","map_id")}
        assert historical(restored)==historical(original)
        assert dict(conn.execute("SELECT * FROM room_note_archives WHERE id=?",(original["id"],)).fetchone())==original
        assert conn.execute("SELECT COUNT(*) FROM room_notes WHERE map_id=?",(restored["map_id"],)).fetchone()[0]==0
        assert conn.execute("PRAGMA foreign_key_check").fetchall()==[]
        assert conn.execute("PRAGMA integrity_check").fetchone()[0]=="ok"


def test_archive_only_change_invalidates_restore_preview(retained):
    db,maps,raw,original=retained
    with db.connect() as conn:
        conn.execute("BEGIN IMMEDIATE")
        token=service.preview_token(conn,1,1,raw)
        service.verify_preview(conn,1,1,raw,token)
        before=conn.execute("SELECT room_notes_version FROM maps WHERE id=1").fetchone()[0]
        keys=list(original)
        copy={k:v for k,v in original.items() if k!="id"}
        copy["origin_uuid"]="another-retained-event"
        keys=list(copy)
        conn.execute(f"INSERT INTO room_note_archives ({','.join(keys)}) VALUES ({','.join('?' for _ in keys)})",[copy[k] for k in keys])
        assert conn.execute("SELECT room_notes_version FROM maps WHERE id=1").fetchone()[0]==before
        with pytest.raises(ValueError,match="changed"):
            service.verify_preview(conn,1,1,raw,token)


def test_restore_failure_at_archive_insertion_rolls_back_database_and_owned_files(retained):
    db,maps,raw,original=retained
    with db.connect() as conn:
        conn.executescript("""CREATE TRIGGER reject_restored_archive AFTER INSERT ON room_note_archives
            BEGIN SELECT RAISE(ABORT,'injected archive restore failure'); END;""")
        before=list(conn.iterdump())
    files_before={p.relative_to(maps):p.read_bytes() for p in maps.rglob("*") if p.is_file()}
    created=[]
    try:
        with pytest.raises(sqlite3.IntegrityError,match="injected archive restore failure"):
            with db.connect() as conn:
                conn.execute("BEGIN IMMEDIATE")
                service.restore_campaign(conn,1,maps,raw,10**7,created)
    finally:
        for path in created:
            images.delete_map_image(maps,path)
    assert created,"Image storage must succeed before the injected archive failure"
    with db.connect() as conn:
        assert list(conn.iterdump())==before
    assert {p.relative_to(maps):p.read_bytes() for p in maps.rglob("*") if p.is_file()}==files_before
