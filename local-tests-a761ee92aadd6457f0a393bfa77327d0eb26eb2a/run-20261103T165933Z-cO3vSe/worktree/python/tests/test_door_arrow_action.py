"""Execute the real action body with SQLite and test dependencies (not HTTP tests)."""
import ast
import asyncio
import json
from pathlib import Path
from types import SimpleNamespace
from dataclasses import replace
import pytest
from test_fog import engine, _setup
from test_door_arrows import pick
from looking_glass.db import Database
from looking_glass.repositories import fog_ops as fog_repo, maps as maps_repo
from looking_glass.services.fog import MapSpec
from looking_glass.services.map_display import checkpoint_if_active


class BadRequest(Exception):
    pass


@pytest.fixture
def action(engine,tmp_path):
    spec,segs=_setup(tmp_path,door=True)
    db=Database(tmp_path/"db.sqlite");db.migrate()
    with db.connect() as c:
        c.execute("INSERT INTO users(id,username,password_hash,role) VALUES(1,'dm','test','admin')")
        c.execute("INSERT INTO campaigns(id,name) VALUES(1,'C')")
        c.execute("INSERT INTO maps(id,campaign_id,name,image_file,width,height,wall_offset_x,wall_offset_y,wall_scale_x,wall_scale_y,walls_version,fog_version) VALUES(1,1,'M','map.png',400,200,?,?,?,?,1,1)",
                  (spec.calibration.offset_x,spec.calibration.offset_y,spec.calibration.scale_x,spec.calibration.scale_y))
        c.execute("UPDATE campaigns SET active_map_id=1")
        fog_repo.add(c,1,'reveal',100,100,1)
        m=maps_repo.get(c,1)
        spec=MapSpec.from_row(m,tmp_path)
        ops=fog_repo.list_for_map(c,1)
        point=pick(engine,spec,segs,ops)
        body=SimpleNamespace(x=point[0],y=point[1],cache_token=m['cache_token'],walls_version=1,fog_version=1)
    ctx=SimpleNamespace(db=db,fog=engine)
    notices=[]
    async def changed(*args):notices.append(args)
    def manage(c,user,mid):
        if user['id']!=1:raise PermissionError('not manager')
        return maps_repo.get(c,mid),None
    def inputs(ctx,c,mid):
        return MapSpec.from_row(maps_repo.get(c,mid),tmp_path),segs,fog_repo.list_for_map(c,mid)
    namespace=dict(__package__='looking_glass.web.admin',BadRequest=BadRequest,
        map_for_manage=manage,fog_inputs=inputs,fog_repo=fog_repo,maps_repo=maps_repo,
        checkpoint_if_active=checkpoint_if_active,notify=SimpleNamespace(map_changed=changed),
        _map_payload=lambda ctx,c,mid:dict(maps_repo.get(c,mid)))
    path=Path(__file__).parents[1]/'looking_glass/web/admin/api.py'
    tree=ast.parse(path.read_text())
    fn=next(n for n in tree.body if isinstance(n,ast.AsyncFunctionDef) and n.name=='reveal_door_arrow')
    assert any(isinstance(d,ast.Call) and d.args[0].value=='/maps/{map_id}/door-arrows/reveal' for d in fn.decorator_list)
    assert fn.args.args[1].annotation.id=='CsrfUserDep'
    fn.decorator_list=[]
    module=ast.Module(body=[ast.ImportFrom(module='__future__',names=[ast.alias(name='annotations')],level=0),fn],type_ignores=[])
    exec(compile(ast.fix_missing_locations(module),str(path),'exec'),namespace)
    return namespace['reveal_door_arrow'],ctx,body,notices


def test_action_reveal_checkpoint_notify_and_undo(action):
    fn,ctx,body,notices=action
    result=asyncio.run(fn(ctx,{'id':1},1,body))
    assert result['fog_version']==2 and result['area_fraction']>0
    with ctx.db.connect() as c:
        ops=fog_repo.list_for_map(c,1)
        assert len(ops)==2 and ops[-1].op=='reveal' and ops[-1].x>200
        snapshot=json.loads(c.execute('SELECT operations FROM map_fog_snapshots').fetchone()[0])
        assert len(snapshot)==2
        assert fog_repo.undo(c,1)
        assert fog_repo.count(c,1)==1
    assert len(notices)==1


@pytest.mark.parametrize('mutation', ['duplicate','incarnation','walls','disabled','non-arrow','permission'])
def test_rejected_click_never_writes(action,mutation):
    fn,ctx,body,notices=action
    user={'id':1}
    if mutation=='duplicate':
        asyncio.run(fn(ctx,user,1,body));expected=2
    else:
        expected=1
        if mutation=='incarnation':body.cache_token='stale'
        elif mutation=='walls':body.walls_version+=1
        elif mutation=='non-arrow':body.x=100;body.y=100
        elif mutation=='permission':user={'id':2}
        elif mutation=='disabled':
            with ctx.db.connect() as c:c.execute('UPDATE maps SET door_arrows_enabled=0')
    with pytest.raises((BadRequest,PermissionError)):
        asyncio.run(fn(ctx,user,1,body))
    with ctx.db.connect() as c:
        assert fog_repo.count(c,1)==expected
        assert maps_repo.get(c,1)['fog_version']==expected
    assert len(notices)==(expected-1)
