"""Full HTTP permission, atomic save and passage-schema integration checks."""
from test_web import env,login,csrf_of
from test_wall_editor_web import prepare,draft
from test_passages import pair
from looking_glass.services.uvtt_export import rows_for
from looking_glass.services.foundry_import import parse_wall_file
from fastapi.testclient import TestClient


def test_portal_save_export_and_stale_save(env):
    ctx,admin,viewer,dm,headers,mid=prepare(env)
    body=draft(dm,mid,rows_for(pair("secret","locked_door")))
    path=f"/api/maps/{mid}/wall-editor"
    assert dm.post(path,json=body).status_code==403
    saved=dm.post(path,json=body,headers=headers)
    assert saved.status_code==200,saved.text
    assert saved.json()["walls"]==body["walls"]
    assert dm.post(path,json=body,headers=headers).status_code==409
    exported=dm.get(f"/api/maps/{mid}/walls.uvtt")
    assert exported.status_code==200
    assert exported.json()["looking_glass"]["version"]==2
    assert [s.passage for s in parse_wall_file(exported.content)[0].segments]==[s.passage for s in pair("secret","locked_door")]
    other=login(admin,"dm2","dmpass123")
    assert other.post(path,json=body,headers={"X-CSRF-Token":csrf_of(other)}).status_code==403
    for suffix in ("wall-editor","door-action","door-arrows/reveal"):
        assert TestClient(viewer).post(f"/api/maps/{mid}/{suffix}",json=body).status_code==404


def test_invalid_graph_save_is_atomic(env):
    ctx,admin,viewer,dm,headers,mid=prepare(env)
    body=draft(dm,mid,rows_for(pair()))
    path=f"/api/maps/{mid}/wall-editor"
    assert dm.post(path,json=body,headers=headers).status_code==200
    before=dm.get(path).json();bad=draft(dm,mid,rows_for(pair())[:1])
    assert dm.post(path,json=bad,headers=headers).status_code==400
    assert dm.get(path).json()==before


def test_portal_wall_type_is_accepted(env):
    ctx,admin,viewer,dm,headers,mid=prepare(env)
    result=dm.post(f"/api/maps/{mid}/wall-types",json={"disabled_wall_types":["portal"]},headers=headers)
    assert result.status_code==200,result.text
    assert "portal" in result.json()["disabled_wall_types"]
