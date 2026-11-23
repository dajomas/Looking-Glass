"""End-to-end suite: real `python/main.py serve` subprocess, real browsers.

Each pytest-playwright browser (Chromium, Firefox) runs every journey. The server
is started once per session with a throwaway config and data directory; tests
isolate themselves with unique campaign and user names.
"""
import os
import re
import signal
import socket
import subprocess
import sys
import time
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen

import pytest
from playwright.sync_api import expect

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "python"))
from looking_glass.server import BROWSER_BLOCKED_PORTS  # noqa: E402

SUPERADMIN, SUPERADMIN_PASSWORD = "superadmin", "e2e-superadmin-password"
expect.set_options(timeout=15_000)


def pytest_configure(config):
    # Failure screenshots and traces go next to the run's other results.
    if config.option.output == "test-results":
        artifacts = os.environ.get("E2E_ARTIFACTS")
        config.option.output = str(Path(artifacts) / "failures") if artifacts else str(ROOT / "e2e-results" / "_local" / "failures")


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()
    setattr(item, "rep_" + report.when, report)


@pytest.fixture(scope="session")
def browser_type_launch_args(browser_type_launch_args, browser_name):
    # Containers and CI runners often lack the user namespaces Chromium's sandbox needs.
    args = dict(browser_type_launch_args)
    if browser_name == "chromium":
        args["args"] = [*args.get("args", []), "--no-sandbox"]
    return args


def free_port(taken):
    while True:
        with socket.socket() as sock:
            sock.bind(("127.0.0.1", 0))
            port = sock.getsockname()[1]
        if port not in BROWSER_BLOCKED_PORTS and port not in taken:
            return port


class Server:
    """One `python/main.py serve` process with its own config and data; restartable."""

    def __init__(self, base, name, fog, viewer):
        self.base, self.name = base, name
        admin_port = free_port(())
        viewer_port = free_port({admin_port})
        self.admin, self.viewer = f"http://127.0.0.1:{admin_port}", f"http://127.0.0.1:{viewer_port}"
        self.config = base / "config.yaml"
        self.config.write_text(f"""\
server: {{host: 127.0.0.1, admin_port: {admin_port}, viewer_port: {viewer_port}, log_level: info, access_log_success: true}}
storage: {{data_dir: "{(base / 'data').as_posix()}"}}
security: {{secure_cookies: false, initial_superadmin: {SUPERADMIN}}}
fog: {fog}
viewer: {viewer}
""", encoding="utf-8")
        self.log = base / "server.log"
        self.process = None

    def start(self):
        environment = {key: value for key, value in os.environ.items() if not key.startswith("LG_")}
        environment.update(LG_SUPERADMIN_PASSWORD=SUPERADMIN_PASSWORD, PYTHONUNBUFFERED="1")
        with self.log.open("ab") as output:
            self.process = subprocess.Popen(
                [sys.executable, str(ROOT / "python/main.py"), "--config", str(self.config), "serve"],
                cwd=self.base, env=environment, stdout=output, stderr=subprocess.STDOUT)
        for url, entry in ((self.admin, "admin"), (self.viewer, "viewer")):
            deadline = time.monotonic() + 60
            while True:
                if self.process.poll() is not None:
                    pytest.fail(f"Server exited with {self.process.returncode}:\n{self.log.read_text(errors='replace')}")
                try:
                    with urlopen(f"{url}/healthz", timeout=1) as response:
                        if f'"entry":"{entry}"' in response.read().decode().replace(" ", ""):
                            break
                except (URLError, OSError):
                    pass
                if time.monotonic() > deadline:
                    pytest.fail(f"{entry} portal did not answer /healthz:\n{self.log.read_text(errors='replace')}")
                time.sleep(0.2)

    def stop(self):
        if self.process is not None and self.process.poll() is None:
            self.process.send_signal(signal.SIGINT)
            try:
                self.process.wait(timeout=15)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait()

    def restart(self):
        self.stop()
        self.start()


def _serve(tmp_path_factory, name, fog, viewer):
    server = Server(tmp_path_factory.mktemp(name), name, fog, viewer)
    try:
        server.start()
        yield server
    finally:
        server.stop()
        artifacts = os.environ.get("E2E_ARTIFACTS")
        if artifacts and server.log.exists():  # keep the whole server log with the run's results
            Path(artifacts).mkdir(parents=True, exist_ok=True)
            (Path(artifacts) / f"{name}.log").write_bytes(server.log.read_bytes())


@pytest.fixture(scope="session")
def server(tmp_path_factory):
    # Small work resolution, no feathering and PNG keep pixel checks exact.
    yield from _serve(tmp_path_factory, "server", "{work_max_dim: 400, feather_px: 0}", "{image_format: png}")


@pytest.fixture(scope="session")
def webp_server(tmp_path_factory):
    # The usual player format with default feathering and quality; started only when used.
    yield from _serve(tmp_path_factory, "webp-server", "{work_max_dim: 400}", "{image_format: webp}")


def _slug(nodeid):
    # Same folder as pytest-playwright's screenshots and trace for this test.
    return re.sub(r"[^a-z0-9]+", "-", nodeid.lower()).strip("-")


@pytest.fixture
def actors(new_context, request, pytestconfig):
    """Factory for logged-out pages in separate browser contexts (one per person)."""
    from support import Watch
    watch = Watch()
    servers = [request.getfixturevalue(name) for name in ("server", "webp_server") if name in request.fixturenames]
    log_starts = [(server, server.log.stat().st_size) for server in servers]
    pages = []

    def page(label):
        context = new_context(viewport={"width": 1280, "height": 900})
        created = context.new_page()
        watch.attach(label, created)
        pages.append(created)
        return created

    yield page
    failed = any(getattr(request.node, f"rep_{phase}", None) is not None and getattr(request.node, f"rep_{phase}").failed
                 for phase in ("setup", "call"))
    if failed:
        folder = Path(pytestconfig.option.output) / _slug(request.node.nodeid)
        folder.mkdir(parents=True, exist_ok=True)
        (folder / "console.txt").write_text("\n".join(watch.lines) + "\n", encoding="utf-8")
        for server, start in log_starts:
            with server.log.open("rb") as handle:
                handle.seek(start)
                (folder / f"{server.name}-log.txt").write_bytes(handle.read())
        for index, current in enumerate(pages):
            try:
                (folder / f"page-{index}-url.txt").write_text(current.url + "\n", encoding="utf-8")
            except Exception:
                pass
    assert not watch.errors, "Uncaught page errors:\n" + "\n".join(watch.errors)
