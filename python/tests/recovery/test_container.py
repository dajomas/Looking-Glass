"""Built-image checks; explicitly enabled in the Recovery CI job."""
import io
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import time
import uuid

import httpx
from PIL import Image
import pytest

from test_restart import login, assert_pixels

ROOT = Path(__file__).resolve().parents[3]
pytestmark = pytest.mark.skipif(
    os.environ.get("LG_RUN_CONTAINER_TESTS") != "1",
    reason="Opt in with LG_RUN_CONTAINER_TESTS=1; requires a disposable Docker environment",
)


def docker(evidence, *arguments, timeout=60, check=True):
    evidence.mkdir(parents=True, exist_ok=True)
    command = ["docker", *arguments]
    try:
        result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, timeout=timeout, check=False)
    except (OSError, subprocess.TimeoutExpired) as exc:
        with (evidence / "docker.log").open("a", encoding="utf-8") as log:
            log.write(f"{command!r}\n{exc!r}\n")
        raise
    with (evidence / "docker.log").open("a", encoding="utf-8") as log:
        log.write(f"{command!r}\nexit={result.returncode}\n{result.stdout}\n{result.stderr}\n")
    if check:
        assert result.returncode == 0, f"Docker command failed: {arguments[0]}; see {evidence / 'docker.log'}"
    return result


@pytest.fixture(scope="session")
def built_image():
    evidence = ROOT / "test-results/container-build"
    assert shutil.which("docker"), "Recovery container checks require Docker; missing Docker is a failure in CI"
    docker(evidence, "version")
    image = "looking-glass-test:" + uuid.uuid4().hex
    try:
        docker(evidence, "build", "--pull", "-f", str(ROOT / "Containerfile"), "-t", image, str(ROOT), timeout=600)
        yield image
    finally:
        # Remove only this invocation's image, never prune shared daemon resources.
        docker(evidence, "image", "rm", image, check=False)


class Container:
    def __init__(self, image, config, evidence):
        self.image, self.config, self.evidence = image, config, evidence
        suffix = uuid.uuid4().hex
        self.name = "looking-glass-test-" + suffix
        self.volume = "looking-glass-test-data-" + suffix
        self.started = False
        self.generation = 0
        self.urls = []

    def command(self, *args, **kwargs):
        return docker(self.evidence, *args, **kwargs)

    def inspect(self):
        return json.loads(self.command("inspect", self.name).stdout)[0]

    def save_logs(self):
        result = self.command("logs", self.name, check=False)
        (self.evidence / f"server-{self.generation}.log").write_text(result.stdout + result.stderr, encoding="utf-8")

    def start(self):
        self.generation += 1
        self.command(
            "run", "--detach", "--name", self.name,
            "--publish", "127.0.0.1::5000", "--publish", "127.0.0.1::5100",
            "--mount", f"type=volume,source={self.volume},target=/app/data",
            "--mount", f"type=bind,source={self.config},target=/app/ci-config.json,readonly",
            "--env", "LG_SUPERADMIN_PASSWORD=container-bootstrap-password",
            self.image, "python", "python/main.py", "--config", "/app/ci-config.json", "serve",
        )
        self.started = True
        info = self.inspect()
        ports = info["NetworkSettings"]["Ports"]
        self.urls = []
        for port in ("5000/tcp", "5100/tcp"):
            binding = ports[port][0]
            assert binding["HostIp"] == "127.0.0.1"
            self.urls.append("http://127.0.0.1:" + binding["HostPort"])
        deadline = time.monotonic() + 30
        with httpx.Client(timeout=1, trust_env=False) as client:
            while time.monotonic() < deadline:
                try:
                    states = [client.get(url + "/healthz").json() for url in self.urls]
                    if all(state.get("ok") and state.get("entry") == entry for state, entry in zip(states, ("admin", "viewer"))):
                        return
                except (httpx.HTTPError, ValueError):
                    pass
                if not self.inspect()["State"]["Running"]:
                    self.save_logs()
                    pytest.fail("Container exited during startup")
                time.sleep(0.1)
        self.save_logs()
        pytest.fail("Container listeners were not ready within 30 seconds")

    def stop_and_remove(self):
        self.command("stop", "--time", "10", self.name, timeout=20)
        info = self.inspect()
        self.save_logs()
        assert not info["State"]["Running"] and info["State"]["ExitCode"] == 0, info["State"]
        self.command("rm", self.name)
        self.started = False


