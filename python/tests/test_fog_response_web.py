"""Bug 4 HTTP regressions; require the normal application dependencies."""
import io
import pytest
pytest.importorskip("fastapi")
from PIL import Image
from conftest import png_bytes
from test_web import env, login
from looking_glass.services import images
from looking_glass.repositories import maps as maps_repo


def prepare(env):
    ctx, admin, viewer = env
    with ctx.db.connect() as conn:
        cid = conn.execute("INSERT INTO campaigns(name,owner_id) VALUES('Race test',2)").lastrowid
        stored = images.store_map_image(png_bytes(),ctx.settings.maps_dir,cid)
        mid = maps_repo.create(conn,cid,"Map",stored.relative_path,stored.width,stored.height,True)
        conn.execute("INSERT INTO fog_ops(map_id,op) VALUES(?,'reveal_all')",(mid,))
        conn.execute("UPDATE campaigns SET active_map_id=? WHERE id=?",(mid,cid))
        conn.execute("INSERT INTO campaign_viewers(campaign_id,user_id) VALUES(?,4)",(cid,))
    return ctx, login(admin,"dm","dmpass123"), login(viewer,"alice","alicepass"), cid, mid


@pytest.mark.parametrize("endpoint",["viewer","preview"])
def test_response_survives_composite_cleanup(env, monkeypatch, endpoint):
    ctx, dm, alice, cid, mid = prepare(env)
    capture = ctx.fog.viewer_bytes
    def prune(*args):
        body = capture(*args)
        ctx.fog.invalidate(mid)
        return body
    monkeypatch.setattr(ctx.fog,"viewer_bytes",prune)
    response = alice.get(f"/api/c/{cid}/image") if endpoint == "viewer" else dm.get(f"/api/maps/{mid}/viewer-preview")
    assert response.status_code == 200, response.text
    assert response.headers["cache-control"] == "no-store"
    assert response.headers["content-type"] == ctx.fog.viewer_media_type
    assert int(response.headers["content-length"]) == len(response.content)
    with Image.open(io.BytesIO(response.content)) as image:
        assert image.size == (400,200)
    assert not list(ctx.fog.cache_dir.glob(f"viewer_{mid}_*"))


def test_stale_version_rejected_before_capture(env, monkeypatch):
    ctx, dm, alice, cid, mid = prepare(env)
    def forbidden(*args):
        raise AssertionError("stale request rendered")
    monkeypatch.setattr(ctx.fog,"viewer_bytes",forbidden)
    assert alice.get(f"/api/c/{cid}/image?v=stale").status_code == 400


@pytest.mark.parametrize("change",["version","revoke"])
def test_post_render_checks_remain(env, monkeypatch, change):
    ctx, dm, alice, cid, mid = prepare(env)
    capture = ctx.fog.viewer_bytes
    def mutate(*args):
        body = capture(*args)
        with ctx.db.connect() as conn:
            if change == "version":
                conn.execute("UPDATE maps SET fog_version=fog_version+1 WHERE id=?",(mid,))
            else:
                conn.execute("DELETE FROM campaign_viewers WHERE campaign_id=? AND user_id=4",(cid,))
        return body
    monkeypatch.setattr(ctx.fog,"viewer_bytes",mutate)
    assert alice.get(f"/api/c/{cid}/image").status_code == (400 if change == "version" else 404)
