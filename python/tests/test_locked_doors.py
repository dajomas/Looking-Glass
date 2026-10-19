import json
from dataclasses import replace
from types import SimpleNamespace
import numpy as np
import pytest
from PIL import Image
from test_fog import engine, _setup
from looking_glass.db import Database, MIGRATIONS
from looking_glass.repositories import walls as walls_repo, maps as maps_repo, fog_ops as fog_repo
from looking_glass.services.fog import MapSpec
from looking_glass.services.door_runtime import set_kind, reset
from looking_glass.services.door_arrows import arrows, hit_at, target_at
from looking_glass.services.door_actions import perform
from looking_glass.services.map_display import activate
from looking_glass.services.wall_type_settings import boundary_segments
from looking_glass.services.wall_model import FogOp
from looking_glass.services.uvtt_export import export_uvtt, encode_uvtt
from looking_glass.services.foundry_import import parse_wall_file


@pytest.fixture
def scene(engine,tmp_path):
    spec,segs=_setup(tmp_path,door=True)
    segs=[replace(s,kind='locked_door') if s.kind=='door' else s for s in segs]
    db=Database(tmp_path/'test.db');db.migrate()
    with db.connect() as c:
        c.execute("INSERT INTO users(id,username,password_hash,role) VALUES(1,'dm','x','admin')")
        c.execute("INSERT INTO campaigns(id,name) VALUES(1,'C')")
        c.execute("INSERT INTO maps(id,campaign_id,name,image_file,width,height,wall_offset_x,wall_offset_y,wall_scale_x,wall_scale_y) VALUES(1,1,'M','map.png',400,200,?,?,?,?)",(spec.calibration.offset_x,spec.calibration.offset_y,spec.calibration.scale_x,spec.calibration.scale_y))
        c.execute('UPDATE campaigns SET active_map_id=1')
        walls_repo.replace(c,1,segs)
        fog_repo.add(c,1,'reveal',100,100,1)
    def inputs(c):
        return MapSpec.from_row(maps_repo.get(c,1),tmp_path),walls_repo.list_for_map(c,1),fog_repo.list_for_map(c,1)
    def click(c,gesture='single',hit='arrow',mode='reveal',body=None):
        spec,segs,ops=inputs(c)
        if body is None:
            if hit=='arrow':
                pixels=np.array(engine.door_arrow_overlay(spec,segs,ops));ys,xs=np.nonzero(pixels[:,:,3]);i=len(xs)//2
                x,y=(xs[i]+.5)/engine.area_map(spec,segs).scale,(ys[i]+.5)/engine.area_map(spec,segs).scale
            else:x,y=200.,100.
            wall=next(s for s in segs if s.kind in ('locked_door','unlocked_door'))
            body=SimpleNamespace(x=x,y=y,wall_id=wall.id,gesture=gesture,hit=hit,mode=mode,tolerance=10,
                cache_token=spec.cache_token,walls_version=spec.walls_version,fog_version=spec.fog_version)
        result=perform(c,engine,spec,segs,ops,body,1)
        return result,body
    return db,inputs,click


def test_locked_single_double_unlock_and_reveal(engine,scene):
    db,inputs,click=scene
    with db.connect() as c:
        spec,segs,ops=inputs(c)
        before=engine.mask(spec,segs,ops).copy()
        (result,changed),_=click(c)
        assert result['door_action']=='none' and not changed and fog_repo.count(c,1)==1
        (result,changed),_=click(c,'double')
        assert result['door_action']=='unlock' and changed
        spec,segs,ops=inputs(c)
        assert next(s for s in segs if s.kind=='unlocked_door')
        assert next(s for s in walls_repo.list_for_map(c,1,designed=True) if s.kind=='locked_door')
        assert np.array_equal(before,engine.mask(spec,segs,ops)) and fog_repo.count(c,1)==1
        (result,changed),_=click(c)
        assert result['door_action']=='reveal' and fog_repo.count(c,1)==2
        spec,segs,ops=inputs(c)
        assert engine.mask(spec,segs,ops)[100,300]
        assert fog_repo.undo(c,1)


def test_unlocked_double_locks_without_revealing_and_stale_rejected(engine,scene):
    db,inputs,click=scene
    with db.connect() as c:
        click(c,'double')
        spec,segs,ops=inputs(c);before=engine.mask(spec,segs,ops).copy()
        (_,changed),body=click(c,'double')
        assert changed and fog_repo.count(c,1)==1
        spec,segs,ops=inputs(c)
        assert next(s for s in segs if s.kind=='locked_door')
        assert np.array_equal(before,engine.mask(spec,segs,ops))
        with pytest.raises(ValueError,match='map changed'):click(c,body=body)
        assert fog_repo.count(c,1)==1


