"""Real SQLite play-state restore, conflict, rollback and migration regressions."""
import json
import sqlite3
import pytest
from PIL import Image
from looking_glass.db import Database,MIGRATIONS
from looking_glass.services import session_checkpoints as cp

@pytest.fixture
def env(settings):
    settings.maps_dir.mkdir(parents=True,exist_ok=True)
    for name in ('one.png','two.png','other.png'):Image.new('RGB',(40,30)).save(settings.maps_dir/name)
    db=Database(settings.database_path);db.migrate()
    with db.connect() as c:
        c.execute("INSERT INTO users(id,username,password_hash,role) VALUES(1,'dm','hash','admin'),(2,'viewer','hash','viewer')")
        c.execute("INSERT INTO campaigns(id,name,owner_id) VALUES(1,'Adventure',1),(2,'Other',1)")
        c.execute("INSERT INTO campaign_viewers(campaign_id,user_id) VALUES(1,2)")
        for mid,cid,name in ((1,1,'one.png'),(2,1,'two.png'),(3,2,'other.png')):
            c.execute("INSERT INTO maps(id,campaign_id,name,image_file,width,height) VALUES(?,?,?, ?,40,30)",(mid,cid,name,name))
            c.execute("INSERT INTO walls(id,map_id,x1,y1,x2,y2,kind) VALUES(?,?,0,0,10,0,'locked_door')",(mid,mid))
        for tid,mid in (('a',1),('b',2)):
            c.execute("INSERT INTO map_transitions(id,map_id,name,kind,x,y,visibility,availability) VALUES(?,?,'Stairs','stairs',5,5,'secret','usable')",(tid,mid))
        c.execute("UPDATE map_transitions SET destination_id='b',link_defined=1 WHERE id='a'")
        c.execute("INSERT INTO fog_ops(map_id,op) VALUES(1,'hide_all')")
        c.execute("INSERT INTO fog_ops(map_id,op,x,y) VALUES(1,'reveal',5,5)")
        c.execute("INSERT INTO door_runtime_states VALUES(1,'unlocked_door')")
        c.execute("INSERT INTO passage_runtime_states VALUES(1,1,'door')")
        c.execute("UPDATE map_transitions SET runtime_visibility='discovered',runtime_availability='approval' WHERE id='a'")
        c.execute("INSERT INTO map_fog_snapshots(map_id,operations) VALUES(1,?)",(json.dumps([dict(op='reveal',x=2,y=3)]),))
        c.execute("INSERT INTO room_notes VALUES(1,'key',5,5,'Room','Authored notes',1)")
        c.execute("UPDATE campaigns SET active_map_id=1 WHERE id=1")
    return db,settings

def save(env,name='Before session'):
    db,s=env
    with db.connect() as c:
        c.execute('BEGIN IMMEDIATE')
        return cp.create(c,1,name,'note',s.maps_dir,s.section('fog'),1)

def view(env,checkpoint):
    db,s=env
    with db.connect() as c:
        c.execute('PRAGMA query_only=ON');c.execute('BEGIN')
        return cp.preview(c,1,checkpoint,s.maps_dir,s.section('fog'))

def restore(env,checkpoint,token=None):
    db,s=env
    token=token if token is not None else view(env,checkpoint)['token']
    with db.connect() as c:
        c.execute('BEGIN IMMEDIATE')
        return cp.restore(c,1,checkpoint,s.maps_dir,s.section('fog'),1,token)

def mutate(env):
    with env[0].connect() as c:
        c.execute('DELETE FROM fog_ops WHERE map_id IN (1,2)')
        c.execute("INSERT INTO fog_ops(map_id,op) VALUES(1,'hide_all')")
        c.execute("UPDATE map_transitions SET runtime_visibility='admin',revision=revision+1 WHERE id='a'")
        c.execute('DELETE FROM map_fog_snapshots WHERE map_id=1')
        c.execute('UPDATE campaigns SET active_map_id=2 WHERE id=1')
        c.execute("INSERT INTO map_transition_travel VALUES(1,1,'request','{}','{}')")

def test_create_and_preview_do_not_change_play_state(env):
    db,s=env
    with db.connect() as c:before=cp.capture(c,1,s.maps_dir,s.section('fog'))
    cid=save(env)
    with db.connect() as c:after=cp.capture(c,1,s.maps_dir,s.section('fog'))
    assert before==after and view(env,cid)['conflicts']==[]
    assert list(s.cache_dir.glob('*'))==[]

