"""Upgrade and empty metadata persistence regressions without HTTP dependencies."""
import sqlite3
import pytest
from looking_glass.db import Database, MIGRATIONS
from looking_glass.services.room_notes import payload


def test_upgrade_preserves_notes_and_allows_clear(tmp_path):
    path=tmp_path/"old.sqlite"
    conn=sqlite3.connect(path)
    conn.execute("CREATE TABLE schema_version(version INTEGER NOT NULL)")
    for version,script in enumerate(MIGRATIONS[:-1],1):
        conn.executescript(script)
        conn.execute("INSERT INTO schema_version VALUES(?)",(version,))
        conn.commit()
    conn.execute("INSERT INTO campaigns(id,name) VALUES(1,'Campaign')")
    conn.execute("INSERT INTO maps(id,campaign_id,name,image_file,width,height) VALUES(1,1,'Map','map.png',400,200)")
    conn.execute("INSERT INTO room_notes VALUES(1,'key',100,100,'Crypt','Gold',7)")
    conn.execute("INSERT INTO imported_room_notes(map_id,name,markdown,digest) VALUES(1,'Library','Treasure','digest')")
    conn.commit();conn.close()
    db=Database(path)
    assert db.migrate()==len(MIGRATIONS)
    assert db.migrate()==len(MIGRATIONS)
    with db.connect() as conn:
        conn.execute("BEGIN")
        before=payload(conn,1,'key',True)
        assert before['revision']==7 and before['name']=='Crypt' and before['markdown']=='Gold'
        conn.execute("UPDATE room_notes SET name='',revision=revision+1 WHERE map_id=1")
        assert payload(conn,1,'key',False)['markdown']=='Gold'
        conn.execute("UPDATE room_notes SET markdown='',revision=revision+1 WHERE map_id=1")
        empty=payload(conn,1,'key',True)
        assert empty['name']==empty['markdown']==empty['html']==''
        assert empty['revision']==9
        assert conn.execute("SELECT COUNT(*) FROM imported_room_notes").fetchone()[0]==1
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute("UPDATE room_notes SET name=?",('x'*201,))
        conn.execute("DELETE FROM maps WHERE id=1")
        assert conn.execute("SELECT COUNT(*) FROM room_notes").fetchone()[0]==0
        assert conn.execute("SELECT COUNT(*) FROM imported_room_notes").fetchone()[0]==0