@pytest.mark.parametrize('original',['locked_door','unlocked_door'])
@pytest.mark.parametrize('method',['fog-reset','activation-reset'])
def test_reset_restores_authored_type(scene,original,method):
    db,inputs,click=scene
    with db.connect() as c:
        wall=next(s for s in walls_repo.list_for_map(c,1) if s.kind=='locked_door')
        c.execute('UPDATE walls SET kind=? WHERE id=?',(original,wall.id))
        set_kind(c,1,wall.id,'unlocked_door' if original=='locked_door' else 'locked_door')
        if method=='fog-reset':fog_repo.add(c,1,'hide_all',None,None,1)
        else:activate(c,1,1,'reset',1)
        assert next(s for s in walls_repo.list_for_map(c,1) if s.id==wall.id).kind==original
        assert c.execute('SELECT count(*) FROM door_runtime_states').fetchone()[0]==0


def test_direct_segment_clicks_and_both_revealed(scene):
    db,inputs,click=scene
    with db.connect() as c:
        (result,changed),_=click(c,'double','wall')
        assert result['door_action']=='none' and not changed
        click(c,'double','arrow')
        fog_repo.add(c,1,'reveal_all',None,None,1)
        (result,changed),_=click(c,'double','wall')
        assert result['door_action']=='lock' and changed and fog_repo.count(c,1)==2


def test_unlocked_segment_honors_hide_mode(scene):
    db,inputs,click=scene
    with db.connect() as c:
        click(c,'double')
        (result,changed),_=click(c,'single','wall','hide')
        assert changed and result['door_action']=='hide'
        assert fog_repo.list_for_map(c,1)[-1].op=='hide'


def test_overlay_colors_and_legacy_cannot_reveal_locked(engine,scene):
    db,inputs,click=scene
    with db.connect() as c:
        spec,segs,ops=inputs(c)
        rgba=np.array(engine.door_arrow_overlay(spec,segs,ops));visible=rgba[:,:,3]>0
        assert np.all(rgba[visible,:3]==[255,159,67])
        ys,xs=np.nonzero(visible);x,y=xs[0]+.5,ys[0]+.5
        assert target_at(engine,spec,segs,ops,x,y) is None
        custom=replace(spec,locked_door_arrow_color='#ff0000')
        assert custom.identity!=spec.identity
        rgb=np.array(engine.door_arrow_overlay(custom,segs,ops))
        assert np.all(rgb[visible,:3]==[255,0,0])
        click(c,'double')
        spec,segs,ops=inputs(c)
        rgba=np.array(engine.door_arrow_overlay(spec,segs,ops));visible=rgba[:,:,3]>0
        assert np.all(rgba[visible,:3]==[70,192,255])
        viewer=np.array(Image.open(engine.viewer_image(spec,segs,ops)))
        assert np.all(viewer[visible]==[70,192,255]) and np.all(viewer[100,300]==0)


def test_runtime_does_not_change_boundary_enable_policy(engine,scene):
    db,inputs,click=scene
    with db.connect() as c:
        wall=next(s for s in walls_repo.list_for_map(c,1) if s.kind=='locked_door')
        set_kind(c,1,wall.id,'unlocked_door')
        segs=walls_repo.list_for_map(c,1)
        assert not next(s for s in boundary_segments(segs,['locked_door']) if s.id==wall.id).blocks
        assert next(s for s in boundary_segments(segs,['unlocked_door']) if s.id==wall.id).blocks


def test_export_uses_design_and_runtime_rows_cascade(scene):
    db,inputs,click=scene
    with db.connect() as c:
        click(c,'double')
        spec,segs,ops=inputs(c)
        designed=walls_repo.list_for_map(c,1,designed=True)
        exported=export_uvtt(designed,400,200,'M')
        parsed=parse_wall_file(encode_uvtt(exported),'x.uvtt')[0]
        assert any(s.kind=='locked_door' for s in parsed.segments)
        assert not any(s.kind=='unlocked_door' for s in parsed.segments)
        walls_repo.replace(c,1,designed)
        assert c.execute('SELECT count(*) FROM door_runtime_states').fetchone()[0]==0


@pytest.mark.parametrize('legacy7',[False,True])
def test_upgrade_from_rolledback_viewer_database(tmp_path,legacy7):
    db=Database(tmp_path/'old.db')
    with db.connect() as c:
        c.executescript(''.join(MIGRATIONS[:6]))
        c.executescript('CREATE TABLE schema_version(version INTEGER); INSERT INTO schema_version VALUES(6);')
        c.execute("INSERT INTO campaigns(id,name) VALUES(1,'C')")
        c.execute("INSERT INTO maps(campaign_id,name,image_file,width,height) VALUES(1,'M','m',10,10)")
        if legacy7:
            c.executescript('ALTER TABLE maps ADD COLUMN viewer_center_enabled INTEGER NOT NULL DEFAULT 1; ALTER TABLE maps ADD COLUMN viewer_fit_enabled INTEGER NOT NULL DEFAULT 1; INSERT INTO schema_version VALUES(7);')
    assert db.migrate()==db.migrate()==8
    with db.connect() as c:
        assert c.execute('SELECT locked_door_arrow_color FROM maps').fetchone()[0]=='#ff9f43'


