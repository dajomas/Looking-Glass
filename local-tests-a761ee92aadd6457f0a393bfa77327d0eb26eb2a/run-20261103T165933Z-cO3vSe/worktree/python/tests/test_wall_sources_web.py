"""HTTP workflow regression tests, using the existing full-app fixtures."""

import json

from conftest import png_bytes, two_room_scene
from test_web import env, login, csrf_of  # noqa: F401


def _campaign(client, token, name):
    r = client.post("/campaigns", data={"csrf_token": token, "name": name}, follow_redirects=False)
    assert r.status_code == 303
    return int(r.headers["location"].split("/")[2].split("?")[0])


def _map(client, token, cid, size=(400, 200), walls=None):
    files = {"image": ("map.png", png_bytes(*size), "image/png")}
    if walls is not None:
        files["walls"] = ("maps.db", walls, "application/octet-stream")
    r = client.post(f"/campaigns/{cid}/maps", data={"csrf_token": token},
                    files=files, follow_redirects=False)
    assert r.status_code == 303, r.text
    return int(r.headers["location"].split("/")[2].split("?")[0])


def _database():
    a = dict(two_room_scene(), _id="a", name="Cellar")
    b = dict(two_room_scene(door=True), _id="b", name="Tower")
    return "\n".join(json.dumps(s) for s in (a, b)).encode()


def test_saved_source_reused_on_independent_maps(env):
    ctx, admin, viewer = env
    dm = login(admin, "dm", "dmpass123")
    token = csrf_of(dm); hdr = {"X-CSRF-Token": token}
    cid = _campaign(dm, token, "Source library")
    mid1 = _map(dm, token, cid, walls=_database())
    url = f"/api/campaigns/{cid}/wall-sources"
    sources = dm.get(url).json()["sources"]
    assert len(sources) == 1 and sources[0]["scene_count"] == 2
    sid = sources[0]["id"]
    assert dm.get(f"/api/maps/{mid1}").json()["walls"] == []
    assert 'saved-wall-library' in dm.get(f"/maps/{mid1}").text
    scenes = dm.get(f"/api/maps/{mid1}/wall-sources/{sid}").json()["scenes"]
    assert [s["name"] for s in scenes] == ["Cellar", "Tower"]
    result = dm.post(f"/api/maps/{mid1}/walls/from-source", headers=hdr,
                     json={"source_id": sid, "scene_index": 1})
    assert result.status_code == 200, result.text
    assert result.json()["scene"] == "Tower" and result.json()["imported"] == 7
    mid2 = _map(dm, token, cid, size=(800, 400))
    r = dm.post(f"/api/maps/{mid2}/walls/from-source", headers=hdr,
                json={"source_id": sid, "scene_index": 0})
    assert r.status_code == 200 and r.json()["imported"] == 5
    assert r.json()["calibration"]["scale_x"] == 2
    before = dm.get(f"/api/maps/{mid1}").json()
    assert before["calibration"]["scale_x"] == 1 and len(before["walls"]) == 7
    # Duplicate bytes retain the original immutable source.
    r = dm.post(url, headers=hdr, files={"file": ("renamed.db", _database())})
    assert r.status_code == 200 and r.json()["source"]["id"] == sid
    # A valid same-campaign import can keep existing calibration.
    r = dm.post(f"/api/maps/{mid2}/walls/from-source", headers=hdr,
                json={"source_id": sid, "scene_index": 1, "use_scene_calibration": False})
    assert r.status_code == 200 and r.json()["calibration"]["scale_x"] == 2
    for body, expected in [({"source_id": sid}, 422),
                           ({"source_id": sid, "scene_index": -1}, 422),
                           ({"source_id": sid, "scene_index": 999}, 400)]:
        assert dm.post(f"/api/maps/{mid1}/walls/from-source", json=body, headers=hdr).status_code == expected
    assert dm.post(f"/api/maps/{mid1}/walls/from-source",
                   json={"source_id": sid, "scene_index": 0}).status_code == 403
    other = _campaign(dm, token, "Other campaign")
    other_map = _map(dm, token, other)
    assert dm.get(f"/api/maps/{other_map}/wall-sources/{sid}").status_code == 400
    assert dm.post(f"/api/maps/{other_map}/walls/from-source", headers=hdr,
                   json={"source_id": sid, "scene_index": 0}).status_code == 400
    dm2 = login(admin, "dm2", "dmpass123")
    assert dm2.get(url).status_code == 403
    alice = login(viewer, "alice", "alicepass")
    assert alice.get(url).status_code == 404
    assert dm.post(url, headers=hdr, files={"file": ("bad.db", b"not json")}).status_code == 400
    assert dm.delete(f"{url}/{sid}", headers=hdr).status_code == 200
    assert dm.get(url).json()["sources"] == []
    assert dm.get(f"/api/maps/{mid1}").json()["walls"] == before["walls"]
    assert dm.get(f"/api/maps/{mid1}/wall-sources/{sid}").status_code == 400
