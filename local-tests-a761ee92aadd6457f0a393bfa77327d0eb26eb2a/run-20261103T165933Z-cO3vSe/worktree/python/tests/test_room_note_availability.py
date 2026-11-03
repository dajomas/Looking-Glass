from looking_glass.db import Database
from looking_glass.services.room_note_import import parse, store, list_entries


def test_assigned_names_are_map_scoped_and_released_by_rename_or_clear(tmp_path):
    db=Database(tmp_path/"db.sqlite");db.migrate()
    with db.connect() as conn:
        conn.execute("INSERT INTO campaigns(id,name) VALUES(1,'Campaign')")
        for mid in (1,2):
            conn.execute("INSERT INTO maps(id,campaign_id,name,image_file,width,height) VALUES(?,1,'Map','map.png',400,200)",(mid,))
            store(conn,mid,parse(b"# Crypt\nGold\n# Crypt\nDifferent notes\n# Hall\nBones\n")["entries"])
        conn.execute("INSERT INTO room_notes VALUES(1,'a',100,100,'  cRyPt  ','Manually edited notes',1)")
        def status(mid):
            return [(r['name'],r['assigned']) for r in list_entries(conn,mid)]
        assert status(1)==[('Crypt',True),('Crypt',True),('Hall',False)]
        assert status(2)==[('Crypt',False),('Crypt',False),('Hall',False)]
        conn.execute("UPDATE room_notes SET name='Hall' WHERE map_id=1")
        assert status(1)==[('Crypt',False),('Crypt',False),('Hall',True)]
        conn.execute("UPDATE room_notes SET name='' WHERE map_id=1")
        assert status(1)==[('Crypt',False),('Crypt',False),('Hall',False)]
        conn.execute("UPDATE room_notes SET name='Crypt' WHERE map_id=1")
        conn.execute("INSERT INTO room_notes VALUES(1,'b',200,100,'CRYPT','',1)")
        conn.execute("UPDATE room_notes SET name='' WHERE area_key='a'")
        assert status(1)[0][1] is True
        conn.execute("UPDATE room_notes SET name='' WHERE area_key='b'")
        assert status(1)[0][1] is False
        assert len(list_entries(conn,1))==3  # No library records are consumed/deleted.