@pytest.fixture
def container(built_image, tmp_path, request):
    config = tmp_path / "container-config.json"
    config.write_text(json.dumps({
        "server":{"host":"0.0.0.0","admin_port":5000,"viewer_port":5100},
        "storage":{"data_dir":"/app/data","database":"looking_glass.db"},
        "fog":{"work_max_dim":400,"feather_px":0},
        "viewer":{"image_format":"png"},
    }), encoding="utf-8")
    config.chmod(0o644)
    app = Container(built_image, config, ROOT / "test-results/container" / request.node.name)
    app.command("volume", "create", app.volume)
    try:
        app.start()
        yield app
    finally:
        try:
            if app.started:
                app.stop_and_remove()
        finally:
            # A partially started or failed container must not keep the volume mounted.
            app.command("rm", "--force", app.name, check=False)
            app.command("volume", "rm", app.volume)


def test_container_nonroot_listeners_templates_and_static_assets(container):
    app = container
    uid = app.command("exec", app.name, "python", "-c", "import os; print(os.stat('/proc/1').st_uid)").stdout.strip()
    assert uid == "1001", f"Expected non-root application PID 1, got uid={uid}"
    for url in app.urls:
        with httpx.Client(base_url=url, timeout=5, trust_env=False) as client:
            response = client.get("/login")
            assert response.status_code == 200 and 'name="username"' in response.text
            css = client.get("/static/css/common.css")
            assert css.status_code == 200 and "text/css" in css.headers.get("content-type", "")
            javascript = client.get("/static/js/pan_zoom.js")
            assert javascript.status_code == 200 and "PanZoom" in javascript.text


def test_container_new_instance_preserves_named_volume_and_viewer_session(container):
    app = container
    seed = """from looking_glass.config import load_settings
from looking_glass.db import Database
from looking_glass.repositories import users
from looking_glass.rbac import Role
settings = load_settings('/app/ci-config.json')
with Database(settings.database_path).connect() as conn:
    users.create(conn, 'restart-dm', 'restart-dm-password', Role.ADMIN)
    viewer = users.create(conn, 'restart-player', 'restart-player-password', Role.VIEWER)
print(viewer)
"""
    viewer_id = int(app.command("exec", "--env", "PYTHONPATH=/app/python", app.name, "python", "-c", seed).stdout.strip())
    with httpx.Client(base_url=app.urls[0], timeout=10, trust_env=False) as dm, httpx.Client(base_url=app.urls[1], timeout=10, trust_env=False) as player:
        csrf = login(dm, "restart-dm", "restart-dm-password")
        created = dm.post("/campaigns", data={"csrf_token":csrf,"name":"Container recovery"})
        assert created.status_code == 303, created.text
        cid = int(re.search(r"/campaigns/(\d+)", created.headers["location"]).group(1))
        buffer = io.BytesIO()
        Image.new("RGB", (400,200), (200,30,30)).save(buffer, "PNG")
        segments = [[10,10,390,10],[390,10,390,190],[390,190,10,190],[10,190,10,10],[200,10,200,190]]
        scene = {"width":400,"height":200,"padding":0,"grid":{"size":100},"walls":[{"c":line,"move":20,"sight":20} for line in segments]}
        uploaded = dm.post(f"/campaigns/{cid}/maps", data={"csrf_token":csrf,"name":"Persistent map"}, files={"image":("map.png",buffer.getvalue(),"image/png"),"walls":("walls.json",json.dumps(scene).encode(),"application/json")})
        assert uploaded.status_code == 303, uploaded.text
        mid = int(re.search(r"/maps/(\d+)", uploaded.headers["location"]).group(1))
        assigned = dm.post(f"/campaigns/{cid}/viewers/add", data={"csrf_token":csrf,"user_id":viewer_id})
        assert assigned.status_code == 303, assigned.text
        headers = {"X-CSRF-Token":csrf}
        active = dm.post(f"/api/campaigns/{cid}/active", json={"map_id":mid,"fog_action":"restore"}, headers=headers)
        assert active.status_code == 200, active.text
        reveal = dm.post(f"/api/maps/{mid}/reveal", json={"x":100,"y":100}, headers=headers)
        assert reveal.status_code == 200, reveal.text
        login(player, "restart-player", "restart-player-password")
        before = assert_pixels(player, cid)
        cookies = httpx.Cookies(player.cookies)
    app.stop_and_remove()
    app.start()
    with httpx.Client(base_url=app.urls[1], cookies=cookies, timeout=10, trust_env=False) as player:
        after = assert_pixels(player, cid)
        assert after["map"]["version"] == before["map"]["version"]
    with httpx.Client(base_url=app.urls[1], timeout=5, trust_env=False) as anonymous:
        assert anonymous.get(f"/api/c/{cid}/state").status_code in (401,403)