@pytest.mark.parametrize('kind',['locked_door','unlocked_door'])
def test_new_type_uvtt_roundtrip(kind):
    from looking_glass.services.wall_model import WallSegment
    walls=[WallSegment(10,10,10,90,kind,True)]
    uvtt=export_uvtt(walls,100,100,'D')
    assert len(uvtt['portals'])==1
    assert parse_wall_file(encode_uvtt(uvtt),'x.uvtt')[0].segments==walls


def route_body(path,name,namespace):
    import ast
    source=ast.parse(path.read_text())
    fn=next(n for n in ast.walk(source) if isinstance(n,ast.AsyncFunctionDef) and n.name==name)
    assert fn.args.args[1].annotation.id=='CsrfUserDep'
    fn.decorator_list=[]
    future=ast.ImportFrom(module='__future__',names=[ast.alias(name='annotations')],level=0)
    exec(compile(ast.fix_missing_locations(ast.Module(body=[future,fn],type_ignores=[])),str(path),'exec'),namespace)
    return namespace[name]


def test_locked_arrow_preference_save_preserves_other_settings(scene):
    import asyncio
    from pathlib import Path
    db,inputs,click=scene
    def manage(c,user,mid):return maps_repo.get(c,mid),None
    async def changed(*args):pass
    namespace=dict(map_for_manage=manage,maps_repo=maps_repo,notify=SimpleNamespace(map_changed=changed),
                   _map_payload=lambda ctx,c,mid:dict(maps_repo.get(c,mid)))
    fn=route_body(Path(__file__).parents[1]/'looking_glass/web/admin/api.py','set_door_arrows',namespace)
    result=asyncio.run(fn(SimpleNamespace(db=db),{'id':1},1,SimpleNamespace(color=None,enabled=None,locked_color='#FF0000')))
    assert result['locked_door_arrow_color']=='#ff0000'
    assert result['door_arrow_color']=='#46c0ff' and result['door_arrows_enabled']==1
    with db.connect() as c:assert fog_repo.count(c,1)==1


def test_door_route_authorizes_before_mutation_and_notifies(scene,engine):
    import asyncio
    from pathlib import Path
    db,inputs,click=scene
    with db.connect() as c:
        spec,segs,ops=inputs(c)
        rgba=np.array(engine.door_arrow_overlay(spec,segs,ops));ys,xs=np.nonzero(rgba[:,:,3]);i=len(xs)//2
        wall=next(s for s in segs if s.kind=='locked_door')
        body=SimpleNamespace(x=xs[i]+.5,y=ys[i]+.5,wall_id=wall.id,gesture='double',hit='arrow',mode='reveal',tolerance=10,
            cache_token=spec.cache_token,walls_version=spec.walls_version,fog_version=spec.fog_version)
    notices=[]
    async def changed(*args):notices.append(args)
    def manage(c,user,mid):
        if user['id']!=1:raise PermissionError('not manager')
        return maps_repo.get(c,mid),None
    namespace=dict(map_for_manage=manage,fog_inputs=lambda ctx,c,mid:inputs(c),perform=perform,
        BadRequest=ValueError,map_payload=lambda ctx,c,mid:dict(maps_repo.get(c,mid)),notify=SimpleNamespace(map_changed=changed))
    fn=route_body(Path(__file__).parents[1]/'looking_glass/web/admin/door_states.py','door_action',namespace)
    ctx=SimpleNamespace(db=db,fog=engine)
    with pytest.raises(PermissionError):asyncio.run(fn(ctx,{'id':2},1,body))
    assert notices==[]
    result=asyncio.run(fn(ctx,{'id':1},1,body))
    assert result['door_action']=='unlock' and len(notices)==1
    with pytest.raises(ValueError):asyncio.run(fn(ctx,{'id':1},1,body))
    with db.connect() as c:assert fog_repo.count(c,1)==1


@pytest.mark.parametrize('kind',['locked_door','unlocked_door'])
def test_managed_doors_honor_global_split_setting(engine,tmp_path,kind):
    spec,segs=_setup(tmp_path,door=True,doors_block=False)
    segs=[replace(s,kind=kind) if s.kind=='door' else s for s in segs]
    assert engine.mask(spec,segs,[FogOp('reveal',100,100)])[100,300]
    assert arrows(engine,spec,segs,[FogOp('reveal',100,100)])==[]


def test_no_viewer_feature_is_reintroduced(tmp_path):
    from pathlib import Path
    db=Database(tmp_path/'fresh');db.migrate()
    with db.connect() as c:
        columns={r['name'] for r in c.execute('PRAGMA table_info(maps)')}
    assert 'viewer_center_enabled' not in columns and 'viewer_fit_enabled' not in columns
    template=(Path(__file__).parents[2]/'web_html/admin/map_editor.html').read_text()
    assert 'viewer-center-enabled' not in template and 'viewer-fit-enabled' not in template
