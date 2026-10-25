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

    library=dm.get(route).json()["entries"]
    assert next(e for e in library if e["name"]=="Crypt")["assigned"] is True
    # Edit overlay must not change fog and stale geometry must be rejected.
    overlay=dm.post(base+"/room-edit-overlay",json={"x":100,"y":100,"area_key":saved.json()["area_key"]},headers=headers)
    assert overlay.status_code==200 and overlay.json()["png"]
    assert dm.get(base).json()["fog_version"]==state["fog_version"]
    assert dm.post(base+"/room-edit-overlay",json={"x":100,"y":100,"area_key":"0"*64},headers=headers).status_code==400
    crypt=next(e for e in library if e["name"]=="Crypt")
    hall=next(e for e in library if e["name"]=="Hall")
    assert dm.delete(route+f"/{hall['id']}").status_code==403
    assert other.delete(route+f"/{hall['id']}",headers={"X-CSRF-Token":csrf_of(other)}).status_code==403
    assert dm.delete(route+f"/{crypt['id']}",headers=headers).status_code==400
    removed=dm.delete(route+f"/{hall['id']}",headers=headers)
    assert removed.status_code==200 and len(removed.json()["entries"])==1
    # Clearing keeps revision history and rejects a subsequent stale edit.
    clear={**body,"revision":saved.json()["revision"],"name":"","markdown":""}
    cleared=dm.post(base+"/room-notes",json=clear,headers=headers)
    assert cleared.status_code==200,cleared.text
    assert cleared.json()["name"]==cleared.json()["markdown"]==""
    assert cleared.json()["revision"]>saved.json()["revision"]
    assert next(e for e in dm.get(route).json()["entries"] if e["name"]=="Crypt")["assigned"] is False
    assert dm.post(base+"/room-notes",json=body,headers=headers).status_code==400
    notes_only={**clear,"revision":cleared.json()["revision"],"markdown":"Notes without a name"}
    result=dm.post(base+"/room-notes",json=notes_only,headers=headers)
    assert result.status_code==200,result.text
    assert result.json()["name"]=="" and result.json()["markdown"]=="Notes without a name"
    assert dm.get(base).json()["fog_version"]==state["fog_version"]
