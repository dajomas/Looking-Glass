"""Database errors after successful image storage must not orphan artwork.

Candidate: python/tests/test_image_database_failures.py
Run: python -m pytest -q python/tests/test_image_database_failures.py
Desired-behavior regressions, not xfails. Current routes may fail file assertions.
Faults are scoped injections, not real disk exhaustion or process termination.
"""
import io
import json
from pathlib import Path
import re
import sqlite3
from types import SimpleNamespace
from unittest.mock import AsyncMock
from urllib.parse import parse_qs, urlsplit

from PIL import Image
import pytest

from conftest import png_bytes, two_room_scene
from test_web import env, login, csrf_of
from looking_glass import db as db_module
from looking_glass.repositories import maps as maps_repo
from looking_glass.services import images

MESSAGE = "injected image/database boundary failure"
RED = (200,30,30)
GREEN = (30,200,30)
FOG = (0,0,0)


def files(root):
    return {p.relative_to(root).as_posix():p.read_bytes()
            for p in root.rglob("*") if p.is_file()}


def location_id(response, pattern):
    assert response.status_code == 303, (response.status_code, response.text)
    parts = urlsplit(response.headers["location"])
    query = parse_qs(parts.query, keep_blank_values=True)
    assert query.get("ok") and "err" not in query and "error" not in query
    match = re.fullmatch(pattern, parts.path)
    assert match, response.headers["location"]
    return int(match.group(1))


def row_snapshot(ctx):
    with ctx.db.connect() as conn:
        return tuple(conn.iterdump())


def viewer_output(case):
    state = case.player.get(f"/api/c/{case.cid}/state")
    assert state.status_code == 200, state.text
    payload = state.json()
    image = case.player.get(payload["map"]["image_url"])
    assert image.status_code == 200
    assert image.headers["content-type"].split(";")[0] == "image/png"
    with Image.open(io.BytesIO(image.content)) as rendered:
        rgb = rendered.convert("RGB")
        pixels = (rgb.getpixel((100,100)), rgb.getpixel((300,100)))
    return payload, image.content, pixels


class CommitProxy:
    """Only commit is intercepted; SQL, reads and rollback use real SQLite."""
    def __init__(self, connection, fault):
        self.connection = connection
        self.fault = fault

    def __getattr__(self, name):
        return getattr(self.connection, name)

    def commit(self):
        if self.fault.phase == "commit" and self.fault.target is self:
            self.fault.events.append("commit")
            raise sqlite3.OperationalError(MESSAGE)
        return self.connection.commit()


@pytest.fixture
def image_case(env, tmp_path):
    ctx, admin, viewer = env
    assert ctx.settings.data_dir.resolve().is_relative_to(tmp_path.resolve())
    dm = login(admin, "dm", "dmpass123")
    player = None
    try:
        csrf = csrf_of(dm)
        cid = location_id(dm.post("/campaigns", data={"csrf_token":csrf,"name":"Database failure"},
                                  follow_redirects=False), r"/campaigns/(\d+)")
        uploaded = dm.post(f"/campaigns/{cid}/maps", data={"csrf_token":csrf,"name":"Original"},
            files={"image":("red.png",png_bytes(color=RED),"image/png"),
                   "walls":("walls.json",json.dumps(two_room_scene()).encode(),"application/json")},
            follow_redirects=False)
        mid = location_id(uploaded, r"/maps/(\d+)")
        headers = {"X-CSRF-Token":csrf}
        response = dm.post(f"/api/campaigns/{cid}/active",
                           json={"map_id":mid,"fog_action":"restore"}, headers=headers)
        assert response.status_code == 200 and response.json()["ok"]
        response = dm.post(f"/api/maps/{mid}/reveal", json={"x":100,"y":100}, headers=headers)
        assert response.status_code == 200
        with ctx.db.connect() as conn:
            uid = conn.execute("SELECT id FROM users WHERE username='alice'").fetchone()[0]
            original = dict(maps_repo.get(conn, mid))
        assigned = dm.post(f"/campaigns/{cid}/viewers/add", data={"csrf_token":csrf,"user_id":uid},
                           follow_redirects=False)
        assert assigned.status_code == 303 and "err=" not in assigned.headers["location"]
        player = login(viewer, "alice", "alicepass")
        case = SimpleNamespace(ctx=ctx,dm=dm,player=player,csrf=csrf,cid=cid,mid=mid,original=original)
        case.before_output = viewer_output(case)
        assert case.before_output[2] == (RED, FOG)
        case.before_files = files(ctx.settings.maps_dir)
        case.before_rows = row_snapshot(ctx)
        yield case
    finally:
        if player is not None:
            player.close()
        dm.close()


def request_image(case, operation):
    path = f"/campaigns/{case.cid}/maps" if operation == "upload" else f"/maps/{case.mid}/image"
    return case.dm.post(path, data={"csrf_token":case.csrf,"name":"New image"},
                       files={"image":("green.png",png_bytes(color=GREEN),"image/png")},
                       follow_redirects=False)


