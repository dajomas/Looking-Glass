import io
import json
import zipfile
import pytest
from PIL import Image
from looking_glass.db import Database
from looking_glass.services.campaign_backup import export_campaign, restore_campaign

@pytest.fixture
def env(tmp_path):
    db = Database(tmp_path / "test.db")
    db.migrate()
    maps = tmp_path / 'maps'
    (maps / '1').mkdir(parents=True)
    Image.new('RGB',(20,30)).save(maps / '1/a.png')
    with db.connect() as c:
        c.execute("INSERT INTO users(id,username,password_hash,role) VALUES(1,'dm','private','admin')")
        c.execute("INSERT INTO campaigns(id,name,owner_id) VALUES(1,'Adventure',1),(2,'Other',1)")
        c.execute("INSERT INTO campaign_viewers VALUES(1,1,NULL,'now')")
        c.execute("INSERT INTO maps(id,campaign_id,name,image_file,width,height) VALUES(1,1,'Map','1/a.png',20,30)")
        c.execute("INSERT INTO walls(id,map_id,x1,y1,x2,y2,kind) VALUES(1,1,0,0,20,0,'locked_door')")
        c.execute("INSERT INTO fog_ops(map_id,op) VALUES(1,'hide_all')")
        c.execute("INSERT INTO door_runtime_states VALUES(1,'unlocked_door')")
        c.execute("INSERT INTO passage_runtime_states VALUES(1,1,'door')")
        c.execute("INSERT INTO room_notes VALUES(1,'area',1,2,'Room','Secret',1)")
        for tid in ('a','b'):
            c.execute("INSERT INTO map_transitions(id,map_id,name,kind,x,y,visibility,availability) VALUES(?,1,?,'stairs',1,2,'secret','usable')",(tid,tid))
        c.execute("UPDATE map_transitions SET destination_id='b' WHERE id='a'")
        c.execute("UPDATE campaigns SET active_map_id=1 WHERE id=1")
    with db.connect() as c:
        raw = export_campaign(c,1,maps)
    return db,maps,raw

def test_roundtrip(env):
    db,maps,raw = env
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        assert b'private' not in z.read('campaign.json')
    with db.connect() as c:
        c.execute('BEGIN IMMEDIATE')
        restore_campaign(c,1,maps,raw,10**7,[])
    with db.connect() as c:
        assert c.execute('PRAGMA foreign_key_check').fetchall() == []
        assert c.execute('SELECT name FROM campaigns WHERE id=2').fetchone()[0] == 'Other'
        assert c.execute('SELECT owner_id FROM campaigns WHERE id=1').fetchone()[0] == 1
        assert c.execute('SELECT COUNT(*) FROM campaign_viewers').fetchone()[0] == 1
        assert c.execute('SELECT kind FROM door_runtime_states').fetchone()[0] == 'unlocked_door'
        assert c.execute('SELECT kind FROM passage_runtime_states').fetchone()[0] == 'door'
        assert c.execute('SELECT markdown FROM room_notes').fetchone()[0] == 'Secret'
        assert c.execute('SELECT COUNT(*) FROM map_transitions WHERE destination_id IS NOT NULL').fetchone()[0] == 1

def test_rollback(env):
    db,maps,raw = env
    out = io.BytesIO()
    with zipfile.ZipFile(io.BytesIO(raw)) as src, zipfile.ZipFile(out,'w') as dst:
        for name in src.namelist():
            body = src.read(name)
            if name == 'campaign.json':
                data = json.loads(body); data['campaign']['name'] = ''
                body = json.dumps(data).encode()
            dst.writestr(name,body)
    with pytest.raises(ValueError):
        with db.connect() as c:
            c.execute('BEGIN IMMEDIATE')
            restore_campaign(c,1,maps,out.getvalue(),10**7,[])
    with db.connect() as c:
        assert c.execute('SELECT name FROM campaigns WHERE id=1').fetchone()[0] == 'Adventure'
        assert c.execute('SELECT COUNT(*) FROM walls').fetchone()[0] == 1

def test_expanded_limit(env):
    db,maps,raw = env
    with pytest.raises(ValueError,match='Expanded'):
        with db.connect() as c:
            restore_campaign(c,1,maps,raw,1,[])


@pytest.mark.parametrize('schema,accepted',[(15,True),(16,True),(17,True),(14,False)])
def test_checkpoint_migration_backup_compatibility(env,schema,accepted):
    db,maps,raw=env
    out=io.BytesIO()
    with zipfile.ZipFile(io.BytesIO(raw)) as source,zipfile.ZipFile(out,'w') as target:
        for name in source.namelist():
            body=source.read(name)
            if name=='campaign.json':
                data=json.loads(body);data['schema']=schema
                if schema in (15,16,17):
                    data['tables'].pop('room_note_archives')
                    for row in data['tables']['maps']:
                        row.pop('room_notes_version')
                if schema in (15,16):
                    for table in ('double_reveal_maps','double_reveal_rooms','double_reveal_history'):
                        data['tables'].pop(table,None)
                body=json.dumps(data).encode()
            target.writestr(name,body)
    def apply():
        with db.connect() as c:
            c.execute('BEGIN IMMEDIATE')
            restore_campaign(c,1,maps,out.getvalue(),10**7,[])
    if accepted:apply()
    else:
        with pytest.raises(ValueError,match='schema'):apply()
