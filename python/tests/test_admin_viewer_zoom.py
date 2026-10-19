import ast
import asyncio
from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4
import pytest
from test_fog import engine
from test_locked_doors import scene
from looking_glass.repositories import maps as maps_repo
from looking_glass.services.viewer_area import revealed_area_bounds


@pytest.fixture
def endpoint(scene,engine):
    db,inputs,_=scene
    notices=[]
    def manage(c,user,mid):
        if user['id']!=1:raise PermissionError('not manager')
        row=maps_repo.get(c,mid)
        if row is None:raise LookupError('map missing')
        return row,c.execute('SELECT * FROM campaigns WHERE id=?',(row['campaign_id'],)).fetchone()
    async def publish(cid,data):notices.append((cid,data))
    hub=SimpleNamespace(viewer_count=lambda cid:2,publish=publish)
    ctx=SimpleNamespace(db=db,fog=engine,hub=hub)
    tree=ast.parse((Path(__file__).parents[1]/'looking_glass/web/admin/viewer_zoom.py').read_text())
    check=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='check_target')
    fn=next(n for n in tree.body if isinstance(n,ast.AsyncFunctionDef))
    assert fn.args.args[1].annotation.id=='CsrfUserDep'
    assert fn.decorator_list[0].args[0].value=='/maps/{map_id}/viewer-zoom'
    fn.decorator_list=[]
    namespace=dict(asyncio=asyncio,uuid4=uuid4,BadRequest=ValueError,map_for_manage=manage,
        fog_inputs=lambda ctx,c,mid:inputs(c),revealed_area_bounds=revealed_area_bounds)
    future=ast.ImportFrom(module='__future__',names=[ast.alias(name='annotations')],level=0)
    exec(compile(ast.fix_missing_locations(ast.Module(body=[future,check,fn],type_ignores=[])),'route','exec'),namespace)
    with db.connect() as c:
        row=maps_repo.get(c,1)
        body=SimpleNamespace(x=100.,y=100.,cache_token=row['cache_token'],walls_version=row['walls_version'],fog_version=row['fog_version'])
    return namespace['viewer_zoom'],ctx,body,notices,namespace


def snapshot(db):
    with db.connect() as c:
        return {t:[dict(r) for r in c.execute('SELECT * FROM '+t)] for t in ['maps','walls','fog_ops','door_runtime_states','map_fog_snapshots','campaigns']}


def test_broadcast_scoped_versioned_and_no_database_write(endpoint):
    fn,ctx,body,notices,_=endpoint
    before=snapshot(ctx.db)
    result=asyncio.run(fn(ctx,{'id':1},1,body))
    assert result=={'ok':True,'sent':True,'viewers':2}
    assert snapshot(ctx.db)==before and len(notices)==1
    cid,msg=notices[0]
    assert cid==1 and msg['type']=='viewer-zoom' and len(msg['command_id'])==32
    assert msg['point']=={'x':100.,'y':100.}
    assert msg['version']==f'1:{body.cache_token}-{body.walls_version}-{body.fog_version}'
    assert set(msg)=={'type','command_id','version','point'} # no hidden room/wall geometry


@pytest.mark.parametrize('mode',['hidden','outside','nonfinite','no-viewers'])
def test_no_broadcast_for_ineligible_or_disconnected(endpoint,mode):
    fn,ctx,body,notices,_=endpoint
    if mode=='hidden':body.x=300
    if mode=='outside':body.x=1000
    if mode=='nonfinite':body.x=float('nan')
    if mode=='no-viewers':ctx.hub.viewer_count=lambda cid:0
    before=snapshot(ctx.db)
    result=asyncio.run(fn(ctx,{'id':1},1,body))
    assert result['sent'] is False and notices==[] and snapshot(ctx.db)==before


@pytest.mark.parametrize('mode',['denied','stale','inactive','changed-during-lookup','revoked-during-lookup'])
def test_authorization_active_map_and_stale_guards(endpoint,mode):
    fn,ctx,body,notices,namespace=endpoint
    user={'id':2 if mode=='denied' else 1}
    if mode=='stale':body.fog_version+=1
    if mode=='inactive':
        with ctx.db.connect() as c:c.execute('UPDATE campaigns SET active_map_id=NULL')
    if mode in ('changed-during-lookup','revoked-during-lookup'):
        original=namespace['revealed_area_bounds']
        def change(*args):
            if mode=='changed-during-lookup':
                with ctx.db.connect() as c:c.execute('UPDATE maps SET fog_version=fog_version+1')
            else:
                def deny(*args):raise PermissionError('revoked')
                namespace['map_for_manage']=deny
            return original(*args)
        namespace['revealed_area_bounds']=change
    with pytest.raises((PermissionError,ValueError)):asyncio.run(fn(ctx,user,1,body))
    assert notices==[]
