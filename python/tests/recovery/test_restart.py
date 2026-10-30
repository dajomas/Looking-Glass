"""Real entry-point restart tests, isolated from all installation data."""
import copy
import io
import json
import os
from pathlib import Path
import re
import socket
import subprocess
import sys
import time

import httpx2 as httpx
from PIL import Image
import pytest

from looking_glass.config import DEFAULTS, Settings
from looking_glass.rbac import Role
from looking_glass.repositories import users
from looking_glass.server import BROWSER_BLOCKED_PORTS
from looking_glass.web.context import AppContext

ROOT = Path(__file__).resolve().parents[3]


class Application:
    def __init__(self, directory, evidence):
        self.directory, self.evidence = directory, evidence
        self.process = None
        self.log = None
        self.starts = 0
        reserved = []
        try:
            for _ in range(2):
                while True:
                    sock = socket.socket()
                    sock.bind(("127.0.0.1", 0))
                    if sock.getsockname()[1] not in BROWSER_BLOCKED_PORTS:
                        reserved.append(sock)
                        break
                    sock.close()
            ports = [sock.getsockname()[1] for sock in reserved]
        finally:
            for sock in reserved:
                sock.close()
        self.urls = [f"http://127.0.0.1:{port}" for port in ports]
        raw = copy.deepcopy(DEFAULTS)
        raw["server"].update(host="127.0.0.1", admin_port=ports[0], viewer_port=ports[1])
        raw["storage"].update(data_dir=str(directory / "data"), database="recovery.db")
        raw["fog"].update(work_max_dim=400, feather_px=0)
        raw["viewer"]["image_format"] = "png"
        self.settings = Settings(raw=raw)
        self.config = directory / "config.json"
        self.config.write_text(json.dumps(raw), encoding="utf-8")
        ctx = AppContext.build(self.settings)
        with ctx.db.connect() as conn:
            users.create(conn, "restart-dm", "restart-dm-password", Role.ADMIN)
            self.viewer_id = users.create(conn, "restart-player", "restart-player-password", Role.VIEWER)
        self.db = ctx.db

    def start(self):
        assert self.process is None
        self.starts += 1
        self.evidence.mkdir(parents=True, exist_ok=True)
        self.log = (self.evidence / f"server-{self.starts}.log").open("wb")
        env = {key: value for key, value in os.environ.items() if not key.startswith("LG_")}
        env.update(PYTHONPATH=str(ROOT / "python"), PYTHONUNBUFFERED="1", LG_SUPERADMIN_PASSWORD="isolated-bootstrap-password")
        self.process = subprocess.Popen(
            [sys.executable, str(ROOT / "python/main.py"), "--config", str(self.config), "serve"],
            cwd=self.directory, env=env, stdout=self.log, stderr=subprocess.STDOUT,
        )
        deadline = time.monotonic() + 25
        with httpx.Client(timeout=1, trust_env=False) as client:
            while time.monotonic() < deadline:
                assert self.process.poll() is None, f"Application exited during startup; see {self.evidence}"
                try:
                    states = [client.get(url + "/healthz").json() for url in self.urls]
                    if all(state.get("ok") and state.get("entry") == entry for state, entry in zip(states, ("admin", "viewer"))):
                        return
                except (httpx.HTTPError, ValueError):
                    pass
                time.sleep(0.05)
        pytest.fail(f"Application startup timed out; see {self.evidence}")

    def stop(self, force=False):
        if self.process is None:
            return
        process, self.process = self.process, None
        try:
            if process.poll() is None:
                process.kill() if force else process.terminate()
            try:
                code = process.wait(timeout=12)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)
                pytest.fail("Application did not terminate within 12 seconds")
            if not force:
                assert code == 0, f"Unclean application shutdown ({code}); see {self.evidence}"
        finally:
            self.log.close()


@pytest.fixture
def application(tmp_path, request):
    evidence = ROOT / "test-results/recovery" / request.node.name
    app = Application(tmp_path, evidence)
    try:
        app.start()
        yield app
    finally:
        app.stop()


