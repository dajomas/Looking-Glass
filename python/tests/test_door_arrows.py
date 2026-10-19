from dataclasses import replace
import io
import numpy as np
import pytest
from PIL import Image
from test_fog import engine, _setup
from looking_glass.db import Database, MIGRATIONS
from looking_glass.services.door_arrows import arrows, target_at
from looking_glass.services.fog import MapSpec
from looking_glass.services.wall_model import FogOp, Calibration


def pick(engine,spec,segs,ops):
    rgba=np.array(engine.door_arrow_overlay(spec,segs,ops))
    ys,xs=np.nonzero(rgba[:,:,3])
    assert len(xs)
    i=len(xs)//2
    area=engine.area_map(spec,segs)
    return (xs[i]+.5)/area.scale,(ys[i]+.5)/area.scale


@pytest.mark.parametrize("source,destination",[(100,300),(300,100)])
def test_click_reveals_other_side_and_undo(engine,tmp_path,source,destination):
    spec,segs=_setup(tmp_path,door=True)
    ops=[FogOp("reveal",source,100)]
    click=pick(engine,spec,segs,ops)
    target=target_at(engine,spec,segs,ops,*click)
    area=engine.area_map(spec,segs)
    assert engine.label_at(area,*target)==engine.label_at(area,destination,100)
    assert engine.label_at(area,*target)!=engine.label_at(area,source,100)
    after=ops+[FogOp("reveal",*target)]
    assert arrows(engine,spec,segs,after)==[]
    assert target_at(engine,spec,segs,after,*click) is None
    assert target_at(engine,spec,segs,after[:-1],*click)==target


def test_raster_hit_matches_visible_pixels(engine,tmp_path):
    spec,segs=_setup(tmp_path,door=True)
    ops=[FogOp("reveal",100,100)]
    rgba=np.array(engine.door_arrow_overlay(spec,segs,ops))
    # Includes arrow pixels, concave gaps and neighboring fog/wall pixels.
    for y in range(85,116):
        for x in range(160,211):
            assert (target_at(engine,spec,segs,ops,x+.5,y+.5) is not None)==bool(rgba[y,x,3])


@pytest.mark.parametrize("x,y",[(-1,100),(400,100),(100,200),(float('nan'),1),(1,float('inf')),(300,100),(100,100)])
def test_off_arrow_not_revealed(engine,tmp_path,x,y):
    spec,segs=_setup(tmp_path,door=True)
    assert target_at(engine,spec,segs,[FogOp("reveal",100,100)],x,y) is None


def test_disabled_and_color_preserved(engine,tmp_path):
    spec,segs=_setup(tmp_path,door=True)
    spec=replace(spec,door_arrow_color="#00ff00")
    ops=[FogOp("reveal",100,100)]
    click=pick(engine,spec,segs,ops)
    before=engine.viewer_image(spec,segs,ops)
    off=replace(spec,door_arrows_enabled=False)
    assert not np.array(engine.door_arrow_overlay(off,segs,ops))[:,:,3].any()
    assert target_at(engine,off,segs,ops,*click) is None
    after=engine.viewer_image(off,segs,ops)
    assert after!=before
    image=np.array(Image.open(after))
    assert np.all(image[100,300]==0)
    assert off.door_arrow_color=="#00ff00"
    assert target_at(engine,replace(off,door_arrows_enabled=True),segs,ops,*click)


@pytest.mark.parametrize("ops",[[],[FogOp("reveal_all")],[FogOp("hide_all")],
    [FogOp("reveal",100,100),FogOp("hide",100,100)]])
def test_no_boundary_no_arrow(engine,tmp_path,ops):
    spec,segs=_setup(tmp_path,door=True)
    assert not arrows(engine,spec,segs,ops)


@pytest.mark.parametrize("kind,blocks,doors_block",[("secret",True,True),("door",False,True),("door",True,False)])
def test_excluded_doors(engine,tmp_path,kind,blocks,doors_block):
    spec,segs=_setup(tmp_path,door=True,doors_block=doors_block)
    segs=[replace(s,kind=kind,blocks=blocks) if s.kind=="door" else s for s in segs]
    assert not arrows(engine,spec,segs,[FogOp("reveal",100,100)])


def test_calibrated_downscaled_target(engine,tmp_path):
    spec,segs=_setup(tmp_path,door=True)
    shifted=[]
    for s in segs:
        x1,y1=spec.calibration.apply(s.x1,s.y1)
        x2,y2=spec.calibration.apply(s.x2,s.y2)
        shifted.append(replace(s,x1=x1*2+20,x2=x2*2+20,y1=y1*2+30,y2=y2*2+30))
    spec=replace(spec,calibration=Calibration(20,30,.5,.5))
    engine.work_max_dim=200
    ops=[FogOp("reveal",100,100)]
    click=pick(engine,spec,shifted,ops)
    target=target_at(engine,spec,shifted,ops,*click)
    area=engine.area_map(spec,shifted)
    assert engine.label_at(area,*target)==engine.label_at(area,300,100)


@pytest.mark.parametrize("version",[4,5,6])
def test_upgrade_persistence(tmp_path,version):
    db=Database(tmp_path/"old.db")
    with db.connect() as c:
        c.executescript("".join(MIGRATIONS[:version]))
        c.executescript(f"CREATE TABLE schema_version(version INTEGER); INSERT INTO schema_version VALUES({version});")
        c.execute("INSERT INTO campaigns(id,name) VALUES(1,'C')")
        c.execute("INSERT INTO maps(id,campaign_id,name,image_file,width,height) VALUES(1,1,'M','a.png',400,200)")
        if version>=5:c.execute("UPDATE maps SET door_arrow_color='#123456'")
        if version==6:c.execute("UPDATE maps SET door_arrows_enabled=0")
        c.execute("INSERT INTO fog_ops(map_id,op,x,y) VALUES(1,'reveal',100,100)")
        before=dict(c.execute("SELECT * FROM maps").fetchone())
    assert db.migrate()==db.migrate()==6
    with db.connect() as c:
        row=c.execute("SELECT * FROM maps").fetchone()
        assert all(row[k]==v for k,v in before.items())
        spec=MapSpec.from_row(row,tmp_path)
        assert spec.door_arrows_enabled==(version!=6)
        assert c.execute("SELECT count(*) FROM fog_ops").fetchone()[0]==1
