"""Room artwork, geometry, persistence, navigation and portability regressions."""
from dataclasses import replace
import io,json,sqlite3,zipfile
import pytest
from PIL import Image
from looking_glass.db import Database
from looking_glass.services import double_reveal as dr,campaign_backup as backup,duplication,session_checkpoints as cp
from looking_glass.services.fog import FogEngine,MapSpec
from looking_glass.services.wall_model import WallSegment
from looking_glass.repositories import fog_ops

@pytest.fixture
def env(settings):
    settings.maps_dir.mkdir(parents=True,exist_ok=True)
    Image.new('RGB',(100,60),(220,20,20)).save(settings.maps_dir/'original.png')
    Image.new('RGB',(100,60),(20,220,20)).save(settings.maps_dir/'alternate.png')
    db=Database(settings.database_path);db.migrate()
    engine=FogEngine(settings.section('fog'),settings.section('viewer'),settings.cache_dir)
    with db.connect() as c:
        c.execute("INSERT INTO users(id,username,password_hash,role) VALUES(1,'dm','hash','admin')")
        c.execute("INSERT INTO campaigns(id,name,owner_id) VALUES(1,'Adventure',1),(2,'Other',1)")
        for mid,cid in ((1,1),(2,1),(3,2)):
            c.execute("INSERT INTO maps(id,campaign_id,name,image_file,width,height) VALUES(?,?,?,'original.png',100,60)",(mid,cid,f'Map {mid}'))
        c.execute("INSERT INTO walls(map_id,x1,y1,x2,y2) VALUES(1,50,0,50,60)")
        c.execute("INSERT INTO double_reveal_maps(map_id,image_file) VALUES(1,'alternate.png')")
    return db,settings,engine

def inputs(env,c,mid=1):
    _,s,_=env;row=c.execute('SELECT * FROM maps WHERE id=?',(mid,)).fetchone()
    alt,rooms=dr.inputs(c,mid,s.maps_dir)
    spec=replace(MapSpec.from_row(row,s.maps_dir),alternate_image_path=alt,double_reveal_rooms=rooms,door_arrows_enabled=False,viewer_door_arrows_enabled=False)
    segs=[WallSegment(r['x1'],r['y1'],r['x2'],r['y2']) for r in c.execute('SELECT * FROM walls WHERE map_id=?',(mid,))]
    return spec,segs,fog_ops.list_for_map(c,mid)

def configure(env,c,x=20,y=30,destination=2):
    spec,segs,_=inputs(env,c)
    return dr.configure(c,spec,env[2].area_map(spec,segs),x,y,0,True,destination)

def change(env,c,key,active=True):
    spec,segs,_=inputs(env,c)
    rev=c.execute('SELECT revision FROM double_reveal_rooms WHERE map_id=1 AND area_key=?',(key,)).fetchone()[0]
    return dr.change(c,spec,env[2].area_map(spec,segs),key,rev,active)

def pixel(env,c,x):
    spec,segs,ops=inputs(env,c)
    with Image.open(env[2].viewer_image(spec,segs,ops)) as img:return img.getpixel((x,30))

def test_artwork_only_selected_room_and_fog_independent(env):
    with env[0].connect() as c:
        key=configure(env,c);fog_ops.add(c,1,'reveal_all',None,None,1)
        assert pixel(env,c,20)==(220,20,20)
        change(env,c,key)
        assert pixel(env,c,20)==(20,220,20) and pixel(env,c,80)==(220,20,20)
        fog_ops.add(c,1,'hide_all',None,None,1);env[2].invalidate(1)
        assert pixel(env,c,20)==env[2].fog_rgb
        assert c.execute('SELECT true_active FROM double_reveal_rooms').fetchone()[0]==1
        fog_ops.add(c,1,'reveal',20,30,1);env[2].invalidate(1)
        assert pixel(env,c,20)==(20,220,20) and pixel(env,c,80)==env[2].fog_rgb

def test_independent_rooms_and_undo_leave_fog_unchanged(env):
    with env[0].connect() as c:
        left=configure(env,c);right=configure(env,c,80);change(env,c,left);change(env,c,right)
        before=[tuple(r) for r in c.execute('SELECT * FROM fog_ops')]
        spec,segs,_=inputs(env,c);area=env[2].area_map(spec,segs);dr.undo(c,spec,area)
        states={r['area_key']:r['true_active'] for r in c.execute('SELECT * FROM double_reveal_rooms')}
        assert states[left]==1 and states[right]==0
        dr.undo(c,spec,area)
        assert sum(r[0] for r in c.execute('SELECT true_active FROM double_reveal_rooms'))==0
        assert before==[tuple(r) for r in c.execute('SELECT * FROM fog_ops')]
        with pytest.raises(ValueError):dr.undo(c,spec,area)