def login(client, username, password):
    response = client.post("/login", data={"username": username, "password": password})
    assert response.status_code == 303, response.text
    response = client.get("/", follow_redirects=True)
    assert response.status_code == 200
    return re.search(r'name="csrf-token" content="([^"]+)"', response.text).group(1)


def assert_pixels(player, cid):
    response = player.get(f"/api/c/{cid}/state")
    assert response.status_code == 200, response.text
    state = response.json()
    assert state["map"]["name"] == "Persistent map"
    image = player.get(state["map"]["image_url"])
    assert image.status_code == 200
    with Image.open(io.BytesIO(image.content)) as artwork:
        rgb = artwork.convert("RGB")
        assert rgb.getpixel((100, 100)) == (200, 30, 30)
        assert rgb.getpixel((300, 100)) == (0, 0, 0)
    return state


@pytest.mark.parametrize("force", [False, True], ids=["graceful-restart", "committed-state-after-kill"])
def test_restart_preserves_displayed_fog_and_access(application, force):
    app = application
    with httpx.Client(base_url=app.urls[0], timeout=10, trust_env=False) as dm, httpx.Client(base_url=app.urls[1], timeout=10, trust_env=False) as player:
        csrf = login(dm, "restart-dm", "restart-dm-password")
        created = dm.post("/campaigns", data={"csrf_token": csrf, "name": "Recovery"})
        assert created.status_code == 303, created.text
        cid = int(re.search(r"/campaigns/(\d+)", created.headers["location"]).group(1))
        buffer = io.BytesIO()
        Image.new("RGB", (400, 200), (200, 30, 30)).save(buffer, "PNG")
        segments = [[10,10,390,10], [390,10,390,190], [390,190,10,190], [10,190,10,10], [200,10,200,190]]
        scene = {"width":400, "height":200, "padding":0, "grid":{"size":100}, "walls":[{"c":line,"move":20,"sight":20} for line in segments]}
        uploaded = dm.post(f"/campaigns/{cid}/maps", data={"csrf_token":csrf,"name":"Persistent map"}, files={"image":("map.png",buffer.getvalue(),"image/png"),"walls":("walls.json",json.dumps(scene).encode(),"application/json")})
        assert uploaded.status_code == 303, uploaded.text
        mid = int(re.search(r"/maps/(\d+)", uploaded.headers["location"]).group(1))
        assigned = dm.post(f"/campaigns/{cid}/viewers/add", data={"csrf_token":csrf,"user_id":app.viewer_id})
        assert assigned.status_code == 303, assigned.text
        headers = {"X-CSRF-Token":csrf}
        active = dm.post(f"/api/campaigns/{cid}/active", json={"map_id":mid,"fog_action":"restore"}, headers=headers)
        assert active.status_code == 200, active.text
        revealed = dm.post(f"/api/maps/{mid}/reveal", json={"x":100,"y":100}, headers=headers)
        assert revealed.status_code == 200, revealed.text
        login(player, "restart-player", "restart-player-password")
        before = assert_pixels(player, cid)
        with app.db.connect() as conn:
            saved = conn.execute("SELECT operations FROM map_fog_snapshots WHERE map_id=?", (mid,)).fetchone()[0]
            assert json.loads(saved)
        app.stop(force=force)
        app.start()
        # Existing cookies must still authorize the viewer after a process restart.
        after = assert_pixels(player, cid)
        assert after["map"]["version"] == before["map"]["version"]
        with app.db.connect() as conn:
            assert conn.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
            assert conn.execute("PRAGMA foreign_key_check").fetchall() == []
            assert conn.execute("SELECT operations FROM map_fog_snapshots WHERE map_id=?", (mid,)).fetchone()[0] == saved
        with httpx.Client(base_url=app.urls[1], timeout=5, trust_env=False) as anonymous:
            assert anonymous.get(f"/api/c/{cid}/state").status_code in (401, 403)
