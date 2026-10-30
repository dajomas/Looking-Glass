"""Recovery-storage failures must block live campaign replacement and notification."""
import errno
import html
import re
from pathlib import Path
from unittest.mock import AsyncMock
from urllib.parse import parse_qs, urlsplit

import pytest

from conftest import png_bytes
from test_web import env, login, csrf_of
from looking_glass.services import campaign_backup
from looking_glass.web.admin import campaigns


def files(root):
    return {path.relative_to(root).as_posix():path.read_bytes() for path in root.rglob("*") if path.is_file()}


@pytest.mark.parametrize("error", [errno.EACCES, errno.ENOSPC, errno.EIO], ids=["permission", "disk-full", "io-error"])
def test_restore_recovery_failure_blocks_live_mutation_and_notification(env, monkeypatch, error):
    ctx, admin, viewer = env
    dm = login(admin, "dm", "dmpass123")
    csrf = csrf_of(dm)
    response = dm.post("/campaigns", data={"csrf_token":csrf,"name":"Storage failure"}, follow_redirects=False)
    assert response.status_code == 303
    cid = int(re.search(r"/campaigns/(\d+)", response.headers["location"]).group(1))
    base = f"/campaigns/{cid}"
    uploaded = dm.post(base + "/maps", data={"csrf_token":csrf,"name":"Keep this map"},
                       files={"image":("map.png",png_bytes(),"image/png")}, follow_redirects=False)
    assert uploaded.status_code == 303
    mid = int(re.search(r"/maps/(\d+)", uploaded.headers["location"]).group(1))
    active = dm.post(f"/api/campaigns/{cid}/active", json={"map_id":mid,"fog_action":"restore"}, headers={"X-CSRF-Token":csrf})
    assert active.status_code == 200
    backup = dm.post(base + "/backup", data={"csrf_token":csrf})
    assert backup.status_code == 200
    raw = backup.content
    preview = dm.post(base + "/restore/inspect", data={"csrf_token":csrf}, files={"backup":("backup.zip",raw)}, follow_redirects=False)
    assert preview.status_code == 200
    token = html.unescape(re.search(r'name="preview" value="([^"]+)"', preview.text).group(1))
    with ctx.db.connect() as conn:
        before_rows = tuple(conn.iterdump())
        before_digest = campaign_backup.target_digest(conn, cid)
    before_maps = files(ctx.settings.maps_dir)
    before_recovery = files(ctx.settings.data_dir / "recovery")
    reached, live_restores = [], []
    real_restore = campaign_backup.restore_campaign

    def failed_recovery(*args, **kwargs):
        reached.append(True)
        raise OSError(error, "injected recovery storage failure")

    def watched_restore(conn, *args, **kwargs):
        database = conn.execute("PRAGMA database_list").fetchone()[2]
        if Path(database).resolve() == ctx.settings.database_path.resolve():
            live_restores.append(True)
        return real_restore(conn, *args, **kwargs)

    notification = AsyncMock()
    monkeypatch.setattr(campaign_backup, "save_recovery", failed_recovery)
    monkeypatch.setattr(campaign_backup, "restore_campaign", watched_restore)
    monkeypatch.setattr(campaigns.notify, "campaign_changed", notification)
    response = dm.post(base + "/restore", data={"csrf_token":csrf,"confirm":"Storage failure","preview":token},
                       files={"backup":("backup.zip",raw)}, follow_redirects=False)
    assert response.status_code == 303
    message = parse_qs(urlsplit(response.headers["location"]).query)["err"][0]
    assert message.startswith("Restore blocked:")
    assert reached == [True] and not live_restores
    notification.assert_not_awaited()
    with ctx.db.connect() as conn:
        assert tuple(conn.iterdump()) == before_rows
        assert campaign_backup.target_digest(conn, cid) == before_digest
        assert conn.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
        assert conn.execute("PRAGMA foreign_key_check").fetchall() == []
    assert files(ctx.settings.maps_dir) == before_maps
    assert files(ctx.settings.data_dir / "recovery") == before_recovery
