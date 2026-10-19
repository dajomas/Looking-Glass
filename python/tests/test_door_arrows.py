from dataclasses import replace
import io
import numpy as np
import pytest
from PIL import Image
from test_fog import engine, _setup
from looking_glass.db import Database, MIGRATIONS
from looking_glass.services.fog import MapSpec
from looking_glass.services.wall_model import FogOp


@pytest.mark.parametrize("x,sign", [(100,-1),(300,1)])
def test_enabled_by_default_revealed_side(engine,tmp_path,x,sign):
    spec,segs=_setup(tmp_path,door=True)
    assert spec.door_arrows_enabled is True
    arr=np.array(engine.door_arrow_overlay(spec,segs,[FogOp("reveal",x,100)]))
    ys,xs=np.nonzero(arr[:,:,3])
    assert len(xs) and np.all((xs-200)*sign>0)
    assert np.all(arr[ys,xs,:3]==[70,192,255])


def test_disable_reenable_preserves_color_and_fog(engine,tmp_path):
    spec,segs=_setup(tmp_path,door=True)
    spec=replace(spec,door_arrow_color="#00ff00")
    ops=[FogOp("reveal",100,100)]
    on=np.array(engine.door_arrow_overlay(spec,segs,ops))
    old=engine.viewer_image(spec,segs,ops)
    disabled=replace(spec,door_arrows_enabled=False)
    off=np.array(Image.open(io.BytesIO(engine.door_arrows_png(disabled,segs,ops))))
    assert not off[:,:,3].any()
    path=engine.viewer_image(disabled,segs,ops)
    assert path!=old
    image=np.array(Image.open(path))
    assert np.all(image[on[:,:,3]>0]==[250,0,0])
    assert np.all(image[100,300]==0)
    assert np.array_equal(on,np.array(engine.door_arrow_overlay(replace(disabled,door_arrows_enabled=True),segs,ops)))
    assert disabled.door_arrow_color=="#00ff00"


@pytest.mark.parametrize("ops", [[],[FogOp("reveal_all")],[FogOp("hide_all")],
    [FogOp("reveal",100,100),FogOp("reveal",300,100)]])
def test_no_boundary_no_arrows(engine,tmp_path,ops):
    spec,segs=_setup(tmp_path,door=True)
    assert not np.array(engine.door_arrow_overlay(spec,segs,ops))[:,:,3].any()


def test_secret_excluded(engine,tmp_path):
    spec,segs=_setup(tmp_path,door=True)
    segs=[replace(s,kind="secret") if s.kind=="door" else s for s in segs]
    assert not np.array(engine.door_arrow_overlay(spec,segs,[FogOp("reveal",100,100)]))[:,:,3].any()


@pytest.mark.parametrize("version",[4,5])
def test_upgrade_and_persistence(tmp_path,version):
    db=Database(tmp_path/"old.db")
    with db.connect() as c:
        c.executescript("".join(MIGRATIONS[:version]))
        c.executescript(f"CREATE TABLE schema_version(version INTEGER); INSERT INTO schema_version VALUES({version});")
        c.execute("INSERT INTO campaigns(id,name) VALUES(1,'C')")
        c.execute("INSERT INTO maps(id,campaign_id,name,image_file,width,height) VALUES(1,1,'M','a.png',400,200)")
        if version==5: c.execute("UPDATE maps SET door_arrow_color='#123456'")
        c.execute("INSERT INTO fog_ops(map_id,op,x,y) VALUES(1,'reveal',100,100)")
        before=dict(c.execute("SELECT * FROM maps").fetchone())
    assert db.migrate()==db.migrate()==6
    with db.connect() as c:
        row=c.execute("SELECT * FROM maps").fetchone()
        assert row['door_arrows_enabled']==1
        assert all(row[k]==v for k,v in before.items())
        c.execute("UPDATE maps SET door_arrows_enabled=0")
    with db.connect() as c:
        row=c.execute("SELECT * FROM maps").fetchone()
        spec=MapSpec.from_row(row,tmp_path)
        assert spec.door_arrows_enabled is False
        assert spec.door_arrow_color==('#123456' if version==5 else '#46c0ff')
        assert c.execute("SELECT count(*) FROM fog_ops").fetchone()[0]==1
