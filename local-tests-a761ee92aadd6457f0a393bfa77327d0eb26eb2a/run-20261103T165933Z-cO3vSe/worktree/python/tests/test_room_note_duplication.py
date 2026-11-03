"""Archive copy regressions with real migrated SQLite/PNG storage, not HTTP."""
import sqlite3

import pytest
from PIL import Image

from test_campaign_backup import env
from test_room_note_backup import retained
from looking_glass.services import duplication, images, room_notes


@pytest.fixture
def source(retained):
    db,maps,_,_=retained
    with db.connect() as conn:
        conn.execute("INSERT INTO room_notes(map_id,area_key,x,y,name,markdown,revision) VALUES(1,'hall',5,5,'Hall','Keep active',4)")
        conn.execute("INSERT INTO maps(id,campaign_id,name,image_file,width,height) VALUES(2,1,'Other map','1/a.png',20,30)")
        conn.execute("INSERT INTO room_notes(map_id,area_key,x,y,name,markdown,revision) VALUES(2,'other',5,5,'Other','Other retained',5)")
        room_notes.archive_assignment(conn,2,"other","geometry_changed")
        conn.execute("DELETE FROM room_notes WHERE map_id=2")
        conn.execute("UPDATE room_note_archives SET archived_at='2001-02-03 04:05:06'")
        conn.execute("UPDATE maps SET room_notes_version=CASE id WHEN 1 THEN 1234 ELSE 5678 END WHERE id IN (1,2)")
    return db,maps


def source_state(conn):
    result={}
    for table in ("maps","room_notes","room_note_archives","fog_ops","map_fog_snapshots"):
        where="id IN (1,2)" if table=="maps" else "map_id IN (1,2)"
        result[table]=[dict(r) for r in conn.execute(f"SELECT * FROM {table} WHERE {where} ORDER BY rowid")]
    result["campaign"]=dict(conn.execute("SELECT * FROM campaigns WHERE id=1").fetchone())
    result["viewers"]=[dict(r) for r in conn.execute("SELECT * FROM campaign_viewers WHERE campaign_id=1 ORDER BY user_id")]
    return result


@pytest.mark.parametrize("kind",["map","campaign"])
def test_repeated_clean_copies_preserve_archives_and_independent_generations(source,kind):
    db,maps=source
    with db.connect() as conn:
        original=source_state(conn)
        archives={r["map_id"]:r for r in original["room_note_archives"]}
    file_bytes=(maps/"1/a.png").read_bytes()
    copied_ids=set()
    copied_paths=set()
    archive_ids={r["id"] for r in archives.values()}
    for index in range(2):
        created=[]
        with db.connect() as conn:
            conn.execute("BEGIN IMMEDIATE")
            target,mapping=duplication.duplicate(conn,1,maps,created,f"Copy {index}",1,1 if kind=="map" else None)
        assert set(mapping)==({1} if kind=="map" else {1,2})
        assert len(created)==len(mapping)
        with db.connect() as conn:
            assert source_state(conn)==original
            assert conn.execute("SELECT active_map_id FROM campaigns WHERE id=1").fetchone()[0]==1
            if kind=="campaign":
                campaign=conn.execute("SELECT * FROM campaigns WHERE id=?",(target,)).fetchone()
                assert campaign["active_map_id"] is None and campaign["owner_id"]==1
                assert conn.execute("SELECT COUNT(*) FROM campaign_viewers WHERE campaign_id=?",(target,)).fetchone()[0]==0
            else:
                assert target==1
            for old,new in mapping.items():
                assert new not in copied_ids and new not in (1,2)
                copied_ids.add(new)
                row=conn.execute("SELECT * FROM maps WHERE id=?",(new,)).fetchone()
                old_row=next(r for r in original["maps"] if r["id"]==old)
                assert row["cache_token"]!=old_row["cache_token"]
                assert row["walls_version"]==row["fog_version"]==0
                active=[dict(r) for r in conn.execute("SELECT * FROM room_notes WHERE map_id=?",(new,))]
                assert [(r["name"],r["markdown"],r["revision"]) for r in active]==([('Hall','Keep active',1)] if old==1 else [])
                assert row["room_notes_version"]==len(active)
                copied=[dict(r) for r in conn.execute("SELECT * FROM room_note_archives WHERE map_id=?",(new,))]
                assert len(copied)==1
                archive=copied[0]
                assert archive["id"] not in archive_ids
                archive_ids.add(archive["id"])
                historical=lambda r:{k:v for k,v in r.items() if k not in ("id","map_id")}
                assert historical(archive)==historical(archives[old])
                assert archive["source_revision"]==(9 if old==1 else 5)
                assert row["image_file"] not in copied_paths and row["image_file"]!=old_row["image_file"]
                copied_paths.add(row["image_file"])
                with Image.open(maps/row["image_file"]) as image:
                    image.load();assert image.size==(20,30)
                for table in ("fog_ops","map_fog_snapshots"):
                    assert conn.execute(f"SELECT COUNT(*) FROM {table} WHERE map_id=?",(new,)).fetchone()[0]==0
                assert conn.execute("SELECT COUNT(*) FROM door_runtime_states WHERE wall_id IN (SELECT id FROM walls WHERE map_id=?)",(new,)).fetchone()[0]==0
                assert conn.execute("SELECT COUNT(*) FROM passage_runtime_states WHERE wall_id IN (SELECT id FROM walls WHERE map_id=?)",(new,)).fetchone()[0]==0
            assert conn.execute("PRAGMA foreign_key_check").fetchall()==[]
    assert (maps/"1/a.png").read_bytes()==file_bytes
    with db.connect() as conn:
        assert conn.execute("SELECT COUNT(*) FROM room_note_archives WHERE origin_uuid=?",(archives[1]["origin_uuid"],)).fetchone()[0]==3


@pytest.mark.parametrize("kind",["map","campaign"])
def test_archive_copy_failure_rolls_back_and_caller_cleans_only_created_images(source,kind):
    db,maps=source
    with db.connect() as conn:
        conn.executescript("""CREATE TRIGGER reject_copied_archive AFTER INSERT ON room_note_archives
            WHEN NEW.map_id NOT IN (1,2)
            BEGIN SELECT RAISE(ABORT,'injected archive copy failure'); END;""")
        before=list(conn.iterdump())
    files={p.relative_to(maps):p.read_bytes() for p in maps.rglob("*") if p.is_file()}
    created=[]
    try:
        with pytest.raises(sqlite3.IntegrityError,match="injected archive copy failure"):
            with db.connect() as conn:
                conn.execute("BEGIN IMMEDIATE")
                duplication.duplicate(conn,1,maps,created,"Failed copy",1,1 if kind=="map" else None)
    finally:
        for path in created:
            images.delete_map_image(maps,path)
    assert created,"The test must reach archival after successful image storage"
    with db.connect() as conn:
        assert list(conn.iterdump())==before
    assert {p.relative_to(maps):p.read_bytes() for p in maps.rglob("*") if p.is_file()}==files
