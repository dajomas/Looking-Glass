import pytest
from looking_glass.db import Database
from looking_glass.services.room_note_import import parse,store,list_entries,unassign,ImportError


def setup(tmp_path):
    db=Database(tmp_path/'test.db');db.migrate()
    with db.connect() as c:
        c.execute("INSERT INTO campaigns(id,name) VALUES(1,'Test')")
        for mid in (1,2):
            c.execute("INSERT INTO maps(id,campaign_id,name,image_file,width,height) VALUES(?,1,'Map','x',400,200)",(mid,))
            store(c,mid,parse(b'# Crypt\nOriginal\n# CRYPT\nAlternative\n# Hall\nOther')['entries'])
            for key,name,notes in [('a',' Crypt ','Custom edits'),('b','cRYpT','Original'),('c','Hall','Other')]:
                c.execute('INSERT INTO room_notes VALUES(?,?,10,10,?,?,7)',(mid,key,name,notes))
    return db


def test_unassign_all_matching_rooms_keeps_imports_and_other_maps(tmp_path):
    db=setup(tmp_path)
    with db.connect() as c:
        c.execute('BEGIN IMMEDIATE')
        before=[dict(r) for r in c.execute('SELECT * FROM imported_room_notes')]
        entry=next(e for e in list_entries(c,1) if e['name']=='Crypt')
        assert set(unassign(c,1,entry['id']))=={'a','b'}
        rows={r['area_key']:r for r in c.execute('SELECT * FROM room_notes WHERE map_id=1')}
        assert all(rows[k]['name']==rows[k]['markdown']=='' and rows[k]['revision']==8 for k in ['a','b'])
        assert rows['c']['name']=='Hall' and rows['c']['revision']==7
        assert [dict(r) for r in c.execute('SELECT * FROM imported_room_notes')]==before
        assert all(e['assigned'] for e in list_entries(c,2))
        assert all(not e['assigned'] for e in list_entries(c,1) if e['name'].casefold()=='crypt')
        assert unassign(c,1,entry['id'])==[]
        assert c.execute("SELECT revision FROM room_notes WHERE map_id=1 AND area_key='a'").fetchone()[0]==8


def test_wrong_map_and_missing_entry_rejected(tmp_path):
    db=setup(tmp_path)
    with db.connect() as c:
        entry=list_entries(c,2)[0]
        with pytest.raises(ImportError):unassign(c,1,entry['id'])
        with pytest.raises(ImportError):unassign(c,1,999999)
        assert c.execute("SELECT COUNT(*) FROM room_notes WHERE name<>''").fetchone()[0]==6


def test_unassign_rolls_back_on_error(tmp_path):
    db=setup(tmp_path)
    with pytest.raises(RuntimeError):
        with db.connect() as c:
            unassign(c,1,next(e for e in list_entries(c,1) if e['name']=='Crypt')['id'])
            raise RuntimeError('abort')
    with db.connect() as c:
        assert all(e['assigned'] for e in list_entries(c,1))
