import pytest
pytest.importorskip("fastapi")
from fastapi.testclient import TestClient
from test_web import env
from test_map_transitions_web import prepare
from looking_glass.services import scrying_glass

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
    bad={**body,"revision":99}
    assert dm.post(path,json=bad,headers=h).status_code==400
