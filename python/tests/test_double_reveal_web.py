"""HTTP ownership, CSRF, dimension checks, previews and stale writes."""
import io
import pytest
pytest.importorskip('fastapi')
from fastapi.testclient import TestClient
from test_web import env,login,csrf_of
from test_map_transitions_web import prepare
from conftest import png_bytes
from PIL import Image

def stamp(data):return {k:data[k] for k in ('cache_token','walls_version','fog_version','image_revision')}
def upload(dm,base,h,w=400,height=200):
    return dm.post(base+'/image',data=stamp(dm.get(base).json()),files={'file':('alternate.png',png_bytes(w,height,(10,200,10)),'image/png')},headers=h)

def test_auth_csrf_upload_and_previews(env):
    ctx,admin,viewer,dm,h,cid,mids=prepare(env);base=f'/api/maps/{mids[0]}/double-reveal'
    assert TestClient(admin).get(base).status_code==401
    stranger=login(admin,'dm2','dmpass123');assert stranger.get(base).status_code==403
    assert stranger.get(base+'/artwork?appearance=true').status_code==403
    assert dm.post(base+'/undo',json=stamp(dm.get(base).json())).status_code==403
    for path in ('','/room?x=100&y=100','/artwork?appearance=true','/room-mask?x=100&y=100'):
        assert TestClient(viewer).get(base+path).status_code==404
    assert upload(dm,base,h,10,10).status_code==400
    assert dm.get(base).json()['image_revision']==0
    response=upload(dm,base,h);assert response.status_code==200,response.text
    for appearance in ('initial','true','current'):
        response=dm.get(base+'/artwork?appearance='+appearance)
        assert response.status_code==200 and response.headers['cache-control']=='no-store'
        assert Image.open(io.BytesIO(response.content)).size==(400,200)
    assert dm.get(base+'/room?x=nan&y=0').status_code==400
    assert dm.get(f'/maps/{mids[0]}').status_code==200

def test_http_state_and_stale_writes(env):
    ctx,admin,viewer,dm,h,cid,mids=prepare(env);mid=mids[0];base=f'/api/maps/{mid}/double-reveal'
    assert upload(dm,base,h).status_code==200
    selected=dm.get(base+'/room?x=100&y=100').json()
    response=dm.post(base+'/room',json=stamp(selected)|dict(x=100,y=100,revision=0,enabled=True,destination_map_id=mids[1]),headers=h)
    assert response.status_code==200,response.text
    state=response.json();room=state['rooms'][0]
    change=stamp(state)|dict(area_key=room['area_key'],revision=room['revision'],true_active=True)
    assert dm.post(base+'/appearance',json=change,headers=h).status_code==200
    assert dm.post(base+'/appearance',json=change,headers=h).status_code==400
    assert dm.post(f'/api/maps/{mid}/reset',json={},headers=h).status_code==200
    assert dm.get(base).json()['rooms'][0]['true_active']==1
    assert dm.post(f'/api/campaigns/{cid}/active',json=dict(map_id=mid,fog_action='restore'),headers=h).status_code==200
    assert dm.post(f'/api/maps/{mid}/reveal',json=dict(x=100,y=100),headers=h).status_code==200
    state=dm.get(base).json();room=state['rooms'][0]
    travel=stamp(state)|dict(area_key=room['area_key'],revision=room['revision'],expected_active_map_id=mid)
    response=dm.post(base+'/travel',json=travel,headers=h);assert response.status_code==200,response.text
    assert response.json()['map_id']==mids[1]
    assert dm.post(base+'/travel',json=travel,headers=h).status_code==400
