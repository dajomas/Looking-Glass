import ast
import asyncio
import math
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace
import numpy as np
import pytest
from test_fog import engine, _setup
from looking_glass.services.viewer_area import revealed_area_bounds
from looking_glass.services.wall_model import FogOp, Calibration
from looking_glass.db import Database
from looking_glass.repositories import maps as maps_repo


@pytest.mark.parametrize('x',[100,300])
def test_only_clicked_revealed_room_bounds(engine,tmp_path,x):
    spec,segs=_setup(tmp_path,door=True)
    ops=[FogOp('reveal',100,100),FogOp('reveal',300,100)]
    b=revealed_area_bounds(engine,spec,segs,ops,x,100)
    assert set(b)=={'x','y','width','height'}
    assert b['x']<x<b['x']+b['width'] and b['y']<100<b['y']+b['height']
    assert b['width']<210
    assert (b['x']<100) if x==100 else (b['x']>180)


@pytest.mark.parametrize('x,y',[(300,100),(0,0),(-1,100),(400,100),(100,200),(float('nan'),100),(float('inf'),100)])
def test_hidden_and_invalid_points_return_no_geometry(engine,tmp_path,x,y):
    spec,segs=_setup(tmp_path,door=True)
    assert revealed_area_bounds(engine,spec,segs,[FogOp('reveal',100,100)],x,y) is None


def test_hidden_near_wall_dilation_does_not_expose_room(engine,tmp_path):
    spec,segs=_setup(tmp_path,door=True)
    ops=[FogOp('reveal',100,100)]
    area=engine.area_map(spec,segs);mask=engine.mask(spec,segs,ops)
    labels=engine.revealed_labels(area,ops)
    for x in range(200,210):
        if area.labels[100,x] and area.labels[100,x] not in labels:
            assert revealed_area_bounds(engine,spec,segs,ops,x+.5,100.5) is None


def test_hidden_reset_and_no_writes(engine,tmp_path):
    spec,segs=_setup(tmp_path,door=True)
    assert revealed_area_bounds(engine,spec,segs,[],100,100) is None
    ops=[FogOp('reveal',100,100),FogOp('hide_all')]
    assert revealed_area_bounds(engine,spec,segs,ops,100,100) is None
    assert len(ops)==2 and spec.fog_version==1


def test_scaled_calibrated_geometry(engine,tmp_path):
    spec,segs=_setup(tmp_path,door=True)
    shifted=[]
    for s in segs:
        x1,y1=spec.calibration.apply(s.x1,s.y1);x2,y2=spec.calibration.apply(s.x2,s.y2)
        shifted.append(replace(s,x1=x1*2+20,x2=x2*2+20,y1=y1*2+30,y2=y2*2+30))
    spec=replace(spec,calibration=Calibration(20,30,.5,.5))
    engine.work_max_dim=197
    b=revealed_area_bounds(engine,spec,shifted,[FogOp('reveal',100,100)],100,100)
    assert b and b['width']<220 and b['x']+b['width']<220


@pytest.fixture
def endpoint(engine,tmp_path):
    spec,segs=_setup(tmp_path,door=True)
    db=Database(tmp_path/'test.db');db.migrate()
    with db.connect() as c:
        c.execute("INSERT INTO campaigns(id,name) VALUES(1,'C')")
        c.execute("INSERT INTO maps(id,campaign_id,name,image_file,width,height) VALUES(1,1,'M','m',400,200)")
        c.execute('UPDATE campaigns SET active_map_id=1')
    ops=[FogOp('reveal',100,100)]
    ctx=SimpleNamespace(db=db,fog=engine)
    def authorize(c,user,cid):
        if user['id']!=1:raise PermissionError()
        return c.execute('SELECT * FROM campaigns WHERE id=?',(cid,)).fetchone()
    version=lambda m:f"{m['id']}:{m['cache_token']}-{m['walls_version']}-{m['fog_version']}"
    with db.connect() as c:v=version(maps_repo.get(c,1))
    async_fn=next(n for n in ast.parse((Path(__file__).parents[1]/'looking_glass/web/viewer/api.py').read_text()).body
                  if isinstance(n,ast.AsyncFunctionDef) and n.name=='area_bounds')
    assert async_fn.args.args[1].annotation.id=='UserDep'
    assert async_fn.decorator_list[0].args[0].value=='/api/c/{campaign_id}/area-bounds'
    async_fn.decorator_list=[]
    namespace=dict(asyncio=asyncio,campaign_for_view=authorize,maps_repo=maps_repo,_version=version,
                   fog_inputs=lambda ctx,c,mid:(spec,segs,ops),revealed_area_bounds=revealed_area_bounds,
                   BadRequest=ValueError,NotFound=LookupError,JSONResponse=lambda data,headers:(data,headers))
    future=ast.ImportFrom(module='__future__',names=[ast.alias(name='annotations')],level=0)
    exec(compile(ast.fix_missing_locations(ast.Module(body=[future,async_fn],type_ignores=[])),'route','exec'),namespace)
    return namespace['area_bounds'],ctx,v,namespace


def test_authorized_read_only_endpoint(endpoint):
    fn,ctx,v,_=endpoint
    result,headers=asyncio.run(fn(ctx,{'id':1},1,100,100,v))
    assert set(result)=={'ok','version','bounds'} and result['bounds']
    assert headers['Cache-Control']=='no-store'
    hidden,_=asyncio.run(fn(ctx,{'id':1},1,300,100,v));assert hidden['bounds'] is None
    with ctx.db.connect() as c:
        assert c.execute('SELECT count(*) FROM fog_ops').fetchone()[0]==0
        assert maps_repo.get(c,1)['fog_version']==0


@pytest.mark.parametrize('mode',['denied','stale','blank','changed-during-lookup'])
def test_endpoint_rejects_invalid_context(endpoint,mode):
    fn,ctx,v,namespace=endpoint
    user={'id':2 if mode=='denied' else 1}
    if mode=='stale':v='old'
    if mode=='blank':
        with ctx.db.connect() as c:c.execute('UPDATE campaigns SET active_map_id=NULL')
    if mode=='changed-during-lookup':
        original=namespace['revealed_area_bounds']
        def changed(*args):
            with ctx.db.connect() as c:c.execute('UPDATE maps SET fog_version=fog_version+1')
            return original(*args)
        namespace['revealed_area_bounds']=changed
    with pytest.raises((PermissionError,ValueError,LookupError)):asyncio.run(fn(ctx,user,1,100,100,v))