def install_fault(patch, case, operation, phase):
    fault = SimpleNamespace(phase=phase,target=None,events=[],stored=[])
    real_connect = db_module._connect
    real_store = images.store_map_image
    attribute = "create" if operation == "upload" else "replace_image"
    real_write = getattr(maps_repo, attribute)

    def connect(path):
        return CommitProxy(real_connect(path), fault)

    def stored_image(*args, **kwargs):
        stored = real_store(*args, **kwargs)
        path = case.ctx.settings.maps_dir / stored.relative_path
        assert path.is_file()
        with Image.open(path) as image:
            image.load()
            assert image.size == (400,200) and image.convert("RGB").getpixel((100,100)) == GREEN
        fault.stored.append(stored)
        fault.events.append("stored")
        return stored

    def write(conn, *args, **kwargs):
        assert len(fault.stored) == 1, "The real image store must finish before database injection"
        fault.target = conn
        fault.events.append("before-write")
        if phase == "before-write":
            raise sqlite3.OperationalError(MESSAGE)
        result = real_write(conn, *args, **kwargs)
        assert conn.in_transaction
        assert conn.execute("SELECT COUNT(*) FROM maps WHERE image_file=?",
                            (fault.stored[0].relative_path,)).fetchone()[0] == 1
        fault.events.append("after-write")
        if phase == "after-write":
            raise sqlite3.OperationalError(MESSAGE)
        return result

    patch.setattr(db_module, "_connect", connect)
    patch.setattr(images, "store_map_image", stored_image)
    patch.setattr(maps_repo, attribute, write)
    return fault


@pytest.mark.parametrize("operation", ["upload", "replace"])
@pytest.mark.parametrize("phase", ["before-write", "after-write", "commit"])
def test_image_database_failure_preserves_prior_state_and_removes_new_file(image_case, monkeypatch, operation, phase):
    case = image_case
    ctx = case.ctx
    notification = AsyncMock(wraps=ctx.hub.publish)
    monkeypatch.setattr(ctx.hub, "publish", notification)
    with monkeypatch.context() as patch:
        fault = install_fault(patch, case, operation, phase)
        # Preserve current exception propagation; no new friendly-error contract.
        with pytest.raises(sqlite3.OperationalError, match=MESSAGE):
            request_image(case, operation)
        expected = ["stored", "before-write"]
        if phase in {"after-write", "commit"}:
            expected.append("after-write")
        if phase == "commit":
            expected.append("commit")
        assert fault.events == expected
        assert len(fault.stored) == 1
        failed_path = fault.stored[0].relative_path
        assert failed_path not in case.before_files
    notification.assert_not_awaited()
    assert row_snapshot(ctx) == case.before_rows
    with ctx.db.connect() as conn:
        assert conn.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
        assert conn.execute("PRAGMA foreign_key_check").fetchall() == []
        assert conn.execute("SELECT COUNT(*) FROM maps WHERE image_file=?", (failed_path,)).fetchone()[0] == 0
    assert viewer_output(case) == case.before_output
    assert files(ctx.settings.maps_dir) == case.before_files, "Database failure left orphan artwork or changed prior bytes"
    assert not (ctx.settings.maps_dir / failed_path).exists()

    # A fresh request must retain exactly its own successful new image.
    response = request_image(case, operation)
    if operation == "upload":
        mid = location_id(response, r"/maps/(\d+)")
        assert mid != case.mid
        assert viewer_output(case) == case.before_output
        notification.assert_not_awaited()
    else:
        assert response.status_code == 303, response.text
        query = parse_qs(urlsplit(response.headers["location"]).query)
        assert query.get("ok") and "err" not in query
        mid = case.mid
        after_output = viewer_output(case)
        assert after_output[2] == (GREEN, FOG)
        assert after_output[0]["map"]["version"] != case.before_output[0]["map"]["version"]
        notification.assert_awaited_once()
        assert notification.await_args.args == (case.cid, {"type":"refresh","reason":"image"})
    with ctx.db.connect() as conn:
        stored = dict(maps_repo.get(conn, mid))
        count = conn.execute("SELECT COUNT(*) FROM maps WHERE campaign_id=?", (case.cid,)).fetchone()[0]
    assert count == (2 if operation == "upload" else 1)
    new_path = stored["image_file"]
    assert new_path not in case.before_files and new_path != failed_path
    after_files = files(ctx.settings.maps_dir)
    expected_keys = set(case.before_files)
    if operation == "replace":
        expected_keys.remove(case.original["image_file"])
    assert set(after_files) == expected_keys | {new_path}
    assert all(after_files[key] == case.before_files[key] for key in expected_keys)
    with Image.open(io.BytesIO(after_files[new_path])) as image:
        assert image.convert("RGB").getpixel((100,100)) == GREEN
