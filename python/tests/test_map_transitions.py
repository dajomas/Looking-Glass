"""Cross-map endpoint validation, atomic travel, replay and viewer privacy."""
from dataclasses import replace
from types import SimpleNamespace
from concurrent.futures import ThreadPoolExecutor
import uuid
import sqlite3
import pytest
import numpy as np
from PIL import Image
from test_fog import engine,_setup
from looking_glass.db import Database,MIGRATIONS
from looking_glass.repositories import maps,walls,fog_ops
from looking_glass.services import map_transitions as tr
from looking_glass.services.wall_model import FogOp


def draft(**kw):
    return dict(name="Stairs",player_label="Up",kind="stairs",x=100.,y=100.,visibility="discovered",availability="usable",destination_id=None,arrival="area",notes="PRIVATE")|kw

@pytest.fixture
def scene(tmp_path,engine):
    db=Database(tmp_path/"db");db.migrate();spec,segs=_setup(tmp_path)
    segs=[replace(s,x1=spec.calibration.apply(s.x1,s.y1)[0],y1=spec.calibration.apply(s.x1,s.y1)[1],x2=spec.calibration.apply(s.x2,s.y2)[0],y2=spec.calibration.apply(s.x2,s.y2)[1]) for s in segs]
    with db.connect() as c:
        c.execute("INSERT INTO users(id,username,password_hash,role) VALUES(1,'dm','x','admin')")
        c.execute("INSERT INTO campaigns(id,name,owner_id) VALUES(1,'C',1),(2,'Other',1)")
        for mid,cid in ((1,1),(2,1),(3,2)):
            c.execute("INSERT INTO maps(id,campaign_id,name,image_file,width,height) VALUES(?,?,'Map','map.png',400,200)",(mid,cid));walls.replace(c,mid,segs)
        c.execute("UPDATE campaigns SET active_map_id=1 WHERE id=1")
        a=tr.save(c,1,1,draft());b=tr.save(c,1,2,draft())
        a=tr.save(c,1,1,draft(destination_id=b["id"]),a["id"],a["revision"],True)
        b=tr.effective(tr.endpoint(c,b["id"],1));fog_ops.add(c,1,"reveal",100,100,1)
    return db,SimpleNamespace(fog=engine,settings=SimpleNamespace(maps_dir=tmp_path)),a,b


def body(c,ctx,a,**kw):
    _,_,p=tr.arrival_info(c,ctx,1,a["id"])
    return dict(source_endpoint_id=a["id"],expected_active_map_id=1,source_revision=p["source_revision"],destination_revision=p["destination_revision"],destination_version=p["destination_version"],request_id=uuid.uuid4().hex,override=False,allow_large_reveal=False)|kw

@pytest.mark.parametrize("kind",sorted(tr.KINDS))
def test_types(scene,kind):
    db,ctx,a,b=scene
    with db.connect() as c:
        r=tr.save(c,1,1,draft(kind=kind));assert r["kind"]==kind
        assert tr.overview(c,1) and not c.execute("PRAGMA foreign_key_check").fetchall()

@pytest.mark.parametrize("kw",[{"x":-1},{"x":400},{"y":200},{"x":float("nan")},{"x":float("inf")},{"name":" "},{"name":"x"*121},{"player_label":"x"*121},{"notes":"x"*2001},{"kind":"bad"},{"visibility":"bad"},{"availability":"bad"},{"arrival":"all"}])
def test_validation(scene,kw):
    db,ctx,a,b=scene
    with db.connect() as c:
        with pytest.raises(ValueError):tr.save(c,1,1,draft(**kw))


def test_link_and_revision_rules(scene):
    db,ctx,a,b=scene
    with db.connect() as c:
        other=tr.save(c,2,3,draft())
        for data in (draft(destination_id=other["id"]),draft(destination_id=a["id"])):
            with pytest.raises(ValueError):tr.save(c,1,1,data)
        with pytest.raises(ValueError):tr.save(c,1,1,draft(),a["id"],0)
        with pytest.raises(ValueError):tr.save(c,1,3,draft())
        with pytest.raises(ValueError):tr.save(c,1,1,draft(destination_id=b["id"]),return_link=True)
        with pytest.raises(sqlite3.IntegrityError):c.execute("UPDATE map_transitions SET destination_id=? WHERE id=?",(other["id"],a["id"]))


