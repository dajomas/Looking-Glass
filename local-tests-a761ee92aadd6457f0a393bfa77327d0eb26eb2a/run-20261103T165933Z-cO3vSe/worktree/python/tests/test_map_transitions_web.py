"""HTTP auth, CSRF and replay checks; requires installed project dependencies."""
import pytest
pytest.importorskip("fastapi")
from test_web import env,login,csrf_of
from conftest import png_bytes
from fastapi.testclient import TestClient


def prepare(env):
    ctx,admin,viewer=env;dm=login(admin,"dm","dmpass123");token=csrf_of(dm);h={"X-CSRF-Token":token}
    r=dm.post("/campaigns",data={"csrf_token":token,"name":"Travel"},follow_redirects=False)
    cid=int(r.headers["location"].split("/")[2].split("?")[0]);mids=[]
    for name in ("Ground","Upper"):
        r=dm.post(f"/campaigns/{cid}/maps",data={"csrf_token":token,"name":name},files={"image":(name+".png",png_bytes(),"image/png")},follow_redirects=False)
        mids.append(int(r.headers["location"].split("/")[2].split("?")[0]))
    return ctx,admin,viewer,dm,h,cid,mids


def test_transition_auth_csrf(env):
    ctx,admin,viewer,dm,h,cid,mids=prepare(env);base=f"/api/campaigns/{cid}"
    body=dict(map_id=mids[0],name="Ladder",player_label="Up",kind="ladder",x=100,y=100,arrival="preserve")
    assert dm.post(base+"/transitions",json=body).status_code==403
    r=dm.post(base+"/transitions",json=body,headers=h);assert r.status_code==200,r.text
    eid=r.json()["endpoints"][0]["id"]
    assert dm.post(base+"/transitions",json=body|{"return_link":"false"},headers=h).status_code==422
    stranger=login(admin,"dm2","dmpass123");sh={"X-CSRF-Token":csrf_of(stranger)}
    assert stranger.get(base+"/transitions").status_code==403
    assert stranger.post(base+"/transitions",json=body,headers=sh).status_code==403
    assert stranger.delete(base+f"/transitions/{eid}?revision=1",headers=sh).status_code==403
    for method,path in (("get",base+"/transitions"),("post",base+"/travel"),("post",base+"/transitions")):
        assert getattr(TestClient(viewer),method)(path).status_code==404
    assert dm.delete(base+f"/transitions/{eid}?revision=99",headers=h).status_code==400
    assert dm.delete(base+f"/transitions/{eid}?revision=1",headers=h).status_code==200


def test_transition_travel_http(env):
    ctx,admin,viewer,dm,h,cid,mids=prepare(env);base=f"/api/campaigns/{cid}"
    draft=dict(name="Target",player_label="Up",kind="stairs",x=100,y=100,arrival="preserve",notes="PRIVATE")
    r=dm.post(base+"/transitions",json=draft|{"map_id":mids[1]},headers=h);assert r.status_code==200,r.text
    dest=r.json()["endpoints"][0]["id"]
    r=dm.post(base+"/transitions",json=draft|{"map_id":mids[0],"name":"Source","destination_id":dest,"return_link":True},headers=h)
    assert r.status_code==200,r.text
    a=next(e for e in r.json()["endpoints"] if e["map_id"]==mids[0])
    assert dm.post(base+"/active",json={"map_id":mids[0],"fog_action":"restore"},headers=h).status_code==200
    p=dm.get(base+f"/transitions/{a['id']}/preview").json()
    body=dict(source_endpoint_id=a["id"],expected_active_map_id=mids[0],source_revision=p["source_revision"],destination_revision=p["destination_revision"],destination_version=p["destination_version"],request_id="http-request-001")
    assert dm.post(base+"/travel",json=body).status_code==403
    r=dm.post(base+"/travel",json=body,headers=h);assert r.status_code==200,r.text
    assert r.json()["active_map_id"]==mids[1]
    assert dm.post(base+"/travel",json=body,headers=h).json()==r.json()
    assert dm.get(f"/maps/{mids[1]}").status_code==200
    assert dm.get(f"/campaigns/{cid}").status_code==200


def test_configuration_and_session_save_scopes(env):
    ctx,admin,viewer,dm,h,cid,mids=prepare(env);base=f"/api/campaigns/{cid}/transitions"
    config=dict(map_id=mids[0],name="Authored",x=100,y=100,visibility="secret",arrival="preserve")
    result=dm.post(base,json=config,headers=h)
    assert result.status_code==200,result.text
    eid=result.json()["saved_endpoint_id"]
    row=next(e for e in result.json()["endpoints"] if e["id"]==eid)
    result=dm.post(base+f"/{eid}/runtime",json=dict(revision=row["revision"],visibility="discovered",availability="blocked"),headers=h)
    assert result.status_code==200,result.text
    row=next(e for e in result.json()["endpoints"] if e["id"]==eid)
    assert row["name"]=="Authored"
    config.update(name="Changed configuration",revision=row["revision"])
    result=dm.post(base+f"/{eid}",json=config,headers=h)
    assert result.status_code==200,result.text
    assert result.json()["saved_endpoint_id"]==eid
    row=next(e for e in result.json()["endpoints"] if e["id"]==eid)
    assert row["runtime_visibility"]=="discovered" and row["runtime_availability"]=="blocked"
    assert dm.post(base+f"/{eid}/runtime",json=dict(revision=config["revision"],visibility=None,availability=None),headers=h).status_code==400
