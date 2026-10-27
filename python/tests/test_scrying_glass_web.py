import pytest
pytest.importorskip("fastapi")
from fastapi.testclient import TestClient
from test_web import env
from test_map_transitions_web import prepare
from looking_glass.services import scrying_glass_access

def test_lookup_auth_and_disabled(env):
    ctx,admin,viewer,dm,h,cid,mids=prepare(env)
    path=f"/api/maps/{mids[0]}/scrying-glass/check"
    point={"x":100,"y":100}
    room=dm.post(f"/api/maps/{mids[0]}/room-at",json=point,headers=h).json()
    body={**point,"area_key":room["area_key"],"revision":room["revision"]}
    assert TestClient(admin).post(path,json=body).status_code in {303,401}
    assert dm.post(path,json=body).status_code==403
    result=dm.post(path,json=body,headers=h)
    assert result.status_code==200 and result.json()["status"]=="disabled"
    assert result.headers["cache-control"]=="no-store"
    assert TestClient(viewer).post(path,json=body).status_code==404
    assert dm.post(path,json={**body,"revision":99},headers=h).status_code==400

def test_access_gate_auth_and_verification(env,monkeypatch):
    ctx,admin,viewer,dm,h,cid,mids=prepare(env)
    path=f"/api/maps/{mids[0]}/scrying-glass/access"
    assert TestClient(admin).post(path,json={}).status_code in {303,401}
    assert dm.post(path,json={}).status_code==403
    result=dm.post(path,json={},headers=h)
    assert result.status_code==200 and not result.json()["verified"] and not result.json()["enabled"]
    assert result.headers["cache-control"]=="no-store"
    assert TestClient(viewer).post(path,json={}).status_code==404
    monkeypatch.setattr(scrying_glass_access,"access",lambda *_: {"enabled":True,"verified":True,"status":"verified","retry_after_seconds":60,"message":""})
    assert dm.post(path,json={},headers=h).json()["verified"]