def test_atomic_reveal_replay_and_existing_exploration(scene):
    db,ctx,a,b=scene
    with db.connect() as c:
        fog_ops.add(c,2,"reveal",300,100,1);request=body(c,ctx,a)
    with db.connect() as c:
        c.execute("BEGIN IMMEDIATE");result=tr.travel(c,ctx,1,1,request)
        assert result["active_map_id"]==2 and fog_ops.count(c,1)==1 and fog_ops.count(c,2)==2
        assert c.execute("SELECT count(*) FROM map_fog_snapshots").fetchone()[0]==2
    with db.connect() as c:
        c.execute("BEGIN IMMEDIATE");assert tr.travel(c,ctx,1,1,request)==result
        assert fog_ops.count(c,2)==2
        with pytest.raises(ValueError):tr.travel(c,ctx,1,1,request|{"override":True})

@pytest.mark.parametrize("change",["source","destination","fog","active"])
def test_stale_travel(scene,change):
    db,ctx,a,b=scene
    with db.connect() as c:
        request=body(c,ctx,a)
        if change in ("source","destination"):
            r=a if change=="source" else b;tr.runtime(c,1,r["id"],r["revision"],"secret",None)
        elif change=="fog":maps.bump_fog(c,2)
        else:c.execute("UPDATE campaigns SET active_map_id=2 WHERE id=1")
    with pytest.raises(ValueError),db.connect() as c:
        c.execute("BEGIN IMMEDIATE");tr.travel(c,ctx,1,1,request)
    with db.connect() as c:assert not fog_ops.count(c,2)

@pytest.mark.parametrize("visibility,availability",[("secret","usable"),("discovered","blocked"),("discovered","approval")])
def test_approval_and_reset(scene,visibility,availability):
    db,ctx,a,b=scene
    with db.connect() as c:
        tr.runtime(c,1,a["id"],a["revision"],visibility,availability);request=body(c,ctx,a)
        with pytest.raises(ValueError):tr.travel(c,ctx,1,1,request)
        assert not fog_ops.count(c,2)
        tr.travel(c,ctx,1,1,request|{"override":True});tr.reset_runtime(c,1)
        r=tr.effective(tr.endpoint(c,a["id"],1));assert r["current_visibility"]=="discovered" and r["current_availability"]=="usable"
        assert fog_ops.count(c,1)==1


def test_preserve_and_one_way(scene):
    db,ctx,a,b=scene
    with db.connect() as c:
        a=tr.save(c,1,1,draft(destination_id=b["id"],arrival="preserve"),a["id"],a["revision"])
        tr.save(c,1,2,draft(),b["id"],b["revision"]);request=body(c,ctx,a);tr.travel(c,ctx,1,1,request)
        assert not fog_ops.count(c,2)
        with pytest.raises(ValueError):tr.arrival_info(c,ctx,1,b["id"])


def test_large_reveal_gate(scene):
    db,ctx,a,b=scene
    with db.connect() as c:
        walls.clear(c,2);request=body(c,ctx,a)
        assert tr.arrival_info(c,ctx,1,a["id"])[2]["warning"]
        with pytest.raises(ValueError):tr.travel(c,ctx,1,1,request)
        assert not fog_ops.count(c,2)
        tr.travel(c,ctx,1,1,request|{"allow_large_reveal":True})


def test_deleted_destination(scene):
    db,ctx,a,b=scene
    with db.connect() as c:
        c.execute("DELETE FROM maps WHERE id=2");r=tr.effective(tr.endpoint(c,a["id"],1))
        assert r["broken"] and r["revision"]>a["revision"]
        assert not c.execute("PRAGMA foreign_key_check").fetchall()
        with pytest.raises(ValueError):tr.arrival_info(c,ctx,1,a["id"])


def test_resize_and_wall_arrival(scene):
    db,ctx,a,b=scene
    with db.connect() as c:
        tr.save(c,1,2,draft(x=200,destination_id=a["id"]),b["id"],b["revision"])
        with pytest.raises(ValueError,match="wall"):tr.arrival_info(c,ctx,1,a["id"])
        c.execute("UPDATE maps SET width=50 WHERE id=2")
        with pytest.raises(ValueError,match="outside"):tr.arrival_info(c,ctx,1,a["id"])


