"""Full-app tests; require FastAPI and runtime dependencies."""
import base64
import io
import json
from PIL import Image
from conftest import png_bytes, two_room_scene
from test_web import env, login, csrf_of  # noqa: F401
from test_wall_sources_web import _campaign, _map


def test_image_choice_and_type_permissions(env):
    ctx, admin, viewer = env
    dm = login(admin,"dm","dmpass123")
    token = csrf_of(dm); hdr = {"X-CSRF-Token": token}
    cid = _campaign(dm,token,"Artwork")
    mid = _map(dm,token,cid)
    scene = dict(two_room_scene(), img="data:image/png;base64," + base64.b64encode(png_bytes(800,400,(20,180,80))).decode())
    url = f"/api/campaigns/{cid}/wall-sources"
    sid = dm.post(url,headers=hdr,files={"file":("scene.json",json.dumps(scene).encode())}).json()["source"]["id"]
    assert dm.get(f"/api/maps/{mid}/wall-sources/{sid}").json()["scenes"][0]["image_available"]
    endpoint = f"/api/maps/{mid}/walls/from-source"
    body = {"source_id":sid,"scene_index":0}
    assert dm.post(endpoint,headers=hdr,json=body).json()["width"] == 400
    body["use_pack_image"] = True
    changed = dm.post(endpoint,headers=hdr,json=body)
    assert changed.status_code == 200, changed.text
    assert changed.json()["width"] == 800 and changed.json()["calibration"]["scale_x"] == 2
    expected_image_url = f"/api/maps/{mid}/image"
    assert changed.json()["image_url"] == expected_image_url
    metadata = dm.get(f"/api/maps/{mid}")
    assert metadata.status_code == 200, metadata.text
    assert metadata.json()["image_url"] == expected_image_url
    admin_art = dm.get(changed.json()["image_url"])
    assert admin_art.status_code == 200, admin_art.text
    assert admin_art.headers["cache-control"] == "no-store"
    dm.post(f"/api/maps/{mid}/reveal-all",headers=hdr)
    with Image.open(io.BytesIO(admin_art.content)) as a, Image.open(io.BytesIO(dm.get(f"/api/maps/{mid}/viewer-preview").content)) as v:
        assert a.convert("RGB").tobytes() == v.convert("RGB").tobytes()
    endpoint = f"/api/maps/{mid}/wall-types"
    assert dm.post(endpoint,json={"disabled":["door"]}).status_code == 403
    assert dm.post(endpoint,headers=hdr,json={"disabled":["invalid"]}).status_code == 400
    assert dm.post(endpoint,headers=hdr,json={"disabled":["door"]}).json()["disabled_wall_types"] == ["door"]
    assert dm.get(f"/api/maps/{mid}").json()["disabled_wall_types"] == ["door"]
    other = login(admin,"dm2","dmpass123")
    assert other.post(endpoint,headers={"X-CSRF-Token":csrf_of(other)},json={"disabled":[]}).status_code == 403
    alice = login(viewer,"alice","alicepass")
    assert alice.get(f"/api/maps/{mid}/image").status_code == 404
    assert alice.post(endpoint,json={"disabled":[]}).status_code == 404