def test_changed_geometry_does_not_apply_to_merged_room(env):
    with env[0].connect() as c:
        key=configure(env,c);change(env,c,key);c.execute('DELETE FROM walls WHERE map_id=1')
        c.execute('UPDATE maps SET walls_version=walls_version+1 WHERE id=1');spec,segs,ops=inputs(env,c)
        assert not dr.listing(c,env[2],spec,segs,ops)['rooms'][0]['valid_geometry']
        with Image.open(env[1].maps_dir/'original.png') as source:
            assert dr.composite(env[2],spec,segs,source.convert('RGB')).getpixel((80,30))==(220,20,20)
        with pytest.raises(ValueError,match='geometry'):change(env,c,key,False)

def test_strict_points_scope_and_optimistic_revision(env):
    with env[0].connect() as c:
        spec,segs,_=inputs(env,c);area=env[2].area_map(spec,segs)
        for x,y in ((-1,30),(100,30),(float('nan'),0),(50,30)):
            with pytest.raises(ValueError):dr.locate(area,spec,x,y)
        for dest in (1,3):
            with pytest.raises(ValueError,match='campaign'):configure(env,c,destination=dest)
        key=configure(env,c);change(env,c,key)
        with pytest.raises(ValueError,match='changed'):dr.change(c,spec,area,key,1,False)
        with pytest.raises(sqlite3.IntegrityError):c.execute('UPDATE double_reveal_rooms SET destination_map_id=3')

def test_state_persistence_and_cache_identity(env):
    with env[0].connect() as c:
        key=configure(env,c);before=inputs(env,c)[0].identity;change(env,c,key)
        assert before!=inputs(env,c)[0].identity
    with env[0].connect() as c:assert inputs(env,c)[0].double_reveal_rooms[0][3]==1

def test_navigation_requires_true_visible_active_source_and_preserves_destination(env):
    with env[0].connect() as c:
        key=configure(env,c);c.execute('UPDATE campaigns SET active_map_id=1 WHERE id=1')
        def travel():
            spec,segs,ops=inputs(env,c);rev=c.execute('SELECT revision FROM double_reveal_rooms').fetchone()[0]
            return dr.navigate(c,env[2],spec,segs,ops,key,rev,1)
        with pytest.raises(ValueError,match='true'):travel()
        change(env,c,key)
        with pytest.raises(ValueError,match='visible'):travel()
        fog_ops.add(c,1,'reveal',20,30,1);fog_ops.add(c,2,'reveal',80,30,1)
        before=[tuple(r) for r in c.execute('SELECT * FROM fog_ops WHERE map_id=2')]
        assert travel()==(2,1)
        assert before==[tuple(r) for r in c.execute('SELECT * FROM fog_ops WHERE map_id=2')]
        with pytest.raises(ValueError,match='active'):travel()

def test_deleted_destination_detaches_link(env):
    with env[0].connect() as c:
        configure(env,c);c.execute('DELETE FROM maps WHERE id=2')
        assert c.execute('SELECT destination_map_id FROM double_reveal_rooms').fetchone()[0] is None

def test_backup_preserves_image_state_history_and_remaps_link(env):
    db,s,_=env
    with db.connect() as c:key=configure(env,c);change(env,c,key)
    with db.connect() as c:raw=backup.export_campaign(c,1,s.maps_dir)
    with db.connect() as c:
        c.execute('BEGIN IMMEDIATE');backup.restore_campaign(c,1,s.maps_dir,raw,10**7,[])
        room=c.execute('SELECT * FROM double_reveal_rooms').fetchone()
        assert room['true_active']==1 and room['destination_map_id'] is not None
        assert c.execute('SELECT campaign_id FROM maps WHERE id=?',(room['destination_map_id'],)).fetchone()[0]==1
        assert c.execute('SELECT COUNT(*) FROM double_reveal_history').fetchone()[0]==1
        alt=c.execute('SELECT image_file FROM double_reveal_maps').fetchone()[0]
        with Image.open(s.maps_dir/alt) as image:assert image.getpixel((20,30))==(20,220,20)
        assert c.execute('PRAGMA foreign_key_check').fetchall()==[]

