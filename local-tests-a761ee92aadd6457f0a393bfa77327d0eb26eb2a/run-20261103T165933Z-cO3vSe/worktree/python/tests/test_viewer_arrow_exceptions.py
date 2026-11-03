from dataclasses import replace
from types import SimpleNamespace
import asyncio
from pathlib import Path
import pytest
from test_fog import engine, _setup
from test_passages import passage_scene, inputs, scene_walls
from test_locked_doors import route_body
from looking_glass.services.door_arrows import arrows, DoorArrow, viewer_exception_visible
from looking_glass.services.wall_model import FogOp
from looking_glass.services.passages import set_state
from looking_glass.repositories import walls as walls_repo, maps as maps_repo
from looking_glass.db import Database, MIGRATIONS


@pytest.mark.parametrize("portal", [False, True])
@pytest.mark.parametrize("secret", [False, True])
@pytest.mark.parametrize("is_portal,origin,kind", [
    (False,False,"door"),(False,True,"door"),(False,True,"secret"),
    (True,False,"door"),(True,True,"locked_door"),(True,True,"secret")])
def test_exception_union(portal,secret,is_portal,origin,kind):
    spec=SimpleNamespace(viewer_portal_arrows_enabled=portal,viewer_secret_arrows_enabled=secret)
    item=DoorArrow(1,(0,0),[],portal=is_portal,secret_origin=origin,kind=kind)
    assert viewer_exception_visible(spec,item)==(kind!="secret" and ((portal and is_portal) or (secret and origin)))
    assert not viewer_exception_visible(spec,replace(item,exit_only=True))


@pytest.mark.parametrize("portal,secret,expected",[(False,False,False),(True,False,True),(False,True,True),(True,True,True)])
def test_portal_discovery_and_rendering(engine,passage_scene,portal,secret,expected):
    db,tmp=passage_scene
    with db.connect() as c:
        walls_repo.replace(c,1,scene_walls("secret","locked_door"))
        spec,segs,ops=inputs(c,tmp)
        spec=replace(spec,door_arrows_enabled=False,viewer_door_arrows_enabled=False,arrow_audience="viewer",
                     viewer_portal_arrows_enabled=portal,viewer_secret_arrows_enabled=secret)
        assert not arrows(engine,spec,segs,ops)
        wall=next(s for s in segs if s.kind=="portal" and s.passage["end"]=="a")
        set_state(c,1,wall,1,"locked_door")
        _,segs,ops=inputs(c,tmp)
        shown=arrows(engine,spec,segs,ops)
        assert bool(shown)==expected
        assert all(a.kind!="secret" and not a.exit_only for a in shown)
        assert not arrows(engine,spec,segs,[])
        assert not arrows(engine,replace(spec,doors_block=False),segs,ops)
        assert bool(arrows(engine,replace(spec,door_arrows_enabled=True),segs,ops))


@pytest.mark.parametrize("portal,secret",[(False,False),(True,False),(False,True),(True,True)])
def test_discovered_secret_door_and_ordinary_door(engine,tmp_path,portal,secret):
    spec,segs=_setup(tmp_path,door=True)
    spec=replace(spec,door_arrows_enabled=False,viewer_door_arrows_enabled=False,arrow_audience="viewer",
                 viewer_portal_arrows_enabled=portal,viewer_secret_arrows_enabled=secret)
    ops=[FogOp("reveal",100,100)]
    assert not arrows(engine,spec,segs,ops)
    discovered=[replace(s,designed_kind="secret") if s.kind=="door" else s for s in segs]
    assert bool(arrows(engine,spec,discovered,ops))==secret
    hidden=[replace(s,kind="secret",designed_kind="secret") if s.kind=="door" else s for s in segs]
    assert not arrows(engine,spec,hidden,ops)
    assert spec.identity!=replace(spec,viewer_secret_arrows_enabled=not secret).identity


def test_migration_defaults_and_restart(tmp_path):
    db=Database(tmp_path/"old.db")
    with db.connect() as c:
        c.executescript("".join(MIGRATIONS[:10]))
        c.executescript("CREATE TABLE schema_version(version INTEGER); INSERT INTO schema_version VALUES(10);")
        c.execute("INSERT INTO campaigns(id,name) VALUES(1,'C')")
        c.execute("INSERT INTO maps(id,campaign_id,name,image_file,width,height,viewer_door_arrows_enabled) VALUES(1,1,'M','m',10,10,0)")
    assert db.migrate()==db.migrate()==len(MIGRATIONS)
    with db.connect() as c:
        row=c.execute("SELECT * FROM maps").fetchone()
        assert row["viewer_portal_arrows_enabled"]==row["viewer_secret_arrows_enabled"]==row["viewer_door_arrows_enabled"]==0


def test_api_partial_update_and_notification(tmp_path):
    db=Database(tmp_path/"db");db.migrate()
    with db.connect() as c:
        c.execute("INSERT INTO campaigns(id,name) VALUES(1,'C')")
        c.execute("INSERT INTO maps(id,campaign_id,name,image_file,width,height) VALUES(1,1,'M','m',10,10)")
    notices=[]
    async def changed(*args): notices.append(args)
    namespace=dict(map_for_manage=lambda c,u,mid:(maps_repo.get(c,mid),None),maps_repo=maps_repo,
                   notify=SimpleNamespace(map_changed=changed),_map_payload=lambda ctx,c,mid:dict(maps_repo.get(c,mid)))
    fn=route_body(Path(__file__).parents[1]/"looking_glass/web/admin/api.py","set_door_arrows",namespace)
    ctx=SimpleNamespace(db=db)
    def body(**kw):
        data=dict(color=None,locked_color=None,enabled=None,admin_enabled=None,viewer_enabled=None,
                  viewer_portal_enabled=None,viewer_secret_enabled=None)
        return SimpleNamespace(**(data|kw))
    for update in [dict(viewer_enabled=False),dict(viewer_portal_enabled=True),dict(viewer_secret_enabled=True)]:
        result=asyncio.run(fn(ctx,{},1,body(**update)))
    assert result["viewer_portal_arrows_enabled"]==result["viewer_secret_arrows_enabled"]==1
    assert result["viewer_door_arrows_enabled"]==0 and result["door_arrows_enabled"]==1
    assert len(notices)==3 and result["fog_version"]==3
    asyncio.run(fn(ctx,{},1,body(viewer_secret_enabled=True)))
    assert len(notices)==3