def test_roundtrip_and_safety_checkpoint(env):
    cid=save(env);mutate(env)
    with env[0].connect() as c:
        before_other=[tuple(r) for r in c.execute('SELECT * FROM maps WHERE campaign_id=2')]
        old_versions=c.execute('SELECT fog_version,walls_version FROM maps WHERE id=1').fetchone()
    safety,mids=restore(env,cid)
    assert mids==[1,2]
    with env[0].connect() as c:
        assert c.execute('SELECT active_map_id FROM campaigns WHERE id=1').fetchone()[0]==1
        assert c.execute('SELECT COUNT(*) FROM fog_ops WHERE map_id=1').fetchone()[0]==2
        assert c.execute('SELECT kind FROM door_runtime_states WHERE wall_id=1').fetchone()[0]=='unlocked_door'
        assert c.execute('SELECT kind FROM passage_runtime_states WHERE wall_id=1').fetchone()[0]=='door'
        assert c.execute("SELECT runtime_visibility FROM map_transitions WHERE id='a'").fetchone()[0]=='discovered'
        assert json.loads(c.execute('SELECT operations FROM map_fog_snapshots WHERE map_id=1').fetchone()[0])[0]['x']==2
        assert c.execute('SELECT COUNT(*) FROM map_transition_travel WHERE campaign_id=1').fetchone()[0]==0
        assert c.execute('SELECT automatic FROM campaign_checkpoints WHERE id=?',(safety,)).fetchone()[0]==1
        new_versions=c.execute('SELECT fog_version,walls_version FROM maps WHERE id=1').fetchone()
        assert all(new>old for new,old in zip(new_versions,old_versions))
        assert [tuple(r) for r in c.execute('SELECT * FROM maps WHERE campaign_id=2')]==before_other
        assert c.execute('PRAGMA foreign_key_check').fetchall()==[]
    restore(env,safety)
    with env[0].connect() as c:assert c.execute('SELECT active_map_id FROM campaigns WHERE id=1').fetchone()[0]==2

def test_authored_content_and_access_preserved(env):
    cid=save(env);mutate(env)
    with env[0].connect() as c:
        c.execute("UPDATE maps SET name='Renamed',door_arrow_color='#123456' WHERE id=1")
        c.execute("UPDATE room_notes SET markdown='New notes' WHERE map_id=1")
        c.execute("UPDATE map_transitions SET name='Renamed stairs',notes='New authored note' WHERE id='a'")
    assert not view(env,cid)['conflicts']
    restore(env,cid)
    with env[0].connect() as c:
        assert c.execute('SELECT markdown FROM room_notes').fetchone()[0]=='New notes'
        assert c.execute('SELECT name,door_arrow_color FROM maps WHERE id=1').fetchone()[:]==('Renamed','#123456')
        assert c.execute('SELECT owner_id FROM campaigns WHERE id=1').fetchone()[0]==1
        assert c.execute('SELECT user_id FROM campaign_viewers WHERE campaign_id=1').fetchone()[0]==2
        assert c.execute("SELECT notes FROM map_transitions WHERE id='a'").fetchone()[0]=='New authored note'

@pytest.mark.parametrize('sql',[
 "UPDATE walls SET x2=20 WHERE id=1",
 "UPDATE maps SET wall_scale_x=2 WHERE id=1",
 "UPDATE maps SET cache_token='new' WHERE id=1",
 "INSERT INTO map_wall_type_settings VALUES(1,'[\"wall\"]')",
 "UPDATE map_transitions SET arrival='preserve' WHERE id='a'",
 "DELETE FROM maps WHERE id=2"])
def test_incompatible_structure_is_blocked_without_safety_write(env,sql):
    cid=save(env)
    with env[0].connect() as c:c.execute(sql)
    assert view(env,cid)['conflicts']
    with pytest.raises(ValueError,match='incompatible'):restore(env,cid)
    with env[0].connect() as c:assert c.execute('SELECT COUNT(*) FROM campaign_checkpoints').fetchone()[0]==1

def test_image_content_and_config_conflicts(env):
    cid=save(env)
    Image.new('RGB',(40,30),'red').save(env[1].maps_dir/'one.png')
    assert view(env,cid)['conflicts']
    env[1].section('fog')['wall_thickness']+=1
    assert any('configuration' in p for p in view(env,cid)['conflicts'])

