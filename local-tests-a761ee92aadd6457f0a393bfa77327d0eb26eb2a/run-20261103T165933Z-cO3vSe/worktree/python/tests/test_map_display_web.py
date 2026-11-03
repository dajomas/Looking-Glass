"""HTTP regressions: run with requirements-dev.txt installed."""
from test_web import env, login, csrf_of
from conftest import png_bytes


def test_display_policy_http(env):
    ctx, admin, viewer = env
    dm = login(admin, "dm", "dmpass123")
    token = csrf_of(dm)
    hdr = {"X-CSRF-Token": token}
    r = dm.post("/campaigns", data={"csrf_token": token, "name": "C"}, follow_redirects=False)
    cid = int(r.headers["location"].split("/")[2].split("?")[0])
    r = dm.post(f"/campaigns/{cid}/maps", data={"csrf_token": token, "name": "A"},
                files={"image": ("a.png", png_bytes(), "image/png")}, follow_redirects=False)
    mid = int(r.headers["location"].split("/")[2].split("?")[0])
    url = f"/api/campaigns/{cid}/active"
    dm.post(f"/api/maps/{mid}/reveal-all", headers=hdr)
    assert dm.post(url, json={"map_id": mid}, headers=hdr).status_code == 400
    assert dm.post(url, json={"map_id": mid, "fog_action": "reset"}).status_code == 403
    assert dm.post(url, json={"map_id": mid, "fog_action": "reset"}, headers=hdr).status_code == 200
    assert dm.get(f"/api/maps/{mid}").json()["op_count"] == 0
    assert dm.post(f"/api/maps/{mid}/undo", headers=hdr).status_code == 400
    assert dm.post(url, json={"map_id": None}, headers=hdr).status_code == 200
    form = f"/campaigns/{cid}/active"
    assert dm.post(form, data={"map_id": mid, "csrf_token": token}).status_code == 400
    assert dm.post(form, data={"map_id": mid, "csrf_token": token, "fog_action": "restore"}, follow_redirects=False).status_code == 303
    assert "map-display-dialog" in dm.get(f"/campaigns/{cid}").text
    assert "map_display_prompt.js" in dm.get(f"/maps/{mid}").text
    dm.post(f"/campaigns/{cid}/viewers/add", data={"csrf_token": token, "user_id": 4})
    alice = login(viewer, "alice", "alicepass")
    state = alice.get(f"/api/c/{cid}/state").json()
    image_url = state["map"]["image_url"]
    assert alice.get(image_url).headers["cache-control"] == "no-store"
    dm.post(f"/api/maps/{mid}/reveal", json={"x": 10, "y": 10}, headers=hdr)
    assert alice.get(image_url).status_code == 400
