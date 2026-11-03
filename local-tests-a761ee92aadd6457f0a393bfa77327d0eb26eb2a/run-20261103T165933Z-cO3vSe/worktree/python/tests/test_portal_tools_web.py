"""HTTP integration checks for an installed project environment (requires FastAPI)."""
import json
from test_web import env,login,csrf_of
from test_wall_editor_web import prepare,draft
from looking_glass.services.wall_model import WallSegment
from looking_glass.services.uvtt_export import rows_for


def test_visible_routes_are_admin_only_and_read_only(env):
    ctx,admin,viewer,dm,headers,mid=prepare(env)
    segs=[WallSegment(10,10,390,10),WallSegment(390,10,390,190),WallSegment(390,190,10,190),WallSegment(10,190,10,10)]
    segs += [WallSegment(x,a,x,b) for x in (150,250) for a,b in ((10,70),(130,190))]
    segs += [WallSegment(150,70,150,130,"portal",True,passage={"pair":"p","end":"a","sides":[{"role":"none"},{"role":"entry","kind":"secret","after":"locked_door","exit":0}]}),
             WallSegment(250,70,250,130,"portal",True,passage={"pair":"p","end":"b","sides":[{"role":"exit"},{"role":"none"}]})]
    saved=dm.post(f"/api/maps/{mid}/wall-editor",json=draft(dm,mid,rows_for(segs)),headers=headers)
    assert saved.status_code==200,saved.text
    cid=saved.json()["campaign_id"]
    active=dm.post(f"/api/campaigns/{cid}/active",json={"map_id":mid,"fog_action":"reset"},headers=headers)
    assert active.status_code==200,active.text
    revealed=dm.post(f"/api/maps/{mid}/reveal",json={"x":50,"y":100},headers=headers)
    assert revealed.status_code==200,revealed.text
    state=dm.get(f"/api/maps/{mid}").json()
    assert len(state["portal_routes"])==1 and state["portal_routes"][0]["state"]=="secret"
    count=state["op_count"]
    again=dm.get(f"/api/maps/{mid}").json();assert again["op_count"]==count
    player=login(viewer,"dm","dmpass123")
    public=player.get(f"/api/c/{cid}/state");assert public.status_code==200,public.text
    assert "portal_routes" not in json.dumps(public.json())
    assert player.get(f"/api/maps/{mid}").status_code==404
    other=login(admin,"dm2","dmpass123");assert other.get(f"/api/maps/{mid}").status_code==403