def test_stale_and_duplicate_restore_tokens(env):
    cid=save(env);token=view(env,cid)['token'];mutate(env)
    with pytest.raises(ValueError,match='after preview'):restore(env,cid,token)
    token=view(env,cid)['token'];restore(env,cid,token)
    with pytest.raises(ValueError,match='after preview'):restore(env,cid,token)

def test_invalid_runtime_reference_rolls_back_safety_and_changes(env):
    cid=save(env);mutate(env)
    with env[0].connect() as c:
        data=json.loads(c.execute('SELECT payload FROM campaign_checkpoints WHERE id=?',(cid,)).fetchone()[0])
        data['maps'][0]['doors'][0]['wall_id']=3
        c.execute('UPDATE campaign_checkpoints SET payload=? WHERE id=?',(json.dumps(data),cid))
        before='\n'.join(c.iterdump())
    with pytest.raises(ValueError,match='different map'):restore(env,cid)
    with env[0].connect() as c:assert '\n'.join(c.iterdump())==before

def test_corrupt_payload_and_size_limit(env,monkeypatch):
    cid=save(env)
    with env[0].connect() as c:c.execute("UPDATE campaign_checkpoints SET payload='bad json' WHERE id=?",(cid,))
    with pytest.raises(ValueError):view(env,cid)
    monkeypatch.setattr(cp,'MAX_BYTES',1)
    with pytest.raises(ValueError,match='limit'):save(env)

def test_scope_and_campaign_delete(env):
    cid=save(env)
    with env[0].connect() as c:
        with pytest.raises(LookupError):cp.get(c,2,cid)
        c.execute('DELETE FROM campaigns WHERE id=1')
        assert c.execute('SELECT COUNT(*) FROM campaign_checkpoints').fetchone()[0]==0

def test_migration_from_previous_schema(tmp_path):
    path=tmp_path/'old.db';c=sqlite3.connect(path)
    c.execute('CREATE TABLE schema_version(version INTEGER NOT NULL)')
    for i,script in enumerate(MIGRATIONS[:-1],1):
        c.executescript(script);c.execute('INSERT INTO schema_version VALUES(?)',(i,));c.commit()
    c.close();db=Database(path)
    assert db.migrate()==16
    with db.connect() as c:assert c.execute('SELECT COUNT(*) FROM campaign_checkpoints').fetchone()[0]==0


def test_blank_active_map_and_absent_snapshot(env):
    with env[0].connect() as c:
        c.execute('UPDATE campaigns SET active_map_id=NULL WHERE id=1')
        c.execute('DELETE FROM map_fog_snapshots WHERE map_id=1')
    cid=save(env);mutate(env);restore(env,cid)
    with env[0].connect() as c:
        assert c.execute('SELECT active_map_id FROM campaigns WHERE id=1').fetchone()[0] is None
        assert c.execute('SELECT COUNT(*) FROM map_fog_snapshots WHERE map_id=1').fetchone()[0]==0


def test_empty_campaign_restore_token_is_single_state_generation(env):
    with env[0].connect() as c:c.execute('DELETE FROM maps WHERE campaign_id=1')
    cid=save(env);token=view(env,cid)['token'];restore(env,cid,token)
    with pytest.raises(ValueError,match='after preview'):restore(env,cid,token)


def test_database_failure_rolls_back_safety_and_partial_restore(env):
    cid=save(env);mutate(env)
    with env[0].connect() as c:
        c.executescript("CREATE TRIGGER fail_checkpoint_restore BEFORE INSERT ON door_runtime_states BEGIN SELECT RAISE(ABORT,'test failure'); END;")
        before='\n'.join(c.iterdump())
    with pytest.raises(sqlite3.IntegrityError):restore(env,cid)
    with env[0].connect() as c:assert '\n'.join(c.iterdump())==before


def test_corrupt_fog_data_and_missing_images_block_capture(env):
    with env[0].connect() as c:
        c.execute("UPDATE map_fog_snapshots SET operations='[{}]' WHERE map_id=1")
    with pytest.raises(ValueError):save(env)
    (env[1].maps_dir/'one.png').unlink()
    with pytest.raises(OSError):save(env)
