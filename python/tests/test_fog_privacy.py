"""Bug 1: fog softness must not disclose hidden-room interiors."""
import hashlib
from dataclasses import replace

import numpy as np
import pytest
from PIL import Image
from looking_glass.config import DEFAULTS
from looking_glass.services.fog import AreaMap, FogEngine, MapSpec
from looking_glass.services.wall_model import Calibration, FogOp, WallSegment


def setup(tmp_path, work=100, viewer=100, feather=2, dimensions=(100,60)):
    engine = FogEngine(dict(DEFAULTS["fog"], work_max_dim=work, feather_px=feather),
        dict(DEFAULTS["viewer"], max_image_dim=viewer, image_format="png"), tmp_path/"cache")
    image = tmp_path/"map.png"
    Image.new("RGB", dimensions, (255,255,255)).save(image)
    spec = MapSpec(1,*dimensions,image,Calibration(),True,1,1,
                   door_arrows_enabled=False,viewer_door_arrows_enabled=False)
    walls = [WallSegment(dimensions[0]/2,0,dimensions[0]/2,dimensions[1]-1)]
    return engine,spec,walls


@pytest.mark.parametrize("work,viewer,dimensions",[(100,100,(100,60)),(50,100,(100,60)),(100,50,(100,60)),(41,71,(101,63))])
@pytest.mark.parametrize("feather",[0,2,5])
def test_hidden_interiors_remain_fogged(tmp_path,work,viewer,dimensions,feather):
    engine,spec,walls=setup(tmp_path,work,viewer,feather,dimensions)
    area=engine.area_map(spec,walls)
    left=engine.label_at(area,dimensions[0]/4,dimensions[1]/2)
    right=engine.label_at(area,dimensions[0]*.75,dimensions[1]/2)
    assert left and right and left!=right
    ops=[FogOp("reveal",dimensions[0]/4,dimensions[1]/2)]
    with Image.open(engine.viewer_image(spec,walls,ops)) as src:
        image=src.convert("RGB")
    hidden=Image.fromarray((area.labels==right).astype(np.uint8)*255).resize(image.size,Image.Resampling.NEAREST)
    pixels=np.asarray(image)
    assert not pixels[np.asarray(hidden)>0].any()
    assert pixels[image.height//2,image.width//4].max()>200


def test_dilation_never_reveals_another_open_component(tmp_path,monkeypatch):
    engine,spec,_=setup(tmp_path,dimensions=(9,3))
    labels=np.tile(np.array([1,1,1,1,0,2,2,2,2],dtype=np.int32),(3,1))
    area=AreaMap(labels,2,np.bincount(labels.ravel()),1.0)
    monkeypatch.setattr(engine,"area_map",lambda *args:area)
    mask=engine.mask(spec,[],[FogOp("reveal",1,1)])
    assert mask[1,4] and mask[1,1]
    assert not mask[labels==2].any()


def test_reveal_all_and_hide_all_keep_their_meaning(tmp_path):
    engine,spec,walls=setup(tmp_path)
    with Image.open(engine.viewer_image(spec,walls,[FogOp("reveal_all")])) as src:
        assert np.all(np.asarray(src.convert("RGB"))==255)
    spec=replace(spec,fog_version=2)
    with Image.open(engine.viewer_image(spec,walls,[FogOp("reveal_all"),FogOp("hide_all")])) as src:
        assert not np.asarray(src.convert("RGB")).any()


def test_restart_ignores_pre_fix_cached_composite(tmp_path):
    engine,spec,walls=setup(tmp_path)
    viewer_spec=replace(spec,door_arrows_enabled=False,arrow_audience="viewer")
    old=("fog-cache-v2",viewer_spec.identity,engine.work_max_dim,engine.thickness,
         engine.feather,engine.fog_rgb,engine.viewer_max_dim,engine.viewer_format,engine.viewer_quality)
    identity=hashlib.sha256(repr(old).encode()).hexdigest()[:32]
    stale=engine.cache_dir/f"viewer_{spec.id}_{identity}_{spec.walls_version}_{spec.fog_version}.png"
    Image.new("RGB",(spec.width,spec.height),(255,0,255)).save(stale)
    restarted=FogEngine(dict(DEFAULTS["fog"],work_max_dim=100,feather_px=2),
        dict(DEFAULTS["viewer"],max_image_dim=100,image_format="png"),engine.cache_dir)
    out=restarted.viewer_image(spec,walls,[])
    assert out!=stale
    with Image.open(out) as src:
        assert not np.asarray(src.convert("RGB")).any()
