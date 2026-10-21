"""Routing, discovery, lock/reset, viewer secrecy and interchange contracts."""
from dataclasses import replace
from types import SimpleNamespace
import numpy as np
import pytest
from PIL import Image,ImageDraw
from test_fog import engine
from looking_glass.db import Database,MIGRATIONS
from looking_glass.repositories import walls as walls_repo,maps as maps_repo,fog_ops
from looking_glass.services.wall_model import WallSegment,FogOp
from looking_glass.services.fog import MapSpec
from looking_glass.services.passages import validate_passages,set_state
from looking_glass.services.door_actions import perform
from looking_glass.services.door_arrows import arrows,hit_at,target_at,overlay
from looking_glass.services.door_runtime import reset
from looking_glass.services.uvtt_export import rows_for,validate_segments,export_uvtt,encode_uvtt
from looking_glass.services.foundry_import import parse_wall_file,WallImportError


def pair(kind="door",after="door"):
    return [WallSegment(200,70,200,130,"portal",True,passage={"pair":"p1","end":"a","sides":[{"role":"none"},{"role":"entry","kind":kind,"after":after,"exit":0}]}),
            WallSegment(400,70,400,130,"portal",True,passage={"pair":"p1","end":"b","sides":[{"role":"exit"},{"role":"none"}]})]


def scene_walls(kind="door",after="door"):
    return [WallSegment(10,10,590,10),WallSegment(590,10,590,190),WallSegment(590,190,10,190),WallSegment(10,190,10,10),
            *[WallSegment(x,y1,x,y2) for x in (200,400) for y1,y2 in ((10,70),(130,190))],*pair(kind,after)]


@pytest.fixture
def passage_scene(tmp_path,engine):
    db=Database(tmp_path/"passages.db");db.migrate()
    Image.new("RGB",(600,200),"white").save(tmp_path/"map.png")
    with db.connect() as c:
        c.execute("INSERT INTO users(id,username,password_hash,role) VALUES(1,'dm','x','admin')")
        c.execute("INSERT INTO campaigns(id,name) VALUES(1,'C')")
        c.execute("INSERT INTO maps(id,campaign_id,name,image_file,width,height) VALUES(1,1,'M','map.png',600,200)")
        c.execute("UPDATE campaigns SET active_map_id=1")
        walls_repo.replace(c,1,scene_walls());fog_ops.add(c,1,"reveal",100,100,1)
    return db,tmp_path


def inputs(c,tmp):
    return MapSpec.from_row(maps_repo.get(c,1),tmp),walls_repo.list_for_map(c,1),fog_ops.list_for_map(c,1)


def click(engine,c,tmp,side=None,gesture="single",body=None):
    spec,segs,ops=inputs(c,tmp)
    if body is None:
        item=next(a for a in arrows(engine,spec,segs,ops) if not a.exit_only and (side is None or a.side==side))
        area=engine.area_map(spec,segs)
        im=Image.new("L",(area.shape[1],area.shape[0]));ImageDraw.Draw(im).polygon(item.polygon,fill=255)
        yy,xx=np.nonzero(np.array(im))
        point=next(((x+.5)/area.scale,(y+.5)/area.scale) for x,y in zip(xx,yy) if (h:=hit_at(engine,spec,segs,ops,(x+.5)/area.scale,(y+.5)/area.scale)) and h.wall_id==item.wall_id and h.side==item.side)
        body=SimpleNamespace(x=point[0],y=point[1],wall_id=item.wall_id,side=item.side,gesture=gesture,hit="arrow",mode="reveal",tolerance=10,
                             cache_token=spec.cache_token,walls_version=spec.walls_version,fog_version=spec.fog_version)
    return perform(c,engine,spec,segs,ops,body,1),body


def test_remote_exit_not_adjacent_and_repeat_noop(engine,passage_scene):
    db,tmp=passage_scene
    with db.connect() as c:
        (result,changed),old=click(engine,c,tmp)
        assert changed and result["door_action"]=="reveal"
        spec,segs,ops=inputs(c,tmp);area=engine.area_map(spec,segs);shown=engine.revealed_labels(area,ops)
        assert engine.label_at(area,500,100) in shown
        assert engine.label_at(area,300,100) not in shown
        assert len([a for a in arrows(engine,spec,segs,ops) if not a.exit_only])==1
        count=fog_ops.count(c,1);(result,changed),_=click(engine,c,tmp)
        assert not changed and result["door_action"]=="none" and fog_ops.count(c,1)==count
        with pytest.raises(ValueError,match="map changed"):click(engine,c,tmp,body=old)
        assert fog_ops.undo(c,1)


