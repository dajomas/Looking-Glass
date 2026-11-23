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
from dataclasses import dataclass
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


@dataclass
class Server:
    admin: str
    viewer: str
    log: Path


def free_port(taken):
    while True:
        with socket.socket() as sock:
            sock.bind(("127.0.0.1", 0))
            port = sock.getsockname()[1]
        if port not in BROWSER_BLOCKED_PORTS and port not in taken:
            return port


@pytest.fixture(scope="session")
def server(tmp_path_factory):
    base = tmp_path_factory.mktemp("server")
    admin_port = free_port(())
    viewer_port = free_port({admin_port})
    config = base / "config.yaml"
    # Small work resolution, no feathering and PNG keep pixel checks exact.
    config.write_text(f"""\
server: {{host: 127.0.0.1, admin_port: {admin_port}, viewer_port: {viewer_port}, log_level: info}}
storage: {{data_dir: "{(base / 'data').as_posix()}"}}
security: {{secure_cookies: false, initial_superadmin: {SUPERADMIN}}}
fog: {{work_max_dim: 400, feather_px: 0}}
viewer: {{image_format: png}}
""", encoding="utf-8")
    environment = {key: value for key, value in os.environ.items() if not key.startswith("LG_")}
    environment.update(LG_SUPERADMIN_PASSWORD=SUPERADMIN_PASSWORD, PYTHONUNBUFFERED="1")
    log = base / "server.log"
    with log.open("wb") as output:
        process = subprocess.Popen([sys.executable, str(ROOT / "python/main.py"), "--config", str(config), "serve"],
                                   cwd=base, env=environment, stdout=output, stderr=subprocess.STDOUT)
    urls = Server(f"http://127.0.0.1:{admin_port}", f"http://127.0.0.1:{viewer_port}", log)
    try:
        for url, entry in ((urls.admin, "admin"), (urls.viewer, "viewer")):
            deadline = time.monotonic() + 60
            while True:
                if process.poll() is not None:
                    pytest.fail(f"Server exited with {process.returncode}:\n{log.read_text(errors='replace')}")
                try:
                    with urlopen(f"{url}/healthz", timeout=1) as response:
                        if f'"entry":"{entry}"' in response.read().decode().replace(" ", ""):
                            break
                except (URLError, OSError):
                    pass
                if time.monotonic() > deadline:
                    pytest.fail(f"{entry} portal did not answer /healthz:\n{log.read_text(errors='replace')}")
                time.sleep(0.2)
        yield urls
    finally:
        if process.poll() is None:
            process.send_signal(signal.SIGINT)
            try:
                process.wait(timeout=15)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
        artifacts = os.environ.get("E2E_ARTIFACTS")
        if artifacts:  # keep the whole server log with the run's results
            Path(artifacts).mkdir(parents=True, exist_ok=True)
            (Path(artifacts) / "server.log").write_bytes(log.read_bytes())


def _slug(nodeid):
    return re.sub(r"[^A-Za-z0-9._-]+", "-", nodeid).strip("-")[:150]


@pytest.fixture
def actors(server, new_context, request, pytestconfig):
    """Factory for logged-out pages in separate browser contexts (one per person)."""
    from support import Watch
    watch = Watch()
    log_start = server.log.stat().st_size
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
        with server.log.open("rb") as handle:
            handle.seek(log_start)
            (folder / "server-log.txt").write_bytes(handle.read())
        for index, current in enumerate(pages):
            try:
                (folder / f"page-{index}-url.txt").write_text(current.url + "\n", encoding="utf-8")
            except Exception:
                pass
    assert not watch.errors, "Uncaught page errors:\n" + "\n".join(watch.errors)