def test_private_and_secret_markers(scene):
    db,ctx,a,b=scene
    with db.connect() as c:
        public=tr.viewer_markers(c,1);assert public==((100.,100.,"stairs","Up"),)
        assert "PRIVATE" not in repr(public) and a["id"] not in repr(public) and b["id"] not in repr(public)
        for vis in ("secret","admin"):
            r=tr.endpoint(c,a["id"],1);tr.runtime(c,1,a["id"],r["revision"],vis,None);assert not tr.viewer_markers(c,1)


def test_reset_authored_secret(scene):
    db,ctx,a,b=scene
    with db.connect() as c:
        a=tr.save(c,1,1,draft(visibility="secret",destination_id=b["id"]),a["id"],a["revision"])
        tr.runtime(c,1,a["id"],a["revision"],"discovered","usable");assert tr.viewer_markers(c,1)
        tr.reset_runtime(c,1);assert not tr.viewer_markers(c,1) and fog_ops.count(c,1)==1


def test_marker_clipping_and_cache(engine,tmp_path):
    spec,segs=_setup(tmp_path);spec=replace(spec,transition_markers=((100,100,"stairs","UP"),(300,100,"portal","HIDDEN")))
    ops=[FogOp("reveal",100,100)]
    overlay=np.array(tr.marker_overlay(engine,spec,segs,ops,(400,200)))
    assert overlay[100,100,3] and not overlay[:,250:,3].any()
    assert not np.array(tr.marker_overlay(engine,replace(spec,fog_version=2),segs,[],(400,200)))[:,:,3].any()
    off=replace(spec,viewer_transition_markers=False)
    assert not np.array(tr.marker_overlay(engine,off,segs,ops,(400,200)))[:,:,3].any()
    first=engine.viewer_image(spec,segs,ops).read_bytes();assert engine.viewer_image(off,segs,ops).read_bytes()!=first
    assert replace(spec,viewer_transition_labels=False).identity!=spec.identity
    assert tuple(np.array(Image.open(engine.viewer_image(spec,segs,ops)))[100,300])==(0,0,0)


def test_transaction_rollback(scene):
    db,ctx,a,b=scene
    with db.connect() as c:
        request=body(c,ctx,a);c.execute("CREATE TRIGGER fail_travel BEFORE UPDATE OF active_map_id ON campaigns BEGIN SELECT RAISE(ABORT,'failure'); END")
    with pytest.raises(sqlite3.IntegrityError),db.connect() as c:
        c.execute("BEGIN IMMEDIATE");tr.travel(c,ctx,1,1,request)
    with db.connect() as c:
        assert not fog_ops.count(c,2) and not c.execute("SELECT * FROM map_fog_snapshots").fetchall()
        assert c.execute("SELECT active_map_id FROM campaigns WHERE id=1").fetchone()[0]==1
        assert not c.execute("SELECT * FROM map_transition_travel").fetchall()


def test_concurrent_duplicate(scene):
    db,ctx,a,b=scene
    with db.connect() as c:request=body(c,ctx,a)
    def execute(_):
        with db.connect() as c:
            c.execute("BEGIN IMMEDIATE");return tr.travel(c,ctx,1,1,request)
    with ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(execute,range(2)))
    assert results[0]==results[1]
    with db.connect() as c:assert fog_ops.count(c,2)==1 and c.execute("SELECT count(*) FROM map_transition_travel").fetchone()[0]==1


def test_migration_preserves_rows(tmp_path):
    db=Database(tmp_path/"old")
    with db.connect() as c:
        c.executescript("".join(MIGRATIONS[:11]));c.executescript("CREATE TABLE schema_version(version INTEGER);INSERT INTO schema_version VALUES(11);")
        c.execute("INSERT INTO campaigns(id,name) VALUES(1,'C')");c.execute("INSERT INTO maps(id,campaign_id,name,image_file,width,height) VALUES(1,1,'M','map.png',400,200)")
        old=dict(maps.get(c,1))
    assert db.migrate()==db.migrate()==12
    with db.connect() as c:
        row=dict(maps.get(c,1));assert all(row[k]==v for k,v in old.items())
        assert row["viewer_transition_markers"]==row["viewer_transition_labels"]==1 and not tr.overview(c,1)
