"""Changed geometry releases imported names without touching unrelated rooms."""
from types import SimpleNamespace
import numpy as np
import pytest
from looking_glass.db import Database
from looking_glass.services.room_notes import area_key, remove_stale
from looking_glass.services.room_note_import import parse, store, list_entries, delete_unassigned


def area(rows):
    labels=np.array(rows,dtype=np.int32)
    return SimpleNamespace(labels=labels,shape=labels.shape,scale=1.0,region_signatures={})

@pytest.mark.parametrize('change',['split','merge','wall_anchor','outside'])
def test_changed_room_releases_library_and_preserves_other_map(tmp_path,change):
    db=Database(tmp_path/'test.db');db.migrate()
    old=area([[1,1,0,2,2],[1,1,0,2,2],[1,1,0,2,2]])
    variants={
        'split':[[1,1,0,2,2],[0,0,0,2,2],[3,3,0,2,2]],
        'merge':[[1,1,0,2,2],[1,1,1,2,2],[1,1,0,2,2]],
        'wall_anchor':[[0,1,0,2,2],[1,1,0,2,2],[1,1,0,2,2]],
        'outside':[[1,1,0,2,2],[1,1,0,2,2],[1,1,0,2,2]]}
    new=area(variants[change])
    with db.connect() as c:
        c.execute("INSERT INTO campaigns(id,name) VALUES(1,'Tour')")
        for mid in (1,2):
            c.execute("INSERT INTO maps(id,campaign_id,name,image_file,width,height) VALUES(?,1,'Map','x.png',5,3)",(mid,))
            store(c,mid,parse(b'# Crypt\nOriginal notes\n# Hall\nOther notes')['entries'])
            for lab,x,name in [(1,0,'Crypt'),(2,3,'Hall')]:
                c.execute('INSERT INTO room_notes VALUES(?,?,?,?,?,?,1)',(mid,area_key(old,lab,5,3),x,0,name,name+' notes'))
        if change=='outside':c.execute("UPDATE room_notes SET x=50 WHERE map_id=1 AND name='Crypt'")
        assert remove_stale(c,1,new,5,3)==1
        status={e['name']:e for e in list_entries(c,1)}
        assert not status['Crypt']['assigned'] and status['Hall']['assigned']
        assert status['Crypt']['markdown']=='Original notes'
        assert all(e['assigned'] for e in list_entries(c,2))
        assert remove_stale(c,1,new,5,3)==0
        # Old geometry returning must not resurrect the detached assignment.
        remove_stale(c,1,old,5,3)
        assert not next(e for e in list_entries(c,1) if e['name']=='Crypt')['assigned']
        delete_unassigned(c,1,status['Crypt']['id'])


def test_renumbering_preserves_names_and_transaction_rollback(tmp_path):
    db=Database(tmp_path/'test.db');db.migrate()
    old=area([[1,1,0,2,2]]);same=area([[9,9,0,7,7]])
    with db.connect() as c:
        c.execute("INSERT INTO campaigns(id,name) VALUES(1,'Tour')")
        c.execute("INSERT INTO maps(id,campaign_id,name,image_file,width,height) VALUES(1,1,'Map','x',5,1)")
        c.execute('INSERT INTO room_notes VALUES(1,?,0,0,?,?,1)',(area_key(old,1,5,1),'Crypt','Custom edits'))
        assert remove_stale(c,1,same,5,1)==0
    with pytest.raises(RuntimeError):
        with db.connect() as c:
            assert remove_stale(c,1,area([[1,0,0,2,2]]),5,1)==1
            raise RuntimeError('abort geometry update')
    with db.connect() as c:
        assert c.execute('SELECT markdown FROM room_notes').fetchone()[0]=='Custom edits'


def test_actual_wall_add_remove_releases_only_affected_rooms(tmp_path):
    from looking_glass.config import DEFAULTS
    from looking_glass.services.fog import FogEngine
    from looking_glass.services.wall_model import Calibration, WallSegment
    engine=FogEngine(DEFAULTS['fog'],DEFAULTS['viewer'],tmp_path/'cache')
    base=[WallSegment(50,0,50,99)]
    before=engine.build_area_map(100,100,base,Calibration(),True)
    added=engine.build_area_map(100,100,base+[WallSegment(0,50,50,50)],Calibration(),True)
    db=Database(tmp_path/'wall.db');db.migrate()
    with db.connect() as c:
        c.execute("INSERT INTO campaigns(id,name) VALUES(1,'Walls')")
        c.execute("INSERT INTO maps(id,campaign_id,name,image_file,width,height) VALUES(1,1,'Map','x',100,100)")
        for x,name in [(20,'Left'),(80,'Right')]:
            label=engine.label_at(before,x,20)
            c.execute('INSERT INTO room_notes VALUES(1,?,?,20,?,?,1)',(area_key(before,label,100,100),x,name,'Notes'))
        assert remove_stale(c,1,added,100,100)==1
        assert c.execute('SELECT name FROM room_notes').fetchone()[0]=='Right'
        label=engine.label_at(added,20,20)
        c.execute('INSERT INTO room_notes VALUES(1,?,20,20,?,?,1)',(area_key(added,label,100,100),'Split left','Notes'))
        assert remove_stale(c,1,before,100,100)==1
        assert c.execute('SELECT name FROM room_notes').fetchone()[0]=='Right'