def test_secret_portal_discovery_unlock_and_viewer_secrecy(engine,passage_scene):
    db,tmp=passage_scene
    with db.connect() as c:
        walls_repo.replace(c,1,scene_walls("secret","locked_door"))
        maps_repo.bump_fog(c,1);c.execute("UPDATE maps SET walls_version=walls_version+1 WHERE id=1")
        spec,segs,ops=inputs(c,tmp)
        assert not arrows(engine,replace(spec,arrow_audience="viewer"),segs,ops)
        assert any(a.kind=="secret" for a in arrows(engine,spec,segs,ops))
        (info,changed),_=click(engine,c,tmp)
        assert not changed and info["door_action"]=="none"
        before=engine.mask(spec,segs,ops).copy()
        (info,changed),_=click(engine,c,tmp,gesture="double")
        assert changed and info["door_action"]=="discover"
        spec,segs,ops=inputs(c,tmp)
        assert np.array_equal(before,engine.mask(spec,segs,ops)) and fog_ops.count(c,1)==1
        view=np.array(overlay(engine,replace(spec,arrow_audience="viewer"),segs,ops));mask=view[:,:,3]>0
        assert mask.any() and np.all(view[mask,:3]==[192,192,192])
        (_,changed),_=click(engine,c,tmp);assert not changed
        (info,changed),_=click(engine,c,tmp,gesture="double")
        assert info["door_action"]=="unlock" and changed
        (info,changed),_=click(engine,c,tmp)
        assert info["door_action"]=="reveal" and changed


def test_entry_independence_shared_exit_and_restart(engine,passage_scene):
    db,tmp=passage_scene;segs=scene_walls("secret","unlocked_door")
    segs[-2].passage["sides"][0]={"role":"entry","kind":"secret","after":"locked_door","exit":0}
    validate_passages(segs)
    with db.connect() as c:
        walls_repo.replace(c,1,segs);c.execute("UPDATE maps SET walls_version=walls_version+1 WHERE id=1")
        fog_ops.add(c,1,"reveal",300,100,1);maps_repo.bump_fog(c,1)
        (info,changed),_=click(engine,c,tmp,side=1,gesture="double")
        assert changed and info["door_action"]=="discover"
        spec,walls,ops=inputs(c,tmp)
        assert {a.side:a.kind for a in arrows(engine,spec,walls,ops) if not a.exit_only}=={0:"secret",1:"unlocked_door"}
        viewer=arrows(engine,replace(spec,arrow_audience="viewer"),walls,ops)
        assert len(viewer)==1 and viewer[0].side==1
        click(engine,c,tmp,side=1,gesture="double")
    reopened=Database(db.path)
    with reopened.connect() as c:
        w=next(w for w in walls_repo.list_for_map(c,1) if w.kind=="portal" and w.passage["end"]=="a")
        assert w.runtime=={"1":"locked_door"}
        fog_ops.add(c,1,"hide_all",None,None,1)
        assert not c.execute("SELECT * FROM passage_runtime_states").fetchall()
        assert not c.execute("PRAGMA foreign_key_check").fetchall()


@pytest.mark.parametrize("method",["explicit","fog-reset","replace"])
def test_reset_restores_authored_state(passage_scene,method):
    db,tmp=passage_scene
    with db.connect() as c:
        w=next(w for w in walls_repo.list_for_map(c,1) if w.kind=="portal" and w.passage["end"]=="a")
        set_state(c,1,w,1,"locked_door")
        if method=="explicit":reset(c,1)
        elif method=="fog-reset":fog_ops.add(c,1,"hide_all",None,None,1)
        else:walls_repo.replace(c,1,scene_walls())
        assert c.execute("SELECT count(*) FROM passage_runtime_states").fetchone()[0]==0


@pytest.mark.parametrize("after",["door","locked_door","unlocked_door"])
def test_secret_door_outcome_and_persistent_arrows(engine,passage_scene,after):
    db,tmp=passage_scene
    with db.connect() as c:
        segs=scene_walls()[:-2]+[WallSegment(200,70,200,130,"secret",True,passage={"after":after}),WallSegment(400,70,400,130)]
        walls_repo.replace(c,1,segs);c.execute("UPDATE maps SET walls_version=walls_version+1 WHERE id=1")
        (info,_),_=click(engine,c,tmp,gesture="double");assert info["door_action"]=="discover"
        spec,walls,ops=inputs(c,tmp);w=next(w for w in walls if w.designed_kind=="secret")
        assert w.kind==after
        authored=next(w for w in walls_repo.list_for_map(c,1,designed=True) if w.kind=="secret")
        assert authored.passage=={"after":after}
        if after=="locked_door":click(engine,c,tmp,gesture="double")
        (info,_),_=click(engine,c,tmp);assert info["door_action"]=="reveal"
        spec,walls,ops=inputs(c,tmp)
        assert len(arrows(engine,replace(spec,arrow_audience="viewer"),walls,ops))==2
        assert all(a.secret_origin for a in arrows(engine,spec,walls,ops))
        reset(c,1)
        assert next(w for w in walls_repo.list_for_map(c,1) if w.designed_kind=="secret").kind=="secret"