@pytest.mark.parametrize('schema',[15,16])
def test_legacy_backup_still_restores(env,schema):
    db,s,_=env
    with db.connect() as c:raw=backup.export_campaign(c,1,s.maps_dir)
    with zipfile.ZipFile(io.BytesIO(raw)) as old:
        data=json.loads(old.read('campaign.json'));data['schema']=schema
        for name in dr.TABLES:data['tables'].pop(name)
        data['tables'].pop('room_note_archives')
        for row in data['tables']['maps']:
            row.pop('room_notes_version')
        out=io.BytesIO()
        with zipfile.ZipFile(out,'w') as new:
            for name in old.namelist():
                if name=='campaign.json':new.writestr(name,json.dumps(data))
                elif not name.startswith('alternate/'):new.writestr(name,old.read(name))
    with db.connect() as c:backup.restore_campaign(c,1,s.maps_dir,out.getvalue(),10**7,[])
    with db.connect() as c:
        assert c.execute('SELECT COUNT(*) FROM double_reveal_maps').fetchone()[0]==0
        assert c.execute('SELECT COUNT(*) FROM room_note_archives').fetchone()[0]==0
        assert c.execute('SELECT COUNT(*) FROM maps WHERE campaign_id=1').fetchone()[0]==2
        assert c.execute('PRAGMA foreign_key_check').fetchall()==[]

def test_duplicate_campaign_resets_runtime_remaps_links(env):
    db,s,_=env
    with db.connect() as c:
        key=configure(env,c);change(env,c,key);_,mapping=duplication.duplicate(c,1,s.maps_dir,[],'Copy',1)
        room=c.execute('SELECT * FROM double_reveal_rooms WHERE map_id=?',(mapping[1],)).fetchone()
        assert room['true_active']==0 and room['destination_map_id']==mapping[2]
        assert c.execute('SELECT COUNT(*) FROM double_reveal_history WHERE map_id=?',(mapping[1],)).fetchone()[0]==0
        assert c.execute('SELECT image_file FROM double_reveal_maps WHERE map_id=?',(mapping[1],)).fetchone()[0]!='alternate.png'

def test_single_map_copy_detaches_external_link(env):
    db,s,_=env
    with db.connect() as c:
        configure(env,c);_,mapping=duplication.duplicate(c,1,s.maps_dir,[],'Map copy',1,map_id=1)
        assert c.execute('SELECT destination_map_id FROM double_reveal_rooms WHERE map_id=?',(mapping[1],)).fetchone()[0] is None

def test_checkpoint_restores_appearance_and_history(env):
    db,s,_=env
    with db.connect() as c:
        key=configure(env,c);saved=cp.create(c,1,'Initial','',s.maps_dir,s.section('fog'),1);change(env,c,key)
        token=cp.preview(c,1,saved,s.maps_dir,s.section('fog'))['token']
        safety,_=cp.restore(c,1,saved,s.maps_dir,s.section('fog'),1,token)
        assert c.execute('SELECT true_active FROM double_reveal_rooms').fetchone()[0]==0
        token=cp.preview(c,1,safety,s.maps_dir,s.section('fog'))['token'];cp.restore(c,1,safety,s.maps_dir,s.section('fog'),1,token)
        assert c.execute('SELECT true_active FROM double_reveal_rooms').fetchone()[0]==1
        assert c.execute('SELECT COUNT(*) FROM double_reveal_history').fetchone()[0]==1

def test_checkpoint_rejects_changed_config_or_artwork(env):
    db,s,_=env
    with db.connect() as c:
        configure(env,c);saved=cp.create(c,1,'Saved','',s.maps_dir,s.section('fog'),1)
        c.execute('UPDATE double_reveal_rooms SET destination_map_id=NULL')
        assert cp.preview(c,1,saved,s.maps_dir,s.section('fog'))['conflicts']
        c.execute('UPDATE double_reveal_rooms SET destination_map_id=2');Image.new('RGB',(100,60),'blue').save(s.maps_dir/'alternate.png')
        assert cp.preview(c,1,saved,s.maps_dir,s.section('fog'))['conflicts']

def test_noop_and_disable_configuration(env):
    with env[0].connect() as c:
        key=configure(env,c);assert change(env,c,key,False) is False;change(env,c,key)
        spec,segs,_=inputs(env,c);rev=c.execute('SELECT revision FROM double_reveal_rooms').fetchone()[0]
        dr.configure(c,spec,env[2].area_map(spec,segs),20,30,rev,False,None)
        assert c.execute('SELECT COUNT(*) FROM double_reveal_history').fetchone()[0]==0
        assert c.execute('SELECT COUNT(*) FROM double_reveal_rooms').fetchone()[0]==0
