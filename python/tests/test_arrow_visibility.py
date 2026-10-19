from dataclasses import replace
import asyncio
import json
from pathlib import Path
from types import SimpleNamespace
import numpy as np
import pytest
from PIL import Image
from test_fog import engine, _setup
from test_locked_doors import route_body
from looking_glass.db import Database, MIGRATIONS
from looking_glass.services.fog import MapSpec
from looking_glass.services.wall_model import FogOp
from looking_glass.services.door_arrows import target_at, arrows
from looking_glass.services.arrow_visibility import resolve_visibility
from looking_glass.repositories import maps as maps_repo


@pytest.mark.parametrize('admin',[False,True])
@pytest.mark.parametrize('viewer',[False,True])
@pytest.mark.parametrize('kind',['door','locked_door','unlocked_door'])
def test_admin_viewer_render_matrix(engine,tmp_path,admin,viewer,kind):
    spec,segs=_setup(tmp_path,door=True)
    segs=[replace(s,kind=kind) if s.kind=='door' else s for s in segs]
    spec=replace(spec,door_arrows_enabled=admin,viewer_door_arrows_enabled=viewer)
    ops=[FogOp('reveal',100,100)]
    reference=np.array(engine.door_arrow_overlay(replace(spec,door_arrows_enabled=True),segs,ops))
    arrow=reference[:,:,3]>0
    assert arrow.any()
    overlay=np.array(engine.door_arrow_overlay(spec,segs,ops))
    assert bool(overlay[:,:,3].any())==admin
    assert bool(arrows(engine,spec,segs,ops))==admin
    ys,xs=np.nonzero(arrow)
    target=target_at(engine,spec,segs,ops,xs[len(xs)//2]+.5,ys[len(ys)//2]+.5)
    assert bool(target)==(admin and kind!='locked_door')
    path=engine.viewer_image(spec,segs,ops)
    rendered=np.array(Image.open(path))
    if viewer:assert np.all(rendered[arrow]==reference[arrow,:3])
    else:assert np.all(rendered[arrow]==[250,0,0])
    assert tuple(rendered[100,300])==(0,0,0)
    assert spec.door_arrows_enabled==admin and spec.viewer_door_arrows_enabled==viewer


def test_viewer_cache_key_tracks_viewer_not_admin(engine,tmp_path):
    spec,segs=_setup(tmp_path,door=True)
    spec=replace(spec,door_arrows_enabled=True,viewer_door_arrows_enabled=True)
    ops=[FogOp('reveal',100,100)]
    first=engine.viewer_image(spec,segs,ops)
    assert engine.viewer_image(replace(spec,door_arrows_enabled=False),segs,ops)==first
    second=engine.viewer_image(replace(spec,viewer_door_arrows_enabled=False),segs,ops)
    assert second!=first


def test_migration_copies_old_shared_values_and_preserves_data(tmp_path):
    db=Database(tmp_path/'old.db')
    with db.connect() as c:
        c.executescript(''.join(MIGRATIONS[:8]))
        c.executescript('CREATE TABLE schema_version(version INTEGER); INSERT INTO schema_version VALUES(8);')
        c.execute("INSERT INTO campaigns(id,name) VALUES(1,'C')")
        for mid,enabled in [(1,0),(2,1)]:
            c.execute("INSERT INTO maps(id,campaign_id,name,image_file,width,height,door_arrows_enabled) VALUES(?,1,'M','m',400,200,?)",(mid,enabled))
        c.execute("INSERT INTO walls(id,map_id,x1,y1,x2,y2,kind,blocks) VALUES(1,1,10,10,10,90,'locked_door',1)")
        c.execute("INSERT INTO door_runtime_states(wall_id,kind) VALUES(1,'unlocked_door')")
        c.execute("INSERT INTO fog_ops(map_id,op,x,y) VALUES(1,'reveal',50,50)")
        before=[dict(r) for r in c.execute('SELECT * FROM maps ORDER BY id')]
    assert db.migrate()==db.migrate()==9
    with db.connect() as c:
        rows=c.execute('SELECT * FROM maps ORDER BY id').fetchall()
        for old,row in zip(before,rows):
            assert all(row[k]==v for k,v in old.items())
            assert row['viewer_door_arrows_enabled']==row['door_arrows_enabled']
            spec=MapSpec.from_row(row,tmp_path)
            assert spec.viewer_arrows_enabled==bool(row['viewer_door_arrows_enabled'])
        assert c.execute('SELECT kind FROM door_runtime_states').fetchone()[0]=='unlocked_door'
        assert c.execute('SELECT count(*) FROM fog_ops').fetchone()[0]==1
        c.execute("INSERT INTO maps(campaign_id,name,image_file,width,height) VALUES(1,'New','m',10,10)")
        new=c.execute('SELECT * FROM maps ORDER BY id DESC').fetchone()
        assert new['door_arrows_enabled']==new['viewer_door_arrows_enabled']==1


@pytest.mark.parametrize('patch,expected',[
    ({'admin_enabled':False},(False,True)),({'viewer_enabled':False},(True,False)),
    ({'enabled':False},(False,False)),({'enabled':False,'admin_enabled':True},(True,False)),
    ({'enabled':False,'viewer_enabled':True},(False,True)),({},(True,True))])
def test_partial_and_legacy_updates(patch,expected):
    assert resolve_visibility({'door_arrows_enabled':1,'viewer_door_arrows_enabled':1},**patch)==expected


@pytest.mark.parametrize('value',[0,1,'false',[],{}])
def test_resolver_rejects_non_boolean(value):
    with pytest.raises(ValueError):resolve_visibility({'door_arrows_enabled':1,'viewer_door_arrows_enabled':1},admin_enabled=value)


@pytest.mark.parametrize('admin,viewer',[(False,True),(True,False),(False,False),(True,True)])
def test_real_settings_handler_partial_updates(tmp_path,admin,viewer):
    db=Database(tmp_path/'db');db.migrate()
    with db.connect() as c:
        c.execute("INSERT INTO campaigns(id,name) VALUES(1,'C')")
        c.execute("INSERT INTO maps(id,campaign_id,name,image_file,width,height) VALUES(1,1,'M','m',10,10)")
    notices=[]
    async def changed(*args):notices.append(args)
    def manage(c,user,mid):
        if user['id']!=1:raise PermissionError()
        return maps_repo.get(c,mid),None
    namespace=dict(map_for_manage=manage,maps_repo=maps_repo,notify=SimpleNamespace(map_changed=changed),
        _map_payload=lambda ctx,c,mid:dict(maps_repo.get(c,mid)))
    fn=route_body(Path(__file__).parents[1]/'looking_glass/web/admin/api.py','set_door_arrows',namespace)
    ctx=SimpleNamespace(db=db)
    def body(**kw):return SimpleNamespace(color=None,locked_color=None,enabled=None,admin_enabled=None,viewer_enabled=None,**kw)
    # Build explicit updates without duplicate keyword keys.
    b=body();b.admin_enabled=admin
    asyncio.run(fn(ctx,{'id':1},1,b))
    b=body();b.viewer_enabled=viewer
    result=asyncio.run(fn(ctx,{'id':1},1,b))
    assert result['door_arrows_enabled']==admin and result['viewer_door_arrows_enabled']==viewer
    assert result['door_arrow_color']=='#46c0ff' and result['locked_door_arrow_color']=='#ff9f43'
    with pytest.raises(PermissionError):asyncio.run(fn(ctx,{'id':2},1,b))
    with db.connect() as c:
        assert c.execute('SELECT count(*) FROM fog_ops').fetchone()[0]==0
        assert c.execute('SELECT count(*) FROM door_runtime_states').fetchone()[0]==0
    assert len(notices)==int(not viewer)
    assert result["fog_version"]==int(not viewer)