def test_both_routes_uvtt_roundtrip():
    segs=pair()
    segs[0].passage["sides"]=[{"role":"none"},{"role":"both","kind":"secret","after":"locked_door","exit":0}]
    segs[1].passage["sides"]=[{"role":"both","kind":"unlocked_door","after":"door","exit":1},{"role":"none"}]
    data=export_uvtt(segs,600,200,"Pair",137)
    assert data["looking_glass"]["version"]==2
    result=parse_wall_file(encode_uvtt(data))[0].segments
    assert [s.passage for s in result]==[s.passage for s in segs]
    assert rows_for(result)[0][:4]==pytest.approx(rows_for(segs)[0][:4])
    assert len(data["line_of_sight"])==2 and not data["portals"]
    data["line_of_sight"][0][0]["x"]+=1
    with pytest.raises(WallImportError,match="geometry changed"):parse_wall_file(encode_uvtt(data))


@pytest.mark.parametrize("bad",["orphan","same-end","two-none","missing-target","target-entry","unused-exit","bad-role","bad-state","passive"])
def test_invalid_portals_rejected(bad):
    segs=pair()
    if bad=="orphan":segs.pop()
    elif bad=="same-end":segs[1].passage["end"]="a"
    elif bad=="two-none":segs[0].passage["sides"]=[{"role":"none"},{"role":"none"}]
    elif bad=="missing-target":del segs[0].passage["sides"][1]["exit"]
    elif bad=="target-entry":segs[1].passage["sides"][0]={"role":"entry","kind":"door","exit":1}
    elif bad=="unused-exit":segs[1].passage["sides"][1]={"role":"exit"}
    elif bad=="bad-role":segs[1].passage["sides"][0]["role"]="evil"
    elif bad=="bad-state":segs[0].passage["sides"][1]["kind"]="open"
    elif bad=="passive":segs[0]=replace(segs[0],blocks=False)
    with pytest.raises(ValueError):validate_segments(rows_for(segs))


def test_source_gating_exit_hints_and_side_validation(engine,passage_scene):
    db,tmp=passage_scene
    with db.connect() as c:
        spec,segs,ops=inputs(c,tmp)
        assert any(a.exit_only for a in arrows(engine,spec,segs,ops))
        assert not any(a.exit_only for a in arrows(engine,replace(spec,arrow_audience="viewer"),segs,ops))
        assert not arrows(engine,spec,segs,[FogOp("hide_all")])
        assert not arrows(engine,replace(spec,doors_block=False),segs,ops)
        (_,changed),body=click(engine,c,tmp,gesture="double");assert not changed
        body.side=0
        with pytest.raises(ValueError,match="side changed"):click(engine,c,tmp,body=body)
        assert fog_ops.count(c,1)==1


def test_migration_preserves_existing_rows(tmp_path):
    db=Database(tmp_path/"old.db")
    with db.connect() as c:
        c.executescript("".join(MIGRATIONS[:9]))
        c.executescript("CREATE TABLE schema_version(version INTEGER); INSERT INTO schema_version VALUES(9);")
        c.execute("INSERT INTO campaigns(id,name) VALUES(1,'C')")
        c.execute("INSERT INTO maps(id,campaign_id,name,image_file,width,height) VALUES(1,1,'M','x',600,200)")
        c.execute("INSERT INTO walls(id,map_id,x1,y1,x2,y2,kind) VALUES(1,1,200,70,200,130,'locked_door')")
        c.execute("INSERT INTO door_runtime_states VALUES(1,'unlocked_door')")
    assert db.migrate()==db.migrate()==len(MIGRATIONS)
    with db.connect() as c:
        assert walls_repo.list_for_map(c,1)[0].kind=="unlocked_door"
        assert walls_repo.list_for_map(c,1,designed=True)[0].kind=="locked_door"
        assert walls_repo.list_for_map(c,1)[0].passage=={}
