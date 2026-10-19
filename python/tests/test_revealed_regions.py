import ast
import hashlib
import threading
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace
import numpy as np
import pytest
from test_fog import engine, _setup
from test_locked_doors import scene
from looking_glass.services.fog import AreaMap, MapSpec
from looking_glass.services.revealed_regions import revealed_area_signatures
from looking_glass.services.reveal_bounds import revealed_bounds
from looking_glass.services.wall_model import FogOp, WallSegment, Calibration


def test_reveal_repeat_hide_and_undo(engine,tmp_path):
    spec,segs=_setup(tmp_path,door=True)
    a=[FogOp('reveal',100,100)]
    first=revealed_area_signatures(engine,spec,segs,a)
    assert len(first)==1 and all(len(x)==64 for x in first)
    assert revealed_area_signatures(engine,spec,segs,a+a)==first
    both=a+[FogOp('reveal',300,100)]
    second=revealed_area_signatures(engine,spec,segs,both)
    assert len(second)==2 and set(second)>set(first)
    hidden=both+[FogOp('hide',300,100)]
    assert revealed_area_signatures(engine,spec,segs,hidden)==first
    assert revealed_area_signatures(engine,spec,segs,hidden[:-1])==second
    assert revealed_area_signatures(engine,spec,segs,both+[FogOp('hide_all')])==[]
    assert len(revealed_area_signatures(engine,spec,segs,[FogOp('reveal_all')]))==engine.area_map(spec,segs).count


def test_new_area_with_identical_overview_rectangle(engine,tmp_path):
    spec=MapSpec(99,300,100,tmp_path/'map.png',Calibration(),True,1,1)
    segs=[WallSegment(5,5,295,5),WallSegment(295,5,295,95),WallSegment(295,95,5,95),
          WallSegment(5,95,5,5),WallSegment(100,5,100,95),WallSegment(200,5,200,95)]
    old=[FogOp('reveal',50,50),FogOp('reveal',250,50)]
    new=old+[FogOp('reveal',150,50)]
    before=engine.mask(spec,segs,old)
    after=engine.mask(replace(spec,fog_version=2),segs,new)
    assert revealed_bounds(before,300,100)==revealed_bounds(after,300,100)
    old_keys=revealed_area_signatures(engine,spec,segs,old)
    new_keys=revealed_area_signatures(engine,spec,segs,new)
    assert len(new_keys)==3 and set(new_keys)>set(old_keys)
    equal_count=revealed_area_signatures(engine,spec,segs,[old[0],new[-1]])
    assert len(equal_count)==len(old_keys) and set(equal_count)-set(old_keys)


@pytest.mark.parametrize('change',[
    {'door_arrow_color':'#ff0000'},{'locked_door_arrow_color':'#00ff00'},
    {'door_arrows_enabled':False},{'viewer_door_arrows_enabled':False},
    {'walls_version':999,'fog_version':999}])
def test_style_visibility_and_version_changes_keep_fingerprints(engine,tmp_path,change):
    spec,segs=_setup(tmp_path,door=True);ops=[FogOp('reveal',100,100)]
    before=revealed_area_signatures(engine,spec,segs,ops)
    assert revealed_area_signatures(engine,replace(spec,**change),segs,ops)==before


def test_lock_unlock_does_not_create_new_area(engine,scene):
    db,inputs,click=scene
    with db.connect() as c:
        before=revealed_area_signatures(engine,*inputs(c))
        click(c,'double')
        assert revealed_area_signatures(engine,*inputs(c))==before
        click(c,'double')
        assert revealed_area_signatures(engine,*inputs(c))==before


def test_label_numbers_not_exposed_or_used_in_fingerprint():
    spec=SimpleNamespace(id=1,width=3,height=2)
    lock=threading.RLock()
    def keys(labels,visible):
        labels=np.array(labels,dtype=np.int32)
        area=AreaMap(labels,int(labels.max()),np.bincount(labels.ravel()),1)
        fake=SimpleNamespace(area_map=lambda *args:area,revealed_labels=lambda *args:{visible},_lock=lambda mid:lock)
        result=revealed_area_signatures(fake,spec,[],[])
        assert len(area.region_signatures)==1 # no hidden-region signatures are generated
        return result
    assert keys([[1,1,0],[0,2,2]],1)==keys([[7,7,0],[0,3,3]],7)


def test_cache_and_restart_stability(engine,tmp_path):
    spec,segs=_setup(tmp_path,door=True);ops=[FogOp('reveal',100,100)]
    before=revealed_area_signatures(engine,spec,segs,ops)
    area=engine.area_map(spec,segs)
    assert area.region_slices is not None and len(area.region_signatures)==1
    assert revealed_area_signatures(engine,spec,segs,ops)==before
    engine.invalidate(spec.id)
    assert revealed_area_signatures(engine,spec,segs,ops)==before


def test_viewer_state_exposes_only_visible_signatures(engine,scene):
    db,inputs,_=scene
    def authorize(c,user,cid):
        if user['id']!=1:raise PermissionError()
        return c.execute('SELECT * FROM campaigns WHERE id=?',(cid,)).fetchone()
    from looking_glass.repositories import maps as maps_repo
    tree=ast.parse((Path(__file__).parents[1]/'looking_glass/web/viewer/api.py').read_text())
    fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='state');fn.decorator_list=[]
    future=ast.ImportFrom(module='__future__',names=[ast.alias(name='annotations')],level=0)
    namespace=dict(campaign_for_view=authorize,maps_repo=maps_repo,fog_inputs=lambda ctx,c,mid:inputs(c),
        revealed_bounds=revealed_bounds,revealed_area_signatures=revealed_area_signatures,
        _version=lambda m:f"{m['id']}:{m['cache_token']}-{m['walls_version']}-{m['fog_version']}")
    exec(compile(ast.fix_missing_locations(ast.Module(body=[future,fn],type_ignores=[])),'state','exec'),namespace)
    response=namespace['state'](SimpleNamespace(db=db,fog=engine),{'id':1},1)
    assert len(response['map']['revealed_area_signatures'])==1
    assert 'walls' not in response['map'] and 'labels' not in response['map']
    with pytest.raises(PermissionError):namespace['state'](SimpleNamespace(db=db,fog=engine),{'id':2},1)


def test_concurrent_signature_reads(engine,tmp_path):
    from concurrent.futures import ThreadPoolExecutor
    spec,segs=_setup(tmp_path,door=True);ops=[FogOp('reveal',100,100),FogOp('reveal',300,100)]
    with ThreadPoolExecutor(max_workers=4) as pool:
        results=list(pool.map(lambda _:revealed_area_signatures(engine,spec,segs,ops),range(16)))
    assert all(keys==results[0] for keys in results) and len(results[0])==2
