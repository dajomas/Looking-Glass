"""HTTP integration coverage; requires the project's installed dev requirements."""
from test_web import env, login, csrf_of
from conftest import png_bytes


def test_room_import_access_and_assignment(env):
    ctx, admin, viewer = env
    dm=login(admin,"dm","dmpass123")
    token=csrf_of(dm)
    response=dm.post("/campaigns",data={"csrf_token":token,"name":"Rooms"},follow_redirects=False)
    cid=int(response.headers["location"].split("/")[2].split("?")[0])
    response=dm.post(f"/campaigns/{cid}/maps",data={"csrf_token":token,"name":"Map"},
                     files={"image":("map.png",png_bytes(),"image/png")},follow_redirects=False)
    mid=int(response.headers["location"].split("/")[2].split("?")[0])
    base=f"/api/maps/{mid}"
    route=base+"/room-note-library"
    upload={"file":("rooms.md",b"# Crypt\n**Gold**\n# Hall\nBones\n","text/markdown")}
    headers={"X-CSRF-Token":token}
    assert dm.post(route+"/import",files=upload).status_code==403
    other=login(admin,"dm2","dmpass123")
    assert other.get(route).status_code==403
    state=dm.get(base).json()
    result=dm.post(route+"/import",files=upload,headers=headers)
    assert result.status_code==200,result.text
    assert result.json()["added"]==2
    assert dm.post(route+"/import",files=upload,headers=headers).json()["added"]==0
    assert dm.get(base).json()["fog_version"]==state["fog_version"]
    assert dm.post(route+"/import",files={"file":("bad.md",b"no headings","text/markdown")},headers=headers).status_code==400
    assert len(dm.get(route).json()["entries"])==2
    room=dm.post(base+"/room-at",json={"x":100,"y":100},headers=headers).json()
    entry=dm.get(route).json()["entries"][0]
    body={"x":100,"y":100,"area_key":room["area_key"],"revision":room["revision"],"name":entry["name"],"markdown":entry["markdown"]}
    saved=dm.post(base+"/room-notes",json=body,headers=headers)
    assert saved.status_code==200,saved.text
    assert saved.json()["name"]=="Crypt" and "<strong>Gold</strong>" in saved.json()["html"]
    assert dm.get(base).json()["fog_version"]==state["fog_version"]
