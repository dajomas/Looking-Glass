"""Read-only readiness checks against real SQLite and area geometry."""
import io
import zipfile
import pytest
from PIL import Image
from looking_glass.db import Database
from looking_glass.services.fog import FogEngine
from looking_glass.services.room_notes import area_key
from looking_glass.services.campaign_readiness import check_campaign
from looking_glass.services.campaign_backup import export_campaign

@pytest.fixture
def env(settings):
    settings.maps_dir.mkdir(parents=True,exist_ok=True)
    Image.new('RGB',(400,200)).save(settings.maps_dir/'map.png')
    db=Database(settings.data_dir / "readiness.db")
    db.migrate()
    fog=FogEngine(settings.section('fog'),settings.section('viewer'),settings.cache_dir)
    with db.connect() as c:
        c.execute("INSERT INTO campaigns(id,name) VALUES(1,'Dungeon'),(2,'Private')")
        c.execute("INSERT INTO maps(id,campaign_id,name,image_file,width,height) VALUES(1,1,'Main','map.png',400,200),(2,2,'Private map','missing.png',400,200)")
        c.execute("INSERT INTO walls(map_id,x1,y1,x2,y2) VALUES(1,200,0,200,200)")
    return db,settings.maps_dir,fog

def run(env,limit=10**8):
    db,maps,fog=env
    with db.connect() as c:
        c.execute('PRAGMA query_only=ON'); c.execute('BEGIN')
        campaign=c.execute('SELECT * FROM campaigns WHERE id=1').fetchone()
        return check_campaign(c,campaign,maps,fog,limit)

def codes(report):return {f['code'] for f in report['findings']}

def test_healthy_and_campaign_isolation(env):
    report=run(env)
    assert report['findings']==[]
    assert report['map_count']==1

def test_missing_image(env):
    (env[1]/'map.png').unlink()
    report=run(env)
    assert 'image_unreadable' in codes(report)
    assert not report['size_complete']

@pytest.mark.parametrize('kind',['corrupt','dimensions','path'])
def test_image_validation(env,kind):
    db,maps,_=env
    if kind=='corrupt': (maps/'map.png').write_bytes(b'not an image')
    if kind=='dimensions': Image.new('RGB',(10,10)).save(maps/'map.png')
    if kind=='path':
        with db.connect() as c:c.execute("UPDATE maps SET image_file='../outside.png' WHERE id=1")
    assert ('image_dimensions' if kind=='dimensions' else 'image_unreadable') in codes(run(env))

def test_no_walls_is_informational(env):
    with env[0].connect() as c:c.execute('DELETE FROM walls WHERE map_id=1')
    finding=next(f for f in run(env)['findings'] if f['code']=='no_walls')
    assert finding['severity']=='info'

def endpoint(c,tid,x=100,y=100,linked=0):
    c.execute("INSERT INTO map_transitions(id,map_id,name,kind,x,y,visibility,availability,link_defined) VALUES(?,1,?,'stairs',?,?,'secret','usable',?)",(tid,tid,x,y,linked))

def test_endpoint_bounds_broken_and_arrival_only(env):
    with env[0].connect() as c:
        endpoint(c,'broken',500,100,1);endpoint(c,'arrival')
    report=run(env)
    assert {'endpoint_bounds','destination_missing','destination_unset'}<=codes(report)
    assert all(f['url'].startswith('/campaigns/1/readiness/maps/1') for f in report['findings'])

def test_wall_arrival_and_same_map_link(env):
    with env[0].connect() as c:
        endpoint(c,'wall',200);endpoint(c,'other')
        c.execute("UPDATE map_transitions SET destination_id='other',link_defined=1 WHERE id='wall'")
    assert {'endpoint_wall','destination_same_map'}<=codes(run(env))

def test_note_geometry_and_no_changes(env):
    db,maps,fog=env
    from looking_glass.services.wall_model import Calibration
    from looking_glass.repositories.walls import list_for_map
    with db.connect() as c:
        area=fog.build_area_map(400,200,list_for_map(c,1),Calibration(),True)
        label=int(area.labels[100,100])
        key=area_key(area,label,400,200)
        c.execute("INSERT INTO room_notes VALUES(1,?,100,100,'Valid','secret',1)",(key,))
        c.execute("INSERT INTO room_notes VALUES(1,'old',100,100,'Stale','keep me',1)")
        c.execute("INSERT INTO fog_ops(map_id,op,x,y) VALUES(1,'reveal',100,100)")
        c.execute('UPDATE campaigns SET active_map_id=1 WHERE id=1')
    with db.connect() as c:before='\n'.join(c.iterdump())
    files={p.relative_to(maps):p.read_bytes() for p in maps.rglob('*') if p.is_file()}
    report=run(env)
    assert [f['code'] for f in report['findings']].count('stale_note')==1
    with db.connect() as c:assert '\n'.join(c.iterdump())==before
    assert {p.relative_to(maps):p.read_bytes() for p in maps.rglob('*') if p.is_file()}==files
    assert list(fog.cache_dir.iterdir())==[]

def test_backup_size_matches_export(env):
    report=run(env,1)
    assert 'backup_size' in codes(report)
    db,maps,_=env
    with db.connect() as c:raw=export_campaign(c,1,maps)
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        assert report['expanded_bytes']==sum(i.file_size for i in z.infolist())

def test_empty_campaign(env):
    with env[0].connect() as c:c.execute('DELETE FROM maps WHERE campaign_id=1')
    assert 'no_maps' in codes(run(env))
